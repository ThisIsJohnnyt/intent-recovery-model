# Controlled Seed-17 Regression-Balanced Repair — Final Outcome Record

**Decision date:** 2026-08-11  
**Repository:** `intent-recovery-model`  
**Branch / commit at decision:** `main` at `c87ebfcd3b30fbd279781dd6f076050fe7c9046a` (`HEAD == origin/main`)  
**Governing design:** `training/seed17_regression_balanced_repair_execution_design_chatgpt.md`  
**Reviewed proposal:** `training/controlled_seed17_regression_balanced_repair_outcome_proposal_chatgpt.md`  
**Proposal SHA-256:** `222e185de46280ab80892e9d3d30f0b0241dad5df263afd379fdf99090da8273`  
**Final decision authority:** Johnny  
**Final outcome:** **`RBR17-C` — treatment fails one or more frozen gates and comparator fails one or more frozen gates.**

## 1. Authorization and review chain

Claude executed the real paired seed-17 regression-balanced-repair experiment after Johnny's explicit `--confirm-execute` authorization. Both arms completed all subprocesses successfully and reached exactly 720 optimizer steps. The four raw result artifacts were preserved at `C:\swrbr17`.

ChatGPT performed primary semantic scoring on copies of the four raw-result files. Claude independently reviewed every flagged judgment, the scoring-field-only preservation boundary, all aggregates, all pass and fail sets, and the full six-gate matrix. Claude reported full agreement with no correction required.

ChatGPT then created the outcome-classification proposal and proposed `RBR17-C`. Claude independently verified the proposal artifact, all eight cited raw/scored hashes, every gate input and result, validity under the `RBR17-X` criteria, the frozen matrix mapping, and the stated consequences. Claude reported full independent agreement and no discrepancy.

On 2026-08-11, Johnny explicitly stated: **“I approve RBR17-C as the final outcome.”** This supplies the final decision required by the governing design. The classification is therefore final.

No material disagreement remains among Johnny, Claude, and ChatGPT concerning the evidence, semantic scoring, gate results, matrix mapping, or governed consequences.

## 2. Accepted scored and raw artifacts

| Arm | Benchmark | Repository-relative scored path | Final scored SHA-256 | Preserved raw SHA-256 |
|---|---|---|---|---|
| Treatment | Protected-16 | `training/controlled_seed17_regression_balanced_repair_run/treatment/protected16_results.json` | `bcf20a2af9232a50eb00bd90351bbf808c9243d3c7fc9a1058f1f899dbc93418` | `dd82f8d998c7f2f7638d148a480294535c3ed45c9241655127a1ecb877f1f646` |
| Treatment | Acceptance-10 | `training/controlled_seed17_regression_balanced_repair_run/treatment/acceptance10_results.json` | `f05b224ebe10fa3a0d4827bd2db9313378115594f8a88204da73fb9058029630` | `df4ac4c88833ccdaeefd1121a4c12cf7dba22ae195a944226dce1dcc05c19516` |
| Comparator | Protected-16 | `training/controlled_seed17_regression_balanced_repair_run/comparator/protected16_results.json` | `e39b3032debb414151655ad065c4b532312fd0bb02f3029147c62b6633bf7e55` | `6c697079626711116345752f870f3671f99fb85d199323a1bb60958996701ade` |
| Comparator | Acceptance-10 | `training/controlled_seed17_regression_balanced_repair_run/comparator/acceptance10_results.json` | `1d2b9f84a60892e7993fbb93c9b5941f76f471859cd1c1bf34e071ccb55ee7ad` | `4412cde563f896d79103c1c99800323fb10ec19212e4e2994e90bf49041421bd` |

The raw originals remain preserved in `C:\swrbr17`. Across all 52 arm-records, every field other than `scores`, `capability_checks`, and `failure_labels` was programmatically verified value-identical between each raw original and its scored copy.

## 3. Final six-gate results

### Treatment

