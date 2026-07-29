# gold_v1.2.1 Probe Suite

The first populated entries in `datasets/benchmark/` — 16 examples in
[`gold_v1.2.1_probes.jsonl`](gold_v1.2.1_probes.jsonl), the trigger
`docs/benchmarks/benchmark_suite.md` named ("once categorized data exists").
Authored by ChatGPT as the "Gold v1.2.1 Semantic Live-Evaluation Suite,"
run against the fine-tuned checkpoint via
`training/run_gold_v1.2.1_probes.py`, and scored by Claude Code — see
[`gold_v1.2.1_lessons_learned.md`](../gold/gold_v1.2.1_lessons_learned.md)
for the full run.

Never read by `training/prepare_data.py`'s training path, per this
directory's own README.

## What these are, and what they aren't

These are **benchmark** examples — synthetic, authored, categorized test
inputs — not `datasets/real_holdout.jsonl` entries. That file serves a
different, narrower purpose (real personal notes, testing whether
synthetic-only training generalizes to actual user writing) and stays
separate; these two concepts shouldn't be merged even though both are
"held out from training."

## Fields

Each entry: `id` (matches the original probe numbering), `category` (the
actual `CATEGORY_REFERENCE.md` category it tests), `kind`
(direct/transfer/adversarial/regression), `status` (see below),
`input`, `expected_behavior` (prose), `primary_checks` (the specific binary
checks that matter for this probe), `likely_failures` (canonical
`TAXONOMY.md` failure category names), and `notes` (what actually happened
on both checkpoints tested so far).

## Status classification

Classified against **`checkpoint-520` (epoch 40)** — the checkpoint
actually deployed after `gold_v1.2.1`'s training run (see the lessons-
learned doc for why `checkpoint-26`, an earlier epoch, was initially
selected instead and isn't the reference point here):

- **`regression_guard`** (11 of 16) — passes cleanly on the current
  deployed model. Its job going forward is to catch backsliding: if a
  future release makes this probe fail, that's a regression, not a
  tradeoff to shrug off.
- **`negative_example`** (5 of 16: `02`, `03`, `08`, `12`, `15`) — reveals a
  real, current limitation on the deployed model. Not a bug in the
  benchmark; the point of a negative example is exactly this. Tracked as
  known limitations to close in a future release, not something to
  silently accept as permanent.

This classification is a snapshot as of this training run, not permanent —
re-running this suite against a future checkpoint should update `status`
and `notes` per probe rather than assuming today's classification still
holds.

## Known limitations this suite currently tracks

- **`15` (idea promoted to a committed action item)** — a confirmed
  regression against established `gold_v1.2` policy
  (`task_plus_idea`/`observation_plus_idea`), present on both checkpoints
  tested. Highest-priority item to close.
- **`02`, `03` (excessive fragmentation / dropped bullet content on
  adversarial nested/interrupted cases)** — narrower quality issues, not
  regressions against prior policy, but real gaps in the specific
  reinforcement `gold_v1.2.1` targeted.
- **`08` (confusingly worded open question)** — no invented answer (the
  core test), but the question's actual content doesn't come through
  clearly. A phrasing-quality gap, not an evidence-first violation.
- **`12` (task dropped from narrative specifically, while surviving in
  bullets/actions)** — a narrower, more specific failure than general Topic
  Loss: the structured fields are reliable even when the prose narrative
  isn't. Worth watching whether this recurs across future releases.

## Extending this suite

Per-category pass-rate reporting (`train.py`'s `evaluate_format_validity`
extended to run against this file and break down results by `category`) is
the next concrete engineering step `benchmark_suite.md` names, once more
categorized data exists — not yet built, since this is the first populated
benchmark set and doing it manually (as this run did) was tractable at 16
examples.
