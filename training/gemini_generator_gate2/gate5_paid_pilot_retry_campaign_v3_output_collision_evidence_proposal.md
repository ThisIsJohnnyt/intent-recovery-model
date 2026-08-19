# Gate 5 paid-pilot retry campaign v3 with output-collision evidence

**Date:** 2026-08-17  
**Status:** Proposal only; preparation authorized by Johnny, execution separately unauthorized  
**Scope:** A fresh, bounded successor to the terminal v2 campaign

## 1. Purpose

The v2 paid-pilot retry campaign is terminal after its first real attempt stopped on
`proposed_output:output.narrative:protected_collision`. That attempt correctly rejected the candidate, wrote no
candidate to quarantine, booked 10,680 USD-millionths, and preserved only the response hash and bare collision
field path. The raw response was never retained, so the historical collision remains undiagnosable.

The independently approved output-collision evidence build can safely retain the protected comparator label,
fixed collision kind, and numeric similarity score for a future collision without retaining candidate or
comparator text. This proposal defines a fresh v3 campaign that uses that reviewed capability and starts from
the independently re-derived terminal v2 component chain.

## 2. Authority boundary

Johnny's statement, "I authorize. Let's keep moving," authorizes preparation of this fresh attempt package.
It does not authorize:

- creation or use of campaign state;
- credential access;
- a provider request, candidate generation, or spend;
- candidate review, promotion, staging, corpus mutation, commit, or push.

After proposal review and a local-only build, a fresh same-day attestation and Johnny's separate, explicit v3
campaign execution authorization are still mandatory. Johnny alone runs every real invocation.

## 3. Immutable v2 terminal baseline

The existing v2 verifier must re-derive the following state directly from the historical files before v3 may
reserve anything:

- terminal state: `stopped_nonretryable_outcome`;
- v2 attempts reserved: `1`;
- historical component count: `6`;
- historical actual cost: `53,400` USD-millionths;
- historical component-manifest SHA-256:
  `568ec00a1a7ad2d9c73ed91a6800f676e1ece4ff0bdd950540503c0531434b80`;
- terminal component: `campaign_v2_attempt_001`, cost `10,680`, disposition
  `proposed_output:output.narrative:protected_collision`;
- candidate quarantine count: `0`.

The new gate must pin and re-verify these canonical-LF file hashes:

| v2 artifact | SHA-256 |
|---|---|
| final attestation | `b1e70f5d177c262932e9018b6352483974401397004011e652ac5850669a3e58` |
| terminal campaign state | `842e12e5d77e6329e4b0da4e565bae2dfbbfdaaf210056a19f8810fcba0c75b8` |
| attempt 1 lock | `3b63928fce7ed78d0f6f0021ce9ca0ead903f8f274294cd10b27ec745ea893e5` |
| attempt 1 completion | `383638a9eab8aa7ae5df981603e927af4effc81c216d07171441fb18c70888cd` |
| pilot reservation | `34383815f8d080f9a605ce232497f861510291961738dbe662f15e4857bfa1ef` |
| request receipts | `2d37648f9c64f0fe2a1467ffe4d9b577d9c99341ab64002fc7a311ce129d7cbe` |
| rejection ledger | `b4daa64e3061cddb17d3e49642e29321e9e67477ef6fc307ce6c95482a8ab646` |
| cost ledger | `48c7fbbb28d7c4a11e18a5f3a79468f333c0848ca45793020a0d19f5bcd2826f` |
| empty candidate quarantine | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| run summary | `5f4583791f91e2d65f6a492a542c59b36802dc1af96c21574d87f4950c8b32ca` |

No v1, v2, earlier pilot, diagnostic, receipt, ledger, state, completion, reservation, quarantine, or
attestation file may be edited or reinterpreted. V3 uses a new directory, files, hashes, gate, and attestation.

## 4. Reviewed capture-build pins

V3 execution eligibility must pin the independently approved build:

- approved proposal:
  `dc5cf11c125d9618cafee13fd972ec41994679f4cd9c9afb6968dbb3f88c178c`;
- `gate2.py` with additive structured collision reasons:
  `65e5808fb6891f70a7e15e13eaf3360d81d2dffd35fc120c37dc3cdad7bf6391`;
- strict output-collision formatter/validator:
  `f58e189e3cb28d7437758ff497801cefc1a37eaa9cb82488f4992094b20de00a`;
- integrated paid-pilot runner:
  `1e751fbed0f33fbae2caa0bc6a657d7135e55bb836233bfa5ac636013e169787`;
- focused test suite:
  `0aa639782bced398778b1747b531b43516f96a2a2b98b41bd34dc3d26d80993f`.

Any drift stops before campaign-state creation, credential access, or network use.

## 5. Bounds and cost controls

The earlier bounded-campaign lineage allowed ten total campaign attempts. V1 reserved two attempts and v2
reserved one, so v3 proposes at most **seven** further attempts. Attempts are not silently restored merely
because a prior attempt was zero-cost or stopped locally.

- historical booked cost entering v3: `53,400` USD-millionths (`$0.0534`);
- maximum v3 attempts: `7`;
- worst-case reservation per full 24-slot attempt: `204,000` USD-millionths (`$0.204`), recomputed from the
  execution-day rate snapshot and frozen token caps before each attempt;
- worst-case aggregate after seven v3 attempts: `53,400 + 7 * 204,000 = 1,481,400`
  USD-millionths (`$1.4814`);
- existing reconciliation stop remains `2,250,000` USD-millionths;
- existing hard pilot ceiling remains `3,000,000` USD-millionths.

