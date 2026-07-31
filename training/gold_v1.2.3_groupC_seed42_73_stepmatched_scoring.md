# Gold v1.2.3 Group C Paired Confirmation — Seeds 42 and 73 Strict Scoring

## Purpose

This report applies the frozen strict benchmark rubric to the paired 640-step Gold v1.2.2 baseline and Group C runs at seeds 42 and 73. It then combines those results with the previously scored seed-17 pair.

The pre-registered primary outcome is Probe 05. Full strict pass rate and regression-guard count are secondary outcomes. Probe 11 remains descriptive and is not attributed to Group C unless a same-seed baseline passes while Group C fails.

All four new runs reached exactly 640 optimizer steps and 16/16 format validity. No dataset, curriculum, validation, benchmark, or decoding change is introduced by this report.

## New-run aggregate results

| Seed | Corpus | Overall | Regression guards | Negative examples | Format validity |
|---:|---|---:|---:|---:|---:|
| 42 | Gold v1.2.2 baseline | 9/16 | 8/12 | 1/4 | 16/16 |
| 42 | Baseline + Group C/example 006 | 9/16 | 8/12 | 1/4 | 16/16 |
| 73 | Gold v1.2.2 baseline | 10/16 | 9/12 | 1/4 | 16/16 |
| 73 | Baseline + Group C/example 006 | 8/16 | 7/12 | 1/4 | 16/16 |

None of the runs is candidate-eligible.

## Probe-level strict results

| Probe | Seed 42 baseline | Seed 42 + Group C | Seed 73 baseline | Seed 73 + Group C |
|---:|:---:|:---:|:---:|:---:|
| 01 | Pass | Pass | Pass | Pass |
| 02 | Fail | Fail | Fail | Fail |
| 03 | Pass | Pass | Pass | Pass |
| 04 | Pass | Pass | Pass | Pass |
| 05 | **Fail** | **Fail** | **Pass** | **Fail** |
| 06 | Fail | Fail | Fail | Fail |
| 07 | Pass | Pass | Pass | Pass |
| 08 | Fail | Fail | Fail | Fail |
| 09 | Fail | Fail | Fail | Fail |
| 10 | Pass | Pass | Pass | Pass |
| 11 | Fail | Fail | Fail | Fail |
| 12 | Pass | Pass | **Pass** | **Fail** |
| 13 | Pass | Pass | Pass | Pass |
| 14 | Pass | Pass | Pass | Pass |
| 15 | Pass | Pass | Pass | Pass |
| 16 | Fail | Fail | Fail | Fail |

## Failure rationale

### Seed 42 baseline

- **Probe 02:** The return phrase becomes semantic content, producing a tautological tablet action; the charger-movement cause remains disconnected.
- **Probe 05:** The narrative says Cole should receive the folder link while bullets and actions correctly name Priya.
- **Probe 06:** The narrative says the inspector should be asked who needs the copy, conflicting with the supported Rowan action retained elsewhere.
- **Probe 08:** The source alternatives are merged with the later drying observation into a confusing question.
- **Probe 09:** The unfinished volunteer-list fragment is promoted into something that "needs to be considered."
- **Probe 11:** The actions lose both the Thursday fee deadline and the content of the Jonah message.
- **Probe 16:** Unsupported referent commentary is added instead of stopping after the supported reminder.

### Seed 42 Group C

- **Probe 02:** The output fabricates "the computer," treats the return marker as content, and fails to reconnect the charger cause.
- **Probe 05:** The same Cole/Priya cross-field recipient error appears as in the baseline.
- **Probe 06:** The earlier permit question is attributed to Rowan, and Rowan is incorrectly asserted to need the stamped copy.
- **Probe 08:** The alternatives are reduced to the tautological question of whether the wet spot "was the plant."
- **Probe 09:** The incomplete volunteer-list fragment becomes a consideration task.
- **Probe 11:** The actions drop the Thursday deadline and the content of the Jonah reply.
- **Probe 16:** The output invents a plural-person referent and adds unsupported commentary.

### Seed 73 baseline

- **Probe 02:** The tablet symptom and donation task survive, but the charger-movement condition is dropped rather than reconnected.
- **Probe 06:** The earlier permit question is attributed to Rowan, and the stamped-copy ambiguity becomes garbled.
- **Probe 08:** The alternatives are again merged with the later drying observation.
- **Probe 09:** The volunteer-list fragment is promoted into a checking task and incorrectly connected to the sent-mail check.
- **Probe 11:** The Thursday fee deadline drops from the action item.
- **Probe 16:** Unsupported referent commentary is added.

### Seed 73 Group C

- **Probe 02:** The return phrase becomes a tautological unresolved question, and the charger cause is not reconnected.
- **Probe 05:** The narrative changes the supported folder-link recipient from Priya to Cole.
- **Probe 06:** The earlier question is attributed to Rowan, and Rowan is incorrectly asserted to need the copy.
- **Probe 08:** The alternatives are merged with the drying observation, and the recycling task becomes the unsupported action "Check the recycling."
- **Probe 09:** The output invents an overwhelmed emotional state and an unsupported action to send the schedule.
- **Probe 11:** The Thursday deadline drops from the narrative and action item.
- **Probe 12:** The output drops the oil-change task from the narrative and falsely attaches the room-temperature observation to it as "Oil change was too warm."
- **Probe 16:** The output invents a relationship among the unresolved referents and adds commentary.

