# Dataset Card: ThoughtOrganizer Gold Corpus

## Purpose

Train and evaluate a model that recovers structured intent — a coherent
narrative, key points, and action items — from scattered, fragmented
personal notes, **without requiring the person to re-enter the mental state
that produced them**. This is the north star for the whole project (see
[../../training/ROADMAP.md](../../training/ROADMAP.md)): *"The model should
adapt to the person — not the person to the model."*

This is not a note-summarization dataset in the generic sense. It's built
around the idea that a fragmented note is not noise — every fragment exists
for a reason (interruption, a repeated worry, a dangling reference, time
pressure) — and the model's job is to recover the intent behind it, not just
compress the text.

## Scope

**In scope (v1, this corpus):** single-note recovery. Input is one
fragmented note; output is three fields — `narrative`, `bullets`,
`action_items`. See [../../training/DATASET_SPEC.md](../../training/DATASET_SPEC.md)
for the exact schema and generation rules.

**Explicitly out of scope for this corpus:**
- **v1.5 richer schema** — topic clusters, an objective emotion summary, a
  "memory-safe" summary that preserves information without replaying
  distressing language, and per-field confidence scores. Planned, not yet
  represented in any example here.
- **v2/v3 architecture** — a thought-graph-driven generator (notes and
  labels derived from a structured graph of thoughts rather than freeform
  generation), a two-model split (intent recovery vs. presentation), and
  longitudinal/multi-day note continuity. These are a deliberately separate
  future effort — see `ROADMAP.md`.

## Generation process

Examples are hand-curated collaboratively between the project owner and
ChatGPT (acting as dataset/evaluation architect), following two rules from
`DATASET_SPEC.md`:

- **"No Magic Examples"**: every fragment in an `input` must be explainable
  — you should be able to say why it's there (interrupted, repeated, no
  punctuation, a dangling reference). Unexplainable fragments are noise, not
  signal, and get regenerated.
- **One lesson per example**: each example is designed to teach one specific
  recovery skill (its `category` field), not a random pile of chaos —
  building the dataset as a curriculum rather than an undifferentiated
  collection.

Every example in the `gold/` tier has a matching `*_design_notes.md` file
explaining, per example, its purpose, expected model behavior, and which
design principle it demonstrates.

## Known limitations

- **Size**: `gold_v1.0` contains only 5 examples, covering 5 categories
  (`simple_list`, `interrupted_thought`, `topic_switching`,
  `zero_action_items`, `unfinished_reference`). This is far too small to
  train a model on alone — a previous pipeline-validation run with 14-15
  placeholder examples already showed clear signs of not generalizing to
  unseen input. More gold batches and a larger synthetic batch are planned
  before any real training run.
- **Coverage**: the full target diversity (cognitive/emotional states,
  structural variety) is specified in `DATASET_SPEC.md` but only partially
  represented so far — this corpus will grow toward that target across
  future batches.
- **No categorized benchmark yet**: a per-category evaluation suite (see
  `ROADMAP.md`) is planned but not yet built; there isn't enough data yet to
  make it meaningful.

## Ethical considerations

- **Synthetic by design**: all examples in `gold/` and `synthetic.jsonl` are
  synthetic — no real personal information. The project owner's actual
  personal notes are kept in `datasets/real_validation.jsonl` (routine
  development-time evaluation) and `datasets/real_holdout.jsonl` (sealed,
  release-milestone-only evaluation — see `docs/decisions/PDR-004.md` for
  why these are two separate files), both excluded from version control
  entirely (see `datasets/.gitignore`) — neither is ever trained on or
  published alongside this corpus.
- **No diagnosis framing**: nothing in this corpus is generated or labeled
  with reference to a diagnosis (e.g. ADHD, autism). Examples describe
  cognitive/emotional *state* (time pressure, interruption, fatigue,
  focus) — the same configuration could describe a student during finals,
  a new parent, or anyone else. This avoids encoding one population's
  stereotype into the model and keeps the corpus broadly applicable. See
  `ROADMAP.md` for the reasoning.
- **Intended use**: fine-tuning small, on-device models for a personal
  note-organizing application. Not intended for any diagnostic, clinical,
  or profiling use.

## Evaluation guidance

At this size (5 examples), no performance conclusions should be drawn —
this batch exists to validate the schema and curation approach, not to
measure model quality. Once a larger, categorized dataset exists, the plan
(per `ROADMAP.md`) is to evaluate per-category pass rate (e.g. does the
model correctly recover a `zero_action_items` example without inventing a
task?) rather than a single aggregate loss number.

## License

CC BY-NC-SA 4.0 (Attribution-NonCommercial-ShareAlike), effective for
material published **2026-08-12 or later** — see [LICENSE.md](LICENSE.md).
Changed from CC-BY-4.0 to match the project's settled noncommercial policy.
**If you obtained this dataset before 2026-08-12** (`gold_v1.1` through
`gold_v1.2.3`), you received it under CC-BY-4.0, which is irrevocable —
see LICENSE.md's "Effective date and prospective scope" section for what
that means for your copy.
