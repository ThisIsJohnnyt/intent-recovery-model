"""Structured private real-validation evaluator, per
training/real_data_scoring_lineage_withdrawal_design.md's implementation
order item 5 (replaces train.py's previous format-only real_validation
path, which called the same generic evaluate_format_validity used for the
synthetic val split and produced no structured artifact at all).

Runs automatically after every training run (see DATASET_SPEC.md) --
routine development-time evidence collection, not a declared release
milestone, so this has no --milestone/seal gate the way evaluate_holdout.py
does. It still fails closed on any unconsented, ineligible, or
tampered/stale real_validation record, using the same
real_data_manifest.link_records_to_manifest linking as evaluate_holdout.py,
and produces the same real-eval-generation-v1 generation artifact -- no
semantic scores, no review status. Independent review, comparison, and
adjudication happen afterward as separate artifacts (see
real_data_lineage.py), not as part of this routine run.
"""
import sys

import real_data_manifest as rdm
from prepare_data import DATA_DIR, check_format_valid, load_jsonl_strict
from real_data_eval_logging import build_generation_artifact, new_generation_record, save_generation_artifact
from real_data_private import dataset_fingerprint


def run_real_validation_evaluation(*, model, tokenizer, device, checkpoint_dir, checkpoint_fingerprint_value: str, git_commit: str, seed: int, run_id: str, generation_max_new_tokens: int) -> dict | None:
    """Returns the saved generation artifact, or None if
    real_validation.jsonl is empty (routine and expected until the
    validation-only pilot is approved and populated)."""
    validation_path = DATA_DIR / "real_validation.jsonl"
    if not validation_path.exists() or not validation_path.read_text(encoding="utf-8").strip():
        print(
            f"\n(no {validation_path.name} examples yet -- do not populate it directly. "
            "Real notes require consent, de-identification, and a private manifest "
            "entry before they may be added; see docs/decisions/PDR-005.md and "
            "datasets/REAL_DATA_GOVERNANCE.md.)"
        )
        return None

    try:
        records = load_jsonl_strict(validation_path)
    except ValueError as e:
        print(f"FAIL CLOSED: real_validation source failed strict parsing: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        linked = rdm.link_records_to_manifest(records, expected_split="real_validation", pilot_mode=True)
    except (rdm.ManifestValidationError, rdm.EligibilityError, rdm.RubricValidationError, rdm.FingerprintMismatchError) as e:
        print(f"FAIL CLOSED: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\n=== Structured real_validation evaluation ({len(linked)} example(s)) ===")
    results = []
    for r in linked:
        inputs = tokenizer(r["prompt"], return_tensors="pt", truncation=True, max_length=512).to(device)
        output_ids = model.generate(**inputs, max_new_tokens=generation_max_new_tokens, repetition_penalty=1.3)
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

    ds_fp = dataset_fingerprint(linked, "real_validation")
    artifact = build_generation_artifact(
        split="real_validation",
        evaluation_reason="routine post-training real_validation evaluation",
        git_commit=git_commit,
        checkpoint={
            "path": str(checkpoint_dir),
            "fingerprint": checkpoint_fingerprint_value,
            "training_seed": seed,
            "run_id": run_id,
        },
        dataset={
            "fingerprint": ds_fp,
            "record_count": len(linked),
            "rubric_schema_version": "real-rubric-v1",
        },
        prompt_contract=None,  # cross-repository prompt-contract sync hasn't happened yet
        generation_config={"max_new_tokens": generation_max_new_tokens, "repetition_penalty": 1.3},
        results=results,
    )
    saved_path = save_generation_artifact(artifact)
    print(f"Saved structured generation artifact: {saved_path}")
    print(f"Format validity: {artifact['aggregate']['format_valid']}")
    print("This is a generation artifact only -- independent Claude/ChatGPT review, comparison, and adjudication artifacts are required before this can guide any decision.")
    return artifact
