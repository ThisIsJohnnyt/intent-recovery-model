# Gold v1.2.3 Group C Paired Confirmation — Seeds 42 & 73, 640 Steps

Raw handoff only — no semantic scoring or interpretation applied, per
`gold_v1.2.2_control_seed17_stepmatched_scoring.md`'s "Recommended Stage 2"
and ownership table ("Run paired 640-step baseline and Group C jobs at
seeds 42 and 73: Claude Code" / "Apply the frozen strict rubric and perform
paired comparisons: ChatGPT"). No dataset changes, no curriculum changes,
no edits to example 006.

## Configuration

Four runs, all `--max-steps 640`, same frozen 6-example val set throughout:

| Run | Data dir | Seed | Train examples | Output |
|---|---|---:|---:|---|
| Baseline | `data/processed_gold_v1.2.2_control` (unchanged) | 42 | 60 | `checkpoints/gold_v1.2.2-control-seed42-steps640/final` |
| Baseline | `data/processed_gold_v1.2.2_control` (unchanged) | 73 | 60 | `checkpoints/gold_v1.2.2-control-seed73-steps640/final` |
| Group C | `data/processed_gold_v1.2.3_groupscreen_seed17_groupC` (reused as-is — content is seed-independent, only example 006 added) | 42 | 61 | `checkpoints/gold_v1.2.3-groupC-seed42-steps640/final` |
| Group C | `data/processed_gold_v1.2.3_groupscreen_seed17_groupC` (reused as-is) | 73 | 61 | `checkpoints/gold_v1.2.3-groupC-seed73-steps640/final` |

Confirmed from the training logs (not assumed): all four runs reached
exactly 640/640 steps.

## Mechanical results (format validity only — no semantic scoring)

| Run | Format validity |
|---|---:|
| Baseline, seed 42 | 16/16 |
| Baseline, seed 73 | 16/16 |
| Group C, seed 42 | 16/16 |
| Group C, seed 73 | 16/16 |

## Raw results files (unscored — `scores`/`capability_checks` left `null`)

- `training/gold_v1.2.2_control_seed42_steps640_results.json`
- `training/gold_v1.2.2_control_seed73_steps640_results.json`
- `training/gold_v1.2.3_groupC_seed42_steps640_results.json`
- `training/gold_v1.2.3_groupC_seed73_steps640_results.json`

## Flagging one raw-text detail before scoring (not a scored verdict)

Since Probe 05 is the pre-registered primary outcome here, this seemed
worth surfacing directly rather than leaving it to be found during
scoring: the **baseline** (unchanged data, no example 006) run at **seed
42** already produces the same narrative-field wording this investigation
has been treating as Group C's signature failure —

> `"...Cole needs to be sent the folder link..."`

— while its `###BULLETS###`/`###ACTIONS###` correctly say Priya (same
cross-field shape as every prior Cole/Priya finding in this investigation).
The **seed 73** baseline instead reads `"The folder link needs to be sent
to Priya"` in the narrative — clean, matching the seed-17 baseline's
earlier clean result. Both Group C runs (seed 42 and seed 73) show the
Cole-in-narrative wording.

Raw narrative field, all four, for direct comparison:

| Run | Probe 05 narrative (folder-link clause only) |
|---|---|
| Baseline, seed 42 | "Cole needs to be sent the folder link" |
| Baseline, seed 73 | "The folder link needs to be sent to Priya" |
| Group C, seed 42 | "Cole needs to be sent the folder link" |
| Group C, seed 73 | "Cole needs to be sent the folder link" |

Full raw output for all 16 probes, both runs, is in the result files above
for the frozen rubric to be applied directly — this section only points at
where to look, it doesn't apply the rubric.

## Reference

- Seed-17 pairing this confirms/extends:
  `training/gold_v1.2.2_control_seed17_steps640_results.json` (baseline) vs.
  `training/gold_v1.2.3_groupscreen_seed17_groupC_results.json` (Group C).

Per the report's decision rule: do not begin an example-006 redesign or
removal ablation, and do not add replacement examples, until this paired
confirmation is scored. Release status unchanged: `checkpoint-520` remains
production, `checkpoint-600` remains the candidate/comparison baseline,
Gold v1.2.3 remains non-promotable.
