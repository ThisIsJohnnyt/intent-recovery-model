# RBR17-C bounded no-compute mechanism and representation audit design

**Date:** 2026-08-13  
**Author:** ChatGPT  
**Status:** Draft for Claude's independent review; not approved for execution or commit  
**Compute authorized:** None  
**Reference lineage:** the 78-record `gold_v1.2.2_phase2_derived_candidate.jsonl` comparator  
**Treatment delta:** the seven records in `regression_balanced_repair_proposal.jsonl`  

## 1. Decision boundary

This document specifies a bounded, static audit. It does not authorize training, inference, checkpoint
selection, seed 73, benchmark execution, corpus mutation, dataset access, promotion, commit, or push.

The 78-record comparator remains the reference lineage. The failed 85-record treatment is evidence, not a
replacement baseline. Its seven added records may be inspected one by one, but no record is presumed fit
to carry forward.

The audit may read only already-committed local artifacts named in section 2. It may quote existing inputs,
targets, accepted outputs, and rubric results. It must not invoke a model, rebuild a split, regenerate a
corpus, or rerun scoring. Any future experiment requires a new design and separate written authorization.

## 2. Frozen evidence set and precedence

Primary evidence, in descending order of authority:

1. `controlled_seed17_regression_balanced_repair_run/{comparator,treatment}/` accepted protected and
   acceptance JSON result files;
2. the frozen benchmark JSONL files and `report_benchmark.py` scoring semantics;
3. the 78-record comparator, seven-record proposal, 85-record candidate, derivation report, split
   comparison, record manifest, frozen execution manifest, and fingerprints;
4. `controlled_seed17_regression_balanced_repair_outcome.md` and the committed RBR17-C postmortem.

If prose conflicts with accepted JSON, the JSON plus the scorer governs. If a target paraphrase in this
audit cannot be traced byte-for-byte to a corpus record, it must be corrected or marked unresolved. No
claim of causal effect may be made from one same-seed A/B outcome.

## 3. Required audit artifacts

The completed static audit must produce these reviewable files:

| Artifact | Required contents |
|---|---|
| Atomic failure ledger | One row per failed atomic capability in the ten-case union, not one row per evaluator label |
| Record-to-mechanism map | Exactly 85 rows: 78 comparator rows plus seven separately marked treatment-delta rows |
| Conflict map | Evidence for compatible, competing, or unresolved supervision across state, role, qualifier, deduplication, bullet budget, and action cardinality |
| Design comparison | Corpus/contrast, representation/objective, capacity, constrained decoding, and deterministic post-validation compared without execution |
| Decision register | Predeclared gates selecting a later ablation, representation change, capacity comparison, deterministic validation, or stop |
| Leakage register | Record-level analogue and wording-overlap controls, including protected 06 |

Every row must carry a source path and stable locator: benchmark ID, corpus record hash or manifest ID, and
field name. Category labels alone are insufficient evidence.

## 4. Atomic failure ledger: frozen ten-case seed

The ten cases failing in at least one final arm are `06`, `08`, `09`, `10`, `11`, `16`, `sdi2-02`,
`sdi2-07`, `sdi2-08`, and `sdi2-10`. The table below freezes the initial decomposition that the completed
ledger must expand into one row per false atomic check or independently visible defect.

