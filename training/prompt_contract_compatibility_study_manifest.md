# Prompt-contract compatibility study — frozen design manifest

**Status: design and commands only. No training or inference has been run.
Compute is held pending joint review of `intent-recovery-model` PR #13,
`thought-organizer-app` PR #4, and this manifest**, per Johnny/ChatGPT's
2026-08-02 refinement replacing an open-ended retrain with a frozen,
single-variable compatibility study.

## Two findings that update the premise before this can be finalized

### 1. Resolved: production `checkpoint-520` is not lost

Earlier in this session, `training/checkpoints_disk_usage_findings.md`
flagged `checkpoint-520` (the currently-deployed production model,
`gold_v1.2.1`, epoch 40) as apparently gone from local storage, with no
`.onnx` file anywhere in this repo, and handed the question to the
app-side chat. Now that both repos are directly accessible from one
session:

- `thought-organizer-app/scripts/fetch-model.mjs` installs the deployed
  model from a **GitHub Release on `intent-recovery-model` itself**
  (`intent-recovery-model-v0.1.0`, tag `pre-repository-split`, commit
  `2cd31dd`), not from anywhere app-side-only.
- Confirmed via `gh release view intent-recovery-model-v0.1.0 --repo
  ThisIsJohnnyt/intent-recovery-model`: quantized ONNX encoder + merged
  decoder, tokenizer/config files, and a checksummed manifest. Release
  body confirms `google/flan-t5-base`, `gold-v1.0`+`v1.1`+`v1.2`+`v1.2.1`
  (54 examples), 40 epochs — matches checkpoint-520's known provenance
  exactly.
- **This resolves open item #1** in `checkpoints_disk_usage_findings.md`.
  `training/production_checkpoint_recovery_handoff.md`'s recovery framing
  is now obsolete for this item; the checkpoint isn't missing, only
  absent from local `training/checkpoints/` in raw (non-ONNX) form. That
  file should be corrected in a follow-up (not done as part of this
  manifest, to keep this change scoped).

**Caveat this creates**: `run_benchmark.py` loads checkpoints via
`AutoModelForSeq2SeqLM.from_pretrained` (safetensors/HF format only) — it
cannot load the ONNX files directly. Confirmed the training venv already
has `optimum` (2.1.0) and `onnxruntime` (1.28.0) installed, and
`optimum.onnxruntime.ORTModelForSeq2SeqLM` imports successfully — so a
small variant of `run_benchmark.py` using `ORTModelForSeq2SeqLM.from_pretrained`
(pointed at the two release `.onnx` files) instead of `AutoModelForSeq2SeqLM`
can run the strict benchmark harness against checkpoint-520 directly. This
is arguably the *more* faithful "deployment-risk check" than a safetensors
checkpoint would be, since the ONNX-quantized export is exactly what
production actually serves — not a stand-in for it.

### 2. Still open: `checkpoint-600`'s original weights

`checkpoint-600` (`gold_v1.2.2`'s original candidate, seed 42, never
released) was never published anywhere the way checkpoint-520 was — there
is no release, no ONNX export, nothing to recover from the app side. It
remains gone under its original identity. What exists instead:
`checkpoints/gold_v1.2.2-seed17-control/checkpoint-600` and
`.../gold_v1.2.2-seed73-control/checkpoint-600` — real `model.safetensors`
weights, same corpus and step count, but seeds 17/73, not the original 42.
`checkpoints_disk_usage_findings.md` already flags these as **not
confirmed equivalent** to the lost original.

**This needs an explicit decision in joint review**, not something to
resolve unilaterally here: either (a) accept the seed-17/73 replicas as
the working stand-in for "old-trained checkpoint" in the comparisons
below, with that caveat attached to every result, or (b) treat
checkpoint-600 as permanently gone and rely on its recorded historical
benchmark number (13/16 pass rate at seed 42, old prompt) as a read-only
reference that can't be re-run under the new prompt. This manifest
proceeds under option (a) below, since it's the only one that produces a
number rather than an assumption, but flags it plainly wherever it
applies.

### 3. Checked: existing gold_v1.2.2 bullets are not artificially padded

