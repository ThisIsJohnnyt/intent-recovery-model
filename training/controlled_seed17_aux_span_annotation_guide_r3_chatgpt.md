# Auxiliary span-supervision annotation guide — revision 3

**Date:** 2026-08-14  
**Author:** ChatGPT  
**Status:** Focused correction draft; not yet independently reviewed; correction rerun not authorized  
**Supersedes for the one correction rerun:** `controlled_seed17_aux_span_annotation_guide_r2_chatgpt.md`  
**Historical preservation:** Revision 2, both sealed initial passes and receipts, the verified disagreement
record, the original selection package, and the supplemental selection package remain unchanged.  

## 1. Scope and authority

This is the single focused correction permitted by revision 2 Section 11.4. It addresses only ambiguities
evidenced in the sealed 14-record validation and the separately frozen supplemental-selection sequence:

1. proposition boundaries, topic fragments, discourse markers, and embedded predicates;
2. target-inferred tasks;
3. semantic role scope;
4. qualifier scope and precedence;
5. target-field obligations across duplicates and combined target items; and
6. demonstratives, omitted arguments, and inferred-task coreference.

It does not edit or adjudicate either sealed initial pass. It does not authorize annotation, opening a new
reviewer's pass before sealing, model/tokenizer use, full-corpus work, training, evaluation, checkpoint
operations, Gemini setup/generation/spending, staging, commit, or push.

The correction rerun, if separately authorized after independent guide review, uses all 15 frozen records:
the original ten regression records, the original four fresh records, and supplemental fresh comparator 018.
There is no second guide-correction round. Any failure of exact agreement or fresh unfielded coverage returns
to Johnny.

## 2. Proposition unit, topic fragments, and order

Annotate every independently classifiable source state, including states omitted from the committed target.
A proposition is the smallest source unit that asserts, asks, proposes, fragments, or assigns one semantic
predicate/state with the explicit arguments and qualifiers required to interpret it.

### 2.1 Separate units

Create separate propositions for:

- each coordinated or adjacent clause with its own predicate/state;
- a topic-style noun phrase lacking a recoverable predicate (`fragment`), even when adjacent to a question;
- a finite metacognitive/discourse assertion such as `I know`, even when it only comments on a reminder;
- explicit restatements;
- an outer report/communication predicate and its independently asserted embedded content;
- an outer message task and an independently asserted embedded message-content state; and
- a source question/fact plus a separately required target-inferred task under Section 3.

Do not split auxiliaries, control/raising chains, or passive causatives that jointly express one predicate:
`need to get that damage claim filed` is one task, not three.

### 2.2 Topic fragments

A standalone topic label is a `fragment` even if a following clause supplies related detail. It receives
only fields that explicitly realize that label's content.

Thus `sunset chasers api integration` is an unfielded fragment separate from
`weather.gov or openweather?`, and `client call notes` is an unfielded fragment. A contentful elliptical
obligation such as `mileage form before Friday` has a recoverable task predicate and is a `task`, not a
fragment.

### 2.3 Discourse markers

Exclude a leading marker from the source span when it only organizes dictation or turn flow and does not
change proposition truth, modality, timing, or reference. Excluded markers include `ok`, `wait`, `anyway`,
`also`, and phrases such as `and before I close this:` when they mean only “before I end this note.”

Include a superficially similar phrase when it semantically constrains the proposition. For example,
`Before the open house doors unlock` is a real shared temporal trigger and must be included.

Terminal punctuation remains boundary-equivalent under revision 2: leading/trailing whitespace or one
terminal `.`, `?`, `!`, comma, or semicolon may differ if the non-punctuation token sequence is identical.

### 2.4 Nested and overlapping propositions

When an outer predicate requires a content argument and that content has its own independently classifiable
predicate, annotate both:

- the outer proposition spans the outer predicate plus the content needed to complete it;
- the embedded proposition spans its own predicate and arguments; and
- overlap is required, not an error.

Examples:

- `Ren said Salma handed the spare clips to the installation lead` creates an outer report fact and an
  embedded transfer fact;
