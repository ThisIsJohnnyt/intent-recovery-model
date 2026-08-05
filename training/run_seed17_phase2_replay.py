"""Execution wrapper for the controlled seed-17 Phase-2 replay
(training/phase2_seed17_replay_interpretation_and_outcome_matrix_chatgpt.md,
training/controlled_seed17_phase2_replay_frozen_manifest.md).

Authorized by Johnny 2026-08-04: "I authorize Claude to author the
uncommitted seed-17 Phase-2 replay package ... Claude may perform static
validation, dummy-subprocess tests, and dry-run receipt generation only."
This module performs no compute on import, and `main()` refuses to start
any real subprocess unless invoked with the explicit `--confirm-execute`
flag, which nothing in this codebase sets automatically. Possession of
that flag is not itself authorization -- Johnny must separately name this
exact replay after the committed package has passed joint review, exactly
as the R2 replay required before its own execution. No such run has been
performed as part of this change.

Runs two independent training + evaluation sequences from the same pinned
base-model snapshot, never resuming one from the other:

- primary: natural 40-epoch run, `--max-steps` omitted, expected exactly
  720 optimizer steps -- the sole decision-bearing Phase-2 candidate.
- control: step-matched diagnostic, `--max-steps=600`, expected exactly
  600 optimizer steps -- explains step-budget sensitivity, never a
  post-hoc substitute for the primary.

Extends training/run_seed17_r2_replay.py's already-reviewed design
(pinned base-model snapshot verified via the local HF cache only, never
network; interruption-safe logging via an exclusively-opened log file
passed directly as subprocess stdout, never a shell pipe or in-memory
buffer; atomic `exist_ok=False` experiment-directory creation; a
pre-execution receipt written before any subprocess starts; an external
fingerprint lock so this file's own hash can be pinned without the
self-reference problem) with the requirements specific to this package,
per the governing document's Section 4:

1. Full local import-closure fingerprinting (Section 4.1): the executable-
   code lock is no longer a manually curated list. compute_import_closure()
   statically parses the AST of the wrapper, train.py, run_benchmark.py,
   and report_benchmark.py, then recursively follows every repo-local
   `import`/`from` statement it finds, so a new local import added to any
   file in the closure is caught automatically -- both because the
   computed *file set* itself would differ from the lock's frozen set, and
   because the new file's content would be unpinned.
2. Byte-empty datasets/real_validation.jsonl preflight (Section 4.1):
   train.py always calls evaluate_real_validation.run_real_validation_evaluation
   after training, which reads this exact file; a nonempty file fails
   closed rather than silently letting undeclared private-data inference
   into a replay whose authorized evaluation scope is only the frozen 26
   benchmark cases.
3. Independent run initialization (Section 3): both runs load the base
   model fresh via train.py's own `AutoModelForSeq2SeqLM.from_pretrained`
   call; neither command references the other run's checkpoint directory
   anywhere.
4. Artifact isolation (Section 4.2): primary/ and control/ are separate
   subdirectories of one atomically-created experiment root, each with its
   own checkpoint directory, result files, and logs.
5. Exact step-count verification (Section 4.2): verify_completed_steps()
   reads the highest-numbered `checkpoint-N/trainer_state.json` Trainer
   itself writes during training (per `save_strategy="epoch"`) and requires
   `global_step` to equal exactly the expected total -- a clean subprocess
   exit code alone is not sufficient.
6. Gate 6's explicit pass set (Section 5.1) is encoded here as data
   (GATE6_REQUIRED_PASS_SET) for later scoring-verification tooling to
   import, not re-derived from the reporter's generic regression-warning
   line, which prior verification showed can over-flag already-failing
   probes.

Revised 2026-08-04 per ChatGPT's review of the first draft, all three
findings independently reproduced before fixing:

7. **BLOCKER, fixed**: preflight originally required `HEAD == <the commit
   this package was built against>`, but committing this very package
   necessarily advances HEAD past that commit -- the committed package
   could never have passed its own preflight. `PINNED_PARENT_COMMIT`
   (renamed from `PINNED_HEAD_COMMIT`) is now the required *parent* of
   HEAD, not a value HEAD itself must equal; `verify_package_commit()`
   requires HEAD to be a direct child of it whose delta contains exactly
   `EXPECTED_PACKAGE_COMMIT_FILES` (the six reviewed package files, no
   more, no less) -- catching both an incompletely-committed package and
   an unreviewed file riding along in the same commit. The receipt now
   also records `package_commit` as an explicit top-level field for the
   later execution authorization to name.
8. **Fixed**: raw benchmark result artifacts were never validated beyond
   the subprocess's own exit code. `verify_raw_result_artifact()` now
   runs after each of the four evaluation subprocesses and fails closed
   unless the result file exists, parses as a JSON array, has exactly the
   expected record count, its IDs appear in exactly the benchmark file's
   own order, every record has a non-empty `raw_output`, and no record's
   semantic score fields are filled -- per the governing document's
   Section 6.1, a missing or invalid raw result is itself an invalid
   experiment (P2-X), not something to discover only later during
   scoring.
9. The governing document (`phase2_seed17_replay_interpretation_and_outcome_matrix_chatgpt.md`)
   was re-saved byte-faithfully after ChatGPT found the first save had
   silently stripped trailing markdown hard-line-break spaces on four
   header lines -- confirmed by hashing a fresh re-paste, which matched
   ChatGPT's claimed hash exactly.

Revised again 2026-08-04 per ChatGPT's second-pass review, one more real
gap found and fixed:

10. **verify_raw_result_artifact() only checked `scores`.** ChatGPT
    reproduced this directly against a real protected-16 raw artifact: a
    record with one `capability_checks` value set to `true` and a
    non-empty `failure_labels` still passed as "no semantic scores
    filled." Independently reproduced the exact same way before fixing.
    Now also requires `capability_checks` keys to exactly match that
    specific probe's own `primary_checks` from the benchmark file (some
    probes, e.g. protected 13-16, legitimately have zero primary_checks
    and an empty capability_checks dict -- confirmed directly against the
    real benchmark file, not assumed), every capability-check value null,
    and `failure_labels` exactly `[]`. `scores` itself is now also
    required to have exactly the four expected dimension keys (confirmed
    identical across every protected and acceptance probe), not just
    all-null values under whatever keys happened to be present.

Usage:
    python run_seed17_phase2_replay.py [--confirm-execute] [--experiment-dir DIR]
"""
import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TRAINING_DIR = Path(__file__).parent
REPO_ROOT = TRAINING_DIR.parent
FROZEN_FINGERPRINTS_PATH = TRAINING_DIR / "controlled_seed17_phase2_replay_frozen_fingerprints.json"

