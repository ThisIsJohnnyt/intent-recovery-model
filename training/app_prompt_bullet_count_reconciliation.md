Handoff for the thought-organizer-app session — bullet-count prompt reconciliation

## Context

The `intent-recovery-model` repo (separate project, separate chat) is working
through a governance package for evaluating the model against real personal
notes. Part of that package flags a prompt-contract conflict that needs to be
fixed on both sides before it goes further: the trained model's instructions
and this app's production instructions must stay identical, because the
model is fine-tuned to expect the exact prompt shape it's served with at
inference time. A mismatch here is a real quality risk, not just a
documentation nit — small-model fine-tuning has shown measurable sensitivity
to exact prompt wording in that project's testing.

**Status**: this is a proposed change, part of a governance package still
mid-review on the training side. Nothing needs to ship immediately, but this
app-side edit should happen in step with the training-side one whenever both
are ready — don't let one land without the other.

## What needs to change

`training/prepare_data.py` in the `intent-recovery-model` repo has this
comment directly above its prompt template:

> "Mirrors src/services/noteOrganizer.ts SYSTEM_PROMPT / USER_PROMPT_TEMPLATE
> exactly, so the model trains on the identical prompt shape it sees in
> production for the single-pass (non-chunked) path."

Its current `USER_PROMPT_TEMPLATE` includes this line for the bullets
section:

```
one key idea per line, 3 to 7 lines
```

**Please locate `SYSTEM_PROMPT`/`USER_PROMPT_TEMPLATE` (or equivalent) in
`src/services/noteOrganizer.ts` and confirm it currently says the same thing**
(or something equivalent — I don't have access to this repo from the
training-side session, so this needs verification on your end before editing).

## Proposed replacement

Replace the bullets-section instruction with:

```
one bullet per source-supported key idea; use as many as the note supports,
up to seven; do not duplicate or invent content to reach a minimum
```

Rationale: a fixed "3 to 7" lower bound forces padding on short, single-idea
notes — which directly conflicts with the project's core "no unsupported
content" rule (used throughout its evaluation/scoring work). The fix is to
make bullet count source-determined instead of padded to a minimum. Upper
bound (seven) stays as a practical cap, not removed.

## Scope

- Only the bullets-count instruction line needs to change. `NARRATIVE`/
  `ACTIONS` section instructions and the rest of `SYSTEM_PROMPT` are
  unaffected.
- Please check for any other place in this app that assumes a 3-7 bullet
  minimum — e.g. UI rendering, placeholder/skeleton states, client-side
  validation — since those weren't visible from the training-side repo and
  might have their own coupled assumption that needs the same fix.
- Please don't change tokenizer/generation settings, marker delimiters, or
  anything else in the prompt — this is scoped narrowly to the one line.

## What happens on the training side once this lands

For reference, not something the app session needs to do: the training repo
will make the matching edit in three places (`training/prepare_data.py`,
`docs/datasets/training_data.schema.json`, `training/DATASET_SPEC.md`) once
both sides are ready to land together, and any future fine-tuning run picks
up the new prompt from that point on. Existing deployed models/checkpoints
are unaffected until a new one is trained and shipped under the new prompt.
