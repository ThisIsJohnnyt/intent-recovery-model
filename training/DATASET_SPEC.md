# Training data spec

This is the format `training/prepare_data.py` expects, and the spec you can hand
to ChatGPT (or fill in yourself for real notes) to generate examples.

**Mission (keep this in view for every example you write or generate):** help
people recover their own intent with as little cognitive and emotional burden
as possible. Not "organize notes." Not "summarize text." See
[ROADMAP.md](ROADMAP.md) for the fuller principles this dataset should serve.

## Data contract (read this before proposing a different schema)

The schema below is the **one authoritative format** for anything that
gets trained on. It exists because it matches what
[`training/prepare_data.py`](prepare_data.py) and the deployed model's
output format (`###NARRATIVE###`/`###BULLETS###`/`###ACTIONS###`, see
[ROADMAP.md](ROADMAP.md)'s hard-won findings) actually require — not by
preference. A prior draft of `gold_v1.2` used a different schema
(`note`/`segmented_intentions`, no `output` object) and was rejected
outright because `prepare_data.py` couldn't read it at all — see
`datasets/gold/gold_v1.2_review_report.md`. Before proposing a richer
per-example format (additional fields, restructured output, etc.), put it
in [`docs/datasets/DESIGN_NOTES_TEMPLATE.md`](../docs/datasets/DESIGN_NOTES_TEMPLATE.md)
instead — design notes carry boundary evidence, failure modes, and any
other analysis, and are never read by the training pipeline, so they're
free to be as rich as useful without risking a repeat of that rejection.

A machine-checkable version of this same contract lives at
[`docs/datasets/training_data.schema.json`](../docs/datasets/training_data.schema.json)
(standard JSON Schema, Draft 2020-12) — useful for validating a batch with
any JSON Schema tool before it even reaches `prepare_data.py`. If the two
ever disagree, `prepare_data.py`'s `validate_record()` wins, since that's
what actually gates training — update the schema file to match, not the
other way around.

## File format

One JSON object per line (JSONL), UTF-8:

```json
{"input": "<raw scattered thoughts, as the user would actually type them>", "output": {"narrative": "<coherent flowing narrative>", "bullets": ["<key point 1>", "<key point 2>"], "action_items": ["<task 1>"]}, "difficulty": "easy|medium|hard|expert", "category": "<short label for the one lesson this example teaches>"}
```

Rules for `output`:
- `narrative`: rewrites `input` as a coherent narrative. Same meaning and tone as the input, just organized. Not therapy-speak, not generic — it should clearly be about the specific things mentioned in `input`.
- `bullets`: 3-7 short key points extracted from `input`.
- `action_items`: concrete tasks/next steps mentioned in `input`. Use an empty array `[]` when the input has none — never invent one.

`difficulty` and `category` are optional annotations, not part of what the model
trains on — `prepare_data.py` only reads `input`/`output` and ignores everything
else, so adding them costs nothing and pays off later when we want to measure
accuracy per category instead of one aggregate number (see ROADMAP.md's
benchmark suite section).

Three files:
- `datasets/synthetic.jsonl` — ChatGPT-generated examples (see prompt below).
- `datasets/real_validation.jsonl` — your real notes, same format, for
  **routine development-time evaluation**. Written by hand (you write the
  `input` from a real note, and either write the `output` yourself or have
  ChatGPT help draft it and you correct it). Evaluated automatically by
  `train.py` after every run. **Not** trained on.
- `datasets/real_holdout.jsonl` — your real notes, same format, but
  **sealed for declared release milestones only** — never consulted for
  routine development, curriculum authoring, seed selection, or checkpoint
  tuning. Evaluated only by the separate, explicit
  `training/evaluate_holdout.py`. **Not** trained on. See
  `docs/decisions/PDR-004.md` for why these two are kept separate rather
  than being one file.

## Two rules for every example

**"No Magic Examples":** every synthetic example should be explainable. For
each fragment in a generated note, you should be able to answer *why* it's
there — why it was interrupted, why it repeats, why it has no punctuation,
why a reference is left dangling. If you can't explain an element, it's
noise, not a useful training signal — regenerate it.

**One lesson per example:** each example should be constructable as teaching
one specific recovery skill, not a random pile of chaos. E.g.: "recover tasks
from a simple list," "separate work/home topics interleaved in one note,"
"handle a thought that gets interrupted and resumed later," "recognize there
are zero action items," "resolve a reminder that's restated twice." Naming
the lesson (the `category` field) as you generate is what makes this a
curriculum instead of an undifferentiated pile.

## Diversity requirements (important)

Do not let every example read like "person overwhelmed by chaos." The same
person produces very different notes depending on their state — the dataset
needs to reflect that range, not a single stereotype. Describe *state*, never
a diagnosis — the same configuration below could describe a grad student
during finals, a new parent, someone brainstorming a startup, or someone
recovering from illness, and the model shouldn't need to know which.

**Context to vary across examples**: location, background noise, time
pressure/available time, interruptions, physical state (tired, rushed, calm).

**Cognitive state to vary**: working-memory load, attention switching,
thought velocity (fast/slow), planning style (reactive vs. organized), how
many unfinished thoughts, task urgency.

**Emotional state to vary**: stress, excitement, frustration, curiosity,
fatigue, hopefulness — the full range, not just anxious/overwhelmed.

**Writing style to vary**: typing speed, voice-to-text artifacts, bullet
fragments vs. full sentences, typos, abbreviations.

Concretely, mix across examples: calm and highly organized, mild distraction,
hyperfocus, executive dysfunction, anxiety, sensory overwhelm, burnout,
rapid-branching excitement (ideas spawning ideas), emotional journaling, dry
random observations, and lists that slowly devolve into unrelated thoughts
partway through.

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

{"input": "...", "output": {"narrative": "...", "bullets": ["..."], "action_items": ["..."]}, "difficulty": "easy|medium|hard|expert", "category": "..."}

"input" = realistic scattered, messy personal notes a real person would
jot down (voice-to-text or quick typing), NOT polished writing. "narrative"
= the same content rewritten as one coherent paragraph, same meaning/tone,
easier to read. "bullets" = 3-7 short key points. "action_items" = concrete
tasks mentioned, or [] if none — never invent tasks that aren't implied by
the input. "difficulty" is your judgment of how hard this example is to
recover correctly. "category" is the one specific recovery skill this
example teaches (e.g. "interrupted_thought", "topic_switching",
"zero_action_items", "repeated_reminder", "simple_list").

Every example must be explainable: for each fragment in "input", you should
be able to say why it's there (interrupted, repeated, dangling reference,
no punctuation, etc.) — don't generate noise you can't account for.

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
datasets/synthetic.jsonl              <- ChatGPT output, appended across batches
datasets/real_validation.jsonl        <- your real notes, routine dev-eval, held out from training (gitignored)
datasets/real_holdout.jsonl           <- your real notes, sealed release-milestone eval only, held out from training (gitignored)
datasets/gold/gold_v1.0.jsonl         <- hand-curated gold-tier examples, one file per batch
                                          (gold_v1.1.jsonl, gold_v1.2.jsonl, ... as more arrive)
                                          — not trained on until the gold tier is consolidated
                                          with (or instead of) synthetic.jsonl
datasets/gold/DATASET_CARD.md         <- purpose, scope, generation process, limitations, ethics
datasets/gold/CHANGELOG.md            <- version history of the gold tier
datasets/gold/LICENSE.md              <- CC-BY-4.0
```

Each gold release is a full bundle, not just the `.jsonl` — design notes,
review report, lessons learned, and (once benchmarking exists) benchmark
results, all sharing the release's `gold_vX.Y` version number. See
[`docs/datasets/REVIEW_GUIDE.md`](../docs/datasets/REVIEW_GUIDE.md)'s
"Release bundle" table for the authoritative list of what files that
includes and who writes each one — not repeated here to avoid the list
drifting out of sync in two places. The conceptual layer that supports
authoring/reviewing a release (category vocabulary, design note format,
review checklist, taxonomy, JSON Schema mirror) lives under
`docs/datasets/`, sibling to this spec.

The dataset lives in its own top-level `datasets/` directory (sibling to
`training/`), separate from the training pipeline/code — see
`datasets/gold/DATASET_CARD.md` for the full picture.

`prepare_data.py` reads both, validates schema, and produces the tokenized
train/val split `train.py` trains on (only from `synthetic.jsonl` in round 1).
