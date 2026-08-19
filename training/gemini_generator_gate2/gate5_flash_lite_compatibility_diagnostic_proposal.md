# Gate 5 Flash-Lite compatibility diagnostic proposal

**Date:** 2026-08-16  
**Status:** Local-only proposal. It authorizes implementation and review only. It does not authorize a
credential read, provider request, spend, candidate generation or review, pilot resumption, corpus mutation,
staging, commit, or push.

## Purpose

The corrected GenerateContent request format has live HTTP-200 evidence for `gemini-3.7-flash`. The frozen
24-slot pilot also assigns 12 slots to `gemini-3.5-flash-lite`, but that model has not received a live request
using the corrected format. This proposal defines one status-only compatibility diagnostic for that second
model before Johnny decides whether to authorize a renewed 24-slot pilot.

The operation uses frozen slot 2 / mechanism `M01`, so the mechanism and prompt construction are the same as
the successful slot-1 diagnostic; the target model is the intentional difference. A 200 is transport and
request-format compatibility evidence only. No response content may be retained, decoded, parsed, reviewed,
quarantined, staged, or used to mutate the corpus.

## Frozen operation

Only after a dedicated runner and its tests are independently reviewed, a fresh same-day attestation
validates, and Johnny gives separate final execution authorization, the runner may make exactly one operation:

- `POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent`;
- frozen slot 2 / mechanism `M01` only;
- corrected provider contract SHA-256
  `4312688168dd349f04bf4307816bded0b98edc9c358873f57fb5e347d2fe431c`;
- corrected provider schema SHA-256
  `b069fbf77d439030ee018f2a773bff07c06f0ded53108d8b98819ee0ba656812`;
- request-body SHA-256 `f940966f6d94654787e7185b30cd98f9d82e0806b7bf6a3a4c12a8cf85747559`;
- full request-envelope SHA-256
  `afc687a97d24cec20c2cc11fafe8a9b5802fff438b9a7e72cd2084dcf86c7285`;
- only `Content-Type` and `x-goog-api-key` header names, a 60-second timeout, no redirect, retry, model
  substitution, alternate endpoint, streaming, tool, caching, grounding, or URL-context feature.

The runner must validate a fresh execution-day rate snapshot. Under the most recently verified rates, the
slot's worst-case reservation is **6,320 USD millionths ($0.00632)**. The fresh snapshot must produce a
reservation no greater than that fixed cap; a higher or malformed rate stops before credential access. The
runner must exclusive-create a new output directory and write its reservation before credential access or
transport. It stops after its one transport attempt regardless of outcome. The reservation is conservative
accounting, not a final-billing assertion.

## Evidence boundary

The receipt may record numeric HTTP status, response byte count and SHA-256, frozen artifact/request hashes,
transport metadata, cost state, redaction state, and final disposition. It must never record raw response
bytes, response headers, prompt text, candidate content, credential data, secret-store paths, or sensitive
account/project/billing/payment identifiers.

For a non-200 response only, the runner may retain one bounded `error.message` string under the already
reviewed control: strict UTF-8; duplicate-key-rejecting JSON; top-level `error` object with a non-empty string
`message`; no more than 4,096 code points; and `gate2.contains_secret()` must pass before storage. Any failure
records a capture-state and a null message. A 200 response body is never decoded or parsed and the stored
message is null. The captured message, if any, appears only in the hash-protected receipt and never on stdout.

## Required sequence

1. Codex and Claude independently review this proposal, the dedicated runner, its tests, receipt validator,
   attestation gate, and template.
2. On the actual execution date, pricing/model availability and the required account controls are rechecked;
   a fresh rate snapshot is created and independently reviewed.
3. Johnny directly confirms the same-day attestation facts, including balance, prepaid state, auto-reload off,
   billing isolation, credential custody, and no unexpected or other Gemini API activity since the successful
   `gemini-3.7-flash` diagnostic.
4. A new secret-free attestation pins this proposal, corrected contract/schema/request hashes, fresh rate
   snapshot, and successful prior diagnostic receipt row
   `5d9c434994855bb81eaeb1fcbc4fce1746cd99a08b19715cbb3266bfd9ac0336`.
5. Johnny separately authorizes exactly one Flash-Lite compatibility request only after the final attestation
   validates and both agents review it.
6. Johnny alone runs the command using the locally stored credential.

Nothing here authorizes a provider request, pilot resumption, retry, candidate handling, or any later action.
