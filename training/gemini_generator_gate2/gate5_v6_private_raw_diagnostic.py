"""Local-only screened raw-text diagnostics for V6 pause-eligible format stops."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable

import gate2


ALLOWED_STOP_CODES = {"schema_invalid", "extra_key", "finish_reason_invalid", "size_limit_failed"}
ALLOWED_FINISH_REASONS = {"STOP", "MAX_TOKENS"}
MAX_TEXT_BYTES = 65_536
LEDGER_NAME = "raw_output_diagnostics.jsonl"
RECORD_FIELDS = {
    "artifact", "sequence", "stop_code", "request_sha256", "raw_response_sha256",
    "rejection_row_sha256", "candidate_text", "candidate_text_sha256",
    "prior_private_row_hash", "record_sha256",
}
LEDGER_FIELDS = {
    "artifact", "sequence", "record_file", "record_sha256", "candidate_text_sha256",
    "rejection_row_sha256", "prior_row_hash", "row_hash",
}


class PrivateRawDiagnosticError(RuntimeError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PrivateRawDiagnosticError("duplicate JSON key")
        result[key] = value
    return result


def _projection(text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except Exception:
        return None
    if not isinstance(value, dict) or set(value) != {"source_input", "proposed_output"}:
        return None
    output = value.get("proposed_output")
    if not isinstance(value.get("source_input"), str) or not isinstance(output, dict) or set(output) != {"narrative", "bullets", "action_items"}:
        return None
    if not isinstance(output.get("narrative"), str) or not isinstance(output.get("bullets"), list) or not isinstance(output.get("action_items"), list):
        return None
    if any(not isinstance(item, str) for item in [*output["bullets"], *output["action_items"]]):
        return None
    return value


def consider(
    value: Any,
    stop_code: str,
    references: Iterable[tuple[str, str]],
    earlier_candidates: Iterable[tuple[str, str]],
    prompt_references: Iterable[tuple[str, str]],
) -> dict[str, Any]:
    """Return a fixed state and, only when safe, the exact candidate text to retain."""
    if stop_code not in ALLOWED_STOP_CODES:
        return {"state": "not_eligible_stop_code", "text": None, "screen": None}
    if not isinstance(value, dict):
        return {"state": "withheld_unparseable_or_unscreenable", "text": None, "screen": None}
    candidates = value.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 1 or not isinstance(candidates[0], dict):
        return {"state": "withheld_unparseable_or_unscreenable", "text": None, "screen": None}
    candidate = candidates[0]
    reason = candidate.get("finishReason")
    if reason not in ALLOWED_FINISH_REASONS:
        return {"state": "withheld_provider_finish_reason", "text": None, "screen": None}
    ratings = candidate.get("safetyRatings")
    if isinstance(ratings, list) and any(isinstance(item, dict) and item.get("blocked") is True for item in ratings):
        return {"state": "withheld_provider_safety_or_citation_signal", "text": None, "screen": None}
    if candidate.get("citationMetadata") is not None:
        return {"state": "withheld_provider_safety_or_citation_signal", "text": None, "screen": None}
    content = candidate.get("content")
    if not isinstance(content, dict) or not isinstance(content.get("parts"), list) or not content["parts"]:
        return {"state": "withheld_unparseable_or_unscreenable", "text": None, "screen": None}
    texts: list[str] = []
    for part in content["parts"]:
        if not isinstance(part, dict) or not isinstance(part.get("text"), str) or not set(part).issubset({"text", "thoughtSignature"}):
            return {"state": "withheld_unparseable_or_unscreenable", "text": None, "screen": None}
        texts.append(part["text"])
    text = "\n".join(texts)
    if not text or len(text.encode("utf-8")) > MAX_TEXT_BYTES:
        return {"state": "withheld_size_limit", "text": None, "screen": None}
    if gate2.contains_secret(text):
        return {"state": "withheld_secret_like_content", "text": None, "screen": None}
    projection = _projection(text)
    if projection is None:
        return {"state": "withheld_unparseable_or_unscreenable", "text": None, "screen": None}
    screen = gate2.screen_candidate(projection, references, earlier_candidates, prompt_references)
    if screen.get("fatal"):
        return {"state": "withheld_protected_or_duplicate_collision", "text": None, "screen": None}
    return {"state": "persisted", "text": text, "screen": screen}


def _write_new(path: Path, data: bytes) -> None:
    try:
        with path.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except (FileExistsError, OSError) as exc:
        raise PrivateRawDiagnosticError("private write failed") from exc


def persist(root: Path, sequence: int, stop_code: str, request_hash: str, raw_response_hash: str, rejection_hash: str, text: str) -> dict[str, Any]:
    if stop_code not in ALLOWED_STOP_CODES or gate2.contains_secret(text):
        raise PrivateRawDiagnosticError("private record invalid")
    directory = root / "private_raw_diagnostics"
    try:
        directory.mkdir(parents=False, exist_ok=False)
    except FileExistsError:
        pass
    except OSError as exc:
        raise PrivateRawDiagnosticError("private write failed") from exc
    ledger = directory / LEDGER_NAME
    prior = None
    if ledger.exists():
        try:
            rows = [json.loads(line, object_pairs_hook=_reject_duplicate_keys) for line in ledger.read_text(encoding="utf-8").splitlines() if line]
            prior = rows[-1]["row_hash"] if rows else None
        except Exception as exc:
            raise PrivateRawDiagnosticError("private ledger invalid") from exc
    record = {"artifact": "gemini_generator_gate5_v6_private_raw_output", "sequence": sequence, "stop_code": stop_code, "request_sha256": request_hash, "raw_response_sha256": raw_response_hash, "rejection_row_sha256": rejection_hash, "candidate_text": text, "candidate_text_sha256": gate2.sha256_bytes(text.encode("utf-8")), "prior_private_row_hash": prior}
    record["record_sha256"] = gate2.sha256_bytes(gate2.canonical_json_bytes(record))
    record_path = directory / f"attempt_{sequence:03d}_raw_output.json"
    _write_new(record_path, gate2.canonical_json_bytes(record))
    row = {"artifact": "gemini_generator_gate5_v6_private_raw_output_ledger", "sequence": sequence, "record_file": record_path.name, "record_sha256": record["record_sha256"], "candidate_text_sha256": record["candidate_text_sha256"], "rejection_row_sha256": rejection_hash, "prior_row_hash": prior}
    row["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(row))
    try:
        with ledger.open("ab") as handle:
            handle.write(gate2.canonical_json_bytes(row))
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        try:
            record_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise PrivateRawDiagnosticError("private write failed") from exc
    return row


def verify(root: Path) -> list[dict[str, Any]]:
    """Verify private records locally without returning any candidate text."""
    directory = root / "private_raw_diagnostics"
    ledger = directory / LEDGER_NAME
    try:
        rows = [json.loads(line, object_pairs_hook=_reject_duplicate_keys) for line in ledger.read_text(encoding="utf-8").splitlines() if line]
    except Exception as exc:
        raise PrivateRawDiagnosticError("private ledger invalid") from exc
    prior = None
    prior_sequence = 0
    safe_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != LEDGER_FIELDS or type(row.get("sequence")) is not int or row["sequence"] <= prior_sequence or row.get("prior_row_hash") != prior or row.get("artifact") != "gemini_generator_gate5_v6_private_raw_output_ledger":
            raise PrivateRawDiagnosticError("private ledger invalid")
        row_payload = {key: value for key, value in row.items() if key != "row_hash"}
        if row.get("row_hash") != gate2.sha256_bytes(gate2.canonical_json_bytes(row_payload)):
            raise PrivateRawDiagnosticError("private ledger invalid")
        record_path = directory / str(row.get("record_file"))
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)
        except Exception as exc:
            raise PrivateRawDiagnosticError("private record invalid") from exc
        if not isinstance(record, dict) or set(record) != RECORD_FIELDS or record.get("artifact") != "gemini_generator_gate5_v6_private_raw_output" or record.get("sequence") != row["sequence"] or record.get("stop_code") not in ALLOWED_STOP_CODES or record.get("prior_private_row_hash") != prior:
            raise PrivateRawDiagnosticError("private record invalid")
        text = record.get("candidate_text")
        if not isinstance(text, str) or not text or len(text.encode("utf-8")) > MAX_TEXT_BYTES or gate2.contains_secret(text) or _projection(text) is None:
            raise PrivateRawDiagnosticError("private record invalid")
        record_payload = {key: value for key, value in record.items() if key != "record_sha256"}
        if record.get("record_sha256") != gate2.sha256_bytes(gate2.canonical_json_bytes(record_payload)) or record.get("candidate_text_sha256") != gate2.sha256_bytes(text.encode("utf-8")):
            raise PrivateRawDiagnosticError("private record invalid")
        if any(not isinstance(record.get(name), str) or not gate2.HEX64_RE.fullmatch(record[name]) for name in ("request_sha256", "raw_response_sha256", "rejection_row_sha256", "candidate_text_sha256", "record_sha256")):
            raise PrivateRawDiagnosticError("private record invalid")
        if row.get("record_sha256") != record["record_sha256"] or row.get("candidate_text_sha256") != record["candidate_text_sha256"] or row.get("rejection_row_sha256") != record["rejection_row_sha256"]:
            raise PrivateRawDiagnosticError("private ledger invalid")
        safe_rows.append({key: row[key] for key in ("sequence", "record_sha256", "candidate_text_sha256", "rejection_row_sha256", "row_hash")})
        prior = row["row_hash"]
        prior_sequence = row["sequence"]
    return safe_rows
