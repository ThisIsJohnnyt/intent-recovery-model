# Controlled Seed-17 R2 Replay — Execution Provenance

**Date:** 2026-08-03
**Authorized by:** Johnny — "AUTHORIZED FOR EXECUTION... exactly one execution of the controlled
seed-17 R2 replay from: Commit `5c3bc1337836300e5ecf9cc435aaa3f6b1bf5673`, Manifest
`eca37fc0caf61365384f59cb7e5bd11fd234bb59192ddc5a937bacab6ecd8bd1`, Fingerprint lock
`3accd2bb95d940310c7e362372a8e7da953e5ccd9691304b7e0386661289676a`." Scope: seed-17 R2 training,
protected-16 evaluation, acceptance-10 evaluation, preservation of receipt/checkpoint/raw
results/logs. Seed 73, Phase-2 work, semantic scoring, export, deployment, activation, and
production promotion explicitly excluded.
**Command:** `python run_seed17_r2_replay.py --confirm-execute`

## Pre-execution re-verification (immediately before running)

Re-confirmed, not assumed, immediately before invoking the wrapper: `HEAD` = `origin/main` =
`5c3bc1337836300e5ecf9cc435aaa3f6b1bf5673`; working tree clean; `controlled_seed17_r2_replay_frozen_manifest.md`
hash `eca37fc0...` and `controlled_seed17_r2_replay_frozen_fingerprints.json` hash `3accd2bb...`
both matched Johnny's authorization message exactly.

## Preflight (all passed, all before the experiment directory was created)

```
[working tree OK] clean, nothing uncommitted.
[dependency versions OK] all 5 pinned package(s) match exactly.
[executable code OK] all 8 file(s) match the frozen lock file exactly.
[governing inputs OK] all 7 file(s) match the frozen lock file exactly.
[snapshot OK] google/flan-t5-base @ 7bcac572ce56db69c1ea7c8af255c5d7c9672fc2: all 7 file(s) match pinned fingerprints.
[baseline provenance OK] final's spiece.model matches the pinned snapshot exactly.
```

Receipt written to `controlled_seed17_r2_replay_run/receipt.json` (exclusive creation) before any
subprocess started. Its own recorded git state: `head_commit` = `origin_main_commit` =
`5c3bc1337836300e5ecf9cc435aaa3f6b1bf5673`, `working_tree_clean: true` — matches the manual
re-verification above exactly, independently confirmed by reading the receipt back after the fact.

## Training

Command run: `train.py --seed 17 --data-dir data/processed_gold_v1.2.2_r2_v2contract_seed17
--output-dir controlled_seed17_r2_replay_run/checkpoint`, offline env
(`HF_HUB_OFFLINE=1`/`TRANSFORMERS_OFFLINE=1`) enforced.

- **Completed cleanly**: 600/600 optimizer steps, epoch 40.0, no early stop, no deviations from
  the authorized command. `train_runtime=302.7648s` (baseline run: 256.7s — different wall clock,
  identical step/epoch count, consistent with normal run-to-run GPU timing variance, not a
  configuration difference).
- Val-split built-in check (`train.py`'s own loose 3-marker check): **6/6 well-formed marker
  sections**. Generated val samples visibly contain real `###BULLET###`-style typed markers,
  confirming the model learned the v2 serialization, not just the outer section markers.
- `real_validation.jsonl` confirmed empty by the run itself; `run_real_validation_evaluation`
  no-opped as expected — no real-data lineage touched.
- Checkpoint: `training/controlled_seed17_r2_replay_run/checkpoint/final`, fingerprint
  (`real_data_private.checkpoint_fingerprint`): `94a4b6e55782d00813675b1d1811bb12b944f0d3f2b0159a5bf74ca6fe927228`.
  Full raw log: `training/controlled_seed17_r2_replay_run/train_log.txt`.

## Evaluation (`run_benchmark.py --contract=v2`, raw/unscored results, structural facts only)

Both commands ran with the same offline env and exited 0. All `scores`/`capability_checks` fields
remain null in both result files — **semantic scoring was explicitly not authorized this round**
and was not performed. Everything below is a directly-computed structural fact, not a semantic
judgment, and `report_benchmark.py` itself warns exactly this ("these probes look completely
unscored... Results will undercount passes until scored") when run against either file as-is.

- **Protected 16-probe benchmark** (`controlled_seed17_r2_replay_run/protected16_results.json`,
  log `protected16_log.txt`): **16/16 structural format validity** (full v2 parse success) — matches
  the baseline's own 16/16 exactly.
- **10-case v2 acceptance set** (`controlled_seed17_r2_replay_run/acceptance10_results.json`, log
  `acceptance10_log.txt`): **10/10 structural format validity**. Structural count-rule results
  (`bullet_count_result`/`action_count_result`, computed automatically, independent of semantic
  scoring, read directly from the raw result file rather than relying on `report_benchmark.py`'s
  default summary since that summary requires non-null semantic scores to report this figure
  correctly): **7/10 satisfy both count rules exactly** — up from the baseline's 6/10. The 3 that
  don't:
  - `sdi2-07`: fails `bullet_count_rule` only (`action_count_rule` passes).
  - `sdi2-08`: fails `action_count_rule` only (`bullet_count_rule` passes).
  - `sdi2-10`: fails `bullet_count_rule` only (`action_count_rule` passes).
  - (For direct comparison: the baseline's 4 failures were `sdi2-06`, `sdi2-07`, `sdi2-08`,
    `sdi2-10` — `sdi2-06` now satisfies both count rules exactly, a structural change from
    baseline. This is a count-rule fact only, not a claim about semantic correctness.)

## Explicit scope confirmation

- Seed 73: **not touched**. Confirmed no pre-existing seed-73 artifact in `training/` has an mtime
  newer than this run's own log files.
- Baseline artifacts (`training/checkpoints/gold_v1.2.2-v2contract-seed17/`, both baseline result
  files, `training/data/processed_gold_v1.2.2_v2contract_seed17/`): confirmed untouched (`git
  status` shows only the new `controlled_seed17_r2_replay_run/` directory; nothing under
  `checkpoints/` has a newer mtime than this run's outputs).
- No application export, deployment, activation, or production-promotion path was invoked.
- No semantic scoring was performed or attempted.
- Working tree immediately after the wrapper completed (before this document existed): only the
  new, untracked `controlled_seed17_r2_replay_run/` directory — no existing tracked file was
  modified. After writing this document, the working tree additionally contains this file itself,
  also untracked; both are held uncommitted pending the scoring/verification/six-gate outcome.

## Next step (not yet performed, not authorized by this run)

Per the governing protocol's §5/§7: ChatGPT scores both raw result files semantically; Claude
independently re-verifies every score against the raw generated text and the frozen rubric before
accepting, exactly as every prior scoring round this project. All 6 frozen gates get recomputed
directly via `report_benchmark.py` once scores exist. That step, and any pass/fail conclusion, is
separate from — and not authorized by — this execution round.
