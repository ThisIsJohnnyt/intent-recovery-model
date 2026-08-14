"""Build the authorized ten-record compact-representation feasibility pilot."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from compact_typed_plan import parse_compact_output, serialize_compact
from prompt_contract_v2_candidate import build_prompt
from prompt_contract_v2_migrate import build_v2_target

ROOT = Path(__file__).resolve().parent
CORPUS = ROOT / "gold_v1.2.2_phase2_derived_candidate.jsonl"
OUTPUT = ROOT / "controlled_seed17_compact_typed_representation_pilot.jsonl"
RECEIPT = ROOT / "controlled_seed17_compact_typed_representation_pilot_receipt.json"
LOCATORS = (7, 40, 42, 48, 53, 54, 56, 69, 74, 75)
CORPUS_SHA = "6e9e5f1bea8fc3cbcb615376a1d055bd273605d0f8c1e40a8c120720c8cb836c"

PROMPT_SUFFIX = (
    "\n\nBefore the ordinary v2 response, emit @P then one compact proposition per line, then @O. "
    "Format: id+state|predicate field ref|N[,B#][,A#][|R:roles][|Q:qualifiers][|C:coref][|D:id]. "
    "States F/Q/G/I/T mean fact/question/fragment/idea/task. Preserve source structure; do not infer."
)

# Authored from committed comparator source/targets. Predicate and field pointers resolve against the
# unchanged rendered v2 suffix, avoiding duplicated natural-language predicate text.
PLANS = {
  7: ["1T|B1|N,B1,A1", "2I|B2|N,B2", "3F|B3|N,B3", "4T|B4|N,B4,A3", "5T|A2|N,A2"],
  40: ["1T|B1|N,B1,A1|Q:tm=3pm", "2T|B2|N,B2,A2", "3F|B3|N,B3|R:e=writer", "4F|B4|N,B4", "5Q|B5|N,B5|Q:tm=Thursday/Friday", "6T|A3|N,A3", "7T|A4|N,A4"],
  42: ["1F|B1|N,B1", "2I|B2|N,B2", "3F|B3|N,B3|Q:qt=ten_minutes", "4T|B4|N,B4,A1|R:r=Nora,o=attendance_sheet"],
  48: ["1F|B1|N,B1|R:s=Rina,r=Marcus|C:r=Marcus", "2F|B2|N,B2|R:a=Marcus", "3Q|B3|N,B3|R:c=Marcus/client,o=signed_copy|C:u=Marcus/client", "4T|B4|N,B4,A1|R:r=Rina,o=who_needs_copy"],
  53: ["1T|B1|N,B1,A1|Q:dl=before_Friday", "2F|B2|N,B2|R:o=kitchen_sink", "3F|B3|N,B3|R:e=writer", "4T|B4|N,B4,A2|R:r=Bea|Q:tm=ten_minutes_late"],
  54: ["1F|B1|N,B1", "2I|B2|N,B2", "3Q|B3|N,B3|R:a=Chris,r=Dana,o=access_list", "4T|B4|N,B4,A1|R:o=dentist", "5F|B5|N,B5", "6T|B6|N,B6,A2|R:o=porch_bulb"],
  56: ["1T|B1|N,B1,A1|R:r=unknown,o=earlier_version|C:d"],
  69: ["1T|B1|N,B1,A1|R:o=damage_claim|Q:dl=before_Friday"],
  74: ["1T|B1|N,B1,A1", "2T|B2|N,B2,A2", "3T|B3|N,B3,A3", "4T|A4|N,A4", "5T|B4|N,B4,A5", "6T|B5|N,B5,A6", "7T|B6|N,B6,A7|Q:ds=freezer_containers", "8T|B7|N,B7,A8|Q:tr=before_pickup"],
  75: ["1T|B1|N,B1,A1|Q:tr=before_doors_unlock", "2T|B2|N,B2,A2|Q:tr=before_doors_unlock", "3Q|B3|N,B3|R:o=west_window", "4F|B4|N,B4|Q:tm=after_setup", "5I|B5|N,B5|Q:ds=near_exit", "6F|B6|N,B6|R:s=Ren,a=Salma,r=installation_lead,o=spare_clips"],
}


def canonical_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> None:
    if canonical_sha(CORPUS) != CORPUS_SHA:
        raise SystemExit("frozen corpus fingerprint mismatch")
    records = [json.loads(x) for x in CORPUS.read_text(encoding="utf-8").splitlines()]
    rows = []
    for n in LOCATORS:
        r = records[n - 1]
        rendered = build_v2_target(r["output"]["narrative"], r["output"]["bullets"], r["output"]["action_items"])
        target = serialize_compact(PLANS[n], rendered)
        parsed = parse_compact_output(target)
        if parsed.rendered_text != rendered:
            raise SystemExit(f"comparator:{n:03d}: rendered suffix changed")
        rows.append({"record_locator": f"comparator:{n:03d}", "source_input": r["input"],
                     "prompt": build_prompt(r["input"]) + PROMPT_SUFFIX, "plan_lines": PLANS[n],
                     "rendered_v2_target": rendered, "compact_target": target,
                     "review_status": "chatgpt_authored_pending_claude_independent_review"})
    OUTPUT.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8", newline="\n")
    receipt = {"status": "static_pilot_no_compute", "frozen_locators": [f"comparator:{n:03d}" for n in LOCATORS],
               "record_count": len(rows), "corpus_canonical_lf_sha256": canonical_sha(CORPUS),
               "pilot_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
               "round_trip_passed": True, "rendered_suffixes_byte_identical": True,
               "independent_review_complete": False, "compute_authorized": False}
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__": main()
