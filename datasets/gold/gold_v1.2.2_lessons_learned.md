# gold_v1.2.2 Lessons Learned

**Date**: 2026-07-30
**Evaluation method**: `datasets/benchmark/gold_v1.2.1_probes.jsonl` (the
same 16-probe protected suite, unchanged) run via `training/run_benchmark.py`
against the newly fine-tuned checkpoint, then scored by Claude Code against
each probe's stated `expected_behavior`, following the same strict rubric
`gold_v1.2.1`'s evaluation established (0/1/2 per dimension, boolean
capability checks, no partial credit in the aggregate). Full raw output and
scores in `training/gold_v1.2.2_benchmark_results_checkpoint600.json`,
machine-readable via `training/report_benchmark.py
datasets/benchmark/gold_v1.2.1_probes.jsonl
training/gold_v1.2.2_benchmark_results_checkpoint600.json`.

## 1. Training configuration

FLAN-T5-base fine-tuned on `datasets/synthetic.jsonl` consolidated to 66
examples (`gold_v1.0`+`v1.1`+`v1.2`+`v1.2.1`+`v1.2.2`), 60 train / 6 val,
40 epochs, `Seq2SeqTrainingArguments(eval_strategy="epoch",
save_strategy="epoch", save_total_limit=2, load_best_model_at_end=False)`.
`load_best_model_at_end=False` (fixed after `gold_v1.2.1`'s run found it
was silently selecting a worse, undertrained checkpoint by `eval_loss`) —
this run correctly saved and evaluated the final epoch-40 checkpoint
(`checkpoint-600`, same as `final/`), not an early one.

## 2. Loss and format-validity results

`train_loss` 0.148 (from 1.74). `eval_loss` bottomed at **~1.03 at epoch
4**, then rose to **1.86 by epoch 40** — the same overfitting shape seen
in every prior run at this data scale; expected, and no longer a
checkpoint-selection risk now that selection doesn't depend on it.
`train.py`'s own built-in val-split check: 6/6 well-formed marker
sections.

## 3. Probe-by-probe semantic findings

All comparisons are against `gold_v1.2.1`'s baseline
(`checkpoint-520`/epoch 40, recorded in
`training/gold_v1.2.1_benchmark_results_epoch40.json`), since that's the
checkpoint this release exists to improve on.

| # | Category | Kind | `gold_v1.2.1` baseline | `gold_v1.2.2` (this run) |
|---|---|---|---|---|
| 01 | interrupted_thought_depth | direct | Pass | Pass (unchanged) |
| 02 | interrupted_thought_depth | transfer | Partial — spurious "Back to the tablet" action (Excessive Fragmentation) | **Fail, different failure** — reconnection now produces a garbled, near-nonsensical clause ("whether the tablet keeps going back to the tablet"), and the actual cause ("screen goes black whenever the charger moves") drops out of the action item entirely, surviving only as a disconnected bullet |
| 03 | nested_boundary_depth | adversarial | Partial — clock observation dropped from bullets, redundant duplicate bullet | **Resolved** — clock observation present in bullets, no duplication, task stays unsplit |
| 04 | multi_person_attribution | direct | Pass | Pass (unchanged) |
| 05 | multi_person_attribution | transfer | Pass (one cosmetic typo, "backped up") | Pass (one cosmetic typo, "back up" wrong tense — same class of surface noise, not semantic) |
| 06 | multi_person_attribution | adversarial | Pass | Pass (near-identical output) |
| 07 | open_question_preservation | direct | Pass | Pass (unchanged) |
| 08 | open_question_preservation | transfer | Partial — question content confusingly worded | Partial, still unresolved — confusing wording persists ("whether...was the wet spot"), and now specifically attributes "dry again" to "the plant" rather than preserving input's ambiguous "it," a mild new lean toward one answer |
| 09 | open_question_preservation | adversarial | Pass | Pass (unchanged) |
| 10 | buried_task_retention | direct | Pass | Pass (unchanged) |
| 11 | standalone_task_retention | transfer | Pass | Pass (garage light present in narrative, missing from bullets only — cosmetic, doesn't touch this probe's actual capability checks) |
| 12 | buried_task_retention | adversarial | Partial — oil-change task missing from narrative | **Resolved** — oil-change task now present in narrative, bullets, and actions; all four capability checks pass |
| 13 | two_unrelated_tasks | regression | Pass | Pass (unchanged) |
| 14 | zero_action_items | regression | Partial (since reclassified) — one harmless filler bullet ("Morning fan") | **Resolved** — no filler, clean pass |
| 15 | task_plus_idea | regression | **Confirmed regression** — idea wrongly promoted to `action_items` | **Resolved** — `action_items` correctly empty; idea preserved as tentative in narrative and bullets |
| 16 | dangling_reference | regression | Partial (since reclassified) — one harmless filler bullet ("Reply to this question") | **Fail, different filler** — new fabricated clause ("both are unrelated") not grounded in the input |

## 4. Capability-level conclusions

- **Unsupported-content resistance** (probes 14, 09-style filler risk):
  genuinely improved — probe 14's filler bullet is gone entirely. Probe 16
  still fails, but on a *different* fabricated clause than before, not the
  same one persisting unfixed.
- **Idea-vs-task boundary** (probe 15): fully resolved. This was the
  single highest-priority regression from `gold_v1.2.1` and the hard
  requirement in this release's gates — it now passes cleanly.
- **Nested-boundary and buried-task completeness** (probes 03, 12): both
  resolved. Cross-field completeness training appears to have generalized
  well to probes that weren't literally memorized (neither 03's nor 12's
  new analogue example shares any wording with the actual probe text).
