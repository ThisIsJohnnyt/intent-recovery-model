# Gold v1.2.2 — Target-Integrity Correction Proposal

**Date:** 2026-08-03
**Companion artifact:** `gold_v1.2.2_target_integrity_corrections_proposal.jsonl`
**Status:** Design-only proposal; independent review required
**Corpus edits authorized:** None
**Compute authorized:** None

## Decision boundary

Gold v1.2.2 is immutable historical evidence. These corrections must not overwrite or silently relabel the 66-example corpus used by prior studies.

If approved, implementation should produce a separately fingerprinted **derived candidate corpus** from the pinned Gold v1.2.2 inputs. A final release/version name is intentionally not chosen in this proposal.

## Why these three records

The no-compute audit and Claude's independent verification found three source/target conflicts in the corpus actually used for the seed-17 v2 study:

1. a dangling-reference target supplies a missing topic and creates an unsupported task;
2. a fragmented-note target promotes an observation and unfinished thought into complete tasks;
3. a standalone-task target grammatically assigns the writer's reaction to an object.

These are not speculative additions designed around one checkpoint output. They are independently confirmed defects in existing gold target text.

## Proposed corrections

### ti-001 — dangling reference

**Input hash:** `b314914e28568a4c38062a66c44e9813b0adede52ffe04ba1e662838407fad21`

Current target invents "plans for Friday" and converts the unresolved question into "Ask daughter about Friday."

Proposed behavior:

- preserve "the thing in the blue folder" without supplying its identity;
- preserve the unresolved question about what the daughter said;
- retain only the two explicit actions: update the router firmware and check the thing in the blue folder.

Count change: **B3/A3 → B3/A2**.

### ti-002 — fragmented rapid switching

**Input hash:** `0b778d450a85284bde042ebd21473c5da4070df191e5ccab90783209a8b80dca`

Current target correctly marks "gas is low" as an observation and the landlord fragment as unfinished in narrative/bullets, but contradicts itself in actions by adding "Get gas" and "Call the landlord."

Proposed behavior:

- leave narrative and bullets unchanged;
- retain the supported checklist, meeting priority, and lunch commitment as actions;
- remove the action inferred from low gas;
- remove the completed landlord action inferred from an unfinished fragment.

Count change: **B5/A5 → B5/A3**.

**Review-sensitive judgment:** retaining "Attend the meeting" and "Lunch with Dana at noon" as action items follows the existing corpus treatment of terse commitments and scheduled events. Claude should explicitly agree or propose a stricter alternative; this choice must not be silently accepted.

### ti-003 — actor/reaction binding

**Input hash:** `d465f20edc074b9536e6fcde489c22c93c3eb96c2b2573b22f909faf0ba4f2fb`

Current target says the sink "feels exhausting." The source supports that the writer finds dealing with the dripping sink exhausting.

Proposed behavior:

- explicitly bind being tired of the situation to the writer;
- preserve the sink observation;
- preserve the mileage-form and Bea tasks unchanged.

Count change: **B4/A2 → B4/A2**.

## Structural impact

No bullet count changes are proposed.

### Train action-count distribution

| Actions | Current | Proposed derived corpus |
|---:|---:|---:|
| 0 | 7 | 7 |
| 1 | 22 | 22 |
| 2 | 16 | 17 |
| 3 | 7 | 7 |
| 4 | 7 | 7 |
| 5 | 1 | 0 |

The corrected 60-example train split would have a maximum action count of four. This is the truthful consequence of removing unsupported actions; the old A5 record must not be retained merely to preserve a convenient histogram.

This makes the action-count coverage gap more—not less—important. A later balanced curriculum must introduce genuinely supported A5–A8 examples rather than relying on inflated targets.

### Full 66-example action-count distribution

| Actions | Current | Proposed derived corpus |
|---:|---:|---:|
| 0 | 8 | 8 |
| 1 | 24 | 24 |
| 2 | 18 | 19 |
| 3 | 8 | 8 |
| 4 | 7 | 7 |
| 5 | 1 | 0 |

## Required implementation safeguards

If the proposal is jointly approved, a corpus-derivation tool should:

1. load the pinned 66-example source artifact, not the live working copy of `synthetic.jsonl`;
2. require exactly 66 unique source inputs;
3. locate each correction by exact SHA-256 of source input;
4. require the stored `current_output` to match before replacement, failing closed on drift;
5. replace only the three `output` objects;
6. preserve every input, category, difficulty label, record order, and split assignment;
7. regenerate both v1 and v2 serialized targets mechanically from the corrected structured outputs;
8. prove that exactly three structured outputs changed;
9. parse every regenerated v2 target and require exact equality with its structured output;
10. record old/new corpus fingerprints and the correction-proposal fingerprint.

No hand-edited serialized target should become the authority. The structured `output` object remains the source of truth.

## Evaluation consequences

These corrections are plausibly relevant to:

- Probe 11's object/reaction distortion;
- Probe 16's supplied dangling referent;
- sdi2-06 and other observation/question-to-action promotion failures.

They are **not** expected to solve:

- sdi2-08's A8 requirement;
- the absence of zero-action either/or training forms;
- sparse unrelated-observation phrasing;
- dense compositional transfer by themselves.

The proposal therefore does not claim that a target-fix-only checkpoint could pass the frozen v2 study.

## Recommended experimental sequencing after review

Do not decide the compute matrix yet. First:

1. jointly approve or revise the three corrections;
2. perform the remaining 63-target integrity scan under the same rubric;
3. freeze a derived corrected-base corpus;
4. design the balanced curriculum against the corrected distribution;
5. then choose whether a target-fix-only cell is worth its diagnostic value or whether a same-seed multi-cell ablation is required.

Any future training remains subject to a separate manifest, fixed step/split controls, frozen scoring, and Johnny's explicit authorization.

## Borderline scan finding

Claude reported one milder borderline case during broader scans. It should be documented in Claude's review, but it is not included in this proposal unless both reviewers agree that it violates the same source-support standard. Awareness alone is not sufficient grounds for mutation.

## Alignment request

Claude should independently verify:

- all three source hashes and current outputs;
- the proposed semantic corrections;
- both action-count distribution tables;
- the review-sensitive ti-002 action judgment;
- the implementation safeguards and historical-versioning boundary.

**ChatGPT status: proposal ready for review; no edits or compute authorized.**
