# Controlled Seed-17 Contrastive Replay — Outcome Classification Proposal

**Date:** 2026-08-11  
**Repository:** `intent-recovery-model`  
**Branch / commit:** `main` at `f60adf232255ab253ae010a90c27e6b6266c416c`  
**Governing design:** `training/seed17_contrastive_replay_design_chatgpt.md`  
**Status:** ChatGPT proposal awaiting Claude's independent review and Johnny's final decision. This document does not finalize an outcome or authorize any downstream action.

## 1. Scope and settled evidence

The paired seed-17 treatment/comparator execution and corrected semantic scoring have been independently reviewed and reconciled. The four scored artifacts remain untracked, unstaged, and uncommitted. Their accepted SHA-256 values are:

| Arm | Benchmark | Scored artifact | SHA-256 |
|---|---|---|---|
| Treatment | Protected-16 | `training/controlled_seed17_contrastive_replay_run/treatment/protected16_results.json` | `ce40e88c9dd84dd9766483fc35bd937a04b4bdbc563ffc316d5fe7f0880dd304` |
| Treatment | Acceptance-10 | `training/controlled_seed17_contrastive_replay_run/treatment/acceptance10_results.json` | `3ec3d2ea1eaeae506f4cd71220264a391700fe4ac0eb657b3f73445ccf6b4c85` |
| Comparator | Protected-16 | `training/controlled_seed17_contrastive_replay_run/comparator/protected16_results.json` | `588215e146de5b195009fed0e68920cb11d44c3bcc1e8a34f9753b9e5597cbd0` |
| Comparator | Acceptance-10 | `training/controlled_seed17_contrastive_replay_run/comparator/acceptance10_results.json` | `0578cda40f5187cb74674a6734d6437f0bf7ff5b6585faf423a46eb0e3074b67` |

The preserved raw originals in `C:\swt17` retain their authorized pre-scoring hashes. Preservation, schema, record counts, exact ID sets, structural integrity, and scoring-field boundaries were already mutually verified before this proposal.

## 2. Recalculation method

ChatGPT recomputed the gates directly from the accepted record-level JSON rather than relying on the reported aggregate summary:

- semantic strict pass requires `format_valid == true`, every required semantic dimension exactly `2`, and every capability check exactly `true`;
- acceptance count conformance requires both stored count-rule results to pass;
- acceptance combined strict pass requires both semantic strict pass and count-rule conformance;
- gate 6 uses the frozen required set `{01, 03, 04, 05, 06, 07, 09, 10, 12, 13, 14, 15, 16}`.

The repository's unchanged `report_benchmark.py --contract=v2` independently accepts all four scored files and reproduces the protected and acceptance combined-pass aggregates.

## 3. Record-level sets used by the gates

### Treatment

- Protected strict-pass set, 11/16: `{01, 02, 03, 04, 05, 06, 07, 12, 13, 14, 15}`
- Protected strict-fail set: `{08, 09, 10, 11, 16}`
- Acceptance count-conforming set, 7/10: `{sdi2-01, sdi2-02, sdi2-03, sdi2-04, sdi2-05, sdi2-06, sdi2-09}`
- Acceptance semantic strict-pass set, 5/10: `{sdi2-01, sdi2-03, sdi2-04, sdi2-05, sdi2-06}`
- Acceptance combined strict-pass set, 5/10: `{sdi2-01, sdi2-03, sdi2-04, sdi2-05, sdi2-06}`
- Gate-6 required probes missing from the protected pass set: `{09, 10, 16}`

### Comparator

- Protected strict-pass set, 11/16: `{01, 03, 04, 05, 07, 10, 12, 13, 14, 15, 16}`
- Protected strict-fail set: `{02, 06, 08, 09, 11}`
- Acceptance count-conforming set, 7/10: `{sdi2-01, sdi2-02, sdi2-03, sdi2-04, sdi2-05, sdi2-06, sdi2-09}`
- Acceptance semantic strict-pass set, 8/10: `{sdi2-01, sdi2-02, sdi2-03, sdi2-04, sdi2-05, sdi2-06, sdi2-08, sdi2-09}`
- Acceptance combined strict-pass set, 7/10: `{sdi2-01, sdi2-02, sdi2-03, sdi2-04, sdi2-05, sdi2-06, sdi2-09}`
- Gate-6 required probes missing from the protected pass set: `{06, 09}`

## 4. Six frozen gates

### Treatment

| # | Gate | Requirement | Result | Status |
|---:|---|---:|---:|---|
| 1 | Protected format validity | 16/16 | 16/16 | **PASS** |
| 2 | Acceptance format validity | 10/10 | 10/10 | **PASS** |
| 3 | Acceptance count-rule conformance | 10/10 | 7/10 | **FAIL** |
| 4 | Acceptance combined strict pass | 10/10 | 5/10 | **FAIL** |
| 5 | Protected semantic strict pass | at least 12/16 | 11/16 | **FAIL** |
| 6 | Protected preservation and repair | all 13 required probes pass | missing `{09, 10, 16}` | **FAIL** |

Treatment gate result: **fails one or more gates** (passes 2/6; fails 4/6).

### Comparator

| # | Gate | Requirement | Result | Status |
|---:|---|---:|---:|---|
| 1 | Protected format validity | 16/16 | 16/16 | **PASS** |
| 2 | Acceptance format validity | 10/10 | 10/10 | **PASS** |
| 3 | Acceptance count-rule conformance | 10/10 | 7/10 | **FAIL** |
| 4 | Acceptance combined strict pass | 10/10 | 7/10 | **FAIL** |
| 5 | Protected semantic strict pass | at least 12/16 | 11/16 | **FAIL** |
| 6 | Protected preservation and repair | all 13 required probes pass | missing `{06, 09}` | **FAIL** |

Comparator gate result: **fails one or more gates** (passes 2/6; fails 4/6).

## 5. Proposed outcome classification

The frozen matrix defines `C17-C` when the treatment fails one or more gates and the comparator also fails one or more gates. The independently recomputed gate results are Fail / Fail.

**ChatGPT proposal: `C17-C` — candidate does not clear.**

If independently verified and approved by Johnny, the governing consequence is: stop; diagnose only verified residuals; no seed 73. It does not authorize checkpoint selection or promotion, additional training or retry, export, deployment, activation, cleanup, commit, or push.

## 6. Requested independent review

Claude should independently verify, without treating this proposal as authoritative:

1. the four scored-file identities and hashes;
2. the semantic, count-conforming, and combined-pass sets for both arms;
3. every gate numerator, threshold, and PASS/FAIL result;
4. the gate-6 required set and each arm's missing identities;
5. that neither arm is invalid under `C17-X` criteria;
6. that Fail / Fail maps uniquely to `C17-C` under the frozen matrix; and
7. that the stated consequences do not exceed the governing design.

Any material disagreement pauses classification and returns to Johnny with both positions and evidence. Agreement would make the proposal ready for Johnny's explicit final classification decision; it would not itself finalize the outcome or authorize a commit.

**Disposition:** SIX-GATE PACKET PREPARED — `C17-C` PROPOSED — AWAITING CLAUDE INDEPENDENT REVIEW — FINAL CLASSIFICATION AND ALL DOWNSTREAM ACTIONS PAUSED.
