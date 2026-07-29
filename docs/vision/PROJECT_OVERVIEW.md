# Project Overview

ThoughtOrganizer is an on-device web app that turns scattered, fragmented
notes into a coherent narrative, key points, and action items. Underneath
it, this project is defining and pursuing **Intent Recovery** as a distinct
NLP task — see [NORTH_STAR.md](NORTH_STAR.md) for the mission and task
definition.

## Where things live

| Area | Location |
|---|---|
| The app (React + TypeScript + Vite, in-browser inference via transformers.js) | [`../../src/`](../../src/), [`../../README.md`](../../README.md) |
| Gold Curriculum Series' stable principles (constitution — link, don't restate) | [`GOLD_PHILOSOPHY.md`](GOLD_PHILOSOPHY.md) |
| Fine-tuning pipeline (data prep → train → export → self-host) | [`../../training/`](../../training/) |
| Engineering roadmap, hard-won findings, v1/v1.5/v2-v3 plan | [`../../training/ROADMAP.md`](../../training/ROADMAP.md) |
| Dataset generation spec (schema, rules, ChatGPT prompt) | [`../../training/DATASET_SPEC.md`](../../training/DATASET_SPEC.md) |
| The actual dataset (gold, synthetic, real holdout) | [`../../datasets/`](../../datasets/) |
| Dataset card, changelog, license (gold tier) | [`../../datasets/gold/`](../../datasets/gold/) |
| Category reference, batch review rubric | [`../datasets/`](../datasets/) *(this `docs/datasets/`, not the data itself)* |
| Benchmark suite plan | [`../benchmarks/benchmark_suite.md`](../benchmarks/benchmark_suite.md) |
| Formal decision records (PDRs) | [`../decisions/`](../decisions/) |
| Research journal — experiments, ideas, meeting notes | [`../../research/`](../../research/) |

## Current status

Fine-tuning pipeline (FLAN-T5-base, self-hosted, delimited-marker output
format) proven end-to-end on a small placeholder fixture. Real dataset
generation is underway: a 5-example hand-curated gold batch (`gold_v1.0`)
exists and validates cleanly; more gold batches and a larger synthetic batch
are the next step before a real training run. See `training/ROADMAP.md` for
the detailed state and `docs/decisions/` for why key choices were made.

## Roles

Product owner (the user), engineering lead (Claude Code), dataset curator
(ChatGPT) — see `NORTH_STAR.md`'s "Collaboration model" for what each role
owns.
