"""Standalone assertion tests for real_data_eval_logging.py (the
real-eval-generation-v1 schema) and real_data_scoring.py -- dummy data
only. Run with `python test_real_data_eval_logging.py`. Exits 0 iff every
test passes.

real_data_scoring.py is tested standalone here (plain dicts, not built via
real_data_eval_logging.py) since generation artifacts no longer carry
scores at all -- compute_strict_pass/apply_scores are generic utilities
now used internally by the review-artifact builder in
real_data_lineage.py, not coupled to the generation schema.
"""
import shutil
import sys
import tempfile
from pathlib import Path

import real_data_eval_logging as rel
import real_data_scoring as rsc

FAILURES = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


def _dummy_generation_record(record_id: str = "rv_dummy0001", raw_output: str = "###NARRATIVE### x ###BULLETS### x ###ACTIONS###", format_valid: bool = True) -> dict:
    return rel.new_generation_record(
        record_id=record_id,
        source_fingerprint="a" * 64,
        pair_fingerprint="b" * 64,
        rubric_fingerprint="c" * 64,
        raw_output=raw_output,
        format_valid=format_valid,
    )


def test_new_generation_record_shape():
    r = _dummy_generation_record()
    check("new_generation_record: has no scores/review fields (generation is evidence, not judgment)", "scores" not in r and "review_status" not in r and "strict_pass" not in r)
    check("new_generation_record: fingerprints are sha256-prefixed", r["source_fingerprint"].startswith("sha256:") and r["pair_fingerprint"].startswith("sha256:") and r["rubric_fingerprint"].startswith("sha256:"))
    check("new_generation_record: raw_output_fingerprint is deterministic for the same raw_output", rel.new_generation_record(record_id="x", source_fingerprint="a" * 64, pair_fingerprint="b" * 64, rubric_fingerprint="c" * 64, raw_output="same text", format_valid=True)["raw_output_fingerprint"] == rel.new_generation_record(record_id="y", source_fingerprint="d" * 64, pair_fingerprint="e" * 64, rubric_fingerprint="f" * 64, raw_output="same text", format_valid=False)["raw_output_fingerprint"])


def test_holdout_requires_milestone():
    r = _dummy_generation_record()
    try:
        rel.build_generation_artifact(
            split="real_holdout",
            evaluation_reason="dummy test",
            git_commit="deadbeef",
            checkpoint={"path": "dummy/checkpoint", "fingerprint": "a" * 64, "training_seed": 42, "run_id": "run_dummy"},
            dataset={"fingerprint": "b" * 64, "record_count": 1, "rubric_schema_version": "real-rubric-v1"},
            generation_config={},
            results=[r],
            release_milestone=None,
        )
        check("build_generation_artifact: holdout without release_milestone raises", False)
    except ValueError:
        check("build_generation_artifact: holdout without release_milestone raises", True)


