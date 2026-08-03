"""Turn a scored benchmark results file into release-gate statistics.

Usage:
    python report_benchmark.py <benchmark.jsonl> <results.json>

Reads probe definitions (category/kind/status) from the benchmark file and
per-probe scores from a results file produced by run_benchmark.py and then
scored (semantic score fields filled in -- see that script's docstring).
Prints:
    - overall pass rate
    - pass rate by category
    - pass rate by probe kind
    - failure count by taxonomy label
    - regression guards passed (of status=="regression_guard" probes)
    - negative examples resolved (of status=="negative_example" probes)
    - format-validity rate

Pass definition (strict, deliberately -- see docs/benchmarks/benchmark_suite.md):
a probe PASSES only if format_valid is true, every non-null score is
exactly 2, and every capability_check is exactly true. Any 0, any 1, any
false check, or invalid format is a FAIL. There is no partial credit in
the aggregate numbers -- "mostly right" is not "right" for a release gate,
even though the underlying scores (still in the results file) preserve the
partial-credit detail for anyone reading the raw data instead of the
summary.
"""
import json
import sys
from collections import Counter
from pathlib import Path

from contract_adapters import (
    evaluate_count_rule,
    preflight_validate_count_rules,
    probe_requires_v2_structural_verification,
    select_contract_adapter,
)

_MISSING = object()


KNOWN_SEMANTIC_DIMENSIONS = {
    "topic_completeness",
    "attribution_accuracy",
    "uncertainty_preservation",
    "unsupported_addition_resistance",
}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def probe_passes(result: dict) -> bool:
    """A null score means "not applicable to this probe" for ordinary
    probes -- but for a probe that declares required_semantic_dimensions,
    null on one of those specific dimensions means "never actually
    scored," not "not applicable," and must fail rather than pass by
    default. Without this, an entirely-unscored result (format_valid=True,
    every score still null, every capability_check already True) passes
    fail-open, since "every non-null score is 2" is vacuously true when
    every score is null."""
    if not result.get("format_valid"):
        return False
    scores = result.get("scores", {})
    if any(v is not None and v != 2 for v in scores.values()):
        return False
    required_dimensions = result.get("required_semantic_dimensions", [])
    unknown = set(required_dimensions) - KNOWN_SEMANTIC_DIMENSIONS
    if unknown:
        raise ValueError(
            f"{result.get('id')}: required_semantic_dimensions names not recognized: {sorted(unknown)}"
        )
    if any(scores.get(dimension) != 2 for dimension in required_dimensions):
        return False
    checks = result.get("capability_checks", {})
    if any(v is not True for v in checks.values()):
        return False
    return True


