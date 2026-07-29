# Benchmark data — never training data

This directory holds evaluation examples, including deliberately
**negative examples** the model is expected to fail until a later version
(see [`docs/benchmarks/benchmark_suite.md`](../../docs/benchmarks/benchmark_suite.md)
for what that means and why).

`training/prepare_data.py` never reads this directory — its training path
only reads `datasets/synthetic.jsonl` (trained on) and
`datasets/real_holdout.jsonl` (held-out eval). Nothing here is wired into
training, intentionally.

Empty for now — no negative or benchmark examples authored yet. That's a
dataset curator decision, not something to fabricate ahead of real content.
