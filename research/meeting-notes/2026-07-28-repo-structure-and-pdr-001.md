# 2026-07-28: Repo structure, PDR-001, naming the task

**Participants**: Product owner (user), Claude Code, ChatGPT (via pasted
conversation)

## What happened

Following the gold_v1.0 batch review, ChatGPT proposed treating project
knowledge (vision, decisions, dataset specs, benchmarks, research findings)
with the same version-control discipline as code, rather than letting it
live only in chat history.

## Decisions made

1. **PDR-001 accepted**: build dataset infrastructure (spec, review process,
   benchmark suite) before generating large datasets. See
   [`../../docs/decisions/PDR-001.md`](../../docs/decisions/PDR-001.md).
2. **Formally named the task**: "Intent Recovery" — input is fragmented
   human cognition, output is recovered intent. Distinct from generic
   summarization/classification. See
   [`../../docs/vision/NORTH_STAR.md`](../../docs/vision/NORTH_STAR.md).
3. **Knowledge management layer added**: `docs/` (vision, decisions, dataset
   reference docs, benchmark plan) and `research/` (experiments, ideas
   parking lot, meeting notes, papers) as new top-level directories.
4. **Same repository, not split**: ChatGPT initially proposed two separate
   GitHub repositories (app vs. research), then revised to recommend a
   single repo with clearly separated top-level directories. Confirmed with
   the product owner: same repo — `docs/` and `research/` sit alongside the
   existing `datasets/` and `training/`.
5. **No `app/` subdirectory move**: the proposal also suggested moving
   `src/`, `training/`, etc. into an `app/` directory for symmetry with
   `datasets/`/`research/`/`docs/`. Claude Code recommended against this —
   there's only one codebase today, and the move would touch vite config,
   tsconfig, training script relative paths, and the self-hosted model's
   public path for no functional benefit. Confirmed with the product owner:
   code stays at the repo root; revisit only if a second, genuinely separate
   project needs root-level space later.

## Collaboration model reaffirmed

Product owner (vision, real-world feedback, ethical use), Claude Code
(engineering: training pipeline, fine-tuning, export, deployment), ChatGPT
(dataset curation: IRDS-track specification, gold datasets, review rubric,
benchmark suite, watching for drift/bias/underrepresentation).
