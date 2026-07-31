# Fixed-Common-Split Ablation — Results and Split Details

Raw handoff only — no semantic scoring or interpretation applied, per the
agreed division of labor (product owner + ChatGPT analyze and lead the
curriculum audits from here). No new Gold examples were authored. This
run only recombines existing content: the original `gold_v1.2.2`
train/val partition (unchanged) plus the existing `gold_v1.2.3.jsonl`
examples (unchanged), added to train only.

## What this ablation controls for

The split-delta report (`gold_v1.2.3_split_delta_report.md`) found that
the prior `gold_v1.2.2`-vs-`gold_v1.2.3` comparison wasn't a clean
single-variable test: going from the 66-example to the 72-example corpus
re-shuffled the whole list, reassigning 9 of the original 66 examples
between train and val — not just adding 6 new ones. This ablation removes
that confound.

## Exact split composition

- **Val (6 examples): byte-identical to the `gold_v1.2.2`-only control
  run's `val.jsonl`.** Verified programmatically (`assert control_val_text
  == new_val_text`) before training began — see
  `training/data/processed_gold_v1.2.3_fixedsplit/val.jsonl` vs.
  `training/data/processed_gold_v1.2.2_control/val.jsonl`.
- **Train (66 examples) = the original fixed 60 `gold_v1.2.2` train
  examples (unchanged, same order) + all 6 `gold_v1.2.3` examples
  (appended, transformed via `prepare_data.py`'s own `validate_record`/
  `build_prompt`, unchanged from `datasets/gold/gold_v1.2.3.jsonl`).**

Nothing was removed from training. Nothing moved between train and val.
The only variable changed relative to the `gold_v1.2.2`-only control run
is: are `gold_v1.2.3`'s 6 examples present in training or not.

## Checkpoint-retention safeguard added first

Per the instruction to add safeguards before running this. `train.py`
now refuses to write into a non-empty `--output-dir` unless `--force` is
passed explicitly (tested — confirmed it blocks reuse of an existing
checkpoint dir). This directly addresses how `checkpoint-520` and the
original `checkpoint-600` were both silently lost earlier in this
investigation (pruned by `save_total_limit` via output-dir reuse).

Checkpoints trained this round, each in its own dedicated directory:
- `training/checkpoints/gold_v1.2.3-ablation-fixedsplit-seed42/final`
- `training/checkpoints/gold_v1.2.3-ablation-fixedsplit-seed17/final`
- `training/checkpoints/gold_v1.2.3-ablation-fixedsplit-seed73/final`

## Mechanical results (format validity only — no semantic scoring)

| Seed | Format validity | Notes |
|---|---|---|
| 42 | 15/16 | Probe 05 fails format validity — degenerates into a repetition loop in `###BULLETS###` and never emits `###ACTIONS###` at all (cut off at the 300-token generation limit). Raw text in the results file. |
| 17 | 16/16 | — |
| 73 | 16/16 | — |

## Raw results files (unscored — `scores`/`capability_checks` left `null`)

- `training/gold_v1.2.3_ablation_fixedsplit_results_seed42.json`
- `training/gold_v1.2.3_ablation_fixedsplit_results_seed17.json`
- `training/gold_v1.2.3_ablation_fixedsplit_results_seed73.json`

Each contains all 16 probes' raw model output plus mechanically-computed
`format_valid`, in the same schema `run_benchmark.py` always produces.
Semantic scoring (`scores`, `capability_checks`, `failure_labels`) is left
`null` throughout — intentionally not filled in this round.

## Reference: prior results, for comparison once scored

- `gold_v1.2.2`-only control (same fixed val, 60 train, no `gold_v1.2.3`
  content): `training/gold_v1.2.2_benchmark_results_seed17_control.json`,
  `..._seed73_control.json`, and the original `checkpoint-600` result
  (`training/gold_v1.2.2_benchmark_results_checkpoint600.json`, seed 42
  implicitly).
- `gold_v1.2.3` reshuffled corpus (confounded — different val,
  different train membership beyond the 6 additions):
  `training/gold_v1.2.3_benchmark_results_seed{17,42,73}.json`.

No dataset, pipeline, or curriculum changes made beyond what's described
above (the ablation data construction and the `train.py` safeguard).
