# Seed-17 v2-Contract Representation Study — Provenance

**Date:** 2026-08-03
**Authorized by:** Johnny, "as I am Johnny, I hereby authorize the compute based on alignment from both Claude and GPT" -- following ChatGPT's recommendation to authorize "the single seed-17 v2 representation study under the frozen design," which listed: mechanically migrated 66-example corpus only, no corrective curriculum examples, explicit `--contract=v2`, protected 16-probe benchmark plus ten-case v2 acceptance set, strict semantic and structural scoring, seed 73 remains blocked unless seed 17 passes every gate.
**Scope:** seed 17 only. Seed 73 explicitly blocked pending this seed's outcome.

## Two gaps found and resolved before any compute

1. **No v2-aware training-data pipeline existed.** `prepare_data.py`/`train.py` were (and remain) hardcoded to the v1 bare-newline contract -- all of the adapter work through this whole effort covered generation (`run_benchmark.py`) and scoring (`report_benchmark.py`) under `--contract=v2`, never training-data preparation. Built `training/prepare_v2_training_data.py` to close this gap (detail below). `train.py` itself required zero changes -- its existing `--data-dir`/`--output-dir` overrides (already used for prior controlled studies) are sufficient.
2. **`datasets/synthetic.jsonl`'s live working copy has 6 uncommitted examples that do not belong to this study** -- they read as recent work from an unrelated, separate `gold_v1.2.3` effort already present in this repo (untracked `gold_v1.2.3_*` files, `training/data/processed_gold_v1.2.3_*` directories). Using the live file would have silently grown the corpus from 66 to 72, in direct violation of the authorization's "mechanically migrated 66-example corpus only." Resolved by sourcing training data from `prompt_contract_v2_migrated_targets_DRAFT.jsonl` instead -- the already-migrated, already-verified (66/66 exact `parse_output()` equality, confirmed earlier this session) corpus pinned to commit `8d7aa09`, which is exactly gold_v1.2.2's 66 examples and nothing else.

## Training data

- Source: `training/prompt_contract_v2_migrated_targets_DRAFT.jsonl` (66 records; SHA-256 `1bef1b0476c372b35dd08a89f7e767e25c46ff1ace202d90ffbb5a3d7e4c0307`), not the live `datasets/synthetic.jsonl`.
- Built by: `python prepare_v2_training_data.py` (new script, this study). Re-verifies all 66 `v2_target` values parse and match their `output` exactly immediately before use (defense in depth on top of the migration script's own prior verification).
- Split: existing frozen `split_manifest.json` (unchanged) -- 60 train / 6 val, identical membership to every prior gold_v1.2.2 study. This study varies serialization only, not the split.
- Each record: `{"prompt": prompt_contract_v2_candidate.build_prompt(input), "target": <already-migrated v2_target>}`.
- Output: `training/data/processed_gold_v1.2.2_v2contract_seed17/{train,val}.jsonl`.
- Independent verification performed before training: 66 unique prompts, 66 unique targets (no duplication/loss); every prompt confirmed to contain v2 marker-based wording ("marker strings define the structure") and confirmed to NOT contain the old v1 line-based wording ("each on their own line"); prompt token lengths 253-317 (max 512), target token lengths 51-244 (max 512) against the real seed-17 checkpoint tokenizer -- no truncation risk on either side.
- Training-data fingerprint (canonical JSON over all 66 {prompt, target} pairs, sorted by prompt): `e548e0b633ac1ca11b109adbf88ddbda95a42add38d93f524b700f4762092fd3`.

## Training command (about to run)

```
python train.py --seed 17 \
  --data-dir data/processed_gold_v1.2.2_v2contract_seed17 \
  --output-dir checkpoints/gold_v1.2.2-v2contract-seed17
```

- Base model: `google/flan-t5-base` (unchanged).
- Hyperparameters: unchanged from every prior gold_v1.2.2/gold_v1.2.3 run (40 epochs, batch 4, lr 3e-4, bf16 on CUDA) -- `--seed 17` only changes `Seq2SeqTrainingArguments.seed`/`data_seed` and where the checkpoint is written, per `train.py`'s own documented `--seed`/`--output-dir` purpose.
- `--output-dir` is a brand-new directory name, never before used -- `train.py`'s own non-empty-output-dir refusal is expected to be a no-op here (nothing to overwrite).
- `train.py`'s built-in post-training checks (`evaluate_format_validity`, `run_real_validation_evaluation`) will run automatically and print v1-oriented diagnostics -- not meaningful for this study (the format check happens to still work since v1/v2 share the same 3 outer section markers, but doesn't validate v2's per-item structure; `run_real_validation_evaluation` is independent of `--data-dir` and will no-op since `datasets/real_validation.jsonl` is confirmed empty, so no real-data lineage risk). The actual evaluation for this study is the two `run_benchmark.py --contract=v2` runs below, against the resulting checkpoint.

## Planned evaluation (after training completes)

```
python run_benchmark.py ../datasets/benchmark/gold_v1.2.1_probes.jsonl \
  checkpoints/gold_v1.2.2-v2contract-seed17/final \
  gold_v1.2.2_seed17_v2contract_protected16_results.json --contract=v2

python run_benchmark.py ../datasets/benchmark/source_determined_items_v2_acceptance_draft.jsonl \
  checkpoints/gold_v1.2.2-v2contract-seed17/final \
  gold_v1.2.2_seed17_v2contract_acceptance10_results.json --contract=v2
```

Both produce raw (structurally computed, semantically unscored) result scaffolds per this session's established contract-adapter work -- `format_valid`/parsed structure/count-rule results computed automatically; `scores`/`capability_checks` left null for the subsequent human/LLM-judge scoring pass (ChatGPT, independently re-verified by Claude, per this project's standing collaboration protocol). No semantic scoring is performed as part of this provenance step.

