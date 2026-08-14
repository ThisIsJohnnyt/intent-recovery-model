# Auxiliary span-supervision annotation guide — revision 2

**Date:** 2026-08-14  
**Author:** ChatGPT  
**Status:** Independently verified by Claude with no disagreement; validation rerun not yet authorized  
**Supersedes for future annotation:** `controlled_seed17_aux_span_annotation_guide.md`  
**Historical preservation:** The original guide, both sealed round-one passes, receipts, and disagreement record remain unchanged.  

## 1. Scope and authority

This revision resolves the four convention gaps exposed by the first ten-record dual-annotation pilot. It defines future annotation policy and a bounded validation design only.

It does not authorize annotation, selection or inspection of fresh records, tokenizer/model use, pilot execution, full-corpus annotation, implementation, training, evaluation, checkpoint operations, seed 73, Gemini setup/generation/spending, staging, commit, or push.

## 2. Annotation unit and order

Annotate every semantically independent proposition expressed in the committed raw source, whether or not the committed target realizes it.

A proposition is the smallest source unit that asserts, asks, proposes, fragments, or assigns one predicate/state with the arguments and qualifiers required to interpret that predicate. Record propositions in the order of their first source character.

Create a separate proposition when a clause has its own predicate or independently classifiable state. Do not merge adjacent clauses merely because they concern the same topic, feed one target item, or appear in one sentence.

Examples of units that require separate propositions:

- a task plus an adjacent reason, price fact, emotional fact, or unresolved alternative;
- an imperative plus a factual consequence inside the same surface clause;
- a question plus a separately target-inferred check task when the committed target requires that action;
- an incomplete noun phrase or clause fragment, even when the committed target drops it;
- a literal or semantic restatement of an earlier proposition.

Do not create a separate proposition for a phrase that only supplies an argument or qualifier to another predicate and has no independently classifiable state.

Worked boundary example from comparator 048:

- `Rina told Marcus the draft was approved` is one `fact` proposition with no referential expression requiring resolution, so coreference is `none`;
- `he asked about it` has its own predicate and is a second `fact` proposition; both pronouns resolve from the full record, so coreference is `resolved`;
- do not widen the first proposition through `he asked about it`, because doing so would merge two independently classifiable predicates and make its coreference label boundary-dependent.

## 3. Unfielded clauses and target obligations

Every independent source proposition is annotated. A proposition omitted from the committed target receives:

```json
"required_output_fields": []
```

Zero field obligations do not make a proposition optional and do not permit folding it into an adjacent proposition.

Derive `narrative`, `bullet`, and `action` obligations independently for each proposition from the committed target:

- every committed action maps to exactly one `task` proposition;
- a non-task proposition never requires `action`;
- a task may have no `action` obligation if the target drops it;
- one target item may realize more than one source proposition, but each source proposition retains its own row and the appropriate shared field obligation;
- a target-inferred follow-up/check is represented by a separate overlapping `task` proposition when the target contains that action.

Do not change source-state labels to make the committed target look internally consistent. The annotation exposes source/target policy conflicts rather than resolving them.

## 4. Span boundaries, discontinuity, and restatement

Select the smallest exact source character interval carrying the proposition's predicate plus required explicit arguments and qualifiers. Ignore surrounding whitespace and terminal separators unless punctuation itself establishes question or fragment state.

Boundary-equivalent annotations may differ only by leading/trailing whitespace or one terminal `.`, `?`, `!`, comma, or semicolon and must map to the same non-punctuation token sequence.

Discontinuous spans are allowed only when one proposition is syntactically interrupted and its meaning cannot be captured by one continuous interval. Topic similarity, shared target realization, or restatement does not justify a discontinuous span.

Every restatement receives its own proposition and later source span. Link it backward with `duplicate_of` when it expresses the same proposition identity as an earlier row. The restatement may have zero field obligations. Never collapse an earlier and later restatement into one discontinuous proposition.

Overlapping spans are allowed only when the same source wording supports distinct proposition states/field obligations, such as an unresolved source question and a committed target action to check it.

## 5. State labels

Assign exactly one state:

- `fact`: asserted observation, event, condition, relation, preference, evaluation, or emotion;
- `question`: information is explicitly requested or alternatives remain interrogative;
- `fragment`: an incomplete thought lacking a recoverable predicate/state, including a standalone topic label dropped by the target;
- `tentative_idea`: a possible plan or suggestion presented as optional rather than assigned;
- `task`: an explicit or grammatically recoverable obligation, imperative, reminder, intention, or target-inferred follow-up action.

Question punctuation alone does not convert an explicit task into a question, and an unresolved question does not become a task unless the source or committed target separately supplies a follow-up action.

