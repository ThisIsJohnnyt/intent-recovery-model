# Gold v1.2.1 Curriculum Specification

**Release:** Gold v1.2.1
**Status:** Approved for authoring
**Theme:** Segmentation Reinforcement
**Release type:** Additive corrective release

---

## Objective

Strengthen segmentation capabilities that remained unreliable after Gold v1.2 training and evaluation.

Gold v1.2.1 focuses on four observed gaps:

1. Deeper interrupted, buried, and nested note structures
2. Correct attribution when multiple people are mentioned
3. Preservation of unanswered questions
4. Retention of brief, buried, or easily dropped tasks

This release reinforces existing intent-recovery capabilities. It does not introduce the next major curriculum theme.

---

## Why This Release Exists

Gold v1.2 taught the model to recover multiple independent intentions from a single interleaved note.

Post-training evaluation showed that the model learned basic and moderate segmentation more reliably than complex segmentation. Generalization weakened when notes contained:

* interrupted thoughts
* nested intentions
* buried reminders or tasks
* multiple named people
* open questions without answers
* brief fragments that could disappear during recovery

These are not unrelated new capabilities. They are underdeveloped parts of the segmentation capability introduced in Gold v1.2.

Gold v1.2.1 therefore acts as a targeted reinforcement release before Gold v1.3 introduces Sensory Overwhelm.

---

## Relationship to Gold v1.2

Gold v1.2.1 is additive.

It does not:

* replace Gold v1.2
* redefine the purpose of Gold v1.2
* introduce a new major cognitive theme
* invalidate previously approved examples

It adds focused examples that strengthen areas where Gold v1.2 provided insufficient depth or where evaluation revealed real failure patterns.

Gold v1.2 and Gold v1.2.1 should be treated as one segmentation curriculum sequence.

---

## Core Learning Principle

> Preserve every supported intention and assign it only to the person, question, or context supported by the note.

The model must not repair uncertainty by inventing information.

It must not improve readability by silently removing inconvenient fragments.

---

## Capabilities Being Reinforced

### 1. Interrupted Thought Recovery

Recognize that an unfinished thought may remain meaningful even when another topic interrupts it.

The model should:

* preserve the unfinished thought
* avoid completing it
* recover the interrupting intention separately
* avoid assuming the interrupted thought was abandoned permanently

Example pattern:

> Need to check whether the account—also remind Sam about the key.

Expected behavior:

* Preserve the incomplete account-related thought
* Recover the reminder involving Sam separately
* Do not invent what should be checked about the account

---

### 2. Buried Intention Recovery

Recover a meaningful task or reminder even when it appears briefly inside a longer narrative.

The model should:

* detect low-salience obligations
* preserve brief reminders
* avoid allowing surrounding narrative to absorb the task
* avoid dropping fragments because they are short

Example pattern:

> The meeting went better than expected and I think the new format helped, send Mia the revised chart, although the ending still felt rushed.

Expected behavior:

* Preserve the meeting reflection
* Recover the task to send Mia the revised chart
* Preserve the observation about the ending
* Do not merge the task into the reflection

---

### 3. Nested Boundary Recovery

Separate intentions that appear inside other thoughts without treating every clause as a separate topic.

The model should:

* identify meaningful internal boundaries
* preserve related context where appropriate
* separate genuinely independent intentions
* avoid both over-segmentation and under-segmentation

The goal is not maximum fragmentation.

The goal is evidence-supported recovery.

---

### 4. Multi-Person Attribution

Assign actions, observations, statements, and questions to the correct person when multiple people appear in the same note.

The model should:

* preserve names or relationship labels explicitly provided
* distinguish who performed an action
* distinguish who should receive a message or item
* avoid transferring one person's action to another
* preserve uncertainty when pronouns are ambiguous

Example pattern:

> Jordan said the file was missing, Casey has the printed copy, ask Jordan whether Casey already sent it.

Expected behavior:

* Attribute the missing-file statement to Jordan
* Attribute possession of the printed copy to Casey
* Preserve the instruction to ask Jordan
* Do not claim that Jordan or Casey sent the file

---

### 5. Open Question Preservation

Recognize a question as an unresolved intention rather than treating it as a request for the model to answer.

The model should:

* preserve the question
* identify it as unresolved
* avoid inventing an answer
* avoid converting uncertainty into a fact
* separate the question from nearby tasks or observations

Example pattern:

> Did the payment actually go through? Need to download the receipt.

Expected behavior:

* Preserve the unresolved payment question
* Recover the receipt-download task separately
* Do not claim that payment succeeded or failed

---

### 6. Task Retention

Preserve every explicitly supported task, including tasks that are:

* very short
* embedded in narrative
* repeated
* interrupted
* placed at the end of a note
* surrounded by more emotionally or descriptively salient content

A task must not silently disappear from all output fields.

