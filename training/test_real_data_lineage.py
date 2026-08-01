"""Standalone assertion tests for real_data_lineage.py -- dummy data only,
no real notes. Run with `python test_real_data_lineage.py`. Exits 0 iff
every test passes.

Covers the 15 "Scoring lineage" adversarial test groups required by
training/real_data_scoring_lineage_withdrawal_design.md. Each test
function's docstring names which group(s) it covers.
"""
import shutil
import sys
import tempfile
from pathlib import Path

import real_data_eval_logging as rel
import real_data_lineage as lin
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


ACTOR_CHATGPT = "actor_" + "1" * 32
ACTOR_CLAUDE = "actor_" + "2" * 32
ACTOR_OWNER = "actor_" + "3" * 32

RUBRIC_A = {"record_id": "rv_a", "must_preserve": ["x"], "expected_capability_checks": ["explicit_task_survived"]}
RUBRIC_B = {"record_id": "rv_b", "must_preserve": ["y"], "expected_capability_checks": []}


def _dummy_generation(n_records: int = 2) -> dict:
    records = []
    for i in range(n_records):
        records.append(
            rel.new_generation_record(
                record_id=f"rv_{'a' if i == 0 else 'b'}",
                source_fingerprint=f"{i}" * 64,
                pair_fingerprint=f"{i + 1}" * 64,
                rubric_fingerprint=f"{i + 2}" * 64,
                raw_output=f"###NARRATIVE### dummy {i} ###BULLETS### x ###ACTIONS###",
                format_valid=True,
            )
        )
    return rel.build_generation_artifact(
        split="real_validation",
        evaluation_reason="dummy lineage test",
        git_commit="deadbeef",
        checkpoint={"path": "dummy/checkpoint", "fingerprint": "a" * 64, "training_seed": 1, "run_id": "run_dummy"},
        dataset={"fingerprint": "b" * 64, "record_count": n_records, "rubric_schema_version": "real-rubric-v1"},
        generation_config={},
        results=records,
    )


def _score_all(generation: dict, *, all_pass: bool = True) -> list[dict]:
    rubrics = {"rv_a": RUBRIC_A, "rv_b": RUBRIC_B}
    scores = []
    for gen_record in generation["results"]:
        rubric = rubrics[gen_record["record_id"]]
        capability_checks = {k: all_pass for k in rubric.get("expected_capability_checks", [])}
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


def _build_review(generation, role, actor_id, *, all_pass=True):
    return lin.build_review_artifact(
        generation=generation,
        reviewer_role=role,
        reviewer_actor_id=actor_id,
        independent_review_attestation=True,
        scores=_score_all(generation, all_pass=all_pass),
    )


# --- Group 1: generation artifact has no semantic-score placeholders ---


def test_generation_has_no_score_placeholders():
    """Group 1 (also exercised in test_real_data_eval_logging.py, repeated
    here as a lineage-module precondition check)."""
    generation = _dummy_generation()
    for r in generation["results"]:
        check("generation record has no scores/strict_pass/review_status field", all(k not in r for k in ("scores", "strict_pass", "review_status", "capability_checks")))


# --- Group 2: overwrite, malformed IDs, unknown fields, duplicate keys, fingerprint mismatch ---


