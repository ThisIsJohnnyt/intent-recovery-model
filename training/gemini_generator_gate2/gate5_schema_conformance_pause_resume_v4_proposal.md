# Gate 5 schema-conformance evidence and bounded pause/resume campaign v4

**Date:** 2026-08-17  
**Status:** Proposal only; design authorized by Johnny, implementation and execution unauthorized  
**Scope:** A fresh successor to terminal v3 with content-free schema diagnostics and narrowly resumable output-shape pauses

## 1. Purpose and historical limitation

Real v3 attempt 3 returned HTTP 200 with a valid provider envelope but stopped at `schema_invalid` while
validating the JSON string inside its sole text part. The candidate was never staged, its text was never
persisted, and the raw response was retained only as a hash. Therefore the specific historical schema failure
cannot be recovered retroactively and this proposal makes no claim about which rule failed.

For future attempts, the paid runner should preserve only a fixed schema-rule identifier and bounded structural
counts or booleans. It should never preserve candidate text, model-controlled key names, JSON parser text, or
any reconstruction aid.

This proposal also replaces the current all-or-nothing campaign transition with two explicit tiers:

- a four-code output-usability tier that pauses for Johnny's review and can resume through a separately
  validated review-confirmation artifact; and
- a permanent hard-terminal tier for every safety, integrity, identity, billing, transport, collision, or
  unknown outcome.

V3 is already terminal and remains immutable. These capabilities begin only in a fresh v4 package.

## 2. Authority boundary

Johnny authorized proposal and local-build work needed to keep the project moving. That does not authorize:

- editing or reopening v3;
- creating v4 campaign state;
- credential access, a provider request, candidate generation, or spend;
- changing prompts, schedule, model selection, schema constraints, collision thresholds, usage caps, the
  reconciliation stop, or the pilot ceiling;
- candidate review, staging, corpus mutation, commit, or push.

Implementation requires Claude's independent proposal approval, followed by local build and independent review.
A fresh v4 attestation must begin execution-unauthorized. Johnny must separately authorize the v4 campaign
before he personally runs any real command.

## 3. Immutable v3 terminal baseline

The current v3 verifier re-derives:

- terminal state: `stopped_nonretryable_outcome`;
- v3 attempts reserved: `3`;
- historical component count: `9`;
- historical actual cost: `85,440` USD-millionths;
- historical component manifest:
  `17980710e16ddab4ed822fae8beebe21a2662df6f45317200efc977e6a6e0993`;
- terminal component row:
  `c1643a53b1940517bdbec8beff4a286c68f7d477c5caf00357b502fd3e4ee16e`;
- terminal disposition: `schema_invalid`;
- terminal attempt booked cost: `10,680` USD-millionths;
- terminal attempt candidate quarantine count: zero.

V4 must invoke v3's own verifier and pin the actual terminal evidence. The principal canonical-LF hashes are:

| v3 artifact | SHA-256 |
|---|---|
| final attestation | `d2b43f895b79e50fd7c268ae2d4ea7dc7b164f5dc30b838e39170ba955d5cc11` |
| terminal campaign state | `b6ce772b8e924cfa2251a87f402bf8bc26807dc9d3570ac1b65c659b2967ce27` |
| attempt 1 lock | `ac9cdf867214859edf1d69ade8c5e404a65500c09c04fbb5b6968e115d14a652` |
| attempt 1 completion | `32cc3ee73cef4fb8278cc3a08afa9b8e7f8d4373fc76f0624ba231d95bcf48cc` |
| attempt 2 lock | `5d46fa41c5daff6a474e72d22db9edfefe0bfb039c093eaa99aeae84b89175a1` |
| attempt 2 completion | `3cececaa22a2e1ad98e743eca8f7ddd7e0c2ddfd5146c8c93771a353e8190079` |
| attempt 3 lock | `dcd0aaaac343348fdbe15d8618b7260755b8242f9d71ad51c31b637ed2a17f86` |
| attempt 3 completion | `db4aedecc290eb12c9a34bdf30bcf967c53d239bbcfacb11507e8bf4ec159bd5` |

The v4 gate must additionally pin each file in all three v3 attempt output directories. Their current hashes
are listed in Appendix A. No historical file may be edited, supplemented, reinterpreted, or required to carry
the new diagnostic/link fields.

## 4. Remaining attempt and monetary bounds

The original campaign lineage allowed ten attempts. V1 consumed two, v2 consumed one, and v3 consumed three.
V4 therefore has at most **four** attempts. A local zero-request failure, a 503, a paused output-shape failure,
or any other completed reservation still consumes one attempt. Resume never restores an attempt.

