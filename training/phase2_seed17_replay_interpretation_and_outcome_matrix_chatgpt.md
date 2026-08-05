# Phase-2 Seed-17 Replay - Interpretation and Outcome Matrix

**Project:** Intent Recovery Model  
**Date:** 2026-08-04  
**Repository milestone:** `main` / `origin/main` at `d90fc13` after the reviewed Phase-2 derivation gate  
**Status:** ChatGPT static decision package for Johnny and Claude review  
**Authorization status:** This document authorizes nothing by itself. It does not authorize package implementation, training, inference, benchmark execution, semantic scoring, seed 73, export, deployment, activation, commit, or push.

## 1. Decision being frozen

The Phase-2 candidate contains 78 records, split into 72 train and 6 validation records. With the existing training configuration (`batch_size=4`, `num_train_epochs=40`), the natural run has exactly 18 optimizer steps per epoch and exactly 720 optimizer steps total. The already-reviewed step-count confound requires a second run capped at 600 optimizer steps.

The two runs do not have equal decision status:

| Run | Frozen role | Step policy | Decision status |
|---|---|---|---|
| Natural 720 | Phase-2 primary candidate | 40 epochs, `--max-steps` omitted | Sole decision-bearing Phase-2 candidate |
| Step-matched 600 | Diagnostic control | Same configuration with `--max-steps=600` | Explains step-budget sensitivity; never a post-hoc substitute for the primary |

The primary checkpoint must not be replaced by the control merely because the control scores better. A future proposal may choose a 600-step regimen only through a new static review and authorization made after this experiment, not by relabeling the diagnostic checkpoint.

## 2. Evidence pinned before implementation

The replay package must use the committed Phase-2 derivation artifacts without rebuilding or mutating them:

| Artifact | Frozen value |
|---|---|
| Candidate corpus | `training/gold_v1.2.2_phase2_derived_candidate.jsonl` - 78 records |
| Candidate corpus SHA-256 | `f738f9eba2e85086bf6019bffdd27410b7add5c566c086a1b3627703e14ad52b` |
| Training split | `training/data/processed_gold_v1.2.2_phase2_v2contract_seed17/train.jsonl` - 72 records |
| Training split SHA-256 | `02d81b3891a517a41cf3261b733f70f5268710b79b18e3b3819e8dbbcdd7cafb` |
| Validation split | `training/data/processed_gold_v1.2.2_phase2_v2contract_seed17/val.jsonl` - 6 records |
| Validation split SHA-256 | `83abbc796187860b511b2c18c964b0757df4bc343ace50862ea15bd590715294` |
| Canonical training-data fingerprint | `9d6817152087685b653830ad671f9304e4226b095a202ca57f5ca52bc3a14c1f` |
| Protected benchmark | `datasets/benchmark/gold_v1.2.1_probes.jsonl` - exactly 16 records |
| Protected benchmark SHA-256 | `044708641c8dd584f334f16bde21ed89550bb7c464160827433f825eb0c48e94` |
| Acceptance benchmark | `datasets/benchmark/source_determined_items_v2_acceptance_draft.jsonl` - exactly 10 records |
| Acceptance benchmark SHA-256 | `b8fe4d4178e5b508757db998eacb1ee979518697c8df759ba1739227c88d448e` |
| Base model | `google/flan-t5-base` |
| Pinned local snapshot revision | `7bcac572ce56db69c1ea7c8af255c5d7c9672fc2` |
| Seed | 17 for both runs |
| Contract | v2 typed-marker contract |
| Dependency versions | `torch==2.11.0+cu128`, `transformers==4.57.6`, `datasets==5.0.0`, `accelerate==1.14.0`, `sentencepiece==0.2.2` |

The base-model file hashes and provenance checks already frozen for the R2 replay should be carried forward unchanged and re-enforced, not summarized from memory.

## 3. Shared variables and the one intended contrast

Both runs must start independently from the same pinned base-model snapshot. Neither run may initialize from, resume from, or reuse optimizer or scheduler state from the other.

Everything below must be identical between runs except the declared step policy and the output paths that keep their artifacts separate:

- seed and data seed: 17;
- candidate `train.jsonl` and byte-identical six-record `val.jsonl`;
- model and tokenizer snapshot;
- prompt contract and serialization;
- batch size 4, learning rate `3e-4`, weight decay `0.01`;
- optimizer family, precision, token limits, generation settings, and checkpoint-selection behavior;
- executable code and installed dependency versions;
- protected-16 and acceptance-10 benchmark definitions, order, and scorer;
- hardware/runtime environment to the extent captured by the receipt.

The natural run omits `--max-steps`; the control includes `--max-steps=600`. This is a step-budget diagnostic, not a claim that the control reproduces the first 600 updates of the natural run. `train.py` explicitly states that `max_steps` also determines the default linear learning-rate scheduler's total-step count. Therefore the two runs can differ in scheduler trajectory before step 600 as well as in total updates.

