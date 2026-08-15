# Gate 5 local redesign draft: common, current-control GenerateContent contract

**Date:** 2026-08-14  
**Status:** Local-only design and fixture work. It does not authorize a key read, network request, model call,
spend, candidate review, corpus mutation, staging, commit, or push.

## Why this draft exists

The committed Gate 2 mock contract uses `thinking_level: minimal`. That representation is deliberately
untouched: it is part of the completed local-only Gate 2 artifact, not a paid request implementation. The
Gate 4 preparation identified that it cannot safely remain the common paid-pilot control for the exact
`gemini-3.7-flash` arm. A two-arm comparison must not silently give each model a different thinking policy.

This draft therefore preserves the frozen experiment while changing only the future, provisional request
surface:

- the same two exact model IDs: `gemini-3.7-flash` and `gemini-3.5-flash-lite`;
- the same twelve mechanism cards and interleaved 24-slot schedule, with 12 slots per arm;
- the same one semantic attempt per model/card pair, 4,000 input-token ceiling, 2,048 output-token ceiling,
  and $3.00 pilot ceiling; and
- common low thinking, one candidate, non-streaming synchronous JSON output, and no tools or external
  context.

## Provisional wire contract

`gate5_provider_contract_draft.json` and `gate5_redesign.py` construct a no-secret, inspectable REST payload
with the following material shape:

```text
POST /v1beta/models/{exact-model}:generateContent
Content-Type: application/json
x-goog-api-key: supplied only inside a future local process

{
  "systemInstruction": { ... },
  "contents": [{"role": "user", "parts": [{"text": "..."}]}],
  "generationConfig": {
    "responseFormat": {"text": {"mimeType": "application/json", "schema": { ... frozen schema ... }}},
    "candidateCount": 1,
    "thinkingConfig": {"thinkingLevel": "low"},
    "maxOutputTokens": 2048
  }
}
```

The local validator rejects legacy `minimal` thinking, model substitution, streaming, retries, redirects,
extra candidates, tool/caching/URL/file controls, sampling parameters, local credential fields, and any
secret-like value. It has no HTTP library, SDK, socket import, or execution command. Its all-24-slot test
only derives local request-body hashes from the existing frozen prompt, schema, cards, and schedule.

## Current official basis, not yet an execution-day attestation

The current GenerateContent reference documents camelCase REST fields including `generationConfig`,
`thinkingConfig.thinkingLevel`, `candidateCount`, `maxOutputTokens`, and JSON response-format controls. Its
ThinkingLevel enum includes `LOW`, and current examples use a low-thinking configuration. The current official
structured-output REST example uses `responseFormat.text.mimeType` and `responseFormat.text.schema`. This draft
follows that current documented REST shape while still requiring an execution-day exact-reference/model-compatibility
check before final freezing.
The current structured-output guide still emphasizes that application-side validation remains required.

Sources: [GenerateContent REST reference](https://ai.google.dev/api/generate-content), [thinking controls](https://ai.google.dev/gemini-api/docs/generate-content/thinking), and [structured outputs](https://ai.google.dev/gemini-api/docs/generate-content/structured-output).

These are design inputs only. Before any paid pilot decision, both agents must recheck the exact model IDs,
the exact GenerateContent field names, the low-thinking compatibility of **both** arms, structured-output
support, current rates, and the paid/billing state. If either arm does not support the common contract, the
pilot stops; no per-model fallback or substitute control is permitted.

## Remaining local work before a Gate 5 decision

1. Freeze this draft only after joint provider-surface review; retain the old Gate 2 mock contract as history.
2. Add mock response fixtures for current REST response/usage shapes and update the runner/receipt parser
   without enabling real transport.
3. Recalculate the 24-slot worst-case reservation with execution-day official rates and explicitly include
   billable thinking tokens.
4. Build a pre-execution attestation and an append-only paid-pilot ledger that cannot start while Gate 4
   reconciliation is unresolved unless Johnny separately decides the recorded unknown state is acceptable.
5. Have Codex and Claude independently validate all local tests and the final request contract, then ask
   Johnny for a new, explicit Gate 5 execution decision.
