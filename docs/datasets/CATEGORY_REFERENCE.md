# Category Reference

The `category` field on a training example (see
[`training/DATASET_SPEC.md`](../../training/DATASET_SPEC.md)) names the one
specific recovery skill that example teaches. This is a living document —
add a category here the first time it's used in a batch.

## Categories in use (as of `gold_v1.0`)

| Category | Teaches | Difficulty seen |
|---|---|---|
| `simple_list` | Recover tasks from a straightforward fragmented list | easy |
| `interrupted_thought` | Resume a thought after it's interrupted by another | easy |
| `topic_switching` | Separate interleaved topics (e.g. work vs. home) that appear out of order | medium |
| `zero_action_items` | Recognize that observations aren't tasks — don't invent one | easy |
| `unfinished_reference` | Preserve uncertainty about a reference without inventing what it means | hard |

## Target categories not yet represented

From `training/DATASET_SPEC.md`'s diversity requirements — structural
variety still needing dedicated examples:

- Multiple unrelated topics interleaved in one note (distinct from
  `topic_switching`, which is two topics out of order — this is many topics
  at once)
- The same worry/reminder restated slightly differently a few times
  (repeated reminder)
- Contradictory statements from a mood shift within one note
- Very short (1-2 line) notes as their own category, distinct from being
  incidental to another category
- Long, rambling entries
- Author-only references beyond "unfinished" — e.g. abbreviations or
  in-jokes only the writer would parse

## Cognitive/emotional states represented

Per `DATASET_SPEC.md`'s "describe state, never a diagnosis" rule — track
here which states have actually appeared in examples, to catch
underrepresentation early (see `REVIEW_GUIDE.md`).

*(none logged yet — `gold_v1.0`'s five examples are mostly neutral/calm in
tone; hyperfocus, burnout, anxiety, sensory overwhelm, rapid-branching
excitement, and emotional journaling from `DATASET_SPEC.md`'s target list
are not yet represented in any batch.)*
