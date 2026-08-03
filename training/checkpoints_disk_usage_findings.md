# Local checkpoint disk usage — verified findings and retention manifest

**Author:** Claude (engineering side).
**Scope:** `training/checkpoints/` only. Not a code change, not part of PR #12
— disk-space triage. This supersedes the first version of this doc:
ChatGPT's two corrections (identity of `thoughtorganizer-flan-t5/`, and that
`final/ == terminal checkpoint` needed per-run verification, not assumption)
are now checked against the actual files, not guessed at.

**Status: resume-state cleanup complete.** Optimizer/scheduler/RNG-state
files were deleted from all 22 structured runs' numbered checkpoints (132
files). `checkpoints/` went from **146.6 GB → 62.0 GB** (712 → 580 files).
Verified afterward: zero `optimizer.pt`/`scheduler.pt`/`rng_state.pth` files
remain anywhere under `checkpoints/`, and all 67 `model.safetensors` files
(every numbered checkpoint + every `final/`, across all 22 structured runs
plus the one flat export) are untouched. No `model.safetensors`, config,
tokenizer, `trainer_state.json`, or `training_args.bin` file was deleted.
The two items below (production `checkpoint-520`, candidate
`checkpoint-600`) are unaffected either way; `checkpoint-520` is now
resolved (see below), `checkpoint-600` remains open.

There are **22 structured runs plus 1 flat run** (`gold_v1.2.3-seed42`) = 23
run directories total under `checkpoints/`. The retention manifest table
below groups same-seed-family runs onto shared rows for readability, so it
has fewer than 23 rows, but represents all 23 directories.

`hash_sweep_results.json` (the full per-run SHA-256/seed/step data this doc
is built from) is now committed at
`training/hash_sweep_results.json` rather than left as a local-only
artifact.

## One item resolved, one still open

**1. `checkpoint-520` — RESOLVED (2026-08-02).** Not lost: it does not
exist in this checkout's `training/checkpoints/` (confirmed — `train.py`'s
default output directory was overwritten by a later run, as suspected
below), but `thought-organizer-app`'s `scripts/fetch-model.mjs` installs
the deployed model from GitHub Release `intent-recovery-model-v0.1.0` on
*this* repo (checksummed manifest, quantized ONNX encoder/decoder,
provenance in the release body matching checkpoint-520 exactly:
`google/flan-t5-base`, `gold-v1.0`..`v1.2.1`, 40 epochs). Confirmed by
checking the app repo directly once both repos became accessible from one
session — see `training/prompt_contract_compatibility_study_manifest.md`
and `training/production_checkpoint_recovery_handoff.md`. The original
default-output-dir overwrite still happened (confirmed below), it just
turned out not to matter for this checkpoint specifically, since the ONNX
export had already been cut and published before the overwrite occurred.

**2. `checkpoint-600` (`gold_v1.2.2`'s original candidate, never released —
`datasets/gold/CHANGELOG.md` line 53) also does not appear to survive under
its original identity.** Two directories use checkpoint numbers 585/600
(`gold_v1.2.2-seed17-control`, `gold_v1.2.2-seed73-control`), but both used
explicit non-default seeds (17, 73) for what looks like the later
seed-stability/control study — there is no `gold_v1.2.2-seed42-control` or
equivalent matching the original run's implicit default seed (`--seed`
defaults to 42 in `train.py`). A different seed means different weights, so
these two are very likely *not* byte-identical to the original checkpoint-600
even though they reproduce its step count. I can't confirm or deny this from
the files alone — this needs whoever ran the original `gold_v1.2.2` training
(`train_gold_v1.2.2.log`, Jul 30 06:57) to confirm whether it was ever
re-run with the default seed, or whether checkpoint-600 is simply gone.

## Headline numbers

- `training/checkpoints/`: **146.6 GB → 62.0 GB** (712 → 580 files) after the
  resume-state cleanup described above. Still gitignored, purely local.
- `training/venv/`: 4.85 GB — leaving alone per your call.

## Verified: `thoughtorganizer-flan-t5/` identity (ChatGPT's correction #1)

