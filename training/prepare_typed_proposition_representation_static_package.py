"""Prepare the no-compute typed-proposition milestone-1 review package.

The script reads the committed 78-record comparator and its frozen split. It never invokes a model,
benchmark, scorer, trainer, or network resource. Semantic plans are conservative target-grounded draft
annotations and require independent record-by-record review before they may be frozen.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from prompt_contract_v2_candidate import build_prompt
from prompt_contract_v2_migrate import build_v2_target
from typed_proposition_plan import parse_typed_output, serialize_plan

ROOT = Path(__file__).resolve().parent
CORPUS = ROOT / "gold_v1.2.2_phase2_derived_candidate.jsonl"
OLD_DATA = ROOT / "data" / "processed_gold_v1.2.2_phase2_v2contract_seed17"
PLAN_PATH = ROOT / "controlled_seed17_typed_proposition_plans_draft.jsonl"
NEW_DATA = ROOT / "data" / "processed_gold_v1.2.2_typed_proposition_seed17_draft"
RECEIPT = ROOT / "controlled_seed17_typed_proposition_static_package_receipt.json"

EXPECTED_CORPUS_SHA = "6e9e5f1bea8fc3cbcb615376a1d055bd273605d0f8c1e40a8c120720c8cb836c"
TREATMENT_INSTRUCTION = (
    "First emit a source-grounded typed proposition plan using the frozen proposition markers and schema. "
    "Then emit ###RENDERED_OUTPUT### followed by the ordinary v2 response. Do not infer missing referents, "
    "answers, causes, chronology, or tasks."
)

QUESTION = re.compile(r"\b(?:unresolved|unclear|unknown|unsure|uncertain|whether|question|did |what |if )\b", re.I)
FRAGMENT = re.compile(r"\b(?:unfinished|incomplete|left unfinished|not sure what)\b", re.I)
IDEA = re.compile(r"\b(?:idea|maybe|may |might |perhaps|consider|possible|could|what if)\b", re.I)
TIME = re.compile(r"\b(?:today|tonight|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|noon|\d+\s*(?:am|pm)|before|after|when|while|until|by )\b", re.I)
PLACE = re.compile(r"\b(?:to|into|in|on|at|beside|under|near)\s+(?:the|a|an|her|him|them|[A-Z])", re.I)
NUMBER = re.compile(r"\b(?:one|two|three|four|five|six|seven|eight|\d+)\b", re.I)

# Exact record/prop overrides carry the high-risk distinctions identified by the audit.
OVERRIDES: dict[tuple[int, int], dict] = {
    (42, 2): {"state": "tentative_idea"},
    (42, 4): {"state": "task", "fields": ["narrative", "bullet", "action"]},
    (48, 1): {"roles": "actor=Marcus; speaker=Rina", "coreference": "resolved:Marcus"},
    (48, 3): {"roles": "candidate_set=Marcus|client", "coreference": "unresolved:Marcus|client"},
    (48, 4): {"state": "task", "roles": "actor=writer; recipient=Rina", "fields": ["narrative", "bullet", "action"]},
    (53, 2): {"state": "fact", "roles": "object=kitchen sink"},
    (53, 3): {"state": "fact", "roles": "experiencer=writer"},
    (54, 2): {"state": "tentative_idea"},
    (54, 3): {"state": "question"},
    (56, 1): {"state": "task", "coreference": "dangling", "fields": ["narrative", "bullet", "action"]},
    (69, 1): {"state": "task", "fields": ["narrative", "bullet", "action"]},
    (70, 1): {"state": "task", "fields": ["narrative", "bullet", "action"]},
    (74, 1): {"state": "task", "fields": ["narrative", "bullet", "action"]},
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_lf_sha(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r\r\n" in raw:
        raise SystemExit(f"{path}: invalid BOM or malformed line endings")
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def normalize(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in {"the", "a", "an", "to", "and", "of", "is", "be"}}


def state_for(bullet: str, task_bullet: bool) -> str:
    if task_bullet:
        return "task"
    if FRAGMENT.search(bullet):
        return "fragment"
    if QUESTION.search(bullet):
        return "question"
    if IDEA.search(bullet):
        return "tentative_idea"
    return "fact"


def qualifiers(text: str) -> str:
    pairs = []
    if TIME.search(text): pairs.append(("time", TIME.search(text).group(0).strip()))
    if PLACE.search(text): pairs.append(("destination", PLACE.search(text).group(0).strip()))
    if NUMBER.search(text): pairs.append(("quantity", NUMBER.search(text).group(0).strip()))
    return "; ".join(f"{k}={v}" for k, v in sorted(pairs)) or "none"


def draft_plan(record_number: int, record: dict) -> list[dict]:
    bullets = record["output"]["bullets"]
    actions = record["output"]["action_items"]
    # Establish one-to-one action identity by greedily taking the strongest unused target-bullet match.
    # This is target-grounded scaffolding, not a semantic reviewer: weak/unmatched actions become their own
    # proposition and every row remains pending independent human review.
    task_bullets: set[int] = set()
    unmatched_actions = []
    for action in actions:
        a = normalize(action)
        candidates = []
        for i, bullet in enumerate(bullets):
            if i in task_bullets:
                continue
            b = normalize(bullet)
            score = len(a & b) / max(1, len(a | b))
            candidates.append((score, i))
        best = max(candidates, default=(0.0, -1))
        if best[0] >= 0.25:
            task_bullets.add(best[1])
        else:
            unmatched_actions.append(action)
    plan = []
    for index, bullet in enumerate(bullets, 1):
        state = state_for(bullet, index - 1 in task_bullets)
        fields = ["narrative", "bullet"] + (["action"] if state == "task" else [])
        item = {
            "id": f"p{index:02d}", "state": state, "predicate": bullet,
            "roles": "none", "qualifiers": qualifiers(bullet), "coreference": "none",
            "duplicate_of": "none", "fields": fields,
        }
        item.update(OVERRIDES.get((record_number, index), {}))
        plan.append(item)
    # Every action must have a proposition. Add an explicit target-grounded task if lexical alignment missed it.
    for action in unmatched_actions:
        plan.append({"id": f"p{len(plan)+1:02d}", "state": "task", "predicate": action,
                     "roles": "none", "qualifiers": qualifiers(action), "coreference": "none",
                     "duplicate_of": "none", "fields": ["narrative", "action"]})
    return plan


def treatment_prompt(raw_input: str) -> str:
    return build_prompt(raw_input) + "\n\n" + TREATMENT_INSTRUCTION


def main() -> None:
    if canonical_lf_sha(CORPUS) != EXPECTED_CORPUS_SHA:
        raise SystemExit("frozen comparator corpus fingerprint mismatch")
    records = [json.loads(x) for x in CORPUS.read_text(encoding="utf-8").splitlines()]
    if len(records) != 78:
        raise SystemExit("expected exactly 78 records")
    authored = []
    by_input = {}
    for n, record in enumerate(records, 1):
        rendered = build_v2_target(record["output"]["narrative"], record["output"]["bullets"], record["output"]["action_items"])
        plan = draft_plan(n, record)
        typed = serialize_plan(plan, rendered)
        parsed = parse_typed_output(typed)
        if parsed.rendered_text != rendered:
            raise SystemExit(f"record {n}: rendered suffix changed")
        entry = {"record_locator": f"comparator:{n:03d}", "input": record["input"], "plan": plan,
                 "rendered_v2_target": rendered, "typed_target": typed, "review_status": "chatgpt_draft_pending_claude_independent_review"}
        authored.append(entry)
        by_input[record["input"]] = entry
    PLAN_PATH.write_text("".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in authored), encoding="utf-8", newline="\n")

    NEW_DATA.mkdir(parents=True, exist_ok=True)
    split_receipt = {}
    for split in ("train", "val"):
        old = [json.loads(x) for x in (OLD_DATA / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()]
        out = []
        for pair in old:
            raw_input = next((r["input"] for r in records if build_prompt(r["input"]) == pair["prompt"]), None)
            if raw_input is None or raw_input not in by_input:
                raise SystemExit(f"{split}: prompt not traceable to frozen corpus")
            out.append({"prompt": treatment_prompt(raw_input), "target": by_input[raw_input]["typed_target"]})
        path = NEW_DATA / f"{split}.jsonl"
        path.write_text("".join(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n" for x in out), encoding="utf-8", newline="\n")
        split_receipt[split] = {"count": len(out), "sha256": sha(path)}
    receipt = {"status": "static_draft_no_compute", "corpus_canonical_lf_sha256": canonical_lf_sha(CORPUS), "plan_count": len(authored),
               "plans_sha256": sha(PLAN_PATH), "splits": split_receipt,
               "rendered_suffixes_byte_identical": True, "independent_review_complete": False,
               "compute_authorized": False}
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
