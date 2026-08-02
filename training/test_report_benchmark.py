"""Standalone assertion tests for report_benchmark.py's probe_passes() --
dummy data only. No pytest dependency: run directly with
`python test_report_benchmark.py`.

Covers a fail-open scoring gap found in review: probe_passes() rejected a
semantic score only when it was non-null and not 2, so a probe with every
score left null (never actually scored) passed as long as format_valid was
true and capability_checks were true. required_semantic_dimensions closes
that gap for probes that declare it, without changing behavior for probes
that don't.
"""
import sys

from report_benchmark import probe_passes

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
