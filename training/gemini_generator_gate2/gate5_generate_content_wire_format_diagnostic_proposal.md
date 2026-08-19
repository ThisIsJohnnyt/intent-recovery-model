# Gate 5 corrected GenerateContent wire-format diagnostic proposal

**Date:** 2026-08-15  
**Status:** Local-only proposal. It authorizes no credential read, provider request, spend, candidate generation,
candidate review, corpus mutation, staging, commit, or push.

## 1. Purpose and historical boundary

The original Gate 5 slot-1 pilot request and its separate first diagnostic both returned HTTP 400 with the
same 708-byte response hash (`7be3c566d0ff2f9618c256da836b51f78762f944071519bee0757b25d0895038`). The
first diagnostic receipt is preserved as row hash
`1264813444d9e846078bf766c0ddd46d63bfb3e4459bc58b32d24080eac7b86c`; neither it nor the original pilot
evidence may be modified.

The cause is now locally corrected: the GenerateContent request must use the flat
`generationConfig.responseMimeType` and `generationConfig.responseSchema` fields, rather than the rejected
`responseFormat.text` nesting. This proposal describes one new diagnostic solely to establish whether that
wire-format correction changes the provider result before any new paid-pilot decision.

The previously consumed diagnostic remains permanently retired. This proposal is a new artifact and cannot
reuse its authority, attestation, output directory, reservation, receipt, or request hash.

## 2. Frozen operation

If separately authorized after a fresh attestation and independent code review, the runner may perform exactly
one direct request:

- `POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent`
- schedule slot 1 / mechanism `M01` only
- exactly the corrected contract SHA-256:
  `5c47896310f9145ea62ec3fcea08d10038ff06f6125c632740222bd3d5f430ab`
- exactly this canonical full request-envelope SHA-256:
  `0b0d3dfb09f428f6c447e3b97407f6aa966f6519f7ba2962a4cd15432b626e7b`
- the only header names: `Content-Type` and `x-goog-api-key`; the key value stays inside Johnny's local
  process and is never persisted or displayed
- empty retry budget: no semantic retry, transport retry, redirect, fallback, model substitution, streaming,
  tools, caching, URL context, or alternate endpoint.

The process must stop immediately after that one transport attempt. A 200 response is still not a pilot
resumption: it must not parse, retain, review, stage, or mutate any candidate or corpus content.

## 3. Monetary boundary

Before reading the local credential or opening transport, the runner must exclusive-create a new output
directory and a reservation record for **10,680 USD millionths ($0.01068)**. That is the slot's existing
worst-case reservation at the verified execution-day rates. The reservation is a hard cap for this diagnostic,
not a billing assertion. Actual provider billing may be delayed or unknown and must remain recorded as such.

Any indication that the cap could be exceeded, an output-path collision, an attestation failure, a credential
failure, or a transport/response error stops the process without retry.

## 4. Evidence boundary

The one receipt may contain only:

- proposal, corrected-contract, and attestation hashes;
- timestamp, method, endpoint, request-envelope hash, header names only, timeout, redirect/retry policy, and
  provider request count;
- numeric HTTP status, response byte count, and response SHA-256;
- reservation/cost reconciliation state, redaction result, and final disposition/stop reason.

It must not contain a response body, response headers, prompt, candidate text, parsed candidate, API key,
credential target, secret-store path, account/project/billing/payment identifier, or any provider content.

## 5. Required sequence before any execution

1. Codex and Claude independently review this proposal, the dedicated new runner, its tests, and its receipt
   schema against the corrected GenerateContent reference.
2. Johnny directly confirms fresh same-day paid/prepay, balance, auto-reload, isolation, no unexpected
   activity, local-key custody, and no additional Gemini/API activity beyond the two recorded failed attempts.
3. A new diagnostic attestation pins this proposal, the corrected contract, current rate snapshot, and the two
   historical failed-attempt records. It must be secret-free and validate locally.
4. Johnny separately and explicitly authorizes this exact one request only after reviewing that attestation.
5. Johnny alone runs the command using the local credential; neither AI accesses it or sends the request.

Nothing in this proposal authorizes a retry, a 24-slot pilot resumption, another diagnostic, or any action
beyond the single future operation above.
