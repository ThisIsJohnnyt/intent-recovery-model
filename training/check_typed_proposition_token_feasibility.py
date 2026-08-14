"""Tokenizer-only feasibility gate for the typed-proposition static package.

Requires the project's existing transformers environment and cached pinned tokenizer. Loads no model and
performs no training, generation, inference, or benchmark work. Writes a receipt even when the gate fails.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "processed_gold_v1.2.2_typed_proposition_seed17_draft"
OUTPUT = ROOT / "controlled_seed17_typed_proposition_token_feasibility.json"
REVISION = "7bcac572ce56db69c1ea7c8af255c5d7c9672fc2"
MAX_INPUT = 512
MAX_TARGET = 512
MAX_GENERATED = 300


def stats(values: list[int]) -> dict:
    ordered = sorted(values)
    return {
        "min": ordered[0], "median": ordered[len(ordered) // 2], "max": ordered[-1],
        "over_512": sum(v > MAX_TARGET for v in values),
        "over_300": sum(v > MAX_GENERATED for v in values),
    }


def main() -> None:
    tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base", revision=REVISION, local_files_only=True)
    result = {"status": "pending", "tokenizer_revision": REVISION, "limits": {
        "input": MAX_INPUT, "target": MAX_TARGET, "generation_max_new_tokens": MAX_GENERATED}, "splits": {}}
    failed = False
    for split in ("train", "val"):
        path = DATA / f"{split}.jsonl"
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        inputs = [len(tokenizer(r["prompt"])["input_ids"]) for r in rows]
        targets = [len(tokenizer(r["target"])["input_ids"]) for r in rows]
        over_target = [{"row_index_zero_based": i, "tokens": n} for i, n in enumerate(targets) if n > MAX_TARGET]
        over_generation = [{"row_index_zero_based": i, "tokens": n} for i, n in enumerate(targets) if n > MAX_GENERATED]
        result["splits"][split] = {"count": len(rows), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                    "input_tokens": stats(inputs), "target_tokens": stats(targets),
                                    "target_limit_failures": over_target, "generation_limit_failures": over_generation}
        failed |= any(n > MAX_INPUT for n in inputs) or bool(over_target) or bool(over_generation)
    result["status"] = "FAIL_HARD_STOP" if failed else "PASS"
    result["compute_authorized"] = False
    result["required_disposition"] = (
        "Return to Johnny. Do not compress, omit, raise limits, change schedule, or continue implementation under this proposal."
        if failed else "Eligible for remaining static review gates only; compute remains unauthorized."
    )
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    if failed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