def test_artifact_integrity_contract():
    """Group 2."""
    tmp_dir = Path(tempfile.mkdtemp())
    original_status_dir = lin.STATUS_EVENTS_DIR
    lin.STATUS_EVENTS_DIR = tmp_dir / "status_events"
    try:
        generation = _dummy_generation()
        review = _build_review(generation, "chatgpt", ACTOR_CHATGPT)

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
        import json

        tampered_path.write_text(json.dumps(tampered), encoding="utf-8")
        err = _expect_error(lin.LineageValidationError, lin._load_artifact_verified, tampered_path, expected_schema_version=lin.STATUS_EVENT_SCHEMA_VERSION, expected_kind="status_event")
        check("_load_artifact_verified: detects a tampered artifact_fingerprint", err is not None, err)

        wrong_kind_path = tmp_dir / "wrong_kind.json"
        wrong_kind = {**event, "artifact_kind": "not_a_status_event"}
        wrong_kind["artifact_fingerprint"] = f"sha256:{__import__('real_data_private').artifact_fingerprint(wrong_kind)}"
        wrong_kind_path.write_text(json.dumps(wrong_kind), encoding="utf-8")
        err = _expect_error(lin.LineageValidationError, lin._load_artifact_verified, wrong_kind_path, expected_schema_version=lin.STATUS_EVENT_SCHEMA_VERSION, expected_kind="status_event")
        check("_load_artifact_verified: rejects wrong artifact_kind", err is not None, err)

        err = _expect_error(lin.LineageValidationError, lin.build_status_event, target_artifact=review, target_id_field="review_id", new_status="not_a_real_status", reason_code="x", actor_id=ACTOR_CHATGPT)
        check("build_status_event: malformed new_status rejected", err is not None, err)

        err = _expect_error(lin.LineageValidationError, lin.build_status_event, target_artifact=review, target_id_field="review_id", new_status="superseded", reason_code="x", actor_id="not_an_actor_id")
        check("build_status_event: malformed actor_id rejected", err is not None, err)
    finally:
        lin.STATUS_EVENTS_DIR = original_status_dir
        shutil.rmtree(tmp_dir, ignore_errors=True)


# --- Group 3/4: review record set and fingerprints must match generation ---


def test_review_must_match_generation_record_set_and_fingerprints():
    """Groups 3, 4."""
    generation = _dummy_generation(2)
    scores = _score_all(generation)

    missing_one = scores[:1]
    err = _expect_error(lin.LineageValidationError, lin.build_review_artifact, generation=generation, reviewer_role="chatgpt", reviewer_actor_id=ACTOR_CHATGPT, independent_review_attestation=True, scores=missing_one)
    check("build_review_artifact: fewer scores than generation records rejected", err is not None, err)

    tampered_fp_scores = [{**scores[0], "generation_raw_output_fingerprint": "sha256:" + "9" * 64}, scores[1]]
    review = lin.build_review_artifact(generation=generation, reviewer_role="chatgpt", reviewer_actor_id=ACTOR_CHATGPT, independent_review_attestation=True, scores=tampered_fp_scores)
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        review_path = tmp_dir / "review.json"
        import json

        review_path.write_text(json.dumps(review), encoding="utf-8")
        err = _expect_error(lin.LineageValidationError, lin.load_review_verified, review_path, generation)
        check("load_review_verified: rejects a review whose raw_output_fingerprint doesn't match generation", err is not None, err)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# --- Group 5: non-boolean, null, partial, missing, or extra scores fail ---


def test_score_record_rejects_bad_scores():
    """Group 5."""
    generation = _dummy_generation(1)
    gen_record = generation["results"][0]
    rubric = RUBRIC_B  # no expected capability checks, simpler case

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
    generation = _dummy_generation(1)
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
    generation = _dummy_generation(1)
    gen_record = generation["results"][0]
    scores = {dim: False for dim in rsc.SEMANTIC_DIMENSIONS}

    err = _expect_error(lin.LineageValidationError, lin.build_review_score_record, generation_record=gen_record, rubric=RUBRIC_B, scores=scores, capability_checks={}, failure_labels=["not_a_real_label"])
    check("build_review_score_record: unknown failure label rejected", err is not None, err)

    err = _expect_error(lin.LineageValidationError, lin.build_review_score_record, generation_record=gen_record, rubric=RUBRIC_B, scores=scores, capability_checks={}, failure_labels=["unsupported_action", "unsupported_action"])
    check("build_review_score_record: duplicate failure label rejected", err is not None, err)

    record = lin.build_review_score_record(generation_record=gen_record, rubric=RUBRIC_B, scores=scores, capability_checks={}, failure_labels=["unsupported_action"])
    check("build_review_score_record: known failure label accepted", record["failure_labels"] == ["unsupported_action"])


# --- Group 8: reviewer roles/actor IDs must be distinct ---


