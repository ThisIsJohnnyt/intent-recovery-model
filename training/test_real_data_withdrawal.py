"""Standalone assertion tests for real_data_withdrawal.py -- dummy data
only, no real notes. Run with `python test_real_data_withdrawal.py`.
Exits 0 iff every test passes.

Covers the 15 "Withdrawal" adversarial test groups required by
training/real_data_scoring_lineage_withdrawal_design.md. Each test
function's docstring names which group(s) it covers. Uses a real,
isolated private-data root (redirecting every module's path constants)
rather than mocks, so the crash-injection tests exercise the actual
file-based lock/plan/completion mechanism.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

import real_data_eval_logging as rel
import real_data_lineage as lin
import real_data_manifest as rdm
import real_data_private as rdp
import real_data_withdrawal as wd

FAILURES = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


ACTOR_OWNER = "actor_" + "9" * 32
ACTOR_A = "actor_" + "1" * 32
ACTOR_B = "actor_" + "2" * 32
ACTOR_C = "actor_" + "3" * 32
ACTOR_D = "actor_" + "4" * 32

T0, T1, T2 = "2026-08-01T17:00:00Z", "2026-08-01T17:10:00Z", "2026-08-01T17:30:00Z"


class Sandbox:
    """Redirects every path constant this module chain uses to a fresh
    temp directory, and restores them on exit -- lets tests use the real
    file-based logic end to end without touching the actual repo paths."""

    def __init__(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.saved = {}

    def __enter__(self):
        datasets_dir = self.tmp / "datasets"
        results_dir = self.tmp / "results" / "private"
        (datasets_dir / "private").mkdir(parents=True)
        self.datasets_dir = datasets_dir
        self.results_dir = results_dir

        def patch(mod, name, value):
            self.saved[(mod, name)] = getattr(mod, name)
            setattr(mod, name, value)

        patch(rdp, "PRIVATE_DIR", datasets_dir / "private")
        patch(rdp, "MANIFEST_PATH", datasets_dir / "private" / "real_data_manifest.jsonl")
        patch(rdp, "RUBRICS_PATH", datasets_dir / "private" / "real_data_rubrics.jsonl")
        patch(rel, "RESULTS_PRIVATE_DIR", results_dir)
        patch(rel, "VALIDATION_RESULTS_DIR", results_dir / "real_validation")
        patch(rel, "HOLDOUT_RESULTS_DIR", results_dir / "real_holdout")
        patch(lin, "AUDIT_DIR", results_dir / "audit")
        patch(lin, "STATUS_EVENTS_DIR", results_dir / "audit" / "status_events")
        patch(lin, "WITHDRAWALS_DIR", results_dir / "audit" / "withdrawals")
        patch(lin, "DATASET_SNAPSHOTS_DIR", results_dir / "audit" / "dataset_snapshots")
        patch(lin, "DECISIONS_DIR", results_dir / "decisions")
        patch(wd, "WITHDRAWALS_DIR", results_dir / "audit" / "withdrawals")
        patch(wd, "LOCKS_DIR", results_dir / "audit" / "withdrawals" / "locks")
        patch(wd, "_SOURCE_PATH_FOR_SPLIT", {"real_validation": datasets_dir / "real_validation.jsonl", "real_holdout": datasets_dir / "real_holdout.jsonl"})
        return self

    def __exit__(self, *exc):
        for (mod, name), value in self.saved.items():
            setattr(mod, name, value)
        shutil.rmtree(self.tmp, ignore_errors=True)


def _allowed_uses(**overrides):
    base = {"private_annotation": True, "private_evaluation": True, "holdout_eligible": False, "training": False, "publication": False}
    base.update(overrides)
    return base


def _manifest_entry(record_id, *, split=None, source_fp=None, pair_fp=None, rubric_fp=None, holdout=False):
    return {
        "manifest_schema_version": rdm.MANIFEST_SCHEMA_VERSION,
        "record_id": record_id,
        "contributor_id": "contributor_" + "1" * 32,
        "consent_version": "real-consent-v1",
        "consented_at_utc": T0,
        "author_confirmed": True,
        "consent_reviewer_id": ACTOR_OWNER,
        "allowed_uses": _allowed_uses(holdout_eligible=holdout),
        "source_kind": "author_supplied_personal_note",
        "split": split,
        "source_fingerprint": f"sha256:{source_fp}" if source_fp else None,
        "pair_fingerprint": f"sha256:{pair_fp}" if pair_fp and split else None,
        "rubric_fingerprint": f"sha256:{rubric_fp}" if rubric_fp and split else None,
        "deidentification_status": "approved" if source_fp else "pending",
        "deidentified_at_utc": T1 if source_fp else None,
        "deidentified_by_id": ACTOR_A if source_fp else None,
        "deidentification_reviewer_id": ACTOR_B if source_fp else None,
        "annotation_status": "adjudicated" if split else "not_started",
        "adjudicated_at_utc": T2 if split else None,
        "annotation_author_id": ACTOR_C if split else None,
        "annotation_reviewer_id": ACTOR_D if split else None,
        "withdrawal_status": "active",
        "withdrawal_status_changed_at_utc": T0,
    }


def _full_rubric(record_id: str, *, capability_checks: list[str] | None = None, **overrides) -> dict:
    """Exact field set per datasets/REAL_DATA_ANNOTATION_GUIDE.md's
    private rubric sidecar schema -- load_rubrics_strict now enforces all
    of this, not just record_id/status/fingerprint."""
    rubric = {
        "record_id": record_id,
        "must_preserve": ["x"],
        "must_not_infer": [],
        "explicit_actions": [],
        "unresolved_questions": [],
        "attribution_map": [],
        "allowed_surface_variants": [],
        "capability_checks": capability_checks if capability_checks is not None else [],
        "adjudication_notes": "",
        "rubric_status": "adjudicated",
    }
    rubric.update(overrides)
    return rubric


def _setup_validation_record(sandbox: Sandbox, suffix: str = "1", *, input_text: str = None):
    record_id = f"rv_{suffix.rjust(32, '0')}"
    inp = input_text or f"TESTMARKER_WITHDRAWAL_DRILL_{suffix} water the plants tomorrow"
    out = {"narrative": f"Water the plants {suffix}.", "bullets": [f"Water plants {suffix}"], "action_items": [f"Water plants {suffix}"]}
    rubric = _full_rubric(record_id, must_preserve=[suffix])

    sfp = rdp.source_fingerprint(inp)
    pfp = rdp.pair_fingerprint(inp, out)
    rfp = rdp.rubric_fingerprint(rubric)
    entry = _manifest_entry(record_id, split="real_validation", source_fp=sfp, pair_fp=pfp, rubric_fp=rfp)
    rdm.upsert_manifest_entry_validated(entry, pilot_mode=True)
    rdp.upsert_rubric_entry({**rubric, "rubric_fingerprint": f"sha256:{rfp}"})

    validation_path = sandbox.datasets_dir / "real_validation.jsonl"
    with validation_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"input": inp, "output": out}) + "\n")
    return record_id, inp, out, rubric, sfp, pfp, rfp


def _build_generation_for(record_id, sfp, pfp, rfp, *, split="real_validation"):
    rec = rel.new_generation_record(record_id=record_id, source_fingerprint=sfp, pair_fingerprint=pfp, rubric_fingerprint=rfp, raw_output="###NARRATIVE### x ###BULLETS### x ###ACTIONS###", format_valid=True)
    artifact = rel.build_generation_artifact(
        split=split,
        evaluation_reason="dummy withdrawal test",
        git_commit="deadbeef",
        checkpoint={"path": "dummy", "fingerprint": "a" * 64, "training_seed": 1, "run_id": "run_dummy"},
        dataset={"fingerprint": "b" * 64, "record_count": 1, "rubric_schema_version": "real-rubric-v1"},
        generation_config={},
        results=[rec],
    )
    saved_path = rel.save_generation_artifact(artifact)
    return artifact, saved_path


def _build_full_lineage(generation, gen_path, rubric, rfp):
    """rubric/rfp: the exact rubric (and its bare fingerprint) that was
    bound to this record's manifest/generation entry at setup time --
    build_review_score_record now verifies a submitted rubric's own
    recomputed fingerprint against the generation record's bound
    rubric_fingerprint (Phase E lineage/withdrawal second review, finding
    2), so an unrelated ad hoc rubric can no longer be substituted here."""
    full_rubric = {**rubric, "rubric_fingerprint": f"sha256:{rfp}"}
    scores = [lin.build_review_score_record(generation_record=generation["results"][0], rubric=full_rubric, scores={dim: True for dim in __import__("real_data_scoring").SEMANTIC_DIMENSIONS}, capability_checks={}, failure_labels=[])]
    chatgpt_review = lin.build_review_artifact(generation_path=gen_path, reviewer_role="chatgpt", reviewer_actor_id=ACTOR_A, independent_review_attestation=True, scores=scores)
    claude_review = lin.build_review_artifact(generation_path=gen_path, reviewer_role="claude", reviewer_actor_id=ACTOR_B, independent_review_attestation=True, scores=scores)
    rubrics = {generation["results"][0]["record_id"]: full_rubric}
    chatgpt_path = lin.save_review_artifact(chatgpt_review, generation_path=gen_path, rubrics=rubrics, split=generation["split"], milestone=generation.get("release_milestone"))
    claude_path = lin.save_review_artifact(claude_review, generation_path=gen_path, rubrics=rubrics, split=generation["split"], milestone=generation.get("release_milestone"))
    comparison = lin.build_comparison_artifact(chatgpt_review_path=chatgpt_path, claude_review_path=claude_path, generation_path=gen_path, rubrics=rubrics)
    comparison_path = lin.save_comparison_artifact(
        comparison,
        chatgpt_review_path=chatgpt_path,
        claude_review_path=claude_path,
        generation_path=gen_path,
        rubrics=rubrics,
        split=generation["split"],
        milestone=generation.get("release_milestone"),
    )
    adjudication = lin.build_adjudication_artifact(
        comparison_path=comparison_path, chatgpt_review_path=chatgpt_path, claude_review_path=claude_path, generation_path=gen_path, rubrics=rubrics, resolution_mode="reviewer_agreement"
    )
    adjudication_path = lin.save_adjudication_artifact(
        adjudication,
        comparison_path=comparison_path,
        chatgpt_review_path=chatgpt_path,
        claude_review_path=claude_path,
        generation_path=gen_path,
        rubrics=rubrics,
        split=generation["split"],
        milestone=generation.get("release_milestone"),
    )
    decision = lin.build_decision_record(decision_type="curriculum", deciding_actor_id=ACTOR_OWNER, adjudication_paths=[adjudication_path], outcome="dummy decision for withdrawal test")
    lin.save_decision_record(decision, adjudication_paths=[adjudication_path])
    return chatgpt_review, claude_review, comparison, adjudication, decision


# --- ChatGPT implementation review finding 1: record_id path escape ---


def _no_files_created_anywhere(sb: "Sandbox") -> bool:
    """Scans the whole sandbox tmp tree (not just the expected results
    root) for any file at all -- a path-escape bug could land a file
    outside the intended root entirely, so checking only the expected
    location would miss exactly the failure mode being tested."""
    return not any(p.is_file() for p in sb.tmp.rglob("*"))


def test_record_id_and_timestamp_validated_before_any_write():
    """ChatGPT review finding 1: a malformed record_id must be rejected
    before _lock_path_for is ever reached, and must not be able to
    traverse outside LOCKS_DIR even as defense in depth. No file may be
    created anywhere for a rejected request."""
    malicious_record_ids = [
        "../../../escaped",
        "../escaped_outside_results",
        "/etc/passwd",
        "rv_short",  # wrong length
        "rv_" + "g" * 32,  # non-hex
        "not_even_the_right_prefix",
        "",
    ]
    for bad_id in malicious_record_ids:
        with Sandbox() as sb:
            raised = False
            try:
                wd.withdraw_record_validated(bad_id, ACTOR_OWNER, "contributor_request", T2)
            except wd.WithdrawalValidationError:
                raised = True
            check(f"withdraw_record_validated: malformed record_id {bad_id!r} rejected", raised)
            check(f"withdraw_record_validated: no file created anywhere for record_id {bad_id!r}", _no_files_created_anywhere(sb))

    for bad_timestamp in ("not-a-timestamp", "2026-08-01T17:00:00+05:00", "2026-08-01", 12345, None):
        with Sandbox() as sb:
            record_id, *_ = _setup_validation_record(sb, "9")
            raised = False
            try:
                wd.withdraw_record_validated(record_id, ACTOR_OWNER, "contributor_request", bad_timestamp)
            except wd.WithdrawalValidationError:
                raised = True
            check(f"withdraw_record_validated: malformed requested_at_utc {bad_timestamp!r} rejected", raised)
            check(f"withdraw_record_validated: no lock file created for malformed timestamp {bad_timestamp!r}", not list(wd.LOCKS_DIR.glob("*")) if wd.LOCKS_DIR.exists() else True)


# --- Group 16: every lifecycle stage withdraws correctly ---


def test_withdrawal_at_every_lifecycle_stage():
    """Group 16."""
    with Sandbox():
        consent_only = _manifest_entry("rv_" + "1" * 32)
        rdm.upsert_manifest_entry_validated(consent_only, pilot_mode=True)
        completion = wd.withdraw_record_validated(consent_only["record_id"], ACTOR_OWNER, "contributor_request", T2)
        manifest = rdm.load_manifest_strict(pilot_mode=True)
        check("withdrawal: consent-only record reaches withdrawn status", manifest[consent_only["record_id"]]["withdrawal_status"] == "withdrawn")
        check("withdrawal: consent-only record produces a completion artifact", completion["record_id"] == consent_only["record_id"])

    with Sandbox() as sb:
        record_id, *_ = _setup_validation_record(sb, "2")
        wd.withdraw_record_validated(record_id, ACTOR_OWNER, "contributor_request", T2)
        manifest = rdm.load_manifest_strict(pilot_mode=True)
        check("withdrawal: evaluation-ready validation record reaches withdrawn status", manifest[record_id]["withdrawal_status"] == "withdrawn")
        check("withdrawal: source row removed from real_validation.jsonl", not (sb.datasets_dir / "real_validation.jsonl").read_text(encoding="utf-8").strip())


# --- Group 17: duplicate/ambiguous source rows fail before mutation ---


def test_ambiguous_source_rows_fail_before_mutation():
    """Group 17."""
    with Sandbox() as sb:
        record_id, inp, out, rubric, sfp, pfp, rfp = _setup_validation_record(sb, "3")
        # Inject a second row with the exact same input (same source_fingerprint).
        validation_path = sb.datasets_dir / "real_validation.jsonl"
        with validation_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"input": inp, "output": out}) + "\n")

        manifest_bytes_before = rdp.MANIFEST_PATH.read_bytes()
        source_bytes_before = validation_path.read_bytes()
        raised = False
        try:
            wd.withdraw_record_validated(record_id, ACTOR_OWNER, "contributor_request", T2)
        except wd.WithdrawalValidationError:
            raised = True
        check("withdrawal: ambiguous duplicate source rows rejected", raised)
        check("withdrawal: manifest unchanged after rejection", rdp.MANIFEST_PATH.read_bytes() == manifest_bytes_before)
        check("withdrawal: source file unchanged after rejection", validation_path.read_bytes() == source_bytes_before)


# --- Group 18: a multi-record generation is wholly invalidated ---


def test_multi_record_generation_wholly_invalidated():
    """Group 18."""
    with Sandbox() as sb:
        record_id_1, _, _, _, sfp1, pfp1, rfp1 = _setup_validation_record(sb, "4")
        record_id_2, _, _, _, sfp2, pfp2, rfp2 = _setup_validation_record(sb, "5")

        rec1 = rel.new_generation_record(record_id=record_id_1, source_fingerprint=sfp1, pair_fingerprint=pfp1, rubric_fingerprint=rfp1, raw_output="x", format_valid=True)
        rec2 = rel.new_generation_record(record_id=record_id_2, source_fingerprint=sfp2, pair_fingerprint=pfp2, rubric_fingerprint=rfp2, raw_output="y", format_valid=True)
        artifact = rel.build_generation_artifact(
            split="real_validation",
            evaluation_reason="multi-record dummy test",
            git_commit="deadbeef",
            checkpoint={"path": "dummy", "fingerprint": "a" * 64, "training_seed": 1, "run_id": "run"},
            dataset={"fingerprint": "b" * 64, "record_count": 2, "rubric_schema_version": "real-rubric-v1"},
            generation_config={},
            results=[rec1, rec2],
        )
        saved_path = rel.save_generation_artifact(artifact)

        wd.withdraw_record_validated(record_id_1, ACTOR_OWNER, "contributor_request", T2)
        check("withdrawal: multi-record generation file deleted even though only one record withdrew", not saved_path.exists())

        manifest = rdm.load_manifest_strict(pilot_mode=True)
        check("withdrawal: the OTHER record's manifest entry remains active (only the generation evidence was invalidated, not its consent)", manifest[record_id_2]["withdrawal_status"] == "active")


# --- Group 19: all descendants discovered ---


def test_all_descendants_discovered():
    """Group 19."""
    with Sandbox() as sb:
        record_id, _, _, rubric, sfp, pfp, rfp = _setup_validation_record(sb, "6")
        generation, gen_path = _build_generation_for(record_id, sfp, pfp, rfp)
        chatgpt_review, claude_review, comparison, adjudication, decision = _build_full_lineage(generation, gen_path, rubric, rfp)

        completion = wd.withdraw_record_validated(record_id, ACTOR_OWNER, "contributor_request", T2)
        plan = wd._load_plan_verified(wd._plan_path_for(completion["withdrawal_id"]))
        check("withdrawal: discovers the generation", len(plan["affected_generations"]) == 1)
        check("withdrawal: discovers both reviews", len(plan["affected_reviews"]) == 2)
        check("withdrawal: discovers the comparison", len(plan["affected_comparisons"]) == 1)
        check("withdrawal: discovers the adjudication", len(plan["affected_adjudications"]) == 1)
        check("withdrawal: discovers the decision", len(plan["affected_decisions"]) == 1)


# --- Group 20: invalidation events exist before deletion ---


def test_invalidation_events_written():
    """Group 20 (ordering enforced by the fixed execution sequence in
    withdraw_record_validated; this confirms the events actually land)."""
    with Sandbox() as sb:
        record_id, _, _, rubric, sfp, pfp, rfp = _setup_validation_record(sb, "7")
        generation, gen_path = _build_generation_for(record_id, sfp, pfp, rfp)
        chatgpt_review, claude_review, comparison, adjudication, decision = _build_full_lineage(generation, gen_path, rubric, rfp)

        wd.withdraw_record_validated(record_id, ACTOR_OWNER, "contributor_request", T2)
        check("withdrawal: generation status resolves to invalidated", lin.resolve_active_status(lin._artifact_ref(generation, "evaluation_id")) == "invalidated")
        check("withdrawal: adjudication status resolves to invalidated", lin.resolve_active_status(lin._artifact_ref(adjudication, "adjudication_id")) == "invalidated")
        check("withdrawal: decision status resolves to invalidated", lin.resolve_active_status(lin._artifact_ref(decision, "decision_id")) == "invalidated")


# --- Group 21: affected holdout seals retired ---


def test_affected_seals_always_empty_no_mechanism_yet():
    """Group 21 -- no holdout-seal mechanism exists yet (see
    real_data_manifest.load_approved_seal), so this documents the current
    stub rather than testing real retirement."""
    with Sandbox() as sb:
        record_id, *_ = _setup_validation_record(sb, "8")
        completion = wd.withdraw_record_validated(record_id, ACTOR_OWNER, "contributor_request", T2)
        plan = wd._load_plan_verified(wd._plan_path_for(completion["withdrawal_id"]))
        check("withdrawal: affected_seals is always empty (no seal mechanism implemented yet)", plan["affected_seals"] == [])


# --- Group 22: dataset fingerprint changes; empty dataset deterministic ---


def test_dataset_fingerprint_changes_and_empty_is_deterministic():
    """Group 22."""
    with Sandbox() as sb:
        record_id, *_ = _setup_validation_record(sb, "9")
        prior_fp = f"sha256:{rdp.dataset_fingerprint([], 'real_validation')}"  # only record active -> after withdrawal, empty
        wd.withdraw_record_validated(record_id, ACTOR_OWNER, "contributor_request", T2)
        snapshot_dir = lin.DATASET_SNAPSHOTS_DIR / "real_validation"
        snapshots = list(snapshot_dir.glob("*.json"))
        check("withdrawal: a post-withdrawal snapshot was written", len(snapshots) == 1)
        snapshot = json.loads(snapshots[0].read_text(encoding="utf-8"))
        check("withdrawal: empty-split snapshot fingerprint matches the deterministic empty-dataset value", snapshot["dataset_fingerprint"] == prior_fp)
        check("withdrawal: empty snapshot has no active_records", snapshot["active_records"] == [])


# --- Group 23: no source/generated text in plan/status/snapshot/completion ---


def test_no_private_content_in_audit_artifacts():
    """Group 23."""
    with Sandbox() as sb:
        marker = "TESTMARKER_SECRET_CONTENT_MUST_NOT_LEAK"
        record_id, inp, out, rubric, sfp, pfp, rfp = _setup_validation_record(sb, "10", input_text=f"{marker} water the plants")
        generation, gen_path = _build_generation_for(record_id, sfp, pfp, rfp)
        _build_full_lineage(generation, gen_path, rubric, rfp)

        completion = wd.withdraw_record_validated(record_id, ACTOR_OWNER, "contributor_request", T2)

        audit_root = sb.results_dir / "audit"
        leaked = []
        for p in audit_root.rglob("*.json"):
            if marker in p.read_text(encoding="utf-8"):
                leaked.append(str(p))
        check("withdrawal: no audit artifact (plan/status/snapshot/completion) contains the source marker text", leaked == [], str(leaked))


# --- ChatGPT implementation review finding 6: plan-creation race ---


def test_concurrent_plan_creation_race_resolves_to_persisted_plan():
    """Two callers racing to create the same withdrawal_id's plan (both
    legitimately resuming the same lock) must both end up using the one
    persisted, verified plan -- not the loser's own in-memory copy, which
    could differ subtly (e.g. active_records computed a moment apart)
    from what was actually committed."""
    with Sandbox() as sb:
        record_id, *_ = _setup_validation_record(sb, "8")
        withdrawal_id, existing_completion = wd._acquire_or_inspect_lock(record_id)
        check("race setup: no completion exists yet for a fresh withdrawal", existing_completion is None)

        first_plan = wd._build_and_save_plan(record_id=record_id, withdrawal_id=withdrawal_id, requested_by_actor_id=ACTOR_OWNER, reason_code="contributor_request", requested_at_utc=T2)
        # Simulate a second, "racing" caller computing the same plan again --
        # it must lose the exclusive-create race and load the winner instead.
        second_plan = wd._build_and_save_plan(record_id=record_id, withdrawal_id=withdrawal_id, requested_by_actor_id=ACTOR_OWNER, reason_code="contributor_request", requested_at_utc=T2)
        check("plan race: both callers converge on the identical persisted plan", first_plan == second_plan)
        check("plan race: only one plan file exists on disk", len(list((wd.WITHDRAWALS_DIR / withdrawal_id).glob("*.json"))) == 1)


def test_concurrent_plan_creation_race_with_conflicting_request_fails_closed():
    """Phase E lineage/withdrawal second review, finding 5: the plan-race
    recovery path previously compared only record_id/withdrawal_id -- a
    second, differently-parameterized request racing for the same
    withdrawal_id (different actor, reason, or requested_at_utc) would
    silently adopt the winner's persisted plan with no mismatch ever
    surfaced. It must instead fail closed on any identity mismatch."""
    with Sandbox() as sb:
        record_id, *_ = _setup_validation_record(sb, "9")
        withdrawal_id, existing_completion = wd._acquire_or_inspect_lock(record_id)
        wd._build_and_save_plan(record_id=record_id, withdrawal_id=withdrawal_id, requested_by_actor_id=ACTOR_OWNER, reason_code="contributor_request", requested_at_utc=T2)

        raised = False
        try:
            wd._build_and_save_plan(record_id=record_id, withdrawal_id=withdrawal_id, requested_by_actor_id=ACTOR_A, reason_code="contributor_request", requested_at_utc=T2)
        except wd.WithdrawalValidationError:
            raised = True
        check("plan race: a racing request with a different requested_by_actor_id fails closed instead of silently adopting the winner", raised)

        raised = False
        try:
            wd._build_and_save_plan(record_id=record_id, withdrawal_id=withdrawal_id, requested_by_actor_id=ACTOR_OWNER, reason_code="consent_expired", requested_at_utc=T2)
        except wd.WithdrawalValidationError:
            raised = True
        check("plan race: a racing request with a different reason_code fails closed", raised)

        raised = False
        try:
            wd._build_and_save_plan(record_id=record_id, withdrawal_id=withdrawal_id, requested_by_actor_id=ACTOR_OWNER, reason_code="contributor_request", requested_at_utc=T1)
        except wd.WithdrawalValidationError:
            raised = True
        check("plan race: a racing request with a different requested_at_utc fails closed", raised)


def test_withdrawal_plan_and_completion_kinds_registered():
    """Phase E lineage/withdrawal second review, finding 3: withdrawal_plan
    and withdrawal_completion must be registered kinds with their own
    exact field set (registered by this module at import time), not
    silently skipped by _assert_exact_fields."""
    check("withdrawal_plan is registered in lin._KIND_METADATA", "withdrawal_plan" in lin._KIND_METADATA)
    check("withdrawal_completion is registered in lin._KIND_METADATA", "withdrawal_completion" in lin._KIND_METADATA)

    with Sandbox():
        fake_plan = {
            "schema_version": wd.WITHDRAWAL_PLAN_SCHEMA_VERSION,
            "artifact_kind": "withdrawal_plan",
            "withdrawal_id": "wd_" + "1" * 32,
            "created_at_utc": T2,
            "unexpected_field": "smuggled",
        }
        fake_plan["artifact_fingerprint"] = f"sha256:{rdp.artifact_fingerprint(fake_plan)}"
        tmp_dir = Path(tempfile.mkdtemp())
        try:
            plan_path = tmp_dir / "plan.json"
            plan_path.write_text(json.dumps(fake_plan), encoding="utf-8")
            raised = False
            try:
                wd._load_plan_verified(plan_path)
            except lin.LineageValidationError:
                raised = True
            check("_load_plan_verified: rejects a withdrawal_plan with an unknown field and missing required fields", raised)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


def test_withdrawal_plan_affected_entry_with_absolute_relative_path_rejected():
    """Phase E lineage/withdrawal third review, finding 4: Path.__truediv__
    silently discards its left operand when the right operand is absolute
    (Path("/a") / "/etc/passwd" == Path("/etc/passwd")), so an absolute
    relative_path in a plan's affected-entry list would let
    _step_delete_generation_and_lineage_files delete an arbitrary file
    outside the private-results tree. Reproduces the review's
    unvalidated_withdrawal_plan_entry_accepted live finding."""
    with Sandbox() as sb:
        record_id, _, _, rubric, sfp, pfp, rfp = _setup_validation_record(sb, "1")
        generation, gen_path = _build_generation_for(record_id, sfp, pfp, rfp)
        completion = wd.withdraw_record_validated(record_id, ACTOR_OWNER, "contributor_request", T2)
        plan_path = wd._plan_path_for(completion["withdrawal_id"])
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        check("plan discovered exactly one affected generation", len(plan["affected_generations"]) == 1)

        tampered = dict(plan)
        tampered["affected_generations"] = [{**plan["affected_generations"][0], "relative_path": "/outside/private/root.json"}]
        tampered["artifact_fingerprint"] = f"sha256:{rdp.artifact_fingerprint(tampered)}"
        plan_path.write_text(json.dumps(tampered), encoding="utf-8")

        raised = False
        try:
            wd._load_plan_verified(plan_path)
        except wd.WithdrawalValidationError:
            raised = True
        check("_load_plan_verified: rejects a plan with an absolute relative_path in an affected entry", raised)


def test_withdrawal_plan_entry_relative_path_must_match_canonical():
    """Phase E lineage/withdrawal fourth verification, finding 4:
    relative_path was checked for containment only, not for equality with
    the canonical path implied by the entry's own identifiers (artifact
    kind, ID, split, milestone) -- an entry could be redirected to a
    different, still-active file inside the private-results root.
    Reproduces the review's noncanonical_withdrawal_path live finding."""
    with Sandbox() as sb:
        record_id, _, _, rubric, sfp, pfp, rfp = _setup_validation_record(sb, "2")
        generation, gen_path = _build_generation_for(record_id, sfp, pfp, rfp)
        completion = wd.withdraw_record_validated(record_id, ACTOR_OWNER, "contributor_request", T2)
        plan_path = wd._plan_path_for(completion["withdrawal_id"])
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        check("plan discovered exactly one affected generation", len(plan["affected_generations"]) == 1)

        tampered = dict(plan)
        tampered["affected_generations"] = [{**plan["affected_generations"][0], "relative_path": "real_validation/different_generation.json"}]
        tampered["artifact_fingerprint"] = f"sha256:{rdp.artifact_fingerprint(tampered)}"
        plan_path.write_text(json.dumps(tampered), encoding="utf-8")

        raised = False
        try:
            wd._load_plan_verified(plan_path)
        except wd.WithdrawalValidationError:
            raised = True
        check("_load_plan_verified: rejects a plan whose relative_path is redirected to a different, still-contained file", raised)


