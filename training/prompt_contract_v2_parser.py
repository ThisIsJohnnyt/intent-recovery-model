"""Candidate vNext output parser -- fail-closed structural parsing for the
typed-item-marker contract in prompt_contract_v2_candidate.py.

Not wired into any live pipeline. Companion to that module for the static
feasibility package (training/prompt_contract_vnext_joint_alignment_review.md).

Every failure mode listed in the vNext decision proposal's Gate 5 raises
ParseError with a specific reason rather than silently guessing:
missing/duplicated/reordered/cross-section markers, empty required
sections, empty items, and text outside the contract.
"""
from dataclasses import dataclass, field

from prompt_contract_v2_candidate import (
    ACTION_ITEM_MARKER,
    ACTIONS_MARKER,
    BULLET_ITEM_MARKER,
    BULLETS_MARKER,
    NARRATIVE_MARKER,
)


# Bumped only if parse_output's structural rules change in a way that could
# alter parsing results for previously-valid input. Stored per-result by
# run_benchmark.py's v2 path and independently re-verified by
# report_benchmark.py's structural-integrity check, so a parser change
# between generation and reporting can't silently go undetected (per
# prompt_contract_vnext_adapter_structural_implementation_review.md's
# Finding 2, "parser version/binding").
PARSER_VERSION = "v2-candidate-parser-1"


class ParseError(ValueError):
    pass


@dataclass
class ParsedOutput:
    narrative: str
    bullets: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)


def _require_single(text: str, marker: str) -> int:
    count = text.count(marker)
    if count == 0:
        raise ParseError(f"missing required marker: {marker}")
    if count > 1:
        raise ParseError(f"duplicated marker (expected exactly once): {marker}")
    return text.index(marker)


def _split_items(section_text: str, item_marker: str, other_item_marker: str, section_name: str) -> list[str]:
    if other_item_marker in section_text:
        raise ParseError(
            f"cross-section leakage: {other_item_marker} found inside the {section_name} section"
        )
    if item_marker not in section_text:
        if section_text.strip():
            raise ParseError(
                f"{section_name} section has content but no {item_marker} markers "
                f"(malformed -- content must be wrapped in item markers, not left bare)"
            )
        return []
    parts = section_text.split(item_marker)
    preamble = parts[0]
    if preamble.strip():
        raise ParseError(
            f"unexpected text before the first {item_marker} in the {section_name} section: {preamble!r}"
        )
    items = []
    for raw_item in parts[1:]:
        item = raw_item.strip()
        if not item:
            raise ParseError(f"empty {item_marker} item in the {section_name} section")
        items.append(item)
    return items


def parse_output(decoded_text: str) -> ParsedOutput:
    """Fail-closed parse of a fully-decoded model output string under the
    v2-candidate contract. Raises ParseError on any structural violation
    rather than returning a best-effort guess."""
    narrative_pos = _require_single(decoded_text, NARRATIVE_MARKER)
    bullets_pos = _require_single(decoded_text, BULLETS_MARKER)
    actions_pos = _require_single(decoded_text, ACTIONS_MARKER)

    if not (narrative_pos < bullets_pos < actions_pos):
        raise ParseError(
            "section markers out of order "
            f"(narrative={narrative_pos}, bullets={bullets_pos}, actions={actions_pos})"
        )

    preamble = decoded_text[:narrative_pos]
    if preamble.strip():
        raise ParseError(f"unexpected text before {NARRATIVE_MARKER}: {preamble!r}")

    narrative_text = decoded_text[narrative_pos + len(NARRATIVE_MARKER) : bullets_pos].strip()
    if not narrative_text:
        raise ParseError("narrative section is empty")

    bullets_section = decoded_text[bullets_pos + len(BULLETS_MARKER) : actions_pos]
    bullets = _split_items(bullets_section, BULLET_ITEM_MARKER, ACTION_ITEM_MARKER, "bullets")

    actions_section = decoded_text[actions_pos + len(ACTIONS_MARKER) :]
    actions = _split_items(actions_section, ACTION_ITEM_MARKER, BULLET_ITEM_MARKER, "actions")

    return ParsedOutput(narrative=narrative_text, bullets=bullets, actions=actions)
