# Training data spec

This is the format `training/prepare_data.py` expects, and the spec you can hand
to ChatGPT (or fill in yourself for real notes) to generate examples.

## File format

One JSON object per line (JSONL), UTF-8:

```json
{"input": "<raw scattered thoughts, as the user would actually type them>", "output": {"narrative": "<coherent flowing narrative>", "bullets": ["<key point 1>", "<key point 2>"], "action_items": ["<task 1>"]}}
```

Rules for `output`:
- `narrative`: rewrites `input` as a coherent narrative. Same meaning and tone as the input, just organized. Not therapy-speak, not generic — it should clearly be about the specific things mentioned in `input`.
- `bullets`: 3-7 short key points extracted from `input`.
- `action_items`: concrete tasks/next steps mentioned in `input`. Use an empty array `[]` when the input has none — never invent one.

Two files:
- `training/data/synthetic.jsonl` — ChatGPT-generated examples (see prompt below).
- `training/data/real_holdout.jsonl` — your real notes, same format. Written by hand (you write the `input` from a real note, and either write the `output` yourself or have ChatGPT help draft it and you correct it). These are **not** trained on in round 1 — they're the eval set that tells us whether synthetic-only training generalizes to how you actually write.

## Diversity requirements (important)

Do not let every example read like "person overwhelmed by chaos." The same
person produces very different notes depending on their state — the dataset
needs to reflect that range, not a single stereotype:

**Cognitive/emotional states to cover** (mix across examples): calm and
highly organized, mild distraction, hyperfocus, executive dysfunction,
anxiety, sensory overwhelm, burnout, rapid-branching excitement (ideas
spawning ideas), emotional journaling, dry random observations, and lists
that slowly devolve into unrelated thoughts partway through.

**Structural variety to include across examples**: multiple unrelated
topics interleaved in one note; abrupt topic switches with no transition;
half-finished thoughts; references only the author would understand
("the thing with the blue folder"); the same worry restated slightly
differently a few times; contradictory statements (mood clearly shifted
between lines); notes with zero action items; very short notes (1-2
lines) and long rambling ones; a range of subjects — work, relationships,
health, chores/errands, hobbies, money, family.

Aim for roughly even coverage across the states above, not mostly-anxious
examples — the model should learn these are all valid "scattered thoughts,"
not that scattered = distressed.

## Prompt to give ChatGPT

Generate in batches (ask for ~15-20 at a time, run it multiple times to
reach a few hundred total). Paste this, adjusting the "batch categories"
line each time to steer toward under-represented states:

```
Generate 15 training examples in JSONL format (one JSON object per line,
no markdown fences, no commentary) for a note-organizing app. Each line:

{"input": "...", "output": {"narrative": "...", "bullets": ["..."], "action_items": ["..."]}}

"input" = realistic scattered, messy personal notes a real person would
jot down (voice-to-text or quick typing), NOT polished writing. "narrative"
= the same content rewritten as one coherent paragraph, same meaning/tone,
easier to read. "bullets" = 3-7 short key points. "action_items" = concrete
tasks mentioned, or [] if none — never invent tasks that aren't implied by
the input.

This batch's cognitive/emotional states to cover (mix these across the 15):
{{e.g. "hyperfocus, burnout, calm/organized, rapid-branching excitement"}}

Also vary structure across the batch: some notes should interleave
multiple unrelated topics, some should have abrupt topic switches, some
should restate the same worry twice in different words, some should have
zero action items, some should be very short (1-2 lines), at least one
should be long and rambling.
```

## Where files go

```
training/data/synthetic.jsonl      <- ChatGPT output, appended across batches
training/data/real_holdout.jsonl   <- your real notes, held out from training
```

`prepare_data.py` reads both, validates schema, and produces the tokenized
train/val split `train.py` trains on (only from `synthetic.jsonl` in round 1).
