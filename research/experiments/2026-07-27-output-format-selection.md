# Output format selection for a fine-tuned FLAN-T5-base

**Date**: 2026-07-27
**Related**: [`training/ROADMAP.md`](../../training/ROADMAP.md)'s "hard-won
findings," [`src/utils/outputParser.ts`](../../src/utils/outputParser.ts),
[`training/train.py`](../../training/train.py)

## Hypothesis

A fine-tuned FLAN-T5-base should be able to reliably emit structured JSON
(`{"narrative": ..., "bullets": [...], "action_items": [...]}`) so the app
can parse output with a simple `JSON.parse` instead of fragile regex
extraction from markdown.

## Method

Fine-tuned FLAN-T5-base on a small (14-15 example) placeholder fixture,
iterating on the target output format:

1. **JSON object**, e.g. `{"narrative": "...", "bullets": [...], "action_items": [...]}`.
2. **JSON array** (positional, no keys), e.g. `["...", [...], [...]]`.
3. **Plain delimited markers**, e.g. `###NARRATIVE###\n...\n###BULLETS###\n...\n###ACTIONS###\n...`.

Each iteration was tested by direct inference against training examples
(to check whether the format was learnable at all) and a held-out val
example (to check generalization), not just by reading training loss.

## Results

1. **JSON object: fails completely, not a training problem.** FLAN-T5-base's
   tokenizer has no vocabulary token for `{` or `}` — both map to `<unk>`.
   `tokenizer.decode(..., skip_special_tokens=True)` silently strips `<unk>`
   tokens, so even a model that "wants" to emit `{`/`}` can't produce them
   in decoded output. Confirmed directly: `tok('{', add_special_tokens=False)`
   → `['▁', '<unk>']` for both `{` and `}`. This is a hard tokenizer
   limitation, not something more training data fixes.

2. **JSON array: works for `[`/`]` (no `<unk>` issue — confirmed `[` → a
   real token, `]` → real tokens), but structurally fragile.** Even after
   fixing an unrelated fp16 NaN-loss bug (see below) and training to
   train_loss ≈ 0.15 (near-memorization) on the 14-example fixture, only
   7/14 *training* examples (already seen, already memorized) produced valid
   JSON on generation. Failures were split roughly evenly between the model
   stopping early (unterminated string, never reaching the closing
   brackets) and losing track of nesting (extra/malformed nested arrays,
   trailing commas). This happened on memorized examples — more data alone
   was very unlikely to fix it; small models appear to struggle with
   globally-balanced bracket/quote state over a full generation.

3. **Delimited markers: format itself no longer the bottleneck.** Switching
   the target to plain `###NARRATIVE###`/`###BULLETS###`/`###ACTIONS###`
   markers (no brackets, no quotes, no comma-matching required) meant a
   parse failure degrades gracefully (e.g. a truncated ACTIONS section still
   leaves a usable narrative + bullets) instead of catastrophically (one
   missing bracket invalidates the whole JSON blob).

## Two additional bugs found along the way

- **T5 + fp16 → NaN loss.** `Seq2SeqTrainingArguments(fp16=True)` produced
  `loss: 0.0`, `grad_norm: nan`, `eval_loss: nan` from step 1 — a
  well-documented T5-specific instability. Switching to `bf16=True` (the
  RTX 50-series supports it natively) fixed this immediately;
  `train_loss` became a real, decreasing number.

- **`no_repeat_ngram_size` corrupts intentional repetition.** After
  switching to delimited markers, generation still looped (repeating
  BULLETS/ACTIONS cycles indefinitely — a separate issue, the model hadn't
  learned to emit EOS reliably on unseen input, itself an artifact of the
  tiny 14-example fixture). The instinctive fix — `no_repeat_ngram_size=3`
  — actively made things worse: it forbids the model from repeating *any*
  3-token sequence it already generated, but the markers legitimately need
  to recur verbatim (once per section). The model started emitting garbled
  near-miss variants (`###BLULLETSM###`, `###ACTIONSNAP###`) instead of the
  real markers, trying to say the same thing without repeating the exact
  n-gram. Removed it; kept a mild `repetition_penalty=1.3` and bounded
  `max_new_tokens=300` as a safety cap on runaway generation instead, relying
  on the parser's tolerance for truncated output rather than fighting the
  model's decoding.

## Decision

Ship the delimited-marker format (`###NARRATIVE###`/`###BULLETS###`/
`###ACTIONS###`) as the model's output contract, not JSON. Documented in
`training/ROADMAP.md` and implemented in `src/services/noteOrganizer.ts`,
`src/utils/outputParser.ts`, and the Python mirror in
`training/prepare_data.py`. Revisit only if a future base model's tokenizer
handles `{`/`}` natively (worth re-checking if the base model ever changes —
see `training/ROADMAP.md`'s v2/v3 section).