# The commit this package was built against -- the milestone named in the
# governing document's own header. This is the PARENT of the eventual
# package commit, never a value HEAD itself is required to equal:
# committing this package necessarily advances HEAD past this commit, so a
# check requiring HEAD == this value would make the committed package
# permanently unable to pass its own preflight (ChatGPT's finding,
# 2026-08-04, independently confirmed by re-reading this exact code before
# fixing). Preflight instead requires HEAD to be a direct child of this
# commit whose delta contains exactly the reviewed package files -- see
# verify_package_commit().
PINNED_PARENT_COMMIT = "d90fc13add15be1ce67ea7b2bb4429e978305e74"

# The exact files this package's own commit is authorized to add on top of
# PINNED_PARENT_COMMIT -- nothing more, nothing less. Paths are repo-root-
# relative, matching `git diff --name-only` output.
EXPECTED_PACKAGE_COMMIT_FILES = frozenset({
    "training/phase2_seed17_replay_interpretation_and_outcome_matrix_chatgpt.md",
    "training/controlled_seed17_phase2_replay_frozen_manifest.md",
    "training/controlled_seed17_phase2_replay_frozen_fingerprints.json",
    "training/run_seed17_phase2_replay.py",
    "training/test_run_seed17_phase2_replay.py",
    "training/controlled_seed17_phase2_replay_manifest_dryrun_receipt_sample.json",
})

HF_REPO_ID = "google/flan-t5-base"
PINNED_BASE_MODEL_REVISION = "7bcac572ce56db69c1ea7c8af255c5d7c9672fc2"
# Unchanged from the R2 replay -- same base model, same pinned snapshot,
# independently reverified against the local HF cache in this round (not
# copied without re-checking).
PINNED_BASE_MODEL_FILE_FINGERPRINTS = {
    "config.json": "7c1853dbfa0e4aac093eb109a358b6ab25fe86b7c15185a91322f0ed26f0f940",
    "generation_config.json": "f5a1c7e2be8092018d8835128987edf0111637dd98e90599cc80310fef75d95a",
    "model.safetensors": "1dfb70afdcedceb9f9fae2f9b68e004ad934361fb35b9b2bd50b45ea90790fc8",
    "special_tokens_map.json": "5c87151ef0f72a99d1f766a4c418bd2a1f90aaa30a8e22fe5eca9641daebb64f",
    "spiece.model": "d60acb128cf7b7f2536e8f38a5b18a05535c9e14c7a355904270e15b0945ea86",
    "tokenizer.json": "fe2ebbbbde2985be723e0ce18217853e4020c5e9d35bd07be2c27ab9d3ead57a",
    "tokenizer_config.json": "4c55124402e4ce48c7125d04b9af152a125eda9e7c80829f8f99f2ec69f3f68d",
}

# Entry points the import closure is computed FROM, not a list of the
# closure itself -- see compute_import_closure(). Both evaluation/
# reporting paths (run_benchmark.py, report_benchmark.py) are included per
# the governing document's explicit requirement, even though report_
# benchmark.py only runs later during scoring verification, not by this
# wrapper directly.
EXECUTABLE_CODE_ENTRY_POINTS = [
    "run_seed17_phase2_replay.py",
    "train.py",
    "run_benchmark.py",
    "report_benchmark.py",
]

GOVERNING_INPUT_FILES = [
    "gold_v1.2.2_phase2_derived_candidate.jsonl",
    "data/processed_gold_v1.2.2_phase2_v2contract_seed17/train.jsonl",
    "data/processed_gold_v1.2.2_phase2_v2contract_seed17/val.jsonl",
    "../datasets/benchmark/gold_v1.2.1_probes.jsonl",
    "../datasets/benchmark/source_determined_items_v2_acceptance_draft.jsonl",
]
REAL_VALIDATION_REL_PATH = "../datasets/real_validation.jsonl"

EXPECTED_PROTECTED_COUNT = 16
EXPECTED_ACCEPTANCE_COUNT = 10
EXPECTED_TRAIN_COUNT = 72
EXPECTED_VAL_COUNT = 6
EXPECTED_CANDIDATE_COUNT = 78
EXPECTED_TRAINING_DATA_FINGERPRINT = "9d6817152087685b653830ad671f9304e4226b095a202ca57f5ca52bc3a14c1f"

# Verified from the R2 replay's own receipt (environment.cuda_available),
# not assumed -- same GPU/venv this package's pinned torch==2.11.0+cu128
# was already confirmed running under.
EXPECTED_CUDA_AVAILABLE = True

PRIMARY_STEPS = 720
CONTROL_STEPS = 600

DATA_DIR_REL = "data/processed_gold_v1.2.2_phase2_v2contract_seed17"

# Section 5.1's fail-closed resolution of the gate-6 wording ambiguity:
# the conjunction of "preserve every R2-passing protected probe" and
# "probe 13 must pass," encoded explicitly here rather than left to be
# inferred later from report_benchmark.py's generic regression-warning
# line (already shown, in the R2 round, to over-flag probes that were
# already failing at baseline). Independently reproduced from the real
# committed R2 scored file via report_benchmark.v2_result_passes() before
# being pinned here, not copied from the governing document without
# re-derivation: PASS = {01,03,04,05,06,07,09,10,12,14,15,16}, FAIL =
# {02,08,11,13} -- so GATE6 = PASS | {13}.
GATE6_REQUIRED_PASS_SET = frozenset({"01", "03", "04", "05", "06", "07", "09", "10", "12", "13", "14", "15", "16"})


class ReplayPreflightError(SystemExit):
    pass


