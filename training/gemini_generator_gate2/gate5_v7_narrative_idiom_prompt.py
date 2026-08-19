"""Local-only V7 prompt scoping for narrative-idiom diversification.

This module cannot read credentials or send requests. It constructs inspectable
request envelopes while keeping the V1-V6 prompt and request pin immutable.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import gate2
import gate5_execution_gate as historical_gate
import gate5_redesign as redesign


PACKAGE = Path(__file__).resolve().parent
PROPOSAL_PATH = PACKAGE / "gate5_narrative_idiom_diversification_proposal.md"
HISTORICAL_SYSTEM_PATH = PACKAGE / "system_instruction.txt"
V7_SYSTEM_PATH = PACKAGE / "system_instruction_v7.txt"
EXPECTED_PROPOSAL_SHA256 = "8f90fb3d341a641a0d847dfeddd9e6fea3c7132906b60ab286a279584453b0bb"
EXPECTED_HISTORICAL_SYSTEM_SHA256 = "339b6f7841248ce40dcd925518cd6cea8fe5c069b2e9cf88b1ab75cbefe7e215"
EXPECTED_HISTORICAL_LIVE_REQUEST_SHA256 = "8420c2d8360f4ffc96fb617dd8d4b081732cf2c87654a65d3ddc2ab8426297b4"
EXPECTED_V7_SYSTEM_SHA256 = "9f67d86da8b53e605f6c93a5fac2a23af333382640aba04ecd5a3ada34d3c68c"
EXPECTED_LIVE_REQUEST_SHA256_V7 = "24dbeb008f4b2735d72ae0debe41729963e2adb3112cb1f9fb472120a63bfd94"
NARRATIVE_LINE = "- use narrative for contextual state, observations, uncertainty, and incomplete thoughts;"
DIVERSIFICATION_BULLET = (
    '- when narrative expresses an unresolved or ambiguous state, vary sentence structure and word choice each time rather than defaulting to a fixed opening '
    '(for example, avoid routinely starting with "It is unresolved whether" or "It remains unclear whether"); express the same required uncertainty in different, natural phrasings;'
)


class Gate5V7PromptError(RuntimeError):
    pass


def canonical_hash(path: Path) -> str:
    try:
        data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    except OSError as exc:
        raise Gate5V7PromptError("prompt artifact unavailable") from exc
    return gate2.sha256_bytes(data)


def load_v7_system_instruction() -> str:
    try:
        historical = HISTORICAL_SYSTEM_PATH.read_text(encoding="utf-8")
        revised = V7_SYSTEM_PATH.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise Gate5V7PromptError("prompt artifact unavailable") from exc
    if canonical_hash(PROPOSAL_PATH) != EXPECTED_PROPOSAL_SHA256:
        raise Gate5V7PromptError("proposal drifted")
    if canonical_hash(HISTORICAL_SYSTEM_PATH) != EXPECTED_HISTORICAL_SYSTEM_SHA256:
        raise Gate5V7PromptError("historical system instruction drifted")
    if canonical_hash(V7_SYSTEM_PATH) != EXPECTED_V7_SYSTEM_SHA256:
        raise Gate5V7PromptError("V7 system instruction drifted")
    marker = NARRATIVE_LINE + "\n"
    if historical.count(marker) != 1 or revised != historical.replace(marker, marker + DIVERSIFICATION_BULLET + "\n", 1):
        raise Gate5V7PromptError("V7 prompt is not the exact one-bullet revision")
    if gate2.contains_secret(revised):
        raise Gate5V7PromptError("secret-like value in V7 prompt")
    return revised


def historical_slot_one_request_hash() -> str:
    schedule = gate2.load_json(PACKAGE / "schedule.json")
    slots = schedule.get("slots") if isinstance(schedule, dict) else None
    if not isinstance(slots, list) or len(slots) != 24:
        raise Gate5V7PromptError("frozen schedule unavailable")
    value = gate2.sha256_bytes(gate2.canonical_json_bytes(redesign.build_request(slots[0])))
    if historical_gate.EXPECTED_LIVE_REQUEST_SHA256 != EXPECTED_HISTORICAL_LIVE_REQUEST_SHA256 or value != EXPECTED_HISTORICAL_LIVE_REQUEST_SHA256:
        raise Gate5V7PromptError("historical request pin drifted")
    return value


def build_request(slot: dict[str, Any]) -> dict[str, Any]:
    request = copy.deepcopy(redesign.build_request(slot))
    request["body"]["systemInstruction"]["parts"][0]["text"] = load_v7_system_instruction()
    redesign.validate_request(request)
    return request


def verify_only() -> dict[str, Any]:
    historical_hash = historical_slot_one_request_hash()
    schedule = gate2.load_json(PACKAGE / "schedule.json")
    requests = [build_request(slot) for slot in schedule["slots"]]
    envelope_hashes = [gate2.sha256_bytes(gate2.canonical_json_bytes(item)) for item in requests]
    body_hashes = [gate2.sha256_bytes(gate2.canonical_json_bytes(item["body"])) for item in requests]
    if envelope_hashes[0] != EXPECTED_LIVE_REQUEST_SHA256_V7 or len(set(envelope_hashes)) != 24 or len(set(body_hashes)) != 12:
        raise Gate5V7PromptError("V7 request pin or schedule cardinality invalid")
    return {
        "artifact": "gemini_generator_gate5_v7_narrative_idiom_prompt_verify_only",
        "proposal_sha256": EXPECTED_PROPOSAL_SHA256,
        "historical_system_instruction_sha256": EXPECTED_HISTORICAL_SYSTEM_SHA256,
        "historical_slot_one_request_sha256": historical_hash,
        "v7_system_instruction_sha256": EXPECTED_V7_SYSTEM_SHA256,
        "v7_slot_one_request_sha256": EXPECTED_LIVE_REQUEST_SHA256_V7,
        "request_count": len(requests),
        "unique_request_count": len(set(envelope_hashes)),
        "network_used": False,
        "credential_read": False,
        "file_output_created": False,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(verify_only(), sort_keys=True))
