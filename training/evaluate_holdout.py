"""Evaluate a checkpoint against the SEALED real_holdout.jsonl set.

Usage:
    python evaluate_holdout.py --milestone MILESTONE_ID [checkpoint_dir]

This is deliberately a separate, explicit script -- NOT run automatically
by train.py or prepare_data.py. datasets/real_holdout.jsonl is reserved
for declared release milestones (see docs/decisions/PDR-004.md and
PDR-005.md): it must not be consulted to guide day-to-day development,
curriculum authoring, seed selection, or checkpoint tuning. Routine
development-time evaluation against real notes belongs in
datasets/real_validation.jsonl instead, which train.py already evaluates
automatically after every run.

Least-privilege by design: loads and validates the sealed source directly
in memory, using prepare_data.py's own load_jsonl (which in turn calls
validate_record/build_prompt) -- never routes through a routinely
materialized processed copy, and writes no processed holdout file.
--milestone is required; there is no default, and this refuses to run
without one.

Fails closed (refuses to evaluate) if any holdout record has no matching
active, holdout_eligible entry in the private consent/provenance
manifest -- per REAL_DATA_SPLIT_AND_SEALING_PROTOCOL.md's assignment
prerequisites, no record should ever be evaluated without a prior,
recorded consent decision. Saves a real-eval-v1 structured result under
training/results/private/real_holdout/<milestone>/, including checkpoint
and dataset fingerprints -- but does not yet compare those against a
previously *declared* fingerprint, since no holdout has ever been sealed
yet to declare one against (see PDR-005 Phase E status).

Before running this: confirm a release milestone has actually been
declared. If you're just curious how a checkpoint is doing, that's
exactly the temptation this file exists to resist -- use
real_validation.jsonl for that instead.
"""
import argparse
import subprocess
import sys
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from prepare_data import ACTIONS_MARKER, BULLETS_MARKER, DATA_DIR, NARRATIVE_MARKER, build_prompt, load_jsonl
from real_data_eval_logging import build_result_artifact, new_result_record, save_result_artifact
from real_data_private import checkpoint_fingerprint, dataset_fingerprint, load_manifest, load_rubrics, source_fingerprint
from train import DEFAULT_OUTPUT_DIR, GENERATION_MAX_NEW_TOKENS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "checkpoint_dir",
        nargs="?",
        default=None,
        help="Checkpoint to evaluate (default: training/checkpoints/thoughtorganizer-flan-t5/final)",
    )
    parser.add_argument(
        "--milestone",
        type=str,
        required=True,
        help="Declared release-milestone identifier. Required -- this script refuses to run without one.",
    )
    parser.add_argument("--seed", type=int, default=None, help="Training seed to record in the result artifact, if known.")
    parser.add_argument("--run-id", type=str, default="unspecified", help="Training run ID to record in the result artifact.")
    parser.add_argument("--reason", type=str, required=True, help="Declared reason for this evaluation (required -- see REAL_DATA_SPLIT_AND_SEALING_PROTOCOL.md's 'Declaring a holdout evaluation').")
    return parser.parse_args()


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True, cwd=Path(__file__).parent
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def _check_format_valid(generated: str) -> bool:
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


def _link_to_manifest(holdout_records: list[dict]) -> list[dict]:
    """Fails closed: every holdout record must have an active,
    holdout_eligible entry in the private manifest, matched by
    source_fingerprint. Unconsented or ineligible content is never
    evaluated, no matter how it got into real_holdout.jsonl."""
    manifest = load_manifest()
    rubrics = load_rubrics()
    by_source_fp = {entry.get("source_fingerprint", "").removeprefix("sha256:"): entry for entry in manifest.values()}

    linked = []
    for r in holdout_records:
        sfp = source_fingerprint(r["_input"])
        entry = by_source_fp.get(sfp)
        if entry is None:
            print(
                f"FAIL CLOSED: a holdout record has no matching entry in the private "
                f"consent/provenance manifest (source_fingerprint={sfp[:12]}...). "
                "Refusing to evaluate content with no recorded consent decision.",
                file=sys.stderr,
            )
            sys.exit(1)
        record_id = entry["record_id"]
        if entry.get("withdrawal_status") != "active":
            print(f"FAIL CLOSED: manifest entry {record_id} is not active (withdrawal_status={entry.get('withdrawal_status')!r}).", file=sys.stderr)
            sys.exit(1)
        allowed_uses = entry.get("allowed_uses")
        if not isinstance(allowed_uses, dict):
            print(f"FAIL CLOSED: manifest entry {record_id} is missing 'allowed_uses' -- malformed manifest entry, not merely ineligible.", file=sys.stderr)
            sys.exit(1)
        if not allowed_uses.get("holdout_eligible"):
            print(f"FAIL CLOSED: manifest entry {record_id} is not marked holdout_eligible.", file=sys.stderr)
            sys.exit(1)
        rubric = rubrics.get(record_id)
        if rubric is None:
            print(f"FAIL CLOSED: manifest entry {record_id} has no matching private rubric entry.", file=sys.stderr)
            sys.exit(1)
        linked.append(
            {
                "record_id": record_id,
                "prompt": r["prompt"],
                "target": r["target"],
                "_input": r["_input"],
                "source_fingerprint": entry["source_fingerprint"],
                "pair_fingerprint": entry["pair_fingerprint"],
                "rubric_fingerprint": entry["rubric_fingerprint"],
            }
        )
    return linked


