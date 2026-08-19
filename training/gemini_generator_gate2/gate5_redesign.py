"""Local-only validator for the provisional Gate 5 provider-request redesign.

This module deliberately has no credential loading, HTTP client, SDK, socket import,
or execution command. It can construct and validate the future wire payload using
only frozen local prompts, schema, cards, and schedule.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import gate2


PACKAGE = Path(__file__).resolve().parent
CONTRACT_PATH = PACKAGE / "gate5_provider_contract_draft.json"
PROVIDER_SCHEMA_PATH = PACKAGE / "gate5_provider_response_schema.json"
EXPECTED_MODELS = ("gemini-3.7-flash", "gemini-3.5-flash-lite")
FORBIDDEN_KEYS = {
    "tools", "toolconfig", "safetysettings", "cachedcontent", "temperature", "topp", "topk",
    "thinkingbudget", "filedata", "inlinedata", "urlcontext", "apikey", "authorization",
}


class Gate5DraftError(RuntimeError):
    pass


def load_contract() -> dict[str, Any]:
    try:
        value = gate2.load_json(CONTRACT_PATH)
    except gate2.Gate2Error as exc:
        raise Gate5DraftError("contract JSON is invalid") from exc
    required = {
        "artifact", "status", "supersedes_for_future_gate5_review_only", "preserves", "api_surface",
        "transport", "request_controls", "redesign_basis", "execution_day_gates", "non_authorization",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise Gate5DraftError("contract fields drifted")
    if value["artifact"] != "gemini_generator_gate5_provider_contract_draft":
        raise Gate5DraftError("wrong contract artifact")
    if value["status"] != "local_only_draft_not_authorized_for_provider_execution":
        raise Gate5DraftError("contract must remain local-only")
    if tuple(value["preserves"].get("models", ())) != EXPECTED_MODELS:
        raise Gate5DraftError("model pair drifted")
    if value["preserves"].get("slot_count") != 24 or value["preserves"].get("slots_per_model") != 12:
        raise Gate5DraftError("schedule cardinality drifted")
    if value["preserves"].get("pilot_ceiling_usd_millionths") != 3_000_000:
        raise Gate5DraftError("pilot ceiling drifted")
    controls = value["request_controls"]
    expected_controls = {"candidateCount", "thinkingConfig", "maxOutputTokens", "responseMimeType", "responseSchema", "forbidden_request_fields"}
    if set(controls) != expected_controls or controls["candidateCount"] != 1 or controls["maxOutputTokens"] != 2048:
        raise Gate5DraftError("request cardinality or token cap drifted")
    if controls["thinkingConfig"] != {"thinkingLevel": "low"}:
        raise Gate5DraftError("common low-thinking control is required")
    if controls["responseMimeType"] != "application/json" or controls["responseSchema"] != "gate5_provider_response_schema.json":
        raise Gate5DraftError("structured-output control drifted")
    api = value["api_surface"]
    if api.get("method") != "POST" or api.get("endpoint_template") != "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent":
        raise Gate5DraftError("endpoint drifted")
    if api.get("header_names") != ["Content-Type", "x-goog-api-key"] or api.get("content_type") != "application/json":
        raise Gate5DraftError("header contract drifted")
    if value["transport"] != {"streaming": False, "timeout_seconds": 60, "semantic_retries": 0, "transport_retries": 0, "redirects": "forbidden"}:
        raise Gate5DraftError("transport contract drifted")
    return value


def _walk_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return {key.lower() for key in value} | set().union(*(_walk_keys(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(*(_walk_keys(item) for item in value)) if value else set()
    return set()


def provider_response_schema() -> dict[str, Any]:
    try:
        value = gate2.load_json(PROVIDER_SCHEMA_PATH)
    except gate2.Gate2Error as exc:
        raise Gate5DraftError("provider response schema is invalid") from exc
    allowed_types = {"STRING", "NUMBER", "INTEGER", "BOOLEAN", "ARRAY", "OBJECT", "NULL"}

    def check(item: Any) -> None:
        if isinstance(item, dict):
            if "type" in item and item["type"] not in allowed_types:
                raise Gate5DraftError("provider response schema type drifted")
            if "additionalProperties" in item:
                raise Gate5DraftError("provider response schema contains unsupported additionalProperties")
            for child in item.values():
                check(child)
        elif isinstance(item, list):
            for child in item:
                check(child)

    if not isinstance(value, dict):
        raise Gate5DraftError("provider response schema is invalid")
    check(value)
    return value


def build_request(slot: dict[str, Any]) -> dict[str, Any]:
    """Build a safe-to-inspect payload; it contains no credentials and cannot send."""
    contract = load_contract()
    model = slot.get("model")
    mechanism_id = slot.get("mechanism_id")
    if model not in EXPECTED_MODELS or not isinstance(mechanism_id, str):
        raise Gate5DraftError("invalid frozen schedule slot")
    system, user = gate2.render_messages(mechanism_id)
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "responseMimeType": contract["request_controls"]["responseMimeType"],
            "responseSchema": provider_response_schema(),
            "candidateCount": contract["request_controls"]["candidateCount"],
            "thinkingConfig": contract["request_controls"]["thinkingConfig"],
            "maxOutputTokens": contract["request_controls"]["maxOutputTokens"],
        },
    }
    request = {
        "method": contract["api_surface"]["method"],
        "endpoint": contract["api_surface"]["endpoint_template"].replace("{model}", model),
        "header_names": contract["api_surface"]["header_names"],
        "body": body,
        "streaming": contract["transport"]["streaming"],
        "timeout_seconds": contract["transport"]["timeout_seconds"],
    }
    validate_request(request)
    return request


def validate_request(request: dict[str, Any]) -> None:
    expected = {"method", "endpoint", "header_names", "body", "streaming", "timeout_seconds"}
    if not isinstance(request, dict) or set(request) != expected:
        raise Gate5DraftError("request envelope drifted")
    if request["method"] != "POST" or request["header_names"] != ["Content-Type", "x-goog-api-key"]:
        raise Gate5DraftError("method or headers drifted")
    if request["streaming"] is not False or request["timeout_seconds"] != 60:
        raise Gate5DraftError("transport drifted")
    if request["endpoint"] not in {f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent" for model in EXPECTED_MODELS}:
        raise Gate5DraftError("model endpoint drifted")
    body = request["body"]
    if not isinstance(body, dict) or set(body) != {"systemInstruction", "contents", "generationConfig"}:
        raise Gate5DraftError("body shape drifted")
    config = body["generationConfig"]
    if not isinstance(config, dict) or set(config) != {"responseMimeType", "responseSchema", "candidateCount", "thinkingConfig", "maxOutputTokens"}:
        raise Gate5DraftError("generation configuration drifted")
    if config["thinkingConfig"] != {"thinkingLevel": "low"} or config["candidateCount"] != 1 or config["maxOutputTokens"] != 2048:
        raise Gate5DraftError("shared generation control drifted")
    if config["responseMimeType"] != "application/json" or config["responseSchema"] != provider_response_schema():
        raise Gate5DraftError("structured-output control drifted")
    if FORBIDDEN_KEYS & _walk_keys(request):
        raise Gate5DraftError("forbidden provider control or secret field present")
    if gate2.contains_secret(request):
        raise Gate5DraftError("secret-like value present")


def validate_schedule_requests() -> list[str]:
    """Validate all 24 frozen slots locally; returns deterministic request-body hashes."""
    schedule = gate2.load_json(PACKAGE / "schedule.json")
    slots = schedule.get("slots") if isinstance(schedule, dict) else None
    if not isinstance(slots, list) or len(slots) != 24:
        raise Gate5DraftError("frozen schedule unavailable")
    hashes = []
    for slot in slots:
        request = build_request(slot)
        hashes.append(gate2.sha256_bytes(gate2.canonical_json_bytes(request["body"])))
    if len(set(hashes)) != 12:
        raise Gate5DraftError("expected one rendered payload per mechanism card")
    return hashes


def main() -> int:
    load_contract()
    hashes = validate_schedule_requests()
    print(json.dumps({"artifact": "gemini_generator_gate5_local_redesign_check", "request_count": len(hashes), "unique_payload_count": len(set(hashes)), "network_used": False, "credential_read": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
