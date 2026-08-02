# Phase E lineage and withdrawal — save-context binding verification

**Reviewer:** ChatGPT
**Repository:** `ThisIsJohnnyt/intent-recovery-model`
**PR:** #12
**Reviewed head:** `087c34f`
**Scope:** the final save-time semantic-validation correction
**Data boundary:** dummy data only; no real notes were used
**Alignment status:** **Not yet aligned — the three named save regressions are fixed; external-context bindings remain absent from several save paths**

## Executive decision

Commit `087c34f` correctly fixes the three minimum regressions from the final narrow verification. All five repository suites pass, and independent replay confirms:

```text
invalid_reviewer_role_save rejected LineageValidationError
nonboolean_strict_pass_save rejected LineageValidationError
altered_comparison_save rejected LineageValidationError
```

The comparison case was rerun with the new required generation/review/rubric context, confirming semantic rejection rather than a signature error.

I agree that the new rubric-free self-consistency validators materially strengthen every save path. I do not agree that the full save-time contract from the prior acceptance document is complete, because only comparison save receives and verifies its external parents. Review, adjudication, and decision saves still validate their own contents without re-establishing the generation/rubric/parent bindings that make those contents authoritative.

## Verified fixed

- Review save rejects invalid reviewer roles, malformed actors, false attestations, invalid score types, unknown labels, and inconsistent strict-pass values.
- Comparison save reloads its generation and both reviews, verifies rubric-bound review content, and recomputes alignment before writing.
- Adjudication save validates resolution mode, actor nullability, result self-consistency, and aggregate strict pass.
- Decision, status-event, and snapshot saves validate their local enums, actors, collections, and recomputed snapshot fingerprint.
- The prior canonical-path, withdrawal, lineage-status, immutability, crash-recovery, and structured-scoring tests remain green.

## Residual finding

### Blocker — save-time validators do not verify external bindings for review and descendant records

The final narrow verification explicitly required review save to validate generation/rubric bindings and descendant saves to validate immutable parent bindings. `save_comparison_artifact()` now does this correctly by requiring parent paths and rubrics. The other relevant save functions do not receive equivalent context.

Three independent dummy cases are still written successfully:

```text
review_missing_rubric_check_save accepted True
review_wrong_generation_binding_save accepted True
decision_wrong_parent_binding_save accepted True
```

The first review silently removed a capability check required by its bound rubric while remaining internally self-consistent. The second review replaced its generation fingerprint with a different fingerprint. The decision replaced its adjudication fingerprint with a different fingerprint. Each artifact's own fingerprint was recomputed, and each public save function admitted it to immutable storage.

Downstream verified use may reject these artifacts later, but the agreed invariant is stronger: an artifact that cannot prove its external bindings must not enter immutable storage.

Relevant code:

- `training/real_data_lineage.py`: `_verify_review_semantics()` and `save_review_artifact()`
- `training/real_data_lineage.py`: `_verify_adjudication_semantics()` and `save_adjudication_artifact()`
- `training/real_data_lineage.py`: `_verify_decision_semantics()` and `save_decision_record()`

## Required correction

Use the same verified external context at save time that each builder needs:

- **Review save:** require `generation_path` and `rubrics`; reload the generation; verify canonical/active status; require the review's generation, dataset, checkpoint, prompt-contract, split/milestone, record set, raw-output fingerprints, format validity, rubric fingerprints, and capability-check keys to match.
- **Adjudication save:** require comparison, both reviews, generation, and rubrics; reload and verify all parents; require references and split/milestone to match; validate reviewer-agreement results against the verified reviews and product-owner results against the bound rubrics.
- **Decision save:** require adjudication paths; reload each canonical active adjudication and require the stored reference list to match exactly before writing.
- Apply equivalent target/replacement verification to status events if they are intended to assert existence and identity of lineage artifacts at creation time; otherwise document the narrower event contract explicitly.

Minimum regression tests:

```text
save_review_artifact rejects a removed rubric-required capability check and writes no file
save_review_artifact rejects a mismatched generation reference and writes no file
save_decision_record rejects a mismatched adjudication reference and writes no file
```

## Holdout status

No disagreement: holdout remains separately fail-closed pending the approved seal mechanism.

## Alignment statement

I agree that `087c34f` fully fixes the three named self-consistency regressions and that comparison save now satisfies the external-context requirement. I disagree that complete build/save/load equivalence has been reached for review, adjudication, and decision lineage bindings.

**Final status: Not aligned for merge, pilot population, real scoring, or decision use. One external-context binding correction remains; preserve all completed validators and canonical-path work.**
