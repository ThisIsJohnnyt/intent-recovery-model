"""Build the RBR17-C static record-to-mechanism map.

This script performs no model, benchmark, training, or corpus-generation work. It reads the frozen
78-record comparator and seven-record treatment proposal and emits an evidence map. Semantic judgments
remain explicit review annotations; deterministic extraction never substitutes for adjudication.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = (
    ("comparator", ROOT / "gold_v1.2.2_phase2_derived_candidate.jsonl", 78),
    ("treatment_delta", ROOT / "regression_balanced_repair_proposal.jsonl", 7),
)
OUTPUT = ROOT / "controlled_seed17_rbr17c_record_to_mechanism_map.jsonl"

MECHANISMS_BY_CATEGORY = {
    "multi_person_attribution": ["role_binding", "speaker_recipient_binding", "coreference"],
    "cross_field_completeness": ["cross_field_realization", "qualifier_binding"],
    "dangling_reference": ["unresolved_reference", "action_status"],
    "open_question_preservation": ["question_state", "non_resolution"],
    "repeated_reminder": ["semantic_identity", "deduplication"],
    "repeated_reminder_multi_topic": ["semantic_identity", "deduplication", "topic_separation"],
    "idea_action_boundary": ["tentative_idea_state", "action_suppression"],
    "task_plus_idea": ["tentative_idea_state", "task_state", "topic_separation"],
    "idea_among_tasks": ["tentative_idea_state", "task_state", "topic_separation"],
    "observation_plus_idea": ["fact_state", "tentative_idea_state", "action_suppression"],
    "zero_action_items": ["fact_state", "zero_action_policy"],
    "unfinished_reference": ["unresolved_reference", "qualifier_binding"],
    "interrupted_thought": ["fragment_state", "interruption_reconnection"],
    "interrupted_thought_depth": ["fragment_state", "interruption_reconnection", "topic_separation"],
    "interrupted_thought_multi_topic": ["fragment_state", "interruption_reconnection", "topic_separation"],
    "half_finished_thoughts": ["fragment_state", "non_completion"],
    "rapid_topic_switching_incomplete_sentences": ["fragment_state", "topic_separation", "action_status"],
    "unsupported_content_resistance": ["non_invention", "unresolved_reference", "action_status"],
    "buried_task_retention": ["task_state", "dense_composition", "cross_field_realization"],
    "maximum_interleaving": ["task_state", "dense_composition", "cross_field_realization"],
    "nested_boundary_depth": ["state_boundary", "topic_separation"],
    "standalone_task_retention": ["task_state", "experiencer_binding"],
}

QUESTION = re.compile(r"\?|\b(?:unclear|unknown|unsure|undecided|can't tell|cannot tell|whether|not sure)\b", re.I)
FRAGMENT_CATEGORIES = {k for k in MECHANISMS_BY_CATEGORY if "fragment_state" in MECHANISMS_BY_CATEGORY[k]}
TIME = re.compile(r"\b(?:before|after|when|while|until|by|tonight|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|noon|morning|bed|closes?|opens?|returns?|arrives?)\b", re.I)
DESTINATION = re.compile(r"\b(?:to|into|in|on|at|beside|under|near)\s+(?:the|a|an|her|him|them|[A-Z])", re.I)
QUANTITY = re.compile(r"\b(?:one|two|three|four|five|six|seven|eight|\d+)\b", re.I)
TENTATIVE = re.compile(r"\b(?:maybe|might|may|perhaps|idea|consider|what if|could)\b", re.I)

# Record-specific manual findings. These are auditable judgments, not inferred by the extractor.
MANUAL = {
    ("comparator", 16): {"review_notes": "Dangling question target preserves uncertainty and suppresses unsupported action; not the close imperative analogue."},
    ("comparator", 35): {"mechanisms_conflicted": ["action_status"], "review_notes": "Promotes overflowing-bin observation to an empty-bin action; policy conflict candidate requiring adjudication."},
    ("comparator", 42): {"protected_overlap": ["protected_10_close_analogue"], "review_notes": "Near-isomorphic buried print-task example; target retains observations and task across fields."},
    ("comparator", 48): {"protected_overlap": ["protected_06_close_analogue"], "review_notes": "Near-isomorphic protected-06 analogue with local resolution, later ambiguity, and clarification action."},
    ("comparator", 53): {"protected_overlap": ["protected_11_close_analogue"], "review_notes": "Near-isomorphic deadline, repeated task, object observation, writer emotion, and separate message task."},
    ("comparator", 54): {"protected_overlap": ["sdi2_10_dense_analogue"], "review_notes": "B6/A2 dense composition with idea, question, observations, and two tasks."},
    ("comparator", 56): {"protected_overlap": ["protected_16_close_analogue"], "review_notes": "Near-word-for-word dangling-reference imperative with unresolved references preserved."},
    ("comparator", 61): {"protected_overlap": ["protected_08_close_analogue"], "review_notes": "Direct toaster-or-kettle alternative plus later observation and separate task."},
    ("comparator", 69): {"protected_overlap": ["sdi2_07_close_analogue"], "review_notes": "Pure paraphrastic restatement target deduplicated to B1/A1."},
    ("comparator", 70): {"protected_overlap": ["sdi2_07_close_analogue"], "review_notes": "Second pure paraphrastic restatement target deduplicated to B1/A1."},
    ("comparator", 74): {"protected_overlap": ["sdi2_08_exact_structural_analogue"], "review_notes": "Exact B7/A8 analogue: eight source tasks, seven target bullets, and eight target actions."},
    ("comparator", 75): {"protected_overlap": ["sdi2_10_dense_analogue"], "review_notes": "B6/A2 dense composition with question, observation, tentative idea, attribution, and deadline."},
    ("comparator", 76): {"protected_overlap": ["sdi2_10_dense_analogue"], "review_notes": "B6/A2 dense composition with role binding, qualifiers, question, observation, and tentative idea."},
    ("treatment_delta", 2): {"protected_overlap": ["protected_06_close_analogue"], "review_notes": "Explicit ambiguity occurs on earlier follow-up pronoun; reordered protected-06 mechanism."},
    ("treatment_delta", 3): {"protected_overlap": ["protected_06_high_risk_analogue"], "review_notes": "Literal protected-06 skeleton: local resolution, later two-candidate ambiguity, clarification task."},
    ("treatment_delta", 7): {"protected_overlap": ["protected_16_close_analogue"], "review_notes": "Close dangling-reference/action skeleton; diagnostic evidence only."},
}


def qualifiers(text: str) -> list[str]:
    found = []
    if TIME.search(text):
        found.append("time_or_condition")
    if DESTINATION.search(text):
        found.append("destination_or_location")
    if QUANTITY.search(text):
        found.append("quantity")
    return found


def row(lineage: str, number: int, raw: str) -> dict:
    obj = json.loads(raw)
    output = obj["output"]
    narrative = output["narrative"]
    bullets = output["bullets"]
    actions = output["action_items"]
    target_text = " ".join([narrative, *bullets, *actions])
    category = obj["category"]
    mechanisms = set(MECHANISMS_BY_CATEGORY.get(category, ["task_state", "topic_separation"]))
    if QUESTION.search(obj["input"]):
        mechanisms.add("question_state")
    if TENTATIVE.search(obj["input"]):
        mechanisms.add("tentative_idea_state")
    if qualifiers(obj["input"]):
        mechanisms.add("qualifier_binding")
    if len(bullets) >= 5 or len(actions) >= 5:
        mechanisms.add("cardinality")
    manual = MANUAL.get((lineage, number), {})
    return {
        "lineage": lineage,
        "record_locator": f"{lineage}:{number:03d}",
        "record_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "category": category,
        "source_span": obj["input"],
        "exact_target_spans": {"narrative": narrative, "bullets": bullets, "action_items": actions},
        "states": {
            "fact": "positive" if len(bullets) > len(actions) else "not_present_or_unseparated",
            "question": "positive" if QUESTION.search(obj["input"]) and QUESTION.search(target_text) else ("unclear" if QUESTION.search(obj["input"]) else "not_present"),
            "fragment": "positive" if category in FRAGMENT_CATEGORIES else "not_present",
            "task": "positive" if actions else "not_present",
            "tentative_idea": "positive" if TENTATIVE.search(obj["input"]) and TENTATIVE.search(target_text) else ("unclear" if TENTATIVE.search(obj["input"]) else "not_present"),
        },
        "role_tuple": "present; inspect exact spans" if category == "multi_person_attribution" or re.search(r"\b(?:told|said|reported|gave|send|ask)\b", obj["input"], re.I) else "not_explicit",
        "qualifier_tuple": {"source_types": qualifiers(obj["input"]), "target_types": qualifiers(target_text)},
        "dedup_relation": "restatement_or_duplicate" if "repeated_reminder" in category else "not_declared",
        "bullet_count": len(bullets),
        "action_count": len(actions),
        "mechanisms_supported": sorted(mechanisms),
        "mechanisms_conflicted": manual.get("mechanisms_conflicted", []),
        "protected_overlap": manual.get("protected_overlap", []),
        "review_notes": manual.get("review_notes", "Exact source and all target fields preserved for manual adjudication."),
    }


def main() -> None:
    rows = []
    for lineage, path, expected in SOURCES:
        raw_lines = path.read_text(encoding="utf-8").splitlines()
        if len(raw_lines) != expected:
            raise SystemExit(f"{path}: expected {expected} records, found {len(raw_lines)}")
        rows.extend(row(lineage, i, raw) for i, raw in enumerate(raw_lines, 1))
    if len(rows) != 85 or len({r["record_sha256"] for r in rows}) != 85:
        raise SystemExit("map must contain 85 unique records")
    OUTPUT.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8", newline="\n")
    print(f"wrote {len(rows)} rows to {OUTPUT.name}")
    print(hashlib.sha256(OUTPUT.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
