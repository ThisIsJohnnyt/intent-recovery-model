# Dataset Batch Review Guide

A checklist for reviewing a new batch of examples (gold or synthetic)
before it's accepted into `datasets/`. Per
[PDR-001](../decisions/PDR-001.md): review process before scale.

## 1. Schema validity

Run it through the pipeline's own validator — don't eyeball this one:

```bash
cd training
./venv/Scripts/python.exe -c "
from prepare_data import load_jsonl
from pathlib import Path
records = load_jsonl(Path('../datasets/<path-to-batch>.jsonl'))
print(f'{len(records)} records validated OK')
"
```

If this throws, the batch has a schema problem (missing field, wrong type)
— fix before anything else. This Python validator is authoritative (it's
literally what gates training); [`training_data.schema.json`](training_data.schema.json)
is a machine-checkable mirror of the same contract, useful for a curator to
self-check a draft with any standard JSON Schema tool before sending it
over for this step.

## 2. "No Magic Examples"

For every example, for every fragment in `input`: can you say *why* it's
there? Why interrupted, why repeated, why no punctuation, why a dangling
reference? If you can't explain a fragment, it's noise — reject or
regenerate that example. (See `training/DATASET_SPEC.md`.)

## 3. One lesson per example

Does the example's `category` actually match what it teaches? Would someone
reading only the `input`/`output` pair understand what skill this example is
meant to test? If an example seems to be testing two unrelated things at
once, split it or simplify it.

## 4. No invented content ("evidence-first" compliance)

Check the model/reference output against each of these specifically —
don't just eyeball for a general sense of accuracy:

- **Preserved uncertainty**: uncertain references (e.g. "the blue folder")
  or genuinely open questions in `input` stay uncertain/open in the
  output — never resolved with a guessed answer.
- **No invented chronology**: the output never asserts an order of events
  that `input` doesn't state.
- **No invented causality**: the output never asserts one fragment caused
  or explains another unless `input` actually says so — adjacency in the
  text is not evidence of a relationship.
- **No merged unrelated intentions**: two fragments that are actually
  unrelated stay represented as separate items, never combined into one
  (even a superficially plausible-sounding) combined statement.
- **No lost low-salience reminders**: every fragment in `input` — however
  brief or seemingly minor — appears *somewhere* in the output (narrative,
  bullets, or action_items). A short fragment being easy to drop is not a
  reason to drop it.
- **No over-summarization**: don't compress `input` so much that a
  distinct fragment disappears into a vaguer, more general statement.
- **No unsupported tasks**: `action_items` never contains a task that
  isn't implied by `input`.
- **No misattribution**: when a note mentions more than one person, a
  fragment belonging to one of them is never reassigned to another.

These aren't hypothetical — `datasets/gold/gold_v1.2_lessons_learned.md`'s
"real-world usage findings" section documents actual instances of several
of these (an invented answer to an open question, a dropped standalone
task, an invented emotion, an invented merge between unrelated fragments,
and cross-person misattribution) from testing the trained model against
real notes. Use it as a reference for what these failures actually look
like, not just an abstract checklist. See
[`TAXONOMY.md`](TAXONOMY.md)'s "Failure categories" for short-hand names
for each of these, useful when tagging findings in a review report or
lessons-learned entry.

## 5. No diagnosis framing

Nothing in `input`, `output`, or design notes should reference a diagnosis
(ADHD, autism, etc.) or assume *why* the note is fragmented. Cognitive/
emotional *state* is fine (rushed, distracted, excited); a label for a
condition is not. (See `docs/vision/NORTH_STAR.md`.)

## 6. Diversity coverage

Check the new batch against
[CATEGORY_REFERENCE.md](CATEGORY_REFERENCE.md)'s "target categories not yet
represented" and "cognitive/emotional states represented" sections. Does
this batch fill a gap, or does it pile onto an already-covered category/
state? Update `CATEGORY_REFERENCE.md` after review with whatever this batch
newly covers.

## 7. Design notes match the data

For gold-tier batches specifically: does the `*_design_notes.md` file
actually describe what's in the `.jsonl`? (Easy to drift if the JSONL gets
edited after the notes are written.)

## 8. Curriculum Integrity

Beyond whether a single example is internally sound (item 3), does this
*batch* still fit the release it's part of?

- **Could this example belong to a different release more naturally?** A
  well-built example that teaches a `v1.4` (emotional journaling) lesson
  doesn't belong in a `v1.2` (multiple interleaved topics) batch just
  because it's good — move it, or hold it for the right release.
- **Does the example introduce capabilities reserved for future releases?**
  Check the batch's `gold_vX.Y_curriculum.md`'s "Out of Scope" section —
  e.g. `gold_v1.2_curriculum.md` explicitly excludes multi-note reasoning,
  longitudinal continuity, temporal recovery, preference learning, calendar
  scheduling, and task prioritization. An example that quietly exercises one
  of those is curriculum creep, even if it's a well-written example on its
  own terms.

## After review

- Accepted batches: update `datasets/gold/CHANGELOG.md` (or the synthetic
  equivalent) and `CATEGORY_REFERENCE.md`.
- Rejected/needs-revision: send back with which checklist item(s) failed —
  specific enough that the fix is obvious, not just "doesn't feel right."

## Release bundle

Every gold release is more than a `.jsonl` file. Going forward (starting
`gold_v1.2`), a release is:

| File | Written by | When |
|---|---|---|
| `gold_vX.Y.jsonl` | Curator | Before release |
| `gold_vX.Y_design_notes.md` (using [DESIGN_NOTES_TEMPLATE.md](DESIGN_NOTES_TEMPLATE.md)) | Curator (author intent) | Before release |
| `gold_vX.Y_review_report.md` (this checklist, filled in) | Claude Code (independent check) | Before release |
| `CHANGELOG.md` entry | Whoever accepts the release | At acceptance |
| `gold_vX.Y_lessons_learned.md` | Shared — all three roles | After training + evaluation |
| `gold_vX.Y_benchmark_results.md` | Whoever runs the benchmark | After training + evaluation |

Three of these ask genuinely different questions, not overlapping ones:

- **Design notes**: why was each example written?
- **Review report**: does this batch pass the quality bar, independently
  checked?
- **Lessons learned**: after actually training and evaluating on it, what
  did we discover — unexpected successes, unexpected failures, surprises,
  recommendations for the next release?

Reuses the existing `gold_vX.Y` version number for every file in the
bundle — one identifier per release, not a separate numbering scheme.
