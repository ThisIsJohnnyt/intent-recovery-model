# Prompt Contract vNext — Decision Proposal

**Status:** Proposed; requires Claude technical review and Johnny approval  
**Implementation authorized:** none  
**Compute authorized:** none

## Decision to make

Choose how the model will represent individual bullet and action items so that:

- item boundaries survive tokenization and decoding;
- Python and TypeScript parse the same output identically;
- counts are directly measurable rather than inferred from prose;
- the small model is not asked to maintain fragile nested syntax;
- the UI can render true arrays;
- semantic requirements—grounding, uncertainty, attribution, deduplication—remain independently scoreable.

## Options

| Option | Boundary mechanism | Machine-verifiable | Small-model risk | App change | Recommendation |
|---|---|---:|---:|---:|---|
| A. Keep v1 | Newlines | No, based on observed outputs | Medium | None | Reject |
| B. Typed item markers | Repeated literal `###BULLET###` / `###ACTION###` markers | Yes, if round-trip test passes | Low–medium | Parser + prompt | **Recommend** |
| C. JSON | Arrays, brackets, quotes | Yes | High; previously unreliable for this model | Parser + prompt | Defer |
| D. Client-side semantic splitting | Infer boundaries from undelimited prose | Not reliably | High ambiguity | Significant heuristic logic | Reject |
| E. Multiple model passes | Separate narrative/bullet/action generations | Yes per pass | Higher latency and cross-pass drift | Pipeline redesign | Defer |

## Recommended option: typed item markers

Candidate shape:

```text
###NARRATIVE###
coherent narrative
###BULLETS###
###BULLET### first supported idea
###BULLET### second supported idea
###ACTIONS###
###ACTION### first explicit task
###ACTION### second explicit task
```

Newlines remain useful for readability but are no longer semantic delimiters. A decoded single-line equivalent remains parseable because `###BULLET###` and `###ACTION###` carry the boundaries.

Typed markers are preferable to one generic `###ITEM###` marker because they:

- make cross-section leakage detectable;
- allow exact counts without relying on section context alone;
- give clearer training supervision;
- reduce the chance that an action accidentally appears as a bullet marker or vice versa.

The identifier and wording are not final. `source-determined-items-v2` is a candidate name only and must not be adopted until cross-repository review is complete.

## Proposed semantic contract

### Narrative

- One coherent recovery of the source-supported intent.
- Preserve uncertainty, attribution, causal relations, deadlines, and dangling references.
- Do not add explanations, diagnoses, emotions, referents, or advice.

### Bullets

- One `###BULLET###` marker per source-supported key idea.
- No minimum count.
- Maximum seven bullet items.
- Do not duplicate content to approach a target count.
- When more than seven ideas exist, preserve the complete content across narrative and appropriate actions without merging unrelated ideas into a false combined bullet.

### Actions

- One `###ACTION###` marker per explicit supported task.
- No artificial minimum.
- Zero actions is valid.
- Do not convert observations, questions, tentative ideas, or incomplete thoughts into actions.
- Deduplicate restated versions of the same task while preserving material qualifiers such as deadlines and recipients.

## Required feasibility gates before implementation

Claude should verify all of the following without GPU training:

1. Python tokenizer encode/decode preserves the exact number and spelling of typed item markers.
2. The browser tokenizer/runtime produces the same marker sequence for the same token IDs.
3. Python and TypeScript parsers return byte-equivalent narrative strings and identical item arrays for a frozen fixture set.
4. Empty action sections parse as an empty array.
5. Malformed, missing, reordered, or cross-section item markers fail closed.
6. Item text containing ordinary hyphens, punctuation, or the words “bullet” and “action” does not split accidentally.
7. Source notes containing marker-like literal text are escaped or otherwise isolated so they cannot alter output parsing.
8. The rendered training and app prompts remain byte-identical for the shared prompt fixture and report the same contract version.
9. Generation-token budgeting remains adequate after marker overhead is included.

If repeated typed markers do not round-trip reliably, stop and return to option review. Do not silently fall back to newlines or punctuation heuristics.

## Dataset transition proposal

If feasibility gates pass:

1. Mechanically migrate the existing 66 targets by prefixing every current bullet with `###BULLET###` and every current action with `###ACTION###`.
2. Do not alter narrative, bullet, or action text during this migration.
3. Recompute and record dataset fingerprints.
4. Verify that item counts before and after migration are identical for all 66 records.
5. Use this mechanically migrated corpus for the first representation study without adding corrective examples. This isolates contract representation from curriculum content.

This first study would test whether the representation is learnable and parseable. It should not be expected to fix every semantic acceptance failure. If structure succeeds but semantic behavior remains weak, a later balanced curriculum can be designed from the resulting evidence.

## Controlled-study proposal after static feasibility

- Reuse the stored seed-17 Cell-A baseline; do not rerun it unnecessarily.
- Train one seed-17 candidate on the mechanically migrated 66-example corpus.
- Use the current benchmark runner with an injected/pinned prompt builder; do not run an old copy of the benchmark runner from the prompt worktree.
- Evaluate structural conformance separately from semantic recovery.
- Run seed 73 only if seed 17 clears every frozen gate.

A fresh study manifest and explicit compute authorization are required. This proposal itself authorizes neither.

## Rejected shortcut: add a few examples now

Adding examples for “garage light,” “upcoming appointment,” or restated insurance tasks before fixing item representation would mix three variables:

- output encoding;
- curriculum content;
- prompt wording.

It would also repeat the narrow-correction pattern that previously caused collateral regressions. Correct the observable contract boundary first, then make content changes only from a controlled baseline.

## Product impact

The app should continue using the current production model and contract until a compatible vNext candidate passes. The open app prompt PR must remain unmerged. No parser-only production change should ship ahead of compatible weights.

## Alignment request

Claude should explicitly report:

- **Aligned**, if typed markers are technically sound and the staged isolation is feasible;
- **Not aligned**, with evidence and an alternative, if tokenizer/runtime or parser behavior contradicts the proposal.

Johnny chooses the option only after that review.
