# Auxiliary span-supervision pilot annotation guide

**Frozen subset:** comparator 007, 040, 042, 048, 053, 054, 056, 069, 074, 075  
**Status:** Frozen before Claude's independent annotation pass  

Annotate propositions from the committed raw source only. Each proposition has ordered exact character
intervals, one state (`fact`, `question`, `fragment`, `tentative_idea`, `task`), role-type and qualifier-type
sets, coreference (`none`, `resolved`, `unresolved`, `dangling`), an optional earlier `duplicate_of`, and
required target fields (`narrative`, `bullet`, `action`).

Boundary rule: select the smallest exact source span carrying the predicate plus required arguments and
qualifiers. Ignore surrounding whitespace and terminal separators unless punctuation itself marks question
or incompleteness. Boundary-equivalent annotations may differ only by leading/trailing whitespace or one
terminal `.`, `?`, `!`, comma, or semicolon; they must map to the same non-punctuation token sequence.

Discontinuous spans are allowed only when interruptions or literal restatements jointly realize one
proposition. Overlapping spans are allowed when the committed target gives one source clause two distinct
states/field obligations (for example, an unresolved question and a target action to check it); the overlap
must be recorded, not silently collapsed.

Roles are types only: `speaker`, `actor`, `recipient`, `object`, `possessor`, `experiencer`, `candidate_set`.
Qualifiers are types only: `time`, `deadline`, `destination`, `trigger`, `condition`, `quantity`, `purpose`,
`object_modifier`. Implicit writer actors are uniformly labeled `actor` for tasks. Do not invent values.

Field obligations are derived from the committed target. Every action maps to exactly one task proposition.
A non-task cannot require `action`. A target-inferred check/follow-up may require a separate task proposition
overlapping its source question/fact; this exposes rather than resolves the corpus policy.

Reviewers annotate independently. Agreement requires exact proposition count/order, state, coreference,
duplicate link, and fields; boundary equivalence as defined above; and adjudication of every role/qualifier
set difference. No protected or acceptance text may be consulted as an annotation template.
