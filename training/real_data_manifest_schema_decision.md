# Canonical Real-Data Manifest Schema Decision

**Schema version:** `real-manifest-v1`  
**Status:** ChatGPT architecture decision for Claude Code verification  
**Input reviewed:** `training/real_data_manifest_schema_proposal.md`  
**Implementation target:** PR #12 after Tier 1 hardening commit `73dc87c`

## Decision

The central reconciliation in the proposal is accepted with amendments: consent and provenance are not separate records. One private manifest entry accumulates consent, de-identification, annotation, split assignment, fingerprints, and withdrawal state over its lifecycle.

The canonical representation:

- keeps every permission boolean inside `allowed_uses`;
- adds authorship confirmation and consent-review provenance;
- removes the ambiguous generic `status` field;
- adds an explicit manifest schema version;
- represents unfinished lifecycle fields as explicit `null`, not arbitrary omissions;
- records independent de-identification and annotation actors;
- rejects a duplicate source fingerprint across the entire manifest, including withdrawn and expired rows; and
- uses strict non-coercing validation and one-way state transitions.

The proposal suggestion to enforce source-fingerprint uniqueness only among active rows is not adopted. Withdrawal must not be bypassed by reintroducing the same source under a new ID. Any future re-consent path requires a separate governance decision.

## Canonical evaluation-ready entry

Every JSONL object has exactly these top-level fields. Unknown fields are rejected under `real-manifest-v1`; additions require a schema-version change.

```json
{
  "manifest_schema_version": "real-manifest-v1",
  "record_id": "rv_0123456789abcdef0123456789abcdef",
  "contributor_id": "contributor_0123456789abcdef0123456789abcdef",
  "consent_version": "real-consent-v1",
  "consented_at_utc": "2026-08-01T17:00:00Z",
  "author_confirmed": true,
  "consent_reviewer_id": "actor_0123456789abcdef0123456789abcdef",
  "allowed_uses": {
    "private_annotation": true,
    "private_evaluation": true,
    "holdout_eligible": false,
    "training": false,
    "publication": false
  },
  "source_kind": "author_supplied_personal_note",
  "split": "real_validation",
  "source_fingerprint": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "pair_fingerprint": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "rubric_fingerprint": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "deidentification_status": "approved",
  "deidentified_at_utc": "2026-08-01T17:10:00Z",
  "deidentified_by_id": "actor_11111111111111111111111111111111",
  "deidentification_reviewer_id": "actor_22222222222222222222222222222222",
  "annotation_status": "adjudicated",
  "adjudicated_at_utc": "2026-08-01T17:30:00Z",
  "annotation_author_id": "actor_33333333333333333333333333333333",
  "annotation_reviewer_id": "actor_44444444444444444444444444444444",
  "withdrawal_status": "active",
  "withdrawal_status_changed_at_utc": "2026-08-01T17:00:00Z"
}
```

At consent time, later-stage fields remain present but are explicitly `null`.

## Field contract

| Field | Type or values | Rule |
|---|---|---|
| `manifest_schema_version` | exact `real-manifest-v1` | Required on every row. |
| `record_id` | `^rv_[0-9a-f]{32}$` | Random, stable, non-semantic, unique across all rows. |
| `contributor_id` | `^contributor_[0-9a-f]{32}$` | Private stable pseudonym; may repeat across records. |
| `consent_version` | supported enum, initially `real-consent-v1` | Arbitrary versions fail. |
| `consented_at_utc` | RFC 3339 UTC timestamp | Canonical writes use `Z`; `+00:00` may be accepted and normalized. |
| `author_confirmed` | boolean | Must be literal `true`. |
| `consent_reviewer_id` | `^actor_[0-9a-f]{32}$` | Stable pseudonymous actor ID. |
| `allowed_uses` | exact five-key object | No omitted or additional keys; values are literal booleans. |
| `source_kind` | initially `author_supplied_personal_note` | A new kind requires governance review. |
| `split` | `null`, `real_validation`, `real_holdout` | Null before assignment; immutable after assignment. |
| fingerprint fields | `null` or `^sha256:[0-9a-f]{64}$` | No prefix repair, case folding, whitespace trimming, or coercion. |
| `deidentification_status` | `pending`, `approved`, `rejected` | Evaluation requires `approved`. |
| de-identification timestamp and actors | UTC/actor IDs or `null` | All required when approved; author and reviewer must differ. |
| `annotation_status` | `not_started`, `draft`, `in_review`, `adjudicated`, `excluded` | Evaluation requires `adjudicated`. |
| adjudication timestamp and actors | UTC/actor IDs or `null` | Author required after annotation starts; independent reviewer and timestamp required when adjudicated. |
| `withdrawal_status` | `active`, `withdrawn`, `expired` | Only active records may be used; other states are terminal in v1. |
| `withdrawal_status_changed_at_utc` | UTC timestamp | Set at consent and updated on withdrawal-state change. |

Stable actor IDs must be reused consistently. Consent verification is required, but the approved text did not require the consent reviewer to be independent of the contributor. De-identification and annotation reviews are explicitly independent.

### Permission invariants

- `allowed_uses.training` and `allowed_uses.publication` are always `false`.
- Evaluation requires `private_annotation` and `private_evaluation` to be `true`.
- The validation-only pilot requires `holdout_eligible: false` and `split: real_validation`.
- A holdout assignment requires `holdout_eligible: true` before assignment.
- No permission is inferred from another permission.

