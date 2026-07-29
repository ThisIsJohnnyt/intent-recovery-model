# Project Overview

This repository (`intent-recovery-model`) is defining and pursuing **Intent
Recovery** as a distinct NLP task — see [NORTH_STAR.md](NORTH_STAR.md) for
the mission and task definition — and contains the dataset, evaluation
methodology, training pipeline, and model releases behind it.

The reference application,
[**Thought Organizer**](https://github.com/ThisIsJohnnyt/thought-organizer-app)
(React + TypeScript + Vite, in-browser inference via transformers.js), is a
separate, independently maintained repository — see
[PDR-003](../decisions/PDR-003.md) for why, and
[`../inference-contract.md`](../inference-contract.md) for the versioned
boundary between the two.

## Where things live

| Area | Location |
|---|---|
| Gold Curriculum Series' stable principles (constitution — link, don't restate) | [`GOLD_PHILOSOPHY.md`](GOLD_PHILOSOPHY.md) |
| How the AI collaborators actually work together (roles, review, conflict resolution) | [`AI_COLLABORATION.md`](AI_COLLABORATION.md) |
| Fine-tuning pipeline (data prep → train → export → release) | [`../../training/`](../../training/) |
| Engineering roadmap, hard-won findings, v1/v1.5/v2-v3 plan | [`../../training/ROADMAP.md`](../../training/ROADMAP.md) |
| Dataset generation spec (schema, rules, ChatGPT prompt) | [`../../training/DATASET_SPEC.md`](../../training/DATASET_SPEC.md) |
| The actual dataset (gold, synthetic, real holdout, benchmark) | [`../../datasets/`](../../datasets/) |
| Dataset card, changelog, license (gold tier) | [`../../datasets/gold/`](../../datasets/gold/) |
| Category reference, taxonomy, batch review rubric, schemas | [`../datasets/`](../datasets/) *(this `docs/datasets/`, not the data itself)* |
| Versioned application boundary | [`../inference-contract.md`](../inference-contract.md) |
| Benchmark suite | [`../benchmarks/benchmark_suite.md`](../benchmarks/benchmark_suite.md) |
| Formal decision records (PDRs) | [`../decisions/`](../decisions/) |
| Research journal — experiments, ideas, meeting notes | [`../../research/`](../../research/) |
| How this repo relates to the app repo | [`PDR-003.md`](../decisions/PDR-003.md), [`PDR-003-migration-plan.md`](../decisions/PDR-003-migration-plan.md) |

## Current status

Curriculum through `gold_v1.2.1` (basic recovery → multiple interleaved
topics → segmentation reinforcement), 54 training examples across
`gold_v1.0`–`v1.2.1`, consolidated into `datasets/synthetic.jsonl`.
Fine-tuning pipeline proven end-to-end on real (not placeholder) data, with
a semantic evaluation pass finding both real strengths and known,
tracked limitations (see
[`../../datasets/gold/gold_v1.2.1_lessons_learned.md`](../../datasets/gold/gold_v1.2.1_lessons_learned.md)).
First tagged model release: `intent-recovery-model-v0.1.0`. First populated
benchmark set exists (`datasets/benchmark/gold_v1.2.1_probes.jsonl`).
`datasets/real_holdout.jsonl` is still unpopulated — the next real gap to
close. See `training/ROADMAP.md` for the detailed release curriculum and
`docs/decisions/` for why key choices were made.

## Roles

Product owner (the user), engineering lead (Claude Code), dataset curator
(ChatGPT) — see `NORTH_STAR.md`'s "Collaboration model" for what each role
owns.
