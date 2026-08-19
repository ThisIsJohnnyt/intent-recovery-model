# Gate 5 V9: full-schedule continue-past-collision campaign proposal

**Date:** 2026-08-17
**Status:** Proposal only. This document authorizes no V9 engine, gate, attestation, campaign state, credential
access, provider request, spend, candidate handling, corpus mutation, staging, commit, or push.

## 1. Authority and origin

Built under the temporary Johnny+Claude working mode (Codex's usage resetting 2026-08-23 09:49; construction
and review both fall on Claude for the duration). Design confirmed directly with Johnny in conversation before
any code was written: scope of "continue past" (all three collision-family reasons), retry semantics (5
attempts per card, 503 only), cost bounds, live visibility, and the review/attestation cycle were each
explicitly confirmed.

## 2. Why V9, and what it changes from V8

The corrected V8 (`gate5_paid_pilot_retry_campaign_v8_2026-08-17_r2`) proved both its own defect fixes in real
use, then immediately went permanently terminal on its first real collision (mechanism M02) — exactly as
every version through V8 is designed to do: any protected collision is unconditionally hard-terminal for the
whole campaign. That design has correctly caught every real content problem this project has ever hit. It
also means answering "does this happen across M02-M12, not just M01/M02" would otherwise take up to eleven
separate authorization cycles, one collision at a time.

V9 changes exactly one thing: **what happens after a protected-collision-family outcome.** Everything else —
the schedule, the prompt, the collision screen itself, the zero-content diagnostic-evidence design, the hard
stop on any other exceptional outcome — is unchanged from the corrected V8 build.

## 3. Reused, unchanged from the corrected V8 build

- Schedule: `schedule_v8_m02_start.json` (hash `a272c5e9...`) — the same 22 retained slots, M02-M12 twice
  each, source slots 3-24, campaign sequence 1-22. V9 does not get its own schedule file; it re-derives and
  pins this exact one, the same way V8 re-derived V7's terminal evidence.
- Prompt: the same V7 diversified system instruction and `v7_prompt.build_request()` — no second wording
  change, avoiding confounding this diagnostic with anything else.
- Historical baseline: the corrected V8's real terminal evidence (1 attempt, real collision on M02,
  $241,280 aggregate, itself built on V7's $234,960) — re-derived and pinned, not trusted from prose.
- The collision screen itself, the four raw-diagnostic pause codes, the private raw-diagnostic module, and
  the zero-content evidence design for both collision and schema diagnostics: unchanged.

## 4. What's new: continue-past-collision, bounded 503 retry, single full-schedule pass

**Continue-past scope**: all three collision-family screen outcomes — `protected_collision`, `pilot_duplicate`,
`prompt_imitation` — record their existing zero-content diagnostic evidence exactly as before, then the run
advances to the next card instead of stopping. Confirmed with Johnny explicitly.

**Everything else remains hard-terminal for the whole run**: HTTP errors other than a retryable 503,
`schema_invalid` (and the other three pause-whitelist codes), `secret_exposure`, `provider_usage_exceeds_frozen_cap`,
`pilot_ceiling_exceeded`, `reconciliation_stop_before_request`, diagnostic-persistence failures, and any
unexpected local error. Confirmed with Johnny explicitly — the only stop condition being relaxed is the
collision family.

**Bounded 503 retry, per card, not global**: up to 5 real attempts on the *same* card before giving up on it
and moving to the next. Every real attempt — including retries — gets its own real, hash-chained
receipt/cost row; nothing is silent or hidden behind a single row. If a card exhausts all 5 attempts still
503ing, it's recorded as `unexpected_http_status_retries_exhausted` in the rejection ledger and the run moves
to the next card. Confirmed with Johnny explicitly, including this exhaustion behavior.

**Single full-schedule pass, not a 15-attempt campaign**: V9 has no multi-invocation "attempt N of 15"
structure. One authorized, attested execution processes the schedule from card 1 forward until either it
completes all 22 cards or a genuinely hard-terminal condition stops it early. There is no concept of a second
V9 attempt on the same campaign directory — a natural-completion or hard-stop is equally final.

