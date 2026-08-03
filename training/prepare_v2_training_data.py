"""Build v2-serialized training data for the seed-17 v2 representation
study authorized 2026-08-03 (Johnny, with ChatGPT's prior alignment on the
frozen static package -- see
source_determined_items_v2_gold_targets_chatgpt_handoff.md and
training/source_determined_items_v2_gold_targets_claude_review.md).

Usage:
    python prepare_v2_training_data.py [--output-dir DIR]

Reads prompt_contract_v2_migrated_targets_DRAFT.jsonl -- the ALREADY
migrated and verified 66-example corpus (built by
prompt_contract_v2_migrate.py, pinned to commit 8d7aa09, confirmed 66/66
exact parse_output() equality earlier this session) -- NOT the live
datasets/synthetic.jsonl, which as of this study has 6 additional
uncommitted examples from an unrelated gold_v1.2.3 effort. Using the live
file here would silently grow the corpus past 66 and violate the
authorization's explicit "mechanically migrated 66-example corpus only,
no corrective curriculum examples."

Splits by the existing frozen split_manifest.json (same 60/6 train/val
membership prepare_data.py itself uses for the v1 corpus -- reused
directly via prepare_data.input_hash/load_val_hashes, not re-derived), so
this study evaluates the identical split under a different serialization,
not a different split. Each record becomes {"prompt": <v2 build_prompt
applied to the original input>, "target": <the already-migrated,
already-verified v2_target>} -- ready for train.py --data-dir <output-dir>
unchanged; no modification to train.py itself.
"""
import argparse
import json
from pathlib import Path

from prepare_data import SPLIT_MANIFEST_PATH, input_hash, load_val_hashes
import prompt_contract_v2_candidate as v2_candidate
from prompt_contract_v2_parser import ParseError, parse_output

TRAINING_DIR = Path(__file__).parent
MIGRATED_TARGETS_PATH = TRAINING_DIR / "prompt_contract_v2_migrated_targets_DRAFT.jsonl"
DEFAULT_OUTPUT_DIR = TRAINING_DIR / "data" / "processed_gold_v1.2.2_v2contract_seed17"
EXPECTED_RECORD_COUNT = 66


def load_migrated_targets(path: Path = MIGRATED_TARGETS_PATH) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_v2_train_val_split(records: list[dict], val_hashes: set[str]) -> tuple[list[dict], list[dict]]:
    train_split: list[dict] = []
    val_split: list[dict] = []
    seen_hashes: set[str] = set()
    for record in records:
        h = input_hash(record["input"])
        seen_hashes.add(h)
        pair = {
            "prompt": v2_candidate.build_prompt(record["input"]),
            "target": record["v2_target"],
        }
        (val_split if h in val_hashes else train_split).append(pair)

    missing = val_hashes - seen_hashes
    if missing:
        raise SystemExit(
            f"split_manifest.json pins {len(missing)} val example(s) whose input hash "
            f"is not present in the migrated-targets corpus: {sorted(missing)}. The "
            "migrated corpus is supposed to be the exact same 66 examples the split "
            "manifest was built against -- refusing to proceed with a mismatched corpus."
        )
    return train_split, val_split


def verify_every_target_parses_and_matches_output(records: list[dict]) -> None:
    """Re-verifies prompt_contract_v2_migrate.py's own 66/66 claim once
    more, immediately before this specific corpus is committed to a real
    training run -- cheap insurance against the migrated-targets file
    having drifted or been hand-edited since that verification last ran."""
    mismatches = []
    for r in records:
        try:
            parsed = parse_output(r["v2_target"])
        except ParseError as e:
            mismatches.append((r["input"][:40], f"does not parse: {e}"))
            continue
        output = r["output"]
        if parsed.narrative != output["narrative"].strip():
            mismatches.append((r["input"][:40], "narrative mismatch"))
        if parsed.bullets != output["bullets"]:
            mismatches.append((r["input"][:40], "bullets mismatch"))
        if parsed.actions != output["action_items"]:
            mismatches.append((r["input"][:40], "actions mismatch"))
    if mismatches:
        raise SystemExit(f"{len(mismatches)} mismatch(es) re-verifying migrated targets: {mismatches}")
    print(f"Re-verified: all {len(records)} migrated v2_target values parse and match their 'output' exactly.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=str, default=None, help="Overrides the default processed-data output dir")
    args = parser.parse_args()
    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR

    records = load_migrated_targets()
    if len(records) != EXPECTED_RECORD_COUNT:
        raise SystemExit(
            f"Expected exactly {EXPECTED_RECORD_COUNT} migrated records in "
            f"{MIGRATED_TARGETS_PATH.name}, got {len(records)} -- refusing to proceed "
            "with an unexpected corpus size."
        )

    verify_every_target_parses_and_matches_output(records)

    val_hashes = load_val_hashes(SPLIT_MANIFEST_PATH)
    train_split, val_split = build_v2_train_val_split(records, val_hashes)
    print(
        f"Split manifest ({SPLIT_MANIFEST_PATH.name}): {len(val_split)} example(s) "
        f"pinned to val, {len(train_split)} default to train (of {EXPECTED_RECORD_COUNT} total)."
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    def write(name: str, recs: list[dict]) -> None:
        path = output_dir / name
        with path.open("w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{path}: {len(recs)} examples")

    write("train.jsonl", train_split)
    write("val.jsonl", val_split)
    print(f"\nWrote v2-serialized train/val data to {output_dir}")
    print(
        "(datasets/real_validation.jsonl is handled separately by "
        "evaluate_real_validation.py directly, independent of --data-dir, and is "
        "currently empty -- no file needed here for that.)"
    )


if __name__ == "__main__":
    main()