# --- Group 24: crash injection -- resumable after failure at each stage ---


def test_crash_injection_resumes_correctly():
    """Group 24. Per the Phase E lineage/withdrawal implementation review's
    finding 6, crash coverage previously stopped at the four 'middle'
    execution steps -- plan creation, completion creation, and lock
    completion are now covered too."""
    runs_before_manifest_update = {"_build_and_save_plan"}
    injection_points = [
        "_build_and_save_plan",
        "_step_mark_manifest_withdrawn",
        "_step_invalidate_descendants",
        "_step_delete_generation_and_lineage_files",
        "_step_recompute_dataset_snapshot",
        "_build_and_save_completion",
        "_mark_lock_completed",
    ]
    for injection_point in injection_points:
        with Sandbox() as sb:
            record_id, _, _, rubric, sfp, pfp, rfp = _setup_validation_record(sb, "1", input_text=f"TESTMARKER_CRASH_{injection_point} water the plants")
            generation, gen_path = _build_generation_for(record_id, sfp, pfp, rfp)
            _build_full_lineage(generation, gen_path, rubric, rfp)

            original = getattr(wd, injection_point)

            def boom(*args, __orig=original, **kwargs):
                raise RuntimeError("injected crash")

            setattr(wd, injection_point, boom)
            crashed = False
            try:
                wd.withdraw_record_validated(record_id, ACTOR_OWNER, "contributor_request", T2)
            except RuntimeError:
                crashed = True
            finally:
                setattr(wd, injection_point, original)
            check(f"crash at {injection_point}: raised as expected", crashed)

            manifest_mid_crash = rdm.load_manifest_strict(pilot_mode=True)
            if injection_point in runs_before_manifest_update or injection_point == "_step_mark_manifest_withdrawn":
                # The crash happens at or before the manifest-update step -- it never ran, so nothing committed yet.
                # Still a safe state: no partial mutation, and resuming below applies it correctly.
                check(f"crash at {injection_point}: manifest still active (the crashed step never ran)", manifest_mid_crash[record_id]["withdrawal_status"] == "active")
            else:
                # Every later injection point runs only after step A (manifest update) already committed.
                check(f"crash at {injection_point}: manifest already shows withdrawn/ineligible despite the crash", manifest_mid_crash[record_id]["withdrawal_status"] == "withdrawn")

            # Resume: same call, no crash this time.
            completion = wd.withdraw_record_validated(record_id, ACTOR_OWNER, "contributor_request", T2)
            check(f"crash at {injection_point}: resumed call completes successfully", completion["record_id"] == record_id)
            check(f"crash at {injection_point}: resumed completion references a real snapshot", completion["post_withdrawal_snapshot"] is not None)


