"""Withdrawal protocol, per
training/real_data_scoring_lineage_withdrawal_design.md's "Withdrawal
protocol" section. One public entry point (withdraw_record_validated)
implements discovery, an immutable plan written before any mutation,
an execution order that updates the manifest first (so eligibility fails
even if later cleanup is interrupted) and deletes source-derived artifacts
only after their invalidation events exist, residual checks, and a
completion artifact -- with every step idempotent so a crashed and
re-run request resumes rather than repeating or corrupting prior work.

Nothing here ever writes note text, generated output, scores, failure
labels, or reviewer notes into a plan/status/snapshot/completion artifact
-- only IDs, kinds, fingerprints, and relative paths.
"""
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import real_data_eval_logging as rel
import real_data_lineage as lin
import real_data_manifest as rdm
import real_data_private as rdp
from prepare_data import DATA_DIR

WITHDRAWALS_DIR = lin.WITHDRAWALS_DIR
LOCKS_DIR = WITHDRAWALS_DIR / "locks"

WITHDRAWAL_PLAN_SCHEMA_VERSION = "real-withdrawal-plan-v1"
WITHDRAWAL_COMPLETION_SCHEMA_VERSION = "real-withdrawal-completion-v1"

ALLOWED_REASON_CODES = ("contributor_request", "consent_expired")
_REASON_TO_WITHDRAWAL_STATUS = {"contributor_request": "withdrawn", "consent_expired": "expired"}

_ACTOR_ID_RE = re.compile(r"^actor_[0-9a-f]{32}$")

_SOURCE_PATH_FOR_SPLIT = {"real_validation": DATA_DIR / "real_validation.jsonl", "real_holdout": DATA_DIR / "real_holdout.jsonl"}


class WithdrawalValidationError(ValueError):
    pass


class WithdrawalLockError(ValueError):
    pass


class WithdrawalDiscoveryError(ValueError):
    pass


class WithdrawalResidualCheckError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_actor_id(value, field_name: str) -> None:
    if not isinstance(value, str) or not _ACTOR_ID_RE.match(value):
        raise WithdrawalValidationError(f"{field_name} must match {_ACTOR_ID_RE.pattern}, got {value!r}")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _lock_path_for(record_id: str) -> Path:
    """Caller must validate record_id (rdm.validate_record_id_format)
    before this is ever reached -- that's what actually prevents a
    crafted record_id from traversing out of LOCKS_DIR. The containment
    assertion below is defense in depth on top of that, not the only
    safeguard, matching the pattern established in
    real_data_eval_logging.py's _validate_split_root."""
    path = LOCKS_DIR / f"{record_id}.json"
    if not _is_relative_to(path.resolve(), LOCKS_DIR.resolve()):
        raise WithdrawalValidationError(f"record_id {record_id!r} produces a lock path outside LOCKS_DIR -- refusing")
    return path


def _parse_source_line_strict(line: str, source_name: str) -> dict:
    """Strict single-line JSON parse for a source-split row: rejects
    duplicate object keys, matching evaluate_holdout.py/
    evaluate_real_validation.py's trust-boundary handling of the same
    files -- withdrawal's own planning/removal/residual-check scans of
    real_validation.jsonl/real_holdout.jsonl must not be less strict than
    routine evaluation is."""
    try:
        return json.loads(line, object_pairs_hook=rdm.reject_duplicate_keys)
    except (json.JSONDecodeError, rdm.DuplicateJSONKeyError) as e:
        raise WithdrawalValidationError(f"{source_name}: invalid JSON row ({e})") from e


