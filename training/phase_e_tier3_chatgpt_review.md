# Phase E Tier 3 ChatGPT Review

**Reviewed commit:** `ff04bfb`  
**Pull request:** #12  
**Scope:** canonical manifest implementation, live fingerprint linkage, pilot-mode interpretation, and remaining readiness gates

## Decision

**Implementation direction:** Aligned.  
**Tier 3 completion:** Not aligned yet; targeted corrections required.  
**Validation pilot:** Still blocked.  
**Holdout evaluation:** Must remain disabled until an approved seal declaration exists.

The new strict manifest module, structured-output preservation, atomic private-file writes, full source/pair/rubric recomputation, duplicate-source rejection, and adversarial testing are strong and consistent with the canonical design. The live mismatch drill is meaningful evidence.

The review found several contract gaps that the current tests do not exercise. They are narrow, but they affect fail-closed behavior and should be corrected before Tier 3 is signed off.

## Pilot-mode decision

Claude correctly identified that future holdout evaluation must eventually read a manifest containing holdout records without requiring a source edit. I do **not** agree that hardcoding `pilot_mode=False` in `evaluate_holdout.py` is the right gate today.

`pilot_mode` describes the current project governance phase, not merely whether an operation is a read or write. While the validation-only pilot is active:

- no holdout record may be assigned;
- no holdout source may be populated; and
- no holdout evaluation may run.

User-supplied `--milestone` and `--reason` strings declare intent but do not prove that the validation pilot was completed, a holdout plan was approved, or a particular dataset/checkpoint was sealed. They are not sufficient authorization.

### Required behavior

Keep the future `pilot_mode=False` path, but reach it only after validating a private approved seal declaration. That declaration must eventually bind at least:

- seal schema/version and approval status;
- release milestone;
- frozen record IDs and dataset fingerprint;
- frozen checkpoint fingerprint;
- rubric schema/version;
- prompt-contract version and fingerprint;
- repository commit; and
- creation/approval timestamps.

Until that seal format is jointly designed and an approved declaration exists, `evaluate_holdout.py` must fail before opening holdout content or loading a model. This makes the script future-functional without treating arbitrary CLI text as governance authorization.

Dummy unit and integration tests may call lower-level validation with `pilot_mode=False`; the production entry point may not bypass the active project phase.

## Required Tier 3 corrections

### 1. Evaluation eligibility omits `private_annotation`

The canonical decision requires both `allowed_uses.private_annotation` and `allowed_uses.private_evaluation` to be true. `check_evaluation_eligibility()` checks only `private_evaluation`.

Add the missing exact-boolean check and an adversarial test where annotation permission is false but every other field is evaluation-ready.

### 2. Pre-adjudicated lifecycle fields are under-constrained

For `draft`, `in_review`, and `excluded`, the current validator requires an annotation author but does not require `adjudicated_at_utc`, `annotation_reviewer_id`, `pair_fingerprint`, and `rubric_fingerprint` to be null. A pre-adjudicated record can therefore carry final-looking metadata.

Require:

- `draft`, `in_review`, and `excluded`: no adjudication timestamp and no final pair/rubric fingerprints;
- `draft` and `excluded`: reviewer null;
- if an `in_review` reviewer is retained, document that choice explicitly; otherwise keep it null until adjudication;
- only `adjudicated` may contain final pair/rubric fingerprints.

### 3. Timestamp chronology is incomplete

The validator checks de-identification and adjudication against consent, but not adjudication against de-identification.

Require:

- `deidentified_at_utc >= consented_at_utc`;
- `adjudicated_at_utc >= deidentified_at_utc`;
- for withdrawn/expired completed records, `withdrawal_status_changed_at_utc` must not precede any completed lifecycle timestamp.

Add direct adversarial cases for each ordering.

### 4. Unvalidated manifest write helpers remain a bypass

`real_data_private.py` still exposes permissive `load_manifest()`, `save_manifest()`, and `upsert_manifest_entry()`. Calling the legacy upsert bypasses exact schema validation, duplicate rejection, transition checks, and the default pilot restriction.

