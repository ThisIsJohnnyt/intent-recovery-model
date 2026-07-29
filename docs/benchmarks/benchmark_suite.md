# Benchmark Suite — first categorized examples now exist

**Status**: `datasets/benchmark/gold_v1.2.1_probes.jsonl` (16 examples) is
the first populated benchmark set — see its companion
[`gold_v1.2.1_probes.md`](../../datasets/benchmark/gold_v1.2.1_probes.md)
for what it covers and current pass/fail status. The per-category
pass-rate engineering work described below ("How this becomes real") is
still not built — 16 examples were scored manually for the
`gold_v1.2.1_lessons_learned.md` run, which was tractable at this size. See
[`training/ROADMAP.md`](../../training/ROADMAP.md)'s "Benchmark suite"
section for the broader plan.

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

## Negative examples

Some benchmark examples should be inputs the model is **expected to fail**
until a later version — not a bug in the benchmark, the point of it.
Example: given a bare `blue folder / Steve / Tuesday / that thing`, there
isn't enough information to say how these relate. A correct response
preserves that uncertainty (*"I noted a blue folder, Steve, Tuesday, and
'that thing,' but there isn't enough information to determine how they
relate"*); an incorrect one invents a connection (*"Steve left the blue
folder for Tuesday's meeting"*).

Negative examples measure whether a model over-invents connections under
ambiguity — the opposite failure mode from under-extracting. They're
**benchmark data, never training data**: live in `datasets/benchmark/`
(see its `README.md`), which `training/prepare_data.py` never reads (it
only reads `synthetic.jsonl`/`real_holdout.jsonl` for the training path).
No negative examples are authored yet — that's a dataset curator decision,
not something to fabricate speculatively here.
