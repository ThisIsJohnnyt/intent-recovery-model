# Controlled Seed-17 Regression-Balanced Repair — Execution Specification

**Date:** 2026-08-11  
**Author:** ChatGPT  
**Status:** Draft for Claude independent review; execution-package design only; no compute authorized  
**Repository:** `ThisIsJohnnyt/intent-recovery-model`  
**Pinned corpus milestone:** `90ee08d17304e5a124f15f19f9644a1f609083ba` on `main`  
**Direct parent:** `43f4fc41264469ac2848340c8bea8e216dba8368`  
**Governing corpus design:** `training/controlled_seed17_regression_balanced_repair_design_chatgpt.md`  
**Governing implementation proposal:** `training/controlled_seed17_regression_balanced_repair_implementation_proposal_chatgpt.md`  
**Static gate result:** 15/15 PASS in `training/regression_balanced_repair_gate_compliance_report.md`  
**Purpose:** Determine whether the reviewed 85-record regression-balanced candidate clears the frozen protected and acceptance gates under the same matched-condition seed-17 comparison used by the prior controlled replay.

## 1. Decision and scope

Design a fail-closed two-arm seed-17 replay:

| Arm | Corpus | Role | Optimizer-step policy |
|---|---|---|---:|
| **Treatment** | Reviewed 85-record regression-balanced candidate; 79 train / 6 validation | Sole decision-bearing candidate | Exactly 720 steps |
| **Comparator** | Preserved 78-record Phase-2 baseline; 72 train / 6 validation | Diagnostic corpus comparator only | Exactly 720 steps |

Both arms use `seed=17` and `data_seed=17`, start independently from the same pinned base-model snapshot, and use isolated output directories. Neither arm may resume from or reuse any checkpoint, optimizer, scheduler, RNG state, or output from another run.

The treatment is the only candidate. The comparator cannot be substituted for it after results are known.

This document does not authorize training, inference, package implementation, checkpoint work, semantic scoring, seed 73, export, deployment, activation, cleanup, commit, or push. It defines the proposed experiment for independent review.

## 2. Mechanism-isolation decision

Run the reviewed 85-record corpus as one combined treatment. Do not create separate, incremental, or ablation training arms for Groups A–D in this experiment.

Reasons:

1. The 85-record combined candidate is the only new corpus that passed the complete 15-gate static review.
2. Separate or incremental arms would require new derived corpora, fingerprints, manifests, collision reviews, splits, and authorizations.
3. Groups B and C contain only two and one added records respectively; training isolated arms would invite unstable post-hoc interpretation.
4. Group D adds no records; its protection is carried by the preserved baseline exemplars and frozen behavioral gates.
5. The experiment asks whether the complete regression-balanced repair clears, not which individual record caused an outcome.

The record manifest's `A_attribution`, `B_action_completeness`, `C_source_state`, and `D_structural` labels remain mandatory for interpretation. They may organize predeclared diagnostic tables after scoring, but they do not create additional promotion rules or permit causal claims from a single paired run.

## 3. Why both arms remain fixed at 720 steps

Use exactly one `--max-steps 720` argument in each training command.

- The comparator's 72-record train split reaches 720 steps at the historical 40-epoch-equivalent schedule.
- The treatment's 79-record train split reaches exactly 36.0 epoch-equivalents at 720 steps (`ceil(79 / 4) = 20` optimizer steps per epoch).
- A natural 40-epoch treatment schedule would reach 800 steps and confound corpus content with 80 additional optimizer updates and a different scheduler horizon.
- The prior controlled seed-17 comparison also used 720/720, preserving schedule continuity with the established protocol.

No natural-800, schedule-search, early-stopping, checkpoint-selection, or alternate-step arm belongs in this experiment. Any future schedule study requires a new design before results are observed.

## 4. Frozen corpus and split inputs

### 4.1 Treatment

