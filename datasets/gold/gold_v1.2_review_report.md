# gold_v1.2 Review Report

**Reviewed against**: `datasets/gold/gold_v1.2.jsonl` (20 examples),
`datasets/gold/gold_v1.2_curriculum.md`,
`datasets/gold/gold_v1.2_design_notes.md`
**Date**: 2026-07-28

## Revision history

An initial draft of `gold_v1.2.jsonl` (Gemini-generated) was reviewed and
found to have two blocking issues: a schema mismatch with
`training/prepare_data.py` (used `note`/`segmented_intentions` instead of
`input`/`output: {narrative, bullets, action_items}`, with no embedded
`difficulty`/`category`), and a diagnosis reference ("Realistic ADHD-style
note capture") in the curriculum document's coverage matrix. See git
history for that review if needed.

With the dataset curator (ChatGPT) unavailable (rate-limited) and the
product owner's authorization, Claude Code authored a replacement batch
directly, correcting both issues, and this report reviews that replacement.

**Important caveat on process**: the project's established process is two
independent reviewers (dataset curator + engineering), where "agreement
increases confidence, disagreement gets a closer look." That can't happen
right now — Claude Code is both author and reviewer for this release. This
report is a rigorous self-check, not a substitute for independent review.
Treat this release as provisionally accepted; a genuine second review once
ChatGPT is available would still be worth doing, particularly for the
subjective calls (difficulty calibration, scenario realism).

## 1. Schema validity — ✅ Pass

```
20 records validated OK
```

Uses the established schema exactly:
`{"input": ..., "output": {"narrative", "bullets", "action_items"}, "difficulty", "category"}`,
matching `training/DATASET_SPEC.md`. No repeat of the previous draft's
schema mismatch.

## 2. "No Magic Examples" — ✅ Pass

Every fragment in every example has a documented reason in
`gold_v1.2_design_notes.md` — what it is, and (where relevant) why it
might be mistaken for something else. No fragment exists without a stated
purpose.

## 3. One lesson per example — ✅ Pass

20 examples, 20 distinct `category` values, each matching one specific
segmentation skill (verified programmatically — no duplicates). Checked
for collisions against `docs/datasets/CATEGORY_REFERENCE.md`'s existing
v1.0/v1.1 categories: none found.

## 4. Evidence-first compliance ("No invented content") — ✅ Pass

Checked every example specifically for invented causality, chronology, or
relationships between unrelated fragments (the curriculum's named failure
modes #2/#3). None found. Deliberately built several examples to test this
directly:

- `08`, `16`: an unresolved question ("did we get the pool cleaned?") and
  a fact outside the writer's control ("insurance said they'd call back")
  are correctly *not* turned into fabricated action items or resolved
  with invented information.
- `11`, `15`: adjacent-but-unrelated facts (a paint decision / a pharmacy
  call; a printer jam / an unfinished report) are kept as separate items
  rather than one implicitly causing the other.
- `19`: "call the landlord about—" is preserved as a valid action item
  without inventing what it's about.
- Narrative connectors use neutral language ("separately," "also") between
  unrelated fragments throughout — never "because," "so," or "which meant."

## 5. No diagnosis framing — ✅ Pass

Scanned the full file and design notes for `adhd`, `autis`, `diagnos`,
`neurodivergen` (case-insensitive): no matches. The prior draft's curriculum
label issue is not repeated in this authored content (the curriculum
document itself is unchanged from the original review — that finding
still stands there and is unaffected by this replacement).

## 6. Category balance — ✅ Pass

20 unique, single-string `category` values per example (not the prior
draft's ad hoc inline compound labels). No controlled vocabulary was
imposed beyond "one clear string per example, matching one lesson" — same
convention as `gold_v1.0`/`gold_v1.1`. `docs/datasets/CATEGORY_REFERENCE.md`
update pending (see §9).

## 7. Difficulty progression — ✅ Pass, matches curriculum definition this time

```
Difficulty distribution: {'easy': 4, 'medium': 6, 'hard': 6, 'expert': 4}
```

Matches the curriculum's target distribution exactly (4/6/6/4 — the prior
draft was 3/7/8/2). Tier assignment follows the curriculum's own stated
level definitions directly, correcting the prior draft's specific
inconsistencies:

- Level 3 (Hard) examples (`11`–`16`) all demonstrate the curriculum's own
  named Level 3 traits — interrupted thoughts (`12`), buried reminders
  (`11`), stream-of-consciousness (`13`), nested asides (`14`) — not just
  higher topic count. (The prior draft tagged `06`/`08` — "buried reminder"
  and "interrupted thought" — as Medium despite the curriculum defining
  both as Level 3 traits.)
- Level 4 (Expert) examples (`17`–`20`) all demonstrate the curriculum's
  named Level 4 traits — emotional asides (`17`), repeated reminders
  (`18`), rapid topic changes with incomplete sentences (`19`), and a
  combination of all of them (`20`). (The prior draft tagged `14`/`18` —
  "emotional aside" and "repeated reminders" — as Hard despite the
  curriculum defining both as Level 4 traits.)
- No Hard/Expert example relies on topic count alone without accompanying
  structural complexity (the prior draft's `12`/`16` issue).

## 8. Design notes — ✅ Present

`gold_v1.2_design_notes.md` written, one entry per example, following
`docs/datasets/DESIGN_NOTES_TEMPLATE.md`'s structure (condensed for volume):
lesson, fragment-by-fragment rationale, failure modes, expected recovery.

## 9. Release-readiness checklist

- [x] Schema validation passes
- [x] Design notes complete
- [x] Review report complete (this document)
- [ ] CHANGELOG updated — next step
- [ ] Category reference updated — next step
- [ ] Benchmark cases identified — not yet done; not blocking, a v1.5+/benchmark-suite concern
- [~] Independent review — **self-review only**, per the caveat above; not a substitute for the project's two-reviewer process

## Findings summary

**Blocking:** none in this authored replacement.

**Borderline:** none found on re-review; the two prior blocking issues
(schema, diagnosis framing) were specifically targeted and corrected.

**Informational:**
- This release lacks true independent review (ChatGPT unavailable) —
  provisionally accepted, flagged for a second look when available,
  especially on subjective calls like difficulty calibration and scenario
  realism.
- `gold_v1.2_curriculum.md`'s own diagnosis-framing issue (§5 of the
  original review) is untouched by this replacement — it's a separate
  document, not modified here, and still needs a wording fix if that
  document is to remain the authoritative curriculum reference.
- No negative/benchmark examples identified yet for this release (per
  `docs/benchmarks/benchmark_suite.md`) — future work, not blocking.