def _acquire_or_inspect_lock(record_id: str) -> tuple[str, dict | None]:
    """Returns (withdrawal_id, completion_or_None). completion is non-None
    only if a prior run of this exact record's withdrawal already reached
    a terminal, saved completion artifact -- callers must return it
    unchanged rather than re-executing anything."""
    path = _lock_path_for(record_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        withdrawal_id = lin.new_withdrawal_id()
        lock_content = {"record_id": record_id, "withdrawal_id": withdrawal_id, "status": "in_progress", "created_at_utc": _now()}
        try:
            with path.open("x", encoding="utf-8") as f:
                json.dump(lock_content, f)
            return withdrawal_id, None
        except FileExistsError:
            # Lost a race with a concurrent caller: another process created
            # the lock between our exists() check and open("x"). Not
            # swallowed -- explicitly handed to the same inspection path
            # used for a lock that already existed, so the race resolves
            # to identical behavior either way.
            return _inspect_existing_lock(path, record_id)
    return _inspect_existing_lock(path, record_id)


_LOCK_FIELDS = frozenset({"record_id", "withdrawal_id", "status", "created_at_utc"})
_WITHDRAWAL_ID_RE = re.compile(r"^wd_[0-9a-f]{32}$")


def _inspect_existing_lock(path: Path, record_id: str) -> tuple[str, dict | None]:
    try:
        lock_content = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=rdm.reject_duplicate_keys)
    except (json.JSONDecodeError, OSError, rdm.DuplicateJSONKeyError) as e:
        raise WithdrawalLockError(
            f"lock file for {record_id} is unreadable/corrupt -- a stale or ambiguous lock fails closed and "
            "requires explicit recovery, never automatic removal"
        ) from e
    if not isinstance(lock_content, dict) or set(lock_content.keys()) != _LOCK_FIELDS:
        raise WithdrawalLockError(f"lock file for {record_id} has an unexpected field set -- stale or ambiguous lock requires explicit recovery")
    if lock_content.get("record_id") != record_id:
        raise WithdrawalLockError(f"lock file at {path} declares record_id {lock_content.get('record_id')!r}, expected {record_id!r} -- ambiguous, requires explicit recovery")
    if not isinstance(lock_content.get("withdrawal_id"), str) or not _WITHDRAWAL_ID_RE.match(lock_content["withdrawal_id"]):
        raise WithdrawalLockError(f"lock file for {record_id} has a malformed withdrawal_id -- stale or ambiguous lock requires explicit recovery")
    if lock_content.get("status") not in ("in_progress", "completed"):
        raise WithdrawalLockError(f"lock file for {record_id} is malformed -- stale or ambiguous lock requires explicit recovery")
    try:
        rdm.validate_utc_timestamp(lock_content.get("created_at_utc"), "created_at_utc")
    except rdm.ManifestValidationError as e:
        raise WithdrawalLockError(f"lock file for {record_id} has a malformed created_at_utc: {e}") from e

    withdrawal_id = lock_content["withdrawal_id"]
    if lock_content["status"] == "completed":
        completion_path = _completion_path_for(withdrawal_id)
        if not completion_path.exists():
            raise WithdrawalLockError(
                f"lock for {record_id} claims completed but no completion artifact exists for {withdrawal_id} -- "
                "ambiguous, requires explicit recovery"
            )
        return withdrawal_id, _load_completion_verified(completion_path)
    return withdrawal_id, None  # in_progress: resume


def _mark_lock_completed(record_id: str, withdrawal_id: str) -> None:
    """Atomic (temp file + os.replace), matching real_data_private.py's
    _save_manifest_raw convention -- a plain write_text here would leave
    an untested crash window where an interrupted write could corrupt or
    truncate the lock file, the one thing every retry depends on being
    readable."""
    path = _lock_path_for(record_id)
    content = json.dumps({"record_id": record_id, "withdrawal_id": withdrawal_id, "status": "completed", "created_at_utc": _now()})
    tmp_path = path.parent / f".{path.name}.{lin.new_withdrawal_id()}.tmp"
    tmp_path.write_text(content, encoding="utf-8")
    os.replace(tmp_path, path)




def _plan_path_for(withdrawal_id: str) -> Path:
    return WITHDRAWALS_DIR / withdrawal_id / "plan.json"


def _completion_path_for(withdrawal_id: str) -> Path:
    return WITHDRAWALS_DIR / withdrawal_id / "completion.json"


def _relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(rel.RESULTS_PRIVATE_DIR.resolve()).as_posix())
    except ValueError:
        return str(path)


def _iter_generation_files():
    if rel.VALIDATION_RESULTS_DIR.exists():
        for p in rel.VALIDATION_RESULTS_DIR.glob("*.json"):
            yield "real_validation", None, p
    if rel.HOLDOUT_RESULTS_DIR.exists():
        for milestone_dir in rel.HOLDOUT_RESULTS_DIR.iterdir():
            if milestone_dir.is_dir():
                for p in milestone_dir.glob("*.json"):
                    yield "real_holdout", milestone_dir.name, p


