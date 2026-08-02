# Real-Data Annotation and Adjudication Guide

## Status

**Proposed, revision 2, for joint review. No real note may be annotated until the governance specification is approved and implemented.**

## Objective

Create an expected intent-recovery output that preserves exactly what the writer's note supports while reducing the effort needed to understand it.

Annotation is not generic summarization, diagnosis, advice, emotional interpretation, or task planning.

## Required record shape

Real records retain the existing dataset shape:

```json
{
  "input": "<de-identified real note>",
  "output": {
    "narrative": "<coherent recovery>",
    "bullets": ["<supported idea>"],
    "action_items": ["<explicit supported task>"]
  },
  "difficulty": "easy|medium|hard|expert",
  "category": "<existing capability label>"
}
```

Only `input` and `output` are model-facing. Governance, provenance, and rubric metadata remain in private sidecars.

## Annotation sequence

### 1. Freeze the de-identified source

Confirm consent, de-identification approval, active status, and source fingerprint. Do not annotate from the raw original.

### 2. Build a fragment inventory

Before drafting an output, list only what the source supports:

- explicit facts and observations;
- explicit actions and their qualifiers;
- unresolved questions and every stated alternative;
- uncertainty markers;
- tentative ideas;
- incomplete or dangling fragments;
- attribution relationships;
- temporal or causal relationships;
- repeated references to the same task; and
- emotional language explicitly stated by the writer.

The inventory is private rubric material, not model input.

### 3. Mark prohibited inferences

Record likely but unsupported completions the model must avoid, including:

- assigning an unclear pronoun or referent;
- treating a later observation as an answer;
- converting an idea, concern, or fragment into an action;
- inventing an emotional reaction;
- inventing a cause, resolution, recipient, deadline, or repair task;
- treating discourse markers as semantic content; and
- splitting one explicitly unified task into several tasks.

### 4. Draft the expected output

Draft all three fields from the same source inventory. Cross-field consistency is mandatory.

### 5. Perform an independent review

The reviewer reads the de-identified input before seeing the draft, creates their own fragment inventory, and then compares it with the annotation.

### 6. Adjudicate

Disagreements are resolved against the source text, not stylistic preference. If two meanings remain equally supported, the expected output must preserve the ambiguity. If safe agreement is impossible, exclude the record.

## Narrative rules

The narrative should:

- reconnect supported fragments into readable prose;
- preserve the writer's meaning, tone, uncertainty, and level of commitment;
- preserve supported chronology and causality;
- keep separate topics separate;
- keep explicitly unified tasks unified;
- identify incomplete thoughts as incomplete without completing them; and
- stop at the final source-supported clause.

The narrative must not:

- explain why the writer feels something unless the source states why;
- add advice, reassurance, interpretation, diagnosis, or commentary;
- resolve an open question;
- lean toward one alternative;
- assign an unclear referent;
- turn a return phrase such as "back to…" into subject matter; or
- add a closing sentence merely to make the output sound complete.

## Bullet rules

- Use one bullet per distinct source-supported idea.
- Preserve qualifiers such as names, deadlines, sequence, uncertainty, and scope.
- Do not merge unrelated ideas merely to reduce bullet count.
- Do not split one coherent action merely to increase bullet count.
- Do not repeat the same task after deduplication.
- Do not include unsupported explanations or headings as bullets.

**The bullet count is source-determined.** A one-idea note receives one bullet. Padding to satisfy a nominal minimum is prohibited because it creates unsupported structure or content. Before the pilot, any existing prompt or documentation requiring 3–7 bullets must be revised or explicitly reconciled with this rule. Seven remains a practical maximum for a single record; notes requiring more should normally be narrowed before acceptance.

### Cross-repository prompt-contract dependency

The bullet rule exists in two deployed prompt surfaces:

- `training/prepare_data.py` in the intent-recovery-model repository; and
- `src/services/noteOrganizer.ts` in the separately maintained thought-organizer-app repository.