def file_fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Import-closure computation (Section 4.1's "full local executable import
# closure," not a manually selected top-level list)
# ---------------------------------------------------------------------------


def local_imports_of(path: Path) -> set[str]:
    """Parses one file's AST (never executes it) and returns the set of
    repo-local module names it imports directly. "Local" means a .py file
    exists at TRAINING_DIR / f"{name}.py" -- this repo's training/ tree is
    flat with no local package/subpackage structure, confirmed by
    inspecting every existing import statement in it."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                names.add(node.module.split(".")[0])
    return {n for n in names if (TRAINING_DIR / f"{n}.py").exists()}


def compute_import_closure(entry_points: list[str]) -> set[str]:
    """BFS over local imports starting from entry_points (filenames
    relative to TRAINING_DIR), returning the full transitive closure of
    repo-local module filenames. Recomputed fresh every time this is
    called -- never cached across a preflight run -- so an import added
    anywhere in the closure is caught the same run it's introduced."""
    seen: set[str] = set()
    queue: list[str] = list(entry_points)
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        path = TRAINING_DIR / name
        if not path.exists():
            raise ReplayPreflightError(f"Import-closure entry point or dependency missing: {path}")
        for local_mod in local_imports_of(path):
            fname = f"{local_mod}.py"
            if fname not in seen:
                queue.append(fname)
    return seen


def fingerprint_import_closure(entry_points: list[str] | None = None) -> dict[str, str]:
    closure = compute_import_closure(entry_points if entry_points is not None else EXECUTABLE_CODE_ENTRY_POINTS)
    return {name: file_fingerprint(TRAINING_DIR / name) for name in closure}


def fingerprint_governing_inputs() -> dict[str, str]:
    result = {}
    for rel in GOVERNING_INPUT_FILES:
        path = TRAINING_DIR / rel
        if not path.exists():
            raise ReplayPreflightError(f"Governing input file missing: {path}")
        result[rel] = file_fingerprint(path)
    return result


def verify_real_validation_empty() -> None:
    """train.py always calls run_real_validation_evaluation after
    training, which reads this exact file -- a nonempty file would let
    undeclared private-data inference into a replay whose authorized
    evaluation scope is only the frozen 26 benchmark cases. Checked by
    both size (the explicit, readable form of the requirement) and
    fingerprint (so the lock file also pins it, catching any drift the
    same way every other governing input is caught)."""
    path = TRAINING_DIR / REAL_VALIDATION_REL_PATH
    if not path.exists():
        raise ReplayPreflightError(f"Missing required (byte-empty) file: {path}")
    size = path.stat().st_size
    if size != 0:
        raise ReplayPreflightError(
            f"{path} is {size} byte(s), expected byte-empty. Refusing to proceed -- this replay's "
            "authorized evaluation scope is only the frozen 26 benchmark cases; a populated "
            "real_validation.jsonl would let train.py's automatic real-validation evaluator run "
            "against undeclared private data."
        )
    print(f"[real-validation OK] {path} is byte-empty as required.")


def load_frozen_fingerprints(path: Path = FROZEN_FINGERPRINTS_PATH) -> dict:
    if not path.exists():
        raise ReplayPreflightError(f"Missing frozen-fingerprints lock file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _compare_fingerprint_dicts(expected: dict[str, str], actual: dict[str, str], label: str) -> None:
    if set(expected) != set(actual):
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        raise ReplayPreflightError(
            f"{label}: file set does not match the frozen lock file. Missing: {missing}. Unexpected extra: {extra}."
        )
    mismatches = {name: (expected[name], actual[name]) for name in expected if expected[name] != actual[name]}
    if mismatches:
        raise ReplayPreflightError(f"{label}: {len(mismatches)} fingerprint mismatch(es) against the frozen lock file: {mismatches}")
    print(f"[{label} OK] all {len(expected)} file(s) match the frozen lock file exactly.")


def verify_frozen_executable_code(lock: dict | None = None) -> None:
    """Two-stage check, stricter than a plain fingerprint comparison:
    (1) the *set* of files the import closure currently resolves to must
    equal the lock's recorded set -- an added or removed local import is
    caught here even before any content is compared; (2) each file's
    content must match its pinned fingerprint."""
    lock = lock if lock is not None else load_frozen_fingerprints()
    expected = lock["executable_code"]
    current_closure = compute_import_closure(EXECUTABLE_CODE_ENTRY_POINTS)
    if current_closure != set(expected):
        missing = sorted(set(expected) - current_closure)
        extra = sorted(current_closure - set(expected))
        raise ReplayPreflightError(
            "executable code: the recomputed import closure does not match the frozen lock's file "
            f"set -- the import graph itself has drifted. Missing: {missing}. Unexpected extra (new "
            f"local import introduced somewhere in the closure): {extra}."
        )
    actual = {name: file_fingerprint(TRAINING_DIR / name) for name in current_closure}
    _compare_fingerprint_dicts(expected, actual, "executable code")


def verify_frozen_governing_inputs(lock: dict | None = None) -> None:
    lock = lock if lock is not None else load_frozen_fingerprints()
    _compare_fingerprint_dicts(lock["governing_inputs"], fingerprint_governing_inputs(), "governing inputs")
    expected_rv_fp = lock["real_validation_fingerprint"]
    actual_rv_fp = file_fingerprint(TRAINING_DIR / REAL_VALIDATION_REL_PATH)
    if actual_rv_fp != expected_rv_fp:
        raise ReplayPreflightError(
            f"real_validation.jsonl fingerprint mismatch: expected {expected_rv_fp}, got {actual_rv_fp}."
        )
    verify_real_validation_empty()


def verify_pinned_dependency_versions(lock: dict | None = None) -> None:
    lock = lock if lock is not None else load_frozen_fingerprints()
    expected = lock["dependency_versions"]
    actual = environment_versions()
    mismatches = {name: (expected_v, actual.get(name)) for name, expected_v in expected.items() if actual.get(name) != expected_v}
    if mismatches:
        raise ReplayPreflightError(f"Dependency version drift detected (expected vs. installed): {mismatches}")
    print(f"[dependency versions OK] all {len(expected)} pinned package(s) match exactly.")


def verify_cuda_bfloat16_expectation() -> None:
    actual = environment_versions().get("cuda_available")
    if actual != EXPECTED_CUDA_AVAILABLE:
        raise ReplayPreflightError(
            f"CUDA availability is {actual}, expected {EXPECTED_CUDA_AVAILABLE} (train.py sets "
            "bf16=(device=='cuda'), so a mismatch here means both runs would train under a "
            "different precision regime than this package was verified against)."
        )
    print(f"[CUDA/bfloat16 OK] torch.cuda.is_available() == {EXPECTED_CUDA_AVAILABLE} as expected.")


def verify_clean_working_tree(state: dict | None = None) -> None:
    state = state if state is not None else git_state()
    if not state["working_tree_clean"]:
        raise ReplayPreflightError(
            "Working tree is not clean -- refusing to proceed with an unreviewed, uncommitted diff "
            f"present. git status --porcelain:\n{state['working_tree_status_raw']}"
        )
    print("[working tree OK] clean, nothing uncommitted.")


def verify_head_matches_origin_main(state: dict | None = None) -> None:
    state = state if state is not None else git_state()
    if not state["head_matches_origin_main"]:
        raise ReplayPreflightError(
            f"HEAD ({state['head_commit']}) does not match origin/main ({state['origin_main_commit']}). "
            "Refusing to proceed against a diverged local branch."
        )
    print(f"[HEAD OK] {state['head_commit']} matches origin/main.")


def verify_package_commit(state: dict | None = None) -> None:
    """Fails closed unless HEAD is a *direct* child of PINNED_PARENT_COMMIT
    (exactly one commit ahead, not any later descendant) whose delta from
    the parent contains exactly EXPECTED_PACKAGE_COMMIT_FILES -- neither a
    subset (an incompletely-committed package) nor a superset (an
    unrelated or unreviewed change riding along in the same commit).
    Together with verify_head_matches_origin_main(), this replaces a
    naive "HEAD == this fixed commit" check, which would make the package
    permanently unable to pass its own preflight once actually committed
    (see PINNED_PARENT_COMMIT's comment)."""
    state = state if state is not None else git_state()
    if state["head_parent_commit"] != PINNED_PARENT_COMMIT:
        raise ReplayPreflightError(
            f"HEAD's parent is {state['head_parent_commit']}, expected the pinned parent commit "
            f"{PINNED_PARENT_COMMIT}. The package commit must be a direct child of the reviewed "
            "derivation-gate commit -- not the parent commit itself (package not yet committed), "
            "not a later descendant, and not a commit on a different history."
        )
    changed = set(state["changed_files_since_parent"] or [])
    if changed != EXPECTED_PACKAGE_COMMIT_FILES:
        missing = sorted(EXPECTED_PACKAGE_COMMIT_FILES - changed)
        extra = sorted(changed - EXPECTED_PACKAGE_COMMIT_FILES)
        raise ReplayPreflightError(
            "The commit delta from the pinned parent to HEAD does not contain exactly the six "
            f"reviewed package files. Missing: {missing}. Unexpected extra (unreviewed file riding "
            f"along in the same commit): {extra}."
        )
    print(
        f"[package commit OK] HEAD ({state['head_commit']}) is a direct child of the pinned parent "
        f"{PINNED_PARENT_COMMIT}, and its delta contains exactly the {len(EXPECTED_PACKAGE_COMMIT_FILES)} "
        "reviewed package files."
    )


def git_state() -> dict:
    def run(args: list[str]) -> str:
        return subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()

    head = run(["git", "rev-parse", "HEAD"])
    try:
        origin_main = run(["git", "rev-parse", "origin/main"])
    except subprocess.CalledProcessError:
        origin_main = None
    try:
        head_parent = run(["git", "rev-parse", "HEAD^"])
    except subprocess.CalledProcessError:
        head_parent = None
    try:
        diff_raw = run(["git", "diff", "--name-only", f"{PINNED_PARENT_COMMIT}..HEAD"])
        # A sorted list, not a set/frozenset -- this whole dict gets written
        # verbatim into the JSON receipt, and sets aren't JSON-serializable.
        # verify_package_commit() converts to a set for the actual
        # order-independent comparison.
        changed_files_since_parent = sorted(f for f in diff_raw.splitlines() if f.strip())
    except subprocess.CalledProcessError:
        changed_files_since_parent = None
    status_porcelain = run(["git", "status", "--porcelain"])
    return {
        "head_commit": head,
        "origin_main_commit": origin_main,
        "head_matches_origin_main": head == origin_main,
        "head_parent_commit": head_parent,
        "changed_files_since_parent": changed_files_since_parent,
        "working_tree_clean": status_porcelain == "",
        "working_tree_status_raw": status_porcelain,
    }


def environment_versions() -> dict:
    versions = {"python": sys.version}
    for mod_name in ("torch", "transformers", "datasets", "accelerate", "sentencepiece", "huggingface_hub"):
        try:
            mod = __import__(mod_name)
            versions[mod_name] = getattr(mod, "__version__", "unknown")
        except ImportError:
            versions[mod_name] = None
    try:
        import torch

        versions["cuda_available"] = torch.cuda.is_available()
    except ImportError:
        versions["cuda_available"] = None
    return versions


def hf_cache_snapshot_info(repo_id: str) -> tuple[str, dict[str, str]]:
    from huggingface_hub import scan_cache_dir

    info = scan_cache_dir()
    matches = [r for r in info.repos if r.repo_id == repo_id]
    if not matches:
        raise ReplayPreflightError(f"'{repo_id}' is not present in the local Hugging Face cache at all.")
    if len(matches) > 1:
        raise ReplayPreflightError(f"Ambiguous cache state: {len(matches)} cache entries found for '{repo_id}'.")
    repo = matches[0]
    if len(repo.revisions) != 1:
        raise ReplayPreflightError(
            f"'{repo_id}' has {len(repo.revisions)} cached revision(s), expected exactly 1 -- "
            "refusing to guess which one would be used."
        )
    revision = next(iter(repo.revisions))
    fingerprints = {f.file_name: file_fingerprint(f.file_path) for f in revision.files}
    return revision.commit_hash, fingerprints


def verify_pinned_base_model_snapshot() -> None:
    revision, fingerprints = hf_cache_snapshot_info(HF_REPO_ID)
    if revision != PINNED_BASE_MODEL_REVISION:
        raise ReplayPreflightError(
            f"Cached '{HF_REPO_ID}' revision is {revision}, expected pinned {PINNED_BASE_MODEL_REVISION}."
        )
    if set(fingerprints) != set(PINNED_BASE_MODEL_FILE_FINGERPRINTS):
        raise ReplayPreflightError(
            f"Cached file set for '{HF_REPO_ID}' does not match the pinned set. "
            f"Cached: {sorted(fingerprints)}. Expected: {sorted(PINNED_BASE_MODEL_FILE_FINGERPRINTS)}."
        )
    for name, expected in PINNED_BASE_MODEL_FILE_FINGERPRINTS.items():
        actual = fingerprints[name]
        if actual != expected:
            raise ReplayPreflightError(f"'{HF_REPO_ID}' file {name!r} fingerprint mismatch: expected {expected}, got {actual}.")
    print(f"[snapshot OK] {HF_REPO_ID} @ {revision}: all {len(fingerprints)} file(s) match pinned fingerprints.")


# ---------------------------------------------------------------------------
# Split / training-data fingerprint recomputation (Section 4.1: "the 72/6
# split and canonical training-data fingerprint recompute exactly")
# ---------------------------------------------------------------------------


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def canonical_training_data_fingerprint(records: list[dict]) -> str:
    sortable = sorted(records, key=lambda r: r["prompt"])
    blob = json.dumps(sortable, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def verify_split_and_fingerprint() -> None:
    candidate_path = TRAINING_DIR / "gold_v1.2.2_phase2_derived_candidate.jsonl"
    train_path = TRAINING_DIR / DATA_DIR_REL / "train.jsonl"
    val_path = TRAINING_DIR / DATA_DIR_REL / "val.jsonl"

    candidate = load_jsonl(candidate_path)
    if len(candidate) != EXPECTED_CANDIDATE_COUNT:
        raise ReplayPreflightError(f"Candidate corpus has {len(candidate)} record(s), expected exactly {EXPECTED_CANDIDATE_COUNT}.")

    train_pairs = load_jsonl(train_path)
    val_pairs = load_jsonl(val_path)
    if len(train_pairs) != EXPECTED_TRAIN_COUNT:
        raise ReplayPreflightError(f"Train split has {len(train_pairs)} record(s), expected exactly {EXPECTED_TRAIN_COUNT}.")
    if len(val_pairs) != EXPECTED_VAL_COUNT:
        raise ReplayPreflightError(f"Val split has {len(val_pairs)} record(s), expected exactly {EXPECTED_VAL_COUNT}.")

    fp = canonical_training_data_fingerprint(train_pairs + val_pairs)
    if fp != EXPECTED_TRAINING_DATA_FINGERPRINT:
        raise ReplayPreflightError(
            f"Canonical training-data fingerprint mismatch: expected {EXPECTED_TRAINING_DATA_FINGERPRINT}, got {fp}."
        )
    print(
        f"[split OK] candidate={len(candidate)}, train={len(train_pairs)}, val={len(val_pairs)}; "
        f"training-data fingerprint matches: {fp}"
    )


def verify_benchmark_counts() -> None:
    protected = load_jsonl(TRAINING_DIR / GOVERNING_INPUT_FILES[3])
    acceptance = load_jsonl(TRAINING_DIR / GOVERNING_INPUT_FILES[4])
    if len(protected) != EXPECTED_PROTECTED_COUNT:
        raise ReplayPreflightError(f"Protected benchmark has {len(protected)} record(s), expected exactly {EXPECTED_PROTECTED_COUNT}.")
    if len(acceptance) != EXPECTED_ACCEPTANCE_COUNT:
        raise ReplayPreflightError(f"Acceptance benchmark has {len(acceptance)} record(s), expected exactly {EXPECTED_ACCEPTANCE_COUNT}.")
    print(f"[benchmark counts OK] protected={len(protected)}, acceptance={len(acceptance)}.")


# ---------------------------------------------------------------------------
# Command construction and self-verification
# ---------------------------------------------------------------------------


def build_commands(primary_dir: Path, control_dir: Path) -> dict[str, list[str]]:
    def train_cmd(output_dir: Path, max_steps: int | None) -> list[str]:
        cmd = [
            sys.executable,
            "train.py",
            "--seed",
            "17",
            "--data-dir",
            DATA_DIR_REL,
            "--output-dir",
            str(output_dir.relative_to(TRAINING_DIR)),
        ]
        if max_steps is not None:
            cmd += ["--max-steps", str(max_steps)]
        return cmd

    def eval_cmd(benchmark_rel: str, checkpoint_dir: Path, output_json: Path) -> list[str]:
        return [
            sys.executable,
            "run_benchmark.py",
            benchmark_rel,
            str((checkpoint_dir / "final").relative_to(TRAINING_DIR)),
            str(output_json.relative_to(TRAINING_DIR)),
            "--contract=v2",
        ]

    primary_checkpoint = primary_dir / "checkpoint"
    control_checkpoint = control_dir / "checkpoint"

    return {
        "primary_train": train_cmd(primary_checkpoint, None),
        "primary_protected16": eval_cmd(GOVERNING_INPUT_FILES[3], primary_checkpoint, primary_dir / "protected16_results.json"),
        "primary_acceptance10": eval_cmd(GOVERNING_INPUT_FILES[4], primary_checkpoint, primary_dir / "acceptance10_results.json"),
        "control_train": train_cmd(control_checkpoint, CONTROL_STEPS),
        "control_protected16": eval_cmd(GOVERNING_INPUT_FILES[3], control_checkpoint, control_dir / "protected16_results.json"),
        "control_acceptance10": eval_cmd(GOVERNING_INPUT_FILES[4], control_checkpoint, control_dir / "acceptance10_results.json"),
    }


def verify_command_shape(commands: dict[str, list[str]]) -> None:
    """Self-verification of build_commands()'s own output, not just trust
    in the construction code: confirms both training commands resolve to
    seed 17 and the shared Phase-2 data directory, the natural command has
    no --max-steps argument at all, and the control command has exactly
    one --max-steps=600 argument -- the two most safety-critical
    properties this whole package exists to guarantee."""
    for key in ("primary_train", "control_train"):
        cmd = commands[key]
        if "--seed" not in cmd or cmd[cmd.index("--seed") + 1] != "17":
            raise ReplayPreflightError(f"{key}: does not resolve to seed 17: {cmd}")
        if "--data-dir" not in cmd or cmd[cmd.index("--data-dir") + 1] != DATA_DIR_REL:
            raise ReplayPreflightError(f"{key}: does not resolve to the pinned Phase-2 data directory: {cmd}")

    primary_cmd = commands["primary_train"]
    if "--max-steps" in primary_cmd:
        raise ReplayPreflightError(f"primary_train: must omit --max-steps entirely, found it in: {primary_cmd}")

    control_cmd = commands["control_train"]
    max_steps_occurrences = [i for i, a in enumerate(control_cmd) if a == "--max-steps"]
    if len(max_steps_occurrences) != 1:
        raise ReplayPreflightError(f"control_train: expected exactly one --max-steps argument, found {len(max_steps_occurrences)}: {control_cmd}")
    idx = max_steps_occurrences[0]
    if control_cmd[idx + 1] != str(CONTROL_STEPS):
        raise ReplayPreflightError(f"control_train: --max-steps value is {control_cmd[idx + 1]!r}, expected {CONTROL_STEPS!r}: {control_cmd}")

    print("[command shape OK] primary omits --max-steps; control has exactly one --max-steps=600; both resolve to seed 17 and the pinned data dir.")


# ---------------------------------------------------------------------------
# Execution primitives (unchanged from run_seed17_r2_replay.py's already-
# reviewed design)
# ---------------------------------------------------------------------------


def create_exclusive_experiment_dir(path: Path) -> Path:
    try:
        path.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        raise ReplayPreflightError(
            f"Experiment directory already exists: {path}. Refusing to reuse or overwrite it -- "
            "every replay attempt must write to a brand-new, exclusive directory."
        )
    return path


def write_exclusive(path: Path, content: str) -> None:
    with path.open("x", encoding="utf-8") as f:
        f.write(content)


def run_logged_subprocess(cmd: list[str], cwd: Path, log_path: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    """Never a shell pipe (which can mask a failing exit code without
    `pipefail`); the log file is opened exclusively before the subprocess
    starts and passed directly as stdout, so a partial log survives even
    if the wrapper itself is interrupted mid-run."""
    full_env = {**os.environ, **(env or {})}
    with log_path.open("x", encoding="utf-8") as log_file:
        log_file.write(f"$ {' '.join(cmd)}\n(cwd={cwd})\n\n=== combined stdout+stderr (streamed live) ===\n")
        log_file.flush()
        proc = subprocess.run(cmd, cwd=cwd, env=full_env, stdout=log_file, stderr=subprocess.STDOUT, text=True, check=False)
        log_file.write(f"\n=== exit code: {proc.returncode} ===\n")
    return proc


def require_success(proc: subprocess.CompletedProcess, step_name: str) -> None:
    if proc.returncode != 0:
        raise ReplayPreflightError(
            f"Step {step_name!r} exited with code {proc.returncode} -- stopping the sequence. "
            "This is a hard stop, not something to retry automatically; see its log file for detail."
        )
    print(f"[step OK] {step_name} exited 0.")


EXPECTED_SCORE_KEYS = frozenset(
    {"topic_completeness", "attribution_accuracy", "uncertainty_preservation", "unsupported_addition_resistance"}
)


def verify_raw_result_artifact(result_path: Path, benchmark_path: Path, expected_count: int, label: str) -> None:
    """Fail-closed validation of a raw benchmark result file, run
    immediately after each evaluation subprocess exits 0. A clean exit
    code alone does not prove run_benchmark.py actually wrote a valid,
    complete, correctly-ordered, still-unscored result file -- per the
    governing document's Section 6.1, a missing or invalid raw result, or
    a scoring-integrity failure, is itself an invalid experiment (P2-X),
    not something to discover only later during scoring.

    Revised 2026-08-04 per ChatGPT's second-pass finding: the original
    version checked only that `scores` values were null, so a record with
    `capability_checks` already filled in and a non-empty `failure_labels`
    still passed as "no semantic scores filled" -- reproduced exactly
    against a real protected-16 raw artifact before fixing. Now checks,
    for every record: the file exists and parses as a JSON array with
    exactly expected_count records whose IDs appear in exactly the
    benchmark file's own order; every record has a non-empty raw_output;
    `scores` has exactly the four expected dimension keys
    (EXPECTED_SCORE_KEYS -- confirmed identical across every protected and
    acceptance probe, not just assumed), all null; `capability_checks`
    keys exactly match that specific probe's own `primary_checks` list
    from the benchmark file (some probes, e.g. protected 13-16, legitimately
    have zero primary_checks and an empty capability_checks dict --
    confirmed directly against the real benchmark file, not assumed
    non-empty), and every value is null; and `failure_labels` is exactly
    an empty list."""
    if not result_path.exists():
        raise ReplayPreflightError(f"{label}: raw result file does not exist: {result_path}")
    try:
        results = json.loads(result_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ReplayPreflightError(f"{label}: raw result file does not parse as JSON: {e}")
    if not isinstance(results, list):
        raise ReplayPreflightError(f"{label}: raw result file is not a JSON array.")
    if len(results) != expected_count:
        raise ReplayPreflightError(
            f"{label}: raw result file has {len(results)} record(s), expected exactly {expected_count}."
        )

    benchmark = load_jsonl(benchmark_path)
    expected_ids = [b["id"] for b in benchmark]
    actual_ids = [r.get("id") for r in results]
    if actual_ids != expected_ids:
        raise ReplayPreflightError(
            f"{label}: raw result IDs/order do not match the benchmark file exactly. "
            f"Expected: {expected_ids}. Got: {actual_ids}."
        )
    probes_by_id = {b["id"]: b for b in benchmark}

    for r in results:
        rid = r.get("id")
        raw_output = r.get("raw_output")
        if not isinstance(raw_output, str) or not raw_output.strip():
            raise ReplayPreflightError(f"{label}: record {rid!r} has no non-empty raw_output.")

        scores = r.get("scores")
        if not isinstance(scores, dict) or set(scores) != EXPECTED_SCORE_KEYS:
            raise ReplayPreflightError(
                f"{label}: record {rid!r} 'scores' keys {sorted(scores) if isinstance(scores, dict) else scores!r} "
                f"!= expected {sorted(EXPECTED_SCORE_KEYS)}."
            )
        filled_scores = {k: v for k, v in scores.items() if v is not None}
        if filled_scores:
            raise ReplayPreflightError(
                f"{label}: record {rid!r} already has semantic score(s) filled ({filled_scores}) -- this "
                "wrapper must only ever produce raw, unscored scaffolds, never fill or accept pre-filled scores."
            )

        expected_check_keys = set(probes_by_id[rid].get("primary_checks") or [])
        capability_checks = r.get("capability_checks")
        if not isinstance(capability_checks, dict) or set(capability_checks) != expected_check_keys:
            raise ReplayPreflightError(
                f"{label}: record {rid!r} 'capability_checks' keys "
                f"{sorted(capability_checks) if isinstance(capability_checks, dict) else capability_checks!r} "
                f"!= this probe's own primary_checks {sorted(expected_check_keys)}."
            )
        filled_checks = {k: v for k, v in capability_checks.items() if v is not None}
        if filled_checks:
            raise ReplayPreflightError(
                f"{label}: record {rid!r} already has capability_check(s) filled ({filled_checks}) -- this "
                "wrapper must only ever produce raw, unscored scaffolds."
            )

        failure_labels = r.get("failure_labels")
        if failure_labels != []:
            raise ReplayPreflightError(
                f"{label}: record {rid!r} 'failure_labels' is {failure_labels!r}, expected an empty list "
                "for an unscored raw scaffold."
            )

    print(
        f"[raw result OK] {label}: {len(results)} record(s), IDs/order match the benchmark exactly, every "
        "record has raw_output, scores/capability_checks have exactly the right keys and are all null, "
        "and failure_labels is empty."
    )


def verify_completed_steps(output_dir: Path, expected_steps: int, run_name: str) -> None:
    """Reads the highest-numbered checkpoint-N/trainer_state.json Trainer
    itself writes at each save_strategy='epoch' boundary and requires its
    global_step to equal exactly expected_steps -- a clean subprocess exit
    code alone does not prove the intended number of optimizer steps ran."""
    checkpoint_dirs = sorted(
        (p for p in output_dir.glob("checkpoint-*") if p.is_dir()),
        key=lambda p: int(p.name.split("-")[-1]),
    )
    if not checkpoint_dirs:
        raise ReplayPreflightError(f"{run_name}: no checkpoint-N directory found under {output_dir} -- cannot verify step count.")
    last_checkpoint = checkpoint_dirs[-1]
    state_path = last_checkpoint / "trainer_state.json"
    if not state_path.exists():
        raise ReplayPreflightError(f"{run_name}: {state_path} does not exist -- cannot verify step count.")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    actual_steps = state.get("global_step")
    if actual_steps != expected_steps:
        raise ReplayPreflightError(
            f"{run_name}: completed {actual_steps} optimizer step(s) ({last_checkpoint.name}), expected exactly "
            f"{expected_steps}. A mismatch is an invalid experiment (P2-X) even though the subprocess exited 0."
        )
    print(f"[step count OK] {run_name}: {last_checkpoint.name}/trainer_state.json confirms exactly {actual_steps} step(s).")


def build_receipt(experiment_dir: Path, commands: dict[str, list[str]]) -> dict:
    """Read-only: touches git, the filesystem, and already-imported module
    __version__ attributes -- never loads a model or starts a subprocess."""
    state = git_state()
    receipt = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git": state,
        # Explicit, top-level label for what execution authorization must
        # name -- per the governing document's own requirement that Johnny
        # separately name the exact replay after joint review, this is the
        # specific commit that authorization refers to, not just something
        # buried inside the "git" sub-object.
        "package_commit": state["head_commit"],
        "package_commit_parent": PINNED_PARENT_COMMIT,
        "planned_commands": {
            "primary": [" ".join(commands["primary_train"]), " ".join(commands["primary_protected16"]), " ".join(commands["primary_acceptance10"])],
            "control": [" ".join(commands["control_train"]), " ".join(commands["control_protected16"]), " ".join(commands["control_acceptance10"])],
        },
        "environment": environment_versions(),
        "shared_configuration": {
            "seed": 17,
            "data_dir": DATA_DIR_REL,
            "contract": "v2",
            "base_model": HF_REPO_ID,
            "base_model_snapshot_revision": PINNED_BASE_MODEL_REVISION,
            "batch_size": 4,
            "learning_rate": "3e-4",
            "weight_decay": 0.01,
            "num_train_epochs": 40,
            "protected_benchmark": GOVERNING_INPUT_FILES[3],
            "acceptance_benchmark": GOVERNING_INPUT_FILES[4],
        },
        "declared_differences": {
            "primary": {"max_steps": None, "expected_steps": PRIMARY_STEPS, "role": "sole decision-bearing Phase-2 candidate"},
            "control": {"max_steps": CONTROL_STEPS, "expected_steps": CONTROL_STEPS, "role": "step-budget diagnostic control, never a substitute for the primary"},
        },
        "gate6_required_pass_set": sorted(GATE6_REQUIRED_PASS_SET),
        "governing_document": "training/phase2_seed17_replay_interpretation_and_outcome_matrix_chatgpt.md",
        "resolved_configuration": {
            "primary_checkpoint_dir": str((experiment_dir / "primary" / "checkpoint").relative_to(TRAINING_DIR)),
            "control_checkpoint_dir": str((experiment_dir / "control" / "checkpoint").relative_to(TRAINING_DIR)),
        },
        "base_model": {
            "repo_id": HF_REPO_ID,
            "pinned_revision": PINNED_BASE_MODEL_REVISION,
            "file_fingerprints": PINNED_BASE_MODEL_FILE_FINGERPRINTS,
        },
        "executable_code_fingerprints": {name: file_fingerprint(TRAINING_DIR / name) for name in compute_import_closure(EXECUTABLE_CODE_ENTRY_POINTS)},
        "governing_input_fingerprints": fingerprint_governing_inputs(),
        "real_validation_fingerprint": file_fingerprint(TRAINING_DIR / REAL_VALIDATION_REL_PATH),
    }
    return receipt


OFFLINE_ENV = {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--confirm-execute",
        action="store_true",
        help=(
            "Required to actually run anything. Without this flag the script only prints what it "
            "would do. Passing it is not itself authorization -- running this for real still "
            "requires Johnny naming this exact replay after joint review of the committed package."
        ),
    )
    parser.add_argument("--experiment-dir", type=str, default=None)
    args = parser.parse_args()

    experiment_dir = Path(args.experiment_dir) if args.experiment_dir else TRAINING_DIR / "controlled_seed17_phase2_replay_run"
    primary_dir = experiment_dir / "primary"
    control_dir = experiment_dir / "control"
    commands = build_commands(primary_dir, control_dir)

    if not args.confirm_execute:
        print("Dry run only (pass --confirm-execute to run for real). Planned sequence:")
        for key in ("primary_train", "primary_protected16", "primary_acceptance10", "control_train", "control_protected16", "control_acceptance10"):
            print(f"  $ {' '.join(commands[key])}")
        print(f"Planned exclusive experiment directory: {experiment_dir}")
        return

    print("=== Preflight ===")
    lock = load_frozen_fingerprints()
    state = git_state()
    verify_head_matches_origin_main(state)
    verify_package_commit(state)
    verify_clean_working_tree(state)
    verify_pinned_dependency_versions(lock)
    verify_frozen_executable_code(lock)
    verify_frozen_governing_inputs(lock)
    verify_benchmark_counts()
    verify_split_and_fingerprint()
    verify_cuda_bfloat16_expectation()
    verify_command_shape(commands)
    verify_pinned_base_model_snapshot()

    if experiment_dir.exists():
        raise ReplayPreflightError(f"Experiment root already exists: {experiment_dir}. Refusing to reuse or overwrite it.")

    create_exclusive_experiment_dir(experiment_dir)
    receipt = build_receipt(experiment_dir, commands)
    write_exclusive(experiment_dir / "receipt.json", json.dumps(receipt, indent=2, ensure_ascii=False))
    print(f"[receipt written] {experiment_dir / 'receipt.json'}")

    create_exclusive_experiment_dir(primary_dir)
    create_exclusive_experiment_dir(control_dir)

    print("\n=== Primary: training (natural, expect 720 steps) ===")
    proc = run_logged_subprocess(commands["primary_train"], cwd=TRAINING_DIR, log_path=primary_dir / "train_log.txt", env=OFFLINE_ENV)
    require_success(proc, "primary train.py")
    verify_completed_steps(primary_dir / "checkpoint", PRIMARY_STEPS, "primary")

    print("\n=== Primary: evaluation (protected 16) ===")
    proc = run_logged_subprocess(commands["primary_protected16"], cwd=TRAINING_DIR, log_path=primary_dir / "protected16_log.txt", env=OFFLINE_ENV)
    require_success(proc, "primary run_benchmark.py (protected16)")
    verify_raw_result_artifact(
        primary_dir / "protected16_results.json", TRAINING_DIR / GOVERNING_INPUT_FILES[3], EXPECTED_PROTECTED_COUNT, "primary protected16"
    )

    print("\n=== Primary: evaluation (acceptance 10) ===")
    proc = run_logged_subprocess(commands["primary_acceptance10"], cwd=TRAINING_DIR, log_path=primary_dir / "acceptance10_log.txt", env=OFFLINE_ENV)
    require_success(proc, "primary run_benchmark.py (acceptance10)")
    verify_raw_result_artifact(
        primary_dir / "acceptance10_results.json", TRAINING_DIR / GOVERNING_INPUT_FILES[4], EXPECTED_ACCEPTANCE_COUNT, "primary acceptance10"
    )

    print("\n=== Control: training (step-matched, expect 600 steps) ===")
    proc = run_logged_subprocess(commands["control_train"], cwd=TRAINING_DIR, log_path=control_dir / "train_log.txt", env=OFFLINE_ENV)
    require_success(proc, "control train.py")
    verify_completed_steps(control_dir / "checkpoint", CONTROL_STEPS, "control")

    print("\n=== Control: evaluation (protected 16) ===")
    proc = run_logged_subprocess(commands["control_protected16"], cwd=TRAINING_DIR, log_path=control_dir / "protected16_log.txt", env=OFFLINE_ENV)
    require_success(proc, "control run_benchmark.py (protected16)")
    verify_raw_result_artifact(
        control_dir / "protected16_results.json", TRAINING_DIR / GOVERNING_INPUT_FILES[3], EXPECTED_PROTECTED_COUNT, "control protected16"
    )

    print("\n=== Control: evaluation (acceptance 10) ===")
    proc = run_logged_subprocess(commands["control_acceptance10"], cwd=TRAINING_DIR, log_path=control_dir / "acceptance10_log.txt", env=OFFLINE_ENV)
    require_success(proc, "control run_benchmark.py (acceptance10)")
    verify_raw_result_artifact(
        control_dir / "acceptance10_results.json", TRAINING_DIR / GOVERNING_INPUT_FILES[4], EXPECTED_ACCEPTANCE_COUNT, "control acceptance10"
    )

    print(f"\nAll steps completed. Artifacts in {experiment_dir}")
    print(
        "Raw benchmark result scaffolds only -- no semantic scores filled, no checkpoint selected. "
        "Semantic scoring and outcome classification (P2-A/B/C/D/X) are separate, later, "
        "separately-authorized steps."
    )


if __name__ == "__main__":
    main()
