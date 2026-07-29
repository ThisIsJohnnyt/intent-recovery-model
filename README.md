# Intent Recovery Model

The Intent Recovery Model is an open language-model training and
evaluation project designed to help people recover what mattered from
fragmented, rushed, incomplete, or interleaved notes — with as little
cognitive and emotional burden as possible.

This repository contains the dataset, evaluation methodology, training
pipeline, model releases, and reference inference code. It does not
contain the application — see
[**Thought Organizer**](https://github.com/ThisIsJohnnyt/thought-organizer-app),
the reference application powered by a versioned release of this model.

## The task: Intent Recovery

Common NLP tasks — translation, summarization, classification — take
well-formed text as input. This one doesn't.

- **Input**: fragmented human cognition — scattered, interrupted,
  incomplete notes written under real-world conditions (time pressure,
  distraction, fatigue, excitement).
- **Output**: recovered intent — what the person was actually trying to
  capture, structured and readable, without inventing what wasn't there.

Every dataset, evaluation, and architecture decision is checked against
one question: **does this make it easier for the person to recover what
mattered, without forcing them to relive more than they need to?** See
[`docs/vision/NORTH_STAR.md`](docs/vision/NORTH_STAR.md) for the full
mission and [`docs/vision/GOLD_PHILOSOPHY.md`](docs/vision/GOLD_PHILOSOPHY.md)
for the stable principles behind every dataset release.

Cognitive/emotional *state* is fair game in this project's data and
documentation (rushed, distracted, excited, overwhelmed); a diagnosis
label is not — see `NORTH_STAR.md`'s mission statement and
[`docs/datasets/REVIEW_GUIDE.md`](docs/datasets/REVIEW_GUIDE.md)'s
"No diagnosis framing" check.

## Where things live

| Area | Location |
|---|---|
| Mission, stable principles, AI collaboration protocol | [`docs/vision/`](docs/vision/) |
| Dataset generation spec, category reference, review checklist, schemas | [`docs/datasets/`](docs/datasets/), [`training/DATASET_SPEC.md`](training/DATASET_SPEC.md) |
| The dataset itself (gold releases, synthetic, benchmark) | [`datasets/`](datasets/) |
| Fine-tuning pipeline (prepare → train → export → release) | [`training/`](training/) |
| Formal decision records | [`docs/decisions/`](docs/decisions/) |
| Benchmark suite | [`docs/benchmarks/`](docs/benchmarks/) |
| Research journal | [`research/`](research/) |
| Model releases | [Releases](https://github.com/ThisIsJohnnyt/intent-recovery-model/releases) |

## Current state

Fine-tuned FLAN-T5-base, delimited-marker output format (see
`training/ROADMAP.md`'s hard-won findings for why JSON isn't viable with
this model). Curriculum through `gold_v1.2.1` (basic recovery → multiple
interleaved topics → segmentation reinforcement), 54 training examples
total. First tagged release: `intent-recovery-model-v0.1.0`.

Known limitations are tracked as negative examples in
[`datasets/benchmark/`](datasets/benchmark/), not silently accepted —
see [`datasets/gold/gold_v1.2.1_lessons_learned.md`](datasets/gold/gold_v1.2.1_lessons_learned.md)
for the most recent evaluation.

## Using this model

Consume a tagged release from [Releases](https://github.com/ThisIsJohnnyt/intent-recovery-model/releases) —
each includes a `manifest.json` with SHA-256 checksums and the
[Intent Recovery Inference Contract](docs/inference-contract.md) version it
satisfies. See `thought-organizer-app`'s
[`scripts/fetch-model.mjs`](https://github.com/ThisIsJohnnyt/thought-organizer-app/blob/main/scripts/fetch-model.mjs)
for a reference implementation of downloading, verifying, and installing a
release.

## Building and evaluating

```bash
cd training
python -m venv venv && ./venv/Scripts/pip install -r requirements.txt
./venv/Scripts/python.exe prepare_data.py   # builds train/val/eval splits
./venv/Scripts/python.exe train.py          # fine-tunes, saves a checkpoint
./venv/Scripts/python.exe export_onnx.py    # exports to ONNX for release
```

See [`docs/datasets/REVIEW_GUIDE.md`](docs/datasets/REVIEW_GUIDE.md) for the
dataset batch review checklist and release process.

## Collaboration model

Built by a product owner, an engineering-lead AI (Claude Code), and a
dataset-curator AI (ChatGPT) working from a documented, versioned process —
see [`docs/vision/AI_COLLABORATION.md`](docs/vision/AI_COLLABORATION.md).

## Issues

Open an issue here for dataset problems, evaluation problems, training
problems, export problems, model behavior, or inference contract changes.
For UI, storage, or application-level issues, open one in
[thought-organizer-app](https://github.com/ThisIsJohnnyt/thought-organizer-app) instead.
