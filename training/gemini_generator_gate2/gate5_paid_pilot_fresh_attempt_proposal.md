# Gate 5 fresh paid-pilot attempt proposal after live response-shape validation

**Date:** 2026-08-16  
**Status:** Proposal only. Johnny authorized beginning a fresh, separately reviewed paid-pilot attempt using
the corrected parser. This document does not itself authorize credential access, a provider request, spend,
candidate handling, pilot execution, staging, commit, or push.

## 1. Purpose and boundary

The first real Gate 5 pilot stopped safely after slot 1 because the local parser rejected a real HTTP-200
response before retaining a candidate. A later bounded key-manifest campaign obtained a real HTTP-200 response
for the same frozen slot-1 request and persisted only key names/counts. That evidence confirmed two parser
corrections: an optional `thoughtSignature` beside `text`, and an optional omitted `thoughtsTokenCount` that
defaults to zero.

The corrected parser and tests have now been independently reviewed against the real manifest. This proposal
defines a **fresh** execution of the same fixed 24-slot schedule. It does not resume, append to, or modify the
failed pilot directory. The previous pilot and diagnostic campaign remain immutable historical evidence.

The fresh run begins at schedule slot 1 and may send at most the existing 24 requests. The earlier failed
slot-1 request produced no accepted candidate and does not satisfy any slot in the fresh run.

## 2. Historical evidence pins

Prior failed pilot:

- run-summary file SHA-256: `627ba8dfba9410a1201907f7d5eb2cce69b2d9f41111cd8c4e84f540f1c16050`
- request-receipts file SHA-256: `b30e21d29868db74d9cee9719f2f8c1f002cc40ff1f5557224e658e3861e62c4`
- cost-ledger file SHA-256: `0c39db795f4ff4a75a199af8b0f8a11ffe08663d67a8148015dd8bd0a47703ae`
- rejection-ledger file SHA-256: `3b1cec5c6c37d0fce25b533a9ba890d3d44d7acc53e3bef9683ec13438634423`
- receipt row SHA-256: `3db5178d10e4c5bfb556711bade9a25381ffffc5b63b78a9a3bef450546e3ee2`
- raw-response SHA-256: `e349b43a5baa75dd3ce1890a2fea8973c7bdd8ec7bb9d40a04886c401a862d35`
- internally verified summary SHA-256:
  `d79003f8ef0b334cc4e2792a0c8095c08e2e8330b6cae781c40cc2bc4103b6ed`
- provider requests: 1
- candidates retained: 0
- conservatively booked pilot cost: 10,680 USD millionths

Successful terminal response-shape campaign:

- receipt file SHA-256: `9110781bdd431e66b13d465551893c8be7402c916afda285ff06d082d0b4ac22`
- receipt row SHA-256: `2f4068298f4fbd65b586fb09584fbc733009bda77571d176c06d4029357732f0`
- campaign-state file SHA-256: `aa8f77a2c3dd2d2c22105470219bf5d6a676afc4861e2511c19e780d61a26a78`
- attempt-lock file SHA-256: `b3e3693d64a14dff8bd9bb12a0fbadb0455416ec8581aabcab2c03c7c0f88175`
- HTTP status: 200
- terminal campaign state: `stopped_on_non_503`
- provider requests: 1
- real manifest: one candidate, one content part, part keys exactly `text` and `thoughtSignature`, usage keys
  without `thoughtsTokenCount`
- raw response values, candidate text, signature value, and token values: never persisted

Corrected local parser:

- `gate5_mock_runner.py` SHA-256:
  `aef817fa39e72591be92a27cfb577746605e004b8e2394f7b6ee3f2d50bae14e`
- optional signature: bounded non-empty string, validated then discarded
- omitted thoughts count: validated default of integer zero
- full package tests after correction: 100/100 pass

## 3. Frozen execution inputs

The fresh attempt keeps the already-reviewed execution surface unchanged:

- provider contract SHA-256:
  `4312688168dd349f04bf4307816bded0b98edc9c358873f57fb5e347d2fe431c`
- provider schema SHA-256:
  `b069fbf77d439030ee018f2a773bff07c06f0ded53108d8b98819ee0ba656812`
