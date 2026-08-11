"""Standalone assertion tests for run_seed17_regression_balanced_repair.py --
dummy subprocesses and synthetic data only, except where explicitly noted
as a live check against the real repository. No pytest dependency: run
directly with `python test_run_seed17_regression_balanced_repair.py`,
matching this repo's existing script-based tooling convention (see
test_run_seed17_contrastive_replay.py, whose structure this file closely
follows -- re-derived directly, not imported, per the governing design's
own instruction that every executable byte, path, fingerprint, command,
test, and import be re-derived and reviewed for this package).

Genuinely dummy-only, not just labeled that way: the real train.py is
never invoked, and this module's own top-level code never imports torch;
only environment_versions()/verify_cuda_bfloat16_expectation() do,
lazily, inside a function body.

Covers everything reused unchanged from the prior contrastive-replay
wrapper's already-proven design (canonicalize_pinned_lf_bytes,
load_canonical_governing_inputs, ensure_real_validation_placeholder,
verify_command_shape, verify_package_commit, verify_frozen_executable_code,
bootstrap_clean_tree_then_real_validation, resolve_experiment_dir) PLUS
the two requirements specific to this package:

1. verify_treatment_candidate_equals_comparator_plus_delta -- the
   treatment candidate's first 78 records must be byte-identical to the
   comparator candidate; the remaining 7 must match the reviewed
   proposal's input text, in order.
2. verify_treatment_proposal_membership, extended with a comparator-
   absence check -- a proposal record must never already exist anywhere
   in the comparator (train or validation), not just absent from
   treatment validation.
"""
import json
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import run_seed17_regression_balanced_repair as w

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
# canonicalize_pinned_lf_bytes -- unchanged design, re-derived and
# independently proven correct here too.
# ---------------------------------------------------------------------------

print("=== canonicalize_pinned_lf_bytes ===")

canon = b'{"prompt": "p1", "target": "t1"}\n{"prompt": "p2", "target": "t2"}\n'
canon_fp = __import__("hashlib").sha256(canon).hexdigest()
crlf_of_canon = canon.replace(b"\n", b"\r\n")

result = None
try:
    result = w.canonicalize_pinned_lf_bytes(canon, canon_fp, "test file")
except SystemExit as e:
    result = str(e)
check("LF checkout passes", result == canon, detail=str(result))

result = None
try:
    result = w.canonicalize_pinned_lf_bytes(crlf_of_canon, canon_fp, "test file")
except SystemExit as e:
    result = str(e)
check("uniform CRLF checkout passes and produces the same LF output", result == canon, detail=str(result))

check(
    "LF and CRLF inputs produce identical generated output",
    w.canonicalize_pinned_lf_bytes(canon, canon_fp, "t") == w.canonicalize_pinned_lf_bytes(crlf_of_canon, canon_fp, "t"),
)

mixed_endings = b'{"prompt": "p1", "target": "t1"}\r\n{"prompt": "p2", "target": "t2"}\n'
msg = expect_system_exit(w.canonicalize_pinned_lf_bytes, mixed_endings, canon_fp, "test file")
check("mixed line endings fail closed", msg is not None)

bare_cr = canon.replace(b'"t1"}\n', b'"t1"}\r', 1)
msg = expect_system_exit(w.canonicalize_pinned_lf_bytes, bare_cr, canon_fp, "test file")
check("bare carriage return fails closed", msg is not None)

content_drift_crlf = crlf_of_canon.replace(b"p1", b"p1-ALTERED", 1)
msg = expect_system_exit(w.canonicalize_pinned_lf_bytes, content_drift_crlf, canon_fp, "test file")
check("content drift fails closed", msg is not None)

blank_line_drift_crlf = crlf_of_canon.replace(b'"t1"}\r\n', b'"t1"}\r\n\r\n', 1)
msg = expect_system_exit(w.canonicalize_pinned_lf_bytes, blank_line_drift_crlf, canon_fp, "test file")
check("blank-line drift fails closed", msg is not None)

msg = expect_system_exit(w.canonicalize_pinned_lf_bytes, canon[:-1], canon_fp, "test file")
check("missing terminal newline (LF form) fails closed", msg is not None)

msg = expect_system_exit(w.canonicalize_pinned_lf_bytes, crlf_of_canon[:-2], canon_fp, "test file")
check("missing terminal newline (CRLF form) fails closed", msg is not None)

msg = expect_system_exit(w.canonicalize_pinned_lf_bytes, b"\xef\xbb\xbf" + canon, canon_fp, "test file")
check("UTF-8 BOM fails closed", msg is not None)


# ---------------------------------------------------------------------------
# load_canonical_governing_inputs -- synthetic files, both LF and CRLF
# checkouts, plus a missing-file and a drifted-content case.
# ---------------------------------------------------------------------------

print("\n=== load_canonical_governing_inputs ===")

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    (tmp_path / "a.jsonl").write_bytes(canon)
    (tmp_path / "b.jsonl").write_bytes(crlf_of_canon)

    _orig_training_dir = w.TRAINING_DIR
    _orig_inputs = w.CANONICAL_LF_GOVERNING_INPUTS
    w.TRAINING_DIR = tmp_path
    w.CANONICAL_LF_GOVERNING_INPUTS = {"a.jsonl": canon_fp, "b.jsonl": canon_fp}
    try:
        result = w.load_canonical_governing_inputs()
        check("both LF and CRLF governing inputs load and canonicalize", result == {"a.jsonl": canon, "b.jsonl": canon})

        w.CANONICAL_LF_GOVERNING_INPUTS = {"a.jsonl": canon_fp, "missing.jsonl": canon_fp}
        msg = expect_system_exit(w.load_canonical_governing_inputs)
        check("a missing governing input fails closed", msg is not None)

        w.CANONICAL_LF_GOVERNING_INPUTS = {"a.jsonl": "0" * 64}
        msg = expect_system_exit(w.load_canonical_governing_inputs)
        check("a fingerprint mismatch fails closed", msg is not None)
    finally:
        w.TRAINING_DIR = _orig_training_dir
        w.CANONICAL_LF_GOVERNING_INPUTS = _orig_inputs


# ---------------------------------------------------------------------------
# verify_real_validation_empty / ensure_real_validation_placeholder
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