# --- Group 25: repeating a completed withdrawal is a no-op ---


def test_repeat_completed_withdrawal_is_noop():
    """Group 25."""
    with Sandbox() as sb:
        record_id, *_ = _setup_validation_record(sb, "2")
        first = wd.withdraw_record_validated(record_id, ACTOR_OWNER, "contributor_request", T2)
        status_events_before = list(lin.STATUS_EVENTS_DIR.glob("*.json"))
        second = wd.withdraw_record_validated(record_id, ACTOR_OWNER, "contributor_request", T2)
        status_events_after = list(lin.STATUS_EVENTS_DIR.glob("*.json"))
        check("withdrawal: repeated call returns the identical completion artifact", first == second)
        check("withdrawal: repeated call creates no new status events", len(status_events_before) == len(status_events_after))


# --- Group 26: terminal records cannot reactivate ---


def test_withdrawn_record_cannot_reactivate():
    """Group 26."""
    with Sandbox() as sb:
        record_id, *_ = _setup_validation_record(sb, "3")
        wd.withdraw_record_validated(record_id, ACTOR_OWNER, "contributor_request", T2)
        manifest = rdm.load_manifest_strict(pilot_mode=True)
        entry = manifest[record_id]
        reactivated = {**entry, "withdrawal_status": "active"}
        raised = False
        try:
            rdm.upsert_manifest_entry_validated(reactivated, pilot_mode=True)
        except rdm.ManifestValidationError:
            raised = True
        check("withdrawal: attempting to reactivate a withdrawn record is rejected", raised)


