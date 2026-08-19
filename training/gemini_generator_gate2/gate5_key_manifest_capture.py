"""Pure, value-discarding response key-manifest extraction helpers."""
from __future__ import annotations

import json
import re
from typing import Any

import gate2

KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
MANIFEST_FIELDS = {"top_level_keys", "candidate_count", "candidates", "usage_metadata_keys", "model_status_keys"}
CANDIDATE_FIELDS = {"candidate_keys", "content_keys", "part_count", "part_key_sets"}


class KeyManifestError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise KeyManifestError("duplicate_json_key")
        value[key] = item
    return value


def _safe_keys(value: dict[str, Any], cap: int) -> list[str]:
    keys = sorted(value)
    if len(keys) > cap or any(not isinstance(key, str) or not KEY_RE.fullmatch(key) for key in keys):
        raise KeyManifestError("key_boundary_invalid")
    return keys


def validate_manifest(manifest: Any) -> None:
    if not isinstance(manifest, dict) or set(manifest) != MANIFEST_FIELDS:
        raise KeyManifestError("manifest_invalid")

    def valid_keys(value: Any, cap: int) -> bool:
        return isinstance(value, list) and len(value) <= cap and value == sorted(set(value)) and all(isinstance(key, str) and KEY_RE.fullmatch(key) for key in value)

    if not valid_keys(manifest["top_level_keys"], 32) or type(manifest["candidate_count"]) is not int or not 0 <= manifest["candidate_count"] <= 4 or not isinstance(manifest["candidates"], list) or len(manifest["candidates"]) != manifest["candidate_count"]:
        raise KeyManifestError("manifest_invalid")
    for candidate in manifest["candidates"]:
        if not isinstance(candidate, dict) or set(candidate) != CANDIDATE_FIELDS or not valid_keys(candidate["candidate_keys"], 32) or not valid_keys(candidate["content_keys"], 8) or type(candidate["part_count"]) is not int or not 0 <= candidate["part_count"] <= 8 or not isinstance(candidate["part_key_sets"], list) or len(candidate["part_key_sets"]) != candidate["part_count"] or any(not valid_keys(keys, 32) for keys in candidate["part_key_sets"]):
            raise KeyManifestError("manifest_invalid")
    for name, cap in (("usage_metadata_keys", 32), ("model_status_keys", 16)):
        if manifest[name] is not None and not valid_keys(manifest[name], cap):
            raise KeyManifestError("manifest_invalid")
    if gate2.contains_secret(manifest):
        raise KeyManifestError("manifest_invalid")


def capture(body: bytes) -> tuple[str, dict[str, Any] | None]:
    try:
        value = json.loads(body.decode("utf-8", errors="strict"), object_pairs_hook=reject_duplicate_keys)
    except UnicodeDecodeError:
        return "withheld_invalid_utf8", None
    except (json.JSONDecodeError, KeyManifestError):
        return "withheld_invalid_json", None
    try:
        if not isinstance(value, dict) or not isinstance(value.get("candidates"), list) or len(value["candidates"]) > 4:
            raise KeyManifestError("shape_invalid")
        candidates = []
        for candidate in value["candidates"]:
            if not isinstance(candidate, dict) or not isinstance(candidate.get("content"), dict):
                raise KeyManifestError("shape_invalid")
            content = candidate["content"]
            parts = content.get("parts")
            if not isinstance(parts, list) or len(parts) > 8 or any(not isinstance(part, dict) for part in parts):
                raise KeyManifestError("shape_invalid")
            candidates.append({"candidate_keys": _safe_keys(candidate, 32), "content_keys": _safe_keys(content, 8), "part_count": len(parts), "part_key_sets": [_safe_keys(part, 32) for part in parts]})
        usage = value.get("usageMetadata")
        status = value.get("modelStatus")
        if (usage is not None and not isinstance(usage, dict)) or (status is not None and not isinstance(status, dict)):
            raise KeyManifestError("shape_invalid")
        manifest = {"top_level_keys": _safe_keys(value, 32), "candidate_count": len(value["candidates"]), "candidates": candidates, "usage_metadata_keys": _safe_keys(usage, 32) if usage is not None else None, "model_status_keys": _safe_keys(status, 16) if status is not None else None}
        validate_manifest(manifest)
        return "captured", manifest
    except KeyManifestError as exc:
        return ("withheld_key_boundary_invalid" if exc.code == "key_boundary_invalid" else "withheld_shape_or_count_invalid"), None
