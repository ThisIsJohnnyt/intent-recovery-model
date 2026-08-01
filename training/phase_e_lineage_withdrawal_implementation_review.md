# Phase E scoring-lineage and withdrawal implementation review

**Reviewer:** ChatGPT
**Repository:** `ThisIsJohnnyt/intent-recovery-model`
**PR:** #12
**Reviewed head:** `fa257865a8893e61cc56bf6121db9ee77dfa7778`
**Implementation commits:** `ce1d05a`, `347f06f`, `fa25786`
**Review scope:** dummy-data implementation only; no real notes were used or populated
**Status:** **Not aligned — corrections required before merge, pilot population, or decision use**

## Executive decision

The architecture is still sound and several important pieces are implemented correctly. The current implementation is not yet faithful to the accepted integrity contract, however. I reproduced failures that allow:

- a withdrawal `record_id` to escape the lock directory;
- a rubric-required capability check to disappear while the record receives `strict_pass: true`;
- invalidated reviews to create a new comparison;
- invalidated adjudications to create a new decision;
- duplicate score rows to pass an "exact record set" check; and
- self-consistent artifacts with unknown fields to pass the generic verified loader.

These are functional gaps, not style findings. They exist even though all five current test suites pass. The test suite is green because several required adversarial groups are named but not fully exercised.

No real-validation pilot data should be populated and no lineage artifact should guide a model or release decision until the blocker and high-severity findings below are corrected and independently re-reviewed.

## What is aligned

The following work is substantively correct and should be preserved:

1. Generation evidence is separated from later semantic judgment through `real-eval-generation-v1`.
2. The validation evaluator now creates a structured private generation artifact and does not print raw generated content.
3. Manifest eligibility and source/pair/rubric fingerprint linking happen before validation generation.
4. Generation and lineage saves use exclusive-create semantics.
5. The normal withdrawal path is manifest-first, writes invalidation events before deleting generation/lineage content, and preserves decisions as invalidated audit records.
6. The four implemented crash-injection points resume correctly in the current dummy tests.
7. The current five test scripts all pass at the reviewed head.
8. I agree with Claude that splitting cohesive modules or replacing `print()` solely to improve the aislop warning-count score would not address the actual risks. The warn-only complexity result is not a merge blocker by itself.

## Required findings

### 1. Blocker — withdrawal `record_id` is path-capable before it is validated

`withdraw_record_validated()` validates the actor and reason but does not validate `record_id` against the manifest contract before `_acquire_or_inspect_lock()` constructs a path. `_lock_path_for()` directly joins `f"{record_id}.json"` beneath `LOCKS_DIR`.

Reviewed locations:

- `training/real_data_withdrawal.py:69-85`
- `training/real_data_withdrawal.py:477-487`

Live reproduction:

```text
withdrawal_record_id_escape /workspace/scratch/escaped.json under_locks False
```

A malformed value such as `../../../escaped` resolves outside the lock root. An absolute value can discard the intended root entirely. The public operation writes the lock before the manifest lookup rejects the nonexistent ID.

Required correction:

- validate `record_id` against the exact `^rv_[0-9a-f]{32}$` manifest pattern before any path construction or write;
- resolve and assert the lock path remains beneath `LOCKS_DIR` as defense in depth;
- validate `requested_at_utc` before acquiring the lock; and
- add adversarial tests for `..`, separators, absolute paths, malformed-but-safe strings, and non-UTC timestamps, asserting that no file is created anywhere.

### 2. Blocker — the scoring code reads the wrong rubric capability-check field

The approved annotation guide defines the rubric field as `capability_checks`. `build_review_score_record()` instead reads optional `expected_capability_checks` and defaults the missing field to an empty set.

Reviewed locations:

- `datasets/REAL_DATA_ANNOTATION_GUIDE.md` private rubric schema
- `training/real_data_lineage.py:148-180`

The lineage tests conceal the mismatch by constructing test-only rubrics with `expected_capability_checks`, a field the real guide does not define.

Live reproduction using the documented rubric shape:

```text
rubric_capability_bypass True {}
```

