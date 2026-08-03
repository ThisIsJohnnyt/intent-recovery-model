"""Standalone assertion tests for run_seed17_r2_replay.py -- dummy
subprocess commands only; the real train.py/run_benchmark.py are never
invoked here. No pytest dependency: run directly with
`python test_run_seed17_r2_replay.py`, matching this repo's existing
script-based tooling convention.

Covers each of the four execution-readiness gaps ChatGPT flagged on the
frozen manifest (2026-08-03): base-model/tokenizer snapshot pinning, raw
log preservation with true exit-status propagation, fail-closed exclusive
outputs, and pre-execution receipt generation -- plus the two further
gaps ChatGPT found on this file's first draft the same day: frozen
fingerprints/dependency versions/working-tree cleanliness were being
recorded but never enforced, and the log was buffered in memory rather
than streamed, so interruption mid-run would have lost everything.
"""
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import run_seed17_r2_replay as r

FAILURES = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


def expect_raises(fn, *args, **kwargs) -> BaseException | None:
    """Catches BaseException, not just Exception -- ReplayPreflightError
    subclasses SystemExit, which except Exception would silently miss."""
    try:
        fn(*args, **kwargs)
    except BaseException as e:
        return e
    return None


def test_real_base_model_snapshot_matches_pinned():
    err = expect_raises(r.verify_pinned_base_model_snapshot)
    check("real HF cache snapshot matches pinned revision/fingerprints", err is None, err)


def test_real_baseline_checkpoint_matches_pinned_snapshot():
    checkpoint_dir = r.TRAINING_DIR / "checkpoints" / "gold_v1.2.2-v2contract-seed17" / "final"
    err = expect_raises(r.verify_baseline_checkpoint_used_pinned_snapshot, checkpoint_dir)
    check("real baseline checkpoint's spiece.model matches the pinned snapshot", err is None, err)


def test_snapshot_check_fails_closed_on_wrong_revision():
    orig = r.PINNED_BASE_MODEL_REVISION
    try:
        r.PINNED_BASE_MODEL_REVISION = "0000000000000000000000000000000000000000"
        err = expect_raises(r.verify_pinned_base_model_snapshot)
        check(
            "snapshot check fails closed when pinned revision is wrong",
            err is not None and "expected pinned" in str(err),
            err,
        )
    finally:
        r.PINNED_BASE_MODEL_REVISION = orig


def test_snapshot_check_fails_closed_on_wrong_fingerprint():
    orig = r.PINNED_BASE_MODEL_FILE_FINGERPRINTS
    try:
        tampered = dict(orig)
        tampered["spiece.model"] = "0" * 64
        r.PINNED_BASE_MODEL_FILE_FINGERPRINTS = tampered
        err = expect_raises(r.verify_pinned_base_model_snapshot)
        check(
            "snapshot check fails closed when a pinned file fingerprint is wrong",
            err is not None and "fingerprint mismatch" in str(err),
            err,
        )
    finally:
        r.PINNED_BASE_MODEL_FILE_FINGERPRINTS = orig


def test_executable_code_fingerprints_cover_all_listed_files():
    fps = r.fingerprint_executable_code()
    check(
        "executable-code fingerprints cover every listed file",
        set(fps) == set(r.EXECUTABLE_CODE_FILES) and all(len(v) == 64 for v in fps.values()),
        fps,
    )


def test_executable_code_fingerprint_fails_closed_on_missing_file():
    orig = r.EXECUTABLE_CODE_FILES
    try:
        r.EXECUTABLE_CODE_FILES = orig + ["this_file_does_not_exist.py"]
        err = expect_raises(r.fingerprint_executable_code)
        check("executable-code fingerprinting fails closed on a missing file", err is not None, err)
    finally:
        r.EXECUTABLE_CODE_FILES = orig


def test_governing_input_fingerprints_cover_all_listed_files():
    fps = r.fingerprint_governing_inputs()
    check(
        "governing-input fingerprints cover every listed file",
        set(fps) == set(r.GOVERNING_INPUT_FILES) and all(len(v) == 64 for v in fps.values()),
        fps,
    )