| Case | Comparator evidence | Treatment evidence | Atomic mechanism(s), not coarse label | Audit question |
|---|---|---|---|---|
| 06 | Ambiguity preserved, but attribution check false | Same | local pronoun resolution; explicit ambiguity preservation; speaker/actor binding | Does one target teach both a resolvable pronoun and an unresolved later referent without collapsing them? |
| 08 | Question retained but invented a dry-weather causal account | Avoided that cause, yet malformed the window-versus-plant alternative and detached “it” | alternative-set preservation; later-observation state; causal non-inference; referent binding | Is the conflict state representation, role binding, or surface decoding? |
| 09 | Preserved question, fragment, and checking task | Converted unresolved send-vs-save question into a send action and rewrote the volunteer fragment | question-versus-task state; incomplete-fragment state; unsupported action promotion | Did added attribution examples increase a general imperative prior? |
| 10 | Shipping-label task absent from actions; supported final-scene observation dropped from narrative but retained in bullets | Same | task survival across fields; fact survival across fields; action realization | Why do an explicit task and a supported observation survive in some required fields but disappear from others? |
| 11 | Deadline weakened in the action; emotion attached to object | Deadline improved; object/emotion binding still wrong; invented chronology (`already texted`) | qualifier binding; experiencer/role binding; chronology preservation; cross-field consistency | Is the target conflict traceable to the known questionable sink analogue, and is chronology drift independent of that binding error? |
| 16 | Unsupported generic “ask them about the other one” action | Identical | dangling-reference preservation; action-status decision; unsupported repair | Why does close clean support fail to block a fabricated actionable repair? |
| sdi2-02 | Task, deadline, destination all retained | Shared-drive destination dropped from bullets and action | destination qualifier binding; cross-field completeness | Did the delta strengthen deadlines while weakening destination slots? |
| sdi2-07 | Three bullets for one restated task; invented “Same reminder” | Two bullets; second restatement still not deduplicated and an unsupported reminder appears in prose | semantic identity; deduplication; unsupported placeholder generation; bullet cardinality | Is identity represented at the proposition level or only lexically? |
| sdi2-08 | Eight tasks and actions survive, but eight bullets exceed max seven | Identical | bullet budget versus atomic action preservation | Is the benchmark contract internally satisfiable without a compression policy distinct from action merging? |
| sdi2-10 | Four of six required bullets; one merged action instead of two; role error | Same counts; additionally promotes delivered fact to imperative | event state; tentative-idea state; question state; role binding; shared deadline; bullet budgeting; action cardinality | Is this a single capacity failure or several slot/state conflicts hidden by one dense record? |

For each case, the completed ledger must separately record: source proposition, expected state, expected
role tuple, expected qualifiers, expected field realizations, observed realization by arm, rubric check,
coarse failure label, and proposed latent mechanism. A coarse label may summarize rows but may not replace
them.

## 5. Record-to-mechanism coverage map

### 5.1 Row schema

The map must contain one immutable row per corpus record with these columns:

`lineage`, `record_id_or_hash`, `category`, `source_span`, `target_field`, `exact_target_span`,
`fact_state`, `question_state`, `fragment_state`, `task_state`, `role_tuple`, `qualifier_tuple`,
`dedup_relation`, `bullet_count`, `action_count`, `mechanisms_supported`, `mechanisms_conflicted`,
`protected_overlap`, and `review_notes`.

State values are `positive`, `negative/counterexample`, `not_present`, or `unclear`. Mere occurrence of a
category does not count as support. For example, a deadline counts as qualifier support only if the exact
deadline token or a meaning-preserving equivalent survives in every required target field.

### 5.2 Seven-record delta: predeclared evidence to verify

| Delta record | Exact field-form evidence to trace | Intended support | Principal conflict/overlap check |
|---:|---|---|---|
| 1 | Owen follows up; Elena tells Owen; Elena sends Owen the link | locally resolved pronoun and multi-person role binding | lexical/template overlap with record 4 and protected 06 |
| 2 | “they” explicitly unresolved between Casey and Morgan in narrative/bullets; no ambiguity becomes an action | explicit ambiguity plus separate supported task | close analogue to protected 06; names differ but mechanism skeleton is near-identical |
| 3 | Joel resolved in the first clause; Joel-versus-courier unresolved later; Priya is clarification target | mixed local resolution and later ambiguity | densest direct overlap with protected 06's two-pronoun structure |
| 4 | Owen follows up; Owen tells Elena; Elena sends Owen the link | swapped surface roles with preserved relation | near-duplicate of record 1 may overweight template tokens rather than mechanism |
| 5 | sealed packet + north depot + service-counter close + Thursday retained in narrative, bullet, and action; clock remains observation | destination, object, temporal qualifier, cross-field completeness | compare sdi2-02 destination loss and protected 11 qualifier drift |
| 6 | three labeled adapters + locked drawer + projector-cart return retained across fields; hallway remains observation | quantity, destination, trigger qualifier, cross-field completeness | distinguish qualifier copying from compositional binding |
| 7 | unresolved `they/it/her/earlier one` preserved; one supported imperative remains an action | dangling references inside an explicit task | close surface/mechanism analogue to protected 16 |