# --- Group 27: malformed artifacts fail closed instead of being skipped ---


def test_malformed_artifact_fails_discovery_closed():
    """Group 27."""
    with Sandbox() as sb:
        record_id, _, _, _, sfp, pfp, rfp = _setup_validation_record(sb, "4")
        generation, gen_path = _build_generation_for(record_id, sfp, pfp, rfp)

        # Plant an unrelated, tampered generation file in the same directory --
        # discovery must fail closed on it rather than silently skipping it,
        # even though it doesn't reference the record being withdrawn.
        tampered_path = rel.VALIDATION_RESULTS_DIR / "eval_tampered000.json"
        tampered = {**generation, "evaluation_id": "eval_tampered000", "evaluation_reason": "tampered after fingerprinting"}
        tampered_path.write_text(json.dumps(tampered), encoding="utf-8")

        raised = False
        try:
            wd.withdraw_record_validated(record_id, ACTOR_OWNER, "contributor_request", T2)
        except wd.WithdrawalDiscoveryError:
            raised = True
        check("withdrawal: a malformed/tampered generation file anywhere in scope fails discovery closed", raised)


# --- Group 28: residual evaluation attempts fail before generation ---


def test_residual_evaluation_attempt_fails_before_generation():
    """Group 28."""
    with Sandbox() as sb:
        record_id, inp, out, rubric, sfp, pfp, rfp = _setup_validation_record(sb, "5")
        wd.withdraw_record_validated(record_id, ACTOR_OWNER, "contributor_request", T2)

        # Re-add the exact same content to the source split (simulating an
        # attempt to re-evaluate) -- linking must fail before any generation.
        validation_path = sb.datasets_dir / "real_validation.jsonl"
        validation_path.write_text(json.dumps({"input": inp, "output": out}) + "\n", encoding="utf-8")
        raised = False
        try:
            import prepare_data

            records = prepare_data.load_jsonl_strict(validation_path)
            rdm.link_records_to_manifest(records, expected_split="real_validation", pilot_mode=True)
        except rdm.EligibilityError:
            raised = True
        check("withdrawal: re-evaluating withdrawn content fails at linking, before any model generation", raised)


