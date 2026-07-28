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

This mirrors real neurodivergent note-taking, where unrelated thoughts are often captured together.

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

- Evidence First
- No Magic Examples
- One primary lesson per example
- Realistic neurodivergent writing
- Increasing difficulty across the release
- Every fragment exists for a documented reason

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
|20|Realistic ADHD-style note capture|Expert|

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

## Design Notes Requirement

Each example includes:

- Example ID
- Lesson
- Author Intent
- Scenario
- Reason each fragment exists
- Expected Failure Modes
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

- Gold v1.3 — Sensory Overwhelm
- Gold v1.4 — Emotional Journaling
- Gold v1.5 — Burnout
- Future: Multi-note reasoning, Longitudinal continuity, Temporal recovery
