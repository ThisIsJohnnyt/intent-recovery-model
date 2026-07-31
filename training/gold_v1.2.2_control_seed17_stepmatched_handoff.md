# Gold v1.2.2 Step-Matched Seed-17 Controls (640 / 680 steps) — Results and Configuration

Raw handoff only — no semantic scoring or interpretation applied, per
`gold_v1.2.3_groupscreen_seed17_scoring.md`'s ownership table ("Run the 640-
and 680-step seed-17 baseline controls and provide raw outputs/configuration:
Claude Code" / "Apply the frozen strict rubric and compare the controls with
the group and all-six runs: ChatGPT"). No dataset changes, no curriculum
changes, no edits to example 006. Required before any Stage 2 expansion of
Group C to other seeds, per that report's "Required control before Stage 2"
section.

## What this isolates

The Stage 1 group screen's Groups A/B/C (63/62/61 train examples) and the
earlier six-example ablation (66 train examples) all round up to a different
steps-per-epoch count than the unchanged 60-example `gold_v1.2.2` baseline
(15 steps/epoch → 600 total over 40 epochs), because `train.py` trains for a
fixed epoch count at batch size 4:

| Corpus | Train examples | Steps/epoch | Total steps (40 epochs) |
|---|---:|---:|---:|
| `gold_v1.2.2` baseline | 60 | 15 | 600 |
| Groups A/B/C | 61–63 | 16 | 640 |
| All six `gold_v1.2.3` examples | 66 | 17 | 680 |

So every group-screen/ablation comparison against the baseline was
confounded by both curriculum content *and* total optimizer steps. These two
runs hold content fixed (the unchanged 60-example `gold_v1.2.2` set, same
frozen val) and instead force the step count to match, using a new
`--max-steps` flag added to `train.py` for exactly this purpose (overrides
`num_train_epochs`, including the default linear LR scheduler's
total-steps count, so the LR decay shape matches what the 640/680-step runs
being compared against actually saw).

## Configuration

| Run | Data dir | Seed | `--max-steps` | Train examples | Output |
|---|---|---:|---:|---:|---|
| 640-step control | `data/processed_gold_v1.2.2_control` (unchanged) | 17 | 640 | 60 | `checkpoints/gold_v1.2.2-control-seed17-steps640/final` |
| 680-step control | `data/processed_gold_v1.2.2_control` (unchanged) | 17 | 680 | 60 | `checkpoints/gold_v1.2.2-control-seed17-steps680/final` |

Val (6 examples) verified identical, as a set of records, to the val used in
every other run referenced in this investigation (the fixed-split ablation,
the group screen, and the original `gold_v1.2.2`-only seed-17/73 controls).

Confirmed from the training logs (not assumed): both runs reached exactly
their target step count (640/640 and 680/680), and the logged
`learning_rate` decays to within a few ×10⁻⁷ of zero by the final logged
step in both runs — consistent with the scheduler's total-steps budget
actually being set to 640 and 680 respectively, not derived from the
original 600-step/40-epoch schedule.

## Mechanical results (format validity only — no semantic scoring)

| Run | Format validity |
|---|---:|
| 640-step control | 16/16 |
| 680-step control | 16/16 |

## Raw results files (unscored — `scores`/`capability_checks` left `null`)

- `training/gold_v1.2.2_control_seed17_steps640_results.json`
- `training/gold_v1.2.2_control_seed17_steps680_results.json`

Same schema `run_benchmark.py` always produces. Semantic scoring left `null`
throughout, including for Probes 05, 06, 09, and 11 — the report's declared
comparison points — so as not to pre-empt the frozen-rubric scoring pass.

## Reference: what these compare against

- Group screen (content changed, steps confounded to 640):
  `training/gold_v1.2.3_groupscreen_seed17_group{A,B,C}_results.json`
- All-six ablation (content changed, steps confounded to 680):
  `training/gold_v1.2.3_ablation_fixedsplit_results_seed17.json`
- Original `gold_v1.2.2`-only seed-17 control (600 steps, uncontrolled for
  step count — the baseline these two new runs are meant to supersede for
  step-matched comparison purposes):
  `training/gold_v1.2.2_benchmark_results_seed17_control.json`

Per the report's declared next steps: do not start seed-42/73 Group C
confirmation runs, edit example 006, or construct a replacement curriculum
until these are scored. Release status unchanged: `checkpoint-520` remains
production, `checkpoint-600` remains the candidate/comparison baseline, Gold
v1.2.3 remains non-promotable.
