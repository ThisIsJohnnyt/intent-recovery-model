# A5 — Dataset-Fit Decision Checklist

**Operationalizes:** `training/intent_recovery_data_model_discovery_plan_chatgpt.md` §3, "A5. Dataset-fit
decision rules".

**Status: fillable checklist, blank.** Every threshold below is copied verbatim from the plan already
reviewed by Johnny and independently verified by Claude — nothing here is a new or renegotiated number.
This document does not decide anything by itself; it is filled in once, after A1–A4 are complete for a
specific candidate, by whoever runs that later authorized audit.

**Revised 2026-08-12** per ChatGPT's independent review: gate 4 originally asked only for a fatal-collision
count, which can't prove "no collision remains" when non-fatal review flags are still sitting unadjudicated.
Gate 5 originally left "usable as inputs" as an unlabeled percentage with no stated formula. Both fixed
then.

**Revised again 2026-08-13** per ChatGPT's second review: (1) added a prerequisite gate 0 — A2's shortfall
is now a hard stop (see the A2 protocol doc), so this checklist may not even be filled in against an
undersized sample; (2) gate 4's wording assumed adjudication happens by mutating A2's manifest in place
(`adjudicated: true`), but that field was removed 2026-08-13 specifically because a "frozen" manifest can't
be mutated without losing its integrity guarantee — gate 4 now checks the separate adjudication artifact
instead (see A2 protocol's "Collision adjudication artifact" section).

**Revised a third time, same day, per ChatGPT's third review:** gate 0 as first written only checked the
*pre-adjudication* manifest's `must_stop` — but adjudication can itself exclude records (a legitimate
`"exclude"` disposition on a non-fatal flag), which can drop the *retained* count below 24 without
`must_stop` ever changing. Gate 0 now checks the count that actually matters: retained count after
adjudication, not just the original selection.

**Revised a fourth time, same day, per ChatGPT's fourth review:** the third-review fix implied an automatic
post-adjudication top-up mechanism that turned out to be incomplete (top-up records had nowhere documented
to live in an immutable manifest, the adjudication artifact had no provision for a second round, and the
gate-0 formula never actually added accepted top-up records back in). Simplified per ChatGPT's own
proposed fix: **any post-adjudication shortfall is now a hard stop, full stop — no automatic top-up.**
Gate 0 below reflects that; see the A2 protocol's "Post-adjudication completeness" section for the full
reasoning.

## Per-candidate checklist

**Candidate:** _______________ **Date completed:** _______________

| # | Gate | Threshold | Result | Pass? |
|---|---|---|---|---|
| 0 | Sample completeness (A2 + post-adjudication) | `must_stop` is `false` in the frozen A2 manifest **AND** retained count (`len(selected_records) − adjudication "exclude" dispositions`) equals **24** after adjudication completes. **No automatic top-up** — if retained count is below 24, this is a hard stop back to Johnny (see A2 protocol's "Post-adjudication completeness"), not a gate to compute a percentage for. | `must_stop`: ______. Retained count: ___ / 24 | ☐ |
| 1 | Rights/governance gate (A1) | No unresolved material issue | A1 disposition: ______ | ☐ |
| 2 | Priority-mechanism coverage (A3) | At least **8 of 24** inputs contain ≥1 priority mechanism (corrected 2026-08-13 definition — action components excluded), under independent adjudication | ___ / 24 | ☐ |
| 3 | Interacting-mechanism coverage (A3) | At least **4 of 24** inputs contain interacting mechanisms (corrected 2026-08-13 dependency test, not mere co-occurrence), under independent adjudication | ___ / 24 | ☐ |
| 4 | Evaluation collision (A2) | No collision with protected/acceptance evaluations remains after quarantine | Fatal collisions after top-up: ___. Non-fatal review flags requiring adjudication (from the frozen manifest): ___. **Must be 0 unresolved** to pass — every flag needs a matching resolved entry in the *separate* adjudication artifact (keyed to this manifest's `compute_manifest_hash()` value, per the A2 protocol) — the frozen manifest itself is never edited to record a disposition. | ☐ |
| 5 | Input usability (A4) | At least **75%** of sampled inputs usable as inputs without reconstructing missing context | Formula: `(count of A4 target-classification `Usable` + `Re-annotation required`) / 24`, expressed as a percentage — both classes count here because A4's "usable as input" question is about the *input*, not the target; only `Incompatible` (input lacks the relevant mechanisms, provenance/rights failed, or reconstruction of missing context would be required) counts against this gate. Result: ___ % | ☐ |
| 6 | Re-annotation affordability (A4) | Estimated re-annotation burden recorded and judged affordable **by Johnny** | Johnny's judgment: ______ | ☐ |

**Gate 0 is a strict prerequisite, not just another row.** If it fails, stop — do not compute gates 1–6 at
all (they're denominated over 24, which a shortfalled sample doesn't have); return to Johnny per the A2
protocol's "Shortfall is a hard stop" section instead.

**Note on gate 6:** this is the one gate this package cannot pre-fill or approximate — it is explicitly
Johnny's affordability call on the A4 timing estimate, not a computed threshold. Every other gate (0–5) is
a fact check against A1–A4 outputs.

## Aggregate rule

- **Gate 0, then all six of gates 1–6, pass** → this candidate may proceed to a bounded conversion proposal
  (a separate, later-authorized milestone — passing this checklist is not that authorization).
- **Any gate fails** → this specific source is rejected for the next milestone (gate 0 failing specifically
  means: stop and return to Johnny, per the hard-stop rule above, rather than "rejected" in the same sense
  as 1–6). Per the plan: "Failure of
  these thresholds rejects that source for the next milestone, not the overall hybrid strategy" — a failed
  DialogSum result, for example, says nothing about whether QMSum or AMI should also be rejected, and does
  not by itself mean the project should abandon the authentic-external-input strategy.

## Explicit non-effect

Existing targets are not required to pass anything here — target quality (A4's Usable / Re-annotation
required / Incompatible split) feeds gate 5's "usable as inputs" and gate 6's effort estimate, but a
candidate with 0 `Usable` targets and 24 `Re-annotation required` targets can still clear this checklist if
gates 1–5 pass and Johnny judges the re-annotation burden affordable. A high re-annotation rate is an
expected, decision-relevant finding, not an automatic disqualifier.
