"""Standalone assertion tests for real_data_lineage.py -- dummy data only,
no real notes. Run with `python test_real_data_lineage.py`. Exits 0 iff
every test passes.

Covers the 15 "Scoring lineage" adversarial test groups required by
training/real_data_scoring_lineage_withdrawal_design.md, plus the residual
findings from the Phase E lineage/withdrawal second review (verified-
stored-parent enforcement, rubric-fingerprint binding, plan/completion
schema registration, duplicate-ID rejection everywhere, nested reference
shapes). Each test function's docstring names which group(s)/finding(s)
it covers.

Every artifact a test needs as a "parent" is actually saved to a sandboxed
filesystem and referenced by path -- build_review_artifact/
build_comparison_artifact/build_adjudication_artifact/build_decision_record
now load and verify parents from their real stored location rather than
trusting a caller-supplied in-memory dict, so an unsaved dict can no
longer be used as a parent at all.
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
import real_data_scoring as rsc

FAILURES = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


def _expect_error(exc_type, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
        return None
    except exc_type as e:
        return str(e)


class Sandbox:
    """Redirects every path constant real_data_eval_logging.py/
    real_data_lineage.py use to a fresh temp directory, and restores them
    on exit -- lets every test save real generation/review/comparison/
    adjudication/decision/status-event files, which is now required since
    every lineage builder loads and verifies its parents from their actual
    stored path rather than accepting an in-memory dict."""

    def __init__(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.saved = {}

    def __enter__(self):
        results_dir = self.tmp / "results" / "private"

        def patch(mod, name, value):
            self.saved[(mod, name)] = getattr(mod, name)
            setattr(mod, name, value)

        patch(rel, "RESULTS_PRIVATE_DIR", results_dir)
        patch(rel, "VALIDATION_RESULTS_DIR", results_dir / "real_validation")
        patch(rel, "HOLDOUT_RESULTS_DIR", results_dir / "real_holdout")
        patch(lin, "AUDIT_DIR", results_dir / "audit")
        patch(lin, "STATUS_EVENTS_DIR", results_dir / "audit" / "status_events")
        patch(lin, "WITHDRAWALS_DIR", results_dir / "audit" / "withdrawals")
        patch(lin, "DATASET_SNAPSHOTS_DIR", results_dir / "audit" / "dataset_snapshots")
        patch(lin, "DECISIONS_DIR", results_dir / "decisions")
        return self

    def __exit__(self, *exc):
        for (mod, name), value in self.saved.items():
            setattr(mod, name, value)
        shutil.rmtree(self.tmp, ignore_errors=True)


ACTOR_CHATGPT = "actor_" + "1" * 32
ACTOR_CLAUDE = "actor_" + "2" * 32
ACTOR_OWNER = "actor_" + "3" * 32

RV_A = "rv_" + "a" * 32
RV_B = "rv_" + "b" * 32


def _full_rubric(record_id: str, *, capability_checks: list[str]) -> dict:
    """Exact field set per datasets/REAL_DATA_ANNOTATION_GUIDE.md's private
    rubric sidecar schema -- build_review_score_record now re-validates a
    submitted rubric through the same strict validator load_rubrics_strict
    uses (Phase E lineage/withdrawal second review finding 2), so a
    partial ad hoc rubric shape no longer passes."""
    return {
        "record_id": record_id,
        "must_preserve": ["dummy preserve"],
        "must_not_infer": [],
        "explicit_actions": [],
        "unresolved_questions": [],
        "attribution_map": [],
        "allowed_surface_variants": [],
        "capability_checks": capability_checks,
        "adjudication_notes": "dummy adjudication notes",
        "rubric_status": "adjudicated",
        "rubric_fingerprint": "sha256:" + "0" * 64,  # format-only placeholder, never cross-checked against content
    }


RUBRIC_A = _full_rubric(RV_A, capability_checks=["explicit_task_survived"])
RUBRIC_B = _full_rubric(RV_B, capability_checks=[])
_RUBRICS_BY_RECORD_ID = {RV_A: RUBRIC_A, RV_B: RUBRIC_B}


def _dummy_generation(rubrics: list[dict] | None = None) -> tuple[dict, Path]:
    """Builds and saves a generation artifact, one record per rubric in
    rubrics (default: both RUBRIC_A and RUBRIC_B) -- each record's
    rubric_fingerprint is the real recomputed fingerprint of its rubric,
    since build_review_score_record now verifies that binding rather than
    trusting whatever rubric a caller hands it."""
    rubrics = rubrics if rubrics is not None else [RUBRIC_A, RUBRIC_B]
    records = []
    for i, rubric in enumerate(rubrics):
        records.append(
            rel.new_generation_record(
                record_id=rubric["record_id"],
                source_fingerprint=f"{i}" * 64,
                pair_fingerprint=f"{i + 1}" * 64,
                rubric_fingerprint=rdp.rubric_fingerprint(rubric),
                raw_output=f"###NARRATIVE### dummy {i} ###BULLETS### x ###ACTIONS###",
                format_valid=True,
            )
        )
    artifact = rel.build_generation_artifact(
        split="real_validation",
        evaluation_reason="dummy lineage test",
        git_commit="deadbeef",
        checkpoint={"path": "dummy/checkpoint", "fingerprint": "a" * 64, "training_seed": 1, "run_id": "run_dummy"},
        dataset={"fingerprint": "b" * 64, "record_count": len(records), "rubric_schema_version": "real-rubric-v1"},
        generation_config={},
        results=records,
    )
    path = rel.save_generation_artifact(artifact)
    return artifact, path


def _score_all(generation: dict, *, all_pass: bool = True) -> list[dict]:
    scores = []
    for gen_record in generation["results"]:
        rubric = _RUBRICS_BY_RECORD_ID[gen_record["record_id"]]
        capability_checks = {k: all_pass for k in rubric["capability_checks"]}
        scores.append(
            lin.build_review_score_record(
                generation_record=gen_record,
                rubric=rubric,
                scores={dim: all_pass for dim in rsc.SEMANTIC_DIMENSIONS},
                capability_checks=capability_checks,
                failure_labels=[] if all_pass else ["unsupported_action"],
            )
        )
    return scores


def _build_review(generation, generation_path, role, actor_id, *, all_pass=True) -> tuple[dict, Path]:
    review = lin.build_review_artifact(
        generation_path=generation_path,
        reviewer_role=role,
        reviewer_actor_id=actor_id,
        independent_review_attestation=True,
        scores=_score_all(generation, all_pass=all_pass),
    )
    path = lin.save_review_artifact(review, split=generation["split"], milestone=generation.get("release_milestone"))
    return review, path


def _build_comparison(chatgpt_path, claude_path, generation) -> tuple[dict, Path]:
    comparison = lin.build_comparison_artifact(chatgpt_review_path=chatgpt_path, claude_review_path=claude_path)
    path = lin.save_comparison_artifact(comparison, split=generation["split"], milestone=generation.get("release_milestone"))
    return comparison, path


def _build_adjudication(comparison_path, chatgpt_path, claude_path, generation, **kwargs) -> tuple[dict, Path]:
    adjudication = lin.build_adjudication_artifact(comparison_path=comparison_path, chatgpt_review_path=chatgpt_path, claude_review_path=claude_path, **kwargs)
    path = lin.save_adjudication_artifact(adjudication, split=generation["split"], milestone=generation.get("release_milestone"))
    return adjudication, path


# --- Group 1: generation artifact has no semantic-score placeholders ---


def test_generation_has_no_score_placeholders():
    """Group 1 (also exercised in test_real_data_eval_logging.py, repeated
    here as a lineage-module precondition check)."""
    generation, _ = _dummy_generation()
    for r in generation["results"]:
        check("generation record has no scores/strict_pass/review_status field", all(k not in r for k in ("scores", "strict_pass", "review_status", "capability_checks")))


# --- Group 2: overwrite, malformed IDs, unknown fields, duplicate keys, fingerprint mismatch ---


def test_artifact_integrity_contract():
    """Group 2."""
    tmp_dir = Path(tempfile.mkdtemp())
    original_status_dir = lin.STATUS_EVENTS_DIR
    lin.STATUS_EVENTS_DIR = tmp_dir / "status_events"
    try:
        generation, gen_path = _dummy_generation()
        review, _ = _build_review(generation, gen_path, "chatgpt", ACTOR_CHATGPT)

        event = lin.build_status_event(target_artifact=review, target_id_field="review_id", new_status="superseded", reason_code="correction", actor_id=ACTOR_CHATGPT)
        path = lin.save_status_event(event)
        raised = False
        try:
            lin.save_status_event(event)
        except lin.LineageArtifactExistsError:
            raised = True
        check("save_status_event: refuses to overwrite an existing status event", raised)

        tampered = {**event, "reason_code": "tampered"}
        tampered_path = tmp_dir / "tampered_event.json"
        tampered_path.write_text(json.dumps(tampered), encoding="utf-8")
        err = _expect_error(lin.LineageValidationError, lin._load_artifact_verified, tampered_path, expected_schema_version=lin.STATUS_EVENT_SCHEMA_VERSION, expected_kind="status_event")
        check("_load_artifact_verified: detects a tampered artifact_fingerprint", err is not None, err)

        wrong_kind_path = tmp_dir / "wrong_kind.json"
        wrong_kind = {**event, "artifact_kind": "not_a_status_event"}
        wrong_kind["artifact_fingerprint"] = f"sha256:{rdp.artifact_fingerprint(wrong_kind)}"
        wrong_kind_path.write_text(json.dumps(wrong_kind), encoding="utf-8")
        err = _expect_error(lin.LineageValidationError, lin._load_artifact_verified, wrong_kind_path, expected_schema_version=lin.STATUS_EVENT_SCHEMA_VERSION, expected_kind="status_event")
        check("_load_artifact_verified: rejects wrong artifact_kind", err is not None, err)

        err = _expect_error(lin.LineageValidationError, lin.build_status_event, target_artifact=review, target_id_field="review_id", new_status="not_a_real_status", reason_code="x", actor_id=ACTOR_CHATGPT)
        check("build_status_event: malformed new_status rejected", err is not None, err)

        err = _expect_error(lin.LineageValidationError, lin.build_status_event, target_artifact=review, target_id_field="review_id", new_status="superseded", reason_code="x", actor_id="not_an_actor_id")
        check("build_status_event: malformed actor_id rejected", err is not None, err)

        unknown_field_event = {**event, "status_event_id": lin.new_status_event_id()}
        unknown_field_event["target_artifact"] = {**unknown_field_event["target_artifact"], "sneaky_extra_field": "smuggled"}
        unknown_field_event["artifact_fingerprint"] = f"sha256:{rdp.artifact_fingerprint(unknown_field_event)}"
        unknown_nested_path = tmp_dir / "unknown_nested_field.json"
        unknown_nested_path.write_text(json.dumps(unknown_field_event), encoding="utf-8")
        err = _expect_error(lin.LineageValidationError, lin._load_artifact_verified, unknown_nested_path, expected_schema_version=lin.STATUS_EVENT_SCHEMA_VERSION, expected_kind="status_event")
        check("_load_artifact_verified: rejects an unknown field smuggled inside a nested target_artifact reference", err is not None, err)

        bad_timestamp_event = {**event, "status_event_id": lin.new_status_event_id(), "created_at_utc": "not-a-timestamp"}
        bad_timestamp_event["artifact_fingerprint"] = f"sha256:{rdp.artifact_fingerprint(bad_timestamp_event)}"
        bad_timestamp_path = tmp_dir / "bad_timestamp.json"
        bad_timestamp_path.write_text(json.dumps(bad_timestamp_event), encoding="utf-8")
        err = _expect_error(lin.LineageValidationError, lin._load_artifact_verified, bad_timestamp_path, expected_schema_version=lin.STATUS_EVENT_SCHEMA_VERSION, expected_kind="status_event")
        check("_load_artifact_verified: rejects a malformed created_at_utc timestamp", err is not None, err)
    finally:
        lin.STATUS_EVENTS_DIR = original_status_dir
        shutil.rmtree(tmp_dir, ignore_errors=True)


# --- Group 3/4: review record set and fingerprints must match generation ---


def test_review_must_match_generation_record_set_and_fingerprints():
    """Groups 3, 4."""
    generation, gen_path = _dummy_generation()
    scores = _score_all(generation)

    missing_one = scores[:1]
    err = _expect_error(lin.LineageValidationError, lin.build_review_artifact, generation_path=gen_path, reviewer_role="chatgpt", reviewer_actor_id=ACTOR_CHATGPT, independent_review_attestation=True, scores=missing_one)
    check("build_review_artifact: fewer scores than generation records rejected", err is not None, err)

    tampered_fp_scores = [{**scores[0], "generation_raw_output_fingerprint": "sha256:" + "9" * 64}, scores[1]]
    review = lin.build_review_artifact(generation_path=gen_path, reviewer_role="chatgpt", reviewer_actor_id=ACTOR_CHATGPT, independent_review_attestation=True, scores=tampered_fp_scores)
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        review_path = tmp_dir / "review.json"
        review_path.write_text(json.dumps(review), encoding="utf-8")
        err = _expect_error(lin.LineageValidationError, lin.load_review_verified, review_path, generation)
        check("load_review_verified: rejects a review whose raw_output_fingerprint doesn't match generation", err is not None, err)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# --- Group 5: non-boolean, null, partial, missing, or extra scores fail ---


def test_score_record_rejects_bad_scores():
    """Group 5."""
    generation, _ = _dummy_generation(rubrics=[RUBRIC_B])
    gen_record = generation["results"][0]
    rubric = RUBRIC_B  # no required capability checks, simpler case

    partial = {dim: True for dim in rsc.SEMANTIC_DIMENSIONS}
    del partial[rsc.SEMANTIC_DIMENSIONS[0]]
    # A dimension omitted from the caller's input merges onto the base
    # record's pre-filled None (not a missing key), so this surfaces as
    # "incomplete review" (LineageValidationError), not the lower-level
    # rsc.ScoringStateError (which only fires for a truly missing key).
    err = _expect_error(lin.LineageValidationError, lin.build_review_score_record, generation_record=gen_record, rubric=rubric, scores=partial, capability_checks={}, failure_labels=[])
    check("build_review_score_record: missing a semantic dimension raises", err is not None, err)

    non_bool = {dim: "true" for dim in rsc.SEMANTIC_DIMENSIONS}
    err = _expect_error(rsc.ScoringStateError, lin.build_review_score_record, generation_record=gen_record, rubric=rubric, scores=non_bool, capability_checks={}, failure_labels=[])
    check("build_review_score_record: non-boolean score value raises", err is not None, err)

    null_score = {dim: None for dim in rsc.SEMANTIC_DIMENSIONS}
    err = _expect_error(lin.LineageValidationError, lin.build_review_score_record, generation_record=gen_record, rubric=rubric, scores=null_score, capability_checks={}, failure_labels=[])
    check("build_review_score_record: null scores fail as an incomplete review", err is not None, err)


# --- Group 6: capability-check keys must exactly equal the rubric contract ---


def test_capability_check_keys_must_match_rubric():
    """Group 6."""
    generation, _ = _dummy_generation(rubrics=[RUBRIC_A])
    gen_record = generation["results"][0]
    good_scores = {dim: True for dim in rsc.SEMANTIC_DIMENSIONS}

    missing_check = {}
    err = _expect_error(lin.LineageValidationError, lin.build_review_score_record, generation_record=gen_record, rubric=RUBRIC_A, scores=good_scores, capability_checks=missing_check, failure_labels=[])
    check("build_review_score_record: missing a required capability check rejected", err is not None, err)

    extra_check = {"explicit_task_survived": True, "not_in_rubric": True}
    err = _expect_error(lin.LineageValidationError, lin.build_review_score_record, generation_record=gen_record, rubric=RUBRIC_A, scores=good_scores, capability_checks=extra_check, failure_labels=[])
    check("build_review_score_record: extra capability check not in rubric rejected", err is not None, err)

    exact = {"explicit_task_survived": True}
    record = lin.build_review_score_record(generation_record=gen_record, rubric=RUBRIC_A, scores=good_scores, capability_checks=exact, failure_labels=[])
    check("build_review_score_record: exact capability check set accepted", record["capability_checks"] == exact)


# --- Group 7: unknown or duplicate failure labels fail ---


def test_failure_labels_validated():
    """Group 7."""
    generation, _ = _dummy_generation(rubrics=[RUBRIC_B])
    gen_record = generation["results"][0]
    scores = {dim: False for dim in rsc.SEMANTIC_DIMENSIONS}

    err = _expect_error(lin.LineageValidationError, lin.build_review_score_record, generation_record=gen_record, rubric=RUBRIC_B, scores=scores, capability_checks={}, failure_labels=["not_a_real_label"])
    check("build_review_score_record: unknown failure label rejected", err is not None, err)

    err = _expect_error(lin.LineageValidationError, lin.build_review_score_record, generation_record=gen_record, rubric=RUBRIC_B, scores=scores, capability_checks={}, failure_labels=["unsupported_action", "unsupported_action"])
    check("build_review_score_record: duplicate failure label rejected", err is not None, err)

    record = lin.build_review_score_record(generation_record=gen_record, rubric=RUBRIC_B, scores=scores, capability_checks={}, failure_labels=["unsupported_action"])
    check("build_review_score_record: known failure label accepted", record["failure_labels"] == ["unsupported_action"])


# --- Group 6/2nd review finding 2: rubric identity/fingerprint binding ---


def test_rubric_must_match_bound_fingerprint_and_schema():
    """Phase E lineage/withdrawal second review, finding 2: a submitted
    rubric must be the exact rubric bound to this record at generation
    time (fingerprint-checked), and must pass the full documented rubric
    schema -- not just have a capability_checks key."""
    generation, _ = _dummy_generation(rubrics=[RUBRIC_A])
    gen_record = generation["results"][0]
    good_scores = {dim: True for dim in rsc.SEMANTIC_DIMENSIONS}

    unrelated_rubric = _full_rubric(RV_A, capability_checks=[])  # same record_id, different content -> different fingerprint
    err = _expect_error(lin.LineageValidationError, lin.build_review_score_record, generation_record=gen_record, rubric=unrelated_rubric, scores=good_scores, capability_checks={}, failure_labels=[])
    check("build_review_score_record: a rubric with the right record_id but wrong content (fingerprint mismatch) is rejected", err is not None, err)

    partial_rubric = {"record_id": RV_A, "must_preserve": ["x"], "capability_checks": ["explicit_task_survived"]}
    err = _expect_error(lin.LineageValidationError, lin.build_review_score_record, generation_record=gen_record, rubric=partial_rubric, scores=good_scores, capability_checks={"explicit_task_survived": True}, failure_labels=[])
    check("build_review_score_record: a partial ad hoc rubric shape missing the documented fields is rejected", err is not None, err)

    record = lin.build_review_score_record(generation_record=gen_record, rubric=RUBRIC_A, scores=good_scores, capability_checks={"explicit_task_survived": True}, failure_labels=[])
    check("build_review_score_record: the exact bound rubric is accepted", record["strict_pass"] is True)


# --- Group 8: reviewer roles/actor IDs must be distinct ---


def test_reviewer_roles_and_actors_distinct():
    """Group 8."""
    generation, gen_path = _dummy_generation()
    _, chatgpt_path = _build_review(generation, gen_path, "chatgpt", ACTOR_CHATGPT)
    _, same_actor_path = _build_review(generation, gen_path, "claude", ACTOR_CHATGPT)  # same actor as chatgpt -- invalid
    err = _expect_error(lin.LineageValidationError, lin.build_comparison_artifact, chatgpt_review_path=chatgpt_path, claude_review_path=same_actor_path)
    check("build_comparison_artifact: identical reviewer_actor_id across roles rejected", err is not None, err)

    _, wrong_role_path = _build_review(generation, gen_path, "chatgpt", ACTOR_CLAUDE)
    err = _expect_error(lin.LineageValidationError, lin.build_comparison_artifact, chatgpt_review_path=chatgpt_path, claude_review_path=wrong_role_path)
    check("build_comparison_artifact: claude_review with reviewer_role='chatgpt' rejected", err is not None, err)


# --- Group 9: comparison of different generations fails ---


def test_comparison_requires_same_generation():
    """Group 9."""
    generation1, gen_path1 = _dummy_generation()
    generation2, gen_path2 = _dummy_generation()  # different evaluation_id
    _, chatgpt_path = _build_review(generation1, gen_path1, "chatgpt", ACTOR_CHATGPT)
    _, claude_path = _build_review(generation2, gen_path2, "claude", ACTOR_CLAUDE)
    err = _expect_error(lin.LineageValidationError, lin.build_comparison_artifact, chatgpt_review_path=chatgpt_path, claude_review_path=claude_path)
    check("build_comparison_artifact: reviews of different generations rejected", err is not None, err)


# --- Group 10: any disagreement produces 'disagreement' ---


def test_comparison_alignment_status():
    """Group 10."""
    generation, gen_path = _dummy_generation()
    _, chatgpt_path = _build_review(generation, gen_path, "chatgpt", ACTOR_CHATGPT, all_pass=True)
    _, claude_aligned_path = _build_review(generation, gen_path, "claude", ACTOR_CLAUDE, all_pass=True)
    aligned_comparison, _ = _build_comparison(chatgpt_path, claude_aligned_path, generation)
    check("build_comparison_artifact: identical scores -> alignment_status='aligned'", aligned_comparison["alignment_status"] == "aligned")

    _, claude_disagree_path = _build_review(generation, gen_path, "claude", ACTOR_CLAUDE, all_pass=False)
    disagree_comparison, _ = _build_comparison(chatgpt_path, claude_disagree_path, generation)
    check("build_comparison_artifact: differing scores -> alignment_status='disagreement'", disagree_comparison["alignment_status"] == "disagreement")
    check("build_comparison_artifact: per-record disagreements recorded", any(rc["score_disagreements"] for rc in disagree_comparison["record_comparisons"]))


# --- Group 11: reviewer_agreement requires an aligned comparison ---


def test_reviewer_agreement_requires_alignment():
    """Group 11."""
    generation, gen_path = _dummy_generation()
    chatgpt_review, chatgpt_path = _build_review(generation, gen_path, "chatgpt", ACTOR_CHATGPT, all_pass=True)
    claude_review, claude_path = _build_review(generation, gen_path, "claude", ACTOR_CLAUDE, all_pass=False)
    disagree_comparison, disagree_path = _build_comparison(chatgpt_path, claude_path, generation)
    err = _expect_error(lin.LineageValidationError, lin.build_adjudication_artifact, comparison_path=disagree_path, chatgpt_review_path=chatgpt_path, claude_review_path=claude_path, resolution_mode="reviewer_agreement")
    check("build_adjudication_artifact: reviewer_agreement on a disagreement rejected", err is not None, err)

    _, claude_aligned_path = _build_review(generation, gen_path, "claude", ACTOR_CLAUDE, all_pass=True)
    aligned_comparison, aligned_path = _build_comparison(chatgpt_path, claude_aligned_path, generation)
    adjudication, _ = _build_adjudication(aligned_path, chatgpt_path, claude_aligned_path, generation, resolution_mode="reviewer_agreement")
    check("build_adjudication_artifact: reviewer_agreement on an aligned comparison succeeds", adjudication["resolution_mode"] == "reviewer_agreement")


# --- Group 12: product-owner adjudication required for a disagreement ---


def test_product_owner_resolution_required_for_disagreement():
    """Group 12."""
    generation, gen_path = _dummy_generation()
    chatgpt_review, chatgpt_path = _build_review(generation, gen_path, "chatgpt", ACTOR_CHATGPT, all_pass=True)
    claude_review_aligned, claude_aligned_path = _build_review(generation, gen_path, "claude", ACTOR_CLAUDE, all_pass=True)
    aligned_comparison, aligned_path = _build_comparison(chatgpt_path, claude_aligned_path, generation)
    err = _expect_error(
        lin.LineageValidationError,
        lin.build_adjudication_artifact,
        comparison_path=aligned_path,
        chatgpt_review_path=chatgpt_path,
        claude_review_path=claude_aligned_path,
        resolution_mode="product_owner_resolution",
        resolved_by_actor_id=ACTOR_OWNER,
        final_scores=chatgpt_review["scores"],
    )
    check("build_adjudication_artifact: product_owner_resolution on an aligned comparison rejected", err is not None, err)

    claude_review_disagree, claude_disagree_path = _build_review(generation, gen_path, "claude", ACTOR_CLAUDE, all_pass=False)
    disagree_comparison, disagree_path = _build_comparison(chatgpt_path, claude_disagree_path, generation)
    err = _expect_error(
        lin.LineageValidationError,
        lin.build_adjudication_artifact,
        comparison_path=disagree_path,
        chatgpt_review_path=chatgpt_path,
        claude_review_path=claude_disagree_path,
        resolution_mode="product_owner_resolution",
    )
    check("build_adjudication_artifact: product_owner_resolution without resolved_by_actor_id/final_scores rejected", err is not None, err)

    adjudication, _ = _build_adjudication(
        disagree_path,
        chatgpt_path,
        claude_disagree_path,
        generation,
        resolution_mode="product_owner_resolution",
        resolved_by_actor_id=ACTOR_OWNER,
        final_scores=chatgpt_review["scores"],
        rubrics={RV_A: RUBRIC_A, RV_B: RUBRIC_B},
    )
    check("build_adjudication_artifact: product_owner_resolution with proper arguments succeeds", adjudication["resolved_by_actor_id"] == ACTOR_OWNER)

    err = _expect_error(
        lin.LineageValidationError,
        lin.build_adjudication_artifact,
        comparison_path=disagree_path,
        chatgpt_review_path=chatgpt_path,
        claude_review_path=claude_disagree_path,
        resolution_mode="product_owner_resolution",
        resolved_by_actor_id=ACTOR_OWNER,
        final_scores=chatgpt_review["scores"],
    )
    check("build_adjudication_artifact: product_owner_resolution without rubrics rejected", err is not None, err)

    tampered_final_scores = [{**s, "generation_raw_output_fingerprint": "sha256:" + "9" * 64} for s in chatgpt_review["scores"]]
    err = _expect_error(
        lin.LineageValidationError,
        lin.build_adjudication_artifact,
        comparison_path=disagree_path,
        chatgpt_review_path=chatgpt_path,
        claude_review_path=claude_disagree_path,
        resolution_mode="product_owner_resolution",
        resolved_by_actor_id=ACTOR_OWNER,
        final_scores=tampered_final_scores,
        rubrics={RV_A: RUBRIC_A, RV_B: RUBRIC_B},
    )
    check("build_adjudication_artifact: product_owner_resolution cannot change generation_raw_output_fingerprint", err is not None, err)

    duplicate_final_scores = chatgpt_review["scores"] + [chatgpt_review["scores"][0]]
    err = _expect_error(
        lin.LineageValidationError,
        lin.build_adjudication_artifact,
        comparison_path=disagree_path,
        chatgpt_review_path=chatgpt_path,
        claude_review_path=claude_disagree_path,
        resolution_mode="product_owner_resolution",
        resolved_by_actor_id=ACTOR_OWNER,
        final_scores=duplicate_final_scores,
        rubrics={RV_A: RUBRIC_A, RV_B: RUBRIC_B},
    )
    check("build_adjudication_artifact: duplicate record_id in final_scores rejected", err is not None, err)


# --- Group 13: strict passes are recomputed, not trusted ---


def test_adjudication_recomputes_strict_pass():
    """Group 13."""
    generation, gen_path = _dummy_generation()
    chatgpt_review, chatgpt_path = _build_review(generation, gen_path, "chatgpt", ACTOR_CHATGPT, all_pass=True)
    claude_review, claude_path = _build_review(generation, gen_path, "claude", ACTOR_CLAUDE, all_pass=True)
    comparison, comparison_path = _build_comparison(chatgpt_path, claude_path, generation)

    # A caller claiming strict_pass=False despite every dimension/check
    # passing must not be trusted -- it's recomputed from the real values.
    adjudication, _ = _build_adjudication(comparison_path, chatgpt_path, claude_path, generation, resolution_mode="reviewer_agreement")
    check("build_adjudication_artifact: recomputes strict_pass from actual scores (all-pass -> True)", all(r["strict_pass"] is True for r in adjudication["results"]))
    check("build_adjudication_artifact: aggregate_strict_pass matches recomputed results", adjudication["aggregate_strict_pass"] == f"{len(adjudication['results'])}/{len(adjudication['results'])}")


# --- Group 14: superseded/invalidated parents cannot create new descendants ---


def test_status_resolution_and_superseded_parent_blocking():
    """Group 14. Also covers the Phase E lineage/withdrawal second review's
    finding 1: comparison/adjudication/decision now load and verify their
    parents from real stored paths, so this exercises the real,
    persisted-artifact path (not an in-memory dict standing in for one)."""
    tmp_dir = Path(tempfile.mkdtemp())
    original_status_dir = lin.STATUS_EVENTS_DIR
    lin.STATUS_EVENTS_DIR = tmp_dir / "status_events"
    try:
        generation, gen_path = _dummy_generation()
        chatgpt_review, chatgpt_path = _build_review(generation, gen_path, "chatgpt", ACTOR_CHATGPT)
        claude_review, claude_path = _build_review(generation, gen_path, "claude", ACTOR_CLAUDE)
        review_ref = lin._artifact_ref(chatgpt_review, "review_id")
        check("resolve_active_status: a fresh artifact with no status events is 'active'", lin.resolve_active_status(review_ref) == "active")

        event = lin.build_status_event(target_artifact=chatgpt_review, target_id_field="review_id", new_status="superseded", reason_code="correction", actor_id=ACTOR_CHATGPT)
        lin.save_status_event(event)
        check("resolve_active_status: reflects a superseded status event", lin.resolve_active_status(review_ref) == "superseded")

        err = _expect_error(lin.ParentNotActiveError, lin.build_comparison_artifact, chatgpt_review_path=chatgpt_path, claude_review_path=claude_path)
        check("build_comparison_artifact: refuses to build from a superseded review parent", err is not None, err)

        invalidate_event = lin.build_status_event(target_artifact=chatgpt_review, target_id_field="review_id", new_status="invalidated", reason_code="withdrawal", actor_id=ACTOR_CHATGPT)
        lin.save_status_event(invalidate_event)
        check("resolve_active_status: invalidated beats superseded when both exist", lin.resolve_active_status(review_ref) == "invalidated")

        err = _expect_error(lin.ParentNotActiveError, lin.build_comparison_artifact, chatgpt_review_path=chatgpt_path, claude_review_path=claude_path)
        check("build_comparison_artifact: refuses to build from an invalidated review parent", err is not None, err)

        # A comparison/adjudication built while both reviews were still
        # active, then invalidated afterward, must also block a *later*
        # adjudication/decision -- not just block re-deriving from the
        # review directly.
        _, aligned_chatgpt_path = _build_review(generation, gen_path, "chatgpt", ACTOR_CHATGPT, all_pass=True)
        _, aligned_claude_path = _build_review(generation, gen_path, "claude", ACTOR_CLAUDE, all_pass=True)
        comparison, comparison_path = _build_comparison(aligned_chatgpt_path, aligned_claude_path, generation)
        comparison_event = lin.build_status_event(target_artifact=comparison, target_id_field="comparison_id", new_status="invalidated", reason_code="withdrawal", actor_id=ACTOR_CHATGPT)
        lin.save_status_event(comparison_event)
        err = _expect_error(lin.ParentNotActiveError, lin.build_adjudication_artifact, comparison_path=comparison_path, chatgpt_review_path=aligned_chatgpt_path, claude_review_path=aligned_claude_path, resolution_mode="reviewer_agreement")
        check("build_adjudication_artifact: refuses to build from an invalidated comparison parent", err is not None, err)

        # And an invalidated adjudication must block a decision citing it.
        _, fresh_chatgpt_path = _build_review(generation, gen_path, "chatgpt", ACTOR_CHATGPT, all_pass=True)
        _, fresh_claude_path = _build_review(generation, gen_path, "claude", ACTOR_CLAUDE, all_pass=True)
        fresh_comparison, fresh_comparison_path = _build_comparison(fresh_chatgpt_path, fresh_claude_path, generation)
        fresh_adjudication, fresh_adjudication_path = _build_adjudication(fresh_comparison_path, fresh_chatgpt_path, fresh_claude_path, generation, resolution_mode="reviewer_agreement")
        adjudication_event = lin.build_status_event(target_artifact=fresh_adjudication, target_id_field="adjudication_id", new_status="invalidated", reason_code="withdrawal", actor_id=ACTOR_CHATGPT)
        lin.save_status_event(adjudication_event)
        err = _expect_error(lin.ParentNotActiveError, lin.build_decision_record, decision_type="curriculum", deciding_actor_id=ACTOR_OWNER, adjudication_paths=[fresh_adjudication_path], outcome="should be blocked")
        check("build_decision_record: refuses to cite an invalidated adjudication", err is not None, err)
    finally:
        lin.STATUS_EVENTS_DIR = original_status_dir
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_never_saved_parent_rejected():
    """Phase E lineage/withdrawal second review, finding 1: a parent that
    was never saved anywhere must be rejected outright -- not treated as
    'active' by default just because no status event mentions it.
    Reproduces the review's missing_parent_reviews_accepted /
    review_from_invalidated_generation_accepted live findings."""
    generation, gen_path = _dummy_generation()
    unsaved_generation_path = gen_path.parent / "eval_never_saved0000000000000000.json"
    err = _expect_error(rel.GenerationValidationError, lin.build_review_artifact, generation_path=unsaved_generation_path, reviewer_role="chatgpt", reviewer_actor_id=ACTOR_CHATGPT, independent_review_attestation=True, scores=_score_all(generation))
    check("build_review_artifact: a generation path that was never actually saved is rejected, not defaulted to active", err is not None, err)

    _, chatgpt_path = _build_review(generation, gen_path, "chatgpt", ACTOR_CHATGPT)
    unsaved_review_path = chatgpt_path.parent / "review_never_saved00000000000000.json"
    err = _expect_error(lin.LineageValidationError, lin.build_comparison_artifact, chatgpt_review_path=chatgpt_path, claude_review_path=unsaved_review_path)
    check("build_comparison_artifact: a review path that was never actually saved is rejected", err is not None, err)


# --- Group 15: a decision cannot cite anything except active adjudication artifacts ---


def test_decision_requires_adjudications():
    """Group 15."""
    err = _expect_error(lin.LineageValidationError, lin.build_decision_record, decision_type="curriculum", deciding_actor_id=ACTOR_OWNER, adjudication_paths=[], outcome="no adjudications, should fail")
    check("build_decision_record: requires at least one adjudication reference", err is not None, err)

    generation, gen_path = _dummy_generation()
    _, chatgpt_path = _build_review(generation, gen_path, "chatgpt", ACTOR_CHATGPT)
    _, claude_path = _build_review(generation, gen_path, "claude", ACTOR_CLAUDE)
    comparison, comparison_path = _build_comparison(chatgpt_path, claude_path, generation)
    adjudication, adjudication_path = _build_adjudication(comparison_path, chatgpt_path, claude_path, generation, resolution_mode="reviewer_agreement")
    decision = lin.build_decision_record(decision_type="curriculum", deciding_actor_id=ACTOR_OWNER, adjudication_paths=[adjudication_path], outcome="dummy decision for testing")
    check("build_decision_record: valid adjudication reference accepted", decision["adjudications"][0]["artifact_id"] == adjudication["adjudication_id"])

    err = _expect_error(lin.LineageValidationError, lin.build_decision_record, decision_type="not_a_real_type", deciding_actor_id=ACTOR_OWNER, adjudication_paths=[adjudication_path], outcome="x")
    check("build_decision_record: invalid decision_type rejected", err is not None, err)

    err = _expect_error(lin.LineageValidationError, lin.build_decision_record, decision_type="curriculum", deciding_actor_id=ACTOR_OWNER, adjudication_paths=[adjudication_path, adjudication_path], outcome="duplicate ref")
    check("build_decision_record: duplicate adjudication reference rejected", err is not None, err)


def test_dataset_snapshot_basic():
    """Not one of the 15 lineage groups directly, but required
    infrastructure for withdrawal (built and sanity-checked here since
    real_data_lineage.py owns it)."""
    empty_snapshot = lin.build_dataset_snapshot(split="real_validation", creation_reason="dummy empty snapshot", active_records=[], rubric_schema_version="real-rubric-v1")
    check("build_dataset_snapshot: empty split still gets a deterministic dataset_fingerprint", empty_snapshot["dataset_fingerprint"].startswith("sha256:"))

    non_empty = lin.build_dataset_snapshot(
        split="real_validation",
        creation_reason="dummy non-empty snapshot",
        active_records=[{"record_id": RV_A, "source_fingerprint": "sha256:" + "1" * 64, "pair_fingerprint": "sha256:" + "2" * 64, "rubric_fingerprint": "sha256:" + "3" * 64}],
        rubric_schema_version="real-rubric-v1",
    )
    check("build_dataset_snapshot: non-empty snapshot differs from empty snapshot", non_empty["dataset_fingerprint"] != empty_snapshot["dataset_fingerprint"])

    duplicate_record = {"record_id": RV_A, "source_fingerprint": "sha256:" + "1" * 64, "pair_fingerprint": "sha256:" + "2" * 64, "rubric_fingerprint": "sha256:" + "3" * 64}
    err = _expect_error(lin.LineageValidationError, lin.build_dataset_snapshot, split="real_validation", creation_reason="dummy", active_records=[duplicate_record, duplicate_record], rubric_schema_version="real-rubric-v1")
    check("build_dataset_snapshot: duplicate record_id in active_records rejected", err is not None, err)


def test_duplicate_generation_results_rejected():
    """Phase E lineage/withdrawal second review, finding 4: duplicate
    record_ids in a generation's results must be rejected before any
    set/dict construction, matching every other collection in the
    lineage/generation schema."""
    rec = rel.new_generation_record(record_id=RV_A, source_fingerprint="1" * 64, pair_fingerprint="2" * 64, rubric_fingerprint=rdp.rubric_fingerprint(RUBRIC_A), raw_output="x", format_valid=True)
    err = _expect_error(
        rel.GenerationValidationError,
        rel.build_generation_artifact,
        split="real_validation",
        evaluation_reason="dup test",
        git_commit="deadbeef",
        checkpoint={"path": "dummy", "fingerprint": "a" * 64, "training_seed": 1, "run_id": "run"},
        dataset={"fingerprint": "b" * 64, "record_count": 2, "rubric_schema_version": "real-rubric-v1"},
        generation_config={},
        results=[rec, rec],
    )
    check("build_generation_artifact: duplicate record_id in results rejected", err is not None, err)


def main() -> None:
    tests = [
        test_generation_has_no_score_placeholders,
        test_artifact_integrity_contract,
        test_review_must_match_generation_record_set_and_fingerprints,
        test_score_record_rejects_bad_scores,
        test_capability_check_keys_must_match_rubric,
        test_failure_labels_validated,
        test_rubric_must_match_bound_fingerprint_and_schema,
        test_reviewer_roles_and_actors_distinct,
        test_comparison_requires_same_generation,
        test_comparison_alignment_status,
        test_reviewer_agreement_requires_alignment,
        test_product_owner_resolution_required_for_disagreement,
        test_adjudication_recomputes_strict_pass,
        test_status_resolution_and_superseded_parent_blocking,
        test_never_saved_parent_rejected,
        test_decision_requires_adjudications,
        test_dataset_snapshot_basic,
        test_duplicate_generation_results_rejected,
    ]
    with Sandbox():
        for t in tests:
            t()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("All real_data_lineage.py tests passed.")


if __name__ == "__main__":
    main()
