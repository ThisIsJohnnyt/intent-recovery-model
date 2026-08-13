# Controlled seed-17 typed-proposition representation comparison proposal

**Date:** 2026-08-13  
**Author:** ChatGPT  
**Status:** Draft proposal for Claude's independent review; not authorized for implementation or execution  
**Governing audit:** `controlled_seed17_rbr17c_static_mechanism_audit_chatgpt.md` and its 85-row map  
**Primary variable:** target/prompt representation only  
**Compute authorized:** None  

## 1. Proposed decision

Compare the current flat v2 output representation against one typed-plan-augmented representation while
holding the semantic corpus, token-level training objective, model capacity, optimizer, step budget, seed,
checkpoint rule, decoding parameters, and frozen evaluations constant.

This proposal chooses **representation**, not an auxiliary objective. It adds no classification head, loss
term, loss weight, sampling weight, corpus record, target correction, or model-capacity change. The ordinary
sequence cross-entropy objective remains unchanged. Any later auxiliary-objective study is a different
milestone.

This document does not authorize implementation, manual 78-plan authoring, automated or model-generated
targets, training, inference, benchmark execution, semantic scoring, checkpoint selection, seed 73, corpus
edits, commit, or push. Section 13 lists possible later milestones; each requires its own authorization.

## 2. Why this is the next discriminating comparison

The static audit found failures despite exact or near-isomorphic comparator support:

- protected 06: local resolution plus later ambiguity;
- protected 10: buried task and supported facts realized inconsistently across fields;
- protected 11 and sdi2-02: one role or qualifier survives while another drifts or disappears;
- protected 16: unresolved-reference marking is inconsistent across fields;
- sdi2-07: semantic duplicates are emitted as separate propositions;
- sdi2-08: an exact eight-source-task B7/A8 target exists but does not transfer;
- sdi2-10: proposition states, roles, two action identities, and field counts collapse under composition.

Broad corpus addition is therefore stopped. Capacity remains deferred because the current representation
does not explicitly expose the distinctions whose loss is being measured.

## 3. Hypothesis and falsifier

**Hypothesis:** Explicit proposition IDs and typed state/role/qualifier/identity/field obligations improve
cross-field semantic preservation under the same model, data, objective, and training schedule.

**Falsifier:** The treatment fails any protected non-regression gate, fails to improve the predeclared atomic
mechanisms, or cannot reliably emit a structurally valid typed plan within the frozen token budget. A lower
training or validation loss does not support the hypothesis and cannot select an outcome.

One same-seed comparison can reject this representation candidate. It cannot establish general causal
superiority or authorize seed 73.

## 4. Arms and the single changed variable

| Dimension | Comparator | Treatment |
|---|---|---|
| Semantic records | frozen 78-record comparator lineage | same 78 records, same order and split membership |
| Prompt task | current v2 instruction and markers | same task plus requirement to emit the typed plan before the unchanged v2 fields |
| Target | current v2 target | typed plan followed by byte-identical current v2 target |
| Objective | existing token-level seq2seq cross-entropy | identical |
| Model/base revision | current pinned FLAN-T5-base revision | identical |
| Capacity/tokenizer | current | identical |
| Seed/data seed | 17/17 | 17/17 |
| Step budget | 720 | 720 |
| Batch/LR/weight decay | 4 / `3e-4` / `0.01` | identical |
| Checkpoint selection | final step only; no best-loss selection | identical |
| Generation | current deterministic generation settings and maximum new-token policy | identical numeric settings; representation adapter is treatment-specific |
| Semantic evaluator | frozen Protected-16 and Acceptance-10 | identical after fail-closed treatment adaptation |

The treatment's prompt/target serialization and its inverse parser are one indivisible representation
variable. No other executable or data difference is allowed.

## 5. Typed-plan contract

### 5.1 Canonical serialization

The treatment target has this order:

```text
###PROPOSITIONS###
###PROP### p01
###STATE### task
###PREDICATE### return
###ROLES### actor=writer; object=borrowed telescope
###QUALIFIERS### destination=observatory desk; deadline=before Monday evening
###COREFERENCE### none
###DUPLICATE_OF### none
###FIELDS### narrative,bullet,action
[zero or more further propositions]
###RENDERED_OUTPUT###
###NARRATIVE### ...
###BULLETS###
###BULLET### ...
###ACTIONS###
###ACTION### ...
```

This is synthetic schema-only content. It is not drawn from, paraphrased from, or intended to resemble any
Protected-16 or Acceptance-10 item, and it must never be treated as an additional corpus record.

