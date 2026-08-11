# Controlled Seed-17 Regression-Balanced Repair — Outcome Classification Proposal

**Date:** 2026-08-11  
**Repository:** `intent-recovery-model`  
**Branch / commit:** `main` at `c87ebfcd3b30fbd279781dd6f076050fe7c9046a` (`HEAD == origin/main`)  
**Governing design:** `training/seed17_regression_balanced_repair_execution_design_chatgpt.md`  
**Status:** ChatGPT proposal awaiting Claude's independent artifact-level review and Johnny's final decision. This document does not finalize an outcome or authorize downstream action.

## 1. Scope and settled evidence

The real paired seed-17 execution completed successfully with both arms at exactly 720 optimizer steps. ChatGPT semantically scored copies of the four raw-result artifacts, preserving the execution originals at `C:\swrbr17`. Claude then independently reviewed all scoring judgments, preservation boundaries, aggregates, pass sets, and gate inputs and reported full agreement with no corrections.

Accepted scored artifacts:

| Arm | Benchmark | Scored artifact | SHA-256 |
|---|---|---|---|
| Treatment | Protected-16 | `training/controlled_seed17_regression_balanced_repair_run/treatment/protected16_results.json` | `bcf20a2af9232a50eb00bd90351bbf808c9243d3c7fc9a1058f1f899dbc93418` |
| Treatment | Acceptance-10 | `training/controlled_seed17_regression_balanced_repair_run/treatment/acceptance10_results.json` | `f05b224ebe10fa3a0d4827bd2db9313378115594f8a88204da73fb9058029630` |
| Comparator | Protected-16 | `training/controlled_seed17_regression_balanced_repair_run/comparator/protected16_results.json` | `e39b3032debb414151655ad065c4b532312fd0bb02f3029147c62b6633bf7e55` |
| Comparator | Acceptance-10 | `training/controlled_seed17_regression_balanced_repair_run/comparator/acceptance10_results.json` | `1d2b9f84a60892e7993fbb93c9b5941f76f471859cd1c1bf34e071ccb55ee7ad` |

The corresponding raw originals retain their execution-time hashes:

| Arm | Benchmark | Preserved raw SHA-256 |
|---|---|---|
| Treatment | Protected-16 | `dd82f8d998c7f2f7638d148a480294535c3ed45c9241655127a1ecb877f1f646` |
| Treatment | Acceptance-10 | `df4ac4c88833ccdaeefd1121a4c12cf7dba22ae195a944226dce1dcc05c19516` |
| Comparator | Protected-16 | `6c697079626711116345752f870f3671f99fb85d199323a1bb60958996701ade` |
| Comparator | Acceptance-10 | `4412cde563f896d79103c1c99800323fb10ec19212e4e2994e90bf49041421bd` |

Across all 52 arm-records, every field other than `scores`, `capability_checks`, and `failure_labels` was programmatically verified value-identical between each raw original and its scored copy.

## 2. Gate calculation method

The six frozen gates are applied separately to each arm exactly as defined by the governing design:

- semantic strict pass requires `format_valid == true`, every applicable/non-null semantic score exactly `2`, and every capability check exactly `true`;
- acceptance count conformance requires both the bullet-count and action-count results to pass;
- acceptance combined strict pass requires both semantic strict pass and count conformance;
- gate 6 requires every identity in `{01, 03, 04, 05, 06, 07, 09, 10, 12, 13, 14, 15, 16}` to pass.

The repository's unmodified `report_benchmark.py` reproduced all aggregates. Claude independently recomputed the sets and gates from the actual scored JSON and reported exact agreement.

## 3. Record-level sets used by the gates

### Treatment

- Protected strict-pass set, 10/16: `{01, 02, 03, 04, 05, 07, 12, 13, 14, 15}`
- Protected strict-fail set: `{06, 08, 09, 10, 11, 16}`
- Acceptance semantic strict-pass set, 7/10: `{sdi2-01, sdi2-03, sdi2-04, sdi2-05, sdi2-06, sdi2-08, sdi2-09}`
- Acceptance count-conforming set, 7/10: `{sdi2-01, sdi2-02, sdi2-03, sdi2-04, sdi2-05, sdi2-06, sdi2-09}`
- Acceptance combined strict-pass set, 6/10: `{sdi2-01, sdi2-03, sdi2-04, sdi2-05, sdi2-06, sdi2-09}`
- Gate-6 required probes missing from the protected pass set: `{06, 09, 10, 16}`