def test_governing_input_files_include_both_benchmark_datasets():
    check(
        "GOVERNING_INPUT_FILES includes both frozen evaluation-set files (missing from the first draft)",
        "../datasets/benchmark/gold_v1.2.1_probes.jsonl" in r.GOVERNING_INPUT_FILES
        and "../datasets/benchmark/source_determined_items_v2_acceptance_draft.jsonl" in r.GOVERNING_INPUT_FILES,
        r.GOVERNING_INPUT_FILES,
    )


def test_frozen_fingerprints_lockfile_has_required_sections():
    lock = r.load_frozen_fingerprints()
    check(
        "frozen-fingerprints lock file has all three required sections",
        {"executable_code", "governing_inputs", "dependency_versions"} <= set(lock),
        sorted(lock),
    )


def test_real_executable_code_matches_frozen_lockfile():
    err = expect_raises(r.verify_frozen_executable_code)
    check("real executable-code fingerprints match the frozen lock file", err is None, err)


def test_frozen_executable_code_fails_closed_on_mismatch():
    lock = r.load_frozen_fingerprints()
    tampered = {**lock, "executable_code": {**lock["executable_code"], "train.py": "0" * 64}}
    err = expect_raises(r.verify_frozen_executable_code, tampered)
    check(
        "executable-code check fails closed when a pinned fingerprint doesn't match",
        err is not None and "fingerprint mismatch" in str(err),
        err,
    )


def test_frozen_executable_code_fails_closed_on_missing_pin():
    lock = r.load_frozen_fingerprints()
    tampered_code = dict(lock["executable_code"])
    del tampered_code["train.py"]
    tampered = {**lock, "executable_code": tampered_code}
    err = expect_raises(r.verify_frozen_executable_code, tampered)
    check(
        "executable-code check fails closed when a file has no pinned entry at all",
        err is not None and "does not match the frozen lock file" in str(err),
        err,
    )


def test_real_governing_inputs_match_frozen_lockfile():
    err = expect_raises(r.verify_frozen_governing_inputs)
    check("real governing-input fingerprints match the frozen lock file", err is None, err)


def test_frozen_governing_inputs_fails_closed_on_mismatch():
    lock = r.load_frozen_fingerprints()
    key = next(iter(lock["governing_inputs"]))
    tampered = {**lock, "governing_inputs": {**lock["governing_inputs"], key: "0" * 64}}
    err = expect_raises(r.verify_frozen_governing_inputs, tampered)
    check(
        "governing-input check fails closed when a pinned fingerprint doesn't match (e.g. benchmark-dataset drift)",
        err is not None and "fingerprint mismatch" in str(err),
        err,
    )


def test_real_dependency_versions_match_frozen_lockfile():
    err = expect_raises(r.verify_pinned_dependency_versions)
    check("real installed dependency versions match the frozen lock file", err is None, err)


def test_dependency_versions_fail_closed_on_drift():
    lock = r.load_frozen_fingerprints()
    tampered = {**lock, "dependency_versions": {**lock["dependency_versions"], "torch": "0.0.0+cpu"}}
    err = expect_raises(r.verify_pinned_dependency_versions, tampered)
    check(
        "dependency-version check fails closed when an installed version doesn't match the pin",
        err is not None and "Dependency version drift" in str(err),
        err,
    )


def test_clean_working_tree_check_passes_on_clean_synthetic_state():
    # Uses a synthetic state rather than the real repo's current git_state(),
    # since this round's own deliverables are legitimately still uncommitted
    # pending review -- asserting "the real tree is clean" would be false
    # right now by design, not a bug this test should chase.
    err = expect_raises(r.verify_clean_working_tree, {"working_tree_clean": True, "working_tree_status_raw": ""})
    check("clean-working-tree check passes on a synthetic clean state", err is None, err)


def test_clean_working_tree_check_fails_closed_on_dirty_synthetic_state():
    err = expect_raises(
        r.verify_clean_working_tree,
        {"working_tree_clean": False, "working_tree_status_raw": " M some_file.py"},
    )
    check(
        "clean-working-tree check fails closed on a synthetic dirty state",
        err is not None and "not clean" in str(err),
        err,
    )


def test_git_state_shape():
    state = r.git_state()
    check(
        "git_state returns the expected keys with plausible types",
        isinstance(state["head_commit"], str)
        and len(state["head_commit"]) == 40
        and isinstance(state["working_tree_clean"], bool)
        and isinstance(state["head_matches_origin_main"], bool),
        state,
    )


