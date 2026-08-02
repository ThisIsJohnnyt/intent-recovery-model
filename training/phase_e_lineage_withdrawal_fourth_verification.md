# Phase E lineage and withdrawal — narrow fourth verification

**Reviewer:** ChatGPT  
**Repository:** `ThisIsJohnnyt/intent-recovery-model`  
**PR:** #12  
**Reviewed head:** `5900c19545708670000df00e9ce49ad4b13c2ebe`  
**Scope:** the four acceptance boundaries from the focused third review  
**Data boundary:** dummy data only; no real notes were used  
**Alignment status:** **Not yet aligned — all four exact reproductions are fixed, but four broader acceptance conditions remain incomplete**

## Executive decision

Commit `5900c19` is another substantial and correct hardening pass. I independently confirmed that each exact third-review failure case now rejects:

```text
original_outside_parent rejected LineageValidationError
original_path_shaped_id rejected LineageValidationError
original_required_check_removed rejected LineageValidationError
original_absolute_withdrawal_path rejected WithdrawalValidationError
```

All five repository suites also pass. I agree with Claude that those concrete defects are fixed.

I do not agree that the four underlying acceptance boundaries are fully closed. Five adjacent dummy cases still pass:

```text
cross_split_parent accepted aligned
invalid_timestamp_save accepted True
nonboolean_stored_strict_pass accepted aligned
altered_comparison_alignment accepted disagreement reviewer_agreement
noncanonical_withdrawal_path accepted real_validation/different_generation.json
```

These are not a new architecture direction. They are the remaining portions of the same canonical-path, save-time-validation, recursive-scoring, and withdrawal-target requirements stated in the third review.

## Verification completed

The following suites pass at `5900c19`:

```text
python training/test_real_data_private.py
python training/test_real_data_eval_logging.py
python training/test_real_data_manifest.py
python training/test_real_data_lineage.py
python training/test_real_data_withdrawal.py
```

Verified improvements:

- a parent outside the approved results tree is rejected;
- a parent copied to a noncanonical location within the same validation tree is rejected;
- path-shaped artifact IDs fail before any save;
- fingerprints are recomputed before generation and lineage saves;
- a stored review missing a rubric-required capability check is rejected;
- absolute, parent-traversing, and backslash-ambiguous withdrawal paths are rejected; and
- affected generation and lineage entries now have exact field sets and kind-specific ID checks.

## Residual findings

### 1. Blocker — canonical parent binding still derives split and milestone from the supplied path

For review/comparison/adjudication parents, `_infer_split_and_milestone_from_path()` treats the physical location as the source of truth for split and milestone. `load_and_require_active_parent()` then reconstructs a canonical path using those inferred values.

That proves the file is canonical *for the directory where it was placed*, but not that the directory matches the verified generation parent. A validation review copied to the equivalent canonical review path under a holdout milestone is accepted when compared against its original validation generation:

```text
cross_split_parent accepted aligned
```

Relevant code:

- `training/real_data_lineage.py:1004-1027`
- `training/real_data_lineage.py:1030-1071`
- `training/real_data_lineage.py:615-662`

Required correction:

- bind review/comparison/adjudication physical split and milestone to the verified generation artifact/path, not to the child path alone;
- either store immutable split/milestone bindings in every lineage artifact or pass a verified generation-location context into canonical parent loading;
- require the child's resolved root, evaluation directory, split, and milestone to match that verified context; and
- add cross-split and cross-milestone copy tests, not only outside-root and same-split noncanonical-copy tests.

### 2. Blocker — save-time validation is still structural rather than full per-kind validation

`_validate_before_save()` calls `_assert_exact_fields()`, verifies the self-fingerprint, and checks path containment. `_assert_exact_fields()` validates top-level fields, the artifact ID, and registered reference shapes; it does not run the complete load-time/per-kind semantic validator.

A review with a valid ID and fingerprint but malformed `created_at_utc` was saved successfully:

```text
invalid_timestamp_save accepted True
```

The loader would later reject this file, leaving an immutable artifact that the save path itself should never have created.

Relevant code:

- `training/real_data_lineage.py:238-255`
- `training/real_data_lineage.py:307-365`
- `training/real_data_lineage.py:609-612`

Required correction:

- create one complete per-kind validator used identically by build, save, and load;
- include timestamps, enums, literal booleans, nested structures, cross-field invariants, aggregates, identifiers, fingerprints, and canonical references;
- perform full validation before directory creation; and
- test a self-consistent malformed timestamp and at least one invalid enum at save time for every artifact family.

### 3. Blocker — recursive score/comparison semantics are not fully re-derived

The new stored-score validator correctly restores rubric capability-check keys and recomputes strict pass. Two gaps remain.

First, it does not require stored `strict_pass` to be a literal boolean. Python considers `True == 1`, so a stored integer `1` matches a recomputed `True`:

```text
nonboolean_stored_strict_pass accepted aligned
```

Second, comparison artifacts still lack a recursive semantic validator. `alignment_status` and `record_comparisons` are trusted if the top-level field set and self-fingerprint are consistent. A genuine reviewer disagreement was changed to `alignment_status: aligned` with an empty comparison list, saved, and accepted for reviewer-agreement adjudication:

```text
altered_comparison_alignment accepted disagreement reviewer_agreement
```

The first status is the comparison computed from the real reviews; the final mode is what the altered stored comparison was allowed to authorize.

Relevant code:

- `training/real_data_lineage.py:495-544`
- `training/real_data_lineage.py:665-734`
- `training/real_data_lineage.py:747-864`

Required correction:

- require `strict_pass` to satisfy `isinstance(value, bool)` before comparison with the recomputed result;
- validate every comparison-result entry's exact schema and value types;
- recompute comparison disagreements and `alignment_status` from both verified reviews on build, save, and downstream load;
- validate adjudication result records and aggregate strict-pass consistency by the same rule; and
- add regressions for integer booleans and a self-consistent altered comparison that attempts reviewer-agreement resolution.

### 4. Blocker — withdrawal paths are contained but not bound to the referenced artifact

`_validate_relative_path()` now blocks absolute paths and root escape. It only proves containment. It does not require `relative_path` to equal the canonical path implied by the entry's artifact kind, artifact ID, split, milestone, and discovered lineage relationship.

A plan's affected generation was redirected to a different path inside the private-results root and passed `_load_plan_verified()`:

```text
noncanonical_withdrawal_path accepted real_validation/different_generation.json
```

The path would later be trusted by deletion and residual-check code. In addition, `intended_actions` remains unvalidated even though it is part of the plan's declared schema.

Relevant code:

- `training/real_data_withdrawal.py:79-157`
- `training/real_data_withdrawal.py:484-487`
- deletion and residual-check consumers of `relative_path`

Required correction:

- reconstruct the exact canonical path for every affected entry and require equality with its normalized `relative_path`;
- for lineage entries, bind the path to the referenced generation/evaluation directory and artifact-kind subdirectory;
- reject noncanonical spellings such as redundant separators or `.` segments before `PurePosixPath` normalization hides them;
- validate `intended_actions` as an exact, versioned value; and
- add in-root wrong-target tests for generation and each lineage kind, proving rejection before any mutation begins.

## Holdout status

No disagreement: the holdout seal remains deferred and fail-closed. No holdout population or evaluation should occur until the seal design is approved and implemented.

## Recommended final correction pass

1. Introduce a verified evaluation-location context binding split, milestone, evaluation ID, and generation path.
2. Replace structural save checks with the complete per-kind validators used by load.
3. Add recursive comparison/adjudication validators and literal-boolean enforcement.
4. Bind every withdrawal `relative_path` to a canonical discovered artifact path and validate the action list.
5. Add the five accepted cases above to the permanent regression suites.
6. Return for a final verification restricted to those five cases and the existing suite.

## Alignment statement

I agree that commit `5900c19` fixes all four exact third-review reproductions and materially improves the implementation. I disagree with the broader claim that all four findings are completely resolved, because their stated acceptance conditions remain reproducibly incomplete.

**Final status: Not aligned for merge, pilot population, real scoring, or decision use. Preserve the completed fixes; close the four residual conditions above; then perform one final narrow verification.**
