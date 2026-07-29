# Design Notes Template

Design notes answer one question: **why was each example written?** They
are written by whoever authors a batch (the dataset curator), never used
for model training, and are distinct from the
[review report](REVIEW_GUIDE.md) (an independent quality check) and
[lessons learned](REVIEW_GUIDE.md#release-bundle) (post-training
discoveries) — see `REVIEW_GUIDE.md`'s release bundle section for how the
three fit together.

## Per-example format

```
Example_ID: <batch-version>-<number>, e.g. G1.2-001

Lesson:
<the one recovery skill this example teaches — should match its `category`>

Author Intent:
<what this example is meant to prove the model can (or, for a negative
example, currently cannot) do>

Scenario:
<the real-world situation this note is set in — grounds the example so
it doesn't feel arbitrary>

Reason each fragment exists:
- <fragment 1>: <why it's there>
- <fragment 2>: <why it's there>
- ...

Failure Modes:
<specific, plausible ways a model could get this wrong — used to sanity
check the review and, later, to explain what actually went wrong if it does>

Expected Recovery:
<what a correct output looks like, in plain terms — not the literal JSON,
the intent>
```

## Example (illustrative, not a real dataset entry)

```
Example_ID: G1.2-014

Lesson:
Multiple interleaved topics

Author Intent:
Teach the model to segment many unrelated topics in one note, not just
summarize them as if they were connected.

Scenario:
Quick voice memo while walking between errands.

Reason each fragment exists:
- "call insurance": first unrelated topic
- "also remember mom wanted...": second, cut off deliberately (See "half
  finished thoughts" — not the focus here, kept brief on purpose)
- "why are printers awful": a non-actionable aside, tests zero_action_items
  handling within a multi-topic note
- "need milk": third topic, simple task
- "friday dentist": fourth topic, simple task

Failure Modes:
- Merges unrelated topics into one narrative thread
- Invents a connection between "mom wanted..." and another fragment
- Drops the printer aside instead of preserving it as a non-task observation

Expected Recovery:
Five distinct topics recognized as such (insurance, mom's unfinished
request, printer complaint, milk, dentist), with action items limited to
the ones that are actually tasks.
```

## Why this exists

Compare to `gold_v1.0_design_notes.md`, which used a simpler three-line
format (Purpose / Expected behavior / Design principle). This richer
template — introduced starting with `gold_v1.2` — adds the pieces that
make a design note actually diagnostic when something goes wrong later:
naming failure modes up front means a review or lessons-learned pass can
check specifically for them, not just eyeball the output.