def _discover_affected(record_id: str) -> dict:
    """Full descendant closure for record_id: every generation containing
    it (whole generation, even if it also covers other records -- partial
    editing would violate immutability), every review/comparison/
    adjudication in that generation's lineage, and every decision citing
    an affected adjudication. Any malformed candidate file fails the whole
    discovery closed rather than being silently skipped -- a corrupt file
    could be hiding whether it references the withdrawn record."""
    affected_generations = []
    affected_reviews = []
    affected_comparisons = []
    affected_adjudications = []

    for split, milestone, gen_path in _iter_generation_files():
        try:
            generation = rel.load_generation_artifact(gen_path)
        except rel.GenerationValidationError as e:
            raise WithdrawalDiscoveryError(f"malformed generation artifact at {gen_path} encountered during discovery: {e}") from e
        if not any(r["record_id"] == record_id for r in generation["results"]):
            continue
        affected_generations.append(
            {"artifact_kind": "generation", "artifact_id": generation["evaluation_id"], "artifact_fingerprint": generation["artifact_fingerprint"], "relative_path": _relpath(gen_path), "split": split, "milestone": milestone}
        )
        lineage_dir = lin.lineage_root_for(split, generation["evaluation_id"], milestone)
        if not lineage_dir.exists():
            continue
        for review_path in sorted((lineage_dir / "reviews").glob("*.json")) if (lineage_dir / "reviews").exists() else []:
            try:
                review = lin._load_artifact_verified(review_path, expected_schema_version=lin.REVIEW_SCHEMA_VERSION, expected_kind="review")
            except lin.LineageValidationError as e:
                raise WithdrawalDiscoveryError(f"malformed review artifact at {review_path} encountered during discovery: {e}") from e
            affected_reviews.append({"artifact_kind": "review", "artifact_id": review["review_id"], "artifact_fingerprint": review["artifact_fingerprint"], "relative_path": _relpath(review_path)})
        for comparison_path in sorted((lineage_dir / "comparisons").glob("*.json")) if (lineage_dir / "comparisons").exists() else []:
            try:
                comparison = lin._load_artifact_verified(comparison_path, expected_schema_version=lin.COMPARISON_SCHEMA_VERSION, expected_kind="comparison")
            except lin.LineageValidationError as e:
                raise WithdrawalDiscoveryError(f"malformed comparison artifact at {comparison_path} encountered during discovery: {e}") from e
            affected_comparisons.append({"artifact_kind": "comparison", "artifact_id": comparison["comparison_id"], "artifact_fingerprint": comparison["artifact_fingerprint"], "relative_path": _relpath(comparison_path)})
        for adjudication_path in sorted((lineage_dir / "adjudications").glob("*.json")) if (lineage_dir / "adjudications").exists() else []:
            try:
                adjudication = lin._load_artifact_verified(adjudication_path, expected_schema_version=lin.ADJUDICATION_SCHEMA_VERSION, expected_kind="adjudication")
            except lin.LineageValidationError as e:
                raise WithdrawalDiscoveryError(f"malformed adjudication artifact at {adjudication_path} encountered during discovery: {e}") from e
            affected_adjudications.append({"artifact_kind": "adjudication", "artifact_id": adjudication["adjudication_id"], "artifact_fingerprint": adjudication["artifact_fingerprint"], "relative_path": _relpath(adjudication_path)})

    affected_adjudication_ids = {a["artifact_id"] for a in affected_adjudications}
    affected_decisions = []
    if lin.DECISIONS_DIR.exists():
        for decision_path in sorted(lin.DECISIONS_DIR.glob("*.json")):
            try:
                decision = lin.load_decision_verified(decision_path)
            except lin.LineageValidationError as e:
                raise WithdrawalDiscoveryError(f"malformed decision artifact at {decision_path} encountered during discovery: {e}") from e
            if any(ref["artifact_id"] in affected_adjudication_ids for ref in decision["adjudications"]):
                affected_decisions.append({"artifact_kind": "decision", "artifact_id": decision["decision_id"], "artifact_fingerprint": decision["artifact_fingerprint"], "relative_path": _relpath(decision_path)})

    return {
        "affected_generations": affected_generations,
        "affected_reviews": affected_reviews,
        "affected_comparisons": affected_comparisons,
        "affected_adjudications": affected_adjudications,
        "affected_decisions": affected_decisions,
        "affected_seals": [],  # no holdout-seal mechanism exists yet -- always empty, see real_data_manifest.load_approved_seal
    }


