# A4 — Target Audit Rubric and Conversion-Effort Timing Protocol

**Operationalizes:** `training/intent_recovery_data_model_discovery_plan_chatgpt.md` §3, "A4. Target audit
and conversion estimate".

**Status: rubric only.** No external target has been read or classified. This document defines the
criteria a future authorized pass would apply, after A3 input tagging is complete and targets are revealed
for the first time.

## Sequencing rule, restated from the plan

Targets are revealed **only after** input labels (A3) freeze. A reviewer who has already seen a candidate's
target and then goes back to tag its input is not doing input-only mapping — this rubric assumes A3 is
already closed for a record before that record's target is opened.

## Classification

Each of the 24 records' existing target gets exactly one classification:

| Class | Criterion |
|---|---|
| **Usable** | Satisfies the project's output contract without unsupported additions or loss. |
| **Re-annotation required** | The input is useful, but the target smooths uncertainty, omits supported details, merges tasks/speakers, or violates the project's structural/tone contract. |
| **Incompatible** | The input lacks the relevant mechanisms, provenance/rights failed at A1, or conversion would require reconstructing context the input doesn't supply. |

Existing targets **do not need to pass** to make the candidate viable — a high re-annotation rate is an
expected, decision-relevant result (plan §3 A5), not a failure of this rubric.

## Scoring dimensions

Score each record's *existing* target against these dimensions. Each is a **fact/criterion check against
the input**, not a style preference:

1. **Supported-fact survival** — every fact stated in the input that a competent summary would need is
   present in the target, or its absence is explainable (irrelevant, not a recovery-relevant fact).
2. **Supported-task-component survival** — every actor/recipient/object/destination/quantity/deadline/
   condition A3 tagged as present in the input survives into the target's task representation.
3. **Uncertainty/open-question preservation** — anything A3 tagged as uncertainty, unresolved state,
   condition, or alternative remains marked as unresolved in the target, rather than being silently
   resolved one way.
4. **Invented facts/tasks** — count anything in the target not supported by the input. This project's
   `action_items` rule (`training/DATASET_SPEC.md`: "Use an empty array `[]` when the input has none — never
   invent one") is the concrete precedent this dimension enforces; a target inventing an action item the
   input never stated fails this dimension regardless of how reasonable the invention sounds.
5. **Task separation** — distinct tasks/speakers A3 tagged as separate remain separate in the target, not
   merged into one.
6. **Attribution** — where A3 tagged multi-person attribution, the target preserves who said or owns what.
7. **Chronology** — where A3 tagged mixed chronology, the target does not silently reorder events into a
   cleaner sequence than the input supports.
8. **Structural-contract compliance** — measured against this project's actual contract
   (`training/DATASET_SPEC.md` §"Rules for `output`"): a `narrative` covering the same input content in
   flowing form; `bullets`, one per source-supported idea, **up to 7, source-determined count** — never
   padded or split to hit a target number; `action_items`, concrete and input-supported, `[]` when none
   exist. A target's own native format almost certainly differs from this contract — this dimension scores
   whether the *content* could be reshaped into it without adding, inferring, or losing anything, not
   whether the target already happens to look like it.

Each dimension is scored **pass / partial / fail** per record, with a one-line rationale citing the
specific input span (from the A3 tags) and target text that drove the score.

## Conversion-effort timing protocol

**Revised 2026-08-12** per ChatGPT's independent review: the first version left the 6-record subset's
selection to reviewer discretion, which risks (even unintentionally) picking the easiest or hardest records
after their difficulty is already apparent — biasing the effort estimate in either direction. The subset
must be drawn by the same predeclared, unbiased method A2 uses, not chosen by feel.

For records classified `Re-annotation required`:

1. **Select the timing subset deterministically, not by discretion.** Reuse `select_sample()`'s
   determinism approach (`training/discovery_audit_package_a2_sample_selection_script.py`): sort the
   `Re-annotation required` records by record_id, then draw 6 of them (or all of them, if fewer than 6
   qualify) with `random.Random(AUDIT_SEED)` — the same pinned seed A2 uses, for the same reason: fixed
   before anyone has looked at which records are easy or hard to re-annotate. Record the exact record_ids
   drawn in the audit report.
2. A reviewer blind-re-annotates each timing-subset record from scratch, under this project's own authoring
   rules (`training/DATASET_SPEC.md`), with a stopwatch, recording elapsed minutes per record.
3. A second reviewer independently re-annotates the same subset, blind to the first reviewer's output and
   time.
4. Report **median minutes per record**, not just a mean (re-annotation effort is expected to be
   right-skewed — a few records will be much harder than the rest), computed **per reviewer** first, then
   the two reviewers' medians reported side by side (not pre-averaged into one number, so a large gap
   between reviewers is visible rather than hidden).
5. Report **disagreement rate**: for the timing subset, score the two independent re-annotations against
   each other on the same 8 dimensions above; a record counts as "disagreed" if the two re-annotations
   diverge by more than one level (e.g. one scores `pass`, the other `fail`) on **any** dimension. Report
   the disagreement count out of the subset size, plus which dimensions drove it.
6. Extrapolate a full-sample effort estimate as a **range** (using the lower and higher of the two
   reviewers' median-minutes figures × the full `Re-annotation required` count), not a single point
   estimate, and flag it explicitly as based on a 6-record subset, not a guarantee.

This estimate is a required input to Johnny's affordability judgment in A5 — it does not itself decide
anything.

## What this rubric does not do

It does not decide whether the candidate as a whole clears the dataset-fit bar — that aggregation happens in
A5, using this rubric's per-record outputs (usable-input percentage) as one required input.
