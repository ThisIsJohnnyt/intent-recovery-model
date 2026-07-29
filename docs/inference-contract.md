# Intent Recovery Inference Contract v1

The versioned boundary between `intent-recovery-model` and any application
consuming it (starting with `thought-organizer`). Formalizes behavior that
already exists today — this document doesn't change anything functionally,
it makes the existing behavior a public, depended-upon guarantee instead of
an implementation detail an application happened to rely on.

**Contract version: 1.0.** An application may consume any model release
that declares support for **major version 1** — this decouples the
application from tracking exact model releases; only a breaking change to
this contract requires a major-version bump and an application-side update.

## Shape

```json
{
  "narrative": "string",
  "bullets": ["string"],
  "action_items": ["string"]
}
```

## Guarantees

- **`narrative` is never empty.** Mirrors
  `training_data.schema.json`'s `minLength: 1` on the training side.
- **`bullets`/`action_items` may be empty arrays.** A note with zero actual
  tasks is a real, intentionally-trained case (`zero_action_items` and
  related categories) — an empty `action_items` array is success, not a
  missing-data signal.
- **`action_items` is always grounded in the input.** Never contains a task
  that isn't implied by what was actually written — the model's training
  contract (`training/DATASET_SPEC.md`'s rules, `docs/vision/GOLD_PHILOSOPHY.md`'s
  "Evidence First") already requires this; this contract makes it a
  guarantee the application can depend on, not just a training aspiration.
- **List ordering is not guaranteed meaningful.** No established convention
  says `bullets`/`action_items` are ordered by priority, chronology, or
  anything else — an application should not infer meaning from position.
- **Unknown fields are ignored, not rejected.** Matches
  `training/prepare_data.py`'s existing behavior toward
  `difficulty`/`category` — additive fields in a future minor version won't
  break an application built against 1.0.

## Failure behavior

A model response that doesn't conform to this contract (missing a section,
sections out of order, an empty narrative) is a **contract violation, not
a degraded-but-usable response**. The reference application's behavior —
throw and surface an error to the user rather than display partial or
malformed output — is the contract's required behavior, not an
implementation choice specific to `thought-organizer`. This is what
actually happened in practice already: see
`datasets/gold/gold_v1.2_lessons_learned.md`'s "Complete generation
failure" finding, where the app correctly surfaced an error instead of
showing broken output.

## What this contract deliberately does not cover

- **The model's internal output format** (currently delimited markers:
  `###NARRATIVE###`/`###BULLETS###`/`###ACTIONS###`) is not part of this
  contract and can change freely between model releases without a
  major-version bump, as long as the parsed result still satisfies the
  shape and guarantees above. See `training/ROADMAP.md`'s hard-won findings
  for why the internal format is what it is; that reasoning can evolve
  independently of this contract.
- **Maximum input/output length** is intentionally not fixed here yet — the
  current implementation's chunking behavior (`src/utils/tokenization.ts`)
  is an application-side concern, not a model guarantee. Worth adding to a
  future contract version if a model release needs to declare a hard limit.
- **Confidence/uncertainty fields** — not part of v1. `training/ROADMAP.md`'s
  v1.5 plan proposes a `confidence` field; that would be a new minor (or
  major, if required rather than optional) version of this contract, not
  a retroactive change to v1.

## Compatibility policy

| Change type | Version bump | Example |
|---|---|---|
| New optional field added to the response | Minor (1.0 → 1.1) | Adding an optional `confidence` field |
| A guarantee above changes or is removed | Major (1.x → 2.0) | Allowing an empty `narrative` |
| Internal model format change with no effect on the parsed shape | None | Changing the delimiter marker text |

An application declares which major version(s) it supports; a model
release declares which major version(s) it satisfies. `thought-organizer`
currently supports `1`.
