# Phase E lineage and withdrawal — second implementation review

**Reviewer:** ChatGPT
**Repository:** `ThisIsJohnnyt/intent-recovery-model`
**PR:** #12
**Reviewed head:** `8d1d72d8f16eff157421229fe7d92e80b37e7b81`
**Scope:** corrections to the seven findings in the first implementation review
**Data boundary:** dummy data only; real validation and holdout files remained empty
**Alignment status:** **Not yet aligned — substantial fixes verified, residual corrections required**

## Executive decision

Commit `8d1d72d` is a meaningful hardening pass. It closes the exact first-round reproductions for path traversal, the documented rubric field name, 32-hex identifiers, top-level unknown fields, review/final-score duplicates, active-status checks on comparison/adjudication/decision, strict withdrawal reads, atomic lock completion, and the originally missing crash points.

It does not yet close the full acceptance conditions attached to those findings. New targeted dummy reproductions show that:

- an invalidated generation can still produce a new review;
- reviews that do not exist in immutable storage can produce a comparison;
- product-owner adjudication can substitute an unbound rubric, remove a genuinely required capability check, and receive `strict_pass: true`;
- nested schema violations and malformed timestamps still pass verified loaders;
- withdrawal plans/completions do not have registered exact schemas;
- duplicate IDs remain accepted in generation results, decision references, and dataset snapshots; and
- a racing withdrawal request with a different actor, reason, and timestamp silently adopts the winning plan instead of failing as a mismatched request.

Therefore, the validation-only pilot and real semantic decision use remain blocked. This is a narrower second pass than the first review: the completed fixes should remain intact, and only the residual gaps below need correction.

## Verification completed

All five repository test suites passed unchanged at the reviewed head:

```text
python test_real_data_private.py
python test_real_data_eval_logging.py
python test_real_data_manifest.py
python test_real_data_lineage.py
python test_real_data_withdrawal.py
```

The expanded tests correctly exercise 32-hex IDs, the documented `capability_checks` rubric field, path-safe withdrawal IDs, malformed request timestamps, parent status for comparison/adjudication/decision, product-owner immutable field binding, review/final-score duplicate rejection, strict rubric shape, plan convergence, atomic completion, and seven crash points.

The following first-review items are verified fixed in their tested scope:

1. `record_id` and `requested_at_utc` fail before any withdrawal path or write.
2. The real rubric field is now `capability_checks`; missing/unknown rubric fields fail strict loading.
3. Comparison, adjudication, and decision builders reject specifically superseded or invalidated parents when a matching status event exists.
4. Artifact IDs are 32-hex and duplicate JSON keys/top-level unknown fields are rejected for registered kinds.
5. Duplicate review scores and product-owner `final_scores` are rejected.
6. Withdrawal source/rubric reads, plan convergence, lock completion, and crash coverage are materially stronger.
7. Holdout seal retirement remains explicitly and honestly deferred.

## Residual findings

### 1. Blocker — parent validity is still status-only, not verified lineage

`require_parent_active()` checks status events for a caller-supplied reference. If there is no matching status event, it returns active. It does not establish that the parent:

- exists in immutable storage;
- was loaded through the strict verified loader;
- has the correct kind and complete schema; or
- is the actual stored artifact matching the supplied fingerprint.

In addition, `build_review_artifact()` does not check the generation parent's status at all.

Relevant code:

- `training/real_data_lineage.py:380-433`
- `training/real_data_lineage.py:482-542`
- `training/real_data_lineage.py:551-659`
- `training/real_data_lineage.py:673-695`
- `training/real_data_lineage.py:737-784`

Live reproductions:

```text
missing_parent_reviews_accepted disagreement
review_from_invalidated_generation_accepted review
```

The first result was built from two reviews that had never been saved. The second was built after a matching invalidation event had already invalidated the generation.

Required correction:

- include review-from-generation in the active-parent chain;
- require a verified stored parent, not merely an in-memory dict and absence of a status event;
- bind verification to expected storage path, exact kind, ID, and fingerprint;
- make every save revalidate the artifact being written; and
- test missing, wrong-kind, wrong-path, fingerprint-mismatched, superseded, and invalidated parents for every lineage edge.

### 2. Blocker — product-owner rubric input is not bound to the adjudicated record

Product-owner resolution accepts a caller-supplied `rubrics` mapping and uses only its `capability_checks` field. It does not validate the full rubric schema or prove that the supplied rubric's recomputed fingerprint equals the immutable `rubric_fingerprint` bound into the generation/reviews.

Relevant code:

- `training/real_data_lineage.py:551-631`

Live reproduction:

```text
unbound_rubric_override_accepted True {}
```

The original reviews used a rubric requiring `required_check`. Product-owner resolution was supplied an unrelated object containing `{"capability_checks": []}`. The required check disappeared and the adjudicated record received `strict_pass: true`.

Required correction:

- validate each supplied rubric through the same exact private-rubric validator;
- require the map key and rubric `record_id` to match the result record;
- recompute `rdp.rubric_fingerprint(rubric)` and require exact equality with the generation-bound fingerprint before reading capability checks; and
- add a regression test using a well-formed but wrong-fingerprint rubric, not only a changed final-score binding.

### 3. High — the artifact integrity contract remains top-level and incomplete

The registered lineage validators check the top-level field set and artifact ID. They do not validate nested reference/result structures, RFC 3339 UTC timestamps, fingerprint formats, enums, literal booleans, aggregate consistency, or other per-kind semantic types. Generation validation checks top-level and result field names, but not the nested checkpoint/dataset/prompt/aggregate shapes or most value types.

Withdrawal plan and completion are passed to the generic lineage loader with kinds that are absent from `_KIND_METADATA`; `_assert_exact_fields()` returns immediately for unknown metadata, so no exact plan/completion schema is enforced.

Relevant code:

- `training/real_data_eval_logging.py:238-301`
- `training/real_data_lineage.py:230-289`
- `training/real_data_withdrawal.py:346-351`

Live reproductions:

```text
nested_unknown_and_bad_timestamp_accepted accepted not-a-timestamp
unknown_withdrawal_plan_shape_accepted accepted
```

The first artifact had an unknown field inside `target_artifact` and a malformed timestamp, then passed `_load_artifact_verified()` after its self-fingerprint was recomputed. The second was a withdrawal plan containing only schema, kind, an unknown field, and a self-fingerprint; it passed `_load_plan_verified()`.

Required correction:

- add recursive, exact validators for every nested structure and every artifact kind;
- register withdrawal plan and completion explicitly;
- validate value types, enums, IDs, fingerprints, timestamps, cross-field nullability, aggregates, and references on both build and load;
- reject unknown nested fields; and
- add load-time adversarial tests using self-consistent recomputed fingerprints, because self-hashing alone is not schema validation.

### 4. High — duplicate identity rejection does not cover all required collections

The shared duplicate check protects review scores and product-owner final scores. It is not applied to generation results, decision adjudication references, or dataset snapshot active records. Review load also performs set/dict conversion without first rejecting duplicate score IDs.

Relevant code:

- `training/real_data_eval_logging.py:176-261`
- `training/real_data_lineage.py:445-477`
- `training/real_data_lineage.py:673-695`
- `training/real_data_lineage.py:789-818`

Live reproductions:

```text
duplicate_generation_results_accepted 2
duplicate_decision_refs_accepted 2
duplicate_snapshot_records_accepted 2
```

Required correction:

- reject duplicate generation result IDs on build and load;
- reject duplicate score/result IDs on every lineage load;
- reject duplicate adjudication references in decisions; and
- reject duplicate record IDs in snapshots before dataset fingerprinting.

### 5. High — plan-race recovery verifies operation IDs, not request identity

After an exclusive-create collision, `_build_and_save_plan()` loads the persisted winner and compares only `record_id` and `withdrawal_id`. It does not compare `requested_by_actor_id`, `reason_code`, or `requested_at_utc`, even though the first review explicitly required the persisted plan to match the lock/request identity.

Relevant code:

- `training/real_data_withdrawal.py:328-343`

Live reproduction:

```text
mismatched_plan_request_accepted True contributor_request
```

The second call used a different actor, `consent_expired` instead of `contributor_request`, and a different timestamp. It silently received the first request's plan.

Required correction:

- compare every immutable request field after loading the persisted winner;
- fail closed with an explicit “existing withdrawal differs” result when any differ; and
- extend the concurrency test to race conflicting requests, not only identical requests.

## Holdout status

No disagreement: holdout seal retirement remains deferred because the seal schema is not yet jointly designed. Holdout population and evaluation therefore remain blocked independently of the residual validation findings above.

## Recommended correction order

1. Bind product-owner rubrics and close review-from-generation status enforcement.
2. Introduce one recursive per-kind validation layer, including plan/completion schemas.
3. Make parent use depend on verified stored artifacts, then enforce it on every lineage edge.
4. Apply duplicate-ID rejection to every collection on build and load.
5. Compare full request identity in the withdrawal plan race.
6. Add the nine live reproductions from this review as regression tests.
7. Return for a focused third review.

These can be implemented as one cohesive hardening pass. The recursive validators and verified-parent representation are shared dependencies; freezing those interfaces before splitting work will prevent parallel branches from inventing incompatible contracts.

## Alignment statement

I agree that commit `8d1d72d` fixes the exact defects demonstrated in the first review and materially improves the implementation. I disagree that all seven findings are fully closed, because broader acceptance conditions from findings 3–6 remain reproducibly bypassable.

**Final status: Not aligned for merge, pilot population, real scoring, or decision use. Preserve the completed fixes; close the five residual findings above; then perform a focused joint re-review.**
