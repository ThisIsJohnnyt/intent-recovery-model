# Seed-17 compatibility study postmortem — Claude's contribution

**Date:** 2026-08-02
**Scope:** serialization/tokenizer investigation, target-distribution analysis, runner/prompt-contract
pinning correction, engineering feasibility review of the postmortem's 5 design questions.
**Status:** input to ChatGPT's postmortem/contract-alternatives design; not a proposal to resume compute.

## Headline finding

**The current output representation cannot mechanically verify "one idea per line," and cannot
even teach it reliably**, because the tokenizer destroys the only signal ("\n") that currently
carries item-boundary information. This isn't a training-data-quality problem or a prompt-wording
problem — it's a representation problem underneath both. Verified empirically, not inferred.

## 1. Serialization/tokenizer investigation

Tested the actual tokenizer (`checkpoints/gold_v1.2.2-newprompt-seed17/final`, the FLAN-T5
SentencePiece tokenizer used throughout this project) on a round-trip encode/decode:

```
input:   'one\ntwo\nthree'
decoded: 'one two three'        <- every newline gone, 0/2 survived
```

Section markers (`###NARRATIVE###`/`###BULLETS###`/`###ACTIONS###`) survive perfectly — they're
literal non-whitespace character sequences, tokenized as ordinary subwords. Newlines don't: this
tokenizer's SentencePiece normalization treats any whitespace run (one newline, three newlines, a
newline plus spaces) identically, collapsing it to nothing distinguishable in the decoded string.
This is a property of the tokenizer/vocabulary, not something `run_benchmark.py`'s decode call
controls (`skip_special_tokens=True` isn't the cause — tested independent of that flag).

Practical consequence: `check_format_valid()` and the marker-based section split work reliably
(hence 16/16 format validity across every cell this study ran). But **within** the `###BULLETS###`
section, there is currently no character sequence that survives to mark where one bullet ends and
the next begins. A human or LLM judge can still parse bullet boundaries semantically (by reading
for coherent ideas) — which is what the acceptance-set scoring in this study actually did — but no
mechanical string operation can.

**Tested candidate delimiters — all round-trip cleanly through this tokenizer:**

| Delimiter style | Round-trips clean? |
|---|---|
| `- ` prefix per item | Yes |
| `\|` separator | Yes |
| `1. 2. 3.` numbering | Yes |
| `###ITEM###` marker (matching existing section-marker style) | Yes |

Any of these would make bullet/action counting mechanically verifiable, the same way section
boundaries already are. This is a low-risk, well-understood category of fix — it's the same
marker-based approach the prompt contract already uses successfully at the section level, applied
one level deeper.

## 2. Target-distribution analysis

Checked what the model is *actually* trained to predict, not just what `prepare_data.py` writes to
the JSONL file. `prepare_data.py` builds `target = "\n".join([NARRATIVE_MARKER, narrative,
BULLETS_MARKER, *bullets, ACTIONS_MARKER, *actions])` — each bullet genuinely is its own line in
the raw `target` string. But once that string passes through `train.py`'s
`tokenizer(text_target=..., ...)` call, the same newline-collapse applies: the token sequence the
model is trained to predict has no item-boundary signal in it at all. Confirmed directly on a real
training example:

```
target (as written):    '...###BULLETS###\nBuy milk\nBuy dog food\nCall dentist Tuesday...'
target (as tokenized):  '...###BULLETS### Buy milk Buy dog food Call dentist Tuesday...'
```

The model was never shown item boundaries during training — not because the data lacks them, but
because they don't survive the tokenizer between "written" and "trained on."

Checked whether anything else could be serving as a de facto boundary signal. Across all 210
bullets in the 66 gold_v1.2.2 examples: **100% start with an uppercase letter, ~0% end with
terminal punctuation.** So there is a *statistical* regularity (capital letter, no preceding
period) the model could in principle exploit as a soft boundary cue — but it's unreliable by
construction: proper nouns (Avery, Morgan, Kira, Priya, Rowan...) are capitalized *mid-bullet* too,
so a capitalization-based heuristic parser would produce exactly the false-split/false-merge
failures actually observed in this study (Excessive Fragmentation, Topic Merge, Topic Loss were
among the most common failure labels across all three cells). This is consistent with, and
plausibly explains, a meaningful share of the semantic failures ChatGPT scored — not as an excuse
for them, but as a mechanistic account of *why* a model with no real boundary signal would fail in
exactly these ways.

## 3. Runner/prompt-contract pinning correction

Fixed in `training/prompt_contract_compatibility_study_manifest.md` (Round 5 section, and the
corresponding cell commands). Summary: the worktree-pinning design pinned *every* file in
`training/`, not just `prepare_data.py` — so `run_benchmark.py`'s later `required_semantic_dimensions`
propagation (added in this same PR #15, after both pin points existed) got silently pinned away,
which is what produced the missing-metadata deviation ChatGPT caught and repaired post-hoc.

Root-caused via `git log`/`git diff` (not assumed): confirmed neither `8d7aa09` nor `80062bc`
contains the propagation code; confirmed `train.py` happened to be byte-identical between `80062bc`
and current `main` this round (so it wasn't actually affected), which was luck, not a guarantee.

Fix: pin only `prepare_data.py` via `sys.path` injection; always execute the *current*
`run_benchmark.py`/`train.py` from `main`. Verified the mechanism directly, twice — once confirming
`build_prompt` resolves to the pinned worktree's object while executing current code, and once with
a dry run of the actual corrected cell command (stopped just before model load, to avoid spending
compute while the study is closed) confirming `sys.argv` parsing and probe loading both work
correctly end to end. This closes the general class of bug, not just this one instance — any future
run using this manifest is protected against silently regressing to stale runner code again.

## 4. Engineering feasibility review of the postmortem's 5 questions

**Should bullets/actions use explicit machine-verifiable item delimiters?**
Yes, and it's low-risk to implement — the tokenizer already handles marker-style delimiters
correctly (that's exactly what `###BULLETS###` etc. already are). Concretely: pick one delimiter
style (a `- ` prefix per item is the least visually disruptive and matches common list conventions),
change `prepare_data.py`'s target construction to use it, change the prompt instruction text to
describe it explicitly, and add a matching parser (Python side for benchmarking, TypeScript side in
`outputParser.ts`) that splits on it. This requires a new training run under the revised contract —
it's a genuine format change, not a wording tweak, so it can't be validated without retraining.

**Is the current output representation capable of teaching and measuring source-determined
counts?** No, not reliably — demonstrated empirically above, not asserted. The current
representation can teach *content* (what the bullets say) but not *structure* (how many bullets,
where one ends). Any acceptance criterion built on "count the bullets" is measuring something the
representation can't reliably produce or the harness can't reliably check without a human/LLM in
the loop making a judgment call — which is exactly why this study's four `capability_checks` around
bullet/action counts (`BULLET_COUNT_RULE_SATISFIED` etc.) had to be scored by ChatGPT's own
semantic reading, not computed.

**Which behavior belongs in the prompt versus training targets?** Engineering framing, not a full
answer: a prompt instruction only reliably shapes generation when the training targets *demonstrate*
that same structure at the token level — next-token prediction learns from what it's shown, not
just what it's told to do in the input. Structural requirements (delimiter discipline, count bounds)
belong in the *target representation* (need a token-level signal to be learnable at all). Content
requirements (don't invent, preserve ambiguity, attribute correctly) are appropriately taught via
instruction-plus-example, since the model doesn't need a special token to learn "don't say things
the source doesn't support" — it needs enough correctly-labeled examples, which the current
representation doesn't block.

**Should the next curriculum cover a balanced capability family instead of patching sdb-01/02/04/05
individually?** This has direct precedent already in this project:
`training/gold_v1.2.2_vs_v1.2.3_control_comparison.md` found that gold_v1.2.3's narrow, single-probe-
motivated additions "interact negatively with several capabilities it wasn't targeting" at this
exact data scale (66-72 examples). Patching sdb-01/02/04/05 individually risks reproducing that same
failure mode a third time. Given that precedent, narrow point-fixes are higher-risk than a balanced
capability-family curriculum at this data scale — this isn't a new concern, it's a previously-
confirmed one recurring in a new context.

**What acceptance set and automated structural checks should gate another compute run?** If explicit
delimiters are adopted (per question 1), a genuinely automated structural check becomes possible:
a small deterministic parser that splits decoded output on the delimiter and mechanically compares
the count against `bullet_count_rule`/`action_count_rule` — turning `BULLET_COUNT_RULE_SATISFIED`
from a human/LLM judgment call into a real, objective, scriptable check, the same way
`check_format_valid()` already mechanically verifies marker presence and ordering. Content-semantic
dimensions (`topic_completeness`, `unsupported_addition_resistance`, etc.) would still need
human/LLM scoring — that's a judgment question, not a parsing one — but decoupling "did the model
produce the right *count*" from "did the model produce the right *content*" removes exactly the
ambiguity this study's acceptance gate ran into.

## What this doc is not

Not a proposal for a specific new prompt contract, not a retrained checkpoint, not a request to
resume compute. Per Johnny's direction: no seed-73, no Cell B1/`run_benchmark_onnx.py` work, no app
PR #4 merge, no corrective dataset work, until the postmortem concludes and Johnny picks a contract
direction.
