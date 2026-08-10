# Controlled Seed-17 Contrastive Replay — Governing Design

**Date:** 2026-08-10  
**Author:** ChatGPT  
**Status:** Draft for Claude's independent review; design and static package construction only; no compute yet  
**Repository:** `ThisIsJohnnyt/intent-recovery-model`  
**Pinned implementation milestone:** `17c58bf102b7cb442c312f916b3c7c52e3cd8815` on `main`  
**Purpose:** Test whether the reviewed 82-record contrastive corpus repairs the Phase-2 attribution/field-role failure without sacrificing protected behavior or the probe-13 repair.

## 1. Decision and scope

Build a new fail-closed seed-17 replay package with two independently initialized, matched-step arms:

| Arm | Data | Role | Step policy |
|---|---|---|---|
| **Treatment** | 82-record contrastive candidate; 76 train / 6 validation | Sole decision-bearing candidate | Exactly 720 optimizer steps via one `--max-steps 720` argument |
| **Comparator** | Historical 78-record Phase-2 candidate; 72 train / 6 validation | Diagnostic corpus comparator only | Exactly 720 optimizer steps via one `--max-steps 720` argument |

Both arms use seed/data-seed 17 and start independently from the same pinned base-model snapshot. Neither arm resumes from, initializes from, or reuses checkpoint, optimizer, scheduler, or RNG state from the other.

The treatment is the only promotion candidate. The comparator can strengthen or weaken causal interpretation, but it can never replace the treatment after results are known.

This design authorizes no training or inference by itself. Under the standing project protocol, Claude's independent agreement authorizes implementation of the static package. Compute becomes authorized only after both reviewers affirmatively agree that the exact committed package and execution preflight are ready.

## 2. Why both arms are fixed at 720 steps

The scientific question is the effect of the corpus revision, not the effect of a longer schedule.

- The historical Phase-2 train split has 72 records, so 40 epochs naturally produced 720 optimizer steps.
- The contrastive train split has 76 records, so 40 epochs would naturally produce 760 optimizer steps.
- Comparing 760 treatment steps with 720 comparator steps would confound corpus content with 40 additional updates and a different scheduler horizon.
- Fixing both arms at 720 steps holds the declared optimizer-step budget and scheduler horizon constant. The treatment therefore sees approximately 37.9 epochs; this is intentional.

No natural-760 arm belongs in this experiment. Schedule calibration is a later question and must not be added after results are seen.

## 3. Frozen inputs

### 3.1 Treatment

| Item | Frozen value |
|---|---|
| Candidate path | `training/gold_v1.2.2_phase2_contrastive_derived_candidate.jsonl` |
| Candidate records | 82 |
| Candidate canonical-LF file SHA-256 | `7760f377dcd7ab35b54fe6c2c274e6615a5641acaa73ec0a30da64d78db9df2d` |
| Processed data directory | `training/data/processed_gold_v1.2.2_phase2_contrastive_v2contract_seed17` |
| Train count / canonical-LF SHA-256 | 76 / `597b61202b4cc805dfc9eb3376e15d10583c13f41d8a44b7d9d13139acd5c658` |
| Validation count / canonical-LF SHA-256 | 6 / `8aa99a794f495cf75e6904ee28789e06ac43c1f9ee424f0b2ce2f219527623c4` |
| Canonical training-data fingerprint | `62bbee12130ea54f6cae3777eb990a9d54a35411ceeba75030755569c44982ae` |
| Candidate content fingerprint | `a35702c584c5a14f6d4515fdbb85702df98a5d82d31e74d03721411caf964b1a` |

The 16 appended/revised proposal records must all be in treatment train and absent from validation. The validation set must remain the pinned canonical-LF representation of the historical six-record R2 validation split.

### 3.2 Comparator