def verify_v2_structural_integrity(probe: dict, result: dict) -> None:
    """Active structural recomputation (per
    prompt_contract_vnext_static_final_review_and_branch_reconciliation.md's
    Disagreement 1, tightened by
    prompt_contract_vnext_adapter_structural_implementation_review.md's
    Finding 2): independently re-derives the ENTIRE stored structural
    package from `probe` (the frozen, trusted benchmark definition) and a
    fresh reparse of `result["raw_output"]`, and requires every one of the
    following to match exactly, raising ValueError on the first mismatch
    or missing field rather than silently returning False:

    - contract name/version/fingerprint, parser version (re-selected via
      select_contract_adapter("v2"), which itself re-verifies the live
      fingerprint against the locked constant);
    - format_valid, recomputed from raw_output, compared with an exact
      boolean check (not truthiness -- a stored string "false" must not
      slip past a bare `if not stored_value` check the way it does in
      probe_passes(), which only ever sees real booleans from the v1 path
      and is intentionally left alone here);
    - parsed narrative/bullets/actions, recomputed from raw_output;
    - bullet_count_rule/action_count_rule, compared against what `probe`
      itself declares (not against another copy in `result` -- this is
      what closes the reproduction where editing result["bullet_count_rule"]
      had no effect on the old, narrower check, because that check never
      read it either; now the frozen probe is the only source of truth for
      what the rule *should* be, and the stored copy must match it exactly);
    - bullet_count_result/action_count_result, recomputed via the same
      evaluate_count_rule() the runner used to write them.

    Called unconditionally, as its own statement, before probe_passes() or
    evaluate_v2_count_rules() run -- never as part of an `and` chain that
    Python could short-circuit past when semantics already fail or are
    unscored. That was Finding 2's ordering bug: a tampered structural
    field went undetected whenever the result also happened to be
    semantically unscored, because the old check only ran on the right-hand
    side of `probe_passes(result) and ...`.
    """
    result_id = result.get("id", probe.get("id"))
    adapter = select_contract_adapter("v2")

    stored_contract = result.get("contract", _MISSING)
    if stored_contract != adapter.name:
        raise ValueError(f"{result_id}: expected contract={adapter.name!r}, stored {stored_contract!r}")

    for field, expected in (
        ("contract_version", adapter.version),
        ("contract_fingerprint", adapter.expected_fingerprint),
        ("parser_version", adapter.parser_version),
    ):
        stored = result.get(field, _MISSING)
        if stored is _MISSING:
            raise ValueError(f"{result_id}: missing required structural field {field!r}")
        if stored != expected:
            raise ValueError(f"{result_id}: {field} mismatch -- stored {stored!r}, expected {expected!r}")

    raw_output = result.get("raw_output", "")
    recomputed_valid = adapter.check_format_valid(raw_output)
    stored_valid = result.get("format_valid", _MISSING)
    if stored_valid is _MISSING or type(stored_valid) is not bool or stored_valid != recomputed_valid:
        raise ValueError(
            f"{result_id}: format_valid mismatch or wrong type -- stored {stored_valid!r} "
            f"({type(stored_valid).__name__}), recomputed {recomputed_valid!r}"
        )

    parsed = adapter.parse(raw_output) if recomputed_valid else None
    if parsed is not None:
        for field, expected in (
            ("parsed_narrative", parsed.narrative),
            ("parsed_bullets", parsed.bullets),
            ("parsed_actions", parsed.actions),
        ):
            stored = result.get(field, _MISSING)
            if stored is _MISSING or stored != expected:
                raise ValueError(f"{result_id}: {field} mismatch -- stored {stored!r}, recomputed {expected!r}")
        actual_bullets, actual_actions = len(parsed.bullets), len(parsed.actions)
    else:
        for field in ("parsed_narrative", "parsed_bullets", "parsed_actions"):
            stored = result.get(field, _MISSING)
            if stored is not None:
                raise ValueError(f"{result_id}: {field} should be None when output doesn't parse, got {stored!r}")
        actual_bullets, actual_actions = None, None

    probe_bullet_rule = probe.get("bullet_count_rule")
    probe_action_rule = probe.get("action_count_rule")
    for field, expected in (("bullet_count_rule", probe_bullet_rule), ("action_count_rule", probe_action_rule)):
        stored = result.get(field, _MISSING)
        if stored is _MISSING or stored != expected:
            raise ValueError(
                f"{result_id}: {field} does not match the frozen probe's declared rule -- "
                f"stored {stored!r}, probe declares {expected!r}"
            )

    recomputed_bullet_result = evaluate_count_rule(probe_bullet_rule, actual_bullets)
    recomputed_action_result = evaluate_count_rule(probe_action_rule, actual_actions)
    for field, expected in (
        ("bullet_count_result", recomputed_bullet_result),
        ("action_count_result", recomputed_action_result),
    ):
        stored = result.get(field, _MISSING)
        if stored is _MISSING or stored != expected:
            raise ValueError(
                f"{result_id}: {field} does not match reparsed/recomputed value -- "
                f"stored {stored!r}, recomputed {expected!r}"
            )


def evaluate_v2_count_rules(probe: dict, result: dict) -> bool:
    """Assumes verify_v2_structural_integrity(probe, result) already ran
    without raising -- v2_result_passes() always calls it first,
    unconditionally. This just reads the now-verified-consistent stored
    rule results and returns whether both are satisfied. Kept separate
    from the integrity check so "genuinely unmet rule" (False) stays
    distinct from "inconsistent record" (raise)."""
    bullet_result = result.get("bullet_count_result")
    action_result = result.get("action_count_result")
    return (bullet_result is None or bullet_result["passed"]) and (
        action_result is None or action_result["passed"]
    )


def v2_result_passes(probe: dict, result: dict) -> bool:
    """Combined pass condition for a v2-structural probe. Structural
    integrity is verified FIRST, as its own statement -- not as the
    left-hand operand of an `and` a failing/unscored semantic gate could
    short-circuit past (Finding 2). Only after a clean structural
    verification does this apply the existing, unmodified probe_passes()
    gate ANDed with the count-rule gate. probe_passes() itself is never
    touched by v2 concerns, so the protected 16-probe/5-historical-case v1
    schema is not weakened by v2's additional requirements."""
    verify_v2_structural_integrity(probe, result)
    return probe_passes(result) and evaluate_v2_count_rules(probe, result)