| # | Gate | Requirement | Result | Status |
|---:|---|---:|---:|---|
| 1 | Protected format validity | 16/16 | 16/16 | **PASS** |
| 2 | Acceptance format validity | 10/10 | 10/10 | **PASS** |
| 3 | Acceptance count-rule conformance | 10/10 | 7/10 | **FAIL** |
| 4 | Acceptance combined strict pass | 10/10 | 6/10 | **FAIL** |
| 5 | Protected semantic strict pass | at least 12/16 | 10/16 | **FAIL** |
| 6 | Protected preservation and repair | all 13 required probes pass | missing `{06, 09, 10, 16}` | **FAIL** |

Treatment protected strict-pass set: `{01, 02, 03, 04, 05, 07, 12, 13, 14, 15}`.  
Treatment acceptance semantic-pass set: `{sdi2-01, sdi2-03, sdi2-04, sdi2-05, sdi2-06, sdi2-08, sdi2-09}`.  
Treatment acceptance count-conforming set: `{sdi2-01, sdi2-02, sdi2-03, sdi2-04, sdi2-05, sdi2-06, sdi2-09}`.  
Treatment acceptance combined-pass set: `{sdi2-01, sdi2-03, sdi2-04, sdi2-05, sdi2-06, sdi2-09}`.

### Comparator

| # | Gate | Requirement | Result | Status |
|---:|---|---:|---:|---|
| 1 | Protected format validity | 16/16 | 16/16 | **PASS** |
| 2 | Acceptance format validity | 10/10 | 10/10 | **PASS** |
| 3 | Acceptance count-rule conformance | 10/10 | 7/10 | **FAIL** |
| 4 | Acceptance combined strict pass | 10/10 | 7/10 | **FAIL** |
| 5 | Protected semantic strict pass | at least 12/16 | 10/16 | **FAIL** |
| 6 | Protected preservation and repair | all 13 required probes pass | missing `{06, 10, 16}` | **FAIL** |

Comparator protected strict-pass set: `{01, 03, 04, 05, 07, 09, 12, 13, 14, 15}`.  
Comparator acceptance semantic-pass set: `{sdi2-01, sdi2-02, sdi2-03, sdi2-04, sdi2-05, sdi2-06, sdi2-08, sdi2-09}`.  
Comparator acceptance count-conforming set: `{sdi2-01, sdi2-02, sdi2-03, sdi2-04, sdi2-05, sdi2-06, sdi2-09}`.  
Comparator acceptance combined-pass set: `{sdi2-01, sdi2-02, sdi2-03, sdi2-04, sdi2-05, sdi2-06, sdi2-09}`.

Neither arm is invalid under `RBR17-X`. Each arm is valid and independently fails four of the six frozen gates.

## 4. Final matrix application

| Arm | Gate result |
|---|---|
| Treatment | **FAIL** |
| Comparator | **FAIL** |

The frozen outcome matrix uniquely maps Fail / Fail to:

> **`RBR17-C` — candidate does not clear. Stop and diagnose verified residuals only. No seed 73.**

## 5. Governed consequences

This final classification closes the controlled seed-17 regression-balanced-repair experiment as a failed candidate. It does not authorize or permit:

- seed-73 execution;
- checkpoint selection, substitution, promotion, export, or further training;
- additional training, retry, or post-hoc experiment alteration;
- deployment or activation;
- cleanup or deletion of the preserved `C:\swrbr17` execution worktree;
- commit or push of any artifact without separate authorization.

A later diagnostic postmortem may examine only verified residual failures. Any new repair proposal, corpus mutation, evaluation change, or experiment design is a separate milestone requiring its own independent review and explicit authorization before compute.

## 6. Current artifact disposition

At the time this record is written, this final outcome record, the reviewed proposal, and the four scored result files are untracked, unstaged, and uncommitted. The repository remains on `main` at `c87ebfcd3b30fbd279781dd6f076050fe7c9046a`, equal to `origin/main`. No commit, push, cleanup, checkpoint action, or downstream compute was performed as part of final classification.

**Disposition:** `RBR17-C` FINAL — CONTROLLED SEED-17 REGRESSION-BALANCED REPAIR DOES NOT CLEAR — NO SEED 73 — DIAGNOSTICS ONLY BY SEPARATE AUTHORIZATION — COMMIT AND ALL OTHER DOWNSTREAM ACTIONS REMAIN SEPARATELY GATED.
