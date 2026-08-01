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

REVIEWER_ROLES = ("chatgpt", "claude")
RESOLUTION_MODES = ("reviewer_agreement", "product_owner_resolution")
DECISION_TYPES = ("curriculum", "training_budget", "seed", "checkpoint", "prompt", "release")
STATUS_VALUES = ("superseded", "invalidated")


class LineageValidationError(ValueError):
    pass


class LineageArtifactExistsError(FileExistsError):
    pass


def _require_actor_id(value, field_name: str) -> None:
    if not isinstance(value, str) or not _ACTOR_ID_RE.match(value):
        raise LineageValidationError(f"{field_name} must match {_ACTOR_ID_RE.pattern}, got {value!r}")


def new_review_id() -> str:
    return f"review_{uuid.uuid4().hex[:12]}"


def new_comparison_id() -> str:
    return f"cmp_{uuid.uuid4().hex[:12]}"


def new_adjudication_id() -> str:
    return f"adj_{uuid.uuid4().hex[:12]}"


def new_decision_id() -> str:
    return f"dec_{uuid.uuid4().hex[:12]}"


def new_status_event_id() -> str:
    return f"sev_{uuid.uuid4().hex[:12]}"


def new_snapshot_id() -> str:
    return f"snap_{uuid.uuid4().hex[:12]}"


def new_withdrawal_id() -> str:
    return f"wd_{uuid.uuid4().hex[:12]}"


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