- `text Bea that I'll be ten minutes late` creates a message task and the embedded lateness fact.

Epistemic wrappers of unresolved alternatives are a controlled exception: `I don't know whether ...` and
`I can't tell whether ...` are one `question` proposition spanning the wrapper and alternatives. Do not
create a second nested row for the `whether` complement. This preserves the unresolved information request
as one state rather than treating the writer's ignorance as a separate target fact.

## 3. Target-inferred tasks

Create a separate overlapping `task` only when the committed action list requires a follow-up that no
explicit source task already represents. The inferred task uses the smallest source span that grounds the
follow-up.

Required examples:

- `weather.gov or openweather?` grounds a separate compare/decide task;
- the trash-day question grounds a separate confirmation task; and
- `plumber never called back` grounds a separate follow-up task because the committed target explicitly
  contains that action.

Do not infer tasks merely because a fact could motivate useful work. A committed action item is required.
Do not create an inferred task if an explicit source task already maps to that action.

Every inferred task has implicit-writer `actor`. Other roles may come from either the grounding source span
or the exact committed action wording, because target inference is the reason the task exists. Coreference is
still evaluated from referential expressions in the grounding source span under Section 6.

## 4. State labels

Assign exactly one state:

- `fact`: asserted observation, event, condition, relation, preference, evaluation, emotion, cognition, or
  metacognitive assertion;
- `question`: requested information, unresolved alternatives, or an epistemic `don't know/can't tell
  whether` wrapper;
- `fragment`: incomplete thought or topic label without a recoverable predicate/state;
- `tentative_idea`: optional possibility or suggestion signaled by `maybe`, `what if`, or equivalent
  non-obligatory language;
- `task`: explicit or recoverable obligation, imperative, reminder, intention, or Section-3 target-inferred
  follow-up.

`should` without `maybe/what if` expresses a task/plan in these notes. A message content fact does not become
a task merely because it is embedded in a text/send task. An unfinished clause may be a fragment even when
some predicate words survive, if the missing complement/state prevents a complete assertion.

## 5. Semantic roles

Roles indicate semantic participation, not every grammatical subject. Allowed roles and canonical order:

`speaker`, `actor`, `recipient`, `object`, `possessor`, `experiencer`, `candidate_set`.

### 5.1 General constraints

Except for the two controlled implicit-role rules below, add a role only when its filler is expressed inside
the proposition span. Do not borrow a candidate, object, or recipient from an adjacent clause.

Controlled implicit roles:

1. every `task` has `actor`; if none is expressed, it is the note writer;
2. an emotion/perception/cognition predicate may have the grammatically recoverable note writer as
   `experiencer` even when first person is omitted (`thinking about...`, `which is exhausting`).

### 5.2 Role definitions

- `speaker`: source of an explicit speech/report predicate (`Rina told`, `Ren said`). A speaker is not also
  `actor` merely for speaking.
- `actor`: intentional agent/doer of the proposition's event, including non-task events. Do not label a
  stative subject or involuntary perceiver as actor.
- `recipient`: explicit destination/addressee of communication or transfer, including the person called,
  texted, asked, told, sent to, handed to, or followed up with. A callback receiver is also a recipient.
- `object`: explicit patient, theme, acted-on item, or propositional content. It includes the topic of
  `about`, the item needed, and a patient of passive action. Do not use `object` for a recipient or merely
  because a stative subject exists.
- `possessor`: an explicit syntactic possession/ownership relation (`the cracked display's paperwork`,
  `your mind`, `has/owns/belongs`). A person who merely needs a future item is not yet a possessor.
- `experiencer`: entity experiencing emotion, perception, memory, cognition, or internal state.
- `candidate_set`: explicitly competing alternatives relevant to a decision, unresolved reference, or
  question. It can include people, systems, days, or other candidate values. It must occur inside the span;
  do not attach candidates from a later ambiguity clause to an earlier need fact.

### 5.3 Load-bearing role examples

- `Rina told Marcus...`: `speaker`, `recipient`, `object`.
- `call the dentist` and `call the lighting supplier`: implicit `actor`, explicit `recipient`, no object
  unless separate call content is expressed.
