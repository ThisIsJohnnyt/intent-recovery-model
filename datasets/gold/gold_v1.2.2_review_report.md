# gold_v1.2.2 Review Report

**Reviewed against**: `gold_v1.2.2.jsonl` (12 examples),
`gold_v1.2.2_curriculum.md`, `gold_v1.2.2_design_notes.md`,
`gold_v1.2.2_category_reference_proposals.md`
**Date**: 2026-07-29
**Author**: Claude Code (implementation engineer), independent check per
`docs/datasets/REVIEW_GUIDE.md`'s release-bundle table.

## 1. Schema validity — ✅ Pass

```
12 records validated OK (training/prepare_data.py's load_jsonl)
```

Every record uses the established schema exactly:
`{"input": ..., "output": {"narrative", "bullets", "action_items"}, "difficulty", "category"}`.
`bullets`/`action_items` are lists on every record.

## 2. "No Magic Examples" — ✅ Pass

Every fragment in every example has a documented reason in
`gold_v1.2.2_design_notes.md`'s "Reason each fragment exists," including
why specific references are left unresolved (e.g. 002's "her"/"earlier
version", 009's "that note"/"which one she meant").

## 3. One lesson per example — ✅ Pass

12 examples, 7 `category` values, each matching its stated lesson and
consistent with `docs/datasets/CATEGORY_REFERENCE.md`'s existing
definitions for the 5 reused categories.

## 4. Evidence-first compliance ("No invented content") — ✅ Pass

Spot-checked all 12 examples against their design notes and against each
other; no invented answers, causality, chronology, or misattribution
found. `action_items` never contains a tentative idea (003, 004, 008, 011,
012 all correctly keep "maybe/perhaps/could" content out of actions), and
every dangling reference (002, 009) stays unresolved in narrative, bullets,
and the action item's own wording.

## 5. No diagnosis framing — ✅ Pass

Scanned all four bundle files for `adhd`, `autis`, `diagnos`,
`neurodivergen` (case-insensitive): no matches.

## 6. Diversity coverage — ⚠️ Borderline (see finding below)

Category distribution matches the approved plan exactly:
`unsupported_content_resistance` (2), `dangling_reference` (1),
`idea_action_boundary` (3), `interrupted_thought_depth` (1),
`nested_boundary_depth` (1), `open_question_preservation` (1),
`cross_field_completeness` (3) — 12 total, difficulty 3 medium / 5 hard /
4 expert, matching the curriculum's target exactly.

The category/difficulty *distribution* is correct. The finding below is
about surface-form diversity within that distribution, not category
balance.

## 7. Design notes match the data — ✅ Pass, no drift

Compared every example's `narrative`/`bullets`/`action_items` in the JSONL
against `gold_v1.2.2_design_notes.md`'s "Expected field-by-field recovery"
word for word. All 12 match exactly — no drift between the notes and the
trained data.

## 8. Curriculum Integrity — ✅ Pass, with the finding below

No example exercises anything in the curriculum's "Out of Scope" list
(Sensory Overwhelm, diagnosis classification, multi-note reasoning,
inference-contract or marker-format changes). Every example belongs to
this release, not a different one.

---

## Finding: benchmark-wording and sentence-pattern reuse (Borderline, recommend revision)

The curriculum's own "Authoring Constraints" require every example to "be
structurally novel" and "avoid copying benchmark nouns, names, settings,
or sentence patterns," and its Release Acceptance Criteria include "no
benchmark wording copied into training" as an explicit checklist item.
Four examples lean on their benchmark analogue closely enough that this
criterion doesn't clearly pass:

- **Example 006** (analogue: probe 03) reuses the clause **"that is one
  question"** verbatim from probe 03 ("...before driving to the office,
  not ask Celia and separately check the cable, **that is one
  question**. The break-room clock is slow again."). This is not
  paraphrase — it's the identical phrase, unchanged, inside a new example.
- **Example 012** (analogue: probes 02/12/15) closes with **"last thing
  replace the conference-room batteries tomorrow,"** echoing probe 12's
  **"last thing replace the smoke-detector battery"** almost word for
  word — only the object noun changed.
- **Example 005** (analogue: probe 02) and **example 012** both reuse the
  exact same interruption template as probe 02 itself: *"[verb] why the
  [object] keeps—[interrupting task]—back to the [object], [cause
  clause]."* Probe 02: *"Figure out why the tablet keeps—put the donation
  box by the front door—back to the tablet, the screen goes black
  whenever the charger moves."* Example 005: *"Need to figure out why the
  scanner keeps—put the donation receipts in the blue folder—back to the
  scanner, it freezes after the second page."* Example 005 also reuses
  the noun **"donation"** from the benchmark probe's interrupting clause.
  This same skeleton is used *twice* within the new batch itself (005 and
  012), so it isn't only an echo of the benchmark — it's the least
  surface-diverse pattern in the release.
- **Example 007** (analogue: probe 08) follows probe 08's sentence
  skeleton closely — *"Was the [A] from the [B] or the [C]? It [state] by
  [time]. [Task] the recycling [object] [time-adverb]."* — and reuses the
  noun **"recycling"** for the task itself.

**Why this matters beyond style**: this release's own premise is that
resolving probes 02/03/08/12 in evaluation demonstrates real
generalization, not memorization. Training on examples this close to the
actual probes weakens that claim — a model could pass these probes partly
because it saw a near-copy during training, not because it generalized
the underlying skill. That's the specific risk "no benchmark wording
copied into training" was written to prevent.

**Recommendation**: send examples 005, 006, 007, and 012 back to the
curator for a revision pass — same lesson, same difficulty, different
sentence skeleton and no reused content words from the analogous probe.
The other 8 examples (001–004, 008–011) don't show this pattern and don't
need changes. Not a blocker on the other 7 checklist items, which all
pass cleanly, but recommend resolving this before training so the
post-release benchmark numbers are trustworthy.

### Re-review after revision — ✅ Resolved

All four examples were rewritten; re-validated against the same probes:

- **005** (probe 02): dropped the "keeps—...—back to" template and the
  "donation" noun entirely. New structure interrupts a conditional clause
  ("it starts chirping when—...—when the door stays open...") and
  reconnects it grammatically instead of via an explicit return phrase.
- **006** (probe 03): dropped "that is one question" and the
  "arrived before" construction. New structure unifies the task via a
  colon-embedded question ("Message Omar: did the venue code change?
  Need the answer before leaving.") instead of an explicit
  anti-splitting instruction.
- **007** (probe 08): dropped "recycling" and the interrogative
  either/or skeleton. New structure states the uncertainty
  declaratively ("I can't tell if...came from the toaster or the
  kettle"), uses different objects throughout, and ends on an unrelated
  library-return task.
- **012** (probes 02/12/15): dropped "back to the reader" and "last
  thing replace the...battery". The interruption now splits a noun
  phrase ("after the first—...—scan") rather than repeating a verb-object
  clause, and the final task is its own plain sentence with no
  benchmark-style closing cue.

Checked all four against all 16 benchmark probes (not just their own
declared analogue) for incidental overlap — none found. Design notes were
rewritten in lockstep; re-verified word-for-word match against the JSONL
(§7 still passes with no drift). Schema re-validated: 12/12 records OK.
Category/difficulty distribution unchanged. The interruption/return
authoring constraint (≥2 examples) is still satisfied — 005 and 012 both
still test reconnect-after-interruption, just via grammatical completion
and mid-noun-phrase splitting instead of an explicit "back to" signal,
which is if anything a better-varied test of the same capability.

**Verdict: no longer borderline. Release is clean.**

---

## Category reference proposal review

`gold_v1.2.2_category_reference_proposals.md` proposes 3 new
`CATEGORY_REFERENCE.md` rows (`unsupported_content_resistance`,
`idea_action_boundary`, `cross_field_completeness`) and reuses 5 existing
categories (`interrupted_thought_depth`, `nested_boundary_depth`,
`open_question_preservation`, `buried_task_retention`,
`dangling_reference`) — matching the approved Decision Point Resolution
in `gold_v1.2.2_curriculum.md` exactly.

- **No naming collisions** with any existing `CATEGORY_REFERENCE.md` row
  — checked directly against the live file.
- **Overlap is explicitly addressed**: the proposal distinguishes
  `unsupported_content_resistance` from `zero_action_items`,
  `idea_action_boundary` from `task_plus_idea`/`observation_plus_idea`/
  `idea_among_tasks`, and `cross_field_completeness` from
  `buried_task_retention`/`long_rambling_multi_topic` — all three
  referenced categories exist in the live file with the stated meaning.
- **Difficulty-seen values** (`medium, expert` / `medium, hard` /
  `expert`) match the actual JSONL exactly.

Recommend accepting all three proposed rows as written.

## Release-readiness checklist

Per `docs/datasets/REVIEW_GUIDE.md`'s "Release Checklist":

- [x] Schema validation passes
- [x] Design notes complete, including Boundary Evidence
- [x] Review report complete (this document)
- [x] Category reference updated — 3 new rows added to `CATEGORY_REFERENCE.md`
- [x] `CHANGELOG.md` updated
- [ ] Benchmark and holdout cases identified — not yet done; not blocking
- [x] Independent review passes (this review)
- [x] Training compatibility confirmed (`prepare_data.py` reads it cleanly)
- [ ] Evaluation shows no unacceptable regression — pending the next
      training run
- [ ] Lessons learned recorded — after training + evaluation
- [x] Coverage distribution satisfied per `gold_v1.2.2_curriculum.md`

## Findings summary

**Blocking**: none.

**Borderline**: none remaining — benchmark-wording/sentence-pattern reuse
in examples 005, 006, 007, 012 (see finding above) was resolved in the
revised bundle; re-review confirmed the fix and found no new issues.

**Informational**: none beyond the above.
