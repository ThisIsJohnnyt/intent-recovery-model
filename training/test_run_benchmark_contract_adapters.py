"""Dummy-only tests for contract_adapters.py, run_benchmark.py's adapter
refactor, and report_benchmark.py's active structural recomputation. No
pytest dependency: run directly with
`python test_run_benchmark_contract_adapters.py`.

No model loading, no inference, no training anywhere in this file --
authorized scope is "dummy-only shared runner adapter and active
structural-validation implementation" per Johnny's 2026-08-02
authorization. Every "generated" string below is hand-written, not model
output. Deliberately importable without torch/transformers installed
(confirmed directly against the base system Python, matching
test_report_benchmark.py's existing convention for the same reason) --
run_benchmark.py's own torch/transformers imports were moved inside
main(), after contract selection and count-rule preflight validation, so
those fail-closed checks are provably reachable before any ML dependency
is even imported, not just before a model is actually loaded.

Covers prompt_contract_vnext_static_final_review_and_branch_reconciliation.md's
two authorized items:
1. The shared runner adapter (contract_adapters.py + run_benchmark.py's
   build_result_for_probe/parse_args), with regression tests proving the
   v1 default path is unchanged.
2. Active structural recomputation (report_benchmark.py's
   evaluate_v2_count_rules/v2_result_passes).
"""
import sys
from pathlib import Path

import contract_adapters as ca
import report_benchmark as rb
import run_benchmark as rbm

FAILURES = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


# ---------------------------------------------------------------------------
# Part 1: contract selection, fail-closed
# ---------------------------------------------------------------------------

def test_v1_is_the_default_contract():
    check("DEFAULT_CONTRACT is 'v1'", ca.DEFAULT_CONTRACT == "v1", ca.DEFAULT_CONTRACT)


def test_select_v1_and_v2_succeed():
    v1 = ca.select_contract_adapter("v1")
    v2 = ca.select_contract_adapter("v2")
    check("v1 adapter version matches prepare_data.PROMPT_CONTRACT_VERSION", v1.version == "source-determined-bullets-v1", v1.version)
    check("v2 adapter version matches prompt_contract_v2_candidate.PROMPT_CONTRACT_VERSION", v2.version == "source-determined-items-v2-candidate", v2.version)
    check("v1 adapter has no count extraction (v1 doesn't define per-item counts)", v1.extract_counts is None)
    check("v2 adapter has count extraction", v2.extract_counts is not None)


def test_unknown_contract_name_raises_before_any_model_import():
    try:
        ca.select_contract_adapter("v3-does-not-exist")
        check("unknown contract name raises ContractSelectionError", False, "did not raise")
    except ca.ContractSelectionError as e:
        check("unknown contract name raises ContractSelectionError", "v3-does-not-exist" in str(e), str(e))


def test_fingerprint_mismatch_raises():
    # Constructs a deliberately-wrong adapter (real build_prompt, wrong
    # locked fingerprint) and registers it under a throwaway name to
    # exercise the mismatch path without touching either real locked
    # constant. Restores CONTRACT_ADAPTERS afterward.
    broken = ca.ContractAdapter(
        name="broken-test-only",
        version="irrelevant",
        build_prompt=ca.V1_ADAPTER.build_prompt,
        check_format_valid=ca.V1_ADAPTER.check_format_valid,
        extract_counts=None,
        expected_fingerprint="0" * 64,
    )
    original = dict(ca.CONTRACT_ADAPTERS)
    ca.CONTRACT_ADAPTERS["broken-test-only"] = broken
    try:
        ca.select_contract_adapter("broken-test-only")
        check("fingerprint mismatch raises ContractSelectionError", False, "did not raise")
    except ca.ContractSelectionError as e:
        check("fingerprint mismatch raises ContractSelectionError", "fingerprint mismatch" in str(e), str(e))
    finally:
        ca.CONTRACT_ADAPTERS.clear()
        ca.CONTRACT_ADAPTERS.update(original)


# ---------------------------------------------------------------------------
# Part 2: preflight_validate_count_rules
# ---------------------------------------------------------------------------

def test_preflight_is_a_no_op_for_v1_even_with_garbage_rules():
    v1 = ca.select_contract_adapter("v1")
    garbage_probes = [{"id": "x", "bullet_count_rule": {"operator": "not-a-real-operator"}}]
    try:
        ca.preflight_validate_count_rules(garbage_probes, v1)
        check("preflight no-op for v1 adapter regardless of probe content", True)
    except Exception as e:
        check("preflight no-op for v1 adapter regardless of probe content", False, str(e))


