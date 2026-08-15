# Gate 4 proposal: one zero-content model-metadata connectivity check

**Date:** 2026-08-14  
**Status:** Draft only. Prepared under Johnny's authorization to plan Gate 4; it does not authorize execution.  
**Authority:** `training/gemini_generator_readiness_package_chatgpt.md`, Sections 8, 9, 11, 15, 17, and 21.  
**Related setup attestation:** `gate3_setup_attestation_draft.json` (uncommitted and independently reviewed).

## 1. Narrow question

Can the locally stored, project-scoped key authenticate one request to the Gemini Developer API and return
metadata for the exact frozen capability model without transmitting any content or invoking inference?

This check does **not** test generation, prompt rendering, JSON schema enforcement, model output, quota
throughput, paid pilot readiness, candidate quality, or the `gemini-3.5-flash-lite` arm. It cannot promote
any candidate or authorize Gate 5.

## 2. Current official basis (recheck required immediately before execution)

- The Gemini REST reference documents `models.get` as `GET
  https://generativelanguage.googleapis.com/v1beta/{name=models/*}` with an empty request body, returning a
  `Model` metadata object. [Models API reference](https://ai.google.dev/api/models)
- The same reference documents `supportedGenerationMethods`, including `generateContent`, as model metadata.
  This permits the check to verify that the frozen generator API remains listed as supported without calling it.
- The current model catalogue lists `gemini-3.7-flash` as Stable and the current latest-model page says it is
  GA. [Models](https://ai.google.dev/gemini-api/docs/models), [latest-model guidance](https://ai.google.dev/gemini-api/docs/latest-model)
- Google documents `x-goog-api-key` as the Gemini API authentication header. [API reference](https://ai.google.dev/api)
- Current paid pricing is token/tool based. This proposal sends no request body, invokes no model generation or
  tool. Google does not document whether metadata-only endpoints are billed, so this proposal reserves a
  separate, explicit one-dollar ceiling rather than assuming zero cost. [Pricing](https://ai.google.dev/gemini-api/docs/pricing)

### Separate Gate 5 control drift discovered during this recheck

The Gate 2 mock-only `provider_contract.json` contains `thinking_level: minimal`. Current 3.7 guidance instead
describes supported thinking levels as `low`, `medium`, and `high`; it also recommends the newer Interactions
API for new development while stating that `generateContent` remains supported. [3.7 guidance](https://ai.google.dev/gemini-api/docs/latest-model), [Interactions migration](https://ai.google.dev/gemini-api/docs/migrate-to-interactions)

This proposal does not resolve, test, or modify that mismatch. It is a later Gate 5 blocker: the exact paid
request surface and control set must be redesigned, locally fixture-tested, independently verified, and
explicitly re-approved before any pilot request. The metadata check below tests only authenticated access and
the continued presence of `generateContent` in model metadata.

## 3. Proposed single request

Only the following provider request is permitted, after a separate explicit execution approval:

```text
GET https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash
Accept: application/json
x-goog-api-key: <key supplied only inside the local process>
```

Frozen transport rules:

- exactly one provider HTTP request; DNS/TLS setup is not a second provider request;
- request body is empty (`0` bytes); no prompt, system instruction, schema, card, tool, file, URL context,
  cache, history, repository material, private note, quarantine text, candidate, or corpus text is present;
- API key is header-only, never a URL query parameter, receipt field, exception string, shell history entry, or
  process argument;
- timeout: 30 seconds; HTTPS only; redirects disabled; streaming disabled; retries disabled; and
- no SDK, no inference endpoint, no model-content endpoint, and no fallback request.

### Monetary authority for a later execution decision

Johnny authorized a maximum total Gate 4 charge of **$1.00** (`1,000,000` integer millionths of USD) for this
single metadata request. This amount is reserved from the `$7.00` explicitly outside the frozen `$3.00` pilot
ceiling; it does not alter the `$3.00` pilot ceiling, 24-slot schedule, or any Gate 5 authority.

The `$1.00` is an authorization ceiling, not a provider-enforced limit. Before sending, the local ledger must
reserve the full `$1.00`. It may send one request only, then stop; delayed or unavailable billing evidence
must be recorded as unknown and cannot justify a second request. This monetary authority does **not** create
permission for retries, an alternate endpoint, a second model, inference, or any other extra operation.

The endpoint is deliberately distinct from the Gate 2 `generateContent` planning contract. Do not silently
rewrite that frozen contract on the strength of this metadata check. The separate current-control mismatch
described above means a later Gate 5 execution contract requires redesign and separately reviewed validation.

## 4. Exact success criteria

All conditions must hold:

1. HTTPS response is `200` and the request has no redirect.
2. Parsed JSON is a single metadata object, not an inference response.
3. `name` is exactly `models/gemini-3.7-flash`.
4. `supportedGenerationMethods` is present and contains exactly the required string `generateContent` among
   its documented values.
5. No model output, candidate, usage-token count, tool trace, or generated-content field is returned or
   accepted as success.
6. The response body is at most 256 KiB and parses without duplicate JSON keys.
7. The local runner's redaction scan finds no key-like string in console output, receipt, error data, or
   persisted artifact.
8. The execution-day review confirms the separate `$1.00` maximum authorization and reserves it before send.
   Any indication that the one metadata request could exceed that ceiling is a stop—not permission to
   substitute a minimal inference request. Absent or delayed billing evidence after the request is recorded as
   unknown and also stops all further activity.

## 5. Stop conditions and disposition

Stop immediately, write a redacted receipt, and make no replacement request on any of the following:

- key unavailable to the local user-run process, secret exposure, or any attempted secret logging;
- DNS/TLS/transport failure, timeout, redirect, HTTP status other than `200`, or any retry temptation;
- nonempty request body, endpoint/method/header drift, or a second provider request;
- model identity mismatch, absent `generateContent` support, malformed/oversized response, or provider error;
- any content-like request or response field, tool/caching/grounding behavior, usage-token field, or inference
  result;
- uncertain paid-tier routing, account state, model availability, or a billing indication above the `$1.00`
  ceiling; or
- any conflict with the Gate 3 attestation, model facts, or this proposal's hash.

Every non-success is `stopped` or `rejected`, never retried, regenerated, or replaced. A failure answers only
that this narrow check did not complete safely.

## 6. Execution receipt contract

Before a later execution decision, a minimal local runner and schema must be independently reviewed. Its single
receipt must contain only:

- proposal SHA-256; execution timestamp; and authorization statement;
- method, endpoint without credentials, request body byte count (`0`), header **names only**, timeout,
  redirect policy, and provider-request count;
- HTTP status, response byte count/SHA-256, provider request ID only if safely redacted, and no raw secret;
- selected metadata fields (`name`, `baseModelId`, `version`, `supportedGenerationMethods`) and their
  validation results;
- redaction-scan result, reported usage fields (expected absent), and local cost authorization/result in integer
  millionths of USD, including the full `$1.00` pre-request reservation and any later reconciliation state; and
- final disposition (`passed`, `stopped`, or `rejected`) plus the prior receipt-row hash.

It must not contain the API key, authorization-header value, secret-store path, account/project/billing/payment
identifier, full environment, raw error text before redaction, or any repository/private/quarantine/candidate
content.

## 7. Preconditions for a later execution decision

Before Johnny may consider authorizing this request, Codex and Claude must independently verify:

1. the proposal's final canonical hash and the locally implemented one-request runner;
2. the current official endpoint, authentication method, `gemini-3.7-flash` availability, and metadata shape;
3. paid/prepay routing, positive balance, auto-reload off, current account isolation, and no unexpected billing
   activity; and
4. that Johnny can run the check without exposing the key to either AI.

This proposal itself creates no API traffic, does not read the key, and does not authorize execution, staging,
commit, or push.
