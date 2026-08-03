"""Turn a scored benchmark results file into release-gate statistics.

Usage:
    python report_benchmark.py <benchmark.jsonl> <results.json> [--contract=v1|v2] [--allow-partial]

--contract selects which prompt-contract adapter (contract_adapters.py)
this report is verified under -- v1 (default) applies the plain
probe_passes() gate; v2 additionally requires and independently
re-verifies the full structural package (contract identity, parsed
structure, count rules) run_benchmark.py's v2 path stores. This is
explicit, never inferred from a probe's shape (category or the presence
of a count-rule field) -- an earlier version tried inference and it broke
in both directions at once: the historical v1 five-case acceptance set
also declares count-rule fields (predating v2) and got wrongly forced
through v2 checks, while a protected-probe result genuinely generated
under v2 has no count rules on the probe and wrongly skipped v2
verification entirely. A benchmark file containing any
source_determined_items_v2 case requires --contract=v2 explicitly; running
it under v1 (default or explicit) raises rather than silently downgrading
the gate.

--allow-partial opts into a warn-only, non-release diagnostic mode for
missing/extra result IDs; by default the benchmark and results ID sets
must match exactly, or the report raises rather than silently scoring a
subset as if it were complete.

Reads probe definitions (category/kind/status) from the benchmark file and
per-probe scores from a results file produced by run_benchmark.py and then
scored (semantic score fields filled in -- see that script's docstring).
Every copied identity/rubric field (category, kind, status,
required_semantic_dimensions, the capability_checks key set) is bound to
and verified against the frozen benchmark probe, not trusted from the
result -- a scorer may change score/check VALUES, never which judgments
are required or which release-gate bucket a result counts toward.
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
    DEFAULT_CONTRACT,
    V2_ACCEPTANCE_CATEGORY,
    ContractSelectionError,
    evaluate_count_rule,
    parse_contract_flag,
    preflight_validate_count_rules,
    reject_duplicate_ids,
    select_contract_adapter,
)

_MISSING = object()


KNOWN_SEMANTIC_DIMENSIONS = {
    "topic_completeness",
    "attribution_accuracy",
    "uncertainty_preservation",
    "unsupported_addition_resistance",
}

# Every field run_benchmark.py's v2 path stores that a v1 result never has
# (per prompt_contract_vnext_final_boundary_rereview.md's Finding 1). A v1-
# mode report must reject a result carrying ANY of these -- checking key
# PRESENCE, not `.get(field) is not None` -- because a v2 result with just
# "contract" nulled out (JSON null, not removed) still carries every other
# field in this set and was previously accepted as an ordinary v1 result
# once only the value of "contract" was checked.
V2_ONLY_STRUCTURAL_FIELDS = (
    "contract",
    "contract_version",
    "contract_fingerprint",
    "parser_version",
    "parsed_narrative",
    "parsed_bullets",
    "parsed_actions",
    "bullet_count_rule",
    "action_count_rule",
    "bullet_count_result",
    "action_count_result",
)


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


def require_format_valid_is_boolean(result: dict) -> None:
    """Per prompt_contract_vnext_final_boundary_rereview.md's Finding 2:
    probe_passes() gates on `if not result.get("format_valid")`, a
    truthiness check -- the non-empty string "false" is truthy in Python,
    so it slips past that check exactly as "false" (the boolean) does not.
    verify_v2_structural_integrity already closes this for v2 by
    recomputing format_valid from a fresh reparse and requiring an exact
    boolean match; v1 has no equivalent recomputation path (no structural
    parser to reparse against), so this is the minimum fix available for
    it: format_valid must be present and must actually be a bool, for
    every result regardless of contract. Called unconditionally in
    main(), alongside verify_rubric_binding -- not folded into
    probe_passes() itself, which stays untouched."""
    stored = result.get("format_valid", _MISSING)
    if stored is _MISSING or type(stored) is not bool:
        raise ValueError(
            f"{result.get('id')}: format_valid must be a literal boolean, "
            f"got {stored!r} ({type(stored).__name__})"
        )


def verify_rubric_binding(probe: dict, result: dict) -> None:
    """Binds every copied scoring/identity field to the canonical, frozen
    probe -- per
    prompt_contract_vnext_adapter_structural_focused_rereview.md's
    Finding 2: verify_v2_structural_integrity bound the count-rule/
    contract fields to the frozen probe, but required_semantic_dimensions,
    the capability_checks key set, and category/kind/status were still
    read straight from the (editable) result. Deleting
    required_semantic_dimensions and capability_checks from a result
    entirely reproduced the exact vacuous-truth pass that dimension was
    originally introduced to prevent -- every score stays null, nothing is
    required, probe_passes() returns True.

    Raises ValueError on any mismatch. Applies to both v1 and v2 reporting
    (called unconditionally in main() for every result) -- a scorer may
    change score/capability_check VALUES, but must never be able to change
    which judgments are required or which release-gate bucket (category,
    kind, status) a result counts toward.
    """
    result_id = result.get("id", probe.get("id"))
    for field in ("category", "kind", "status"):
        if result.get(field) != probe.get(field):
            raise ValueError(
                f"{result_id}: {field} does not match the frozen probe -- "
                f"stored {result.get(field)!r}, probe declares {probe.get(field)!r}"
            )
    if result.get("required_semantic_dimensions", []) != probe.get("required_semantic_dimensions", []):
        raise ValueError(
            f"{result_id}: required_semantic_dimensions does not match the frozen probe -- "
            f"stored {result.get('required_semantic_dimensions', [])!r}, "
            f"probe declares {probe.get('required_semantic_dimensions', [])!r}"
        )
    stored_check_keys = set(result.get("capability_checks", {}).keys())
    expected_check_keys = set(probe.get("primary_checks", []))
    if stored_check_keys != expected_check_keys:
        raise ValueError(
            f"{result_id}: capability_checks keys do not match the frozen probe's primary_checks -- "
            f"stored {sorted(stored_check_keys)}, probe declares {sorted(expected_check_keys)}"
        )


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

    # Finding 4 fix (prompt_contract_vnext_adapter_structural_focused_rereview.md):
    # raw_output is the source evidence every recomputation below depends
    # on -- result.get("raw_output", "") let a result with the key deleted
    # entirely be silently treated as an honest empty-string output, which
    # could spuriously "match" a genuinely-empty parse. Required, and must
    # actually be a string (not e.g. null or a number that happened to be
    # written by a bug elsewhere).
    raw_output = result.get("raw_output", _MISSING)
    if raw_output is _MISSING or not isinstance(raw_output, str):
        raise ValueError(f"{result_id}: raw_output must be a literal string, got {raw_output!r}")

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


def parse_report_args(argv: list[str]) -> tuple[list[str], str, bool]:
    """CLI parsing for report_benchmark.py. --contract=v1|v2 is explicit
    and required-to-be-correct, never inferred from probe shape (Finding 1:
    inferring from category/count-rule presence broke both directions at
    once -- see contract_adapters.py's V2_ACCEPTANCE_CATEGORY comment).
    --allow-partial opts into the old warn-only behavior for missing/extra
    result IDs, for diagnostic use only -- strict exact-match is the
    default (Finding 3)."""
    remaining, contract = parse_contract_flag(argv)
    if contract is None:
        contract = DEFAULT_CONTRACT
    positional = []
    allow_partial = False
    for arg in remaining:
        if arg == "--allow-partial":
            if allow_partial:
                raise ContractSelectionError("--allow-partial specified more than once")
            allow_partial = True
        elif arg.startswith("--"):
            raise ContractSelectionError(f"unrecognized flag: {arg}")
        else:
            positional.append(arg)
    if len(positional) != 2:
        raise ContractSelectionError(
            "expected exactly 2 positional arguments (benchmark.jsonl results.json), "
            f"got {len(positional)}: {positional}"
        )
    return positional, contract, allow_partial


def main() -> None:
    try:
        positional, contract_name, allow_partial = parse_report_args(sys.argv[1:])
    except ContractSelectionError as e:
        print(
            "Usage: python report_benchmark.py <benchmark.jsonl> <results.json> "
            "[--contract=v1|v2] [--allow-partial]",
            file=sys.stderr,
        )
        print(str(e), file=sys.stderr)
        sys.exit(1)

    benchmark_path = Path(positional[0])
    results_path = Path(positional[1])

    # Fail-closed, explicit contract selection -- see contract_adapters.py.
    adapter = select_contract_adapter(contract_name)
    print(f"Reporting under contract adapter: {adapter.name} ({adapter.version})")

    # Finding 3 fix: validate the RAW list for duplicates before collapsing
    # it into an {id: probe} dict -- {p["id"]: p for p in probe_list}
    # silently keeps only the last of any duplicate, which is exactly what
    # let two same-ID benchmark rows through undetected before.
    probe_list = load_jsonl(benchmark_path)
    reject_duplicate_ids(probe_list, "benchmark file")
    probes = {p["id"]: p for p in probe_list}

    # Finding 1 fix: a v2-acceptance-category case run/reported under
    # anything but --contract=v2 is a silent release-gate downgrade, not a
    # legitimate v1 report -- reject it outright rather than let a
    # forgotten flag quietly weaken the gate.
    v2_acceptance_ids = [p["id"] for p in probe_list if p.get("category") == V2_ACCEPTANCE_CATEGORY]
    if v2_acceptance_ids and adapter.name != "v2":
        raise ContractSelectionError(
            f"benchmark file contains {len(v2_acceptance_ids)} {V2_ACCEPTANCE_CATEGORY} "
            f"case(s) ({v2_acceptance_ids}) but --contract={adapter.name!r} was selected -- "
            "these require --contract=v2 explicitly; a default/inferred v1 report would "
            "silently skip their structural verification"
        )
    if adapter.parse is not None:
        preflight_validate_count_rules(probe_list, adapter)

    results = json.loads(results_path.read_text(encoding="utf-8"))
    if not isinstance(results, list):
        raise ContractSelectionError("results file must contain a JSON array of result objects")
    reject_duplicate_ids(results, "results file")
    results_by_id = {r["id"]: r for r in results}

    benchmark_ids = set(probes)
    result_ids = set(results_by_id)
    missing = benchmark_ids - result_ids
    extra = result_ids - benchmark_ids
    if missing or extra:
        if not allow_partial:
            raise ContractSelectionError(
                "benchmark/results ID sets do not match exactly -- pass --allow-partial for a "
                f"non-release diagnostic report. Missing from results: {sorted(missing)}. "
                f"Extra in results (not in benchmark): {sorted(extra)}."
            )
        if missing:
            print(f"WARNING: (--allow-partial) benchmark file has probes missing from results: {sorted(missing)}", file=sys.stderr)
        if extra:
            print(f"WARNING: (--allow-partial) results file has probes not in the benchmark file: {sorted(extra)}", file=sys.stderr)

    # Finding 3 fix: aggregate over the benchmark's own canonical order and
    # count, not the (editable, reorderable, previously-incomplete-without-
    # raising) results list. Pairing probe+result here also gives every
    # check below the frozen probe it needs for verify_rubric_binding/
    # verify_v2_structural_integrity, instead of trusting anything in `r`
    # about its own identity.
    scored_pairs = [(p, results_by_id[p["id"]]) for p in probe_list if p["id"] in results_by_id]

    def has_unscored_field(r: dict) -> bool:
        return any(v is None for v in r.get("scores", {}).values()) or any(
            v is None for v in r.get("capability_checks", {}).values()
        )

    unscored = [r["id"] for _, r in scored_pairs if has_unscored_field(r)]
    still_null = [
        r["id"]
        for _, r in scored_pairs
        if all(v is None for v in r.get("scores", {}).values())
        and all(v is None for v in r.get("capability_checks", {}).values())
    ]
    if still_null:
        print(
            f"WARNING: these probes look completely unscored (all null): {still_null}. "
            "Results will undercount passes until scored.",
            file=sys.stderr,
        )

    total = len(scored_pairs)
    passes: dict = {}
    for probe, r in scored_pairs:
        require_format_valid_is_boolean(r)
        verify_rubric_binding(probe, r)
        if adapter.name == "v2":
            passes[r["id"]] = v2_result_passes(probe, r)
        else:
            # Finding 1's "in v1 mode, unexpected v2 structural fields
            # should raise rather than be ignored" -- a result carrying any
            # v2-only structural field while being reported in v1 mode
            # means either the wrong --contract was passed or the result
            # was generated under v2 and is being silently downgraded.
            # Presence, not value: an earlier version only checked
            # `r.get("contract") is not None`, which a v2 result survives
            # by having just "contract" nulled to JSON null while every
            # other v2-only field stays present.
            present_v2_fields = [f for f in V2_ONLY_STRUCTURAL_FIELDS if f in r]
            if present_v2_fields:
                raise ContractSelectionError(
                    f"{r['id']}: result has v2-only structural field(s) present "
                    f"({present_v2_fields}) but this report is running in v1 mode -- pass "
                    "--contract=v2 if this result was generated under the v2 contract"
                )
            passes[r["id"]] = probe_passes(r)
    overall_passed = sum(passes.values())

    print(f"\n=== Benchmark report: {benchmark_path.name} vs {results_path.name} ===\n")
    print(f"Overall pass rate: {pct(overall_passed, total)}")
    print(f"Format-validity rate: {pct(sum(r['format_valid'] for _, r in scored_pairs), total)}\n")

    print("Pass rate by category:")
    by_category = Counter()
    passed_by_category = Counter()
    for probe, r in scored_pairs:
        by_category[probe["category"]] += 1
        if passes[r["id"]]:
            passed_by_category[probe["category"]] += 1
    for category in sorted(by_category):
        print(f"  {category}: {pct(passed_by_category[category], by_category[category])}")

    print("\nPass rate by probe kind:")
    by_kind = Counter()
    passed_by_kind = Counter()
    for probe, r in scored_pairs:
        by_kind[probe["kind"]] += 1
        if passes[r["id"]]:
            passed_by_kind[probe["kind"]] += 1
    for kind in sorted(by_kind):
        print(f"  {kind}: {pct(passed_by_kind[kind], by_kind[kind])}")

    print("\nFailure count by taxonomy label:")
    label_counts = Counter()
    for _, r in scored_pairs:
        for label in r.get("failure_labels", []):
            label_counts[label] += 1
    if label_counts:
        for label, count in label_counts.most_common():
            print(f"  {label}: {count}")
    else:
        print("  (none recorded)")

    regression_guards = [(p, r) for p, r in scored_pairs if p.get("status") == "regression_guard"]
    guards_passed = sum(passes[r["id"]] for _, r in regression_guards)
    print(f"\nRegression guards passed: {pct(guards_passed, len(regression_guards))}")
    if guards_passed < len(regression_guards):
        failed_guards = [r["id"] for _, r in regression_guards if not passes[r["id"]]]
        print(f"  REGRESSION: previously-passing guard(s) now failing: {failed_guards}")

    negative_examples = [(p, r) for p, r in scored_pairs if p.get("status") == "negative_example"]
    negatives_resolved = sum(passes[r["id"]] for _, r in negative_examples)
    print(f"\nNegative examples resolved: {pct(negatives_resolved, len(negative_examples))}")
    if negatives_resolved:
        resolved_ids = [r["id"] for _, r in negative_examples if passes[r["id"]]]
        print(f"  Known limitation(s) now fixed -- reclassify to regression_guard: {resolved_ids}")

    # acceptance_gate: a new capability being checked for the first time, with
    # no established prior-passing baseline -- unlike regression_guard, a
    # first-run failure here is not a "regression," so it gets its own count
    # instead of being folded into either existing category.
    acceptance_gates = [(p, r) for p, r in scored_pairs if p.get("status") == "acceptance_gate"]
    gates_passed = sum(passes[r["id"]] for _, r in acceptance_gates)
    print(f"\nAcceptance gates passed: {pct(gates_passed, len(acceptance_gates))}")
    if gates_passed < len(acceptance_gates):
        failed_gates = [r["id"] for _, r in acceptance_gates if not passes[r["id"]]]
        print(f"  Not yet passing: {failed_gates}")

    if unscored:
        print(f"\nNote: {len(unscored)} probe(s) have at least one null score/check: {unscored}")


if __name__ == "__main__":
    main()