def pct(passed: int, total: int) -> str:
    if total == 0:
        return "n/a (0 probes)"
    return f"{passed}/{total} ({100 * passed / total:.0f}%)"


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python report_benchmark.py <benchmark.jsonl> <results.json>", file=sys.stderr)
        sys.exit(1)

    benchmark_path = Path(sys.argv[1])
    results_path = Path(sys.argv[2])

    probes = {p["id"]: p for p in load_jsonl(benchmark_path)}
    results = json.loads(results_path.read_text(encoding="utf-8"))

    # Finding 5 fix: repeat the same preflight validation run_benchmark.py
    # applies before generation -- so a benchmark file hand-edited after
    # generation (or a results file produced by a different process that
    # skipped runner-side preflight) can't bypass it and reach an
    # unvalidated pass/fail computation below. Only imports/selects the v2
    # adapter if this benchmark file actually contains a v2-structural
    # probe -- an ordinary v1-only report run never touches v2 modules.
    probe_list = list(probes.values())
    if any(probe_requires_v2_structural_verification(p) for p in probe_list):
        preflight_validate_count_rules(probe_list, select_contract_adapter("v2"))

    missing = set(probes) - {r["id"] for r in results}
    extra = {r["id"] for r in results} - set(probes)
    if missing:
        print(f"WARNING: benchmark file has probes missing from results: {sorted(missing)}", file=sys.stderr)
    if extra:
        print(f"WARNING: results file has probes not in the benchmark file: {sorted(extra)}", file=sys.stderr)

    def has_unscored_field(r: dict) -> bool:
        return any(v is None for v in r.get("scores", {}).values()) or any(
            v is None for v in r.get("capability_checks", {}).values()
        )

    unscored = [r["id"] for r in results if has_unscored_field(r)]
    still_null = [
        r["id"]
        for r in results
        if all(v is None for v in r.get("scores", {}).values())
        and all(v is None for v in r.get("capability_checks", {}).values())
    ]
    if still_null:
        print(
            f"WARNING: these probes look completely unscored (all null): {still_null}. "
            "Results will undercount passes until scored.",
            file=sys.stderr,
        )

    total = len(results)
    # Finding 1 fix: the actual pass computation must route a v2-structural
    # probe's result through v2_result_passes() (structural integrity +
    # count rules + semantics), not the plain probe_passes() gate alone --
    # v2_result_passes() previously existed but nothing in main() ever
    # called it. Routing is driven by the frozen `probes` entry, never by
    # anything in `r` itself (a result claiming a contract it doesn't
    # actually have must not be able to dodge this).
    passes = {}
    for r in results:
        probe = probes.get(r["id"])
        if probe is not None and probe_requires_v2_structural_verification(probe):
            passes[r["id"]] = v2_result_passes(probe, r)
        else:
            passes[r["id"]] = probe_passes(r)
    overall_passed = sum(passes.values())

    print(f"=== Benchmark report: {benchmark_path.name} vs {results_path.name} ===\n")
    print(f"Overall pass rate: {pct(overall_passed, total)}")
    print(f"Format-validity rate: {pct(sum(r['format_valid'] for r in results), total)}\n")

    print("Pass rate by category:")
    by_category = Counter()
    passed_by_category = Counter()
    for r in results:
        by_category[r["category"]] += 1
        if passes[r["id"]]:
            passed_by_category[r["category"]] += 1
    for category in sorted(by_category):
        print(f"  {category}: {pct(passed_by_category[category], by_category[category])}")

    print("\nPass rate by probe kind:")
    by_kind = Counter()
    passed_by_kind = Counter()
    for r in results:
        by_kind[r["kind"]] += 1
        if passes[r["id"]]:
            passed_by_kind[r["kind"]] += 1
    for kind in sorted(by_kind):
        print(f"  {kind}: {pct(passed_by_kind[kind], by_kind[kind])}")

    print("\nFailure count by taxonomy label:")
    label_counts = Counter()
    for r in results:
        for label in r.get("failure_labels", []):
            label_counts[label] += 1
    if label_counts:
        for label, count in label_counts.most_common():
            print(f"  {label}: {count}")
    else:
        print("  (none recorded)")

    regression_guards = [r for r in results if r.get("status") == "regression_guard"]
    guards_passed = sum(passes[r["id"]] for r in regression_guards)
    print(f"\nRegression guards passed: {pct(guards_passed, len(regression_guards))}")
    if guards_passed < len(regression_guards):
        failed_guards = [r["id"] for r in regression_guards if not passes[r["id"]]]
        print(f"  REGRESSION: previously-passing guard(s) now failing: {failed_guards}")

    negative_examples = [r for r in results if r.get("status") == "negative_example"]
    negatives_resolved = sum(passes[r["id"]] for r in negative_examples)
    print(f"\nNegative examples resolved: {pct(negatives_resolved, len(negative_examples))}")
    if negatives_resolved:
        resolved_ids = [r["id"] for r in negative_examples if passes[r["id"]]]
        print(f"  Known limitation(s) now fixed -- reclassify to regression_guard: {resolved_ids}")

    # acceptance_gate: a new capability being checked for the first time, with
    # no established prior-passing baseline -- unlike regression_guard, a
    # first-run failure here is not a "regression," so it gets its own count
    # instead of being folded into either existing category.
    acceptance_gates = [r for r in results if r.get("status") == "acceptance_gate"]
    gates_passed = sum(passes[r["id"]] for r in acceptance_gates)
    print(f"\nAcceptance gates passed: {pct(gates_passed, len(acceptance_gates))}")
    if gates_passed < len(acceptance_gates):
        failed_gates = [r["id"] for r in acceptance_gates if not passes[r["id"]]]
        print(f"  Not yet passing: {failed_gates}")

    if unscored:
        print(f"\nNote: {len(unscored)} probe(s) have at least one null score/check: {unscored}")


if __name__ == "__main__":
    main()
