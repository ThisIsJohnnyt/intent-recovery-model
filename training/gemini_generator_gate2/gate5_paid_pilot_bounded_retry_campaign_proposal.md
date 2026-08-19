# Gate 5 paid-pilot bounded retry campaign proposal

**Date:** 2026-08-16  
**Status:** Proposal only. No campaign runner, state, attestation, credential access, provider request, spend,
parser or threshold change, candidate handling, staging, commit, or push is authorized by this document.

## 1. Purpose and narrow continuation rule

Three separately authorized real pilot attempts have been preserved:

1. the original attempt stopped safely on the then-unknown response shape; that parser gap is now fixed and
   verified against live evidence;
2. the completed fresh attempt returned HTTP 200 and was stopped by the unchanged protected-collision screen;
3. the third attempt stopped on a real HTTP 503 from `gemini-3.7-flash`, with zero candidates retained.

The third result is byte-consistent with the provider's previously observed high-demand response and is the
only outcome in this history that warrants trying the unchanged pilot again without a new proposal cycle.
Johnny therefore requested a bounded campaign that lets him manually start a new full-pilot attempt at his
own chosen time after, and only after, a completely validated transient 503 result.

This is not an automated retry loop. One invocation can start at most one full execution of the already-
reviewed fixed 24-slot pilot. The campaign may remain open only when that attempt ends with all of the
following facts simultaneously true:

- `candidate_quarantine_count == 0`;
- `global_stop == "unexpected_http_status"`;
- the terminal receipt has numeric `http_status == 503`;
- every reservation, receipt, cost, rejection, candidate, and summary artifact validates and cross-links;
- the attempt's output directory is complete, immutable, and newly created;
- aggregate historical plus campaign cost remains within both existing monetary controls.

Any other result permanently stops the campaign for review. In particular, another protected collision, any
quarantined candidate, a non-503 status, any local/credential/transport/evidence ambiguity, a reconciliation
or ceiling stop, or a complete 24-slot run cannot auto-continue.

## 2. Immutable initial historical evidence

### Component 1 — original response-shape stop

- directory: `gate5_pilot_run_2026-08-16`
- summary file SHA-256: `627ba8dfba9410a1201907f7d5eb2cce69b2d9f41111cd8c4e84f540f1c16050`
- receipts file SHA-256: `b30e21d29868db74d9cee9719f2f8c1f002cc40ff1f5557224e658e3861e62c4`
- cost file SHA-256: `0c39db795f4ff4a75a199af8b0f8a11ffe08663d67a8148015dd8bd0a47703ae`
- rejection file SHA-256: `3b1cec5c6c37d0fce25b533a9ba890d3d44d7acc53e3bef9683ec13438634423`
- receipt row SHA-256: `3db5178d10e4c5bfb556711bade9a25381ffffc5b63b78a9a3bef450546e3ee2`
- booked pilot cost: `10,680` USD millionths

### Component 2 — completed fresh protected-collision stop

- directory: `gate5_pilot_run_fresh_2026-08-16`
- reservation file SHA-256: `aa91f8d811adb31644b0d86021781bf7a97aa0658e1e03f2876fd8ccfc4cb970`
- summary file SHA-256: `16d624cc6b8d698bf3a34bce5f919eba38f9bc4babe7fc8ed50981568bcc9169`
- receipts file SHA-256: `fd290052ddeeec186b62d768f89122185509d94af72139ac85443bf79a8d4105`
- cost file SHA-256: `c90f5a8dd089d5a1e1e5f0b2a7c699346101ce24b84b1b47cc5713ca39f01413`
- rejection file SHA-256: `20db77f940829a50b4b06eae3bfe07f4e6539d89f4ea89f912444484341544d3`
- empty quarantine SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- receipt row SHA-256: `34cb7d2f3ba34d5438b539f4d83581d7cc47c32203379d1d85616646f01453be`
- exact stop: `proposed_output:output.bullets:02:protected_collision`
- booked pilot cost: `10,680` USD millionths

### Component 3 — third-attempt transient 503 stop

- directory: `gate5_pilot_run_third_2026-08-16`
- final attestation SHA-256: `3a8078ec873a0b77c8848c431fef47453e8323bab8ba23dbf62b109a2a3d6671`
- reservation file SHA-256: `14ae47b46b0263752757bfc10fa3bfef5581c61b83a4f4c3aeec05d5cb4fbf0a`
- summary file SHA-256: `23fd84fd59ad9455e14429363617e3906e75802d78713da1ce67902dc2efd6e3`
- receipts file SHA-256: `6044b56813dbabdfc86a02acc8012ef17d513b2d7719eaae785df44b374f75d2`
- cost file SHA-256: `a74aad50c129660c0bd976b0586797e46c4c0a4ff0729894efcd42c46f854ca5`
- rejection file SHA-256: `3137726f1b6ea7a5d50e517001cd93578bd9441a6d7c108db10ece7ddc216c65`
- empty quarantine SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- receipt row SHA-256: `057b1138e8297ff7ceee61e172b349ea31a17499b47b4eca653e3a00b9918c02`
- raw-response SHA-256: `01f5c7d4e4d8ec06c8098777e731b3d552ba518feb02b681f6c569edcd9c6f6d`
- internally verified summary SHA-256:
  `bb9118b8fe72c8cf2fa3af32d351871acd9d8b4e65e57120ced17a8561834f97`
