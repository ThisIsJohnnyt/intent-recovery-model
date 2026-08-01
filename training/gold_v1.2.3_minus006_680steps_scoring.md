# Gold v1.2.3 Minus-006 and 680-Step Baselines — Strict Scoring

## Purpose

This report applies the frozen strict benchmark rubric to:

- the missing unchanged Gold v1.2.2 680-step baselines at seeds 42 and 73; and
- the Gold v1.2.3 leave-one-out corpus containing examples 001–005 but excluding example 006, at seeds 17, 42, and 73.

It completes two paired analyses:

1. unchanged Gold v1.2.2 versus the full six-example Gold v1.2.3 bundle at the same 680-step budget; and
2. the full six-example bundle versus the same bundle without example 006 at the same seeds and step budget.

Probe 05 is the pre-registered primary outcome for the leave-one-out comparison. Probe 12 is the collateral guard, and Probe 16 is example 006's intended target. All five new runs reached 680/680 steps and 16/16 format validity.

## New-run aggregate results

| Run | Overall | Regression guards | Negative examples | Format validity |
|---|---:|---:|---:|---:|
| Baseline, seed 42 | 10/16 | 9/12 | 1/4 | 16/16 |
| Baseline, seed 73 | 10/16 | 9/12 | 1/4 | 16/16 |
| Minus 006, seed 17 | 8/16 | 8/12 | 0/4 | 16/16 |
| Minus 006, seed 42 | 10/16 | 9/12 | 1/4 | 16/16 |
| Minus 006, seed 73 | 10/16 | 9/12 | 1/4 | 16/16 |

None of the runs is candidate-eligible.

## Probe-level strict results

| Probe | Baseline 42 | Baseline 73 | Minus 006 — 17 | Minus 006 — 42 | Minus 006 — 73 |
|---:|:---:|:---:|:---:|:---:|:---:|
| 01 | Pass | Pass | Pass | Pass | Pass |
| 02 | Fail | Fail | Fail | Fail | Fail |
| 03 | Pass | Pass | **Fail** | Pass | Pass |
| 04 | Pass | Pass | Pass | Pass | Pass |
| 05 | Pass | Pass | **Fail** | Pass | **Fail** |
| 06 | Fail | Fail | Fail | Fail | Fail |
| 07 | Pass | Pass | Pass | Pass | Pass |
| 08 | Fail | Fail | Fail | Fail | Fail |
| 09 | Fail | Fail | Fail | Fail | Fail |
| 10 | Pass | Pass | Pass | Pass | Pass |
| 11 | Fail | Fail | **Pass** | Fail | **Pass** |
| 12 | Pass | Pass | **Fail** | Pass | Pass |
| 13 | Pass | Pass | Pass | Pass | Pass |
| 14 | Pass | Pass | Pass | Pass | Pass |
| 15 | Pass | Pass | Pass | Pass | Pass |
| 16 | Fail | Fail | Fail | Fail | Fail |

## Failure rationale for the new 680-step baselines

Both new baselines fail the same six probes: 02, 06, 08, 09, 11, and 16.

### Baseline seed 42

- **Probe 02:** The tablet causal chain remains fragmented, the return phrase becomes a tautological action, and the charger behavior is labeled unrelated.
- **Probe 06:** A bullet misattributes Tessa's earlier permit question to Rowan.
- **Probe 08:** The output invents "a lack of moisture" and incorrectly says the plant should be put outside.
- **Probe 09:** The unfinished volunteer-list fragment is promoted into a checking task.
- **Probe 11:** The narrative attaches the writer's fatigue to the garage light as though the light "feels tired."
- **Probe 16:** The output adds the unsupported assertion that both referents are unrelated.

### Baseline seed 73

- **Probe 02:** The charger-movement cause is not connected to the tablet investigation.
- **Probe 06:** The earlier permit question is attributed to Rowan.
- **Probe 08:** The alternatives are merged with the later drying observation.
- **Probe 09:** The volunteer-list fragment is promoted into a question/check and incorrectly connected to the sent-mail action.
- **Probe 11:** The Thursday deadline drops from the fee action.
- **Probe 16:** Unsupported referent commentary is added.

Together with the previously scored seed-17 control, all three unchanged 680-step baselines have the identical strict result: 10/16 overall, 9/12 guards, and 1/4 negative examples.