## 4. Replay-package implementation requirements

If Johnny later authorizes Claude to implement the package, the reviewed draft should contain exactly these new package-level deliverables:

1. a frozen manifest;
2. an external fingerprint lock;
3. one execution wrapper;
4. wrapper tests using dummy subprocesses only;
5. a labeled dry-run receipt sample.

Recommended names are:

- `training/controlled_seed17_phase2_replay_frozen_manifest.md`;
- `training/controlled_seed17_phase2_replay_frozen_fingerprints.json`;
- `training/run_seed17_phase2_replay.py`;
- `training/test_run_seed17_phase2_replay.py`;
- `training/controlled_seed17_phase2_replay_manifest_dryrun_receipt_sample.json`.

The wrapper must default to plan-only behavior and require a literal `--confirm-execute` flag for real subprocess execution. Possession of that flag is not authorization; Johnny must separately name this exact replay after the committed package has passed joint review.

### 4.1 Fail-closed preflight

All preflight checks must pass before the exclusive experiment root is created:

- `HEAD` equals `origin/main` at the package's pinned commit;
- working tree is clean;
- installed dependency versions exactly match the lock;
- the local Hugging Face cache contains the one pinned snapshot and every pinned snapshot file matches;
- all governing inputs and their required record counts match;
- the 72/6 split and canonical training-data fingerprint recompute exactly;
- neither output root exists;
- CUDA/bfloat16 availability matches the frozen runtime expectation;
- both commands resolve to seed 17 and the same Phase-2 data directory;
- the natural command has no `--max-steps` argument;
- the control command has exactly one `--max-steps=600` argument.

The lock must cover the full local executable import closure reached by the wrapper, `train.py`, and both evaluation/reporting paths, not only a manually selected top-level list. At minimum this includes the wrapper, `train.py`, `run_benchmark.py`, `report_benchmark.py`, the contract/parser modules, `prepare_data.py`, `evaluate_real_validation.py`, `real_data_private.py`, and every additional repository-local module imported by those files. The implementation should have a test proving a drift in a transitive local module fails preflight.

`train.py` automatically calls the real-validation evaluator after training. The package must pin `datasets/real_validation.jsonl` and require it to be byte-empty for this replay. A nonempty file must fail preflight. This prevents undeclared private-data inference or an extra artifact from entering a replay whose authorized evaluation scope is only the frozen 26 cases.

### 4.2 Execution and artifact isolation

The wrapper should execute the decision-bearing primary first, then the diagnostic control:

1. primary training at natural 40 epochs / 720 expected steps;
2. primary protected-16 raw evaluation;
3. primary acceptance-10 raw evaluation;
4. control training at exactly 600 steps;
5. control protected-16 raw evaluation;
6. control acceptance-10 raw evaluation.

The root must be atomically created with `exist_ok=False`. Each run must have its own checkpoint directory, result files, and streaming logs. A pre-execution receipt must be written before the first subprocess starts and must include the two exact command sequences, git state, environment, shared configuration, declared differences, and live fingerprints.

Every subprocess must write stdout and stderr directly to an exclusively created log file, preserve its true exit code, and stop the wrapper immediately on failure. No shell pipe, implicit rerun, resume, overwrite, or cleanup is allowed. Partial artifacts and logs must remain in place after interruption or failure.

Completing training must be verified from structured trainer state or an equally direct artifact: exactly 720 steps for the primary and exactly 600 for the control. A mismatch is an invalid experiment even if the subprocess exits zero.

The wrapper produces raw benchmark result scaffolds only. It must not fill semantic scores or select a preferred checkpoint from benchmark results.

## 5. Frozen semantic gates, applied separately to each run

The same six gates apply independently to the primary and control after ChatGPT scoring and Claude verification:

| # | Gate | Pass requirement |
|---:|---|---|
| 1 | Protected format validity | 16/16 |
| 2 | Acceptance format validity | 10/10 |
| 3 | Acceptance count-rule conformance | 10/10 |
| 4 | Acceptance combined strict pass | 10/10 |
| 5 | Protected strict pass | At least 12/16, the R2 replay result |
| 6 | Protected preservation and repair | Every R2-passing protected probe remains a strict pass, and probe 13 is also a strict pass |

### 5.1 Gate 6 wording resolution

The committed static review says both that gate 6 preserves every protected probe passed by the R2 replay and that probe 13 must pass. Read literally, the first clause alone cannot require probe 13 because R2 failed probe 13. This is an internal wording ambiguity, not a reason to weaken the gate.

The fail-closed interpretation frozen here is the conjunction of both stated intentions:

- preserve the R2 strict-pass set `{01, 03, 04, 05, 06, 07, 09, 10, 12, 14, 15, 16}`; and
- repair protected probe `13`.

