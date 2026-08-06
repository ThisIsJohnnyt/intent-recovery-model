# Controlled Seed-17 Phase-2 Replay — Outcome Record (P2-D)

**Date:** 2026-08-06
**Governing document:** `training/phase2_seed17_replay_interpretation_and_outcome_matrix_chatgpt.md`
**Package commit (exact, pinned):** `1ee8ad5976f3243269c7476000d49b1d8140205c` (`HEAD` = `origin/main`,
reconfirmed immediately before execution and again while writing this record)
**Authorized scope:** exact package at commit `1ee8ad5`; seed 17 only; natural 720-step run as sole
primary; 600-step run as diagnostic control only; no seed 73, corpus change, export, deployment, or
activation; stop and report on any frozen preflight failure.
**Disposition: P2-D — Fail / Fail. Phase-2 does not clear the frozen gate under either tested
step budget.**

## 1. Package integrity at execution time

| Artifact | SHA-256 |
|---|---|
| `controlled_seed17_phase2_replay_frozen_manifest.md` | `f3772cd0d6090b67cfdcb52f539ba29a1e961cea75590ecb54f401ecfb8b1bf7` |
| `controlled_seed17_phase2_replay_frozen_fingerprints.json` | `1350e14de5c6553116c30a50fcf1e0b811e676be8b2c4c3ad15c2c91f2f81e89` |
| `controlled_seed17_phase2_replay_run/receipt.json` | `526f7d264e163d6e443ce2b4a0a3caa9b519b93d8e8e196b3d27becfcd48d875` |

### 1.1 Execution chronology and authorization chain