These rows are not credited as seven independent demonstrations. Records 1 and 4 form a controlled
surface-role pair; records 1–4 form one attribution bundle; records 5–6 form one qualifier bundle; record 7
is one dangling-reference example. Effective weight must therefore be reported both as raw record count
and as mechanism-template cluster count.

### 5.3 Comparator mapping rules

All 78 comparator rows must be inspected; sampling is prohibited. The prior 66-record audit is a lead, not
a substitute, because the reference lineage contains 12 later records. At minimum, the map must explicitly
locate and quote:

- the close protected-06 attribution/ambiguity analogue;
- the window/toaster-or-kettle alternative analogue for protected 08;
- the protected-11 sink/emotion target suspected of actor/emotion drift;
- every dangling-reference target relevant to protected 16;
- every literal or semantic restatement-dedup target relevant to sdi2-07;
- the full bullet/action-count ladder, especially maxima and singleton counts;
- every dense B6/A2-like composition relevant to sdi2-10;
- every destination, deadline, trigger, quantity, and object qualifier realized across all three fields.

The completed map must publish raw counts, cluster-adjusted counts, and conflicting-target counts for each
mechanism. “Covered” is not an acceptable final judgment without all three.

## 6. Conflict map

For every record pair or cluster that supports incompatible output behavior, create one edge with exact
target spans. Use these node types:

- **state:** fact, unresolved question, incomplete fragment, tentative idea, or task;
- **role:** speaker, actor, recipient, possessor, experiencer, or unresolved candidate set;
- **qualifier:** time/deadline, destination, trigger/condition, quantity, object, or purpose;
- **identity:** duplicate, paraphrastic restatement, related-but-distinct, or unrelated;
- **budget:** bullet atom, compressible non-action facts, and non-mergeable actions;
- **cardinality:** source task count, target bullet count, and target action count.

Each edge is `compatible`, `competing`, or `unresolved`. A competing edge requires an actual target-policy
incompatibility, not merely different wording. The first required checks are:

1. observations/fragments/questions promoted to actions versus examples that correctly suppress them;
2. resolved local pronouns versus later explicit ambiguity within one record;
3. deadlines copied while destinations, objects, or conditions disappear;
4. paraphrastic duplicates retained as separate bullets versus genuinely distinct related tasks;
5. the seven-bullet ceiling versus eight non-mergeable actions;
6. dense records whose six bullet atoms coexist with two actions, role bindings, uncertainty, and a shared
   deadline.

The map must not presume that `sdi2-08` demands action merging. Its accepted rubric requires eight actions
while allowing at most seven bullets; therefore bullet compression and action identity are separate design
problems.

## 7. Design-only intervention comparison

| Intervention family | What it can test | Required isolation | Disqualifying interpretation |
|---|---|---|---|
| Corpus correction | Whether inconsistent or unsafe targets drive a failure | corrections only; no new examples | improvement cannot justify unrelated additions |
| Balanced corpus/contrast | Whether sparse mechanism variation or counterexamples improve transfer | cluster-balanced additions; fixed base and objective | raw record count presented as independent mechanism coverage |
| Explicit intermediate representation | Whether typed event/state/role/qualifier slots reduce cross-field loss | same corpus and capacity; representation alone changes | free-text rationale that cannot be deterministically scored |
| Auxiliary training objective | Whether role, state, qualifier, or count supervision improves preservation | one declared auxiliary loss at a time | simultaneous corpus and loss changes |
| Capacity comparison | Whether failures persist when representation and data are fixed | same data, objective, decoding, seed policy, and checkpoint rule | comparing unrelated model families or moving checkpoints |
| Constrained decoding | Whether grammar/count constraints prevent structural failures | identical trained artifact and semantic scoring | counting a parse/count win as a semantic win |
| Deterministic post-validation | Whether supported slots can be checked or a result rejected safely | validator may reject/flag; repair must be separately specified | silently inventing or rewriting content to satisfy a gate |

Preferred representation candidate for later design is a typed proposition table with stable proposition
IDs: `state`, `predicate`, `roles`, `qualifiers`, `coreference_status`, `duplicate_of`, and required output
fields. This is a hypothesis, not authorization. It is preferable to an unconstrained chain-of-thought
target because every slot can be scored against the frozen rubric without exposing hidden reasoning.

## 8. Predeclared decision and stop conditions

### 8.1 Choose a corpus-only ablation only if

- the 85-row map finds a material absence or conflict in the 78-record reference for the implicated atomic
  mechanism;
