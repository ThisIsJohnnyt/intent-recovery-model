# Gold v1.2.3 Group Screen — Seed 17 Strict Scoring

## Purpose

This report scores the seed-17 fixed-split group screen and determines whether one Gold v1.2.3 category group is sufficient to reproduce the Probe 05 and Probe 11 regressions seen in the six-example ablation.

The three additions were evaluated separately against the frozen Gold v1.2.2 split:

- Group A: examples 001–003 (`interrupted_thought_depth`), 63 training examples
- Group B: examples 004–005 (`open_question_preservation`), 62 training examples
- Group C: example 006 (`dangling_reference`), 61 training examples

The strict benchmark rule is unchanged. A probe passes only if every required check passes. Format validity is reported separately.

## Aggregate results

| Group | Overall | Regression guards | Negative examples | Format validity |
|---|---:|---:|---:|---:|
| A — interruption | 10/16 | 9/12 | 1/4 | 16/16 |
| B — open question | 11/16 | 10/12 | 1/4 | 16/16 |
| C — dangling reference | 9/16 | 8/12 | 1/4 | 16/16 |

None of the three groups is candidate-eligible.

## Probe-level strict results

| Probe | Group A | Group B | Group C |
|---:|:---:|:---:|:---:|
| 01 | Pass | Pass | Pass |
| 02 | Fail | Fail | Fail |
| 03 | Pass | Pass | Pass |
| 04 | Pass | Pass | Pass |
| 05 | Pass | Pass | **Fail** |
| 06 | Fail | Fail | Fail |
| 07 | Pass | Pass | Pass |
| 08 | Fail | Fail | Fail |
| 09 | Fail | Fail | Fail |
| 10 | Pass | Pass | Pass |
| 11 | **Fail** | Pass | **Fail** |
| 12 | Pass | Pass | Pass |
| 13 | Pass | Pass | Pass |
| 14 | Pass | Pass | Pass |
| 15 | Pass | Pass | Pass |
| 16 | Fail | Fail | Fail |

## Targeted finding

- Group A is sufficient to reproduce the Probe 11 failure, but not Probe 05.
- Group B reproduces neither targeted failure.
- Group C alone is sufficient to reproduce both targeted failures at seed 17.
  - Probe 05 reproduces the same cross-field recipient error as the all-six seed-17 run: the narrative says Cole receives the folder link while the supported recipient is Priya.
  - Probe 11 reproduces the qualifier loss: the Thursday fee deadline disappears from the action.

Group C therefore has the strongest observed association with the paired regression. This is not yet causal proof because all three group runs also changed training duration relative to the baseline.

## Failure notes

### Group A

- Probe 02: the interrupted causal chain remains garbled.
- Probe 06: the question is attributed to Rowan instead of Tessa.
- Probe 08: the unresolved alternatives are phrased confusingly and the plant observation is treated as if it bears on the answer.
- Probe 09: the volunteer list is promoted into an unsupported action.
- Probe 11: the narrative invents a need to keep the garage light flickering, and the Thursday deadline is lost from the action.
- Probe 16: unsupported trailing commentary remains after the source-supported clause.

### Group B

- Probe 02: the interruption is garbled and the tablet is incorrectly merged with the donation detail.
- Probe 06: the question is attributed to Rowan instead of Tessa.
- Probe 08: both alternatives remain present, but the question is still confusing rather than cleanly unresolved.
- Probe 09: the volunteer list is promoted into an unsupported task.
- Probe 16: unsupported trailing commentary remains.

### Group C

- Probe 02: the stated cause is dropped.
- Probe 05: the narrative assigns Priya's folder link to Cole.
- Probe 06: a bullet attributes the question to Rowan instead of Tessa.
- Probe 08: the unresolved alternatives remain confusingly phrased.
- Probe 09: the volunteer list becomes an invalid unresolved question.
- Probe 11: the Thursday fee deadline is lost from the action.
- Probe 16: the output invents a referent rather than stopping at the supported dangling reference.

## Shared Probe 06 regression

Probe 06 fails in all three group runs even though it passed in the Gold v1.2.2-only seed-17 control. Because Groups A, B, and C contain different content, this common movement is evidence that a shared training-configuration change may be contributing to the regression.

## Optimizer-step confound

With batch size 4 and 40 epochs, adding even one example changes the number of batches per epoch:

| Corpus | Training examples | Steps per epoch | Total optimizer steps |
|---|---:|---:|---:|
| Gold v1.2.2 baseline | 60 | 15 | 600 |
| Group C | 61 | 16 | 640 |
| Group B | 62 | 16 | 640 |
| Group A | 63 | 16 | 640 |
| All six Gold v1.2.3 examples | 66 | 17 | 680 |

The group screen therefore changes two variables at once: curriculum content and optimizer-step count/batch geometry. The shared Probe 06 failure across all three groups makes this confound operationally important, not merely theoretical.

## Interpretation

1. Group C is the strongest content-level suspect for the paired Probe 05/11 regression, because it alone reproduces both failures.
2. Group A independently reproduces Probe 11, showing that Probe 11 is broadly vulnerable to added-data distribution shifts and is not uniquely tied to example 006.
3. Group B avoids Probes 05 and 11, but it still breaks existing guards, so it is not a safe candidate addition.
4. Example 006 may be overgeneralizing its unresolved-recipient and compression pattern into unrelated inputs, but rewriting or removing it is premature until the step-count confound is isolated.

## Required control before Stage 2

Run two step-matched controls using the unchanged 60-example Gold v1.2.2 training set at seed 17:

1. A 640-step baseline, with the scheduler and all step-dependent settings configured for 640 steps, for direct comparison with Groups A, B, and C.
2. A 680-step baseline, configured equivalently, for direct comparison with the all-six fixed-split ablation.

Keep all other training arguments, validation examples, evaluation inputs, decoding settings, and checkpoint-selection rules frozen. Use dedicated output directories.

Declared comparisons:

- At 640 steps, score Probes 05, 06, and 11 first, then the full strict benchmark and regression-guard count.
- At 680 steps, compare the all-six targeted failures and full regression-guard count.
- If the 640-step baseline passes Probes 05 and 11 while Group C fails them, the evidence for a Group C content effect strengthens.
- If the 640-step baseline reproduces either failure, attribute that portion of the movement to training duration or batch geometry before auditing individual examples.

Do not start the seed-42/73 Group C confirmation runs, edit example 006, or construct a replacement curriculum until these controls are scored.

## Ownership

| Action | Owner |
|---|---|
| Run the 640- and 680-step seed-17 baseline controls and provide raw outputs/configuration | Claude Code |
| Apply the frozen strict rubric and compare the controls with the group and all-six runs | ChatGPT |
| Approve any Stage 2 expansion or curriculum change | Johnny |

## Release status

This investigation does not change release status. Gold v1.2.3 remains non-promotable; checkpoint-600 remains the candidate/comparison baseline; checkpoint-520 remains in production. No dataset examples are promoted, removed, or rewritten by this report.
