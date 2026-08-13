# RBR17-C static mechanism audit and intervention decision memo

**Date:** 2026-08-13  
**Author:** ChatGPT  
**Status:** Draft audit complete; Claude independent verification required  
**Governing design:** `controlled_seed17_rbr17c_mechanism_representation_audit_design_chatgpt.md` at `9f2226f`  
**Compute:** None  

## 1. Executive decision

The evidence stops a broad “add examples” response and does not yet justify a capacity comparison.

The 78-record comparator already contains close or near-isomorphic support for protected 06, 08, 10, 11,
and 16; two pure paraphrastic-dedup records for sdi2-07; an exact B7/A8 record for sdi2-08; and three
dense B6/A2 compositions relevant to sdi2-10. The older 66-record finding that action support stopped at A5
is no longer true of the actual RBR17-C comparator: its final twelve records include one each at A6, A7,
and A8.

The strongest supported interpretation is a mixture of:

1. **cross-field representation failure** — a proposition survives in narrative or bullets but not actions,
   or vice versa;
2. **state/role/qualifier binding failure** — questions become tasks, facts become imperatives, roles drift,
   or one bound qualifier disappears while another survives;
3. **bullet-budget generalization failure at sdi2-08** — comparator record 74 already teaches the exact
   B7/A8 source-to-target structure, yet both arms emit B8/A8;
4. **bundle interference** — the seven-record treatment cluster improved protected 02 but regressed protected
   09 and sdi2-02 without resolving the targeted families.

The next proposal should therefore be a **representation/objective comparison**, not a larger-model study
and not automatic adoption of the seven records. A small corpus-correction ablation may be proposed
separately only if target-integrity candidates are independently confirmed; it must not be mixed with the
representation experiment.

## 2. Frozen evidence and generated map

The record map is `controlled_seed17_rbr17c_record_to_mechanism_map.jsonl`, generated reproducibly by
`build_rbr17c_static_audit_map.py`. It contains exactly 85 unique rows: 78 comparator and seven
`treatment_delta`. Each row retains the full source, exact narrative/bullet/action targets, SHA-256 record
fingerprint, field counts, mechanism annotations, conflicts, and protected-overlap flags.

The generator reads only the two frozen JSONL files. It performs no model, benchmark, scoring, split, or
corpus-generation operation. Deterministic annotations are leads; the exact spans remain authoritative for
manual adjudication.

## 3. Atomic failure ledger

Each row below is one false rubric check or independently visible defect. `C` and `T` mean comparator and
treatment. “Visible” means the accepted output itself establishes the defect even where the frozen rubric
does not expose a separate Boolean check.