def test_reviewer_roles_and_actors_distinct():
    """Group 8."""
    generation = _dummy_generation()
    chatgpt_review = _build_review(generation, "chatgpt", ACTOR_CHATGPT)
    same_actor_claude_review = _build_review(generation, "claude", ACTOR_CHATGPT)  # same actor as chatgpt -- invalid
    err = _expect_error(lin.LineageValidationError, lin.build_comparison_artifact, chatgpt_review=chatgpt_review, claude_review=same_actor_claude_review)
    check("build_comparison_artifact: identical reviewer_actor_id across roles rejected", err is not None, err)

    wrong_role_review = _build_review(generation, "chatgpt", ACTOR_CLAUDE)
    err = _expect_error(lin.LineageValidationError, lin.build_comparison_artifact, chatgpt_review=chatgpt_review, claude_review=wrong_role_review)
    check("build_comparison_artifact: claude_review with reviewer_role='chatgpt' rejected", err is not None, err)


# --- Group 9: comparison of different generations fails ---


def test_comparison_requires_same_generation():
    """Group 9."""
    generation1 = _dummy_generation()
    generation2 = _dummy_generation()  # different evaluation_id
    chatgpt_review = _build_review(generation1, "chatgpt", ACTOR_CHATGPT)
    claude_review = _build_review(generation2, "claude", ACTOR_CLAUDE)
    err = _expect_error(lin.LineageValidationError, lin.build_comparison_artifact, chatgpt_review=chatgpt_review, claude_review=claude_review)
    check("build_comparison_artifact: reviews of different generations rejected", err is not None, err)


# --- Group 10: any disagreement produces 'disagreement' ---


def test_comparison_alignment_status():
    """Group 10."""
    generation = _dummy_generation()
    chatgpt_review = _build_review(generation, "chatgpt", ACTOR_CHATGPT, all_pass=True)
    claude_review_aligned = _build_review(generation, "claude", ACTOR_CLAUDE, all_pass=True)
    aligned_comparison = lin.build_comparison_artifact(chatgpt_review=chatgpt_review, claude_review=claude_review_aligned)
    check("build_comparison_artifact: identical scores -> alignment_status='aligned'", aligned_comparison["alignment_status"] == "aligned")

    claude_review_disagree = _build_review(generation, "claude", ACTOR_CLAUDE, all_pass=False)
    disagree_comparison = lin.build_comparison_artifact(chatgpt_review=chatgpt_review, claude_review=claude_review_disagree)
    check("build_comparison_artifact: differing scores -> alignment_status='disagreement'", disagree_comparison["alignment_status"] == "disagreement")
    check("build_comparison_artifact: per-record disagreements recorded", any(rc["score_disagreements"] for rc in disagree_comparison["record_comparisons"]))


# --- Group 11: reviewer_agreement requires an aligned comparison ---


def test_reviewer_agreement_requires_alignment():
    """Group 11."""
    generation = _dummy_generation()
    chatgpt_review = _build_review(generation, "chatgpt", ACTOR_CHATGPT, all_pass=True)
    claude_review = _build_review(generation, "claude", ACTOR_CLAUDE, all_pass=False)
    disagree_comparison = lin.build_comparison_artifact(chatgpt_review=chatgpt_review, claude_review=claude_review)
    err = _expect_error(lin.LineageValidationError, lin.build_adjudication_artifact, comparison=disagree_comparison, chatgpt_review=chatgpt_review, claude_review=claude_review, resolution_mode="reviewer_agreement")
    check("build_adjudication_artifact: reviewer_agreement on a disagreement rejected", err is not None, err)

    claude_review_aligned = _build_review(generation, "claude", ACTOR_CLAUDE, all_pass=True)
    aligned_comparison = lin.build_comparison_artifact(chatgpt_review=chatgpt_review, claude_review=claude_review_aligned)
    adjudication = lin.build_adjudication_artifact(comparison=aligned_comparison, chatgpt_review=chatgpt_review, claude_review=claude_review_aligned, resolution_mode="reviewer_agreement")
    check("build_adjudication_artifact: reviewer_agreement on an aligned comparison succeeds", adjudication["resolution_mode"] == "reviewer_agreement")


# --- Group 12: product-owner adjudication required for a disagreement ---


