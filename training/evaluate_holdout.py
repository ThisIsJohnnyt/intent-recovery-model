"""Evaluate a checkpoint against the SEALED real_holdout.jsonl set.

Usage:
    python evaluate_holdout.py [checkpoint_dir]

This is deliberately a separate, explicit script -- NOT run automatically
by train.py. datasets/real_holdout.jsonl is reserved for declared release
milestones (see docs/decisions/PDR-004.md): it must not be consulted to
guide day-to-day development, curriculum authoring, seed selection, or
checkpoint tuning. Routine development-time evaluation against real notes
belongs in datasets/real_validation.jsonl instead, which train.py already
evaluates automatically after every run.

Before running this: confirm a release milestone has actually been
declared. If you're just curious how a checkpoint is doing, that's
exactly the temptation this file exists to resist -- use
real_validation.jsonl for that instead.
"""
import sys
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from train import DATA_DIR, OUTPUT_DIR, evaluate_format_validity, load_split


def main() -> None:
    checkpoint_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT_DIR / "final"
    holdout_path = DATA_DIR / "real_holdout_eval.jsonl"

    if not holdout_path.exists() or not holdout_path.read_text(encoding="utf-8").strip():
        print(
            f"{holdout_path} is empty -- nothing to evaluate. This is expected "
            "until a real release milestone calls for populating "
            "datasets/real_holdout.jsonl. See docs/decisions/PDR-004.md.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        "=== SEALED HOLDOUT EVALUATION ===\n"
        "This should only run at a declared release milestone. If that's not "
        "why you're running this, stop and use real_validation.jsonl instead.\n"
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    print(f"Checkpoint: {checkpoint_dir}")

    tokenizer = AutoTokenizer.from_pretrained(str(checkpoint_dir))
    model = AutoModelForSeq2SeqLM.from_pretrained(str(checkpoint_dir)).to(device)

    holdout_ds = load_split("real_holdout_eval.jsonl")
    evaluate_format_validity(model, tokenizer, device, "real_holdout", holdout_ds)


if __name__ == "__main__":
    main()
