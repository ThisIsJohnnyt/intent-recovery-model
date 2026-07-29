# Gold v1.2 Curriculum Specification

**Release:** Gold v1.2

**Status:** Approved

**Theme:** Multiple Interleaved Topics

## Objective

Teach the model to identify and separate multiple independent intentions contained within a single note.

This release focuses on **segmentation rather than summarization**. The model should recognize that a note may contain several unrelated topics and preserve those boundaries without inventing relationships.

## Why This Release Exists

Previous releases primarily taught accurate interpretation of individual notes.

Gold v1.2 introduces a new cognitive capability:

> Recover multiple independent intentions from one note.

This mirrors how anyone captures scattered thoughts under real-world
conditions (time pressure, interruption, distraction, excitement) — unrelated
thoughts are often recorded together regardless of who's writing them.

### Core Learning Principle

> Separate before summarizing.

A note containing multiple intentions should first be segmented into
independent components. Only after accurate segmentation should
interpretation or summarization occur. Gold v1.2 intentionally teaches this
separation step, not a more polished rewrite.

## Capability Being Taught

- Detect multiple independent topics.
- Separate tasks, observations, ideas, reminders, and reflections.
- Preserve uncertainty where evidence is insufficient.
- Avoid merging unrelated thoughts.
- Avoid inventing chronology or causality.
- Preserve every meaningful topic, including brief reminders.

## Out of Scope

- Multi-note reasoning
- Longitudinal continuity
- Temporal recovery
- Preference learning
- Calendar scheduling
- Task prioritization

## Design Principles

The stable, cross-release principles (Evidence First, No Magic Examples,
One Lesson Per Example, Progressive Difficulty, Boundary Evidence, Preserve
Uncertainty, Human-Centered Intent Recovery) are defined once in
[`docs/vision/GOLD_PHILOSOPHY.md`](../../docs/vision/GOLD_PHILOSOPHY.md) —
see that document rather than this section for their definitions, so a
wording change doesn't have to be repeated in every `gold_vX.Y_curriculum.md`.

What's specific to this release:

- Realistic scattered-note writing patterns (not a single stereotype — see
  `training/DATASET_SPEC.md`'s "Diversity requirements")
- Every fragment exists for a documented reason (this release's application
  of "No Magic Examples," per-example in `gold_v1.2_design_notes.md`)

## Curriculum Progression

### Level 1 — Basic Segmentation
Two unrelated topics.

### Level 2 — Moderate Segmentation
Three to five unrelated topics.

### Level 3 — Complex Notes
Interrupted thoughts, buried reminders, stream-of-consciousness.

### Level 4 — High Cognitive Load
Rapid topic changes, incomplete sentences, emotional asides, repeated reminders.

## Target Dataset Size

20–25 examples.

Distribution:

- 4 Basic
- 6 Moderate
- 6 Complex
- 4 High Cognitive Load

## Example Coverage Matrix

**Note:** this matrix is the pre-authoring plan, not a description of the
final release. The examples actually authored diverged from it in two ways
worth knowing before reading this table: (1) several row labels below
("Multiple errands," "Multiple projects," "Ideas mixed with obligations")
don't correspond 1:1 to the `category` values actually built — see
[`docs/datasets/CATEGORY_REFERENCE.md`](../../docs/datasets/CATEGORY_REFERENCE.md)
for the real category list; (2) some difficulty tags below (rows `06`,
`08`, `14`, `18`) predate the Curriculum Progression section above and
don't match it — e.g. row `06` "Buried reminder" is tagged Medium here even
though Level 3 above names "buried reminders" as a Level 3 trait.
`gold_v1.2_review_report.md` §7 documents finding and correcting this exact
mismatch in the actually-built `gold_v1.2.jsonl` (where `buried_reminder`
is tagged `hard`), but that fix was never applied retroactively to this
planning table. Treat
[`gold_v1.2_design_notes.md`](gold_v1.2_design_notes.md) and
`CATEGORY_REFERENCE.md` as authoritative for what was actually built and at
what difficulty; this table is kept as-is below for historical reference.

| Example | Primary Lesson | Difficulty |
|---------|----------------|------------|
|01|Two unrelated tasks|Easy|
|02|Task + observation|Easy|
|03|Task + idea|Easy|
|04|Three independent topics|Medium|
|05|Observation among tasks|Medium|
|06|Buried reminder|Medium|
|07|Topic switching|Medium|
|08|Interrupted thought|Medium|
|09|Four independent intentions|Medium|
|10|Reminder inside narrative|Medium|
|11|Stream of consciousness|Hard|
|12|Multiple errands|Hard|
|13|Nested thoughts|Hard|
|14|Emotional aside|Hard|
|15|Long chaotic note|Hard|
|16|Multiple projects|Hard|
|17|Ideas mixed with obligations|Hard|
|18|Repeated reminders|Hard|
|19|Maximum interleaving|Expert|
|20|Realistic high-cognitive-load capture|Expert|

## Success Criteria

Improve:

- Topic segmentation
- Boundary detection
- Intent preservation
- Uncertainty preservation
- Reduced hallucinated relationships
- Recovery of buried reminders

## Expected Failure Modes

1. Topic merging
2. Invented causality
3. Invented chronology
4. Lost topics
5. Over-summarization

## Boundary Evidence

Every segmentation boundary an example contains should be documented with
what evidence in the text supports it and how confident that signal is —
not just that a boundary exists, but why. This lets a reviewer check
segmentation *reasoning*, not just the final answer. See
[`docs/datasets/DESIGN_NOTES_TEMPLATE.md`](../../docs/datasets/DESIGN_NOTES_TEMPLATE.md)'s
"Boundary Evidence" field for the exact format and a worked example.

**Important**: boundary evidence, like everything else in this section,
belongs in design notes only. It is never a field in the trained JSONL —
see [`training/DATASET_SPEC.md`](../../training/DATASET_SPEC.md)'s "Data
contract" for the one schema that's actually authoritative for training.

## Design Notes Requirement

Each example includes (using
[`docs/datasets/DESIGN_NOTES_TEMPLATE.md`](../../docs/datasets/DESIGN_NOTES_TEMPLATE.md)):

- Example ID
- Lesson
- Author Intent
- Scenario
- Reason each fragment exists
- Boundary Evidence
- Failure Modes
- Hallucinations to watch for
- Why this example is at this point in the curriculum
- Expected Recovery

## Review Expectations

Independent review verifies:

- Evidence First
- No Magic Examples
- Curriculum coverage
- Difficulty progression
- Category balance
- Schema validity

## Release Acceptance Criteria

- Schema validation passes
- Design notes complete
- Review report complete
- CHANGELOG updated
- Category reference updated
- Benchmark cases identified
- Independent review passes

## Future Curriculum

- Gold v1.2.1 — Segmentation Reinforcement (additive corrective release,
  addressing gaps this training run surfaced — see
  [`gold_v1.2.1_curriculum.md`](gold_v1.2.1_curriculum.md))
- Gold v1.3 — Sensory Overwhelm
- Gold v1.4 — Emotional Journaling
- Gold v1.5 — Burnout
- Future: Multi-note reasoning, Longitudinal continuity, Temporal recovery