The portion after `###RENDERED_OUTPUT###` must be byte-identical to that record's existing v2 target. It is
not re-authored or paraphrased. The plan is additional representation, not a semantic target change.

### 5.2 Proposition schema

Each proposition has exactly these keys:

| Key | Allowed value |
|---|---|
| `id` | `p01`, `p02`, ... in source order, no gaps or duplicates |
| `state` | `fact`, `question`, `fragment`, `tentative_idea`, or `task` |
| `predicate` | normalized source-supported predicate; no inferred repair or answer |
| `roles` | sorted `role=value` pairs from `speaker`, `actor`, `recipient`, `object`, `possessor`, `experiencer`, or `candidate_set`; `none` allowed |
| `qualifiers` | sorted `type=value` pairs from `time`, `deadline`, `destination`, `trigger`, `condition`, `quantity`, `purpose`, or `object_modifier`; `none` allowed |
| `coreference` | `resolved:<referent>`, `unresolved:<candidate_set>`, `dangling`, or `none` |
| `duplicate_of` | earlier proposition ID or `none` |
| `fields` | ordered nonempty subset of `narrative,bullet,action`; `action` permitted only for `task` |

No field may contain a free-form explanation, chain of thought, confidence score, inferred cause, supplied
referent, or invented action. The plan records source-grounded structure only.

### 5.3 Mechanism invariants

- Protected 06 must use distinct propositions/coreference values for the locally resolved earlier pronoun
  and the later unresolved candidate set.
- Questions, fragments, tentative ideas, and facts must never include `action` in `fields`.
- Every action target must map to exactly one canonical task proposition; two actions may share qualifiers
  without sharing IDs.
- A semantic restatement points `duplicate_of` to the first proposition and has no independent field
  obligation unless source policy requires its surface mention.
- Bullet grouping and action identity are separate: sdi2-08 may map eight task IDs to seven bullets and
  eight actions.
- Every material qualifier required by the frozen rubric must remain bound to its proposition in every
  required field.

## 6. Deterministic authoring and validation

If implementation is later authorized, all 78 treatment plans must be authored and independently reviewed
before any compute. The existing narrative, bullet, and action strings remain immutable.

The static builder must fail closed unless:

1. record order, inputs, output objects, and split membership match the frozen 78-record comparator;
2. the rendered suffix equals the existing v2 target byte-for-byte;
3. proposition IDs are unique, ordered, and referenced validly;
4. enum, role, qualifier, duplicate, and field values validate;
5. non-task propositions never require actions;
6. each existing action has exactly one task proposition and each action-required proposition is realized;
7. every authored plan receives two independent semantic reviews with disagreements adjudicated before
   freezing;
8. protected-overlap analysis covers the plans as well as surface text; and
9. complete prompt and target token histograms prove no input or target truncation at the frozen 512-token
   limits and no generated plan+output can exceed the frozen generation budget.

If any record exceeds a frozen token limit, stop. Do not shorten, omit, compress, or selectively exclude
records after seeing benchmark behavior. A larger token budget would be a second changed variable and needs
a new proposal.

## 7. Treatment adapter and evaluation boundary

The treatment adapter must:

1. parse the typed plan with a dedicated fail-closed parser;
2. validate all schema and cross-field invariants;
3. require exactly one `###RENDERED_OUTPUT###` suffix;
4. extract that suffix without rewriting it;
5. pass the extracted bytes to the existing v2 parser and frozen evaluator.

Malformed plans, missing propositions, invalid references, plan/output contradictions, duplicate markers,
or invalid suffixes are treatment failures. The adapter may reject; it may not repair, infer, regenerate,
reorder, merge, or add content.

The comparator uses the existing v2 parser directly. This asymmetry is the declared representation
treatment, not constrained decoding or post-hoc semantic repair.

## 8. Frozen evaluation sets and leakage

Use the full existing Protected-16 and Acceptance-10 suites. Do not add plan annotations to benchmark
inputs, expose gold proposition tables at evaluation, or tune the schema after viewing outputs.

Before implementation, freeze benchmark-side **scoring rubrics** for typed-plan correctness without creating
gold training examples from protected wording. The rubric describes atomic states/roles/qualifiers and field
obligations; it must not be included in the training corpus or prompt.

The seven failed-treatment delta records remain excluded. In particular, delta 2/3 are quarantined for
protected 06 and delta 7 for protected 16. The representation authoring must not use protected outputs as
templates. Pre-existing comparator analogues remain disclosed baseline exposure.

## 9. Atomic metrics

