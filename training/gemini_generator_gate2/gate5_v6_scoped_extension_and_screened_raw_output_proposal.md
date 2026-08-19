# Gate 5 V6: scoped extension and screened raw-output diagnostic proposal

**Date:** 2026-08-17  
**Status:** Proposal only. This document authorizes no implementation, credential access, provider request, spend, campaign state, parser change, candidate handling, staging, commit, or push.

## 1. Authority boundary

The original ten-attempt retry lineage is complete and immutable: V1 used 2 attempts, V2 used 1, V3 used 3, V4 used 1, and V5 used 3. V6 is therefore not a continuation implicitly permitted by the prior lineage.

Johnny has made a new, explicit decision to consider a separate V6 extension. The requested V6 parameters are a fresh, version-scoped maximum of 15 attempts, a $5.00 ceiling, a $3.75 reconciliation stop, and a narrowly screened local raw-output diagnostic for only the four already pause-eligible format outcomes. That decision permits this proposal only. It does not authorize building, a V6 attestation, a campaign, a credential read, a provider request, or spend.

Every real V6 invocation would still require the same later sequence: reviewed local build, fresh same-day facts, an execution-unauthorized attestation draft, independent review, Johnny's separate V6 authorization, and Johnny personally running a fully substituted command.

## 2. Re-derived V5 baseline and arithmetic

The V6 build must independently call V5's own `load_and_verify_campaign()` rather than trust these stated values. Read-only re-derivation performed for this proposal produced:

| Fact | Re-derived value |
| --- | --- |
| V5 terminal state | `attempt_cap_reached` |
| V5 attempts reserved | 3 |
| Historical component count | 13 |
| Historical component manifest | `42aa31db451e7e9f9d191f2ad88d18227730ba14d4b78c4da86ca3c17cac8e87` |
| Historical booked cost | 117,480 USD-millionths ($0.11748) |
| Final V5 state-row hash | `e7b0d8880a51e6a8512a61e89f39b0784ecad3f164b5acb626948ab787df2bad` |
| Final V5 component-row hash | `a219a3ecb8cf24a564681ac51edda802eda0050dc97ed24ef793013cba0fd29d` |
| Final component disposition | `unexpected_http_status` |
| Final component booked cost | 10,680 USD-millionths |

Using the verified 2026-08-17 rate snapshot and the frozen 24-slot schedule, the per-full-attempt worst-case reservation remains 204,000 USD-millionths. The independent V6 upper bound is:

`117,480 + (15 × 204,000) = 3,177,480 USD-millionths ($3.17748)`

This is below the proposed V6 reconciliation stop of 3,750,000 and the V6 hard ceiling of 5,000,000. The build must recompute this from its rate snapshot and schedule; it must not trust the prose or an attestation scalar.

## 3. Version-scoped money controls

### 3.1 No mutation of shared historical constants

`gate5_paid_pilot_runner.py` currently defines shared `RECONCILIATION_STOP = 2,250,000` and `PILOT_CEILING = 3,000,000`. V1 through V5 validate their recorded attestations against those live constants. Changing either would make historical attestations fail on re-validation even though their recorded events never changed.

V6 must not modify those shared constants or change the meaning of any V1-V5 attestation, runner, state, receipt, ledger, or verifier.

### 3.2 Dedicated V6 engine and controls

The build should add a dedicated local `gate5_paid_pilot_v6_engine.py`, rather than modifying the shared paid-pilot engine. It may reuse read-only helpers for schedule loading, request construction, canonical JSON, pricing, response validation, collision screening, and secret detection. Its execution function must take an immutable V6 controls object:

```python
V6_PILOT_CEILING = 5_000_000
V6_RECONCILIATION_STOP = 3_750_000
```

V6 pre-request reservation uses the live component-chain total plus the candidate reservation against `V6_RECONCILIATION_STOP`. Actual booked cost uses the same live chain and is hard-stopped if it exceeds `V6_PILOT_CEILING`. The V6 receipt, cost row, reservation, summary, completion, campaign state, review artifact, and attestation each record those V6 values explicitly.

The V6 gate—not the shared engine constants—validates V6's `$5.00` / `$3.75` attestation fields. V1-V5 remain byte-for-byte and behaviorally untouched. The V6 build must include a regression test that V1-V5 validators still accept their own historical records after V6 modules are imported and exercised locally.

## 4. Outcome policy stays restrictive

V6 keeps the existing positive pause whitelist exactly:

- `schema_invalid`
- `extra_key`
- `finish_reason_invalid`
- `size_limit_failed`

These may pause only after all normal evidence is written and only when the specific pause requirements are met. The current one-use review artifact, same-day and immediate-next-local-calendar-day refresh, exact rate-tuple equality, and fresh account/provider-fact rules carry forward unchanged.