def main() -> None:
    cli_args = parse_args()
    checkpoint_dir = Path(cli_args.checkpoint_dir) if cli_args.checkpoint_dir else DEFAULT_OUTPUT_DIR / "final"

    holdout_path = DATA_DIR / "real_holdout.jsonl"
    if not holdout_path.exists() or not holdout_path.read_text(encoding="utf-8").strip():
        print(
            f"{holdout_path} is empty -- nothing to evaluate. This is expected "
            "until a real release milestone calls for populating "
            "datasets/real_holdout.jsonl. See docs/decisions/PDR-005.md.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        "=== SEALED HOLDOUT EVALUATION ===\n"
        f"Milestone: {cli_args.milestone}\n"
        "This should only run at a declared release milestone. If that's not "
        "why you're running this, stop and use real_validation.jsonl instead.\n"
    )

    # Loaded and validated directly in memory -- never through
    # prepare_data.py's routine processed-output path, and never written
    # back to disk as a processed copy of the sealed source.
    holdout_records = load_jsonl(holdout_path)
    linked = _link_to_manifest(holdout_records)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    print(f"Checkpoint: {checkpoint_dir}")

    tokenizer = AutoTokenizer.from_pretrained(str(checkpoint_dir))
    model = AutoModelForSeq2SeqLM.from_pretrained(str(checkpoint_dir)).to(device)

    generation_config = {"max_new_tokens": GENERATION_MAX_NEW_TOKENS, "repetition_penalty": 1.3}
    results = []
    for r in linked:
        inputs = tokenizer(r["prompt"], return_tensors="pt", truncation=True, max_length=512).to(device)
        output_ids = model.generate(**inputs, max_new_tokens=GENERATION_MAX_NEW_TOKENS, repetition_penalty=1.3)
        generated = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        valid = _check_format_valid(generated)
        results.append(new_result_record(r["record_id"], generated, valid))
        print(f"[{r['record_id']}] format_valid={valid}")

    ckpt_fp = checkpoint_fingerprint(checkpoint_dir)
    ds_fp = dataset_fingerprint(linked, "real_holdout")
    print(f"Checkpoint fingerprint: sha256:{ckpt_fp}")
    print(f"Dataset fingerprint: sha256:{ds_fp}")
    print(
        "(Computed, not yet compared against a declared value -- no holdout "
        "has ever been sealed to declare one against. Comparison arrives "
        "once a real sealing event exists.)"
    )

    artifact = build_result_artifact(
        split="real_holdout",
        evaluation_reason=cli_args.reason,
        git_commit=_git_commit(),
        checkpoint={
            "path": str(checkpoint_dir),
            "fingerprint": ckpt_fp,
            "training_seed": cli_args.seed if cli_args.seed is not None else -1,
            "run_id": cli_args.run_id,
        },
        dataset={
            "fingerprint": ds_fp,
            "record_count": len(linked),
            "rubric_version": "real-rubric-v1",
        },
        generation_config=generation_config,
        results=results,
        release_milestone=cli_args.milestone,
    )
    saved_path = save_result_artifact(artifact)
    print(f"\nSaved structured result: {saved_path}")
    print(f"Format validity: {artifact['aggregate']['format_valid']}")
    print("Semantic scores are unscored -- independent Claude Code / ChatGPT review still required before this can guide any decision.")


if __name__ == "__main__":
    main()
