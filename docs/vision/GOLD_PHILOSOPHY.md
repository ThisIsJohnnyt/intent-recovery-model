# Gold Philosophy

The constitution of the Gold Curriculum Series: principles that hold across
every release, unlike a `gold_vX.Y_curriculum.md` (one release's specific
theme and examples), a dataset card (one release's scope/limitations), or a
review report (one release's quality check) — all of which are expected to
change release to release. These seven don't. A new release proposing to
violate one of these isn't a new curriculum choice, it's a regression.

Curriculum specs should **link here, not restate these** — see
`gold_v1.2_curriculum.md`'s "Design Principles" section for the pattern.

## The seven principles

**Evidence First** — every recovered fragment, boundary, and relationship in
the output must be traceable to something actually in the input. Nothing is
inferred from plausibility alone. Operationalized in
[`docs/datasets/REVIEW_GUIDE.md`](../datasets/REVIEW_GUIDE.md)'s "No invented
content" checklist.

**No Magic Examples** — every fragment in a generated note must be
explainable: why it's interrupted, why it repeats, why it has no
punctuation, why a reference dangles. An unexplainable fragment is noise,
not signal. Defined in
[`training/DATASET_SPEC.md`](../../training/DATASET_SPEC.md)'s "Two rules
for every example."

**One Lesson Per Example** — each example teaches one specific recovery
skill, named as its `category`. An example testing two unrelated things at
once should be split or simplified. Also defined in `DATASET_SPEC.md`'s
"Two rules," enforced by `REVIEW_GUIDE.md` item 3.

**Progressive Difficulty** — a release's examples build in difficulty
deliberately, each tier introducing traits named by that tier's own
definition, not just more topics. See
[`docs/datasets/TAXONOMY.md`](../datasets/TAXONOMY.md)'s "Difficulty
categories" for the four-tier vocabulary (Basic/Moderate/Complex/High
Cognitive Load, mapping to `easy`/`medium`/`hard`/`expert`).

**Boundary Evidence** — a segmentation boundary is never asserted without
citing what in the text signals it and how confident that signal is. Turns
"the model segmented this correctly" from a subjective read into something
checkable. See `TAXONOMY.md`'s "Boundary categories"/"Confidence categories"
and [`docs/datasets/DESIGN_NOTES_TEMPLATE.md`](../datasets/DESIGN_NOTES_TEMPLATE.md)'s
"Boundary Evidence" field. Design-notes-only — never a field in the trained
JSONL (see `DATASET_SPEC.md`'s "Data contract").

**Preserve Uncertainty** — an incomplete thought or an unresolved reference
stays incomplete/unresolved in the output. The model is never rewarded for
guessing a plausible resolution. See `TAXONOMY.md`'s "Dataset labeling
rules" #3 and `REVIEW_GUIDE.md`'s "Preserved uncertainty" check.

**Human-Centered Intent Recovery** — the task is recovering what a person
meant to capture, not diagnosing why they wrote it that way. Cognitive/
emotional *state* is fair game (rushed, distracted, excited); a diagnosis
label (ADHD, autism, etc.) never is. See
[`NORTH_STAR.md`](NORTH_STAR.md)'s mission statement and
`REVIEW_GUIDE.md`'s "No diagnosis framing" check.

## Why this document exists

Without a stable reference, these principles get re-stated inside every
`gold_vX.Y_curriculum.md`'s "Design Principles" section — harmless the first
time, but a duplication risk on every release after: a wording tweak in one
curriculum doc doesn't propagate to the others, and eventually two releases
describe "Evidence First" slightly differently. Centralizing them here means
a curriculum spec only needs to state what's *new* about that release, and
link back here for what isn't.