def _save_artifact_exclusive(path: Path, artifact: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(artifact, indent=2, ensure_ascii=False)
    try:
        with path.open("x", encoding="utf-8") as f:
            f.write(payload)
    except FileExistsError as e:
        raise LineageArtifactExistsError(f"Refusing to overwrite an existing artifact at {path} -- lineage artifacts are immutable.") from e
    return path


def _load_artifact_verified(path: Path, *, expected_schema_version: str, expected_kind: str) -> dict:
    """Loads and verifies schema/kind match and that the recomputed
    artifact_fingerprint matches the stored one -- a tampered artifact
    must never be trusted just because it parses as JSON."""
    path = Path(path)
    if not path.exists():
        raise LineageValidationError(f"{path}: artifact does not exist")
    artifact = json.loads(path.read_text(encoding="utf-8"))
    if artifact.get("schema_version") != expected_schema_version:
        raise LineageValidationError(f"{path}: schema_version is {artifact.get('schema_version')!r}, expected {expected_schema_version!r}")
    if artifact.get("artifact_kind") != expected_kind:
        raise LineageValidationError(f"{path}: artifact_kind is {artifact.get('artifact_kind')!r}, expected {expected_kind!r}")
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


# --- Review artifact (real-eval-review-v1) ---


def build_review_score_record(*, generation_record: dict, rubric: dict, scores: dict, capability_checks: dict, failure_labels: list[str]) -> dict:
    """One complete score record for one generation record. rubric:
    the loaded, strictly-validated private rubric for this record_id.
    expected_capability_checks on the rubric is read opportunistically
    (defaults to none required) -- it isn't part of the Tier 3-agreed
    rubric structural contract, so an absent field means "no capability
    checks required for this record" rather than an error; whether it
    should become a required rubric field is worth confirming with
    ChatGPT rather than something this code should decide unilaterally."""
    record_id = generation_record["record_id"]
    expected_checks = set(rubric.get("expected_capability_checks", []))
    if set(capability_checks.keys()) != expected_checks:
        raise LineageValidationError(
            f"{record_id}: capability_checks keys must exactly match the rubric's expected capability checks -- "
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


def build_review_artifact(
    *,
    generation: dict,
    reviewer_role: str,
    reviewer_actor_id: str,
    independent_review_attestation: bool,
    scores: list[dict],
    review_notes: str | None = None,
    supersedes_review: dict | None = None,
) -> dict:
    """generation: an already fingerprint-verified generation artifact
    (see real_data_eval_logging.load_generation_artifact). scores: one
    build_review_score_record() output per generation record -- no
    omissions, no extras."""
    if reviewer_role not in REVIEWER_ROLES:
        raise LineageValidationError(f"reviewer_role must be one of {REVIEWER_ROLES}, got {reviewer_role!r}")
    _require_actor_id(reviewer_actor_id, "reviewer_actor_id")
    if independent_review_attestation is not True:
        raise LineageValidationError("independent_review_attestation must be literal True -- a review cannot be recorded without attesting independence")

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
    return artifact


def _review_path(split: str, evaluation_id: str, review_id: str, milestone: str | None = None) -> Path:
    return lineage_root_for(split, evaluation_id, milestone) / "reviews" / f"{review_id}.json"


def save_review_artifact(review: dict, *, split: str, milestone: str | None = None) -> Path:
    path = _review_path(split, review["generation"]["evaluation_id"], review["review_id"], milestone)
    return _save_artifact_exclusive(path, review)


def load_review_verified(path: Path, generation: dict) -> dict:
    """Loads a review and cross-checks it against its claimed generation
    parent: exact fingerprint match, matching copied dataset/checkpoint/
    rubric-schema fingerprints, and an exactly-matching record set with
    per-record raw-output/rubric-fingerprint/format-validity agreement."""
    review = _load_artifact_verified(path, expected_schema_version=REVIEW_SCHEMA_VERSION, expected_kind="review")
    gen_ref = review.get("generation", {})
    if gen_ref.get("artifact_kind") != "generation":
        raise LineageValidationError(f"{path}: review's parent reference is not kind 'generation'")
    if gen_ref.get("evaluation_id") != generation["evaluation_id"] or gen_ref.get("artifact_fingerprint") != generation["artifact_fingerprint"]:
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
    return review


# --- Comparison artifact (real-eval-comparison-v1), computed not authored ---


def build_comparison_artifact(*, chatgpt_review: dict, claude_review: dict) -> dict:
    if chatgpt_review["reviewer_role"] != "chatgpt":
        raise LineageValidationError("chatgpt_review must have reviewer_role 'chatgpt'")
    if claude_review["reviewer_role"] != "claude":
        raise LineageValidationError("claude_review must have reviewer_role 'claude'")
    if chatgpt_review["reviewer_actor_id"] == claude_review["reviewer_actor_id"]:
        raise LineageValidationError("chatgpt and claude reviews must use distinct reviewer actor IDs")
    if chatgpt_review["generation"] != claude_review["generation"]:
        raise LineageValidationError("both reviews must share the exact same generation parent reference -- cannot compare reviews of different generations")

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
    return artifact


def _comparison_path(split: str, evaluation_id: str, comparison_id: str, milestone: str | None = None) -> Path:
    return lineage_root_for(split, evaluation_id, milestone) / "comparisons" / f"{comparison_id}.json"


def save_comparison_artifact(comparison: dict, *, split: str, milestone: str | None = None) -> Path:
    path = _comparison_path(split, comparison["generation"]["evaluation_id"], comparison["comparison_id"], milestone)
    return _save_artifact_exclusive(path, comparison)


# --- Adjudication artifact (real-eval-adjudication-v1) ---


def build_adjudication_artifact(
    *,
    comparison: dict,
    chatgpt_review: dict,
    claude_review: dict,
    resolution_mode: str,
    resolved_by_actor_id: str | None = None,
    final_scores: list[dict] | None = None,
) -> dict:
    if resolution_mode not in RESOLUTION_MODES:
        raise LineageValidationError(f"resolution_mode must be one of {RESOLUTION_MODES}, got {resolution_mode!r}")
    if comparison["chatgpt_review"] != _artifact_ref(chatgpt_review, "review_id"):
        raise LineageValidationError("comparison's chatgpt_review reference does not match the supplied chatgpt_review")
    if comparison["claude_review"] != _artifact_ref(claude_review, "review_id"):
        raise LineageValidationError("comparison's claude_review reference does not match the supplied claude_review")

    if resolution_mode == "reviewer_agreement":
        if comparison["alignment_status"] != "aligned":
            raise LineageValidationError("reviewer_agreement adjudication requires an aligned comparison")
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
        comparison_record_ids = {rc["record_id"] for rc in comparison["record_comparisons"]}
        final_record_ids = {s["record_id"] for s in final_scores}
        if comparison_record_ids != final_record_ids:
            raise LineageValidationError("final_scores must cover exactly the compared record set")
        final_by_id = {s["record_id"]: s for s in final_scores}

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
    return artifact


def _adjudication_path(split: str, evaluation_id: str, adjudication_id: str, milestone: str | None = None) -> Path:
    return lineage_root_for(split, evaluation_id, milestone) / "adjudications" / f"{adjudication_id}.json"


def save_adjudication_artifact(adjudication: dict, *, split: str, milestone: str | None = None) -> Path:
    path = _adjudication_path(split, adjudication["generation"]["evaluation_id"], adjudication["adjudication_id"], milestone)
    return _save_artifact_exclusive(path, adjudication)


# --- Decision record (real-eval-decision-v1) ---


def build_decision_record(*, decision_type: str, deciding_actor_id: str, adjudications: list[dict], outcome: str, reference: str | None = None) -> dict:
    if decision_type not in DECISION_TYPES:
        raise LineageValidationError(f"decision_type must be one of {DECISION_TYPES}, got {decision_type!r}")
    _require_actor_id(deciding_actor_id, "deciding_actor_id")
    if not adjudications:
        raise LineageValidationError("a decision record requires at least one adjudication reference")

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
    return artifact


def save_decision_record(decision: dict) -> Path:
    return _save_artifact_exclusive(DECISIONS_DIR / f"{decision['decision_id']}.json", decision)


def load_decision_verified(path: Path) -> dict:
    return _load_artifact_verified(path, expected_schema_version=DECISION_SCHEMA_VERSION, expected_kind="decision")


# --- Status events (real-lineage-status-v1) ---


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
    return artifact


def save_status_event(event: dict) -> Path:
    return _save_artifact_exclusive(STATUS_EVENTS_DIR / f"{event['status_event_id']}.json", event)


def resolve_active_status(artifact_id: str) -> str:
    """Scans every status event for one targeting artifact_id and returns
    the most terminal outcome found: 'invalidated' beats 'superseded'
    beats the default 'active'. This tolerates multiple/out-of-order
    events for the same artifact rather than assuming exactly one --
    status transitions are one-way facts, not commands to replay in
    sequence, so taking the most-terminal result is always correct
    regardless of how many events exist or what order they were written in."""
    if not STATUS_EVENTS_DIR.exists():
        return "active"
    statuses = set()
    for path in STATUS_EVENTS_DIR.glob("*.json"):
        event = json.loads(path.read_text(encoding="utf-8"))
        if event.get("target_artifact", {}).get("artifact_id") == artifact_id:
            statuses.add(event.get("new_status"))
    if "invalidated" in statuses:
        return "invalidated"
    if "superseded" in statuses:
        return "superseded"
    return "active"


# --- Dataset snapshots (real-dataset-snapshot-v1) ---


def build_dataset_snapshot(*, split: str, creation_reason: str, active_records: list[dict], rubric_schema_version: str, parent_snapshot: dict | None = None) -> dict:
    """active_records: one {"record_id", "source_fingerprint",
    "pair_fingerprint", "rubric_fingerprint"} dict per currently-active
    record in split -- may be empty (an empty split still gets a
    deterministic dataset_fingerprint via real_data_private.dataset_fingerprint)."""
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
    return artifact


def save_dataset_snapshot(snapshot: dict) -> Path:
    path = DATASET_SNAPSHOTS_DIR / snapshot["split"] / f"{snapshot['snapshot_id']}.json"
    return _save_artifact_exclusive(path, snapshot)


def load_dataset_snapshot_verified(path: Path) -> dict:
    return _load_artifact_verified(path, expected_schema_version=SNAPSHOT_SCHEMA_VERSION, expected_kind="dataset_snapshot")