## 6. Role convention

Role labels are type presence only; do not create role-value spans. Allowed types remain:

`speaker`, `actor`, `recipient`, `object`, `possessor`, `experiencer`, `candidate_set`.

Apply these rules uniformly:

1. Every `task` proposition has `actor`.
2. If no actor is explicit, `actor` represents the implicit writer. This is mandatory, not optional.
3. Add `object` only when the source proposition explicitly expresses a patient, theme, content, or item acted on. Do not invent an implicit object merely because a task normally takes one.
4. Explicit named/pronominal actors also receive `actor`; the implicit-writer convention applies only when no actor is expressed.
5. `speaker` marks an explicit source-of-speech/report role, not the implicit writer of the note.
6. `recipient` requires an explicitly expressed destination person/group of transfer, speech, or communication.
7. `possessor` requires an explicitly expressed possession relation relevant to the proposition.
8. `experiencer` marks the entity experiencing an emotion, perception, or internal state.
9. `candidate_set` marks explicitly expressed competing candidate entities/referents. It is not added merely because an event outcome is uncertain.

Role sets contain each applicable type once and are serialized in the canonical order shown above.

## 7. Coreference convention

Coreference describes reference resolution, not general uncertainty.

Evaluate only referential expressions inside the proposition span—pronouns, demonstratives, anaphoric noun phrases, or omitted arguments whose interpretation depends on an antecedent. Resolve them using the full raw source record, not only the selected proposition span.

Assign exactly one status:

- `none`: the proposition contains no referential expression requiring antecedent resolution;
- `resolved`: all such expressions resolve uniquely from the raw source;
- `unresolved`: at least one expression has two or more plausible antecedents/candidate entities;
- `dangling`: at least one required antecedent is absent or unrecoverable from the raw source.

If multiple expressions yield different statuses, use precedence `dangling` > `unresolved` > `resolved` > `none`.

Do not mark `unresolved` merely because:

- a question asks which event occurred;
- two actions or states are alternatives;
- a value, decision, or outcome is unknown;
- an interrogative `who`/`what` requests new information without an ambiguous antecedent.

Examples fixed by this rule:

- “whether the west window was measured or only photographed” is event-alternative uncertainty, not coreference; absent another anaphor, status is `none`;
- in “Ask Rina who needs it,” `who` is interrogative rather than an ambiguous reference, while `it` is evaluated against the full record and is `resolved` if it uniquely refers to the signed copy;
- “he means Marcus or the client” is `unresolved` because the pronoun has an explicit candidate set;
- “ask her about the earlier version” is `dangling` when no antecedent for `her` exists in the record.

## 8. Qualifier convention

Qualifier labels are type presence only. Allowed types remain:

`time`, `deadline`, `destination`, `trigger`, `condition`, `quantity`, `purpose`, `object_modifier`.

Apply the smallest applicable semantic type and avoid redundant parent/subtype tagging for the same phrase:

1. `deadline`: a latest/required completion boundary. Do not also add `time` for that same phrase.
2. `trigger`: an event/state that starts or bounds when an action applies. Do not also add `time` for that same phrase unless a separate temporal phrase exists.
3. `time`: a temporal point, period, duration, sequence, or delay that is neither a deadline nor a trigger.
4. A numeric temporal duration/delay (for example, “ten minutes late”) is `time`, not also `quantity`.
5. `quantity`: a non-temporal count, amount, measurement, or cardinality.
6. `destination`: an endpoint/location of movement, transfer, placement, upload, or delivery.
7. `condition`: a prerequisite or contingency controlling whether the proposition applies.
8. `purpose`: an explicitly expressed intended goal or use.
9. `object_modifier`: a restrictive descriptor needed to identify the relevant object/version/state, not every adjective or descriptive fact.

Multiple qualifier types are allowed when distinct phrases—or one phrase with genuinely orthogonal meanings—independently satisfy different definitions. Do not add a second label solely because one type logically entails a broader type.

Worked `object_modifier` examples from the regression set:

- `Send the cracked display's warranty paperwork before Friday` receives `object_modifier` for `cracked display's` and `deadline` for the separate phrase `before Friday`;
- its restatement `Need to get that damage claim filed by Friday` receives `deadline` only; conventional type compounds such as `damage claim`, `warranty paperwork`, `translation headsets`, and `display easels` do not by themselves receive `object_modifier`;
- `document the repaired frames` receives `object_modifier` because `repaired` is an explicit state descriptor that distinguishes which frames are meant.

Qualifier sets contain each applicable type once and are serialized in the canonical order shown above.