The repeated malformed form "backped up" is treated consistently as a surface-generation error rather than a semantic failure. It does not change who backed up the photos, the two unresolved alternatives, or the explicit folder-link task. Probe 05 fails only when the folder-link recipient changes from Priya to Cole.

## Paired classification for the pre-registered Probe 05 outcome

| Seed | Baseline | Group C | Classification |
|---:|:---:|:---:|---|
| 17 | Pass | Fail | Group C uniquely breaks Probe 05 |
| 42 | Fail | Fail | Tie; failure already present without example 006 |
| 73 | Pass | Fail | Group C uniquely breaks Probe 05 |

The seed-42 result is not attributable to Group C. It demonstrates that the Cole/Priya error can arise from the unchanged Gold v1.2.2 corpus at this training duration. Seed 73 nevertheless satisfies the pre-registered decision rule, and together with seed 17 provides two same-seed matched replications in which adding example 006 changes Probe 05 from pass to fail.

## Three-seed paired synthesis at 640 steps

| Corpus | Overall | Regression guards | Negative examples |
|---|---:|---:|---:|
| Unchanged Gold v1.2.2 baseline | 28/48 | 25/36 | 3/12 |
| Baseline + Group C/example 006 | 26/48 | 23/36 | 3/12 |
| Difference | -2 | -2 | 0 |

Only three probe statuses differ across the paired seed set:

| Probe | Baseline passes | Group C passes | Difference | Interpretation |
|---:|---:|---:|---:|---|
| 05 | 2/3 | 0/3 | -2 | Repeated recipient-attribution regression |
| 07 | 2/3 | 3/3 | +1 | One seed-specific gain |
| 12 | 3/3 | 2/3 | -1 | One collateral attribution/completeness regression |

Every other probe has the same strict pass count under the paired conditions.

## Example 006 decision

Gold v1.2.3 example 006 is not suitable for promotion in its current form:

- Its intended target, Probe 16, remains 0/3 under both the baseline and Group C conditions. No measured target benefit appears.
- It changes Probe 05 from pass to fail at two of three matched seeds and makes that failure stable at 0/3.
- It introduces an additional Probe 12 failure at seed 73.
- Its one measured gain is Probe 07 at seed 17, outside the example's intended category.

This is sufficient to proceed under the pre-registered decision rule. The finding is not that example 006 is the only possible source of the Cole/Priya error; seed 42 disproves that stronger claim. The supported finding is that adding example 006 increases the error's frequency and stability under the tested 640-step configuration.

## Training-duration finding

The paired work also reveals a larger training-protocol effect. The unchanged Gold v1.2.2 corpus scored 35/48 across the original 600-step controls but only 28/48 across the new 640-step controls.

| Probe | Baseline at 600 steps | Baseline at 640 steps | Change |
|---:|---:|---:|---:|
| 05 | 3/3 | 2/3 | -1 |
| 06 | 2/3 | 0/3 | -2 |
| 07 | 3/3 | 2/3 | -1 |
| 09 | 1/3 | 0/3 | -1 |
| 10 | 2/3 | 3/3 | +1 |
| 11 | 3/3 | 0/3 | -3 |
| **Overall** | **35/48** | **28/48** | **-7** |

All other probe pass counts remain unchanged. In particular, Probe 11's apparent Gold v1.2.3 regression is reproduced at every seed by adding 40 optimizer steps to unchanged Gold v1.2.2 training. Dataset-size changes must therefore be step-matched in future curriculum ablations; fixed epochs alone do not isolate content effects at this scale.

## Recommended next experiment

Run a leave-one-out ablation containing Gold v1.2.3 examples 001–005 but excluding example 006.

- Use the frozen Gold v1.2.2 train/validation split.
- Run seeds 17, 42, and 73 at exactly 680 steps, matching the existing all-six fixed-split runs.
- Compare all-six-minus-006 directly with the existing all-six results at the same seed and step budget.
- Pre-register Probe 05 as primary, Probe 12 as the collateral guard, and Probe 16 as the intended target.
- Score the full benchmark and guard count secondarily.

This determines whether removing example 006 restores Probe 05 inside the complete Gold v1.2.3 context, where Groups A and B may interact with it. Do not author a replacement dangling-reference example until this leave-one-out result is scored.

Separately, to finish estimating the full six-example bundle's content effect, run unchanged Gold v1.2.2 680-step controls at seeds 42 and 73. The corresponding all-six 680-step outputs already exist. These two baseline jobs and the three leave-one-out jobs may run in parallel if compute permits.

## Ownership

| Action | Owner |
|---|---|
| Commit and push the four raw paired runs, handoff, and this scoring report as investigation evidence | Claude Code |
| Run the three 680-step all-six-minus-006 jobs and the two missing 680-step baselines | Claude Code |
| Apply the frozen strict rubric to both experiment sets | ChatGPT |
| Approve any replacement for example 006 or broader training-protocol change | Johnny |

## Release status

Gold v1.2.3 remains non-promotable. Example 006 remains in the historical rejected bundle for reproducibility but should not be carried into a new candidate unchanged. Checkpoint-600 remains the candidate/comparison baseline, and checkpoint-520 remains in production.