| ID | Arm | Source proposition/state | Expected fields | Observed evidence | Atomic mechanism | Evidence status |
|---|---|---|---|---|---|---|
| 06-a | C,T | Tessa is the locally plausible actor for “she asked” | narrative/bullets | permit fact is detached from Tessa in bullets; attribution check false | local coreference and speaker/actor binding | rubric false |
| 06-b | C,T | stamped-copy need is unresolved between Tessa and inspector | all | ambiguity is retained | ambiguity-set preservation | passes; paired load matters |
| 08-a | C | wet-spot source remains window-or-plant | narrative/bullets | output attributes the spot to “dry weather” | alternative-set and causal non-inference | rubric false: invented causality |
| 08-b | T | same unresolved alternative | narrative/bullets | “whether the wet spot from the window or the plant was the wet spot” loses the source relation | question predicate and alternative binding | visible defect despite broad question check |
| 08-c | T | “It was dry again by lunchtime” is a later observation | narrative/bullets | narrative changes subject to plant; bullet leaves “it” detached | referent binding and fact preservation | visible defect |
| 09-a | T | sent-versus-saved remains unresolved | all; no send action | narrative/bullet question coexists with `Send the revised schedule` action | question/task state separation | rubric false: question unresolved |
| 09-b | T | volunteer-list thought remains incomplete | narrative/bullets; no action | rewritten as check task/question rather than incomplete thought | fragment-state preservation | rubric false |
| 09-c | T | only supported action is checking sent mail | actions | unsupported send action added | action-status decision | visible and evaluator-labeled unsupported addition |
| 10-a | C,T | print shipping label is explicit task | narrative, bullets, actions | survives narrative/bullets but action section is empty | cross-field task realization | rubric false |
| 10-b | C,T | final scene still dragged is supported fact | narrative and bullets | absent from narrative, present in bullets | cross-field fact realization | visible defect |
| 11-a | C | registration fee deadline is Thursday | narrative/bullets/actions | deadline is attached in bullet but absent from action | qualifier binding across fields | visible defect |
| 11-b | C,T | writer is tired; garage light flickers | narrative/bullets | output attaches tiredness/reminder semantics to the light or an unresolved “it” | experiencer and referent binding | visible defect |
| 11-c | T | text Jonah that writer will call tomorrow | all | “already texted” invents completion chronology | chronology/state preservation | evaluator label: Invented Chronology |
| 16-a | C,T | reminder is supported but all references remain unresolved | all | generic “ask someone/them about the other one” is retained as a confident action without explicit uncertainty in action field | unresolved-reference marking across fields | evaluator label: Unsupported Addition |
| sdi2-02-a | T | upload destination is shared drive | narrative, bullet, action | destination survives narrative but is absent from bullet/action | destination binding across fields | rubric false |
| sdi2-07-a | C,T | two clauses are one paraphrastic task | exactly one bullet | C emits 3 bullets; T emits 2 | semantic identity and bullet deduplication | rubric and count false |
| sdi2-07-b | C | no independent “Same reminder” proposition | narrative/bullets | unsupported placeholder bullet appears | non-invention during deduplication | evaluator-labeled unsupported addition |
| sdi2-07-c | T | second clause restates room reservation | narrative | rewritten as an unsupported task to book “the reminder” | proposition identity and role/object binding | visible defect |
| sdi2-08-a | C,T | eight independent tasks | actions | all eight actions survive | action cardinality | passes |
| sdi2-08-b | C,T | bullet ceiling is seven | bullets | eight bullets emitted | bullet budgeting distinct from action identity | count false only |
| sdi2-10-a | C,T | courier delivered samples to gallery assistant, attributed to coordinator | narrative/bullets | role/attribution check false; T promotes delivery to imperative bullet | event state and role binding | rubric false |
| sdi2-10-b | C,T | send code and pack bowls are two tasks | bullets/actions | merged into one bullet and one action | action identity/cardinality | rubric and count false |
| sdi2-10-c | C,T | six distinct ideas are required | bullets | only four bullets | bullet budgeting without proposition loss/merge | count false |
| sdi2-10-d | T | delivered-samples event is a fact | bullets/actions | imperative “Deliver the glaze samples” appears in bullets | fact/task state separation | rubric false: non-task promotion |

The ledger contains 24 atomic rows. It deliberately retains passing companion mechanisms where their
co-occurrence creates the load being diagnosed, as in 06-b and sdi2-08-a.

## 4. Coverage findings from the 78+7 map

### 4.1 Cardinality is present, but bullet compression is not

Comparator target counts are:

- bullets: B1=6, B2=17, B3=24, B4=18, B5=7, B6=4, B7=2;
- actions: A0=9, A1=28, A2=23, A3=7, A4=7, A5=1, A6=1, A7=1, A8=1.

Comparator record 74 is the exact eight-task ladder endpoint and already teaches B7/A8: it omits one task
from bullets while preserving all eight action items. The acceptance case asks for the same B<=7/A8
structure. Both arms nevertheless emit B8/A8. This is neither absence of A8 support nor a corpus/contract
policy mismatch; it is failure to transfer an exact structural budgeting pattern.

### 4.2 Close support exists for the shared protected failures