def _build_and_save_plan(*, record_id: str, withdrawal_id: str, requested_by_actor_id: str, reason_code: str, requested_at_utc: str) -> dict:
    manifest = rdm.load_manifest_strict(pilot_mode=False)  # pilot_mode=False: reading an existing entry, not assigning a new one -- see real_data_manifest.py's pilot_mode docstring
    entry = manifest.get(record_id)
    if entry is None:
        raise WithdrawalValidationError(f"no manifest entry for record_id {record_id!r}")

    split = entry.get("split")
    source_fp = entry.get("source_fingerprint")
    if split is not None and source_fp is not None:
        source_path = _SOURCE_PATH_FOR_SPLIT[split]
        matching_rows = 0
        if source_path.exists():
            for line in source_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                row = _parse_source_line_strict(line, source_path.name)
                if rdp.source_fingerprint(row["input"]) == source_fp.removeprefix("sha256:"):
                    matching_rows += 1
        if matching_rows > 1:
            raise WithdrawalValidationError(f"source_fingerprint for {record_id} matches {matching_rows} rows in {source_path.name} -- ambiguous, refusing to withdraw before this is resolved")

    closure = _discover_affected(record_id)

    active_records = [
        {"record_id": rid, "source_fingerprint": e["source_fingerprint"], "pair_fingerprint": e["pair_fingerprint"], "rubric_fingerprint": e["rubric_fingerprint"]}
        for rid, e in manifest.items()
        if e.get("split") == split and e.get("withdrawal_status") == "active" and e.get("source_fingerprint")
    ]
    prior_dataset_fingerprint = f"sha256:{rdp.dataset_fingerprint(active_records, split)}" if split is not None else None

    plan = {
        "schema_version": WITHDRAWAL_PLAN_SCHEMA_VERSION,
        "artifact_kind": "withdrawal_plan",
        "withdrawal_id": withdrawal_id,
        "created_at_utc": _now(),
        "record_id": record_id,
        "requested_by_actor_id": requested_by_actor_id,
        "reason_code": reason_code,
        "requested_at_utc": requested_at_utc,
        "split": split,
        "manifest_source_fingerprint": source_fp,
        "prior_dataset_fingerprint": prior_dataset_fingerprint,
        **closure,
        "intended_actions": [
            "mark_manifest_withdrawn",
            "remove_source_row",
            "remove_rubric_entry",
            "invalidate_descendants",
            "retire_affected_seals",
            "delete_generation_and_lineage_files",
            "delete_other_source_derived_artifacts",
            "recompute_dataset_snapshot",
            "run_residual_checks",
            "write_completion",
        ],
    }
    plan["artifact_fingerprint"] = f"sha256:{rdp.artifact_fingerprint(plan)}"
    path = _plan_path_for(withdrawal_id)
    try:
        lin._save_artifact_exclusive(path, plan)
        return plan
    except lin.LineageArtifactExistsError:
        # Two callers racing to create the same withdrawal_id's plan (both
        # legitimately resuming the same lock) must both proceed from the
        # one persisted, verified plan -- not from the loser's own
        # in-memory copy, which could differ subtly (e.g. active_records
        # computed a moment apart) from what actually got committed.
        persisted = _load_plan_verified(path)
        if persisted["record_id"] != record_id or persisted["withdrawal_id"] != withdrawal_id:
            raise WithdrawalValidationError(
                f"plan at {path} does not match the expected record_id/withdrawal_id -- ambiguous, requires explicit recovery"
            )
        return persisted


def _load_plan_verified(path: Path) -> dict:
    return lin._load_artifact_verified(path, expected_schema_version=WITHDRAWAL_PLAN_SCHEMA_VERSION, expected_kind="withdrawal_plan")