**Live visibility**: the runner prints one JSON line per card as it resolves (whether accepted, collision,
retries-exhausted, or the final hard stop), not just a single summary after the whole run. Confirmed with
Johnny explicitly, since a human is no longer confirming between every individual real result the way V1-V8
required.

## 5. The sequence-numbering fix this design requires

`gate5_output_collision_evidence.build_row()` and `gate5_schema_conformance_evidence.build_row()` — shared
modules every version depends on — each internally require the row's `sequence` field to equal both its own
position within that specific evidence list and the row's own `schedule_slot` value. That holds trivially in
every version through V8, where a real `execute_pilot()` call has only ever produced at most one row of any
given type before stopping. V9 can produce several diagnostics scattered non-consecutively across up to 22
cards in a single run, which breaks that assumption the moment it's exercised — this is the same class of
chain-mismatch Claude found and set aside as "a separate, pre-existing, out-of-scope path" while building
V8's test coverage; V9 is precisely the design that exercises it for real.

**Fix (V9-local only, the shared modules are not touched):** V9's engine keeps five independent, densely-
incrementing counters instead of one shared per-slot `sequence` — one for the real-request-level ledgers
(receipts, cost; these are 1:1 with every real HTTP request including retries, so no sparsity issue) and one
each for rejections, collision diagnostics, schema diagnostics, and accepted candidates (each incrementing
only when that specific kind of row actually gets produced). Receipts/cost rows keep an accurate
`schedule_slot` (the real card position, 1-22) since they're dense by construction. Collision/schema
diagnostic rows use their own dense counter as both `sequence` and `schedule_slot` to satisfy the shared
modules' internal self-consistency check — `mechanism_id`/`model`, recorded independently in every row
regardless, remain the reliable "which card" identifier; a diagnostic's `schedule_slot` in V9 should be read
as "the Nth diagnostic of that type in this run," not the source schedule position. This will be called out
explicitly in every diagnostic-related test and in the runner's own output.

## 6. Cost arithmetic

At the same verified rate snapshot, per-card reservation is unchanged (187,000 USD-millionths for one pass
through all 22 slots exactly once, matching V8). With up to 5 attempts per card in the worst case:

`22 slots x 5 attempts x average per-card rate = 935,000` USD-millionths worst case for one full V9 run,
**up from V8's 187,000 for a single pass** — a real 5x increase in the worst-case reservation, though still
trivial against the ceilings.

Proposed maximum aggregate: `241,280 (V8 historical, incl. all prior versions) + 935,000 = 1,176,280`
USD-millionths ($1.17628), carried forward against the same $5,000,000 hard ceiling / $3,750,000
reconciliation stop as every version since V6. A future V9 build must recompute this from its own bound
execution-day rate snapshot and real schedule; this arithmetic is not a substitute for that check.

## 7. Explicit non-goals

V9 does not relax the collision screen itself, does not accept a colliding candidate, does not persist
candidate or reference text beyond the existing zero-content diagnostic design, does not retry any outcome
other than a genuine transport-level 503, does not retry past 5 attempts on a card, does not skip a card, does
not reorder the schedule, does not weaken schema/secret/cost-ceiling handling, and does not become a
resumable multi-attempt campaign — one authorized execution is the whole thing.

## 8. Review and authorization sequence

Same sequence as every prior version, with Claude filling both the build and review role for the duration of
the temporary working mode:

1. Claude independently reviews this proposal (self-review, disclosed as such).
2. Claude builds the local V9 package (engine, gate, runner, attestation template, focused tests).
3. Claude independently reviews the build from scratch, same rigor as reviewing Codex's work — recompute
   every hash, run the real tests, reproduce the sequence-numbering fix's correctness directly rather than
   trust it by construction.
4. Johnny re-confirms fresh same-day rate/account/activity/model facts.
5. Claude prepares an execution-disabled draft attestation and validates it.
6. Johnny separately decides whether to authorize V9 execution.
7. Claude validates the final one-field authorization change.
8. Only then may Johnny personally run a fully substituted command.

No step authorizes the next one automatically.