### Comparator

- Protected strict-pass set, 10/16: `{01, 03, 04, 05, 07, 09, 12, 13, 14, 15}`
- Protected strict-fail set: `{02, 06, 08, 10, 11, 16}`
- Acceptance semantic strict-pass set, 8/10: `{sdi2-01, sdi2-02, sdi2-03, sdi2-04, sdi2-05, sdi2-06, sdi2-08, sdi2-09}`
- Acceptance count-conforming set, 7/10: `{sdi2-01, sdi2-02, sdi2-03, sdi2-04, sdi2-05, sdi2-06, sdi2-09}`
- Acceptance combined strict-pass set, 7/10: `{sdi2-01, sdi2-02, sdi2-03, sdi2-04, sdi2-05, sdi2-06, sdi2-09}`
- Gate-6 required probes missing from the protected pass set: `{06, 10, 16}`

## 4. Six frozen gates

### Treatment

| # | Gate | Requirement | Result | Status |
|---:|---|---:|---:|---|
| 1 | Protected format validity | 16/16 | 16/16 | **PASS** |
| 2 | Acceptance format validity | 10/10 | 10/10 | **PASS** |
| 3 | Acceptance count-rule conformance | 10/10 | 7/10 | **FAIL** |
| 4 | Acceptance combined strict pass | 10/10 | 6/10 | **FAIL** |
| 5 | Protected semantic strict pass | at least 12/16 | 10/16 | **FAIL** |
| 6 | Protected preservation and repair | all 13 required probes pass | missing `{06, 09, 10, 16}` | **FAIL** |

Treatment gate result: **fails one or more gates** (passes 2/6; fails 4/6).

### Comparator

| # | Gate | Requirement | Result | Status |
|---:|---|---:|---:|---|
| 1 | Protected format validity | 16/16 | 16/16 | **PASS** |
| 2 | Acceptance format validity | 10/10 | 10/10 | **PASS** |
| 3 | Acceptance count-rule conformance | 10/10 | 7/10 | **FAIL** |
| 4 | Acceptance combined strict pass | 10/10 | 7/10 | **FAIL** |
| 5 | Protected semantic strict pass | at least 12/16 | 10/16 | **FAIL** |
| 6 | Protected preservation and repair | all 13 required probes pass | missing `{06, 10, 16}` | **FAIL** |

Comparator gate result: **fails one or more gates** (passes 2/6; fails 4/6).

Both arms are valid under the `RBR17-X` criteria. Each independently fails gates 3–6.

## 5. Proposed outcome classification

The frozen matrix maps a treatment that fails one or more gates and a comparator that fails one or more gates uniquely to:

> **`RBR17-C` — candidate does not clear. Stop and diagnose verified residuals only. No seed 73.**

**ChatGPT proposal: `RBR17-C`.**

This proposal does not authorize checkpoint selection or promotion, additional training or retry, seed 73, export, deployment, activation, cleanup of `C:\swrbr17`, commit, or push.

## 6. Requested independent artifact-level review

Claude should independently verify this proposal document as an artifact, without reopening the already settled semantic scoring unless the document itself exposes a concrete inconsistency:

1. confirm this proposal's SHA-256 and repository disposition;
2. confirm all scored and raw hashes match the accepted evidence;
3. confirm every semantic, count-conforming, and combined-pass set;
4. confirm every gate numerator, threshold, and PASS/FAIL result;
5. confirm the gate-6 required set and each arm's missing identities;
6. confirm neither arm is invalid under `RBR17-X`;
7. confirm Fail / Fail maps uniquely to `RBR17-C`; and
8. confirm the stated consequences do not exceed the governing design.

Any material disagreement pauses classification and returns to Johnny with both positions and evidence. Full agreement would make this proposal ready for Johnny's explicit final classification decision; agreement alone would not finalize the outcome or authorize a commit.

**Disposition:** SIX-GATE OUTCOME PROPOSAL PREPARED — `RBR17-C` PROPOSED — AWAITING CLAUDE INDEPENDENT ARTIFACT-LEVEL REVIEW — FINAL CLASSIFICATION AND ALL DOWNSTREAM ACTIONS PAUSED.
