# Gold v1.2.3 Leave-One-Out (Examples 001–005, No 006) — 680 Steps — Results and Configuration

Raw handoff only — no semantic scoring or interpretation applied, per
`gold_v1.2.3_groupC_seed42_73_stepmatched_scoring.md`'s "Recommended next
experiment" and ownership table ("Run the three 680-step
all-six-minus-006 jobs and the two missing 680-step baselines: Claude
Code" / "Apply the frozen strict rubric to both experiment sets: ChatGPT").
No dataset changes, no curriculum changes, no edits to example 006 — this
run excludes it entirely rather than rewriting it.

## What this isolates

Tests whether removing Gold v1.2.3 example 006 (`dangling_reference`)
restores Probe 05 inside the *complete* Gold v1.2.3 context (examples
001–005 present, so Groups A/B's content is still in training) — as
opposed to the isolated Group C ablation, which only ever tested example
006 alone against the bare baseline. Also completes the 680-step baseline
set: seed 17's 680-step baseline already existed; seeds 42 and 73 did not.

## Configuration

Five runs, all `--max-steps 680` (matching the existing all-six
fixed-split results' step budget), same frozen 6-example val set
throughout (verified identical to every other run in this investigation):

| Run | Data dir | Seed | Train examples | Output |
|---|---|---:|---:|---|
| Baseline (missing) | `data/processed_gold_v1.2.2_control` (unchanged, 60) | 42 | 60 | `checkpoints/gold_v1.2.2-control-seed42-steps680/final` |
| Baseline (missing) | `data/processed_gold_v1.2.2_control` (unchanged, 60) | 73 | 60 | `checkpoints/gold_v1.2.2-control-seed73-steps680/final` |
| Minus-006 | `data/processed_gold_v1.2.3_minus006` (60 baseline + examples 001–005, new) | 17 | 65 | `checkpoints/gold_v1.2.3-minus006-seed17-steps680/final` |
| Minus-006 | `data/processed_gold_v1.2.3_minus006` | 42 | 65 | `checkpoints/gold_v1.2.3-minus006-seed42-steps680/final` |
| Minus-006 | `data/processed_gold_v1.2.3_minus006` | 73 | 65 | `checkpoints/gold_v1.2.3-minus006-seed73-steps680/final` |

Confirmed from the training logs (not assumed): all five runs reached
exactly 680/680 steps.

## Mechanical results (format validity only — no semantic scoring)

| Run | Format validity |
|---|---:|
| Baseline, seed 42 | 16/16 |
| Baseline, seed 73 | 16/16 |
| Minus-006, seed 17 | 16/16 |
| Minus-006, seed 42 | 16/16 |
| Minus-006, seed 73 | 16/16 |

## Raw results files (unscored — `scores`/`capability_checks` left `null`)

- `training/gold_v1.2.2_control_seed42_steps680_results.json`
- `training/gold_v1.2.2_control_seed73_steps680_results.json`
- `training/gold_v1.2.3_minus006_seed17_steps680_results.json`
- `training/gold_v1.2.3_minus006_seed42_steps680_results.json`
- `training/gold_v1.2.3_minus006_seed73_steps680_results.json`

Same schema `run_benchmark.py` always produces. Semantic scoring left
`null` throughout, including for the report's declared outcomes (Probe 05
primary, Probe 12 collateral guard, Probe 16 intended target).

## Reference: what these compare against

- Existing 680-step all-six-example results (the full bundle this
  leave-one-out is meant to be compared against, same seeds/step budget):
  `training/gold_v1.2.3_ablation_fixedsplit_results_seed{17,42,73}.json`,
  `training/gold_v1.2.3_benchmark_results_checkpoint680.json` (seed 42).
- Seed 17's 680-step baseline (already existed, not rerun here):
  `training/gold_v1.2.2_control_seed17_steps680_results.json`.

Per the report's standing instruction: do not author a replacement
`dangling_reference` example until this is scored. Release status
unchanged: `checkpoint-520` remains production, `checkpoint-600` remains
the candidate/comparison baseline, Gold v1.2.3 remains non-promotable.