- the proposed additions form at least two independent template clusters per mechanism, except where the
  study is explicitly a one-record correction ablation;
- protected overlap checks pass; and
- no representation or capacity variable changes.

Otherwise stop the corpus-only branch.

### 8.2 Choose a representation/objective comparison only if

- failures persist despite at least one close, non-conflicting comparator analogue; or
- the same proposition is inconsistently realized across narrative, bullets, and actions; and
- the proposed representation has deterministic, pre-frozen scoring for states, roles, qualifiers,
  identity, and field obligations.

If the representation cannot distinguish protected 06's locally resolved pronoun from its later unresolved
candidate set, stop before compute.

### 8.3 Choose a capacity comparison only if

- corpus integrity and mechanism coverage are adequate;
- a representation-only comparison is either negative or cannot plausibly express the observed load;
- the comparison changes capacity while holding corpus, objective, decoding, seed policy, and checkpoint
  selection fixed; and
- the larger model is evaluated on the same frozen acceptance and protected sets.

Capacity is not selected merely because `sdi2-10` is long. If atomic evidence localizes the failure to a
specific policy conflict, stop the capacity branch.

### 8.4 Choose constrained decoding or deterministic validation only if

- the failure is structural and semantics are already correct, as in the count-only portion of
  `sdi2-08`; or
- the validator can reject/flag a missing bound qualifier or field without fabricating content.

Never use post-validation to turn a fact, question, fragment, or tentative idea into a task. A repair system
that generates new wording is a separate model intervention and needs separate evaluation.

### 8.5 Global stop

Stop and return to Johnny without proposing compute if any of the following occurs:

- accepted JSON and the scorer disagree;
- a corpus record cannot be uniquely traced to its source and target fields;
- protected leakage cannot be ruled out;
- the later comparison would change more than one primary variable;
- the metric cannot distinguish semantic improvement from parser/count compliance;
- the proposed acceptance gain depends on a protected regression;
- the seven treatment records are treated as the default new baseline;
- Claude finds a material evidence or policy disagreement.

## 9. Leakage controls

Before any future artifact is authored, freeze a protected-overlap register using normalized tokens,
entity-masked forms, predicate/role/qualifier skeletons, and manual semantic review. Automatic similarity is
only a flag; manual adjudication governs.

Protected 06 receives a dedicated exclusion family. Quarantine any candidate that combines:

1. a named speaker telling a named recipient a fact;
2. an earlier pronoun that is locally resolvable;
3. a later explicit two-candidate ambiguity about a needed object; and
4. a clarification task directed to one participant.

Delta records 2 and 3 must be marked as close analogues, with record 3 the highest-risk structural match.
They may remain evidence for diagnosing the failed treatment but cannot automatically become training
material in a later experiment. Renaming people or objects does not clear leakage.

The four-part skeleton matches delta record 3 literally, but it is not an exhaustive mechanical filter.
Delta record 2 places its explicit two-candidate ambiguity on the earlier follow-up pronoun rather than on
a later needed-object reference; the leakage register must therefore test reordered variants of the same
resolved-versus-unresolved role-binding mechanism and must retain record 2 as a close analogue.

Apply the same skeleton review to protected 08, 09, 10, 11, and 16 and to all acceptance cases. The audit
must distinguish pre-existing comparator analogues from newly proposed protected-targeted additions; the
former explain baseline exposure, while the latter can contaminate a claimed generalization test.

## 10. Review and authorization protocol

Claude must independently verify every ledger row, target quotation, count, conflict edge, and leakage
classification against the primary artifacts. A material disagreement stops work and returns to Johnny.

Completion of this draft or of the static audit does not authorize implementation. A later proposal must
name exactly one primary intervention family, freeze all other variables, define atomic success and
regression criteria, and receive separate authorization. Nothing is committed or pushed without Johnny's
hand-typed instruction.

## 11. Current disposition

- RBR17-C outcome and postmortem: **closed**.
- 78-record comparator: **reference lineage**.
- 85-record treatment: **failed evidence only**.
- Seven-record delta: **individually auditable; not carried forward by default**.
- This mechanism/representation document: **draft awaiting independent review**.
- Compute, corpus edits, dataset access, model execution, seed 73, checkpoint action, commit, and push:
  **not authorized**.
