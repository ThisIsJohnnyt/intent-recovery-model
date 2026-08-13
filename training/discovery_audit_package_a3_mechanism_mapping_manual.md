# A3 — Input-Only Mechanism Mapping Coding Manual

**Operationalizes:** `training/intent_recovery_data_model_discovery_plan_chatgpt.md` §3, "A3. Input-only
mechanism mapping".

**Status: coding manual only.** No external sample has been coded. Every worked example below is freshly
hand-written for this manual, is not part of any frozen protected/acceptance evaluation set, and is not
drawn from any external dataset.

**Revised 2026-08-12** after ChatGPT's independent review found four real gaps in the first version,
addressed below: (1) the agreement metric was labeled "span-level" but was actually record-level presence/
absence; (2) several categories bundled distinct mechanisms into one flag with no subtype breakdown; (3)
"priority mechanism" and "interacting mechanisms" — both load-bearing for A5's 8/24 and 4/24 gates — were
never operationally defined; (4) the manual hard-wired "Claude and ChatGPT, jointly" as the disagreement
adjudicator, which risks sending real (possibly licensed/sensitive) candidate text to a hosted model without
the separate approval plan §5 requires.

**Revised again 2026-08-13** after ChatGPT's second independent review found the 2026-08-12 fix for (3) was
itself broken, plus two further real defects, all confirmed by Claude re-reading this document before
fixing: (a) the proposed "priority mechanism" set included every action-component subtype, so an ordinary
well-formed task ("Send Priya the invoice Friday") trivially contains multiple "priority" mechanisms and
satisfies the "interacting" gate without presenting any actual difficult-recovery phenomenon — this
defeated the entire point of A5's gates, not a minor imprecision; (b) the reviewer protocol told reviewers
to annotate spans on the "normalized input text," which — if that meant A2's collision-normalization — would
destroy the punctuation, case, and whitespace signals several categories directly depend on; (c) the
span-level F1 metric never required one-to-one matching between reviewers' spans, so a single broad span
from one reviewer could match multiple spans from the other and inflate agreement. All three fixed below.
`actor_recipient` (category 8) is also split into separate `actor` and `recipient` subtypes this round, for
role-binding fidelity the project's mission statement actually cares about.

**Corrected a third time, same day (2026-08-13, ChatGPT's third review):** the interaction test's
overlap/adjacency criterion was itself too permissive — proximity was listed as independently sufficient
evidence of dependency, when it's actually just one thing an adjudicator might consider. Fixed below, with
a worked example showing spans that are adjacent but not actually dependent. Also fixed a mislabeling in
the interaction manual's own worked example (`alternative` was used where `uncertainty_hedge` was the
correct subtype).

## Purpose

Once a candidate clears A1 (rights) and has a frozen A2 sample, two reviewers independently tag **spans**,
not inferred diagnoses, in the 24 input texts — before any target is revealed. This manual defines each tag
operationally so two independent reviewers converge, and states explicitly what must never be inferred.

## Hard rule, stated once and binding throughout

**Tag observable language, never the person.** Per plan §3 A3: "Do not infer disability, diagnosis, age,
stress, or cognitive status from language." A span like "I— wait, no, the other one" is tagged
`self_correction`; it is never grounds for tagging (anywhere, in any note) that the speaker is anxious,
fatigued, neurodivergent, or anything else about who they are.

## Tag categories and subtypes

Each top-level category below now has an explicit, enumerated subtype list — no category is left as one
catch-all flag when the plan's own bullet names multiple distinct phenomena under it.

