# Gate 5 response-shape key-manifest bounded campaign proposal

**Date:** 2026-08-16  
**Status:** Proposal only. No runner, campaign state, attestation, credential access, provider request, spend,
parser change, candidate handling, staging, commit, or push is authorized by this document.

## 1. Purpose and historical basis

Two separately authorized, manually executed key-manifest diagnostics sent the same frozen slot-1 request and
both received the same transient HTTP 503 response. Both attempts safely persisted only bounded diagnostic
evidence and learned nothing about the HTTP-200 response shape. Their immutable evidence remains historical
and must never be modified or reused as execution authority.

First consumed diagnostic evidence:

- proposal SHA-256: `b361734c6fe329e96002237ea0b7babe671bd009f6b44297aa8f58f8fa3e41d5`
- receipt file SHA-256: `4cf8be458dbc639d6336c9832a3538ad79f6423d10cb1069eb4b1612bf05711c`
- receipt row SHA-256: `391215e0ee809e79f59bcceb636efb47acd1c50af37ff055471c3411ca151531`
- attempt-lock file SHA-256: `48dc28526a2ba5b4ce310e15467e6899e36aa6521bae338f377f60dfd86c065a`
- final attestation SHA-256: `6407098105d1b57369cb68ca3d161e162be47fc9c0146db52b1a30db85aaba31`

Second consumed retry evidence:

- proposal SHA-256: `403ee7c770893121ff6c70c82099365fa4823fa51a325060ea300b83a6287546`
- receipt file SHA-256: `bee2e6cdface66cf0bdb46d535e410717806a371bb9d548e3e70d23cd3de3b6f`
- receipt row SHA-256: `31b8e0010fd4ed16a931263e8e6f407fc1096b7a0b076dd48795ceee3b0ce96c`
- reservation file SHA-256: `96c901826f6577ddfaf695470e9a82a9856457316a7936e2c37d3d9e16812512`
- attempt-lock file SHA-256: `2c979648e8c3e868d243b18c6346ed8714c312c47e227f57f61e3d55285a3a0d`
- final attestation SHA-256: `8218134dcb626e47ef881417f804e57503b1e441e477333a5a4f136a5be57117`

Both receipts record HTTP 503, raw-response SHA-256
`01f5c7d4e4d8ec06c8098777e731b3d552ba518feb02b681f6c569edcd9c6f6d`, the same bounded provider overload
message, one provider request, and a conservative booked cost of 10,680 USD millionths each.

The proposed capability lets Johnny manually make bounded attempts at his own chosen times without rebuilding
and reauthorizing a new one-shot package after every validated 503. It is not an automated poller and cannot
resume the paid pilot.

## 2. Frozen request and evidence boundary

Every campaign invocation uses exactly the already-reviewed slot-1 request:

- model: `gemini-3.7-flash`
- mechanism: `M01`
- method: exactly one `POST` per invocation
- endpoint: `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent`
- request-envelope SHA-256:
  `8420c2d8360f4ffc96fb617dd8d4b081732cf2c87654a65d3ddc2ab8426297b4`
- timeout: 60 seconds
- redirects, SDK retries, application retries, fallbacks, substitutions, tools, caching, and streaming:
  prohibited
- credential: read only from Windows Credential Manager after all local gates and the attempt reservation

On HTTP 200, the response is decoded only in memory with strict UTF-8 and duplicate-key rejection. The runner
may persist only the already-reviewed bounded manifest of JSON key names and counts. It must never persist
response values, candidate text, thought signatures, token values, identifiers, the raw body, or headers.

On HTTP 503, the runner may persist only numeric status, byte count/hash, and the already-reviewed bounded
`error.message` extraction. A fully validated 503 is the only outcome that may leave the campaign open.

On any other HTTP status, the same bounded non-200 evidence path applies and the campaign permanently stops.
On a transport failure, malformed response, credential failure, local exception, evidence mismatch, or state
ambiguity, the campaign also stops and requires review. None of those outcomes may be treated as a retryable
503.

## 3. Campaign and monetary limits

- Maximum provider requests: **20**.
- Per-attempt authorization ceiling: **10,680 USD millionths ($0.01068)**.
- Aggregate campaign ceiling: **213,600 USD millionths ($0.21360)**.
- Each invocation can make at most one provider request.
- Johnny manually starts each invocation. There is no loop, timer, scheduler, background process, automatic
  wait, or agent-triggered execution.
- The campaign permanently stops immediately after the first non-503 response.
- If attempt 20 returns 503, the campaign stops as `attempt_cap_reached`.
- Continuing after any terminal state requires a new proposal, review, attestation, and authorization.

