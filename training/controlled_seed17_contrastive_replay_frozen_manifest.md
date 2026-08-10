# Controlled Seed-17 Contrastive Replay — Frozen Manifest

**Date:** 2026-08-10
**Author:** Claude, implementing ChatGPT's governing design after independent review and agreement
**Governing design:** `training/seed17_contrastive_replay_design_chatgpt.md`
**Package parent commit:** `2595f563712ae0989f6f26f646c841eede900ca0` (must be HEAD's direct parent at execution time — advanced from `17c58bf...` in the third review round, §1.2, since this correction is a direct child of the first replay-package commit, not of the corpus baseline)
**Corpus baseline commit:** `17c58bf102b7cb442c312f916b3c7c52e3cd8815` (documentation only from here on — the commit the treatment/comparator corpora, splits, and benchmarks are all pinned against; no active git-ancestry check requires HEAD to descend from it directly)
**Status:** Static package only. No training, inference, or compute of any kind performed by this document or its sibling package files.

## 1. Independent review findings (before implementation)

Every fingerprint below was recomputed by Claude directly from committed git blobs
(`git show HEAD:<path> | sha256sum`) at the pinned parent commit — never copied from the governing
design draft's own citations. Four corrections were found and applied:

| File | Draft cited (wrong) | Corrected (canonical git blob) | Cause |
|---|---|---|---|
| `gold_v1.2.2_phase2_derived_candidate.jsonl` | `f738f9eb...` | `6e9e5f1bea8fc3cbcb615376a1d055bd273605d0f8c1e40a8c120720c8cb836c` | Windows CRLF-checkout hash |
| `data/processed_gold_v1.2.2_phase2_v2contract_seed17/train.jsonl` | `02d81b38...` | `8760378519365c4fe2ae4dcebdc6379214cc0fcf93442521f64d6d4508bafae6` | Windows CRLF-checkout hash |
| `data/processed_gold_v1.2.2_phase2_v2contract_seed17/val.jsonl` | `83abbc79...` | `8aa99a794f495cf75e6904ee28789e06ac43c1f9ee424f0b2ce2f219527623c4` | Windows CRLF-checkout hash |
| `datasets/benchmark/gold_v1.2.1_probes.jsonl` (protected-16) | `044708641c...` (not explicitly cited under this key in the draft, but this is the value every prior script in this repo has pinned) | `767fe21a1097b51cef38728dcff0ff9ca4cf280bde8e65a7d885729f40990c0f` | Windows CRLF-checkout hash — an adjacent finding, separate from the draft's own three flagged items |

The fourth finding is worth stating plainly: **`prepare_phase2_contrastive_candidate_corpus.py`'s own
`EXPECTED_PROTECTED_PROBES_FINGERPRINT` (already committed at `17c58bf`) is pinned to this same wrong,
checkout-dependent hash.** This wrapper pins the correct value independently and is not affected, but
the already-committed derivation script's pin remains uncorrected — a separate, later decision, not
bundled into this package.

Also independently confirmed, not assumed:

- `train.py --max-steps N` overrides `num_train_epochs` **and** the default linear LR scheduler's
  total-steps count (confirmed by reading the flag's own docstring in `train.py`), so both arms
  fixed at 720 steps get a complete, symmetric decay-to-zero schedule — not one full epoch-based
  schedule and one truncated one. This flag exists in this codebase specifically to prevent an
  optimizer-step confound (its docstring cites `gold_v1.2.3_groupscreen_seed17_scoring.md`, confirmed
  to exist).
- The comparator's `training_data_fingerprint` (`9d681715...`, content-based — sorted canonical JSON
  of parsed prompt/target pairs, not raw file bytes) was independently recomputed from the actual
  committed `train.jsonl`/`val.jsonl` content and matches the design draft's citation exactly, as
  expected, since it doesn't depend on checkout line endings.
- `datasets/real_validation.jsonl` has no committed blob of its own (0 bytes on disk, but never
  committed) — it's listed in the committed, tracked `datasets/.gitignore`, so a fresh worktree or
  clone at the pinned commit will not have it on disk, though the ignore rule protecting it will
  already be present. See §1.1 and §3.

## 1.1 Second review round (2026-08-10): one disagreement, two accepted corrections

ChatGPT's second review reported an execution-blocking defect: creating the real-validation
placeholder before verifying a clean working tree would make a fresh checkout's own `git status`
report that new file as untracked, failing preflight. **Claude found this specific mechanism does not
currently reproduce** — `datasets/.gitignore` (committed, part of the pinned tree) already lists
`real_validation.jsonl`, confirmed three ways: `git check-ignore -v`, an empty/recreate test against
the real repository, and an isolated scratch-repository reproduction of the fresh-worktree scenario.
Full detail and disposition in §3.

Two non-blocking findings were both confirmed exactly as reported and fixed:

- The package canonicalizes **nine** physical governing inputs, not eight (the treatment composite
  proposal is the ninth) — a documentation undercount in the module's own docstrings; the code itself
  always canonicalized all nine correctly.
- A relative `--experiment-dir` raised an uncontrolled `ValueError` from deep inside `build_commands()`
  — reproduced exactly. Fixed via `resolve_experiment_dir()`: relative paths now resolve against
  `TRAINING_DIR`; an absolute path outside `TRAINING_DIR` now fails with a controlled diagnostic
  instead of a raw traceback. The default path was already correct and is unchanged.

## 1.2 Third review round (2026-08-10): a real execution attempt, one confirmed defect, zero compute

The prior package (commit `2595f563...`) was fully accepted through two review rounds and explicitly
authorized for execution. Claude set up a genuine fresh `git worktree add` at exactly that commit
(verified: correct HEAD, clean tree, `datasets/.gitignore` present, `real_validation.jsonl` correctly
absent beforehand) and ran the wrapper with `--confirm-execute` for real.

**Result: preflight failure, before any experiment directory was created or any subprocess started.**
Confirmed directly, not assumed: no `controlled_seed17_contrastive_replay_run/` directory exists after
the attempt; no checkpoint, log, or result file of any kind was written; zero GPU time, zero compute
cost. This is the wrapper's fail-closed design working exactly as intended — an unauthorized or
defective execution stops before doing anything, not partway through.

**Root cause, fully diagnosed:** `verify_frozen_executable_code()` did a flat hash comparison against
raw checkout bytes. This repository's `core.autocrlf=true` materializes *every* text file with CRLF on
a genuine checkout (`git worktree add`, `git clone`, `git checkout`) — unconditionally, regardless of
what's actually stored — but the pinned lock hashes had been computed from Claude's main working
directory, which is a mix of git-checked-out CRLF files and tool-written LF files that happened, for
only 5 of the 12 executable-code closure files, to still be LF. Those 5 (`contract_adapters.py`,
`prompt_contract_v2_candidate.py`, `prompt_contract_v2_parser.py`, `run_benchmark.py`,
`run_seed17_contrastive_replay.py`) failed outright against the real fresh checkout. The other 7 had
*also* been mispinned (to CRLF-checkout bytes, not the canonical LF blob) but never surfaced, because
a genuine fresh checkout's CRLF happened to coincidentally match the old, wrong pin. **No prior review
round caught this because every "live check against real pinned files" in the test suite ran against
Claude's main working directory, never an actual fresh checkout** — this was the first time the
wrapper was genuinely checked out and run.

**Fix applied**, all independently verified end-to-end, including against the actual fresh worktree
that originally failed:

1. `verify_frozen_executable_code()` now canonicalizes each of the 12 closure files exactly like the
   nine governing data inputs (accepts pinned canonical LF or a uniform CRLF checkout of exactly those
   bytes; rejects everything else) and returns the verified canonical-LF byte map.
2. All 12 executable-code lock entries repinned to their canonical git-blob (LF) hash — recomputed
   directly from `git show 2595f563:training/<file>`, not copied from the prior (partially wrong) lock.
   7 of the 11 unchanged files actually needed a new value; the other 4 happened to already be correct.
3. `build_receipt()` no longer re-reads raw checkout bytes for its executable-code fingerprints (which
   would have silently reintroduced a platform-dependent value into the receipt even after
   verification passed) — it now receives and records the exact canonical byte map
   `verify_frozen_executable_code()` already verified. Receipt field renamed
   `executable_code_canonical_fingerprints` to document this explicitly, matching
   `governing_input_canonical_fingerprints`'s existing naming.
4. `PINNED_PARENT_COMMIT` advanced to `2595f563...` (see header); `EXPECTED_PACKAGE_COMMIT_FILES`
   narrowed to the exact five-file correction delta (§6 lists all seven package files' roles; only
   five change in this round: the lock file, this manifest, the dry-run receipt sample, the wrapper,
   and its test suite — the two ChatGPT-authored design documents are untouched).
5. Added a real scratch-git-repository regression test (`core.autocrlf=true` explicitly configured, a
   genuine `git worktree add`) that asserts CRLF materialization actually occurred *before* proving
   the corrected verifier passes against it — the only way to catch this exact bug class in an
   automated suite rather than a live execution attempt. All prior rejection tests (mixed endings,
   bare CR, BOM, missing newline, content drift, closure-set drift) remain, now also covering the
   executable-code path directly rather than only the data-input path.

The fresh worktree from the failed attempt was reused (not recreated) to independently confirm the
fix against the exact same real CRLF checkout that originally failed, before this correction was
written up.

## 2. Frozen arms

### 2.1 Treatment (sole decision-bearing candidate)

| Item | Value |
|---|---|
| Candidate | `training/gold_v1.2.2_phase2_contrastive_derived_candidate.jsonl`, 82 records, canonical LF SHA-256 `7760f377dcd7ab35b54fe6c2c274e6615a5641acaa73ec0a30da64d78db9df2d` |
| Split | `training/data/processed_gold_v1.2.2_phase2_contrastive_v2contract_seed17/`, 76 train / 6 val |
| Training-data fingerprint | `62bbee12130ea54f6cae3777eb990a9d54a35411ceeba75030755569c44982ae` |
| Composite proposal (for membership verification) | `training/phase2_contrastive_attribution_composite_proposal.jsonl`, 16 records, `519823faf69bda2dcf74b816c63f15ecc16e5e902bc8f8bdee73a559326fba9c` |
| Steps | Exactly 720, via one explicit `--max-steps 720` |

### 2.2 Comparator (diagnostic corpus comparator, never a promotion candidate)

| Item | Value |
|---|---|
| Candidate | `training/gold_v1.2.2_phase2_derived_candidate.jsonl`, 78 records, canonical LF SHA-256 `6e9e5f1bea8fc3cbcb615376a1d055bd273605d0f8c1e40a8c120720c8cb836c` |
| Split | `training/data/processed_gold_v1.2.2_phase2_v2contract_seed17/`, 72 train / 6 val |
| Training-data fingerprint | `9d6817152087685b653830ad671f9304e4226b095a202ca57f5ca52bc3a14c1f` |
| Steps | Exactly 720, via one explicit `--max-steps 720` |

### 2.3 Shared

| Item | Value |
|---|---|
| Protected-16 benchmark | `datasets/benchmark/gold_v1.2.1_probes.jsonl`, canonical LF SHA-256 `767fe21a1097b51cef38728dcff0ff9ca4cf280bde8e65a7d885729f40990c0f` |
| Acceptance-10 benchmark | `datasets/benchmark/source_determined_items_v2_acceptance_draft.jsonl`, canonical LF SHA-256 `b8fe4d4178e5b508757db998eacb1ee979518697c8df759ba1739227c88d448e` |
| Base model | `google/flan-t5-base` @ `7bcac572ce56db69c1ea7c8af255c5d7c9672fc2` |
| Contract | `v2` |
| Real validation | `datasets/real_validation.jsonl`, must be byte-empty |

All governing inputs are verified via `canonicalize_pinned_lf_bytes()`: accepts the pinned canonical
LF bytes or a uniform CRLF checkout of exactly those bytes, rejects mixed endings, bare CR, BOM,
missing terminal newline, and any content drift after normalization. As of the third review round
(§1.2), the same function verifies all 12 executable-code closure files too, not just the nine
governing data inputs — a real fresh-checkout execution attempt found the executable-code path had
been left on a flat, checkout-dependent comparison.

## 3. Execution-environment requirement

Run from a **fresh linked worktree or fresh clone at the exact corrective package commit** (the
not-yet-created commit whose immediate parent is `2595f563712ae0989f6f26f646c841eede900ca0` — never
at `2595f563...` itself, which `verify_package_commit()` requires to be HEAD's *parent*, not HEAD),
not the main Windows checkout directly — the main checkout deliberately carries legitimate untracked
historical artifacts (prior replay run logs/checkpoints, earlier design/review docs) that would
otherwise always fail the wrapper's unmodified, strict `git status --porcelain == ""` check. This
avoids needing any allowlist.

`datasets/real_validation.jsonl` has no committed blob of its own — it's listed in the committed,
tracked `datasets/.gitignore` alongside `real_holdout.jsonl` and `private/` — so a fresh worktree or
clone at the pinned commit will not have it on disk. `run_seed17_contrastive_replay.py`'s `main()`
handles this via `bootstrap_clean_tree_then_real_validation(state)`, in this exact order:

1. `verify_clean_working_tree(state)` — against the state captured **before** any mutation.
2. `ensure_real_validation_placeholder()` — creates a genuinely empty file at the exact expected path,
   only if absent; logs explicitly either way; never overwrites an existing file, empty or not.
3. `verify_real_validation_empty()` — unchanged fail-closed check, still fails closed on both a
   missing and a non-empty file.

**Correction record (2026-08-10):** ChatGPT's review reported that placeholder creation happening
before clean-tree verification would make a fresh checkout's own `git status` report the newly
created file as untracked, failing `verify_clean_working_tree()`. Claude independently checked this
before implementing anything and found the specific mechanism does not currently reproduce —
`datasets/.gitignore` already covers this exact path and is itself part of the committed, pinned
tree, confirmed via `git check-ignore`, a direct empty/recreate test against the real repository, and
an isolated scratch-repository reproduction of the fresh-worktree scenario (all three: file creation
never appears in `git status --porcelain`). The verify-before-mutate reordering above was adopted
anyway, as defense-in-depth — this wrapper's correctness should not depend on that `.gitignore` entry
persisting — not as confirmation of the originally reported failure mode. See
`test_run_seed17_contrastive_replay.py`'s scratch-repository regression tests, which prove the
corrected sequence succeeds both with and without gitignore protection present, and that dirty-tree
rejection for an unrelated cause is not weakened by the reordering.

## 4. Six frozen semantic gates (unchanged from the Phase-2 replay)

1. Protected format validity: 16/16.
2. Acceptance format validity: 10/10.
3. Acceptance count-rule conformance: 10/10.
4. Acceptance combined strict pass: 10/10.
5. Protected semantic strict pass: at least 12/16.
6. Protected preservation and repair — required pass set: `{01,03,04,05,06,07,09,10,12,13,14,15,16}`.

## 5. Outcome matrix

`C17-A` (treatment passes all six, comparator fails one or more) — discriminating success, seed 73
review-eligible (not automatic). `C17-B` (both pass) — candidate clears but doesn't discriminate the
corpus revision from run variability; stop for interpretation. `C17-C` (both fail) — stop, no seed 73.
`C17-D` (treatment fails, comparator passes) — negative/reversed result, stop. `C17-X` (either arm
invalid) — entire paired experiment invalid, preserve partial artifacts, no automatic rerun.

## 6. Package files

| File | Purpose |
|---|---|
| `training/seed17_contrastive_replay_design_chatgpt.md` | Governing design (exact bytes as authored) |
| `training/seed17_contrastive_replay_design_constants_chatgpt.json` | Machine-readable design constants (exact bytes as authored — never silently changed) |
| `training/controlled_seed17_contrastive_replay_frozen_manifest.md` | This document |
| `training/controlled_seed17_contrastive_replay_frozen_fingerprints.json` | Runtime lock file the wrapper actually reads |
| `training/run_seed17_contrastive_replay.py` | Plan-only by default; execution requires `--confirm-execute` |
| `training/test_run_seed17_contrastive_replay.py` | Dummy subprocess/static test suite |
| `training/controlled_seed17_contrastive_replay_manifest_dryrun_receipt_sample.json` | Labeled non-execution dry-run sample |

## 7. Explicit non-authorizations

No training, inference, semantic scoring, seed 73, corpus/benchmark mutation, checkpoint
selection/reuse, export, deployment, or activation is performed or authorized by this package.
