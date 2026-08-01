# Gold v1.2.2 Seed-17 Step-Matched Controls — Strict Scoring

## Purpose

This report applies the frozen strict benchmark rubric to the unchanged Gold v1.2.2 seed-17 controls trained for 640 and 680 optimizer steps. These runs isolate optimizer-step count from Gold v1.2.3 curriculum content.

The comparison targets were declared before scoring:

- 640-step Gold v1.2.2 control versus the 640-step Groups A, B, and C screens
- 680-step Gold v1.2.2 control versus the 680-step all-six Gold v1.2.3 fixed-split ablation
- Primary probes: 05, 06, and 11
- Full strict benchmark and regression-guard count as secondary outcomes

No dataset, curriculum, decoding, validation, or benchmark changes are introduced here.

## Aggregate results

| Run | Overall | Regression guards | Negative examples | Format validity |
|---|---:|---:|---:|---:|
| Gold v1.2.2 seed 17 — 640 steps | 9/16 | 8/12 | 1/4 | 16/16 |
| Gold v1.2.2 seed 17 — 680 steps | 10/16 | 9/12 | 1/4 | 16/16 |

Neither step-matched control is candidate-eligible.

## Probe-level strict results

| Probe | 640-step control | 680-step control |
|---:|:---:|:---:|
| 01 | Pass | Pass |
| 02 | Fail | Fail |
| 03 | Pass | Pass |
| 04 | Pass | Pass |
| 05 | **Pass** | **Pass** |
| 06 | **Fail** | **Fail** |
| 07 | Fail | Pass |
| 08 | Fail | Fail |
| 09 | Fail | Fail |
| 10 | Pass | Pass |
| 11 | **Fail** | **Fail** |
| 12 | Pass | Pass |
| 13 | Pass | Pass |
| 14 | Pass | Pass |
| 15 | Pass | Pass |
| 16 | Fail | Fail |

## Failure rationale

### 640-step control

- **Probe 02:** The return phrase is treated as semantic content, the tablet thought becomes tautological, and the charger-movement cause is not correctly reconnected to the investigation.
- **Probe 06:** A bullet says Rowan asked about the permit, misattributing Tessa's earlier question.
- **Probe 07:** The explicit task to save the confirmation page survives in the narrative and bullets, but the action list replaces it with the unsupported action "Check if the refund reached the card."
- **Probe 08:** Both source alternatives remain, but the question is tautological and confusing rather than a clear unresolved window-versus-plant question.
- **Probe 09:** The output adds the unsupported bullet "Send mail to Imani."
- **Probe 11:** Both tasks survive, but the Thursday deadline drops from the fee action.
- **Probe 16:** The output adds unsupported referent commentary instead of stopping after the source-supported reminder.

### 680-step control

- **Probe 02:** The return phrase is again treated as content, the donation-box detail is incorrectly merged into the tablet causal chain, and the charger-movement cause is lost.
- **Probe 06:** The bullets again attribute the earlier permit question to Rowan and recast a past statement as "Tell Rowan."
- **Probe 08:** The output invents "an accident" as a possible cause and adds an unsupported checking action.
- **Probe 09:** "Consider the volunteer list" promotes the unfinished fragment into a task-like instruction.
- **Probe 11:** Both tasks survive, but the Thursday deadline again drops from the fee action.
- **Probe 16:** The output adds unsupported commentary about the unresolved referents.

The malformed inflection "backped up" in Probe 05 at 680 steps is treated as a surface-generation error rather than a semantic failure: Nina remains the person who backed up the photos, Priya remains the folder-link recipient, both alternatives remain present, and the explicit task survives.

## Declared target comparison

| Probe | Baseline 640 | Group A 640 | Group B 640 | Group C 640 | Baseline 680 | All six 680 |
|---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 05 | **Pass** | Pass | Pass | **Fail** | **Pass** | **Fail** |
| 06 | Fail | Fail | Fail | Fail | Fail | Fail |
| 11 | Fail | Fail | **Pass** | Fail | Fail | Fail |

### Probe 05: a Group C content effect remains the strongest explanation

Probe 05 passes in both unchanged-data step-matched controls. At 640 steps it also passes with Groups A and B, but fails with Group C alone through the same cross-field recipient error seen in the all-six 680-step run. At 680 steps the unchanged baseline again passes while the all-six run fails.