| # | Category | Subtypes (each gets its own flag) |
|---|---|---|
| 1 | False starts / repairs | (single) `false_start_repair` |
| 2 | Repetition / restatement | (single) `repetition_restatement` |
| 3 | Incomplete thoughts | (single) `incomplete_thought` |
| 4 | Ambiguous references | (single) `ambiguous_reference` |
| 5 | Speaker / multi-person attribution | (single) `multi_person_attribution` |
| 6 | Topic shifts / mixed chronology | `topic_shift`, `mixed_chronology` — **two distinct subtypes** |
| 7 | Questions / uncertainty / unresolved states / conditions / alternatives | `question`, `uncertainty_hedge`, `unresolved_state`, `condition`, `alternative` — **five distinct subtypes** |
| 8 | Candidate action components | `actor`, `recipient`, `object`, `destination`, `quantity`, `deadline_time`, `condition_on_action` — `actor`/`recipient` split 2026-08-13 (were one merged `actor_recipient` subtype) |
| 9 | Observation / question / idea / action distinction | `observation`, `question_clause`, `idea`, `action` (one of these four, exclusive, per clause) |
| 10 | Emotionally compressed / hurried wording (textually observable only) | (single) `emotional_compression_textual` |
| 11 | Privacy / sensitivity / transcription artifacts / context dependencies | `privacy_sensitivity`, `transcription_artifact`, `context_dependency` — **three distinct subtypes** |

Definitions and worked examples for each subtype:

### 1. `false_start_repair`
*Positive:* "Can you send the— actually, can you just bring the folder tomorrow?"
*Negative:* "Can you send the folder, or bring it tomorrow?" — a genuine either/or, not an abandoned
restart.

### 2. `repetition_restatement`
*Positive:* "I need to call the dentist. ... Don't let me forget the dentist thing."
*Negative:* "I need to call the dentist, then the vet." — two distinct tasks.

### 3. `incomplete_thought`
*Positive:* "If the shipment doesn't arrive by Friday then I don't even know—"
*Negative:* "If the shipment doesn't arrive by Friday, call the supplier." — complete conditional (tag as
`condition` under category 7 instead, if the condition itself is unresolved — see below).

### 4. `ambiguous_reference`
*Positive:* "Tell her I'll bring it on Tuesday." (no antecedent anywhere in the input)
*Negative:* "Tell Priya I'll bring the folder on Tuesday. She said she needs it by then." — recoverable.

### 5. `multi_person_attribution`
*Positive:* "Marcus said he'd handle the invoice. I still need to call the vendor myself."
*Negative:* a single-speaker monologue with no other person mentioned.

### 6a. `topic_shift`
*Positive:* "Dinner reservation for 7. Also — remembered this morning I never replied to Dana's email."
*Negative:* "First I called the bank, then I emailed Dana about the same invoice." — one topic.

### 6b. `mixed_chronology`
*Positive:* "Forgot to mention — the thing I said was done yesterday, I actually did that this morning."
*Negative:* a strictly forward-moving narration, even across multiple topics.

### 7a. `question`
*Positive:* "Should we just replace the fixture?"
*Negative:* "We should replace the fixture." — a stated idea/decision, not an open question.

### 7b. `uncertainty_hedge`
*Positive:* "Not sure if the meeting's Tuesday or Wednesday."
*Negative:* "The meeting is Tuesday." — no hedge marker.

### 7c. `unresolved_state`
*Positive:* "Still waiting to hear back from the landlord."
*Negative:* "The landlord got back to me — we're all set."