def test_approved_root_enforcement_and_roundtrip():
    tmp = Path(tempfile.mkdtemp())
    original_results_dir = rel.RESULTS_PRIVATE_DIR
    original_val_dir = rel.VALIDATION_RESULTS_DIR
    original_holdout_dir = rel.HOLDOUT_RESULTS_DIR
    rel.RESULTS_PRIVATE_DIR = tmp / "results" / "private"
    rel.VALIDATION_RESULTS_DIR = rel.RESULTS_PRIVATE_DIR / "real_validation"
    rel.HOLDOUT_RESULTS_DIR = rel.RESULTS_PRIVATE_DIR / "real_holdout"
    try:
        # Attempt to read outside the approved roots must fail closed.
        try:
            rel._validate_any_approved_root(tmp / "not_approved" / "sneaky.json")
            check("approved-root enforcement: rejects a path outside both roots", False)
        except rel.ApprovedRootError:
            check("approved-root enforcement: rejects a path outside both roots", True)

        # Unsafe identifiers must be rejected before they ever reach a path.
        for bad_id in ("../escape", "a/b", "a\\b", "..", "has spaces", ""):
            try:
                rel.result_path_for("real_validation", bad_id)
                check(f"result_path_for: rejects unsafe evaluation_id {bad_id!r}", False)
            except rel.UnsafeIdentifierError:
                check(f"result_path_for: rejects unsafe evaluation_id {bad_id!r}", True)

        for bad_milestone in ("../real_validation", "a/../../escape", "a/b"):
            try:
                rel.result_path_for("real_holdout", "eval_ok", milestone=bad_milestone)
                check(f"result_path_for: rejects unsafe milestone {bad_milestone!r}", False)
            except rel.UnsafeIdentifierError:
                check(f"result_path_for: rejects unsafe milestone {bad_milestone!r}", True)

        # Split-specific root enforcement: a holdout path must land under
        # HOLDOUT_RESULTS_DIR specifically, not merely "some approved root".
        holdout_path = rel.result_path_for("real_holdout", "eval_ok", milestone="milestone_ok")
        check(
            "result_path_for: real_holdout path lands under HOLDOUT_RESULTS_DIR, not VALIDATION_RESULTS_DIR",
            rel._is_relative_to(holdout_path.resolve(), rel.HOLDOUT_RESULTS_DIR.resolve())
            and not rel._is_relative_to(holdout_path.resolve(), rel.VALIDATION_RESULTS_DIR.resolve()),
        )

        r = _dummy_generation_record()
        artifact = rel.build_generation_artifact(
            split="real_validation",
            evaluation_reason="dummy roundtrip test",
            git_commit="deadbeef",
            checkpoint={"path": "dummy/checkpoint", "fingerprint": "a" * 64, "training_seed": 42, "run_id": "run_dummy"},
            dataset={"fingerprint": "b" * 64, "record_count": 1, "rubric_schema_version": "real-rubric-v1"},
            generation_config={"max_new_tokens": 300},
            results=[r],
        )
        check("build_generation_artifact: schema_version is real-eval-generation-v1", artifact["schema_version"] == "real-eval-generation-v1")
        check("build_generation_artifact: artifact_kind is 'generation'", artifact["artifact_kind"] == "generation")
        check("build_generation_artifact: aggregate.format_valid counts correctly", artifact["aggregate"]["format_valid"] == "1/1")
        check("build_generation_artifact: prompt_contract defaults to None (not yet synchronized)", artifact["prompt_contract"] is None)

        saved_path = rel.save_generation_artifact(artifact)
        check("save_generation_artifact: writes inside the approved validation root", rel._is_relative_to(saved_path.resolve(), rel.VALIDATION_RESULTS_DIR.resolve()))

        loaded = rel.load_generation_artifact(saved_path)
        check("load_generation_artifact: roundtrips identically", loaded == artifact)

        # Tamper detection: altering the file on disk after the fact must
        # be caught by the recomputed artifact_fingerprint on load.
        tampered_path = rel.VALIDATION_RESULTS_DIR / "tampered.json"
        import json as _json

        tampered_content = {**artifact, "evaluation_reason": "tampered after the fact"}
        tampered_path.write_text(_json.dumps(tampered_content), encoding="utf-8")
        try:
            rel.load_generation_artifact(tampered_path)
            check("load_generation_artifact: detects a tampered artifact_fingerprint", False)
        except rel.GenerationValidationError:
            check("load_generation_artifact: detects a tampered artifact_fingerprint", True)

        # Immutability: saving again with the same evaluation_id must not
        # silently overwrite the original.
        tampered = {**artifact, "evaluation_reason": "an attempt to overwrite the original"}
        try:
            rel.save_generation_artifact(tampered)
            check("save_generation_artifact: refuses to overwrite an existing evaluation_id", False)
        except rel.ArtifactExistsError:
            check("save_generation_artifact: refuses to overwrite an existing evaluation_id", True)
        reloaded = rel.load_generation_artifact(saved_path)
        check("save_generation_artifact: original artifact content survives an attempted overwrite", reloaded["evaluation_reason"] == "dummy roundtrip test")
    finally:
        rel.RESULTS_PRIVATE_DIR = original_results_dir
        rel.VALIDATION_RESULTS_DIR = original_val_dir
        rel.HOLDOUT_RESULTS_DIR = original_holdout_dir
        shutil.rmtree(tmp, ignore_errors=True)


