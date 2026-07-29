# gold_v1.2.1 Lessons Learned

**Date**: 2026-07-29
**Evaluation method**: Gold v1.2.1 Semantic Live-Evaluation Suite (proposed
by ChatGPT) — 16 probes (12 capability probes across 4 reinforcement skills
+ 4 regression probes), run via
`training/run_gold_v1.2.1_probes.py` against the fine-tuned checkpoint
directly (not the browser app), then scored by Claude Code against each
probe's stated Expected Behavior. Full raw outputs in
`training/gold_v1.2.1_probe_results.json` (epoch 2) and
`training/gold_v1.2.1_probe_results_epoch40.json` (epoch 40).

## 1. Training configuration

FLAN-T5-base fine-tuned on `datasets/synthetic.jsonl` consolidated to 54
examples (`gold_v1.0`+`v1.1`+`v1.2`+`v1.2.1`), 49 train / 5 val, 40 epochs,
`Seq2SeqTrainingArguments(eval_strategy="epoch", save_strategy="epoch",
save_total_limit=2, load_best_model_at_end=True)`.

## 2. Loss and format-validity results

`train_loss` 0.1647 (from 1.89). `eval_loss` bottomed at **1.24 at epoch 2**,
then rose to 2.45 by epoch 40 — the same overfitting shape seen in
`gold_v1.2`'s run, expected at this data scale.

**Because `load_best_model_at_end=True` selects by lowest `eval_loss`, the
checkpoint actually saved to `checkpoints/thoughtorganizer-flan-t5/final`
and exported to ONNX for the app was epoch 2 (`checkpoint-26`, confirmed via
`trainer_state.json`'s `best_model_checkpoint`), not epoch 40.** Format
validity on the train.py's own built-in val-split check: 5/5 (all
well-formed) — this check alone didn't reveal the problem below.

## 3. Probe-by-probe semantic findings

Ran both checkpoints against all 16 probes for comparison. Format validity:
**epoch 2 = 12/16, epoch 40 = 16/16.**

| # | Capability | Kind | Epoch 2 | Epoch 40 |
|---|---|---|---|---|
| 01 | Interrupted/Nested Depth | direct | **Fail** — invents "is working" to complete the interrupted thought, wrongly promotes it to `action_items` | **Pass** — preserves incompleteness, correctly excludes it from actions |
| 02 | Interrupted/Nested Depth | transfer | Pass — correctly reconnects the interrupted/resumed fragments | Partial — reconnects correctly but adds a spurious third action item ("Back to the tablet") |
| 03 | Interrupted/Nested Depth | adversarial | Partial — `actions` correct (unsplit), but `bullets` splits the explicitly-combined task anyway | Partial — `actions` correct, but drops the clock observation from `bullets` entirely and adds a redundant duplicate bullet |
| 04 | Multi-Person Attribution | direct | **Fail** — narrative/actions misattribute the ask-target to Morgan instead of Avery (bullets alone got it right) | **Pass** — all three fields consistently attribute to Avery |
| 05 | Multi-Person Attribution | transfer | **Severe fail** — reverses speaker/actor roles, invents a completed action, missing `###ACTIONS###` entirely | Pass — correct attribution, question stays unresolved, task correctly phrased as pending (one typo, "backped up") |
| 06 | Multi-Person Attribution | adversarial | Partial — narrative preserves ambiguity, but `bullets` invents an assignment to a third party (Rowan) who isn't even a candidate | Pass — ambiguity preserved consistently across all fields |
| 07 | Open-Question Preservation | direct | Partial — question stays unresolved, but the pending task gets reframed as already completed ("I saved...") | Pass — question unresolved, task correctly phrased as pending |
| 08 | Open-Question Preservation | transfer | **Severe fail** — confidently asserts the wet spot "was the plant" (Invented Answer), degenerate repetition in `actions` | Partial — no invented answer, but the question's specific content (window vs. plant) comes through confusingly worded |
| 09 | Open-Question Preservation | adversarial | **Severe fail** — confidently asserts the schedule "was sent," missing `###ACTIONS###` entirely | Pass — question stays unresolved, checking task correctly tied to resolving it |
| 10 | Task Retention | direct | Partial — task correct in `bullets`/`actions` but dropped from `narrative`, plus a duplicated clause | Pass — task present in all three fields, no duplication |
| 11 | Task Retention | transfer | Pass — clean dedup, no invented repair task, both real tasks survive | Pass — same clean result |
| 12 | Task Retention | adversarial | Partial — oil-change task missing from `narrative` and `bullets` (present in `actions`); "maybe" hedge on screenshots dropped | Partial — oil-change task still missing from `narrative` (now present in `bullets`); "maybe" hedge correctly preserved |
| 13 | Regression: basic tasks | — | Pass | Pass |
| 14 | Regression: zero action items | — | **Fail** — missing `###ACTIONS###` entirely, so the "don't invent a task" behavior can't even be confirmed | Pass — `actions` correctly empty (one spurious, harmless hallucinated bullet, "Morning fan") |
| 15 | Regression: idea without commitment | — | **Fail** — drops the "maybe" hedge, invents an unrelated fabricated detail, promotes the idea to a committed action item | Partial — "might"/"considering" hedge preserved in narrative, but still invents a fabricated detail *and* still promotes the idea to a committed action item |
| 16 | Regression: dangling reference | — | **Severe fail** — invents "my colleagues" as who "them" refers to, missing `###ACTIONS###` | Pass — preserves the dangling reference without inventing the referent (one spurious harmless bullet, "Reply to this question") |

