"""Standalone assertion tests for run_seed17_phase2_replay.py -- dummy
subprocesses and synthetic data only, except where explicitly noted as a
live check against the real repository. No pytest dependency: run
directly with `python test_run_seed17_phase2_replay.py`, matching this
repo's existing script-based tooling convention (see
test_run_seed17_r2_replay.py).

Genuinely dummy-only, not just labeled that way: the real train.py is
never invoked, and this whole suite runs clean under the base system
Python with no torch/transformers installed (confirmed by running it
that way -- run_seed17_phase2_replay.py's own module-level code never
imports torch; only environment_versions()/verify_cuda_bfloat16_expectation()
do, lazily, inside a function body).

Revised 2026-08-04 per ChatGPT's review: added real scratch-git-repository
tests (actual `git init`/commits, not just synthetic state dicts) proving
verify_package_commit() correctly handles the new package-commit-as-
direct-child-of-a-pinned-parent design -- a new package commit with
exactly the right files passes, remaining at the parent commit fails, an
unrelated intermediate commit (wrong parent) fails, and an unexpected
extra file in the commit fails; added verify_raw_result_artifact() tests
(missing, malformed, wrong count, reordered, empty raw_output,
prematurely-scored, and not-a-list); added a live check confirming the
governing document's on-disk hash matches the byte-faithful value ChatGPT
confirmed.
"""
import json
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import run_seed17_phase2_replay as w

FAILURES = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


def expect_system_exit(fn, *args, **kwargs) -> str | None:
    try:
        fn(*args, **kwargs)
    except SystemExit as e:
        return str(e)
    return None


# ---------------------------------------------------------------------------
# Import-closure computation, including the governing document's explicitly
# required test: a drift in a TRANSITIVE (not top-level) local module fails
# preflight.
# ---------------------------------------------------------------------------

print("=== import-closure computation ===")

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    (tmp_path / "entry.py").write_text("import mid\nimport os\n", encoding="utf-8")
    (tmp_path / "mid.py").write_text("import leaf\nimport sys\n", encoding="utf-8")
    (tmp_path / "leaf.py").write_text("import json\n", encoding="utf-8")
    (tmp_path / "unrelated.py").write_text("import re\n", encoding="utf-8")

    _orig_training_dir = w.TRAINING_DIR
    w.TRAINING_DIR = tmp_path
    try:
        closure = w.compute_import_closure(["entry.py"])
        check("closure includes the entry point itself", "entry.py" in closure)
        check("closure includes a direct local import", "mid.py" in closure)
        check("closure includes a TRANSITIVE local import (entry -> mid -> leaf)", "leaf.py" in closure)
        check("closure excludes an unreferenced local file", "unrelated.py" not in closure)
        check("closure excludes stdlib imports (os, sys, json)", closure == {"entry.py", "mid.py", "leaf.py"})

        # The governing document's explicit requirement: a drift in a
        # transitive module -- one never named in any manually-curated
        # list -- still fails preflight, because it's part of the
        # recomputed closure's file set.
        lock = {
            "executable_code": {"entry.py": w.file_fingerprint(tmp_path / "entry.py"), "mid.py": w.file_fingerprint(tmp_path / "mid.py"), "leaf.py": w.file_fingerprint(tmp_path / "leaf.py")},
            "governing_inputs": {},
            "real_validation_fingerprint": "irrelevant",
            "dependency_versions": {},
        }
        _orig_entry_points = w.EXECUTABLE_CODE_ENTRY_POINTS
        w.EXECUTABLE_CODE_ENTRY_POINTS = ["entry.py"]
        try:
            msg = expect_system_exit(w.verify_frozen_executable_code, lock)
            check("unmodified transitive closure passes against its own lock", msg is None, detail=str(msg))

            (tmp_path / "leaf.py").write_text("import json\nX = 'drifted content'\n", encoding="utf-8")
            msg = expect_system_exit(w.verify_frozen_executable_code, lock)
            check("content drift in a TRANSITIVE local module fails closed", msg is not None)

            (tmp_path / "leaf.py").write_text("import json\n", encoding="utf-8")  # restore
            (tmp_path / "mid.py").write_text("import leaf\nimport newdep\nimport sys\n", encoding="utf-8")
            (tmp_path / "newdep.py").write_text("X = 1\n", encoding="utf-8")
            msg = expect_system_exit(w.verify_frozen_executable_code, lock)
            check("a NEW transitive import (changing the closure's file set) fails closed", msg is not None)
        finally:
            w.EXECUTABLE_CODE_ENTRY_POINTS = _orig_entry_points
    finally:
        w.TRAINING_DIR = _orig_training_dir