def _load_completion_verified(path: Path) -> dict:
    return lin._load_artifact_verified(path, expected_schema_version=WITHDRAWAL_COMPLETION_SCHEMA_VERSION, expected_kind="withdrawal_completion")




def _step_mark_manifest_withdrawn(plan: dict) -> None:
    """pilot_mode=False here is deliberate, not a convenience shortcut:
    this write never assigns split or sets holdout_eligible on any entry,
    so the pilot's write-side holdout restriction has nothing to do with
    it. Requiring pilot_mode=True would mean an unrelated, pre-existing
    holdout-eligible entry elsewhere in the manifest could block a
    privacy-remedial withdrawal for a completely different record -- the
    one class of operation that should have the fewest possible blockers."""
    manifest = rdm.load_manifest_strict(pilot_mode=False)
    entry = manifest[plan["record_id"]]
    target_status = _REASON_TO_WITHDRAWAL_STATUS[plan["reason_code"]]
    if entry.get("withdrawal_status") == target_status:
        return  # already done
    updated = {**entry, "withdrawal_status": target_status, "withdrawal_status_changed_at_utc": plan["requested_at_utc"]}
    rdm.upsert_manifest_entry_validated(updated, pilot_mode=False)


def _step_remove_source_row(plan: dict) -> None:
    split = plan["split"]
    if split is None or plan["manifest_source_fingerprint"] is None:
        return  # never assigned to a split -- no source row could exist
    source_path = _SOURCE_PATH_FOR_SPLIT[split]
    if not source_path.exists():
        return
    target_fp = plan["manifest_source_fingerprint"].removeprefix("sha256:")
    kept_lines = []
    changed = False
    for line in source_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        row = _parse_source_line_strict(stripped, source_path.name)
        if rdp.source_fingerprint(row["input"]) == target_fp:
            changed = True
            continue
        kept_lines.append(stripped)
    if not changed:
        return  # already removed (resume case)
    tmp_path = source_path.parent / f".{source_path.name}.tmp"
    tmp_path.write_text("\n".join(kept_lines) + ("\n" if kept_lines else ""), encoding="utf-8")
    os.replace(tmp_path, source_path)


def _step_remove_rubric_entry(plan: dict) -> None:
    """Reads through the strict, schema-validated loader -- deleting an
    entry from a rubric file we haven't verified is well-formed could
    silently mask corruption elsewhere in the file. The write-back uses
    the plain (already-atomic) save primitive since we're only removing
    a key, not adding one that would need validation."""
    rubrics = rdm.load_rubrics_strict()
    if plan["record_id"] not in rubrics:
        return
    del rubrics[plan["record_id"]]
    rdp.save_rubrics(rubrics)


def _canonical_ref(ref: dict) -> dict:
    """Extracts just the three artifact_ref fields from a plan entry that
    may carry extra bookkeeping keys (relative_path, split, milestone) --
    resolve_active_status matches all three fields exactly, so it needs
    the canonical shape, not the plan's richer per-entry dict."""
    return {"artifact_kind": ref["artifact_kind"], "artifact_id": ref["artifact_id"], "artifact_fingerprint": ref["artifact_fingerprint"]}


def _step_invalidate_descendants(plan: dict) -> None:
    all_affected = plan["affected_generations"] + plan["affected_reviews"] + plan["affected_comparisons"] + plan["affected_adjudications"] + plan["affected_decisions"]
    for ref in all_affected:
        if lin.resolve_active_status(_canonical_ref(ref)) == "invalidated":
            continue
        id_field = f"{ref['artifact_kind']}_id"
        target_artifact = {"artifact_kind": ref["artifact_kind"], id_field: ref["artifact_id"], "artifact_fingerprint": ref["artifact_fingerprint"]}
        event = lin.build_status_event(
            target_artifact=target_artifact,
            target_id_field=id_field,
            new_status="invalidated",
            reason_code="withdrawal",
            actor_id=plan["requested_by_actor_id"],
            withdrawal_id=plan["withdrawal_id"],
        )
        try:
            lin.save_status_event(event)
        except lin.LineageArtifactExistsError:
            pass