- historical cost entering v4: `85,440` USD-millionths;
- maximum v4 attempts: `4`;
- current full-attempt worst-case reservation: `204,000` USD-millionths;
- maximum aggregate: `85,440 + 4 * 204,000 = 901,440` USD-millionths;
- reconciliation stop remains `2,250,000`;
- hard ceiling remains `3,000,000`.

Every monetary decision must use the live, independently re-derived component chain. The attested
`85,440` baseline only proves what Johnny reviewed; it can never replace the live total in reservation,
reconciliation, cost-ledger, or ceiling calculations.

Neither a pause nor a review-confirmation row changes any cost field. A review artifact with a lower total,
different component hash/count, restored attempt count, changed rate hash, or changed ceiling is invalid.

## 5. Part A — content-free schema-conformance evidence

### 5.1 Additive in-memory error contract

`gate2.parse_response()` must keep its current return value, validation order, thresholds, and human-readable
exception messages. A narrow `ResponseSchemaError(Gate2Error)` (or equivalent reviewed mechanism) may add one
strict `structured_reason` attribute. Existing callers that catch `Gate2Error` continue to behave exactly
as before.

The safe fixed reason kinds are:

- `response_json_invalid`;
- `top_level_keys_invalid`;
- `source_input_not_plain_string`;
- `source_input_word_count_out_of_range`;
- `proposed_output_keys_invalid`;
- `narrative_not_plain_string`;
- `narrative_sentence_count_out_of_range`;
- `list_not_array`;
- `list_item_count_out_of_range`;
- `list_item_not_plain_string`.

Allowed details by kind:

- key-set kinds: booleans `has_source_input`/`has_proposed_output` or
  `has_narrative`/`has_bullets`/`has_action_items`, plus bounded nonnegative
  `extra_key_count`; actual model-controlled key names are forbidden;
- count kinds: bounded integer `actual_count`, `min_allowed`, and `max_allowed`;
- list kinds: fixed field enum `bullets|action_items`, and for invalid items a bounded integer `index`;
- all other kinds: no details beyond the fixed kind.

The raw JSON parser exception must never cross this boundary because it may quote response fragments.

### 5.2 Diagnostic artifact

Every future attempt directory reserves `schema_conformance_diagnostics.jsonl` empty before credential access.
It is append-only and independently row-hash chained. Under the stop-on-first-rejection engine, at most one row
may exist.

A row may contain only:

- fixed artifact/schema version;
- request sequence, schedule slot number, model, mechanism, request hash, and raw-response hash;
- rejection reason code `schema_invalid`;
- one validated fixed `structured_reason`;
- linked rejection sequence;
- literal false flags for candidate-text persistence, candidate review, and corpus mutation;
- prior-row and row hashes.

It must never contain:

- candidate text or any value derived from it beyond the approved counts/booleans;
- a raw or unexpected key name;
- a JSON fragment, parse position, parser/exception message, snippet, prefix, suffix, token, n-gram, or
  signature;
- prompt, comparator, or protected-reference text;
- provider headers/body beyond the already-approved raw-response hash;
- credentials, secret-store details, identifiers, or raw exceptions.

The row must use an exact field set, fixed enums, non-boolean bounded integers, an explicit byte cap, duplicate
rejection, and `gate2.contains_secret()` before persistence. Any validation failure withholds it and raises
`schema_conformance_diagnostic_withheld`, which is hard-terminal.

### 5.3 Rejection linkage and write failure

Future rejection rows gain one nullable field:

`schema_conformance_diagnostic_row_hash`.

It is required and non-null only for `schema_invalid`. The rejection and diagnostic must agree on sequence,
slot, model, mechanism, request hash, raw-response hash, and reason code. The run summary gains diagnostic count
and chain-head fields.

Core receipt, cost, and rejection evidence must be written before the diagnostic. If diagnostic persistence
fails after a real request, core evidence remains conserved, the run stops immediately with
`schema_conformance_diagnostic_persistence_failed`, and no further request can occur. That code is permanently
hard-terminal and never eligible for pause/resume.

## 6. Part B — tiered pause and review-confirmed resume

### 6.1 Exact pause-eligible whitelist

Only these four stop codes may produce `paused_pending_review`:

- `schema_invalid`;
- `extra_key`;
- `finish_reason_invalid`;
- `size_limit_failed`.

`schema_invalid` is pause-eligible only when its diagnostic row and rejection cross-link validate. A missing,
withheld, malformed, orphaned, duplicated, or unwritable schema diagnostic is hard-terminal.

