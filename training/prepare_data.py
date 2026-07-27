"""Validate raw JSONL examples and build the train/val/eval splits train.py reads.

Usage:
    python prepare_data.py

Reads training/data/synthetic.jsonl (trained on) and training/data/real_holdout.jsonl
(held out, eval only) and writes training/data/processed/{train,val,real_eval}.jsonl,
each record shaped {"prompt": ..., "target": ...} ready for tokenization.
"""
import json
import random
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"
VAL_FRACTION = 0.1
SEED = 42

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


def main() -> None:
    synthetic_path = DATA_DIR / "synthetic.jsonl"
    holdout_path = DATA_DIR / "real_holdout.jsonl"

    synthetic = load_jsonl(synthetic_path)
    real_holdout = load_jsonl(holdout_path)

    if not synthetic:
        print(
            f"No usable examples found in {synthetic_path}.\n"
            f"See training/DATASET_SPEC.md for the format and the ChatGPT prompt to generate examples.",
            file=sys.stderr,
        )
        sys.exit(1)

    random.Random(SEED).shuffle(synthetic)
    val_size = max(1, int(len(synthetic) * VAL_FRACTION))
    val_split = synthetic[:val_size]
    train_split = synthetic[val_size:]

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    def write(name: str, records: list[dict]) -> None:
        path = PROCESSED_DIR / name
        with path.open("w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{path}: {len(records)} examples")

    write("train.jsonl", train_split)
    write("val.jsonl", val_split)
    write("real_eval.jsonl", real_holdout)

    if not real_holdout:
        print(
            f"Note: {holdout_path} is empty. Add some of your real notes there "
            "(same format) to evaluate how well synthetic-only training generalizes.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
