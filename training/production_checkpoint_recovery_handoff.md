# Production checkpoint recovery — handoff to the app/deployment side

**Item 1 RESOLVED (2026-08-02).** See
`training/prompt_contract_compatibility_study_manifest.md`'s findings
section: `checkpoint-520` is not lost. `thought-organizer-app`'s
`scripts/fetch-model.mjs` installs the deployed model from GitHub Release
`intent-recovery-model-v0.1.0` on this repo (tag `pre-repository-split`,
commit `2cd31dd`) — quantized ONNX encoder/decoder, checksummed manifest,
provenance confirmed (`google/flan-t5-base`, `gold-v1.0`..`v1.2.1`, 40
epochs) matching checkpoint-520 exactly. This was found by checking the
app repo directly once both repos became accessible from one session (see
[[chat_scope_division]]) — the "what we need from the app side" question
below is answered, no further app-side action needed for item 1. Item 2
(`checkpoint-600`) is still open; item 3 is partially actionable now (see
each section below).

**Original framing (now partly stale, kept for history):** while freeing
local disk space in `training/checkpoints/`, a training-side hash sweep
found that the exact model weights currently deployed to production
appeared no longer recoverable from the training repo. This doc laid out
what was confirmed, what was missing, and what was needed from the app
side to close the gap — written when this was still being coordinated
across two separate conversations.

## What's confirmed (training side)

`training/checkpoints/` holds 22 fine-tuned FLAN-T5 runs plus one flat
export. Every run was hashed (SHA-256 of `model.safetensors`) and
cross-referenced against `training_args.bin` (seed, epoch count) and each
run's recorded benchmark result. Two specific checkpoints, both referenced
by name in `datasets/gold/CHANGELOG.md` and the per-release
`*_lessons_learned.md` docs, are **not among the 23 currently-present
directories under any identity we can establish:**

### 1. `checkpoint-520` (`gold_v1.2.1`, epoch 40) — currently deployed to production — RESOLVED

- `training/ROADMAP.md` and `datasets/gold/CHANGELOG.md` both state this is
  the checkpoint the app is running today (`gold_v1.2.2`'s and
  `gold_v1.2.3`'s candidates were each evaluated and explicitly **not**
  promoted past it — see finding 3 below).
- No directory under `training/checkpoints/` contains it, and no `.onnx`
  file exists anywhere in the training repo checkout.
- Root cause: `train.py`'s default output directory
  (`checkpoints/thoughtorganizer-flan-t5/`) has been reused across multiple
  training runs since `gold_v1.2.1`. Each later run that didn't pass
  `--output-dir` explicitly overwrote whatever was there. The version
  currently sitting in that directory has been hash-verified (SHA-256
  `b964c7e7...d654d4a`) to be a `gold_v1.2.3` run (seed 42), not `gold_v1.2.1`.
- **What we need from the app side:** where does the deployed model
  currently come from — a copy of the ONNX export bundled in the app repo,
  a build/release artifact store, a CDN, something else? If a durable copy
  of the exact deployed weights exists anywhere in that chain, please:
  1. confirm it's backed up somewhere outside the live deployment path
     (i.e., not solely "whatever's currently served"), and
  2. record its fingerprint (a SHA-256 of the ONNX file(s), or whatever
     provenance scheme is already in use app-side) so this exact question
     doesn't recur.
  If no such durable copy exists, the exact weights behind the current
  production behavior are permanently lost — worth knowing explicitly
  either way, even if the practical answer ends up being "acceptable, we'll
  retrain if we ever need to change it."

### 2. `checkpoint-600` (`gold_v1.2.2`, epoch 40) — evaluated candidate, never released

- `datasets/gold/CHANGELOG.md`: trained as candidate `checkpoint-600`,
  benchmark rose 9/16 → 13/16, but **not cut into a production release** —
  kept only as a candidate/comparison baseline while `checkpoint-520`
  remained deployed.
- Two directories in `training/checkpoints/` land on step 600
  (`gold_v1.2.2-seed17-control`, `gold_v1.2.2-seed73-control`), but both were
  trained with explicit non-default seeds (17, 73) for what looks like a
  later seed-stability/control study — `train.py --seed` defaults to 42, and
  there's no `gold_v1.2.2-seed42-control` or equivalent. Different seed means
  different weights (different init + data shuffling), so these two are
  very likely **not** the original checkpoint-600, just same-shaped reruns.
- This one was never deployed, so it's lower urgency than item 1, but should
  be recorded as **missing unless someone still has an untouched copy**
  (a build artifact, an old export, anything). If nobody does, this is a
  known, accepted loss — worth a one-line note in the gold dataset's
  CHANGELOG/lessons-learned trail rather than silently forgotten.

### 3. `run_benchmark.py`/`export_onnx.py`'s default checkpoint path is misleading

Both scripts default `checkpoint_dir` to
`checkpoints/thoughtorganizer-flan-t5/final` when no path is given. That
directory currently holds the `gold_v1.2.3` seed-42/checkpoint-680 run
(hash-confirmed identical to `gold_v1.2.3-seed42/`, which is that run's
explicitly-labeled copy). `datasets/gold/gold_v1.2.3_lessons_learned.md`'s
own recommendation section says:

> **Do not prefer `checkpoint-680` over `checkpoint-600`.** By raw pass rate
> and regression-guard count, `checkpoint-600` is the better checkpoint
> (13/16 and 12/12 guards vs. 11/16 and 10/12 guards)... Recommend keeping
> `checkpoint-600` as the candidate/comparison baseline... `checkpoint-520`
> remains production, unaffected either way.

So the default path in both scripts currently points at a checkpoint that
was explicitly evaluated and rejected, not at production (`checkpoint-520`,
missing per item 1) or the standing candidate (`checkpoint-600`, missing per
item 2). Anyone running either script without an explicit path today gets
neither the production model nor the best candidate — silently.

**Recommended fix**, once items 1 and 2 are resolved one way or another:
either point the default at wherever the recovered/backed-up production
checkpoint ends up, or remove the default entirely and require an explicit
`checkpoint_dir` argument so a bare invocation can't silently run the wrong
model.

## What we're holding off on (training side)

No further model-weight deletions in `training/checkpoints/` (specifically:
no numbered-checkpoint `model.safetensors` copies, no whole-run-directory
deletions) until items 1 and 2 above are resolved or explicitly accepted as
losses. The already-completed cleanup (deleting only optimizer/scheduler/RNG
resume-state files, ~87GB) never touched any `model.safetensors` and doesn't
affect either open item.

## Reference

Full verification detail (hashes, per-run seeds/steps, retention
classification for all 23 current runs) is in
`training/checkpoints_disk_usage_findings.md` and
`training/hash_sweep_results.json` in the `intent-recovery-model` repo,
branch `claude/ai-note-organization-luz6rk`.
