# Gate 5 paid-pilot retry campaign V5 scope note

**Date:** 2026-08-17  
**Status:** Local build scope only. This note does not authorize credential access, a provider request, spend, candidate handling, campaign-state creation, staging, commit, or push.

## Why V5 exists

The independently reviewed V4 campaign terminated after its first reserved attempt because the manually entered command retained an unfilled credential-target placeholder. The paid-pilot engine stopped at local credential lookup before transport. The sealed V4 evidence records zero provider requests, zero booked cost for that attempt, no candidate handling, and a terminal `zero_request_local_failure` disposition.

This was an operator-command error, not a defect in V4's schema-conformance evidence, four-code pause whitelist, review-artifact validation, transport, parser, collision screening, or monetary controls. Those reviewed controls remain unchanged in V5.

## Frozen V4 terminal baseline

V5 must re-derive V4 through V4's own `load_and_verify_campaign()` and pin its final attestation, terminal state ledger, attempt lock, completion record, and every attempt-output artifact. The required terminal facts are:

- campaign state: `stopped_nonretryable_outcome`;
- V4 attempts reserved: 1;
- historical components: 10;
- historical component-manifest SHA-256: `5294a3c58730769560b9f60e6982a3addda1b35606a5884cc5a1885c1ff3fa75`;
- historical booked cost: 85,440 USD-millionths;
- terminal component row SHA-256: `86e883d6f6c91b135c934a10ee306241f12a38d4be345a9277c67244fc94be24`;
- terminal disposition: `zero_request_local_failure`;
- V4 terminal attempt booked cost: 0.

V4 remains immutable and terminal. V5 creates new state only in a new V5 campaign directory.

## Attempt and monetary bounds

The original lineage permits ten campaign attempts. V1 consumed 2, V2 consumed 1, V3 consumed 3, and V4 consumed 1, including zero-request attempts. V5 therefore permits at most 3 attempts.

The frozen full-attempt worst-case reservation remains 204,000 USD-millionths. The independently recomputed V5 worst-case aggregate is:

`85,440 + (3 * 204,000) = 697,440 USD-millionths ($0.69744)`

The existing reconciliation stop (2,250,000 USD-millionths) and hard pilot ceiling (3,000,000 USD-millionths) remain unchanged. All actual monetary decisions use the live, independently verified component chain, never a stored scalar.

## Unchanged V4 controls

V5 copies the reviewed V4 wrapper behavior without widening it:

- the same content-free schema-conformance diagnostics;
- the same protected-collision diagnostic and no-candidate-text boundary;
- the same pause whitelist: `schema_invalid`, `extra_key`, `finish_reason_invalid`, `size_limit_failed`;
- every unrecognized or other outcome is hard-terminal;
- the same one-use, hash-linked pause-review artifact and exclusive review lock;
- the same same-day review and immediate-next-local-calendar-day refresh logic;
- the same exact rate-tuple equality, fresh dashboard/provider facts, and fail-closed N+2 behavior;
- the same append-only evidence, attempt reservation before credential access, incomplete-attempt recovery, concurrency exclusion, and no-retry transport behavior.

## Required build and review

Build a new V5 attestation gate/template, pause-review template, campaign runner/state validator, and focused tests. Tests must prove at least:

- V4 terminal evidence re-derives exactly and remains byte-identical;
- 10-component / 85,440 baseline and three-attempt / 697,440 bounds;
- V5 state is separate and V4 cannot be resurrected;
- old V4 attestations fail the V5 gate;
- attempt-cap, live-cost, pause whitelist, review, next-day, recovery, concurrency, and diagnostic privacy controls remain unchanged;
- a zero-request credential failure is evidenced, costs zero, and is terminal;
- verify-only performs no credential, network, or output action.

A fresh V5 attestation must begin with execution authorization false and receive independent review. Johnny must separately authorize V5 execution and personally run every real command. Nothing in this scope note authorizes execution.
