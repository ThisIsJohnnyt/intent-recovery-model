# Gate 5 provider-schema type diagnostic proposal

**Date:** 2026-08-15  
**Status:** Local-only proposal. It authorizes no credential read, provider request, spend, candidate generation,
candidate review, corpus mutation, staging, commit, or push.

## Purpose and historical boundary

Three one-request Gate 5 attempts have returned HTTP 400 and are preserved as immutable evidence. The original
pilot and first diagnostic shared the same 708-byte response hash. The second diagnostic, after correcting the
GenerateContent field shape, returned a different 1026-byte response hash and thereby showed that the provider
processed further into the request.

The remaining locally verified correction is the provider-only schema's `type` casing: GenerateContent
`responseSchema` uses the uppercase Gemini/OpenAPI Type enum, while the immutable Gate 2 local parser schema
correctly remains standard lowercase JSON Schema. This proposal describes one new single-request diagnostic to
test only that provider-wire correction before a renewed pilot could possibly continue beyond slot 1.

The previous two diagnostic runners are permanently retired and cannot be reused. This proposal cannot reuse
their authority, output directories, reservation records, requests, or attestations.

## Frozen operation

After independent review, a fresh same-day attestation, and a separate direct Johnny authorization, a new
runner may perform exactly one operation:

- `POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent`
- slot 1 / mechanism `M01` only;
- corrected contract SHA-256
  `fecaa69bbea4a0e16749e7537b0ab1720cd6d386a19cd4736cfb436bcb11f96d`;
- provider-only uppercase-schema SHA-256
  `f42d19f841aa95949ce075cd0ec80c63f1a930fbb023c5f3eb4543d5cdc376c9`;
- canonical full request-envelope SHA-256
  `ab9757d003cf09dd06ecf55b435c10bd676932d92f7989417baa6d17f4f29379`;
- the fixed POST endpoint, exact M01 model, only `Content-Type` and `x-goog-api-key` header names, and a
  60-second non-streaming timeout.

There is no retry, redirect, alternate endpoint, model substitution, fallback, streaming, tool, cache, URL
context, or candidate extraction. The runner stops after its single transport attempt regardless of HTTP status.
A 200 result is status evidence only: it must not parse, retain, review, stage, or mutate any candidate or corpus
content, and it does not resume the 24-slot pilot.

## Cost and evidence controls

Before reading the local credential or opening transport, the runner must exclusive-create a new output directory
and a reservation record for exactly **10,680 USD millionths ($0.01068)**. The record is a worst-case reservation,
not a claim about final provider billing. Missing or delayed billing reconciliation remains unknown and must stop
any continuation.

The receipt may contain only safe metadata: proposal/contract/schema/attestation hashes; timestamp; method;
endpoint; request hash; header names; timeout; retry/redirect policy; request count; numeric HTTP status; response
byte count/hash; reservation/reconciliation state; redaction result; and final disposition/stop reason. It must
not persist or display response body/headers, error text, prompt, candidate, credential, secret-store path, or
account/project/billing/payment identifier.

## Required fresh attestation and review sequence

1. Codex and Claude independently review this proposal, a dedicated new runner, and its tests.
2. Johnny directly confirms same-day paid/prepay status, balance, auto-reload off, isolation, no unexpected
   activity since the second diagnostic, local encrypted key custody, and understanding that even a 200 is not a
   pilot resumption.
3. A new secret-free attestation pins this proposal, contract, provider-only schema, request envelope, execution-day
   rate snapshot, and the historical second-diagnostic receipt row
   `fc3897a6d4d3161405c4d5e453c25edc35578165a563a6806300dbaec8c96d9b`.
4. Johnny separately authorizes this exact one operation after the attestation validates and both agents review it.
5. Johnny alone runs the command using the local encrypted credential; neither AI accesses it.

Nothing here authorizes a pilot, retry, another diagnostic, candidate handling, or any action beyond the one
future provider-schema type diagnostic.