| Failure | Comparator locator | Effective evidence | Judgment |
|---|---|---|---|
| protected 06 | comparator:048 | near-isomorphic local pronoun resolution + later ambiguity + clarification action | strong singleton; treatment adds a highly overlapping cluster rather than a new mechanism |
| protected 08 | comparator:061 | toaster-or-kettle question + later observation + separate task | strong singleton plus other open-question records |
| protected 10 | comparator:042 | near-isomorphic observations + buried print task + final observation, correctly realized | strong direct support |
| protected 11 | comparator:053 | repeated deadline task + object observation + writer emotion + separate message task | strong direct support; current target correctly binds writer emotion |
| protected 16 | comparator:056 | near-word-for-word dangling-reference imperative with unresolved references | strong direct support |
| sdi2-07 | comparator:069,070 | two pure paraphrastic B1/A1 dedup targets | two independent surfaces, same mechanism cluster |
| sdi2-08 | comparator:074 | exact eight-source-task, B7/A8 target | exact structural analogue still does not transfer |
| sdi2-10 | comparator:054,075,076 | three B6/A2 dense composites with varied roles, questions, ideas, observations, and qualifiers | repeated dense support; not simple absence |

### 4.3 Effective weight of the seven-record delta

The delta is seven raw records but only three mechanism bundles:

- records 1–4: attribution/coreference, with records 1 and 4 a role-swapped surface pair;
- records 5–6: cross-field qualifier copying;
- record 7: dangling-reference preservation.

Records 2 and 3 overlap protected 06, and record 7 overlaps protected 16. The delta therefore increases
effective weight near protected forms while leaving deduplication, bullet compression, question/task state,
and dense proposition identity largely untouched. Treatment regressions on protected 09 and sdi2-02 show
that raw targeted-example count is not a reliable mechanism intervention.

## 5. Conflict map

| Edge | Evidence nodes | Type | Finding |
|---|---|---|---|
| CM-01 | comparator:074 B7/A8 ↔ sdi2-08 required B<=7/A8 | compatible but non-generalizing | exact structural budgeting support exists; both arms still emit B8/A8 |
| CM-02 | comparator:048 ↔ protected 06 | compatible but non-generalizing | exact mechanism support exists; both final arms still fail attribution |
| CM-03 | delta:003 ↔ protected 06 | leakage/high overlap | treatment targets the protected skeleton almost literally without fixing it |
| CM-04 | comparator:042 ↔ protected 10 | compatible but non-generalizing | buried task is taught correctly, yet action-field realization fails |
| CM-05 | comparator:053 ↔ protected 11 | compatible but non-generalizing | deadline/experiencer pattern is taught correctly; output binding still drifts |
| CM-06 | comparator:056 ↔ protected 16 | compatible but non-generalizing | close dangling-reference target exists; uncertainty marking does not transfer consistently across fields |
| CM-07 | comparator:069,070 ↔ sdi2-07 | compatible but non-generalizing | pure paraphrastic dedup is present twice; output still fragments the restatement |
| CM-08 | comparator:054,075,076 ↔ sdi2-10 | compatible but compositional | constituent mechanisms and B6/A2 forms exist, but role/state/action identities collapse under new composition |
| CM-09 | comparator:035 observation → inferred action ↔ non-promotion acceptance policy | potentially competing | overflowing-bin observation becomes `Empty the recycling bin`; requires policy adjudication |
| CM-10 | deadline survival ↔ destination loss in sdi2-02 treatment | competing realization pressure | one qualifier survives while another bound slot vanishes; category coverage does not ensure slot binding |
| CM-11 | question/fragment states ↔ imperative prior in protected 09 treatment | competing state pressure | unresolved and incomplete content is rewritten into actions after the attribution-heavy delta |
| CM-12 | six bullet atoms ↔ two action identities in sdi2-10 | unresolved representation | current flat text has no stable proposition IDs linking fields, allowing merges and promotions |

No confirmed corpus/contract policy conflict was found. CM-09 is a target-integrity candidate and must not
be called a defect until Claude independently adjudicates the project's intended inference policy. The
remaining edges show adequate nominal support but failed transfer or composition.

## 6. Leakage register