---

## Primary Failure Patterns Addressed

### Dropped Task

A supported task is absent from the entire recovered output.

This differs from topic merging.

In a topic merge, the task may still be represented inaccurately inside another topic. In a dropped-task failure, the task disappears completely.

---

### Person Misattribution

An action, statement, object, or responsibility is assigned to the wrong person.

---

### Invented Answer

The model converts an unresolved question into an unsupported answer or conclusion.

---

### Premature Completion

The model completes an unfinished thought using plausible but unstated information.

---

### Nested Topic Merge

A buried or nested intention is absorbed into the surrounding narrative and loses its independence.

---

### Excessive Fragmentation

The model separates closely related clauses that should remain together.

This release reinforces boundary precision, not segmentation quantity.

---

## Proposed Recovery Categories

The following category additions should be reviewed against the repository's controlled vocabulary before dataset authoring:

* `multi_person_attribution`
* `open_question_preservation`
* `standalone_task_retention`
* `buried_task_retention`
* `interrupted_thought_depth`
* `nested_boundary_depth`

These categories describe desired recovery capabilities.

Failure labels such as `dropped_task`, `person_misattribution`, and `invented_answer` belong in the evaluation and review layers rather than serving as training categories.

---

## Dataset Size

**Target:** 14 examples

This is intentionally smaller than a major thematic release.

The release should be large enough to provide meaningful reinforcement while remaining narrow enough to evaluate as a controlled correction.

---

## Coverage Distribution

| Focus                                      | Example count |
| ------------------------------------------ | ------------: |
| Interrupted, buried, and nested structures |             5 |
| Multi-person attribution                   |             3 |
| Open-question preservation                 |             3 |
| Task retention                             |             3 |
| **Total**                                  |        **14** |

Some advanced examples may contain secondary challenges from another focus area, but every example must retain one primary lesson.

---

## Curriculum Progression

### Stage 1 — Isolated Reinforcement

**Examples 01–05**

Each example isolates one known weakness with limited surrounding complexity.

Goals:

* establish clear expected behavior
* distinguish new categories from existing categories
* prevent ambiguity from obscuring the lesson

Suggested coverage:

* interrupted thought
* buried task
* nested reminder
* two-person attribution
* open question plus unrelated task

---

### Stage 2 — Realistic Context

**Examples 06–10**

The target skill appears inside a realistic note containing multiple intentions.

Goals:

* recover low-salience fragments
* maintain attribution through topic changes
* preserve open questions inside narrative
* distinguish incomplete thoughts from unanswered questions

---

### Stage 3 — Controlled Combination

**Examples 11–14**

Each example combines one primary challenge with one previously taught secondary challenge.

Possible combinations:

* multi-person attribution with a buried task
* open question with an interrupted thought
* nested intention with repeated reminder
* brief final task after a long narrative

These examples test generalization without turning the release into unrestricted maximum complexity.

---

## Proposed Example Coverage Matrix

| Example | Primary lesson                     | Secondary pressure      |
| ------- | ----------------------------------- | ------------------------ |
| 01      | Interrupted thought preservation   | Unrelated reminder      |
| 02      | Buried task retention              | Reflective narrative    |
| 03      | Nested reminder recovery           | Related observation     |
| 04      | Multi-person statement attribution | Shared object           |
| 05      | Open question preservation         | Independent task        |
| 06      | Interrupted thought depth          | Topic switching         |
| 07      | Buried task retention              | Long narrative          |
| 08      | Multi-person action attribution    | Pronoun ambiguity       |
| 09      | Open question preservation         | Nearby observation      |
| 10      | Nested boundary precision          | Avoid over-segmentation |
| 11      | Multi-person attribution           | Buried task             |
| 12      | Open question preservation         | Interrupted thought     |
| 13      | Repeated task retention            | Emotional aside         |
| 14      | Final-fragment task retention      | Long interleaved note   |

The final dataset may adjust scenarios or ordering while preserving this coverage.

---

## Design Requirements

Every example must document:

* Example ID
* Primary lesson
* Secondary pressure, when present
* Difficulty
* Author intent
* Scenario
* Input note
* Expected recovery
* Fragment-by-fragment rationale
* Boundary Evidence
* Expected failure modes
* Expected recovery behavior
* Reason the example belongs in Gold v1.2.1

---

## Boundary Evidence Requirements

Boundary Evidence remains part of the human-facing design and review layer.

For every meaningful segmentation decision, design notes should document:

* where the boundary occurs
* which intentions the boundary separates
* what textual evidence supports separation
* whether the boundary is clear or ambiguous
* what an over-segmented recovery would look like
* what an under-segmented recovery would look like

Boundary Evidence must not be inserted into the training output unless the established training contract is intentionally changed through a separate architecture decision.

---

## Open Question Rules

An open question is distinct from an incomplete or dangling reference.

