# Seed-17 v2-Contract Representation Study — ChatGPT Scoring Handoff

**Date:** 2026-08-03
**Source commit:** `07de0d4f4cd65707f7a0bac46ccc0a6a83586939`
**Scorer:** ChatGPT
**Status:** Independent scoring complete; Claude verification required
**Further compute authorized:** None

## Decision

The seed-17 v2 candidate **does not clear the frozen study gates**. Seed 73 remains blocked.

The run establishes a meaningful representation result: all 26 generated outputs—16 protected probes and 10 v2 acceptance cases—are parse-valid under the real typed-marker parser. The model learned the serialization. However, exact count conformance, semantic acceptance, and same-seed regression protection do not all hold.

## Gate results

| Gate | Required | Result | Status |
|---|---|---:|---|
| Protected benchmark parse validity | 16/16 | 16/16 | **PASS** |
| v2 acceptance parse validity | 10/10 | 10/10 | **PASS** |
| v2 acceptance count-rule conformance | 10/10 | 6/10 | **FAIL** |
| v2 acceptance combined strict pass | 10/10 | 4/10 | **FAIL** |
| Protected benchmark strict passes vs. Cell A | Candidate ≥ Cell A | 11/16 vs. 10/16 | **PASS** |
| Same-seed regression-guard preservation | No Cell-A pass becomes a candidate failure | Probe 11 regressed | **FAIL** |

Because every frozen gate was required, this is a study failure even though several individual measures improved.

## Important layer distinction

The v2 acceptance set has three useful totals:

- **10/10 parse-valid**: every output is structurally readable;
- **5/10 semantic-only strict passes**: sdi2-01, 02, 05, 08, and 09 satisfy their semantic dimensions and capability checks when count rules are considered separately;
- **4/10 combined strict passes**: sdi2-01, 02, 05, and 09 satisfy semantics **and** both count rules.

sdi2-08 is the deliberate separator: all eight source tasks survive somewhere without merger or invention, so its semantic checks pass, but only five appear as actions. It therefore fails the exact-eight-action structural requirement.

## Acceptance-case scoring

| ID | Count rules | Semantic layer | Combined | Finding |
|---|---|---|---|---|
| sdi2-01 | Pass | Pass | **Pass** | Observation preserved without action or explanation. |
| sdi2-02 | Pass | Pass | **Pass** | Task, deadline, and destination survive; no extra step. |
| sdi2-03 | Pass | Fail | **Fail** | "Followed by the blue scarf" invents a relationship between unrelated observations. |
| sdi2-04 | Pass | Fail | **Fail** | "So" invents a causal link between the paint observation and fabric-sample task. |
| sdi2-05 | Pass | Pass | **Pass** | Tentative idea remains tentative and non-actionable. |
| sdi2-06 | Fail | Fail | **Fail** | Two unsupported actions are invented, including finishing the album. |
| sdi2-07 | Fail | Fail | **Fail** | One restated task becomes duplicated bullets/actions and gains unsupported meeting wording. |
| sdi2-08 | Fail | Pass | **Fail** | All eight tasks remain represented, but only five survive in the action section. |
| sdi2-09 | Pass | Pass | **Pass** | Dangling references remain unresolved; output stops cleanly. |
| sdi2-10 | Fail | Fail | **Fail** | Deadline is lost, task attribution is distorted, and the tile question is merged confusingly with the bowls. |

Scored artifact:

- `gold_v1.2.2_seed17_v2contract_acceptance10_scored_chatgpt.json`
- SHA-256: `7e1003512762a5ad4461d0a29b02c4f2302d88d2aa564ca5ff90b8305c0fbd46`

## Protected 16-probe scoring

Strict pass set:

`01, 03, 04, 05, 07, 09, 10, 12, 13, 14, 15`

| Probe | Result | Finding when failed |
|---|---|---|
| 01 | Pass | — |
| 02 | **Fail** | Replaces the stated charger-movement cause with invented "battery life" and loses the supported causal detail. |
| 03 | Pass | — |
| 04 | Pass | — |
| 05 | Pass | — |
| 06 | **Fail** | Misattributes the earlier asking to Rowan; stamped-copy ambiguity itself remains preserved. |
| 07 | Pass | — |
| 08 | **Fail** | Replaces the window-or-plant alternatives with an invented "underlying problem" framing and changes the dry wet-spot observation into a claim about the plant. |
| 09 | Pass | — |
| 10 | Pass | — |
| 11 | **Fail** | Falsely makes the fee "include" the garage light and shifts the writer's tiredness onto the light. |
| 12 | Pass | — |
| 13 | Pass | — |
| 14 | Pass | — |
| 15 | Pass | — |
| 16 | **Fail** | Invents "two men" as the unresolved referent. |

Scored artifact:

- `gold_v1.2.2_seed17_v2contract_protected16_scored_chatgpt.json`
- SHA-256: `2828a83830f7ef715f33e3a31046102cffc6dc7a431223e12fc1f5f644853f55`

## Same-seed comparison with Cell A

| Measure | Cell A, old contract | v2 candidate | Delta |
|---|---:|---:|---:|
| Overall strict passes | 10/16 | 11/16 | +1 |
| Regression guards passed | 9/12 | 10/12 | +1 |

The aggregate improvement does not satisfy the frozen regression rule because the sets differ:

- **Lost:** Probe 11
- **Gained:** Probes 09 and 10

Probe 06 also fails the candidate, but it already failed the actual seed-17 Cell-A run; it is not a same-seed gate regression. The reporter's historical-note warning lists 06 and 11 because it compares against checkpoint-era annotations, not the actual Cell-A pass set. The controlled-study gate must use the actual Cell-A results, making Probe 11 the single relevant flip.

## Process disagreement to flag

One narrow framing disagreement should be returned under the project's standing protocol. Once the automatically computed acceptance count result was known to be 6/10, the frozen Layer-1 gate was already mathematically failed. Semantic scoring was still required to characterize the run, evaluate the protected benchmark, and guide the next investigation—but it was not necessary to know whether seed 17 had passed **every** gate.

This does not dispute Claude's reported structural facts or provenance; those checked out.

## Interpretation

The evidence supports retaining the typed-marker direction for investigation:

- the representation boundary works far better than newline delimiters—26/26 outputs parse;
- remaining failures are primarily content selection, semantic relation, task classification, deduplication, qualifier retention, and high-count generalization;
- contract repair alone does not solve those learned behaviors.

The result does **not** support activating v2 in the app, exporting this checkpoint, running seed 73, or adding narrow corrective examples immediately.

## Recommended next work

1. Claude independently verifies every score and the two same-seed pass sets.
2. Freeze this run as a failed-but-informative representation study.
3. Perform a no-compute coverage audit of the 66-example corpus against the observed failure families:
   - unrelated observations without connective invention;
   - observation-plus-task without causal linking;
   - unresolved alternatives with zero actions;
   - literal restatement deduplication;
   - six-to-eight explicit action counts;
   - dense attribution and qualifier retention.
4. Jointly decide whether the next experiment should test a balanced curriculum under v2 or revise the acceptance/training design. Do not authorize another seed until that analysis is aligned.

## Alignment status

**Scoring complete. Not yet jointly Aligned pending Claude's independent verification. Seed 73 remains blocked.**