Thus gate 6 requires all 13 listed probes to pass. Probes `02`, `08`, and `11` may still fail gate 6, although they continue to count normally under gate 5. This explicit set must be encoded in the manifest/tests rather than inferred from the reporter's generic regression-warning line, which prior verification showed can over-flag already-failing probes.

Gate 5 becomes mathematically redundant whenever gate 6 passes, but it remains frozen as a separately reported continuity metric because the approved protocol contains six gates.

## 6. Outcome matrix

An experiment enters this matrix only after both runs complete validly and both sets of raw outputs receive ChatGPT semantic scoring plus Claude's independent verification. A pass below means all six gates pass for that run.

| Outcome | Natural 720 primary | Step-matched 600 control | Interpretation | Next action |
|---|---|---|---|---|
| P2-A | Pass | Pass | Phase-2 clears the gate and the result is robust to the tested step budget | Seed 73 becomes eligible for a new, separate static review and explicit authorization; nothing starts automatically |
| P2-B | Pass | Fail | The primary clears, but the result is schedule/exposure sensitive under this control | Do not authorize seed 73 yet; perform a separate static interpretation review before deciding whether the evidence is strong enough |
| P2-C | Fail | Pass | The approved primary fails while the diagnostic regimen passes | Do not substitute the control post hoc; stop and require a new proposal if a 600-step primary regimen is desired |
| P2-D | Fail | Fail | Phase-2 does not clear the frozen gate under either tested budget | Stop; no seed 73; use only verified residual failures for any later proposal |

Partial metric changes should still be reported, but they cannot convert a fail into a pass or change which run is primary.

### 6.1 Invalid experiment state

Operational invalidity is not P2-A, P2-B, P2-C, or P2-D. Any failed preflight, missing/mismatched fingerprint, dirty or divergent git state, wrong command, wrong step count, nonzero subprocess exit, overwritten output, missing raw result, unauthorized real-validation input, or scoring-integrity failure yields **P2-X: invalid experiment**.

For P2-X, stop immediately, preserve all artifacts and partial logs, make no semantic or seed-73 decision, and return the failure to Johnny. A rerun requires a separately reviewed disposition; it is never automatic.

## 7. Scoring, comparison, and selection rules

1. Execution stops after raw inference on the frozen protected-16 and acceptance-10 sets.
2. ChatGPT scores each run independently using the existing per-probe rubric and 0/1/2 scale.
3. Claude independently verifies artifact integrity, every score, all gate totals, the exact pass-set transitions, and the outcome cell.
4. Any disagreement is surfaced to Johnny and resolved on record; it is not silently averaged or overridden.
5. The primary is always interpreted first. The control explains sensitivity; it does not compete for promotion.
6. No checkpoint is exported, deployed, activated, or treated as a release candidate through this replay.
7. Seed 73 is never automatic. Only P2-A makes it eligible for a later authorization without an intervening interpretation review. P2-B requires such a review first; P2-C, P2-D, and P2-X block it.

## 8. Ownership and the next authorization gate

| Action | Owner | Current status |
|---|---|---|
| Accept, modify, or reject this interpretation policy | Johnny | Next decision |
| Independently challenge the gate-6 resolution and package requirements | Claude | Static review only, if Johnny requests it |
| Build manifest, lock, wrapper, tests, and dry-run receipt | Claude | Not authorized by this document |
| Independently review the uncommitted package | ChatGPT | After implementation is separately authorized and completed |
| Authorize commit/push of reviewed package | Johnny | Later decision |
| Authorize execution of the named replay | Johnny | Separate later decision |
| Score raw outputs | ChatGPT | Only after an authorized valid execution |
| Independently verify scoring and outcome | Claude | Only after ChatGPT scoring |
| Decide whether seed 73 may proceed | Johnny | Only after joint seed-17 review |

## 9. Recommended narrow authorization text

If Johnny accepts this policy, the next authorization should cover package implementation only:

> I authorize Claude to author the uncommitted seed-17 Phase-2 replay package defined by `phase2_seed17_replay_interpretation_and_outcome_matrix_chatgpt.md`: the frozen manifest, external fingerprint lock, plan-only execution wrapper, dummy-subprocess test suite, and labeled dry-run receipt sample for the natural 720-step primary and 600-step diagnostic control. Claude may perform static validation and dry-run receipt generation only. The package must implement the explicit gate-6 pass set and probe-13 repair requirement, full local import-closure fingerprinting, byte-empty real-validation preflight, independent run initialization, artifact isolation, and the P2-A through P2-X outcome rules.
>
> This authorization does not include training, inference, benchmark execution, semantic scoring, corpus mutation, derivation changes, seed 73, export, deployment, activation, commit, or push. All drafts remain uncommitted pending joint ChatGPT/Claude review.

## 10. Verdict

Proceed next only to independent static challenge and, if Johnny accepts the policy, implementation of the frozen replay package. The 720-step natural run is the sole Phase-2 candidate; the 600-step run is a diagnostic control. No compute is authorized at this gate.
