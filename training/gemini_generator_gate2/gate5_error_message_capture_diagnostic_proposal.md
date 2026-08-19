# Gate 5 non-200 error-message-capture diagnostic proposal

**Date:** 2026-08-15  
**Status:** Local-only proposal. It authorizes no runner implementation, credential read, provider request,
spend, candidate generation, candidate review, corpus mutation, staging, commit, or push.

## 1. Purpose and evidence boundary

Four one-request Gate 5 attempts are immutable historical evidence. The original slot-1 pilot and first
diagnostic each returned HTTP 400 with the same 708-byte response hash. The corrected-wire-format diagnostic
then returned HTTP 400 with a distinct 1,026-byte response hash. The provider-schema-type diagnostic retry
also returned HTTP 400 with that same 1,026-byte hash
`100db9d01698cf4c34dcef54c24931364c73887ca3ec2e0a9fcb33b1b6d923e8`.

The byte-identical latter responses show that changing provider-schema type casing did not change this failure.
The existing receipts deliberately retained only status, byte count, and hash, so they do not reveal the
provider's diagnostic explanation. This proposal defines a possible next diagnostic that would retain one
strictly bounded piece of non-200 provider evidence: the JSON `error.message` string, if and only if it passes
the safeguards below.

The string is still untrusted provider data. It is not model output and no candidate, prompt, header, or raw
response is permitted to be retained. A 200 response must not be parsed for, displayed as, or recorded with any
response-derived text.

## 2. Frozen future operation

After independent review of a new dedicated runner, a fresh same-day attestation, and a separate explicit
authorization from Johnny, that runner may make exactly one request:

- `POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent`;
- slot 1 / mechanism `M01`, with the same corrected request contract and provider-only schema as the most
  recent diagnostic;
- contract SHA-256 `fecaa69bbea4a0e16749e7537b0ab1720cd6d386a19cd4736cfb436bcb11f96d`;
- provider-schema SHA-256 `f42d19f841aa95949ce075cd0ec80c63f1a930fbb023c5f3eb4543d5cdc376c9`;
- full request-envelope SHA-256 `ab9757d003cf09dd06ecf55b435c10bd676932d92f7989417baa6d17f4f29379`;
- only `Content-Type` and `x-goog-api-key` header names, a 60-second timeout, no redirect, no retry, no model
  substitution, no alternate endpoint, no streaming, no tool, no cache, and no URL-context feature.

The runner must stop unconditionally after the one transport attempt. A 200 does not resume the pilot, create
or retain a candidate, or authorize any later operation.

Before credential read or transport, it must exclusive-create a new output directory and a reservation for
exactly **10,680 USD millionths ($0.01068)**. This is a hard diagnostic cap and worst-case reservation, not a
claim about final provider billing. Any billing reconciliation remains unknown until separately observed.

## 3. Exact non-200 extraction rule

On a non-200 response only, after enforcing the existing response-size limit, a future runner may attempt this
local-only parsing sequence:

1. Decode the captured response bytes as strict UTF-8. Decode failure produces a receipt state of
   `unavailable_invalid_utf8`; no response text is retained or displayed.
2. Parse the resulting text as JSON with duplicate-key rejection. Syntax or duplicate-key failure produces,
   respectively, `unavailable_non_json` or `unavailable_ambiguous_json`; no response text is retained or
   displayed.
3. Accept only a top-level JSON object containing an `error` object whose `message` member is a non-empty
   string. Any other shape produces `unavailable_unexpected_error_shape`; no response text is retained or
   displayed. No other member of the error object is read into evidence.
4. Limit a candidate message to 4,096 Unicode code points. A longer value produces
   `unavailable_message_too_long`; it is not retained or displayed.
5. Run `gate2.contains_secret()` against the candidate value before it can be persisted or displayed. A match
   produces `withheld_secret_like`; the message itself is not retained or displayed.
6. Only a candidate that passes every preceding step may be stored as the receipt's
   `non_200_provider_error_message` string, with `error_message_capture_state: "captured"`.

The receipt must include `non_200_provider_error_message: null` and
`error_message_capture_state: "not_applicable_http_200"` for a 200 response; it must not decode or parse that
response body. For every non-captured non-200 outcome, the message field remains `null` and the capture-state
code records why. Thus parsing failure, an unexpected shape, a prohibited length, or a secret-like value leaves
auditable evidence without retaining the body or silently hiding the reason it was withheld.

## 4. Storage and display decision

The approved message, if any, is written only to the new, explicit receipt field above. It is **not printed to
stdout**. This keeps terminal history from becoming an uncontrolled extra copy and leaves one canonical,
hash-protected, reviewable record. The command's normal stdout remains a status/receipt-path summary and never
echoes provider text.

The receipt continues to retain the pre-existing safe metadata only: frozen hashes, timestamp, method,
endpoint, request hash, header names only, timeout/policy, request count, numeric HTTP status, response byte
count/hash, reservation and reconciliation state, redaction/capture result, disposition, and stop reason. It
must never contain raw body bytes, response headers, any error-object member other than a successfully captured
`error.message`, prompt text, candidate content, credential, secret-store path, or account/project/billing/
payment identifier.

## 5. Required sequence before any execution

1. Codex and Claude independently review this proposal, a new dedicated runner, its tests, and its strict
   receipt schema.
2. Johnny confirms fresh same-day billing/setup facts, local encrypted-key custody, no unexpected activity
   since the provider-schema diagnostic retry, and understanding of the one-message-only evidence boundary.
3. A new secret-free attestation pins this proposal, the request artifacts, the rate snapshot, and the prior
   provider-schema diagnostic receipt row
   `64147baa85ca4e81e2aec7b065b36d35c046ba2f6c7f52f70e7312390eaeb981`.
4. Johnny separately authorizes exactly one capped request after the attestation and runner are independently
   verified.
5. Johnny alone runs the resulting command with the local credential. Neither AI accesses the credential or
   triggers the provider request.

Nothing in this proposal authorizes a runner, an actual diagnostic, a retry, pilot resumption, candidate
handling, or any other provider operation.
