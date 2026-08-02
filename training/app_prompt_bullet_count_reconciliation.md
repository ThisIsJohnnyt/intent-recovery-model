Handoff for the thought-organizer-app session — prompt-contract v1 (source-determined bullets)

## Status: approved, training side landed, app side + activation still pending

This supersedes the earlier draft of this file. Johnny (relaying ChatGPT's
review) has approved the exact rule text below. The training-side change
has landed on `intent-recovery-model` branch `claude/prompt-contract-sync`
(PR #13, not yet merged) — commit `7c6ca6f`. This document specifies
exactly what still needs to happen in `thought-organizer-app`.

## Context

The `intent-recovery-model` repo (separate project, separate chat) fine-tunes
a model against an exact prompt shape. The model is sensitive to exact
prompt wording, so `training/prepare_data.py`'s prompt template and this
app's `src/services/noteOrganizer.ts` `SYSTEM_PROMPT`/`USER_PROMPT_TEMPLATE`
must stay byte-identical, not just semantically equivalent.

**Why this change**: the old bullets instruction ("one key idea per line, 3
to 7 lines") forces padding on short, single-idea notes, which conflicts
with the project's "no unsupported content" rule. The fix makes bullet
count source-determined instead of padded to a minimum.

## The approved contract

**`PROMPT_CONTRACT_VERSION` string** (must match exactly, both repositories):

```
source-determined-bullets-v1
```

**Canonical rule** — replace the bullets-section instruction line with this
exact text, verbatim, no rewording:

```
One source-supported key idea per line, up to 7 lines. Use fewer lines when the source supports fewer ideas. Never add, split, or repeat content to reach a target count.
```

Everything else in `SYSTEM_PROMPT`/`USER_PROMPT_TEMPLATE` — narrative
instruction, actions instruction, section markers (`###NARRATIVE###`,
`###BULLETS###`, `###ACTIONS###`), wording, line breaks — must stay exactly
as it already is. This is scoped narrowly to the one bullets line.

## Verification target (must reproduce exactly)

`training/REAL_DATA_EVALUATION_PROTOCOL.md`'s prompt-contract fingerprint
test specifies rendering this exact fixture note through both prompt
builders and hashing the complete rendered prompt:

**Fixture note text:**
```
Prompt contract fixture: review the blue folder tomorrow?
```

**Fingerprint rule**: encode the complete rendered prompt (the full text
sent to the model — system prompt + raw input + user prompt template, in
whatever order/wrapping `noteOrganizer.ts` actually assembles them) as
UTF-8, with no normalization and no appended newline, then compute SHA-256
of those bytes.

**The training side's rendered prompt for this fixture is:**
```
You are a compassionate AI assistant helping someone organize scattered, fragmented thoughts written under real-world conditions like time pressure, interruption, or fatigue.

The user has provided messy, non-linear thoughts below. Your job is to transform them into three clear, organized views that reduce anxiety and improve clarity.

USER'S RAW THOUGHTS:
Prompt contract fixture: review the blue folder tomorrow?

Respond with exactly this format, using these three section markers each on their own line, with no other text before or after:

###NARRATIVE###
a coherent, flowing narrative that groups related ideas, keeps the original meaning and tone, and reads less anxiety-inducing than the raw thoughts
###BULLETS###
One source-supported key idea per line, up to 7 lines. Use fewer lines when the source supports fewer ideas. Never add, split, or repeat content to reach a target count.
###ACTIONS###
one task per line; leave this section empty if there are no tasks
```

**Expected SHA-256 (hex) of that exact byte sequence:**
```
161661198071fd81310681f69381ec8e0287141e1e75b09d3a342414af31ccf1
```

If `noteOrganizer.ts` assembles the prompt differently (different
system/user message boundary, different concatenation order for a chat-API
call, etc.), the two repos may legitimately produce different raw text for
the same logical prompt. What must match is the **agreed instruction
wording and version string** — if the full concatenated bytes can't match
because of a structural difference in how the two repos call their
respective model APIs, flag that back rather than silently accepting a
hash mismatch; that's a discrepancy to resolve jointly, not paper over.

## What needs to change in thought-organizer-app

1. Locate `SYSTEM_PROMPT`/`USER_PROMPT_TEMPLATE` (or equivalent) in
   `src/services/noteOrganizer.ts`.
2. Replace the bullets-section instruction with the canonical rule text
   above, verbatim.
3. Expose `PROMPT_CONTRACT_VERSION = "source-determined-bullets-v1"` (as a
   constant, matching whatever convention this repo uses for such things)
   so it can be asserted/logged and compared against the training side's.
4. Add a fixture test: render the fixture note above, hash the result the
   same way (UTF-8 bytes, no normalization, no trailing newline, SHA-256),
   and assert it equals `161661198071fd81310681f69381ec8e0287141e1e75b09d3a342414af31ccf1`
   — or, if the assembled-prompt structure genuinely differs from the
   training side's (see note above), assert against a value confirmed by
   direct comparison with the training-side test instead of this one.
5. Check for any other place in this app that assumes a 3-7 bullet
   minimum — UI rendering, placeholder/skeleton states, client-side
   validation — since those weren't visible from the training-side repo.
6. Don't change tokenizer/generation settings, marker delimiters, or
   anything else in the prompt — scoped narrowly to the bullets line plus
   the version constant and test.

## Release gate — do not deploy this yet

**Implement and commit this on a branch, but do not activate the new
wording in production.** Existing deployed checkpoints (including the
current production checkpoint) were trained on the old "3 to 7 lines"
prompt. Serving the new prompt wording to a model trained on the old
wording is an untested compatibility risk — this needs evaluation before
going live.

**The release plan**: the app-side change and a checkpoint trained or
verified under this new contract release together, not separately. Land
the code and tests now; hold activation until:
- a checkpoint has been trained (or an existing one verified) under
  `source-determined-bullets-v1`, and
- that checkpoint's compatibility with the new prompt has been confirmed
  by the training-side evaluation.

The training side will follow up when that checkpoint work is ready.
Until then, production should keep serving the old prompt wording even
after this app-side branch exists.

## What happens on the training side (for reference)

Already done, for reference — not something the app session needs to do:
`training/prepare_data.py`, `training/DATASET_SPEC.md`, and
`docs/datasets/training_data.schema.json` now reflect the new contract
(PR #13 on `intent-recovery-model`, not yet merged pending this app-side
change landing in step). `training/test_prepare_data.py` locks the
fixture-prompt hash above so the training side can't drift from this
document without its own test failing. No new checkpoint has been trained
under this contract yet — that's separate follow-up work, not part of
this handoff.
