# Category Reference

The `category` field on a training example (see
[`training/DATASET_SPEC.md`](../../training/DATASET_SPEC.md)) names the one
specific recovery skill that example teaches. This is a living document —
add a category here the first time it's used in a batch.

This tracks actual `category` values used in real data. For the
conceptual vocabulary used *while authoring* examples (fragment types,
boundary types, failure types), see [`TAXONOMY.md`](TAXONOMY.md) instead —
the two are complementary, not duplicates.

## Categories in use (as of `gold_v1.2.1`)

A category is never deleted from this table just because a later release
stops using it — see "Category lifecycle" below.

| Category | Teaches | Difficulty seen | Introduced in | Deprecated |
|---|---|---|---|---|
| `simple_list` | Recover tasks from a straightforward fragmented list | easy | v1.0 | — |
| `interrupted_thought` | Resume a thought after it's interrupted by another | easy | v1.0 | — |
| `topic_switching` | Separate interleaved topics (e.g. work vs. home) that appear out of order | medium | v1.0 | — |
| `zero_action_items` | Recognize that observations aren't tasks — don't invent one | easy | v1.0 | — |
| `unfinished_reference` | Preserve uncertainty about a reference without inventing what it means | hard | v1.0 | — |
| `interleaved_work_personal` | Separate work and personal threads woven through one note | medium | v1.1 | — |
| `rapid_branching_excitement` | Track fast-branching ideas without losing the thread | hard | v1.1 | — |
| `voice_to_text_artifacts` | Recover intent through transcription self-corrections/artifacts | medium | v1.1 | — |
| `abrupt_topic_switching` | Handle a hard cut between unrelated topics with no transition | medium | v1.1 | — |
| `repeated_reminder` | Recognize the same reminder restated differently, dedupe it | easy | v1.1 | — |
| `half_finished_thoughts` | Don't invent the ending of a thought that was cut off | hard | v1.1 | — |
| `contradictory_statements`* | A note that resolves from frustration to relief within itself | hard | v1.1 | — |
| `short_note` | Handle a 1-2 line note as its own case, not just incidentally | easy | v1.1 | — |
| `long_rambling` | Recover structure from a long entry without losing content to length | hard | v1.1 | — |
| `dangling_reference` | A second flavor of unresolved reference (a memory-recall prompt, not just an object) | medium | v1.1 | — |
| `anxious_task_dump` | Recover tasks from a note where the writer names being overwhelmed | medium | v1.1 | — |
| `hyperfocus_details` | Distinguish technical detail/observations from the one real task among them | medium | v1.1 | — |
| `two_unrelated_tasks` | Two unrelated tasks, no relationship between them | easy | v1.2 | — |
| `task_plus_observation` | One task, one non-actionable observation | easy | v1.2 | — |
| `task_plus_idea` | One task, one speculative (not committed) idea | easy | v1.2 | — |
| `observation_plus_idea` | Two non-actionable fragments — action_items should stay empty | easy | v1.2 | — |
| `three_independent_topics` / `four_independent_topics` / `five_independent_topics` | Scale topic count with no structural complexity | medium | v1.2 | — |
| `topic_switch_and_return` | Leave a topic, insert an unrelated aside, then return to the original | medium | v1.2 | — |
| `observation_among_tasks` / `idea_among_tasks` | Position in the note doesn't change classification | medium | v1.2 | — |
| `buried_reminder` | A real task hidden inside a much longer unrelated reflection | hard | v1.2 | — |
| `interrupted_thought_multi_topic` | A thought interrupted by an unrelated topic, then explicitly resumed | hard | v1.2 | — |
| `stream_of_consciousness_topics` | Run-on style blurs topics that aren't actually related | hard | v1.2 | — |
| `nested_thought` | A parenthetical aside nested within one topic, not a second topic | hard | v1.2 | — |
| `long_rambling_multi_topic` | Length alone shouldn't merge or drop topics | hard | v1.2 | — |
| `reminder_inside_narrative` | A task remembered mid-story; distinguish it from what's outside the writer's control | hard | v1.2 | — |
| `emotional_aside_multi_topic` | An emotional reflection interleaved with tasks it isn't causally connected to | expert | v1.2 | — |
| `repeated_reminder_multi_topic` | Dedupe a reminder repeated under emphasis, not just simple restatement | expert | v1.2 | — |
| `rapid_topic_switching_incomplete_sentences` | Very rapid topic changes with a genuinely unfinished sentence | expert | v1.2 | — |
| `maximum_interleaving` | Combines rapid switching, an emotional aside, and a repeated mention at once | expert | v1.2 | — |
| `interrupted_thought_depth` | Preserve an interrupted thought, connect an explicit return to the original topic, and avoid inventing the missing content | medium, hard | v1.2.1 | — |
| `buried_task_retention` | Recover a brief task embedded in a longer narrative or interleaved note without allowing it to disappear | medium, hard, expert | v1.2.1 | — |
| `nested_boundary_depth` | Keep qualifiers and governed clauses attached to one coherent intention while separating genuinely independent content | medium, hard | v1.2.1 | — |
| `multi_person_attribution` | Preserve who said, did, has, needs, or receives each item when multiple people are mentioned; retain ambiguity when attribution is unresolved | medium, hard, expert | v1.2.1 | — |
| `open_question_preservation` | Preserve a question as unresolved instead of inventing an answer, while recovering any supported checking task separately | medium, hard, expert | v1.2.1 | — |
| `standalone_task_retention` | Preserve a brief or repeatedly emphasized task as one action item even when more salient narrative, emotion, or other tasks surround it | expert | v1.2.1 | — |

