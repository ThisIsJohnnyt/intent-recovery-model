# Gold Curriculum Taxonomy

**Purpose:** controlled vocabulary for describing examples, boundaries, and
failures consistently across dataset creation, design notes, review
reports, and evaluation.

**This is not the same thing as
[`CATEGORY_REFERENCE.md`](CATEGORY_REFERENCE.md).** `CATEGORY_REFERENCE.md`
is a living inventory of the actual `category` field values used in real
data (`simple_list`, `buried_reminder`, `two_unrelated_tasks`, etc.) — what
has actually been built. This document is a conceptual vocabulary — types
of fragments, boundaries, and failures — used *while authoring and
reviewing* examples. Neither replaces the other.

**None of the categories below are trained-schema fields.** They're
concepts for design notes, review reports, and lessons-learned entries.
The one schema that's actually authoritative for training is in
[`training/DATASET_SPEC.md`](../../training/DATASET_SPEC.md)'s "Data
contract" section (`input`/`output: {narrative, bullets, action_items}`/
`difficulty`/`category`) — a note fragment is never tagged "Task:" or
"Observation:" in the trained JSONL itself.

---

## Intent categories

What kind of thing a fragment is. Useful vocabulary for a design note's
"reason each fragment exists" field. A fragment may have more than one
characteristic; identify the primary one.

**Task** — a specific action the writer intends to perform (e.g. "call the
mechanic"). Indicators: action verbs, implied obligation. Not: general
ideas, observations, preferences.

**Reminder** — a prompt meant to help the writer remember something later
(e.g. "don't forget the password change"). Indicators: future-recall
language, "remember"/"don't forget," embedded obligations. Prefer this
over "Task" when the primary purpose is memory retrieval rather than the
action itself.

**Observation** — something noticed, experienced, or recorded, with no
action implied (e.g. "the printer sounded strange"). Indicators:
descriptive language, no explicit action required.

**Idea** — a possible concept or thought not yet an assigned action (e.g.
"maybe create a backup system"). Indicators: possibility language,
brainstorming.

**Reflection** — a thought about feelings, experiences, or personal
interpretation (e.g. "today felt overwhelming"). Indicators: evaluation,
personal meaning.

**Incomplete Thought** — a fragment the writer begins but doesn't finish
(e.g. "need to check if..."). Purpose: tests whether the model preserves
uncertainty rather than inventing a completion.

## Difficulty categories

Curriculum-level names for the four difficulty tiers. **These map to the
actual `difficulty` field values used in the trained data** — use the
right-hand value when tagging an actual example, not the level name:

| Curriculum level name | Actual `difficulty` value | Characteristics |
|---|---|---|
| Basic | `easy` | Two independent topics, clear boundaries, minimal ambiguity |
| Moderate | `medium` | Three to five topics, mixed intent categories, buried reminders |
| Complex | `hard` | Interrupted thoughts, topic switching, incomplete context |
| High Cognitive Load | `expert` | Rapid switching, repeated thoughts, emotional interruptions, multiple active threads |

Topic *count* is the calibration axis for `gold_v1.2`-style releases, but
it isn't the only valid one. A reinforcement release like `gold_v1.2.1` can
have a `medium` example with only two topics if the difficulty comes from
depth — e.g. one topic being a deliberately incomplete thought that
tempts invented completion — rather than from topic count. Calibrate on
whichever axis (count or depth) the release is actually teaching, and say
which one in the design notes if it isn't count.

## Boundary categories

Standard vocabulary for the "Evidence" field in a design note's Boundary
Evidence section (see
[`DESIGN_NOTES_TEMPLATE.md`](DESIGN_NOTES_TEMPLATE.md)).

**Topic Shift** — the writer moves to an unrelated subject. E.g. "Need to
email John. The garden tomatoes are finally growing."

**Intent Shift** — the *type* of intention changes even if the subject is
related. E.g. "Buy printer ink. The printer has been making a clicking
sound." (task → observation)

**Context Shift** — the implied situation changes. E.g. "Finish the report
tonight. My neighbor's dog keeps barking." (work responsibility →
environmental observation)

**Thought Interruption** — an unfinished thought is abandoned and replaced.
E.g. "Need to figure out why the account... also remember the dentist
appointment."

**Embedded Reminder** — a reminder appears inside another thought stream.
E.g. "Meeting went okay, remember to send the notes tomorrow."