print("\n=== ensure_real_validation_placeholder ===")

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    rv_path = tmp_path / "sub" / "real_validation.jsonl"

    _orig_training_dir = w.TRAINING_DIR
    _orig_rv_rel = w.REAL_VALIDATION_REL_PATH
    w.TRAINING_DIR = tmp_path
    w.REAL_VALIDATION_REL_PATH = "sub/real_validation.jsonl"
    try:
        check("file absent before the placeholder step", not rv_path.exists())
        w.ensure_real_validation_placeholder()
        check("placeholder step creates a genuinely empty file when absent", rv_path.exists() and rv_path.stat().st_size == 0)

        w.ensure_real_validation_placeholder()
        check("placeholder step is a no-op when the file already exists (empty)", rv_path.stat().st_size == 0)

        rv_path.write_bytes(b"not empty")
        w.ensure_real_validation_placeholder()
        check("placeholder step never overwrites an existing non-empty file", rv_path.read_bytes() == b"not empty")
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
# git state, never the real repo.
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
# verify_package_commit -- real scratch git repository, adapted for this
# package's seven-file set and pinned parent commit.
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
    "training/pkg_c.json": "c",
    "training/pkg_d.json": "d",
    "training/pkg_e.py": "e",
    "training/pkg_f.py": "f",
    "training/pkg_g.json": "g",
}

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    make_scratch_repo(tmp_path)
    parent_hash = commit_files(tmp_path, {"README.md": "parent"}, "parent commit (stand-in for the corpus-implementation milestone)")

    _orig_repo_root = w.REPO_ROOT
    _orig_pinned_parent = w.PINNED_PARENT_COMMIT
    _orig_expected_files = w.EXPECTED_PACKAGE_COMMIT_FILES
    w.REPO_ROOT = tmp_path
    w.PINNED_PARENT_COMMIT = parent_hash
    w.EXPECTED_PACKAGE_COMMIT_FILES = frozenset(TEST_PACKAGE_FILES)
    try:
        state = w.git_state()
        msg = expect_system_exit(w.verify_package_commit, state)
        check("remaining at the parent commit (package not yet committed) fails closed", msg is not None)

        commit_files(tmp_path, TEST_PACKAGE_FILES, "add the reviewed package")
        state = w.git_state()
        msg = expect_system_exit(w.verify_package_commit, state)
        check("a direct child commit containing exactly the expected seven files passes", msg is None, detail=str(msg))
    finally:
        w.REPO_ROOT = _orig_repo_root
        w.PINNED_PARENT_COMMIT = _orig_pinned_parent
        w.EXPECTED_PACKAGE_COMMIT_FILES = _orig_expected_files

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    make_scratch_repo(tmp_path)
    parent_hash = commit_files(tmp_path, {"README.md": "parent"}, "parent commit")
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
# bootstrap_clean_tree_then_real_validation -- real scratch git repositories.
# Unchanged design from the prior wrapper.
# ---------------------------------------------------------------------------

print("\n=== bootstrap_clean_tree_then_real_validation (real scratch git repositories) ===")

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    make_scratch_repo(tmp_path)
    (tmp_path / "datasets").mkdir()
    (tmp_path / "datasets" / ".gitignore").write_text("real_validation.jsonl\n", encoding="utf-8")
    commit_files(tmp_path, {"README.md": "x"}, "initial commit with nested gitignore (mirrors the real repository)")
    (tmp_path / "training").mkdir()

    _orig_repo_root, _orig_training_dir, _orig_rv_rel = w.REPO_ROOT, w.TRAINING_DIR, w.REAL_VALIDATION_REL_PATH
    w.REPO_ROOT = tmp_path
    w.TRAINING_DIR = tmp_path / "training"
    w.REAL_VALIDATION_REL_PATH = "../datasets/real_validation.jsonl"
    try:
        state = w.git_state()
        check("fresh checkout with nested gitignore starts clean", state["working_tree_clean"])
        msg = expect_system_exit(w.bootstrap_clean_tree_then_real_validation, state)
        check("corrected sequence succeeds when the path is gitignore-protected (matches the real repo)", msg is None, detail=str(msg))
        check("placeholder file was created, genuinely empty", (tmp_path / "datasets" / "real_validation.jsonl").read_bytes() == b"")
    finally:
        w.REPO_ROOT, w.TRAINING_DIR, w.REAL_VALIDATION_REL_PATH = _orig_repo_root, _orig_training_dir, _orig_rv_rel

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    make_scratch_repo(tmp_path)
    commit_files(tmp_path, {"README.md": "x"}, "initial commit, NO gitignore protection for real_validation.jsonl")
    (tmp_path / "training").mkdir()

    _orig_repo_root, _orig_training_dir, _orig_rv_rel = w.REPO_ROOT, w.TRAINING_DIR, w.REAL_VALIDATION_REL_PATH
    w.REPO_ROOT = tmp_path
    w.TRAINING_DIR = tmp_path / "training"
    w.REAL_VALIDATION_REL_PATH = "../real_validation.jsonl"
    try:
        state = w.git_state()
        check("fresh checkout without gitignore protection also starts clean", state["working_tree_clean"])
        msg = expect_system_exit(w.bootstrap_clean_tree_then_real_validation, state)
        check(
            "corrected sequence still succeeds even WITHOUT gitignore protection -- proves the "
            "ordering itself, not the gitignore entry, is what makes this safe",
            msg is None, detail=str(msg),
        )
    finally:
        w.REPO_ROOT, w.TRAINING_DIR, w.REAL_VALIDATION_REL_PATH = _orig_repo_root, _orig_training_dir, _orig_rv_rel

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    make_scratch_repo(tmp_path)
    commit_files(tmp_path, {"README.md": "x"}, "initial commit")
    (tmp_path / "training").mkdir()
    (tmp_path / "unrelated_dirty_file.txt").write_text("uncommitted, unrelated to real_validation.jsonl entirely", encoding="utf-8")

    _orig_repo_root, _orig_training_dir, _orig_rv_rel = w.REPO_ROOT, w.TRAINING_DIR, w.REAL_VALIDATION_REL_PATH
    w.REPO_ROOT = tmp_path
    w.TRAINING_DIR = tmp_path / "training"
    w.REAL_VALIDATION_REL_PATH = "../real_validation.jsonl"
    try:
        state = w.git_state()
        check("an unrelated uncommitted file makes the fresh checkout dirty", not state["working_tree_clean"])
        msg = expect_system_exit(w.bootstrap_clean_tree_then_real_validation, state)
        check("dirty tree from an unrelated cause still fails closed -- rejection is not weakened by the reordering", msg is not None)
        check("placeholder was NOT created -- clean-tree verification ran and failed BEFORE any mutation", not (tmp_path / "real_validation.jsonl").exists())
    finally:
        w.REPO_ROOT, w.TRAINING_DIR, w.REAL_VALIDATION_REL_PATH = _orig_repo_root, _orig_training_dir, _orig_rv_rel