- exact result: one slot-1 request, HTTP 503, `unexpected_http_status`, zero candidates retained
- booked pilot cost: `10,680` USD millionths

All historical directories are immutable. Their ledgers must independently pass their hash chains, their
summaries must recompute, and their recorded outcomes and costs must be revalidated before campaign state or
credential access is possible.

## 3. Generalized historical cost ledger

The initial pilot cost carried into the campaign is:

`10,680 + 10,680 + 10,680 = 32,040 USD millionths ($0.03204)`

The campaign must replace the fixed two-component assumption with a validated ordered component manifest.
Each component records an attempt identifier, terminal disposition, booked cost, and hashes of its immutable
reservation/receipt/cost/rejection/quarantine/summary evidence as applicable. The initial three components
above are frozen. After each campaign attempt, exactly one newly validated completed-attempt component is
appended; no component can be edited, removed, reordered, duplicated, or silently collapsed into only a
scalar total.

The historical total must always be recomputed by summing the validated component costs. A stored total is
only a cross-check, never the source of truth. Every request reservation inside attempt `N` must use:

`validated prior-component total + attempt-N cumulative cost + next worst-case slot reservation`

The existing $2.25 reconciliation stop and $3.00 pilot ceiling remain unchanged and apply across the entire
component sequence. The frozen worst-case reservation for one full 24-slot attempt remains `204,000` USD
millionths. Ten campaign attempts at that full worst case plus the initial `32,040` would total `2,072,040`
USD millionths ($2.07204), below the $2.25 stop. This arithmetic does not create a new campaign budget or
permission to bypass either existing control; both controls still fail closed on every individual slot.

Separately authorized diagnostic spending remains outside this pilot ledger exactly as previously recorded.

## 4. Campaign bound and manual operation

- Maximum campaign attempts: **10 full-pilot attempts**. The three historical attempts predate the campaign
  and are not counted against this new ten-attempt bound, but their costs remain fully carried forward.
- One CLI invocation may launch at most one full-pilot attempt.
- Johnny alone manually starts each invocation at a time of his choosing.
- No loop, timer, scheduler, background process, agent-triggered call, automatic delay, or automatic request
  exists.
- Every attempt starts at slot 1 with the unchanged fixed 24-slot schedule and receives a new exclusive output
  directory. No prior directory can be appended to, resumed, replaced, or modified.
- After a fully validated clean 503, the campaign state may permit one later manual invocation.
- The tenth clean 503 ends as `attempt_cap_reached`; no eleventh attempt is possible without a new proposal,
  review, attestation, and authorization.
- The first outcome other than the exact clean-503 continuation condition ends the campaign permanently.

The authorization is therefore for a bounded manual capability, not for ten automatic executions and not
for retries inside any individual pilot attempt.

## 5. Persistent state, attempt locking, and crash behavior

The build must use a brand-new campaign directory containing an append-only hash-chained campaign ledger and
separate output directory for each full attempt. The genesis row pins the reviewed proposal, final campaign
attestation, initial three-component manifest, current runner/parser/contract/schema/schedule/rate evidence,
the 10-attempt bound, and the unchanged monetary controls.

Before credential access for sequence `N`, the wrapper must:

1. fully validate the campaign ledger and every historical component;
2. reject any terminal, incomplete, ambiguous, or over-cap state;
3. exclusive-create a fixed-name sequence-N attempt lock that pins the prior campaign-state hash, component-
   manifest hash, recomputed historical cost, final attestation, and intended new output-directory name;
4. append a matching `attempt_reserved` state row;
5. invoke the reviewed paid-pilot mechanism once, passing only the validated component manifest and brand-new
   output path.

Two concurrent invocations selecting the same next sequence cannot both win the exclusive attempt lock or
reach the credential. A lock without one complete matching pilot evidence set and one completion row is an
incomplete attempt and permanently blocks further invocations pending human review. A crash, interruption,
partial ledger write, or ambiguous provider result is never interpreted as a retryable 503.

After the pilot invocation returns, the wrapper must independently validate its full output evidence before
appending a completion row. That row cross-links the attempt lock, output directory, reservation, all output
artifact hashes, chain heads, internal summary hash, component cost, cumulative component-manifest hash,
candidate count, terminal receipt/status, and campaign disposition.

