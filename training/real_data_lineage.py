"""Immutable scoring-lineage artifacts (review, comparison, adjudication,
decision, status event, dataset snapshot), per
training/real_data_scoring_lineage_withdrawal_design.md (ChatGPT's
architecture decision, accepted after Phase E Tier 3 commit `48ab66b`).

A generation artifact (real_data_eval_logging.py) records only what a
checkpoint produced. Everything in this module records what happened to
that generation afterward: independent review, comparison, adjudication,
and the private decision it may go on to support. No artifact here is
ever edited in place -- status (superseded/invalidated) is derived from
immutable status events, never from mutating the artifact that changed
status. Nothing in this module ever touches note content directly; every
check operates on IDs, fingerprints, booleans, and enums already computed
elsewhere.
"""
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import real_data_eval_logging as rel
import real_data_manifest as rdm
import real_data_private as rdp
import real_data_scoring as rsc

AUDIT_DIR = rel.RESULTS_PRIVATE_DIR / "audit"
STATUS_EVENTS_DIR = AUDIT_DIR / "status_events"
WITHDRAWALS_DIR = AUDIT_DIR / "withdrawals"
DATASET_SNAPSHOTS_DIR = AUDIT_DIR / "dataset_snapshots"
DECISIONS_DIR = rel.RESULTS_PRIVATE_DIR / "decisions"

_ACTOR_ID_RE = re.compile(r"^actor_[0-9a-f]{32}$")

REVIEW_SCHEMA_VERSION = "real-eval-review-v1"
COMPARISON_SCHEMA_VERSION = "real-eval-comparison-v1"
ADJUDICATION_SCHEMA_VERSION = "real-eval-adjudication-v1"
DECISION_SCHEMA_VERSION = "real-eval-decision-v1"
STATUS_EVENT_SCHEMA_VERSION = "real-lineage-status-v1"
SNAPSHOT_SCHEMA_VERSION = "real-dataset-snapshot-v1"

_KIND_SCHEMA_VERSIONS = {
    "review": REVIEW_SCHEMA_VERSION,
    "comparison": COMPARISON_SCHEMA_VERSION,
    "adjudication": ADJUDICATION_SCHEMA_VERSION,
    "decision": DECISION_SCHEMA_VERSION,
    "status_event": STATUS_EVENT_SCHEMA_VERSION,
    "dataset_snapshot": SNAPSHOT_SCHEMA_VERSION,
}

REVIEWER_ROLES = ("chatgpt", "claude")
RESOLUTION_MODES = ("reviewer_agreement", "product_owner_resolution")
DECISION_TYPES = ("curriculum", "training_budget", "seed", "checkpoint", "prompt", "release")
STATUS_VALUES = ("superseded", "invalidated")

# Exact top-level field sets per artifact kind, per the design's "Common
# integrity contract" (reject unknown/missing fields on every load, not
# just on build -- the Phase E lineage/withdrawal implementation review's
# finding 4 confirmed a self-consistent artifact with an extra unknown
# field previously passed the loader as long as its own fingerprint was
# recomputed over the tampered content).
_GENERATION_REF_FIELDS = frozenset({"evaluation_id", "artifact_kind", "artifact_fingerprint"})
_ARTIFACT_REF_FIELDS = frozenset({"artifact_kind", "artifact_id", "artifact_fingerprint"})

_REVIEW_FIELDS = frozenset(
    {
        "schema_version",
        "artifact_kind",
        "review_id",
        "created_at_utc",
        "generation",
        "reviewer_role",
        "reviewer_actor_id",
        "independent_review_attestation",
        "dataset_fingerprint",
        "rubric_schema_version",
        "checkpoint_fingerprint",
        "prompt_contract",
        "scores",
        "review_notes",
        "supersedes_review",
        "artifact_fingerprint",
    }
)
_COMPARISON_FIELDS = frozenset(
    {
        "schema_version",
        "artifact_kind",
        "comparison_id",
        "created_at_utc",
        "generation",
        "chatgpt_review",
        "claude_review",
        "record_comparisons",
        "alignment_status",
        "artifact_fingerprint",
    }
)
_ADJUDICATION_FIELDS = frozenset(
    {
        "schema_version",
        "artifact_kind",
        "adjudication_id",
        "created_at_utc",
        "generation",
        "comparison",
        "chatgpt_review",
        "claude_review",
        "resolution_mode",
        "resolved_by_actor_id",
        "results",
        "aggregate_strict_pass",
        "artifact_fingerprint",
    }
)
_DECISION_FIELDS = frozenset(
    {
        "schema_version",
        "artifact_kind",
        "decision_id",
        "decision_type",
        "created_at_utc",
        "deciding_actor_id",
        "adjudications",
        "outcome",
        "reference",
        "artifact_fingerprint",
    }
)
_STATUS_EVENT_FIELDS = frozenset(
    {
        "schema_version",
        "artifact_kind",
        "status_event_id",
        "created_at_utc",
        "target_artifact",
        "new_status",
        "reason_code",
        "replacement_artifact",
        "withdrawal_id",
        "actor_id",
        "artifact_fingerprint",
    }
)
_SNAPSHOT_FIELDS = frozenset(
    {
        "schema_version",
        "artifact_kind",
        "snapshot_id",
        "created_at_utc",
        "split",
        "creation_reason",
        "active_records",
        "rubric_schema_version",
        "dataset_fingerprint",
        "parent_snapshot",
        "artifact_fingerprint",
    }
)

_ID_PATTERNS = {
    "review": re.compile(r"^review_[0-9a-f]{32}$"),
    "comparison": re.compile(r"^cmp_[0-9a-f]{32}$"),
    "adjudication": re.compile(r"^adj_[0-9a-f]{32}$"),
    "decision": re.compile(r"^dec_[0-9a-f]{32}$"),
    "status_event": re.compile(r"^sev_[0-9a-f]{32}$"),
    "dataset_snapshot": re.compile(r"^snap_[0-9a-f]{32}$"),
    "withdrawal": re.compile(r"^wd_[0-9a-f]{32}$"),
}


class LineageValidationError(ValueError):
    pass


class LineageArtifactExistsError(FileExistsError):
    pass


def _require_actor_id(value, field_name: str) -> None:
    if not isinstance(value, str) or not _ACTOR_ID_RE.match(value):
        raise LineageValidationError(f"{field_name} must match {_ACTOR_ID_RE.pattern}, got {value!r}")


def new_review_id() -> str:
    return f"review_{uuid.uuid4().hex}"


def new_comparison_id() -> str:
    return f"cmp_{uuid.uuid4().hex}"


def new_adjudication_id() -> str:
    return f"adj_{uuid.uuid4().hex}"


def new_decision_id() -> str:
    return f"dec_{uuid.uuid4().hex}"


def new_status_event_id() -> str:
    return f"sev_{uuid.uuid4().hex}"


