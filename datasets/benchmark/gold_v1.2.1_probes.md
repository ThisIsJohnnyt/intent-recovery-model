# gold_v1.2.1 Probe Suite

The first populated entries in `datasets/benchmark/` — 16 examples in
[`gold_v1.2.1_probes.jsonl`](gold_v1.2.1_probes.jsonl), the trigger
`docs/benchmarks/benchmark_suite.md` named ("once categorized data exists").
Authored by ChatGPT as the "Gold v1.2.1 Semantic Live-Evaluation Suite,"
run against the fine-tuned checkpoint via `training/run_benchmark.py`, and
scored by Claude Code — see
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

- **`regression_guard`** (9 of 16, currently) — should pass. Its job going
  forward is to catch backsliding: if a future release makes this probe
  fail, that's a regression, not a tradeoff to shrug off.
- **`negative_example`** (7 of 16, currently: `02`, `03`, `08`, `12`, `14`,
  `15`, `16`) — reveals a real, current limitation on the deployed model.
  Not a bug in the benchmark; the point of a negative example is exactly
  this. Tracked as known limitations to close in a future release, not
  something to silently accept as permanent.

This classification is a snapshot as of this training run, not permanent —
re-running this suite against a future checkpoint should update `status`
and `notes` per probe rather than assuming today's classification still
holds. **`14` and `16` were reclassified from `regression_guard` to
`negative_example`** (approved as part of the `gold_v1.2.2` curriculum
decision) — see "Automated scoring and reporting" below; a stricter pass
rule than the informal read that first produced the original classification
found a real, if minor, issue in both.

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
- **`14`, `16` (minor ungrounded filler bullets)** — found by the stricter
  scoring pass below, not the original informal review, and now formally
  reclassified from `regression_guard` to `negative_example`: both produce
  one vague, unsupported bullet (`"Morning fan"`, `"Reply to this
  question"`) that doesn't affect `action_items` but is a real
  `Unsupported Addition`. Lower severity than `15` — nothing gets promoted
  to a task — but still a genuine gap, not currently fixed.

## Automated scoring and reporting

Two scripts, generalized beyond this one probe set:

- **`training/run_benchmark.py <benchmark.jsonl> [checkpoint_dir] [out.json]`**
  — runs every probe in any `datasets/benchmark/*.jsonl` file against a
  checkpoint, writes raw output and automatically-computed `format_valid`,
  and scaffolds (as `null`) the semantic fields a human (or a future
  LLM-judge pass) still has to fill in: `topic_completeness`,
  `attribution_accuracy`, `uncertainty_preservation`,
  `unsupported_addition_resistance` (the suite's original 0/1/2 rubric),
  and one boolean per probe's own `primary_checks`.
- **`training/report_benchmark.py <benchmark.jsonl> <scored-results.json>`**
  — once those fields are filled in, computes: overall pass rate, pass
  rate by category, pass rate by probe kind, failure count by canonical
  `TAXONOMY.md` label, how many `regression_guard` probes still pass, how
  many `negative_example` probes have newly started passing ("resolved"),
  and the format-validity rate. **Pass rule is strict, deliberately**: a
  probe passes only if `format_valid` is true, every non-null score is
  exactly `2`, and every capability check is exactly `true` — no partial
  credit in the aggregate numbers, even though the underlying scores (still
  in the results file) keep the partial-credit detail for anyone reading
  the raw data instead of the summary.

`training/gold_v1.2.1_benchmark_results_epoch40.json` is the first fully
scored results file (checkpoint-520, all 16 probes). Current report:

```
Overall pass rate: 9/16 (56%)
Format-validity rate: 16/16 (100%)
Regression guards passed: 9/9 (100%)
Negative examples resolved: 0/7 (0%)
Failure count by taxonomy label: Unsupported Addition: 3, Topic Loss: 2, Excessive Fragmentation: 1
```

Full per-category/per-kind breakdown reproducible via:
```
training/venv/Scripts/python.exe training/report_benchmark.py datasets/benchmark/gold_v1.2.1_probes.jsonl training/gold_v1.2.1_benchmark_results_epoch40.json
```

This is now the actual release gate `docs/benchmarks/benchmark_suite.md`
described as a future goal, not just documentation — the per-category
pass-rate extension to `train.py`'s `evaluate_format_validity` that doc
named as the next step was superseded by this standalone pair of scripts
instead of being folded into `train.py` itself, since scoring (the
judgment-requiring half) has to happen as a separate pass regardless of
where the aggregation logic lives.
