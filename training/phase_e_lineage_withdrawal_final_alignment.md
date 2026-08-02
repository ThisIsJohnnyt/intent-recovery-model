# Phase E Lineage and Withdrawal — Final Alignment Review

**Reviewer:** ChatGPT
**Repository:** `ThisIsJohnnyt/intent-recovery-model`
**PR:** #12
**Reviewed head:** `509d4c8c2f40703711f8d7c702e758f39c4c2e17`
**Scope:** external-context binding corrections after the save-context verification
**Data boundary:** dummy data only; no real notes were used

## Decision

**Aligned.** The three previously open external-context binding gaps are closed at the reviewed head. I found no technical disagreement to relay to Claude or Johnny.

This closes the Phase E lineage and withdrawal implementation review. It does not approve collecting real notes or opening the holdout: the separately deferred holdout-seal mechanism remains fail-closed and must still be jointly designed and approved before holdout use.

## Verification performed

### Repository suites

All five suites passed from a clean checkout of the reviewed commit:

- `training/test_real_data_private.py`
- `training/test_real_data_eval_logging.py`
- `training/test_real_data_manifest.py`
- `training/test_real_data_lineage.py`
- `training/test_real_data_withdrawal.py`

### Independent reproductions

I replayed the three cases that were accepted at the previous reviewed head. The reproduction harness was updated only to supply the newly required verified-parent arguments, so each case reached the intended semantic check.

| Case | Result at `509d4c8` | Rejection basis |
| --- | --- | --- |
| Review missing a rubric-required capability check | Rejected | Stored capability checks did not exactly match the bound rubric |
| Review claiming the wrong generation fingerprint | Rejected | Claimed generation reference did not match the verified stored generation |
| Decision claiming the wrong adjudication fingerprint | Rejected | Stored adjudication-reference list did not match the verified adjudication paths |

The repository regression tests also assert that these rejected saves write no artifact.

## Code-path findings

1. `save_review_artifact` now reloads the stored generation, requires it to be active, and invokes `_verify_review_bindings` before writing. The same binding helper is used by `load_review_verified`, so save and later consumption enforce one contract.
2. `save_adjudication_artifact` reloads and verifies the generation, both independent reviews, and the comparison, then invokes `_verify_adjudication_bindings`. Reviewer-agreement results must reproduce the verified reviewer result; product-owner resolutions may change judgment fields only, not immutable bindings.
3. `save_decision_record` reloads every supplied adjudication path, requires active verified parents, reconstructs the expected references, and requires exact ordered equality before writing.
4. Status events deliberately retain a narrower contract: they are immutable claims matched by artifact kind, ID, and fingerprint and interpreted only through `resolve_active_status`. This exception is now explicit and is internally consistent with the event-sourced status model. I accept it for this phase.

## Non-blocking observation

The previously committed `training/phase_e_lineage_withdrawal_context_binding_verification.md` has trailing spaces on six metadata lines. This is cosmetic and has no effect on the implementation or alignment decision; it can be cleaned during ordinary documentation maintenance.

## Remaining gates outside this review

- The holdout seal schema and seal-retirement behavior remain deferred and fail-closed.
- The cross-repository prompt-contract synchronization and fixed-fixture acceptance check remain required before the real-validation pilot.
- Production checkpoint-520 artifact recovery and backup remain an operational follow-up separate from PR #12.
- Real-note collection remains blocked until every governance prerequisite approved in PDR-005 is operational.

