"""Content-free evidence for future Gate 5 response-schema failures."""

from __future__ import annotations

import re
from typing import Any

import gate2


ARTIFACT = "gemini_generator_gate5_schema_conformance_diagnostic_row"
SCHEMA_VERSION = 1
MAX_CANONICAL_ROW_BYTES = 16_384
MAX_COUNT = 1_000_000
HASH_RE = re.compile(r"[0-9a-f]{64}")
MODELS = {"gemini-3.7-flash", "gemini-3.5-flash-lite"}
MECHANISM_RE = re.compile(r"M(?:0[1-9]|1[0-2])")
KINDS = {
    "response_json_invalid",
    "top_level_keys_invalid",
    "source_input_not_plain_string",
    "source_input_word_count_out_of_range",
    "proposed_output_keys_invalid",
    "narrative_not_plain_string",
    "narrative_sentence_count_out_of_range",
    "list_not_array",
    "list_item_count_out_of_range",
    "list_item_not_plain_string",
}
NO_DETAIL_KINDS = {"response_json_invalid", "source_input_not_plain_string", "narrative_not_plain_string"}
COUNT_KINDS = {"source_input_word_count_out_of_range", "narrative_sentence_count_out_of_range"}
ROW_FIELDS = {
    "artifact", "schema_version", "sequence", "schedule_slot", "model", "mechanism_id",
    "request_hash", "raw_response_hash", "rejection_reason_code", "structured_reason",
    "linked_rejection_sequence", "candidate_text_persisted", "candidate_review_performed",
    "corpus_mutation_performed", "prior_row_hash", "row_hash",
}


class SchemaConformanceEvidenceError(RuntimeError):
    pass


def _fail() -> None:
    raise SchemaConformanceEvidenceError("schema_conformance_diagnostic_withheld")


def _bounded_int(value: Any) -> bool:
    return type(value) is int and 0 <= value <= MAX_COUNT


def validate_reason(value: Any) -> None:
    if not isinstance(value, dict) or value.get("kind") not in KINDS:
        _fail()
    kind = value["kind"]
    if kind in NO_DETAIL_KINDS:
        expected = {"kind"}
    elif kind == "top_level_keys_invalid":
        expected = {"kind", "has_source_input", "has_proposed_output", "extra_key_count"}
        if type(value.get("has_source_input")) is not bool or type(value.get("has_proposed_output")) is not bool or not _bounded_int(value.get("extra_key_count")):
            _fail()
    elif kind == "proposed_output_keys_invalid":
        expected = {"kind", "has_narrative", "has_bullets", "has_action_items", "extra_key_count"}
        if any(type(value.get(name)) is not bool for name in ("has_narrative", "has_bullets", "has_action_items")) or not _bounded_int(value.get("extra_key_count")):
            _fail()
    elif kind in COUNT_KINDS:
        expected = {"kind", "actual_count", "min_allowed", "max_allowed"}
        if not all(_bounded_int(value.get(name)) for name in ("actual_count", "min_allowed", "max_allowed")) or value["min_allowed"] > value["max_allowed"]:
            _fail()
    elif kind == "list_not_array":
        expected = {"kind", "field"}
        if value.get("field") not in {"bullets", "action_items"}:
            _fail()
    elif kind == "list_item_count_out_of_range":
        expected = {"kind", "field", "actual_count", "min_allowed", "max_allowed"}
        if value.get("field") not in {"bullets", "action_items"} or not all(_bounded_int(value.get(name)) for name in ("actual_count", "min_allowed", "max_allowed")) or value["min_allowed"] > value["max_allowed"]:
            _fail()
    else:
        expected = {"kind", "field", "index"}
        if value.get("field") not in {"bullets", "action_items"} or not _bounded_int(value.get("index")):
            _fail()
    if set(value) != expected or gate2.contains_secret(value):
        _fail()


