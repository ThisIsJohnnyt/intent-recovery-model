"""Run a datasets/benchmark/*.jsonl probe set against a checkpoint and write
a results scaffold ready for semantic scoring.

Usage:
    python run_benchmark.py <benchmark.jsonl> [checkpoint_dir] [output.json] [--contract=v1|v2]

Defaults: checkpoint_dir=checkpoints/thoughtorganizer-flan-t5/final,
output.json=<benchmark-file-stem>_results.json next to this script,
--contract=v1 (the live prompt contract; omitting the flag reproduces
exactly the pre-adapter behavior of this script).

Reads probe definitions from the benchmark file itself (not hardcoded here
-- avoids the earlier duplication where probes lived both inline in a
script and in datasets/benchmark/gold_v1.2.1_probes.jsonl), generates with
the identical prompt shape and generation settings train.py uses, and
writes raw output + automatically-computed format validity.

--contract selects which prompt-contract adapter (see contract_adapters.py)
builds prompts and checks format validity. v1 is the live contract and
stays the default; v2 is the typed-marker candidate, opt-in only, per
prompt_contract_vnext_static_final_review_and_branch_reconciliation.md's
Disagreement 2 -- one runner with an adapter, not a second script, so
scoring-safety logic (this file's result schema, report_benchmark.py's
pass/fail logic) can never drift between a v1-only and a v2-only copy.
An unrecognized --contract value, a duplicated/empty --contract flag, a
missing or excess positional argument, a prompt-template drift from the
locked fingerprint, or a malformed count-rule/duplicate-ID declaration in
the benchmark file all raise before any model is loaded -- see
contract_adapters.py and parse_args() below for why.

This script does NOT score semantics -- topic completeness, attribution
accuracy, uncertainty preservation, and unsupported-addition resistance all
require judgment a script can't respectably fake. It writes those fields as
null, one entry per check named in each probe's own "primary_checks", ready
for a human (or a future LLM-judge pass) to fill in. Run report_benchmark.py
against the *scored* result to get pass rates and the other release-gate
statistics -- this script only produces the raw material for that step.
"""
import json
import sys
from pathlib import Path

from contract_adapters import (
    DEFAULT_CONTRACT,
    ContractAdapter,
    ContractSelectionError,
    evaluate_count_rule,
    known_contract_names,
    parse_contract_flag,
    preflight_validate_count_rules,
    select_contract_adapter,
)

MAX_INPUT_TOKENS = 512
GENERATION_MAX_NEW_TOKENS = 300


