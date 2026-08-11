# Regression-Balanced Repair — Design-Only Specification

**Date:** 2026-08-11  
**Author:** ChatGPT  
**Evidence commit:** `43f4fc41264469ac2848340c8bea8e216dba8368` on `main`  
**Governing outcome:** `C17-C`, final and verified  
**Governing diagnostic:** `training/controlled_seed17_contrastive_replay_diagnostic_postmortem_chatgpt.md`, SHA-256 `33e349850b9e61f68eda59ff53951981408ccf388cfc19b067d4f234a12e7632`  
**Status:** Design-only draft awaiting Claude's independent review.  
**Non-authorization:** This document does not authorize final example wording, JSONL creation, corpus mutation or derivation, split generation, training, inference, seed 73, checkpoint work, benchmark/rubric/contract changes, export, deployment, activation, cleanup, commit, or push.

## 1. Decision proposed

Advance a static, regression-balanced repair design organized into four independently reviewable teaching groups:

1. attribution and ambiguity;
2. action completeness;
3. source-state preservation; and
4. structural behavior.

The design is not a request to append another broad curriculum to the failed 82-record treatment. A later implementation proposal, if separately authorized, should use the committed 78-record comparator corpus as the default reference baseline because it preserves the effective two-task repair while avoiding automatic inheritance of the failed treatment's bundled target revisions.

The four existing AT-C attribution records may be proposed for exact reuse only after a committed-byte and semantic audit. The P2-009/P2-010 bullet revisions from the failed treatment are **not** presumed to carry forward. Their comparator targets remain the default until a separately reviewed field-role group demonstrates why any target revision is necessary.

## 2. Evidence this design must explain

The failed treatment produced a mixed exchange rather than a general improvement:

- protected gains over comparator: `{02, 06}`;
- protected regressions versus comparator: `{10, 16}`;
- acceptance regressions versus comparator: `{sdi2-02, sdi2-09}`;
- identical acceptance count-rule failures in both arms: `{sdi2-07, sdi2-08, sdi2-10}`;
- shared protected residual failures: `{08, 09, 11}`;
- protected 13's two-task repair preserved in both arms.

Protected 06 is aligned with the AT-C attribution intervention, but a single paired run cannot establish causation. Any future design must preserve that possible gain without weakening task survival, qualifiers, incomplete thoughts, dangling references, or structural counts.

## 3. Governing semantic invariants

Every later candidate record must satisfy all applicable invariants. These are field-specific; presence in narrative does not excuse omission or corruption elsewhere.

### 3.1 Attribution and ambiguity

- Resolve a reference only when source evidence supports a unique referent.
- Preserve every explicitly stated or genuinely unresolved alternative.
- Treat separate references in one note independently.
- Do not use name position, recency, grammatical object position, gender alone, or an always-ambiguous rule as a shortcut.
- A correct earlier resolution must not force resolution of a later ambiguity.
- No field may contradict another field's attribution or uncertainty state.

### 3.2 Action completeness

For every explicit task, `action_items` must preserve the complete supported task frame:

- action predicate;
- object;
- recipient or beneficiary;
- destination;
- deadline or temporal constraint;
- condition or trigger;
- quantity or cardinality; and
- source-supported purpose when it constrains task identity.

Each explicit task appears exactly once unless the source genuinely contains separate tasks. A qualifier appearing only in narrative is not sufficient. Background observations, tentative ideas, and open questions must not become actions.

### 3.3 Source-state preservation

- Incomplete thoughts remain incomplete; do not invent what is missing.
- Open questions remain questions; do not answer them directly or indirectly.
- Dangling references remain unresolved; do not invent identities, relationships, plurality, ownership, or expected answers.
- Tentative ideas remain tentative and are not promoted to actions.
- Do not add unsupported evaluation such as “good idea,” advice, causality, chronology, or confidence.
- A supported checking or clarification task may survive without converting the underlying uncertainty into an answer.

### 3.4 Structural behavior