The training template states that it mirrors the production template exactly. Therefore neither side may be changed alone. The bullet-contract change is a tracked cross-repository action and must be performed in the appropriate repository scopes.

Before the pilot:

1. both repositories adopt the same prompt-contract version identifier;
2. both replace the 3–7 minimum with source-determined wording;
3. a fixed dummy note is rendered through both prompt builders;
4. the complete rendered prompts must match byte-for-byte and have the same SHA-256 hash; and
5. the paired commits and verification hash are recorded in the readiness review.

Until both repositories are synchronized, no real-data pilot or new training run under the revised contract is authorized.

## Action-item rules

Include only concrete actions explicitly supported by the source.

Preserve:

- actor or recipient;
- object;
- deadline or timing;
- sequence and prerequisites;
- negation;
- scope; and
- whether repeated mentions refer to one task.

Do not promote:

- tentative ideas;
- observations;
- emotions;
- open questions, unless the source explicitly says to investigate or ask;
- dangling fragments whose intended action is unknown; or
- plausible next steps invented by the annotator.

If no explicit action exists, `action_items` is empty.

## Uncertainty and open questions

- Preserve every stated alternative.
- State clearly that the answer remains unresolved.
- Keep later observations separate unless the source explicitly connects them as evidence or resolution.
- Do not rewrite an either/or question into a tautology.
- Do not introduce a checking action unless the source asks for one.

## Dangling references

Preserve the reminder or clause without guessing who or what the referent means. The output stops after the last supported clause. Phrases such as "both are unresolved," "they are unrelated," or an invented description of the referents are unsupported unless present in the source.

## Attribution

Track each statement and action to the correct person or entity across narrative, bullets, and actions. Pronouns are resolved only when the source makes resolution unambiguous. A correct action field does not repair an incorrect narrative attribution; strict scoring considers the full output.

## Difficulty labels

Difficulty describes the recovery operation, not the writer.

- `easy`: one or two ideas with direct wording and low attribution risk;
- `medium`: several fragments, interruptions, repeated tasks, or one unresolved relationship;
- `hard`: multiple interacting fragments, attribution ambiguity, nested boundaries, or several strict failure opportunities; and
- `expert`: unusually dense interaction among several recovery mechanisms where correct annotation requires resolving multiple boundaries while preserving ambiguity, attribution, and qualifiers. Use sparingly and only when `hard` would materially understate the annotation burden.

Difficulty is assigned only after the expected output and rubric are stable.

## Category labels

Use the existing capability taxonomy when a clear primary lesson exists. Do not create labels based on diagnosis, identity, contributor type, or emotional state. If no existing category fits, mark the record for taxonomy review rather than improvising a new label during annotation.

## Private rubric sidecar

Each record receives a private rubric entry in `datasets/private/real_data_rubrics.jsonl`, keyed by `record_id`:

```json
{
  "record_id": "rv_<random-id>",
  "must_preserve": [],
  "must_not_infer": [],
  "explicit_actions": [],
  "unresolved_questions": [],
  "attribution_map": [],
  "allowed_surface_variants": [],
  "capability_checks": [],
  "adjudication_notes": "",
  "rubric_status": "adjudicated",
  "rubric_fingerprint": "sha256:<fingerprint>"
}
```

Rubric text should use de-identified terms and avoid repeating more source content than needed.

## Quality checklist

A record is annotation-ready only when all answers are yes:

- Is the source consented and de-identified?
- Does the fragment inventory cover every supported idea?
- Does the expected output preserve all explicit actions and qualifiers?
- Are uncertainty and dangling references still unresolved where required?
- Are all fields mutually consistent?
- Is every action source-supported?
- Does the output stop without commentary?
- Is the bullet count source-determined rather than padded?
- Can strict failure conditions be scored from the private rubric?
- Did an independent reviewer agree or complete adjudication?

## Alignment status

**ChatGPT revision 2 for Claude verification.**