def new_snapshot_id() -> str:
    return f"snap_{uuid.uuid4().hex}"


def new_withdrawal_id() -> str:
    return f"wd_{uuid.uuid4().hex}"


def lineage_root_for(split: str, evaluation_id: str, milestone: str | None = None) -> Path:
    """The lineage/<evaluation_id>/ directory beneath a generation's own
    approved split root -- reuses real_data_eval_logging.py's identifier
    and split-root validation rather than re-implementing it."""
    evaluation_id = rel._validate_identifier(evaluation_id, "evaluation_id")
    root = rel._root_for_split(split)
    if split == "real_validation":
        path = root / "lineage" / evaluation_id
    else:
        if not milestone:
            raise ValueError("milestone is required for real_holdout lineage paths")
        milestone = rel._validate_identifier(milestone, "milestone")
        path = root / milestone / "lineage" / evaluation_id
    rel._validate_split_root(path, split)
    return path


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
        return True
    except ValueError:
        return False


def _validate_before_save(artifact: dict, kind: str, path: Path, *, expected_root: Path) -> None:
    """Re-validates an artifact's exact schema (including nested reference
    shapes and its own ID format) and recomputed fingerprint, and confirms
    the destination path is contained within the correct approved root --
    immediately before any directory or file is created. A builder already
    validates once before returning, but nothing previously stopped a
    caller from mutating the in-memory dict (most importantly, the ID
    field the destination path is derived from) between build and save.
    Per the Phase E lineage/withdrawal third review's finding 2, a review
    whose review_id was replaced with a path-shaped value after building
    -- with the fingerprint recomputed over the tampered content -- was
    written successfully outside its approved lineage root."""
    _assert_exact_fields(artifact, kind, path)
    computed_fp = f"sha256:{rdp.artifact_fingerprint(artifact)}"
    if artifact.get("artifact_fingerprint") != computed_fp:
        raise LineageValidationError(f"{path}: artifact_fingerprint does not match recomputed content -- refusing to save")
    if not _is_relative_to(path, expected_root):
        raise LineageValidationError(f"{path}: resolved save path escapes the approved root {expected_root}")


def _save_artifact_exclusive(path: Path, artifact: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(artifact, indent=2, ensure_ascii=False)
    try:
        with path.open("x", encoding="utf-8") as f:
            f.write(payload)
    except FileExistsError as e:
        raise LineageArtifactExistsError(f"Refusing to overwrite an existing artifact at {path} -- lineage artifacts are immutable.") from e
    return path


_KIND_METADATA = {
    "review": {"fields": _REVIEW_FIELDS, "id_field": "review_id", "id_pattern": _ID_PATTERNS["review"]},
    "comparison": {"fields": _COMPARISON_FIELDS, "id_field": "comparison_id", "id_pattern": _ID_PATTERNS["comparison"]},
    "adjudication": {"fields": _ADJUDICATION_FIELDS, "id_field": "adjudication_id", "id_pattern": _ID_PATTERNS["adjudication"]},
    "decision": {"fields": _DECISION_FIELDS, "id_field": "decision_id", "id_pattern": _ID_PATTERNS["decision"]},
    "status_event": {"fields": _STATUS_EVENT_FIELDS, "id_field": "status_event_id", "id_pattern": _ID_PATTERNS["status_event"]},
    "dataset_snapshot": {"fields": _SNAPSHOT_FIELDS, "id_field": "snapshot_id", "id_pattern": _ID_PATTERNS["dataset_snapshot"]},
}

# Per-kind nested single-reference fields: {kind: {field_name: (expected_ref_field_set, nullable)}}.
# Per the Phase E lineage/withdrawal second review's finding 3, a nested
# reference (e.g. a status event's target_artifact) was never checked for
# its own exact field set on load -- an unknown field smuggled inside a
# nested dict passed as long as the top-level fields and self-fingerprint
# were consistent. real_data_withdrawal.py extends both dicts below via
# register_kind_metadata for its own withdrawal_plan/withdrawal_completion
# kinds, which have no nested reference fields of their own.
_NESTED_REF_FIELDS = {
    "review": {"generation": (_GENERATION_REF_FIELDS, False)},
    "comparison": {
        "generation": (_GENERATION_REF_FIELDS, False),
        "chatgpt_review": (_ARTIFACT_REF_FIELDS, False),
        "claude_review": (_ARTIFACT_REF_FIELDS, False),
    },
    "adjudication": {
        "generation": (_GENERATION_REF_FIELDS, False),
        "comparison": (_ARTIFACT_REF_FIELDS, False),
        "chatgpt_review": (_ARTIFACT_REF_FIELDS, False),
        "claude_review": (_ARTIFACT_REF_FIELDS, False),
    },
    "status_event": {
        "target_artifact": (_ARTIFACT_REF_FIELDS, False),
        "replacement_artifact": (_ARTIFACT_REF_FIELDS, True),
    },
    "dataset_snapshot": {"parent_snapshot": (_ARTIFACT_REF_FIELDS, True)},
}
# Per-kind nested list-of-reference fields: {kind: {field_name: expected_ref_field_set}}.
_NESTED_REF_LIST_FIELDS = {
    "decision": {"adjudications": _ARTIFACT_REF_FIELDS},
}


def register_kind_metadata(kind: str, *, fields: frozenset, id_field: str, id_pattern: re.Pattern) -> None:
    """Lets a sibling module (real_data_withdrawal.py, for its
    withdrawal_plan/withdrawal_completion kinds) extend the exact-field-set
    registry _load_artifact_verified enforces, without real_data_lineage.py
    needing to know that module's schemas itself. Per the Phase E lineage/
    withdrawal second review's finding 3: withdrawal_plan/withdrawal_completion
    were never registered here, so _assert_exact_fields silently no-op'd for
    them and a plan/completion with an unknown or missing field passed the
    strict loader as long as its own fingerprint was recomputed over the
    tampered content."""
    if kind in _KIND_METADATA:
        raise LineageValidationError(f"kind {kind!r} is already registered")
    _KIND_METADATA[kind] = {"fields": fields, "id_field": id_field, "id_pattern": id_pattern}


def _assert_ref_shape(ref, *, expected_fields: frozenset, field_name: str, context_id, nullable: bool) -> None:
    if ref is None:
        if nullable:
            return
        raise LineageValidationError(f"{context_id}: {field_name} must not be null")
    if not isinstance(ref, dict) or set(ref.keys()) != expected_fields:
        raise LineageValidationError(f"{context_id}: {field_name} does not have the exact expected reference field set {sorted(expected_fields)}")


def _assert_exact_fields(obj: dict, kind: str, context_id) -> None:
    """Rejects unknown or missing top-level fields for a known artifact
    kind -- called both after loading from disk and, in each builder,
    just before returning, so an in-memory artifact can never drift from
    its schema either. A kind with no registered metadata (e.g.
    'generation', validated separately in real_data_eval_logging.py) is
    skipped, not silently accepted as fine -- callers for registered
    kinds always pass one of the keys in _KIND_METADATA. Also recurses
    into every registered nested single-reference and reference-list
    field, checking each nested dict's exact field set the same way."""
    meta = _KIND_METADATA.get(kind)
    if meta is None:
        return
    extra = set(obj.keys()) - meta["fields"]
    if extra:
        raise LineageValidationError(f"{context_id}: unknown {kind} field(s) not permitted: {sorted(extra)}")
    missing = meta["fields"] - set(obj.keys())
    if missing:
        raise LineageValidationError(f"{context_id}: {kind} missing required field(s): {sorted(missing)}")
    own_id = obj.get(meta["id_field"])
    if not isinstance(own_id, str) or not meta["id_pattern"].match(own_id):
        raise LineageValidationError(f"{context_id}: {meta['id_field']} is malformed: {own_id!r}")
    for field_name, (expected_fields, nullable) in _NESTED_REF_FIELDS.get(kind, {}).items():
        _assert_ref_shape(obj.get(field_name), expected_fields=expected_fields, field_name=field_name, context_id=context_id, nullable=nullable)
    for field_name, expected_fields in _NESTED_REF_LIST_FIELDS.get(kind, {}).items():
        for i, item in enumerate(obj.get(field_name, [])):
            _assert_ref_shape(item, expected_fields=expected_fields, field_name=f"{field_name}[{i}]", context_id=context_id, nullable=False)


def _load_artifact_verified(path: Path, *, expected_schema_version: str, expected_kind: str) -> dict:
    """Loads and verifies: duplicate-key-free JSON, schema/kind match,
    exact field set for the kind including nested reference shapes
    (reject unknown or missing top-level or nested-reference fields -- a
    self-consistent artifact with an extra field must not pass just
    because its own fingerprint was recomputed over that tampered
    content), a well-formed created_at_utc, and that the recomputed
    artifact_fingerprint matches the stored one."""
    path = Path(path)
    if not path.exists():
        raise LineageValidationError(f"{path}: artifact does not exist")
    try:
        artifact = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=rdm.reject_duplicate_keys)
    except (json.JSONDecodeError, rdm.DuplicateJSONKeyError) as e:
        raise LineageValidationError(f"{path}: invalid JSON ({e})") from e
    if not isinstance(artifact, dict):
        raise LineageValidationError(f"{path}: artifact is not a JSON object")
    if artifact.get("schema_version") != expected_schema_version:
        raise LineageValidationError(f"{path}: schema_version is {artifact.get('schema_version')!r}, expected {expected_schema_version!r}")
    if artifact.get("artifact_kind") != expected_kind:
        raise LineageValidationError(f"{path}: artifact_kind is {artifact.get('artifact_kind')!r}, expected {expected_kind!r}")
    _assert_exact_fields(artifact, expected_kind, path)
    try:
        rdm.validate_utc_timestamp(artifact.get("created_at_utc"), "created_at_utc")
    except rdm.ManifestValidationError as e:
        raise LineageValidationError(f"{path}: {e}") from e
    declared_fp = artifact.get("artifact_fingerprint", "")
    computed_fp = f"sha256:{rdp.artifact_fingerprint(artifact)}"
    if declared_fp != computed_fp:
        raise LineageValidationError(f"{path}: artifact_fingerprint mismatch -- artifact may have been altered on disk")
    return artifact