### 7d. `condition`
*Positive:* "If the shipment doesn't arrive by Friday, call the supplier." (the condition itself, distinct
from whether it's ever resolved)
*Negative:* an unconditional statement.

### 7e. `alternative`
*Positive:* "Either push the meeting to Thursday or just do it over email."
*Negative:* a single course of action with no stated alternative.

### 8. Action components — `actor` / `recipient` split 2026-08-13
*Positive:* "Send Priya the three invoices to the shared drive by Friday" → `actor` (implicit "I," the one
doing the sending), `recipient` (Priya), `object` (three invoices), `destination` (shared drive),
`deadline_time` (Friday). `actor` and `recipient` are tagged separately even when one is implicit — role-
binding fidelity (who does something vs. who it's done to/for) is exactly the kind of distinction the
plan's own action-component list is trying to preserve, and merging the two loses it.
*Negative:* "Send the invoices" tagged with an inferred `recipient` — the input never names one; mark only
`object` (and the implicit `actor`) present.

**Note: action-component subtypes are not "priority mechanisms"** (see the redefinition below) — a plain,
well-formed task with a clear actor/object/deadline is normal task structure, not itself a difficult
recovery phenomenon. They remain useful, scored tags (A4 depends on them for target-component-survival
scoring) but do not feed A5's 8/24 or 4/24 gates.

### 9. `observation` / `question_clause` / `idea` / `action`
*Positive set:* "The kitchen light's been flickering" (`observation`) / "Should we just replace the
fixture?" (`question_clause`) / "Could repaint the hallway while we're at it" (`idea`) / "Buy a new light
fixture Saturday" (`action`).
*Negative:* tagging "Should we just replace the fixture?" as `action` — it is unresolved into a task.

### 10. `emotional_compression_textual`
*Positive:* "ok ok ok — pick up dry cleaning, DON'T forget this time, call mom, ugh where's my—"
*Negative:* inferring "the speaker sounds anxious" — a diagnosis, prohibited by the hard rule above.

### 11a. `privacy_sensitivity`
*Positive:* a specific health condition, account number, or legal matter named in the input.
*Negative:* a generic, non-identifying mention ("doctor's appointment" with no further detail).

### 11b. `transcription_artifact`
*Positive:* "um so basically the the thing with um the account" (repeated tokens, filler residue).
*Negative:* deliberate authorial repetition for emphasis in clearly-typed text — context matters.

### 11c. `context_dependency`
*Positive:* "the thing with the blue folder" (only the author would understand the referent).
*Negative:* a reference fully specified within the input itself.

## Priority and interacting mechanisms — operational definitions (proposed, not plan-given)

The plan's A5 thresholds ("8 of 24 inputs contain one or more priority mechanisms," "4 of 24 contain
interacting mechanisms") depend on both terms being defined before any real sample is coded. **The plan
itself does not define either term** — this is this package's own proposed operational definition, offered
for Johnny's and ChatGPT's confirmation before it governs a real A5 gate, not an authoritative reading of
the plan.

**Priority mechanisms — corrected 2026-08-13.** The 2026-08-12 version included the six category-8
action-component subtypes in "priority," which ChatGPT's second review showed makes the gates nearly
trivial: an ordinary, well-formed task like "Send Priya the invoice Friday" contains `recipient`, `object`,
and `deadline_time` — three "priority" subtypes by the old definition — and satisfies the old "two or more
co-occur" interaction rule without containing any genuinely difficult language at all. That defeats what
A5's gates exist to measure (whether a candidate's inputs actually contain the project's hard recovery
phenomena, not just whether they contain ordinary complete tasks).

**Priority mechanisms (corrected set):** only the subtypes that are themselves difficult-recovery
phenomena — `false_start_repair`, `incomplete_thought`, `ambiguous_reference`, `multi_person_attribution`,
`topic_shift`, `mixed_chronology`, `question`, `uncertainty_hedge`, `unresolved_state`, `condition` (7d —
an unresolved conditional in the source, distinct from `condition_on_action`), `alternative`. **Excluded**:
all seven category-8 action-component subtypes (`actor`, `recipient`, `object`, `destination`, `quantity`,
`deadline_time`, `condition_on_action` — ordinary task structure, not a difficulty phenomenon on its own),
`repetition_restatement`, the four category-9 clause-type tags, `emotional_compression_textual`, and all
three category-11 subtypes. A record counts toward the "8 of 24" gate if it contains **at least one**
priority-mechanism span, under independent adjudication — this part is unchanged from 2026-08-12.

**Interacting mechanisms — corrected 2026-08-13.** The old definition ("two or more distinct priority
subtypes anywhere in the record") is also too permissive on its own terms once priority is narrowed above —
a long note easily contains two unrelated difficult phenomena (e.g. a topic shift on one line, an
unrelated hedge three lines later) with no actual interaction between them. "Interacting" should mean what
it says: recovering one mechanism correctly depends on the other, not that both merely appear somewhere in
the same note.

**Corrected again 2026-08-13 (same day, third review)**: the version above listed overlap/adjacency as one
of three *independently sufficient* ways to satisfy the dependency test. ChatGPT's review correctly pointed
out that proximity alone doesn't establish dependency — two unrelated priority phenomena can simply sit
next to each other in one sentence with no actual link ("Not sure about Tuesday — Marcus is coming by
too," where the uncertainty is about the day and Marcus's visit is an unrelated aside that merely happens
to be adjacent). Overlap and adjacency are now **evidence the adjudicator weighs**, never an automatic
qualifier on their own.

A record contains interacting mechanisms only if the adjudicator affirmatively establishes, for that
specific pair of spans, that **recovering one mechanism changes, constrains, or depends on recovering the
other** — not merely that both are present, and not merely that they sit near each other. Overlap or
direct adjacency may be considered as supporting evidence toward that judgment, but never substitutes for
it; a pair judged to lack real dependency does not count no matter how close together the spans sit.

*Positive (interacting):* "Not sure if it was Marcus or Priya who said we could push the deadline" — the
`uncertainty_hedge` (not sure which person) directly governs the `multi_person_attribution` (who said
what); recovering the attribution requires resolving the uncertainty first — an actual dependency, not just
proximity. **Corrected 2026-08-13**: the prior version of this example mislabeled the "Marcus or Priya"
choice as the `alternative` subtype; per this manual's own §7e definition, `alternative` is a stated
alternative *course of action* ("push the meeting to Thursday or do it over email"), not uncertainty about
*which person* did something — that is `uncertainty_hedge` (§7b). The interacting pair here is
`uncertainty_hedge` + `multi_person_attribution`.
*Negative (adjacent but not dependent, does NOT count):* "Not sure about Tuesday — Marcus is coming by
too." — an `uncertainty_hedge` (Tuesday) sits directly adjacent to a `multi_person_attribution`-adjacent
mention (Marcus), in the same sentence, but the uncertainty is about the day, not about Marcus, and
resolving one has no bearing on the other. Adjacent, but not interacting — exactly the case the pure
overlap/adjacency rule would have wrongly counted.
*Negative (mere co-occurrence, does NOT count):* "Dinner's at 7. Also not sure if I already replied to that
email from last week." — a `topic_shift` (dinner → email) and an `uncertainty_hedge` (the reply) both
appear in the record, but about unrelated topics with no dependency between them.

A record counts toward the "4 of 24" gate only under this dependency test, under independent adjudication.
Because this test now turns on adjudicator judgment rather than a mechanically checkable proximity rule,
the adjudicator's one-line rationale (required by the reviewer protocol below) is what makes a counted
interaction auditable — a bare "yes, interacting" without the stated dependency is not sufficient
documentation.

## Reviewer protocol

1. Two reviewers work independently on the same frozen, input-only view (targets remain quarantined per A2
   step 8). Neither sees the other's tags until both are complete.
2. Each reviewer records spans with start/end offsets in the **original input text** — never A2's
   collision-normalized text. **Corrected 2026-08-13**: an earlier version of this line said "normalized
   input text," which, if read as A2's `normalize_for_collision()` output, would strip exactly the signals
   several categories depend on (question marks for `question`, repeated punctuation and capitalization for
   `emotional_compression_textual`, capitalization/name boundaries for `multi_person_attribution`,
   whitespace/dash patterns for `false_start_repair`). Reviewers work from a stable, lossless view of the
   candidate's actual input text — a fixed canonical form (e.g. Unicode NFC, consistent line endings) is
   fine if applied identically to the whole record so offsets stay meaningful, but case, punctuation, and
   whitespace must never be stripped from what reviewers see. Each span also carries the specific subtype
   from the table above (not just the top-level category).
3. **Two distinct agreement metrics, reported separately — not conflated:**
   - **Span-level agreement:** for each subtype, compute span-level F1 using **one-to-one matching** —
     sort all candidate (reviewer-A-span, reviewer-B-span) pairs of the same subtype by overlap fraction
     descending, then greedily match each span to at most one counterpart, highest-overlap pairs first,
     removing both from further consideration once matched. **Corrected 2026-08-13**: the original version
     didn't specify one-to-one matching, so a single broad span from one reviewer could match several
     narrower spans from the other and inflate agreement — greedy one-to-one matching closes that. A
     matched pair counts as a true positive only if overlap is **at least 50%** of the shorter span's
     length (unchanged, fixed threshold, predeclared before any real disagreement is seen); every unmatched
     span is a false positive or false negative for its reviewer. This is what "span-level reviewer
     agreement" in the plan actually requires, and is distinct from —
   - **Record-level presence agreement:** for each subtype, Cohen's kappa over a record-level presence/
     absence matrix (did each reviewer mark this subtype present *anywhere* in this record). This is the
     granularity A5's own thresholds are phrased at ("contain one or more priority mechanisms"), so it is
     reported too, but never presented as span-level agreement — the two measure different things and an
     earlier version of this manual conflated them.
4. **Adjudication:** any record where the two reviewers disagree (at either the span or record-presence
   level) goes to adjudication. **The adjudicator is not decided by this document.** Per plan §5's
   requirement — never send private, licensed, or sensitive text to a hosted model without Johnny's
   explicit approval and a completed terms/privacy review — and per Johnny's 2026-08-12 disposition, no
   default adjudicator (AI or otherwise) is assumed here. Johnny must separately approve who serves as
   adjudicator for a specific real candidate, informed by that candidate's own A1 privacy/rights findings,
   at the point a real audit actually begins. Adjudication never revises the frozen sample or drops a
   disputed record — it only resolves the tag.
5. Record **prevalence** (how many of the 24 records contain each subtype at least once) and
   **co-occurrence** (which subtypes tend to appear together) — both feed directly into the A5 decision
   thresholds, using the priority/interacting definitions above.

## Annotation schema (per record)

```json
{
  "record_id": "...",
  "reviewer_id": "...",
  "spans": [
    {"start": 0, "end": 0, "category": "false_start_repair", "note": ""}
  ],
  "subtype_present": {
    "false_start_repair": false, "repetition_restatement": false, "incomplete_thought": false,
    "ambiguous_reference": false, "multi_person_attribution": false,
    "topic_shift": false, "mixed_chronology": false,
    "question": false, "uncertainty_hedge": false, "unresolved_state": false, "condition": false, "alternative": false,
    "actor": false, "recipient": false, "object": false, "destination": false, "quantity": false, "deadline_time": false, "condition_on_action": false,
    "observation": false, "question_clause": false, "idea": false, "action": false,
    "emotional_compression_textual": false,
    "privacy_sensitivity": false, "transcription_artifact": false, "context_dependency": false
  },
  "priority_mechanism_present": false,
  "interacting_mechanisms_present": false
}
```

`priority_mechanism_present` and `interacting_mechanisms_present` are derived fields (computed from
`subtype_present` using the definitions above), included explicitly so A5's gate counts are a direct read
of the schema, not a re-derivation someone could get wrong later.

## What this manual does not do

It does not classify targets (that is A4), does not decide dataset fit (that is A5), and does not itself
touch any external sample — it is the instrument two future reviewers would apply to a real A2 sample, once
that sample exists under separate authorization, with an adjudicator Johnny separately approves at that
time.
