# Controlled Seed-17 Regression-Balanced Repair Execution — Frozen Manifest

**Date:** 2026-08-11
**Author:** Claude, implementing ChatGPT's governing execution design after independent review and agreement, per Johnny's direct authorization
**Governing design:** `training/seed17_regression_balanced_repair_execution_design_chatgpt.md` (SHA-256 `fe316fb1ee919f9f56ba01be559be1fa7781135f9610ceacca4990637bba6fa6` -- corrected during this review from the originally-cited `ceac0d2f8ae3d93ad1bd2b57ffaff453c3d444fda8233239a9a0d84c437bedb9`; see §1)
**Package parent commit:** `90ee08d17304e5a124f15f19f9644a1f609083ba` (must be HEAD's direct parent at execution time — the corpus-implementation milestone, 15/15 static gates PASS)
**Status:** Static package only. No training, inference, or compute of any kind performed by this document or its sibling package files.

## 1. Independent review of the governing execution design (before implementation)

Every fingerprint in the governing design's §4 was independently recomputed by Claude directly from
committed git blobs (`git show HEAD:<path> | sha256sum`) at the pinned parent commit `90ee08d...` —
never assumed from the design document's own citations, even though in this case all nine matched
exactly. One non-blocking finding:

**Section 3's epoch-equivalent arithmetic is internally inconsistent.** The design states, in the same
paragraph: the comparator's 72-record train split reaches 720 steps at "the historical 40-epoch-
equivalent schedule" (correct); the treatment's 79-record train split reaches "approximately 36.46
epoch-equivalents" at 720 steps; and a natural 40-epoch treatment schedule "would reach 800 steps"
(also correct). These cannot all be true simultaneously — if 40 epochs is 800 steps for a 79-record
split, steps-per-epoch is exactly 20, which makes 720 steps exactly **36.0** epoch-equivalents, not
36.46. The 36.46 figure comes from continuous division (79/4 = 19.75, unrounded); the 800 figure comes
from ceiling-based division (⌈79/4⌉ = 20). Independently confirmed which convention this codebase
actually uses: `train.py` runs Hugging Face `Seq2SeqTrainer` with the default `dataloader_drop_last=False`
and no gradient accumulation, so the dataloader's own length — and therefore `num_update_steps_per_epoch`
— is ceiling-based; this is also exactly the convention this repository's own
`gold_v1.2.3_groupscreen_seed17_scoring.md` (the document that originally named the "optimizer-step
confound") uses consistently across five different corpus sizes. **800 is correct; 36.46 is wrong — the
correct figure is exactly 36.0 epoch-equivalents.** Confirmed non-blocking at the time this finding was
made: no gate, hash, pinned constant, or authorization depended on this figure (`TREATMENT_STEPS = 720`
either way), and the design's actual recommendation — fix both arms at 720, never let the treatment run
its larger natural schedule — was unaffected, if anything more clearly justified by the corrected
number (720-vs-800 is a larger, more obviously severe avoided confound than 36.46-vs-40 made it look).

**The governing design document has since been corrected.** Re-reading it during this same
implementation turn found its own SHA-256 had changed from the originally-cited
`ceac0d2f8ae3d93ad1bd2b57ffaff453c3d444fda8233239a9a0d84c437bedb9` to
`fe316fb1ee919f9f56ba01be559be1fa7781135f9610ceacca4990637bba6fa6`. A full line-by-line comparison
against the version originally reviewed confirmed exactly one line changed — section 3 now reads "the
treatment's 79-record train split reaches exactly 36.0 epoch-equivalents at 720 steps (`ceil(79 / 4) =
20` optimizer steps per epoch)" — precisely the correction recommended above, and nothing else in the
document moved. This package cites the corrected hash throughout (header, above). Recorded plainly in
this package's own design-constants file (`epoch_equivalent_at_720_steps: 36.0`) and in
`run_seed17_regression_balanced_repair.py`'s own module docstring.

Everything else in the governing design was independently verified and found correct: all treatment/
comparator/benchmark/base-model hashes; the six frozen semantic gates and gate-6 required set (byte-
identical to every prior seed-17 replay package, `{01,03,04,05,06,07,09,10,12,13,14,15,16}`); the
gate-6 diagnostic-emphasis descriptions for probes 06/08/09/10/11/13/16, cross-checked against the
actual diagnostic postmortem's findings; the frozen training configuration, cross-checked directly
against `train.py`'s own code; and the dependency-version table, cross-checked against
`requirements.txt`. Full detail in the chat record of this review; not restated here.

## 2. Frozen arms

### 2.1 Treatment (sole decision-bearing candidate)

| Item | Value |
|---|---|
| Candidate | `training/gold_v1.2.2_regression_balanced_repair_candidate.jsonl`, 85 records, canonical LF SHA-256 `955437e2ac014c3e48402867e51ac539334e907d61d05dde6e7d7da1ded254ea` |
| Split | `training/data/processed_gold_v1.2.2_regression_balanced_repair_v2contract_seed17/`, 79 train / 6 val |
| Training-data fingerprint | `badfed9f946bd13379e1f74336b18c596c922cf378cc3853ea95a2098ea03800` |
| Proposal (for structural + membership verification) | `training/regression_balanced_repair_proposal.jsonl`, 7 records, `192372fd44fc87ea879d2ab7b751a3d54be100b447b886c213b26553284a747a` |
| Steps | Exactly 720, via one explicit `--max-steps 720` |
| Structural relationship | The candidate's first 78 records are byte-identical to the comparator candidate; the remaining 7 records match the proposal's `input` text, in order — independently re-verified at execution time (`verify_treatment_candidate_equals_comparator_plus_delta`), not merely trusted from the corpus-implementation script's own construction-time check |

### 2.2 Comparator (diagnostic corpus comparator, never a promotion candidate)

| Item | Value |
|---|---|
| Candidate | `training/gold_v1.2.2_phase2_derived_candidate.jsonl`, 78 records, canonical LF SHA-256 `6e9e5f1bea8fc3cbcb615376a1d055bd273605d0f8c1e40a8c120720c8cb836c` |
| Split | `training/data/processed_gold_v1.2.2_phase2_v2contract_seed17/`, 72 train / 6 val |
| Training-data fingerprint | `9d6817152087685b653830ad671f9304e4226b095a202ca57f5ca52bc3a14c1f` |
| Steps | Exactly 720, via one explicit `--max-steps 720` |

**Same corpus, same paths, same hashes as the prior contrastive-replay package's comparator arm** —
independently reverified fresh from committed git blobs for this package, not carried forward on the
assumption of no drift. All nine values matched exactly, confirming no drift occurred.

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
missing terminal newline, and any content drift after normalization. The same function verifies all 12
executable-code closure files.

## 3. Execution-environment requirement

Run from a **fresh linked worktree or fresh clone at the exact package commit** (the not-yet-created
commit whose immediate parent is `90ee08d17304e5a124f15f19f9644a1f609083ba`), not the main Windows
checkout directly — the main checkout deliberately carries legitimate untracked historical artifacts
(prior replay run logs/checkpoints, earlier design/review docs) that would otherwise always fail the
wrapper's unmodified, strict `git status --porcelain == ""` check.

`datasets/real_validation.jsonl` has no committed blob of its own — it's listed in the committed,
tracked `datasets/.gitignore` alongside `real_holdout.jsonl` and `private/` — so a fresh worktree or
clone at the pinned commit will not have it on disk. `main()` handles this via
`bootstrap_clean_tree_then_real_validation(state)`, in this exact order: verify the pre-mutation clean
tree, then create the placeholder only if absent, then verify byte-empty. Unchanged design from every
prior seed-17 replay package in this repository.

## 4. Six frozen semantic gates (unchanged from every prior seed-17 replay package)

1. Protected format validity: 16/16.
2. Acceptance format validity: 10/10.
3. Acceptance count-rule conformance: 10/10.
4. Acceptance combined strict pass: 10/10.
5. Protected semantic strict pass: at least 12/16.
6. Protected preservation and repair — required pass set: `{01,03,04,05,06,07,09,10,12,13,14,15,16}`.

Excluded from the required set as diagnostic-emphasis-only, per the governing design §9: `{02, 08, 11}`
— still covered by the full-suite gates 1 and 5, just not individually mandatory.

## 5. Outcome matrix

`RBR17-A` (treatment passes all six, comparator fails one or more) — discriminating success, seed 73
review-eligible (not automatic). `RBR17-B` (both pass) — candidate clears but doesn't discriminate the
corpus revision from run variability; stop for interpretation. `RBR17-C` (both fail) — stop, no seed 73.
`RBR17-D` (treatment fails, comparator passes) — negative/reversed result, stop. `RBR17-X` (either arm
invalid) — entire paired experiment invalid, preserve partial artifacts, no automatic rerun.

## 6. Two new verification steps beyond the prior contrastive-replay package

The prior package's treatment and comparator were unrelated corpora (different lineages, sharing only
incidental content). This package's treatment is constructed FROM the comparator plus a reviewed delta,
so two additional structural claims exist and are independently verified at execution time, not merely
inherited from the corpus-implementation script's own construction-time checks:

1. **`verify_treatment_candidate_equals_comparator_plus_delta`** (governing design §4.1 / preflight item
   9): the treatment candidate's first 78 records must be byte-identical to the full comparator
   candidate; its remaining 7 records must match the reviewed proposal's `input` text, in order.
2. **`verify_treatment_proposal_membership`, extended** (governing design preflight item 8): all 7
   proposal records must resolve, via the real v2 prompt-builder, to prompts present exactly once in
   treatment train, absent from treatment validation, AND absent from the comparator (train or
   validation) entirely — the comparator-absence check is new; the prior package only checked treatment
   train/validation, since its two arms shared no construction relationship.

## 7. Package files

| File | Purpose |
|---|---|
| `training/seed17_regression_balanced_repair_execution_design_chatgpt.md` | Governing design (exact bytes as authored) |
| `training/seed17_regression_balanced_repair_execution_design_constants.json` | Machine-readable design constants (Claude-authored — no separate ChatGPT JSON draft exists for this package) |
| `training/controlled_seed17_regression_balanced_repair_execution_frozen_manifest.md` | This document |
| `training/controlled_seed17_regression_balanced_repair_execution_frozen_fingerprints.json` | Runtime lock file the wrapper actually reads |
| `training/run_seed17_regression_balanced_repair.py` | Plan-only by default; execution requires `--confirm-execute` |
| `training/test_run_seed17_regression_balanced_repair.py` | Dummy subprocess/static test suite |
| `training/controlled_seed17_regression_balanced_repair_execution_manifest_dryrun_receipt_sample.json` | Labeled non-execution dry-run sample |

## 8. Explicit non-authorizations

No training, inference, semantic scoring, seed 73, corpus/benchmark mutation, checkpoint
selection/reuse, export, deployment, or activation is performed or authorized by this package. This
package's static correctness is not itself a downstream authorization of any kind.
