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
— fix before anything else.

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

## 4. No invented content

- `action_items` never contains a task that isn't implied by `input`.
- `narrative`/`bullets` never introduce facts not present in `input`.
- Uncertain references (e.g. "the blue folder") stay uncertain in the
  output — the model should not guess what they mean.

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

## After review

- Accepted batches: update `datasets/gold/CHANGELOG.md` (or the synthetic
  equivalent) and `CATEGORY_REFERENCE.md`.
- Rejected/needs-revision: send back with which checklist item(s) failed —
  specific enough that the fix is obvious, not just "doesn't feel right."