def _step_delete_generation_and_lineage_files(plan: dict) -> None:
    for gen_ref in plan["affected_generations"]:
        gen_path = rel.RESULTS_PRIVATE_DIR / gen_ref["relative_path"]
        if gen_path.exists():
            gen_path.unlink()
        lineage_dir = lin.lineage_root_for(gen_ref["split"], gen_ref["artifact_id"], gen_ref["milestone"])
        if lineage_dir.exists():
            shutil.rmtree(lineage_dir)


def _step_delete_other_source_derived_artifacts(plan: dict) -> None:
    """No additional source-derived artifact kinds exist yet beyond
    generation+lineage (already handled above). If a future artifact kind
    is added (e.g. draft annotations), a matching plan entry and deletion
    here is required -- flagged, not silently assumed complete."""
    return


def _step_recompute_dataset_snapshot(plan: dict) -> dict | None:
    split = plan["split"]
    if split is None:
        return None
    manifest = rdm.load_manifest_strict(pilot_mode=False)
    active_records = [
        {"record_id": rid, "source_fingerprint": e["source_fingerprint"], "pair_fingerprint": e["pair_fingerprint"], "rubric_fingerprint": e["rubric_fingerprint"]}
        for rid, e in manifest.items()
        if e.get("split") == split and e.get("withdrawal_status") == "active" and e.get("source_fingerprint")
    ]
    expected_fp = f"sha256:{rdp.dataset_fingerprint(active_records, split)}"

    snapshot_dir = lin.DATASET_SNAPSHOTS_DIR / split
    if snapshot_dir.exists():
        for existing_path in snapshot_dir.glob("*.json"):
            existing = lin.load_dataset_snapshot_verified(existing_path)
            if existing["dataset_fingerprint"] == expected_fp:
                return existing  # already recomputed in an earlier, interrupted attempt

    snapshot = lin.build_dataset_snapshot(
        split=split,
        creation_reason=f"post-withdrawal snapshot for {plan['withdrawal_id']}",
        active_records=active_records,
        rubric_schema_version="real-rubric-v1",
    )
    lin.save_dataset_snapshot(snapshot)
    return snapshot


def _run_residual_checks(plan: dict, snapshot: dict | None) -> None:
    manifest = rdm.load_manifest_strict(pilot_mode=False)
    entry = manifest[plan["record_id"]]

    if entry.get("withdrawal_status") not in ("withdrawn", "expired"):
        raise WithdrawalResidualCheckError(f"{plan['record_id']}: manifest is not terminal after withdrawal")
    try:
        rdm.check_evaluation_eligibility(entry, expected_split=plan["split"] or "real_validation")
        raise WithdrawalResidualCheckError(f"{plan['record_id']}: eligibility check unexpectedly still passes after withdrawal")
    except rdm.EligibilityError:
        pass

    if plan["manifest_source_fingerprint"] is not None:
        target_fp = plan["manifest_source_fingerprint"].removeprefix("sha256:")
        for split_name, source_path in _SOURCE_PATH_FOR_SPLIT.items():
            if not source_path.exists():
                continue
            for line in source_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                row = _parse_source_line_strict(stripped, source_path.name)
                if rdp.source_fingerprint(row["input"]) == target_fp:
                    raise WithdrawalResidualCheckError(f"{plan['record_id']}: source_fingerprint still resolves to a row in {source_path.name}")

    if plan["record_id"] in rdm.load_rubrics_strict():
        raise WithdrawalResidualCheckError(f"{plan['record_id']}: rubric entry still present")

    for ref in plan["affected_generations"]:
        gen_path = rel.RESULTS_PRIVATE_DIR / ref["relative_path"]
        if gen_path.exists():
            raise WithdrawalResidualCheckError(f"{ref['artifact_id']}: generation artifact still present in active storage")
    for ref in plan["affected_reviews"] + plan["affected_comparisons"] + plan["affected_adjudications"]:
        path = rel.RESULTS_PRIVATE_DIR / ref["relative_path"]
        if path.exists():
            raise WithdrawalResidualCheckError(f"{ref['artifact_id']}: lineage artifact still present in active storage")
    for ref in plan["affected_decisions"]:
        if lin.resolve_active_status(_canonical_ref(ref)) != "invalidated":
            raise WithdrawalResidualCheckError(f"{ref['artifact_id']}: affected decision not invalidated")

    if plan["split"] is not None:
        if snapshot is None:
            raise WithdrawalResidualCheckError(f"{plan['record_id']}: no post-withdrawal dataset snapshot recorded")
        if plan["prior_dataset_fingerprint"] is not None and snapshot["dataset_fingerprint"] == plan["prior_dataset_fingerprint"]:
            raise WithdrawalResidualCheckError(f"{plan['record_id']}: dataset_fingerprint unchanged after withdrawal -- the withdrawn record's removal was not reflected")