# ---------------------------------------------------------------------------
# resolve_experiment_dir
# ---------------------------------------------------------------------------

print("\n=== resolve_experiment_dir ===")

check("default (None) resolves under TRAINING_DIR", w.resolve_experiment_dir(None) == w.TRAINING_DIR / "controlled_seed17_regression_balanced_repair_run")

relative_result = w.resolve_experiment_dir("some/relative/path")
check("a relative path resolves against TRAINING_DIR, not the cwd", relative_result == w.TRAINING_DIR / "some" / "relative" / "path")

absolute_under = str(w.TRAINING_DIR / "already_absolute_and_under")
check("an absolute path already under TRAINING_DIR passes through", w.resolve_experiment_dir(absolute_under) == Path(absolute_under))

msg = expect_system_exit(w.resolve_experiment_dir, "C:\\definitely\\outside\\training_dir_entirely")
check("an absolute path outside TRAINING_DIR fails with a controlled diagnostic, not a raw traceback", msg is not None)

resolved = w.resolve_experiment_dir("relative_dir_for_build_commands_test")
try:
    _ = w.build_commands(resolved / "treatment", resolved / "comparator")
    check("build_commands() does not raise for a resolved relative --experiment-dir", True)
except ValueError as e:
    check("build_commands() does not raise for a resolved relative --experiment-dir", False, detail=str(e))


# ---------------------------------------------------------------------------
# verify_arm_split_and_fingerprint -- synthetic files, both arm shapes
# (treatment: 85/79/6; comparator: 78/72/6)
# ---------------------------------------------------------------------------

print("\n=== verify_arm_split_and_fingerprint ===")


def make_pair_bytes(n: int, prefix: str) -> bytes:
    return b"".join((json.dumps({"prompt": f"{prefix}-{i}", "target": f"t{i}"}) + "\n").encode("utf-8") for i in range(n))


treatment_candidate_bytes = make_pair_bytes(85, "cand")
treatment_train_bytes = make_pair_bytes(79, "train")
treatment_val_bytes = make_pair_bytes(6, "val")
synthetic_treatment_fp = w.canonical_training_data_fingerprint(
    [json.loads(l) for l in treatment_train_bytes.decode().splitlines() if l.strip()]
    + [json.loads(l) for l in treatment_val_bytes.decode().splitlines() if l.strip()]
)
synthetic_canonical = {
    "candidate.jsonl": treatment_candidate_bytes,
    "train.jsonl": treatment_train_bytes,
    "val.jsonl": treatment_val_bytes,
}

msg = expect_system_exit(
    w.verify_arm_split_and_fingerprint, synthetic_canonical, "candidate.jsonl", "train.jsonl", "val.jsonl",
    85, 79, 6, synthetic_treatment_fp, "synthetic-treatment",
)
check("correct 85/79/6 split with matching fingerprint passes", msg is None, detail=str(msg))

msg = expect_system_exit(
    w.verify_arm_split_and_fingerprint, synthetic_canonical, "candidate.jsonl", "train.jsonl", "val.jsonl",
    85, 79, 6, "0" * 64, "synthetic-treatment",
)
check("training-data fingerprint mismatch fails closed", msg is not None)

msg = expect_system_exit(
    w.verify_arm_split_and_fingerprint, synthetic_canonical, "candidate.jsonl", "train.jsonl", "val.jsonl",
    85, 78, 6, synthetic_treatment_fp, "synthetic-treatment",
)
check("wrong expected train count fails closed", msg is not None)

msg = expect_system_exit(
    w.verify_arm_split_and_fingerprint, synthetic_canonical, "candidate.jsonl", "train.jsonl", "val.jsonl",
    84, 79, 6, synthetic_treatment_fp, "synthetic-treatment",
)
check("wrong expected candidate count fails closed", msg is not None)


# ---------------------------------------------------------------------------
# verify_treatment_candidate_equals_comparator_plus_delta -- NEW for this
# package. Synthetic comparator/treatment/proposal triples.
# ---------------------------------------------------------------------------

print("\n=== verify_treatment_candidate_equals_comparator_plus_delta ===")


def make_candidate_record_bytes(inp: str) -> bytes:
    return (json.dumps({"category": "x", "difficulty": "hard", "input": inp, "output": {}, "v1_target": "t1", "v2_target": "t2"}) + "\n").encode("utf-8")


def make_proposal_record_bytes(inp: str) -> bytes:
    return (json.dumps({"category": "x", "difficulty": "hard", "input": inp, "output": {}}) + "\n").encode("utf-8")


synthetic_comparator_bytes = b"".join(make_candidate_record_bytes(f"comparator input {i}") for i in range(5))
synthetic_delta_inputs = [f"new record {i}" for i in range(3)]
synthetic_treatment_tail_bytes = b"".join(make_candidate_record_bytes(inp) for inp in synthetic_delta_inputs)
synthetic_treatment_bytes = synthetic_comparator_bytes + synthetic_treatment_tail_bytes
synthetic_proposal_bytes = b"".join(make_proposal_record_bytes(inp) for inp in synthetic_delta_inputs)

good_delta_canonical = {
    w.TREATMENT_CANDIDATE_REL: synthetic_treatment_bytes,
    w.COMPARATOR_CANDIDATE_REL: synthetic_comparator_bytes,
    w.TREATMENT_PROPOSAL_REL: synthetic_proposal_bytes,
}
msg = expect_system_exit(w.verify_treatment_candidate_equals_comparator_plus_delta, good_delta_canonical)
check("correct comparator-prefix + exact proposal-matching tail passes", msg is None, detail=str(msg))

