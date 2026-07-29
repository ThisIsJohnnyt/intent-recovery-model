# gold_v1.1 Review Report

**Reviewer**: Claude Code (independent engineering review, per
[`docs/datasets/REVIEW_GUIDE.md`](../../docs/datasets/REVIEW_GUIDE.md))
**Date**: 2026-07-28
**Source**: Gemini-generated, 15 examples, no author design notes provided

This is an independent review, run separately from the dataset curator's
own assessment — per the project's two-reviewer process, agreement
increases confidence and disagreement gets a closer look.

## 1. Schema validity — ✅ Pass

All 15 records validate against `training/prepare_data.py`'s schema
validator without error.

## 2. "No Magic Examples" — ✅ Pass

Every fragment across all 15 examples is explainable: interruptions (door/
package arrival, stove-check), self-corrections (voice-to-text example),
repeated reminders, dangling references. Example 14 (camera settings) is a
particularly clean case — it correctly keeps technical calculations
(f-stop, ISO) and a pure status note ("tripod is in the trunk") out of
`action_items`, extracting only the one genuine task ("pack the 50mm
lens"). That's exactly the observation-vs-task discrimination the review
guide asks for.

## 3. One lesson per example — ⚠️ One soft mismatch

`contradictory_statements` (the Python script example: "completely broken...
oh wait, just a missing comma... works perfectly now!") is a coherent
frustration → relief narrative arc, not the "mood clearly shifted between
lines" *unresolved* contradiction `training/DATASET_SPEC.md` originally
described for this category. Still a good, useful example — flagging for
the curator to consider whether it needs a different category label (e.g.
something like `resolved_frustration`) rather than rejecting it.

## 4. No invented content — ⚠️ Two borderline examples

- **Example 5** (meeting/tired/glasses): input says "need new glasses
  prescription"; `action_items` includes "Schedule an eye exam for a new
  prescription." The input doesn't state the mechanism (scheduling an eye
  exam) — it's a reasonable real-world inference, but it does add a
  specific action beyond what's literally there.
- **Example 11** (router/blue folder/daughter): input is a self-directed
  question ("what did my daughter say about friday?"); `action_items`
  includes "Ask daughter about Friday," which assumes the person needs to
  go ask her, rather than just recall it themselves. Also a reasonable
  inference, but similarly adds a mechanism not stated.

Neither is egregious. Flagging both for the curator's judgment call rather
than editing the data myself — dataset content decisions aren't Claude
Code's to make unilaterally.

## 5. No diagnosis framing — ✅ Pass

All 15 examples describe cognitive/emotional state (tired, overwhelmed,
excited, hyperfocused, anxious) without referencing a diagnosis.

## 6. Diversity coverage — ✅ Strong

This batch meaningfully advances coverage against
[`CATEGORY_REFERENCE.md`](../../docs/datasets/CATEGORY_REFERENCE.md)'s gap
list:

- Fills previously-empty categories: `short_note`, `long_rambling`,
  `repeated_reminder`, `dangling_reference`.
- First-ever examples of three cognitive/emotional states:
  `rapid_branching_excitement`, `hyperfocus` (as `hyperfocus_details`),
  and `anxiety` (as `anxious_task_dump`).
- Adds `interleaved_work_personal`, `voice_to_text_artifacts`,
  `abrupt_topic_switching` as useful additional structural variety.

Still open after this batch: sensory overwhelm, burnout, emotional
journaling, and "many unrelated topics interleaved at once" (distinct from
this batch's `interleaved_work_personal`, which is two topics — work and
personal — not several at once).

## 7. Design notes — ⚠️ Not provided

This batch has no author-side design notes (unlike `gold_v1.0`). Per
[`DESIGN_NOTES_TEMPLATE.md`](../../docs/datasets/DESIGN_NOTES_TEMPLATE.md),
these should come from whoever authored the batch (author intent isn't
something a reviewer can originate after the fact) — pending from the
curator if desired for this release.

## Summary

**Recommendation: accept as `gold_v1.1`.** Strong schema validity, strong
"No Magic Examples" adherence, and the best diversity gains of any batch so
far. Two borderline action-items and one category-label nuance flagged
above for the curator's consideration on a future revision — not blocking
acceptance.