## 4. Capability-level conclusions

- **Interrupted/Nested Depth**: unstable on both checkpoints. Epoch 40 fixed
  the direct case's core failure (inventing thought completion) but
  introduced a new excessive-fragmentation artifact on the transfer case.
  Neither checkpoint cleanly passes all three probes.
- **Multi-Person Attribution**: epoch 2 failed this capability outright
  (all three probes had a misattribution somewhere); epoch 40 passes all
  three cleanly. The clearest capability-level improvement from using the
  correct checkpoint.
- **Open-Question Preservation**: epoch 2 invented a confident answer on
  2 of 3 probes — exactly the failure this release was built to prevent.
  Epoch 40 invents no answers on any probe, though phrasing quality varies.
- **Task Retention**: the strongest capability on both checkpoints. Tasks
  reliably survive in `action_items` even when dropped elsewhere, and the
  transfer probe (repeated task, emotional aside) passes cleanly on both.

## 5. Regressions

Probe 15 (idea without commitment) is a **confirmed, unresolved regression
on both checkpoints** against established `gold_v1.2` policy
(`task_plus_idea`/`observation_plus_idea`: an idea should appear in
`bullets`, never promoted to `action_items`). Epoch 40 improved the
narrative-level hedging but the `action_items` field — the one that
actually drives the app's UI — still fails this test on both checkpoints.
This needs attention before `gold_v1.3`, independent of the
checkpoint-selection issue below.

## 6. Surprising successes or failures

**The most significant finding of this run isn't about the dataset — it's
about the training configuration.** `load_best_model_at_end=True` with only
5 validation examples selected epoch 2 (`eval_loss` 1.24) over epoch 40
(`eval_loss` 2.45) as "best," but epoch 2 is clearly the worse checkpoint on
every semantic dimension tested: it fails all three multi-person-attribution
probes, invents confident answers on two of three open-question probes, and
fails two of four regression probes outright (missing `###ACTIONS###`
entirely). `eval_loss` on a 5-example set is not a reliable proxy for
semantic quality at this data scale — it happened to reward an undertrained
checkpoint that hadn't yet learned the harder "don't invent" discipline,
while the fully-trained checkpoint that "overfit" by the loss metric is
actually the better model by every semantic measure in this suite.

**The app is currently running the worse checkpoint.** This should be
corrected — re-export `checkpoint-520` (epoch 40) to ONNX and redeploy,
rather than the current `final/` (epoch 2).

## 7. Changes recommended before Gold v1.3

1. **Fix checkpoint selection**: either set `load_best_model_at_end=False`
   and always use the final epoch, or increase the validation set size
   enough that `eval_loss` is a meaningful signal again (5 examples is too
   few) — the latter depends on populating `real_holdout.jsonl` or growing
   `synthetic.jsonl`'s validation split.
2. **Address the idea-vs-action-item regression** (probe 15) — this is an
   established `gold_v1.2` behavior that both checkpoints fail; worth a
   small, targeted set of reinforcement examples rather than folding it into
   `gold_v1.3`'s sensory-overwhelm theme.
3. **Watch narrative-field completeness specifically** — several probes
   (10, 12) show a task surviving in `bullets`/`actions` but dropping from
   `narrative`. This is a distinct, narrower failure than general Topic Loss
   and worth naming if it recurs.

## 8. Which probes become protected regression benchmarks

Done — all 16 probes moved to `datasets/benchmark/gold_v1.2.1_probes.jsonl`
(with a companion `gold_v1.2.1_probes.md`), the first real entries in that
directory. Classified against `checkpoint-520`'s actual results: 11 as
`regression_guard` (currently passing — protect against future backsliding)
and 5 as `negative_example` (`02`, `03`, `08`, `12`, `15` — currently
revealing a real limitation, tracked for future improvement rather than
silently accepted).

## 9. Is a populated `real_holdout.jsonl` now required before the next training run?

Yes, recommended. This run's `eval_loss`-based checkpoint selection problem
is a direct symptom of the validation set being too small (5 examples) to
be a meaningful signal — a populated `real_holdout.jsonl` would both fix
that and restore the original purpose it was designed for (checking
synthetic-only training generalizes to real writing), which still hasn't
been exercised in any run so far.
