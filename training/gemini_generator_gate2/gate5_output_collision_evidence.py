"""Strict future-only output-collision evidence formatting and validation.

This module accepts only the already-computed, content-free portion of a
mechanical screen. Candidate and comparator text are deliberately absent from
every public function signature used to build a persisted row.
"""

from __future__ import annotations

import math
import re
from typing import Any, Iterable

import gate2


ARTIFACT = "gemini_generator_gate5_output_collision_diagnostic_row"
SCHEMA_VERSION = 1
MAX_CANONICAL_ROW_BYTES = 65_536
HASH_RE = re.compile(r"[0-9a-f]{64}")
MODEL_RE = re.compile(r"gemini-[a-z0-9.-]{1,48}")
EXPECTED_MODELS = {"gemini-3.7-flash", "gemini-3.5-flash-lite"}
MECHANISM_RE = re.compile(r"M(?:0[1-9]|1[0-2])")
REASON_SUFFIX = ":protected_collision"
# Real bug, found via a real production hard-stop on 2026-08-18 (V12's real
# campaign, card 9): this set previously capped bullets/action_items at
# index :03, silently latent since this module was first built (V6) because
# no real collision had ever hit a 4th-or-later list item until this run.
# response_schema.json allows bullets 2-8 items and action_items 1-6 items
# -- this set must cover the full real range or a genuine, schema-valid
# collision on e.g. bullets:04 fails closed (output_collision_diagnostic_
# withheld, hard-terminal in every version) instead of being diagnosed.
# Reproduced directly against the real bug class before this fix, confirmed
# fixed after. Fixing this file in place (not version-scoping it) is the
# same category of change as V10's real gate5_schema_conformance_evidence.py
# crash fix: a genuine correctness bug in shared evidence-building code, not
# a policy change -- V6-V11's own historical behavior is unaffected since
# none of them ever exercised this path for real.
EXPECTED_CANDIDATE_FIELD_PATHS = {
    "source_input",
    "proposed_output:output.narrative",
    "proposed_output:output.bullets:01",
    "proposed_output:output.bullets:02",
    "proposed_output:output.bullets:03",
    "proposed_output:output.bullets:04",
    "proposed_output:output.bullets:05",
    "proposed_output:output.bullets:06",
    "proposed_output:output.bullets:07",
    "proposed_output:output.bullets:08",
    "proposed_output:output.action_items:01",
    "proposed_output:output.action_items:02",
    "proposed_output:output.action_items:03",
    "proposed_output:output.action_items:04",
    "proposed_output:output.action_items:05",
    "proposed_output:output.action_items:06",
}
KINDS = {
    "normalized_exact_match",
    "normalized_containment",
    "token_jaccard_threshold",
    "character_5gram_jaccard_threshold",
}
NULL_SCORE_KINDS = {"normalized_exact_match", "normalized_containment"}
ROW_FIELDS = {
    "artifact",
    "schema_version",
    "sequence",
    "schedule_slot",
    "model",
    "mechanism_id",
    "request_hash",
    "raw_response_hash",
    "rejection_reason_code",
    "field_path",
    "protected_collision",
    "candidate_text_persisted",
    "protected_reference_text_persisted",
    "candidate_review_performed",
    "corpus_mutation_performed",
    "prior_row_hash",
    "row_hash",
}
PROTECTED_FIELDS = {
    "reasons",
    "maximum_token_jaccard",
    "maximum_character_5gram_jaccard",
}
REASON_FIELDS = {"kind", "reference", "score"}
MAXIMUM_FIELDS = {"reference", "score"}
FUTURE_REJECTION_FIELDS = {
    "artifact",
    "sequence",
    "request_hash",
    "raw_response_hash",
    "reason_code",
    "output_collision_diagnostic_row_hash",
    "disposition",
    "no_corpus_mutation",
    "prior_row_hash",
    "row_hash",
}


class OutputCollisionEvidenceError(RuntimeError):
    pass


def _fail() -> None:
    raise OutputCollisionEvidenceError("output_collision_diagnostic_withheld")


def _valid_score(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value) and 0.0 <= value <= 1.0


def _validate_reason(reason: Any, allowed_labels: set[str]) -> None:
    if not isinstance(reason, dict) or set(reason) != REASON_FIELDS:
        _fail()
    kind = reason.get("kind")
    reference = reason.get("reference")
    score = reason.get("score")
    if kind not in KINDS or reference not in allowed_labels:
        _fail()
    if kind in NULL_SCORE_KINDS:
        if score is not None:
            _fail()
    elif not _valid_score(score):
        _fail()