- `Follow up with the vendor about the late shipment`: `actor`, `recipient`, `object`.
- `He still needs the signed copy`: `object`, but not `possessor` or `candidate_set`.
- `i never heard back from the plumber about the leak`: `recipient` for the explicit writer `i`, who is the
  intended receiver of the callback, and `object` for the leak topic. The plumber is the callback source,
  not the recipient; hearing is not intentional actor behavior.
- `still stressed about that`: `object`, `experiencer`.
- `taste so good it will blow your mind`: `object` for `mind` and `possessor` for `your`.

## 6. Coreference

Coreference describes antecedent resolution for pronouns, demonstratives, anaphoric noun phrases, or truly
required omitted arguments. Use full-record source context and precedence
`dangling` > `unresolved` > `resolved` > `none`.

### 6.1 What counts

- A complete demonstrative noun phrase with its own lexical head (`that old Zesto commercial`) is deictic
  but self-identifying for this schema: `none` unless understanding requires a missing textual antecedent.
- A bare/substitutive demonstrative (`that`, `it`, `that one`) referring backward is evaluated normally.
- Generic `your` does not require a textual antecedent.
- An omitted argument counts only when syntax/meaning requires a specific antecedent whose identity changes
  interpretation. Optional understood complements such as `the shorter agenda probably helped` do not count.
- Idiomatic/expletive `it` does not count.
- Interrogative `who/what` seeks new information and is not itself an unresolved antecedent.

### 6.2 Controlled examples

- `things like that` in comparator 008 resolves to the preceding commercial/slogan; the opening
  `that old Zesto commercial` is `none`.
- `don't let the mileage form disappear under everything else` is `none`; `everything else` is a
  self-contained quantifier, not an anaphor requiring one antecedent.
- `the shorter agenda probably helped` is `none`.
- `Remember to ask her about the earlier version` is `dangling` because `her` and the anaphoric version lack
  recoverable antecedents.
- A target-inferred trash-day confirmation task inherits the grounding question's resolved `it`; a plumber
  follow-up task grounded in `plumber never called back` is `none`.

## 7. Qualifiers

Allowed qualifier order:

`time`, `deadline`, `destination`, `trigger`, `condition`, `quantity`, `purpose`, `object_modifier`.

### 7.1 Time, deadline, and trigger

- `time`: explicit temporal point, occasion, duration, sequence, or delay. This includes `this time`,
  `ran long`, `last ten minutes`, `after setup`, `years ago`, and `by 5` inside a non-task planning fragment.
- `deadline`: latest required completion boundary for a task/obligation. Use for `before Friday`, `by 3`, or
  `before pickup` on a task. Do not use deadline for an unfinished possibility merely mentioning a time.
- `trigger`: event/state that activates or bounds an action. A shared subordinate trigger applies to every
  coordinated task. Use discontinuous spans where necessary to attach the exact shared phrase without
  swallowing the neighboring predicate.

Do not label note-navigation language (`before I close this`) as time/trigger/deadline when it only marks
dictation order.

### 7.2 Other qualifiers

- `destination`: endpoint/location of movement, placement, upload, delivery, or transfer.
- `condition`: contingency controlling whether the proposition applies.
- `quantity`: explicit count, amount, cardinality, or measurement expression. `percentage` is a measurement
  expression even without a numeric value. Numeric temporal durations remain `time`, not quantity.
- `purpose`: explicitly stated intended goal/use.
- `object_modifier`: restrictive state/version descriptor needed to identify the item: `updated`, `signed`,
  `earlier`, `cracked`, `repaired`, `revised`, `spare`, `late`. Conventional type/material compounds such as
  `damage claim`, `translation headsets`, `ceramic samples`, and `display easels` are not modifiers.

Distinct phrases may supply orthogonal qualifiers. The same phrase does not receive a redundant broader
type.

## 8. Duplicates and target-field obligations

`duplicate_of` links a later proposition to an earlier proposition with the same semantic identity. The
later row retains its own span, state, roles, qualifiers, coreference, and fields.

### 8.1 Field mapping rule

