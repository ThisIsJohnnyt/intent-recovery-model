# Auxiliary span guide revision-2 validation disagreement record

**Date:** 2026-08-14  
**Status:** Initial validation failed; sealed passes preserved unchanged; design-level fresh-coverage stop requires Johnny  
**ChatGPT pass SHA-256:** `55e688425a0e2cd5c409af58e4403ce117d8fe373014a4fed223e3805ce86e37`  
**Claude pass SHA-256:** `d7b1d73f14406b4b81da9327f26a79ea8fd6e8c32fa92fcdc27e5c5b57dc6943`  
**Governing guide SHA-256:** `d652cc02958e8575f24d20ab0ecc674f5ce7887f55fd0d8403d58d913dcd0923`  
**Frozen manifest SHA-256:** `6314b4336e0fac4a52735f0072ce82a2d5ba44f65a90ef536628a7d34d70dcb5`  

## 1. Scope and authority

This record compares the two sealed independent passes. Neither pass was edited after sealing. Boundaries
that differ only by one permitted terminal punctuation mark are treated as boundary-equivalent and are not
listed as disagreements by themselves.

The initial gate fails because exact record-level agreement was not reached. Guide Section 11.4 permits at
most one focused guide-correction round, but this record does not begin that round. A separate design-level
fresh-set coverage problem described in Section 5 must first return to Johnny.

Nothing here authorizes annotation edits, replacement or addition of fresh records, guide revision,
rerunning annotation, opening Gemini, model/tokenizer use, staging, commit, or push.

## 2. Sealing and comparison integrity

Both receipts match their annotation files exactly. Each pass contains 14 records and 78 propositions, but
the matching total is coincidental: proposition counts differ within four records and offset elsewhere.
Both passes were sealed before either reviewer opened the other's file. Claude's receipt accurately
discloses unavoidable prior memory of the ten-record regression disagreement and worked guide examples;
the four fresh records had no prior semantic annotation exposure.

Boundary-equivalent punctuation differences occur in comparators 040, 042, 056, 069, 075, 012, 008, and
030. They are accepted under guide Section 4 and omitted below unless the same proposition has another
substantive disagreement.

## 3. Result summary

- Exact agreement after boundary equivalence: **2 of 14 records** (`074`, `073`).
- Records with substantive disagreement: **12 of 14**.
- Proposition-count disagreement: `007` (ChatGPT 8 / Claude 9), `040` (10 / 11), `048` (5 / 4), and
  `075` (7 / 6).
- Global proposition count: 78 / 78.
- Gate result: **FAIL**. Required result is 100% record-level agreement.

## 4. Complete disagreement inventory

### Comparator 007

1. Claude separates `sunset chasers api integration` as an unfielded `fragment`; ChatGPT includes it in the
   API-alternative `question`. This changes proposition count, span, state, roles, and field obligations.
2. For `weather.gov or openweather?`, both create a question plus target-inferred compare task, but disagree
   on spans after the split, `object`/`candidate_set`/task roles, and allocation of `bullet` versus `action`.
3. The cloud-cover idea includes discourse marker `wait` for Claude and excludes it for ChatGPT; this is not
   a punctuation-only boundary difference. ChatGPT adds `quantity` for `percentage`; Claude does not.
4. The free-tier Azure/Heroku question has `object` plus `candidate_set` and `narrative`+`bullet` for ChatGPT,
   versus `candidate_set` and `narrative` only for Claude.

### Comparator 040

1. The pushed client call has `object`+`time` for ChatGPT and neither for Claude.
2. The missing plumber callback has `recipient`+`object` and `narrative`+`bullet` for ChatGPT, versus `actor`
   and `narrative` for Claude.
3. `still stressed about that` has `object`+`experiencer` for ChatGPT and no roles for Claude.
4. `remember to grab the mail` requires `narrative`+`action` for ChatGPT and
   `narrative`+`bullet`+`action` for Claude.
5. The trash-day question and its target-inferred confirmation task disagree on `object`, `candidate_set`,
   `time`, and whether the inferred task inherits resolved coreference.
6. The repeated plumber-callback fact has zero fields for ChatGPT versus `narrative`+`bullet` for Claude.
7. Claude creates an additional target-inferred plumber-follow-up task with `action`; ChatGPT does not.

### Comparator 042

1. `this time` receives `time` from ChatGPT and no qualifier from Claude.
2. The omitted complement of `the shorter agenda probably helped` is `resolved` for ChatGPT and `none` for
   Claude.

### Comparator 048

1. `Rina told Marcus...` has `speaker`+`recipient`+`object` for ChatGPT versus `actor`+`recipient` for Claude.
2. `He still needs the signed copy` has `object`+`possessor` and `object_modifier` for ChatGPT, versus
   `object`+`candidate_set` and no qualifier for Claude.
3. ChatGPT creates a separate epistemic fact for `I can't tell whether 'he' means Marcus or the client`,
   with `experiencer`+`candidate_set`, unresolved coreference, and narrative/bullet obligations. Claude
   creates no proposition for this clause and attaches candidate-set information to the preceding need fact.
4. The final ask task includes `object` for ChatGPT and not for Claude.

### Comparator 053

1. The first mileage-form task requires all three fields for ChatGPT versus narrative only for Claude.
2. Claude annotates `I know` as an unfielded fact with `actor`; ChatGPT does not create that proposition.
3. Both annotate the deadline restatement as a duplicate task with all three fields; its proposition number
   differs because of item 2.
4. `which is exhausting` has `experiencer` for ChatGPT and no roles for Claude.
5. The `don't let the mileage form disappear...` duplicate has resolved coreference and all three fields for
   ChatGPT, versus no coreference and zero fields for Claude.