## Failure rationale for the minus-006 runs

### Minus 006, seed 17

- **Probe 02:** The return phrase becomes tautological semantic content and the donation-box task drops from the action list.
- **Probe 03:** The combined Celia task is duplicated into a second "Check the cable" instruction, violating the unsplit-task requirement.
- **Probe 05:** The narrative changes the folder-link recipient from Priya to Cole.
- **Probe 06:** A bullet attributes the earlier permit question to Rowan.
- **Probe 08:** The source alternatives remain confusingly merged with the drying observation.
- **Probe 09:** The volunteer-list fragment gains unsupported task-like commentary and is incorrectly connected to the sent-mail check.
- **Probe 12:** The oil-change task disappears from the narrative and action list.
- **Probe 16:** Unsupported referent commentary is added.

### Minus 006, seed 42

- **Probe 02:** The output fabricates "the computer" and treats the return marker as content.
- **Probe 06:** The earlier permit question is attributed to Rowan.
- **Probe 08:** The output invents a lack-of-water explanation and changes which thing was dry.
- **Probe 09:** The unfinished volunteer-list fragment is promoted into a consideration task.
- **Probe 11:** The Thursday deadline drops from the narrative and action item.
- **Probe 16:** Unsupported referent commentary is added.

### Minus 006, seed 73

- **Probe 02:** The return phrase becomes a tautological action and the charger cause remains disconnected.
- **Probe 05:** The narrative changes the folder-link recipient from Priya to Cole.
- **Probe 06:** A bullet attributes the earlier permit question to Rowan.
- **Probe 08:** The output invents a causal relationship between the drying observation and recycling.
- **Probe 09:** The unfinished volunteer-list fragment is promoted into a checking task.
- **Probe 16:** Unsupported referent commentary is added.

The malformed form "backped up" remains classified as a surface-generation error rather than a semantic failure. Probe 05 fails only when the supported folder-link recipient changes from Priya to Cole.

## Complete 680-step baseline comparison

| Corpus | Overall | Regression guards | Negative examples |
|---|---:|---:|---:|
| Unchanged Gold v1.2.2 | 30/48 | 27/36 | 3/12 |
| Baseline + all six Gold v1.2.3 examples | 31/48 | 27/36 | 4/12 |
| Difference | +1 | 0 | +1 |

The unchanged 680-step baseline is perfectly stable across the three seeds: each passes Probes 01, 03, 04, 05, 07, 10, 12, 13, 14, and 15, and fails Probes 02, 06, 08, 09, 11, and 16.

The full bundle changes four probe pass counts relative to that step-matched baseline:

| Probe | Baseline passes | All-six passes | Difference |
|---:|---:|---:|---:|
| 05 | 3/3 | 1/3 | -2 |
| 06 | 0/3 | 1/3 | +1 |
| 08 | 0/3 | 1/3 | +1 |
| 11 | 0/3 | 1/3 | +1 |

All other probes are unchanged. Therefore the Gold v1.2.3 content does not produce the previously claimed aggregate fixed-split decline when optimizer steps are matched. It produces a net gain of one strict pass, while trading two Probe 05 losses for one gain each on Probes 06, 08, and 11. The bundle remains unsuitable for promotion because the gains are unstable, Probe 05 degrades materially, and targets 02 and 16 remain unresolved.

## Leave-one-out comparison: all six versus minus 006

| Corpus | Overall | Regression guards | Negative examples |
|---|---:|---:|---:|
| All six examples | 31/48 | 27/36 | 4/12 |
| Examples 001–005 only | 28/48 | 26/36 | 2/12 |
| Removing example 006 | -3 | -1 | -2 |

Six probes show a seed-level or aggregate change; Probe 05 changes which seed passes while retaining the same 1/3 aggregate:

| Probe | All-six passes | Minus-006 passes | Change after removal |
|---:|---:|---:|---:|
| 03 | 3/3 | 2/3 | -1 |
| 05 | 1/3 | 1/3 | 0 |
| 06 | 1/3 | 0/3 | -1 |
| 08 | 1/3 | 0/3 | -1 |
| 11 | 1/3 | 2/3 | +1 |
| 12 | 3/3 | 2/3 | -1 |

