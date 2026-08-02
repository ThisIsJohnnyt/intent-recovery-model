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
    passes = {r["id"]: probe_passes(r) for r in results}
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
