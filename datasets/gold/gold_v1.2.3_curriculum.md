# Gold v1.2.3 Curriculum Specification

**Release:** Gold v1.2.3  
**Status:** Authored — pending independent review, training, and strict benchmark evaluation  
**Theme:** Discourse Reconnection and Clean Evidence Boundaries  
**Release type:** Compact additive corrective release  
**Depends on:** Gold v1.2, Gold v1.2.1, and Gold v1.2.2

## Objective

Correct the three failures that remain after Gold v1.2.2:

- reconnect an explicitly interrupted thought without garbling it, losing supported detail, or extracting a return phrase as content;
- phrase an unresolved either/or question clearly while preserving both alternatives and keeping later observations non-answering;
- preserve a reminder with dangling references and stop after the final source-supported clause.

Gold v1.2.3 does not broaden the curriculum. It adds six narrowly selected examples for benchmark probes `02`, `08`, and `16`.

## Approved benchmark baseline

Gold v1.2.2 checkpoint-600 is the candidate and comparison baseline. Production remains on Gold v1.2.1 checkpoint-520.

- Overall strict benchmark pass rate: 13/16
- Format-validity rate: 16/16
- Existing regression guards retained: 9/9
- Negative examples resolved: probes `03`, `12`, `14`, and `15`
- Probes `12`, `14`, and `15` promoted to `regression_guard`
- Probe `03` remains a `negative_example` pending one additional clean run
- Remaining failing probes: `02`, `08`, and `16`

## Core principles

> Recover the note's discourse relationship and evidentiary boundary without turning structural language into meaning.

For this release:

1. An interruption and its explicit resumption form one recovered thought.
2. The inserted note remains a separate topic.
3. Phrases that only signal a return to the earlier thought do not appear as facts, bullets, or action items.
4. Both alternatives in an unresolved question remain visible.
5. A later observation does not select an alternative unless the source explicitly says it does.
6. A dangling-reference reminder remains usable without guessed referents or trailing editorial commentary.

## Category plan

Reuse only:

- `interrupted_thought_depth`
- `open_question_preservation`
- `dangling_reference`

No new categories are introduced.

## Dataset plan

Six examples:

- 1 medium
- 4 hard
- 1 expert

Stages:

1. Interruption and Resumption Across Surface Forms — examples 01–03
2. Clear Unresolved Alternatives — examples 04–05
3. Clean Stop With Dangling References — example 06

## Coverage matrix

| Example | Primary lesson | Difficulty | Benchmark analogue |
|---|---|---|---|
| 01 | sentence-level pause and explicit resumption | hard | 02 |
| 02 | parenthetical interruption inside a diagnostic thought | hard | 02 |
| 03 | topic-label return after an inserted reminder | expert | 02 |
| 04 | direct either/or question with surrounding observations | hard | 08 |
| 05 | declarative alternatives plus a later non-answer | hard | 08 |
| 06 | dangling-reference reminder with an exact clean stop | medium | 16 |

## Surface-form coverage

The three interruption examples deliberately teach the same discourse relationship through different structures:

- complete sentence, explicit pause, then resumption;
- interrupted diagnostic sentence with a parenthetical reminder;
- topic label, inserted reminder, then a return using a different topic label.

The two uncertainty examples deliberately vary how alternatives are introduced:

- a direct either/or interrogative;
- a declarative statement of unresolved possibilities.

None of the examples reproduces protected benchmark wording, nouns, or full sentence skeletons.

## Strict benchmark scoring rule

The existing strict rule is unchanged:

- A probe passes only when every required check passes.
- Partial compliance receives no partial credit.
- Valid formatting does not compensate for a semantic failure.
- A preserved main clause does not compensate for an unsupported addition.
- A correct action item does not compensate for lost or garbled causal detail.

## Release gates after training

- Format validity remains 16/16.
- All current regression guards pass, including promoted probes `12`, `14`, and `15`.
- Probe `03` passes one additional run and becomes eligible for promotion.
- Probes `02`, `08`, and `16` each pass every strict check.
- Overall strict benchmark pass rate reaches 16/16.
- Probe `02` preserves the full reconnected thought and the inserted task without a return-marker action.
- Probe `08` states both alternatives clearly, preserves unresolved status, and does not convert the later observation into an answer.
- Probe `16` preserves the reminder and contains no unsupported trailing clause.
- No new unsupported-addition, topic-loss, task-promotion, or excessive-fragmentation failures appear.

## Out of scope

- Gold v1.3 Sensory Overwhelm
- diagnosis or classification
- new categories
- multi-note reasoning
- inference-contract changes
- marker-format changes
- benchmark wording in training examples
- changes to benchmark inputs, expected behaviors, checks, or strict scoring

## Curatorial rationale

Gold v1.2.2 substantially improved the benchmark, so this release should not add broad combination pressure. Each example is traceable to one of the three remaining failures. The only deliberate repetition is structural: three distinct resumption forms and two distinct uncertainty forms provide enough contrast to teach general relationships instead of one memorized template.
