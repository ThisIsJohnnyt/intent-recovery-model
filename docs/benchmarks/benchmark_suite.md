# Benchmark Suite — categorized examples and automated reporting now exist

**Status**: `datasets/benchmark/gold_v1.2.1_probes.jsonl` (16 examples) is
the first populated benchmark set — see its companion
[`gold_v1.2.1_probes.md`](../../datasets/benchmark/gold_v1.2.1_probes.md)
for what it covers and current pass/fail status. The per-category
pass-rate reporting described below ("How this becomes real") **is now
built**: `training/run_benchmark.py` generates results, semantic scoring is
still a human (or future LLM-judge) pass since that's real judgment a
script can't fake, and `training/report_benchmark.py` turns scored results
into overall/per-category/per-kind pass rates, failure counts by taxonomy
label, regression-guard and negative-example tracking, and format-validity
rate — see `gold_v1.2.1_probes.md`'s "Automated scoring and reporting"
section for the actual current report. See
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

`category`/`kind`/`status` tags on benchmark examples are already free —
`prepare_data.py` never reads `datasets/benchmark/` at all (see
`training/DATASET_SPEC.md`). `training/run_benchmark.py <benchmark.jsonl>`
runs any such file against a checkpoint and captures raw output plus
automatically-computed format validity; the semantic dimensions (topic
completeness, attribution accuracy, uncertainty preservation,
unsupported-addition resistance, plus each probe's own named checks) are
scaffolded as `null` for a human to score, since that's real judgment, not
something to fake with a heuristic. `training/report_benchmark.py` then
turns a scored results file into the actual per-category/per-kind pass
rates below — this ended up as a standalone script pair rather than an
extension to `train.py`'s `evaluate_format_validity`, since the
judgment-requiring scoring step has to happen as its own pass regardless
of where the aggregation logic lives.

## Example report (real numbers — gold_v1.2.1_probes.jsonl vs. checkpoint-520)

```
Overall pass rate: 9/16 (56%)
Format-validity rate: 16/16 (100%)

Pass rate by category:
  buried_task_retention: 1/2 (50%)
  dangling_reference: 0/1 (0%)
  interrupted_thought_depth: 1/2 (50%)
  multi_person_attribution: 3/3 (100%)
  nested_boundary_depth: 0/1 (0%)
  open_question_preservation: 2/3 (67%)
  standalone_task_retention: 1/1 (100%)
  task_plus_idea: 0/1 (0%)
  two_unrelated_tasks: 1/1 (100%)
  zero_action_items: 0/1 (0%)

Pass rate by probe kind:
  adversarial: 2/4 (50%)   direct: 4/4 (100%)
  regression: 1/4 (25%)    transfer: 2/4 (50%)

Failure count by taxonomy label:
  Unsupported Addition: 3, Topic Loss: 2, Excessive Fragmentation: 1

Regression guards passed: 9/11 (82%)
Negative examples resolved: 0/5 (0%)
```

See `datasets/benchmark/gold_v1.2.1_probes.md` for what this reveals
(probes `14`/`16` are candidates to reclassify from `regression_guard` to
`negative_example` under this stricter scoring) and the exact command to
reproduce it.

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
Five now exist — `gold_v1.2.1_probes.jsonl`'s `02`, `03`, `08`, `12`, `15`
(`status: "negative_example"`), each already revealing a specific,
documented limitation rather than a hypothetical one. See
`gold_v1.2.1_probes.md` for what each currently fails on.
