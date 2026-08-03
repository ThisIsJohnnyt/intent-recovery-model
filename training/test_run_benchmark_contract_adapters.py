"""Dummy-only tests for contract_adapters.py, run_benchmark.py's adapter
refactor, and report_benchmark.py's active structural recomputation. No
pytest dependency: run directly with
`python test_run_benchmark_contract_adapters.py`.

No model loading, inference, or training anywhere in this file --
authorized scope is "dummy-only shared runner adapter and active
structural-validation implementation" per Johnny's 2026-08-02
authorization. Every "generated" string below is hand-written, not model
output.

Covers the 12 minimum re-review acceptance tests from
prompt_contract_vnext_adapter_structural_implementation_review.md's six
findings, all independently reproduced against the pre-fix code before
being fixed (see that review and the commit message for detail):

1/2. The actual report_benchmark.py CLI path (not just the underlying
     functions) reports failure for an honestly-unmet count rule, and
     raises on tampered structural data.
3. Structural verification runs even when semantics are unscored/failing
   (no short-circuit).
4. A copied top-level count-rule mismatch against the frozen probe raises.
5. Contract/version/fingerprint/parser-version mismatch or omission
   raises.
6. Parse-validity/parsed-structure/count mismatches raise.
7. Missing one or both count rules on a source_determined_items_v2 case
   raises at both runner preflight and report time.
8. Duplicate IDs and malformed rule shapes/values fail before model
   import and at report time.
9. The default v1 import path does not import v2 candidate/parser modules
   (fresh-subprocess test -- a same-process check would be tainted by any
   earlier test in this file that already selected v2).
10. The protected v1 result scaffold remains unchanged for representative
    cases (the narrower, accurate claim -- not "all runner behavior is
    byte-for-byte identical," which the review correctly pointed out is
    too strong given stdout and the import graph both changed).
11. The protected 16-probe benchmark can still run under v2 without being
    forced to declare acceptance-only count rules.
12. Malformed/duplicate CLI contract selection fails with a clear domain
    error.

Also covers the 10 minimum focused re-review gates from
prompt_contract_vnext_adapter_structural_focused_rereview.md, all
independently reproduced against the pre-fix code before being fixed:

1. The historical five-case v1 scored artifact reports successfully under
   default v1 (using the real committed files, not a synthetic stand-in --
   this is exactly the file/scored-result pair the review's reproduction
   used).
2. Every protected 16-probe v2 result receives structural verification
   despite having no count rules, because report_benchmark.py now takes
   --contract explicitly rather than inferring per-probe from shape.
3. A v2 acceptance benchmark cannot be reported under v1/default downgrade
   -- raises rather than silently skipping structural verification.
4. Tampering or removing required_semantic_dimensions/capability_checks
   keys raises (verify_rubric_binding).
5. category/kind/status edits raise (also verify_rubric_binding).
6. Duplicate benchmark IDs raise before the {id: probe} map is built.
7. Duplicate, missing, or extra result IDs raise before scoring (strict
   by default; --allow-partial opts into the old warn-only behavior).
8. Missing or non-string raw_output raises.
9. Default v1 imports still do not load v2 modules (re-verified against
   the new report_benchmark.py flow, including the v2-acceptance-under-v1
   rejection path itself never needing to import v2 modules).
10. Existing v1 scaffold and protected strict scoring remain unchanged for
    valid artifacts (re-verified end-to-end against the real historical
    5-case file: still exactly 1/5, matching the known-good result from
    before this whole adapter/structural-validation project started).
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import contract_adapters as ca
import report_benchmark as rb
import run_benchmark as rbm

FAILURES = []
TRAINING_DIR = Path(__file__).parent


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


def _v2_probe(id_: str, bullet_rule=None, action_rule=None, category="source_determined_items_v2", **extra) -> dict:
    probe = {
        "id": id_, "category": category, "kind": "direct", "status": "acceptance_gate",
        "required_semantic_dimensions": [], "primary_checks": [],
    }
    if bullet_rule is not None:
        probe["bullet_count_rule"] = bullet_rule
    if action_rule is not None:
        probe["action_count_rule"] = action_rule
    probe.update(extra)
    return probe


def _fully_score(result: dict) -> dict:
    for dim in result["required_semantic_dimensions"]:
        result["scores"][dim] = 2
    for check_name in result["capability_checks"]:
        result["capability_checks"][check_name] = True
    return result


ONE_BULLET_ONE_ACTION = "###NARRATIVE### text ###BULLETS### ###BULLET### one idea ###ACTIONS### ###ACTION### one task"
TWO_BULLETS_ZERO_ACTIONS = "###NARRATIVE### text ###BULLETS### ###BULLET### one ###BULLET### two ###ACTIONS###"


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
    check("v1 adapter has no structural parser (v1 doesn't define per-item counts)", v1.parse is None)
    check("v2 adapter has a structural parser", v2.parse is not None)
    check("v2 adapter carries a parser_version", v2.parser_version is not None, v2.parser_version)


def test_unknown_contract_name_raises_before_any_model_import():
    try:
        ca.select_contract_adapter("v3-does-not-exist")
        check("unknown contract name raises ContractSelectionError", False, "did not raise")
    except ca.ContractSelectionError as e:
        check("unknown contract name raises ContractSelectionError", "v3-does-not-exist" in str(e), str(e))


def test_fingerprint_mismatch_raises():
    broken = ca.ContractAdapter(
        name="broken-test-only", version="irrelevant",
        build_prompt=ca.select_contract_adapter("v1").build_prompt,
        check_format_valid=ca.select_contract_adapter("v1").check_format_valid,
        parse=None, parser_version=None, expected_fingerprint="0" * 64,
    )
    original = dict(ca._ADAPTER_BUILDERS)
    ca._ADAPTER_BUILDERS["broken-test-only"] = lambda: broken
    try:
        ca.select_contract_adapter("broken-test-only")
        check("fingerprint mismatch raises ContractSelectionError", False, "did not raise")
    except ca.ContractSelectionError as e:
        check("fingerprint mismatch raises ContractSelectionError", "fingerprint mismatch" in str(e), str(e))
    finally:
        ca._ADAPTER_BUILDERS.clear()
        ca._ADAPTER_BUILDERS.update(original)


# ---------------------------------------------------------------------------
# Part 2 (acceptance test 9): fresh-process import isolation
# ---------------------------------------------------------------------------

def test_fresh_process_v1_selection_never_imports_v2_modules():
    script = (
        "import sys, run_benchmark, contract_adapters as ca\n"
        "ca.select_contract_adapter('v1')\n"
        "present = [m for m in sys.modules if 'prompt_contract_v2' in m]\n"
        "print('PRESENT:' + repr(present))\n"
    )
    out = subprocess.run([sys.executable, "-c", script], cwd=str(TRAINING_DIR), capture_output=True, text=True)
    check("fresh process: importing run_benchmark + selecting v1 does not exit nonzero", out.returncode == 0, out.stderr)
    check(
        "fresh process: v2 candidate/parser modules absent from sys.modules after only selecting v1",
        "PRESENT:[]" in out.stdout,
        out.stdout + out.stderr,
    )


def test_fresh_process_v2_selection_does_import_v2_modules():
    script = (
        "import sys, contract_adapters as ca\n"
        "ca.select_contract_adapter('v2')\n"
        "present = sorted(m for m in sys.modules if 'prompt_contract_v2' in m)\n"
        "print('PRESENT:' + repr(present))\n"
    )
    out = subprocess.run([sys.executable, "-c", script], cwd=str(TRAINING_DIR), capture_output=True, text=True)
    check(
        "fresh process: selecting v2 does import both v2 candidate/parser modules",
        "prompt_contract_v2_candidate" in out.stdout and "prompt_contract_v2_parser" in out.stdout,
        out.stdout + out.stderr,
    )


# ---------------------------------------------------------------------------
# Part 3 (acceptance tests 7, 8, 11): preflight validation
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
    one_sided = [_v2_probe("p1", bullet_rule={"operator": "exact", "value": 1}, category="direct")]
    try:
        ca.preflight_validate_count_rules(one_sided, v2)
        check("preflight rejects a rule declared on only one of bullet/action", False, "did not raise")
    except ca.ContractSelectionError as e:
        check("preflight rejects a rule declared on only one of bullet/action", "p1" in str(e), str(e))


def test_preflight_rejects_unknown_operator():
    v2 = ca.select_contract_adapter("v2")
    bad_op = [_v2_probe("p2", bullet_rule={"operator": "at-least", "value": 2}, action_rule={"operator": "exact", "value": 1}, category="direct")]
    try:
        ca.preflight_validate_count_rules(bad_op, v2)
        check("preflight rejects an unrecognized operator", False, "did not raise")
    except ca.ContractSelectionError as e:
        check("preflight rejects an unrecognized operator", "at-least" in str(e), str(e))


def test_preflight_accepts_well_formed_rules():
    v2 = ca.select_contract_adapter("v2")
    good = [_v2_probe("p3", bullet_rule={"operator": "max", "value": 7}, action_rule={"operator": "exact", "value": 8})]
    try:
        ca.preflight_validate_count_rules(good, v2)
        check("preflight accepts well-formed exact/max rules", True)
    except Exception as e:
        check("preflight accepts well-formed exact/max rules", False, str(e))


def test_preflight_rejects_duplicate_probe_ids():
    v2 = ca.select_contract_adapter("v2")
    dup_rule = {"operator": "exact", "value": 1}
    dup = [_v2_probe("dup", bullet_rule=dup_rule, action_rule=dup_rule) for _ in range(2)]
    try:
        ca.preflight_validate_count_rules(dup, v2)
        check("preflight rejects duplicate probe ids", False, "did not raise")
    except ca.ContractSelectionError as e:
        check("preflight rejects duplicate probe ids", "dup" in str(e), str(e))


def test_preflight_rejects_malformed_rule_values():
    v2 = ca.select_contract_adapter("v2")
    action_rule = {"operator": "exact", "value": 1}
    malformed_cases = [
        ("string value", {"operator": "exact", "value": "1"}),
        ("negative max", {"operator": "max", "value": -1}),
        ("unknown key", {"operator": "exact", "value": 1, "extra": "huh"}),
        ("boolean value", {"operator": "exact", "value": True}),
    ]
    for name, bad_rule in malformed_cases:
        probes = [_v2_probe("p", bullet_rule=bad_rule, action_rule=action_rule, category="direct")]
        try:
            ca.preflight_validate_count_rules(probes, v2)
            check(f"preflight rejects malformed rule value ({name})", False, "did not raise")
        except ca.ContractSelectionError as e:
            check(f"preflight rejects malformed rule value ({name})", True, str(e))


def test_preflight_requires_both_rules_for_v2_acceptance_category_even_if_both_absent():
    v2 = ca.select_contract_adapter("v2")
    missing = [{"id": "sdi2-oops", "category": "source_determined_items_v2"}]
    try:
        ca.preflight_validate_count_rules(missing, v2)
        check("preflight rejects a source_determined_items_v2 probe missing both rules", False, "did not raise")
    except ca.ContractSelectionError as e:
        check("preflight rejects a source_determined_items_v2 probe missing both rules", "sdi2-oops" in str(e), str(e))


def test_preflight_accepts_protected_16_probes_under_v2_without_requiring_rules():
    v2 = ca.select_contract_adapter("v2")
    probes = rbm.load_probes(TRAINING_DIR.parent / "datasets" / "benchmark" / "gold_v1.2.1_probes.jsonl")
    check("gold_v1.2.1_probes.jsonl loads as 16 probes", len(probes) == 16, str(len(probes)))
    try:
        ca.preflight_validate_count_rules(probes, v2)
        check("preflight accepts the protected 16 probes under v2 with no count rules declared", True)
    except Exception as e:
        check("preflight accepts the protected 16 probes under v2 with no count rules declared", False, str(e))


def test_report_time_preflight_also_rejects_missing_rules_and_duplicates():
    # Finding 5/7's "repeat the same validations in the reporter" -- these
    # go through report_benchmark.py's own re-validation, not
    # contract_adapters directly, proving main()'s report-time path (not
    # just the runner's) is protected too.
    tmpdir = Path(tempfile.mkdtemp())
    bench_path = tmpdir / "bench.jsonl"
    results_path = tmpdir / "results.json"
    bench_path.write_text(json.dumps({"id": "sdi2-oops", "category": "source_determined_items_v2"}) + "\n", encoding="utf-8")
    results_path.write_text("[]", encoding="utf-8")
    out = subprocess.run(
        [sys.executable, "report_benchmark.py", str(bench_path), str(results_path), "--contract=v2"],
        cwd=str(TRAINING_DIR), capture_output=True, text=True,
    )
    check(
        "report_benchmark.py CLI exits nonzero on a v2-acceptance probe missing both count rules",
        out.returncode != 0,
        f"returncode={out.returncode} stdout={out.stdout} stderr={out.stderr}",
    )
    check("... with a traceback mentioning the offending probe id", "sdi2-oops" in out.stderr, out.stderr)


# ---------------------------------------------------------------------------
# Part 4 (acceptance test 10, 12): v1 default path and CLI validation
# ---------------------------------------------------------------------------

def _pre_refactor_check_format_valid(generated: str) -> bool:
    """Independent reference implementation, copied verbatim from the
    pre-adapter version of run_benchmark.py -- a second copy to cross-
    check against, not just re-reading the code the refactor now calls."""
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
    valid = _pre_refactor_check_format_valid(generated)
    return {
        "id": probe["id"], "category": probe["category"], "kind": probe["kind"], "status": probe.get("status"),
        "required_semantic_dimensions": probe.get("required_semantic_dimensions", []),
        "raw_output": generated, "format_valid": valid,
        "scores": {"topic_completeness": None, "attribution_accuracy": None, "uncertainty_preservation": None, "unsupported_addition_resistance": None},
        "capability_checks": {c: None for c in probe.get("primary_checks", [])},
        "failure_labels": [],
    }


V1_REGRESSION_CASES = [
    ({"id": "reg-1", "category": "direct", "kind": "direct", "status": "regression_guard",
      "required_semantic_dimensions": ["topic_completeness"], "primary_checks": ["SOME_CHECK"]},
     "###NARRATIVE###\nsome narrative text\n###BULLETS###\nfirst\nsecond\n###ACTIONS###\ntask one"),
    ({"id": "reg-2", "category": "transfer", "kind": "transfer", "status": None},
     "###NARRATIVE###\ntext\n###BULLETS###\n###ACTIONS###"),
    ({"id": "reg-3", "category": "adversarial", "kind": "adversarial", "status": "negative_example",
      "required_semantic_dimensions": [], "primary_checks": ["A", "B"]},
     "###BULLETS###\n###NARRATIVE###\ntext\n###ACTIONS###"),
    ({"id": "reg-4", "category": "direct", "kind": "direct", "status": "acceptance_gate",
      "required_semantic_dimensions": ["unsupported_addition_resistance"], "primary_checks": []},
     "###NARRATIVE###   \n###BULLETS###\nx\n###ACTIONS###"),
    ({"id": "reg-5", "category": "direct", "kind": "direct"}, "just plain text with no structure whatsoever"),
]


def test_v1_build_result_matches_pre_refactor_reference_exactly():
    # Narrower, accurate claim per the review's correction: this proves the
    # per-probe v1 result scaffold is unchanged for these representative
    # cases -- not that every aspect of runner behavior (stdout, import
    # graph) is byte-for-byte identical, which it isn't and doesn't need
    # to be.
    v1 = ca.select_contract_adapter("v1")
    for probe, generated in V1_REGRESSION_CASES:
        expected = _pre_refactor_build_result_for_probe(probe, generated)
        actual = rbm.build_result_for_probe(probe, v1, generated)
        check(f"v1 build_result_for_probe('{probe['id']}') matches pre-refactor reference exactly", actual == expected, f"expected={expected!r} actual={actual!r}")
        check(
            f"v1 build_result_for_probe('{probe['id']}') has no v2-only keys",
            "contract" not in actual and "bullet_count_rule" not in actual and "parsed_narrative" not in actual,
            str(actual.keys()),
        )


def test_v1_adapter_check_format_valid_matches_prepare_data_directly():
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
    check("parse_args: three positional args preserved in order, contract defaults to v1", positional == ["bench.jsonl", "ckpt_dir", "out.json"] and contract == "v1", (positional, contract))


def test_parse_args_extracts_contract_flag_from_any_position():
    positional, contract = rbm.parse_args(["--contract=v2", "bench.jsonl", "ckpt_dir"])
    check("parse_args: --contract=v2 extracted from front, positionals intact", positional == ["bench.jsonl", "ckpt_dir"] and contract == "v2", (positional, contract))
    positional, contract = rbm.parse_args(["bench.jsonl", "--contract=v2", "ckpt_dir"])
    check("parse_args: --contract=v2 extracted from middle, positionals intact and in order", positional == ["bench.jsonl", "ckpt_dir"] and contract == "v2", (positional, contract))


def test_parse_args_rejects_malformed_cli_invocations():
    malformed = [
        (["--contract=v1", "bench.jsonl", "--contract=v2"], "repeated --contract flag"),
        (["--contract=v2"], "no benchmark positional"),
        (["bench.jsonl", "a", "b", "c"], "excess positional arguments"),
        (["--contract="], "empty --contract value"),
        (["--bogus-flag", "bench.jsonl"], "unrecognized flag"),
    ]
    for argv, name in malformed:
        try:
            result = rbm.parse_args(argv)
            check(f"parse_args rejects: {name}", False, f"wrongly accepted -> {result}")
        except ValueError as e:
            check(f"parse_args rejects: {name}", True, str(e))


# ---------------------------------------------------------------------------
# Part 5: v2 result construction (dummy-only)
# ---------------------------------------------------------------------------

def test_v2_build_result_includes_full_structural_package():
    v2 = ca.select_contract_adapter("v2")
    probe = _v2_probe("sdi2-02", bullet_rule={"operator": "exact", "value": 1}, action_rule={"operator": "exact", "value": 1})
    result = rbm.build_result_for_probe(probe, v2, ONE_BULLET_ONE_ACTION)
    check("v2 result carries contract='v2'", result.get("contract") == "v2", result.get("contract"))
    check("v2 result carries contract_version", result.get("contract_version") == v2.version, result.get("contract_version"))
    check("v2 result carries contract_fingerprint", result.get("contract_fingerprint") == v2.expected_fingerprint, result.get("contract_fingerprint"))
    check("v2 result carries parser_version", result.get("parser_version") == v2.parser_version, result.get("parser_version"))
    check("v2 result carries parsed_narrative", result.get("parsed_narrative") == "text", result.get("parsed_narrative"))
    check("v2 result carries parsed_bullets", result.get("parsed_bullets") == ["one idea"], result.get("parsed_bullets"))
    check("v2 result carries parsed_actions", result.get("parsed_actions") == ["one task"], result.get("parsed_actions"))
    check("v2 result bullet_count_result actual=1, passed=True", result["bullet_count_result"] == {"actual": 1, "rule": probe["bullet_count_rule"], "passed": True}, result["bullet_count_result"])


def test_v2_unparseable_output_fails_count_rules_without_raising_and_nulls_parsed_fields():
    v2 = ca.select_contract_adapter("v2")
    probe = _v2_probe("sdi2-02", bullet_rule={"operator": "exact", "value": 1}, action_rule={"operator": "exact", "value": 1})
    result = rbm.build_result_for_probe(probe, v2, "not structured at all")
    check("unparseable v2 output: format_valid is False", result["format_valid"] is False)
    check("unparseable v2 output: parsed_narrative is None", result["parsed_narrative"] is None)
    check("unparseable v2 output: bullet_count_result fails with actual=None (no raise)", result["bullet_count_result"] == {"actual": None, "rule": probe["bullet_count_rule"], "passed": False}, result["bullet_count_result"])


def test_v2_probe_without_count_rules_gets_none_for_count_fields():
    v2 = ca.select_contract_adapter("v2")
    probe = {"id": "p", "category": "direct", "kind": "direct"}
    result = rbm.build_result_for_probe(probe, v2, ONE_BULLET_ONE_ACTION)
    check("v2 probe with no declared rules: bullet_count_rule is None", result["bullet_count_rule"] is None)
    check("v2 probe with no declared rules: bullet_count_result is None", result["bullet_count_result"] is None)


# ---------------------------------------------------------------------------
# Part 6 (acceptance tests 4, 5, 6): structural integrity, field by field
# ---------------------------------------------------------------------------

def _consistent_v2_result():
    # required_semantic_dimensions/primary_checks are deliberately non-empty
    # here (not _v2_probe's bare default of []/[]) -- a gate-4/5 test tampers
    # these down to []/{} and needs that to be a real, detectable change,
    # not a no-op against an already-empty rubric.
    v2 = ca.select_contract_adapter("v2")
    probe = _v2_probe(
        "sdi2-02", bullet_rule={"operator": "exact", "value": 1}, action_rule={"operator": "exact", "value": 1},
        required_semantic_dimensions=["topic_completeness"], primary_checks=["TASK_SURVIVED"],
    )
    result = rbm.build_result_for_probe(probe, v2, ONE_BULLET_ONE_ACTION)
    result["id"] = probe["id"]
    return probe, _fully_score(result)


def test_verify_v2_structural_integrity_passes_on_untampered_result():
    probe, result = _consistent_v2_result()
    try:
        rb.verify_v2_structural_integrity(probe, result)
        check("verify_v2_structural_integrity: untampered result passes", True)
    except ValueError as e:
        check("verify_v2_structural_integrity: untampered result passes", False, str(e))


def test_verify_v2_structural_integrity_catches_every_tampered_field():
    tamper_cases = {
        "contract": "v1",
        "contract_version": "wrong-version",
        "contract_fingerprint": "0" * 64,
        "parser_version": "wrong-parser-version",
        "format_valid": "false",  # Finding 2 repro 3: string, not bool
        "parsed_narrative": "a different narrative",
        "parsed_bullets": ["a different bullet"],
        "parsed_actions": ["a different action"],
        "bullet_count_rule": {"operator": "exact", "value": 99},  # Finding 2 repro 1
        "action_count_rule": {"operator": "max", "value": 5},
        "bullet_count_result": {"actual": 1, "rule": {"operator": "exact", "value": 1}, "passed": False},
        "action_count_result": {"actual": 1, "rule": {"operator": "exact", "value": 1}, "passed": False},
    }
    for field, bad_value in tamper_cases.items():
        probe, result = _consistent_v2_result()
        tampered = dict(result)
        tampered[field] = bad_value
        try:
            rb.verify_v2_structural_integrity(probe, tampered)
            check(f"verify_v2_structural_integrity catches tampered {field!r}", False, "did not raise")
        except ValueError as e:
            check(f"verify_v2_structural_integrity catches tampered {field!r}", True, str(e))


def test_verify_v2_structural_integrity_catches_missing_fields():
    required_fields = [
        "contract", "contract_version", "contract_fingerprint", "parser_version",
        "format_valid", "parsed_narrative", "parsed_bullets", "parsed_actions",
        "bullet_count_rule", "action_count_rule", "bullet_count_result", "action_count_result",
    ]
    for field in required_fields:
        probe, result = _consistent_v2_result()
        del result[field]
        try:
            rb.verify_v2_structural_integrity(probe, result)
            check(f"verify_v2_structural_integrity catches missing {field!r}", False, "did not raise")
        except (ValueError, KeyError) as e:
            check(f"verify_v2_structural_integrity catches missing {field!r}", True, str(e))


# ---------------------------------------------------------------------------
# Part 7 (acceptance tests 1, 2, 3): the actual report_benchmark.py CLI path
# ---------------------------------------------------------------------------

def _run_reporter_cli(probe: dict, result: dict, contract: str = "v2", extra_args: list = ()) -> subprocess.CompletedProcess:
    tmpdir = Path(tempfile.mkdtemp())
    bench_path = tmpdir / "bench.jsonl"
    results_path = tmpdir / "results.json"
    bench_path.write_text(json.dumps(probe) + "\n", encoding="utf-8")
    results_path.write_text(json.dumps([result]), encoding="utf-8")
    return subprocess.run(
        [sys.executable, "report_benchmark.py", str(bench_path), str(results_path), f"--contract={contract}", *extra_args],
        cwd=str(TRAINING_DIR), capture_output=True, text=True,
    )


def test_report_cli_reports_failure_for_honestly_unmet_count_rule():
    # The exact scenario ChatGPT's review reproduced against the old code:
    # a fully-scored v2 case whose output has two bullets against an
    # exact-one rule must report 0/1, not 1/1.
    v2 = ca.select_contract_adapter("v2")
    probe = _v2_probe("sdi2-test", bullet_rule={"operator": "exact", "value": 1}, action_rule={"operator": "exact", "value": 0})
    result = rbm.build_result_for_probe(probe, v2, TWO_BULLETS_ZERO_ACTIONS)
    result["id"] = probe["id"]
    _fully_score(result)
    check("stored bullet_count_result correctly says passed=False", result["bullet_count_result"]["passed"] is False, result["bullet_count_result"])

    out = _run_reporter_cli(probe, result)
    check("report_benchmark.py CLI exits 0 for an honest (non-tampered) failing case", out.returncode == 0, out.stderr)
    check("report_benchmark.py CLI: Overall pass rate: 0/1", "Overall pass rate: 0/1" in out.stdout, out.stdout)
    check("report_benchmark.py CLI: Acceptance gates passed: 0/1", "Acceptance gates passed: 0/1" in out.stdout, out.stdout)


def test_report_cli_raises_on_tampered_stored_structural_result():
    probe, result = _consistent_v2_result()
    tampered = dict(result)
    tampered["action_count_result"] = {"actual": 1, "rule": probe["action_count_rule"], "passed": False}
    out = _run_reporter_cli(probe, tampered)
    check("report_benchmark.py CLI exits nonzero on a tampered structural result", out.returncode != 0, out.stdout + out.stderr)
    check("... traceback mentions the mismatch", "action_count_result" in out.stderr, out.stderr)


def test_report_cli_runs_structural_check_even_when_semantics_unscored():
    # Not fully scored (semantics still null) AND structurally tampered --
    # must still raise, proving structural verification isn't
    # short-circuited away by probe_passes() already being False.
    v2 = ca.select_contract_adapter("v2")
    probe = _v2_probe("sdi2-test", bullet_rule={"operator": "exact", "value": 1}, action_rule={"operator": "exact", "value": 1})
    result = rbm.build_result_for_probe(probe, v2, ONE_BULLET_ONE_ACTION)
    result["id"] = probe["id"]
    # Deliberately NOT calling _fully_score -- scores/capability_checks stay null.
    tampered = dict(result)
    tampered["contract"] = "v1"  # Finding 2 repro 2, on an unscored result
    out = _run_reporter_cli(probe, tampered)
    check(
        "report_benchmark.py CLI raises on tampering even when semantics are unscored (no short-circuit)",
        out.returncode != 0 and "contract" in out.stderr,
        out.stdout + out.stderr,
    )


def test_probe_passes_itself_is_unmodified_by_this_round():
    result = {
        "id": "x", "format_valid": True,
        "scores": {"topic_completeness": None, "attribution_accuracy": None, "uncertainty_preservation": None, "unsupported_addition_resistance": None},
        "capability_checks": {}, "required_semantic_dimensions": [],
    }
    check("probe_passes: unchanged legacy no-required-dimensions behavior still holds", rb.probe_passes(result) is True)


# ---------------------------------------------------------------------------
# Part 8: prompt_contract_vnext_adapter_structural_focused_rereview.md's
# 10 minimum focused re-review gates. All 4 findings behind these gates
# were independently reproduced against the pre-fix commit before being
# fixed (same reproductions as the review itself, re-run here as
# permanent regression tests, not just checked once by hand).
# ---------------------------------------------------------------------------

HISTORICAL_V1_BENCHMARK = TRAINING_DIR.parent / "datasets" / "benchmark" / "source_determined_bullets_acceptance.jsonl"
HISTORICAL_V1_SCORED_RESULTS = TRAINING_DIR / "gold_v1.2.2_seed17_newprompt_candidate_bullets_acceptance_scored_chatgpt.json"


def test_gate1_historical_v1_five_case_artifact_reports_under_default_v1():
    # Finding 1A's exact reproduction: sdb-01..05 declare only
    # bullet_count_rule (predating v2), which used to get force-routed
    # through v2 preflight by shape-based inference and broke outright.
    out = subprocess.run(
        [sys.executable, "report_benchmark.py", str(HISTORICAL_V1_BENCHMARK), str(HISTORICAL_V1_SCORED_RESULTS)],
        cwd=str(TRAINING_DIR), capture_output=True, text=True,
    )
    check("gate 1: historical v1 5-case artifact reports successfully under default (no --contract)", out.returncode == 0, out.stdout + out.stderr)
    check("gate 1: reports under the v1 adapter", "Reporting under contract adapter: v1" in out.stdout, out.stdout)


def test_gate10_historical_v1_pass_rate_is_unchanged_from_before_this_project():
    # The known-good number from the seed-17 compatibility study, recorded
    # in memory/provenance docs well before this adapter/structural-
    # validation work started: 1/5 (only sdb-03 passes). If this ever
    # reports anything else, either a real regression was introduced or
    # the historical artifact was edited -- both worth stopping on.
    out = subprocess.run(
        [sys.executable, "report_benchmark.py", str(HISTORICAL_V1_BENCHMARK), str(HISTORICAL_V1_SCORED_RESULTS)],
        cwd=str(TRAINING_DIR), capture_output=True, text=True,
    )
    check("gate 10: historical v1 5-case pass rate unchanged (1/5)", "Overall pass rate: 1/5" in out.stdout, out.stdout)


def test_gate2_protected_16_probes_under_explicit_v2_receive_structural_verification():
    # Finding 1B's exact reproduction: a protected probe (no count rules,
    # wrong category for the old shape-based inference) run under explicit
    # --contract=v2 must still have its parsed structure independently
    # re-verified, not skipped because the probe "doesn't look like v2."
    v2 = ca.select_contract_adapter("v2")
    probes = rbm.load_probes(TRAINING_DIR.parent / "datasets" / "benchmark" / "gold_v1.2.1_probes.jsonl")
    probe = probes[0]
    result = rbm.build_result_for_probe(probe, v2, ONE_BULLET_ONE_ACTION)
    result["id"] = probe["id"]
    _fully_score(result)
    tampered = dict(result)
    tampered["parsed_bullets"] = ["a fabricated bullet that was never really there"]
    out = _run_reporter_cli(probe, tampered, contract="v2")
    check(
        "gate 2: a protected (no-count-rule) probe's tampered v2 result still raises under --contract=v2",
        out.returncode != 0 and "parsed_bullets" in out.stderr,
        out.stdout + out.stderr,
    )


def test_gate3_v2_acceptance_benchmark_rejects_v1_downgrade():
    # A source_determined_items_v2 case must never be silently scored
    # under a default/v1 report -- that would skip its structural
    # verification entirely without anyone noticing.
    probe = _v2_probe("sdi2-01", bullet_rule={"operator": "exact", "value": 1}, action_rule={"operator": "exact", "value": 0})
    result = {"id": "sdi2-01"}  # doesn't even need to be well-formed -- must reject before scoring
    for contract, args in (("v1", ()), (None, ())):  # None => default, no --contract flag at all
        tmpdir = Path(tempfile.mkdtemp())
        bench_path, results_path = tmpdir / "bench.jsonl", tmpdir / "results.json"
        bench_path.write_text(json.dumps(probe) + "\n", encoding="utf-8")
        results_path.write_text(json.dumps([result]), encoding="utf-8")
        cmd = [sys.executable, "report_benchmark.py", str(bench_path), str(results_path)]
        if contract is not None:
            cmd.append(f"--contract={contract}")
        out = subprocess.run(cmd, cwd=str(TRAINING_DIR), capture_output=True, text=True)
        label = contract or "default (no flag)"
        check(f"gate 3: v2-acceptance case rejected under {label}", out.returncode != 0 and "source_determined_items_v2" in out.stderr, out.stdout + out.stderr)


def test_gate4_and_5_rubric_binding_catches_every_tampered_field():
    for field, bad_value in (
        ("required_semantic_dimensions", []),
        ("capability_checks", {}),
        ("category", "some-other-category"),
        ("kind", "some-other-kind"),
        ("status", "some-other-status"),
    ):
        probe, result = _consistent_v2_result()
        tampered = dict(result)
        tampered[field] = bad_value
        try:
            rb.verify_rubric_binding(probe, tampered)
            check(f"gate 4/5: verify_rubric_binding catches tampered {field!r}", False, "did not raise")
        except ValueError as e:
            check(f"gate 4/5: verify_rubric_binding catches tampered {field!r}", True, str(e))
    probe, result = _consistent_v2_result()
    try:
        rb.verify_rubric_binding(probe, result)
        check("gate 4/5: verify_rubric_binding accepts an untampered result", True)
    except ValueError as e:
        check("gate 4/5: verify_rubric_binding accepts an untampered result", False, str(e))


def test_gate6_duplicate_benchmark_ids_raise_before_map_construction():
    dup_rule = {"operator": "exact", "value": 1}
    probe = _v2_probe("dup", bullet_rule=dup_rule, action_rule=dup_rule)
    tmpdir = Path(tempfile.mkdtemp())
    bench_path, results_path = tmpdir / "bench.jsonl", tmpdir / "results.json"
    bench_path.write_text(json.dumps(probe) + "\n" + json.dumps(dict(probe)) + "\n", encoding="utf-8")
    results_path.write_text("[]", encoding="utf-8")
    out = subprocess.run(
        [sys.executable, "report_benchmark.py", str(bench_path), str(results_path), "--contract=v2"],
        cwd=str(TRAINING_DIR), capture_output=True, text=True,
    )
    check("gate 6: duplicate benchmark IDs raise", out.returncode != 0 and "duplicate id in benchmark file" in out.stderr, out.stdout + out.stderr)


def test_gate7_duplicate_missing_extra_result_ids():
    probe, result = _consistent_v2_result()

    def run(probes: list, results: list, extra_args=()) -> subprocess.CompletedProcess:
        tmpdir = Path(tempfile.mkdtemp())
        bench_path, results_path = tmpdir / "bench.jsonl", tmpdir / "results.json"
        bench_path.write_text("\n".join(json.dumps(p) for p in probes) + "\n", encoding="utf-8")
        results_path.write_text(json.dumps(results), encoding="utf-8")
        return subprocess.run(
            [sys.executable, "report_benchmark.py", str(bench_path), str(results_path), "--contract=v2", *extra_args],
            cwd=str(TRAINING_DIR), capture_output=True, text=True,
        )

    out = run([probe], [result, dict(result)])
    check("gate 7: duplicate result IDs raise", out.returncode != 0 and "duplicate id in results file" in out.stderr, out.stdout + out.stderr)

    out = run([probe], [])
    check("gate 7: missing result (strict default) raises", out.returncode != 0 and "do not match exactly" in out.stderr, out.stdout + out.stderr)

    probe2, result2 = _consistent_v2_result()
    result2["id"] = "not-in-benchmark"
    out = run([probe], [result2])
    check("gate 7: extra result not in benchmark (strict default) raises", out.returncode != 0 and "do not match exactly" in out.stderr, out.stdout + out.stderr)

    out = run([probe], [], extra_args=["--allow-partial"])
    check(
        "gate 7: --allow-partial permits a missing result as a diagnostic (non-release) report",
        out.returncode == 0 and "n/a (0 probes)" in out.stdout,
        out.stdout + out.stderr,
    )


def test_gate8_missing_or_non_string_raw_output_raises():
    for label, mutate in (
        ("missing", lambda d: d.pop("raw_output")),
        ("null", lambda d: d.__setitem__("raw_output", None)),
        ("a number", lambda d: d.__setitem__("raw_output", 12345)),
    ):
        probe, result = _consistent_v2_result()
        tampered = dict(result)
        mutate(tampered)
        try:
            rb.verify_v2_structural_integrity(probe, tampered)
            check(f"gate 8: raw_output ({label}) raises", False, "did not raise")
        except ValueError as e:
            check(f"gate 8: raw_output ({label}) raises", "raw_output" in str(e), str(e))


def test_gate9_default_v1_still_never_imports_v2_modules_including_the_rejection_path():
    # Re-verified against the new report_benchmark.py flow specifically:
    # even the "v2-acceptance case rejected under v1" error path (gate 3)
    # must not need to import v2 modules to detect and raise that error.
    script = (
        "import sys, json, tempfile\n"
        "from pathlib import Path\n"
        "tmpdir = Path(tempfile.mkdtemp())\n"
        "bench = tmpdir / 'bench.jsonl'\n"
        "results = tmpdir / 'results.json'\n"
        "bench.write_text(json.dumps({'id': 'x', 'category': 'source_determined_items_v2'}) + '\\n', encoding='utf-8')\n"
        "results.write_text('[]', encoding='utf-8')\n"
        "import report_benchmark\n"
        "try:\n"
        "    import sys as _s\n"
        "    sys.argv = ['report_benchmark.py', str(bench), str(results)]\n"
        "    report_benchmark.main()\n"
        "except SystemExit:\n"
        "    pass\n"
        "except Exception:\n"
        "    pass\n"
        "present = [m for m in sys.modules if 'prompt_contract_v2' in m]\n"
        "print('PRESENT:' + repr(present))\n"
    )
    out = subprocess.run([sys.executable, "-c", script], cwd=str(TRAINING_DIR), capture_output=True, text=True)
    check(
        "gate 9: the v2-acceptance-under-v1 rejection path itself never imports v2 modules",
        "PRESENT:[]" in out.stdout,
        out.stdout + out.stderr,
    )


# ---------------------------------------------------------------------------
# Part 9: prompt_contract_vnext_final_boundary_rereview.md's 3 findings.
# All independently reproduced against the pre-fix code before being fixed.
# ---------------------------------------------------------------------------

def test_final1_v1_downgrade_guard_checks_field_presence_not_contract_value():
    # The exact reproduction: nulling only "contract" (not removing it, and
    # not touching any other v2-only field) used to be enough to evade the
    # old `r.get("contract") is not None` check entirely.
    v2 = ca.select_contract_adapter("v2")
    probes = rbm.load_probes(TRAINING_DIR.parent / "datasets" / "benchmark" / "gold_v1.2.1_probes.jsonl")
    probe = probes[0]
    result = rbm.build_result_for_probe(probe, v2, ONE_BULLET_ONE_ACTION)
    result["id"] = probe["id"]
    _fully_score(result)

    nulled_contract = dict(result)
    nulled_contract["contract"] = None
    out = _run_reporter_cli(probe, nulled_contract, contract="v1")
    check(
        "final finding 1: contract=None (not removed) still raises under v1 mode",
        out.returncode != 0 and "v2-only structural field" in out.stderr,
        out.stdout + out.stderr,
    )

    # Each remaining v2-only field, present alone on top of an otherwise
    # complete and valid v1 result (so the v2-only-field check is the only
    # thing that can fire -- not an earlier check reacting to some other
    # missing v1 field), must also individually trigger rejection.
    v1 = ca.select_contract_adapter("v1")
    v1_shaped = rbm.build_result_for_probe(probe, v1, "###NARRATIVE###\nx\n###BULLETS###\n###ACTIONS###")
    v1_shaped["id"] = probe["id"]
    _fully_score(v1_shaped)
    other_v2_only_fields = [f for f in rb.V2_ONLY_STRUCTURAL_FIELDS if f != "contract"]
    for field in other_v2_only_fields:
        with_one_v2_field = dict(v1_shaped)
        with_one_v2_field[field] = result[field]
        out = _run_reporter_cli(probe, with_one_v2_field, contract="v1")
        check(
            f"final finding 1: {field!r} present alone (on an otherwise-valid v1 result) still raises under v1 mode",
            out.returncode != 0 and "v2-only structural field" in out.stderr,
            out.stdout + out.stderr,
        )


def test_final2_format_valid_must_be_a_literal_boolean_for_both_contracts():
    for label, bad_value in (("missing", None), ("null", None), ("a number", 1), ("string true", "true"), ("string false", "false")):
        result = {
            "id": "v1-test", "category": "direct", "kind": "direct", "status": "regression_guard",
            "required_semantic_dimensions": [],
            "scores": {"topic_completeness": None, "attribution_accuracy": None, "uncertainty_preservation": None, "unsupported_addition_resistance": None},
            "capability_checks": {},
        }
        if label != "missing":
            result["format_valid"] = bad_value
        try:
            rb.require_format_valid_is_boolean(result)
            check(f"final finding 2: format_valid ({label}) raises", False, "did not raise")
        except ValueError as e:
            check(f"final finding 2: format_valid ({label}) raises", "format_valid" in str(e), str(e))

    for real_bool in (True, False):
        result = {"id": "v1-test", "format_valid": real_bool}
        try:
            rb.require_format_valid_is_boolean(result)
            check(f"final finding 2: literal {real_bool} is accepted", True)
        except ValueError as e:
            check(f"final finding 2: literal {real_bool} is accepted", False, str(e))


def test_final2_report_cli_rejects_string_format_valid_end_to_end():
    probe = {
        "id": "v1-test", "category": "direct", "kind": "direct", "status": "regression_guard",
        "required_semantic_dimensions": ["topic_completeness"], "primary_checks": [],
    }
    result = {
        "id": "v1-test", "category": "direct", "kind": "direct", "status": "regression_guard",
        "required_semantic_dimensions": ["topic_completeness"], "format_valid": "false",
        "scores": {"topic_completeness": 2, "attribution_accuracy": None, "uncertainty_preservation": None, "unsupported_addition_resistance": None},
        "capability_checks": {},
    }
    out = _run_reporter_cli(probe, result, contract="v1")
    check(
        "final finding 2: report_benchmark.py CLI rejects a string format_valid under v1",
        out.returncode != 0 and "format_valid" in out.stderr,
        out.stdout + out.stderr,
    )


def test_final3_v1_runner_preflight_rejects_duplicate_ids_before_torch_import():
    tmpdir = Path(tempfile.mkdtemp())
    bench_path = tmpdir / "bench.jsonl"
    dup = {"id": "dup", "input": "x", "category": "c", "kind": "direct"}
    bench_path.write_text(json.dumps(dup) + "\n" + json.dumps(dict(dup, input="y")) + "\n", encoding="utf-8")
    out = subprocess.run(
        [sys.executable, "run_benchmark.py", str(bench_path), "ckpt", "out.json"],
        cwd=str(TRAINING_DIR), capture_output=True, text=True,
    )
    check(
        "final finding 3: duplicate-ID v1 benchmark fails before the torch import",
        out.returncode != 0 and "duplicate id in benchmark file" in out.stderr and "torch" not in out.stderr,
        out.stdout + out.stderr,
    )


def test_final3_ordinary_v1_runner_preflight_still_reaches_torch_import_unchanged():
    # Confirms the fix didn't add a false-positive rejection for the
    # normal, non-duplicate case -- must get past contract selection and
    # the new unconditional duplicate check without complaint. What it
    # fails on next is environment-dependent (this project's base Python
    # has no torch installed at all and fails on that import; the venv
    # has torch but no real "ckpt" checkpoint directory and fails trying
    # to load a tokenizer from it) -- either is fine; a "duplicate id"
    # rejection is the only wrong outcome here.
    out = subprocess.run(
        [sys.executable, "run_benchmark.py",
         str(TRAINING_DIR.parent / "datasets" / "benchmark" / "gold_v1.2.1_probes.jsonl"), "ckpt", "out.json"],
        cwd=str(TRAINING_DIR), capture_output=True, text=True,
    )
    check(
        "final finding 3: ordinary (non-duplicate) v1 benchmark isn't falsely rejected as a duplicate",
        out.returncode != 0 and "duplicate id" not in out.stderr,
        out.stdout + out.stderr,
    )


def main() -> None:
    tests = [
        test_v1_is_the_default_contract,
        test_select_v1_and_v2_succeed,
        test_unknown_contract_name_raises_before_any_model_import,
        test_fingerprint_mismatch_raises,
        test_fresh_process_v1_selection_never_imports_v2_modules,
        test_fresh_process_v2_selection_does_import_v2_modules,
        test_preflight_is_a_no_op_for_v1_even_with_garbage_rules,
        test_preflight_requires_both_rules_or_neither,
        test_preflight_rejects_unknown_operator,
        test_preflight_accepts_well_formed_rules,
        test_preflight_rejects_duplicate_probe_ids,
        test_preflight_rejects_malformed_rule_values,
        test_preflight_requires_both_rules_for_v2_acceptance_category_even_if_both_absent,
        test_preflight_accepts_protected_16_probes_under_v2_without_requiring_rules,
        test_report_time_preflight_also_rejects_missing_rules_and_duplicates,
        test_v1_build_result_matches_pre_refactor_reference_exactly,
        test_v1_adapter_check_format_valid_matches_prepare_data_directly,
        test_parse_args_default_contract_is_v1_and_positional_args_unaffected,
        test_parse_args_extracts_contract_flag_from_any_position,
        test_parse_args_rejects_malformed_cli_invocations,
        test_v2_build_result_includes_full_structural_package,
        test_v2_unparseable_output_fails_count_rules_without_raising_and_nulls_parsed_fields,
        test_v2_probe_without_count_rules_gets_none_for_count_fields,
        test_verify_v2_structural_integrity_passes_on_untampered_result,
        test_verify_v2_structural_integrity_catches_every_tampered_field,
        test_verify_v2_structural_integrity_catches_missing_fields,
        test_report_cli_reports_failure_for_honestly_unmet_count_rule,
        test_report_cli_raises_on_tampered_stored_structural_result,
        test_report_cli_runs_structural_check_even_when_semantics_unscored,
        test_probe_passes_itself_is_unmodified_by_this_round,
        test_gate1_historical_v1_five_case_artifact_reports_under_default_v1,
        test_gate10_historical_v1_pass_rate_is_unchanged_from_before_this_project,
        test_gate2_protected_16_probes_under_explicit_v2_receive_structural_verification,
        test_gate3_v2_acceptance_benchmark_rejects_v1_downgrade,
        test_gate4_and_5_rubric_binding_catches_every_tampered_field,
        test_gate6_duplicate_benchmark_ids_raise_before_map_construction,
        test_gate7_duplicate_missing_extra_result_ids,
        test_gate8_missing_or_non_string_raw_output_raises,
        test_gate9_default_v1_still_never_imports_v2_modules_including_the_rejection_path,
        test_final1_v1_downgrade_guard_checks_field_presence_not_contract_value,
        test_final2_format_valid_must_be_a_literal_boolean_for_both_contracts,
        test_final2_report_cli_rejects_string_format_valid_end_to_end,
        test_final3_v1_runner_preflight_rejects_duplicate_ids_before_torch_import,
        test_final3_ordinary_v1_runner_preflight_still_reaches_torch_import_unchanged,
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