def build_row(sequence: int, slot: dict[str, Any], request_hash: str, raw_response_hash: str,
              error: gate2.ResponseSchemaError, prior_row_hash: str | None) -> dict[str, Any]:
    if type(sequence) is not int or not 1 <= sequence <= 24:
        _fail()
    if not isinstance(slot, dict) or slot.get("slot") != sequence or slot.get("model") not in MODELS or not MECHANISM_RE.fullmatch(str(slot.get("mechanism_id", ""))):
        _fail()
    if not HASH_RE.fullmatch(request_hash) or not HASH_RE.fullmatch(raw_response_hash):
        _fail()
    if prior_row_hash is not None and not HASH_RE.fullmatch(str(prior_row_hash)):
        _fail()
    if not isinstance(error, gate2.ResponseSchemaError):
        _fail()
    reason = error.structured_reason
    validate_reason(reason)
    row = gate2.chained_row({
        "artifact": ARTIFACT,
        "schema_version": SCHEMA_VERSION,
        "sequence": sequence,
        "schedule_slot": slot["slot"],
        "model": slot["model"],
        "mechanism_id": slot["mechanism_id"],
        "request_hash": request_hash,
        "raw_response_hash": raw_response_hash,
        "rejection_reason_code": "schema_invalid",
        "structured_reason": reason,
        "linked_rejection_sequence": sequence,
        "candidate_text_persisted": False,
        "candidate_review_performed": False,
        "corpus_mutation_performed": False,
    }, prior_row_hash)
    validate_row(row)
    return row


def validate_row(row: Any) -> None:
    if not isinstance(row, dict) or set(row) != ROW_FIELDS or row.get("artifact") != ARTIFACT or row.get("schema_version") != SCHEMA_VERSION:
        _fail()
    sequence = row.get("sequence")
    if type(sequence) is not int or not 1 <= sequence <= 24 or row.get("schedule_slot") != sequence or row.get("linked_rejection_sequence") != sequence:
        _fail()
    if row.get("model") not in MODELS or not MECHANISM_RE.fullmatch(str(row.get("mechanism_id", ""))):
        _fail()
    if not HASH_RE.fullmatch(str(row.get("request_hash", ""))) or not HASH_RE.fullmatch(str(row.get("raw_response_hash", ""))) or row.get("rejection_reason_code") != "schema_invalid":
        _fail()
    validate_reason(row.get("structured_reason"))
    if any(row.get(name) is not False for name in ("candidate_text_persisted", "candidate_review_performed", "corpus_mutation_performed")):
        _fail()
    prior = row.get("prior_row_hash")
    if prior is not None and not HASH_RE.fullmatch(str(prior)):
        _fail()
    payload = {key: value for key, value in row.items() if key != "row_hash"}
    if row.get("row_hash") != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)):
        _fail()
    encoded = gate2.canonical_json_bytes(row)
    if len(encoded) > MAX_CANONICAL_ROW_BYTES or gate2.contains_secret(row):
        _fail()


def verify_chain(rows: Any) -> None:
    # No upper bound on chain length: this was `len(rows) > 1: fail()` before,
    # which was silently correct for every version through V9 (schema_invalid
    # was always hard-terminal there, so no run could ever produce more than
    # one row) and is a real defect for V10 onward, where schema_invalid can
    # legitimately continue past and accumulate several rows in one run - the
    # loop below already verifies an arbitrary-length hash chain correctly,
    # matching gate5_output_collision_evidence.verify_chain()'s identical,
    # already-proven pattern. Found via a real crash on the second genuine
    # schema_invalid in a single real V10 campaign run.
    if not isinstance(rows, list):
        _fail()
    prior = None
    for row in rows:
        validate_row(row)
        if row.get("prior_row_hash") != prior:
            _fail()
        prior = row["row_hash"]


def validate_rejection_links(rejections: Any, diagnostics: Any, summary: Any) -> None:
    if not isinstance(rejections, list) or not isinstance(diagnostics, list) or not isinstance(summary, dict):
        _fail()
    verify_chain(diagnostics)
    by_hash = {row["row_hash"]: row for row in diagnostics}
    linked: set[str] = set()
    for rejection in rejections:
        if not isinstance(rejection, dict):
            _fail()
        link = rejection.get("schema_conformance_diagnostic_row_hash")
        if rejection.get("reason_code") == "schema_invalid":
            if not isinstance(link, str) or link not in by_hash or link in linked:
                _fail()
            diagnostic = by_hash[link]
            if any(diagnostic[left] != rejection[right] for left, right in (("sequence", "sequence"), ("request_hash", "request_hash"), ("raw_response_hash", "raw_response_hash"), ("rejection_reason_code", "reason_code"))):
                _fail()
            linked.add(link)
        elif link is not None:
            _fail()
    if linked != set(by_hash):
        _fail()
    if summary.get("schema_conformance_diagnostic_count") != len(diagnostics):
        _fail()
    expected_head = diagnostics[-1]["row_hash"] if diagnostics else None
    if summary.get("schema_conformance_diagnostic_chain_head") != expected_head:
        _fail()
