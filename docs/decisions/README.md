# Project Decision Records (PDRs)

A PDR captures a significant project decision at the time it's made:
what was decided, why, and who approved it — so nobody has to reconstruct
the reasoning from chat history six months later.

## When to write one

Write a PDR for decisions with lasting consequences: architecture choices,
dataset/process rules, format changes, anything that would be genuinely
confusing to reverse-engineer later. Not every choice needs one — day-to-day
implementation details belong in code comments or `training/ROADMAP.md`'s
"hard-won findings," not here.

**PDR-001 is the first *formal* record.** Several significant decisions were
already made before this process existed and remain documented informally:

- Delimited-marker output format over JSON (a small model's tokenizer can't
  represent `{`/`}`, and even bracket-matched JSON arrays failed ~50% of the
  time on memorized examples) — see `training/ROADMAP.md`'s "hard-won
  findings."
- Self-hosting the fine-tuned model via Git LFS rather than the Hugging
  Face Hub.
- Staged sequencing (v1 real data → v1.5 richer schema → v2/v3 architecture)
  rather than building the full intent-recovery vision at once.

These aren't retroactively renumbered — they're real decisions, just not
recorded in this format.

## Format

Each PDR is a short file: `PDR-NNN.md`, three-digit zero-padded, sequential.

```markdown
# PDR-NNN: <short title>

**Date**: YYYY-MM-DD
**Status**: Accepted | Superseded by PDR-XXX

## Decision
<what was decided, one or two sentences>

## Reasoning
<why>

## Approved by
- Product Owner
- Engineering Lead
- Dataset Curator
```

## Index

- [PDR-001](PDR-001.md) — Build dataset infrastructure before large datasets
- [PDR-002](PDR-002.md) — Sync the dataset curator via live GitHub read access, not manual relay
- [PDR-003](PDR-003.md) — Split into `intent-recovery-model` and `thought-organizer` repos (see [migration plan](PDR-003-migration-plan.md))
- [PDR-004](PDR-004.md) — Split real-note evaluation into routine validation and sealed holdout
- [PDR-005](PDR-005.md) — Govern and strictly evaluate private real-note data
- [PDR-006](PDR-006.md) — License the gold dataset CC BY-NC-SA 4.0, not CC-BY-4.0
