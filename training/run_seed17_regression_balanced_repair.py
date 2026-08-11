"""Execution wrapper for the controlled seed-17 regression-balanced repair
replay (training/seed17_regression_balanced_repair_execution_design_chatgpt.md,
training/seed17_regression_balanced_repair_execution_design_constants.json,
training/controlled_seed17_regression_balanced_repair_execution_frozen_manifest.md).

Authorized by Johnny directly (2026-08-11, "Claude should create, without
running training: ... The package must remain uncommitted for
[ChatGPT's] independent review") after the governing execution design was
independently reviewed by Claude (recomputing every fingerprint from
committed git blobs, cross-checking train.py's actual --max-steps/
scheduler mechanics and this repository's own established steps-per-epoch
convention rather than assuming, and finding one non-blocking arithmetic
correction -- see this file's own FROZEN_FINGERPRINTS lock and the frozen
manifest's review notes). This module performs no compute on import, and
`main()` refuses to start any real subprocess unless invoked with the
explicit `--confirm-execute` flag, which nothing in this codebase sets
automatically. Possession of that flag is not itself authorization --
running this for real still requires a separate, explicit go-ahead after
the committed package has passed joint review, exactly as every prior
replay in this project has required.

Runs two independently initialized training + evaluation sequences from
the same pinned base-model snapshot, never resuming one from the other,
BOTH at exactly 720 optimizer steps via one explicit `--max-steps 720`
argument each -- isolating the corpus revision from an optimizer-step
confound (train.py's own --max-steps docstring: it "overrides
num_train_epochs with an exact optimizer-step budget... including the
default linear LR scheduler's total-steps count", so both arms get a
complete, symmetric decay-to-zero schedule ending at step 720):

- treatment: 85-record regression-balanced-repair candidate corpus, 79
  train / 6 validation. The sole decision-bearing candidate. Its first 78
  records are byte-identical to the comparator candidate; the remaining 7
  are the reviewed proposal delta, in order.
- comparator: the preserved 78-record Phase-2 candidate corpus, 72 train /
  6 validation -- the SAME comparator corpus and paths as the prior
  contrastive-replay package. A diagnostic corpus comparator only -- can
  strengthen or weaken causal interpretation, never a substitute for the
  treatment.

Extends training/run_seed17_contrastive_replay.py's already-reviewed
design (checkout-portable canonicalization for every governing input and
every executable-code closure file; a pre-execution receipt written
before any subprocess starts; atomic `exist_ok=False` experiment-directory
creation; interruption-safe logging via an exclusively-opened log file
passed directly as subprocess stdout; raw benchmark result validation;
exact optimizer-step verification against Trainer's own trainer_state.json)
with the requirements specific to this package:

1. Every executable byte, path, fingerprint, command, test, and import is
   re-derived and independently re-verified against the actual committed
   git blobs at this package's own pinned parent commit
   (90ee08d17304e5a124f15f19f9644a1f609083ba) -- never copied from the
   prior package's lock file, even where the underlying files (train.py,
   run_benchmark.py, report_benchmark.py, and their shared dependencies)
   are unchanged and so happen to hash identically.
2. Treatment-candidate structural verification against the comparator
   (governing execution design section 4.1 / preflight item 9): the first
   78 records of the treatment candidate must be byte-identical to the
   full comparator candidate, and the remaining 7 records must match the
   reviewed proposal's `input` text, in order. Implemented as an
   independent re-check at execution time
   (verify_treatment_candidate_equals_comparator_plus_delta) of a
   relationship the corpus-implementation script already enforced during
   construction -- never trusted from that prior verification alone.
3. Extended proposal-membership verification (governing execution design
   preflight item 8): all 7 reviewed proposal records must resolve (via
   the real v2 prompt-builder, not string matching) to prompts that occur
   exactly once in treatment train, zero times in treatment validation,
   AND zero times anywhere in the comparator (train or validation) -- the
   comparator check is new relative to the prior package, where treatment
   and comparator were unrelated corpora and no such cross-arm membership
   claim applied.
4. Symmetric `--max-steps 720` for both arms (same shape as the prior
   contrastive-replay package, not the earlier primary/control package
   that had one natural/omitted-flag arm).
5. Gate-6's explicit pass set is unchanged from every prior seed-17 replay
   package (same six frozen semantic gates, same required-pass set),
   encoded here as data for later scoring-verification tooling to import.
6. `ensure_real_validation_placeholder()`: unchanged design and unchanged
   finding -- `datasets/real_validation.jsonl` has no committed blob of
   its own (covered by the committed, tracked `datasets/.gitignore`), so a
   fresh worktree or clone at the pinned milestone will not have it on
   disk. Called only from `bootstrap_clean_tree_then_real_validation()`,
   strictly after `verify_clean_working_tree()` has already passed for the
   pre-mutation state.

Independent review note on the governing execution design (recorded here,
not silently corrected): Claude's review of the original draft found
section 3 self-inconsistent -- it stated the treatment's 79-record train
split reaches "approximately 36.46 epoch-equivalents" at 720 steps, in the
same paragraph as the (correct) claim that a natural 40-epoch treatment
schedule would reach 800 steps. These two figures were mutually
inconsistent -- if 40 epochs is 800 steps, steps-per-epoch is exactly 20
(matching this codebase's actual, ceiling-based `dataloader_drop_last=False`
behavior, and the identical convention already established in
`gold_v1.2.3_groupscreen_seed17_scoring.md`), which makes 720 steps exactly
36.0 epoch-equivalents, not 36.46. Confirmed non-blocking at the time
(changed no gate, hash, or authorization). **The governing design document
has since been corrected** (its own section 3 now reads "exactly 36.0
epoch-equivalents... (`ceil(79 / 4) = 20` optimizer steps per epoch)"),
independently reconfirmed by re-reading the document and re-hashing it
(canonical LF SHA-256 `fe316fb1ee919f9f56ba01be559be1fa7781135f9610ceacca4990637bba6fa6`,
changed from the pre-correction `ceac0d2f8ae3d93ad1bd2b57ffaff453c3d444fda8233239a9a0d84c437bedb9`
originally cited when this review began -- confirmed via a full line-by-line
comparison that this is the ONLY change in the document). No pinned
constant in this module ever depended on the "36.46" figure; TREATMENT_STEPS
is 720 either way.

Usage:
    python run_seed17_regression_balanced_repair.py [--confirm-execute] [--experiment-dir DIR]
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
FROZEN_FINGERPRINTS_PATH = TRAINING_DIR / "controlled_seed17_regression_balanced_repair_execution_frozen_fingerprints.json"

# This package's corpus baseline and its execution-package parent commit
# are the same commit -- unlike the prior contrastive-replay package
# (whose lock had already advanced past one corrective round by the time
# it was finalized), this is a first-time implementation with no prior
# correction round yet. If a future correction advances PINNED_PARENT_COMMIT
# past this value, CORPUS_BASELINE_COMMIT stays fixed as documentation of
# where the corpus/split/benchmark inputs are actually pinned.
CORPUS_BASELINE_COMMIT = "90ee08d17304e5a124f15f19f9644a1f609083ba"
PINNED_PARENT_COMMIT = "90ee08d17304e5a124f15f19f9644a1f609083ba"

EXPECTED_PACKAGE_COMMIT_FILES = frozenset({
    "training/seed17_regression_balanced_repair_execution_design_chatgpt.md",
    "training/seed17_regression_balanced_repair_execution_design_constants.json",
    "training/controlled_seed17_regression_balanced_repair_execution_frozen_manifest.md",
    "training/controlled_seed17_regression_balanced_repair_execution_frozen_fingerprints.json",
    "training/run_seed17_regression_balanced_repair.py",
    "training/test_run_seed17_regression_balanced_repair.py",
    "training/controlled_seed17_regression_balanced_repair_execution_manifest_dryrun_receipt_sample.json",
})

HF_REPO_ID = "google/flan-t5-base"
PINNED_BASE_MODEL_REVISION = "7bcac572ce56db69c1ea7c8af255c5d7c9672fc2"
# Unchanged from every prior seed-17 replay package -- same base model,
# same pinned snapshot, independently reverified against the local HF
# cache this round via verify_pinned_base_model_snapshot(), not copied
# forward without re-checking.
PINNED_BASE_MODEL_FILE_FINGERPRINTS = {
    "config.json": "7c1853dbfa0e4aac093eb109a358b6ab25fe86b7c15185a91322f0ed26f0f940",
    "generation_config.json": "f5a1c7e2be8092018d8835128987edf0111637dd98e90599cc80310fef75d95a",
    "model.safetensors": "1dfb70afdcedceb9f9fae2f9b68e004ad934361fb35b9b2bd50b45ea90790fc8",
    "special_tokens_map.json": "5c87151ef0f72a99d1f766a4c418bd2a1f90aaa30a8e22fe5eca9641daebb64f",
    "spiece.model": "d60acb128cf7b7f2536e8f38a5b18a05535c9e14c7a355904270e15b0945ea86",
    "tokenizer.json": "fe2ebbbbde2985be723e0ce18217853e4020c5e9d35bd07be2c27ab9d3ead57a",
    "tokenizer_config.json": "4c55124402e4ce48c7125d04b9af152a125eda9e7c80829f8f99f2ec69f3f68d",
}

EXECUTABLE_CODE_ENTRY_POINTS = [
    "run_seed17_regression_balanced_repair.py",
    "train.py",
    "run_benchmark.py",
    "report_benchmark.py",
]

# ---------------------------------------------------------------------------
# Dual-arm frozen inputs. Every fingerprint below is the CANONICAL LF git-
# blob hash, independently recomputed from `git show HEAD:<path>` at
# 90ee08d17304e5a124f15f19f9644a1f609083ba during Claude's review -- never
# copied from any prior package's lock file, even where a value turns out
# identical (the comparator arm below is byte-for-byte the same corpus,
# same paths, as the prior contrastive-replay package's comparator arm;
# every one of its fingerprints was still independently recomputed fresh,
# not carried forward on the assumption of no drift).
# ---------------------------------------------------------------------------

TREATMENT_CANDIDATE_REL = "gold_v1.2.2_regression_balanced_repair_candidate.jsonl"
TREATMENT_DATA_DIR_REL = "data/processed_gold_v1.2.2_regression_balanced_repair_v2contract_seed17"
TREATMENT_TRAIN_REL = f"{TREATMENT_DATA_DIR_REL}/train.jsonl"
TREATMENT_VAL_REL = f"{TREATMENT_DATA_DIR_REL}/val.jsonl"
TREATMENT_PROPOSAL_REL = "regression_balanced_repair_proposal.jsonl"

COMPARATOR_CANDIDATE_REL = "gold_v1.2.2_phase2_derived_candidate.jsonl"
COMPARATOR_DATA_DIR_REL = "data/processed_gold_v1.2.2_phase2_v2contract_seed17"
COMPARATOR_TRAIN_REL = f"{COMPARATOR_DATA_DIR_REL}/train.jsonl"
COMPARATOR_VAL_REL = f"{COMPARATOR_DATA_DIR_REL}/val.jsonl"

PROTECTED_BENCHMARK_REL = "../datasets/benchmark/gold_v1.2.1_probes.jsonl"
ACCEPTANCE_BENCHMARK_REL = "../datasets/benchmark/source_determined_items_v2_acceptance_draft.jsonl"
REAL_VALIDATION_REL_PATH = "../datasets/real_validation.jsonl"

# rel_path -> expected canonical-LF SHA-256. All nine independently
# recomputed from committed git blobs at 90ee08d17304e5a124f15f19f9644a1f609083ba.
CANONICAL_LF_GOVERNING_INPUTS: dict[str, str] = {
    TREATMENT_CANDIDATE_REL: "955437e2ac014c3e48402867e51ac539334e907d61d05dde6e7d7da1ded254ea",
    TREATMENT_TRAIN_REL: "7b76450be9f38447b8d5d0acc88d9b3683fd68a3af834961c425f50a97024578",
    TREATMENT_VAL_REL: "8aa99a794f495cf75e6904ee28789e06ac43c1f9ee424f0b2ce2f219527623c4",
    TREATMENT_PROPOSAL_REL: "192372fd44fc87ea879d2ab7b751a3d54be100b447b886c213b26553284a747a",
    COMPARATOR_CANDIDATE_REL: "6e9e5f1bea8fc3cbcb615376a1d055bd273605d0f8c1e40a8c120720c8cb836c",
    COMPARATOR_TRAIN_REL: "8760378519365c4fe2ae4dcebdc6379214cc0fcf93442521f64d6d4508bafae6",
    COMPARATOR_VAL_REL: "8aa99a794f495cf75e6904ee28789e06ac43c1f9ee424f0b2ce2f219527623c4",
    PROTECTED_BENCHMARK_REL: "767fe21a1097b51cef38728dcff0ff9ca4cf280bde8e65a7d885729f40990c0f",
    ACCEPTANCE_BENCHMARK_REL: "b8fe4d4178e5b508757db998eacb1ee979518697c8df759ba1739227c88d448e",
}

EXPECTED_PROTECTED_COUNT = 16
EXPECTED_ACCEPTANCE_COUNT = 10

TREATMENT_EXPECTED_CANDIDATE_COUNT = 85
TREATMENT_EXPECTED_TRAIN_COUNT = 79
TREATMENT_EXPECTED_VAL_COUNT = 6
TREATMENT_EXPECTED_TRAINING_DATA_FINGERPRINT = "badfed9f946bd13379e1f74336b18c596c922cf378cc3853ea95a2098ea03800"
TREATMENT_EXPECTED_PROPOSAL_COUNT = 7

COMPARATOR_EXPECTED_CANDIDATE_COUNT = 78
COMPARATOR_EXPECTED_TRAIN_COUNT = 72
COMPARATOR_EXPECTED_VAL_COUNT = 6
COMPARATOR_EXPECTED_TRAINING_DATA_FINGERPRINT = "9d6817152087685b653830ad671f9304e4226b095a202ca57f5ca52bc3a14c1f"

EXPECTED_CUDA_AVAILABLE = True

TREATMENT_STEPS = 720
COMPARATOR_STEPS = 720

GATE6_REQUIRED_PASS_SET = frozenset({"01", "03", "04", "05", "06", "07", "09", "10", "12", "13", "14", "15", "16"})


class ReplayPreflightError(SystemExit):
    pass


def file_fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Checkout-portable canonicalization (ported from
# prepare_phase2_contrastive_candidate_corpus.py's canonicalize_pinned_lf_bytes,
# via run_seed17_contrastive_replay.py -- re-derived here directly, not
# imported, so this wrapper's import closure stays self-contained)
# ---------------------------------------------------------------------------

CANONICAL_LF = b"\n"


def canonicalize_pinned_lf_bytes(raw: bytes, expected_fingerprint: str, label: str) -> bytes:
    """Accepts only two forms of a pinned, LF-committed file: the exact
    canonical LF bytes, or a uniform CRLF re-encoding of exactly those
    same bytes -- the only difference a stock Windows checkout
    (`core.autocrlf=true`) can introduce. Normalizes the latter to LF and
    independently re-verifies the *normalized* result against the pinned
    fingerprint before ever trusting it. Rejects, with a specific
    diagnostic: a UTF-8 BOM; any bare carriage return not followed by a
    line feed; mixed CRLF/bare-LF line endings; a missing terminal
    newline; and -- via the final fingerprint re-check -- blank-line
    drift, whitespace drift, or any other real content change."""
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ReplayPreflightError(f"FATAL: {label} begins with a UTF-8 BOM. Refusing to proceed against an altered input.")

    if b"\r" not in raw:
        if raw and not raw.endswith(b"\n"):
            raise ReplayPreflightError(f"FATAL: {label} is missing its terminal newline. Refusing to proceed against an altered input.")
        canonical = raw
    else:
        bare_cr = raw.count(b"\r") - raw.count(b"\r\n")
        bare_lf = raw.count(b"\n") - raw.count(b"\r\n")
        if bare_cr:
            raise ReplayPreflightError(
                f"FATAL: {label} contains {bare_cr} bare carriage return(s) not followed by a line feed. "
                "Refusing to proceed against an altered input."
            )
        if bare_lf:
            raise ReplayPreflightError(
                f"FATAL: {label} has mixed line endings ({bare_lf} bare LF alongside CRLF). "
                "Refusing to proceed against an altered input."
            )
        if not raw.endswith(b"\r\n"):
            raise ReplayPreflightError(f"FATAL: {label} is missing its terminal newline. Refusing to proceed against an altered input.")
        canonical = raw.replace(b"\r\n", CANONICAL_LF)

    actual = hashlib.sha256(canonical).hexdigest()
    if actual != expected_fingerprint:
        raise ReplayPreflightError(
            f"FATAL: {label}, after canonicalizing to LF, does not match the pinned canonical fingerprint: "
            f"expected {expected_fingerprint}, got {actual}. Refusing to proceed against an unpinned or altered input."
        )
    return canonical


def load_canonical_governing_inputs() -> dict[str, bytes]:
    """Canonicalizes and returns all nine governing inputs' verified
    bytes, keyed by rel_path. Called once per preflight run; downstream
    checks (counts, splits, proposal membership, treatment-equals-
    comparator-plus-delta) parse from these same verified bytes, never a
    second unverified read of the file at its path."""
    result: dict[str, bytes] = {}
    for rel_path, expected_fp in CANONICAL_LF_GOVERNING_INPUTS.items():
        path = TRAINING_DIR / rel_path
        if not path.exists():
            raise ReplayPreflightError(f"Missing required governing input: {path}")
        raw = path.read_bytes()
        canonical = canonicalize_pinned_lf_bytes(raw, expected_fp, rel_path)
        form = "already canonical LF" if raw == canonical else "uniform-CRLF checkout, normalized to canonical LF"
        print(f"[fingerprint OK] {rel_path}: {expected_fp} ({form})")
        result[rel_path] = canonical
    return result


def parse_jsonl_records_from_bytes(data: bytes) -> list[dict]:
    text = data.decode("utf-8")
    return [json.loads(line) for line in text.split("\n") if line.strip()]


def verify_real_validation_empty() -> None:
    """train.py always calls run_real_validation_evaluation after
    training, which reads this exact file -- a nonempty file would let
    undeclared private-data inference into a replay whose authorized
    evaluation scope is only the frozen 26 benchmark cases. Fails closed
    on both a missing file and a non-empty one. See
    ensure_real_validation_placeholder() for the separate, explicit,
    opt-in step that creates this file when a fresh worktree/clone
    doesn't have it -- that step never lives inside this or any other
    verify_* function, which must never mutate anything."""
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


def ensure_real_validation_placeholder() -> None:
    """`datasets/real_validation.jsonl` has no committed blob of its own
    at this path in the working tree until this step runs (the file is
    listed in the committed, tracked `datasets/.gitignore`, so a fresh
    worktree or clone at the pinned milestone will not have it on disk,
    even though the main Windows checkout does). This step exists ONLY to
    bridge that gap: if the file is already present, it does nothing and
    logs that fact; if absent, it creates a genuinely empty file at the
    exact expected path and logs that it did so, explicitly and loudly.
    It never runs inside verify_real_validation_empty() or any other
    verify_* function -- this wrapper's verify_* functions must never
    mutate anything.

    Must only ever be called AFTER verify_clean_working_tree() has
    already passed for the pre-mutation state -- see
    bootstrap_clean_tree_then_real_validation(). Verifying before any
    mutation is the more robust default regardless of whether
    `datasets/.gitignore` continues to cover this exact path."""
    path = TRAINING_DIR / REAL_VALIDATION_REL_PATH
    if path.exists():
        print(f"[real-validation placeholder] {path} already present, not touched.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")
    print(f"[real-validation placeholder] {path} was absent; created genuinely empty.")


def bootstrap_clean_tree_then_real_validation(state: dict) -> None:
    """The exact required ordering: verify the working tree is clean
    BEFORE ever creating the real-validation placeholder file, then
    create it, then verify it is byte-empty. Isolating this as its own
    function makes the sequence itself directly unit-testable against a
    real scratch git repository, not just its two halves independently."""
    verify_clean_working_tree(state)
    ensure_real_validation_placeholder()
    verify_real_validation_empty()


def load_frozen_fingerprints(path: Path = FROZEN_FINGERPRINTS_PATH) -> dict:
    if not path.exists():
        raise ReplayPreflightError(f"Missing frozen-fingerprints lock file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Import-closure computation (unchanged design from the prior wrapper)
# ---------------------------------------------------------------------------


def local_imports_of(path: Path) -> set[str]:
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


def verify_frozen_executable_code(lock: dict | None = None) -> dict[str, bytes]:
    """Canonicalizes each closure file exactly like the nine governing
    data inputs: accepts the pinned canonical LF bytes or a uniform CRLF
    re-encoding of exactly those bytes, rejects everything else -- a
    stock Windows checkout (`core.autocrlf=true`) materializes every text
    file with CRLF on a genuine `git worktree add`/clone/checkout,
    regardless of what's actually stored, so a flat hash comparison
    against raw checkout bytes would fail closed for the wrong reason (a
    real prior package found exactly this). The closure-set comparison (a
    new or removed local import) runs first, independent of any
    byte-level check.

    Returns the verified canonical-LF byte map, keyed by filename, so
    callers never need a second, unverified raw read of these files --
    build_receipt() consumes this exact map rather than re-reading raw
    checkout bytes, which would silently reintroduce a platform-dependent
    value into the receipt even after this check had already passed."""
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
    canonical_bytes: dict[str, bytes] = {}
    for name in sorted(current_closure):
        raw = (TRAINING_DIR / name).read_bytes()
        canonical_bytes[name] = canonicalize_pinned_lf_bytes(raw, expected[name], f"executable code: {name}")
    print(f"[executable code OK] all {len(current_closure)} file(s) match the frozen lock file exactly (checkout-portable).")
    return canonical_bytes


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
    """Strict check: `git status --porcelain == ''`. Run this wrapper
    from a fresh linked worktree or fresh clone at the pinned commit
    specifically because the main Windows checkout deliberately carries
    legitimate untracked historical artifacts that would otherwise always
    fail this check. This function itself never allowlists anything."""
    state = state if state is not None else git_state()
    if not state["working_tree_clean"]:
        raise ReplayPreflightError(
            "Working tree is not clean -- refusing to proceed with an unreviewed, uncommitted diff "
            f"present. git status --porcelain:\n{state['working_tree_status_raw']}\n"
            "If this is the main checkout, run from a fresh linked worktree or fresh clone at the "
            "pinned commit instead."
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
    state = state if state is not None else git_state()
    if state["head_parent_commit"] != PINNED_PARENT_COMMIT:
        raise ReplayPreflightError(
            f"HEAD's parent is {state['head_parent_commit']}, expected the pinned parent commit "
            f"{PINNED_PARENT_COMMIT}. The package commit must be a direct child of the reviewed "
            "corpus-implementation milestone -- not that commit itself, not a later descendant, and "
            "not a commit on a different history, unless both reviewers explicitly approve a revised "
            "lineage before implementation."
        )
    changed = set(state["changed_files_since_parent"] or [])
    if changed != EXPECTED_PACKAGE_COMMIT_FILES:
        missing = sorted(EXPECTED_PACKAGE_COMMIT_FILES - changed)
        extra = sorted(changed - EXPECTED_PACKAGE_COMMIT_FILES)
        raise ReplayPreflightError(
            f"The commit delta from the pinned parent to HEAD does not contain exactly the "
            f"{len(EXPECTED_PACKAGE_COMMIT_FILES)} reviewed package files. Missing: {missing}. "
            f"Unexpected extra (unreviewed file riding along in the same commit): {extra}."
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
# Dual-arm split / training-data fingerprint / proposal-membership /
# treatment-equals-comparator-plus-delta verification -- all parsed from
# the already-canonicalized bytes load_canonical_governing_inputs()
# returns, never a second unverified read.
# ---------------------------------------------------------------------------


def canonical_training_data_fingerprint(records: list[dict]) -> str:
    sortable = sorted(records, key=lambda r: r["prompt"])
    blob = json.dumps(sortable, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def verify_arm_split_and_fingerprint(
    canonical_inputs: dict[str, bytes],
    candidate_rel: str,
    train_rel: str,
    val_rel: str,
    expected_candidate_count: int,
    expected_train_count: int,
    expected_val_count: int,
    expected_training_data_fingerprint: str,
    arm_label: str,
) -> None:
    candidate = parse_jsonl_records_from_bytes(canonical_inputs[candidate_rel])
    if len(candidate) != expected_candidate_count:
        raise ReplayPreflightError(
            f"{arm_label}: candidate corpus has {len(candidate)} record(s), expected exactly {expected_candidate_count}."
        )
    train_pairs = parse_jsonl_records_from_bytes(canonical_inputs[train_rel])
    val_pairs = parse_jsonl_records_from_bytes(canonical_inputs[val_rel])
    if len(train_pairs) != expected_train_count:
        raise ReplayPreflightError(f"{arm_label}: train split has {len(train_pairs)} record(s), expected exactly {expected_train_count}.")
    if len(val_pairs) != expected_val_count:
        raise ReplayPreflightError(f"{arm_label}: val split has {len(val_pairs)} record(s), expected exactly {expected_val_count}.")

    fp = canonical_training_data_fingerprint(train_pairs + val_pairs)
    if fp != expected_training_data_fingerprint:
        raise ReplayPreflightError(
            f"{arm_label}: canonical training-data fingerprint mismatch: expected {expected_training_data_fingerprint}, got {fp}."
        )
    print(
        f"[split OK] {arm_label}: candidate={len(candidate)}, train={len(train_pairs)}, val={len(val_pairs)}; "
        f"training-data fingerprint matches: {fp}"
    )


def verify_treatment_candidate_equals_comparator_plus_delta(canonical_inputs: dict[str, bytes]) -> None:
    """Governing execution design section 4.1 / preflight item 9: 'the
    first 78 candidate records must remain byte-identical to the
    preserved comparator corpus, followed by the reviewed seven-record
    delta in manifest order.' This is an independent re-check at
    execution time of a relationship the corpus-implementation script
    already enforced during construction (verify_baseline_preserved_byte_for_byte
    / verify_proposal_appended_in_order in
    prepare_regression_balanced_repair_candidate_corpus.py) -- never
    trusted from that prior verification alone. Operates on the already-
    canonicalized (LF) bytes; a genuine fresh checkout of the treatment
    candidate is pure LF as written by the corpus script, while the
    comparator candidate is a pre-existing git-tracked file materialized
    with CRLF under this repository's core.autocrlf=true -- comparing raw
    checkout bytes directly would produce a false mismatch for a reason
    having nothing to do with content, which is exactly why this operates
    on canonical_inputs rather than re-reading either path."""
    treatment_bytes = canonical_inputs[TREATMENT_CANDIDATE_REL]
    comparator_bytes = canonical_inputs[COMPARATOR_CANDIDATE_REL]
    if treatment_bytes[: len(comparator_bytes)] != comparator_bytes:
        raise ReplayPreflightError(
            "treatment candidate's leading records are not byte-identical to the comparator candidate -- "
            "the required byte-preserved-prefix relationship does not hold."
        )
    tail_bytes = treatment_bytes[len(comparator_bytes) :]
    tail_records = parse_jsonl_records_from_bytes(tail_bytes)
    proposal_records = parse_jsonl_records_from_bytes(canonical_inputs[TREATMENT_PROPOSAL_REL])
    if len(tail_records) != len(proposal_records):
        raise ReplayPreflightError(
            f"treatment candidate's tail has {len(tail_records)} record(s) after the comparator "
            f"prefix, expected exactly {len(proposal_records)} (the reviewed proposal record count)."
        )
    tail_inputs = [r.get("input") for r in tail_records]
    proposal_inputs = [r.get("input") for r in proposal_records]
    if tail_inputs != proposal_inputs:
        raise ReplayPreflightError(
            "treatment candidate's tail records do not match the reviewed proposal's input text, in "
            "order -- refusing to proceed against an unreviewed or reordered delta."
        )
    print(
        f"[treatment=comparator+delta OK] treatment candidate's first {len(comparator_bytes)} byte(s) "
        f"are byte-identical to the comparator candidate; the remaining {len(tail_records)} record(s) "
        "match the reviewed proposal's input text exactly, in order."
    )


def verify_treatment_proposal_membership(canonical_inputs: dict[str, bytes]) -> None:
    """Governing execution design preflight item 8: all 7 proposal
    records must resolve (via the real v2 prompt-builder, not string
    matching) to prompts that occur exactly once in treatment train, zero
    times in treatment validation, AND zero times anywhere in the
    comparator (train or validation combined). The comparator check is
    new relative to the prior contrastive-replay package, where treatment
    and comparator were unrelated corpora with no such cross-arm
    membership claim -- here the comparator is literally the treatment's
    own 78-record prefix, so an accidental comparator-side leak of a
    'new' record would mean it was never actually new."""
    import prompt_contract_v2_candidate as v2_candidate

    proposal = parse_jsonl_records_from_bytes(canonical_inputs[TREATMENT_PROPOSAL_REL])
    if len(proposal) != TREATMENT_EXPECTED_PROPOSAL_COUNT:
        raise ReplayPreflightError(
            f"treatment proposal membership: proposal has {len(proposal)} record(s), "
            f"expected exactly {TREATMENT_EXPECTED_PROPOSAL_COUNT}."
        )
    expected_prompts = {v2_candidate.build_prompt(r["input"]) for r in proposal}
    if len(expected_prompts) != len(proposal):
        raise ReplayPreflightError("treatment proposal membership: duplicate input hash within the proposal.")

    train_pairs = parse_jsonl_records_from_bytes(canonical_inputs[TREATMENT_TRAIN_REL])
    val_pairs = parse_jsonl_records_from_bytes(canonical_inputs[TREATMENT_VAL_REL])
    comparator_train_pairs = parse_jsonl_records_from_bytes(canonical_inputs[COMPARATOR_TRAIN_REL])
    comparator_val_pairs = parse_jsonl_records_from_bytes(canonical_inputs[COMPARATOR_VAL_REL])

    train_prompts = {p["prompt"] for p in train_pairs}
    val_prompts = {p["prompt"] for p in val_pairs}
    comparator_prompts = {p["prompt"] for p in comparator_train_pairs} | {p["prompt"] for p in comparator_val_pairs}

    missing_from_train = expected_prompts - train_prompts
    if missing_from_train:
        raise ReplayPreflightError(
            f"treatment proposal membership: {len(missing_from_train)} proposal record(s) are absent "
            "from treatment train."
        )
    present_in_val = expected_prompts & val_prompts
    if present_in_val:
        raise ReplayPreflightError(
            f"treatment proposal membership: {len(present_in_val)} proposal record(s) are present in "
            "treatment validation -- validation must remain exactly the frozen split."
        )
    present_in_comparator = expected_prompts & comparator_prompts
    if present_in_comparator:
        raise ReplayPreflightError(
            f"treatment proposal membership: {len(present_in_comparator)} proposal record(s) are "
            "present in the comparator (train or validation) -- a 'new' record must not already exist "
            "in the comparator corpus this repair is being compared against."
        )
    print(
        f"[proposal membership OK] all {len(proposal)} proposal record(s) resolve to prompts present "
        "in treatment train, absent from treatment validation, and absent from the comparator entirely."
    )


def verify_benchmark_counts(canonical_inputs: dict[str, bytes]) -> None:
    protected = parse_jsonl_records_from_bytes(canonical_inputs[PROTECTED_BENCHMARK_REL])
    acceptance = parse_jsonl_records_from_bytes(canonical_inputs[ACCEPTANCE_BENCHMARK_REL])
    if len(protected) != EXPECTED_PROTECTED_COUNT:
        raise ReplayPreflightError(f"Protected benchmark has {len(protected)} record(s), expected exactly {EXPECTED_PROTECTED_COUNT}.")
    if len(acceptance) != EXPECTED_ACCEPTANCE_COUNT:
        raise ReplayPreflightError(f"Acceptance benchmark has {len(acceptance)} record(s), expected exactly {EXPECTED_ACCEPTANCE_COUNT}.")
    ids = [b["id"] for b in protected] + [b["id"] for b in acceptance]
    if len(set(ids)) != len(ids):
        raise ReplayPreflightError("Benchmark IDs are not unique across protected + acceptance.")
    print(f"[benchmark counts OK] protected={len(protected)}, acceptance={len(acceptance)}, all IDs unique.")


# ---------------------------------------------------------------------------
# Command construction and self-verification
# ---------------------------------------------------------------------------


def build_commands(treatment_dir: Path, comparator_dir: Path) -> dict[str, list[str]]:
    def train_cmd(output_dir: Path, data_dir_rel: str, max_steps: int) -> list[str]:
        return [
            sys.executable,
            "train.py",
            "--seed",
            "17",
            "--data-dir",
            data_dir_rel,
            "--output-dir",
            str(output_dir.relative_to(TRAINING_DIR)),
            "--max-steps",
            str(max_steps),
        ]

    def eval_cmd(benchmark_rel: str, checkpoint_dir: Path, output_json: Path) -> list[str]:
        return [
            sys.executable,
            "run_benchmark.py",
            benchmark_rel,
            str((checkpoint_dir / "final").relative_to(TRAINING_DIR)),
            str(output_json.relative_to(TRAINING_DIR)),
            "--contract=v2",
        ]

    treatment_checkpoint = treatment_dir / "checkpoint"
    comparator_checkpoint = comparator_dir / "checkpoint"

    return {
        "treatment_train": train_cmd(treatment_checkpoint, TREATMENT_DATA_DIR_REL, TREATMENT_STEPS),
        "treatment_protected16": eval_cmd(PROTECTED_BENCHMARK_REL, treatment_checkpoint, treatment_dir / "protected16_results.json"),
        "treatment_acceptance10": eval_cmd(ACCEPTANCE_BENCHMARK_REL, treatment_checkpoint, treatment_dir / "acceptance10_results.json"),
        "comparator_train": train_cmd(comparator_checkpoint, COMPARATOR_DATA_DIR_REL, COMPARATOR_STEPS),
        "comparator_protected16": eval_cmd(PROTECTED_BENCHMARK_REL, comparator_checkpoint, comparator_dir / "protected16_results.json"),
        "comparator_acceptance10": eval_cmd(ACCEPTANCE_BENCHMARK_REL, comparator_checkpoint, comparator_dir / "acceptance10_results.json"),
    }


def verify_command_shape(commands: dict[str, list[str]]) -> None:
    """Self-verification of build_commands()'s own output: both training
    commands resolve to seed 17, each resolves to its OWN arm's data
    directory (never the other's -- explicit cross-arm confusion check),
    and each has exactly one `--max-steps 720` argument -- both arms
    symmetric."""
    arm_data_dirs = {"treatment_train": TREATMENT_DATA_DIR_REL, "comparator_train": COMPARATOR_DATA_DIR_REL}
    for key, expected_data_dir in arm_data_dirs.items():
        cmd = commands[key]
        if "--seed" not in cmd or cmd[cmd.index("--seed") + 1] != "17":
            raise ReplayPreflightError(f"{key}: does not resolve to seed 17: {cmd}")
        if "--data-dir" not in cmd or cmd[cmd.index("--data-dir") + 1] != expected_data_dir:
            raise ReplayPreflightError(f"{key}: does not resolve to its own pinned data directory: {cmd}")
        other_data_dir = COMPARATOR_DATA_DIR_REL if key == "treatment_train" else TREATMENT_DATA_DIR_REL
        if other_data_dir in cmd:
            raise ReplayPreflightError(f"{key}: unexpectedly references the OTHER arm's data directory: {cmd}")

        max_steps_occurrences = [i for i, a in enumerate(cmd) if a == "--max-steps"]
        if len(max_steps_occurrences) != 1:
            raise ReplayPreflightError(f"{key}: expected exactly one --max-steps argument, found {len(max_steps_occurrences)}: {cmd}")
        idx = max_steps_occurrences[0]
        if cmd[idx + 1] != "720":
            raise ReplayPreflightError(f"{key}: --max-steps value is {cmd[idx + 1]!r}, expected '720': {cmd}")

    treatment_out = commands["treatment_train"][commands["treatment_train"].index("--output-dir") + 1]
    comparator_out = commands["comparator_train"][commands["comparator_train"].index("--output-dir") + 1]
    if treatment_out == comparator_out:
        raise ReplayPreflightError(f"treatment/comparator output directories collide: {treatment_out!r}")

    print("[command shape OK] both arms resolve to seed 17, their own (never the other's) data directory, exactly one --max-steps 720, and non-overlapping output directories.")


# ---------------------------------------------------------------------------
# Execution primitives (unchanged design from the prior wrapper)
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


def verify_raw_result_artifact(result_path: Path, benchmark_records: list[dict], expected_count: int, label: str) -> None:
    """Parameterized on the already-canonicalized benchmark records
    rather than re-reading the benchmark path itself."""
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

    expected_ids = [b["id"] for b in benchmark_records]
    actual_ids = [r.get("id") for r in results]
    if actual_ids != expected_ids:
        raise ReplayPreflightError(
            f"{label}: raw result IDs/order do not match the benchmark file exactly. "
            f"Expected: {expected_ids}. Got: {actual_ids}."
        )
    probes_by_id = {b["id"]: b for b in benchmark_records}

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
            f"{expected_steps}. A mismatch is an invalid experiment (RBR17-X) even though the subprocess exited 0."
        )
    print(f"[step count OK] {run_name}: {last_checkpoint.name}/trainer_state.json confirms exactly {actual_steps} step(s).")


def build_receipt(experiment_dir: Path, commands: dict[str, list[str]], executable_code_canonical: dict[str, bytes]) -> dict:
    """Read-only: touches git, the filesystem, and already-imported
    module __version__ attributes -- never loads a model or starts a
    subprocess. Only hashes the already-verified canonical-LF bytes
    verify_frozen_executable_code() returned this run, never a second raw
    read of those files (which on a genuine fresh CRLF checkout would
    silently write a platform-dependent fingerprint into the receipt even
    after verification had already passed against the canonical form)."""
    state = git_state()
    receipt = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git": state,
        "package_commit": state["head_commit"],
        "package_commit_parent": PINNED_PARENT_COMMIT,
        "planned_commands": {
            "treatment": [" ".join(commands["treatment_train"]), " ".join(commands["treatment_protected16"]), " ".join(commands["treatment_acceptance10"])],
            "comparator": [" ".join(commands["comparator_train"]), " ".join(commands["comparator_protected16"]), " ".join(commands["comparator_acceptance10"])],
        },
        "environment": environment_versions(),
        "shared_configuration": {
            "seed": 17,
            "contract": "v2",
            "base_model": HF_REPO_ID,
            "base_model_snapshot_revision": PINNED_BASE_MODEL_REVISION,
            "batch_size": 4,
            "learning_rate": "3e-4",
            "weight_decay": 0.01,
            "max_steps": 720,
            "protected_benchmark": PROTECTED_BENCHMARK_REL,
            "acceptance_benchmark": ACCEPTANCE_BENCHMARK_REL,
        },
        "arms": {
            "treatment": {
                "data_dir": TREATMENT_DATA_DIR_REL,
                "candidate_record_count": TREATMENT_EXPECTED_CANDIDATE_COUNT,
                "train_count": TREATMENT_EXPECTED_TRAIN_COUNT,
                "val_count": TREATMENT_EXPECTED_VAL_COUNT,
                "max_steps": TREATMENT_STEPS,
                "role": "sole decision-bearing candidate",
            },
            "comparator": {
                "data_dir": COMPARATOR_DATA_DIR_REL,
                "candidate_record_count": COMPARATOR_EXPECTED_CANDIDATE_COUNT,
                "train_count": COMPARATOR_EXPECTED_TRAIN_COUNT,
                "val_count": COMPARATOR_EXPECTED_VAL_COUNT,
                "max_steps": COMPARATOR_STEPS,
                "role": "diagnostic corpus comparator, never a promotion candidate",
            },
        },
        "gate6_required_pass_set": sorted(GATE6_REQUIRED_PASS_SET),
        "governing_document": "training/seed17_regression_balanced_repair_execution_design_chatgpt.md",
        "resolved_configuration": {
            "treatment_checkpoint_dir": str((experiment_dir / "treatment" / "checkpoint").relative_to(TRAINING_DIR)),
            "comparator_checkpoint_dir": str((experiment_dir / "comparator" / "checkpoint").relative_to(TRAINING_DIR)),
        },
        "base_model": {
            "repo_id": HF_REPO_ID,
            "pinned_revision": PINNED_BASE_MODEL_REVISION,
            "file_fingerprints": PINNED_BASE_MODEL_FILE_FINGERPRINTS,
        },
        "executable_code_canonical_fingerprints": {name: hashlib.sha256(data).hexdigest() for name, data in executable_code_canonical.items()},
        "governing_input_canonical_fingerprints": dict(CANONICAL_LF_GOVERNING_INPUTS),
        "real_validation_fingerprint": file_fingerprint(TRAINING_DIR / REAL_VALIDATION_REL_PATH),
    }
    return receipt


OFFLINE_ENV = {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}


def resolve_experiment_dir(raw: str | None) -> Path:
    """A relative --experiment-dir is resolved against TRAINING_DIR, not
    the current working directory (which could be anywhere depending on
    how this script is invoked) -- matching the default's own base. An
    absolute path that doesn't resolve under TRAINING_DIR fails with a
    controlled diagnostic instead of an opaque traceback deep inside
    build_commands(), where every planned path is computed via
    .relative_to(TRAINING_DIR). Purely lexical (os.path.normpath), never
    touches the filesystem or resolves symlinks."""
    if raw is None:
        return TRAINING_DIR / "controlled_seed17_regression_balanced_repair_run"
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = TRAINING_DIR / candidate
    candidate = Path(os.path.normpath(str(candidate)))
    try:
        candidate.relative_to(TRAINING_DIR)
    except ValueError:
        raise ReplayPreflightError(
            f"--experiment-dir must resolve to a path under {TRAINING_DIR} -- every planned command "
            f"path is computed relative to it. Got: {candidate}"
        )
    return candidate


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

    experiment_dir = resolve_experiment_dir(args.experiment_dir)
    treatment_dir = experiment_dir / "treatment"
    comparator_dir = experiment_dir / "comparator"
    commands = build_commands(treatment_dir, comparator_dir)

    if not args.confirm_execute:
        print("Dry run only (pass --confirm-execute to run for real). Planned sequence:")
        for key in ("treatment_train", "treatment_protected16", "treatment_acceptance10", "comparator_train", "comparator_protected16", "comparator_acceptance10"):
            print(f"  $ {' '.join(commands[key])}")
        print(f"Planned exclusive experiment directory: {experiment_dir}")
        return

    print("=== Preflight ===")
    lock = load_frozen_fingerprints()
    state = git_state()
    verify_head_matches_origin_main(state)
    verify_package_commit(state)
    # Clean-tree verification must happen against the pre-mutation state,
    # before the real-validation placeholder is ever created -- see
    # bootstrap_clean_tree_then_real_validation().
    bootstrap_clean_tree_then_real_validation(state)
    verify_pinned_dependency_versions(lock)
    executable_code_canonical = verify_frozen_executable_code(lock)
    canonical_inputs = load_canonical_governing_inputs()
    verify_benchmark_counts(canonical_inputs)
    verify_arm_split_and_fingerprint(
        canonical_inputs, TREATMENT_CANDIDATE_REL, TREATMENT_TRAIN_REL, TREATMENT_VAL_REL,
        TREATMENT_EXPECTED_CANDIDATE_COUNT, TREATMENT_EXPECTED_TRAIN_COUNT, TREATMENT_EXPECTED_VAL_COUNT,
        TREATMENT_EXPECTED_TRAINING_DATA_FINGERPRINT, "treatment",
    )
    verify_arm_split_and_fingerprint(
        canonical_inputs, COMPARATOR_CANDIDATE_REL, COMPARATOR_TRAIN_REL, COMPARATOR_VAL_REL,
        COMPARATOR_EXPECTED_CANDIDATE_COUNT, COMPARATOR_EXPECTED_TRAIN_COUNT, COMPARATOR_EXPECTED_VAL_COUNT,
        COMPARATOR_EXPECTED_TRAINING_DATA_FINGERPRINT, "comparator",
    )
    verify_treatment_candidate_equals_comparator_plus_delta(canonical_inputs)
    verify_treatment_proposal_membership(canonical_inputs)
    verify_cuda_bfloat16_expectation()
    verify_command_shape(commands)
    verify_pinned_base_model_snapshot()

    if experiment_dir.exists():
        raise ReplayPreflightError(f"Experiment root already exists: {experiment_dir}. Refusing to reuse or overwrite it.")

    create_exclusive_experiment_dir(experiment_dir)
    receipt = build_receipt(experiment_dir, commands, executable_code_canonical)
    write_exclusive(experiment_dir / "receipt.json", json.dumps(receipt, indent=2, ensure_ascii=False))
    print(f"[receipt written] {experiment_dir / 'receipt.json'}")

    create_exclusive_experiment_dir(treatment_dir)
    create_exclusive_experiment_dir(comparator_dir)

    protected_records = parse_jsonl_records_from_bytes(canonical_inputs[PROTECTED_BENCHMARK_REL])
    acceptance_records = parse_jsonl_records_from_bytes(canonical_inputs[ACCEPTANCE_BENCHMARK_REL])

    print("\n=== Treatment: training (matched 720 steps) ===")
    proc = run_logged_subprocess(commands["treatment_train"], cwd=TRAINING_DIR, log_path=treatment_dir / "train_log.txt", env=OFFLINE_ENV)
    require_success(proc, "treatment train.py")
    verify_completed_steps(treatment_dir / "checkpoint", TREATMENT_STEPS, "treatment")

    print("\n=== Treatment: evaluation (protected 16) ===")
    proc = run_logged_subprocess(commands["treatment_protected16"], cwd=TRAINING_DIR, log_path=treatment_dir / "protected16_log.txt", env=OFFLINE_ENV)
    require_success(proc, "treatment run_benchmark.py (protected16)")
    verify_raw_result_artifact(treatment_dir / "protected16_results.json", protected_records, EXPECTED_PROTECTED_COUNT, "treatment protected16")

    print("\n=== Treatment: evaluation (acceptance 10) ===")
    proc = run_logged_subprocess(commands["treatment_acceptance10"], cwd=TRAINING_DIR, log_path=treatment_dir / "acceptance10_log.txt", env=OFFLINE_ENV)
    require_success(proc, "treatment run_benchmark.py (acceptance10)")
    verify_raw_result_artifact(treatment_dir / "acceptance10_results.json", acceptance_records, EXPECTED_ACCEPTANCE_COUNT, "treatment acceptance10")

    print("\n=== Comparator: training (matched 720 steps) ===")
    proc = run_logged_subprocess(commands["comparator_train"], cwd=TRAINING_DIR, log_path=comparator_dir / "train_log.txt", env=OFFLINE_ENV)
    require_success(proc, "comparator train.py")
    verify_completed_steps(comparator_dir / "checkpoint", COMPARATOR_STEPS, "comparator")

    print("\n=== Comparator: evaluation (protected 16) ===")
    proc = run_logged_subprocess(commands["comparator_protected16"], cwd=TRAINING_DIR, log_path=comparator_dir / "protected16_log.txt", env=OFFLINE_ENV)
    require_success(proc, "comparator run_benchmark.py (protected16)")
    verify_raw_result_artifact(comparator_dir / "protected16_results.json", protected_records, EXPECTED_PROTECTED_COUNT, "comparator protected16")

    print("\n=== Comparator: evaluation (acceptance 10) ===")
    proc = run_logged_subprocess(commands["comparator_acceptance10"], cwd=TRAINING_DIR, log_path=comparator_dir / "acceptance10_log.txt", env=OFFLINE_ENV)
    require_success(proc, "comparator run_benchmark.py (acceptance10)")
    verify_raw_result_artifact(comparator_dir / "acceptance10_results.json", acceptance_records, EXPECTED_ACCEPTANCE_COUNT, "comparator acceptance10")

    print(f"\nAll steps completed. Artifacts in {experiment_dir}")
    print(
        "Raw benchmark result scaffolds only -- no semantic scores filled, no checkpoint selected. "
        "Semantic scoring and outcome classification (RBR17-A/B/C/D/X) are separate, later, "
        "separately-authorized steps."
    )


if __name__ == "__main__":
    main()