- **Interrupted-thought reconnection** (probe 02): got *worse*, and in a
  new way — see the surprising-finding section below, this is the most
  important result of this run.
- **Open-question wording clarity** (probe 08): unchanged in severity,
  still a known limitation, with one new nuance noted above.

## 5. Surprising finding: the contamination fix may have traded away transfer on probe 02

This is the most important result of this run, and it's a genuine
tension, not a simple win.

`gold_v1.2.2`'s independent review (`gold_v1.2.2_review_report.md`)
correctly required example 005 (probe 02's analogue) to stop using the
literal "keeps—...—back to the X" template, since that phrasing was
copied too closely from probe 02 itself. The revised example uses a
repeated conditional clause instead ("it starts chirping when—...—when
the door stays open...").

Probe 02's own text is permanent — it's protected benchmark wording and
will never be rewritten. It still uses the literal "keeps—...—back to the
tablet" construction. By training on a structurally-different
reconnection pattern instead of that one, the model may have gotten
*less* reinforcement on exactly the surface form probe 02 tests — and
probe 02 didn't just fail to improve, it regressed to a new, more
confused failure mode (a garbled clause plus the causal reason dropping
out of the action item), worse than the "just one spurious action"
failure it had before.

This suggests a real tradeoff: avoiding benchmark contamination by
diversifying training-example wording is correct and necessary (see the
review report for why), but it can leave a specific literal-probe-wording
case under-reinforced. Worth watching whether this is a one-probe
coincidence or a pattern as more releases go through the same
contamination-avoidance discipline.

## 6. Release gate evaluation (per `gold_v1.2.2_curriculum.md`)

| Gate | Result |
|---|---|
| Format validity remains 100% | ✅ 16/16 |
| All 9 baseline regression guards still pass | ✅ 9/9 |
| At least 4 of 7 negative examples resolve | ✅ 4/7 (03, 12, 14, 15) |
| Probe 15 resolves | ✅ Yes |
| At least one of probes 14 or 16 resolves without regressing the other | ✅ 14 resolved; 16 stayed a fail on the same failure category (Unsupported Addition) it already had — didn't newly break |
| No resolved probe counted as passing with partial credit | ✅ Verified — 03/12/14/15 all score exactly 2 on every non-null dimension |
| No new unsupported-addition failures appear | ⚠️ **Not clean** — probe 02 didn't have "Unsupported Addition" among its failure labels before (it had "Excessive Fragmentation"); this run's garbled reconnection is scored as a new Unsupported Addition instance. Flagging this explicitly rather than silently passing the gate: the letter of "no *new* unsupported-addition failures" is arguably violated by one probe, even though the release's overall unsupported-addition count moved in the right direction otherwise (probe 14 fully fixed, probe 16 same as before). |

**Overall**: 6 of 7 gates pass cleanly; the seventh has a specific, narrow,
well-evidenced exception (probe 02) rather than a passing result. Given
probe 15's resolution (the hard requirement) and 3 additional resolved
negative examples against only one probe getting a different kind of
failure, this reads as net positive — but the exception should be a
decision point for acceptance, not something to average away.

**Stretch goal** (7/7 negatives, 16/16 strict): not met — 4/7 and 13/16
respectively. Not required for acceptance.

## 7. Decision: reclassify 03, 12, 14, 15 back to `regression_guard`?

**Decided**: product owner approved reclassifying `12`, `14`, and `15` to
`regression_guard` — all three are now protected against future
backsliding, updated in `datasets/benchmark/gold_v1.2.1_probes.jsonl` and
in this run's own results file
(`training/gold_v1.2.2_benchmark_results_checkpoint600.json`). `03` stays
`negative_example` pending one additional clean run before promotion, per
the same caution — probe `02`'s new regression (see above) is a live
reminder that a resolution on this checkpoint isn't automatically stable.
Re-run: `regression_guard` count is now 12/16, `negative_example` count is
4/16 (`02`, `03`, `08`, `16`) — regression guards 12/12 (100%), negative
examples resolved 1/4 (25%, just `03`).

Also decided: **not** cutting a production release from `checkpoint-600`.
It's kept as a candidate/comparison baseline only — `checkpoint-520`
remains deployed. Next release: a compact `gold_v1.2.3` corrective release
targeting exactly the three remaining negative examples (`02`, `08`,
`16`), rather than folding them into a broader theme.

## 8. Changes recommended before Gold v1.3

1. **Investigate probe 02's regression specifically** — a follow-up
   example that reinforces correct "explicit interruption marker →
   resume" reconnection *without* reusing probe 02's literal wording
   (unlike the now-revised example 005) would test whether the transfer
   loss above is fixable without recreating the contamination risk.
2. **Continue watching probe 08's wording clarity** — unresolved across
   three consecutive releases now (`gold_v1.2.1` and `gold_v1.2.2` both
   score it partial for the same reason: correct non-answer, unclear
   phrasing). May need a dedicated wording-clarity-focused example rather
   than assuming a general evidence-boundary release will fix it as a
   side effect.
3. **Populate `real_holdout.jsonl`** — still the single most-repeated
   recommendation across every lessons-learned doc so far, still not
   done.

## 9. Is a populated `real_holdout.jsonl` now required before the next training run?

Same answer as `gold_v1.2.1`'s: yes, recommended, still not done. 6
validation examples is still too few for `eval_loss` to be a meaningful
signal, though this no longer causes a checkpoint-selection bug since
`load_best_model_at_end=False`.