# ---------------------------------------------------------------------------
# verify_real_validation_empty
# ---------------------------------------------------------------------------

print("\n=== verify_real_validation_empty ===")

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    empty_file = tmp_path / "real_validation.jsonl"
    empty_file.write_bytes(b"")

    _orig_training_dir = w.TRAINING_DIR
    _orig_rv_rel = w.REAL_VALIDATION_REL_PATH
    w.TRAINING_DIR = tmp_path
    w.REAL_VALIDATION_REL_PATH = "real_validation.jsonl"
    try:
        msg = expect_system_exit(w.verify_real_validation_empty)
        check("byte-empty real_validation.jsonl passes", msg is None, detail=str(msg))

        empty_file.write_bytes(b'{"input": "a real note"}\n')
        msg = expect_system_exit(w.verify_real_validation_empty)
        check("nonempty real_validation.jsonl fails closed", msg is not None)

        empty_file.unlink()
        msg = expect_system_exit(w.verify_real_validation_empty)
        check("missing real_validation.jsonl fails closed", msg is not None)
    finally:
        w.TRAINING_DIR = _orig_training_dir
        w.REAL_VALIDATION_REL_PATH = _orig_rv_rel


# ---------------------------------------------------------------------------
# verify_pinned_dependency_versions / verify_cuda_bfloat16_expectation
# ---------------------------------------------------------------------------

print("\n=== verify_pinned_dependency_versions / verify_cuda_bfloat16_expectation ===")

_orig_env_versions = w.environment_versions
w.environment_versions = lambda: {"torch": "2.11.0+cu128", "transformers": "4.57.6", "datasets": "5.0.0", "accelerate": "1.14.0", "sentencepiece": "0.2.2", "cuda_available": True}
try:
    lock = {"dependency_versions": {"torch": "2.11.0+cu128", "transformers": "4.57.6", "datasets": "5.0.0", "accelerate": "1.14.0", "sentencepiece": "0.2.2"}}
    msg = expect_system_exit(w.verify_pinned_dependency_versions, lock)
    check("matching dependency versions pass", msg is None, detail=str(msg))

    msg = expect_system_exit(w.verify_cuda_bfloat16_expectation)
    check("matching CUDA availability passes", msg is None, detail=str(msg))

    w.environment_versions = lambda: {"torch": "9.9.9", "transformers": "4.57.6", "datasets": "5.0.0", "accelerate": "1.14.0", "sentencepiece": "0.2.2", "cuda_available": True}
    msg = expect_system_exit(w.verify_pinned_dependency_versions, lock)
    check("dependency version drift fails closed", msg is not None)

    w.environment_versions = lambda: {"torch": "2.11.0+cu128", "transformers": "4.57.6", "datasets": "5.0.0", "accelerate": "1.14.0", "sentencepiece": "0.2.2", "cuda_available": False}
    msg = expect_system_exit(w.verify_cuda_bfloat16_expectation)
    check("CUDA availability drift fails closed", msg is not None)
finally:
    w.environment_versions = _orig_env_versions


# ---------------------------------------------------------------------------
# verify_clean_working_tree / verify_head_matches_origin_main -- synthetic
# git state, never the real repo (which is legitimately dirty right now
# with this package's own deliverables).
# ---------------------------------------------------------------------------

print("\n=== verify_clean_working_tree / verify_head_matches_origin_main ===")

clean_matching_state = {
    "head_commit": w.PINNED_PARENT_COMMIT,
    "origin_main_commit": w.PINNED_PARENT_COMMIT,
    "head_matches_origin_main": True,
    "head_parent_commit": "0" * 40,
    "changed_files_since_parent": frozenset(),
    "working_tree_clean": True,
    "working_tree_status_raw": "",
}
msg = expect_system_exit(w.verify_clean_working_tree, clean_matching_state)
check("clean tree passes", msg is None, detail=str(msg))
msg = expect_system_exit(w.verify_head_matches_origin_main, clean_matching_state)
check("HEAD matching origin/main passes", msg is None, detail=str(msg))

dirty_state = {**clean_matching_state, "working_tree_clean": False, "working_tree_status_raw": " M some_file.py"}
msg = expect_system_exit(w.verify_clean_working_tree, dirty_state)
check("dirty tree fails closed", msg is not None)

diverged_state = {**clean_matching_state, "origin_main_commit": "1" * 40, "head_matches_origin_main": False}
msg = expect_system_exit(w.verify_head_matches_origin_main, diverged_state)
check("HEAD diverged from origin/main fails closed", msg is not None)