The net change is negative three because four passes are lost and one is gained.

### Pre-registered Probe 05 outcome

Removing example 006 does not restore Probe 05:

| Seed | All six | Minus 006 |
|---:|:---:|:---:|
| 17 | Fail | Fail |
| 42 | Fail | Pass |
| 73 | Pass | Fail |
| **Aggregate** | **1/3** | **1/3** |

The passing seed changes, but failure frequency does not. This directly contradicts a simple account in which example 006 is independently responsible for the full bundle's Probe 05 regression.

### Probe 12 collateral outcome

Probe 12 changes from 3/3 with all six examples to 2/3 after example 006 is removed. The removal creates rather than repairs the pre-registered collateral loss in the full-bundle context.

### Probe 16 intended target

Probe 16 remains 0/3 with and without example 006. The example provides no measured benefit on its intended benchmark target, but its removal also provides no benefit.

## Reconciliation with the isolated Group C result

The isolated 640-step Group C experiment showed that adding example 006 to the bare Gold v1.2.2 baseline changed Probe 05 from pass to fail at seeds 17 and 73. The 680-step leave-one-out experiment shows that removing the same example from the full Gold v1.2.3 bundle does not improve Probe 05 frequency and worsens aggregate performance.

These findings are not interchangeable:

- the isolated experiment estimates example 006's behavior against the baseline corpus at 640 steps;
- the leave-one-out experiment estimates its behavior in the presence of examples 001–005 at 680 steps.

Together they establish a seed-, context-, and training-budget-dependent interaction. They do not support treating example 006 as a universally harmful example or its removal as a validated corrective action.

## Revised conclusions

1. The earlier recommendation to retire example 006 based on the isolated Group C screen is superseded.
2. Example 006 is not validated as an effective dangling-reference correction because Probe 16 remains 0/3.
3. Removing example 006 is also not validated: it leaves Probe 05 at 1/3 and reduces the bundle from 31/48 to 28/48.
4. The previously reported `35/48 → 31/48` fixed-split content decline was primarily a training-budget comparison error. At the correct matched 680-step budget, the comparison is `30/48 → 31/48`.
5. Fixed epoch counts are unsuitable for curriculum-causality experiments at this data scale because changing dataset size changes optimizer-step count. Future ablations should pre-register and hold `max_steps` constant.
6. Gold v1.2.3 remains non-promotable despite the revised causal account.

## ChatGPT recommended action

- Preserve Gold v1.2.3 and example 006 unchanged as rejected historical evidence.
- Do not carry example 006 unchanged into a new candidate, because it has no demonstrated Probe 16 benefit.
- Do not treat simple removal as the Probe 05 correction; the leave-one-out result rejects that approach.
- Stop further example-level salvage ablations on this six-example bundle unless Claude identifies a specific unresolved hypothesis that would change a concrete decision.
- Adopt fixed-step, multi-seed comparisons as the required protocol for future curriculum experiments.
- Shift the next dataset effort away from wording iteration on these six examples and toward the already proposed real-validation/sealed-holdout workflow, followed by a newly scoped curriculum only after the evaluation foundation is in place.

## Alignment status

**Aligned.** Claude Code independently re-derived every probe-level call in the five new result files against each probe's `expected_behavior` (80 probe-instances total), and independently re-verified the aggregate/difference tables against raw data already checked in earlier reports in this investigation (the fixed-split ablation, the seed-17 step-matched controls, and the seed-42/73 paired confirmation). All numbers and probe-level calls reconcile exactly, including the subtle finding that Probe 05's passing seed differs between the all-six run (seed 73) and the minus-006 run (seed 42) while the aggregate stays 1/3 in both. No disagreement to raise.

## Ownership

| Action | Owner |
|---|---|
| Independently review the scoring and recommendation; report alignment status | Claude Code |
| Resolve any scoring disagreement with evidence from the frozen rubric | ChatGPT and Claude Code |
| Decide only if alignment remains unresolved | Johnny |
| Commit and push the complete investigation after alignment | Claude Code |

## Release status

Gold v1.2.3 remains non-promotable. Checkpoint-600 remains the candidate/comparison baseline, and checkpoint-520 remains in production. No training example or deployed artifact changes as a result of this report.
