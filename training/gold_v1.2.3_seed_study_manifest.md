# Gold v1.2.3 Multi-Seed Stability Study — Frozen-Input Manifest

Recorded before any seed-17/seed-73 runs, per
`gold_v1.2.3_stability_investigation.md`'s Phase A §5.3. All fields below
must stay identical across seeds 17 and 73 — only `--seed` and
`--output-dir` vary.

## Frozen file hashes (SHA-256)

```
9d449d643d03a81275e0bb1be1cf683135b7659260a14ea3fd5ef91873536edc  datasets/synthetic.jsonl
c39ccd936055599510980a73d6e43f7dff9ea3713f81427db1d470cfc9100acb  training/data/processed/train.jsonl
604ef5ea17bbdc36d0675164044317c0b363c5affb58686823be237cee26087d  training/data/processed/val.jsonl
514bf17b4b5289d0bcaf4b9b8d00c8addc2116963428da7a1269efcf9577bf77  datasets/benchmark/gold_v1.2.1_probes.jsonl
```

(Corrected: the first recording of these hashes was hand-transcribed and
silently dropped the last character of each — a real error, caught by
directly diffing freshly recomputed hashes against this file rather than
eyeballing them. The underlying files were never at risk; only this
written record was wrong.)

`training/prepare_data.py` is **not** re-run between seeds —
`train.jsonl`/`val.jsonl` above are the exact files seed 42
(`checkpoint-680`) was already trained/evaluated on.

## Environment

- Git commit: `ea0942f3760b91c447ac4506dba11b6737f44e62`
- Python: 3.11.9
- PyTorch: 2.11.0+cu128
- Transformers: 4.57.6
- CUDA: 12.8
- GPU: NVIDIA GeForce RTX 5060

## Base model and training arguments (unchanged from the seed-42 run)

- Base model: `google/flan-t5-base`
- `per_device_train_batch_size`: 4
- `per_device_eval_batch_size`: 4
- `num_train_epochs`: 40
- `learning_rate`: 3e-4
- `weight_decay`: 0.01
- `eval_strategy` / `save_strategy`: `"epoch"`, `save_total_limit=2`
- `load_best_model_at_end`: `False` (final epoch always used)
- `predict_with_generate`: `True`, `generation_max_length`: 512
- `bf16`: `True` (CUDA available)
- Generation (benchmark/eval): `max_new_tokens=300`, `repetition_penalty=1.3`

## Seed assignments

| Seed | Role | Checkpoint dir |
|---|---|---|
| 42 | Existing run (already completed, preserved) | `training/checkpoints/gold_v1.2.3-seed42/` (verified copy of `checkpoints/thoughtorganizer-flan-t5/final`, diffed identical) |
| 17 | New run | `training/checkpoints/gold_v1.2.3-seed17/` |
| 73 | New run | `training/checkpoints/gold_v1.2.3-seed73/` |

Seed passed explicitly to both `seed` and `data_seed` in
`Seq2SeqTrainingArguments` for the two new runs (see `train.py`'s
`--seed`/`--output-dir` CLI args, added for this study only).
