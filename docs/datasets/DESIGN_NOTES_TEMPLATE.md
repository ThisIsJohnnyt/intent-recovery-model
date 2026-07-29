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

Boundary Evidence:
<for each topic boundary this example contains, what in the text actually
signals it, and how confident that signal is — makes segmentation
decisions objectively reviewable rather than a judgment call. See
docs/datasets/TAXONOMY.md's "Boundary categories" for standard evidence
types (Topic Shift, Intent Shift, Context Shift, Thought Interruption,
Embedded Reminder) and "Confidence categories" for what High/Medium/Low
mean precisely.>
- Boundary: <topic N -> topic N+1>
  Evidence: <e.g. "new imperative verb introduces an unrelated obligation",
  "speaker abandons an unfinished thought and introduces a new reminder">
  Confidence: High | Medium | Low

Failure Modes:
<specific, plausible ways a model could get this wrong — used to sanity
check the review and, later, to explain what actually went wrong if it does>

Hallucinations to watch for:
<beyond generic failure modes — the specific plausible-sounding but false
things a reviewer should check the model didn't invent for *this*
example: an answer to an open question, an emotion never stated, a
relationship between two fragments that are actually unrelated, etc.>

Why this example is at this point in the curriculum:
<what makes it harder or different from the examples before it — ties the
example back to the curriculum's progression, not just to its own lesson>

Expected Recovery:
<what a correct output looks like, in plain terms — not the literal JSON,
the intent>
```

**Important**: `Boundary Evidence`, `Failure Modes`, `Hallucinations to
watch for`, and everything else here live in this document only — never in
the trained JSONL. See `training/DATASET_SPEC.md`'s "Data contract" section
for the one schema that's actually authoritative for training.

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

Boundary Evidence:
- Boundary: insurance -> "mom wanted..."
  Evidence: new imperative-adjacent reminder with no shared subject/verb
  Confidence: High
- Boundary: "mom wanted..." -> printer aside
  Evidence: speaker abandons the unfinished thought mid-clause and pivots
  to an unrelated complaint
  Confidence: Medium (the pivot is abrupt; a model could plausibly read it
  as the same train of thought)
- Boundary: printer aside -> "need milk" -> "friday dentist"
  Evidence: each is a bare imperative/task fragment with no connective
  tissue to its neighbor
  Confidence: High

Failure Modes:
- Merges unrelated topics into one narrative thread
- Invents a connection between "mom wanted..." and another fragment
- Drops the printer aside instead of preserving it as a non-task observation

Hallucinations to watch for:
- Inventing what mom wanted (the fragment is deliberately incomplete —
  correct output preserves that incompleteness, doesn't guess)
- Turning "why are printers awful" into an action item (e.g. "fix printer")

Why this example is at this point in the curriculum:
Five topics with one deliberately-unresolved fragment and one deliberately
non-actionable aside — harder than the plain topic-counting examples
earlier in the curriculum because it combines two failure-prone patterns
(unresolved content, non-task asides) with topic segmentation at once.

Expected Recovery:
Five distinct topics recognized as such (insurance, mom's unfinished
request, printer complaint, milk, dentist), with action items limited to
the ones that are actually tasks.
```

## Why this exists

Compare to `gold_v1.0_design_notes.md`, which used a simpler three-line
format (Purpose / Expected behavior / Design principle). This richer
template — introduced starting with `gold_v1.2`, and extended further
after `gold_v1.2`'s actual training run surfaced concrete failure patterns
(see `datasets/gold/gold_v1.2_lessons_learned.md`) — adds the pieces that
make a design note actually diagnostic when something goes wrong later:
naming failure modes and specific hallucination risks up front means a
review or lessons-learned pass can check specifically for them, not just
eyeball the output. `Boundary Evidence` in particular turns "the model
segmented this correctly" from a subjective read into something a reviewer
can check against a stated, citable reason.