| Item | Frozen value |
|---|---|
| Candidate | `training/gold_v1.2.2_regression_balanced_repair_candidate.jsonl` |
| Candidate records / git-blob SHA-256 | 85 / `955437e2ac014c3e48402867e51ac539334e907d61d05dde6e7d7da1ded254ea` |
| Processed directory | `training/data/processed_gold_v1.2.2_regression_balanced_repair_v2contract_seed17` |
| Train records / git-blob SHA-256 | 79 / `7b76450be9f38447b8d5d0acc88d9b3683fd68a3af834961c425f50a97024578` |
| Validation records / git-blob SHA-256 | 6 / `8aa99a794f495cf75e6904ee28789e06ac43c1f9ee424f0b2ce2f219527623c4` |
| Canonical training-data fingerprint | `badfed9f946bd13379e1f74336b18c596c922cf378cc3853ea95a2098ea03800` |

All seven reviewed proposal records must occur exactly once in treatment train and zero times in validation. The first 78 candidate records must remain byte-identical to the preserved comparator corpus, followed by the reviewed seven-record delta in manifest order.

### 4.2 Comparator

| Item | Frozen value |
|---|---|
| Candidate | `training/gold_v1.2.2_phase2_derived_candidate.jsonl` |
| Candidate records / git-blob SHA-256 | 78 / `6e9e5f1bea8fc3cbcb615376a1d055bd273605d0f8c1e40a8c120720c8cb836c` |
| Processed directory | `training/data/processed_gold_v1.2.2_phase2_v2contract_seed17` |
| Train records / git-blob SHA-256 | 72 / `8760378519365c4fe2ae4dcebdc6379214cc0fcf93442521f64d6d4508bafae6` |
| Validation records / git-blob SHA-256 | 6 / `8aa99a794f495cf75e6904ee28789e06ac43c1f9ee424f0b2ce2f219527623c4` |
| Canonical training-data fingerprint | `9d6817152087685b653830ad671f9304e4226b095a202ca57f5ca52bc3a14c1f` |

The treatment and comparator validation files must be byte-identical. The comparator must be freshly trained in the same execution package; prior checkpoints or prior raw results are evidence only and cannot replace the comparator arm.

### 4.3 Benchmarks and immutable shared inputs

| Item | Frozen value |
|---|---|
| Protected benchmark | `datasets/benchmark/gold_v1.2.1_probes.jsonl`; 16 records; git-blob SHA-256 `767fe21a1097b51cef38728dcff0ff9ca4cf280bde8e65a7d885729f40990c0f` |
| Acceptance benchmark | `datasets/benchmark/source_determined_items_v2_acceptance_draft.jsonl`; 10 records; git-blob SHA-256 `b8fe4d4178e5b508757db998eacb1ee979518697c8df759ba1739227c88d448e` |
| Base model | `google/flan-t5-base` |
| Base-model snapshot revision | `7bcac572ce56db69c1ea7c8af255c5d7c9672fc2` |
| Contract | `v2` |

The later static package must independently re-pin the real-validation file, prompt/parser/evaluator import closure, model snapshot files, and every executable dependency it will trust. It must accept canonical LF or its exact uniform-CRLF checkout representation only and fail on mixed endings, bare CR, BOM, missing terminal newline, blank-line drift, whitespace/content drift, or fingerprint mismatch.

## 5. Frozen shared training configuration

Both arms must use exactly:

- `seed=17`, `data_seed=17`;
- per-device train batch size 4;
- per-device evaluation batch size 4;
- learning rate `3e-4`;
- weight decay `0.01`;
- exactly 720 optimizer steps;
- `load_best_model_at_end=False`;
- input and target token limits 512;
- generation `max_new_tokens=300` and `repetition_penalty=1.3`;
- bf16 on CUDA;
- the same pinned Python interpreter, dependency versions, base-model snapshot, training code, evaluator code, and import closure.

Expected dependency versions, subject to exact preflight verification:

| Dependency | Version |
|---|---|
| torch | `2.11.0+cu128` |
| transformers | `4.57.6` |
| datasets | `5.0.0` |
| accelerate | `1.14.0` |
| sentencepiece | `0.2.2` |

The receipt must capture the actual Python, CUDA, GPU, driver, operating-system, and dependency state. CUDA training is not presumed bit-identical; this is a paired matched-condition corpus comparison, not an exact counterfactual trajectory.

## 6. Frozen run order and artifact isolation

Run order is fixed before results:

1. Treatment training.
2. Treatment Protected-16 raw evaluation.
3. Treatment Acceptance-10 raw evaluation.
4. Comparator training.
5. Comparator Protected-16 raw evaluation.
6. Comparator Acceptance-10 raw evaluation.

Proposed experiment root:

`training/controlled_seed17_regression_balanced_repair_run/`

Each arm must have isolated `checkpoint/`, `train_log.txt`, `protected16_log.txt`, `acceptance10_log.txt`, `protected16_results.json`, and `acceptance10_results.json`. The root, arm directories, receipt, logs, result files, and checkpoint directories must be exclusively created and never reused or overwritten.

The execution wrapper produces raw, unscored evaluation scaffolds only. Semantic scoring, independent verification, aggregate computation, outcome classification, checkpoint disposition, and any commit are later milestones.

## 7. Preflight before any experiment-root creation

The future wrapper must fail closed unless all checks pass:

1. Fetch and require `HEAD == origin/main ==` the eventual execution-package commit.
2. Require that package commit's direct parent to be `90ee08d17304e5a124f15f19f9644a1f609083ba`, unless both reviewers explicitly approve a revised lineage before implementation.
3. Require the execution-package commit delta to contain exactly its reviewed manifest; no extra path.
4. Run from a fresh clean linked worktree or clone at the exact package commit. Do not delete, move, or allowlist the unrelated untracked artifacts in the main checkout.
5. Verify every trusted working file against its committed git blob and external fingerprint lock.
6. Verify the recursive repository-local executable import closure.
7. Verify corpus/split counts, canonical hashes, logical fingerprints, validation identity/order, and arm-path separation.
8. Verify all seven proposal records occur exactly once in treatment train, zero times in treatment validation, and zero times in comparator.
9. Verify treatment candidate equals the comparator's 78 records plus exactly the reviewed seven records in order.
10. Verify benchmark count, ID uniqueness, ID order, schema, and canonical hash.
11. Verify the real-validation file remains in the frozen empty state required by the evaluator.
12. Verify dependency versions, interpreter, CUDA availability, bf16 capability, GPU visibility, and pinned base-model snapshot files.
13. Verify each train command contains seed/data-seed 17, its own data/output paths, and exactly one `--max-steps 720`.
14. Verify no treatment/comparator path overlap and no reference to historical checkpoints.
15. Verify the experiment root does not exist.
16. Write a pre-execution receipt by exclusive creation before launching the first subprocess.

Any failure stops before compute and preserves diagnostics. The wrapper may not weaken checks, rewrite inputs, clean the repository, choose another interpreter, retry automatically, or silently continue.

## 8. Execution and raw-artifact validation

Use the previously accepted interruption-safe behavior:

- stream stdout/stderr directly to exclusively created logs;
- check every exit code immediately;
- preserve partial logs/artifacts on failure or interruption;
- use no shell pipeline and no in-memory-only logging;
- perform no automatic rerun.

After each training arm, require the completed trainer state to show `global_step == 720`. After each benchmark evaluation, immediately require:

- a parseable JSON array;
- exactly 16 or 10 records;
- IDs unique and identical to benchmark order;
- non-empty `raw_output` for every record;
- `scores` with exactly the expected keys and every value null;
- `capability_checks` exactly matching that probe's `primary_checks`, every value null, with legitimate empty dictionaries accepted;
- `failure_labels == []`;
- no result/log/checkpoint path overlap across arms.

Invalid raw output or an invalid arm makes the entire paired experiment `RBR17-X`. A valid treatment does not survive an invalid comparator because the authorized experiment is the pair.