Before credential access, each invocation must reserve its next sequence number and the full 10,680 maximum.
The pre-request aggregate reservation must not exceed 213,600. Every provider request is conservatively booked
at the full per-attempt ceiling unless a later, separately reviewed reconciliation record establishes less;
the campaign never assumes a cheaper cost in order to permit another attempt.

## 4. Persistent state and concurrency control

The implementation must use a new campaign directory and new campaign-specific artifacts, distinct from both
consumed one-shot packages.

The campaign state is an append-only, hash-chained JSONL ledger. Its exclusive-created genesis row pins the
reviewed campaign proposal, final campaign attestation, frozen request, rate snapshot, maximum attempts,
per-attempt cap, and aggregate cap. Every later row includes an integer sequence number, prior-row hash,
attempt count, cumulative reserved/booked cost, campaign disposition, and its own row hash. The validator must
enforce exact field sets and the entire chain on every invocation.

For attempt `N`, the runner must exclusive-create a fixed-name attempt lock for sequence `N` before credential
access. The lock pins the current state-row hash, attestation, request, sequence, and pre-request cumulative
reservation. A second process observing the same state can neither replace that lock nor select another
sequence; it stops locally. The matching receipt and completion-state row are also exclusive-created.

The ledger records a reservation row before credential access and a completion row after the attempt. Until a
reserved attempt has exactly one valid matching receipt and completion row, the campaign is incomplete and
must refuse every further invocation. A crash, interruption, or partial write therefore pauses permanently for
human review rather than silently consuming another slot.

The state validator must cross-link sequence, request hash, attempt-lock hash, receipt hash, request count,
cost, HTTP outcome, and campaign disposition. It must reject duplicate, skipped, reordered, missing,
extra-field, rehashed-tampered, or over-cap rows.

## 5. State transitions

The only permitted transitions are:

1. `authorized_not_started -> attempt_reserved`
2. `active_after_503 -> attempt_reserved`
3. `attempt_reserved -> active_after_503` only after exactly one request and a fully validated HTTP 503,
   provided fewer than 20 requests have been made
4. `attempt_reserved -> stopped_on_non_503` after exactly one request with any status other than 503
5. `attempt_reserved -> attempt_cap_reached` after the twentieth fully validated HTTP 503
6. `attempt_reserved -> stopped_local_or_transport_failure` for zero-request credential/local failure,
   transport ambiguity, invalid response, invalid evidence, or any unexpected exception

All stopped states are permanent for this campaign. HTTP 200 is a `stopped_on_non_503` success outcome with a
bounded key manifest; it does not stage, review, or approve a candidate and does not resume the pilot.

## 6. Required runner and receipt controls

The reviewed build must provide:

- a local-only `verify_only()` path that verifies both consumed attempts, all frozen artifacts, the campaign
  state schema, request construction, caps, and absence of network/credential/output side effects;
- strict response transport validation before inspecting status/body;
- the already-reviewed pure key-manifest extraction helper, unchanged unless separately reviewed;
- bounded non-200 message extraction, unchanged unless separately reviewed;
- exact receipt/state/lock schemas and secret scans before persistence;
- no raw exception text or traceback in persisted evidence or CLI output;
- a CLI that prints only disposition, numeric HTTP status when available, attempt number, campaign state, and
  receipt path—never captured message, manifest, response content, header values, or credential data;
- tests for caps, all state transitions, tampering after rehash, concurrency/duplicate invocation, incomplete
  attempts, zero-request failure, transport failure, 503 continuation, twentieth-503 termination, HTTP-200
  manifest termination, other-status termination, and the no-values boundary.

## 7. Authorization sequence

This proposal authorizes no implementation or execution by itself. The required sequence is:

1. Codex builds the local-only runner, state validator, attestation gate/template, and tests under the standing
   local-build permission.
2. Claude independently reads the source, recomputes hashes, runs tests, adversarially checks the state machine
   and value-discarding boundary, and confirms no real request occurs during review.
3. Fresh same-day dashboard, activity, model/rate, secret-store, consumed-evidence, campaign-cap, and evidence-
   boundary facts are confirmed directly with Johnny.
4. Codex drafts a campaign attestation with the campaign authorization field set to `false`; Claude verifies
   it.
5. Johnny separately and explicitly authorizes the bounded campaign: at most 20 manually initiated requests,
   10,680 USD millionths each, 213,600 aggregate, permanent stop on the first non-503 or the twentieth 503.
6. Codex finalizes the attestation; Claude independently verifies it.
7. Johnny alone runs each command manually. Neither AI touches the credential or triggers an invocation.
8. Both agents independently verify the terminal or cap-reaching evidence before any parser change or pilot
   decision.

No parser change, pilot resumption, candidate review, corpus mutation, staging, commit, or push is authorized
by this proposal.
