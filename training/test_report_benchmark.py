"""Standalone assertion tests for report_benchmark.py's probe_passes() --
dummy data only. No pytest dependency: run directly with
`python test_report_benchmark.py`.

Covers a fail-open scoring gap found in review: probe_passes() rejected a
semantic score only when it was non-null and not 2, so a probe with every
score left null (never actually scored) passed as long as format_valid was
true and capability_checks were true. required_semantic_dimensions closes
that gap for probes that declare it, without changing behavior for probes
that don't.

Also covers the same gap found in the shared, protected
datasets/benchmark/gold_v1.2.1_probes.jsonl benchmark: probes 13-16 there
have no primary_checks at all, so an entirely-unscored scaffold vacuously
passed all four of them (4/16) until required_semantic_dimensions was
added to all 16 probes -- these are integration tests against that real
file, not synthetic probe dicts, since the whole point is proving the
actual shared fixture is fail-closed, not just the mechanism in the
abstract.
"""
import sys
from pathlib import Path

# report_benchmark.load_jsonl, not run_benchmark.load_probes -- run_benchmark.py
# imports torch/transformers at module level, so importing anything from it
# (even a trivial JSONL reader) would drag those into what's supposed to be a
# lightweight reporter test, breaking it in any environment without the ML
# dependencies installed. Both functions are identical one-line JSONL readers.
from report_benchmark import load_jsonl as load_probes
from report_benchmark import probe_passes

GOLD_V1_2_1_PROBES_PATH = Path(__file__).parent.parent / "datasets" / "benchmark" / "gold_v1.2.1_probes.jsonl"

FAILURES = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


def _base_result(**overrides) -> dict:
    result = {
        "id": "test-probe",
        "format_valid": True,
        "scores": {
            "topic_completeness": None,
            "attribution_accuracy": None,
            "uncertainty_preservation": None,
            "unsupported_addition_resistance": None,
        },
        "capability_checks": {"SOME_CHECK": True},
        "required_semantic_dimensions": [],
    }
    result.update(overrides)
    return result


def test_no_required_dimensions_all_null_still_passes():
    # Backward compatibility: a probe that never declares
    # required_semantic_dimensions keeps the original lenient behavior --
    # null means "not applicable to this probe," same as every existing
    # regression_guard/negative_example probe already relies on.
    result = _base_result()
    check(
        "probe_passes: no required_semantic_dimensions -- all-null scores still pass (unchanged legacy behavior)",
        probe_passes(result) is True,
    )


def test_fail_open_gap_is_closed_all_required_dimensions_null():
    # The exact bug found in review: format_valid=True, every score null,
    # capability_checks all True -- previously passed fail-open.
    result = _base_result(
        required_semantic_dimensions=["topic_completeness", "unsupported_addition_resistance"],
    )
    check(
        "probe_passes: all required dimensions null -> fails (was the fail-open gap)",
        probe_passes(result) is False,
    )


def test_one_required_dimension_null_fails():
    result = _base_result(
        required_semantic_dimensions=["topic_completeness", "unsupported_addition_resistance"],
        scores={
            "topic_completeness": 2,
            "attribution_accuracy": None,
            "uncertainty_preservation": None,
            "unsupported_addition_resistance": None,  # required, still null
        },
    )
    check(
        "probe_passes: one required dimension still null (others scored) -> fails",
        probe_passes(result) is False,
    )


def test_one_required_dimension_missing_from_scores_entirely_fails():
    result = _base_result(
        required_semantic_dimensions=["topic_completeness", "unsupported_addition_resistance"],
        scores={"topic_completeness": 2},  # unsupported_addition_resistance key absent, not just null
    )
    check(
        "probe_passes: required dimension missing from scores dict entirely -> fails",
        probe_passes(result) is False,
    )


def test_all_required_dimensions_scored_2_format_valid_checks_true_passes():
    result = _base_result(
        required_semantic_dimensions=["topic_completeness", "unsupported_addition_resistance"],
        scores={
            "topic_completeness": 2,
            "attribution_accuracy": None,
            "uncertainty_preservation": None,
            "unsupported_addition_resistance": 2,
        },
    )
    check(
        "probe_passes: all required dimensions scored 2, format valid, checks true -> passes",
        probe_passes(result) is True,
    )


def test_required_dimension_scored_1_fails():
    result = _base_result(
        required_semantic_dimensions=["topic_completeness"],
        scores={"topic_completeness": 1, "attribution_accuracy": None,
                 "uncertainty_preservation": None, "unsupported_addition_resistance": None},
    )
    check(
        "probe_passes: required dimension scored 1 (partial credit) -> fails, no partial credit at the gate",
        probe_passes(result) is False,
    )


