"""Evaluate a checkpoint against the SEALED real_holdout.jsonl set.

Usage:
    python evaluate_holdout.py --milestone MILESTONE_ID --reason REASON CHECKPOINT_DIR

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

import real_data_manifest as rdm
from prepare_data import ACTIONS_MARKER, BULLETS_MARKER, DATA_DIR, NARRATIVE_MARKER, build_prompt, load_jsonl
from real_data_eval_logging import UnsafeIdentifierError, _validate_identifier, build_result_artifact, new_result_record, save_result_artifact
from real_data_private import checkpoint_fingerprint, dataset_fingerprint, load_rubrics, pair_fingerprint, rubric_fingerprint, source_fingerprint
from train import GENERATION_MAX_NEW_TOKENS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "checkpoint_dir",
        type=str,
        help="Checkpoint to evaluate. Required -- a declared holdout evaluation names a single frozen candidate explicitly, never a silent default.",
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
    """Fails closed at every step, per real_data_manifest_schema_decision.md:
    every holdout record must have a manifest entry that (1) passes full
    real-manifest-v1 schema validation, (2) is eligible for real_holdout
    evaluation (active, author-confirmed, de-identification approved,
    annotation adjudicated, holdout_eligible, split assigned to
    real_holdout), and (3) has source/pair/rubric fingerprints that,
    freshly recomputed from the actual holdout record and rubric, match
    the manifest's declared values exactly. Unconsented, ineligible, or
    tampered/stale content is never evaluated, no matter how it got into
    real_holdout.jsonl or the manifest.

    Loaded with pilot_mode=False: pilot_mode gates *assigning* new
    holdout-eligible entries into the manifest (enforced at write time by
    real_data_manifest.upsert_manifest_entry_validated), not evaluating
    entries that already exist there. This script's own required
    --milestone/--reason declaration is the gate for whether a holdout
    evaluation may proceed at all; conflating that with the pilot's
    write-side restriction would make this script permanently unusable
    for a legitimately declared milestone without a source change.
    """
    try:
        manifest = rdm.load_manifest_strict(pilot_mode=False)
    except rdm.ManifestValidationError as e:
        print(f"FAIL CLOSED: private manifest failed real-manifest-v1 schema validation: {e}", file=sys.stderr)
        sys.exit(1)
    rubrics = load_rubrics()
    by_source_fp = {
        entry["source_fingerprint"].removeprefix("sha256:"): entry
        for entry in manifest.values()
        if entry.get("source_fingerprint")
    }

    linked = []
    for r in holdout_records:
        computed_sfp = source_fingerprint(r["_input"])
        entry = by_source_fp.get(computed_sfp)
        if entry is None:
            print(
                f"FAIL CLOSED: a holdout record has no matching entry in the private "
                f"consent/provenance manifest (source_fingerprint={computed_sfp[:12]}...). "
                "Refusing to evaluate content with no recorded consent decision.",
                file=sys.stderr,
            )
            sys.exit(1)
        record_id = entry["record_id"]

        try:
            rdm.check_evaluation_eligibility(entry, expected_split="real_holdout")
        except rdm.EligibilityError as e:
            print(f"FAIL CLOSED: {e}", file=sys.stderr)
            sys.exit(1)

        rubric = rubrics.get(record_id)
        if rubric is None:
            print(f"FAIL CLOSED: manifest entry {record_id} has no matching private rubric entry.", file=sys.stderr)
            sys.exit(1)
        computed_pfp = pair_fingerprint(r["_input"], r["_output"])
        computed_rfp = rubric_fingerprint(rubric)

        try:
            rdm.verify_fingerprint(computed=computed_sfp, declared=entry["source_fingerprint"], field_name="source_fingerprint", record_id=record_id)
            rdm.verify_fingerprint(computed=computed_pfp, declared=entry["pair_fingerprint"], field_name="pair_fingerprint", record_id=record_id)
            rdm.verify_fingerprint(computed=computed_rfp, declared=entry["rubric_fingerprint"], field_name="rubric_fingerprint", record_id=record_id)
        except rdm.FingerprintMismatchError as e:
            print(f"FAIL CLOSED: {e}", file=sys.stderr)
            sys.exit(1)

        linked.append(
            {
                "record_id": record_id,
                "prompt": r["prompt"],
                "target": r["target"],
                "_input": r["_input"],
                "source_fingerprint": f"sha256:{computed_sfp}",
                "pair_fingerprint": f"sha256:{computed_pfp}",
                "rubric_fingerprint": f"sha256:{computed_rfp}",
            }
        )
    return linked


def main() -> None:
    cli_args = parse_args()
    try:
        _validate_identifier(cli_args.milestone, "--milestone")  # fail fast, before any generation work
    except UnsafeIdentifierError as e:
        print(f"FAIL CLOSED: {e}", file=sys.stderr)
        sys.exit(1)
    checkpoint_dir = Path(cli_args.checkpoint_dir)
    if not checkpoint_dir.is_dir():
        print(f"FAIL CLOSED: checkpoint directory does not exist: {checkpoint_dir}", file=sys.stderr)
        sys.exit(1)

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
