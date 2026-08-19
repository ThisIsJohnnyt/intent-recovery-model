# Gate 5 response-shape key-manifest diagnostic proposal

**Date:** 2026-08-16  
**Status:** Local-only proposal. It authorizes no credential read, provider request, spend, retry, pilot
resumption, candidate review or retention, corpus mutation, staging, commit, or push.

## Incident and purpose

The independently reviewed August 16 paid-pilot run sent frozen slot 1 / mechanism M01 to
`gemini-3.7-flash` and received HTTP 200, then stopped fail-closed with
`provider_response_shape_invalid`. The existing parser requires the sole returned content part to contain
exactly `{"text"}`. Current official Google documentation says a Gemini 3 non-streaming response may attach
`thoughtSignature` metadata to its final content part. That is a strong root-cause lead, but the failed run
correctly retained only the raw-response hash, not the body, so the actual field set cannot be recovered.

This proposal defines one diagnostic request that repeats the exact known request and persists only a bounded
manifest of JSON object key names and structural counts. It never persists response field values, candidate
text, structured output, a thought signature, headers, or raw response bytes. Its purpose is to identify the
exact response-envelope mismatch before any parser change or renewed pilot decision.

## Frozen evidence and operation

The diagnostic must pin:

- failed pilot summary file SHA-256
  `627ba8dfba9410a1201907f7d5eb2cce69b2d9f41111cd8c4e84f540f1c16050`;
- failed request-receipt row SHA-256
  `3db5178d10e4c5bfb556711bade9a25381ffffc5b63b78a9a3bef450546e3ee2`;
- failed raw-response SHA-256
  `e349b43a5baa75dd3ce1890a2fea8973c7bdd8ec7bb9d40a04886c401a862d35`;
- final August 16 pilot attestation SHA-256
  `a504ca4117a02613894f4244d9345c66cfc91a2b55489b2546a1bfcc0105673f`;
- corrected provider contract SHA-256
  `4312688168dd349f04bf4307816bded0b98edc9c358873f57fb5e347d2fe431c`;
- corrected provider schema SHA-256
  `b069fbf77d439030ee018f2a773bff07c06f0ded53108d8b98819ee0ba656812`;
- exact slot-1 request-envelope SHA-256
  `8420c2d8360f4ffc96fb617dd8d4b081732cf2c87654a65d3ddc2ab8426297b4`;
- August 16 rate snapshot SHA-256
  `f24991917538caf8bcf4340f18ef0a78cbdeadce6e14845b5fe28e69720ddca2`.

Only after a dedicated runner, tests, attestation gate, and receipt rules are independently reviewed; fresh
same-day facts are confirmed; and Johnny gives separate final authorization, the runner may make exactly one
`POST` to
`https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent` using frozen slot
1/M01. Its fixed maximum reservation is **10,680 USD millionths ($0.01068)**. It uses only `Content-Type` and
`x-goog-api-key`, a 60-second timeout, and no redirect, retry, alternate endpoint, model substitution,
streaming, tools, caching, grounding, or URL context. It stops after the single transport attempt regardless
of outcome and cannot continue to slot 2 or resume the pilot.

## HTTP-200 key-manifest boundary

For HTTP 200 only, the runner may decode the body in local process memory under all of these controls:

1. body size no greater than 1 MiB;
2. strict UTF-8;
3. duplicate JSON keys rejected;
4. no existing candidate/usage parser is called and no field value is serialized, displayed, logged, or
   returned;
5. every retained key name must be a string matching `^[A-Za-z][A-Za-z0-9_]{0,63}$`;
6. every key list is sorted, unique, and capped by an exact manifest schema;
7. the completed manifest must pass `gate2.contains_secret()` before receipt storage.

The only permitted manifest is:

- sorted top-level response key names;
- `candidate_count` as a nonnegative integer capped at 4;
- for each candidate, sorted candidate key names;
- for each candidate content object, sorted content key names;
- for each candidate, `part_count` capped at 8 and sorted key names for each part;
- sorted `usageMetadata` key names when that object exists;
- sorted `modelStatus` key names when that object exists.

No string, number, boolean, object, or array value from any provider field may be retained. In particular,
the values of `text`, `thoughtSignature`, token counts, identifiers, versions, finish reasons, safety fields,
and status fields are prohibited. The receipt records the raw body's byte count and SHA-256 separately, never
the bytes themselves. Any malformed or out-of-bounds structure produces a static capture-state and null
manifest.

For non-200 only, the runner may use the already reviewed bounded `error.message` capture control; it must not
attempt the key manifest. Stdout contains only disposition, numeric status, and receipt path—never the
manifest, error message, or any response-derived key/value.

## Expected parser correction after evidence

If the manifest confirms the sole text part has exactly `text` plus `thoughtSignature`, the narrow production
change should be:

- require `text`;
- allow only optional `thoughtSignature` at that part level;
- require the signature value to be a non-empty JSON string within a fixed length bound, then discard it;
- continue rejecting function calls, thought-summary parts, media, executable code/results, tools, grounding,
  URL context, unknown fields, multiple candidates, unexpected part counts, or any other expansion;
- add a mock fixture and tests for accepted bounded signature metadata and rejected unknown/non-string/empty/
  oversized signature fields.

`gate5_provider_response_schema.json` describes the JSON document inside the text value, not the outer Gemini
`Part` envelope. It should not be changed merely to represent `thoughtSignature`. The response-envelope parser
and mock provider fixture are the relevant correction surfaces. If the manifest shows a different shape, no
parser change is authorized until that exact shape is separately reviewed.

## Required sequence

1. Codex and Claude independently review this proposal and the incident pins.
2. A dedicated runner, receipt validator, attestation gate/template, and tests are built and independently
   reviewed without credential or network access.
3. Johnny confirms fresh same-day account/activity facts and explicitly acknowledges that the process will
   inspect the response structure in memory but persist key names only.
4. A fresh secret-free attestation initially leaves the one-request authorization false and is independently
   reviewed.
5. Johnny separately authorizes exactly one key-manifest diagnostic request, capped at $0.01068.
6. Johnny alone runs the command using the local credential.
7. Both agents independently verify the receipt before any parser fix or renewed pilot proposal.

The existing `gate5_pilot_run_2026-08-16` directory is immutable evidence and must remain untouched. Any
future diagnostic uses a brand-new output directory. Nothing in this proposal authorizes that diagnostic,
any parser change, or any pilot retry.