## 6. State transitions

Only these transitions are permitted:

1. `authorized_not_started -> attempt_reserved`
2. `active_after_clean_503 -> attempt_reserved`
3. `attempt_reserved -> active_after_clean_503` only after a complete, independently validated attempt with
   zero quarantined candidates, exact stop `unexpected_http_status`, and terminal receipt status 503, for
   campaign attempts 1 through 9
4. `attempt_reserved -> attempt_cap_reached` after the same exact clean-503 result on attempt 10
5. `attempt_reserved -> stopped_for_candidate_review` if one or more candidates were quarantined
6. `attempt_reserved -> stopped_completed` if all 24 slots completed
7. `attempt_reserved -> stopped_nonretryable_outcome` for a protected collision, non-503 HTTP status,
   reconciliation or ceiling stop, local/credential/transport/evidence error, incomplete output, or any other
   result not explicitly enumerated above

All stopped states are absorbing. Candidate review, promotion, corpus mutation, and another campaign attempt
require separate later decisions as applicable.

## 7. Unchanged per-attempt execution and evidence controls

Every full attempt retains the already-reviewed rules:

- exact fixed 24-slot, two-model schedule beginning at slot 1;
- corrected response parser and live response-shape evidence pinned;
- one candidate per request, nonstreaming, common low thinking, structured output;
- no SDK retry, application retry, redirect, substitution, fallback, tool, caching, or streaming path;
- protected corpus, exact/containment/token-Jaccard/character-5gram screening and thresholds unchanged;
- the first fatal finding stops that attempt;
- candidates enter only that attempt's new quarantine pending independent review;
- no candidate review decision, promotion, corpus mutation, staging, commit, or push during execution;
- output directory and campaign attempt lock reserved before credential access;
- conservative full reservation booked whenever clean usage cannot be validated;
- no raw exception, credential, header value, secret path, candidate text, or response body added to campaign
  state. Candidate content remains only within the already-reviewed quarantine boundary when permitted.

## 8. Required build and adversarial tests

The local build must include a campaign proposal pin, state/manifest validator, campaign execution gate and
template, wrapper runner, and tests. The existing paid-pilot engine may be refactored only as needed to accept
the validated ordered historical-component manifest; request construction, parser, screening, schedule, and
transport behavior must remain unchanged.

Tests must prove at least:

- all three initial components and exact `32,040` total are required;
- dropped, duplicated, reordered, altered, or rehashed-tampered components fail before credential access;
- later campaign-component cost and artifact tampering fails;
- the exact $2.25 and $3.00 boundaries use the recomputed N-component total;
- two or more simultaneous invocations can produce only one lock winner and at most one credential/provider
  path;
- an orphan lock, reservation-only state, partial pilot directory, missing completion row, or unexpected file
  permanently blocks continuation;
- attempts 1-9 continue only on the exact fully validated zero-candidate/503 condition;
- attempt 10 clean-503 terminates at the cap;
- a candidate, protected collision, full completion, 400/401/403/429/5xx-other-than-503, transport failure,
  reconciliation stop, hard ceiling, parser/evidence/local error, and any ambiguous outcome are terminal;
- each attempt gets a distinct brand-new directory and cannot modify historical evidence;
- output/campaign evidence remains hash-linked and secret-clean;
- local `verify_only()` creates no state/output, reads no credential, and uses no network;
- the full existing suite and unchanged protected-collision behavior remain passing.

## 9. Review and authorization sequence

1. Claude independently reviews this proposal, historical pins, state machine, and cost arithmetic.
2. Codex builds the local-only campaign gate/template/runner/state validation/tests under the standing local-
   build permission.
3. Claude independently reviews source and hashes, runs all tests, and adversarially checks component
   tampering, concurrency, incomplete-state behavior, cost boundaries, and the exact continuation predicate.
4. Fresh same-day dashboard/activity/model/rate/secret-store/evidence/campaign facts are confirmed directly
   with Johnny.
5. Codex drafts a new campaign attestation with campaign authorization `false`; Claude verifies it.
6. Johnny separately and explicitly authorizes at most 10 manually initiated full-pilot attempts, with the
   campaign permanently stopping on the first result other than a fully validated clean zero-candidate 503 or
   on the tenth such 503, while the existing $2.25/$3.00 controls continue across all components.
7. Codex finalizes the attestation; Claude independently verifies it.
8. Johnny alone runs each invocation. Neither AI touches the credential or triggers a provider request.
9. Both agents verify each completed attempt and the campaign state before the state may permit another manual
   invocation or any candidate review.

No execution, parser/threshold/screening change, candidate review, corpus mutation, staging, commit, or push
is authorized by this proposal.