drifted_prefix_bytes = synthetic_comparator_bytes.replace(b"comparator input 0", b"DRIFTED", 1) + synthetic_treatment_tail_bytes
bad_prefix_canonical = {**good_delta_canonical, w.TREATMENT_CANDIDATE_REL: drifted_prefix_bytes}
msg = expect_system_exit(w.verify_treatment_candidate_equals_comparator_plus_delta, bad_prefix_canonical)
check("a drifted comparator-prefix fails closed", msg is not None)

short_tail_bytes = synthetic_comparator_bytes + b"".join(make_candidate_record_bytes(inp) for inp in synthetic_delta_inputs[:-1])
bad_count_canonical = {**good_delta_canonical, w.TREATMENT_CANDIDATE_REL: short_tail_bytes}
msg = expect_system_exit(w.verify_treatment_candidate_equals_comparator_plus_delta, bad_count_canonical)
check("a tail with the wrong record count fails closed", msg is not None)

reordered_tail_bytes = synthetic_comparator_bytes + b"".join(make_candidate_record_bytes(inp) for inp in reversed(synthetic_delta_inputs))
bad_order_canonical = {**good_delta_canonical, w.TREATMENT_CANDIDATE_REL: reordered_tail_bytes}
msg = expect_system_exit(w.verify_treatment_candidate_equals_comparator_plus_delta, bad_order_canonical)
check("a tail whose records are reordered relative to the proposal fails closed", msg is not None)

wrong_text_tail_bytes = synthetic_comparator_bytes + b"".join(make_candidate_record_bytes(inp) for inp in ["not the proposal text"] * len(synthetic_delta_inputs))
bad_text_canonical = {**good_delta_canonical, w.TREATMENT_CANDIDATE_REL: wrong_text_tail_bytes}
msg = expect_system_exit(w.verify_treatment_candidate_equals_comparator_plus_delta, bad_text_canonical)
check("a tail whose input text does not match the proposal fails closed", msg is not None)


# ---------------------------------------------------------------------------
# verify_treatment_proposal_membership -- synthetic proposal/train/val/
# comparator quadruples. 7-record proposal count; includes the new
# comparator-absence dimension.
# ---------------------------------------------------------------------------

print("\n=== verify_treatment_proposal_membership ===")

import prompt_contract_v2_candidate as _v2c

proposal_records = [
    {"input": f"proposal input {i}", "output": {"narrative": "n", "bullets": ["b"], "action_items": []}, "difficulty": "hard", "category": "test"}
    for i in range(w.TREATMENT_EXPECTED_PROPOSAL_COUNT)
]
proposal_bytes = b"".join((json.dumps(r) + "\n").encode("utf-8") for r in proposal_records)
proposal_prompts = [_v2c.build_prompt(r["input"]) for r in proposal_records]

good_train_bytes = b"".join((json.dumps({"prompt": p, "target": "t"}) + "\n").encode("utf-8") for p in proposal_prompts + ["unrelated train prompt"])
good_val_bytes = b"".join((json.dumps({"prompt": p, "target": "t"}) + "\n").encode("utf-8") for p in ["unrelated val prompt"])
good_comparator_train_bytes = b"".join((json.dumps({"prompt": p, "target": "t"}) + "\n").encode("utf-8") for p in ["unrelated comparator train prompt"])
good_comparator_val_bytes = b"".join((json.dumps({"prompt": p, "target": "t"}) + "\n").encode("utf-8") for p in ["unrelated comparator val prompt"])

good_canonical = {
    w.TREATMENT_PROPOSAL_REL: proposal_bytes,
    w.TREATMENT_TRAIN_REL: good_train_bytes,
    w.TREATMENT_VAL_REL: good_val_bytes,
    w.COMPARATOR_TRAIN_REL: good_comparator_train_bytes,
    w.COMPARATOR_VAL_REL: good_comparator_val_bytes,
}
msg = expect_system_exit(w.verify_treatment_proposal_membership, good_canonical)
check("all proposal records in train, none in val, none in comparator passes", msg is None, detail=str(msg))

missing_one_train_bytes = b"".join((json.dumps({"prompt": p, "target": "t"}) + "\n").encode("utf-8") for p in proposal_prompts[1:])
bad_canonical_missing = {**good_canonical, w.TREATMENT_TRAIN_REL: missing_one_train_bytes}
msg = expect_system_exit(w.verify_treatment_proposal_membership, bad_canonical_missing)
check("a proposal record absent from train fails closed", msg is not None)

leaked_val_bytes = good_val_bytes + (json.dumps({"prompt": proposal_prompts[0], "target": "t"}) + "\n").encode("utf-8")
bad_canonical_leak = {**good_canonical, w.TREATMENT_VAL_REL: leaked_val_bytes}
msg = expect_system_exit(w.verify_treatment_proposal_membership, bad_canonical_leak)
check("a proposal record present in treatment val fails closed", msg is not None)

leaked_comparator_train_bytes = good_comparator_train_bytes + (json.dumps({"prompt": proposal_prompts[0], "target": "t"}) + "\n").encode("utf-8")
bad_canonical_comparator_leak_train = {**good_canonical, w.COMPARATOR_TRAIN_REL: leaked_comparator_train_bytes}
msg = expect_system_exit(w.verify_treatment_proposal_membership, bad_canonical_comparator_leak_train)
check("a proposal record present in comparator train fails closed (NEW check)", msg is not None)

leaked_comparator_val_bytes = good_comparator_val_bytes + (json.dumps({"prompt": proposal_prompts[-1], "target": "t"}) + "\n").encode("utf-8")
bad_canonical_comparator_leak_val = {**good_canonical, w.COMPARATOR_VAL_REL: leaked_comparator_val_bytes}
msg = expect_system_exit(w.verify_treatment_proposal_membership, bad_canonical_comparator_leak_val)
check("a proposal record present in comparator val fails closed (NEW check)", msg is not None)


# ---------------------------------------------------------------------------
# verify_benchmark_counts
# ---------------------------------------------------------------------------

print("\n=== verify_benchmark_counts ===")


def make_bench_bytes(n: int, prefix: str) -> bytes:
    return b"".join((json.dumps({"id": f"{prefix}{i:02d}", "input": f"x{i}"}) + "\n").encode("utf-8") for i in range(n))