## Failure categories

Short names for the evaluation questions in
[`REVIEW_GUIDE.md`](REVIEW_GUIDE.md)'s "No invented content" checklist —
use these as shorthand tags in review reports and lessons-learned entries
instead of re-describing the failure in prose each time.

| Category | REVIEW_GUIDE.md check |
|---|---|
| **Topic Merge** | No merged unrelated intentions |
| **Topic Loss** | No lost low-salience reminders |
| **Unsupported Addition** | No unsupported tasks / invented content |
| **Invented Causality** | No invented causality |
| **Invented Chronology** | No invented chronology |
| **Over-Summarization** | No over-summarization |
| **Misattribution** | *(new — see below)* |
| **Invented Answer** | An unresolved question is converted into an unsupported answer, conclusion, or factual statement |
| **Excessive Fragmentation** | One coherent intention is split into multiple independent topics without sufficient boundary evidence |

**Misattribution** was added after `gold_v1.2_lessons_learned.md`'s
real-world usage findings: the model reassigned a question the writer
asked about themselves to a different person mentioned earlier in the
note. None of the other six categories describe this failure — it's not a
merge, loss, invention, or over-summarization, it's assigning a correctly-
recovered fragment to the wrong person. Worth its own category rather than
stretching an existing one to cover it.

**Invented Answer** was added for `gold_v1.2.1` after the same real-world
evaluation showed the model could turn an open question into a confident
factual answer. This is a specific form of unsupported invention, but it
deserves a separate canonical label because it removes uncertainty and may
falsely signal that no follow-up is needed:

> Did Morgan already submit the form?

Incorrect recovery: *"Morgan submitted the form."*
Correct recovery: *"It is unresolved whether Morgan submitted the form."*

Use **Invented Answer** specifically when a question is answered
affirmatively, negatively, or indirectly without evidence. Continue using
**Unsupported Addition** for other invented content — completing an
unfinished thought, adding a deadline, inventing a task mechanism.

**Excessive Fragmentation** was added for `gold_v1.2.1` as the
over-segmentation counterpart to **Topic Merge**. It occurs when content
forming one governed, qualified, or otherwise coherent intention is split
into separate topics:

> Ask Priya whether the revised chart is ready.

Incorrect recovery: two separate items ("Ask Priya" / "Determine whether
the revised chart is ready"). Correct recovery: one item ("Ask Priya
whether the revised chart is ready"). Boundary Evidence must be evaluated
in both directions — **Topic Merge** (separate intentions joined without
support) and **Excessive Fragmentation** (one coherent intention divided
without support) are opposite failure modes, not the same check run twice.

### Release-specific wording

Curriculum and design notes may use concrete, descriptive language in
prose (a design note can say "dropped task" or "wrong speaker"). Review
reports and aggregated results should use the canonical labels above
instead, so results stay comparable across releases:

| Descriptive wording | Canonical failure category |
|---|---|
| Dropped task / lost reminder / missing final fragment | Topic Loss |
| Person misattribution / wrong speaker / wrong owner | Misattribution |
| Premature completion / completed unfinished thought | Unsupported Addition |
| Nested topic merge / buried intention absorbed into narrative | Topic Merge |
| Answered open question / uncertainty converted to fact | Invented Answer |
| Over-segmentation / split coherent task | Excessive Fragmentation |

## Confidence categories

Used in a design note's Boundary Evidence field, alongside the evidence
text itself:

- **High** — clear evidence supports the boundary.
- **Medium** — evidence suggests the boundary, but some ambiguity exists.
- **Low** — limited evidence; multiple interpretations are plausible.

## Dataset labeling rules

1. **Use the most specific applicable intent category** — prefer
   "Reminder" over "Task" when the primary purpose is memory retrieval.
2. **Don't infer hidden intent** — a fragment only gets categories
   supported by evidence in the text.
3. **Preserve ambiguity** — an Incomplete Thought should remain incomplete
   in the output, not resolved.
4. **Multiple intentions are expected** — a single note may contain many
   independent categories; that's the point of the `gold_v1.2` curriculum,
   not an exception to it.

## Future compatibility

New categories (e.g. for sensory states, emotional processing, burnout
indicators, or eventually temporal relationships once
[`training/ROADMAP.md`](../../training/ROADMAP.md)'s v2/v3 input-schema
work happens) should extend this reference, not replace existing
definitions.
