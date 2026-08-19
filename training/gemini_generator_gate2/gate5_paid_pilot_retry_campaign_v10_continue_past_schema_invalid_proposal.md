# Gate 5 Paid Pilot — V10: Continue Past `schema_invalid`

## Origin

V9's real full-schedule run (2026-08-17) proved the continue-past-collision mechanism works in real
production (card 1: real `protected_collision` on `source_input`, correctly continued), but the run's
practical value — visibility into what happens across all 22 cards — was cut short at 2/22 cards when card 2
hit a genuine `schema_invalid` (real HTTP 200, `source_input` restated at 78 words against an 80-word floor),
which stayed hard-terminal per V9's original scope and stopped the whole run.

Johnny reviewed the full hard-terminal set with Claude before deciding anything, and explicitly agreed to move
only `schema_invalid` into the continue-past set. Nothing else changes.

## Scope: what moves, what stays

**Moves to continue-past**: `schema_invalid` — but only the case where a schema-conformance diagnostic row was
successfully built. If diagnostic-evidence construction itself fails, the outcome remains
`schema_conformance_diagnostic_withheld`, which is **not** added to continue-past — an evidence-integrity
failure is a different kind of problem than a content-quality miss, and V9's `output_collision_diagnostic_
withheld` was never continue-past-eligible for the identical reason. This mirrors that precedent exactly.

**Stays hard-terminal, unchanged, explicitly reconfirmed rather than silently carried forward**:
- `secret_exposure` — direct precedent from the V6-era design discussion: collision/secret/security stays
  permanently zero-content and hard-terminal, full stop, regardless of any other scope change.
- `schema_conformance_diagnostic_withheld` / `output_collision_diagnostic_withheld` — evidence-integrity
  failures, not content signals; continuing here means silently accepting a gap in the record.
- Cost-tier stops (`pilot_ceiling_exceeded`, `reconciliation_stop_before_request`) — these describe aggregate
  spend, not a single card's outcome; "continue past" doesn't apply to them by nature.
- Every structural/integrity failure (attestation mismatch, credential failure, schedule tamper, quarantine
  manifest drift, output-path problems, `unexpected_local_error`, etc.) — these mean the run's own foundation
  can't be trusted for *any* card, not just the current one.

## What does not change

- Same 22-slot M02–M12 schedule and prompt, reused entirely unchanged from V8/V9 (re-derived and pinned, not
  trusted from a constant).
- Same per-card 503 retry budget (up to 5 real attempts, every attempt its own real ledger row).
- Same collision-family continue-past reasons (`protected_collision`, `pilot_duplicate`, `prompt_imitation`)
  and the same retries-exhausted continue-past case.
- Same zero-content-persistence discipline on every diagnostic row.
- Same live per-card progress reporting.
- Same $5,000,000 pilot ceiling / $3,750,000 reconciliation stop (still enormous headroom over the real worst
  case — see below).

## Historical baseline carried forward

V9's real terminal run becomes V10's newest historical component, chained onto V8's real 25-component list the
same way V8's own real attempt became V7's historical component 25. V10 independently re-derives and pins:

- V8's real 25-component list (re-verified via the same `v8_terminal_components()` V9 used).
- V9's real terminal campaign ledger and final attestation (hash-pinned against the actual files on disk).
- A new component 26: `attempt_id: "campaign_v9_full_schedule_2026-08-17"`, `booked_cost_usd_millionths:
  38360`, `terminal_disposition: "schema_invalid"`, evidence hash over V9's real 8 output files, chained onto
  component 25's row hash.
- Resulting 26-component total: **$279,640** — matches V9's real `run_summary.json` aggregate exactly.

## Cost arithmetic

- Single full-pass worst case (unchanged schedule): **$935,000** (same as V9 — the schedule and retry budget
  didn't change).
- Worst-case aggregate: $279,640 historical + $935,000 = **$1,214,640** — still trivial against the
  $5,000,000/$3,750,000 ceilings.

## Non-goals

- Does not touch `secret_exposure`, either diagnostic-withheld reason, or any structural/cost-tier stop.
- Does not change the schedule, prompt, retry budget, or collision-family scope.
- Does not guarantee more cards get reached — any hard-terminal reason still in scope (most obviously
  `secret_exposure`, or a second, distinct `schema_conformance_diagnostic_withheld`) can still stop the whole
  run at any card.
- Does not mutate V9's engine, gate, runner, or the real V9 campaign directory — all built as new,
  version-scoped V10 artifacts, per this project's standing rule against mutating shared/prior-version
  constants.

## Sequence

Same 8-step review/authorization sequence as every prior version, steps 1–4 self-performed by Claude under the
still-active temporary two-party mode (through 2026-08-23 09:49): proposal (this document) → local build →
self-review → formal test verification → fresh same-day facts + live model/pricing re-verification → draft
attestation, self-validated → Johnny's direct final authorization → final attestation → real command handed to
Johnny, who alone runs it.
