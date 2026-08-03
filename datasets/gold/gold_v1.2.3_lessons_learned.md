# gold_v1.2.3 Lessons Learned

**Date**: 2026-07-30
**Evaluation method**: `datasets/benchmark/gold_v1.2.1_probes.jsonl` (the
same 16-probe protected suite, unchanged) run via `training/run_benchmark.py`
against the newly fine-tuned checkpoint, then scored by Claude Code against
each probe's stated `expected_behavior`, same strict rubric as prior
releases. Full raw output and scores in
`training/gold_v1.2.3_benchmark_results_checkpoint680.json`,
machine-readable via `training/report_benchmark.py
datasets/benchmark/gold_v1.2.1_probes.jsonl
training/gold_v1.2.3_benchmark_results_checkpoint680.json`.

**Headline: mixed result, net negative.** The one probe this release
existed specifically to fix in a clean, unambiguous way (`08`) is
resolved. But two previously rock-solid regression guards (`06`, `09`)
newly failed, `02` still fails (differently), and `03` — held back from
promotion last release specifically pending "one more clean run" —
failed that run. Overall pass rate **dropped** from 13/16 (81%,
`checkpoint-600`) to **11/16 (69%, `checkpoint-680`)**.

## 1. Training configuration

FLAN-T5-base fine-tuned on `datasets/synthetic.jsonl` consolidated to 72
examples (`gold_v1.0` through `gold_v1.2.3`), 65 train / 7 val, 40 epochs,
same `Seq2SeqTrainingArguments` as `gold_v1.2.2`'s run
(`load_best_model_at_end=False`, final epoch used directly).

## 2. Loss and format-validity results

`train_loss` 0.134 (from 1.74 — very similar starting/ending loss to the
`gold_v1.2.2` run). `eval_loss` 2.55 at epoch 40 (higher than
`gold_v1.2.2`'s 1.86, on one more validation example — not directly
comparable, and not treated as a signal either way given
`load_best_model_at_end=False`). `train.py`'s own val-split check: 7/7
well-formed marker sections.

## 3. Probe-by-probe findings vs. `checkpoint-600` (the immediately prior candidate)

