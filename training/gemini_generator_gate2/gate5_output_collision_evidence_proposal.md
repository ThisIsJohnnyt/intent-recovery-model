# Gate 5 future output-collision evidence proposal

**Date:** 2026-08-17  
**Status:** Proposal only; no implementation or execution authority  
**Scope:** Local evidence-capture design for future paid-pilot attempts

## 1. Purpose and known limitation

Two real paid-pilot attempts have stopped on protected-content collisions: the earlier fresh attempt at
`output.bullets:02` and the later v2 attempt at `output.narrative`. Their raw provider responses were hashed
and discarded, as designed. Consequently, this proposal cannot identify the protected reference or similarity
score involved in either historical collision. Those records remain intentionally unknowable from the retained
evidence and must not be modified, reinterpreted, or replayed.

For a future attempt only, this proposal would preserve the safe diagnostic facts that
`gate2.screen_candidate()` already computes in memory and currently discards when the paid runner retains only
the first `fatal_reasons` field-path code. The retained facts would be limited to comparator reference labels,
metric names, and numeric scores. No candidate text or derivative of candidate text would be retained.

The existing prompt-side precedent is `schedule.json`'s `prompt_collision_preflight`, which already records
`reasons`, `maximum_token_jaccard`, and `maximum_character_5gram_jaccard` as reference-label-and-score evidence
without retaining comparator text.

## 2. Non-authority statement

This document authorizes none of the following:

- implementation;
- credential access;
- a provider request or spend;
- a threshold, comparator-pool, parser, prompt, schedule, or screening change;
- candidate review, staging, corpus mutation, commit, or push;
- resumption or replacement of any pilot or campaign.

Implementation would require a separate local build and independent review. Any later real attempt would still
require its own reviewed execution package, fresh attestation, and Johnny's explicit execution authorization.

## 3. Frozen privacy boundary

The future artifact may contain only:

- fixed artifact and schema identifiers;
- the request sequence and existing schedule slot/model/mechanism identifiers;
- the existing request hash and raw-response hash;
- the collision field path already used in the rejection reason code;
- protected-reference labels already present in the local comparator manifest;
- fixed metric/reason names;
- finite numeric similarity scores in the inclusive range `0.0` through `1.0`;
- the linked rejection sequence and the diagnostic chain hashes;
- fixed disposition and no-mutation flags.

It must never contain:

- candidate text, a candidate object, a field value, a snippet, quotation, prefix, suffix, token, n-gram,
  signature, or reconstruction aid;
- protected-reference text or any excerpt from it;
- prompt text or earlier-candidate text;
- a provider response body or header;
- a credential, credential-store target, account/project/billing identifier, or raw exception text;
- qualitative-similarity details such as shared entities, quantities, phrases, clauses, or role terms.

The diagnostic is not a relaxed quarantine path. A colliding candidate remains rejected, is never written to
candidate quarantine, and is never reviewed.

## 4. Proposed future artifact

A new empty file, `output_collision_diagnostics.jsonl`, would be exclusive-created with the other output
artifacts before credential access. It would be append-only and independently row-hash chained with the same
canonical-JSON and `prior_row_hash` convention used by the existing ledgers.

At most one diagnostic row can be written in a paid-pilot run under the current stop-on-first-rejection
behavior. A row would have this exact conceptual shape:

```json
{
  "artifact": "gemini_generator_gate5_output_collision_diagnostic_row",
  "schema_version": 1,
  "sequence": 1,
  "schedule_slot": "S01",
  "model": "gemini-3.7-flash",
  "mechanism_id": "M01",
  "request_hash": "<sha256>",
  "raw_response_hash": "<sha256>",
  "rejection_reason_code": "proposed_output.narrative:protected_collision",
  "field_path": "proposed_output.narrative",
  "protected_collision": {
    "reasons": [
      {
        "kind": "token_jaccard_threshold",
        "reference": "acceptance:009:expected_behavior",
        "score": 0.812345
      }
    ],
    "maximum_token_jaccard": {
      "reference": "acceptance:009:expected_behavior",
      "score": 0.812345678
    },
    "maximum_character_5gram_jaccard": {
      "reference": "acceptance:006:expected_behavior",
      "score": 0.456789012
    }
  },
  "candidate_text_persisted": false,
  "protected_reference_text_persisted": false,
  "candidate_review_performed": false,
  "corpus_mutation_performed": false,
  "prior_row_hash": null,
  "row_hash": "<sha256>"
}
```

The example labels and scores above are illustrative only and are not claims about either historical
collision.

### 4.1 Structured reason derivative

The artifact should not persist the current human-readable `protected["reasons"]` strings verbatim. The build
should add a small pure local formatter that converts only those already-computed protected-collision reasons
into a strict structured derivative. Its allowed `kind` values would be exactly:

- `normalized_exact_match`;
- `normalized_containment`;
- `token_jaccard_threshold`;
- `character_5gram_jaccard_threshold`.

Exact-match and containment entries would have `score: null`, because the current collision result does not
assign a meaningful numeric score to those predicates. Jaccard entries would contain the same rounded score
already computed for the reason. No free-form reason string would cross the persistence boundary.

