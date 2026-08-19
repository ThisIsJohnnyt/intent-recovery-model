# Gate 5 one-request HTTP-status diagnostic proposal

**Date:** 2026-08-15  
**Status:** Local proposal only. It does not authorize credential access, a provider request, spend, candidate
generation, candidate review, corpus mutation, staging, commit, or push.

## 1. Why this exists

Johnny personally ran the authorized 24-slot Gate 5 pilot once. Its first request stopped on a non-200
response. The completed run directory is immutable evidence: one request, no candidate staged, and a
conservative 10,680 USD-millionth reservation booked. Its receipt records a response-body hash but, by the
then-frozen receipt shape, not the numeric HTTP status. Consequently the cause cannot be distinguished from
the preserved evidence alone.

The reviewed runner now captures a numeric `http_status` in *future* receipts without storing response body
or headers. This proposal narrowly tests that diagnostic improvement before any decision about a resumed
pilot. It is not a retry of the 24-slot pilot and it cannot continue to slot 2.

## 2. Exact proposed operation

- At most one synchronous HTTPS `POST` to the existing Gemini Developer API `generateContent` endpoint.
- Exact request: the frozen schedule's slot 1 (`gemini-3.7-flash`, mechanism `M01`), with the same locally
  derived request-envelope hash (method, endpoint, header names, and body; no header value) recorded in the completed first run:
  `02007b81e50d846c5a6cf3d321650c8a6c4c83ec60647d346d8d73c6450e3a36`.
- Exact controls remain: one candidate, low thinking, 2,048 maximum output tokens, current structured-output
  shape, non-streaming, no tools, no cache, no URL context, no retries, no redirects, no model substitution,
  and no fallback endpoint.
- Credential use is local only: read from Windows Credential Manager by Johnny's process; the value appears
  only in the request header and is neither printed nor written.
- A fresh dedicated diagnostic runner must hard-stop after this one POST regardless of HTTP status. It may not
  call the 24-slot pilot runner or share its output directory.

## 3. Narrow cost authority proposed for a later decision

At the independently verified execution-day rate snapshot, the exact slot's worst-case reservation is
10,680 USD millionths ($0.01068). A future execution authorization should cap the diagnostic at that amount.
It must explicitly state that this is a new, single diagnostic request; it does not authorize a 24-slot retry,
any further request, or reuse of the prior execution attestation.

## 4. Required preconditions before any diagnostic execution

1. A fresh same-day diagnostic attestation records the previous one-request failure, no subsequent Gemini/API
   activity, current paid/prepay balance and auto-reload state, isolation, key custody, and direct diagnostic
   authorization.
2. Codex and Claude independently verify the proposal, diagnostic runner, tests, and fresh attestation.
3. Johnny separately authorizes this exact one request and runs the command himself.
4. The new output directory does not exist before the process begins and is reserved before credential access.

## 5. Receipt and stop contract

The diagnostic receipt may persist only: contract/rate/attestation hashes; request-body hash; method and
endpoint path; header names (not values); request count; numeric HTTP status; response byte count and
SHA-256; reservation/cost state; stop reason; and a redaction result. It must not persist response body,
response headers, candidate content, prompt text, API key, credential label/path, or billing/account/project
identifier.

Regardless of 200/non-200, body shape, parseability, or transport outcome, the diagnostic stops after its
single attempt. A 200 only means the later governance decision can consider a refreshed pilot proposal; it
does not stage or review the generated candidate and does not resume the original pilot.

## 6. Non-authorization boundary

This document neither changes nor repairs the completed first run. It does not authorize a second provider
request, a resumed 24-slot pilot, candidate use, corpus mutation, Git activity, or any provider-facing action.
