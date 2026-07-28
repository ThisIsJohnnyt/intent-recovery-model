# Benchmark Suite — not yet implemented

**Status**: planned, needs categorized examples first. See
[`training/ROADMAP.md`](../../training/ROADMAP.md)'s "Benchmark suite"
section.

## Goal

Move from "loss went down" to per-category pass rate — know *what kind* of
recovery a model is actually getting better or worse at, not just one
aggregate number.

## Proposed categories

| Category | Tests |
|---|---|
| Simple lists | Basic extraction without inventing tasks |
| Topic switching | Grouping interleaved topics by intent, not order |
| Repeated thoughts | Recognizing the same reminder restated differently |
| Incomplete references | Preserving uncertainty instead of inventing meaning |
| Emotional notes | Objective emotion summary without diagnosis language |
| Long rambling entries | Recovery without losing content to length |
| Zero action items | Not inventing a task where there isn't one |
| Longitudinal notes | Recognizing the same thought evolving across entries (v2/v3, not yet in scope) |

## How this becomes real

`category`/`difficulty` tags on stored examples are already free —
`prepare_data.py` ignores fields it doesn't recognize (see
`training/DATASET_SPEC.md`). Once the dataset curator provides a set of
examples tagged with these categories (a proper "benchmark split," held out
from training the same way `real_holdout.jsonl` is), `train.py`'s
`evaluate_format_validity` can be extended to report pass-rate per category
instead of a single aggregate. That's the concrete engineering task once
categorized data exists — not something to build speculatively against
placeholder data now.

## Example report (illustrative, not real numbers)

```
Model 0.1
  simple_lists          96%
  topic_switching        83%
  repeated_thoughts      61%
  incomplete_references  44%
  emotional_notes        79%
  long_rambling          58%
  zero_action_items      99%
  longitudinal           N/A
```
