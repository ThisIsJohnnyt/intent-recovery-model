# gold_v1.2.1 Review Report

**Reviewed against**: `gold_v1.2.1.jsonl` (14 examples, drafted from
`C:\Users\thisi\Downloads\gold_v1.2.1_draft_bundle`),
`gold_v1.2.1_curriculum.md`, `gold_v1.2.1_design_notes.md`,
`gold_v1.2.1_category_taxonomy_proposals.md`
**Date**: 2026-07-29
**Author**: ChatGPT (dataset and evaluation architect), drafted using its
GitHub connector's confirmed read access to the live repo — the first
release authored this way rather than from a relayed file bundle.

## 1. Schema validity — ✅ Pass

```
14 records validated OK (training/prepare_data.py's load_jsonl)
```

Every record uses the established schema exactly:
`{"input": ..., "output": {"narrative", "bullets", "action_items"}, "difficulty", "category"}`.
`action_items`/`bullets` are lists on every record. No repeat of any prior
schema mismatch.

## 2. "No Magic Examples" — ✅ Pass

Every fragment in every example has a documented reason in
`gold_v1.2.1_design_notes.md`'s "Reason each fragment exists," including
*why* a fragment is deliberately ambiguous or incomplete (e.g. example 08's
pronoun that the input itself flags as unresolved). No fragment exists
without a stated purpose.

## 3. One lesson per example — ✅ Pass

14 examples, 6 distinct `category` values, each matching one specific
reinforcement skill. Checked against `docs/datasets/CATEGORY_REFERENCE.md`'s
existing categories: none collide.

## 4. Evidence-first compliance ("No invented content") — ✅ Pass

Spot-checked the examples most likely to tempt invention:

- **08** (ambiguous "he"): the input explicitly flags the pronoun in
  "He still needs the signed copy" as unresolvable between two people — the
  output correctly preserves that ambiguity. Separately, it resolves a
  *different*, earlier pronoun ("after he asked about it") to Marcus via
  ordinary nearest-antecedent grammar, which the design notes explicitly
  justify as a resolvable case distinct from the flagged one. This is a
  genuinely nuanced, correct distinction, not sloppy invention.
- **04**, **11** (multi-person attribution): statements, possession, and
  open questions across Maya/Theo and Leah/Omar stay correctly attributed;
  neither example invents whether an email was forwarded or which receipts
  were photographed.
- **05**, **09**, **12** (open questions): payment status, noise source, and
  room-change confirmation all stay explicitly unresolved in the narrative —
  none get a fabricated yes/no.
- **13** (repeated task): the mileage form, restated three ways, produces
  exactly one action item, not three; no invented sink-repair task despite
  "exhausting" being emotionally loaded language.
- **14** (maximum interleaving): all 6 topics from the input appear
  somewhere in the output; `action_items` contains exactly the 2 that are
  actually tasks (dentist, porch bulb) — the tentative "maybe... labels"
  idea correctly stays out of `action_items`.

No invented causality, chronology, answers, or misattributions found in
this pass.

## 5. No diagnosis framing — ✅ Pass

Scanned all four bundle files for `adhd`, `autis`, `diagnos`,
`neurodivergen` (case-insensitive): no matches.

## 6. Category balance — ✅ Pass, with one informational note

6 unique categories, distribution: `interrupted_thought_depth` (2),
`buried_task_retention` (3), `nested_boundary_depth` (2),
`multi_person_attribution` (3), `open_question_preservation` (3),
`standalone_task_retention` (1). Total 14, matching the curriculum's target.

**Informational**: the curriculum's "Coverage Distribution" table groups
targets as Interrupted/buried/nested = 5, Task retention = 3. The actual
draft has 7 examples in the first bucket (2+3+2) and only 1 example
dedicated solely to the second, with the proposal document explicitly
double-counting all 3 `buried_task_retention` examples toward *both*
buckets. The total (14) and the per-category counts are internally
consistent and well-justified individually — this is a bucket-labeling
looseness in the curriculum's grouping, not a defect in the dataset. Not
blocking; worth tightening the curriculum doc's bucket definitions before
the next reinforcement-style release, so the target table means one thing.

## 7. Design notes — ✅ Present, matches the data

One entry per example, following `DESIGN_NOTES_TEMPLATE.md`'s full structure
including Boundary Evidence, Hallucinations to watch for, and Why-here
placement. Spot-checked several entries against the actual JSONL content
(narrative/bullets/action_items) — accurate correspondence, no drift.