# --- Group 29: active-storage artifacts absent after completion ---


def test_active_storage_artifacts_absent_after_completion():
    """Group 29."""
    with Sandbox() as sb:
        record_id, _, _, rubric, sfp, pfp, rfp = _setup_validation_record(sb, "6")
        generation, gen_path = _build_generation_for(record_id, sfp, pfp, rfp)
        chatgpt_review, claude_review, comparison, adjudication, decision = _build_full_lineage(generation, gen_path, rubric, rfp)

        wd.withdraw_record_validated(record_id, ACTOR_OWNER, "contributor_request", T2)
        check("withdrawal: generation file absent from active storage", not gen_path.exists())
        lineage_dir = lin.lineage_root_for("real_validation", generation["evaluation_id"])
        check("withdrawal: entire lineage directory removed from active storage", not lineage_dir.exists())


# --- Group 30: invalidated decisions cannot be used as current evidence ---


def test_invalidated_decision_not_current_evidence():
    """Group 30."""
    with Sandbox() as sb:
        record_id, _, _, rubric, sfp, pfp, rfp = _setup_validation_record(sb, "7")
        generation, gen_path = _build_generation_for(record_id, sfp, pfp, rfp)
        chatgpt_review, claude_review, comparison, adjudication, decision = _build_full_lineage(generation, gen_path, rubric, rfp)

        wd.withdraw_record_validated(record_id, ACTOR_OWNER, "contributor_request", T2)
        check("withdrawal: decision's status resolves to invalidated, not active", lin.resolve_active_status(lin._artifact_ref(decision, "decision_id")) == "invalidated")