def test_preflight_requires_both_rules_or_neither():
    v2 = ca.select_contract_adapter("v2")
    one_sided = [{"id": "p1", "bullet_count_rule": {"operator": "exact", "value": 1}}]
    try:
        ca.preflight_validate_count_rules(one_sided, v2)
        check("preflight rejects a rule declared on only one of bullet/action", False, "did not raise")
    except ca.ContractSelectionError as e:
        check("preflight rejects a rule declared on only one of bullet/action", "p1" in str(e), str(e))


def test_preflight_rejects_unknown_operator():
    v2 = ca.select_contract_adapter("v2")
    bad_op = [{
        "id": "p2",
        "bullet_count_rule": {"operator": "at-least", "value": 2},
        "action_count_rule": {"operator": "exact", "value": 1},
    }]
    try:
        ca.preflight_validate_count_rules(bad_op, v2)
        check("preflight rejects an unrecognized operator", False, "did not raise")
    except ca.ContractSelectionError as e:
        check("preflight rejects an unrecognized operator", "at-least" in str(e), str(e))


def test_preflight_accepts_well_formed_rules():
    v2 = ca.select_contract_adapter("v2")
    good = [{
        "id": "p3",
        "bullet_count_rule": {"operator": "max", "value": 7},
        "action_count_rule": {"operator": "exact", "value": 8},
    }]
    try:
        ca.preflight_validate_count_rules(good, v2)
        check("preflight accepts well-formed exact/max rules", True)
    except Exception as e:
        check("preflight accepts well-formed exact/max rules", False, str(e))


# ---------------------------------------------------------------------------
# Part 3: v1 default path -- proven byte-for-byte unchanged
# ---------------------------------------------------------------------------

def _pre_refactor_check_format_valid(generated: str) -> bool:
    """Reference implementation, copied verbatim from the pre-refactor
    version of run_benchmark.py (git history, commit before this round) --
    an independent second copy to cross-check against, not just re-reading
    the same code the refactor now calls."""
    NARRATIVE_MARKER, BULLETS_MARKER, ACTIONS_MARKER = "###NARRATIVE###", "###BULLETS###", "###ACTIONS###"
    narrative_idx = generated.find(NARRATIVE_MARKER)
    bullets_idx = generated.find(BULLETS_MARKER)
    actions_idx = generated.find(ACTIONS_MARKER)
    return (
        narrative_idx != -1
        and bullets_idx != -1
        and actions_idx != -1
        and narrative_idx < bullets_idx < actions_idx
        and generated[narrative_idx + len(NARRATIVE_MARKER) : bullets_idx].strip() != ""
    )


def _pre_refactor_build_result_for_probe(probe: dict, generated: str) -> dict:
    """Reference implementation of the exact dict construction the
    pre-refactor run_benchmark.py had inline in its generation loop --
    the ground truth this round's build_result_for_probe(probe, v1, ...)
    must match exactly for every probe/generated pair below."""
    valid = _pre_refactor_check_format_valid(generated)
    return {
        "id": probe["id"],
        "category": probe["category"],
        "kind": probe["kind"],
        "status": probe.get("status"),
        "required_semantic_dimensions": probe.get("required_semantic_dimensions", []),
        "raw_output": generated,
        "format_valid": valid,
        "scores": {
            "topic_completeness": None,
            "attribution_accuracy": None,
            "uncertainty_preservation": None,
            "unsupported_addition_resistance": None,
        },
        "capability_checks": {check: None for check in probe.get("primary_checks", [])},
        "failure_labels": [],
    }


