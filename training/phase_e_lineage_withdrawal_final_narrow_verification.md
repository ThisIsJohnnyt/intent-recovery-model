# Phase E lineage and withdrawal — final narrow verification

**Reviewer:** ChatGPT
**Repository:** `ThisIsJohnnyt/intent-recovery-model`
**PR:** #12
**Reviewed head:** `2ab864737a60fb274b4ce1388dffda442eb67f97`
**Scope:** the five accepted cases and four residual conditions from the fourth verification
**Data boundary:** dummy data only; no real notes were used
**Alignment status:** **Not yet aligned — all five named cases are fixed; one save-time integrity condition remains**

## Executive decision

Commit `2ab8647` correctly closes all five cases from the fourth verification. I ran the independently authored reproduction script unchanged against the new commit, and every case now rejects for the intended reason:

```text
cross_split_parent rejected LineageValidationError
invalid_timestamp_save rejected LineageValidationError
nonboolean_stored_strict_pass rejected LineageValidationError
altered_comparison_alignment rejected LineageValidationError
noncanonical_withdrawal_path rejected WithdrawalValidationError
```

All five repository suites pass. I am aligned on split/milestone binding, downstream stored-score/comparison re-verification, and canonical withdrawal paths.

One narrowly scoped disagreement remains. The new `_assert_full_integrity()` is described as the complete per-kind structural/semantic validator shared by build, save, and load, but it currently checks only:

- exact top-level/reference field shapes and artifact ID format;
- `created_at_utc`; and
- split/milestone for review, comparison, and adjudication.

It does not invoke the per-kind semantic checks performed by builders or downstream verified loaders. As a result, semantically invalid immutable artifacts can still be written and only rejected later when consumed.

## Verification completed

The following suites pass at `2ab8647`:

```text
python training/test_real_data_private.py
python training/test_real_data_eval_logging.py
python training/test_real_data_manifest.py
python training/test_real_data_lineage.py
python training/test_real_data_withdrawal.py
```

Verified fully closed:

1. **Split/milestone binding:** lineage artifacts carry immutable, fingerprint-bound split/milestone fields; cross-split copies fail canonical-path verification.
2. **Named timestamp case:** malformed `created_at_utc` is rejected before a save.
3. **Downstream score/comparison verification:** stored integer `strict_pass` and altered comparison alignment are rejected before comparison/adjudication use.
4. **Withdrawal paths:** affected entries are bound to exact canonical paths, and `intended_actions` is fixed and versioned.

## Residual finding

### Blocker — save-time validation does not yet run complete per-kind semantic validation

`_validate_before_save()` calls `_assert_full_integrity()`. Despite its name and docstring, `_assert_full_integrity()` does not validate review roles, reviewer attestations, actor IDs, score-record semantics, comparison derivation, adjudication aggregates, decision enums, status-event enums, or other kind-specific invariants.

Three independent dummy checks demonstrate the gap:

```text
invalid_reviewer_role_save accepted True
nonboolean_strict_pass_save accepted True
altered_comparison_save accepted True
```

The first review carried an invalid `reviewer_role`. The second review carried integer `strict_pass: 1`. The third comparison changed a genuine disagreement to `aligned` and emptied `record_comparisons`. In every case, the artifact's self-fingerprint was recomputed and the public save function wrote the invalid immutable artifact successfully.

The downstream loaders now reject the latter two when used, which protects model/release decisions. The remaining problem is the immutable-storage contract: an artifact that cannot pass verified use should not be admitted to immutable storage in the first place. This was an explicit fourth-review acceptance condition: complete per-kind validation must be used identically by build, save, and load, including invalid enums and recursive semantics.

Relevant code:

- `training/real_data_lineage.py:245-266`
- `training/real_data_lineage.py:346-412`
- `training/real_data_lineage.py:601-668`
- `training/real_data_lineage.py:722-835`

## Required final correction

Use artifact-kind-specific validators behind a single save dispatcher rather than treating `_assert_full_integrity()` as complete by itself:

- **Review save:** validate reviewer role, actor ID, literal attestation, exact score records, literal booleans, failure labels, strict-pass recomputation, and generation/rubric bindings. This likely requires verified generation and rubric context at save time.
- **Comparison save:** load/verify both reviews and generation, recompute `record_comparisons` and `alignment_status`, and require exact equality before writing.
- **Adjudication save:** validate resolution mode, actors, result records, strict-pass recomputation, aggregate consistency, and immutable parent bindings.
- **Decision/status/snapshot save:** re-run the same enums, actors, nonempty collections, nested record schemas, aggregates, and cross-field rules enforced by their builders/loaders.
- Keep the existing shared field/timestamp/split/path/fingerprint checks as the structural layer under those validators.

Minimum regression additions:

```text
save_review_artifact rejects an otherwise self-consistent invalid reviewer_role
save_review_artifact rejects an otherwise self-consistent strict_pass=1
save_comparison_artifact rejects altered alignment_status/record_comparisons before writing
```

The tests should also assert that no destination file exists after each rejection.

## Holdout status

No disagreement: holdout remains separately fail-closed pending the jointly designed seal mechanism.

## Alignment statement

I agree that commit `2ab8647` fixes every named live case from the fourth verification and fully closes split/milestone binding, downstream comparison/score verification, and canonical withdrawal targeting. I disagree only with the claim that save-time validation is now complete and used identically across build/save/load.

**Final status: Not aligned for merge, pilot population, real scoring, or decision use. One narrowly scoped save-time validation correction remains; preserve all other completed work.**