def _fully_scored_record(*, format_valid=True, all_pass=True) -> dict:
    """A plain scoring-shaped dict, independent of the generation schema
    -- real_data_scoring.py's functions are generic and will be reused by
    the review-artifact builder, not tied to real_data_eval_logging.py."""
    r = {
        "record_id": "rv_dummy0001",
        "format_valid": format_valid,
        "scores": {dim: None for dim in rsc.SEMANTIC_DIMENSIONS},
        "capability_checks": {},
        "strict_pass": None,
        "failure_labels": [],
        "review_status": "unscored",
    }
    scores = {dim: all_pass for dim in rsc.SEMANTIC_DIMENSIONS}
    capability_checks = {"explicit_task_survived": all_pass}
    return rsc.apply_scores(r, scores=scores, capability_checks=capability_checks, failure_labels=[] if all_pass else ["unsupported_action"])


def test_strict_pass_computation():
    unscored = {
        "record_id": "rv_dummy0001",
        "format_valid": True,
        "scores": {dim: None for dim in rsc.SEMANTIC_DIMENSIONS},
        "capability_checks": {},
        "strict_pass": None,
        "failure_labels": [],
        "review_status": "unscored",
    }
    check("compute_strict_pass: unscored record returns None", rsc.compute_strict_pass(unscored) is None)

    passing = _fully_scored_record(format_valid=True, all_pass=True)
    check("compute_strict_pass: all dimensions + checks true -> True", passing["strict_pass"] is True)

    failing_semantic = _fully_scored_record(format_valid=True, all_pass=False)
    check("compute_strict_pass: any semantic dimension false -> False", failing_semantic["strict_pass"] is False)

    failing_format = _fully_scored_record(format_valid=False, all_pass=True)
    check("compute_strict_pass: format_valid false -> False even if semantics pass", failing_format["strict_pass"] is False)

    one_check_fails = {
        "record_id": "rv_dummy0002",
        "format_valid": True,
        "scores": {dim: None for dim in rsc.SEMANTIC_DIMENSIONS},
        "capability_checks": {},
        "strict_pass": None,
        "failure_labels": [],
        "review_status": "unscored",
    }
    one_check_fails = rsc.apply_scores(
        one_check_fails,
        scores={dim: True for dim in rsc.SEMANTIC_DIMENSIONS},
        capability_checks={"deadline_survived": True, "second_check": False},
        failure_labels=["dropped_qualifier"],
    )
    check("compute_strict_pass: one failing capability check -> False", one_check_fails["strict_pass"] is False)

    check(
        "apply_scores: does not mutate the input record",
        unscored["scores"]["topic_completeness"] is None,
    )

    missing_dim = {"format_valid": True, "scores": {"topic_completeness": True}, "capability_checks": {}}
    try:
        rsc.compute_strict_pass(missing_dim)
        check("compute_strict_pass: missing a required dimension raises", False)
    except rsc.ScoringStateError:
        check("compute_strict_pass: missing a required dimension raises", True)


def test_aggregate_strict_pass_rate():
    r1 = _fully_scored_record(all_pass=True)
    r2 = _fully_scored_record(all_pass=False)
    r3 = {
        "record_id": "rv_dummy0003",
        "format_valid": True,
        "scores": {dim: None for dim in rsc.SEMANTIC_DIMENSIONS},
        "capability_checks": {},
        "strict_pass": None,
        "failure_labels": [],
        "review_status": "unscored",
    }  # still unscored

    check(
        "aggregate_strict_pass_rate: null while any record unscored",
        rsc.aggregate_strict_pass_rate([r1, r2, r3]) is None,
    )
    check(
        "aggregate_strict_pass_rate: correct ratio once fully scored",
        rsc.aggregate_strict_pass_rate([r1, r2]) == "1/2",
    )


def main() -> None:
    tests = [
        test_new_generation_record_shape,
        test_holdout_requires_milestone,
        test_approved_root_enforcement_and_roundtrip,
        test_strict_pass_computation,
        test_aggregate_strict_pass_rate,
    ]
    for t in tests:
        t()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("All real_data_eval_logging.py / real_data_scoring.py tests passed.")


if __name__ == "__main__":
    main()