This isolates the additional Probe 05 failure to curriculum content rather than optimizer-step count at seed 17. Because Group C contains only Gold v1.2.3 example 006, that example is the strongest current source candidate. The evidence is still seed-specific; it does not yet prove that example 006 will cause the failure across seeds.

### Probe 06: the apparent group regression is explained by step count at seed 17

Probe 06 fails in both unchanged-data controls and in every content-added comparison. Its failure cannot be attributed to any Gold v1.2.3 group at seed 17. The common 640-step failure that motivated the control is reproduced without any Gold v1.2.3 data.

### Probe 11: the seed-17 failure is also reproduced by training duration

Probe 11 fails in both unchanged-data controls through the same loss of the Thursday qualifier from the action item. Group A and Group C therefore do not provide evidence of a content-caused Probe 11 regression at seed 17. Group B actually passes Probe 11 at the same 640-step budget.

The earlier claim that Probe 11 was the strongest Gold v1.2.3 content-interaction candidate must be withdrawn for seed 17. Its prior multi-seed pattern remains descriptive, but the existing fixed-split comparison confounded curriculum additions with optimizer-step count.

## Full step-matched comparisons

### At 640 steps

| Corpus | Overall | Guards | Difference from unchanged baseline |
|---|---:|---:|---:|
| Gold v1.2.2 unchanged | 9/16 | 8/12 | — |
| + Group A | 10/16 | 9/12 | +1 overall, +1 guard |
| + Group B | 11/16 | 10/12 | +2 overall, +2 guards |
| + Group C | 9/16 | 8/12 | 0 overall, 0 guards |

Group C's unchanged aggregate hides an exact trade: it gains Probe 07 relative to the baseline but loses Probe 05. Groups A and B do not show net degradation at this seed and step budget, although neither is release-eligible.

### At 680 steps

| Corpus | Overall | Guards | Difference from unchanged baseline |
|---|---:|---:|---:|
| Gold v1.2.2 unchanged | 10/16 | 9/12 | — |
| + all six Gold v1.2.3 examples | 9/16 | 8/12 | -1 overall, -1 guard |

The sole strict difference is Probe 05: the unchanged control passes and the all-six run fails. Every other probe has the same pass/fail status.

## Revised interpretation

1. The optimizer-step confound materially changes the earlier account. At seed 17, it explains the observed Probe 06 and Probe 11 failures without any Gold v1.2.3 data.
2. Gold v1.2.3 example 006 remains specifically associated with the Probe 05 recipient regression. That association appears both in the Group C-only 640-step run and the all-six 680-step run against their respective step-matched controls.
3. The earlier aggregate claim that fixed-split Gold v1.2.3 content caused a `35/48 → 31/48` decline is not causally established, because the seed-42 and seed-73 comparisons remain unmatched for optimizer steps.
4. The same-seed step-matched finding is narrower: at seed 17, the full six-example addition causes a one-probe strict loss relative to unchanged data, and that loss is Probe 05.
5. Probe 02, Probe 09, and Probe 16 remain baseline weaknesses. Neither control resolves them.

## Recommended Stage 2

Run a paired Group C confirmation at seeds 42 and 73:

- unchanged Gold v1.2.2 training set, 640 steps
- unchanged Gold v1.2.2 training set plus Group C/example 006, 640 steps
- same frozen validation set and evaluation configuration

Pre-register Probe 05 as the primary outcome. Score the full benchmark and regression-guard count secondarily. Keep Probe 11 descriptive, but do not use it as evidence against example 006 unless the matched baseline passes and the Group C run fails at the same seed.

Decision rule:

- If Group C uniquely breaks Probe 05 at either additional seed, proceed to an example-006 redesign or removal ablation.
- If both paired comparisons show the same Probe 05 status, treat the seed-17 effect as seed-specific and do not rewrite example 006 on that evidence alone.
- Do not add replacement examples until this paired confirmation is complete.

## Ownership

| Action | Owner |
|---|---|
| Run paired 640-step baseline and Group C jobs at seeds 42 and 73 | Claude Code |
| Apply the frozen strict rubric and perform paired comparisons | ChatGPT |
| Approve any example-006 redesign, removal ablation, or release change | Johnny |

## Release status

Release status remains unchanged. Gold v1.2.3 is non-promotable; checkpoint-600 remains the candidate/comparison baseline; checkpoint-520 remains in production. This report changes the causal interpretation, not the deployed model or dataset.
