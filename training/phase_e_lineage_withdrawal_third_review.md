# Phase E lineage and withdrawal — focused third implementation review

**Reviewer:** ChatGPT  
**Repository:** `ThisIsJohnnyt/intent-recovery-model`  
**PR:** #12  
**Reviewed head:** `9942b72264beff7992f4d536031c63b3bffa7b1e`  
**Scope:** corrections to the five residual findings in the second implementation review  
**Data boundary:** dummy data only; no real notes were used  
**Alignment status:** **Not yet aligned — prior corrections verified, four residual integrity gaps remain**

## Executive decision

Commit `9942b72` genuinely fixes the nine specific failure cases documented in the second review. Parent builders now take stored paths; generation status is checked before review creation; scoring rubrics are schema-validated and fingerprint-bound; top-level schemas, nested artifact references, timestamps, duplicate identities, and withdrawal request identity are materially stronger.

The focused review found four narrower gaps in the same acceptance boundaries:

1. a valid parent copied outside the approved immutable-results tree is still accepted as a stored parent;
2. lineage save functions do not revalidate the artifact or its final canonical path, so a malformed artifact ID can make a save leave the declared split tree;
3. stored review score records are not recursively validated, allowing required capability checks to disappear before comparison and reviewer-agreement adjudication; and
4. withdrawal-plan affected-artifact entries are not schema- or path-validated, including the `relative_path` later used for file deletion and residual checks.

These findings block pilot population and real semantic decision use. They do not negate the corrections already completed, and they can be addressed as a focused hardening pass without redesigning the lineage architecture.

## Verification completed

All five repository suites pass at the reviewed head:

```text
python test_real_data_private.py
python test_real_data_eval_logging.py
python test_real_data_manifest.py
python test_real_data_lineage.py
python test_real_data_withdrawal.py
```

Verified fixed from the second review:

- builders reject missing, superseded, and invalidated parents in the covered cases;
- review scoring and product-owner resolution bind rubrics to the generation fingerprint;
- generation results, review scores, decision references, and snapshot records reject duplicate IDs in the covered builders/loaders;
- top-level plan/completion schemas, nested artifact-reference shapes, and `created_at_utc` are checked;
- the plan-race recovery path compares full immutable request identity; and
- the holdout seal remains honestly deferred and fail-closed.

## Residual findings

### 1. Blocker — a stored parent is not bound to approved canonical storage

`load_and_require_active_parent()` verifies that the supplied file exists, has a valid schema/self-fingerprint, and is active. For non-generation parents it does not require the supplied path to be inside the correct private results root or equal the canonical path implied by split, milestone, generation ID, artifact kind, and artifact ID.

A valid review written outside the approved results tree was accepted by `build_comparison_artifact()`:

```text
outside_storage_parents_accepted aligned
```

Relevant code:

- `training/real_data_lineage.py:336-365`
- `training/real_data_lineage.py:572-578`
- `training/real_data_lineage.py:892-914`

Required correction:

- derive the canonical expected path for every parent kind;
- require the resolved supplied path to equal that canonical path and remain under the correct split/milestone root;
- bind the path to the artifact's own immutable identifiers; and
- test copied-outside-root, wrong-split, wrong-milestone, wrong-generation-directory, and wrong-kind-directory parents for every lineage edge.

### 2. Blocker — lineage saves do not revalidate artifact identity or path containment

The lineage save functions build a destination from fields in the caller-supplied artifact and pass it directly to `_save_artifact_exclusive()`. They do not rerun the kind validator, recompute/verify the artifact fingerprint, validate the artifact ID, or assert that the resolved final path remains inside the expected canonical root.

A review whose in-memory `review_id` was replaced with a path-leaving value and whose fingerprint was recomputed was written successfully outside the validation lineage root:

```text
save_path_left_validation_root False True
```

The first value means “resolved path is inside the validation root”; the second means “file exists.”

Relevant code:

- `training/real_data_lineage.py:230-238`
- `training/real_data_lineage.py:525-531`
- equivalent save functions for comparison, adjudication, decision, status event, and dataset snapshot

Required correction:

- centralize save-time validation per artifact kind;
- require exact schema, identifier formats, semantic invariants, and a matching recomputed fingerprint before any directory or file is created;
- validate split/milestone/evaluation IDs and the artifact-kind ID before path construction;
- assert the resolved destination equals the canonical expected path and is contained by the correct approved root; and
- apply the same rule to every lineage, status, snapshot, plan, and completion save path.

