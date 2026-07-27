# Training data spec

This is the format `training/prepare_data.py` expects, and the spec you can hand
to ChatGPT (or fill in yourself for real notes) to generate examples.

**Mission (keep this in view for every example you write or generate):** help
people recover their own intent with as little cognitive and emotional burden
as possible. Not "organize notes." Not "summarize text." See
[ROADMAP.md](ROADMAP.md) for the fuller principles this dataset should serve.

## File format

One JSON object per line (JSONL), UTF-8:

```json
{"input": "<raw scattered thoughts, as the user would actually type them>", "output": {"narrative": "<coherent flowing narrative>", "bullets": ["<key point 1>", "<key point 2>"], "action_items": ["<task 1>"]}, "difficulty": "easy|medium|hard", "category": "<short label for the one lesson this example teaches>"}
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

Two files:
- `training/data/synthetic.jsonl` — ChatGPT-generated examples (see prompt below).
- `training/data/real_holdout.jsonl` — your real notes, same format. Written by hand (you write the `input` from a real note, and either write the `output` yourself or have ChatGPT help draft it and you correct it). These are **not** trained on in round 1 — they're the eval set that tells us whether synthetic-only training generalizes to how you actually write.

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

{"input": "...", "output": {"narrative": "...", "bullets": ["..."], "action_items": ["..."]}, "difficulty": "easy|medium|hard", "category": "..."}

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
training/data/synthetic.jsonl      <- ChatGPT output, appended across batches
training/data/real_holdout.jsonl   <- your real notes, held out from training
```

`prepare_data.py` reads both, validates schema, and produces the tokenized
train/val split `train.py` trains on (only from `synthetic.jsonl` in round 1).