### 9.1 Representation validity

- typed-plan parse rate: 26/26 required;
- v2 suffix parse rate: 26/26 required;
- plan/output consistency: 26/26 required;
- no truncation, duplicate IDs, invalid references, or illegal action field on non-task state.

Any failure is a treatment gate failure regardless of semantic scores.

### 9.2 Predeclared mechanism endpoints

| Mechanism | Cases | Required treatment result |
|---|---|---|
| resolved versus unresolved coreference | 06, 08, 16 | correct state/referent distinctions in plan and rendered fields; no protected regression |
| question/fragment/task separation | 09 | question and fragment remain non-actions; checking task remains the only action |
| cross-field proposition realization | 10 | shipping task in all required fields and final-scene fact in narrative/bullets |
| role/experiencer/chronology binding | 11 | writer emotion retained, no object-emotion drift, no invented completion chronology |
| qualifier binding | sdi2-02 | deadline and destination survive in bullet/action |
| semantic identity | sdi2-07 | exactly one canonical task, B1/A1, no placeholder proposition |
| bullet budget versus action identity | sdi2-08 | B<=7/A8 with eight distinct task IDs |
| dense compositional binding | sdi2-10 | B6/A2, correct roles/states/deadline, no promotion or merge |

All ordinary protected and acceptance checks remain governing; this table does not reduce them.

## 10. Outcome matrix

The six established aggregate semantic gates remain necessary but are not sufficient. Treatment must also
pass all representation-validity gates and the atomic endpoints above.

| Outcome | Treatment | Comparator | Disposition |
|---|---|---|---|
| TR17-A | all representation, atomic, protected, and acceptance gates pass | fails one or more corresponding semantic/atomic gates | discriminating success; stop and propose independent replication only |
| TR17-B | both pass all semantic/atomic gates; treatment passes representation validity | parity/non-discriminating; stop, no capacity claim |
| TR17-C | treatment fails any gate; comparator fails any | representation does not clear; stop and diagnose only |
| TR17-D | treatment fails any gate; comparator passes all | negative/reversed result; reject representation candidate |

No aggregate average, favorable subgroup, loss value, or parser-only gain can override a failed case gate.
Seed 73 is not authorized by any outcome.

## 11. Variables frozen for a later execution design

Any later execution proposal must re-pin exact paths and fingerprints, but it may not change:

- the 78-record semantic corpus or frozen split membership (72 train / 6 validation);
- base model and revision, tokenizer, capacity, device policy, dependencies, and import closure;
- seed/data seed 17;
- 720 optimizer steps, batch sizes, learning rate, weight decay, scheduler, precision, and collator;
- token-level objective and uniform record sampling;
- final-step checkpoint rule and isolated output directories;
- numeric decoding parameters, including repetition penalty and generation limit;
- Protected-16, Acceptance-10, their contracts, parser/scorer semantics, or case order.

Because the treatment target is longer, equal optimizer steps—not equal target tokens—is the predeclared
training-budget control. Target-token totals must be reported as an exposure difference inherent in the
representation, not “corrected” with loss weights or schedule changes.

## 12. Hard stops before compute

Stop and return to Johnny if:

- Claude finds a material design or evidence disagreement;
- any typed plan changes existing semantic output text;
- a plan cannot be authored without subjective invented structure;
- inter-reviewer plan agreement is incomplete;
- any prompt, target, or generated output would truncate under frozen limits;
- implementation would require an auxiliary loss, capacity increase, schedule/token-budget adjustment,
  constrained decoding, generative repair, corpus correction, or benchmark change;
- protected leakage cannot be controlled;
- the comparator cannot be freshly run under the same pinned environment;
- more than the declared representation variable differs.

## 13. Required milestones after this proposal

Approval of this proposal alone authorizes neither compute nor milestone 1's manual plan authoring or
implementation. The following are possible later milestones, each separately gated:

1. static schema, 78-plan authoring, independent review, token feasibility, parser, and dry-run package;
2. frozen execution manifest and fingerprints;
3. Johnny's explicit compute authorization;
4. raw two-arm execution;
5. independent semantic scoring and outcome adjudication;
6. only after TR17-A, a separately designed replication decision.

Nothing is committed or pushed without Johnny's hand-typed instruction.

## 14. Current disposition

- Static RBR17-C audit: independently verified, held uncommitted by Johnny.
- This representation-only comparison: draft proposal awaiting independent review.
- Auxiliary objective, capacity, corpus correction, implementation, compute, seed 73, checkpoint action,
  commit, and push: not authorized.