def test_unknown_required_dimension_name_raises():
    result = _base_result(required_semantic_dimensions=["not_a_real_dimension"])
    try:
        probe_passes(result)
        check("probe_passes: unknown required_semantic_dimensions name raises", False)
    except ValueError as e:
        check(
            "probe_passes: unknown required_semantic_dimensions name raises",
            "not_a_real_dimension" in str(e),
            str(e),
        )


def test_format_invalid_fails_even_with_required_dimensions_satisfied():
    result = _base_result(
        format_valid=False,
        required_semantic_dimensions=["topic_completeness"],
        scores={"topic_completeness": 2, "attribution_accuracy": None,
                 "uncertainty_preservation": None, "unsupported_addition_resistance": None},
    )
    check(
        "probe_passes: format_valid=False fails regardless of required-dimension scores",
        probe_passes(result) is False,
    )


def _unscored_scaffold_for(probe: dict) -> dict:
    """Mirrors run_benchmark.py's exact result shape for a probe nobody has
    scored yet -- every score null, every declared capability_check null."""
    return {
        "id": probe["id"],
        "required_semantic_dimensions": probe.get("required_semantic_dimensions", []),
        "format_valid": True,
        "scores": {
            "topic_completeness": None,
            "attribution_accuracy": None,
            "uncertainty_preservation": None,
            "unsupported_addition_resistance": None,
        },
        "capability_checks": {c: None for c in probe.get("primary_checks", [])},
    }


def test_gold_v1_2_1_probes_all_declare_required_semantic_dimensions():
    probes = load_probes(GOLD_V1_2_1_PROBES_PATH)
    check("gold_v1.2.1_probes.jsonl: loads as 16 probes", len(probes) == 16, str(len(probes)))
    missing = [p["id"] for p in probes if not p.get("required_semantic_dimensions")]
    check(
        "gold_v1.2.1_probes.jsonl: every probe declares at least one required_semantic_dimensions",
        not missing,
        f"missing on: {missing}",
    )


def test_gold_v1_2_1_probes_unscored_scaffold_reports_zero_of_sixteen():
    # The exact gap found in review: probes 13-16 have empty primary_checks,
    # so an entirely-unscored scaffold vacuously passed all four of them
    # (4/16) before required_semantic_dimensions was added to every probe.
    probes = load_probes(GOLD_V1_2_1_PROBES_PATH)
    results = [_unscored_scaffold_for(p) for p in probes]
    passing = [r["id"] for r in results if probe_passes(r)]
    check(
        "gold_v1.2.1_probes.jsonl: entirely-unscored scaffold reports 0/16, not 4/16",
        passing == [],
        f"vacuously passing: {passing}",
    )


def test_gold_v1_2_1_probes_fully_scored_scaffold_reports_sixteen_of_sixteen():
    # Confirms the added required_semantic_dimensions are satisfiable, not
    # an over-constraint that makes every probe unpassable.
    probes = load_probes(GOLD_V1_2_1_PROBES_PATH)
    results = []
    for p in probes:
        result = _unscored_scaffold_for(p)
        for dimension in result["required_semantic_dimensions"]:
            result["scores"][dimension] = 2
        result["capability_checks"] = {c: True for c in result["capability_checks"]}
        results.append(result)
    passing = [r["id"] for r in results if probe_passes(r)]
    check(
        "gold_v1.2.1_probes.jsonl: fully and correctly scored scaffold reports 16/16",
        len(passing) == 16,
        f"passing: {passing}",
    )


def main() -> None:
    tests = [
        test_no_required_dimensions_all_null_still_passes,
        test_fail_open_gap_is_closed_all_required_dimensions_null,
        test_one_required_dimension_null_fails,
        test_one_required_dimension_missing_from_scores_entirely_fails,
        test_all_required_dimensions_scored_2_format_valid_checks_true_passes,
        test_required_dimension_scored_1_fails,
        test_unknown_required_dimension_name_raises,
        test_format_invalid_fails_even_with_required_dimensions_satisfied,
        test_gold_v1_2_1_probes_all_declare_required_semantic_dimensions,
        test_gold_v1_2_1_probes_unscored_scaffold_reports_zero_of_sixteen,
        test_gold_v1_2_1_probes_fully_scored_scaffold_reports_sixteen_of_sixteen,
    ]
    for t in tests:
        t()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("All report_benchmark.py tests passed.")


if __name__ == "__main__":
    main()