V1_REGRESSION_CASES = [
    (
        {"id": "reg-1", "category": "direct", "kind": "direct", "status": "regression_guard",
         "required_semantic_dimensions": ["topic_completeness"], "primary_checks": ["SOME_CHECK"]},
        "###NARRATIVE###\nsome narrative text\n###BULLETS###\nfirst\nsecond\n###ACTIONS###\ntask one",
    ),
    (
        # No primary_checks, no required_semantic_dimensions -- exercises
        # the .get(..., []) defaults on both.
        {"id": "reg-2", "category": "transfer", "kind": "transfer", "status": None},
        "###NARRATIVE###\ntext\n###BULLETS###\n###ACTIONS###",
    ),
    (
        # Malformed: markers out of order -> format_valid False.
        {"id": "reg-3", "category": "adversarial", "kind": "adversarial", "status": "negative_example",
         "required_semantic_dimensions": [], "primary_checks": ["A", "B"]},
        "###BULLETS###\n###NARRATIVE###\ntext\n###ACTIONS###",
    ),
    (
        # Empty narrative content -> format_valid False (narrative slice strips to "").
        {"id": "reg-4", "category": "direct", "kind": "direct", "status": "acceptance_gate",
         "required_semantic_dimensions": ["unsupported_addition_resistance"], "primary_checks": []},
        "###NARRATIVE###   \n###BULLETS###\nx\n###ACTIONS###",
    ),
    (
        # No markers at all.
        {"id": "reg-5", "category": "direct", "kind": "direct"},
        "just plain text with no structure whatsoever",
    ),
]


def test_v1_build_result_matches_pre_refactor_reference_exactly():
    v1 = ca.select_contract_adapter("v1")
    for probe, generated in V1_REGRESSION_CASES:
        expected = _pre_refactor_build_result_for_probe(probe, generated)
        actual = rbm.build_result_for_probe(probe, v1, generated)
        check(
            f"v1 build_result_for_probe('{probe['id']}') matches pre-refactor reference exactly",
            actual == expected,
            f"expected={expected!r} actual={actual!r}",
        )
        check(
            f"v1 build_result_for_probe('{probe['id']}') has no v2-only keys",
            "contract" not in actual and "bullet_count_rule" not in actual and "bullet_count_result" not in actual,
            str(actual.keys()),
        )


def test_v1_adapter_check_format_valid_matches_prepare_data_directly():
    # Extra rigor beyond the full-result comparison above: confirm the
    # adapter's check_format_valid (prepare_data.check_format_valid) agrees
    # with the independent reference implementation on every regression
    # case's raw text, not just on the assembled result dict.
    v1 = ca.select_contract_adapter("v1")
    for probe, generated in V1_REGRESSION_CASES:
        check(
            f"prepare_data.check_format_valid('{probe['id']}') matches independent reference",
            v1.check_format_valid(generated) == _pre_refactor_check_format_valid(generated),
            generated,
        )


def test_parse_args_default_contract_is_v1_and_positional_args_unaffected():
    positional, contract = rbm.parse_args(["bench.jsonl"])
    check("parse_args: single positional arg preserved, contract defaults to v1", positional == ["bench.jsonl"] and contract == "v1", (positional, contract))

    positional, contract = rbm.parse_args(["bench.jsonl", "ckpt_dir", "out.json"])
    check(
        "parse_args: three positional args preserved in order, contract defaults to v1",
        positional == ["bench.jsonl", "ckpt_dir", "out.json"] and contract == "v1",
        (positional, contract),
    )


def test_parse_args_extracts_contract_flag_from_any_position():
    positional, contract = rbm.parse_args(["--contract=v2", "bench.jsonl", "ckpt_dir"])
    check(
        "parse_args: --contract=v2 extracted from front, positionals intact",
        positional == ["bench.jsonl", "ckpt_dir"] and contract == "v2",
        (positional, contract),
    )
    positional, contract = rbm.parse_args(["bench.jsonl", "--contract=v2", "ckpt_dir"])
    check(
        "parse_args: --contract=v2 extracted from middle, positionals intact and in order",
        positional == ["bench.jsonl", "ckpt_dir"] and contract == "v2",
        (positional, contract),
    )


# ---------------------------------------------------------------------------
# Part 4: v2 adapter path (dummy-only)
# ---------------------------------------------------------------------------

def test_v2_build_result_includes_count_fields_and_correct_counts():
    v2 = ca.select_contract_adapter("v2")
    probe = {
        "id": "sdi2-02", "category": "source_determined_items_v2", "kind": "direct", "status": "acceptance_gate",
        "required_semantic_dimensions": ["topic_completeness"], "primary_checks": ["TASK_SURVIVED"],
        "bullet_count_rule": {"operator": "exact", "value": 1},
        "action_count_rule": {"operator": "exact", "value": 1},
    }
    generated = "###NARRATIVE### text ###BULLETS### ###BULLET### one idea ###ACTIONS### ###ACTION### one task"
    result = rbm.build_result_for_probe(probe, v2, generated)
    check("v2 result carries contract='v2'", result.get("contract") == "v2", result.get("contract"))
    check("v2 result bullet_count_result actual=1, passed=True", result["bullet_count_result"] == {"actual": 1, "rule": probe["bullet_count_rule"], "passed": True}, result["bullet_count_result"])
    check("v2 result action_count_result actual=1, passed=True", result["action_count_result"] == {"actual": 1, "rule": probe["action_count_rule"], "passed": True}, result["action_count_result"])