def test_environment_versions_shape():
    env = r.environment_versions()
    check(
        "environment_versions reports live installed versions, not placeholders",
        env.get("torch") not in (None, "unknown") and env.get("transformers") not in (None, "unknown"),
        env,
    )


def test_exclusive_dir_fails_closed_when_already_exists():
    with tempfile.TemporaryDirectory() as tmp:
        existing = Path(tmp) / "already-here"
        existing.mkdir()
        err = expect_raises(r.create_exclusive_experiment_dir, existing)
        check("exclusive experiment dir creation fails closed when path exists", err is not None, err)

        fresh = Path(tmp) / "brand-new"
        err2 = expect_raises(r.create_exclusive_experiment_dir, fresh)
        check("exclusive experiment dir creation succeeds for a new path", err2 is None and fresh.is_dir(), err2)


def test_write_exclusive_fails_closed_when_already_exists():
    with tempfile.TemporaryDirectory() as tmp:
        existing = Path(tmp) / "already-here.txt"
        existing.write_text("original", encoding="utf-8")
        err = expect_raises(r.write_exclusive, existing, "clobbered")
        check("write_exclusive fails closed rather than overwriting", err is not None, err)
        check("write_exclusive did not modify the existing file's content", existing.read_text(encoding="utf-8") == "original")


def test_logged_subprocess_captures_output_and_preserves_success_exit_code():
    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "ok.log"
        cmd = [sys.executable, "-c", "print('hello from dummy step'); import sys; sys.exit(0)"]
        proc = r.run_logged_subprocess(cmd, cwd=r.TRAINING_DIR, log_path=log_path)
        content = log_path.read_text(encoding="utf-8")
        check(
            "logged subprocess captures real stdout and a real 0 exit code",
            proc.returncode == 0 and "hello from dummy step" in content and "exit code: 0" in content,
            (proc.returncode, content),
        )
        err = expect_raises(r.require_success, proc, "dummy-ok-step")
        check("require_success does not raise on a 0 exit code", err is None, err)


def test_logged_subprocess_preserves_failure_exit_code_and_require_success_raises():
    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "fail.log"
        cmd = [sys.executable, "-c", "print('about to fail'); import sys; sys.exit(7)"]
        proc = r.run_logged_subprocess(cmd, cwd=r.TRAINING_DIR, log_path=log_path)
        content = log_path.read_text(encoding="utf-8")
        check(
            "logged subprocess preserves a real nonzero exit code, unmasked",
            proc.returncode == 7 and "exit code: 7" in content,
            (proc.returncode, content),
        )
        err = expect_raises(r.require_success, proc, "dummy-failing-step")
        check(
            "require_success raises and reports the failing step name on nonzero exit",
            err is not None and "dummy-failing-step" in str(err) and "7" in str(err),
            err,
        )


def test_log_content_survives_subprocess_being_killed_before_completion():
    # Tests the underlying durability mechanism directly (open the log file
    # exclusively, pass it as the child's stdout, so the OS writes output
    # to disk as it's produced) using subprocess.Popen + an explicit kill,
    # rather than going through run_logged_subprocess/subprocess.run --
    # subprocess.run always blocks until the child has actually terminated
    # one way or another, so it can't itself simulate "the wrapper's own
    # Python process is interrupted mid-run"; killing the child mid-stream
    # while writing to an already-open file handle is the closest faithful
    # reproduction of that failure mode achievable within one test process.
    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "interrupted.log"
        marker = "=== combined stdout+stderr (streamed live) ==="
        child_script = (
            "import sys, time\n"
            "print('partial output before interruption', flush=True)\n"
            "time.sleep(30)\n"
            "print('this line should never be reached')\n"
        )
        cmd = [sys.executable, "-c", child_script]
        with log_path.open("x", encoding="utf-8") as log_file:
            # Deliberately does NOT echo the full command (which would
            # embed this multi-line script's literal source, including the
            # unexecuted print's text, into the header itself -- a real
            # single-line train.py/run_benchmark.py invocation wouldn't do
            # this, but checking only the section after `marker` sidesteps
            # it either way and is the honest place to look for the
            # child's actual runtime output, not its source code).
            log_file.write(f"{marker}\n")
            log_file.flush()
            proc = subprocess.Popen(cmd, cwd=r.TRAINING_DIR, stdout=log_file, stderr=subprocess.STDOUT, text=True)
            time.sleep(1.5)  # let the child flush its first line and start sleeping
            proc.kill()
            proc.wait()
        content = log_path.read_text(encoding="utf-8")
        runtime_output = content.split(marker, 1)[1]
        check(
            "partial output survives on disk even when the subprocess is killed before it exits normally",
            "partial output before interruption" in runtime_output and "this line should never be reached" not in runtime_output,
            content,
        )