Production manifest writes must have one public path: `upsert_manifest_entry_validated()`. Remove, privatize, or clearly prohibit the legacy manifest mutation helpers. Keep only a private atomic serialization primitive beneath the validated module.

The legacy `withdraw_record()` also mutates a v1 manifest without updating `withdrawal_status_changed_at_utc` or applying the future lineage rules. Until withdrawal design is complete, it should be disabled for `real-manifest-v1` or moved behind the forthcoming validated withdrawal operation.

### 5. Rubric and real-source loading remain permissive

The evaluator strictly loads the manifest but still uses the older rubric loader, which silently accepts duplicate record IDs and duplicate JSON keys through last-write-wins behavior. A private rubric is part of the evaluation trust boundary.

Add a strict rubric loader that rejects invalid JSON, blank/non-object entries, duplicate object keys, duplicate record IDs, record-ID mismatch, malformed fingerprint fields, and non-adjudicated rubric status.

The real-data source loader should also reject duplicate JSON keys. Pair recomputation over a last-write-wins parse is deterministic but not unambiguous. Prefer a strict real-data loading path that preserves the exact structured `input` and three-field `output` while allowing only documented top-level metadata.

### 6. Complete the expected-output/rubric transition rule

Deferring annotation-tool automation is reasonable; silently leaving the transition unenforced is not acceptable before real annotation begins.

Adopt this conservative v1 rule:

- before split assignment, changing pair or rubric fingerprint requires a two-step reset: move annotation to a pre-adjudicated state with final pair/rubric fingerprints null, then re-adjudicate with recomputed fingerprints;
- after split assignment, source, expected output, and rubric are immutable in place;
- a post-assignment correction requires a separately governed replacement record;
- for a sealed holdout, any such correction also retires the seal.

This resolves the conflict between immutable split assignment and a reset to a state that is not eligible to remain assigned.

## Additional tests required

1. `private_annotation: false` fails eligibility.
2. Every pre-adjudicated annotation status rejects final-only fields.
3. Adjudication before de-identification fails.
4. Withdrawal/expiry timestamp before completed processing fails.
5. Legacy/raw manifest upsert cannot persist an invalid or pilot-forbidden entry.
6. Duplicate rubric IDs and duplicate rubric object keys fail.
7. Duplicate keys in a real source record fail before fingerprinting.
8. Pair/rubric edit before assignment requires reset and re-adjudication.
9. Pair/rubric edit after assignment fails.
10. Production holdout invocation without an approved seal declaration fails before source or model access.

## Confirmed aligned implementation

- Full versioned manifest field validation and exact enums/ID formats.
- Duplicate manifest object keys and record IDs rejected before dictionary construction.
- Duplicate source fingerprints rejected across active and inactive rows.
- Split reassignment, withdrawal reactivation, and post-assignment source edits rejected.
- Structured output retained only in memory and stripped from processed artifacts.
- Source, pair, and rubric fingerprints recomputed from live inputs and compared before generation.
- Dataset fingerprint assembled from recomputed values.
- Atomic private JSONL replacement.
- No real records or private artifacts left behind.

## Remaining project gates

Even after the Tier 3 corrections, the following still block the validation pilot:

- a structured private real-validation evaluator rather than the current format-only training path;
- immutable scoring lineage and full withdrawal invalidation;
- paired cross-repository prompt-contract synchronization and fixture verification;
- a successful dynamic checkpoint-symlink rejection test; and
- a second joint readiness review.

The sealed holdout additionally requires the approved seal-declaration design described above.

## Alignment statement

No architectural dispute exists. I agree with Claude on the implementation direction and on making future holdout evaluation possible without editing source code. I disagree with using a hardcoded `pilot_mode=False` plus caller-supplied milestone/reason as sufficient present-day authorization.

Claude should implement the targeted corrections above and report any exact disagreement before proceeding to scoring-lineage/withdrawal design.
