# Gold v1.2.2 Curriculum Specification

**Release:** Gold v1.2.2  
**Status:** Approved — authored, revised, and independently reviewed clean
(see `gold_v1.2.2_review_report.md`)  
**Theme:** Intent Fidelity and Evidence-Boundary Reinforcement  
**Release type:** Additive corrective release  
**Depends on:** Gold v1.2 and Gold v1.2.1

## Objective

Preserve exactly what a note supports across narrative, bullets, and action items. Correct the seven protected failures identified by strict Gold v1.2.1 benchmark scoring without introducing Gold v1.3's Sensory Overwhelm theme.

## Approved benchmark baseline

Benchmark probes `14` and `16` were reclassified from `regression_guard`
to `negative_example` (executed in
`datasets/benchmark/gold_v1.2.1_probes.jsonl` and
`training/gold_v1.2.1_benchmark_results_epoch40.json`, without changing
their inputs, expected behaviors, checks, or failure labels).

- Overall strict pass rate: 9/16 (56%)
- Format-validity rate: 16/16 (100%)
- Regression guards passed: 9/9 (100%)
- Negative examples resolved: 0/7 (0%)

Protected negative examples: `02`, `03`, `08`, `12`, `14`, `15`, `16`.

## Core principle

> Preserve the note's intent type and evidentiary boundary in every output field: do not add, promote, split, obscure, or silently drop what the note does and does not support.

## Approved category plan

Reuse:

- `interrupted_thought_depth`
- `nested_boundary_depth`
- `open_question_preservation`
- `buried_task_retention`
- `dangling_reference`

Add:

- `unsupported_content_resistance`
- `idea_action_boundary`
- `cross_field_completeness`

## Dataset plan

12 examples:

- 3 medium
- 5 hard
- 4 expert

Stages:

1. Isolated Intent-Type Fidelity — examples 01–04
2. Boundary Precision in Realistic Notes — examples 05–08
3. Controlled Combination — examples 09–12

## Coverage matrix

| Example | Primary lesson | Difficulty | Benchmark analogue |
|---|---|---|---|
| 01 | unsupported filler resistance: observation | medium | 14 |
| 02 | dangling-reference restraint | medium | 16 |
| 03 | tentative idea only | medium | 15 |
| 04 | tentative idea plus explicit task | hard | 15 |
| 05 | interrupted return without redundant action | hard | 02 |
| 06 | coherent nested task plus surviving observation | hard | 03 |
| 07 | clear unresolved alternatives | hard | 08 |
| 08 | idea embedded in reflection | hard | 15 |
| 09 | unsupported-content restraint under multiple topics | expert | 14 / 16 |
| 10 | buried and final tasks across fields | expert | 12 |
| 11 | question, idea, task, and observation across fields | expert | 08 / 15 |
| 12 | maximum controlled interleaving | expert | 02 / 12 / 15 |

## Release gates after training

- Format validity remains 100%.
- All 9 baseline regression guards still pass.
- No new unsupported-addition failures appear.
- At least 4 of 7 negative examples resolve.
- Probe 15 resolves.
- At least one of probes 14 or 16 resolves without regressing the other.
- No probe passes through partial credit.

Stretch goal: 16/16 strict benchmark passes.

## Out of scope

- Sensory Overwhelm
- diagnosis classification
- multi-note reasoning
- inference-contract changes
- marker-format changes
- training on benchmark probes

## Decision Point Resolution

Approved by ChatGPT (Dataset Curator), the product owner, and Claude Code
(Engineering Lead): the benchmark reclassification, 12-example target,
three-stage structure, release gates, and category plan above (5 reused,
3 new) all as proposed, with the one amendment already reflected in
"Approved category plan" (`dangling_reference` reused rather than adding
a parallel `dangling_reference_restraint` category).

Independent review (`gold_v1.2.2_review_report.md`) initially flagged
examples 005, 006, 007, and 012 for reusing benchmark wording/sentence
patterns closely enough to risk contaminating the benchmark improvement
this release is meant to demonstrate — most notably example 006's verbatim
reuse of probe 03's "that is one question." All four were rewritten (new
surface forms, same lesson/category/difficulty) and re-reviewed clean; the
review report's verdict is final: no remaining borderline or blocking
findings.
