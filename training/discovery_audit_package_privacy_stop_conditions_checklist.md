# Privacy, Contamination, and Work-Stopping Conditions Checklist

**Operationalizes:** `training/intent_recovery_data_model_discovery_plan_chatgpt.md` §5, "Privacy,
contamination, and work-stopping conditions".

**Status: runnable checklist, to be checked at every stage of a later authorized audit (A1–A5, B1–B3), not
just once at the end.**

**Revised 2026-08-13** per ChatGPT's second independent review: added the A2-shortfall stop below, which
round 1's fix reported but didn't actually treat as work-stopping — a real gap in this checklist
specifically, since this is where every other stop condition already lives.

## Standing rules (apply throughout, not just at specific gates)

- [ ] No private, licensed, or sensitive text has been sent to any hosted model without explicit Johnny
      approval and a completed terms/privacy review.
- [ ] No raw external sample has been stored in this repository during discovery. (A later audit must
      define encrypted/restricted storage, minimum retention, deletion, and access roles *before* any raw
      sample is stored anywhere — this checklist does not itself grant permission to store one.)
- [ ] No identifiable or sensitive source text is quoted in any report produced by this package's
      instruments — reports use record IDs and aggregate mechanism counts only.
- [ ] Every candidate record has been hashed and compared (normalized text/scenario) against the full
      protected+acceptance pool before selection (A2 step 5); any collision is quarantined, not silently
      dropped without a log entry.
- [ ] No evaluation set has been "repaired" after seeing model outputs — the protected/acceptance
      benchmarks are read-only inputs to this process, never edited in response to a result.

## Work-stopping conditions

Any one of the following stops the current step and **returns to Johnny**. It does not authorize a
workaround, a substitute source, or a substitute model chosen to route around the problem.

- [ ] Provenance or license is unclear after checking primary sources (A1).
- [ ] Unexpected personal data appears in a sample (any stage after A2).
- [ ] A required term acceptance appears that Johnny has not approved (A1, or discovered later).
- [ ] Evaluation leakage is found (a frozen protected/acceptance example, or something too close to one,
      turns up inside a candidate's sample or a B2 frozen example).
- [ ] Reproducibility information (revision, seed, environment) needed to redo a step is inaccessible.
- [ ] A model must be substituted for hardware reasons **after** outputs have already been seen (the B1
      replacement rule requires this to happen *before* outputs — a post-hoc substitution is a violation,
      not a normal adjustment).
- [ ] A scorer becomes unblinded before adjudication is complete (B3).
- [ ] A prompt, demonstration, parser, or decoding setting is changed after outputs have been viewed (B2/
      B3).
- [ ] Two independent reviewers materially disagree and adjudication does not resolve it (A3, B3).
- [ ] **A2 returns `must_stop: true` (a non-null `shortfall_reason`)** — added 2026-08-13. The sample
      achieved fewer than the 24-record target even after top-up. A3 does not begin and A5's gates are not
      computed against a smaller denominator; this returns to Johnny per the A2 protocol's "Shortfall is a
      hard stop" section, same as every other condition in this list.

## Disposition on stop

1. Stop the specific step in progress. Do not continue past it "just to finish this part."
2. Document what triggered the stop, in the relevant artifact's own log (A2 manifest, A3/B3 adjudication
   record, etc.) — not just in conversation.
3. Report to Johnny plainly, without speculating about cause beyond what's actually verified (per this
   project's general standing practice — see `[[intent_recovery_collab_model]]`'s pattern of independent
   re-verification before accepting a claim).
4. Wait for Johnny's decision. Neither Claude nor ChatGPT resolves a work-stopping condition unilaterally,
   per the responsibility protocol (`intent_recovery_data_strategy_new_chat_handoff_2026-08-11.md` §8):
   "Any material disagreement is work-stopping and returns to Johnny."