Confirmed by reading `train.py`, `run_benchmark.py`, `export_onnx.py`:

- `train.py`: `BASE_MODEL = "google/flan-t5-base"` is loaded fresh from the
  HF hub every run — never stored locally under `thoughtorganizer-flan-t5/`.
  `DEFAULT_OUTPUT_DIR = checkpoints/thoughtorganizer-flan-t5` — it's purely
  the default *output* location when `--output-dir` isn't passed.
- `run_benchmark.py` and `export_onnx.py` both default `checkpoint_dir` to
  `checkpoints/thoughtorganizer-flan-t5/final` — so this location has live
  operational significance regardless of which experiment currently occupies
  it: any script invocation that omits an explicit path reads from here.

**Identity, established by hash + `training_args.bin`:**
`thoughtorganizer-flan-t5/final/model.safetensors`,
`thoughtorganizer-flan-t5/checkpoint-680/model.safetensors`, and
`gold_v1.2.3-seed42/model.safetensors` (the flat, irregular one) are **all
three byte-identical** (SHA-256 `b964c7e7...d654d4a`). `training_args.bin`
inside `thoughtorganizer-flan-t5/checkpoint-680` and inside
`gold_v1.2.3-seed42/` both record `seed: 42, num_train_epochs: 40,
output_dir: .../thoughtorganizer-flan-t5` — and the step count (663/680)
matches the `gold_v1.2.3` step-budget pattern, not `gold_v1.2.2`'s (600) or
`gold_v1.2.1`'s (520-ish). Its published result is almost certainly
`gold_v1.2.3_benchmark_results_checkpoint680.json` (Jul 30 09:34, the only
`gold_v1.2.3` base-run result without an explicit seed suffix — consistent
with seed 42 being the implicit default at the time, before the later
seed-stability study needed to name it explicitly).

**Conclusion: `thoughtorganizer-flan-t5/` and `gold_v1.2.3-seed42/` are the
same trained model** (`gold_v1.2.3`, seed 42, the base/default run) — not a
pretrained base checkpoint, and not two different experiments. Treat them as
one duplicate pair, not two separate artifacts to preserve.

## Verified: `final/ == terminal checkpoint` (ChatGPT's correction #2)

Hashed `model.safetensors` in every `final/` and every numbered checkpoint
across all 23 run directories (SHA-256, full file). Result: **`final ==
terminal checkpoint` is true for all 22 structured runs, with no
exceptions.** This is consistent with `train.py`'s current
`load_best_model_at_end=False` (confirmed in code) — the `gold_v1.2.1`
`load_best_model_at_end=True` failure mode ChatGPT described doesn't apply to
any currently-present run. No run's `final/` was found to silently hold an
earlier epoch than its last numbered checkpoint.

Also confirmed: every run's model hash is unique except for the
`thoughtorganizer-flan-t5` / `gold_v1.2.3-seed42` pair above — no other
hidden duplicates.

## Retention manifest