def load_probes(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args(argv: list[str]) -> tuple[list[str], str]:
    """Splits a leading --contract=X flag out of argv (via the shared
    parse_contract_flag(), also used by report_benchmark.py -- one
    implementation of that validation, not two that could drift apart),
    leaving positional-argument parsing itself completely untouched for
    every well-formed invocation -- the whole point of proving the v1
    default path is unaffected by this refactor.

    Fail-closed per prompt_contract_vnext_adapter_structural_implementation_review.md's
    Finding 6: raises ContractSelectionError (a ValueError subclass, not a
    silent best-effort guess, not an IndexError from unrelated code
    further down) on a repeated --contract flag, an empty --contract
    value, an unrecognized flag, a missing benchmark-file argument, or
    more than 3 positional arguments.
    """
    remaining, contract = parse_contract_flag(argv)
    if contract is None:
        contract = DEFAULT_CONTRACT
    positional = []
    for arg in remaining:
        if arg.startswith("--"):
            raise ContractSelectionError(f"unrecognized flag: {arg}")
        positional.append(arg)
    if not positional:
        raise ContractSelectionError("missing required <benchmark.jsonl> argument")
    if len(positional) > 3:
        raise ContractSelectionError(
            "too many positional arguments (expected at most 3: "
            f"benchmark.jsonl [checkpoint_dir] [output.json]), got {len(positional)}: {positional}"
        )
    return positional, contract


def build_result_for_probe(probe: dict, adapter: ContractAdapter, generated: str) -> dict:
    """Pure function, no model/tokenizer involved -- everything about a
    result that doesn't require actually generating text lives here, so it
    can be tested directly against synthetic `generated` strings (dummy
    data only, no inference) rather than only through a full model run.

    For the v1 adapter (parse is None) this produces exactly the dict
    shape/values the pre-adapter version of this script always produced --
    no new keys are added. For a counting-capable adapter (v2), stores the
    complete structural package report_benchmark.py's structural-integrity
    check independently re-derives and compares against: contract identity
    (name/version/fingerprint/parser version), parse validity, the parsed
    narrative/bullets/actions themselves (not just their counts), the
    count rules copied from the probe, and each rule's evaluated result.
    Storing more than just the final pass/fail is what makes independent
    re-verification possible at report time instead of a bare trust-the-
    stored-bool convention.
    """
    valid = adapter.check_format_valid(generated)
    result = {
        "id": probe["id"],
        "category": probe["category"],
        "kind": probe["kind"],
        "status": probe.get("status"),
        # Copied from the probe so the results file is self-contained --
        # report_benchmark.py's probe_passes() requires these specific
        # dimensions to be non-null and exactly 2, not just any dimension
        # the scorer happened to fill in.
        "required_semantic_dimensions": probe.get("required_semantic_dimensions", []),
        "raw_output": generated,
        "format_valid": valid,
        # Semantic scoring: null until a human (or LLM-judge) pass fills
        # these in. 0/1/2 per Gold v1.2.1 Semantic Live-Evaluation Suite's
        # rubric (2=correct, 1=partially correct, 0=failed); leave null for
        # a dimension this probe doesn't test.
        "scores": {
            "topic_completeness": None,
            "attribution_accuracy": None,
            "uncertainty_preservation": None,
            "unsupported_addition_resistance": None,
        },
        # One entry per check named in this probe's own primary_checks;
        # true/false once scored.
        "capability_checks": {check: None for check in probe.get("primary_checks", [])},
        # Canonical TAXONOMY.md failure-category names observed, if any.
        "failure_labels": [],
    }

    if adapter.parse is not None:
        bullet_rule = probe.get("bullet_count_rule")
        action_rule = probe.get("action_count_rule")
        parsed = adapter.parse(generated) if valid else None
        if parsed is not None:
            actual_bullets, actual_actions = len(parsed.bullets), len(parsed.actions)
        else:
            # Output that doesn't even parse can't satisfy a declared count
            # rule -- evaluate_count_rule(rule, None) always fails it
            # rather than raising, distinct from a malformed operator.
            actual_bullets, actual_actions = None, None

        result["contract"] = adapter.name
        result["contract_version"] = adapter.version
        result["contract_fingerprint"] = adapter.expected_fingerprint
        result["parser_version"] = adapter.parser_version
        result["parsed_narrative"] = parsed.narrative if parsed is not None else None
        result["parsed_bullets"] = parsed.bullets if parsed is not None else None
        result["parsed_actions"] = parsed.actions if parsed is not None else None
        result["bullet_count_rule"] = bullet_rule
        result["action_count_rule"] = action_rule
        result["bullet_count_result"] = evaluate_count_rule(bullet_rule, actual_bullets)
        result["action_count_result"] = evaluate_count_rule(action_rule, actual_actions)

    return result


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage: python run_benchmark.py <benchmark.jsonl> [checkpoint_dir] [output.json] "
            f"[--contract={'|'.join(known_contract_names())}]",
            file=sys.stderr,
        )
        sys.exit(1)

    positional, contract_name = parse_args(sys.argv[1:])

    benchmark_path = Path(positional[0])
    checkpoint_dir = (
        Path(positional[1]) if len(positional) > 1 else Path(__file__).parent / "checkpoints" / "thoughtorganizer-flan-t5" / "final"
    )
    output_path = Path(positional[2]) if len(positional) > 2 else Path(__file__).parent / f"{benchmark_path.stem}_results.json"

    # Fail-closed contract selection: unknown name or a fingerprint that
    # doesn't match the locked value raises here, before torch/transformers
    # are even imported below -- see contract_adapters.py.
    adapter = select_contract_adapter(contract_name)
    print(f"Using contract adapter: {adapter.name} ({adapter.version})")

    probes = load_probes(benchmark_path)
    preflight_validate_count_rules(probes, adapter)

    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    tokenizer = AutoTokenizer.from_pretrained(str(checkpoint_dir))
    model = AutoModelForSeq2SeqLM.from_pretrained(str(checkpoint_dir)).to(device)
    model.eval()

    results = []
    for probe in probes:
        prompt = adapter.build_prompt(probe["input"])
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=MAX_INPUT_TOKENS).to(device)
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=GENERATION_MAX_NEW_TOKENS,
                repetition_penalty=1.3,
            )
        generated = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        result = build_result_for_probe(probe, adapter, generated)
        results.append(result)
        print(f"[{probe['id']}] format_valid={result['format_valid']}")

    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote results scaffold to {output_path}")
    print(f"Format validity: {sum(r['format_valid'] for r in results)}/{len(results)}")
    print("Semantic scores are unfilled -- score against each probe's expected_behavior, then run report_benchmark.py.")


if __name__ == "__main__":
    main()