def _artifact_ref(artifact: dict, id_field: str) -> dict:
    """Normalized parent/target reference: every artifact kind uses a
    different ID field name (evaluation_id, review_id, ...) but status
    events and cross-artifact references need one common shape."""
    return {
        "artifact_kind": artifact["artifact_kind"],
        "artifact_id": artifact[id_field],
        "artifact_fingerprint": artifact["artifact_fingerprint"],
    }


def _require_unique_record_ids(items: list[dict], *, context_label: str) -> list[str]:
    """Thin wrapper around the shared rdm.require_unique_record_ids,
    re-raising as this module's own error type -- see that function's
    docstring for why this check exists everywhere a list of records is
    about to be converted into a set or dict."""
    try:
        return rdm.require_unique_record_ids(items, context_label=context_label)
    except rdm.DuplicateRecordIdError as e:
        raise LineageValidationError(str(e)) from e




def build_review_score_record(*, generation_record: dict, rubric: dict, scores: dict, capability_checks: dict, failure_labels: list[str]) -> dict:
    """One complete score record for one generation record. rubric: the
    loaded, strictly-validated private rubric for this record_id.
    rubric["capability_checks"] (per datasets/REAL_DATA_ANNOTATION_GUIDE.md's
    documented private rubric schema -- required, fails closed if the key
    is missing entirely; an explicit empty list is valid and means no
    capability checks apply to this record) is the list of required check
    names; the capability_checks *parameter* here is the reviewer's
    submitted name->pass/fail dict, which must cover that list exactly."""
    record_id = generation_record["record_id"]
    # Full schema + identity validation (record_id match, adjudicated
    # status, well-formed fingerprint, exact field set) -- the same
    # validator load_rubrics_strict applies, re-run here as a
    # defense-in-depth boundary check rather than trusting a caller-
    # supplied rubric dict at face value.
    try:
        rdm._validate_rubric_entry(rubric, record_id)
    except rdm.ManifestValidationError as e:
        raise LineageValidationError(f"{record_id}: submitted rubric failed strict validation: {e}") from e
    # The rubric's *content* must be exactly what was bound to this record
    # at generation time -- per the Phase E lineage/withdrawal second
    # review's finding 2, a caller could previously substitute any rubric
    # object (even an unrelated one) as long as it had a capability_checks
    # key, since nothing ever compared the submitted rubric's own
    # fingerprint against generation_record["rubric_fingerprint"].
    try:
        rdm.verify_fingerprint(
            computed=rdp.rubric_fingerprint(rubric),
            declared=generation_record["rubric_fingerprint"],
            field_name="rubric_fingerprint",
            record_id=record_id,
        )
    except rdm.ManifestValidationError as e:
        raise LineageValidationError(f"{record_id}: submitted rubric does not match the fingerprint bound at generation time: {e}") from e

    required_check_names = rubric["capability_checks"]
    expected_checks = set(required_check_names)
    if set(capability_checks.keys()) != expected_checks:
        raise LineageValidationError(
            f"{record_id}: submitted capability check keys must exactly match the rubric's capability_checks -- "
            f"missing {sorted(expected_checks - set(capability_checks.keys()))}, "
            f"extra {sorted(set(capability_checks.keys()) - expected_checks)}"
        )
    if len(set(failure_labels)) != len(failure_labels):
        raise LineageValidationError(f"{record_id}: failure_labels contains a duplicate")
    unknown_labels = set(failure_labels) - rsc.FAILURE_LABEL_VOCABULARY
    if unknown_labels:
        raise LineageValidationError(f"{record_id}: unknown failure label(s) {sorted(unknown_labels)} -- not in the frozen vocabulary")

    base = {
        "record_id": record_id,
        "format_valid": generation_record["format_valid"],
        "scores": {dim: None for dim in rsc.SEMANTIC_DIMENSIONS},
        "capability_checks": {k: None for k in expected_checks},
        "strict_pass": None,
        "failure_labels": [],
        "review_status": "unscored",
    }
    scored = rsc.apply_scores(base, scores=scores, capability_checks=capability_checks, failure_labels=list(failure_labels), review_status="scored")
    if scored["strict_pass"] is None:
        raise LineageValidationError(f"{record_id}: a review score record must be fully scored -- no null dimension or capability check")

    return {
        "record_id": record_id,
        "generation_raw_output_fingerprint": generation_record["raw_output_fingerprint"],
        "rubric_fingerprint": generation_record["rubric_fingerprint"],
        "format_valid": scored["format_valid"],
        "scores": scored["scores"],
        "capability_checks": scored["capability_checks"],
        "failure_labels": scored["failure_labels"],
        "strict_pass": scored["strict_pass"],
    }


