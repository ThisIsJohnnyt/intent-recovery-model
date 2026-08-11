# Controlled Seed-17 Contrastive Replay — Final Outcome Record

**Decision date:** 2026-08-11  
**Repository:** `intent-recovery-model`  
**Branch / commit at decision:** `main` at `f60adf232255ab253ae010a90c27e6b6266c416c` (`HEAD == origin/main`)  
**Governing design:** `training/seed17_contrastive_replay_design_chatgpt.md`  
**Reviewed proposal:** `training/controlled_seed17_contrastive_replay_outcome_proposal_chatgpt.md`  
**Proposal SHA-256:** `affe28c96c259c1bece62e62d358287027331f84f3d2c313ef113edd06d96078`  
**Final decision authority:** Johnny  
**Final outcome:** **`C17-C` — treatment fails one or more frozen gates and comparator fails one or more frozen gates.**

## 1. Authorization and review chain

Claude performed primary semantic scoring on copies of the four raw-result files. ChatGPT independently audited preservation, structure, and every record-level judgment. Four corrections were resolved by genuine independent agreement and applied by Claude. ChatGPT then recomputed the six frozen gates and proposed `C17-C`. Claude independently recomputed the gates from scratch, confirmed every number and identity set, and agreed that Fail / Fail maps uniquely to `C17-C` under the frozen matrix.

On 2026-08-11, after reviewing the meaning and consequences of approving a failure classification, Johnny explicitly stated: **“In this case, I approve.”** This supplies the final decision required by the standing protocol. The classification is therefore final.

No material disagreement remains between Johnny, Claude, and ChatGPT concerning the evidence, gate results, matrix mapping, or governed consequences.

## 2. Accepted scored artifacts

| Arm | Benchmark | Repository-relative path | Final scored SHA-256 |
|---|---|---|---|
| Treatment | Protected-16 | `training/controlled_seed17_contrastive_replay_run/treatment/protected16_results.json` | `ce40e88c9dd84dd9766483fc35bd937a04b4bdbc563ffc316d5fe7f0880dd304` |
| Treatment | Acceptance-10 | `training/controlled_seed17_contrastive_replay_run/treatment/acceptance10_results.json` | `3ec3d2ea1eaeae506f4cd71220264a391700fe4ac0eb657b3f73445ccf6b4c85` |
| Comparator | Protected-16 | `training/controlled_seed17_contrastive_replay_run/comparator/protected16_results.json` | `588215e146de5b195009fed0e68920cb11d44c3bcc1e8a34f9753b9e5597cbd0` |
| Comparator | Acceptance-10 | `training/controlled_seed17_contrastive_replay_run/comparator/acceptance10_results.json` | `0578cda40f5187cb74674a6734d6437f0bf7ff5b6585faf423a46eb0e3074b67` |

The corresponding raw originals remain preserved in `C:\swt17` at their authorized pre-scoring hashes. The scored files change only authorized scoring fields. Record counts, ID sets, non-scoring fields, schema, structural data, and raw-output provenance were mutually verified before classification.

## 3. Final six-gate results

### Treatment

| # | Gate | Requirement | Result | Status |
|---:|---|---:|---:|---|
| 1 | Protected format validity | 16/16 | 16/16 | **PASS** |
| 2 | Acceptance format validity | 10/10 | 10/10 | **PASS** |
| 3 | Acceptance count-rule conformance | 10/10 | 7/10 | **FAIL** |
| 4 | Acceptance combined strict pass | 10/10 | 5/10 | **FAIL** |
| 5 | Protected semantic strict pass | at least 12/16 | 11/16 | **FAIL** |
| 6 | Protected preservation and repair | all 13 required probes pass | missing `{09, 10, 16}` | **FAIL** |

Treatment protected strict-pass set: `{01, 02, 03, 04, 05, 06, 07, 12, 13, 14, 15}`.  
Treatment acceptance combined-pass set: `{sdi2-01, sdi2-03, sdi2-04, sdi2-05, sdi2-06}`.

### Comparator

| # | Gate | Requirement | Result | Status |
|---:|---|---:|---:|---|
| 1 | Protected format validity | 16/16 | 16/16 | **PASS** |
| 2 | Acceptance format validity | 10/10 | 10/10 | **PASS** |
| 3 | Acceptance count-rule conformance | 10/10 | 7/10 | **FAIL** |
| 4 | Acceptance combined strict pass | 10/10 | 7/10 | **FAIL** |
| 5 | Protected semantic strict pass | at least 12/16 | 11/16 | **FAIL** |
| 6 | Protected preservation and repair | all 13 required probes pass | missing `{06, 09}` | **FAIL** |

Comparator protected strict-pass set: `{01, 03, 04, 05, 07, 10, 12, 13, 14, 15, 16}`.  
Comparator acceptance combined-pass set: `{sdi2-01, sdi2-02, sdi2-03, sdi2-04, sdi2-05, sdi2-06, sdi2-09}`.

Neither arm is invalid under `C17-X`. Each arm is valid and independently fails four of the six frozen gates.

## 4. Final matrix application

| Arm | Gate result |
|---|---|
| Treatment | **FAIL** |
| Comparator | **FAIL** |

The frozen outcome matrix uniquely maps Fail / Fail to:

> **`C17-C` — candidate does not clear. Stop; diagnose only verified residuals. No seed 73.**

## 5. Governed consequences

This final classification closes the controlled seed-17 contrastive replay as a failed candidate experiment. It does not authorize or permit:

- seed-73 execution;
- checkpoint selection, substitution, or promotion;
- additional training, retry, or post-hoc experiment alteration;
- export, deployment, or activation;
- cleanup or deletion of the preserved `C:\swt17` execution worktree;
- commit or push of any artifact without separate authorization.

A later diagnostic postmortem may use only verified residual failures. Any new corpus proposal, evaluation change, or experiment design is a separate static-review milestone requiring its own scope, independent review, and explicit authorization before compute.

## 6. Current artifact disposition

This outcome record, the reviewed proposal, and the four scored result files are untracked, unstaged, and uncommitted at the time this record is written. The repository remains on `main` at `f60adf232255ab253ae010a90c27e6b6266c416c`. No commit, push, cleanup, or downstream action was performed as part of classification.

**Disposition:** `C17-C` FINAL — CONTROLLED SEED-17 CONTRASTIVE REPLAY DOES NOT CLEAR — NO SEED 73 — DIAGNOSTICS ONLY BY SEPARATE AUTHORIZATION — COMMIT AND ALL OTHER DOWNSTREAM ACTIONS REMAIN SEPARATELY GATED.