- Repeated reminders for one task deduplicate to one semantic item and one action.
- Distinct tasks remain distinct actions, even when the bullet ceiling requires selective or grouped bullets.
- Bullet ceilings never justify dropping an action.
- Dense mixed-content notes preserve every required semantic idea while respecting exact structural counts.
- Structural compliance never excuses semantic merging, loss, or invention.

## 4. Reference baseline and change discipline

### 4.1 Default reference baseline

Any later implementation proposal should begin its record-level manifest from the committed 78-record comparator candidate, not from the failed 82-record treatment, unless Johnny separately approves a different lineage after review.

Reasons:

- it avoids silently retaining the unisolated P2-009/P2-010 revisions;
- it makes every proposed repair an explicit, reviewable delta;
- it prevents the failed treatment from becoming an accidental new baseline merely because it was most recent.

This is a design recommendation, not authorization to create a candidate.

### 4.2 Preserve list

The following must remain unchanged in any later proposal unless a separate defect is proven and authorized:

- the 66-record R2 parent prefix;
- the two historical `two_unrelated_tasks` repair records;
- frozen validation membership and split policy;
- protected and acceptance benchmarks;
- scoring dimensions, capability checks, thresholds, and failure-label vocabulary;
- prompt contract and parser;
- the committed `C17-C` evidence and outcome records.

### 4.3 No presumed carry-forward

- Do not automatically carry forward the P2-009/P2-010 treatment revisions.
- Do not automatically append all four AT-C records without exact audit.
- Do not add paraphrase volume merely to increase category counts.
- Do not reuse benchmark wording, entities, clause order, quantities, deadlines, or distinctive combinations.

## 5. Four reviewable teaching groups

The following are abstract semantic templates, not final examples. Bracketed elements are roles, not wording. No template may be converted to JSONL without separate authorization.

### Group A — Attribution and ambiguity

**Purpose:** preserve the likely protected-06 gain while preventing positional, gender-only, recency, or always-ambiguous shortcuts.

**Maximum later records:** four, preferably exact audited reuse of AT-C1 through AT-C4 rather than new additions.

| Template | Required contrast | Required target behavior |
|---|---|---|
| A1 | Earlier reference uniquely resolvable to the second-mentioned person | Resolve it consistently; preserve all unrelated content; do not create a background-only bullet or action. |
| A2 | Same surface family, but earlier reference genuinely unresolved | Preserve both candidates in every field; do not invent a clarification task unless explicitly requested. |
| A3 | Earlier reference resolvable; later reference explicitly ambiguous | Resolve the earlier reference and preserve the later alternatives independently; retain the requested clarification action. |
| A4 | Order-swapped control for A1 | Resolve the same semantic actor despite reversed name order; keep field shape semantically matched to A1. |

**Balance gates:** resolve/preserve outcomes both present; correct referent occupies different name positions; no single lexical cue solves all four; A1/A4 differ enough to avoid duplication while remaining a true semantic control.

### Group B — Action completeness

**Purpose:** teach that selective bullets never weaken complete action transfer.

**Maximum later records:** four. Existing corpus coverage must be audited first; reuse or target-only correction is preferred over adding a record when an exact clean teaching case already exists.

| Template | Qualifier coverage | Required contrast |
|---|---|---|
| B1 | deadline + destination | One explicit task; both qualifiers must appear in its action. A nearby observation remains non-actionable. |
| B2 | recipient + object | Two named people or organizations; the action retains who receives what without role reassignment. |
| B3 | condition + quantity | One task gated by an event/condition and a specified count; neither qualifier may disappear under summarization. |
| B4 | dense two-task control | Two actions with different qualifier types; both remain separate, complete, and correctly scoped despite intervening non-task content. |

**Negative pressure required across the group:** at least one matched non-action clause per record family, varying among observation, tentative idea, and unresolved question. Correct behavior is complete actions plus no promotion of the non-action clause.

### Group C — Source-state preservation

**Purpose:** prevent incomplete, open, or dangling content from being completed, answered, linked, evaluated, or promoted.

**Maximum later records:** four.