good_bench_canonical = {
    w.PROTECTED_BENCHMARK_REL: make_bench_bytes(16, "p"),
    w.ACCEPTANCE_BENCHMARK_REL: make_bench_bytes(10, "a"),
}
msg = expect_system_exit(w.verify_benchmark_counts, good_bench_canonical)
check("correct 16/10 benchmark counts pass", msg is None, detail=str(msg))

msg = expect_system_exit(w.verify_benchmark_counts, {**good_bench_canonical, w.PROTECTED_BENCHMARK_REL: make_bench_bytes(15, "p")})
check("wrong protected count fails closed", msg is not None)

msg = expect_system_exit(w.verify_benchmark_counts, {**good_bench_canonical, w.ACCEPTANCE_BENCHMARK_REL: make_bench_bytes(9, "a")})
check("wrong acceptance count fails closed", msg is not None)

dup_ids_canonical = {
    w.PROTECTED_BENCHMARK_REL: make_bench_bytes(16, "p"),
    w.ACCEPTANCE_BENCHMARK_REL: make_bench_bytes(10, "p"),
}
msg = expect_system_exit(w.verify_benchmark_counts, dup_ids_canonical)
check("duplicate IDs across protected/acceptance fail closed", msg is not None)


# ---------------------------------------------------------------------------
# build_commands / verify_command_shape -- both arms symmetric
# ---------------------------------------------------------------------------

print("\n=== build_commands / verify_command_shape ===")

treatment_dir = w.TRAINING_DIR / "x_test_treatment"
comparator_dir = w.TRAINING_DIR / "x_test_comparator"
commands = w.build_commands(treatment_dir, comparator_dir)

check("treatment_train has --max-steps 720", "--max-steps" in commands["treatment_train"] and "720" in commands["treatment_train"])
check("comparator_train has --max-steps 720", "--max-steps" in commands["comparator_train"] and "720" in commands["comparator_train"])
check("treatment_train resolves to the regression-balanced-repair data dir", w.TREATMENT_DATA_DIR_REL in commands["treatment_train"])
check("comparator_train resolves to the historical data dir", w.COMPARATOR_DATA_DIR_REL in commands["comparator_train"])
msg = expect_system_exit(w.verify_command_shape, commands)
check("correctly-shaped commands pass verify_command_shape", msg is None, detail=str(msg))

broken_missing_maxsteps = {**commands, "treatment_train": [a for a in commands["treatment_train"] if a not in ("--max-steps", "720")]}
msg = expect_system_exit(w.verify_command_shape, broken_missing_maxsteps)
check("treatment command missing --max-steps entirely fails closed", msg is not None)

broken_wrong_value = {**commands, "comparator_train": [a if a != "720" else "719" for a in commands["comparator_train"]]}
msg = expect_system_exit(w.verify_command_shape, broken_wrong_value)
check("comparator command with wrong --max-steps value fails closed", msg is not None)

broken_duplicate_maxsteps = {**commands, "treatment_train": commands["treatment_train"] + ["--max-steps", "720"]}
msg = expect_system_exit(w.verify_command_shape, broken_duplicate_maxsteps)
check("duplicate --max-steps argument fails closed", msg is not None)

broken_wrong_seed = {**commands, "treatment_train": [a if a != "17" else "42" for a in commands["treatment_train"]]}
msg = expect_system_exit(w.verify_command_shape, broken_wrong_seed)
check("command not resolving to seed 17 fails closed", msg is not None)

swapped_data_dir = [w.COMPARATOR_DATA_DIR_REL if a == w.TREATMENT_DATA_DIR_REL else a for a in commands["treatment_train"]]
broken_swapped = {**commands, "treatment_train": swapped_data_dir}
msg = expect_system_exit(w.verify_command_shape, broken_swapped)
check("treatment command pointed at the comparator's data dir fails closed", msg is not None)

collide_out = {**commands, "comparator_train": [a if a != str((comparator_dir / "checkpoint").relative_to(w.TRAINING_DIR)) else str((treatment_dir / "checkpoint").relative_to(w.TRAINING_DIR)) for a in commands["comparator_train"]]}
msg = expect_system_exit(w.verify_command_shape, collide_out)
check("treatment/comparator output-directory collision fails closed", msg is not None)


# ---------------------------------------------------------------------------
# verify_completed_steps -- unchanged design, reused directly
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
    (output_dir / "checkpoint-720").mkdir()
    msg = expect_system_exit(w.verify_completed_steps, output_dir, 720, "test-run")
    check("checkpoint dir missing trainer_state.json fails closed", msg is not None)


# ---------------------------------------------------------------------------
# verify_raw_result_artifact -- signature takes benchmark_records directly
# (already-canonicalized), not a path.
# ---------------------------------------------------------------------------

print("\n=== verify_raw_result_artifact ===")

BENCH_PRIMARY_CHECKS = {"01": ["CHECK_A", "CHECK_B"], "02": ["CHECK_C"], "03": []}
BENCH_RECORDS = [{"id": rid, "input": f"input {rid}", "primary_checks": checks} for rid, checks in BENCH_PRIMARY_CHECKS.items()]