## 8. Curriculum Integrity — ✅ Pass

No example drifts into `gold_v1.2.1`'s declared out-of-scope territory
(sensory overwhelm, emotional journaling, burnout, multi-note reasoning,
etc.). Incidental emotional language (example 13's "exhausting") stays
exactly that — incidental, not the instructional focus, consistent with
`gold_v1.2`'s own precedent for incidental emotional content. Every example
belongs in this release, not a different one.

## Category/Taxonomy proposal review

`gold_v1.2.1_category_taxonomy_proposals.md` proposes 6 new
`CATEGORY_REFERENCE.md` rows and 2 new `TAXONOMY.md` failure categories.

- **No naming collisions** with any of the 33 existing categories in
  `CATEGORY_REFERENCE.md` — checked directly against the live file.
- **Overlap with existing categories is explicitly addressed**, not glossed
  over: the proposal directly explains how `buried_task_retention`,
  `interrupted_thought_depth`, and `nested_boundary_depth` extend rather
  than duplicate `buried_reminder`, `interrupted_thought`/
  `interrupted_thought_multi_topic`, and `nested_thought` — this is exactly
  the reconciliation this repo asked for after `gold_v1.2`'s own review
  flagged the same class of concern for a different reason.
- **`Invented Answer` and `Excessive Fragmentation`** as new `TAXONOMY.md`
  failure categories independently match what this review would have
  proposed: `Invented Answer` is directly evidenced in
  `gold_v1.2_lessons_learned.md`'s real-world findings, and
  `Excessive Fragmentation` fills the real gap that every existing failure
  category describes under-recovery, none describe over-segmentation.
- **The proposed "Release-specific wording" mapping table** (dropped
  task→Topic Loss, person misattribution→Misattribution, premature
  completion→Unsupported Addition, nested topic merge→Topic Merge) resolves
  the terminology-duplication risk flagged when `gold_v1.2.1_curriculum.md`
  was first drafted, and does it more precisely than a simple rename would
  have: descriptive language stays usable in prose, canonical labels are
  mandated only where consistency actually matters (review reports,
  aggregated results).
- Difficulty-seen values in the proposed `CATEGORY_REFERENCE.md` rows were
  checked against the actual JSONL and match exactly.

Recommend accepting both proposed additions as written.

## Informational: difficulty calibration doesn't fully match `TAXONOMY.md`'s generic table

`TAXONOMY.md`'s "Difficulty categories" table calibrates primarily on topic
*count* (Moderate = "three to five topics"). Several `medium`-tagged
examples here have only 2 topics (e.g. example 01) — the calibration is
instead based on the *depth of a specific failure mode* (an incomplete
thought's temptation to invent completion, a buried task's salience versus
surrounding narrative), which is a reasonable and arguably more precise
approach for a reinforcement release, but doesn't cleanly fit the existing
table's stated criteria. Not blocking — the actual tags are individually
defensible — but worth a follow-up note in `TAXONOMY.md` acknowledging that
topic count isn't the only valid difficulty axis, so this doesn't read as
miscalibration on a future re-review.

## Release-readiness checklist

Per `docs/datasets/REVIEW_GUIDE.md`'s "Release Checklist":

- [x] Schema validation passes
- [x] Design notes complete, including Boundary Evidence
- [x] Review report complete (this document)
- [ ] Category reference updated — recommend accepting the proposed rows
- [ ] `CHANGELOG.md` updated — next step
- [ ] Benchmark and holdout cases identified — not yet done; not blocking
- [x] Independent review passes (this review; first release reviewed from
      a live-read draft rather than a relayed bundle)
- [x] Training compatibility confirmed (`prepare_data.py` reads it cleanly)
- [ ] Evaluation shows no unacceptable regression — pending the next
      training run
- [ ] Lessons learned recorded — after training + evaluation
- [x] Coverage distribution satisfied per `gold_v1.2.1_curriculum.md` (with
      the bucket-labeling note above)

## Findings summary

**Blocking**: none.

**Borderline**: none.

**Informational**:
- Curriculum doc's "Coverage Distribution" bucket grouping is looser than
  the actual per-category counts — worth tightening before the next
  reinforcement release, not this one.
- `TAXONOMY.md`'s difficulty table doesn't fully account for depth-based
  (vs. count-based) calibration — worth a follow-up amendment, not a
  blocker for accepting this dataset.