def _validate_maximum(value: Any, allowed_labels: set[str]) -> None:
    if not isinstance(value, dict) or set(value) != MAXIMUM_FIELDS:
        _fail()
    if value.get("reference") not in allowed_labels or not _valid_score(value.get("score")):
        _fail()


def _validate_protected(value: Any, allowed_labels: set[str]) -> None:
    if not isinstance(value, dict) or set(value) != PROTECTED_FIELDS:
        _fail()
    reasons = value.get("reasons")
    if not isinstance(reasons, list) or not reasons or len(reasons) > 4 * len(allowed_labels):
        _fail()
    for reason in reasons:
        _validate_reason(reason, allowed_labels)
    encoded_reasons = [gate2.canonical_json_bytes(reason) for reason in reasons]
    if len(set(encoded_reasons)) != len(encoded_reasons):
        _fail()
    _validate_maximum(value.get("maximum_token_jaccard"), allowed_labels)
    _validate_maximum(value.get("maximum_character_5gram_jaccard"), allowed_labels)


def _selected_protected_result(reason_code: str, screen: Any, allowed_field_paths: set[str]) -> tuple[str, dict[str, Any]]:
    if not isinstance(reason_code, str) or not reason_code.endswith(REASON_SUFFIX):
        _fail()
    field_path = reason_code[: -len(REASON_SUFFIX)]
    if field_path not in allowed_field_paths or field_path not in EXPECTED_CANDIDATE_FIELD_PATHS:
        _fail()
    if not isinstance(screen, dict) or set(screen) != {"fatal", "fatal_reasons", "fields"} or screen.get("fatal") is not True:
        _fail()
    fatal_reasons = screen.get("fatal_reasons")
    fields = screen.get("fields")
    if not isinstance(fatal_reasons, list) or reason_code not in fatal_reasons or not isinstance(fields, list):
        _fail()
    matches = [item for item in fields if isinstance(item, dict) and item.get("field") == field_path]
    if len(matches) != 1:
        _fail()
    protected = matches[0].get("protected")
    if not isinstance(protected, dict) or protected.get("fatal") is not True:
        _fail()
    return field_path, protected


def build_row(
    sequence: int,
    slot: dict[str, Any],
    request_hash: str,
    raw_response_hash: str,
    rejection_reason_code: str,
    screen: dict[str, Any],
    allowed_reference_labels: Iterable[str],
    allowed_field_paths: Iterable[str],
    prior_row_hash: str | None,
) -> dict[str, Any]:
    """Build one content-free diagnostic row or fail closed."""
    labels = set(allowed_reference_labels)
    fields = set(allowed_field_paths)
    if not labels or not fields:
        _fail()
    if type(sequence) is not int or not 1 <= sequence <= 24:
        _fail()
    if not isinstance(slot, dict) or slot.get("slot") != sequence or slot.get("model") not in EXPECTED_MODELS or not MODEL_RE.fullmatch(str(slot.get("model", ""))) or not MECHANISM_RE.fullmatch(str(slot.get("mechanism_id", ""))):
        _fail()
    if not HASH_RE.fullmatch(request_hash) or not HASH_RE.fullmatch(raw_response_hash):
        _fail()
    if prior_row_hash is not None and (not isinstance(prior_row_hash, str) or not HASH_RE.fullmatch(prior_row_hash)):
        _fail()
    field_path, protected = _selected_protected_result(rejection_reason_code, screen, fields)
    protected_value = {
        "reasons": protected.get("structured_reasons"),
        "maximum_token_jaccard": protected.get("maximum_token_jaccard"),
        "maximum_character_5gram_jaccard": protected.get("maximum_character_5gram_jaccard"),
    }
    _validate_protected(protected_value, labels)
    row = gate2.chained_row({
        "artifact": ARTIFACT,
        "schema_version": SCHEMA_VERSION,
        "sequence": sequence,
        "schedule_slot": slot["slot"],
        "model": slot["model"],
        "mechanism_id": slot["mechanism_id"],
        "request_hash": request_hash,
        "raw_response_hash": raw_response_hash,
        "rejection_reason_code": rejection_reason_code,
        "field_path": field_path,
        "protected_collision": protected_value,
        "candidate_text_persisted": False,
        "protected_reference_text_persisted": False,
        "candidate_review_performed": False,
        "corpus_mutation_performed": False,
    }, prior_row_hash)
    validate_row(row, labels, fields)
    return row