def make_result_record(rid, raw_output="some generated text", scores=None, capability_checks=None, failure_labels=None) -> dict:
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

    valid_path = tmp_path / "valid_results.json"
    valid_path.write_text(json.dumps([make_result_record(r) for r in ("01", "02", "03")]), encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, valid_path, BENCH_RECORDS, 3, "test")
    check("valid, complete, correctly-ordered, unscored result (incl. a zero-check probe) passes", msg is None, detail=str(msg))

    missing_path = tmp_path / "does_not_exist.json"
    msg = expect_system_exit(w.verify_raw_result_artifact, missing_path, BENCH_RECORDS, 3, "test")
    check("missing result file fails closed", msg is not None)

    malformed_path = tmp_path / "malformed.json"
    malformed_path.write_text("{not valid json", encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, malformed_path, BENCH_RECORDS, 3, "test")
    check("malformed (unparseable) result file fails closed", msg is not None)

    wrong_count_path = tmp_path / "wrong_count.json"
    wrong_count_path.write_text(json.dumps([make_result_record(r) for r in ("01", "02")]), encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, wrong_count_path, BENCH_RECORDS, 3, "test")
    check("wrong record count fails closed", msg is not None)

    reordered_path = tmp_path / "reordered.json"
    reordered_path.write_text(json.dumps([make_result_record(r) for r in ("02", "01", "03")]), encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, reordered_path, BENCH_RECORDS, 3, "test")
    check("reordered IDs fail closed", msg is not None)

    empty_raw_path = tmp_path / "empty_raw.json"
    recs = [make_result_record(r) for r in ("01", "02", "03")]
    recs[1]["raw_output"] = ""
    empty_raw_path.write_text(json.dumps(recs), encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, empty_raw_path, BENCH_RECORDS, 3, "test")
    check("empty raw_output on one record fails closed", msg is not None)

    prescored_path = tmp_path / "prescored.json"
    recs = [make_result_record(r) for r in ("01", "02", "03")]
    recs[0]["scores"] = {**{k: None for k in w.EXPECTED_SCORE_KEYS}, "topic_completeness": 2}
    prescored_path.write_text(json.dumps(recs), encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, prescored_path, BENCH_RECORDS, 3, "test")
    check("a record with a semantic score already filled fails closed", msg is not None)

    not_a_list_path = tmp_path / "not_a_list.json"
    not_a_list_path.write_text(json.dumps({"not": "a list"}), encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, not_a_list_path, BENCH_RECORDS, 3, "test")
    check("result file that is not a JSON array fails closed", msg is not None)

    prefilled_checks_path = tmp_path / "prefilled_checks.json"
    recs = [make_result_record(r) for r in ("01", "02", "03")]
    recs[0]["capability_checks"] = {"CHECK_A": True, "CHECK_B": None}
    prefilled_checks_path.write_text(json.dumps(recs), encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, prefilled_checks_path, BENCH_RECORDS, 3, "test")
    check("a record with a capability_check already filled fails closed", msg is not None)

    nonempty_labels_path = tmp_path / "nonempty_labels.json"
    recs = [make_result_record(r) for r in ("01", "02", "03")]
    recs[0]["failure_labels"] = ["Topic Loss"]
    nonempty_labels_path.write_text(json.dumps(recs), encoding="utf-8")
    msg = expect_system_exit(w.verify_raw_result_artifact, nonempty_labels_path, BENCH_RECORDS, 3, "test")
    check("a record with a non-empty failure_labels fails closed", msg is not None)

# Cross-check against a real, previously-generated raw artifact from an
# actual prior seed-17 replay run (same 16-probe protected benchmark
# content, unscored scaffold shape) -- proves this function still accepts
# genuine real-world output, not just synthetic fixtures. Corpus-agnostic
# check: unaffected by which package generated the raw file.
real_protected_path = w.TRAINING_DIR / "controlled_seed17_phase2_replay_run" / "primary" / "protected16_results.json"
if real_protected_path.exists():
    canonical = w.canonicalize_pinned_lf_bytes(
        (w.TRAINING_DIR / w.PROTECTED_BENCHMARK_REL).read_bytes(),
        w.CANONICAL_LF_GOVERNING_INPUTS[w.PROTECTED_BENCHMARK_REL],
        "protected16 (live)",
    )
    real_benchmark_records = w.parse_jsonl_records_from_bytes(canonical)
    msg = expect_system_exit(w.verify_raw_result_artifact, real_protected_path, real_benchmark_records, 16, "real-untampered")
    check("a real, genuinely-unscored protected-16 artifact from a prior wrapper still passes", msg is None, detail=str(msg))

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        real_results = json.loads(real_protected_path.read_text(encoding="utf-8"))
        tampered = json.loads(json.dumps(real_results))
        first_checks = tampered[0]["capability_checks"]
        tampered[0]["capability_checks"] = {(next(iter(first_checks)) if first_checks else "FAKE_CHECK"): True}
        tampered[0]["failure_labels"] = ["Topic Loss"]
        tampered_path = tmp_path / "tampered_real.json"
        tampered_path.write_text(json.dumps(tampered), encoding="utf-8")
        msg = expect_system_exit(w.verify_raw_result_artifact, tampered_path, real_benchmark_records, 16, "real-repro")
        check("a tampered real protected-16 artifact fails closed", msg is not None)


# ---------------------------------------------------------------------------
# create_exclusive_experiment_dir / run_logged_subprocess / require_success
# -- unchanged design, reused directly
# ---------------------------------------------------------------------------

print("\n=== create_exclusive_experiment_dir ===")

with tempfile.TemporaryDirectory() as tmp:
    fresh = Path(tmp) / "fresh_root"
    result = w.create_exclusive_experiment_dir(fresh)
    check("fresh directory creates cleanly", result == fresh and fresh.is_dir())

    msg = expect_system_exit(w.create_exclusive_experiment_dir, fresh)
    check("re-creating an existing directory fails closed", msg is not None)


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

fresh_experiment_dir = w.TRAINING_DIR / "x_test_dryrun_experiment_root"
assert not fresh_experiment_dir.exists(), "test fixture collision -- pick a different throwaway name"
try:
    result = subprocess.run(
        [sys.executable, str(w.TRAINING_DIR / "run_seed17_regression_balanced_repair.py"), "--experiment-dir", str(fresh_experiment_dir)],
        cwd=w.TRAINING_DIR,
        capture_output=True,
        text=True,
    )
    check("dry-run exits 0", result.returncode == 0, detail=result.stderr[-500:])
    check("dry-run prints all 6 planned commands", result.stdout.count("$ ") == 6)
    check("dry-run's two training commands both show --max-steps 720", result.stdout.count("--max-steps 720") == 2)
    check("dry-run mentions --confirm-execute", "--confirm-execute" in result.stdout)
    check("dry-run creates NO experiment directory", not fresh_experiment_dir.exists())
    check("dry-run performs NO real-validation placeholder creation (setup step is inside --confirm-execute only)", "real-validation placeholder" not in result.stdout)
finally:
    if fresh_experiment_dir.exists():
        import shutil

        shutil.rmtree(fresh_experiment_dir)


# ---------------------------------------------------------------------------
# verify_frozen_executable_code -- synthetic closure-set-drift and
# canonicalization coverage first, then the real scratch-repository
# regression that reproduces the checkout-vs-blob failure mode a real
# execution attempt against the prior package originally found.
# ---------------------------------------------------------------------------