Before the successful execution, two invocations stopped during preflight without starting
training or evaluation: the first on the known untracked-tree condition, and the second because
bare system `python` lacked the pinned dependencies. Neither created an experiment directory or
any artifact (both wrappers' `verify_*` failures occur before `create_exclusive_experiment_dir`).

1. **Attempt 1** ran under Johnny's original scoped authorization ("Exact package at commit
   1ee8ad5... Stop and report if any frozen preflight check fails"). Failed at
   `verify_clean_working_tree`: 7 untracked files present (two never-committed relay docs, the R2
   replay's leftover checkpoint/logs, this round's own session-handoff document). Per that
   authorization's own "stop and report" term, Claude stopped, reported the failure verbatim, and
   returned three resolution options to Johnny rather than retrying automatically.
2. Johnny separately authorized relocating the R2 checkpoint/logs and the two relay docs out of
   the repo tree ("B"), then separately authorized relocating the session-handoff document the
   same way. Neither action was an execution attempt. After both, Claude re-verified `git status
   --porcelain` was fully empty and `HEAD`/`main`/`origin/main` were all still `1ee8ad5`, then
   explicitly asked: "Awaiting your fresh, explicit authorization to reissue `python
   run_seed17_phase2_replay.py --confirm-execute`."
3. Johnny replied "I authorize" — fresh authorization, in direct response to that specific
   request. **Attempt 2** ran under it (still bare system `python`, since the repo's `venv` had
   not yet been identified as the cause). Failed at `verify_pinned_dependency_versions`: bare
   `python` had none of the five pinned packages installed (`ModuleNotFoundError: No module named
   'torch'`) — an interpreter-selection error on Claude's part, not a package or repo-state defect.
   Claude reported this, diagnosed the cause, confirmed the repo's own `training/venv/` held the
   exact pinned versions, and explicitly asked: "If you want me to retry using
   `training/venv/Scripts/python.exe run_seed17_phase2_replay.py --confirm-execute` — same
   command, same scope, same commit — say the word and I'll proceed." Did not retry automatically.
4. Johnny replied "Go ahead" — fresh authorization, again in direct response to that specific
   request. **Attempt 3** ran under it, using `training/venv/Scripts/python.exe`
   (`torch==2.11.0+cu128`, `transformers==4.57.6`, `datasets==5.0.0`, `accelerate==1.14.0`,
   `sentencepiece==0.2.2` — exact match to the pinned lock). All twelve preflight checks
   (HEAD/origin sync, package-commit parentage, clean tree, dependency versions, executable-code
   lock, governing-input lock, real-validation emptiness, benchmark counts, split/training-data
   fingerprint, CUDA/bfloat16, command shape, pinned base-model snapshot) passed before the
   experiment directory was created, and the run completed all six execution stages.

**Resolution of the authorization-chain question:** fresh, explicit authorization — each a direct
reply to a specific request Claude posed after reporting the prior failure, not an unprompted or
assumed retry — preceded both attempt 2 and attempt 3. No artifact was ever produced by a failed
attempt, so no invalid-but-completed experiment was ever left unreviewed; each failure was stopped,
reported, and returned to Johnny before any further action, matching §6.1's requirement that "a
rerun requires a separately reviewed disposition; it is never automatic." Attempt 3 is therefore
the one, validly and freshly authorized experiment that entered the outcome matrix. **P2-D stands**
for it; attempts 1 and 2 are recorded here as the preflight-stopped invocations they were, not as
P2-X — no experiment was ever produced by either to classify as invalid, and both were properly
disposed by Johnny before any subsequent action.

## 2. Execution

The successful invocation (attempt 3, §1.1), `training/venv/Scripts/python.exe
run_seed17_phase2_replay.py --confirm-execute`, ran the full authorized sequence with no manual
intervention between stages: primary train → primary eval ×2 → control train → control eval ×2,
all offline (`HF_HUB_OFFLINE=1`/`TRANSFORMERS_OFFLINE=1`), fail-closed at every step.

| | Primary (natural) | Control (step-matched) |
|---|---|---|
| Seed | 17 | 17 |
| `--max-steps` | unset (epoch-based) | `600` |
| Completed steps (`trainer_state.json`, independently read) | **720/720**, epoch 40.0 | **600/600**, epoch 33.33 |
| `train_runtime` | 277.99s | 272.57s |
| Checkpoint | `controlled_seed17_phase2_replay_run/primary/checkpoint/final` | `controlled_seed17_phase2_replay_run/control/checkpoint/final` |

Both runs used `data/processed_gold_v1.2.2_phase2_v2contract_seed17`, base model
`google/flan-t5-base` @ `7bcac572ce56db69c1ea7c8af255c5d7c9672fc2`, contract `v2`. No seed 73
appears anywhere in either train log (confirmed by direct search). Total wall-clock: receipt
written 08:42:06, control finished 08:53 — roughly 11 minutes.

Raw evaluation artifacts, independently verified against the actual benchmark files (not the
wrapper's own summary) — record counts, ID/order match, every record carrying `raw_output`, every
`scores`/`capability_checks` value still null, `failure_labels` empty:

| | count | IDs/order match benchmark |
|---|---|---|
| primary/protected16 | 16/16 | ✓ |
| primary/acceptance10 | 10/10 | ✓ |
| control/protected16 | 16/16 | ✓ |
| control/acceptance10 | 10/10 | ✓ |

## 3. Semantic scoring — ChatGPT scored, Claude independently re-verified

Four raw files scored by ChatGPT; four scored artifacts written to disk and independently
re-verified: SHA-256 recomputed and matched against ChatGPT's manifest; every non-scoring field
(`id`, `raw_output`, `parsed_*`, count rules, contract metadata, ordering) confirmed byte-identical
to the raw originals across all 52 records — only `scores`/`capability_checks`/`failure_labels`
were touched, exactly as claimed.

| Role | Raw SHA-256 | Scored artifact | Scored SHA-256 (current) |
|---|---|---|---|
| Primary 720 / protected-16 | `024d9f20f92cd6340404fd29d7439cbd2b3eac65afe5c3d935e464c2966ea59f` | `phase2_seed17_primary720_protected16_scored_chatgpt.json` | `ea0864b26df3ea5d207d1f736a486ec1d3910728597a445334562a7f2b1dacc9` |
| Primary 720 / acceptance-10 | `6b90f54456c59330518608a6d23996e7b7c13804baf939cd549522e643ce4c69` | `phase2_seed17_primary720_acceptance10_scored_chatgpt.json` | `a9a47ac42c50009ac36b2788bf889a5e74d1e5ad07c980396487783075a1fb89` (revised, §5) |
| Control 600 / protected-16 | `f9ca51334414426255a6babf8f9d16375e2956acae516e1619d0214f8785a36f` | `phase2_seed17_control600_protected16_scored_chatgpt.json` | `8fb5829f2c472ef4c3ede234d68af2b2c57ecd89891d346db9ff8792417f129b` |
| Control 600 / acceptance-10 | `414e75468392cdde61f312b34117e09c37df7bf5324c4754d1dce54ade628cf4` | `phase2_seed17_control600_acceptance10_scored_chatgpt.json` | `900c6b44ee4fef50ffc06ef5011bdb213761d1bf91bfedd3bc6ef052026c2c29` |

Every aggregate below was recomputed independently two different ways — once via the real,
unmodified `report_benchmark.py --contract=v2`, once via a from-scratch pass over the raw scored
JSON against the stated pass definition — and both match ChatGPT's manifest exactly, with no
discrepancy found in any number or ID set.

| Measure | Primary 720 | Control 600 |
|---|---:|---:|
| Protected format validity | 16/16 | 16/16 |
| Protected semantic strict pass | **12/16** | **11/16** |
| Acceptance format validity | 10/10 | 10/10 |
| Acceptance count-rule conformance | 6/10 | 5/10 |
| Acceptance semantic strict pass | 6/10 | 6/10 |
| Acceptance combined strict pass | **5/10** | **5/10** |

Primary protected strict-pass set: `{01, 03, 04, 05, 07, 09, 10, 12, 13, 14, 15, 16}`
Control protected strict-pass set: `{01, 03, 04, 05, 07, 10, 12, 13, 14, 15, 16}`
Both acceptance combined-pass sets: `{sdi2-01, sdi2-02, sdi2-04, sdi2-05, sdi2-09}`
Both acceptance failing sets: `{sdi2-03, sdi2-06, sdi2-07, sdi2-08, sdi2-10}`

Case-by-case semantic judgments were independently read against the actual benchmark rubric
(`expected_behavior`/`primary_checks`) and `raw_output` text for every failing probe plus the one
flagged item; all held up under independent reading, including subtle primary/control differences
(e.g. control sdi2-03 invents two *separate* actions vs. primary's one *merged* action — the
scoring correctly differentiates `NO_TOPIC_MERGE` true-vs-false between them).

## 4. Probe-06 regression (the reason gate 6 fails for both runs)

**Protected probe 06** (`multi_person_attribution`, adversarial) is the single required-set probe
missing from primary's pass set, and one of two missing from control's. Both runs misattribute who
asked about the permit:

- Expected: preserve the ambiguity over who needs the stamped copy; "she asked" may resolve to
  Tessa via ordinary nearest-antecedent reading, but must not be confidently reassigned.
- **Primary** misattributes in both fields: narrative reads "...after **Rowan** asked about it,"
  and the bullet reads "**Rowan** had asked about the permit."
- **Control** keeps the narrative correctly ambiguous ("...after **she** asked about it") but
  still misattributes in the bullet: "**Rowan** had asked about the permit" — the same wrong
  resolution, confined to a different field. (Verified by direct string comparison of both raw
  texts, not assumed identical across runs — an earlier draft of this record incorrectly stated
  both runs used identical wording.)
- The separate stamped-copy-need ambiguity *is* correctly preserved in both
  (`ambiguity preserved: true`), so this is a partial defect in both
  (`attribution_accuracy=1`, `unsupported_addition_resistance=1`, `ATTRIBUTION_CORRECT: false`) —
  a real, visible regression against the R2 replay's own passing result on this probe in both
  runs, not a scoring artifact.

**Protected probe 09** fails for control only (not primary) — a second, distinct diagnostic-control
difference: primary keeps the volunteer-list reference an incomplete thought
(`INCOMPLETE_THOUGHT_REMAINED_INCOMPLETE: true`), while control's `raw_output` invents a new
question ("whether the volunteer list was sent to Imani") not present in the source
(`INCOMPLETE_THOUGHT_REMAINED_INCOMPLETE: false`). Independently confirmed against both raw texts.

**Protected probe 13** (the R2 replay's known failure) is repaired in both runs — both action items
survive as separate, distinct actions in both `raw_output`s.

## 5. Metadata correction (does not affect any outcome)

`primary/acceptance10` record `sdi2-06` carried `failure_labels: ["Topic Loss"]` despite
`topic_completeness=2` and every capability check `true` — an inconsistent leftover label, caught
independently and confirmed by Johnny. Corrected to `failure_labels: []`; no other field touched.
New SHA-256 `a9a47ac4...` (table in §3). Preservation diff re-run on all four files: still clean.
Reporter re-run on the corrected file: **5/10 acceptance gates, identical failing set** — the only
change anywhere in any report output is the taxonomy tally (`Topic Loss: 2 → 1`). This correction
lives entirely in the acceptance-10 ID space (`sdi2-*`) and cannot affect gate 6, which is computed
solely from the protected-16 files (`01`–`16`), confirmed disjoint and untouched.

## 6. Six frozen gates, applied independently to each run

Required protected preservation-and-repair set (13 probes, confirmed identical across
`receipt.json`, the `GATE6_REQUIRED_PASS_SET` constant in `run_seed17_phase2_replay.py`, and the
governing document's §5.1 derivation): `{01, 03, 04, 05, 06, 07, 09, 10, 12, 13, 14, 15, 16}`.

### Primary 720

| # | Gate | Requirement | Result | Status |
|---:|---|---|---|---|
| 1 | Protected format validity | 16/16 | 16/16 | **PASS** |
| 2 | Acceptance format validity | 10/10 | 10/10 | **PASS** |
| 3 | Acceptance count-rule conformance | 10/10 | 6/10 | **FAIL** |
| 4 | Acceptance combined strict pass | 10/10 | 5/10 | **FAIL** |
| 5 | Protected strict pass | ≥ 12/16 | 12/16 | **PASS** |
| 6 | Protected preservation and repair | all 13 listed probes pass | missing `{06}` | **FAIL** |

### Control 600

| # | Gate | Requirement | Result | Status |
|---:|---|---|---|---|
| 1 | Protected format validity | 16/16 | 16/16 | **PASS** |
| 2 | Acceptance format validity | 10/10 | 10/10 | **PASS** |
| 3 | Acceptance count-rule conformance | 10/10 | 5/10 | **FAIL** |
| 4 | Acceptance combined strict pass | 10/10 | 5/10 | **FAIL** |
| 5 | Protected strict pass | ≥ 12/16 | 11/16 | **FAIL** |
| 6 | Protected preservation and repair | all 13 listed probes pass | missing `{06, 09}` | **FAIL** |

Neither run passes all six gates (primary: 3/6; control: 2/6). Per §6 of the governing document, a
pass requires all six.

## 7. Outcome classification

| | Natural 720 primary | Step-matched 600 control |
|---|---|---|
| Gate result | **Fail** | **Fail** |

Per the governing document's outcome matrix: **Fail / Fail → P2-D — Phase-2 does not clear the
frozen gate under either tested step budget.**

Per §6/§7 of the governing document, P2-D's required next actions:

- Stop. No automatic rerun.
- Seed 73 is **not eligible** — P2-D blocks it entirely, and it was never automatic regardless.
- The control does not and cannot substitute for the primary — it never competed for promotion
  (§7, item 5: "The primary is always interpreted first. The control explains sensitivity; it does
  not compete for promotion"), and both fail independently in any case.
- No export, deployment, activation, or production promotion follows.
- Use only verified residual failures (probe 06 misattribution common to both; probe 09 as an
  additional control-only diagnostic difference; the unresolved acceptance-10 failure classes on
  `sdi2-03/06/07/08/10`, unchanged in character from the R2 replay's own residuals) for any later
  proposal — itself a separate, later, separately authorized static review, not started by this
  record.

## 8. Preservation

Preserved on disk, uncommitted, pending Johnny's authorization to commit/push: the raw result
files, both train logs, and both eval logs per run (under
`controlled_seed17_phase2_replay_run/{primary,control}/`), the single shared
`controlled_seed17_phase2_replay_run/receipt.json` (at the run root, not under either
`primary/` or `control/`), the four scored artifacts, the scoring manifest, ChatGPT's
scoring-review document, and this outcome record. Checkpoints
(`controlled_seed17_phase2_replay_run/{primary,control}/checkpoint/`) are preserved on local disk;
consistent with this repository's unbroken history, no checkpoint or raw execution log is intended
for commit.

## 9. Independent verification of this record

Every hash, count, ID set, and gate result above was recomputed fresh from the pinned files on disk
after this document's first draft was complete (`receipt.json`, the four scored JSON files as
currently saved, the raw result files, `run_seed17_phase2_replay.py`'s own
`GATE6_REQUIRED_PASS_SET` constant, and the governing document's §5 text), not merely transcribed
from earlier chat turns or memory. All eleven hashes, both step counts, and both capability-check
values checked matched exactly. This pass caught one real inaccuracy in the first draft's own
prose (§4): it had described both runs' probe-06 `raw_output` as identically worded ("...after
Rowan asked about it"), which direct string comparison showed was true only for primary — control
keeps its narrative correctly ambiguous and misattributes only in the bullet field. Corrected
before finalizing. This did not change any score, capability check, aggregate, gate result, or the
P2-D classification — only the precision of the field-level description in §4.

## 10. Explicit non-authorizations (unchanged)

This record does not authorize: seed 73 (blocked outright by P2-D), a new Phase-2 proposal, corpus
mutation, export, deployment, activation, production promotion, or commit/push. Commit and push of
this record and its companion artifacts require Johnny's separate, explicit authorization, per this
project's standing pattern.