# ---------------------------------------------------------------------------
# verify_package_commit -- ChatGPT's 2026-08-04 finding: the ORIGINAL check
# required HEAD to equal the commit this package was built against, but
# committing the package necessarily advances HEAD past that commit, so the
# committed package could never have passed its own preflight. Tested here
# against a REAL scratch git repository with real commits (not just
# synthetic state dicts), per ChatGPT's explicit request for proof the new
# commit-then-verify transition actually works, not just a mocked pass.
# ---------------------------------------------------------------------------

print("\n=== verify_package_commit (real scratch git repository) ===")


def make_scratch_repo(tmp_path: Path) -> None:
    def run(*args):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True)

    run("init", "-q")
    run("config", "user.email", "test@example.com")
    run("config", "user.name", "Test")


def commit_files(tmp_path: Path, files: dict[str, str], message: str) -> str:
    for rel_path, content in files.items():
        full = tmp_path / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=tmp_path, check=True, capture_output=True, text=True)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path, check=True, capture_output=True, text=True).stdout.strip()


TEST_PACKAGE_FILES = {
    "training/pkg_a.md": "a",
    "training/pkg_b.json": "b",
    "training/pkg_c.py": "c",
    "training/pkg_d.py": "d",
    "training/pkg_e.json": "e",
    "training/pkg_f.md": "f",
}

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    make_scratch_repo(tmp_path)
    parent_hash = commit_files(tmp_path, {"README.md": "parent"}, "parent commit (stand-in for the derivation gate)")

    _orig_repo_root = w.REPO_ROOT
    _orig_pinned_parent = w.PINNED_PARENT_COMMIT
    _orig_expected_files = w.EXPECTED_PACKAGE_COMMIT_FILES
    w.REPO_ROOT = tmp_path
    w.PINNED_PARENT_COMMIT = parent_hash
    w.EXPECTED_PACKAGE_COMMIT_FILES = frozenset(TEST_PACKAGE_FILES)
    try:
        # "remaining at d90fc13 fails": no package commit made yet, HEAD is
        # still the parent commit itself.
        state = w.git_state()
        msg = expect_system_exit(w.verify_package_commit, state)
        check("remaining at the parent commit (package not yet committed) fails closed", msg is not None)

        # "the new package commit passes": commit exactly the six expected
        # files as a direct child of the parent.
        commit_files(tmp_path, TEST_PACKAGE_FILES, "add the reviewed package")
        state = w.git_state()
        msg = expect_system_exit(w.verify_package_commit, state)
        check("a direct child commit containing exactly the expected files passes", msg is None, detail=str(msg))
    finally:
        w.REPO_ROOT = _orig_repo_root
        w.PINNED_PARENT_COMMIT = _orig_pinned_parent
        w.EXPECTED_PACKAGE_COMMIT_FILES = _orig_expected_files

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    make_scratch_repo(tmp_path)
    parent_hash = commit_files(tmp_path, {"README.md": "parent"}, "parent commit")
    # "a wrong parent fails": an unrelated intermediate commit sits between
    # the pinned parent and the package commit.
    commit_files(tmp_path, {"unrelated.md": "x"}, "an unrelated intermediate commit")
    commit_files(tmp_path, TEST_PACKAGE_FILES, "add the reviewed package (wrong parent)")

    _orig_repo_root = w.REPO_ROOT
    _orig_pinned_parent = w.PINNED_PARENT_COMMIT
    _orig_expected_files = w.EXPECTED_PACKAGE_COMMIT_FILES
    w.REPO_ROOT = tmp_path
    w.PINNED_PARENT_COMMIT = parent_hash
    w.EXPECTED_PACKAGE_COMMIT_FILES = frozenset(TEST_PACKAGE_FILES)
    try:
        state = w.git_state()
        msg = expect_system_exit(w.verify_package_commit, state)
        check("package commit with a wrong (non-direct) parent fails closed", msg is not None)
    finally:
        w.REPO_ROOT = _orig_repo_root
        w.PINNED_PARENT_COMMIT = _orig_pinned_parent
        w.EXPECTED_PACKAGE_COMMIT_FILES = _orig_expected_files

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    make_scratch_repo(tmp_path)
    parent_hash = commit_files(tmp_path, {"README.md": "parent"}, "parent commit")
    # "an unexpected committed file fails": the package commit includes one
    # extra file beyond the six reviewed ones.
    commit_files(tmp_path, {**TEST_PACKAGE_FILES, "training/unexpected_extra.py": "surprise"}, "add the package plus an extra file")

    _orig_repo_root = w.REPO_ROOT
    _orig_pinned_parent = w.PINNED_PARENT_COMMIT
    _orig_expected_files = w.EXPECTED_PACKAGE_COMMIT_FILES
    w.REPO_ROOT = tmp_path
    w.PINNED_PARENT_COMMIT = parent_hash
    w.EXPECTED_PACKAGE_COMMIT_FILES = frozenset(TEST_PACKAGE_FILES)
    try:
        state = w.git_state()
        msg = expect_system_exit(w.verify_package_commit, state)
        check("package commit with an unexpected extra file fails closed", msg is not None)
    finally:
        w.REPO_ROOT = _orig_repo_root
        w.PINNED_PARENT_COMMIT = _orig_pinned_parent
        w.EXPECTED_PACKAGE_COMMIT_FILES = _orig_expected_files