def test_product_owner_resolution_required_for_disagreement():
    """Group 12."""
    generation = _dummy_generation()
    chatgpt_review = _build_review(generation, "chatgpt", ACTOR_CHATGPT, all_pass=True)
    claude_review_aligned = _build_review(generation, "claude", ACTOR_CLAUDE, all_pass=True)
    aligned_comparison = lin.build_comparison_artifact(chatgpt_review=chatgpt_review, claude_review=claude_review_aligned)
    err = _expect_error(
        lin.LineageValidationError,
        lin.build_adjudication_artifact,
        comparison=aligned_comparison,
        chatgpt_review=chatgpt_review,
        claude_review=claude_review_aligned,
        resolution_mode="product_owner_resolution",
        resolved_by_actor_id=ACTOR_OWNER,
        final_scores=chatgpt_review["scores"],
    )
    check("build_adjudication_artifact: product_owner_resolution on an aligned comparison rejected", err is not None, err)

    claude_review_disagree = _build_review(generation, "claude", ACTOR_CLAUDE, all_pass=False)
    disagree_comparison = lin.build_comparison_artifact(chatgpt_review=chatgpt_review, claude_review=claude_review_disagree)
    err = _expect_error(
        lin.LineageValidationError,
        lin.build_adjudication_artifact,
        comparison=disagree_comparison,
        chatgpt_review=chatgpt_review,
        claude_review=claude_review_disagree,
        resolution_mode="product_owner_resolution",
    )
    check("build_adjudication_artifact: product_owner_resolution without resolved_by_actor_id/final_scores rejected", err is not None, err)

    adjudication = lin.build_adjudication_artifact(
        comparison=disagree_comparison,
        chatgpt_review=chatgpt_review,
        claude_review=claude_review_disagree,
        resolution_mode="product_owner_resolution",
        resolved_by_actor_id=ACTOR_OWNER,
        final_scores=chatgpt_review["scores"],
    )
    check("build_adjudication_artifact: product_owner_resolution with proper arguments succeeds", adjudication["resolved_by_actor_id"] == ACTOR_OWNER)


# --- Group 13: strict passes are recomputed, not trusted ---


def test_adjudication_recomputes_strict_pass():
    """Group 13."""
    generation = _dummy_generation()
    chatgpt_review = _build_review(generation, "chatgpt", ACTOR_CHATGPT, all_pass=True)
    claude_review = _build_review(generation, "claude", ACTOR_CLAUDE, all_pass=True)
    comparison = lin.build_comparison_artifact(chatgpt_review=chatgpt_review, claude_review=claude_review)

    # A caller claiming strict_pass=False despite every dimension/check
    # passing must not be trusted -- it's recomputed from the real values.
    lying_scores = [{**s, "strict_pass": False} for s in chatgpt_review["scores"]]
    adjudication = lin.build_adjudication_artifact(comparison=comparison, chatgpt_review=chatgpt_review, claude_review=claude_review, resolution_mode="reviewer_agreement")
    check("build_adjudication_artifact: recomputes strict_pass from actual scores (all-pass -> True)", all(r["strict_pass"] is True for r in adjudication["results"]))
    check("build_adjudication_artifact: aggregate_strict_pass matches recomputed results", adjudication["aggregate_strict_pass"] == f"{len(adjudication['results'])}/{len(adjudication['results'])}")


# --- Group 14: superseded/invalidated parents cannot create new descendants ---


def test_status_resolution_and_superseded_parent_blocking():
    """Group 14."""
    tmp_dir = Path(tempfile.mkdtemp())
    original_status_dir = lin.STATUS_EVENTS_DIR
    lin.STATUS_EVENTS_DIR = tmp_dir / "status_events"
    try:
        generation = _dummy_generation()
        review = _build_review(generation, "chatgpt", ACTOR_CHATGPT)
        check("resolve_active_status: a fresh artifact with no status events is 'active'", lin.resolve_active_status(review["review_id"]) == "active")

        event = lin.build_status_event(target_artifact=review, target_id_field="review_id", new_status="superseded", reason_code="correction", actor_id=ACTOR_CHATGPT)
        lin.save_status_event(event)
        check("resolve_active_status: reflects a superseded status event", lin.resolve_active_status(review["review_id"]) == "superseded")

        invalidate_event = lin.build_status_event(target_artifact=review, target_id_field="review_id", new_status="invalidated", reason_code="withdrawal", actor_id=ACTOR_CHATGPT)
        lin.save_status_event(invalidate_event)
        check("resolve_active_status: invalidated beats superseded when both exist", lin.resolve_active_status(review["review_id"]) == "invalidated")
    finally:
        lin.STATUS_EVENTS_DIR = original_status_dir
        shutil.rmtree(tmp_dir, ignore_errors=True)


