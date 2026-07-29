# Roadmap

## North star

See [../docs/vision/NORTH_STAR.md](../docs/vision/NORTH_STAR.md) for the
mission and the formal definition of Intent Recovery as a task.

## Collaboration model

See [../docs/vision/NORTH_STAR.md](../docs/vision/NORTH_STAR.md)'s
"Collaboration model" section. In short: dataset-content decisions come from
the product owner + ChatGPT; this repo's job is building what that
specification asks for.

## v1 — prove the pipeline (current)

Single fine-tuned FLAN-T5-base, delimited-marker output format
(`###NARRATIVE###`/`###BULLETS###`/`###ACTIONS###` — JSON is not viable for
this model, see below). Pipeline: `prepare_data.py` → `train.py` →
`export_onnx.py`, self-hosted in `public/models/`. Proven end-to-end on a
15-example placeholder fixture. Real dataset generation is underway per
[DATASET_SPEC.md](DATASET_SPEC.md) — see the release curriculum below.

## Release curriculum

Each gold release teaches one new capability, not just more volume — see
[`../docs/datasets/REVIEW_GUIDE.md`](../docs/datasets/REVIEW_GUIDE.md)'s
"release bundle" section for what a release actually consists of.

| Release | Focus | Status |
|---|---|---|
| `gold_v1.0` | Basic recovery (schema validation, pipeline proof) | ✅ Complete |
| `gold_v1.1` | Realistic note styles, authentic messiness | ✅ Complete |
| `gold_v1.2` | Multiple interleaved topics (many unrelated topics at once — segmentation, not summarization) | ✅ Complete |
| `gold_v1.2.1` | Segmentation reinforcement (additive corrective release — deeper Level 3 structures, multi-person attribution, open-question preservation, task retention; see [`gold_v1.2_lessons_learned.md`](../datasets/gold/gold_v1.2_lessons_learned.md)'s recommendations) | Next |
| `gold_v1.3` | Sensory overwhelm | Planned |
| `gold_v1.4` | Emotional journaling | Planned |
| `gold_v1.5` | Burnout (follows emotional journaling — enough overlap that it shouldn't lead) | Planned |

**Temporal Recovery is explicitly not on this list.** It requires
multi-note/sequence input (e.g. "Monday: mentioned an invoice, Wednesday:
asked if it was ever sent, Friday: mentioned it again" — recognizing a
thought resurfacing across *separate* notes), which is a different input
shape than today's single-note `{"input": "...", "output": {...}}` schema.
It belongs under **v2/v3**'s "Longitudinal continuity" below, gated behind
input-schema work that doesn't exist yet — not a same-architecture gold
release.

Hard-won findings from getting v1 working, worth remembering before changing
the format or model again:
- FLAN-T5-base's tokenizer has no vocabulary token for `{`/`}` — both map to
  `<unk>` and get silently stripped on decode, so **no JSON object output is
  possible** with this model.
- A JSON *array* avoids the brace problem but still failed ~50% of the time
  even on memorized training examples — small models lose track of
  bracket/quote nesting. Plain delimited markers degrade gracefully instead.
- T5 + fp16 → NaN loss; use bf16.
- `no_repeat_ngram_size` actively corrupts literal marker text (it forbids
  intentional repetition) — use a bounded `max_new_tokens` instead, and rely
  on the parser tolerating a truncated/partial response.
- ONNX export defaults to IR version 9; the bundled `onnxruntime-web`
  (1.14.0) only supports up to IR version 8 — must downgrade the field
  post-export (see `export_onnx.py`).
- Dynamic quantization silently skips the merged decoder's weights (nested
  in an `If`-branch subgraph) without `extra_options={"EnableSubgraph": True}`.

## v1.5 — richer output schema (same architecture)

Once v1 is proven with real data, expand the output schema — still one
fine-tuned model, still the delimited-marker format:

```
narrative
bullets
action_items
topic_clusters      <- which bullets/tasks belong to which topic
emotion_summary     <- objective, e.g. "elevated frustration while tracking several unrelated tasks" — never a diagnosis, never "you seem depressed"
memory_safe_summary <- preserves information, doesn't replay emotion, e.g. "one financial reminder was recorded; the note also reflects a period of high emotional distress" instead of quoting distressing language back
confidence          <- per-field confidence, so the model can be uncertain instead of guessing
```

The memory-safe summary is the feature most aligned with the mission above:
recover the useful information from a note written during a hard moment,
without forcing the person to re-read the hard moment itself.

## Benchmark suite (built)

Moved from "loss went down" to per-category/per-kind pass rate — see
[`../docs/benchmarks/benchmark_suite.md`](../docs/benchmarks/benchmark_suite.md).
`run_benchmark.py` runs any `datasets/benchmark/*.jsonl` file against a
checkpoint; `report_benchmark.py` turns scored results into overall/
per-category/per-kind pass rates, failure counts by taxonomy label,
regression-guard and negative-example tracking, and format-validity rate.
Ended up as a standalone script pair rather than an extension to
`evaluate_format_validity`, since semantic scoring is a judgment-requiring
pass regardless of where the aggregation logic lives.

## v2/v3 — separate project, later

These are bigger architectural bets, deliberately deferred until v1/v1.5 are
proven — build as a dedicated `intent-recovery/` effort rather than
extending `training/`:

- **Thought-graph-driven synthetic data generator.** Instead of asking an
  LLM to "generate messy notes," generate a structured thought graph first
  (topics, importance, interruptions, references between thoughts), then
  derive both the messy note *and* the ground-truth labels from the graph.
  Makes examples reproducible and automatically labelable, and gives every
  apparent bit of randomness in a note a traceable cause — a stronger,
  systematic version of the "No Magic Examples" rule already in
  DATASET_SPEC.md.
- **Two-model split.** Model A (Intent Recovery): fragmented input →
  topics, tasks, relationships, uncertainty, emotional context — never
  rewrites for readability. Model B (Presentation): Model A's structured
  output → narrative / task list / memory-safe summary / briefing. Lets
  presentation quality improve without retraining the reasoning model, and
  lets "did it recover the right intent" be evaluated independently of
  "does it read well."
- **Longitudinal continuity / Temporal Recovery.** Real notes aren't
  independent — the same thought resurfaces and evolves across days.
  Training on sequences (not isolated notes) so the model learns "this is
  the same thought evolving," not "four unrelated notes." See the release
  curriculum above for why this waits for input-schema work rather than
  becoming a near-term gold release.
- **Formal Intent Recovery Dataset Specification (IRDS).** A versioned,
  RFC-style spec — hidden generation data (metadata, cognitive/emotional
  context, thought graph) never seen by the model, separate from the
  input/output pairs it actually trains on — so any generator (GPT, Claude,
  Gemini, a future model) that follows the spec produces compatible data.
