"""Standalone assertion tests for real_data_eval_logging.py and
real_data_scoring.py -- dummy data only. Run with
`python test_real_data_eval_logging.py`. Exits 0 iff every test passes.
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


def test_new_result_record_initial_state():
    r = rel.new_result_record("rv_dummy0001", "###NARRATIVE### x ###BULLETS### x ###ACTIONS###", True)
    check(
        "new_result_record: all four semantic scores start null",
        all(v is None for v in r["scores"].values()),
    )
    check("new_result_record: strict_pass starts null", r["strict_pass"] is None)
    check("new_result_record: review_status starts 'unscored'", r["review_status"] == "unscored")


def test_holdout_requires_milestone():
    r = rel.new_result_record("rv_dummy0001", "x", True)
    try:
        rel.build_result_artifact(
            split="real_holdout",
            evaluation_reason="dummy test",
            git_commit="deadbeef",
            checkpoint={"path": "dummy/checkpoint", "fingerprint": "a" * 64, "training_seed": 42, "run_id": "run_dummy"},
            dataset={"fingerprint": "b" * 64, "record_count": 1, "rubric_version": "real-rubric-v1"},
            generation_config={},
            results=[r],
            release_milestone=None,
        )
        check("build_result_artifact: holdout without release_milestone raises", False)
    except ValueError:
        check("build_result_artifact: holdout without release_milestone raises", True)


def test_approved_root_enforcement_and_roundtrip():
    tmp = Path(tempfile.mkdtemp())
    original_results_dir = rel.RESULTS_PRIVATE_DIR
    original_val_dir = rel.VALIDATION_RESULTS_DIR
    original_holdout_dir = rel.HOLDOUT_RESULTS_DIR
    rel.RESULTS_PRIVATE_DIR = tmp / "results" / "private"
    rel.VALIDATION_RESULTS_DIR = rel.RESULTS_PRIVATE_DIR / "real_validation"
    rel.HOLDOUT_RESULTS_DIR = rel.RESULTS_PRIVATE_DIR / "real_holdout"
    try:
        # Attempt to write outside the approved roots must fail closed.
        try:
            rel._validate_output_path(tmp / "not_approved" / "sneaky.json")
            check("approved-root enforcement: rejects a path outside both roots", False)
        except rel.ApprovedRootError:
            check("approved-root enforcement: rejects a path outside both roots", True)

        r = rel.new_result_record("rv_dummy0001", "###NARRATIVE### x ###BULLETS### x ###ACTIONS###", True)
        artifact = rel.build_result_artifact(
            split="real_validation",
            evaluation_reason="dummy roundtrip test",
            git_commit="deadbeef",
            checkpoint={"path": "dummy/checkpoint", "fingerprint": "a" * 64, "training_seed": 42, "run_id": "run_dummy"},
            dataset={"fingerprint": "b" * 64, "record_count": 1, "rubric_version": "real-rubric-v1"},
            generation_config={"max_new_tokens": 300},
            results=[r],
        )
        check("build_result_artifact: schema_version is real-eval-v1", artifact["schema_version"] == "real-eval-v1")
        check("build_result_artifact: aggregate.strict_pass is null while unscored", artifact["aggregate"]["strict_pass"] is None)
        check("build_result_artifact: aggregate.format_valid counts correctly", artifact["aggregate"]["format_valid"] == "1/1")

        saved_path = rel.save_result_artifact(artifact)
        check("save_result_artifact: writes inside the approved validation root", rel._is_relative_to(saved_path.resolve(), rel.VALIDATION_RESULTS_DIR.resolve()))

        loaded = rel.load_result_artifact(saved_path)
        check("load_result_artifact: roundtrips identically", loaded == artifact)
    finally:
        rel.RESULTS_PRIVATE_DIR = original_results_dir
        rel.VALIDATION_RESULTS_DIR = original_val_dir
        rel.HOLDOUT_RESULTS_DIR = original_holdout_dir
        shutil.rmtree(tmp, ignore_errors=True)


def _fully_scored_record(*, format_valid=True, all_pass=True) -> dict:
    r = rel.new_result_record("rv_dummy0001", "dummy output", format_valid)
    scores = {dim: all_pass for dim in rsc.SEMANTIC_DIMENSIONS}
    capability_checks = {"explicit_task_survived": all_pass}
    return rsc.apply_scores(r, scores=scores, capability_checks=capability_checks, failure_labels=[] if all_pass else ["unsupported_action"])


def test_strict_pass_computation():
    unscored = rel.new_result_record("rv_dummy0001", "x", True)
    check("compute_strict_pass: unscored record returns None", rsc.compute_strict_pass(unscored) is None)

    passing = _fully_scored_record(format_valid=True, all_pass=True)
    check("compute_strict_pass: all dimensions + checks true -> True", passing["strict_pass"] is True)

    failing_semantic = _fully_scored_record(format_valid=True, all_pass=False)
    check("compute_strict_pass: any semantic dimension false -> False", failing_semantic["strict_pass"] is False)

    failing_format = _fully_scored_record(format_valid=False, all_pass=True)
    check("compute_strict_pass: format_valid false -> False even if semantics pass", failing_format["strict_pass"] is False)

    one_check_fails = rel.new_result_record("rv_dummy0002", "x", True)
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
    r3 = rel.new_result_record("rv_dummy0003", "x", True)  # still unscored

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
        test_new_result_record_initial_state,
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