For each proposition and each field independently, ask whether an identifiable part of the committed field
realizes that proposition's semantic contribution. If yes, include the field. One target item may realize
multiple source propositions; shared realization gives the field to every contributing proposition even
though it remains one output item.

Consequences:

- a duplicate/restatement can share `narrative`, `bullet`, and `action` with the first proposition;
- sharing an action field does not create a second action identity;
- a duplicate receives zero fields only when no committed field realizes that occurrence's semantic
  contribution;
- non-task propositions never receive `action`.

### 8.2 Required examples

- All three mileage-form reminders contribute to the target's explicit “emphasized repeatedly” treatment and
  the one submission action; each receives all three fields.
- Both comparator-069 task restatements contribute to the merged damage-claim item; each receives all three
  fields.
- Both plumber-callback facts contribute to the repeated unresolved-callback target content and receive
  narrative+bullet; the separate inferred follow-up task receives action.
- `client call notes` remains unfielded because talking points do not explicitly realize the noun-fragment
  note label.
- `I know` remains unfielded.

### 8.3 Source state plus inferred task

The source state and inferred task map independently:

- API question: narrative+bullet; inferred decide/compare task: bullet+action because the committed bullet is
  itself an explicit decision instruction.
- Trash-day question: narrative+bullet; inferred confirmation task: action only.
- Plumber-callback fact: narrative+bullet; inferred follow-up task: action only.

## 9. Span, schema, and serialization

Each record contains exactly, in order:

- `record_locator`;
- exact `source_input`;
- ordered `propositions`;
- `reviewer`;
- `review_status`.

Each proposition contains exactly, in order:

- sequential `proposition_id` (`p01`, `p02`, ...);
- ordered `source_character_spans` with exact `start`, `end`, and `text`;
- one `state`;
- canonical unique `roles`;
- canonical unique `qualifiers`;
- one `coreference_status`;
- backward-only `duplicate_of` or `null`;
- canonical unique `required_output_fields` in `narrative`, `bullet`, `action` order.

Spans use the smallest intervals satisfying Sections 2-3. Intervals inside a proposition must be sorted and
nonoverlapping. Discontinuous spans are permitted only for syntactically shared material, especially a
common trigger. Overlap between different propositions is permitted for nested content and inferred tasks.

Validation fails closed on unknown fields/labels, duplicate keys, non-exact span text, unsorted or overlapping
within-proposition intervals, forward/self duplicates, duplicate labels, missing task actor, non-task action,
or noncanonical ordering.

## 10. Worked resolution matrix

This matrix makes the correction choices auditable without editing either sealed pass.

### Comparator 007

- Separate unfielded fragment `sunset chasers api integration`.
- API alternative is a question with `candidate_set`+`object`, narrative+bullet.
- Create overlapping inferred task with `actor`+`object`+`candidate_set`, bullet+action.
- Exclude `wait` from the cloud idea; add `destination`+`quantity`.
- Free-tier alternatives use `object`+`candidate_set`, narrative+bullet.

### Comparator 040

- Pushed call: `object`+`time`.
- Missing callback: writer-as-`recipient`+leak-topic-`object`; stressed clause: `object`+`experiencer`.
- Mail reminder maps narrative+action; piling-up fact maps narrative+bullet.
- Trash question uses `object`+`candidate_set`+`time` and resolved coreference; inferred confirmation uses the
  same grounding roles/coreference plus actor and action only.
- Repeated callback fact maps narrative+bullet; add a separate action-only inferred plumber follow-up task.

### Comparator 042

- `this time` is time; `probably helped` has coreference `none`.

### Comparator 048

- Report uses `speaker`+`recipient`+`object`; asked clause remains separate and resolved.
- Need fact has `object`+`object_modifier`, unresolved coreference, but no candidate set borrowed from the next
  clause and no possessor.
- Create separate `question` for `I can't tell whether...` with `experiencer`+`candidate_set`.
- Final ask has actor+recipient+object and resolved coreference.

### Comparator 053