### Open question

A grammatically or semantically recognizable question whose answer is unknown.

Example:

> Did Lee already submit the form?

Expected recovery:

> Unresolved question about whether Lee submitted the form.

### Incomplete thought

A thought whose intended meaning is unfinished.

Example:

> Need to figure out whether Lee...

Expected recovery:

> Incomplete thought involving Lee; the intended question or action is unspecified.

The model must preserve this distinction.

---

## Multi-Person Attribution Rules

When multiple people appear:

1. Preserve explicit attribution.
2. Do not transfer actions between people.
3. Do not resolve ambiguous pronouns without evidence.
4. Preserve relationship terms when names are absent.
5. Do not infer that two people share knowledge, responsibility, or intent.
6. Separate an action involving one person from an observation involving another when they are independent.

Names should be varied across the release to prevent memorization of recurring roles.

Scenarios should also vary:

* work
* family
* friends
* service interactions
* shared projects
* appointments

---

## Task Retention Rules

A supported task must appear in the recovered output even when:

* it contains only a few words
* it appears once
* it appears at the end
* it interrupts a more detailed thought
* another fragment appears more urgent or emotional
* the task has no stated deadline
* the task is repeated with slightly different wording

Repeated tasks should not automatically become multiple separate tasks unless the note supports distinct obligations.

---

## Evidence First

Every recovered item must be traceable to the note.

The model must not:

* invent missing answers
* invent task mechanisms
* assign actions to unstated people
* complete unfinished thoughts
* create deadlines
* infer chronology
* infer causality
* remove uncertainty for readability

---

## No Magic Examples

Examples must resemble authentic note capture.

Avoid:

* headings inside input notes
* numbered topic lists
* artificial labels
* explicit separators
* repeated use of identical transition phrases
* unnaturally perfect examples designed only to expose the answer

Difficulty should come from realistic cognitive structure rather than artificial obscurity.

---

## Benchmark and Holdout Policy

The real-world failures that motivated this release should remain protected benchmark or holdout cases.

They should not be copied into training.

Training examples should be newly authored structural analogues that teach the same capability using different:

* people
* settings
* objects
* wording
* ordering
* surface details

Benchmark-only cases should test:

* whether every task survives recovery
* whether attribution remains correct
* whether open questions remain unanswered
* whether unfinished thoughts remain unfinished
* whether nested intentions remain distinct
* whether the model avoids excessive fragmentation

---

## Success Criteria

Gold v1.2.1 succeeds when evaluation shows improvement in:

* Level 3 segmentation reliability
* buried intention recovery
* brief task retention
* multi-person attribution accuracy
* unanswered-question preservation
* incomplete-thought preservation
* boundary precision

Improvement should occur without regression in:

* basic topic segmentation
* uncertainty preservation
* unsupported-addition resistance
* no-magic behavior
* action-item faithfulness

---

## Out of Scope

Gold v1.2.1 does not primarily teach:

* Sensory Overwhelm
* Emotional Journaling
* Burnout
* Multi-note reasoning
* Longitudinal continuity
* Temporal recovery
* Preference learning
* Task prioritization
* Calendar scheduling
* relationship inference
* diagnosis or identity classification

Sensory content may appear only incidentally if needed for realism. It must not become the instructional focus.

---

## Review Expectations

Independent review should verify:

* each example addresses an observed reinforcement need
* each example has one primary lesson
* categories match the controlled vocabulary
* multi-person attribution is evidence-based
* unanswered questions remain unanswered
* no tasks are dropped
* no unfinished thoughts are completed
* nested boundaries are neither merged nor over-segmented
* design notes include Boundary Evidence
* training data remains compatible with the established schema
* benchmark cases are not duplicated in training
* the release does not drift into Gold v1.3 content

---

## Release Acceptance Criteria

Gold v1.2.1 is accepted when:

* all training examples pass schema validation
* the planned coverage distribution is satisfied
* design notes are complete
* Boundary Evidence is documented
* category-reference updates are approved
* review-guide updates are approved, if required
* benchmark and holdout cases are identified
* independent review passes
* training compatibility is confirmed
* evaluation shows no unacceptable regression
* the Gold dataset changelog is updated
* lessons learned are recorded after training

---

## Transition to Gold v1.3

After Gold v1.2.1 is trained and evaluated, development proceeds to:

**Gold v1.3 — Sensory Overwhelm**

Gold v1.3 may include limited transfer checks involving skills reinforced here, such as:

* correct attribution between two people
* preservation of an open question
* retention of a buried task

Those skills must remain secondary.

The primary lesson of Gold v1.3 must remain recovery of intent from notes shaped by sensory overload.

---

## Release Summary

Gold v1.2.1 strengthens the segmentation foundation before the curriculum expands.

Its purpose is not to add breadth.

Its purpose is to repair depth.
