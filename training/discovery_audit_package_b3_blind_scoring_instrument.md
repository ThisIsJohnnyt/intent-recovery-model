# B3 — Blind Scoring Instrument and Interpretation Table

**Operationalizes:** `training/intent_recovery_data_model_discovery_plan_chatgpt.md` §4, "B3. Scoring" and
"B4. Interpretation".

**Status: instrument only.** No output has been scored — none exists yet, since no model has run (B1/B2
remain gated). This document is what a future authorized scoring pass would use.

**Revised 2026-08-12** per ChatGPT's independent review and Johnny's dispositions: (1) the plan's ≥6-gain/
≤1-regression success threshold was never translated into a computable per-example verdict from this
instrument's multidimensional scores — fixed below with an explicit aggregation rule; (2) the scoring
schema collapsed distinct dimensions (questions/alternatives folded into "uncertainty," narrative/bullets/
action-items folded into one contract-validity boolean) — fixed below to match A3's now-split subtypes and
the contract's three actual parts; (3) the panel grew from 3 to 4 models (Johnny added a current-fine-
tuned-checkpoint arm — see B1) — every count and the B4 table below are updated accordingly.

**Revised again 2026-08-13** per ChatGPT's second review: the 2026-08-12 revision introduced a real
self-contradiction — it re-scoped the ≥6-gain threshold to protected-cases-only, directly contradicting
this document's own unedited verbatim-plan section a few paragraphs below it. Fixed: gains are counted over
the full 36-example set (unpooled across conditions), only the ≤1-regression ceiling is scoped to
protected-style cases, matching the plan's actual sentence. Also fixed a stale "baseline/stronger/ceiling"
reference in the reporting rules that never got updated for the fourth arm.

## Blinding requirement

Reviewers score outputs **without knowing which model or condition produced them**. The freeze manifest
(B2) already fixes which examples/conditions/models exist before any output is generated; the scoring pass
adds one more blind layer — outputs are shuffled and stripped of model/condition identity before reaching a
scorer. Reuse this project's frozen rubrics where they already apply (the existing protected/acceptance
scoring conventions), rather than inventing a parallel one.

## Per-example scoring dimensions

For every one of the 36 examples × 2 conditions × 4 models = 288 scored outputs:

1. **Supported facts retained** — count of input facts a correct recovery needs, present in the output.
2. **Supported task components retained** — count of A3-style task components (actor/recipient/object/
   destination/quantity/deadline/condition) present in the input, present in the output.
3. **Unsupported facts/tasks introduced** — count of anything in the output not supported by the input.
   Mirrors this project's `action_items` invention rule (`training/DATASET_SPEC.md`): any invented item
   counts here regardless of plausibility.
4. **Uncertainty preservation, split to match A3's own subtypes** (an earlier version of this instrument
   collapsed these into one field, inconsistent with A3's split): `question_preservation`,
   `uncertainty_hedge_preservation`, `unresolved_state_preservation`, `condition_preservation`,
   `alternative_preservation` — each scored pass/partial/fail against whether the output preserves what
   the input actually supports.
5. **Attribution, chronology, task separation** — each scored pass/partial/fail, same standard as A4 uses
   for existing targets, now applied to model outputs.
6. **Output-contract validity, split into its three actual parts** (an earlier version of this instrument
   collapsed these into one boolean, losing exactly the breakdown structural error analysis needs):
   `narrative_valid` (covers the input faithfully, same meaning/tone), `bullets_valid` (≤7,
   source-determined count — never padded or split to hit a number), `action_items_valid` (concrete,
   input-supported, `[]` when none exist).
7. **Tone** — respectful, calm, non-diagnostic, non-patronizing. Scored pass/fail with a one-line rationale
   quoting the offending phrase, if any.
8. **Repairability** — can a deterministic validator/formatter fix any contract violation without
   regenerating semantic content? (E.g. a bullet count over 7 that's actually just formatting, versus a
   bullet that invents content — the former is repairable, the latter is not.)

## Paired verdict — how these dimensions become a "gain," "regression," or "no change" (added 2026-08-12)

The plan's success criterion ("improves at least 6 paired examples... no more than 1 paired regression")
presupposes a single verdict per example, but the dimensions above are multidimensional. This instrument
did not previously say how they combine — fixed here with an explicit, predeclared rule rather than one
chosen after seeing results:

**Clean pass (binary, per output):** an output counts as a clean pass only if *all* of the following hold:
`unsupported_facts_tasks_introduced == 0`; every one of dimensions 4–5 above is `pass` (not `partial` or
`fail`); all three of `narrative_valid`/`bullets_valid`/`action_items_valid` are true; `tone` is `pass`; and
`supported_facts_retained` / `supported_task_components_retained` both equal their respective totals (no
partial credit — this mirrors this project's existing all-or-nothing protected/acceptance gate style, not a
new invention). Anything short of all of these is **not** a clean pass.

**Paired verdict, per example, per condition, for a given candidate arm vs. the baseline arm (arm 1,
untuned FLAN-T5-base):**
- **Gain:** baseline is not a clean pass, candidate is.
- **Regression:** baseline is a clean pass, candidate is not.
- **No change:** both are clean passes, or neither is.

**Per-condition, not pooled:** gains/regressions are counted **separately** for the zero-example and
fixed-few-example conditions, never merged into one pooled count. Pooling would let a model "pass" by
improving under few-shot while failing zero-shot, which conflates two different capability questions the
plan's own B4 table treats as distinct (its own row: "Few-example condition succeeds where zero-example
fails" is a specific, separately meaningful finding — it can only be reported if the two conditions were
never merged in the first place).