`extra_key` and `size_limit_failed` are included for forward compatibility but are not currently reachable.
`finish_reason_invalid` currently has no new content diagnostic; its pause evidence is the validated ordinary
receipt/rejection/cost/summary bundle and fixed stop code.

The implementation must use this positive whitelist. Every unrecognized or newly introduced stop code defaults
to hard-terminal.

### 6.2 Permanent hard-terminal tier

The following are explicitly never resumable without a fresh version/build/attestation:

- `protected_collision`, `prompt_imitation`, `pilot_duplicate`, `secret_exposure`,
  `provider_blocked`, `manual_global_stop`, `budget_or_usage_unknown`,
  `transport_failed_no_retry`, `model_identity_mismatch`;
- `zero_request_local_failure`, `unexpected_local_error`,
  `attestation_artifact_hash_mismatch`, `execution_day_rate_snapshot_mismatch`,
  `provider_usage_exceeds_frozen_cap`, `pilot_ceiling_exceeded`,
  `reconciliation_stop_before_request`;
- `output_collision_diagnostic_withheld`,
  `output_collision_diagnostic_persistence_failed`,
  `schema_conformance_diagnostic_withheld`,
  `schema_conformance_diagnostic_persistence_failed`;
- any generated candidate, completed 24-slot pilot, attempt cap, evidence ambiguity, chain/hash mismatch,
  incomplete crash state, or unknown code.

This list is documentation; the security control is the four-code positive whitelist.

### 6.3 Review-confirmation artifact

A pause does not authorize another attempt. It leaves the campaign in the absorbing-for-execution state
`paused_pending_review`. The only allowed next event is `pause_review_confirmed`, produced from a new strict
review-confirmation JSON artifact for that exact pause.

The artifact must bind:

- fixed artifact/schema version;
- v4 final attestation hash and campaign proposal/build hashes;
- pause local date, review local date, review mode `same_day|next_day`, and the rate-snapshot hash effective for
  the next attempt;
- paused campaign-state row hash;
- paused attempt sequence, lock hash, completion hash, and output-evidence manifest hash;
- exact pause stop code;
- schema diagnostic row hash for `schema_invalid`, otherwise null;
- current attempts reserved and remaining;
- current historical component count, manifest hash, and live cost;
- unchanged maximum attempts, reconciliation stop, and hard ceiling;
- `reviewed_by: "Johnny"`;
- literal `pause_evidence_reviewed: true`;
- literal `resume_one_next_manual_attempt_authorized_by_johnny: true`;
- non-secret notes and the artifact's own canonical hash.

It must contain no credential, candidate text, response content, identifier, secret path, or raw exception.
The campaign runner validates it against freshly re-derived state and evidence before appending anything.

Each review artifact authorizes only the transition back to `active_after_review`; it does not itself invoke
transport. Johnny must still manually run the ordinary attempt command afterward. The artifact is
exclusive-created or must have a unique pause sequence, is hash-pinned into the campaign ledger, and cannot be
reused for a later pause.

For `same_day`, the review local date must equal the pause local date and the effective rate-snapshot hash must
equal the final v4 attestation's execution-day snapshot hash. The ordinary same-day path otherwise remains
unchanged.

For `next_day`, Section 6.5 adds mandatory fields and validation. The review artifact remains one-use and
pause-specific; a next-day refresh does not amend the v4 attestation, authorize multiple future dates, or
authorize transport.

### 6.4 Repeated pauses

Multiple pause/resume cycles are allowed within v4 because the safety bounds are monotonic:

- each paused attempt has already consumed one of the fixed four attempts;
- each real request's conservative booked cost is already appended to the component chain;
- the live total can only increase;
- the review artifact cannot change attempts, cost, rates, ceilings, or historical evidence;
- the next attempt still passes the ordinary reservation and reconciliation checks;
- the fourth attempt terminates regardless of outcome.

Example: attempt 1 pauses, Johnny reviews and unlocks attempt 2; attempt 2 may pause again, but requires a new
artifact bound to pause 2. No artifact can authorize more than one state transition.

Same-day review/resume remains restricted to the pause's local calendar date and original attested rate
snapshot. A narrowly bounded next-day path is permitted only under Section 6.5. Any other date relationship,
rate drift, missing fresh fact, or unverifiable snapshot fails closed and requires a fresh version and
attestation.

### 6.5 Immediate-next-calendar-day review and resume

"Next-day" means the immediately following local calendar date on Johnny's execution host: the review date
must equal `pause_local_date + 1 calendar day`. It is not a rolling 24-hour window. This matches the project's
existing execution-day controls, which use the host's local date, and prevents an artifact from remaining
valid merely because fewer than 24 elapsed hours have passed. A review two or more local dates after the pause
is invalid and requires a fresh version/attestation.

