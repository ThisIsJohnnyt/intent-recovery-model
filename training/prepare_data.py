"""Validate raw JSONL examples and build the train/val/eval splits train.py reads.

Usage:
    python prepare_data.py

Reads datasets/synthetic.jsonl (trained on) and datasets/real_validation.jsonl
(held out, routine dev-eval), and writes
training/data/processed/{train,val,real_validation}.jsonl, each record shaped
{"prompt": ..., "target": ...} ready for tokenization.

Train/val membership for synthetic.jsonl comes from split_manifest.json, not a
random shuffle -- see that file's own description for why. Every example not
listed there defaults to train, so appending new Gold examples can never
silently move an existing example between train and val.

real_validation.jsonl and real_holdout.jsonl serve different roles -- see
docs/decisions/PDR-004.md and PDR-005.md. Routine development work
(checkpoint comparison, error analysis, curriculum decisions) should use
real_validation.jsonl. real_holdout.jsonl is reserved for declared release
milestones only and, per PDR-005's least-privilege requirement, is never
opened, validated, or copied here at all -- the separate
training/evaluate_holdout.py script loads it directly in memory, only when
explicitly invoked with a declared milestone. Neither file is ever written
into train.jsonl.
"""
import hashlib
import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "datasets"
PROCESSED_DIR = Path(__file__).parent / "data" / "processed"
SPLIT_MANIFEST_PATH = Path(__file__).parent / "split_manifest.json"

# Mirrors src/services/noteOrganizer.ts SYSTEM_PROMPT / USER_PROMPT_TEMPLATE
# exactly, so the model trains on the identical prompt shape it sees in
# production for the single-pass (non-chunked) path.
SYSTEM_PROMPT = (
    "You are a compassionate AI assistant helping someone organize scattered, "
    "fragmented thoughts written under real-world conditions like time "
    "pressure, interruption, or fatigue.\n\n"
    "The user has provided messy, non-linear thoughts below. Your job is to "
    "transform them into three clear, organized views that reduce anxiety "
    "and improve clarity."
)

# Plain delimited text, not JSON: testing showed a small model reliably gets
# the *content* right after fine-tuning, but frequently loses track of
# bracket/quote nesting on a JSON array (fails even on memorized training
# examples). Marker lines degrade gracefully instead of catastrophically.
NARRATIVE_MARKER = "###NARRATIVE###"
BULLETS_MARKER = "###BULLETS###"
ACTIONS_MARKER = "###ACTIONS###"

USER_PROMPT_TEMPLATE = (
    "Respond with exactly this format, using these three section markers "
    "each on their own line, with no other text before or after:\n\n"
    f"{NARRATIVE_MARKER}\n"
    "a coherent, flowing narrative that groups related ideas, keeps the "
    "original meaning and tone, and reads less anxiety-inducing than the "
    f"raw thoughts\n{BULLETS_MARKER}\n"
    "one key idea per line, 3 to 7 lines\n"
    f"{ACTIONS_MARKER}\n"
    "one task per line; leave this section empty if there are no tasks"
)


def build_prompt(raw_input: str) -> str:
    return f"{SYSTEM_PROMPT}\n\nUSER'S RAW THOUGHTS:\n{raw_input}\n\n{USER_PROMPT_TEMPLATE}"