| Run | Seed(s) | Terminal step | `final == terminal`? | Associated results/handoff | Classification |
|---|---|---|---|---|---|
| thoughtorganizer-flan-t5 | 42 (default) | 680 | ✅ | `gold_v1.2.3_benchmark_results_checkpoint680.json` | **Operational** — live default for `run_benchmark.py`/`export_onnx.py`. Duplicate of the row below. |
| gold_v1.2.3-seed42 (flat) | 42 | 680 (no optimizer state saved) | n/a (flat export only) | same as above | Duplicate of `thoughtorganizer-flan-t5` — same model, same result |
| gold_v1.2.3-seed17 | 17 | 680 | ✅ | `gold_v1.2.3_benchmark_results_seed17.json` | Historical evidence — seed-stability study |
| gold_v1.2.3-seed73 | 73 | 680 | ✅ | `gold_v1.2.3_benchmark_results_seed73.json` | Historical evidence — seed-stability study |
| gold_v1.2.3-ablation-fixedsplit-seed{17,42,73} | 17/42/73 | 680 | ✅ (all 3) | `gold_v1.2.3_ablation_fixedsplit_results_seed*.json`, `gold_v1.2.3_fixedsplit_ablation_handoff.md` | Historical evidence — closed ablation |
| gold_v1.2.3-groupC-seed{42,73}-steps640 | 42/73 | 640 | ✅ (both) | `gold_v1.2.3_groupC_seed*_steps640_results.json`, `gold_v1.2.3_groupC_seed42_73_stepmatched_{handoff,scoring}.md` | Historical evidence — closed step-matched control |
| gold_v1.2.3-groupscreen-seed17-group{A,B,C} | 17 | 640 | ✅ (all 3) | `gold_v1.2.3_groupscreen_seed17_group*_results.json`, `gold_v1.2.3_groupscreen_seed17_{handoff,scoring}.md` | Historical evidence — closed group screen |
| gold_v1.2.3-minus006-seed{17,42,73}-steps680 | 17/42/73 | 680 | ✅ (all 3) | `gold_v1.2.3_minus006_seed*_steps680_results.json`, `gold_v1.2.3_minus006_680steps_{handoff,scoring}.md` | Historical evidence — closed ablation |
| gold_v1.2.2-control-seed{17,42,73}-steps640 | 17/42/73 | 640 | ✅ (all 3) | `gold_v1.2.2_control_seed*_steps640_results.json`, `gold_v1.2.2_control_seed17_stepmatched_{handoff,scoring}.md` | Historical evidence — closed step-matched control |
| gold_v1.2.2-control-seed{17,42,73}-steps680 | 17/42/73 | 680 | ✅ (all 3) | `gold_v1.2.2_control_seed*_steps680_results.json` | Historical evidence — closed step-matched control |
| gold_v1.2.2-seed17-control | 17 | 600 | ✅ | `gold_v1.2.2_benchmark_results_seed17_control.json` | Historical evidence — **not** confirmed equivalent to lost original `checkpoint-600` (different seed) |
| gold_v1.2.2-seed73-control | 73 | 600 | ✅ | `gold_v1.2.2_benchmark_results_seed73_control.json` | Historical evidence — same caveat |
| *(original `gold_v1.2.2` default-seed run, `checkpoint-600`)* | 42 (default) | 600 | unknown | `gold_v1.2.2_benchmark_results_checkpoint600.json` (Jul 30 07:12) | **Not found on disk under any current name** — see open item #2 above |
| *(original `gold_v1.2.1` run, `checkpoint-520`)* | — | 520-ish | n/a (ONNX only) | GitHub Release `intent-recovery-model-v0.1.0` | **RESOLVED** — not on disk locally, but durably preserved as a checksummed release asset; see item #1 above |

All 23 currently-present runs' `model.safetensors` SHA-256 hashes, seeds, and
`final`/terminal-checkpoint equivalence are in `training/hash_sweep_results.json`
(committed — see note above).

## Status and next steps

Resume-state cleanup is complete (see top of doc). No further model-weight
deletions (numbered-checkpoint `model.safetensors` copies, or whole run
directories) will happen until:
- ~~the production `checkpoint-520` question is resolved~~ — done, see
  above and `production_checkpoint_recovery_handoff.md`, and
- someone confirms whether the `gold_v1.2.2-seed{17,73}-control` runs are
  meant to stand in for the lost original `checkpoint-600`, or whether that
  candidate is simply gone and the team is accepting that — still open,
  see `training/prompt_contract_compatibility_study_manifest.md`'s finding
  #2 for the current framing of this exact question in the context of the
  prompt-contract compatibility study.

`run_benchmark.py`/`export_onnx.py`'s default checkpoint path
(`checkpoints/thoughtorganizer-flan-t5/final`) currently points at the
`gold_v1.2.3` seed-42/checkpoint-680 run, which
`datasets/gold/gold_v1.2.3_lessons_learned.md`'s recommendation section
explicitly says not to prefer over `checkpoint-600` (11/16 pass rate and
10/12 regression guards vs. 13/16 and 12/12) — this default is misleading
and still needs fixing (not done as part of this correction, to keep it
scoped to the checkpoint-520 status update).