A rubric containing `"capability_checks": ["explicit_task_survived"]` accepted an empty submitted check set and produced `strict_pass: true`.

Required correction:

- make one rubric field authoritative across the annotation guide, strict rubric validator, scoring builder, fixtures, and tests;
- do not default a missing required field to "no checks"; fail closed;
- validate that capability-check names are unique non-empty identifiers; and
- add a test built from the exact documented and strictly loaded rubric shape, proving a missing check cannot pass.

### 3. Blocker — status resolution exists, but descendant and decision builders do not enforce it

The accepted design requires every child to reject a missing, mismatched, wrong-kind, superseded, or invalidated parent. `resolve_active_status()` exists, but the comparison, adjudication, and decision builders never call it.

Reviewed locations:

- `training/real_data_lineage.py:295-345`
- `training/real_data_lineage.py:359-419`
- `training/real_data_lineage.py:433-452`
- `training/test_real_data_lineage.py`, groups 14 and 15

Live reproductions:

```text
invalidated_parent_comparison_accepted aligned
invalidated_adjudication_decision_accepted curriculum
```

The group-14 test verifies only that the standalone resolver returns `superseded` or `invalidated`; it does not attempt the descendant creation its title claims to block. Group 15 verifies that a decision has at least one adjudication-shaped dict, not that the adjudication is verified and active.

Required correction:

- child creation must receive verified parent artifacts or parent paths/repositories that can be verified;
- enforce exact kind, ID, fingerprint, existence, and `active` status immediately before every child save/use;
- require decisions to cite only verified active adjudications;
- make status resolution bind all three reference fields, not only `artifact_id`; and
- add tests that actually attempt comparison, adjudication, and decision creation after parent supersession/invalidation.

### 4. High — the common artifact integrity contract is largely unimplemented

The design requires every artifact to use a 32-hex kind-specific ID, reject duplicate JSON keys and unknown fields, validate IDs/fingerprints/timestamps, and be fully verified on every load. The current generic lineage loader checks only file existence, schema version, kind, and a self-fingerprint. The generation loader has the same structural gap.

Reviewed locations:

- `training/real_data_lineage.py:60-85, 105-143`
- `training/real_data_eval_logging.py:56-71, 232-248`

Live reproductions:

```text
unknown_field_accepted accepted
id_hex_lengths 12 12
```

All generated artifact IDs currently use 12 hex characters, not the designed 32. An unknown field is accepted when the caller recomputes the artifact fingerprint. Duplicate JSON keys are also accepted through ordinary `json.loads` last-key-wins behavior.

Required correction:

- implement exact per-kind schemas or equivalent explicit validators;
- use duplicate-key-rejecting JSON loading;
- reject unknown/missing fields, malformed IDs/fingerprints, non-UTC timestamps, invalid enums and non-literal booleans;
- change new artifact IDs to the agreed 32-hex form; and
- ensure builders validate before save rather than relying on trusted callers.

This must cover generation, review, comparison, adjudication, decision, status event, snapshot, withdrawal plan/completion, and withdrawal lock records.

### 5. High — set/dict normalization silently accepts duplicate records and under-validates adjudication results

`build_review_artifact()` compares sets of record IDs, so two score rows with the same ID satisfy a one-record generation. Comparison and adjudication then convert lists to dicts, silently selecting the last duplicate. Product-owner `final_scores` are checked by record-ID set and strict-pass recomputation, but their complete field shape and bindings are not validated against the generation, rubric, and parent reviews.

Reviewed locations:

- `training/real_data_lineage.py:216-222`
- `training/real_data_lineage.py:305-308`
- `training/real_data_lineage.py:375-402`

Live reproduction:

```text
duplicate_review_rows_accepted 2
```

Required correction:

- reject duplicate generation result IDs, review score IDs, comparison record IDs, adjudication result IDs, decision references, and snapshot record IDs before any set/dict construction;
- validate every review/adjudication score record against one exact schema;
- for product-owner resolution, permit changes only to the intended adjudicated fields while preserving record ID, raw-output fingerprint, rubric fingerprint, and generation-copied format validity;
- validate failure-label vocabulary and capability-check key contract again at adjudication; and
- prove aggregate strict pass is derived from an exactly validated unique result list.

