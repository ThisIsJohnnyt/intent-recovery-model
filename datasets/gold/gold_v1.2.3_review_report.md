# gold_v1.2.3 Review Report

**Reviewed against**: `gold_v1.2.3.jsonl` (6 examples),
`gold_v1.2.3_curriculum.md`, `gold_v1.2.3_design_notes.md`
**Date**: 2026-07-30
**Author**: Claude Code (implementation engineer), independent check per
`docs/datasets/REVIEW_GUIDE.md`'s release-bundle table.

## 1. Schema validity — ✅ Pass

```
6 records validated OK (training/prepare_data.py's load_jsonl)
```

## 2. "No Magic Examples" — ✅ Pass

Every fragment in every example has a documented reason in
`gold_v1.2.3_design_notes.md`'s "Reason each fragment exists," including
why discourse-marker phrases ("Quick interruption," "Resuming the upload
issue," "To finish that thought," "Coming back to the export") are
present but must never leak into recovered content.

## 3. One lesson per example — ✅ Pass

6 examples, 3 categories, all pre-existing
(`interrupted_thought_depth`, `open_question_preservation`,
`dangling_reference`) — no new categories introduced, matching the
curriculum's stated plan.

## 4. Evidence-first compliance ("No invented content") — ✅ Pass

Checked all 6 examples for invented causes, invented answers, or
resolved ambiguity: none found. Both `open_question_preservation`
examples (004, 005) correctly keep both alternatives visible and keep
the later observation from resolving either one. `dangling_reference`
(006) preserves both unresolved references and stops at the last
supported clause with no appended commentary.

## 5. No diagnosis framing — ✅ Pass

Scanned all three bundle files for `adhd`, `autis`, `diagnos`,
`neurodivergen` (case-insensitive): matches exist only as "diagnose the
greenhouse monitor" / "diagnostic thought" (example 002, targeting a
technical malfunction) — not a reference to a person's condition. No
actual diagnosis-framing violation.

## 6. Benchmark-wording/pattern reuse — ✅ Pass (the finding that blocked `gold_v1.2.2`'s first draft)

This is the check that mattered most given `gold_v1.2.2`'s independent
review found real violations here (a verbatim phrase copied from probe
`03`, plus reused nouns and sentence skeletons on 3 other examples).
Checked all 6 new examples individually against the actual text of
probes `02`, `08`, and `16` — not just against the curriculum's own
"Benchmark separation" claims:

- **Probe 02 analogues (001, 002, 003)**: no shared nouns with probe 02
  (tablet, donation box, front door, screen, charger appear nowhere).
  None reproduce the "back to the X" resumption phrase — the exact
  literal element flagged as reused in `gold_v1.2.2`. Three genuinely
  different structures: explicit discourse labels (001), grammatical
  continuation with no marker phrase for the interruption itself plus a
  different marker ("to finish that thought") for a later resumed detail
  (002), and topic-label return (003).
- **Probe 08 analogues (004, 005)**: no shared nouns (wet spot, window,
  plant, lunchtime, recycling appear nowhere). 004 changes the
  information order (observation-question-observation, not
  probe 08's question-observation-task) and drops the third topic
  entirely. 005 uses declarative modal wording ("may have come from X or
  Y; the note does not settle which") instead of probe 08's direct
  interrogative.
- **Probe 16 analogue (006)**: no shared words at all. Different verb
  frame ("send it back to..." vs. "remember to ask them about..."),
  different reference type (a recipient description vs. a pronoun +
  object).

No verbatim phrases, no reused nouns, no reused sentence skeletons found
in any of the 6 examples. This is a genuine improvement in discipline
over the first `gold_v1.2.2` draft, not just an assertion — independently
re-verified, not taken on the curriculum doc's word.

## 7. Design notes match the data — ✅ Pass, no drift

Compared every example's `narrative`/`bullets`/`action_items` against
`gold_v1.2.3_design_notes.md`'s "Expected field-by-field recovery" word
for word. All 6 match exactly.

## 8. Curriculum Integrity — ✅ Pass

No example exercises anything in the "Out of scope" list. Every example
traces to one of the three named target probes (02, 08, 16) via an
explicit "Benchmark analogue" field, and the curriculum's own
"Curatorial rationale" correctly argues against adding broad combination
pressure this release.

## 9. Distribution check — ✅ Pass

| | Planned | Actual |
|---|---|---|
| Difficulty | 1 medium, 4 hard, 1 expert | 1 medium, 4 hard, 1 expert |
| Category | 3 interrupted_thought_depth, 2 open_question_preservation, 1 dangling_reference | Same |

## Finding: `CATEGORY_REFERENCE.md` difficulty-seen column needs updating

`interrupted_thought_depth` is used at `expert` difficulty for the first
time (example 003) — the live `CATEGORY_REFERENCE.md` row currently lists
`medium, hard` only. Not a defect in this release, just an update this
release triggers, per the table's own maintenance convention. Recommend
adding `expert` to that row's "Difficulty seen" column at acceptance.
`open_question_preservation` and `dangling_reference` are used at
difficulty tiers already listed for each — no change needed there.

## Release-readiness checklist

Per `docs/datasets/REVIEW_GUIDE.md`'s "Release Checklist":

- [x] Schema validation passes
- [x] Design notes complete, including Boundary Evidence
- [x] Review report complete (this document)
- [x] Category reference updated — added `expert` to
      `interrupted_thought_depth`'s difficulty-seen column; no new rows
      needed
- [ ] `CHANGELOG.md` updated — next step
- [ ] Benchmark and holdout cases identified — not yet done; not blocking
- [x] Independent review passes (this review)
- [x] Training compatibility confirmed (`prepare_data.py` reads it cleanly)
- [ ] Evaluation shows no unacceptable regression — pending the next
      training run
- [ ] Lessons learned recorded — after training + evaluation
- [x] Coverage distribution satisfied per `gold_v1.2.3_curriculum.md`

## Findings summary

**Blocking**: none.

**Borderline**: none.

**Informational**: `CATEGORY_REFERENCE.md`'s `interrupted_thought_depth`
row should gain `expert` in its difficulty-seen column at acceptance
(see finding above).
