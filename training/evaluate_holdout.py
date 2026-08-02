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
in memory using a strict parser (rejects duplicate JSON object keys before
calling prepare_data.py's validate_record/build_prompt -- a last-write-wins
parse of a crafted duplicate key would be deterministic but not the
unambiguous input the private manifest's fingerprint was computed over)
-- never routes through a routinely materialized processed copy, and
writes no processed holdout file. --milestone is required; there is no
default, and this refuses to run without one.

Also requires an approved holdout-seal declaration for the given milestone
(real_data_manifest.load_approved_seal) before opening any holdout content
or loading a model. That mechanism is not built yet -- see
real_data_manifest_schema_decision.md's pilot-mode review -- so this
currently always fails closed regardless of what --milestone/--reason say;
a CLI string alone is not authorization to treat the validation-only
pilot's holdout restriction as lifted.

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
import sys
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

import real_data_manifest as rdm
from prepare_data import DATA_DIR, check_format_valid, load_jsonl_strict
from real_data_eval_logging import UnsafeIdentifierError, _validate_identifier, build_generation_artifact, new_generation_record, save_generation_artifact
from real_data_private import checkpoint_fingerprint, dataset_fingerprint, git_commit
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




def _link_to_manifest(holdout_records: list[dict]) -> list[dict]:
    """Thin wrapper around real_data_manifest.link_records_to_manifest
    (shared with evaluate_real_validation.py, so this fail-closed linking
    logic exists in exactly one place): translates its exceptions into
    this script's FAIL CLOSED + exit convention.

    Only reached after main() has already validated an approved holdout-seal
    declaration for this milestone (rdm.load_approved_seal) -- that check,
    not the pilot_mode=False passed below, is what authorizes reading
    holdout-eligible manifest entries during the pilot. pilot_mode=False
    here reflects that the seal check already did the authorizing; it does
    not itself authorize anything.
    """
    try:
        return rdm.link_records_to_manifest(holdout_records, expected_split="real_holdout", pilot_mode=False)
    except (rdm.ManifestValidationError, rdm.EligibilityError, rdm.RubricValidationError, rdm.FingerprintMismatchError) as e:
        print(f"FAIL CLOSED: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    cli_args = parse_args()
    try:
        _validate_identifier(cli_args.milestone, "--milestone")  # fail fast, before any generation work
    except UnsafeIdentifierError as e:
        print(f"FAIL CLOSED: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        rdm.load_approved_seal(cli_args.milestone)
    except rdm.SealNotApprovedError as e:
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
    try:
        holdout_records = load_jsonl_strict(holdout_path)
    except (ValueError, rdm.DuplicateJSONKeyError) as e:
        print(f"FAIL CLOSED: sealed holdout source failed strict parsing: {e}", file=sys.stderr)
        sys.exit(1)
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
        valid = check_format_valid(generated)
        results.append(
            new_generation_record(
                record_id=r["record_id"],
                source_fingerprint=r["source_fingerprint"],
                pair_fingerprint=r["pair_fingerprint"],
                rubric_fingerprint=r["rubric_fingerprint"],
                raw_output=generated,
                format_valid=valid,
            )
        )
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

    artifact = build_generation_artifact(
        split="real_holdout",
        evaluation_reason=cli_args.reason,
        git_commit=git_commit(),
        checkpoint={
            "path": str(checkpoint_dir),
            "fingerprint": ckpt_fp,
            "training_seed": cli_args.seed if cli_args.seed is not None else -1,
            "run_id": cli_args.run_id,
        },
        dataset={
            "fingerprint": ds_fp,
            "record_count": len(linked),
            "rubric_schema_version": "real-rubric-v1",
        },
        prompt_contract=None,  # cross-repository prompt-contract sync hasn't happened yet
        generation_config=generation_config,
        results=results,
        release_milestone=cli_args.milestone,
    )
    saved_path = save_generation_artifact(artifact)
    print(f"\nSaved structured generation artifact: {saved_path}")
    print(f"Format validity: {artifact['aggregate']['format_valid']}")
    print("This is a generation artifact only -- independent Claude/ChatGPT review, comparison, and adjudication artifacts are required before this can guide any decision.")


if __name__ == "__main__":
    main()