# ---------------------------------------------------------------------------
# verify_split_and_fingerprint / verify_benchmark_counts -- synthetic files
# ---------------------------------------------------------------------------

print("\n=== verify_split_and_fingerprint / verify_benchmark_counts ===")

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    data_dir = tmp_path / "data_dir"
    data_dir.mkdir()

    def write_jsonl(path: Path, n: int, prefix: str) -> None:
        with path.open("w", encoding="utf-8") as f:
            for i in range(n):
                f.write(json.dumps({"prompt": f"{prefix}-{i}", "target": f"t{i}"}) + "\n")

    write_jsonl(tmp_path / "candidate.jsonl", 78, "c")
    write_jsonl(data_dir / "train.jsonl", 72, "train")
    write_jsonl(data_dir / "val.jsonl", 6, "val")

    _orig_training_dir = w.TRAINING_DIR
    _orig_data_dir_rel = w.DATA_DIR_REL
    w.TRAINING_DIR = tmp_path
    w.DATA_DIR_REL = "data_dir"
    try:
        # Candidate path is hardcoded inside verify_split_and_fingerprint;
        # patch the module-level filename constant it derives from by
        # placing our synthetic candidate at the expected relative name.
        (tmp_path / "gold_v1.2.2_phase2_derived_candidate.jsonl").write_text(
            (tmp_path / "candidate.jsonl").read_text(encoding="utf-8"), encoding="utf-8"
        )
        train_pairs = [json.loads(l) for l in (data_dir / "train.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        val_pairs = [json.loads(l) for l in (data_dir / "val.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        synthetic_fp = w.canonical_training_data_fingerprint(train_pairs + val_pairs)

        _orig_expected_fp = w.EXPECTED_TRAINING_DATA_FINGERPRINT
        try:
            w.EXPECTED_TRAINING_DATA_FINGERPRINT = synthetic_fp
            msg = expect_system_exit(w.verify_split_and_fingerprint)
            check("correct 78/72/6 split with matching fingerprint passes", msg is None, detail=str(msg))

            w.EXPECTED_TRAINING_DATA_FINGERPRINT = "0" * 64
            msg = expect_system_exit(w.verify_split_and_fingerprint)
            check("training-data fingerprint mismatch fails closed", msg is not None)

            w.EXPECTED_TRAINING_DATA_FINGERPRINT = synthetic_fp
            write_jsonl(data_dir / "train.jsonl", 71, "train")  # wrong count
            msg = expect_system_exit(w.verify_split_and_fingerprint)
            check("wrong train count fails closed", msg is not None)
            write_jsonl(data_dir / "train.jsonl", 72, "train")  # restore
        finally:
            # Unconditional restoration to the module's real pinned value --
            # no dir()/locals() guessing, which previously left this constant
            # mutated and corrupted the later live-repository checks.
            w.EXPECTED_TRAINING_DATA_FINGERPRINT = _orig_expected_fp
    finally:
        w.TRAINING_DIR = _orig_training_dir
        w.DATA_DIR_REL = _orig_data_dir_rel


# ---------------------------------------------------------------------------
# build_commands / verify_command_shape
# ---------------------------------------------------------------------------

print("\n=== build_commands / verify_command_shape ===")

primary_dir = w.TRAINING_DIR / "x_test_primary"
control_dir = w.TRAINING_DIR / "x_test_control"
commands = w.build_commands(primary_dir, control_dir)

check("primary_train has no --max-steps", "--max-steps" not in commands["primary_train"])
check("control_train has --max-steps 600", "--max-steps" in commands["control_train"] and "600" in commands["control_train"])
msg = expect_system_exit(w.verify_command_shape, commands)
check("correctly-shaped commands pass verify_command_shape", msg is None, detail=str(msg))

broken_primary_has_maxsteps = {**commands, "primary_train": commands["primary_train"] + ["--max-steps", "600"]}
msg = expect_system_exit(w.verify_command_shape, broken_primary_has_maxsteps)
check("primary command WITH --max-steps fails closed", msg is not None)

broken_control_wrong_value = {**commands, "control_train": [a if a != "600" else "599" for a in commands["control_train"]]}
msg = expect_system_exit(w.verify_command_shape, broken_control_wrong_value)
check("control command with wrong --max-steps value fails closed", msg is not None)

broken_control_no_maxsteps = {**commands, "control_train": [a for a in commands["control_train"] if a not in ("--max-steps", "600")]}
msg = expect_system_exit(w.verify_command_shape, broken_control_no_maxsteps)
check("control command missing --max-steps entirely fails closed", msg is not None)

broken_wrong_seed = {**commands, "primary_train": [a if a != "17" else "42" for a in commands["primary_train"]]}
msg = expect_system_exit(w.verify_command_shape, broken_wrong_seed)
check("command not resolving to seed 17 fails closed", msg is not None)


# ---------------------------------------------------------------------------
# verify_completed_steps
# ---------------------------------------------------------------------------

print("\n=== verify_completed_steps ===")

with tempfile.TemporaryDirectory() as tmp:
    output_dir = Path(tmp)

    def make_checkpoint(n: int, global_step: int) -> None:
        ckpt = output_dir / f"checkpoint-{n}"
        ckpt.mkdir()
        (ckpt / "trainer_state.json").write_text(json.dumps({"global_step": global_step}), encoding="utf-8")

    make_checkpoint(360, 360)
    make_checkpoint(720, 720)
    msg = expect_system_exit(w.verify_completed_steps, output_dir, 720, "test-run")
    check("exact expected step count (highest checkpoint) passes", msg is None, detail=str(msg))

    msg = expect_system_exit(w.verify_completed_steps, output_dir, 600, "test-run")
    check("wrong expected step count fails closed", msg is not None)

with tempfile.TemporaryDirectory() as tmp:
    output_dir = Path(tmp)
    msg = expect_system_exit(w.verify_completed_steps, output_dir, 720, "test-run")
    check("no checkpoint-N directory at all fails closed", msg is not None)

with tempfile.TemporaryDirectory() as tmp:
    output_dir = Path(tmp)
    (output_dir / "checkpoint-600").mkdir()  # no trainer_state.json inside
    msg = expect_system_exit(w.verify_completed_steps, output_dir, 600, "test-run")
    check("checkpoint dir missing trainer_state.json fails closed", msg is not None)


# ---------------------------------------------------------------------------
# verify_raw_result_artifact -- ChatGPT's 2026-08-04 finding: a benchmark
# subprocess exiting 0 was never followed by any check that the result file
# it wrote is actually valid, complete, correctly ordered, and still
# unscored. Field names below match the real schema read directly off an
# actual run_benchmark.py output file (id/raw_output/scores with per-
# dimension null values), not guessed.
# ---------------------------------------------------------------------------

print("\n=== verify_raw_result_artifact ===")

# Revised 2026-08-04 per ChatGPT's second-pass finding: reproduced exactly
# against a real protected-16 raw artifact -- the original validator
# checked only that `scores` values were null, so a record with
# capability_checks already filled in and a non-empty failure_labels still
# passed as "no semantic scores filled." Fixture below gives each probe a
# distinct primary_checks list, including one probe with *zero* checks
# (confirmed a real, valid state -- protected probes 13-16 all have
# primary_checks: [] in the real benchmark file), so the fixture matches
# real schema shape, not a simplified guess.
BENCH_PRIMARY_CHECKS = {"01": ["CHECK_A", "CHECK_B"], "02": ["CHECK_C"], "03": []}


def make_result_record(
    rid: str,
    raw_output: str = "some generated text",
    scores: dict | None = None,
    capability_checks: dict | None = None,
    failure_labels: list | None = None,
) -> dict:
    checks = BENCH_PRIMARY_CHECKS[rid]
    return {
        "id": rid,
        "raw_output": raw_output,
        "scores": scores if scores is not None else {k: None for k in w.EXPECTED_SCORE_KEYS},
        "capability_checks": capability_checks if capability_checks is not None else {c: None for c in checks},
        "failure_labels": failure_labels if failure_labels is not None else [],
    }


with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    benchmark_path = tmp_path / "bench.jsonl"
    with benchmark_path.open("w", encoding="utf-8") as f:
        for rid, checks in BENCH_PRIMARY_CHECKS.items():
            f.write(json.dumps({"id": rid, "input": f"input {rid}", "primary_checks": checks}) + "\n")

    valid_path = tmp_path / "valid_results.json"
    valid_path.write_text(json.dumps([make_result_record(r) for r in ("01", "02", "03")]), encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, valid_path, benchmark_path, 3, "test")
    check("valid, complete, correctly-ordered, unscored result (incl. a zero-check probe) passes", msg is None, detail=str(msg))

    missing_path = tmp_path / "does_not_exist.json"
    msg = expect_system_exit(w.verify_raw_result_artifact, missing_path, benchmark_path, 3, "test")
    check("missing result file fails closed", msg is not None)

    malformed_path = tmp_path / "malformed.json"
    malformed_path.write_text("{not valid json", encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, malformed_path, benchmark_path, 3, "test")
    check("malformed (unparseable) result file fails closed", msg is not None)

    wrong_count_path = tmp_path / "wrong_count.json"
    wrong_count_path.write_text(json.dumps([make_result_record(r) for r in ("01", "02")]), encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, wrong_count_path, benchmark_path, 3, "test")
    check("wrong record count fails closed", msg is not None)

    reordered_path = tmp_path / "reordered.json"
    reordered_path.write_text(json.dumps([make_result_record(r) for r in ("02", "01", "03")]), encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, reordered_path, benchmark_path, 3, "test")
    check("reordered IDs (same set, wrong order) fail closed", msg is not None)

    missing_raw_output_path = tmp_path / "missing_raw_output.json"
    recs = [make_result_record(r) for r in ("01", "02", "03")]
    recs[1]["raw_output"] = ""
    missing_raw_output_path.write_text(json.dumps(recs), encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, missing_raw_output_path, benchmark_path, 3, "test")
    check("empty raw_output on one record fails closed", msg is not None)

    prescored_path = tmp_path / "prescored.json"
    recs = [make_result_record(r) for r in ("01", "02", "03")]
    recs[0]["scores"] = {**{k: None for k in w.EXPECTED_SCORE_KEYS}, "topic_completeness": 2}
    prescored_path.write_text(json.dumps(recs), encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, prescored_path, benchmark_path, 3, "test")
    check("a record with a semantic score already filled fails closed", msg is not None)

    not_a_list_path = tmp_path / "not_a_list.json"
    not_a_list_path.write_text(json.dumps({"not": "a list"}), encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, not_a_list_path, benchmark_path, 3, "test")
    check("result file that is not a JSON array fails closed", msg is not None)

    missing_score_key_path = tmp_path / "missing_score_key.json"
    recs = [make_result_record(r) for r in ("01", "02", "03")]
    del recs[0]["scores"]["attribution_accuracy"]
    missing_score_key_path.write_text(json.dumps(recs), encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, missing_score_key_path, benchmark_path, 3, "test")
    check("scores dict missing one of the four expected keys fails closed", msg is not None)

    extra_score_key_path = tmp_path / "extra_score_key.json"
    recs = [make_result_record(r) for r in ("01", "02", "03")]
    recs[0]["scores"]["an_unexpected_extra_dimension"] = None
    extra_score_key_path.write_text(json.dumps(recs), encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, extra_score_key_path, benchmark_path, 3, "test")
    check("scores dict with an unexpected extra key fails closed", msg is not None)

    malformed_checks_path = tmp_path / "malformed_checks.json"
    recs = [make_result_record(r) for r in ("01", "02", "03")]
    recs[0]["capability_checks"] = {"CHECK_A": None}  # probe 01 actually needs CHECK_A and CHECK_B
    malformed_checks_path.write_text(json.dumps(recs), encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, malformed_checks_path, benchmark_path, 3, "test")
    check("capability_checks keys not matching the probe's own primary_checks fails closed", msg is not None)

    prefilled_checks_path = tmp_path / "prefilled_checks.json"
    recs = [make_result_record(r) for r in ("01", "02", "03")]
    recs[0]["capability_checks"] = {"CHECK_A": True, "CHECK_B": None}
    prefilled_checks_path.write_text(json.dumps(recs), encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, prefilled_checks_path, benchmark_path, 3, "test")
    check("a record with a capability_check already filled fails closed -- this is ChatGPT's exact reproduction case", msg is not None)

    nonempty_labels_path = tmp_path / "nonempty_labels.json"
    recs = [make_result_record(r) for r in ("01", "02", "03")]
    recs[0]["failure_labels"] = ["Topic Loss"]
    nonempty_labels_path.write_text(json.dumps(recs), encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, nonempty_labels_path, benchmark_path, 3, "test")
    check("a record with a non-empty failure_labels fails closed -- also ChatGPT's exact reproduction case", msg is not None)

    malformed_labels_path = tmp_path / "malformed_labels.json"
    recs = [make_result_record(r) for r in ("01", "02", "03")]
    recs[0]["failure_labels"] = "not-a-list"
    malformed_labels_path.write_text(json.dumps(recs), encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, malformed_labels_path, benchmark_path, 3, "test")
    check("a record with a malformed (non-list) failure_labels fails closed", msg is not None)

# Independently reconstruct ChatGPT's exact reported reproduction against
# the real, committed protected-16 raw artifact (not a synthetic fixture)
# -- one record tampered with a filled capability_check and a non-empty
# failure_labels, scores left entirely null.
real_protected_path = w.TRAINING_DIR / "controlled_seed17_r2_replay_run" / "protected16_results.json"
if real_protected_path.exists():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        real_results = json.loads(real_protected_path.read_text(encoding="utf-8"))
        tampered = json.loads(json.dumps(real_results))
        first_checks = tampered[0]["capability_checks"]
        tampered[0]["capability_checks"] = {(next(iter(first_checks)) if first_checks else "FAKE_CHECK"): True}
        tampered[0]["failure_labels"] = ["Topic Loss"]
        tampered_path = tmp_path / "tampered_real.json"
        tampered_path.write_text(json.dumps(tampered), encoding="utf-8")
        real_benchmark_path = w.TRAINING_DIR / w.GOVERNING_INPUT_FILES[3]
        msg = expect_system_exit(w.verify_raw_result_artifact, tampered_path, real_benchmark_path, 16, "real-repro")
        check("ChatGPT's exact reported reproduction (real protected-16 artifact, tampered) fails closed", msg is not None)

        msg = expect_system_exit(w.verify_raw_result_artifact, real_protected_path, real_benchmark_path, 16, "real-untampered")
        check("the real, genuinely-unscored protected-16 artifact still passes untampered", msg is None, detail=str(msg))


# ---------------------------------------------------------------------------
# create_exclusive_experiment_dir
# ---------------------------------------------------------------------------

print("\n=== create_exclusive_experiment_dir ===")

with tempfile.TemporaryDirectory() as tmp:
    fresh = Path(tmp) / "fresh_root"
    result = w.create_exclusive_experiment_dir(fresh)
    check("fresh directory creates cleanly", result == fresh and fresh.is_dir())

    msg = expect_system_exit(w.create_exclusive_experiment_dir, fresh)
    check("re-creating an existing directory fails closed", msg is not None)


# ---------------------------------------------------------------------------
# run_logged_subprocess / require_success -- dummy subprocesses only, same
# interruption-durability property already proven for run_seed17_r2_replay.py
# ---------------------------------------------------------------------------

print("\n=== run_logged_subprocess / require_success ===")

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    log_path = tmp_path / "ok.log"
    proc = w.run_logged_subprocess([sys.executable, "-c", "print('hello')"], cwd=tmp_path, log_path=log_path)
    check("successful dummy subprocess returns exit code 0", proc.returncode == 0)
    check("log file was written", log_path.exists() and "hello" in log_path.read_text(encoding="utf-8"))
    msg = expect_system_exit(w.require_success, proc, "dummy-ok")
    check("require_success passes on exit code 0", msg is None, detail=str(msg))

    fail_log_path = tmp_path / "fail.log"
    proc = w.run_logged_subprocess([sys.executable, "-c", "import sys; sys.exit(7)"], cwd=tmp_path, log_path=fail_log_path)
    check("failing dummy subprocess returns exit code 7", proc.returncode == 7)
    msg = expect_system_exit(w.require_success, proc, "dummy-fail")
    check("require_success fails closed on nonzero exit", msg is not None)

    # Interruption durability: the log file must contain output produced
    # before an external kill, proving stdout is written to disk as
    # produced rather than buffered in Python memory until completion.
    interrupt_log_path = tmp_path / "interrupt.log"
    script = textwrap.dedent(
        """
        import sys, time
        print("before-kill-marker", flush=True)
        time.sleep(30)
        print("this line should never be reached")
        """
    )
    full_env = {**__import__("os").environ}
    with interrupt_log_path.open("x", encoding="utf-8") as log_file:
        log_file.write("=== combined stdout+stderr ===\n")
        log_file.flush()
        proc2 = subprocess.Popen([sys.executable, "-c", script], cwd=tmp_path, env=full_env, stdout=log_file, stderr=subprocess.STDOUT, text=True)
        import time as _time

        _time.sleep(1.5)
        proc2.kill()
        proc2.wait()
    content_after_marker = interrupt_log_path.read_text(encoding="utf-8").split("=== combined stdout+stderr ===\n", 1)[1]
    check("interrupted subprocess's pre-kill output survives on disk", "before-kill-marker" in content_after_marker)
    check("interrupted subprocess's post-kill output does not appear", "should never be reached" not in content_after_marker)


# ---------------------------------------------------------------------------
# main() dry-run path -- no side effects without --confirm-execute
# ---------------------------------------------------------------------------

print("\n=== main() dry-run (no --confirm-execute) ===")

# Must be a path *under* TRAINING_DIR: build_commands() computes each
# command's paths via .relative_to(TRAINING_DIR), which raises for any
# path outside it -- an arbitrary tempfile location (outside the repo)
# would break that, unrelated to whatever main() itself is doing.
fresh_experiment_dir = w.TRAINING_DIR / "x_test_dryrun_experiment_root"
assert not fresh_experiment_dir.exists(), "test fixture collision -- pick a different throwaway name"
try:
    result = subprocess.run(
        [sys.executable, str(w.TRAINING_DIR / "run_seed17_phase2_replay.py"), "--experiment-dir", str(fresh_experiment_dir)],
        cwd=w.TRAINING_DIR,
        capture_output=True,
        text=True,
    )
    check("dry-run exits 0", result.returncode == 0, detail=result.stderr[-500:])
    check("dry-run prints all 6 planned commands", result.stdout.count("$ ") == 6)
    check("dry-run mentions --confirm-execute", "--confirm-execute" in result.stdout)
    check("dry-run creates NO experiment directory", not fresh_experiment_dir.exists())
finally:
    if fresh_experiment_dir.exists():
        import shutil

        shutil.rmtree(fresh_experiment_dir)


# ---------------------------------------------------------------------------
# GATE6_REQUIRED_PASS_SET sanity
# ---------------------------------------------------------------------------

print("\n=== GATE6_REQUIRED_PASS_SET ===")

check("gate-6 pass set has exactly 13 probes", len(w.GATE6_REQUIRED_PASS_SET) == 13)
check(
    "gate-6 pass set is exactly the R2 pass set plus repaired probe 13",
    w.GATE6_REQUIRED_PASS_SET == frozenset({"01", "03", "04", "05", "06", "07", "09", "10", "12", "13", "14", "15", "16"}),
)
check("gate-6 pass set excludes 02, 08, 11", not ({"02", "08", "11"} & w.GATE6_REQUIRED_PASS_SET))


# ---------------------------------------------------------------------------
# Live checks against the real, pinned repository files
# ---------------------------------------------------------------------------

print("\n=== live checks against real pinned files ===")

lock = w.load_frozen_fingerprints()
msg = expect_system_exit(w.verify_frozen_executable_code, lock)
check("real import closure (12 files) verifies clean against the real lock", msg is None, detail=str(msg))

msg = expect_system_exit(w.verify_frozen_governing_inputs, lock)
check("real governing inputs (78/72/6/16/10, real_validation empty) verify clean", msg is None, detail=str(msg))

msg = expect_system_exit(w.verify_benchmark_counts)
check("real benchmark counts (16/10) verify clean", msg is None, detail=str(msg))

msg = expect_system_exit(w.verify_split_and_fingerprint)
check("real split and training-data fingerprint verify clean", msg is None, detail=str(msg))

real_commands = w.build_commands(w.TRAINING_DIR / "controlled_seed17_phase2_replay_run" / "primary", w.TRAINING_DIR / "controlled_seed17_phase2_replay_run" / "control")
msg = expect_system_exit(w.verify_command_shape, real_commands)
check("real constructed commands verify clean", msg is None, detail=str(msg))

state = w.git_state()
check("HEAD currently matches origin/main (package built on a synced repo)", state["head_matches_origin_main"])

# verify_package_commit is correctly NOT expected to pass yet -- this
# package hasn't been committed, so HEAD still IS the pinned parent commit
# rather than a child of it. This is a live sanity check that the
# mechanism is wired correctly against the real repo, not a claim it
# should pass pre-commit.
msg = expect_system_exit(w.verify_package_commit, state)
check("verify_package_commit correctly fails pre-commit (HEAD is still the parent, not a child)", msg is not None)

governing_doc_path = w.TRAINING_DIR / "phase2_seed17_replay_interpretation_and_outcome_matrix_chatgpt.md"
governing_doc_hash = w.file_fingerprint(governing_doc_path)
check(
    "governing document on disk matches the byte-faithful hash ChatGPT confirmed (1a801768...)",
    governing_doc_hash == "1a80176849941a3a0582b82f31978d2285644ec99af489fbefa16488183585f9",
    detail=governing_doc_hash,
)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print(f"\n{'='*60}")
if FAILURES:
    print(f"{len(FAILURES)} check(s) FAILED: {FAILURES}")
    sys.exit(1)
else:
    print("All checks passed.")