| Item | Frozen value |
|---|---|
| Candidate path | `training/gold_v1.2.2_phase2_derived_candidate.jsonl` |
| Candidate records | 78 |
| Historical package file SHA-256 | `f738f9eba2e85086bf6019bffdd27410b7add5c566c086a1b3627703e14ad52b` |
| Processed data directory | `training/data/processed_gold_v1.2.2_phase2_v2contract_seed17` |
| Train / validation counts | 72 / 6 |
| Historical package train SHA-256 | `02d81b3891a517a41cf3261b733f70f5268710b79b18e3b3819e8dbbcdd7cafb` |
| Historical package validation SHA-256 | `83abbc796187860b511b2c18c964b0757df4bc343ace50862ea15bd590715294` |
| Canonical training-data fingerprint | `9d6817152087685b653830ad671f9304e4226b095a202ca57f5ca52bc3a14c1f` |

The three historical file hashes above came from the sealed earlier replay package and may represent Windows checkout bytes. During implementation, Claude must independently compute and record the actual git-blob SHA-256 values at `17c58bf...`. The new wrapper must accept only the pinned canonical LF blob or its exact uniform-CRLF checkout representation, normalize for integrity verification, and reject all other byte forms. The logical training-data fingerprint and record counts must also match. No physical-byte pin may be silently copied from the older package without this staged/blob-level check.

### 3.3 Shared benchmarks and model

| Item | Frozen value |
|---|---|
| Protected benchmark | `datasets/benchmark/gold_v1.2.1_probes.jsonl`; 16 records; canonical SHA-256 `044708641c8dd584f334f16bde21ed89550bb7c464160827433f825eb0c48e94` |
| Acceptance benchmark | `datasets/benchmark/source_determined_items_v2_acceptance_draft.jsonl`; 10 records; canonical SHA-256 `b8fe4d4178e5b508757db998eacb1ee979518697c8df759ba1739227c88d448e` |
| Real validation | `datasets/real_validation.jsonl`; must remain byte-empty; SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| Base model | `google/flan-t5-base` |
| Snapshot revision | `7bcac572ce56db69c1ea7c8af255c5d7c9672fc2` |
| Contract | `v2` |

Benchmark and dataset verification must be line-ending portable but fail closed: canonical LF or its exact uniform-CRLF checkout form may be accepted; mixed endings, bare CR, BOM, missing terminal newline, blank-line drift, whitespace/content drift, and any post-normalization fingerprint mismatch must fail.

## 4. Frozen shared training configuration

Both arms must use exactly:

- `seed=17`, `data_seed=17`
- per-device training batch size 4
- per-device evaluation batch size 4
- learning rate `3e-4`
- weight decay `0.01`
- exactly 720 optimizer steps
- `load_best_model_at_end=False`
- base model and tokenizer from the pinned local snapshot
- bf16 on CUDA
- input and target token limits 512
- the existing generation configuration, including `max_new_tokens=300` and `repetition_penalty=1.3`
- the same executable-code import closure and pinned dependency versions for both arms

Expected dependency versions remain:

| Dependency | Version |
|---|---|
| torch | `2.11.0+cu128` |
| transformers | `4.57.6` |
| datasets | `5.0.0` |
| accelerate | `1.14.0` |
| sentencepiece | `0.2.2` |

The exact hardware/runtime environment must be captured in the receipt. Because the current stack does not guarantee bit-identical CUDA training, results may be described only as a **paired matched-condition corpus comparison**, never as the same trajectory or exact counterfactual state.

## 5. Frozen run order and artifacts

Run order is fixed before results:

1. Treatment training.
2. Treatment Protected-16 raw evaluation.
3. Treatment Acceptance-10 raw evaluation.
4. Comparator training.
5. Comparator Protected-16 raw evaluation.
6. Comparator Acceptance-10 raw evaluation.

Recommended experiment root:

`training/controlled_seed17_contrastive_replay_run/`

Each arm must have isolated `checkpoint/`, `train_log.txt`, `protected16_log.txt`, `acceptance10_log.txt`, `protected16_results.json`, and `acceptance10_results.json`. The root and arm directories must be created exclusively and must never be reused or overwritten.

The wrapper produces raw evaluation scaffolds only. Semantic scoring, scoring-manifest creation, aggregate recomputation, and final outcome classification remain a subsequent jointly reviewed checkpoint.

## 6. Preflight — all checks before creating the experiment root