_REVIEW_SCORE_FIELDS = frozenset(
    {"record_id", "generation_raw_output_fingerprint", "rubric_fingerprint", "format_valid", "scores", "capability_checks", "failure_labels", "strict_pass"}
)


def _verify_stored_score_record(score: dict, *, rubric: dict) -> None:
    """Re-validates an already-built, stored score record (loaded from a
    saved review) against its bound rubric. Per the Phase E lineage/
    withdrawal third review's finding 3: the generic artifact loader only
    checks a review's top-level shape, not each score record's exact field
    set or whether its capability-check keys and strict_pass still
    genuinely reflect the fingerprint-bound rubric. A stored review file
    can be self-consistent (its own fingerprint recomputed over tampered
    content) while a required capability check has silently been removed
    -- this closes that gap by re-deriving the required check set from a
    freshly supplied rubric and recomputing strict_pass, rather than
    trusting whatever the file claims."""
    if not isinstance(score, dict) or set(score.keys()) != _REVIEW_SCORE_FIELDS:
        raise LineageValidationError(f"stored score record does not have the exact expected field set {sorted(_REVIEW_SCORE_FIELDS)}")
    record_id = score["record_id"]
    try:
        rdm._validate_rubric_entry(rubric, record_id)
    except rdm.ManifestValidationError as e:
        raise LineageValidationError(f"{record_id}: rubric supplied to verify a stored score failed strict validation: {e}") from e
    try:
        rdm.verify_fingerprint(
            computed=rdp.rubric_fingerprint(rubric),
            declared=score["rubric_fingerprint"],
            field_name="rubric_fingerprint",
            record_id=record_id,
        )
    except rdm.ManifestValidationError as e:
        raise LineageValidationError(f"{record_id}: stored score's rubric_fingerprint does not match the supplied rubric: {e}") from e

    expected_checks = set(rubric["capability_checks"])
    if not isinstance(score.get("scores"), dict) or set(score["scores"].keys()) != set(rsc.SEMANTIC_DIMENSIONS):
        raise LineageValidationError(f"{record_id}: stored scores do not have the exact expected semantic-dimension keys")
    if not isinstance(score.get("capability_checks"), dict) or set(score["capability_checks"].keys()) != expected_checks:
        raise LineageValidationError(f"{record_id}: stored capability_checks do not exactly match the rubric's required checks {sorted(expected_checks)}")
    failure_labels = score.get("failure_labels")
    if not isinstance(failure_labels, list) or len(set(failure_labels)) != len(failure_labels) or not set(failure_labels) <= rsc.FAILURE_LABEL_VOCABULARY:
        raise LineageValidationError(f"{record_id}: stored failure_labels are malformed, duplicated, or contain an unknown label")
    if not isinstance(score.get("format_valid"), bool):
        raise LineageValidationError(f"{record_id}: stored format_valid must be a literal boolean")

    recomputed = rsc.compute_strict_pass({**score, "review_status": "scored"})
    if recomputed is None:
        raise LineageValidationError(f"{record_id}: stored score record is not fully scored")
    if recomputed != score.get("strict_pass"):
        raise LineageValidationError(f"{record_id}: stored strict_pass does not match the value recomputed from its own scores -- possible tampering")