| Template | Source state | Required target behavior |
|---|---|---|
| C1 | Incomplete thought interrupted by a separate explicit task | Keep the fragment incomplete; retain the task exactly once; do not connect their entities. |
| C2 | Open question plus a supported checking task | Preserve the question; retain the check; do not convert either alternative into fact or action. |
| C3 | Explicit task containing dangling object/owner/arrival references | Preserve all unresolved references and every supported condition; add no identity, plurality, relationship, or opinion. |
| C4 | Tentative idea plus unrelated observation or task | Preserve tentativeness; do not promote the idea; do not add advice, causality, or evaluation. |

**Balance gates:** at least one case with an action and one without; uncertainty appears in different clause positions; no recurring phrase such as “it remains unclear” becomes the only cue; actions and uncertainties use different entity sets to expose accidental merging.

### Group D — Structural behavior

**Purpose:** teach structural counts without sacrificing semantic identity.

**Maximum later records:** four.

| Template | Structural boundary | Required target behavior |
|---|---|---|
| D1 | One task restated twice | Exactly one bullet and one complete action; retain all qualifiers; no duplicate reservation/task identity. |
| D2 | Eight distinct explicit tasks under a seven-bullet ceiling | At most seven bullets but exactly eight separate complete actions; no loss, merge, reassignment, or invention. |
| D3 | Six mixed semantic ideas with exactly two explicit tasks | Exactly six semantically faithful bullets and two separate complete actions; tentative/question/observation content remains non-actionable. |
| D4 | Two similar but distinct tasks | Preserve two actions despite shared verbs/entities; demonstrate the difference between legitimate separation and duplicate fragmentation. |

**Structural gates:** counts computed from parsed markers; every action independently compared with its source task frame; bullet grouping justified explicitly; no semantic pass granted merely because counts match.

## 6. Size ceiling and reuse-first rule

A later implementation may propose at most twelve genuinely new records across Groups B–D and at most four audited reused attribution records in Group A. Twelve is a ceiling, not a target.

Before authoring anything, the implementation proposal must audit the 78-record baseline for each template and classify existing coverage as:

- clean reusable coverage;
- near coverage needing no change;
- defective coverage requiring a separately justified target-only correction; or
- genuine missing coverage.

Only genuine missing coverage may justify a new record. A target-only correction counts as a record-level change and must identify the defect, changed fields, expected benefit, and regression risk.

## 7. Mechanism isolation

The prior treatment bundled attribution additions with field-role revisions. A later proposal must keep four independent change groups in its manifest even if Johnny eventually authorizes a combined candidate.

For every changed record, the manifest must name exactly one primary mechanism: `A_attribution`, `B_action_completeness`, `C_source_state`, or `D_structural`. Secondary protections may be listed, but no record may be justified as teaching “everything.”

Any later execution design must decide before compute whether mechanism groups are screened separately, incrementally, or only as a combined package. That decision, step budget, seeds, controls, and outcome matrix are outside this design and require a separate reviewed execution specification.

## 8. Benchmark-leakage and shortcut controls

Before exact wording is approved, static review must demonstrate:

- no exact or near input overlap with any protected or acceptance probe;
- no reuse of distinctive benchmark entity combinations, task objects, deadlines, quantities, destinations, or clause sequences;
- no template solvable by a single position, gender, punctuation, marker-count, or stock uncertainty phrase;
- matched pairs vary surface form without changing the governed semantic distinction;
- no benchmark output is used as a target-writing scaffold;
- collision checks cover the parent, historical proposal, all proposed records, both benchmarks, and all prior rejected candidates.

Similarity thresholds and normalization rules must be specified before the exact records are written, not selected after collisions are observed.

## 9. Record-level review schema for a later proposal

Every proposed record or target revision must include a human-readable manifest entry with:

- stable proposal-local ID;
- primary mechanism group;
- source-state inventory;
- explicit task-frame inventory, including every qualifier;
- required narrative content;
- required bullet roles and count rationale;
- required action items and exact semantic frames;
- forbidden inferences, promotions, merges, and omissions;
- paired/control relationship, if any;
- expected protected/acceptance behavior affected;
- named regression risks;
- intended split membership;
- near-duplicate and leakage evidence; and
- independent reviewer disposition.

No record advances on aggregate approval alone.

## 10. Static gates before JSONL authorization

A later implementation request must fail closed unless all of the following pass:

1. The 78-record baseline and every preserved record are fingerprint-pinned.
2. Existing coverage audit justifies every proposed addition or correction.
3. The total delta stays within the size ceiling.
4. Every record has exactly one primary mechanism.
5. Group A passes resolve/preserve/order balance checks.
6. Group B preserves complete action frames field-by-field.
7. Group C adds no answer, relationship, plurality, evaluation, cause, chronology, or unsupported task.
8. Group D satisfies both semantic identity and parsed count requirements.
9. The two protected-13 repair records remain unchanged.
10. P2-009/P2-010 treatment revisions are excluded unless separately re-justified.
11. Validation membership and split policy are unchanged.
12. Benchmark, rubric, prompt, parser, and scoring rules are unchanged.
13. Near-duplicate, leakage, schema, enum, and formatting checks pass.
14. Exact expected change paths, record counts, fingerprints, and generated artifacts are declared before implementation.
15. ChatGPT and Claude independently agree on every record-level disposition.

Failure of any gate returns the work to design. It does not authorize implementation or compute as a diagnostic shortcut.

## 11. Evaluation protections for a later execution design

This document does not define or authorize an experiment, but any later execution proposal must explicitly protect at least:

- protected 06 attribution/ambiguity repair;
- protected 13 two-task repair;
- protected 08 unresolved-source and drying-observation separation;
- protected 09 incomplete-thought preservation;
- protected 10 buried-task survival;
- protected 11 deadline retention;
- protected 16 dangling-reference preservation;
- acceptance `sdi2-02` destination retention;
- acceptance `sdi2-07` deduplication;
- acceptance `sdi2-08` eight-action survival under the bullet ceiling;
- acceptance `sdi2-09` condition and unresolved-reference preservation; and
- acceptance `sdi2-10` six-idea/two-action separation.

The complete frozen benchmark sets remain governing; this list is a diagnostic emphasis list, not a reduced evaluation subset or permission to weaken gates.

## 12. Expected benefits and principal risks

| Group | Expected benefit | Principal risk | Required protection |
|---|---|---|---|
| A | Retain evidence-based attribution and protected-06 behavior | positional, gender-only, recency, or always-ambiguous shortcut | balanced resolve/preserve/order controls |
| B | Preserve complete tasks and qualifiers in actions | promoting nearby non-task content or duplicating tasks | explicit task-frame inventories and negative-pressure clauses |
| C | Preserve incomplete/open/dangling states | overcorrecting by making resolvable content ambiguous | mix resolvable and intentionally unresolved cases across groups |
| D | Meet count rules without semantic loss | optimizing marker counts while merging/dropping meaning | semantic identity checks before count checks |

Cross-group risk is curriculum interference. The manifest and any later execution design must keep group membership explicit so a combined failure cannot again be described only as a broad corpus effect.

## 13. Requested independent review

Claude should independently determine:

1. whether the 78-record comparator is the defensible default reference baseline;
2. whether exact audited reuse of AT-C1–AT-C4 is preferable to new attribution records;
3. whether excluding P2-009/P2-010 treatment revisions by default follows from the evidence;
4. whether the four abstract groups cover the verified failures without benchmark mimicry;
5. whether the maximum of twelve new records plus four reused attribution records is appropriately bounded;
6. whether the action-frame and source-state invariants are complete and non-conflicting;
7. whether mechanism isolation and static gates are strong enough to prevent another bundled, uninterpretable change; and
8. whether any part of the document silently crosses into record authoring, corpus implementation, or compute authorization.

Any material disagreement is work-stopping and returns to Johnny with both positions and evidence.

## 14. Decision after review

If Claude agrees, the design becomes ready for Johnny's decision on a **separate implementation-proposal milestone**. That later milestone would audit baseline coverage and draft record-level manifests and exact wording for review. It would still not authorize corpus derivation or training.

**Disposition:** REGRESSION-BALANCED REPAIR DESIGN DRAFTED — FOUR MECHANISM GROUPS DEFINED — NO JSONL OR TRAINING CANDIDATE CREATED — AWAITING CLAUDE INDEPENDENT REVIEW.
