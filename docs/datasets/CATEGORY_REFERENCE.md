# Category Reference

The `category` field on a training example (see
[`training/DATASET_SPEC.md`](../../training/DATASET_SPEC.md)) names the one
specific recovery skill that example teaches. This is a living document —
add a category here the first time it's used in a batch.

## Categories in use (as of `gold_v1.1`)

| Category | Teaches | Difficulty seen | Introduced in |
|---|---|---|---|
| `simple_list` | Recover tasks from a straightforward fragmented list | easy | v1.0 |
| `interrupted_thought` | Resume a thought after it's interrupted by another | easy | v1.0 |
| `topic_switching` | Separate interleaved topics (e.g. work vs. home) that appear out of order | medium | v1.0 |
| `zero_action_items` | Recognize that observations aren't tasks — don't invent one | easy | v1.0 |
| `unfinished_reference` | Preserve uncertainty about a reference without inventing what it means | hard | v1.0 |
| `interleaved_work_personal` | Separate work and personal threads woven through one note | medium | v1.1 |
| `rapid_branching_excitement` | Track fast-branching ideas without losing the thread | hard | v1.1 |
| `voice_to_text_artifacts` | Recover intent through transcription self-corrections/artifacts | medium | v1.1 |
| `abrupt_topic_switching` | Handle a hard cut between unrelated topics with no transition | medium | v1.1 |
| `repeated_reminder` | Recognize the same reminder restated differently, dedupe it | easy | v1.1 |
| `half_finished_thoughts` | Don't invent the ending of a thought that was cut off | hard | v1.1 |
| `contradictory_statements`* | A note that resolves from frustration to relief within itself | hard | v1.1 |
| `short_note` | Handle a 1-2 line note as its own case, not just incidentally | easy | v1.1 |
| `long_rambling` | Recover structure from a long entry without losing content to length | hard | v1.1 |
| `dangling_reference` | A second flavor of unresolved reference (a memory-recall prompt, not just an object) | medium | v1.1 |
| `anxious_task_dump` | Recover tasks from a note where the writer names being overwhelmed | medium | v1.1 |
| `hyperfocus_details` | Distinguish technical detail/observations from the one real task among them | medium | v1.1 |

*\*See [`gold_v1.1_review_report.md`](../../datasets/gold/gold_v1.1_review_report.md)
— this label may not perfectly match what the example demonstrates
(a resolved narrative arc, not an unresolved mood contradiction).*

## Target categories not yet represented

- **Multiple unrelated topics interleaved at once** (distinct from
  `topic_switching`'s two-out-of-order and `interleaved_work_personal`'s
  two-threads — this is several unrelated topics at once). **Confirmed as
  `gold_v1.2`'s focus** — see `training/ROADMAP.md`'s release curriculum.
- Author-only references/abbreviations beyond "unfinished" — in-jokes or
  shorthand only the writer would parse (distinct from `dangling_reference`,
  which is closer to a memory-recall prompt).

## Cognitive/emotional states represented

Per `DATASET_SPEC.md`'s "describe state, never a diagnosis" rule — track
here which states have actually appeared in examples, to catch
underrepresentation early (see `REVIEW_GUIDE.md`).

**Represented**: hyperfocus (`hyperfocus_details`, v1.1), rapid-branching
excitement (`rapid_branching_excitement`, v1.1), anxiety
(`anxious_task_dump`, v1.1).

**Not yet represented** — prioritized by the dataset curator for upcoming
releases: sensory overwhelm (next, `gold_v1.3`), emotional journaling
(`gold_v1.4`), burnout (`gold_v1.5` — overlaps enough with emotional
journaling that it should follow rather than lead).