A next-day review-confirmation artifact must include every field required by Section 6.3 and additionally bind:

- fixed `review_mode: "next_day"`;
- the paused attempt's recorded local date and the immediately following review local date;
- a new immutable execution-day rate-snapshot artifact dated exactly to the review local date, its canonical
  SHA-256, and literal `execution_day_rate_snapshot_verified: true`;
- exact per-model input/output USD-millionth rates from that snapshot;
- the prior attested rate-snapshot hash and exact rates, so equality is checked rather than inferred;
- literal fresh confirmations for paid tier, prepay plan, auto-reload off, billing-account isolation, no
  unexpected billing activity since the pause, no other Gemini/API activity since the pause, and the key
  remaining only in Windows Credential Manager;
- a freshly observed prepaid balance in USD-millionths, which must be a non-boolean integer at least the
  unchanged `$3.00` pilot ceiling and sufficient for the freshly re-derived next reservation;
- literal fresh confirmation that both exact models remain available/non-deprecated with `generateContent`
  support and that the frozen common `low` thinking and structured-output surfaces remain applicable;
- Johnny's review of these fresh facts and authorization of exactly one next manual attempt, as already
  required by Section 6.3.

The new snapshot may have a different file hash because its date and verification metadata are new, but its
actual rate tuple must exactly equal both the final v4 attestation's rate tuple and the frozen provider
contract. The runner must load and validate the snapshot through the ordinary execution-day-rate validator,
require its date to equal the host's current local date, and compare each price field exactly. If the rates
differ by even one USD-millionth, the snapshot cannot be fetched or verified, the provider facts cannot be
reconfirmed, the balance/fresh-account facts are absent, or the host date has advanced again, validation stops
before campaign mutation, credential access, or transport. There is no stale-snapshot fallback.

On successful next-day confirmation, `pause_review_confirmed` records the fresh snapshot hash, review date,
and review-artifact hash in the campaign ledger. `active_after_review` carries that snapshot as the effective
execution-day context for exactly the next attempt. Before reserving that attempt, the runner revalidates the
campaign chain, review artifact, current host date, fresh snapshot hash/content, identical rates, live cost,
attempt counts, and unchanged caps. A second attempt or later pause requires the ordinary state-machine path
and, if another calendar boundary is crossed, another new pause-specific next-day artifact. No refresh can
resurrect a terminal state, restore an attempt, reduce booked cost, or bypass the four-code whitelist.

## 7. Proposed v4 state machine

Allowed events and transitions:

1. `campaign_authorized`: none -> `authorized_not_started`.
2. `attempt_reserved`: `authorized_not_started|active_after_clean_503|active_after_review` ->
   `attempt_reserved`.
3. `attempt_completed`:
   - clean, fully evidenced zero-candidate/zero-diagnostic HTTP 503 and attempts remain ->
     `active_after_clean_503`;
   - exact pause-eligible result and attempts remain -> `paused_pending_review`;
   - any hard-tier/unknown result, candidate, completed pilot, or fourth attempt -> a terminal state.
4. `pause_review_confirmed`: `paused_pending_review` -> `active_after_review`.

No attempt may be reserved from `paused_pending_review`. No transition leaves a terminal state. An incomplete
`attempt_reserved` state blocks all new attempts; recovery may only derive completion from existing evidence
and never send a request.

## 8. Required local build and tests

Before any fresh attestation, local tests must prove:

1. Every `parse_response()` failure point yields the correct fixed structured reason while legacy exception
   text and successful return behavior remain unchanged.
2. Invalid JSON never persists parser text or raw fragments.
3. Missing/extra key cases persist only expected-key booleans and bounded extra counts, never actual key names.
4. Word, sentence, list-count, non-array, and invalid-item cases persist only approved counts/enums/indexes.
5. A unique candidate-text canary and secret-shaped value are absent from every serialized artifact.
6. Exact schema-diagnostic field set, byte/count bounds, duplicate-key rejection, secret scan, and hash chain.
7. Rejection/diagnostic cross-links catch rehashed tampering, orphan, missing, duplicate, and mismatch cases.
8. Injected diagnostic I/O failure preserves core evidence, sends no later request, and is hard-terminal.
9. Only the four whitelisted codes pause; every hard-tier, unknown, candidate, collision, and integrity outcome
   terminates.
10. `schema_invalid` without a valid diagnostic cannot pause.
11. A paused campaign cannot reserve another attempt without a valid new review artifact.
12. Review artifacts reject stale/reused pause hashes, changed attempt/cost/component/rate/cap fields, false
   authorization, extra fields, identifiers, and secrets.