def validate_row(row: Any, allowed_reference_labels: Iterable[str], allowed_field_paths: Iterable[str]) -> None:
    labels = set(allowed_reference_labels)
    fields = set(allowed_field_paths)
    if not isinstance(row, dict) or set(row) != ROW_FIELDS:
        _fail()
    if row.get("artifact") != ARTIFACT or row.get("schema_version") != SCHEMA_VERSION:
        _fail()
    if type(row.get("sequence")) is not int or not 1 <= row["sequence"] <= 24 or row.get("schedule_slot") != row["sequence"]:
        _fail()
    if row.get("model") not in EXPECTED_MODELS or not MODEL_RE.fullmatch(str(row.get("model", ""))) or not MECHANISM_RE.fullmatch(str(row.get("mechanism_id", ""))):
        _fail()
    if not HASH_RE.fullmatch(str(row.get("request_hash", ""))) or not HASH_RE.fullmatch(str(row.get("raw_response_hash", ""))):
        _fail()
    reason_code = row.get("rejection_reason_code")
    field_path = row.get("field_path")
    if not isinstance(field_path, str) or field_path not in fields or field_path not in EXPECTED_CANDIDATE_FIELD_PATHS or reason_code != field_path + REASON_SUFFIX:
        _fail()
    _validate_protected(row.get("protected_collision"), labels)
    for name in ("candidate_text_persisted", "protected_reference_text_persisted", "candidate_review_performed", "corpus_mutation_performed"):
        if row.get(name) is not False:
            _fail()
    prior = row.get("prior_row_hash")
    if prior is not None and (not isinstance(prior, str) or not HASH_RE.fullmatch(prior)):
        _fail()
    payload = {key: value for key, value in row.items() if key != "row_hash"}
    if row.get("row_hash") != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)):
        _fail()
    if gate2.contains_secret(row) or len(gate2.canonical_json_bytes(row)) > MAX_CANONICAL_ROW_BYTES:
        _fail()


def verify_chain(rows: Any, allowed_reference_labels: Iterable[str], allowed_field_paths: Iterable[str]) -> None:
    if not isinstance(rows, list):
        _fail()
    prior = None
    for row in rows:
        validate_row(row, allowed_reference_labels, allowed_field_paths)
        if row.get("prior_row_hash") != prior:
            _fail()
        prior = row["row_hash"]


def validate_rejection_links(rejections: Any, diagnostics: Any, summary: Any, allowed_reference_labels: Iterable[str], allowed_field_paths: Iterable[str]) -> None:
    """Validate strict future rejection rows and their diagnostic cross-links."""
    if not isinstance(rejections, list) or not isinstance(diagnostics, list) or not isinstance(summary, dict):
        _fail()
    gate2.verify_chain(rejections)
    verify_chain(diagnostics, allowed_reference_labels, allowed_field_paths)
    by_hash = {row["row_hash"]: row for row in diagnostics}
    linked: set[str] = set()
    for rejection in rejections:
        if not isinstance(rejection, dict) or set(rejection) != FUTURE_REJECTION_FIELDS:
            _fail()
        link = rejection.get("output_collision_diagnostic_row_hash")
        protected = isinstance(rejection.get("reason_code"), str) and rejection["reason_code"].endswith(REASON_SUFFIX)
        if protected:
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
    if summary.get("output_collision_diagnostic_count") != len(diagnostics):
        _fail()
    expected_head = diagnostics[-1]["row_hash"] if diagnostics else None
    if summary.get("output_collision_diagnostic_chain_head") != expected_head:
        _fail()


# --- schema_version 2 additions below this line ------------------------------
# Purely additive: SCHEMA_VERSION, ROW_FIELDS, build_row, validate_row,
# verify_chain, and validate_rejection_links above are all completely
# unmodified -- every real schema_version-1 row already persisted (V6
# through V12's real campaigns) keeps validating against them exactly as it
# always has. This adds a second, parallel row shape rather than changing
# the first, for the same reason V11/V12 added new gate2.py functions
# instead of editing collision_check in place: nothing about this file's
# already-real, already-reviewed behavior can be allowed to shift under it.
#
# The new content: two small non-negative integers (gate2.field_length_metadata's
# output), attached to the candidate's own screened field and to each
# reference a real collision reason points at. Still zero raw text -- the
# module's stated invariant ("Candidate and comparator text are deliberately
# absent from every public function signature used to build a persisted
# row") holds exactly as before; callers compute lengths themselves (via
# gate2.field_length_metadata, which only ever returns integers) and pass
# already-reduced integer dicts in here, the same way they already compute
# and pass in hashes rather than raw request/response bodies.
SCHEMA_VERSION_2 = 2
LENGTH_FIELDS = {"normalized_char_length", "stopword_filtered_token_count"}
REASON_FIELDS_V2 = REASON_FIELDS | {"reference_field_length"}
MAXIMUM_FIELDS_V2 = MAXIMUM_FIELDS | {"reference_field_length"}
ROW_FIELDS_V2 = ROW_FIELDS | {"candidate_field_length"}


