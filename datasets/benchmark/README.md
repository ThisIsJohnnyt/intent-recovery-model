# Benchmark data — never training data

This directory holds evaluation examples, including deliberately
**negative examples** the model is expected to fail until a later version
(see [`docs/benchmarks/benchmark_suite.md`](../../docs/benchmarks/benchmark_suite.md)
for what that means and why).

`training/prepare_data.py` never reads this directory — its training path
only reads `datasets/synthetic.jsonl` (trained on) and
`datasets/real_holdout.jsonl` (held-out eval). Nothing here is wired into
training, intentionally.

First populated entries: [`gold_v1.2.1_probes.md`](gold_v1.2.1_probes.md) /
[`gold_v1.2.1_probes.jsonl`](gold_v1.2.1_probes.jsonl) — 16 examples
authored by the dataset curator (ChatGPT) as a live-evaluation suite for
`gold_v1.2.1`, repurposed here as protected regression/negative-example
benchmarks per `docs/benchmarks/benchmark_suite.md`'s "build once
categorized examples exist" trigger.