| # | Category | `checkpoint-600` | `checkpoint-680` (this run) |
|---|---|---|---|
| 01 | interrupted_thought_depth | Pass | Pass (unchanged) |
| 02 | interrupted_thought_depth | Fail — garbled reconnection, causal reason dropped | **Still fails, differently** — now invents a fabricated noun ("the computer") not in the input at all, and misattributes causing the black screen to "getting back to the computer" rather than the actual stated cause (the charger moving), which itself disappears from the output entirely |
| 03 | nested_boundary_depth | **Resolved** (held at `negative_example` pending one more clean run) | **Regressed** — bullets now include "Check the cable separately," exactly the split the input explicitly prohibits ("not ask Celia and separately check the cable, that is one question") |
| 04 | multi_person_attribution | Pass | Pass (unchanged) |
| 05 | multi_person_attribution | Pass (cosmetic typo) | Pass (same class of cosmetic typo) |
| 06 | multi_person_attribution | Pass | **New regression** — misattributes "she asked about it" to Rowan instead of Tessa, reversing an attribution this probe has gotten right on every prior checkpoint |
| 07 | open_question_preservation | Pass | Pass (unchanged) |
| 08 | open_question_preservation | Partial — confusing wording, mild lean toward "the plant" | **Resolved** — clear, non-tautological phrasing; later observation stays clearly non-answering |
| 09 | open_question_preservation | Pass | **New regression** — invents an emotional reaction ("Feeling overwhelmed by the demands of the volunteer list") not licensed by the input, which only says the writer isn't sure what to think about it yet |
| 10 | buried_task_retention | Pass | Pass (unchanged) |
| 11 | standalone_task_retention | Pass | Pass (garage light now in bullets instead of narrative — same cosmetic field-placement issue as before, just swapped fields) |
| 12 | buried_task_retention | Resolved | Pass, holds (one redundant/awkwardly-phrased extra bullet, "Needed the account list," but doesn't invent or lose anything) |
| 13 | two_unrelated_tasks | Pass | Pass (unchanged) |
| 14 | zero_action_items | Resolved | Pass, holds |
| 15 | task_plus_idea | Resolved | Pass, holds |
| 16 | dangling_reference | Fail — fabricated false clause ("both are unrelated") | **Fails, but qualitatively better** — new clause ("both references are unresolved") is at least accurate rather than fabricated nonsense, but still adds commentary beyond the input, which is exactly what this release's own corrective example (a "clean stop," no added commentary at all) was designed to teach |

## 4. Release gate evaluation (per `gold_v1.2.3_curriculum.md`)

| Gate | Result |
|---|---|
| Format validity remains 16/16 | ✅ 16/16 |
| All current regression guards pass, including 12/14/15 | ❌ **10/12** — `06` and `09` newly fail |
| Probe 03 passes one additional run, becomes eligible for promotion | ❌ Failed this run |
| Probes 02, 08, 16 each pass every strict check | ❌ Only `08` resolves; `02` and `16` still fail |
| Overall strict benchmark pass rate reaches 16/16 | ❌ 11/16 |
| No new unsupported-addition/topic-loss/task-promotion/excessive-fragmentation failures appear | ❌ New: Unsupported Addition (03, 09), Invented Causality (02), Excessive Fragmentation (03), Misattribution (06) |

**1 of 6 release gates passes cleanly (format validity); the other 5
fail.** This is a genuinely disappointing result relative to
`gold_v1.2.2`'s run, not just a "mostly
there" one.

## 5. Surprising finding: a compact, narrowly-targeted release introduced more instability than the broader one did — but not all of it is "collateral"

**Correction to this section's original framing**: grouping `03`, `06`,
and `09` together as generic "collateral regressions" understated what's
actually going on. A more precise classification, by whether the probe's
category actually received new `gold_v1.2.3` training data:

| Probe | Category trained this release? | Classification |
|---|---|---|
| `02` | Yes (`interrupted_thought_depth`, 3 examples) | Target failure — directly trained, still fails |
| `03` | No (`nested_boundary_depth`) | Structurally adjacent regression — plausibly negative transfer from interruption examples that reinforce *separating* inserted material, bleeding into a probe that requires the opposite: keeping one governed task *together* |
| `06` | No (`multi_person_attribution`) | Cross-category collateral regression — no plausible mechanistic link to this release's content |
| `08` | Yes (`open_question_preservation`, 2 examples) | Target resolution |
| `09` | Yes (`open_question_preservation`, 2 examples) | **In-category regression** — the same category that was directly retrained got worse on a different probe within it, not an unrelated capability drifting at random |
| `16` | Yes (`dangling_reference`, 1 example) | Target partial improvement, still a strict failure |

Only `06` is unexplainable collateral damage with no plausible mechanism.
`03` has a plausible structural-transfer explanation. `09` isn't
collateral at all — it's the same category regressing internally, which
is a different (and arguably more concerning, since it's not "random")
kind of finding than what this section originally implied.

`gold_v1.2.2` trained 12 examples across 7 categories and caused one
clearly cross-category regression (`02`, already discussed in that
release's own lessons-learned doc). `gold_v1.2.3` trained only 6 examples
across 3 categories — deliberately narrow, per its own "compact" framing
— and still produced one clear cross-category regression (`06`), one
structurally-adjacent regression (`03`), and one in-category regression
(`09`).

This suggests being narrow doesn't automatically mean being safe, though
the mechanism is more varied than "random collateral damage" — some of
it plausibly traces to specific training interactions (`03`, `09`), not
just unexplainable noise (`06`). This isn't evidence that `gold_v1.2.3`'s
examples themselves are flawed (the independent review found no defects,
and probe `08` genuinely resolved) — it's evidence that at this data
scale, additional training data can shift behavior on both related and
unrelated capabilities, through more than one mechanism, and distinguishing
"seed noise" from "real conflict" requires more evidence than a single
run provides.

## 6. Recommendation

**Do not prefer `checkpoint-680` over `checkpoint-600`.** By raw pass
rate and regression-guard count, `checkpoint-600` is the better
checkpoint (13/16 and 12/12 guards vs. 11/16 and 10/12 guards).
`checkpoint-680` only wins on probe `08`.

Recommend keeping `checkpoint-600` as the candidate/comparison baseline
(unchanged from the last decision), and treating `checkpoint-680` as a
second comparison point that confirms one thing worth knowing — probe
`08`'s specific fix works — without adopting the checkpoint it came
from. `checkpoint-520` remains production, unaffected either way.

Recommend against reclassifying anything based on this run: `08` is not
promoted to `regression_guard` on the strength of a checkpoint that
regressed elsewhere; `03` stays `negative_example` (its promotion
condition — one clean run — was not met, and the pending caution from
last release's decision is now validated by exactly this outcome).

## 7. Changes recommended before the next attempt

1. **Investigate whether `06` and `09`'s regressions are a training-data
   interaction or training-run noise.** A repeat run on the identical
   72-example dataset (same data, different random seed) would help
   distinguish "this batch destabilizes these probes" from "this was one
   unlucky run" — small-sample fine-tuning is known to have run-to-run
   variance.
2. **Reconsider probe 02's approach entirely** rather than iterating on
   wording again. Two consecutive corrective attempts (three examples in
   `gold_v1.2.3` alone) have not fixed it, and this run's failure mode
   (inventing a fabricated noun, "the computer") is arguably worse than
   either prior attempt. This may need a different capability-training
   strategy, not just more/better examples of the same kind.
3. **Populate `real_holdout.jsonl`.** Repeated in every lessons-learned
   doc so far; still not done. At this point, with three consecutive
   releases showing collateral regressions on a 6-7-example validation
   split, this is no longer just a nice-to-have.

## 8. Is a populated `real_holdout.jsonl` now required before the next training run?

Same answer as every prior release: yes. This run adds a new, sharper
reason: with only 7 validation examples and three consecutive releases
showing unrelated-capability regressions, there's no way to tell from
training alone whether a given batch will destabilize something else
until after a full benchmark run — a larger, more representative
validation signal would help catch this earlier.