## 9. Frozen semantic gates

After ChatGPT scores all four raw artifacts and Claude independently verifies preservation and scoring, apply these six gates separately to each arm:

1. Protected format validity: 16/16.
2. Acceptance format validity: 10/10.
3. Acceptance count-rule conformance: 10/10.
4. Acceptance combined strict pass: 10/10.
5. Protected semantic strict pass: at least 12/16.
6. Every protected identity in the required set passes.

Semantic strict pass requires `format_valid == true`, every applicable/non-null semantic score exactly 2, and every capability check exactly `true`. Acceptance combined pass additionally requires both bullet-count and action-count results to pass.

Gate-6 required protected set:

`{01, 03, 04, 05, 06, 07, 09, 10, 12, 13, 14, 15, 16}`

Aggregate improvement cannot compensate for a missing required identity. In particular, protected 06 must retain the attribution/ambiguity repair; 08 must not distort the unresolved source/drying observation; 09 must preserve open and incomplete states; 10 must retain the shipping-label task; 11 must retain `by Thursday` in the action; 13 must retain two distinct tasks; and 16 must preserve unresolved references without losing supported action content.

The complete protected and acceptance suites remain governing. The named cases are diagnostic emphases, not a reduced evaluation subset.

## 10. Predeclared diagnostic views

After gate computation—and never as substitutes for the gates—report:

- protected and acceptance pass/fail sets for each arm;
- treatment-only gains, treatment-only regressions, shared passes, and shared failures;
- count-conformance sets;
- the exact required-set misses;
- outcomes for protected `{06, 08, 09, 10, 11, 13, 16}` and acceptance `{sdi2-02, sdi2-07, sdi2-08, sdi2-09, sdi2-10}`;
- record-group-aligned interpretation for Groups A–D, explicitly labeled observational rather than causal.

No result may be reclassified by aggregate score, validation loss, checkpoint loss, narrative impression, or a favorable subgroup if a frozen gate fails.

## 11. Frozen outcome matrix

| Outcome | Treatment | Comparator | Consequence |
|---|---|---|---|
| **RBR17-A** | Passes all six gates | Fails one or more | Discriminating candidate success. Preserve and verify artifacts. Seed 73 becomes eligible for a separately reviewed matched-package proposal; it does not start automatically. |
| **RBR17-B** | Passes all six gates | Passes all six | Candidate clears, but comparison does not discriminate the repair from run variability. Stop for interpretation. Seed 73 is not automatically eligible. |
| **RBR17-C** | Fails one or more | Fails one or more | Candidate does not clear. Stop and diagnose verified residuals only. No seed 73. |
| **RBR17-D** | Fails one or more | Passes all six | Negative/reversed result. Stop. No seed 73 and no comparator substitution. |
| **RBR17-X** | Either arm invalid | Either arm invalid | Entire experiment invalid. Preserve partial artifacts. No automatic rerun. |

The comparator is not required to reproduce earlier raw text or an earlier exact pass set. Configuration, provenance, and artifact integrity determine validity; behavior is evidence.

## 12. Checkpoint, scoring, and preservation policy

- Neither final nor intermediate checkpoint may be selected, promoted, exported, deployed, or used for further training during this experiment.
- Validation loss does not select an outcome and cannot override gates.
- Raw results must be copied for scoring without modifying the execution originals; originals remain hash-pinned.
- Only scoring fields may change in scored copies: `scores`, `capability_checks`, and `failure_labels`.
- ChatGPT is the default primary semantic scorer; Claude independently verifies every judgment and all non-scoring-field preservation. Any role reversal must be explicitly recorded and receive independent review.
- Final outcome classification requires a jointly verified gate matrix and Johnny's decision.

## 13. Required future static execution package

After this design is independently accepted and Johnny separately authorizes implementation, Claude should create an uncommitted static package for ChatGPT review containing at least:

1. this exact design document;
2. machine-readable frozen design constants;
3. a frozen manifest;
4. a frozen fingerprint/import-closure lock;
5. `training/run_seed17_regression_balanced_repair.py`, plan-only by default and requiring `--confirm-execute`;
6. `training/test_run_seed17_regression_balanced_repair.py` with dummy subprocess and fail-closed tests;
7. a clearly labeled non-execution dry-run receipt sample.

Implementation may reuse proven functions from `run_seed17_contrastive_replay.py`, but every executable byte, path, fingerprint, command, test, and import must be re-derived and reviewed. It must not edit corpus, split, benchmark, rubric, prompt, parser, evaluator, historical run, checkpoint, scoring, or production files.

## 14. Minimum static and dry-run test matrix

The future test suite must cover at least:

- plan-only default creates no experiment root and performs no compute or input mutation;
- exact treatment/comparator command construction;
- missing, duplicate, or wrong `--max-steps` failure;
- seed, data-directory, arm, or output-path swap failure;
- wrong HEAD, wrong parent, unsynced origin, dirty execution checkout, wrong package delta, or unexpected path failure;
- working-tree versus committed-blob mismatch failure;
- canonical LF and exact uniform-CRLF equivalence, with mixed/bare-CR/BOM/whitespace/blank-line/terminal-newline drift failure;
- corpus/split counts, fingerprints, validation identity, seven-record membership, and exact 78+7 ordering checks;
- dependency, CUDA/bf16, model snapshot, benchmark, real-validation, or import-closure drift failure;
- pre-existing experiment root or output collision failure;
- exclusive receipt creation before subprocess launch;
- interruption/subprocess failure preserving partial artifacts and stopping the sequence;
- wrong final global step failure;
- malformed, missing, reordered, cross-arm, or partially scored raw-result failure;
- legitimate empty `capability_checks` acceptance;
- dry-run receipt containing no claim that compute occurred.

Claude should report assertion count, dry-run behavior, exact package paths/hashes, and staged-blob verification plan. ChatGPT must independently review the complete static package before any commit or compute decision.

## 15. Authorization ladder

1. **Current milestone:** execution specification draft only.
2. Claude independently reviews this design; material disagreement stops.
3. Johnny decides whether to authorize static execution-package implementation.
4. Claude implements the static package uncommitted; ChatGPT independently reviews it.
5. Johnny separately authorizes commit/push if desired.
6. Both reviewers verify the exact committed package and execution preflight.
7. Johnny explicitly authorizes `--confirm-execute` compute.
8. Execution produces raw artifacts only; scoring and classification are later gated milestones.

No earlier rung implies a later one.

## 16. Questions for Claude's independent review

Claude should answer with direct evidence:

1. Does the combined 85-versus-78 design answer the narrow candidate question without requiring unreviewed group-specific corpora?
2. Does fixed 720/720 isolate corpus content better than 800/720 in this training stack?
3. Are all corpus, split, benchmark, fingerprint, validation-membership, and seven-record-delta values correct at `90ee08d...`?
4. Are the six gates and five outcome cells mechanically reproducible and consistent with the prior frozen protocol?
5. Does the required-set and diagnostic-emphasis list adequately protect every verified regression boundary without becoming a reduced benchmark?
6. Can the prior wrapper be adapted without weakening clean-worktree, import-closure, line-ending, interruption, raw-result, or exclusive-write protections?
7. Is seed-73 eligibility appropriately limited to `RBR17-A` and separately gated?
8. Does any statement silently authorize compute, scoring, checkpoint use, commit, deployment, or another corpus mutation?

Any material disagreement is work-stopping and returns to Johnny with both positions and evidence.

**Disposition:** EXECUTION SPECIFICATION DRAFTED — COMBINED 85-vs-78 MATCHED 720/720 DESIGN — AWAITING CLAUDE INDEPENDENT REVIEW — NO STATIC EXECUTION PACKAGE OR COMPUTE AUTHORIZED.