The campaign bound does not replace either existing monetary control. Every attempt must use the live,
independently verified component total for reservation, reconciliation, cost-ledger, and hard-ceiling math.
The frozen attested pre-v3 baseline is `53,400`; it is used only to prove what Johnny reviewed and must never
substitute for the growing live total in monetary calculations.

## 6. Manual campaign state machine

Johnny manually invokes one command at a time. There is no timer, background loop, automatic retry, provider
retry, redirect, model substitution, or hidden request.

Each invocation:

1. verifies the terminal v2 evidence and all v3 pins;
2. validates the fresh v3 attestation;
3. re-derives the full historical component chain and live monetary total;
4. exclusive-creates one attempt lock and a brand-new output directory before credential access;
5. runs at most one fixed 24-slot paid-pilot attempt with the existing per-slot reservation and stop controls;
6. appends one completion and one campaign-state transition from the real output evidence.

The campaign remains active only after a clean transient HTTP 503 outcome with:

- exactly one request and one receipt/cost/rejection row;
- zero quarantined candidates;
- zero output-collision diagnostic rows;
- a valid conservative booked cost;
- no ambiguity or incomplete evidence.

Every other result is terminal for review, including:

- any protected collision, now with exactly one validated output-collision diagnostic row;
- any generated/quarantined candidate;
- any non-503 HTTP status;
- parser, screening, usage, cost, local, secret-scan, or evidence-validation failure;
- `output_collision_diagnostic_withheld`;
- `output_collision_diagnostic_persistence_failed`;
- a completed 24-slot run;
- the seventh v3 attempt.

An incomplete reservation or crash remains blocking. Recovery, if ever needed, must derive the completion only
from already-written evidence and requires its own reviewed command surface; it may never re-send a request.

## 7. Future output-collision evidence contract

Every new attempt directory reserves `output_collision_diagnostics.jsonl` empty before credential access.

For a protected-collision stop:

- the diagnostic ledger must contain exactly one strict, hash-chained row;
- the rejection row must link its `output_collision_diagnostic_row_hash` to that row;
- both must agree on sequence, request hash, raw-response hash, and reason code;
- the diagnostic may retain only the approved reference label, fixed collision-kind enum, bounded finite score,
  field path, fixed identifiers/hashes, and false safety flags;
- no candidate/comparator/prompt text, snippets, tokens, n-grams, signatures, qualitative shared features,
  response body/headers, or raw errors may appear;
- candidate quarantine remains empty and candidate review remains false.

For a non-protected rejection, the diagnostic ledger is empty and the rejection diagnostic link is null.

If diagnostic persistence fails after a real request, receipt/rejection/cost evidence must already exist,
the summary must explicitly state `output_collision_diagnostic_persistence_failed`, no next request may occur,
and the campaign terminates for manual review. It must not pretend the cross-link is complete.

## 8. Fresh execution-day requirements

Before any v3 execution authorization is requested:

- obtain a fresh same-day official rate snapshot; yesterday's snapshot must remain stale and untouched;
- recheck both exact models, `generateContent`, common `low` thinking, structured output, and the corrected
  provider request/schema surface;
- reconfirm paid/prepay state, current balance, auto-reload off, billing isolation, no unexpected activity,
  no other Gemini/API activity, and key retention only in Windows Credential Manager;
- validate all static and historical hashes;
- independently review the v3 gate, template, runner, state validator, recovery behavior, and tests;
- draft the attestation with `v3_campaign_execution_authorized_by_johnny: false`;
- obtain Johnny's separate explicit bounded-v3 execution authorization, then finalize and independently verify
  the attestation before giving Johnny a command.

## 9. Required local build and tests

The local-only build must include a new v3 gate, attestation template, campaign runner/state validator, and
tests. It may reuse the approved paid-pilot engine and collision module only through their pinned hashes.

Tests must prove:

1. terminal v2 evidence and all ten listed v2 file hashes re-derive exactly, with no historical write;
2. the six-component `53,400` baseline and component-manifest hash are recomputed, never trusted from a scalar;
3. frozen attested baseline remains `53,400` while every monetary calculation uses the growing live total;
4. seven-attempt and `1,481,400` boundaries have no off-by-one path;
5. concurrency allows exactly one reservation for a sequence;
6. incomplete/crashed evidence blocks another request and recovery cannot invoke transport;
7. clean zero-candidate 503 is the only nonterminal result;
8. protected collision validates the diagnostic/rejection cross-link and is terminal;
9. canary candidate and protected text are absent from every diagnostic and other non-quarantine evidence file;
10. missing/orphan/duplicate/tampered diagnostics and spoofed labels terminate fail-closed;
11. diagnostic I/O failure preserves core evidence and is terminal;
12. non-protected rejection requires an empty diagnostic ledger and null link;
13. old v1/v2 evidence remains valid under its own verifier without the new field;
14. old attestations fail the new v3 gate;
15. relative CLI paths, exact cost boundaries, secret scans, focused tests, and the available package suite are
    exercised without credential, network, or provider use;
16. `--verify-only` reports the v2 baseline, seven-attempt bound, worst-case total, all build pins, and
    `network_used: false`, `credential_read: false`, `file_output_created: false`.

## 10. Sequence

1. Codex drafts this proposal under Johnny's preparation authorization.
2. Claude independently verifies its evidence pins, arithmetic, privacy boundary, and state-machine design.
3. If approved, Codex builds the v3 local-only gate/template/runner/tests.
4. Claude independently reads, hashes, tests, and adversarially verifies the build.
5. Fresh execution-day facts and rates are gathered and a still-unauthorized attestation draft is reviewed.
6. Johnny separately decides whether to authorize the bounded v3 campaign.
7. Only after final attestation review does Johnny personally run any real command.