1. Fetch and require `HEAD == origin/main ==` the eventual package commit.
2. Require the package commit's direct parent to be `17c58bf102b7cb442c312f916b3c7c52e3cd8815` unless Claude and ChatGPT explicitly agree to a revised lineage before implementation.
3. Require the package commit delta to contain exactly the reviewed package manifest; no extra path.
4. Require a clean execution checkout. Because the main Windows checkout deliberately contains historical untracked outputs, execution should occur from a fresh linked worktree or fresh clone at the exact package commit. Do not delete, move, or silently allowlist the historical files merely to satisfy preflight.
5. Verify working files against committed git blobs and the external fingerprint lock. Generated data must be verified at the committed/staged-blob level, not only as working-tree files.
6. Recompute the recursive repository-local Python import closure and verify every executable file against the lock.
7. Verify the treatment and comparator counts, normalized canonical hashes, logical training-data fingerprints, exact validation membership/order, and absence of cross-arm path confusion.
8. Verify all 16 contrastive proposal records occur in treatment train and none occur in treatment validation.
9. Verify both benchmarks by canonical hash, record count, ID uniqueness, and ID order.
10. Verify `datasets/real_validation.jsonl` remains byte-empty.
11. Verify dependency versions, Python version, CUDA availability, bf16 capability, and pinned base-model files.
12. Verify both generated train commands contain seed 17, their correct data directory, isolated output paths, and exactly one `--max-steps 720`; neither may omit or duplicate the argument.
13. Verify the experiment root does not exist.
14. Write the pre-execution receipt by exclusive creation before starting the first subprocess.

Any failure stops before compute, preserves diagnostics, and requires correction and joint re-review. The wrapper must never weaken a check, clean the repository, rewrite an input, select another interpreter, or retry automatically.

## 7. Execution and raw-artifact validation

Use the interruption-safe subprocess/logging design already accepted for the prior Phase-2 wrapper:

- direct stdout/stderr streaming to exclusively created log files;
- immediate exit-code checks;
- partial logs/artifacts preserved on failure;
- no shell pipe and no in-memory-only logs;
- no automatic rerun.

After each training arm, inspect Trainer state and require `global_step == 720`. After each benchmark call, validate the raw result immediately:

- file exists and parses as a JSON array;
- exact count 16 or 10;
- IDs are unique and match benchmark ID/order exactly;
- every record has non-empty `raw_output`;
- `scores` contains exactly the expected four keys and every value is null;
- `capability_checks` keys exactly match that probe's `primary_checks` and every value is null, including legitimate empty dictionaries;
- `failure_labels == []`;
- no result path overlaps the other arm.

Any invalid output makes the entire paired experiment `C17-X`. A successful treatment does not survive an invalid comparator, because the agreed experiment is the matched pair.

## 8. Frozen semantic gates

After ChatGPT scores all four raw artifacts and Claude independently verifies preservation and scoring, the same six gates used for the earlier Phase-2 replay apply separately to both arms:

1. Protected format validity: 16/16.
2. Acceptance format validity: 10/10.
3. Acceptance count-rule conformance: 10/10.
4. Acceptance combined strict pass: 10/10.
5. Protected semantic strict pass: at least 12/16.
6. Protected preservation and repair: all probes in the exact required set pass.

Gate-6 required pass set:

`{01, 03, 04, 05, 06, 07, 09, 10, 12, 13, 14, 15, 16}`

Aggregate improvement cannot compensate for a missing required identity. In particular, probe 06 must be repaired, probe 13 must remain repaired, and probe 09 must remain preserved.

## 9. Frozen outcome matrix

| Outcome | Treatment | Comparator | Meaning and next action |
|---|---|---|---|
| **C17-A** | Passes all six gates | Fails one or more gates | Discriminating candidate success. Preserve and verify artifacts; seed 73 becomes eligible for a new matched-package review. It does not start automatically. |
| **C17-B** | Passes all six gates | Passes all six gates | Candidate clears, but the comparison does not discriminate the contrastive revision from run variability. Stop for interpretation; seed 73 is not automatically eligible. |
| **C17-C** | Fails one or more gates | Fails one or more gates | Candidate does not clear. Stop; diagnose only verified residuals. No seed 73. |
| **C17-D** | Fails one or more gates | Passes all six gates | Negative/reversed result. Stop; no seed 73 and no post-hoc substitution. |
| **C17-X** | Either arm invalid | Either arm invalid | Entire paired experiment invalid. Preserve partial artifacts; no automatic rerun. |

