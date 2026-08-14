"""Tokenizer-only measurement for the authorized compact pilot; no model load or execution."""

import hashlib
import json
from pathlib import Path

from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parent
PILOT = ROOT / "controlled_seed17_compact_typed_representation_pilot.jsonl"
OUTPUT = ROOT / "controlled_seed17_compact_typed_representation_token_receipt.json"
REVISION = "7bcac572ce56db69c1ea7c8af255c5d7c9672fc2"


def summary(values):
    x = sorted(values)
    return {"min": x[0], "median": x[len(x)//2], "max": x[-1]}


def main():
    tok = AutoTokenizer.from_pretrained("google/flan-t5-base", revision=REVISION, local_files_only=True)
    rows = [json.loads(x) for x in PILOT.read_text(encoding="utf-8").splitlines()]
    details = []
    for row in rows:
        prompt = len(tok(row["prompt"])["input_ids"])
        target = len(tok(row["compact_target"])["input_ids"])
        rendered = len(tok(row["rendered_v2_target"])["input_ids"])
        details.append({"record_locator": row["record_locator"], "prompt_tokens": prompt,
                        "compact_target_tokens": target, "rendered_v2_tokens": rendered,
                        "plan_overhead_tokens": target-rendered, "under_512_prompt": prompt <= 512,
                        "under_512_target": target <= 512, "under_300_generation": target <= 300,
                        "at_or_under_270_preferred": target <= 270})
    targets = [r["compact_target_tokens"] for r in details]
    result = {"status": "PASS_WITH_MARGIN" if max(targets) <= 270 else ("PASS_WITHOUT_PREFERRED_MARGIN" if max(targets) <= 300 else "FAIL"),
              "tokenizer_revision": REVISION, "pilot_sha256": hashlib.sha256(PILOT.read_bytes()).hexdigest(),
              "record_count": len(rows), "prompt_tokens": summary([r["prompt_tokens"] for r in details]),
              "target_tokens": summary(targets), "records_over_prompt_512": sum(not r["under_512_prompt"] for r in details),
              "records_over_target_512": sum(not r["under_512_target"] for r in details),
              "records_over_generation_300": sum(not r["under_300_generation"] for r in details),
              "records_over_preferred_270": sum(not r["at_or_under_270_preferred"] for r in details),
              "records": details, "model_loaded": False, "compute_authorized": False}
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    if result["status"] == "FAIL": raise SystemExit(2)


if __name__ == "__main__": main()