## 9. Duplicate convention

`duplicate_of` is `null` or the ID of one earlier proposition in the same record. Use it only when the later proposition restates the same semantic proposition, not merely the same topic, entity, task family, or target field.

A duplicate proposition remains a full row with its own span, state, roles, qualifiers, coreference status, and target-field obligations. A duplicate does not create a second action identity unless the committed target independently contains a second action.

## 10. Canonical schema and ordering

Each record retains:

- `record_locator`;
- exact `source_input`;
- ordered `propositions`;
- `reviewer`;
- `review_status`.

Each proposition retains:

- sequential `proposition_id` (`p01`, `p02`, ...);
- ordered `source_character_spans` with exact `start`, `end`, and `text`;
- one `state`;
- canonical-order unique `roles`;
- canonical-order unique `qualifiers`;
- one `coreference_status`;
- backward-only `duplicate_of` or `null`;
- canonical-order unique `required_output_fields` in `narrative`, `bullet`, `action` order.

Validation fails closed on unknown fields or labels, duplicate keys, non-exact span text, overlapping/unsorted intervals within one proposition, forward/self duplicate links, duplicate roles/qualifiers/fields, non-task action obligations, or noncanonical ordering.

## 11. Bounded validation design

The revised guide must pass a sealed independent validation before generator readiness or full annotation.

### 11.1 Regression set

Re-annotate the same ten records from round one:

`007, 040, 042, 048, 053, 054, 056, 069, 074, 075`.

Because both reviewers have prior exposure, this is a regression test of the four known convention gaps, not a genuinely blind generalization test. Round-one annotations remain sealed historical evidence and must not be edited.

### 11.2 Fresh sanity set

Add 3–5 previously unannotated records from the remaining 68-record comparator pool. They must:

- exclude all Protected-16, Acceptance-10, and failed seven-record treatment-delta text;
- be frozen before either reviewer begins annotation;
- be selected through a predeclared mechanical/stress-coverage protocol that does not inspect reviewer outputs;
- cover, across the set, at least unfielded independent content, an implicit-actor task, a referential-expression case, and a qualifier-precedence case;
- remain unavailable to any future Gemini generator prompt or candidate context.

The selection manifest and exact records require a separate authorization before inspection or annotation.

### 11.3 Review protocol

ChatGPT and Claude annotate independently from the frozen guide, raw source, and committed target only. Each pass is sealed and SHA-256 reported before either reviewer opens the other's pass. Prior round-one files may be consulted only after both new passes are sealed.

The comparison reports every disagreement without post-hoc edits. Agreement requires, for every record:

- exact proposition count and order;
- boundary-equivalent spans under Section 4;
- exact state, roles, qualifiers, coreference, duplicate link, and field obligations;
- schema validation success.

### 11.4 Gate and correction limit

The initial revision-2 validation passes only at 100% record-level agreement across both the ten-record regression set and fresh sanity set.

If it fails:

1. preserve both sealed passes and create a disagreement record;
2. permit one focused guide-correction round addressing only evidenced ambiguity;
3. rerun the full frozen validation set independently under the corrected guide;
4. if exact agreement still fails, stop and return to Johnny. Do not begin generator readiness or full annotation.

No disagreement may be silently adjudicated into apparent agreement.

## 12. Relationship to generator readiness

Passing this guide-validation gate establishes that ChatGPT and Claude can apply the structural schema consistently. It does not validate Gemini, authorize candidate generation, or make generated candidates acceptable by default.

Only after the guide passes may a generator-readiness package freeze:

- the literal generator prompt;
- candidate JSON schema;
- leakage protections;
- rejection ledger;
- sealed review protocol;
- numeric gates and spending ceiling.

The generator remains a candidate source only. It receives no gold-label, reviewer, adjudication, or corpus-mutation authority.

## 13. Review checklist for Claude

Claude should independently verify:

- each rule resolves the corresponding round-one disagreement without post-hoc harmonization;
- unfielded-clause inclusion does not force phrases without predicates into artificial propositions;
- mandatory implicit actor does not create implicit objects;
- coreference examples follow the full-record/referential-expression definition;
- qualifier precedence is deterministic and does not suppress orthogonal labels;
- restatements cannot be hidden in discontinuous spans;
- the schema/order rules are implementable without model execution;
- the regression/fresh-set design adequately controls memory bias and protected-data leakage;
- the one-correction limit and exact-agreement gate are proportionate.

Material disagreement stops the revision and returns to Johnny. Review agreement does not authorize annotation, fresh-record inspection, tokenizer/model use, pilot execution, full annotation, implementation, compute, Gemini activity, staging, commit, or push.
