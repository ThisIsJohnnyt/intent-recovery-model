"""Mock-only Gate 5 response validator; it cannot perform a provider request.

It exists to exercise the provisional GenerateContent response/usage contract with
fictional fixtures.  It imports no network or credential library and writes no
candidate, review, corpus, or paid-pilot artifact.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import gate2
import gate5_redesign as redesign


PACKAGE = Path(__file__).resolve().parent
FIXTURES_PATH = PACKAGE / "gate5_mock_provider_fixtures.json"
REQUIRED_USAGE_FIELDS = (
    "promptTokenCount",
    "candidatesTokenCount",
    "totalTokenCount",
)
OPTIONAL_COUNT_USAGE_FIELDS = ("thoughtsTokenCount",)
ZERO_ONLY_USAGE_FIELDS = ("cachedContentTokenCount", "toolUsePromptTokenCount")
DETAIL_USAGE_FIELDS = (
    "promptTokensDetails",
    "cacheTokensDetails",
    "candidatesTokensDetails",
    "toolUsePromptTokensDetails",
)
OPTIONAL_USAGE_FIELDS = set(OPTIONAL_COUNT_USAGE_FIELDS + ZERO_ONLY_USAGE_FIELDS + DETAIL_USAGE_FIELDS + ("serviceTier",))
MAX_THOUGHT_SIGNATURE_CODEPOINTS = 65_536
REQUIRED_RESPONSE_FIELDS = {"candidates", "modelVersion"}
OPTIONAL_RESPONSE_FIELDS = {"usageMetadata", "promptFeedback", "responseId", "modelStatus"}
REQUIRED_CANDIDATE_FIELDS = {"content", "finishReason"}
OPTIONAL_CANDIDATE_FIELDS = {
    "safetyRatings",
    "citationMetadata",
    "tokenCount",
    "groundingAttributions",
    "groundingMetadata",
    "avgLogprobs",
    "logprobsResult",
    "urlContextMetadata",
    "index",
    "finishMessage",
}


class Gate5MockError(RuntimeError):
    pass


def load_fixtures() -> dict[str, dict[str, Any]]:
    value = gate2.load_json(FIXTURES_PATH)
    if not isinstance(value, dict) or set(value) != {"artifact", "status", "fixtures"}:
        raise Gate5MockError("fixture manifest drifted")
    fixtures = value["fixtures"]
    if value["artifact"] != "gemini_generator_gate5_mock_provider_fixtures" or not isinstance(fixtures, list):
        raise Gate5MockError("fixture manifest invalid")
    result = {item.get("id"): item for item in fixtures if isinstance(item, dict) and isinstance(item.get("id"), str)}
    if set(result) != {"valid_stop_with_usage", "blocked_without_usage", "schema_invalid_before_usage"}:
        raise Gate5MockError("fixture set drifted")
    return result


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise Gate5MockError("duplicate JSON key")
        result[key] = value
    return result


def parse_usage(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        raise Gate5MockError("budget_or_usage_unknown")
    fields = set(value)
    if not set(REQUIRED_USAGE_FIELDS) <= fields or fields - set(REQUIRED_USAGE_FIELDS) - OPTIONAL_USAGE_FIELDS:
        raise Gate5MockError("budget_or_usage_unknown")
    if any(type(value[field]) is not int or value[field] < 0 for field in REQUIRED_USAGE_FIELDS):
        raise Gate5MockError("budget_or_usage_unknown")
    for field in OPTIONAL_COUNT_USAGE_FIELDS:
        if field in value and (type(value[field]) is not int or value[field] < 0):
            raise Gate5MockError("budget_or_usage_unknown")
    for field in DETAIL_USAGE_FIELDS:
        if field in value and (
            not isinstance(value[field], list) or any(not isinstance(item, dict) for item in value[field])
        ):
            raise Gate5MockError("budget_or_usage_unknown")
    if "serviceTier" in value and (not isinstance(value["serviceTier"], str) or not value["serviceTier"]):
        raise Gate5MockError("budget_or_usage_unknown")
    for field in ZERO_ONLY_USAGE_FIELDS:
        if field in value and (type(value[field]) is not int or value[field] < 0):
            raise Gate5MockError("budget_or_usage_unknown")
    if value.get("cachedContentTokenCount", 0) != 0:
        raise Gate5MockError("cached_usage_forbidden")
    if value.get("toolUsePromptTokenCount", 0) != 0:
        raise Gate5MockError("tool_usage_forbidden")
    usage = {field: value[field] for field in REQUIRED_USAGE_FIELDS}
    usage["thoughtsTokenCount"] = value.get("thoughtsTokenCount", 0)
    usage["cachedContentTokenCount"] = value.get("cachedContentTokenCount", 0)
    usage["toolUsePromptTokenCount"] = value.get("toolUsePromptTokenCount", 0)
    if usage["totalTokenCount"] < usage["promptTokenCount"] + usage["candidatesTokenCount"] + usage["thoughtsTokenCount"]:
        raise Gate5MockError("budget_or_usage_unknown")
    return usage


def parse_generate_content_response(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise Gate5MockError("provider_response_shape_invalid")
    response_fields = set(value)
    if not REQUIRED_RESPONSE_FIELDS <= response_fields or response_fields - REQUIRED_RESPONSE_FIELDS - OPTIONAL_RESPONSE_FIELDS:
        raise Gate5MockError("provider_response_shape_invalid")
    model_version = value["modelVersion"]
    candidates = value["candidates"]
    if not isinstance(model_version, str) or not model_version or not isinstance(candidates, list) or len(candidates) != 1:
        raise Gate5MockError("model_identity_or_candidate_count_invalid")
    if "responseId" in value and (not isinstance(value["responseId"], str) or not value["responseId"]):
        raise Gate5MockError("provider_response_shape_invalid")
    if "promptFeedback" in value and not isinstance(value["promptFeedback"], dict):
        raise Gate5MockError("provider_response_shape_invalid")
    if "modelStatus" in value:
        status = value["modelStatus"]
        if not isinstance(status, dict) or set(status) - {"modelStage", "retirementTime", "message"}:
            raise Gate5MockError("provider_response_shape_invalid")
        if status.get("modelStage") != "STABLE":
            raise Gate5MockError("model_status_unacceptable")
        if any(field in status and (not isinstance(status[field], str) or not status[field]) for field in ("retirementTime", "message")):
            raise Gate5MockError("provider_response_shape_invalid")
    candidate = candidates[0]
    if not isinstance(candidate, dict):
        raise Gate5MockError("provider_response_shape_invalid")
    candidate_fields = set(candidate)
    if not REQUIRED_CANDIDATE_FIELDS <= candidate_fields or candidate_fields - REQUIRED_CANDIDATE_FIELDS - OPTIONAL_CANDIDATE_FIELDS:
        raise Gate5MockError("provider_response_shape_invalid")
    if candidate["finishReason"] != "STOP":
        raise Gate5MockError("finish_reason_invalid")
    for field in ("safetyRatings", "groundingAttributions"):
        if field in candidate and (not isinstance(candidate[field], list) or any(not isinstance(item, dict) for item in candidate[field])):
            raise Gate5MockError("provider_response_shape_invalid")
    for field in ("citationMetadata", "logprobsResult"):
        if field in candidate and not isinstance(candidate[field], dict):
            raise Gate5MockError("provider_response_shape_invalid")
    for field in ("tokenCount", "index"):
        if field in candidate and (type(candidate[field]) is not int or candidate[field] < 0):
            raise Gate5MockError("provider_response_shape_invalid")
    if "avgLogprobs" in candidate and (type(candidate["avgLogprobs"]) not in (int, float)):
        raise Gate5MockError("provider_response_shape_invalid")
    if "finishMessage" in candidate and not isinstance(candidate["finishMessage"], str):
        raise Gate5MockError("provider_response_shape_invalid")
    if any(field in candidate for field in ("groundingAttributions", "groundingMetadata", "urlContextMetadata")):
        raise Gate5MockError("unapproved_retrieval_or_url_context")
    if "usageMetadata" not in value:
        raise Gate5MockError("budget_or_usage_unknown")
    content = candidate["content"]
    if not isinstance(content, dict) or set(content) != {"role", "parts"} or content["role"] != "model":
        raise Gate5MockError("provider_response_shape_invalid")
    parts = content["parts"]
    if not isinstance(parts, list) or len(parts) != 1 or not isinstance(parts[0], dict) or "text" not in parts[0] or set(parts[0]) - {"text", "thoughtSignature"}:
        raise Gate5MockError("provider_response_shape_invalid")
    text = parts[0]["text"]
    if not isinstance(text, str):
        raise Gate5MockError("provider_response_shape_invalid")
    if "thoughtSignature" in parts[0]:
        signature = parts[0]["thoughtSignature"]
        if not isinstance(signature, str) or not signature or len(signature) > MAX_THOUGHT_SIGNATURE_CODEPOINTS:
            raise Gate5MockError("provider_response_shape_invalid")
    try:
        candidate_payload = gate2.parse_response(text)
    except gate2.Gate2Error as exc:
        raise Gate5MockError("schema_invalid") from exc
    return {
        "model_version": model_version,
        "candidate_payload": candidate_payload,
        "candidate_payload_hash": gate2.sha256_bytes(gate2.canonical_json_bytes(candidate_payload)),
        "usage": parse_usage(value["usageMetadata"]),
    }


def run_mock_slot(slot: dict[str, Any], fixture_id: str) -> dict[str, Any]:
    """Exercise exactly one local fixture after validating the frozen request shape."""
    request = redesign.build_request(slot)
    fixture = load_fixtures().get(fixture_id)
    if fixture is None:
        raise Gate5MockError("unknown_fixture")
    try:
        parsed = parse_generate_content_response({key: value for key, value in fixture.items() if key != "id"})
        disposition = "locally_validated_no_candidate_review"
        stop_reason = None
    except Gate5MockError as exc:
        parsed = None
        disposition = "stopped"
        stop_reason = str(exc)
    return {
        "artifact": "gemini_generator_gate5_mock_run",
        "fixture_id": fixture_id,
        "request_hash": gate2.sha256_bytes(gate2.canonical_json_bytes(request)),
        "network_used": False,
        "credential_read": False,
        "candidate_reviewed": False,
        "corpus_mutated": False,
        "disposition": disposition,
        "stop_reason": stop_reason,
        "parsed": parsed,
    }