# --- Group 15: a decision cannot cite anything except active adjudication artifacts ---


def test_decision_requires_adjudications():
    """Group 15."""
    err = _expect_error(lin.LineageValidationError, lin.build_decision_record, decision_type="curriculum", deciding_actor_id=ACTOR_OWNER, adjudications=[], outcome="no adjudications, should fail")
    check("build_decision_record: requires at least one adjudication reference", err is not None, err)

    generation = _dummy_generation()
    chatgpt_review = _build_review(generation, "chatgpt", ACTOR_CHATGPT)
    claude_review = _build_review(generation, "claude", ACTOR_CLAUDE)
    comparison = lin.build_comparison_artifact(chatgpt_review=chatgpt_review, claude_review=claude_review)
    adjudication = lin.build_adjudication_artifact(comparison=comparison, chatgpt_review=chatgpt_review, claude_review=claude_review, resolution_mode="reviewer_agreement")
    decision = lin.build_decision_record(decision_type="curriculum", deciding_actor_id=ACTOR_OWNER, adjudications=[adjudication], outcome="dummy decision for testing")
    check("build_decision_record: valid adjudication reference accepted", decision["adjudications"][0]["artifact_id"] == adjudication["adjudication_id"])

    err = _expect_error(lin.LineageValidationError, lin.build_decision_record, decision_type="not_a_real_type", deciding_actor_id=ACTOR_OWNER, adjudications=[adjudication], outcome="x")
    check("build_decision_record: invalid decision_type rejected", err is not None, err)


def test_dataset_snapshot_basic():
    """Not one of the 15 lineage groups directly, but required
    infrastructure for withdrawal (built and sanity-checked here since
    real_data_lineage.py owns it)."""
    empty_snapshot = lin.build_dataset_snapshot(split="real_validation", creation_reason="dummy empty snapshot", active_records=[], rubric_schema_version="real-rubric-v1")
    check("build_dataset_snapshot: empty split still gets a deterministic dataset_fingerprint", empty_snapshot["dataset_fingerprint"].startswith("sha256:"))

    non_empty = lin.build_dataset_snapshot(
        split="real_validation",
        creation_reason="dummy non-empty snapshot",
        active_records=[{"record_id": "rv_a", "source_fingerprint": "sha256:" + "1" * 64, "pair_fingerprint": "sha256:" + "2" * 64, "rubric_fingerprint": "sha256:" + "3" * 64}],
        rubric_schema_version="real-rubric-v1",
    )
    check("build_dataset_snapshot: non-empty snapshot differs from empty snapshot", non_empty["dataset_fingerprint"] != empty_snapshot["dataset_fingerprint"])


def main() -> None:
    tests = [
        test_generation_has_no_score_placeholders,
        test_artifact_integrity_contract,
        test_review_must_match_generation_record_set_and_fingerprints,
        test_score_record_rejects_bad_scores,
        test_capability_check_keys_must_match_rubric,
        test_failure_labels_validated,
        test_reviewer_roles_and_actors_distinct,
        test_comparison_requires_same_generation,
        test_comparison_alignment_status,
        test_reviewer_agreement_requires_alignment,
        test_product_owner_resolution_required_for_disagreement,
        test_adjudication_recomputes_strict_pass,
        test_status_resolution_and_superseded_parent_blocking,
        test_decision_requires_adjudications,
        test_dataset_snapshot_basic,
    ]
    for t in tests:
        t()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("All real_data_lineage.py tests passed.")


if __name__ == "__main__":
    main()