print("\n=== verify_frozen_executable_code (synthetic closure + canonicalization) ===")

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    entry_lf = b"import mid\nimport os\n"
    mid_lf = b"import leaf\nimport sys\n"
    leaf_lf = b"import json\n"
    (tmp_path / "entry.py").write_bytes(entry_lf)
    (tmp_path / "mid.py").write_bytes(mid_lf)
    (tmp_path / "leaf.py").write_bytes(leaf_lf)
    (tmp_path / "unrelated.py").write_bytes(b"import re\n")

    _orig_training_dir, _orig_entry_points = w.TRAINING_DIR, w.EXECUTABLE_CODE_ENTRY_POINTS
    w.TRAINING_DIR = tmp_path
    w.EXECUTABLE_CODE_ENTRY_POINTS = ["entry.py"]
    try:
        closure = w.compute_import_closure(["entry.py"])
        check("closure includes the entry point, a direct import, and a transitive import", closure == {"entry.py", "mid.py", "leaf.py"})
        check("closure excludes an unreferenced local file", "unrelated.py" not in closure)

        import hashlib as _hashlib

        lf_lock = {"executable_code": {
            "entry.py": _hashlib.sha256(entry_lf).hexdigest(),
            "mid.py": _hashlib.sha256(mid_lf).hexdigest(),
            "leaf.py": _hashlib.sha256(leaf_lf).hexdigest(),
        }}
        result = None
        try:
            result = w.verify_frozen_executable_code(lf_lock)
        except SystemExit as e:
            result = str(e)
        check(
            "LF checkout matches its own canonical pin and returns the exact canonical byte map",
            result == {"entry.py": entry_lf, "mid.py": mid_lf, "leaf.py": leaf_lf},
            detail=str(result),
        )

        (tmp_path / "entry.py").write_bytes(entry_lf.replace(b"\n", b"\r\n"))
        (tmp_path / "mid.py").write_bytes(mid_lf.replace(b"\n", b"\r\n"))
        (tmp_path / "leaf.py").write_bytes(leaf_lf.replace(b"\n", b"\r\n"))
        result = None
        try:
            result = w.verify_frozen_executable_code(lf_lock)
        except SystemExit as e:
            result = str(e)
        check(
            "uniform CRLF checkout of the same content still passes, canonicalizing to the LF pin",
            result == {"entry.py": entry_lf, "mid.py": mid_lf, "leaf.py": leaf_lf},
            detail=str(result),
        )
        (tmp_path / "entry.py").write_bytes(entry_lf)
        (tmp_path / "mid.py").write_bytes(mid_lf)
        (tmp_path / "leaf.py").write_bytes(leaf_lf)

        (tmp_path / "leaf.py").write_bytes(b"import json\nX = 'drifted content'\n")
        msg = expect_system_exit(w.verify_frozen_executable_code, lf_lock)
        check("content drift in a transitive module fails closed", msg is not None)
        (tmp_path / "leaf.py").write_bytes(leaf_lf)

        (tmp_path / "mid.py").write_bytes(b"import leaf\nimport newdep\nimport sys\n")
        (tmp_path / "newdep.py").write_bytes(b"X = 1\n")
        msg = expect_system_exit(w.verify_frozen_executable_code, lf_lock)
        check("a NEW transitive import (closure-set drift) fails closed", msg is not None)
        (tmp_path / "mid.py").write_bytes(mid_lf)
    finally:
        w.TRAINING_DIR, w.EXECUTABLE_CODE_ENTRY_POINTS = _orig_training_dir, _orig_entry_points


print("\n=== verify_frozen_executable_code (real scratch git repository, core.autocrlf=true, genuine `git worktree add`) ===")

with tempfile.TemporaryDirectory() as tmp:
    origin_path = Path(tmp) / "origin"
    worktree_path = Path(tmp) / "fresh_checkout"
    origin_path.mkdir()

    def run_git(*args, cwd):
        return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)

    run_git("init", "-q", cwd=origin_path)
    run_git("config", "user.email", "test@example.com", cwd=origin_path)
    run_git("config", "user.name", "Test", cwd=origin_path)
    run_git("config", "core.autocrlf", "true", cwd=origin_path)

    entry_lf = b"import mid\n"
    mid_lf = b"import json\n"
    (origin_path / "entry.py").write_bytes(entry_lf)
    (origin_path / "mid.py").write_bytes(mid_lf)
    run_git("add", "-A", cwd=origin_path)
    run_git("commit", "-q", "-m", "initial commit, LF-committed source", cwd=origin_path)
    commit_hash = run_git("rev-parse", "HEAD", cwd=origin_path).stdout.strip()

    run_git("worktree", "add", "--detach", str(worktree_path), commit_hash, cwd=origin_path)

    fresh_entry_bytes = (worktree_path / "entry.py").read_bytes()
    fresh_mid_bytes = (worktree_path / "mid.py").read_bytes()
    entry_cr_count = fresh_entry_bytes.count(b"\r")
    mid_cr_count = fresh_mid_bytes.count(b"\r")
    check(
        "genuine `git worktree add` under core.autocrlf=true actually materialized CRLF (precondition for this test to mean anything)",
        entry_cr_count > 0 and mid_cr_count > 0,
        detail=f"entry.py CR count={entry_cr_count}, mid.py CR count={mid_cr_count}",
    )
    check("the committed blob itself is pure LF (the checkout, not the storage, introduced CRLF)", entry_lf.count(b"\r") == 0 and mid_lf.count(b"\r") == 0)

    import hashlib as _hashlib

    real_worktree_lock = {"executable_code": {
        "entry.py": _hashlib.sha256(entry_lf).hexdigest(),
        "mid.py": _hashlib.sha256(mid_lf).hexdigest(),
    }}

    _orig_training_dir, _orig_entry_points = w.TRAINING_DIR, w.EXECUTABLE_CODE_ENTRY_POINTS
    w.TRAINING_DIR = worktree_path
    w.EXECUTABLE_CODE_ENTRY_POINTS = ["entry.py"]
    try:
        result = None
        try:
            result = w.verify_frozen_executable_code(real_worktree_lock)
        except SystemExit as e:
            result = str(e)
        check(
            "the verifier passes against a genuine fresh CRLF checkout, canonicalizing to the LF-committed pin",
            result == {"entry.py": entry_lf, "mid.py": mid_lf},
            detail=str(result),
        )
    finally:
        w.TRAINING_DIR, w.EXECUTABLE_CODE_ENTRY_POINTS = _orig_training_dir, _orig_entry_points
        run_git("worktree", "remove", "--force", str(worktree_path), cwd=origin_path)