- schedule SHA-256: `aff503c2dce8428cf83d6e25fa1e06e07d2ce9fedd06cc805f186b1be3e9b87a`
- execution-day rate snapshot SHA-256:
  `f24991917538caf8bcf4340f18ef0a78cbdeadce6e14845b5fe28e69720ddca2`
- models: exactly `gemini-3.7-flash` and `gemini-3.5-flash-lite`
- slots: exactly 24, in the frozen schedule order
- one candidate per request; nonstreaming; no tools; no caching; low thinking; structured JSON output
- no redirects, retries, model substitution, fallback, automatic resume, candidate promotion, or corpus mutation

The existing independently verified HTTP-200 model-compatibility receipts remain required. The new build must
additionally pin the successful response-shape campaign and corrected parser so the fresh execution gate cannot
pass against the older rejecting parser.

## 4. Cost accounting

The frozen pilot ceiling remains 3,000,000 USD millionths ($3.00), and the reconciliation stop remains
2,250,000 USD millionths ($2.25).

The prior failed pilot's conservatively booked 10,680 is not erased or reset. The fresh runner must initialize
its **aggregate pilot cost** at 10,680 before considering slot 1. Every pre-request reservation check must use:

`prior pilot booked cost + fresh-run cumulative cost + next worst-case reservation`

The resulting value must remain at or below the $2.25 reconciliation stop before any request. Every hard-
ceiling check and final summary must likewise include the 10,680 historical pilot amount. Diagnostic and
compatibility-check costs previously authorized from the separate non-pilot budget remain outside this pilot
ledger, consistent with their recorded scope.

The fresh run's own cost ledger still records each new slot's reservation and actual/conservative cost. The
reservation record and final summary must separately expose the pinned historical 10,680, fresh-run cumulative
cost, and aggregate pilot cost so no reader can mistake a restart for a budget reset.

## 5. Required build hardening

Before execution, the paid-pilot runner, execution gate/template, and tests must be updated so that:

1. the final attestation and reservation pin this proposal, corrected-parser hash, successful campaign receipt
   file/row, campaign-state file, and prior failed-pilot evidence;
2. local verification reruns the campaign receipt and campaign-state validators and confirms the campaign is
   terminal HTTP 200 with exactly the reviewed key manifest;
3. the parser module hash is checked immediately before output-directory creation and credential access;
4. the prior 10,680 pilot cost participates in every reconciliation-stop and hard-ceiling calculation;
5. the reservation and summary distinguish historical, fresh-run, and aggregate pilot costs;
6. the new output directory must not exist and is created before credential access;
7. every sent request still leaves receipt, rejection, cost, and quarantine evidence under the existing
   append-only controls, including on failure;
8. a parser mismatch, campaign-evidence mismatch, historical-evidence mismatch, stale rate snapshot, invalid
   attestation, or output collision stops before credential access and network use.

Tests must prove the historical cost cannot be reset or omitted, the campaign/parser pins are enforced,
the corrected live-observed response shape reaches local candidate screening, and all prior safety and
evidence controls remain intact.

## 6. Execution and review sequence

1. Codex builds the local-only hardening described above under the standing local-build permission.
2. Claude independently reads all changes, recomputes hashes, runs the complete suite, verifies the immutable
   historical evidence, and adversarially tests the cost carry-forward and campaign/parser pins.
3. Fresh same-day dashboard, balance, activity, model/rate, secret-store, historical-evidence, corrected-parser,
   and fixed-schedule facts are confirmed directly with Johnny.
4. Codex drafts a fresh-attempt attestation with the actual execution trigger set to `false`; Claude verifies
   it.
5. Johnny gives the final explicit execution authorization after the reviewed build and attestation are in
   hand. His authorization to begin this fresh, separately reviewed attempt does not bypass that final gate.
6. Codex finalizes the attestation; Claude verifies it.
7. Johnny alone runs the command using the key from Windows Credential Manager. Neither AI touches the
   credential or triggers execution.
8. Both agents independently verify the resulting reservation, ledgers, summary, quarantine, cost, and stop
   state before any candidate review, corpus decision, commit, or push.

No provider request, candidate review, corpus mutation, staging, commit, or push is authorized by this
proposal.
