"""Validator for the canonical real-manifest-v1 consent/provenance schema,
per real_data_manifest_schema_decision.md (ChatGPT's canonical-schema
decision, accepted after Claude's real_data_manifest_schema_proposal.md).

This module is deliberately separate from real_data_private.py: that module
is generic private-data I/O (canonical JSON, fingerprints, load/save any
JSONL-by-record-id file) and knows nothing about what a valid manifest
*entry* looks like. This module owns the schema itself -- field set, types,
enums, lifecycle nullability, cross-field invariants, collection-wide
uniqueness, operation eligibility, and one-way transitions -- and is the
only place that schema should be encoded.

Nothing here ever touches note content. Every check operates on IDs,
timestamps, enums, booleans, and fingerprints already computed elsewhere.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import real_data_private as rdp

MANIFEST_SCHEMA_VERSION = "real-manifest-v1"

SUPPORTED_CONSENT_VERSIONS = ("real-consent-v1",)
SUPPORTED_SOURCE_KINDS = ("author_supplied_personal_note",)
VALID_SPLITS = ("real_validation", "real_holdout")
VALID_DEIDENTIFICATION_STATUSES = ("pending", "approved", "rejected")
VALID_ANNOTATION_STATUSES = ("not_started", "draft", "in_review", "adjudicated", "excluded")
VALID_WITHDRAWAL_STATUSES = ("active", "withdrawn", "expired")

_RECORD_ID_RE = re.compile(r"^rv_[0-9a-f]{32}$")
_CONTRIBUTOR_ID_RE = re.compile(r"^contributor_[0-9a-f]{32}$")
_ACTOR_ID_RE = re.compile(r"^actor_[0-9a-f]{32}$")
_FINGERPRINT_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

_ALLOWED_USES_KEYS = frozenset({"private_annotation", "private_evaluation", "holdout_eligible", "training", "publication"})

_TOP_LEVEL_FIELDS = frozenset(
    {
        "manifest_schema_version",
        "record_id",
        "contributor_id",
        "consent_version",
        "consented_at_utc",
        "author_confirmed",
        "consent_reviewer_id",
        "allowed_uses",
        "source_kind",
        "split",
        "source_fingerprint",
        "pair_fingerprint",
        "rubric_fingerprint",
        "deidentification_status",
        "deidentified_at_utc",
        "deidentified_by_id",
        "deidentification_reviewer_id",
        "annotation_status",
        "adjudicated_at_utc",
        "annotation_author_id",
        "annotation_reviewer_id",
        "withdrawal_status",
        "withdrawal_status_changed_at_utc",
    }
)


class ManifestValidationError(ValueError):
    pass


class EligibilityError(ValueError):
    pass


class FingerprintMismatchError(ManifestValidationError):
    pass


def verify_fingerprint(*, computed: str, declared: str, field_name: str, record_id: str) -> None:
    """Compares a freshly recomputed fingerprint (bare hex) against the
    manifest's declared value (prefixed or bare) for one record. Shared by
    evaluate_holdout.py and by tests, so the comparison logic that gates a
    real evaluation is the exact logic exercised in adversarial tests --
    not a second, untested inline copy of the same check."""
    declared_bare = declared.removeprefix("sha256:")
    if computed != declared_bare:
        raise FingerprintMismatchError(
            f"{record_id}: recomputed {field_name} does not match the manifest's declared value"
        )


def _fail(record_id: str, reason: str) -> None:
    raise ManifestValidationError(f"{record_id}: {reason}")


def _require_literal_bool(entry: dict, field: str, expected: bool, record_id: str) -> None:
    value = entry.get(field)
    if not isinstance(value, bool) or value is not expected:
        _fail(record_id, f"{field!r} must be literal {expected!r}, got {value!r}")


def _parse_utc(value, field: str, record_id: str) -> datetime:
    if not isinstance(value, str):
        _fail(record_id, f"{field!r} must be an RFC 3339 UTC timestamp string, got {value!r}")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        _fail(record_id, f"{field!r} is not a valid RFC 3339 timestamp: {value!r}")
        raise  # unreachable, keeps type-checkers happy
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(None):
        _fail(record_id, f"{field!r} must be UTC (Z or +00:00), got {value!r}")
    return parsed


def _require_id(value, pattern: re.Pattern, field: str, record_id: str) -> None:
    if not isinstance(value, str) or not pattern.match(value):
        _fail(record_id, f"{field!r} does not match {pattern.pattern}: {value!r}")


def _require_fingerprint_or_none(value, field: str, record_id: str) -> None:
    if value is None:
        return
    if not isinstance(value, str) or not _FINGERPRINT_RE.match(value):
        _fail(record_id, f"{field!r} must be null or match {_FINGERPRINT_RE.pattern} exactly (no coercion): {value!r}")


def _require_null(value, field: str, record_id: str, context: str) -> None:
    if value is not None:
        _fail(record_id, f"{field!r} must be null {context}, got {value!r}")


def _require_non_null(value, field: str, record_id: str, context: str):
    if value is None:
        _fail(record_id, f"{field!r} must not be null {context}")
    return value


def validate_entry(entry: dict) -> None:
    """Structural, type, enum, nullability-by-stage, and cross-field
    validation for a single manifest entry. Independent of any requested
    operation -- see check_evaluation_eligibility for that."""
    if not isinstance(entry, dict):
        raise ManifestValidationError(f"manifest entry is not a JSON object: {entry!r}")

    record_id = entry.get("record_id") if isinstance(entry.get("record_id"), str) else "<unknown>"

    extra = set(entry.keys()) - _TOP_LEVEL_FIELDS
    if extra:
        _fail(record_id, f"unknown field(s) not permitted under {MANIFEST_SCHEMA_VERSION}: {sorted(extra)}")
    missing = _TOP_LEVEL_FIELDS - set(entry.keys())
    if missing:
        _fail(record_id, f"missing required field(s): {sorted(missing)}")

    if entry.get("manifest_schema_version") != MANIFEST_SCHEMA_VERSION:
        _fail(record_id, f"manifest_schema_version must be {MANIFEST_SCHEMA_VERSION!r}, got {entry.get('manifest_schema_version')!r}")

    _require_id(entry.get("record_id"), _RECORD_ID_RE, "record_id", record_id)
    _require_id(entry.get("contributor_id"), _CONTRIBUTOR_ID_RE, "contributor_id", record_id)

    if entry.get("consent_version") not in SUPPORTED_CONSENT_VERSIONS:
        _fail(record_id, f"consent_version must be one of {SUPPORTED_CONSENT_VERSIONS}, got {entry.get('consent_version')!r}")
    consented_at = _parse_utc(entry.get("consented_at_utc"), "consented_at_utc", record_id)

    _require_literal_bool(entry, "author_confirmed", True, record_id)
    _require_id(entry.get("consent_reviewer_id"), _ACTOR_ID_RE, "consent_reviewer_id", record_id)

    allowed_uses = entry.get("allowed_uses")
    if not isinstance(allowed_uses, dict) or set(allowed_uses.keys()) != _ALLOWED_USES_KEYS:
        _fail(record_id, f"allowed_uses must be an object with exactly these keys: {sorted(_ALLOWED_USES_KEYS)}")
    for key in _ALLOWED_USES_KEYS:
        if not isinstance(allowed_uses.get(key), bool):
            _fail(record_id, f"allowed_uses[{key!r}] must be a literal boolean, got {allowed_uses.get(key)!r}")
    if allowed_uses["training"] is not False or allowed_uses["publication"] is not False:
        _fail(record_id, "allowed_uses.training and allowed_uses.publication must always be false")

    if entry.get("source_kind") not in SUPPORTED_SOURCE_KINDS:
        _fail(record_id, f"source_kind must be one of {SUPPORTED_SOURCE_KINDS}, got {entry.get('source_kind')!r}")

    split = entry.get("split")
    if split is not None and split not in VALID_SPLITS:
        _fail(record_id, f"split must be null or one of {VALID_SPLITS}, got {split!r}")

    for field in ("source_fingerprint", "pair_fingerprint", "rubric_fingerprint"):
        _require_fingerprint_or_none(entry.get(field), field, record_id)

    deid_status = entry.get("deidentification_status")
    if deid_status not in VALID_DEIDENTIFICATION_STATUSES:
        _fail(record_id, f"deidentification_status must be one of {VALID_DEIDENTIFICATION_STATUSES}, got {deid_status!r}")

    if deid_status == "pending":
        _require_null(entry.get("deidentified_at_utc"), "deidentified_at_utc", record_id, "while deidentification_status is 'pending'")
        _require_null(entry.get("deidentified_by_id"), "deidentified_by_id", record_id, "while deidentification_status is 'pending'")
        _require_null(entry.get("deidentification_reviewer_id"), "deidentification_reviewer_id", record_id, "while deidentification_status is 'pending'")
        _require_null(entry.get("source_fingerprint"), "source_fingerprint", record_id, "before de-identification is approved")
    else:
        deid_at = _require_non_null(entry.get("deidentified_at_utc"), "deidentified_at_utc", record_id, f"once deidentification_status is {deid_status!r}")
        by_id = _require_non_null(entry.get("deidentified_by_id"), "deidentified_by_id", record_id, f"once deidentification_status is {deid_status!r}")
        reviewer_id = _require_non_null(entry.get("deidentification_reviewer_id"), "deidentification_reviewer_id", record_id, f"once deidentification_status is {deid_status!r}")
        deid_at = _parse_utc(deid_at, "deidentified_at_utc", record_id)
        _require_id(by_id, _ACTOR_ID_RE, "deidentified_by_id", record_id)
        _require_id(reviewer_id, _ACTOR_ID_RE, "deidentification_reviewer_id", record_id)
        if by_id == reviewer_id:
            _fail(record_id, "deidentified_by_id and deidentification_reviewer_id must be independent (different actors)")
        if deid_at < consented_at:
            _fail(record_id, "deidentified_at_utc precedes consented_at_utc -- chronologically impossible")
        if deid_status == "approved":
            _require_non_null(entry.get("source_fingerprint"), "source_fingerprint", record_id, "once deidentification_status is 'approved'")

    annotation_status = entry.get("annotation_status")
    if annotation_status not in VALID_ANNOTATION_STATUSES:
        _fail(record_id, f"annotation_status must be one of {VALID_ANNOTATION_STATUSES}, got {annotation_status!r}")

    if annotation_status == "not_started":
        _require_null(entry.get("adjudicated_at_utc"), "adjudicated_at_utc", record_id, "while annotation_status is 'not_started'")
        _require_null(entry.get("annotation_author_id"), "annotation_author_id", record_id, "while annotation_status is 'not_started'")
        _require_null(entry.get("annotation_reviewer_id"), "annotation_reviewer_id", record_id, "while annotation_status is 'not_started'")
        _require_null(entry.get("pair_fingerprint"), "pair_fingerprint", record_id, "before annotation starts")
        _require_null(entry.get("rubric_fingerprint"), "rubric_fingerprint", record_id, "before annotation starts")
    else:
        author_id = _require_non_null(entry.get("annotation_author_id"), "annotation_author_id", record_id, f"once annotation_status is {annotation_status!r}")
        _require_id(author_id, _ACTOR_ID_RE, "annotation_author_id", record_id)
        if annotation_status == "adjudicated":
            adjudicated_at = _require_non_null(entry.get("adjudicated_at_utc"), "adjudicated_at_utc", record_id, "once annotation_status is 'adjudicated'")
            reviewer_id = _require_non_null(entry.get("annotation_reviewer_id"), "annotation_reviewer_id", record_id, "once annotation_status is 'adjudicated'")
            adjudicated_at = _parse_utc(adjudicated_at, "adjudicated_at_utc", record_id)
            _require_id(reviewer_id, _ACTOR_ID_RE, "annotation_reviewer_id", record_id)
            if author_id == reviewer_id:
                _fail(record_id, "annotation_author_id and annotation_reviewer_id must be independent (different actors)")
            if adjudicated_at < consented_at:
                _fail(record_id, "adjudicated_at_utc precedes consented_at_utc -- chronologically impossible")
            if deid_status != "approved":
                _fail(record_id, "annotation_status is 'adjudicated' but deidentification_status is not 'approved'")
            _require_non_null(entry.get("pair_fingerprint"), "pair_fingerprint", record_id, "once annotation_status is 'adjudicated'")
            _require_non_null(entry.get("rubric_fingerprint"), "rubric_fingerprint", record_id, "once annotation_status is 'adjudicated'")

    if split is not None:
        if deid_status != "approved" or annotation_status != "adjudicated":
            _fail(record_id, "split may only be assigned once de-identification is approved and annotation is adjudicated")
        if split == "real_holdout" and allowed_uses["holdout_eligible"] is not True:
            _fail(record_id, "split is 'real_holdout' but allowed_uses.holdout_eligible is not true")

    withdrawal_status = entry.get("withdrawal_status")
    if withdrawal_status not in VALID_WITHDRAWAL_STATUSES:
        _fail(record_id, f"withdrawal_status must be one of {VALID_WITHDRAWAL_STATUSES}, got {withdrawal_status!r}")
    changed_at = _parse_utc(entry.get("withdrawal_status_changed_at_utc"), "withdrawal_status_changed_at_utc", record_id)
    if changed_at < consented_at:
        _fail(record_id, "withdrawal_status_changed_at_utc precedes consented_at_utc -- chronologically impossible")


def validate_manifest_collection(entries: dict[str, dict], *, pilot_mode: bool = True) -> None:
    """Cross-entry checks: each entry must already pass validate_entry.
    Duplicate source_fingerprint is rejected across every row regardless of
    withdrawal_status -- a withdrawn source must not be reintroducible under
    a fresh record_id (see real_data_manifest_schema_decision.md).

    pilot_mode (default True, fail-safe) governs whether any entry may be
    holdout-assigned/holdout-eligible at all -- this is a write-side/
    assignment-time restriction ("no sealed-holdout population" during the
    validation-only pilot), not a read-side one. upsert_manifest_entry_validated
    inherits this default deliberately, so assigning a new holdout-eligible
    entry during the pilot fails closed by default. A caller evaluating
    entries that already legitimately exist (e.g. evaluate_holdout.py,
    which has its own --milestone/--reason declaration gate) may pass
    pilot_mode=False explicitly -- that's a conscious, visible opt-out at
    the call site, not a silent default, and is about *reading* an
    existing entry, not about whether it was proper to assign it."""
    seen_source_fps: dict[str, str] = {}
    for record_id, entry in entries.items():
        validate_entry(entry)
        sfp = entry.get("source_fingerprint")
        if sfp is not None:
            prior = seen_source_fps.get(sfp)
            if prior is not None:
                raise ManifestValidationError(
                    f"duplicate source_fingerprint shared by {prior!r} and {record_id!r} "
                    "(rejected across all rows, including withdrawn/expired -- see schema decision)"
                )
            seen_source_fps[sfp] = record_id

        if pilot_mode:
            allowed_uses = entry.get("allowed_uses") or {}
            if entry.get("split") == "real_holdout" or allowed_uses.get("holdout_eligible") is True:
                raise ManifestValidationError(
                    f"{record_id}: holdout assignment/eligibility is not permitted during the validation-only pilot"
                )


def _no_duplicate_keys(pairs: list[tuple]) -> dict:
    seen = set()
    for key, _ in pairs:
        if key in seen:
            raise ManifestValidationError(f"duplicate key {key!r} in manifest JSON object")
        seen.add(key)
    return dict(pairs)


def load_manifest_strict(path: Path | None = None, *, pilot_mode: bool = True) -> dict[str, dict]:
    """Strict manifest loader: rejects invalid JSON, blank lines,
    non-object records, duplicate keys inside an object, and duplicate
    record_ids -- the last of these checked before any dict is built, per
    the schema decision's "Strict JSONL loader" requirement. Then validates
    every entry and the collection as a whole."""
    path = path or rdp.MANIFEST_PATH
    if not path.exists():
        return {}

    ordered: list[tuple[int, str, dict]] = []
    seen_ids: set[str] = set()
    with path.open("r", encoding="utf-8") as f:
        for line_no, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                raise ManifestValidationError(f"{path.name}:{line_no}: blank line is not permitted in a manifest file")
            try:
                obj = json.loads(line, object_pairs_hook=_no_duplicate_keys)
            except (json.JSONDecodeError, ManifestValidationError) as e:
                raise ManifestValidationError(f"{path.name}:{line_no}: invalid JSON ({e})") from e
            if not isinstance(obj, dict):
                raise ManifestValidationError(f"{path.name}:{line_no}: record is not a JSON object")
            record_id = obj.get("record_id")
            if not isinstance(record_id, str):
                raise ManifestValidationError(f"{path.name}:{line_no}: missing or non-string 'record_id'")
            if record_id in seen_ids:
                raise ManifestValidationError(f"{path.name}:{line_no}: duplicate record_id {record_id!r} (rejected before dictionary construction)")
            seen_ids.add(record_id)
            ordered.append((line_no, record_id, obj))

    entries = {record_id: obj for _, record_id, obj in ordered}
    validate_manifest_collection(entries, pilot_mode=pilot_mode)
    return entries


def upsert_manifest_entry_validated(entry: dict, *, pilot_mode: bool = True) -> None:
    """Validates entry, the one-way transition from any prior entry with
    the same record_id, and the resulting collection -- all before writing.
    Failed validation leaves the on-disk manifest untouched (validation
    happens entirely before rdp.save_manifest's atomic write)."""
    current = load_manifest_strict(pilot_mode=pilot_mode)
    record_id = entry.get("record_id")
    validate_transition(current.get(record_id), entry)
    updated = {**current, record_id: entry}
    validate_manifest_collection(updated, pilot_mode=pilot_mode)
    rdp.save_manifest(updated)


def check_evaluation_eligibility(entry: dict, *, expected_split: str) -> None:
    """Operation eligibility for using entry in an evaluation against
    expected_split ('real_validation' or 'real_holdout'). Assumes entry
    already passed validate_entry -- this checks the operation-specific
    permission/state requirements on top of that."""
    record_id = entry.get("record_id", "<unknown>")

    def fail(reason: str) -> None:
        raise EligibilityError(f"{record_id}: {reason}")

    if entry.get("withdrawal_status") != "active":
        fail(f"withdrawal_status is {entry.get('withdrawal_status')!r}, not 'active'")
    if entry.get("author_confirmed") is not True:
        fail("author_confirmed is not literal true")
    if entry.get("deidentification_status") != "approved":
        fail(f"deidentification_status is {entry.get('deidentification_status')!r}, not 'approved'")
    if entry.get("annotation_status") != "adjudicated":
        fail(f"annotation_status is {entry.get('annotation_status')!r}, not 'adjudicated'")
    if entry.get("split") != expected_split:
        fail(f"split is {entry.get('split')!r}, expected {expected_split!r}")

    allowed_uses = entry.get("allowed_uses")
    if not isinstance(allowed_uses, dict):
        fail("missing or malformed 'allowed_uses'")
    if allowed_uses.get("training") is not False or allowed_uses.get("publication") is not False:
        fail("allowed_uses.training/publication must always be false")
    if allowed_uses.get("private_evaluation") is not True:
        fail("allowed_uses.private_evaluation is not true")
    if expected_split == "real_holdout" and allowed_uses.get("holdout_eligible") is not True:
        fail("allowed_uses.holdout_eligible is not true")


def validate_transition(old_entry: dict | None, new_entry: dict) -> None:
    """One-way transitions the schema decision requires. Only the
    transitions explicitly and unambiguously specified are enforced here:
    split is assigned at most once and never reassigned; withdrawal never
    reactivates; a source edit (source_fingerprint change) after split
    assignment is rejected rather than silently applied. The broader
    "editing output/rubric resets annotation to pre-adjudicated" behavior
    is intentionally not implemented yet -- it depends on annotation
    tooling that doesn't exist, and a partial heuristic here would be
    worse than an explicit gap. Flagged, not silently skipped."""
    validate_entry(new_entry)
    if old_entry is None:
        return
    record_id = new_entry.get("record_id", "<unknown>")

    old_split = old_entry.get("split")
    new_split = new_entry.get("split")
    if old_split is not None and new_split != old_split:
        raise ManifestValidationError(f"{record_id}: split is immutable once assigned (was {old_split!r}, attempted {new_split!r})")

    old_withdrawal = old_entry.get("withdrawal_status")
    new_withdrawal = new_entry.get("withdrawal_status")
    if old_withdrawal in ("withdrawn", "expired") and new_withdrawal != old_withdrawal:
        raise ManifestValidationError(f"{record_id}: withdrawal_status {old_withdrawal!r} is terminal and cannot change to {new_withdrawal!r}")

    old_source_fp = old_entry.get("source_fingerprint")
    new_source_fp = new_entry.get("source_fingerprint")
    if old_split is not None and old_source_fp is not None and new_source_fp != old_source_fp:
        raise ManifestValidationError(
            f"{record_id}: source_fingerprint cannot change after split assignment -- a separately governed "
            "replacement record is required instead of an in-place source edit"
        )