### 6. High — withdrawal's strict-loading and crash/concurrency boundary is incomplete

The normal single-process path is good, but several trust-boundary operations remain permissive:

- source rows are read with plain `json.loads` during planning, removal, and residual checks rather than the existing strict source loader;
- rubrics are read/written through `real_data_private.load_rubrics()`/`save_rubrics()`, whose own documentation says they do not enforce the strict rubric contract;
- if concurrent callers race to create the same plan, the loser catches `LineageArtifactExistsError` and returns its unsaved local plan instead of loading and verifying the persisted winner;
- the completed lock is overwritten with non-atomic `write_text`, creating an untested final crash window; and
- malformed lock/plan fields are not covered by exact schemas.

Reviewed locations:

- `training/real_data_withdrawal.py:97-122`
- `training/real_data_withdrawal.py:219-282`
- `training/real_data_withdrawal.py:312-345`
- `training/real_data_private.py:239-247`

Required correction:

- reuse strict source and rubric loaders throughout withdrawal;
- after an exclusive-create collision, load and verify the persisted plan and require it to match the lock/request identity;
- make lock state transitions atomic and fingerprint/schema validated;
- test two callers racing before plan creation; and
- inject crashes during plan creation, completion creation, and lock completion, not only the four middle execution steps.

### 7. Explicitly deferred blocker — holdout seal retirement does not exist yet

The implementation honestly records `affected_seals: []` because the holdout seal schema has not been jointly designed. That transparency is good, but it means this is not yet a full holdout withdrawal implementation and adversarial group 21 is not satisfied; the test documents the stub instead of testing retirement.

This does not need to block dummy development or a later validation-only pilot once findings 1-6 and the pre-existing pilot gates are closed. It does block holdout population, holdout evaluation, and any claim that withdrawal is complete for holdout data.

## Test assessment

I ran, unchanged, at reviewed head:

```text
python test_real_data_private.py
python test_real_data_eval_logging.py
python test_real_data_manifest.py
python test_real_data_lineage.py
python test_real_data_withdrawal.py
```

All passed. I then ran targeted dummy reproductions outside the repository source tree and obtained:

```text
rubric_capability_bypass True {}
duplicate_review_rows_accepted 2
invalidated_parent_comparison_accepted aligned
invalidated_adjudication_decision_accepted curriculum
unknown_field_accepted accepted
withdrawal_record_id_escape /workspace/scratch/escaped.json under_locks False
id_hex_lengths 12 12
```

The discrepancy means the current assertion count is real, but coverage does not satisfy the acceptance wording in adversarial groups 2, 6, 14, 15, and 21.

## Recommended correction order

1. Close the withdrawal path/timestamp boundary before any other withdrawal work.
2. Reconcile the rubric capability-check schema and add an end-to-end strict-scoring fixture.
3. Build a shared strict artifact-validation layer and adopt 32-hex IDs.
4. Enforce verified active parents inside comparison, adjudication, and decision workflows.
5. Reject duplicate records/references and fully validate product-owner final scores.
6. Harden withdrawal strict loading, plan races, atomic lock completion, and remaining crash points.
7. Return for independent re-review.
8. Keep holdout sealed and empty until the separate seal/retirement design is jointly approved and implemented.

These correction tracks can be implemented in parallel if they share one frozen artifact-schema contract first. The capability-check field decision and common validator are upstream dependencies; they should not be independently guessed in separate branches.

## Alignment statement for Johnny and Claude

I agree with Claude on the architecture, the usefulness of the new structured validation path, the normal-case withdrawal ordering, and the decision not to chase cosmetic aislop warnings. I disagree with the readiness conclusion implied by "full immutable lineage" and "full withdrawal protocol": the reviewed code does not yet enforce several invariants the jointly accepted design calls mandatory.

**Final status: Not aligned on implementation readiness. No merge, pilot population, real semantic scoring, or model/release decision use from these artifacts yet. Corrections and a second joint review are required.**
