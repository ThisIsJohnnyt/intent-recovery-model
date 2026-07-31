# Gold v1.2.3 Stage 1 Group Screen (Seed 17) — Results and Split Details

Raw handoff only — no semantic scoring or interpretation applied, per the
agreed division of labor (product owner + ChatGPT score and interpret
group-ablation outputs from here, per
`gold_v1.2.3_probe11_05_conflict_audit.md` section 12's ownership table).
No new Gold examples were authored, and no existing Gold v1.2.3 example was
edited. This is Stage 1 of the audit's recommended next experiment (section
10): a seed-17-only screen of whether one category group alone is
sufficient to reproduce the Probe 11/05 fixed-split regressions.

## Configuration

Three training corpora, each = the frozen 60-example `gold_v1.2.2` train
set (unchanged, same order) plus one category-group subset of
`gold_v1.2.3`'s 6 examples, all built from the same `split_manifest.json`
used everywhere else (see `training/split_manifest.json` and the commit
that introduced it). Val is the same frozen 6-example set in all three
configurations — verified identical as a set of records across all three
(and against the fixed-split ablation's own val) before training began.

| Config | Group examples added | Category | Train size |
|---|---|---|---:|
| Group A | `gold_v1.2.3` examples 001–003 | `interrupted_thought_depth` | 63 |
| Group B | `gold_v1.2.3` examples 004–005 | `open_question_preservation` | 62 |
| Group C | `gold_v1.2.3` example 006 | `dangling_reference` | 61 |

All three trained at `--seed 17` only (per the audit's own dispatch rule:
seed 17 is where both Probe 11 and Probe 05 fail in the all-six
fixed-split model, so it's the first screen). Checkpoints, each in its own
dedicated directory (respecting `train.py`'s non-empty-output-dir
safeguard):

- `training/checkpoints/gold_v1.2.3-groupscreen-seed17-groupA/final`
- `training/checkpoints/gold_v1.2.3-groupscreen-seed17-groupB/final`
- `training/checkpoints/gold_v1.2.3-groupscreen-seed17-groupC/final`

## Mechanical results (format validity only — no semantic scoring)

| Config | Format validity |
|---|---:|
| Group A | 16/16 |
| Group B | 16/16 |
| Group C | 16/16 |

## Raw results files (unscored — `scores`/`capability_checks` left `null`)

- `training/gold_v1.2.3_groupscreen_seed17_groupA_results.json`
- `training/gold_v1.2.3_groupscreen_seed17_groupB_results.json`
- `training/gold_v1.2.3_groupscreen_seed17_groupC_results.json`

Each contains all 16 probes' raw model output plus mechanically-computed
`format_valid`, in the same schema `run_benchmark.py` always produces.
Semantic scoring (`scores`, `capability_checks`, `failure_labels`) is left
`null` throughout, for Probes 11 and 05 specifically as well as the
regression-guard suite generally — intentionally not filled in this round,
consistent with the audit's declared outcomes (Probe 11 behavior, Probe 05
behavior, and regression-guard count) and its warning not to choose a
group based on unrelated probe gains.

## Reference: prior results, for comparison once scored

- All-six fixed-split, seed 17 (the configuration these three group
  screens decompose):
  `training/gold_v1.2.3_ablation_fixedsplit_results_seed17.json`.
- `gold_v1.2.2`-only, no `gold_v1.2.3` content, seed 17 control:
  `training/gold_v1.2.2_benchmark_results_seed17_control.json`.

No dataset, pipeline, or curriculum changes made beyond what's described
above (the three group corpora and their training/benchmark runs). Per
the audit's standing instruction: no Gold v1.2.3 example edited, no Gold
v1.2.4 authored, checkpoint-520 remains production, checkpoint-600 remains
the comparison baseline.