*\*See [`gold_v1.1_review_report.md`](../../datasets/gold/gold_v1.1_review_report.md)
— this label may not perfectly match what the example demonstrates
(a resolved narrative arc, not an unresolved mood contradiction).*

### Category lifecycle

`Deprecated` is set to the release where a category was superseded (e.g. by
a better-calibrated replacement), never left blank retroactively and never
used as a reason to delete the row — per [`PDR-001`](../decisions/PDR-001.md)'s
stance that past decisions aren't retroactively erased, a deprecated
category's row stays as the historical record of what was tried and why it
changed (that "why" belongs in the superseding release's `CHANGELOG.md`
entry). None of the categories above are deprecated yet.

`gold_v1.2` categories and difficulty calibration: see
[`gold_v1.2_review_report.md`](../../datasets/gold/gold_v1.2_review_report.md)
for how the difficulty tiers were derived directly from
`gold_v1.2_curriculum.md`'s own level definitions (an initial draft had
inconsistencies between the two that this release corrects).

`gold_v1.2.1`'s six categories reinforce rather than duplicate existing
`v1.2` categories — each targets a broader or previously-untested failure
mode of an already-taught skill:

- `buried_task_retention` is intentionally broader than `buried_reminder`:
  the `v1.2` category teaches recovery of one reminder hidden in
  reflection, while this one targets the general failure mode where *any*
  brief supported task can disappear from the output.
- `interrupted_thought_depth` extends `interrupted_thought` and
  `interrupted_thought_multi_topic` by adding explicit return-linking,
  unresolved content, and competing inserted intentions.
- `nested_boundary_depth` extends `nested_thought` by testing both
  boundary directions — avoiding merging independent content *and*
  avoiding splitting one governed or qualified intention (see
  `TAXONOMY.md`'s new `Excessive Fragmentation` failure category).
- `standalone_task_retention` is scoped narrowly to survival/deduplication
  of a brief, explicitly repeated task — not a generic label for every
  example that happens to contain a task.

See [`gold_v1.2.1_review_report.md`](../../datasets/gold/gold_v1.2.1_review_report.md)
for the full review.

## Target categories not yet represented

- Author-only references/abbreviations beyond "unfinished" — in-jokes or
  shorthand only the writer would parse (distinct from `dangling_reference`,
  which is closer to a memory-recall prompt).
- Multi-note/longitudinal recovery — explicitly out of scope for any
  single-note gold release; see `training/ROADMAP.md`'s v2/v3 section.

## Cognitive/emotional states represented

Per `DATASET_SPEC.md`'s "describe state, never a diagnosis" rule — track
here which states have actually appeared in examples, to catch
underrepresentation early (see `REVIEW_GUIDE.md`).

**Represented**: hyperfocus (`hyperfocus_details`, v1.1), rapid-branching
excitement (`rapid_branching_excitement`, v1.1), anxiety
(`anxious_task_dump`, v1.1, and incidentally in `maximum_interleaving`,
v1.2).

**Incidentally touched, not yet a dedicated release**: burnout language
appears in `emotional_aside_multi_topic` (v1.2, "feeling really burnt out
lately") as one fragment within a topic-segmentation example — this is not
a substitute for `gold_v1.3`'s planned dedicated burnout release, just an
early, brief appearance worth noting so `v1.3` isn't designed as if burnout
were entirely unrepresented.

**Not yet represented** — prioritized by the dataset curator for upcoming
releases: sensory overwhelm (next, `gold_v1.3`), emotional journaling
(`gold_v1.4`), burnout (`gold_v1.5` — overlaps enough with emotional
journaling that it should follow rather than lead).