### 3. Blocker — stored review scores are not validated against their rubric contract

`build_review_score_record()` correctly validates rubric shape, fingerprint, capability-check keys, failure labels, booleans, and strict-pass computation. That contract is not re-established when a stored review is loaded as a comparison or adjudication parent.

The generic artifact loader validates the review's top-level shape and generation reference, but not each score record's exact schema or semantic contract. `build_comparison_artifact()` uses that generic loader through `load_and_require_active_parent()`, rather than `load_review_verified()` plus rubric-bound score validation. Reviewer-agreement adjudication then copies the accepted scores.

Two otherwise valid stored reviews were changed to remove a genuinely required capability check, assigned internally consistent fingerprints, and saved through the public save function. Comparison and reviewer-agreement adjudication accepted them:

```text
required_check_removed_in_saved_reviews True {}
```

The adjudicated record received `strict_pass: true` with an empty capability-check map.

Relevant code:

- `training/real_data_lineage.py:307-333`
- `training/real_data_lineage.py:534-567`
- `training/real_data_lineage.py:572-630`
- `training/real_data_lineage.py:892-914`

Required correction:

- define exact recursive validators for review score records and comparison/adjudication result records;
- on every load and save, enforce literal booleans, semantic-dimension keys/values, failure-label vocabulary, recomputed `strict_pass`, and exact per-record bindings;
- require the stored review's capability-check keys to match the fingerprint-bound rubric before comparison or adjudication;
- load review parents through a generation- and rubric-aware verified path, not only the generic top-level loader; and
- add a regression test using self-consistent stored artifacts with a required check removed.

### 4. Blocker — withdrawal affected-artifact entries and deletion paths are not validated

Withdrawal plan registration now enforces the plan's top-level field set, but no nested schema is registered for `affected_generations`, `affected_reviews`, `affected_comparisons`, `affected_adjudications`, `affected_decisions`, `affected_seals`, or `intended_actions`.

The affected entries are later trusted for status invalidation, file deletion, and residual checks. In particular, `RESULTS_PRIVATE_DIR / ref["relative_path"]` accepts an absolute `relative_path` by discarding the intended root.

A self-consistent plan containing an unknown field and an absolute `relative_path` was accepted by `_load_plan_verified()`:

```text
unvalidated_withdrawal_plan_entry_accepted accepted /outside/private/root.json
```

Relevant code:

- `training/real_data_withdrawal.py:35-75`
- `training/real_data_withdrawal.py:400-405`
- `training/real_data_withdrawal.py:474-502`
- `training/real_data_withdrawal.py:570-577`

Required correction:

- give every affected-entry kind an exact nested schema and validate it recursively on plan build, save, and load;
- reject absolute paths, `..`, empty segments, backslash ambiguity, and non-canonical relative paths;
- resolve every referenced path and assert it is under the approved private-results root and equals the canonical path implied by the entry's identifiers;
- validate kind-specific fields such as split/milestone nullability and artifact ID/fingerprint formats; and
- add tests proving malformed plan entries fail before manifest mutation, invalidation, deletion, or residual checking begins.

## Holdout status

No disagreement: holdout seal retirement is still deferred and fail-closed. Holdout population and evaluation remain blocked independently of this review.

## Recommended correction order

1. Introduce one canonical-path resolver/validator shared by parent loading, saving, and withdrawal discovery/execution.
2. Make every save validate the complete artifact and canonical destination before creating a directory or file.
3. Add recursive score/result validators and require rubric-bound review validation at every downstream edge.
4. Add exact nested withdrawal-plan schemas and fail-closed path validation.
5. Add the four focused reproductions from this review to the permanent regression suites.
6. Return for a narrow fourth verification limited to these acceptance cases.

## Alignment statement

I agree that commit `9942b72` closes the nine concrete failure cases from the second review and materially strengthens the design. I do not agree that the second review's broader stored-parent, save-time-validation, recursive-schema, and withdrawal-path acceptance conditions are fully satisfied.

**Final status: Not aligned for merge, pilot population, real scoring, or decision use. Preserve the completed fixes; close the four residual findings above; then perform one narrow joint verification.**