6. The final text task excludes discourse marker `also`, adds `object`, and shares its temporal qualifier with
   an additional embedded lateness fact for ChatGPT. Claude includes `also`, has no `object`, and creates only
   the outer task. Thus ChatGPT includes a separate `I'll be ten minutes late` fact; Claude does not.

### Comparator 054

1. `The demo ran long` has `time` for ChatGPT and no qualifier for Claude.
2. `I lost the thread...` has `actor`+`object` for ChatGPT versus `actor` only for Claude.
3. The access-list question requires `narrative`+`bullet` for ChatGPT versus narrative only for Claude.
4. `call the dentist` treats the dentist as `recipient` for ChatGPT and `object` for Claude.
5. The porch-bulb task excludes `before I close this` and has no qualifier for ChatGPT; Claude includes that
   prefix and labels it `trigger`.

### Comparator 056

The dangling-reference task includes `object` for ChatGPT and not for Claude. Its punctuation-only boundary
difference is otherwise equivalent.

### Comparator 069

1. The first paperwork task includes `possessor` for ChatGPT and not for Claude.
2. That first task receives all three target fields for ChatGPT versus narrative only for Claude; both give
   the later deadline restatement all three fields.

### Comparator 074

Exact agreement on all eight tasks after no boundary adjustment. This record passes.

### Comparator 075

1. The second task uses a discontinuous span to inherit the common `Before the open house doors unlock`
   clause and therefore receives `trigger` for ChatGPT. Claude spans only `call the lighting supplier` and
   supplies no trigger. It treats the supplier as `object`; ChatGPT treats it as `recipient`.
2. The west-window uncertainty is a `question` with `object` for ChatGPT versus a `fact` with `actor` for
   Claude.
3. The optional visitor-card idea has no actor for ChatGPT versus `actor` for Claude.
4. ChatGPT separates the outer Ren speech report from the embedded Salma transfer, producing two overlapping
   facts. Claude creates one combined fact. The role allocation consequently differs: ChatGPT assigns
   `speaker`+`object` to the outer report and `actor`+`recipient`+`object` plus `object_modifier` to the
   transfer; Claude assigns `speaker`+`actor`+`recipient`+`object` to one row and no modifier.

### Comparator 012 (fresh)

1. `by 5` is `deadline` for ChatGPT and `time` for Claude in both unfinished departure/traffic thoughts.
2. The stove question excludes discourse marker `wait` and requires narrative+bullet for ChatGPT; Claude
   includes `wait` and requires narrative only.
3. The final unfinished traffic thought excludes `anyway` for ChatGPT and includes it for Claude; this is not
   a punctuation-only boundary difference.

### Comparator 073 (fresh)

Exact agreement on all seven tasks after no boundary adjustment. This record passes.

### Comparator 008 (fresh)

1. The opening memory thought has `experiencer` and treats demonstrative `that` as dangling for ChatGPT;
   Claude assigns no role and coreference `none`.
2. The slogan has `object`+`possessor` for ChatGPT versus no roles for Claude.
3. The long-term-memory reflection has `possessor`+`experiencer` and `time` for ChatGPT versus no roles or
   qualifier for Claude.

### Comparator 030 (fresh)

The vendor follow-up task includes shipment content as `object` for ChatGPT and not for Claude. All other
fields agree after boundary-equivalent terminal punctuation.

## 5. Design-level fresh-set coverage stop

The frozen selector assigned comparator 012 to `unfielded_independent_content`. That assignment was honestly
mechanical: its low-target-overlap heuristic did not claim to know annotation labels. The sealed semantic
passes now agree that all four comparator-012 propositions have at least one required output field. They also
agree that every proposition in the other three fresh records (073, 008, 030) has at least one field.

Therefore the four-record **fresh** sanity set contains no agreed proposition with
`required_output_fields: []`. The combined regression set does contain an agreed unfielded fragment
(`comparator:040`, `client call notes`), so revision 2's unfielded rule is exercised somewhere in the
14-record run, but not in the fresh subset required by guide Section 11.2.

Redefining `unfielded independent content` after seeing the annotations to mean merely low lexical overlap
would weaken a target-omission concept whose operational annotation is Section 3's empty field list. Swapping
records until one produces the desired annotation would be outcome-guided sampling. Neither is acceptable by
inference.

This is a major stop point under Johnny's standing risk-flagging rule. Before the one permitted guide-
correction round can be designed, Johnny must decide whether to:

1. require a newly authorized, predeclared supplemental fresh-record selection that restores actual
   unfielded coverage while preserving these sealed artifacts; or
2. explicitly amend the validation design so the agreed regression example supplies unfielded coverage for
   the combined set, acknowledging that fresh generalization of that convention was not tested.

Option 1 preserves the original intent and is recommended, but its selection protocol must avoid repeated
draw-and-annotate tuning. Neither option is authorized by the prior annotation permission.

## 6. Evidenced correction themes, not yet a revision

If Johnny resolves Section 5, the one allowed focused guide correction must be limited to ambiguities shown
above:

1. topic fragments, discourse markers, and nested/embedded predicates;
2. when a committed target action creates a separate overlapping inferred task;
3. role scope for subjects, report speech, recipients, themes, possession, experience, and candidate sets;
4. qualifier scope and precedence for generic time, deadlines, shared triggers, quantities, and object
   modifiers;
5. target-field allocation across duplicates/restatements and combined target items; and
6. deictic demonstratives, omitted arguments, and whether inferred tasks inherit source coreference.

The correction round may address these evidenced ambiguities only. It may not edit either sealed pass or
silently convert a disagreement into agreement.