All other outcomes remain hard-terminal. This includes `protected_collision`, `prompt_imitation`, `pilot_duplicate`, `secret_exposure`, diagnostic withholding/persistence failures, provider/auth/usage errors, unexpected local errors, and any unknown future code. V6 must not introduce an “always continue” path.

## 5. Additive screened raw-output diagnostic

### 5.1 Purpose and boundary

The existing `schema_conformance_diagnostics.jsonl` remains unchanged and content-free. V6 adds an optional, local-only raw candidate-text record to help a human diagnose a pause-eligible format failure without rebuilding a one-off diagnostic for each schema class.

It is not a general response archive. It never persists response headers, credentials, API keys, signatures, thought signatures, tool data, error bodies, unrecognized Part fields, candidate text from a hard-tier failure, or model output that cannot be fully screened.

The only potentially persisted content is the model's extracted candidate text from an HTTP 200 response that produced one of the four whitelist codes and passed every gate below. The original outer response body remains hash-only as it is today.

### 5.2 Eligibility pipeline

Raw candidate text may be written only when every condition below holds, in order:

1. The status is 200 and the final stop code is one of the four pause-eligible codes.
2. The outer response can be decoded as strict UTF-8 JSON with duplicate-key rejection and remains within the existing provider response size cap.
3. The extractor inspects the actual candidate `finishReason` before any text can be retained. The capture allow-list is exactly `STOP` and `MAX_TOKENS`; every absent, unknown, or other finish reason is denied. This is deliberately narrower than the pause-code bucket: current official GenerateContent documentation lists `SAFETY`, `RECITATION`, `LANGUAGE`, `OTHER`, `BLOCKLIST`, `PROHIBITED_CONTENT`, `SPII`, `MALFORMED_FUNCTION_CALL`, `IMAGE_SAFETY`, and `IMAGE_PROHIBITED_CONTENT` in addition to `STOP` and `MAX_TOKENS`. A provider safety/content signal is never overridden by local collision or secret checks. `OTHER` is also denied because the provider defines it as unknown, not structural.
4. The extractor withholds if any candidate `safetyRatings` entry is explicitly blocked or if `citationMetadata` is present. The API documents `citationMetadata` as potentially carrying recitation information for returned text. These fields are controls only; none of their values are persisted.
5. A dedicated extractor can identify all candidate `text` values needed to build a complete screenable projection using only known candidate paths. It never copies or persists any non-`text` Part value. Any unknown field, missing textual surface, malformed structure, over-cap text, or ambiguous projection withholds capture.
6. The projection is screened through the existing `gate2.screen_candidate()` machinery, including protected references, prompt references, and earlier-candidate checks. A collision, imitation, duplicate, or any other fatal screen result withholds capture.
7. `gate2.contains_secret()` is run over the exact extracted text that would be written. Any hit withholds capture.
8. The extracted UTF-8 text is capped at 65,536 bytes. A cap exceedance withholds capture.
9. Only after all preceding checks pass may the private raw record be serialized and hash-linked.

The key rule is conservative completeness: if the extractor cannot prove it screened every text value that it would persist, it persists nothing. That means many structurally malformed `schema_invalid`, `extra_key`, and `size_limit_failed` cases will deliberately fall back to the existing structured-only diagnostic. This is expected, safe, and still provides the pause record.

### 5.3 Private storage layout and git exclusion

The V6 runner must require its campaign root to be a package-local directory named `gate5_paid_pilot_retry_campaign_v6_YYYY-MM-DD`. Its private diagnostics live under that root:

```text
training/gemini_generator_gate2/
  gate5_paid_pilot_retry_campaign_v6_YYYY-MM-DD/
    private_raw_diagnostics/
      raw_output_diagnostics.jsonl
      attempt_001_raw_output.json
      attempt_002_raw_output.json
      ...
```

The implementation must add this exact `.gitignore` pattern before any V6 execution is eligible:

```gitignore
/training/gemini_generator_gate2/gate5_paid_pilot_retry_campaign_v6_*/private_raw_diagnostics/
```

`attempt_NNN_raw_output.json` is exclusive-created and contains only a fixed schema, the permitted stop code, request/response hashes, screening-result metadata, extracted candidate text, its text hash, a prior private-ledger hash, and a record hash. `raw_output_diagnostics.jsonl` is append-only and hash-chained; every row binds the attempt number, core rejection-row hash, private-record hash, extracted-text hash, and prior row hash. The normal campaign/core evidence stores only a capture state and private-record hash—not raw text.

The directory is deliberately local and gitignored, but it is still tamper-evident while present. A later V6 review must verify the private ledger and its cross-links before treating a saved raw diagnostic as evidence.

### 5.4 Withheld and write-failure behavior