def validate_record(record: dict, source: str, line_no: int) -> dict:
    if "input" not in record or not isinstance(record["input"], str) or not record["input"].strip():
        raise ValueError(f"{source}:{line_no}: missing/empty 'input' string")

    output = record.get("output")
    if not isinstance(output, dict):
        raise ValueError(f"{source}:{line_no}: missing 'output' object")

    narrative = output.get("narrative")
    if not isinstance(narrative, str) or not narrative.strip():
        raise ValueError(f"{source}:{line_no}: 'output.narrative' must be a non-empty string")

    bullets = output.get("bullets")
    if not isinstance(bullets, list) or not all(isinstance(b, str) for b in bullets):
        raise ValueError(f"{source}:{line_no}: 'output.bullets' must be a list of strings")

    action_items = output.get("action_items")
    if not isinstance(action_items, list) or not all(isinstance(a, str) for a in action_items):
        raise ValueError(f"{source}:{line_no}: 'output.action_items' must be a list of strings")

    target_lines = [NARRATIVE_MARKER, narrative.strip(), BULLETS_MARKER, *bullets, ACTIONS_MARKER, *action_items]
    return {
        "prompt": build_prompt(record["input"]),
        "target": "\n".join(target_lines),
        "_input": record["input"],
    }


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path.name}:{line_no}: invalid JSON ({e})") from e
            records.append(validate_record(raw, path.name, line_no))
    return records


def input_hash(raw_input: str) -> str:
    return hashlib.sha256(raw_input.encode("utf-8")).hexdigest()


def load_val_hashes(path: Path) -> set[str]:
    if not path.exists():
        raise SystemExit(
            f"Missing split manifest: {path}. Train/val membership for "
            "synthetic.jsonl is no longer computed by a random shuffle -- it "
            "must come from this file. See split_manifest.json's own "
            "description if it needs to be recreated."
        )
    manifest = json.loads(path.read_text(encoding="utf-8"))
    return {entry["input_sha256"] for entry in manifest["val"]}


def split_by_manifest(records: list[dict], val_hashes: set[str]) -> tuple[list[dict], list[dict]]:
    train_split, val_split = [], []
    seen_hashes = set()
    for record in records:
        h = input_hash(record["_input"])
        seen_hashes.add(h)
        (val_split if h in val_hashes else train_split).append(
            {k: v for k, v in record.items() if k != "_input"}
        )

    missing = val_hashes - seen_hashes
    if missing:
        raise SystemExit(
            f"split_manifest.json pins {len(missing)} val example(s) whose "
            f"input text no longer matches anything in datasets/synthetic.jsonl "
            f"(hash(es): {sorted(missing)}). An example was edited, renamed, or "
            "removed without updating the manifest -- val-set membership must "
            "stay frozen and explicit, not silently shrink. Fix the manifest or "
            "restore the example before proceeding."
        )
    return train_split, val_split


def main() -> None:
    synthetic_path = DATA_DIR / "synthetic.jsonl"
    validation_path = DATA_DIR / "real_validation.jsonl"

    synthetic = load_jsonl(synthetic_path)
    real_validation = load_jsonl(validation_path)

    if not synthetic:
        print(
            f"No usable examples found in {synthetic_path}.\n"
            f"See training/DATASET_SPEC.md for the format and the ChatGPT prompt to generate examples.",
            file=sys.stderr,
        )
        sys.exit(1)

    val_hashes = load_val_hashes(SPLIT_MANIFEST_PATH)
    train_split, val_split = split_by_manifest(synthetic, val_hashes)
    print(
        f"Split manifest ({SPLIT_MANIFEST_PATH.name}): {len(val_split)} example(s) "
        f"pinned to val, {len(train_split)} default to train."
    )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    def write(name: str, records: list[dict]) -> None:
        path = PROCESSED_DIR / name
        with path.open("w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{path}: {len(records)} examples")

    write("train.jsonl", train_split)
    write("val.jsonl", val_split)
    write("real_validation.jsonl", [{k: v for k, v in r.items() if k != "_input"} for r in real_validation])

    if not real_validation:
        print(
            f"Note: {validation_path} is empty. Add some of your real notes there "
            "(same format) for routine development-time evaluation.",
            file=sys.stderr,
        )

    print(
        "\n(datasets/real_holdout.jsonl is never opened here -- it's sealed for "
        "release milestones; evaluate_holdout.py loads it directly, in memory, "
        "only when explicitly invoked. See docs/decisions/PDR-005.md.)"
    )


if __name__ == "__main__":
    main()