The preferred implementation is to make `collision_check()` construct this structured trigger data at the
same time it constructs its current in-memory human-readable reasons, avoiding fragile parsing of strings.
The existing `fatal`, `reasons`, and maximum-score fields must remain semantically unchanged. Any addition to
the in-memory return value must be treated as a versioned local API extension and must not cause regeneration
or mutation of the already-frozen `schedule.json` or any historical evidence.

### 4.2 Strict validation before persistence

Before a diagnostic row is serialized:

- the selected field must be the field named by the first `:protected_collision` fatal reason and must map to
  exactly one `screen["fields"]` entry;
- `protected.fatal` must be literal `true`, with at least one structured trigger;
- every reference label must exactly equal a label from the already-loaded protected comparator references;
- field path, slot, model, and mechanism must match the current frozen request slot and candidate-field set;
- every score must be a non-boolean finite number from `0.0` through `1.0`, rounded no more precisely than the
  existing collision result;
- reason count must be bounded by four times the comparator-manifest `screened_field_count`; duplicate reason
  objects must be rejected;
- the object must have the exact versioned field set, pass `gate2.contains_secret()`, and contain none of the
  forbidden content-bearing key names;
- canonical serialization must remain within a small explicit byte cap selected and tested during the build.

Failure of any validation withholds the diagnostic entirely and stops with a fixed local code such as
`output_collision_diagnostic_withheld`; it must never fall back to storing a string representation, exception,
candidate value, or response body.

## 5. Link to the ordinary rejection evidence

For a future-version run only, the paid rejection row would gain one nullable field:

```json
"output_collision_diagnostic_row_hash": "<sha256-or-null>"
```

It must be non-null only when `reason_code` ends in `:protected_collision`. The diagnostic row and rejection
row must agree exactly on sequence, request hash, raw-response hash, and rejection reason code. The run summary
would add `output_collision_diagnostic_count` and `output_collision_diagnostic_chain_head`.

The future result validator must verify both chains independently and then verify these cross-links. A
re-hashed tamper to either row, a missing linked row, an orphan diagnostic, a duplicate diagnostic, or a
protected-collision rejection with a null link must fail validation.

The build must choose and test a write/recovery ordering that never sacrifices the existing receipt,
rejection, or cost evidence if diagnostic persistence fails after a real request. The diagnostic is secondary;
core request and cost evidence remains mandatory. No live attempt may be authorized until an injected-I/O-
failure test demonstrates that a post-request diagnostic-write failure leaves conservative, reviewable core
evidence and cannot silently continue to another slot.

## 6. Backward compatibility and immutable history

This capability must be introduced through new future-version validators and execution artifacts. It must not:

- edit any original, fresh, third-attempt, v1-campaign, v2-campaign, diagnostic, receipt, ledger, summary,
  quarantine, reservation, completion, lock, state, or attestation file;
- add the new field to old rows or require old rows to contain it;
- change the hash, schema interpretation, or verifier outcome of any historical artifact;
- claim to diagnose either past collision;
- alter the protected comparator corpus or collision thresholds.

Any future campaign that uses this capture must pin the reviewed capture implementation and new validator in
a fresh attestation. Existing runners remain responsible only for verifying their own historical formats.

## 7. Required local build and tests before review

A later implementation review must include, at minimum:

1. A synthetic protected collision whose unique candidate-text canary is absent from the canonical diagnostic
   row bytes and from every other non-quarantine output artifact.
2. A synthetic collision containing a secret-shaped value in candidate text; only the approved reference
   label/metric/score may survive, and the secret-shaped value must be absent from all serialized evidence.
3. Exact-match, containment, token-Jaccard, and character-5-gram triggers mapped to the correct fixed enums,
   labels, and nullable/finite scores.
4. Multiple triggered references retained without candidate or comparator text, with the reason-count and byte
   caps tested at and one past their boundaries.
5. Rejection-to-diagnostic cross-link validation, including re-hashed tampering, orphan, missing, duplicate,
   sequence/hash mismatch, and null-link cases.
6. Unknown reference labels, unknown fields/kinds, booleans as scores, NaN/infinity, negative scores, scores
   above one, malformed field paths, and secret-scan failures all rejected before persistence.
7. Non-protected rejection reasons produce no diagnostic row and a null diagnostic link.
8. A protected collision still produces zero quarantined candidates, stops the run, and leaves thresholds,
   screening, parser behavior, and cost accounting unchanged.
9. Injected diagnostic-file I/O failure after a simulated real response preserves conservative receipt,
   rejection, and cost evidence, stops the run, and never advances to another request.
10. Output files, including the empty diagnostic ledger, are reserved before credential access.
11. Every currently retained real evidence file remains byte-identical, and its existing verifier still
    passes without invoking the new validator.
12. Secret scans, focused tests, the full package suite, `git diff --check`, and a local verify-only path all
    pass with `network_used: false`, `credential_read: false`, and `file_output_created: false`.

## 8. Proposed sequence

1. Codex prepares this proposal only.
2. Claude independently reviews its scope, privacy boundary, linkage, and backward-compatibility claims.
3. If approved, Codex builds the local-only future capture module, strict schema/validator, runner integration,
   and tests without credential or network access.
4. Claude independently reads the source, recomputes hashes, runs tests, and adversarially checks that no
   candidate or comparator text can persist.
5. Only after a clean joint review may Johnny decide whether to authorize preparing a fresh future execution
   package and attestation.
6. A real request remains separately and explicitly unauthorized until Johnny personally authorizes it.