def main() -> None:
    tests = [
        test_record_id_and_timestamp_validated_before_any_write,
        test_withdrawal_at_every_lifecycle_stage,
        test_ambiguous_source_rows_fail_before_mutation,
        test_multi_record_generation_wholly_invalidated,
        test_all_descendants_discovered,
        test_invalidation_events_written,
        test_affected_seals_always_empty_no_mechanism_yet,
        test_dataset_fingerprint_changes_and_empty_is_deterministic,
        test_no_private_content_in_audit_artifacts,
        test_concurrent_plan_creation_race_resolves_to_persisted_plan,
        test_concurrent_plan_creation_race_with_conflicting_request_fails_closed,
        test_withdrawal_plan_and_completion_kinds_registered,
        test_withdrawal_plan_affected_entry_with_absolute_relative_path_rejected,
        test_withdrawal_plan_entry_relative_path_must_match_canonical,
        test_crash_injection_resumes_correctly,
        test_repeat_completed_withdrawal_is_noop,
        test_withdrawn_record_cannot_reactivate,
        test_malformed_artifact_fails_discovery_closed,
        test_residual_evaluation_attempt_fails_before_generation,
        test_active_storage_artifacts_absent_after_completion,
        test_invalidated_decision_not_current_evidence,
    ]
    for t in tests:
        t()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("All real_data_withdrawal.py tests passed.")


if __name__ == "__main__":
    main()
