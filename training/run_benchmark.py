"""Run a datasets/benchmark/*.jsonl probe set against a checkpoint and write
a results scaffold ready for semantic scoring.

Usage:
    python run_benchmark.py <benchmark.jsonl> [checkpoint_dir] [output.json]

Defaults: checkpoint_dir=checkpoints/thoughtorganizer-flan-t5/final,
output.json=<benchmark-file-stem>_results.json next to this script.

Reads probe definitions from the benchmark file itself (not hardcoded here
-- avoids the earlier duplication where probes lived both inline in a
script and in datasets/benchmark/gold_v1.2.1_probes.jsonl), generates with
the identical prompt shape and generation settings train.py uses, and
writes raw output + automatically-computed format validity.

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

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from prepare_data import ACTIONS_MARKER, BULLETS_MARKER, NARRATIVE_MARKER, build_prompt

MAX_INPUT_TOKENS = 512
GENERATION_MAX_NEW_TOKENS = 300


def load_probes(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def check_format_valid(generated: str) -> bool:
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


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python run_benchmark.py <benchmark.jsonl> [checkpoint_dir] [output.json]", file=sys.stderr)
        sys.exit(1)

    benchmark_path = Path(sys.argv[1])
    checkpoint_dir = (
        Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent / "checkpoints" / "thoughtorganizer-flan-t5" / "final"
    )
    output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(__file__).parent / f"{benchmark_path.stem}_results.json"

    probes = load_probes(benchmark_path)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    tokenizer = AutoTokenizer.from_pretrained(str(checkpoint_dir))
    model = AutoModelForSeq2SeqLM.from_pretrained(str(checkpoint_dir)).to(device)
    model.eval()

    results = []
    for probe in probes:
        prompt = build_prompt(probe["input"])
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=MAX_INPUT_TOKENS).to(device)
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=GENERATION_MAX_NEW_TOKENS,
                repetition_penalty=1.3,
            )
        generated = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        valid = check_format_valid(generated)

        results.append(
            {
                "id": probe["id"],
                "category": probe["category"],
                "kind": probe["kind"],
                "status": probe.get("status"),
                "raw_output": generated,
                "format_valid": valid,
                # Semantic scoring: null until a human (or LLM-judge) pass fills
                # these in. 0/1/2 per Gold v1.2.1 Semantic Live-Evaluation
                # Suite's rubric (2=correct, 1=partially correct, 0=failed);
                # leave null for a dimension this probe doesn't test.
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
        )
        print(f"[{probe['id']}] format_valid={valid}")

    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote results scaffold to {output_path}")
    print(f"Format validity: {sum(r['format_valid'] for r in results)}/{len(results)}")
    print("Semantic scores are unfilled -- score against each probe's expected_behavior, then run report_benchmark.py.")


if __name__ == "__main__":
    main()