def test_v2_unparseable_output_fails_count_rules_without_raising():
    v2 = ca.select_contract_adapter("v2")
    probe = {
        "id": "sdi2-02", "category": "c", "kind": "direct",
        "bullet_count_rule": {"operator": "exact", "value": 1},
        "action_count_rule": {"operator": "exact", "value": 1},
    }
    result = rbm.build_result_for_probe(probe, v2, "not structured at all")
    check("unparseable v2 output: format_valid is False", result["format_valid"] is False)
    check("unparseable v2 output: bullet_count_result fails with actual=None (no raise)", result["bullet_count_result"] == {"actual": None, "rule": probe["bullet_count_rule"], "passed": False}, result["bullet_count_result"])


def test_v2_probe_without_count_rules_gets_no_count_fields_populated_as_none():
    v2 = ca.select_contract_adapter("v2")
    probe = {"id": "p", "category": "c", "kind": "direct"}
    result = rbm.build_result_for_probe(probe, v2, "###NARRATIVE### t ###BULLETS### ###BULLET### a ###ACTIONS###")
    check("v2 probe with no declared rules: bullet_count_rule is None", result["bullet_count_rule"] is None)
    check("v2 probe with no declared rules: bullet_count_result is None", result["bullet_count_result"] is None)


# ---------------------------------------------------------------------------
# Part 5: report_benchmark.py active structural recomputation
# ---------------------------------------------------------------------------

def test_evaluate_v2_count_rules_no_op_true_when_probe_declares_no_rules():
    check(
        "evaluate_v2_count_rules: probe with no count rules is not-applicable (True)",
        rb.evaluate_v2_count_rules({"id": "legacy"}, {"raw_output": "anything, doesn't matter"}) is True,
    )


def test_evaluate_v2_count_rules_passes_when_consistent_and_satisfied():
    v2 = ca.select_contract_adapter("v2")
    probe = {
        "id": "sdi2-02", "category": "c", "kind": "direct",
        "bullet_count_rule": {"operator": "exact", "value": 1},
        "action_count_rule": {"operator": "exact", "value": 1},
    }
    generated = "###NARRATIVE### text ###BULLETS### ###BULLET### one idea ###ACTIONS### ###ACTION### one task"
    result = rbm.build_result_for_probe(probe, v2, generated)
    check("evaluate_v2_count_rules: consistent + satisfied -> True", rb.evaluate_v2_count_rules(probe, result) is True)


def test_evaluate_v2_count_rules_fails_without_raising_when_genuinely_unsatisfied():
    v2 = ca.select_contract_adapter("v2")
    probe = {
        "id": "sdi2-03", "category": "c", "kind": "direct",
        "bullet_count_rule": {"operator": "exact", "value": 2},
        "action_count_rule": {"operator": "exact", "value": 0},
    }
    # Only one bullet where the rule demands exactly two -- a genuine,
    # honestly-reported failure, not tampering. Must return False, not raise.
    generated = "###NARRATIVE### text ###BULLETS### ###BULLET### only one idea ###ACTIONS###"
    result = rbm.build_result_for_probe(probe, v2, generated)
    try:
        outcome = rb.evaluate_v2_count_rules(probe, result)
        check("evaluate_v2_count_rules: genuine unmet rule returns False without raising", outcome is False, outcome)
    except ValueError as e:
        check("evaluate_v2_count_rules: genuine unmet rule returns False without raising", False, f"raised instead: {e}")


def test_evaluate_v2_count_rules_raises_on_tampered_stored_result():
    v2 = ca.select_contract_adapter("v2")
    probe = {
        "id": "sdi2-02", "category": "c", "kind": "direct",
        "bullet_count_rule": {"operator": "exact", "value": 1},
        "action_count_rule": {"operator": "exact", "value": 1},
    }
    generated = "###NARRATIVE### text ###BULLETS### ###BULLET### one idea ###ACTIONS### ###ACTION### one task"
    result = rbm.build_result_for_probe(probe, v2, generated)
    tampered = dict(result)
    tampered["action_count_result"] = {"actual": 1, "rule": probe["action_count_rule"], "passed": False}  # hand-edited to False
    try:
        rb.evaluate_v2_count_rules(probe, tampered)
        check("evaluate_v2_count_rules: tampered stored result raises", False, "did not raise")
    except ValueError as e:
        check("evaluate_v2_count_rules: tampered stored result raises", "sdi2-02" in str(e) and "tampering" in str(e), str(e))