**Success criterion applies to the stronger and ceiling arms only** (arms 3–4, Qwen3-4B and Qwen3-14B),
each compared against arm 1 (untuned baseline), separately per condition. **Corrected 2026-08-13**: the
2026-08-12 version of this paragraph scoped *both* the gain count and the regression ceiling to the 12
protected-style cases — ChatGPT's second review caught that this directly contradicts the plan's actual
wording (and this document's own unedited "Success criterion (plan §4 B3, verbatim thresholds)" section
just below, which was never wrong) and re-scoped both together during an unrelated edit. The plan's
sentence only scopes the *regression ceiling* to protected cases; the *gain count* is over the full frozen
set. Corrected:

A model "succeeds" only if, in **both** conditions:
- it passes every safety/non-invention gate on all 36 examples (zero
  `unsupported_facts_tasks_introduced` and `tone == pass` on every one of its 72 outputs), **and**
- it achieves **≥6 gains over the full 36-example set** (all three categories — protected-style,
  acceptance-style, adversarial — count toward this), **with ≤1 regression counted specifically among the
  12 protected-style cases** (regressions in the other 24 examples don't count against this particular
  ceiling, but do still count against the general "no more than what the safety gate allows" framing above
  and must be reported regardless).

**Arm 2 (current fine-tuned checkpoint) is diagnostic, not subject to the same pass/fail label.** It is
scored with the identical clean-pass framework, compared against arm 1, to feed the B4 table's "untuned
baseline succeeds where current fine-tuned checkpoint fails" row directly — but this comparison answers a
different question (is fine-tuning helping or hurting relative to the untuned base?) than the stronger/
ceiling "succeeds" criterion, and the two must not be conflated into one number.

## Reporting rules

- Report **exact counts and paired differences** per example, for every arm compared against baseline
  (arm 1 untuned vs. arm 2 current-fine-tuned-checkpoint, arm 1 vs. arm 3 stronger, arm 1 vs. arm 4
  ceiling), per condition — not an aggregate score that hides which specific examples changed. **Corrected
  2026-08-13**: an earlier version of this line still listed only "baseline/stronger/ceiling," left over
  from before Johnny added the fourth arm.
- **Do not claim statistical generalization** from 36 examples. This is a bounded capability probe, not a
  population estimate — say so explicitly in any report this instrument produces.
- **Adjudicate disagreements between scorers before unblinding.** Unblinding first and adjudicating after
  risks the adjudicator's judgment being colored by which model they now know produced the disputed output.

## Success criterion (plan §4 B3, verbatim thresholds — see the operational "Paired verdict" section above
for exactly how these get computed from the scoring dimensions)

A model "succeeds" for this discovery only if it:

- passes all existing safety/non-invention gates, **and**
- improves at least **6 paired examples** over baseline, **with no more than 1 paired regression on
  protected semantic cases**.

Both conditions are required. Improving 6+ examples while regressing 2+ protected semantic cases does not
meet this bar.

## Interpretation table (plan §4 B4, reproduced for use alongside the scored results)

**Revised 2026-08-12:** the "untuned baseline succeeds where current fine-tuned checkpoint fails" row was
previously unsupportable by the declared panel (no arm was the project's actual checkpoint). Per Johnny's
2026-08-12 disposition, B1 gained a fourth arm specifically so this row is now testable — see B1 and the
"Arm 2 is diagnostic" note above.

| Frozen observation | Supported next decision |
|---|---|
| Stronger and ceiling models succeed; baseline fails | Capacity is material; propose deployment/finetuning feasibility work. |
| All models fail the same semantic cases | Prioritize specification, annotation, or task decomposition. |
| Semantic content survives but structure fails across models | Prototype deterministic validation/formatting or constrained generation before adding data. |
| Few-example condition succeeds where zero-example fails | Annotation examples carry value; consider distillation or retrieval of demonstrations. |
| Untuned baseline (arm 1) succeeds where current fine-tuned checkpoint (arm 2) fails | Audit training-induced regression before more training. |
| Ceiling alone succeeds | Capability exists but may be impractical; assess distillation/decomposition rather than automatic scale-up. |
| Results are mixed below the declared threshold | No capacity conclusion; inspect predeclared error strata and redesign a later audit. |

This table interprets a result once one exists — it does not, by itself, authorize acting on any row
(training, deployment, or further data work each remain separately gated per plan §4 and the responsibility
protocol).

## Scoring record schema

```json
{
  "example_id": "b2-protected-01",
  "condition": "zero_example",
  "model_blinded_label": "model_B",
  "scores": {
    "supported_facts_retained": 0,
    "supported_facts_total": 0,
    "task_components_retained": 0,
    "task_components_total": 0,
    "unsupported_facts_tasks_introduced": 0,
    "question_preservation": "pass|partial|fail",
    "uncertainty_hedge_preservation": "pass|partial|fail",
    "unresolved_state_preservation": "pass|partial|fail",
    "condition_preservation": "pass|partial|fail",
    "alternative_preservation": "pass|partial|fail",
    "attribution": "pass|partial|fail",
    "chronology": "pass|partial|fail",
    "task_separation": "pass|partial|fail",
    "narrative_valid": true,
    "bullets_valid": true,
    "action_items_valid": true,
    "tone_pass": true,
    "repairable_without_regeneration": true
  },
  "clean_pass": false,
  "scorer_id": "...",
  "adjudicated": false
}
```

`clean_pass` is a derived field (computed from the scores above using the "Clean pass" definition earlier
in this document), included explicitly so the paired-verdict computation is a direct read of the record,
not a re-derivation someone could get wrong later — the same pattern A3's schema uses for
`priority_mechanism_present`.

## What remains gated

Scoring requires outputs to score, which requires B1 (model freeze) and B2 (example freeze) to be executed
first — both remain gated behind Johnny's separate authorization of acquisition/execution.