def build_review_artifact(
    *,
    generation_path: Path,
    reviewer_role: str,
    reviewer_actor_id: str,
    independent_review_attestation: bool,
    scores: list[dict],
    review_notes: str | None = None,
    supersedes_review: dict | None = None,
) -> dict:
    """generation_path: the actual stored path of the generation artifact
    this review is about -- loaded, verified, and required to be 'active'
    here (see load_and_require_active_parent), never a caller-supplied
    in-memory dict. scores: one build_review_score_record() output per
    generation record -- no omissions, no extras."""
    if reviewer_role not in REVIEWER_ROLES:
        raise LineageValidationError(f"reviewer_role must be one of {REVIEWER_ROLES}, got {reviewer_role!r}")
    _require_actor_id(reviewer_actor_id, "reviewer_actor_id")
    if independent_review_attestation is not True:
        raise LineageValidationError("independent_review_attestation must be literal True -- a review cannot be recorded without attesting independence")

    generation = load_and_require_active_parent(generation_path, expected_kind="generation", parent_label="generation")
    _require_unique_record_ids(generation["results"], context_label="generation results")
    _require_unique_record_ids(scores, context_label="review scores")
    generation_record_ids = {r["record_id"] for r in generation["results"]}
    score_record_ids = {s["record_id"] for s in scores}
    if generation_record_ids != score_record_ids:
        raise LineageValidationError(
            f"review must cover exactly the generation's record set -- "
            f"missing {sorted(generation_record_ids - score_record_ids)}, extra {sorted(score_record_ids - generation_record_ids)}"
        )

    artifact = {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "artifact_kind": "review",
        "review_id": new_review_id(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "generation": {
            "evaluation_id": generation["evaluation_id"],
            "artifact_kind": generation["artifact_kind"],
            "artifact_fingerprint": generation["artifact_fingerprint"],
        },
        "reviewer_role": reviewer_role,
        "reviewer_actor_id": reviewer_actor_id,
        "independent_review_attestation": True,
        "dataset_fingerprint": generation["dataset"]["fingerprint"],
        "rubric_schema_version": generation["dataset"]["rubric_schema_version"],
        "checkpoint_fingerprint": generation["checkpoint"]["fingerprint"],
        "prompt_contract": generation["prompt_contract"],
        "scores": scores,
        "review_notes": review_notes,
        "supersedes_review": supersedes_review,
    }
    artifact["artifact_fingerprint"] = f"sha256:{rdp.artifact_fingerprint(artifact)}"
    _assert_exact_fields(artifact, "review", artifact["review_id"])
    return artifact


def _review_path(split: str, evaluation_id: str, review_id: str, milestone: str | None = None) -> Path:
    return lineage_root_for(split, evaluation_id, milestone) / "reviews" / f"{review_id}.json"


def save_review_artifact(review: dict, *, split: str, milestone: str | None = None) -> Path:
    path = _review_path(split, review["generation"]["evaluation_id"], review["review_id"], milestone)
    _validate_before_save(review, "review", path, expected_root=lineage_root_for(split, review["generation"]["evaluation_id"], milestone))
    return _save_artifact_exclusive(path, review)


def load_review_verified(path: Path, generation: dict, rubrics: dict[str, dict]) -> dict:
    """Loads a review parent (canonical path, active status -- see
    load_and_require_active_parent) and cross-checks it against its
    claimed generation parent: exact fingerprint match, matching copied
    dataset/checkpoint/rubric-schema fingerprints, and an exactly-matching
    record set with per-record raw-output/rubric-fingerprint/format-
    validity agreement. Also re-validates every stored score record
    against its fingerprint-bound rubric (see _verify_stored_score_record)
    -- per the Phase E lineage/withdrawal third review's finding 3, a
    self-consistent but tampered review (e.g. a required capability check
    silently removed, with the fingerprint recomputed over the tampered
    content) must not pass just because its own hash is internally
    consistent. rubrics: {record_id: rubric}, one entry per record this
    review covers."""
    review = load_and_require_active_parent(path, expected_kind="review", parent_label="review")
    _require_unique_record_ids(review["scores"], context_label="loaded review scores")
    # review's shape (including "generation") is guaranteed by the fingerprint
    # check above -- it's byte-identical to what build_review_artifact produced.
    gen_ref = review["generation"]
    if gen_ref["artifact_kind"] != "generation":
        raise LineageValidationError(f"{path}: review's parent reference is not kind 'generation'")
    if gen_ref["evaluation_id"] != generation["evaluation_id"] or gen_ref["artifact_fingerprint"] != generation["artifact_fingerprint"]:
        raise LineageValidationError(f"{path}: review's generation reference does not match the verified generation artifact")
    if review.get("dataset_fingerprint") != generation["dataset"]["fingerprint"]:
        raise LineageValidationError(f"{path}: review's copied dataset_fingerprint does not match generation")
    if review.get("checkpoint_fingerprint") != generation["checkpoint"]["fingerprint"]:
        raise LineageValidationError(f"{path}: review's copied checkpoint_fingerprint does not match generation")
    if review.get("rubric_schema_version") != generation["dataset"]["rubric_schema_version"]:
        raise LineageValidationError(f"{path}: review's copied rubric_schema_version does not match generation")

    generation_by_id = {r["record_id"]: r for r in generation["results"]}
    review_record_ids = {s["record_id"] for s in review["scores"]}
    if set(generation_by_id.keys()) != review_record_ids:
        raise LineageValidationError(f"{path}: review record set does not exactly match generation record set")
    for score in review["scores"]:
        gen_r = generation_by_id[score["record_id"]]
        if score["generation_raw_output_fingerprint"] != gen_r["raw_output_fingerprint"]:
            raise LineageValidationError(f"{path}: {score['record_id']}: review's raw_output_fingerprint does not match generation")
        if score["rubric_fingerprint"] != gen_r["rubric_fingerprint"]:
            raise LineageValidationError(f"{path}: {score['record_id']}: review's rubric_fingerprint does not match generation")
        if score["format_valid"] != gen_r["format_valid"]:
            raise LineageValidationError(f"{path}: {score['record_id']}: review's format_valid does not match generation")
        rubric = rubrics.get(score["record_id"])
        if rubric is None:
            raise LineageValidationError(f"{path}: {score['record_id']}: no rubric available to verify this stored score")
        _verify_stored_score_record(score, rubric=rubric)
    return review




def build_comparison_artifact(*, chatgpt_review_path: Path, claude_review_path: Path, generation_path: Path, rubrics: dict[str, dict]) -> dict:
    """chatgpt_review_path/claude_review_path: the actual stored paths of
    both parent reviews. generation_path/rubrics: required to load each
    review through a generation- and rubric-aware verified path
    (load_review_verified), not only the generic top-level loader -- per
    the Phase E lineage/withdrawal third review's finding 3, the generic
    loader alone does not re-validate a stored review's score records
    against their bound rubric, so a tampered-but-self-consistent review
    could otherwise pass."""
    generation = load_and_require_active_parent(generation_path, expected_kind="generation", parent_label="generation")
    chatgpt_review = load_review_verified(chatgpt_review_path, generation, rubrics)
    claude_review = load_review_verified(claude_review_path, generation, rubrics)
    if chatgpt_review["reviewer_role"] != "chatgpt":
        raise LineageValidationError("chatgpt_review must have reviewer_role 'chatgpt'")
    if claude_review["reviewer_role"] != "claude":
        raise LineageValidationError("claude_review must have reviewer_role 'claude'")
    if chatgpt_review["reviewer_actor_id"] == claude_review["reviewer_actor_id"]:
        raise LineageValidationError("chatgpt and claude reviews must use distinct reviewer actor IDs")
    if chatgpt_review["generation"] != claude_review["generation"]:
        raise LineageValidationError("both reviews must share the exact same generation parent reference -- cannot compare reviews of different generations")

    _require_unique_record_ids(chatgpt_review["scores"], context_label="chatgpt_review scores")
    _require_unique_record_ids(claude_review["scores"], context_label="claude_review scores")
    chatgpt_by_id = {s["record_id"]: s for s in chatgpt_review["scores"]}
    claude_by_id = {s["record_id"]: s for s in claude_review["scores"]}
    if set(chatgpt_by_id.keys()) != set(claude_by_id.keys()):
        raise LineageValidationError("both reviews must cover exactly the same record set to be compared")

    record_comparisons = []
    any_disagreement = False
    for record_id in sorted(chatgpt_by_id.keys()):
        c, l = chatgpt_by_id[record_id], claude_by_id[record_id]
        if c["generation_raw_output_fingerprint"] != l["generation_raw_output_fingerprint"] or c["rubric_fingerprint"] != l["rubric_fingerprint"]:
            raise LineageValidationError(f"{record_id}: reviews bind different raw-output/rubric fingerprints -- not comparable")
        score_diffs = {dim: [c["scores"][dim], l["scores"][dim]] for dim in rsc.SEMANTIC_DIMENSIONS if c["scores"][dim] != l["scores"][dim]}
        all_checks = set(c["capability_checks"].keys()) | set(l["capability_checks"].keys())
        check_diffs = {k: [c["capability_checks"].get(k), l["capability_checks"].get(k)] for k in all_checks if c["capability_checks"].get(k) != l["capability_checks"].get(k)}
        label_diff = sorted(set(c["failure_labels"]) ^ set(l["failure_labels"]))
        strict_pass_diff = c["strict_pass"] != l["strict_pass"]
        record_disagrees = bool(score_diffs or check_diffs or label_diff or strict_pass_diff)
        any_disagreement = any_disagreement or record_disagrees
        record_comparisons.append(
            {
                "record_id": record_id,
                "score_disagreements": score_diffs,
                "capability_check_disagreements": check_diffs,
                "failure_label_symmetric_difference": label_diff,
                "strict_pass_disagreement": strict_pass_diff,
            }
        )

    artifact = {
        "schema_version": COMPARISON_SCHEMA_VERSION,
        "artifact_kind": "comparison",
        "comparison_id": new_comparison_id(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "generation": chatgpt_review["generation"],
        "chatgpt_review": _artifact_ref(chatgpt_review, "review_id"),
        "claude_review": _artifact_ref(claude_review, "review_id"),
        "record_comparisons": record_comparisons,
        "alignment_status": "disagreement" if any_disagreement else "aligned",
    }
    artifact["artifact_fingerprint"] = f"sha256:{rdp.artifact_fingerprint(artifact)}"
    _assert_exact_fields(artifact, "comparison", artifact["comparison_id"])
    return artifact


def _comparison_path(split: str, evaluation_id: str, comparison_id: str, milestone: str | None = None) -> Path:
    return lineage_root_for(split, evaluation_id, milestone) / "comparisons" / f"{comparison_id}.json"


def save_comparison_artifact(comparison: dict, *, split: str, milestone: str | None = None) -> Path:
    path = _comparison_path(split, comparison["generation"]["evaluation_id"], comparison["comparison_id"], milestone)
    _validate_before_save(comparison, "comparison", path, expected_root=lineage_root_for(split, comparison["generation"]["evaluation_id"], milestone))
    return _save_artifact_exclusive(path, comparison)




def build_adjudication_artifact(
    *,
    comparison_path: Path,
    chatgpt_review_path: Path,
    claude_review_path: Path,
    generation_path: Path,
    resolution_mode: str,
    rubrics: dict[str, dict] | None = None,
    resolved_by_actor_id: str | None = None,
    final_scores: list[dict] | None = None,
) -> dict:
    """comparison_path/chatgpt_review_path/claude_review_path: the actual
    stored paths of all three parents -- each loaded, verified, and
    required to be 'active' here (see load_and_require_active_parent),
    never caller-supplied in-memory dicts. generation_path/rubrics: both
    reviews are loaded through the generation- and rubric-aware verified
    path (load_review_verified) regardless of resolution_mode, per the
    Phase E lineage/withdrawal third review's finding 3 -- a tampered-but-
    self-consistent stored review must not pass just because its own
    fingerprint checks out. rubrics is also used directly for
    product_owner_resolution, to re-validate the capability-check key
    contract and failure-label vocabulary for each disputed record (per
    the Phase E lineage/withdrawal implementation review's finding 5: a
    product-owner override was previously checked only by record-ID set
    and a blind strict_pass recompute, with no re-validation of the
    submitted score shape or its binding to the original generation/
    rubric)."""
    if resolution_mode not in RESOLUTION_MODES:
        raise LineageValidationError(f"resolution_mode must be one of {RESOLUTION_MODES}, got {resolution_mode!r}")
    if rubrics is None:
        raise LineageValidationError("rubrics (record_id -> rubric) is required to verify both review parents")
    comparison = load_and_require_active_parent(comparison_path, expected_kind="comparison", parent_label="comparison")
    generation = load_and_require_active_parent(generation_path, expected_kind="generation", parent_label="generation")
    chatgpt_review = load_review_verified(chatgpt_review_path, generation, rubrics)
    claude_review = load_review_verified(claude_review_path, generation, rubrics)
    if comparison["chatgpt_review"] != _artifact_ref(chatgpt_review, "review_id"):
        raise LineageValidationError("comparison's chatgpt_review reference does not match the supplied chatgpt_review")
    if comparison["claude_review"] != _artifact_ref(claude_review, "review_id"):
        raise LineageValidationError("comparison's claude_review reference does not match the supplied claude_review")

    if resolution_mode == "reviewer_agreement":
        if comparison["alignment_status"] != "aligned":
            raise LineageValidationError("reviewer_agreement adjudication requires an aligned comparison")
        _require_unique_record_ids(chatgpt_review["scores"], context_label="chatgpt_review scores")
        final_by_id = {s["record_id"]: s for s in chatgpt_review["scores"]}
        resolved_by_actor_id = None
    else:
        if comparison["alignment_status"] != "disagreement":
            raise LineageValidationError("product_owner_resolution is only valid when the comparison shows disagreement")
        if resolved_by_actor_id is None:
            raise LineageValidationError("product_owner_resolution requires resolved_by_actor_id")
        _require_actor_id(resolved_by_actor_id, "resolved_by_actor_id")
        if not final_scores:
            raise LineageValidationError("product_owner_resolution requires final_scores for the disputed fields")
        _require_unique_record_ids(final_scores, context_label="final_scores")
        comparison_record_ids = {rc["record_id"] for rc in comparison["record_comparisons"]}
        final_record_ids = {s["record_id"] for s in final_scores}
        if comparison_record_ids != final_record_ids:
            raise LineageValidationError("final_scores must cover exactly the compared record set")

        # Every immutable binding field (raw-output/rubric fingerprint,
        # format_valid) must match what the original reviews recorded --
        # both reviews already bind the same values for each record, per
        # build_comparison_artifact's own fingerprint-match check, so
        # chatgpt_review is an equally valid source of truth here. Only
        # scores/capability_checks/failure_labels may differ. Re-running
        # build_review_score_record re-validates the full capability-check
        # contract and failure-label vocabulary, not just strict_pass.
        original_by_id = {s["record_id"]: s for s in chatgpt_review["scores"]}
        final_by_id = {}
        for entry in final_scores:
            record_id = entry["record_id"]
            original = original_by_id[record_id]
            for immutable_field in ("generation_raw_output_fingerprint", "rubric_fingerprint", "format_valid"):
                if entry.get(immutable_field) != original[immutable_field]:
                    raise LineageValidationError(f"{record_id}: final_scores may not change {immutable_field!r} -- only scores/capability_checks/failure_labels may be resolved")
            rubric = rubrics.get(record_id)
            if rubric is None:
                raise LineageValidationError(f"{record_id}: product_owner_resolution requires a rubric to re-validate this record")
            pseudo_generation_record = {
                "record_id": record_id,
                "format_valid": original["format_valid"],
                "raw_output_fingerprint": original["generation_raw_output_fingerprint"],
                "rubric_fingerprint": original["rubric_fingerprint"],
            }
            final_by_id[record_id] = build_review_score_record(
                generation_record=pseudo_generation_record,
                rubric=rubric,
                scores=entry["scores"],
                capability_checks=entry["capability_checks"],
                failure_labels=entry.get("failure_labels", []),
            )

    # Strict passes are recomputed from the final scores, never trusted
    # from caller input -- a caller-supplied strict_pass is discarded.
    recomputed_final = []
    for record_id in sorted(final_by_id.keys()):
        record = dict(final_by_id[record_id])
        record["strict_pass"] = rsc.compute_strict_pass({**record, "review_status": "adjudicated"})
        if record["strict_pass"] is None:
            raise LineageValidationError(f"{record_id}: adjudicated result must be fully scored, not partial")
        recomputed_final.append(record)

    artifact = {
        "schema_version": ADJUDICATION_SCHEMA_VERSION,
        "artifact_kind": "adjudication",
        "adjudication_id": new_adjudication_id(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "generation": comparison["generation"],
        "comparison": _artifact_ref(comparison, "comparison_id"),
        "chatgpt_review": comparison["chatgpt_review"],
        "claude_review": comparison["claude_review"],
        "resolution_mode": resolution_mode,
        "resolved_by_actor_id": resolved_by_actor_id,
        "results": recomputed_final,
        "aggregate_strict_pass": rsc.aggregate_strict_pass_rate(recomputed_final),
    }
    artifact["artifact_fingerprint"] = f"sha256:{rdp.artifact_fingerprint(artifact)}"
    _assert_exact_fields(artifact, "adjudication", artifact["adjudication_id"])
    return artifact


def _adjudication_path(split: str, evaluation_id: str, adjudication_id: str, milestone: str | None = None) -> Path:
    return lineage_root_for(split, evaluation_id, milestone) / "adjudications" / f"{adjudication_id}.json"


def save_adjudication_artifact(adjudication: dict, *, split: str, milestone: str | None = None) -> Path:
    path = _adjudication_path(split, adjudication["generation"]["evaluation_id"], adjudication["adjudication_id"], milestone)
    _validate_before_save(adjudication, "adjudication", path, expected_root=lineage_root_for(split, adjudication["generation"]["evaluation_id"], milestone))
    return _save_artifact_exclusive(path, adjudication)




def build_decision_record(*, decision_type: str, deciding_actor_id: str, adjudication_paths: list[Path], outcome: str, reference: str | None = None) -> dict:
    """adjudication_paths: the actual stored paths of every adjudication
    this decision cites -- each loaded, verified, and required to be
    'active' here (see load_and_require_active_parent), never caller-
    supplied in-memory dicts."""
    if decision_type not in DECISION_TYPES:
        raise LineageValidationError(f"decision_type must be one of {DECISION_TYPES}, got {decision_type!r}")
    _require_actor_id(deciding_actor_id, "deciding_actor_id")
    if not adjudication_paths:
        raise LineageValidationError("a decision record requires at least one adjudication reference")
    adjudications = [load_and_require_active_parent(p, expected_kind="adjudication", parent_label="adjudication") for p in adjudication_paths]
    _require_unique_record_ids(
        [{"record_id": a["adjudication_id"]} for a in adjudications],
        context_label="decision adjudication references",
    )

    artifact = {
        "schema_version": DECISION_SCHEMA_VERSION,
        "artifact_kind": "decision",
        "decision_id": new_decision_id(),
        "decision_type": decision_type,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "deciding_actor_id": deciding_actor_id,
        "adjudications": [_artifact_ref(a, "adjudication_id") for a in adjudications],
        "outcome": outcome,
        "reference": reference,
    }
    artifact["artifact_fingerprint"] = f"sha256:{rdp.artifact_fingerprint(artifact)}"
    _assert_exact_fields(artifact, "decision", artifact["decision_id"])
    return artifact


def save_decision_record(decision: dict) -> Path:
    path = DECISIONS_DIR / f"{decision['decision_id']}.json"
    _validate_before_save(decision, "decision", path, expected_root=DECISIONS_DIR)
    return _save_artifact_exclusive(path, decision)


def load_decision_verified(path: Path) -> dict:
    return _load_artifact_verified(path, expected_schema_version=DECISION_SCHEMA_VERSION, expected_kind="decision")




def build_status_event(*, target_artifact: dict, target_id_field: str, new_status: str, reason_code: str, actor_id: str, replacement_artifact: dict | None = None, withdrawal_id: str | None = None) -> dict:
    if new_status not in STATUS_VALUES:
        raise LineageValidationError(f"new_status must be one of {STATUS_VALUES}, got {new_status!r}")
    _require_actor_id(actor_id, "actor_id")
    artifact = {
        "schema_version": STATUS_EVENT_SCHEMA_VERSION,
        "artifact_kind": "status_event",
        "status_event_id": new_status_event_id(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "target_artifact": _artifact_ref(target_artifact, target_id_field),
        "new_status": new_status,
        "reason_code": reason_code,
        "replacement_artifact": replacement_artifact,
        "withdrawal_id": withdrawal_id,
        "actor_id": actor_id,
    }
    artifact["artifact_fingerprint"] = f"sha256:{rdp.artifact_fingerprint(artifact)}"
    _assert_exact_fields(artifact, "status_event", artifact["status_event_id"])
    return artifact


def save_status_event(event: dict) -> Path:
    path = STATUS_EVENTS_DIR / f"{event['status_event_id']}.json"
    _validate_before_save(event, "status_event", path, expected_root=STATUS_EVENTS_DIR)
    return _save_artifact_exclusive(path, event)


class ParentNotActiveError(LineageValidationError):
    pass


def resolve_active_status(artifact_ref: dict) -> str:
    """Scans every status event for one targeting artifact_ref and returns
    the most terminal outcome found: 'invalidated' beats 'superseded'
    beats the default 'active'. This tolerates multiple/out-of-order
    events for the same artifact rather than assuming exactly one --
    status transitions are one-way facts, not commands to replay in
    sequence, so taking the most-terminal result is always correct
    regardless of how many events exist or what order they were written in.

    artifact_ref: {"artifact_kind", "artifact_id", "artifact_fingerprint"}
    (see _artifact_ref) -- all three fields are matched, not just
    artifact_id, per the Phase E lineage/withdrawal implementation
    review's finding 3: binding only the ID would let a status event for
    a coincidentally-reused ID (or a wrong-kind/stale-fingerprint
    artifact) affect an unrelated artifact's resolved status.

    Every candidate file is loaded through the verified loader, not a bare
    json.loads with defensive .get(...) defaults -- a malformed or
    tampered status event must fail this scan closed, not be silently
    treated as "doesn't match, keep looking" (that could hide a real
    invalidation, which is exactly the failure mode status events exist
    to prevent)."""
    if not STATUS_EVENTS_DIR.exists():
        return "active"
    statuses = set()
    for path in STATUS_EVENTS_DIR.glob("*.json"):
        event = _load_artifact_verified(path, expected_schema_version=STATUS_EVENT_SCHEMA_VERSION, expected_kind="status_event")
        if event["target_artifact"] == artifact_ref:
            statuses.add(event["new_status"])
    if "invalidated" in statuses:
        return "invalidated"
    if "superseded" in statuses:
        return "superseded"
    return "active"


def require_parent_active(parent_ref: dict, *, parent_label: str) -> None:
    """Fails closed unless parent_ref resolves to 'active'. Every lineage
    builder that consumes a parent artifact (comparison consuming reviews,
    adjudication consuming a comparison and both reviews, decision
    consuming adjudications) must call this before using that parent --
    per the Phase E lineage/withdrawal implementation review's finding 3,
    resolve_active_status previously existed but nothing ever called it,
    so a superseded or invalidated parent could silently produce a new
    child artifact."""
    status = resolve_active_status(parent_ref)
    if status != "active":
        raise ParentNotActiveError(f"{parent_label} ({parent_ref['artifact_id']}) is {status!r}, not active -- refusing to build a new descendant from it")


def _infer_split_and_milestone_from_path(path: Path) -> tuple[str, str | None]:
    """Determines which approved private-results root a path falls under
    and, for holdout, which milestone directory. review/comparison/
    adjudication artifacts don't carry split/milestone as JSON fields
    themselves (only generation does), so the only way to know where a
    loaded parent is *supposed* to live is to read it back out of the path
    it was actually loaded from, then require that to reproduce the exact
    canonical path implied by the artifact's own stored content."""
    resolved = Path(path).resolve()
    if _is_relative_to(resolved, rel.VALIDATION_RESULTS_DIR):
        return "real_validation", None
    if _is_relative_to(resolved, rel.HOLDOUT_RESULTS_DIR):
        remainder = resolved.relative_to(rel.HOLDOUT_RESULTS_DIR.resolve()).parts
        if not remainder:
            raise LineageValidationError(f"{path}: cannot infer milestone from holdout path")
        return "real_holdout", remainder[0]
    raise LineageValidationError(f"{path}: not under an approved private-results root")


_PARENT_PATH_BUILDERS = {
    "review": _review_path,
    "comparison": _comparison_path,
    "adjudication": _adjudication_path,
}


def load_and_require_active_parent(path: Path, *, expected_kind: str, parent_label: str) -> dict:
    """Loads a parent artifact from its actual stored path -- never a
    caller-supplied in-memory dict, which could describe an artifact that
    was never actually saved anywhere, or that has silently drifted from
    what is really on disk -- verifies it via the strict per-kind loader
    (schema, exact field set including nested reference shapes, self-
    fingerprint), requires the supplied path to equal the exact canonical
    path implied by the artifact's own content (not merely "somewhere
    under an approved root"), and requires it to resolve to 'active'
    before returning it. Every lineage builder that consumes a parent goes
    through this.

    Per the Phase E lineage/withdrawal second review's finding 1:
    resolve_active_status only ever scanned status events and defaulted an
    artifact with zero matching events -- including one that was never
    saved at all -- to 'active', and build_review_artifact never checked
    its generation parent's status in the first place. Per the third
    review's finding 1: a valid, active review copied to some other
    location (even still under the approved results tree) was accepted as
    a stored parent just because it existed and was self-consistent --
    nothing checked it was actually AT the location its own content
    implies. Callers must use the dict this returns for all subsequent
    processing, not whatever in-memory object they originally had."""
    path = Path(path)
    if expected_kind == "generation":
        loaded = rel.load_generation_artifact(path)
        canonical = rel.result_path_for(loaded["split"], loaded["evaluation_id"], loaded.get("release_milestone"))
        ref = _artifact_ref(loaded, "evaluation_id")
    elif expected_kind == "decision":
        loaded = _load_artifact_verified(path, expected_schema_version=_KIND_SCHEMA_VERSIONS[expected_kind], expected_kind=expected_kind)
        canonical = DECISIONS_DIR / f"{loaded['decision_id']}.json"
        ref = _artifact_ref(loaded, _KIND_METADATA[expected_kind]["id_field"])
    else:
        loaded = _load_artifact_verified(path, expected_schema_version=_KIND_SCHEMA_VERSIONS[expected_kind], expected_kind=expected_kind)
        split, milestone = _infer_split_and_milestone_from_path(path)
        id_field = _KIND_METADATA[expected_kind]["id_field"]
        canonical = _PARENT_PATH_BUILDERS[expected_kind](split, loaded["generation"]["evaluation_id"], loaded[id_field], milestone)
        ref = _artifact_ref(loaded, id_field)
    if path.resolve() != canonical.resolve():
        raise LineageValidationError(f"{path}: does not match the canonical path {canonical} implied by its own content -- refusing to treat as a valid stored parent")
    require_parent_active(ref, parent_label=parent_label)
    return loaded




def build_dataset_snapshot(*, split: str, creation_reason: str, active_records: list[dict], rubric_schema_version: str, parent_snapshot: dict | None = None) -> dict:
    """active_records: one {"record_id", "source_fingerprint",
    "pair_fingerprint", "rubric_fingerprint"} dict per currently-active
    record in split -- may be empty (an empty split still gets a
    deterministic dataset_fingerprint via real_data_private.dataset_fingerprint)."""
    if split not in rdm.VALID_SPLITS:
        raise LineageValidationError(f"split must be one of {rdm.VALID_SPLITS}, got {split!r}")
    _require_unique_record_ids(active_records, context_label="dataset snapshot active_records")
    ds_fp = rdp.dataset_fingerprint(active_records, split)
    artifact = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "artifact_kind": "dataset_snapshot",
        "snapshot_id": new_snapshot_id(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "split": split,
        "creation_reason": creation_reason,
        "active_records": sorted(active_records, key=lambda r: r["record_id"]),
        "rubric_schema_version": rubric_schema_version,
        "dataset_fingerprint": f"sha256:{ds_fp}",
        "parent_snapshot": parent_snapshot,
    }
    artifact["artifact_fingerprint"] = f"sha256:{rdp.artifact_fingerprint(artifact)}"
    _assert_exact_fields(artifact, "dataset_snapshot", artifact["snapshot_id"])
    return artifact


def save_dataset_snapshot(snapshot: dict) -> Path:
    if snapshot.get("split") not in rdm.VALID_SPLITS:
        raise LineageValidationError(f"dataset_snapshot has an invalid split {snapshot.get('split')!r}")
    path = DATASET_SNAPSHOTS_DIR / snapshot["split"] / f"{snapshot['snapshot_id']}.json"
    _validate_before_save(snapshot, "dataset_snapshot", path, expected_root=DATASET_SNAPSHOTS_DIR / snapshot["split"])
    return _save_artifact_exclusive(path, snapshot)


def load_dataset_snapshot_verified(path: Path) -> dict:
    return _load_artifact_verified(path, expected_schema_version=SNAPSHOT_SCHEMA_VERSION, expected_kind="dataset_snapshot")