The core rejection row and summary must record a fixed, content-free capture state such as:

- `not_eligible_stop_code`
- `withheld_unparseable_or_unscreenable`
- `withheld_provider_finish_reason`
- `withheld_provider_safety_or_citation_signal`
- `withheld_protected_or_duplicate_collision`
- `withheld_secret_like_content`
- `withheld_size_limit`
- `persisted`
- `write_failed`

No raw value, parser message, unknown key name, snippet, or secret scan match is placed in those core rows.

If private serialization or append fails after an eligible write was attempted, the core receipt/rejection/cost evidence must still record `write_failed`; the attempt then stops with the new hard-terminal `raw_output_diagnostic_persistence_failed`. It must not pause and resume without the requested diagnostic, and it must never silently treat the failed write as `persisted` or `withheld`.

## 6. V6 lineage and state

V6 is a fresh campaign directory and re-derives V5 through V5's own verifier. It must pin, at minimum, the V5 final attestation, terminal campaign state, all three locks and completions, all per-attempt output artifacts, final state row, final component row, and the 13-component manifest. The following top-level V5 hashes are proposal anchors for that work:

| V5 artifact | SHA-256 |
| --- | --- |
| Final attestation | `1365385852a3182a73e133680625d49842fe71d6e85ff2f8caf37d65d2047bf3` |
| Campaign state ledger | `300431df17fc7a70cf310afc8f8df3046a2310698809ba6cb618b5f1d19e9b7c` |
| Attempt 1 lock / completion | `7ff8216f78035c718762199365269d4ac0b3a90a2eb68e13f41afa5c53aef0e4` / `139cf084d55abdcbd3d13b9daad20c94e5f6cebcb15e8f9c701127a9f5ade864` |
| Attempt 2 lock / completion | `8e0cd93c4ad3831b405a397b2e950efb6fdfb231234e70c78f2cfac5f86ac360` / `84f60291578e8ae6c62f3ad6f3259c9c786db9b926dfa69dbb52cb0c8d452c94` |
| Attempt 3 lock / completion | `b3f80e5030174971b45128202787f504257e428ecd15d9d336203511084d388a` / `0cf51c580cd18cd17b50720fd93eee28ba35c04b5a11729b587211161e0d5bbd` |

V6 attempt numbering begins at 1 while its component sequence begins after the verified 13-component history. Every V6 monetary calculation uses the growing live component chain. A V6 frozen attestation baseline can detect review drift but can never replace that live total.

## 7. Required local tests before any attestation

The build must include and pass tests for:

1. re-derivation of V5 terminal evidence, 13 components, 117,480 cost, and V5 immutability;
2. V6 scoped controls: exact $3.75 pre-request boundary, exact $5 hard boundary, 15-attempt cap, 3,177,480 worst-case arithmetic, and all shared V1-V5 constants untouched;
3. a V6 engine receiving scoped controls while V1-V5 validators remain able to verify their own historical records;
4. each whitelist code and every non-whitelist code, with unknown codes hard-terminal;
5. raw capture for an eligible schema-format failure with a fully screenable, non-secret, non-colliding candidate text;
6. withholding for malformed/ambiguous extraction, unknown textual field, size cap, duplicate JSON key, secret-like content, protected collision, prompt imitation, duplicate candidate, every hard-tier code, and each non-allow-listed `finishReason`;
7. a fabricated `finishReason: "SAFETY"` response that otherwise passes local screening: private capture must be withheld with `withheld_provider_finish_reason`; likewise test `RECITATION`, `SPII`, `BLOCKLIST`, `PROHIBITED_CONTENT`, `OTHER`, missing reason, and a blocked `safetyRatings` or present `citationMetadata` control;
8. proof that thought signatures, tool fields, headers, credentials, provider safety/citation metadata, and outer response bodies never appear in private or core diagnostics;
9. private JSON and ledger hash-chain/cross-link tampering; core evidence must remain content-free;
10. private write failure: core rows show `write_failed`, no raw text survives, and the outcome is hard-terminal;
11. concurrency, incomplete-attempt recovery without transport, repeated pauses, review-lock reuse, same-day review, exact next-day refresh, N+2 failure, rate drift, missing facts, and insufficient balance;
12. no network, credential, or output side effects from `--verify-only`;
13. a full secret scan and `git check-ignore` confirmation for the private diagnostic path.

## 8. Deliberate non-goals

This proposal does not retroactively recover any old raw response. It does not relax collision thresholds, permit raw collision data, save arbitrary provider failures, change the fixed 24-slot schedule, add streaming/tools/caching/retries/substitutions, alter old shared ceiling constants, or make V6 execution automatic.

## 9. Next step

Claude independently reviews this proposal. Only if approved may the V6 local build begin. The later V6 attestation and every real attempt remain separately gated.