def _valid_length(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == LENGTH_FIELDS
        and all(type(value.get(key)) is int and value[key] >= 0 for key in LENGTH_FIELDS)
    )


def _validate_reason_v2(reason: Any, allowed_labels: set[str]) -> None:
    if not isinstance(reason, dict) or set(reason) != REASON_FIELDS_V2:
        _fail()
    kind = reason.get("kind")
    reference = reason.get("reference")
    score = reason.get("score")
    if kind not in KINDS or reference not in allowed_labels:
        _fail()
    if kind in NULL_SCORE_KINDS:
        if score is not None:
            _fail()
    elif not _valid_score(score):
        _fail()
    if not _valid_length(reason.get("reference_field_length")):
        _fail()


def _validate_maximum_v2(value: Any, allowed_labels: set[str]) -> None:
    if not isinstance(value, dict) or set(value) != MAXIMUM_FIELDS_V2:
        _fail()
    if value.get("reference") not in allowed_labels or not _valid_score(value.get("score")):
        _fail()
    if not _valid_length(value.get("reference_field_length")):
        _fail()


def _validate_protected_v2(value: Any, allowed_labels: set[str]) -> None:
    if not isinstance(value, dict) or set(value) != PROTECTED_FIELDS:
        _fail()
    reasons = value.get("reasons")
    if not isinstance(reasons, list) or not reasons or len(reasons) > 4 * len(allowed_labels):
        _fail()
    for reason in reasons:
        _validate_reason_v2(reason, allowed_labels)
    encoded_reasons = [gate2.canonical_json_bytes(reason) for reason in reasons]
    if len(set(encoded_reasons)) != len(encoded_reasons):
        _fail()
    _validate_maximum_v2(value.get("maximum_token_jaccard"), allowed_labels)
    _validate_maximum_v2(value.get("maximum_character_5gram_jaccard"), allowed_labels)


def _with_reference_length(item: dict[str, Any], reference_field_lengths: dict[str, dict[str, int]]) -> dict[str, Any]:
    length = reference_field_lengths.get(item.get("reference"))
    return {**item, "reference_field_length": length}


def build_row_v2(
    sequence: int,
    slot: dict[str, Any],
    request_hash: str,
    raw_response_hash: str,
    rejection_reason_code: str,
    screen: dict[str, Any],
    allowed_reference_labels: Iterable[str],
    allowed_field_paths: Iterable[str],
    prior_row_hash: str | None,
    candidate_field_length: dict[str, int],
    reference_field_lengths: dict[str, dict[str, int]],
) -> dict[str, Any]:
    """Identical to build_row in every respect except the persisted row also
    carries content-free length metadata: `candidate_field_length` for the
    one candidate field that triggered the rejection, and a
    `reference_field_length` alongside every reason and maximum-score entry
    for the reference it points at. Both parameters must already be reduced
    to integers by the caller (gate2.field_length_metadata) -- this function
    still never receives candidate or reference text."""
    labels = set(allowed_reference_labels)
    fields = set(allowed_field_paths)
    if not labels or not fields:
        _fail()
    if type(sequence) is not int or not 1 <= sequence <= 24:
        _fail()
    if not isinstance(slot, dict) or slot.get("slot") != sequence or slot.get("model") not in EXPECTED_MODELS or not MODEL_RE.fullmatch(str(slot.get("model", ""))) or not MECHANISM_RE.fullmatch(str(slot.get("mechanism_id", ""))):
        _fail()
    if not HASH_RE.fullmatch(request_hash) or not HASH_RE.fullmatch(raw_response_hash):
        _fail()
    if prior_row_hash is not None and (not isinstance(prior_row_hash, str) or not HASH_RE.fullmatch(prior_row_hash)):
        _fail()
    if not _valid_length(candidate_field_length) or not isinstance(reference_field_lengths, dict):
        _fail()
    field_path, protected = _selected_protected_result(rejection_reason_code, screen, fields)
    protected_value = {
        "reasons": [_with_reference_length(reason, reference_field_lengths) for reason in protected.get("structured_reasons", [])],
        "maximum_token_jaccard": _with_reference_length(protected.get("maximum_token_jaccard") or {}, reference_field_lengths),
        "maximum_character_5gram_jaccard": _with_reference_length(protected.get("maximum_character_5gram_jaccard") or {}, reference_field_lengths),
    }
    _validate_protected_v2(protected_value, labels)
    row = gate2.chained_row({
        "artifact": ARTIFACT,
        "schema_version": SCHEMA_VERSION_2,
        "sequence": sequence,
        "schedule_slot": slot["slot"],
        "model": slot["model"],
        "mechanism_id": slot["mechanism_id"],
        "request_hash": request_hash,
        "raw_response_hash": raw_response_hash,
        "rejection_reason_code": rejection_reason_code,
        "field_path": field_path,
        "protected_collision": protected_value,
        "candidate_field_length": candidate_field_length,
        "candidate_text_persisted": False,
        "protected_reference_text_persisted": False,
        "candidate_review_performed": False,
        "corpus_mutation_performed": False,
    }, prior_row_hash)
    validate_row_v2(row, labels, fields)
    return row