The comparator is not required to reproduce the earlier P2-D raw text or exact pass set. CUDA nondeterminism makes that too strong. Its behavioral result is evidence, not a precondition for validity; configuration, provenance, and artifact integrity determine validity.

## 10. Required static package

Claude should implement and leave uncommitted for ChatGPT's independent review:

1. `training/seed17_contrastive_replay_design_chatgpt.md` — exact governing design bytes.
2. `training/seed17_contrastive_replay_design_constants_chatgpt.json` — exact machine-readable design constants; implementation locks may add verified repository-specific blob hashes but may not change these values silently.
3. `training/controlled_seed17_contrastive_replay_frozen_manifest.md`.
4. `training/controlled_seed17_contrastive_replay_frozen_fingerprints.json`.
5. `training/run_seed17_contrastive_replay.py` — plan-only by default; execution requires `--confirm-execute`.
6. `training/test_run_seed17_contrastive_replay.py` — dummy subprocess/static test suite.
7. `training/controlled_seed17_contrastive_replay_manifest_dryrun_receipt_sample.json` — clearly labeled non-execution sample.

The implementation may reuse proven functions from the previous wrapper, but the new file and import-closure hashes must be recomputed. The new package must not edit the committed corpus, split, benchmark, historical replay, postmortem, scoring, checkpoint, or production files.

## 11. Minimum static and dry-run test matrix

The suite must cover at least:

- plan-only default performs no training, inference, directory creation, or input mutation;
- valid treatment/comparator command construction;
- missing, duplicate, or wrong `--max-steps` fails;
- arm/data-directory swap fails;
- treatment/comparator output-path overlap fails;
- wrong HEAD, wrong parent, unsynced origin, dirty checkout, wrong package delta, or unexpected file fails;
- working-tree-versus-git-blob mismatch fails;
- LF and exact uniform-CRLF checkouts pass and resolve to identical canonical hashes;
- mixed endings, bare CR, BOM, whitespace/content drift, blank-line drift, and terminal-newline drift fail;
- treatment/comparator record counts, membership, validation identity, and training-data fingerprints are independently checked;
- any missing contrastive record from treatment train or any contrastive record in validation fails;
- dependency, CUDA/bf16, base-model snapshot, benchmark, or real-validation drift fails;
- pre-existing experiment root or output collision fails;
- receipt is exclusively created before subprocess launch;
- subprocess failure and interruption preserve partial logs and stop the sequence;
- wrong completed step count fails;
- missing/malformed/reordered/partially scored raw result fails;
- legitimate empty `capability_checks` dictionaries pass;
- dry-run receipt contains no claim that compute occurred.

Claude should report assertion count, actual dry-run output, exact package paths/hashes, and a staged-blob verification plan. The final commit review must hash staged blobs for every package file before commit.

## 12. Explicit exclusions

Until the exact package is implemented, independently reviewed, committed, and passes execution preflight, do not perform:

- training or inference;
- semantic scoring;
- seed 73;
- corpus or benchmark mutation;
- checkpoint selection or reuse;
- export;
- deployment;
- activation or production promotion.

## 13. Claude review questions

Claude should independently answer, with evidence:

1. Does fixed 720/720 isolate the corpus revision better than a natural 760/720 comparison in this repository's training stack?
2. Are the treatment and comparator paths, counts, logical fingerprints, and canonical git-blob bytes correct at `17c58bf...`?
3. Can the existing wrapper be safely adapted without weakening import-closure, raw-result, collision, and interruption checks?
4. Does the clean-worktree requirement preserve the deliberately untracked historical artifacts without introducing an allowlist hole?
5. Are all six semantic gates and the five outcome cells unambiguous and mechanically reproducible?
6. Is any proposed implementation change outside this exact static-package scope?

If Claude agrees, that agreement authorizes static implementation under the standing protocol. Any substantive disagreement pauses the package and comes to Johnny with both positions and evidence.

**Disposition:** DESIGN AUTHORED — AWAITING CLAUDE INDEPENDENT REVIEW — STATIC PACKAGE NOT YET IMPLEMENTED — COMPUTE NOT YET READY.