| Candidate | Protected/acceptance analogue | Risk | Disposition |
|---|---|---|---|
| delta:001 | protected 06 role/speaker skeleton | medium | diagnostic only; same template cluster as delta:004 |
| delta:002 | protected 06 with ambiguity reordered earlier | high | quarantine from any claimed protected-generalization training set |
| delta:003 | protected 06 literal four-part skeleton | critical | quarantine; highest-risk overlap |
| delta:004 | protected 06 role-swapped surface pair | medium | diagnostic only; not independent coverage |
| delta:005 | sdi2-02 destination/deadline completeness; protected 11 qualifier retention | high | quarantine from those claimed transfer tests unless protected cases are replaced and refrozen |
| delta:006 | sdi2-02 qualifier completeness | medium-high | same qualifier bundle as delta:005; not independent |
| delta:007 | protected 16 dangling-reference imperative | critical | quarantine from protected-16 generalization claim |
| comparator:048 | protected 06 | pre-existing close analogue | retain as baseline exposure; do not mislabel as new leakage |
| comparator:061 | protected 08 | pre-existing close analogue | retain as baseline exposure |
| comparator:042 | protected 10 | pre-existing close analogue | retain as baseline exposure |
| comparator:053 | protected 11 | pre-existing close analogue | retain as baseline exposure |
| comparator:056 | protected 16 | pre-existing close analogue | retain as baseline exposure |
| comparator:069,070 | sdi2-07 | pre-existing close analogues | retain as baseline exposure |
| comparator:074 | sdi2-08 | pre-existing exact B7/A8 analogue | retain; disclose failed transfer despite exact structural support |
| comparator:054,075,076 | sdi2-10 | pre-existing dense analogues | retain as baseline exposure |

Renaming entities or objects does not lower risk. Future overlap review must compare normalized text,
entity-masked form, predicate/role/qualifier skeleton, state sequence, and field-count contract. Manual
adjudication governs every automatic flag.

## 7. Intervention decision register

| Branch | Gate result | Decision |
|---|---|---|
| Broad corpus additions | fails: close support already exists; delta is clustered and leaky | stop |
| Narrow corpus correction | conditionally eligible for confirmed target conflicts only | separate proposal; isolate from all other changes |
| Typed representation/objective | passes: failures persist despite close support and cross-field identity repeatedly breaks | recommended next proposal |
| Capacity comparison | fails now: representation and compositional-transfer explanations are not exhausted | defer |
| Constrained decoding | eligible only for syntax/count enforcement; cannot choose semantic compression | do not use as primary intervention |
| Deterministic post-validation | eligible to reject/flag count, missing qualifier, or field mismatch; no generative repair | secondary safety proposal only |
| Stop all experimentation | not required: a single-variable representation hypothesis is testable | do not stop, but require new authorization |

### Recommended representation hypothesis

Represent each source proposition with a stable ID and typed fields:

`state`, `predicate`, `roles`, `qualifiers`, `coreference_status`, `duplicate_of`, and
`required_output_fields`.

The representation must deterministically distinguish:

- a locally resolved pronoun from a later unresolved candidate set (protected 06);
- a fact, question, fragment, tentative idea, and task (08, 09, 10, 16, sdi2-10);
- deadline, destination, trigger, quantity, object, and purpose slots (11, sdi2-02);
- semantic duplicate identity from related-but-distinct propositions (sdi2-07);
- bullet grouping from action identity (sdi2-08);
- two actions sharing one deadline without merging (sdi2-10).

The future proposal must hold the 78-record corpus, model capacity, seed policy, checkpoint rule, decoding,
and frozen evaluation sets constant. It may change only the representation or one declared auxiliary
objective—not both. Atomic slot/field scores must be frozen before compute.

## 8. Stop conditions carried forward

Return to Johnny without compute if Claude finds any material map, ledger, count, conflict, or leakage
disagreement; if the B7/A8 target policy cannot be defined without subjective generation; if the proposed
representation cannot score protected 06's two distinct coreference states; if more than one primary
variable would change; or if protected overlap cannot be controlled.

This audit does not authorize implementation, corpus edits, model or benchmark execution, seed 73,
checkpoint selection, commit, or push. The 78-record comparator remains the reference lineage; the failed
85-record treatment and seven-record delta remain evidence only.