## Lifecycle

### Consent recorded

- Consent, permissions, source kind, and active withdrawal fields are complete.
- `split` and all three fingerprints are `null`.
- De-identification is `pending`; its timestamp and actors are `null`.
- Annotation is `not_started`; its timestamp and actors are `null`.
- The manifest contains no note text.

### De-identified

- De-identification is `approved` with timestamp, author, and independent reviewer.
- `source_fingerprint` is recomputed and required.
- Pair and rubric fingerprints remain `null` until adjudication.

### Adjudicated

- De-identification is approved.
- Annotation is `adjudicated` with author, independent reviewer, and timestamp.
- Source, pair, and rubric fingerprints are recomputed and required.

### Evaluation-ready

- All adjudicated requirements pass.
- A split is assigned.
- Withdrawal is active.
- Permissions cover the requested operation.
- Exact source, pair, rubric, and dataset linkage checks pass.

### Withdrawn or expired

The record is permanently ineligible under v1. Existing hashes may remain in the private tombstone to prevent accidental re-ingestion and retain non-content-bearing audit linkage. Rubric and result deletion or invalidation follows the separate withdrawal-lineage decision.

## Transition rules

- `split` moves from `null` to one split at most once and never changes between validation and holdout.
- Withdrawal moves from `active` to `withdrawn` or `expired` and never returns to active.
- Before split assignment, editing de-identified source resets de-identification approval, annotation, and all fingerprints. After split assignment, an in-place source edit is rejected rather than silently changing the assigned record; a separately governed replacement record is required.
- Editing expected output or rubric resets annotation to a pre-adjudicated state and invalidates pair, rubric, and dataset fingerprints.
- Rejected or excluded records cannot become evaluation-ready without an explicit new review cycle under the same ID.
- Manifest updates are atomic. Failed validation leaves prior bytes unchanged.

## Required implementation behavior

### Strict JSONL loader

- Reject invalid JSON, blank/non-object records, and duplicate keys inside an object.
- Reject duplicate record IDs before constructing a dictionary.

### Entry and collection validation

- Require the exact versioned field set and reject coercion.
- Validate IDs, enums, timestamps, nullability, chronology, and cross-field invariants.
- Reject duplicate non-null source fingerprints across all rows, including inactive rows.
- Permit repeated contributor IDs.
- Send near-duplicates to manual review; exact hashing does not detect them.

### Operation eligibility

Accept the expected split and operation, then enforce active consent, permissions, de-identification, adjudication, split, and pilot/holdout restrictions.

### Live fingerprint verification

- Recompute source fingerprint from the exact de-identified `input`.
- Recompute pair fingerprint from exact structured `input` and `output` before prompt/target transformation.
- Recompute rubric fingerprint from the loaded rubric after omitting its own fingerprint field.
- Compare exact prefixed values with the manifest.
- Build the dataset fingerprint from recomputed values only after comparison succeeds.

Errors identify the record ID and mismatch type without quoting source or expected output.

## Required document corrections

Update `datasets/REAL_DATA_GOVERNANCE.md` and linked protocols to:

- use `allowed_uses.<name>` instead of duplicate top-level permission names;
- rename generic `reviewer` to `consent_reviewer_id`;
- add `manifest_schema_version`;
- remove generic `status`;
- add lifecycle nullability and actor fields;
- make source-fingerprint uniqueness include inactive rows; and
- record the one-way transitions.

The existing proposal remains useful design history, but this decision supersedes its example where they differ.

## Required adversarial tests

All use plainly synthetic data.

1. Every valid lifecycle state passes only its appropriate validator.
2. Missing, extra, misspelled, or duplicate JSON-object keys fail.
3. Duplicate record IDs fail before dictionary construction.
4. Duplicate source fingerprints fail for active rows and still fail when either row is withdrawn or expired.
5. Malformed, unprefixed, uppercase, or wrong-length fingerprints fail.
6. String or integer substitutes for booleans fail.
7. False authorship, unsafe permissions, or missing private-use permission fails eligibility.
8. Pending/rejected de-identification and non-independent de-identification review fail.
9. Non-adjudicated/excluded annotation and non-independent annotation review fail.
10. Invalid, non-UTC, or chronologically impossible timestamps fail.
11. Split mismatch and any attempted split reassignment fail.
12. Holdout assignment without holdout permission fails.
13. Any holdout assignment during the validation-only pilot fails.
14. Withdrawn/expired rows fail eligibility and cannot reactivate.
15. Source, pair, and rubric mismatch cases fail independently.
16. Editing only expected output changes the recomputed pair fingerprint.
17. Editing only rubric changes the recomputed rubric and dataset fingerprints.
18. Manifest line order does not alter the dataset fingerprint.
19. Invalid updates leave the prior manifest bytes unchanged.
20. Record IDs and all manifest metadata remain absent from model-facing prompts.

## Authorization boundary

This decision authorizes Claude to implement strict loading, schema validation, duplicate rejection, lifecycle and eligibility checks, and live source/pair/rubric fingerprint verification against dummy data.

It does not authorize real-note collection, prompt-contract changes, unagreed withdrawal-lineage behavior, holdout population/evaluation, or merging PR #12 as Phase E-complete before joint review.

## Alignment request

Claude should report either:

- **Aligned** -- implement this contract and return test evidence; or
- **Not aligned** -- identify the exact field, invariant, transition, or test in dispute before implementation.

No schema-dependent code should proceed under an unreported disagreement.