13. A valid same-day review artifact appends exactly one transition and never accesses credential or transport.
14. A valid immediate-next-calendar-day artifact accepts a newly dated snapshot only when every actual rate
   equals the original attested tuple, all fresh dashboard/provider facts validate, and the balance remains
   sufficient.
15. Next-day validation rejects a rolling-24-hour interpretation, a two-or-more-day gap, stale/future snapshot,
   unavailable verification, missing fresh fact, insufficient balance, any price-field drift, and host-date
   rollover before credential access or campaign mutation.
16. The next real reservation revalidates the accepted refresh context; its one-use authority cannot be reused
   for a second attempt or later pause.
17. Two concurrent resume attempts or two concurrent next-attempt reservations have exactly one winner.
18. Two or more same-day/next-day pause-resume cycles work without restoring attempts or reducing live cost.
19. The fourth v4 attempt is terminal; worst-case aggregate remains exactly `901,440`.
20. Crash/recovery paths never resend and cannot bypass a pending review.
21. All v3 evidence stays byte-identical and passes v3's verifier.
22. Verify-only, focused tests, available package tests, compilation, secret scans, and `git diff --check`
   complete with no credential, network, provider use, or campaign-state output.

## 9. Sequence

1. Codex prepares this proposal only.
2. Claude independently verifies v3 evidence pins, privacy boundary, whitelist, state machine, repeated-pause
   safety, and unchanged money math.
3. If approved, Codex builds the local-only schema diagnostic module, paid-runner integration, v4 gate/template,
   v4 campaign/review validator, and tests.
4. Claude independently reads, hashes, tests, and adversarially checks for content leakage and any path that
   restores attempts, understates spend, changes rates/caps, reuses review authority, or resumes a hard stop.
5. Fresh same-day facts and a still-unauthorized v4 attestation are reviewed.
6. Johnny separately decides whether to authorize v4.
7. For each future pause, Johnny separately reviews the exact pause evidence and authorizes at most one resume
   transition through a fresh review-confirmation artifact. If review occurs on the immediately following local
   date, the artifact must also carry the fresh rate/account/provider facts required by Section 6.5.
8. Johnny personally runs every real attempt. Neither AI touches the credential or sends a request.

## Appendix A — v3 attempt-output hashes

| attempt | artifact | SHA-256 |
|---|---|---|
| 1 | candidate quarantine | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 1 | cost ledger | `860beafd9662987d7b1710fe8b384c899031980e6a3295b34484d73947cc5a60` |
| 1 | output-collision diagnostics | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 1 | reservation | `a2848e1368e801638c3dde06e6ba2bc3c7587a413e773faa4c6f207191cb9819` |
| 1 | rejection ledger | `a0e8d6b9de821698dd585fbb87712316ccf284d70714bb45a3814fafffe4aa99` |
| 1 | receipts | `6044b56813dbabdfc86a02acc8012ef17d513b2d7719eaae785df44b374f75d2` |
| 1 | summary | `09a94607649da202af979548c5c187596df9e97180c30d1ab1381b96374a2f31` |
| 2 | candidate quarantine | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 2 | cost ledger | `4c3ddc8c2d609eb5b39dd811ecd0fecb70c8cbab3b92133010ffc0bac9b1bbcb` |
| 2 | output-collision diagnostics | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 2 | reservation | `9a838cfe8b93842542654207a35b6e9ca92b8df979cb867f6da8f1d9ffccb2b8` |
| 2 | rejection ledger | `a0e8d6b9de821698dd585fbb87712316ccf284d70714bb45a3814fafffe4aa99` |
| 2 | receipts | `6044b56813dbabdfc86a02acc8012ef17d513b2d7719eaae785df44b374f75d2` |
| 2 | summary | `3045746c22467d0f64f5068ca08b023990fc8d39b673fbe05e53158338ddfc9a` |
| 3 | candidate quarantine | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 3 | cost ledger | `3d59e204925f5216db60c7229d3b5bccf012f381c5a927b77e0716323b931d57` |
| 3 | output-collision diagnostics | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| 3 | reservation | `98f4f39283a4b75e241421cdf181193153b33e0758af4cb36f0ede2629def0df` |
| 3 | rejection ledger | `2db33bd2e92b46f3763c8185f542029bca66188dd3658c4888a6f6d281f07e62` |
| 3 | receipts | `a31f082c561737a2f857ad7c926c8e13ae599f1ab0922dcd4b6f4b2dbc09d947` |
| 3 | summary | `ddbb22ed1aab9d32e788740028ac14c410e117a9e76dcbb3eaa168fb8b7e4050` |