def validate_row_v2(row: Any, allowed_reference_labels: Iterable[str], allowed_field_paths: Iterable[str]) -> None:
    labels = set(allowed_reference_labels)
    fields = set(allowed_field_paths)
    if not isinstance(row, dict) or set(row) != ROW_FIELDS_V2:
        _fail()
    if row.get("artifact") != ARTIFACT or row.get("schema_version") != SCHEMA_VERSION_2:
        _fail()
    if type(row.get("sequence")) is not int or not 1 <= row["sequence"] <= 24 or row.get("schedule_slot") != row["sequence"]:
        _fail()
    if row.get("model") not in EXPECTED_MODELS or not MODEL_RE.fullmatch(str(row.get("model", ""))) or not MECHANISM_RE.fullmatch(str(row.get("mechanism_id", ""))):
        _fail()
    if not HASH_RE.fullmatch(str(row.get("request_hash", ""))) or not HASH_RE.fullmatch(str(row.get("raw_response_hash", ""))):
        _fail()
    reason_code = row.get("rejection_reason_code")
    field_path = row.get("field_path")
    if not isinstance(field_path, str) or field_path not in fields or field_path not in EXPECTED_CANDIDATE_FIELD_PATHS or reason_code != field_path + REASON_SUFFIX:
        _fail()
    _validate_protected_v2(row.get("protected_collision"), labels)
    if not _valid_length(row.get("candidate_field_length")):
        _fail()
    for name in ("candidate_text_persisted", "protected_reference_text_persisted", "candidate_review_performed", "corpus_mutation_performed"):
        if row.get(name) is not False:
            _fail()
    prior = row.get("prior_row_hash")
    if prior is not None and (not isinstance(prior, str) or not HASH_RE.fullmatch(prior)):
        _fail()
    payload = {key: value for key, value in row.items() if key != "row_hash"}
    if row.get("row_hash") != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)):
        _fail()
    if gate2.contains_secret(row) or len(gate2.canonical_json_bytes(row)) > MAX_CANONICAL_ROW_BYTES:
        _fail()


def verify_chain_v2(rows: Any, allowed_reference_labels: Iterable[str], allowed_field_paths: Iterable[str]) -> None:
    if not isinstance(rows, list):
        _fail()
    prior = None
    for row in rows:
        validate_row_v2(row, allowed_reference_labels, allowed_field_paths)
        if row.get("prior_row_hash") != prior:
            _fail()
        prior = row["row_hash"]


def validate_rejection_links_v2(rejections: Any, diagnostics: Any, summary: Any, allowed_reference_labels: Iterable[str], allowed_field_paths: Iterable[str]) -> None:
    """Identical to validate_rejection_links except diagnostic rows are
    validated as schema_version-2 rows via verify_chain_v2."""
    if not isinstance(rejections, list) or not isinstance(diagnostics, list) or not isinstance(summary, dict):
        _fail()
    gate2.verify_chain(rejections)
    verify_chain_v2(diagnostics, allowed_reference_labels, allowed_field_paths)
    by_hash = {row["row_hash"]: row for row in diagnostics}
    linked: set[str] = set()
    for rejection in rejections:
        if not isinstance(rejection, dict) or set(rejection) != FUTURE_REJECTION_FIELDS:
            _fail()
        link = rejection.get("output_collision_diagnostic_row_hash")
        protected = isinstance(rejection.get("reason_code"), str) and rejection["reason_code"].endswith(REASON_SUFFIX)
        if protected:
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
    if summary.get("output_collision_diagnostic_count") != len(diagnostics):
        _fail()
    expected_head = diagnostics[-1]["row_hash"] if diagnostics else None
    if summary.get("output_collision_diagnostic_chain_head") != expected_head:
        _fail()
# --- end schema_version 2 additions -------------------------------------------