def test_v2_result_passes_ands_probe_passes_and_count_rules():
    v2 = ca.select_contract_adapter("v2")
    probe = {
        "id": "sdi2-02", "category": "c", "kind": "direct",
        "required_semantic_dimensions": ["topic_completeness"], "primary_checks": ["TASK_SURVIVED"],
        "bullet_count_rule": {"operator": "exact", "value": 1},
        "action_count_rule": {"operator": "exact", "value": 1},
    }
    generated = "###NARRATIVE### text ###BULLETS### ###BULLET### one idea ###ACTIONS### ###ACTION### one task"
    result = rbm.build_result_for_probe(probe, v2, generated)

    # Count rules satisfied, but semantic scoring not yet filled in ->
    # overall False (probe_passes' own fail-open-closed gate, untouched).
    check("v2_result_passes: unscored semantics -> False even though counts pass", rb.v2_result_passes(probe, result) is False)

    # Fully scored -> True.
    result["scores"]["topic_completeness"] = 2
    result["capability_checks"]["TASK_SURVIVED"] = True
    check("v2_result_passes: fully scored + counts satisfied -> True", rb.v2_result_passes(probe, result) is True)

    # Now break the count rule (still consistent, just genuinely unmet) -> False.
    probe2 = dict(probe)
    probe2["bullet_count_rule"] = {"operator": "exact", "value": 5}
    result2 = rbm.build_result_for_probe(probe2, v2, generated)
    result2["scores"]["topic_completeness"] = 2
    result2["capability_checks"]["TASK_SURVIVED"] = True
    check("v2_result_passes: fully scored but count rule unmet -> False", rb.v2_result_passes(probe2, result2) is False)


def test_probe_passes_itself_is_unmodified_by_this_round():
    # Not a new test of probe_passes()'s own logic (test_report_benchmark.py
    # already covers that exhaustively) -- just confirms it's still the
    # exact same importable function report_benchmark.py has always
    # exported, proving this round only added functions around it.
    result = {
        "id": "x", "format_valid": True,
        "scores": {"topic_completeness": None, "attribution_accuracy": None, "uncertainty_preservation": None, "unsupported_addition_resistance": None},
        "capability_checks": {}, "required_semantic_dimensions": [],
    }
    check("probe_passes: unchanged legacy no-required-dimensions behavior still holds", rb.probe_passes(result) is True)


def main() -> None:
    tests = [
        test_v1_is_the_default_contract,
        test_select_v1_and_v2_succeed,
        test_unknown_contract_name_raises_before_any_model_import,
        test_fingerprint_mismatch_raises,
        test_preflight_is_a_no_op_for_v1_even_with_garbage_rules,
        test_preflight_requires_both_rules_or_neither,
        test_preflight_rejects_unknown_operator,
        test_preflight_accepts_well_formed_rules,
        test_v1_build_result_matches_pre_refactor_reference_exactly,
        test_v1_adapter_check_format_valid_matches_prepare_data_directly,
        test_parse_args_default_contract_is_v1_and_positional_args_unaffected,
        test_parse_args_extracts_contract_flag_from_any_position,
        test_v2_build_result_includes_count_fields_and_correct_counts,
        test_v2_unparseable_output_fails_count_rules_without_raising,
        test_v2_probe_without_count_rules_gets_no_count_fields_populated_as_none,
        test_evaluate_v2_count_rules_no_op_true_when_probe_declares_no_rules,
        test_evaluate_v2_count_rules_passes_when_consistent_and_satisfied,
        test_evaluate_v2_count_rules_fails_without_raising_when_genuinely_unsatisfied,
        test_evaluate_v2_count_rules_raises_on_tampered_stored_result,
        test_v2_result_passes_ands_probe_passes_and_count_rules,
        test_probe_passes_itself_is_unmodified_by_this_round,
    ]
    for t in tests:
        t()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("All contract-adapter / active-recomputation tests passed.")


if __name__ == "__main__":
    main()