- Annotate unfielded `I know` fact.
- All three mileage reminders are duplicate-linked tasks with all three fields.
- Exhausting clause has implicit-writer experiencer and resolved coreference.
- `everything else` is coreference none.
- Exclude `also`; annotate both outer text task and embedded lateness fact. The outer task has
  actor+recipient+object+time; the embedded fact has actor+time.

### Comparator 054

- `ran long` is time; lost-thread fact has actor+object.
- Access-list question maps narrative+bullet.
- Dentist is recipient.
- Exclude note-navigation prefix before porch-bulb task; no trigger.

### Comparator 056

- Dangling-reference task has actor+recipient+object and object modifier.

### Comparator 069

- First task has actor+object+possessor, deadline+object modifier, and all three fields.
- Restatement has actor+object, deadline, resolved coreference, duplicate link, and all three fields.

### Comparator 074

The sealed passes already agree; preserve that interpretation unchanged.

### Comparator 075

- Shared open-house trigger applies to both tasks; second task uses a discontinuous span. Supplier is
  recipient.
- West-window epistemic wrapper is one question with object+experiencer and coreference none. The explicit
  writer `I` is the cognition experiencer; question state does not suppress semantic roles.
- Optional visitor-card idea has object+destination but no implicit actor because it is not a task.
- Separate outer Ren report (`speaker`+`object`) and embedded Salma transfer
  (`actor`+`recipient`+`object`, spare=`object_modifier`).

### Comparator 012

- `by 5` is time, not deadline, in both non-task fragments.
- Exclude `wait` and `anyway`; stove question maps narrative+bullet.

### Comparator 073

The sealed passes already agree; preserve that interpretation unchanged.

### Comparator 008

- Opening thought has implicit-writer experiencer+time and coreference none for the complete demonstrative NP.
- Slogan has object+possessor and resolved coreference.
- Memory reflection has possessor+experiencer+time and resolved coreference.

### Comparator 030

- Vendor follow-up has actor+recipient+object and late=`object_modifier`.

### Comparator 018 (supplemental fresh record)

No semantic result is predeclared. Apply the general rules without treating the lexical omission signature as
an annotation. The fresh-coverage gate passes only if both independent correction passes agree that at least
one proposition among fresh comparators 012, 073, 008, 030, and 018 has
`required_output_fields: []`.

## 11. Correction rerun protocol and gates

After this guide is independently verified and the rerun is separately authorized:

1. ChatGPT and Claude independently annotate all 15 frozen records from this guide, exact source, and
   committed target only.
2. Neither opens the other's correction pass before both are schema-validated, sealed, and hashed.
3. Initial sealed passes and disagreement evidence may be consulted only as historical input already embodied
   in this guide; no old annotation row may be copied as authority.
4. Compare every proposition count/order, boundary-equivalent span, state, role, qualifier, coreference,
   duplicate link, and field obligation.

The correction rerun passes only if:

- all 15 records achieve exact agreement under boundary equivalence;
- schema validation succeeds for both passes; and
- at least one of the five fresh records contains an agreed proposition with empty
  `required_output_fields`.

If any condition fails, preserve both passes, create a complete disagreement record, and stop with Johnny.
There is no additional guide correction, record replacement, or redraw.

## 12. Claude review checklist

Claude should independently verify:

- every substantive initial disagreement has one deterministic resolution here;
- the correction does not reach beyond evidenced ambiguity;
- topic fragments and nested predicates cannot be inconsistently merged;
- discourse-marker exclusion does not drop semantic triggers;
- inferred-task creation and field mapping are deterministic;
- semantic roles distinguish speaker/actor/recipient/object/possessor/experiencer/candidate sets;
- coreference handles complete demonstrative NPs, optional omitted complements, and inferred tasks;
- qualifier rules resolve time/deadline/trigger and modifier disputes;
- duplicate field sharing is explicit and does not create extra output identity;
- comparator 018 is not pre-annotated by its selector signature;
- the 15-record exact-agreement and fresh-empty-field gates are fail-closed; and
- no second correction or redraw remains available.

Material disagreement stops this guide revision and returns to Johnny. Review agreement does not authorize
annotation, rerun execution, model/tokenizer use, Gemini activity, staging, commit, or push.
