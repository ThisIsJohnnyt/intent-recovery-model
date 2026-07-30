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

**Current classification** (12 `regression_guard` / 4 `negative_example`:
`02`, `03`, `08`, `16`), updated after `gold_v1.2.2`'s training run
against a candidate checkpoint (`checkpoint-600`, epoch 40 — see
[`gold_v1.2.2_lessons_learned.md`](../gold/gold_v1.2.2_lessons_learned.md)).
Probes `12`, `14`, and `15` were promoted from `negative_example` back to
`regression_guard` after that run resolved all three cleanly. Probe `03`
also resolved on that run but is deliberately being held at
`negative_example` for one additional clean run before promotion, given
the same run also surfaced a new regression on probe `02` — a reminder
that resolutions on this checkpoint aren't uniformly stable yet.

**Important**: this reclassification is based on `checkpoint-600`, a
*candidate* checkpoint that has **not** been cut into a production
release — the deployed model is still `checkpoint-520` (`gold_v1.2.1`).
The "Example report" below, computed against `checkpoint-520`, still
correctly shows `12`/`14`/`15` failing under the classification that was
canonical *at that time* (9 guards / 7 negatives) — that historical report
is intentionally left unchanged; it documents what was actually deployed,
not the current benchmark-suite classification. See
`training/gold_v1.2.2_benchmark_results_checkpoint600.json` for the
candidate checkpoint's full report.

- **`regression_guard`** (12 of 16, currently) — should pass. Its job going
  forward is to catch backsliding: if a future release makes this probe
  fail, that's a regression, not a tradeoff to shrug off.
- **`negative_example`** (4 of 16, currently: `02`, `03`, `08`, `16`) —
  reveals a real, current limitation not yet resolved on a stable,
  released checkpoint. Not a bug in the benchmark; the point of a negative
  example is exactly this. Tracked as known limitations to close in a
  future release, not something to silently accept as permanent.

This classification is a snapshot, not permanent — re-running this suite
against a future checkpoint should update `status` and `notes` per probe
rather than assuming today's classification still holds. Note `14`'s
history: `regression_guard` → `negative_example` (when the stricter pass
rule found its filler bullet) → `regression_guard` again (once
`checkpoint-600` produced no filler at all) — a round trip, not an error.

## Known limitations this suite currently tracks

- **`02` (interrupted-thought reconnection)** — newly regressed on
  `checkpoint-600`: produces a garbled, near-nonsensical reconnection
  clause and drops the causal reason out of the action item entirely.
  Worse than `gold_v1.2.1`'s baseline failure (which only added one
  spurious extra action). Suspected cause: this probe's analogue training
  example was deliberately rewritten away from probe `02`'s literal
  wording template after `gold_v1.2.2`'s independent review flagged
  wording reuse — see `gold_v1.2.2_lessons_learned.md`'s "surprising
  finding" section. Targeted by the planned `gold_v1.2.3` release.
- **`03` (dropped bullet content on adversarial nested case)** — resolved
  on `checkpoint-600`, held at `negative_example` pending one more clean
  run before promotion to `regression_guard`.
- **`08` (confusingly worded open question)** — unresolved across three
  consecutive releases now (`gold_v1.2.1` and `gold_v1.2.2` both score it
  partial for the same reason: correct non-answer, unclear phrasing).
  `checkpoint-600` also shows a new, milder issue: attributing a later
  observation to one specific candidate ("the plant") rather than
  preserving the input's ambiguous "it." Targeted by the planned
  `gold_v1.2.3` release.
- **`16` (minor ungrounded filler)** — `checkpoint-600` no longer produces
  the original filler bullet ("Reply to this question") but fabricates a
  different one instead ("both are unrelated"), so this remains a real,
  if changed, `Unsupported Addition`. Targeted by the planned
  `gold_v1.2.3` release.

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