# ---------------------------------------------------------------------------
# GATE6_REQUIRED_PASS_SET sanity
# ---------------------------------------------------------------------------

print("\n=== GATE6_REQUIRED_PASS_SET ===")

check("gate-6 pass set has exactly 13 probes", len(w.GATE6_REQUIRED_PASS_SET) == 13)
check(
    "gate-6 pass set matches every prior seed-17 replay package's pass set exactly (unchanged)",
    w.GATE6_REQUIRED_PASS_SET == frozenset({"01", "03", "04", "05", "06", "07", "09", "10", "12", "13", "14", "15", "16"}),
)
check("gate-6 pass set excludes 02, 08, 11", not ({"02", "08", "11"} & w.GATE6_REQUIRED_PASS_SET))


# ---------------------------------------------------------------------------
# Live checks against the real, pinned repository files
# ---------------------------------------------------------------------------

print("\n=== live checks against real pinned files ===")

lock = w.load_frozen_fingerprints()
real_executable_code_canonical = None
try:
    real_executable_code_canonical = w.verify_frozen_executable_code(lock)
except SystemExit as e:
    real_executable_code_canonical = str(e)
check(
    "real import closure (12 files) verifies clean against the real lock, checkout-portable",
    isinstance(real_executable_code_canonical, dict) and len(real_executable_code_canonical) == 12,
    detail=str(real_executable_code_canonical),
)
check(
    "returned canonical bytes are all genuinely LF (no CR), regardless of this checkout's own line endings",
    isinstance(real_executable_code_canonical, dict) and all(b"\r" not in data for data in real_executable_code_canonical.values()),
)

msg = expect_system_exit(w.verify_pinned_dependency_versions, lock)
check("real dependency versions verify clean", msg is None, detail=str(msg))

msg = expect_system_exit(w.verify_cuda_bfloat16_expectation)
check("real CUDA availability verifies clean", msg is None, detail=str(msg))

w.ensure_real_validation_placeholder()
real_canonical_inputs = None
try:
    real_canonical_inputs = w.load_canonical_governing_inputs()
except SystemExit as e:
    real_canonical_inputs = str(e)
check("all nine real governing inputs canonicalize cleanly, no manual normalization", isinstance(real_canonical_inputs, dict), detail=str(real_canonical_inputs))

if isinstance(real_canonical_inputs, dict):
    msg = expect_system_exit(w.verify_real_validation_empty)
    check("real real_validation.jsonl verifies byte-empty", msg is None, detail=str(msg))

    msg = expect_system_exit(w.verify_benchmark_counts, real_canonical_inputs)
    check("real benchmark counts (16/10) verify clean", msg is None, detail=str(msg))

    msg = expect_system_exit(
        w.verify_arm_split_and_fingerprint, real_canonical_inputs,
        w.TREATMENT_CANDIDATE_REL, w.TREATMENT_TRAIN_REL, w.TREATMENT_VAL_REL,
        w.TREATMENT_EXPECTED_CANDIDATE_COUNT, w.TREATMENT_EXPECTED_TRAIN_COUNT, w.TREATMENT_EXPECTED_VAL_COUNT,
        w.TREATMENT_EXPECTED_TRAINING_DATA_FINGERPRINT, "treatment",
    )
    check("real treatment split (85/79/6) and fingerprint verify clean", msg is None, detail=str(msg))

    msg = expect_system_exit(
        w.verify_arm_split_and_fingerprint, real_canonical_inputs,
        w.COMPARATOR_CANDIDATE_REL, w.COMPARATOR_TRAIN_REL, w.COMPARATOR_VAL_REL,
        w.COMPARATOR_EXPECTED_CANDIDATE_COUNT, w.COMPARATOR_EXPECTED_TRAIN_COUNT, w.COMPARATOR_EXPECTED_VAL_COUNT,
        w.COMPARATOR_EXPECTED_TRAINING_DATA_FINGERPRINT, "comparator",
    )
    check("real comparator split (78/72/6) and fingerprint verify clean", msg is None, detail=str(msg))

    msg = expect_system_exit(w.verify_treatment_candidate_equals_comparator_plus_delta, real_canonical_inputs)
    check("real treatment candidate == real comparator candidate + real 7-record delta, in order", msg is None, detail=str(msg))

    msg = expect_system_exit(w.verify_treatment_proposal_membership, real_canonical_inputs)
    check("real treatment proposal membership (7 records: train-only, absent from val AND comparator) verifies clean", msg is None, detail=str(msg))

real_commands = w.build_commands(
    w.TRAINING_DIR / "controlled_seed17_regression_balanced_repair_run" / "treatment",
    w.TRAINING_DIR / "controlled_seed17_regression_balanced_repair_run" / "comparator",
)
msg = expect_system_exit(w.verify_command_shape, real_commands)
check("real constructed commands verify clean", msg is None, detail=str(msg))

msg = expect_system_exit(w.verify_pinned_base_model_snapshot)
check("real base-model snapshot verifies clean", msg is None, detail=str(msg))

state = w.git_state()
check("HEAD currently matches origin/main (package built on a synced repo)", state["head_matches_origin_main"])

# verify_package_commit's expected outcome depends on whether this package
# has been committed yet -- adaptive rather than hardcoded to one state, so
# this suite stays correct whether run pre-commit (HEAD still IS the pinned
# parent) or post-commit (HEAD is a direct child whose delta is exactly the
# seven reviewed package files).
msg = expect_system_exit(w.verify_package_commit, state)
if state["head_commit"] == w.PINNED_PARENT_COMMIT:
    check("verify_package_commit correctly fails pre-commit (HEAD is still the parent, not a child)", msg is not None)
elif state["head_parent_commit"] == w.PINNED_PARENT_COMMIT:
    check("verify_package_commit correctly passes post-commit (HEAD is a direct child with exactly the reviewed delta)", msg is None, detail=str(msg))
else:
    check(f"verify_package_commit: unexpected repo state -- HEAD {state['head_commit']!r} is neither the pinned parent nor its direct child", False)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print(f"\n{'='*60}")
if FAILURES:
    print(f"{len(FAILURES)} check(s) FAILED: {FAILURES}")
    sys.exit(1)
else:
    print("All checks passed.")