def _build_and_save_completion(plan: dict, snapshot: dict | None) -> dict:
    completion = {
        "schema_version": WITHDRAWAL_COMPLETION_SCHEMA_VERSION,
        "artifact_kind": "withdrawal_completion",
        "withdrawal_id": plan["withdrawal_id"],
        "created_at_utc": _now(),
        "record_id": plan["record_id"],
        "plan_artifact_fingerprint": plan["artifact_fingerprint"],
        "post_withdrawal_snapshot": {"snapshot_id": snapshot["snapshot_id"], "artifact_kind": "dataset_snapshot", "artifact_fingerprint": snapshot["artifact_fingerprint"]} if snapshot else None,
    }
    completion["artifact_fingerprint"] = f"sha256:{rdp.artifact_fingerprint(completion)}"
    path = _completion_path_for(plan["withdrawal_id"])
    try:
        lin._save_artifact_exclusive(path, completion)
    except lin.LineageArtifactExistsError:
        return _load_completion_verified(path)  # resume: already written
    return completion


def withdraw_record_validated(record_id: str, requested_by_actor_id: str, reason_code: str, requested_at_utc: str) -> dict:
    """The one public withdrawal entry point. Idempotent: repeating an
    already-completed request for the same record_id returns the same
    completion artifact without further mutation; repeating an
    interrupted request resumes from the first unfinished step. Failure
    reports the pending withdrawal_id without quoting any private content."""
    if reason_code not in ALLOWED_REASON_CODES:
        raise WithdrawalValidationError(f"reason_code must be one of {ALLOWED_REASON_CODES}, got {reason_code!r}")
    _require_actor_id(requested_by_actor_id, "requested_by_actor_id")
    # Both validated -- and record_id specifically -- before any path is
    # constructed or any file touched. A malformed record_id must never
    # reach _lock_path_for; that's what actually prevents a path escape,
    # not the containment check inside _lock_path_for (defense in depth).
    try:
        rdm.validate_record_id_format(record_id)
    except rdm.ManifestValidationError as e:
        raise WithdrawalValidationError(str(e)) from e
    try:
        rdm.validate_utc_timestamp(requested_at_utc, "requested_at_utc")
    except rdm.ManifestValidationError as e:
        raise WithdrawalValidationError(str(e)) from e

    withdrawal_id, existing_completion = _acquire_or_inspect_lock(record_id)
    if existing_completion is not None:
        return existing_completion

    plan_path = _plan_path_for(withdrawal_id)
    try:
        if plan_path.exists():
            plan = _load_plan_verified(plan_path)
        else:
            plan = _build_and_save_plan(record_id=record_id, withdrawal_id=withdrawal_id, requested_by_actor_id=requested_by_actor_id, reason_code=reason_code, requested_at_utc=requested_at_utc)

        _step_mark_manifest_withdrawn(plan)
        _step_remove_source_row(plan)
        _step_remove_rubric_entry(plan)
        _step_invalidate_descendants(plan)
        _step_delete_generation_and_lineage_files(plan)
        _step_delete_other_source_derived_artifacts(plan)
        snapshot = _step_recompute_dataset_snapshot(plan)
        _run_residual_checks(plan, snapshot)
        completion = _build_and_save_completion(plan, snapshot)
        _mark_lock_completed(record_id, withdrawal_id)
        return completion
    except Exception:
        print(f"Withdrawal {withdrawal_id} for the requested record did not complete -- pending, resumable.", file=sys.stderr)
        raise