A real risk for "the prompt change is the only experimental variable": if
the existing gold_v1.2.2 ground-truth `bullets` were hand-padded to the
old prompt's "3 to 7" floor, training a new checkpoint on that data under
the *new* prompt wording would train the model to imitate padded targets
while being told not to pad — a second variable, not a clean ablation.
Checked directly: bullet-count distribution across all 66 gold_v1.2.2
examples (`git show HEAD:datasets/synthetic.jsonl`, current committed
state, before the pending uncommitted gold_v1.2.3 hunk) —

| bullets | examples |
|---|---|
| 1 | 4 |
| 2 | 13 |
| 3 | 24 |
| 4 | 18 |
| 5 | 6 |
| 6 | 1 |

17 of 66 examples (26%) already have fewer than 3 bullets. The existing
ground truth was never rigidly padded to a 3-bullet floor despite the old
prompt's wording — training on it unchanged, under the new prompt, is a
clean single-variable change, not a second confound.

## Frozen parameters

- **Corpus**: gold_v1.2.2-only, 66 examples, 60 train / 6 val by
  `split_manifest.json` (existing, frozen, unaffected by the pending
  gold_v1.2.3 hunk since that's a strict append). Old-prompt processed
  copy already exists at `training/data/processed_gold_v1.2.2_control/`.
  New-prompt copy needs regenerating (command below) — not yet done.
- **Seeds**: 42 (screen first), 17, 73 — matches every prior seed study
  in this project. Run 17 and 73 only if 42 shows no material
  regression, per the instruction.
- **Steps**: 600 (40 epochs x ceil(60/4)=15 steps/epoch — `train.py`'s
  `num_train_epochs=40` and `per_device_train_batch_size=4` are hardcoded,
  not CLI-configurable, so this falls out automatically from the existing
  corpus size; no `--max-steps` override needed or wanted). Matches the
  step count already implied by "checkpoint-600."
- **Base model / decoding**: `google/flan-t5-base`, `learning_rate=3e-4`,
  `weight_decay=0.01`, `predict_with_generate=True`,
  `generation_max_length=512`, `GENERATION_MAX_NEW_TOKENS=300` at
  benchmark time — all hardcoded in `train.py`/`run_benchmark.py`, not
  touched by `--seed`/`--output-dir`/`--data-dir`, so "unchanged base
  model and decoding settings" holds automatically as long as those three
  flags are the only ones passed.
- **Fingerprints** (both computed via `real_data_private.prompt_contract_fingerprint`
  against the shared fixture `Prompt contract fixture: review the blue
  folder tomorrow?`):
  - Old contract (pre-versioning, no `PROMPT_CONTRACT_VERSION` existed):
    `b325c0640db95f238ac97cc4b254db6347df78144fed0ddb2e6a084bba20e4c5`
  - New contract (`source-determined-bullets-v1`, PR #13 / PR #4):
    `161661198071fd81310681f69381ec8e0287141e1e75b09d3a342414af31ccf1`

## Comparison cells

### A. old-trained + old prompt — reference

Use the seed-17 and seed-73 `checkpoint-600` control replicas (original
seed-42 weights unavailable, see finding #2). Historical seed-42 number
(13/16, old prompt) stays on record but can't be re-run.

```
git checkout main -- training/prepare_data.py   # old prompt wording
python run_benchmark.py datasets/benchmark/gold_v1.2.1_probes.jsonl \
    checkpoints/gold_v1.2.2-seed17-control/checkpoint-600 \
    gold_v1.2.2_seed17_oldprompt_reference_results.json
python run_benchmark.py datasets/benchmark/gold_v1.2.1_probes.jsonl \
    checkpoints/gold_v1.2.2-seed73-control/checkpoint-600 \
    gold_v1.2.2_seed73_oldprompt_reference_results.json
```

### B. old-trained + new prompt — deployment-risk check

Two variants, both cheap (inference only, no training):

**B1. The actual production model** (checkpoint-520, ONNX):
```
git checkout claude/prompt-contract-sync -- training/prepare_data.py   # new prompt wording
# Requires a small ORTModelForSeq2SeqLM-based variant of run_benchmark.py
# (not yet written) pointed at the downloaded checkpoint-520 release assets.
python run_benchmark_onnx.py datasets/benchmark/gold_v1.2.1_probes.jsonl \
    <path-to-downloaded-checkpoint-520-onnx-release> \
    checkpoint520_newprompt_deployment_risk_results.json
```

**B2. checkpoint-600 replicas** (seed 17/73, safetensors, direct):
```
git checkout claude/prompt-contract-sync -- training/prepare_data.py   # new prompt wording
python run_benchmark.py datasets/benchmark/gold_v1.2.1_probes.jsonl \
    checkpoints/gold_v1.2.2-seed17-control/checkpoint-600 \
    gold_v1.2.2_seed17_newprompt_deployment_risk_results.json
python run_benchmark.py datasets/benchmark/gold_v1.2.1_probes.jsonl \
    checkpoints/gold_v1.2.2-seed73-control/checkpoint-600 \
    gold_v1.2.2_seed73_newprompt_deployment_risk_results.json
```

### C. new-trained + new prompt — compatibility candidate

Screen seed 42 first. Only run 17/73 if 42 shows no material regression
against cell A.

```
git checkout claude/prompt-contract-sync -- training/prepare_data.py   # new prompt wording

# Regenerate the gold_v1.2.2-only split under the new prompt (writes a new
# directory, does not touch the existing old-prompt copy):
python - <<'PY'
from pathlib import Path
import subprocess, json
import prepare_data as pd

synthetic_66 = subprocess.run(
    ["git", "show", "HEAD:datasets/synthetic.jsonl"],
    capture_output=True, text=True, check=True,
).stdout
records = [pd.validate_record(json.loads(l), "synthetic.jsonl", i)
           for i, l in enumerate(synthetic_66.splitlines(), 1) if l.strip()]
val_hashes = pd.load_val_hashes(pd.SPLIT_MANIFEST_PATH)
train_split, val_split = pd.split_by_manifest(records, val_hashes)

out = Path("data/processed_gold_v1.2.2_control_newprompt")
out.mkdir(parents=True, exist_ok=True)
for name, split in [("train.jsonl", train_split), ("val.jsonl", val_split)]:
    with (out / name).open("w", encoding="utf-8") as f:
        for r in split:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(name, len(split))
PY

# Screen seed 42:
python train.py --seed 42 \
    --output-dir checkpoints/gold_v1.2.2-newprompt-seed42 \
    --data-dir data/processed_gold_v1.2.2_control_newprompt
python run_benchmark.py datasets/benchmark/gold_v1.2.1_probes.jsonl \
    checkpoints/gold_v1.2.2-newprompt-seed42/final \
    gold_v1.2.2_seed42_newprompt_candidate_results.json

# Only if seed 42 avoids material regression vs. cell A:
python train.py --seed 17 \
    --output-dir checkpoints/gold_v1.2.2-newprompt-seed17 \
    --data-dir data/processed_gold_v1.2.2_control_newprompt
python train.py --seed 73 \
    --output-dir checkpoints/gold_v1.2.2-newprompt-seed73 \
    --data-dir data/processed_gold_v1.2.2_control_newprompt
```

`train.py --output-dir` defaults to refusing a non-empty target directory
(`--force` is off by default, specifically because this is the mechanism
that silently pruned the original checkpoint-520 and checkpoint-600 via
`save_total_limit` output-dir reuse) — every command above uses a fresh,
never-before-used directory name, so this protection shouldn't even need
to trigger.

## What "material regression" should mean here

Not decided in this manifest — recommend joint review pin this down
explicitly before screening seed 42, e.g. as a specific pass-rate
threshold or "no probe regresses from P to F relative to cell A that
wasn't already failing under cell B." Left open deliberately rather than
guessed at unilaterally.

## Release gate (unchanged)

Neither `intent-recovery-model` PR #13 nor `thought-organizer-app` PR #4
merges, and nothing deploys, until a checkpoint from cell C passes its
release gates. This manifest only prepares the comparison; it doesn't
authorize running it.
