"""Execution wrapper for the controlled seed-17 R2 replay
(training/controlled_seed17_r2_replay_protocol.md,
training/controlled_seed17_r2_replay_frozen_manifest.md).

Addresses ChatGPT's four execution-readiness findings on manifest revision
1 (2026-08-03), and the two further findings on this file's first draft
(2026-08-03, same day):

1. Base-model/tokenizer pinning: verify_pinned_base_model_snapshot() reads
   the local Hugging Face cache directly (via huggingface_hub.scan_cache_dir,
   never the network) and fails closed unless the cached google/flan-t5-base
   snapshot's revision and every file's SHA-256 exactly match the pinned
   values below. Both the real training and evaluation subprocesses are run
   with HF_HUB_OFFLINE=1/TRANSFORMERS_OFFLINE=1, so no newer files can ever
   be fetched even if the Hub changes later. verify_baseline_checkpoint_used_pinned_snapshot()
   is strong provenance evidence that the baseline checkpoint's tokenizer
   came from this exact snapshot (spiece.model, the raw SentencePiece
   vocabulary, never re-serialized by save_pretrained, matches byte-for-byte)
   -- it is not independent cryptographic proof of the model's initial
   *weight* identity, since fine-tuning necessarily changes every weight and
   a direct byte comparison of them isn't possible; the inference to the
   weights follows from from_pretrained(repo_id) resolving model and
   tokenizer from the same implicit revision in one call, not from a
   separate weight-level check.
2. Raw, interruption-safe log preservation (fixed after ChatGPT's second
   review found the first draft's capture_output=True buffered everything
   in memory until the subprocess had already finished, losing all output
   if the wrapper itself were killed mid-run): run_logged_subprocess() now
   opens the log file exclusively *before* the subprocess starts and passes
   that open file handle directly as stdout (stderr=subprocess.STDOUT) --
   never a shell pipe, which can also mask a failing exit code without
   `pipefail`, and never Python-level buffering -- so the OS writes output
   to disk as the child produces it, durable even if the wrapper process
   itself is interrupted. require_success() still raises immediately on any
   nonzero return code, before any later step runs.
3. Fail-closed outputs: every artifact this replay produces (receipt,
   checkpoint, both result files, all logs) lives inside exactly one
   experiment directory created via create_exclusive_experiment_dir()
   (Path.mkdir(exist_ok=False)) -- the same atomic-creation pattern already
   tested in prepare_v2_r2_training_data.py -- closing the gap between
   "confirmed the name is unused" and actual execution.
4. Pre-execution receipt: build_receipt() captures the timestamp, checked-
   out commit, origin/main commit, working-tree cleanliness, the exact
   commands about to run, the live environment (interpreter and installed
   package versions), the resolved configuration, and fingerprints of every
   governing input file and every piece of executable code. Written with
   exclusive creation before any subprocess starts.

**Fixed after ChatGPT's second review (2026-08-03)**: fingerprints/versions
were being *recorded* in the receipt but never *enforced* -- the wrapper
would have proceeded even if train.py, the evaluator/scorer/contract code,
the candidate data, either benchmark dataset, or installed dependency
versions had drifted, and even with an unreviewed dirty working tree.
Fixed by verify_frozen_executable_code(), verify_frozen_governing_inputs(),
verify_pinned_dependency_versions(), and verify_clean_working_tree(), all
checked against controlled_seed17_r2_replay_frozen_fingerprints.json (kept
external to this file specifically so this file's own hash can be pinned
there too, without the self-reference problem of a file asserting its own
hash inside itself) and called as preflight, before the experiment
directory is even created. Both benchmark datasets are now included among
the governing inputs (they were missing before).

This module performs no compute on import. Its individual functions are
read-only or operate on dummy/stand-in subprocesses when exercised by
test_run_seed17_r2_replay.py. `main()` is the only path that can start
real training, and it refuses to do anything unless invoked with the
explicit `--confirm-execute` flag, which nothing in this codebase sets
automatically -- running it for real still requires Johnny separately
naming this replay, per the protocol's §5 authorization gate. No such run
has been performed as part of this change.
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TRAINING_DIR = Path(__file__).parent
REPO_ROOT = TRAINING_DIR.parent
FROZEN_FINGERPRINTS_PATH = TRAINING_DIR / "controlled_seed17_r2_replay_frozen_fingerprints.json"

HF_REPO_ID = "google/flan-t5-base"
PINNED_BASE_MODEL_REVISION = "7bcac572ce56db69c1ea7c8af255c5d7c9672fc2"
# Independently recomputed this session by hashing every file in the local
# HF cache snapshot directory (resolving the snapshot's symlinks to their
# real blob content), and cross-checked against the already-committed
# seed-17 baseline checkpoint: spiece.model (the actual SentencePiece
# vocabulary, not re-serialized by save_pretrained) matches byte-for-byte;
# config.json's architecture parameters match exactly (only
# transformers_version and newer-library default fields differ);
# tokenizer.json/tokenizer_config.json/special_tokens_map.json differ only
# in transformers' own re-serialization format (bare-string special tokens
# upgraded to structured AddedToken dicts) between library version 4.23.1
# (the file as originally cached) and 4.57.6 (the pinned training venv) --
# same 100 additional_special_tokens, same content, not a different model.
PINNED_BASE_MODEL_FILE_FINGERPRINTS = {
    "config.json": "7c1853dbfa0e4aac093eb109a358b6ab25fe86b7c15185a91322f0ed26f0f940",
    "generation_config.json": "f5a1c7e2be8092018d8835128987edf0111637dd98e90599cc80310fef75d95a",
    "model.safetensors": "1dfb70afdcedceb9f9fae2f9b68e004ad934361fb35b9b2bd50b45ea90790fc8",
    "special_tokens_map.json": "5c87151ef0f72a99d1f766a4c418bd2a1f90aaa30a8e22fe5eca9641daebb64f",
    "spiece.model": "d60acb128cf7b7f2536e8f38a5b18a05535c9e14c7a355904270e15b0945ea86",
    "tokenizer.json": "fe2ebbbbde2985be723e0ce18217853e4020c5e9d35bd07be2c27ab9d3ead57a",
    "tokenizer_config.json": "4c55124402e4ce48c7125d04b9af152a125eda9e7c80829f8f99f2ec69f3f68d",
}

# The set of executable-code files this replay's correctness depends on.
# Fingerprints are recomputed live at receipt/verification time, never
# hardcoded here, and enforced against controlled_seed17_r2_replay_frozen_fingerprints.json
# (see verify_frozen_executable_code() below) so a future edit to any of
# these is caught, not silently missed.
EXECUTABLE_CODE_FILES = [
    "train.py",
    "run_benchmark.py",
    "report_benchmark.py",
    "contract_adapters.py",
    "prompt_contract_v2_candidate.py",
    "prompt_contract_v2_parser.py",
    "prepare_v2_r2_training_data.py",
    "run_seed17_r2_replay.py",
]

GOVERNING_INPUT_FILES = [
    "gold_v1.2.2_r2_derived_candidate.jsonl",
    "prompt_contract_v2_migrated_targets_DRAFT.jsonl",
    "split_manifest.json",
    "data/processed_gold_v1.2.2_r2_v2contract_seed17/train.jsonl",
    "data/processed_gold_v1.2.2_r2_v2contract_seed17/val.jsonl",
    # Both frozen evaluation-set files -- missing from the first draft,
    # caught by ChatGPT's second review; without these, a drifted
    # benchmark/acceptance file would have gone completely unchecked.
    "../datasets/benchmark/gold_v1.2.1_probes.jsonl",
    "../datasets/benchmark/source_determined_items_v2_acceptance_draft.jsonl",
]


class ReplayPreflightError(SystemExit):
    pass


def file_fingerprint(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def hf_cache_snapshot_info(repo_id: str) -> tuple[str, dict[str, str]]:
    """Reads the local HF cache only (no network). Fails closed if the repo
    isn't cached at all, or if more than one revision is cached (ambiguous
    which one 'main' would resolve to)."""
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
            f"Cached '{HF_REPO_ID}' revision is {revision}, expected pinned {PINNED_BASE_MODEL_REVISION}. "
            "Refusing to proceed -- the base model has drifted from the snapshot this replay was verified against."
        )
    if set(fingerprints) != set(PINNED_BASE_MODEL_FILE_FINGERPRINTS):
        raise ReplayPreflightError(
            f"Cached file set for '{HF_REPO_ID}' does not match the pinned set. "
            f"Cached: {sorted(fingerprints)}. Expected: {sorted(PINNED_BASE_MODEL_FILE_FINGERPRINTS)}."
        )
    for name, expected in PINNED_BASE_MODEL_FILE_FINGERPRINTS.items():
        actual = fingerprints[name]
        if actual != expected:
            raise ReplayPreflightError(
                f"'{HF_REPO_ID}' file {name!r} fingerprint mismatch: expected {expected}, got {actual}. "
                "Refusing to proceed."
            )
    print(f"[snapshot OK] {HF_REPO_ID} @ {revision}: all {len(fingerprints)} file(s) match pinned fingerprints.")


def verify_baseline_checkpoint_used_pinned_snapshot(checkpoint_dir: Path) -> None:
    """Strong provenance evidence, not independent proof of weight
    identity, that the already-committed seed-17 baseline checkpoint came
    from the pinned snapshot: spiece.model is a raw binary SentencePiece
    vocabulary, never re-serialized by save_pretrained, so a byte-for-byte
    match here is direct proof of *tokenizer* identity. It does not, on its
    own, cryptographically verify the model's initial *weight* values --
    fine-tuning necessarily changes every weight, so a direct byte
    comparison against the cached model.safetensors isn't possible. The
    inference that the weights also came from this snapshot rests on
    from_pretrained(repo_id) resolving both the model and the tokenizer
    from the same implicit revision in one call, not on an independent
    weight-level check."""
    snapshot_revision, _ = hf_cache_snapshot_info(HF_REPO_ID)
    if snapshot_revision != PINNED_BASE_MODEL_REVISION:
        raise ReplayPreflightError("Cannot verify baseline checkpoint provenance -- cache is not at the pinned revision.")

    from huggingface_hub import scan_cache_dir

    info = scan_cache_dir()
    repo = next(r for r in info.repos if r.repo_id == HF_REPO_ID)
    revision = next(iter(repo.revisions))
    snapshot_dir = revision.snapshot_path

    checkpoint_spiece = checkpoint_dir / "spiece.model"
    snapshot_spiece = Path(snapshot_dir) / "spiece.model"
    checkpoint_hash = file_fingerprint(checkpoint_spiece)
    snapshot_hash = file_fingerprint(snapshot_spiece)
    if checkpoint_hash != snapshot_hash:
        raise ReplayPreflightError(
            f"Baseline checkpoint's spiece.model ({checkpoint_hash}) does not match the pinned snapshot's "
            f"({snapshot_hash}) -- the baseline may not have used this snapshot after all."
        )
    print(f"[baseline provenance OK] {checkpoint_dir.name}'s spiece.model matches the pinned snapshot exactly.")


def fingerprint_executable_code() -> dict[str, str]:
    result = {}
    for name in EXECUTABLE_CODE_FILES:
        path = TRAINING_DIR / name
        if not path.exists():
            raise ReplayPreflightError(f"Executable-code file missing: {path}")
        result[name] = file_fingerprint(path)
    return result


def fingerprint_governing_inputs() -> dict[str, str]:
    result = {}
    for rel in GOVERNING_INPUT_FILES:
        path = TRAINING_DIR / rel
        if not path.exists():
            raise ReplayPreflightError(f"Governing input file missing: {path}")
        result[rel] = file_fingerprint(path)
    return result


def load_frozen_fingerprints(path: Path = FROZEN_FINGERPRINTS_PATH) -> dict:
    if not path.exists():
        raise ReplayPreflightError(f"Missing frozen-fingerprints lock file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _compare_fingerprint_dicts(expected: dict[str, str], actual: dict[str, str], label: str) -> None:
    """Shared enforcement logic for both executable-code and
    governing-input checks: fails closed on a missing file, an extra
    unexpected file, or any fingerprint mismatch -- never just logs a
    warning and continues."""
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
    lock = lock if lock is not None else load_frozen_fingerprints()
    _compare_fingerprint_dicts(lock["executable_code"], fingerprint_executable_code(), "executable code")


def verify_frozen_governing_inputs(lock: dict | None = None) -> None:
    lock = lock if lock is not None else load_frozen_fingerprints()
    _compare_fingerprint_dicts(lock["governing_inputs"], fingerprint_governing_inputs(), "governing inputs")


def verify_pinned_dependency_versions(lock: dict | None = None) -> None:
    lock = lock if lock is not None else load_frozen_fingerprints()
    expected = lock["dependency_versions"]
    actual = environment_versions()
    mismatches = {name: (expected_v, actual.get(name)) for name, expected_v in expected.items() if actual.get(name) != expected_v}
    if mismatches:
        raise ReplayPreflightError(f"Dependency version drift detected (expected vs. installed): {mismatches}")
    print(f"[dependency versions OK] all {len(expected)} pinned package(s) match exactly.")


def verify_clean_working_tree(state: dict | None = None) -> None:
    state = state if state is not None else git_state()
    if not state["working_tree_clean"]:
        raise ReplayPreflightError(
            "Working tree is not clean -- refusing to proceed with an unreviewed, uncommitted diff present. "
            f"git status --porcelain:\n{state['working_tree_status_raw']}"
        )
    print("[working tree OK] clean, nothing uncommitted.")


def git_state() -> dict:
    def run(args: list[str]) -> str:
        return subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()

    head = run(["git", "rev-parse", "HEAD"])
    try:
        origin_main = run(["git", "rev-parse", "origin/main"])
    except subprocess.CalledProcessError:
        origin_main = None
    status_porcelain = run(["git", "status", "--porcelain"])
    return {
        "head_commit": head,
        "origin_main_commit": origin_main,
        "head_matches_origin_main": head == origin_main,
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


def build_receipt(experiment_dir: Path, planned_commands: list[str]) -> dict:
    """Assembles the full pre-execution receipt. Read-only: touches git,
    the filesystem, and already-imported module __version__ attributes --
    never loads a model or starts a subprocess."""
    receipt = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git": git_state(),
        "planned_commands": planned_commands,
        "environment": environment_versions(),
        "resolved_configuration": {
            "seed": 17,
            "data_dir": "data/processed_gold_v1.2.2_r2_v2contract_seed17",
            "checkpoint_dir": str((experiment_dir / "checkpoint").relative_to(TRAINING_DIR)),
            "contract": "v2",
            "governing_protocol": "training/controlled_seed17_r2_replay_protocol.md",
            "governing_manifest": "training/controlled_seed17_r2_replay_frozen_manifest.md",
        },
        "base_model": {
            "repo_id": HF_REPO_ID,
            "pinned_revision": PINNED_BASE_MODEL_REVISION,
            "file_fingerprints": PINNED_BASE_MODEL_FILE_FINGERPRINTS,
        },
        "executable_code_fingerprints": fingerprint_executable_code(),
        "governing_input_fingerprints": fingerprint_governing_inputs(),
    }
    return receipt


def run_logged_subprocess(cmd: list[str], cwd: Path, log_path: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    """Runs cmd via subprocess.run (never a shell pipe, which can also mask
    a failing exit code without `pipefail`) so the returned exit code is
    the real, unmasked process exit status. The log file is opened
    exclusively *before* the subprocess starts and passed directly as
    stdout (stderr merged in via stderr=subprocess.STDOUT) -- the OS writes
    the child's output to disk as it's produced, so a partial log survives
    even if the wrapper process itself is interrupted mid-run, unlike
    buffering everything in Python memory until the subprocess finishes."""
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


OFFLINE_ENV = {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--confirm-execute",
        action="store_true",
        help=(
            "Required to actually run anything. Without this flag the script only prints what it "
            "would do. Passing it is not itself authorization -- running this for real still "
            "requires Johnny naming this replay specifically, per the protocol's own §5 gate."
        ),
    )
    parser.add_argument("--experiment-dir", type=str, default=None)
    args = parser.parse_args()

    experiment_dir = (
        Path(args.experiment_dir)
        if args.experiment_dir
        else TRAINING_DIR / "controlled_seed17_r2_replay_run"
    )

    train_cmd = [
        sys.executable,
        "train.py",
        "--seed",
        "17",
        "--data-dir",
        "data/processed_gold_v1.2.2_r2_v2contract_seed17",
        "--output-dir",
        str((experiment_dir / "checkpoint").relative_to(TRAINING_DIR)),
    ]
    protected16_cmd = [
        sys.executable,
        "run_benchmark.py",
        "../datasets/benchmark/gold_v1.2.1_probes.jsonl",
        str((experiment_dir / "checkpoint" / "final").relative_to(TRAINING_DIR)),
        str((experiment_dir / "protected16_results.json").relative_to(TRAINING_DIR)),
        "--contract=v2",
    ]
    acceptance10_cmd = [
        sys.executable,
        "run_benchmark.py",
        "../datasets/benchmark/source_determined_items_v2_acceptance_draft.jsonl",
        str((experiment_dir / "checkpoint" / "final").relative_to(TRAINING_DIR)),
        str((experiment_dir / "acceptance10_results.json").relative_to(TRAINING_DIR)),
        "--contract=v2",
    ]
    planned = [" ".join(c) for c in (train_cmd, protected16_cmd, acceptance10_cmd)]

    if not args.confirm_execute:
        print("Dry run only (pass --confirm-execute to run for real). Planned sequence:")
        for line in planned:
            print(f"  $ {line}")
        print(f"Planned exclusive experiment directory: {experiment_dir}")
        return

    print("=== Preflight ===")
    lock = load_frozen_fingerprints()
    verify_clean_working_tree()
    verify_pinned_dependency_versions(lock)
    verify_frozen_executable_code(lock)
    verify_frozen_governing_inputs(lock)
    verify_pinned_base_model_snapshot()
    verify_baseline_checkpoint_used_pinned_snapshot(
        TRAINING_DIR / "checkpoints" / "gold_v1.2.2-v2contract-seed17" / "final"
    )
    create_exclusive_experiment_dir(experiment_dir)
    receipt = build_receipt(experiment_dir, planned)
    write_exclusive(experiment_dir / "receipt.json", json.dumps(receipt, indent=2, ensure_ascii=False))
    print(f"[receipt written] {experiment_dir / 'receipt.json'}")

    print("\n=== Training ===")
    proc = run_logged_subprocess(train_cmd, cwd=TRAINING_DIR, log_path=experiment_dir / "train_log.txt", env=OFFLINE_ENV)
    require_success(proc, "train.py")

    print("\n=== Evaluation: protected 16 ===")
    proc = run_logged_subprocess(
        protected16_cmd, cwd=TRAINING_DIR, log_path=experiment_dir / "protected16_log.txt", env=OFFLINE_ENV
    )
    require_success(proc, "run_benchmark.py (protected16)")

    print("\n=== Evaluation: acceptance 10 ===")
    proc = run_logged_subprocess(
        acceptance10_cmd, cwd=TRAINING_DIR, log_path=experiment_dir / "acceptance10_log.txt", env=OFFLINE_ENV
    )
    require_success(proc, "run_benchmark.py (acceptance10)")

    print(f"\nAll steps completed. Artifacts in {experiment_dir}")


if __name__ == "__main__":
    main()