## Outcome (2026-08-03, all commands run as specified above)

**Training**: completed cleanly. 600/600 optimizer steps, epoch 40.0, `train_runtime=256.7s`, no early stop, no deviations from the command above. Log: `training/gold_v1.2.2_seed17_v2contract_train.log`. Checkpoint: `training/checkpoints/gold_v1.2.2-v2contract-seed17/final`, fingerprint (`real_data_private.checkpoint_fingerprint`) `5687a7602d3ab79ff7f054b80c399738a9b27a959845c27bcf7aa918b638227c`. `train.py`'s own built-in val-split check (v1's loose 3-marker check, not full v2 parsing) reported 6/6 -- printed generated samples visibly contain real `###BULLET###`/`###ACTION###` typed markers, confirming the model learned the new serialization, not just the outer section markers. `real_validation.jsonl` confirmed empty; `run_real_validation_evaluation` no-opped as expected, no real-data lineage touched.

**Evaluation** (`run_benchmark.py --contract=v2` against both files, raw/unscored results):

- Protected 16-probe benchmark: **16/16 structural format validity** (full v2 parse success, not the looser v1 marker check) -- `training/gold_v1.2.2_seed17_v2contract_protected16_results.json`.
- 10-case v2 acceptance set: **10/10 structural format validity** -- `training/gold_v1.2.2_seed17_v2contract_acceptance10_results.json`. Structural count-rule results (computed automatically, independent of semantic scoring): **6/10 satisfy both bullet_count_rule and action_count_rule exactly**. The 4 that don't:
  - sdi2-06 (expected 0 actions): model produced 2 actions.
  - sdi2-07 (expected 1 bullet/1 action): model produced 3 bullets/2 actions -- matches this case's own predicted `likely_failures: ["Excessive Fragmentation", ...]` exactly.
  - sdi2-08 (expected exactly 8 actions): model produced 5 actions -- task loss on the ceiling-stress case.
  - sdi2-10 (expected 6 bullets): model produced 5 bullets -- topic loss on the dense mixed-capability case.

All `scores`/`capability_checks` fields remain null in both result files -- semantic scoring (ChatGPT, independently re-verified by Claude per this project's standing protocol) is the required next step before any pass/fail release-gate conclusion. The structural facts above are directly computed and reported as-is, not a semantic judgment.

## Explicit exclusions (unchanged from every prior compute-authorization round)

- Seed 73: blocked, contingent on seed 17 passing every gate.
- No new/corrective curriculum examples of any kind.
- No changes to `datasets/synthetic.jsonl` (live file untouched by this study).
- No changes to `train.py`, `prepare_data.py`, or any live v1 pipeline code.
- No app-repo activation, deployment, or export step.