def test_build_receipt_shape_and_fingerprint_consistency():
    with tempfile.TemporaryDirectory(dir=r.TRAINING_DIR) as tmp:
        experiment_dir = Path(tmp)
        receipt = r.build_receipt(experiment_dir, ["dummy command 1", "dummy command 2"])
        has_expected_keys = {
            "timestamp_utc",
            "git",
            "planned_commands",
            "environment",
            "resolved_configuration",
            "base_model",
            "executable_code_fingerprints",
            "governing_input_fingerprints",
        } <= set(receipt)
        train_py_fp_matches = receipt["executable_code_fingerprints"]["train.py"] == r.file_fingerprint(r.TRAINING_DIR / "train.py")
        check(
            "receipt has all required top-level sections",
            has_expected_keys,
            sorted(receipt),
        )
        check(
            "receipt's train.py fingerprint matches an independent direct recomputation",
            train_py_fp_matches,
        )
        check(
            "receipt's planned_commands are recorded verbatim",
            receipt["planned_commands"] == ["dummy command 1", "dummy command 2"],
        )


def test_dry_run_main_creates_nothing():
    default_dir = r.TRAINING_DIR / "controlled_seed17_r2_replay_run"
    pre_existing = default_dir.exists()
    old_argv = sys.argv
    try:
        sys.argv = ["run_seed17_r2_replay.py"]  # no --confirm-execute
        r.main()
    finally:
        sys.argv = old_argv
    check(
        "dry-run main() (no --confirm-execute) creates no experiment directory",
        default_dir.exists() == pre_existing,
        f"existed before={pre_existing}, exists after={default_dir.exists()}",
    )


def main() -> None:
    tests = [
        test_real_base_model_snapshot_matches_pinned,
        test_real_baseline_checkpoint_matches_pinned_snapshot,
        test_snapshot_check_fails_closed_on_wrong_revision,
        test_snapshot_check_fails_closed_on_wrong_fingerprint,
        test_executable_code_fingerprints_cover_all_listed_files,
        test_executable_code_fingerprint_fails_closed_on_missing_file,
        test_governing_input_fingerprints_cover_all_listed_files,
        test_governing_input_files_include_both_benchmark_datasets,
        test_frozen_fingerprints_lockfile_has_required_sections,
        test_real_executable_code_matches_frozen_lockfile,
        test_frozen_executable_code_fails_closed_on_mismatch,
        test_frozen_executable_code_fails_closed_on_missing_pin,
        test_real_governing_inputs_match_frozen_lockfile,
        test_frozen_governing_inputs_fails_closed_on_mismatch,
        test_real_dependency_versions_match_frozen_lockfile,
        test_dependency_versions_fail_closed_on_drift,
        test_clean_working_tree_check_passes_on_clean_synthetic_state,
        test_clean_working_tree_check_fails_closed_on_dirty_synthetic_state,
        test_git_state_shape,
        test_environment_versions_shape,
        test_exclusive_dir_fails_closed_when_already_exists,
        test_write_exclusive_fails_closed_when_already_exists,
        test_logged_subprocess_captures_output_and_preserves_success_exit_code,
        test_logged_subprocess_preserves_failure_exit_code_and_require_success_raises,
        test_log_content_survives_subprocess_being_killed_before_completion,
        test_build_receipt_shape_and_fingerprint_consistency,
        test_dry_run_main_creates_nothing,
    ]
    for t in tests:
        t()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print(f"All {len(tests)} run_seed17_r2_replay.py tests passed. No training or inference was performed.")


if __name__ == "__main__":
    main()
