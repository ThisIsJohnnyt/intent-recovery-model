# Gate 5 corrected-provider-schema diagnostic proposal

**Date:** 2026-08-15  
**Status:** Local-only proposal. It authorizes no runner implementation, credential read, provider request,
spend, candidate generation/review, corpus mutation, staging, commit, or push.

## Purpose

The fifth one-request diagnostic captured Google's own non-200 error message. It established that
`additionalProperties` is unsupported inside `generationConfig.responseSchema` on this GenerateContent
surface. The provider-only schema has now removed exactly those two entries; the immutable Gate 2 local schema
and all historical receipts remain unchanged.

This proposal defines one possible sixth, diagnostic-only request to test that empirical correction. It does
not resume the 24-slot pilot. A 200 remains status evidence only: no candidate, prompt-derived output, or other
response content may be retained, reviewed, staged, or used to mutate the corpus.

## Frozen operation

After independent review of a dedicated new runner, a fresh same-day attestation, and Johnny's separate final
authorization, the runner may make exactly one operation:

- `POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent`;
- frozen slot 1 / mechanism `M01` only;
- corrected contract SHA-256 `4312688168dd349f04bf4307816bded0b98edc9c358873f57fb5e347d2fe431c`;
- corrected provider-schema SHA-256 `b069fbf77d439030ee018f2a773bff07c06f0ded53108d8b98819ee0ba656812`;
- corrected full request-envelope SHA-256 `8420c2d8360f4ffc96fb617dd8d4b081732cf2c87654a65d3ddc2ab8426297b4`;
- only `Content-Type` and `x-goog-api-key` header names, a 60-second timeout, no redirect, retry, model
  substitution, alternate endpoint, streaming, tool, cache, or URL-context feature.

Before credential read or transport, the runner must exclusive-create a new output directory and reserve
exactly **10,680 USD millionths ($0.01068)**. It stops after its one transport attempt regardless of outcome.
The reservation is a cap, not a final-billing assertion; delayed reconciliation remains unknown.

## Evidence boundary

The runner records numeric HTTP status, response byte count/hash, frozen hashes, transport metadata, cost state,
and final disposition. It never records raw response bytes, headers, prompt, candidate content, credential, or
sensitive account/billing identifiers.

For a non-200 response only, it may retain one `error.message` string exactly under the previously reviewed
control: strict UTF-8; duplicate-key-rejecting JSON; top-level `error` object with non-empty string `message`;
maximum 4,096 code points; then `gate2.contains_secret()` before storage. Any failure records a capture-state
with a null message. A 200 response body is neither decoded nor parsed and has a null message. A captured
message appears only in the hash-protected receipt, never stdout.

## Required sequence

1. Codex and Claude independently review this proposal, a dedicated new runner, its tests, and receipt rules.
2. Johnny confirms fresh same-day paid/prepay, balance, auto-reload, isolation, local encrypted-key custody,
   and no unexpected activity since the error-message-capture diagnostic.
3. A new secret-free attestation pins this proposal, the three corrected request artifacts, the rate snapshot,
   and prior error-message-capture receipt row
   `26c28a6a90761d68c7ce1b6d771387e9bc6e7ae0785d6028c6cdc2beb3cf6b20`.
4. Johnny separately authorizes exactly one request only after the attestation validates and both agents review
   it.
5. Johnny alone runs the command using the local credential.

Nothing here authorizes a runner, request, pilot resumption, retry, candidate handling, or any later action.
