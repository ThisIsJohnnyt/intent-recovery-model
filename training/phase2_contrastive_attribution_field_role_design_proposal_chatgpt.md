# Phase-2 Follow-up: Contrastive Attribution and Field-Role Design Proposal

**Date:** 2026-08-09  
**Author:** ChatGPT  
**Status:** Design proposal for independent cross-review; not a corpus patch  
**Evidence base:** `main` at `398874504f2ea3bc8a710a2de56225381ea3900f`  
**Governing decision memo:** `phase2_seed17_p2d_postmortem_final_decision_memo_chatgpt.md`, SHA-256 `0c6260b081df1e71951d07c3fc8f9d4d71d5db75dc8f4e3870451d2d3d10b716`

## 1. Decision proposed

Advance a minimal six-record design to repository-level cross-review:

- add exactly four contrastive `multi_person_attribution` candidates;
- consider target-only remediation for exactly two existing `cross_field_completeness` records;
- preserve the valid Rina/Marcus record byte-for-byte;
- preserve both effective `two_unrelated_tasks` additions byte-for-byte; and
- make no other corpus, benchmark, prompt-contract, split-policy, or training-horizon change.

This proposal is intentionally narrow. It addresses the attribution boundary exposed by protected probe 06 and the field-role pressure identified in the P2-D postmortem, while protecting the probe-13 repair.

## 2. Authorization boundary

Johnny authorized **proposal design only**. This document does not authorize:

- creating, changing, or deleting corpus records;
- deriving or writing processed train/validation splits;
- training, inference, benchmark execution, evaluation, or scoring;
- a rerun of the closed seed-17 package;
- seed 73;
- checkpoint selection;
- commit or push;
- export, deployment, activation, or production promotion.

The next permitted action is independent, read-only cross-review and exact repository mapping by Claude.

## 3. Design hypothesis

The next curriculum should teach two separable rules:

1. **Attribution rule:** resolve a pronoun only when the source provides adequate evidence. Preserve uncertainty when it does not. Treat separate pronouns in the same note independently.
2. **Field-role rule:** preserving a fact in the narrative does not automatically justify restating it as a bullet. A bullet requires an actionable role, a decision-relevant constraint, preserved uncertainty, or another explicit contract-required purpose.

The proposal does not claim that these mechanisms are proven causes of the Phase-2 regression. They are the smallest evidence-supported intervention targets.

## 4. Frozen records and invariants

| Item | Required disposition | Reason |
|---|---|---|
| Existing Rina/Marcus `multi_person_attribution` record | Preserve byte-for-byte | Its earlier pronoun is reasonably resolved from gender agreement; its later Marcus-or-client ambiguity is correctly preserved. It is not a bad label. |
| Two Phase-2 `two_unrelated_tasks` additions | Preserve byte-for-byte | Their realized training exposure directly supports the repair of protected probe 13. |
| Protected benchmark records, including probes 06, 09, and 13 | No changes | The proposal must change teaching data, not redefine success. |
| Prompt and v2 output contract | No changes | Contract changes would confound the curriculum hypothesis. |
| Existing split policy | No changes during design | Any need to alter split logic requires separate evidence and authorization. |

## 5. Four-case attribution contrast

The text below is a semantic design, not final JSONL. Proposal-local labels `AT-C1` through `AT-C4` are not repository IDs. Exact wording may be adjusted during static review only to remove duplication, leakage, unnatural phrasing, or schema conflicts without changing the required semantic distinction.

### AT-C1 — Earlier pronoun resolvable to the second-named person

**Candidate source**

> Maya told Owen the exhibit plan was approved after he followed up with the museum. The final diagram is in the shared folder. Ask Maya to send Owen the access link.

**Required interpretation**

- `he` refers to Owen based on the available gender cue.
- The exhibit plan is approved.
- The final diagram is in the shared folder.
- The action is to ask Maya to send Owen the access link.

**Required target behavior by field**

| Field | Required content |
|---|---|
| Narrative | May explicitly resolve the earlier pronoun as "Owen followed up with the museum." Preserve the approval, diagram location, and requested action. |
| Bullets | Preserve the approval, diagram location, and requested action. Do **not** create a standalone bullet merely to echo that Owen followed up. |
| Actions | Include only the request for Maya to send Owen the access link. |

**Failure conditions**

- assigns the follow-up to Maya;
- leaves the resolvable pronoun ambiguous;
- creates a standalone non-actionable "Owen followed up" bullet; or
- drops or changes the requested action.

### AT-C2 — Earlier pronoun genuinely unresolved

**Candidate source**

> Casey told Morgan the exhibit plan was approved after they followed up with the museum. The note does not say whether "they" means Casey or Morgan. The final diagram is in the shared folder. Ask Casey to send Morgan the access link.

**Required interpretation**

- The source does not establish whether Casey or Morgan followed up.
- The uncertainty must remain explicit.
- The exhibit plan is approved and the diagram is in the shared folder.
- The action is to ask Casey to send Morgan the access link.

**Required target behavior by field**

| Field | Required content |
|---|---|
| Narrative | State that the plan was approved and that the source does not identify whether Casey or Morgan followed up. Preserve the diagram location and action. |
| Bullets | An uncertainty bullet is permitted because it preserves a decision-relevant unresolved attribution. Do not choose Casey or Morgan. |
| Actions | Include only the request for Casey to send Morgan the access link. Do not invent an action to determine who followed up. |

**Failure conditions**

- resolves `they` to either person;
- removes one candidate from the uncertainty;
- invents a clarification task not requested by the source; or
- drops or changes the actual requested action.

### AT-C3 — Earlier pronoun resolvable; later pronoun explicitly ambiguous

**Candidate source**

> After Joel called security, Priya told him the venue was unlocked. The next line says, "He still needs the access badge," but the writer cannot tell whether that means Joel or the courier. Ask Priya to clarify who needs the badge.

**Required interpretation**

- The earlier `him` refers to Joel.
- The later `He` remains unresolved between Joel and the courier.
- These are separate attribution decisions; resolving the first must not resolve the second.
- The action is to ask Priya who needs the badge.

**Required target behavior by field**

| Field | Required content |
|---|---|
| Narrative | May state that Priya told Joel the venue was unlocked. Must explicitly preserve the Joel-or-courier uncertainty about the badge. |
| Bullets | Preserve the venue status, the badge uncertainty, and the clarification request. Do **not** create a standalone bullet merely stating that Joel called security. |
| Actions | Include only the request to ask Priya who needs the badge. |

**Failure conditions**

- fails to resolve the earlier `him` to Joel;
- assigns the badge need to Joel, the courier, Priya, or another person;
- carries the earlier resolution into the later clause;
- turns "Joel called security" into a standalone background bullet; or
- changes the clarification target from Priya.

### AT-C4 — Order-swapped control; resolvable to the first-named person

**Candidate source**

> Owen told Maya the exhibit plan was approved after he followed up with the museum. The final diagram is in the shared folder. Ask Maya to send Owen the access link.

**Required interpretation**

- `he` still refers to Owen, but Owen is now the first-named person.
- The target must not use "second-named," object-of-`told`, or nearest-name position as a shortcut.
- All non-attribution content and field roles should match AT-C1.

**Required target behavior by field**

| Field | Required content |
|---|---|
| Narrative | May explicitly resolve the earlier pronoun as "Owen followed up with the museum." Preserve the approval, diagram location, and action. |
| Bullets | Match AT-C1's semantic bullet roles. Do **not** add a standalone follow-up bullet. |
| Actions | Include only the request for Maya to send Owen the access link. |

**Failure conditions**

- assigns the follow-up to Maya;
- changes the resolution merely because name order changed;
- produces a materially different field shape from AT-C1 without source-based justification; or
- drops or changes the requested action.

## 6. Contrast-set balance

| Property | AT-C1 | AT-C2 | AT-C3 | AT-C4 |
|---|---|---|---|---|
| Earlier pronoun outcome | Resolve | Preserve uncertainty | Resolve | Resolve |
| Correct referent position | Second named | Neither | First named in its sentence context | First named |
| Later identity ambiguity | None | None | Preserve | None |
| Gender cue available | Yes | No | Yes/contextual | Yes |
| Background clause must stay out of bullets | Yes | Not the main test | Yes | Yes |
| Requested action survives | Yes | Yes | Yes | Yes |

The set intentionally prevents four unsafe shortcuts:

- always select the second-named person;
- always select the nearest name;
- always preserve every pronoun as ambiguous; or
- always convert resolved/background clauses into bullets.

The set does not establish that gender alone is the project's general attribution policy. Gender agreement is one legitimate textual cue represented in a balanced set that also contains genuine uncertainty and order reversal.

## 7. Field-role remediation design

Claude should first map the evidence labels "curriculum addition #9" and "curriculum addition #10" to their exact repository IDs and current source/target fields. No edit should be drafted until that mapping is verified.

### Existing `cross_field_completeness` addition #9

Evidence identified three target patterns:

| Content | Proposed role | Design requirement |
|---|---|---|
| Ren reported that Salma handed spare clips to the installation lead | Narrative by default | Do not repeat as a bullet unless the source or contract gives it a decision-relevant role. Preserve speaker and actor attribution in the narrative. |
| Whether the west window was measured or only photographed | Preserved uncertainty | Keep unresolved. A bullet is acceptable only if static review establishes that it is a required uncertainty/decision constraint; otherwise keep it in narrative. |
| Folding screens looked uneven after setup | Narrative observation | Do not create a standalone bullet merely because the observation appears in the narrative. If the source separately requests inspection or correction, express that request — not the observation — as the action. |

### Existing `cross_field_completeness` addition #10

Evidence identified three target patterns:

| Content | Proposed role | Design requirement |
|---|---|---|
| Jae reported that the vendor changed the north gate code | Narrative by default | Preserve attribution in narrative. Do not echo it as a bullet unless it constrains a decision or requested task. |
| Whether the vendor tested the backup keypad | Preserved uncertainty | Keep unresolved. A bullet is acceptable only with a contract-based uncertainty/decision role. Never infer that testing occurred. |
| Lobby smelled like fresh paint | Narrative observation | Do not create a standalone bullet unless the source makes it operationally relevant. Do not invent a ventilation, inspection, or safety action. |

### Remediation limits

- Target-only changes are preferred; source text should remain unchanged unless static review proves the intended completeness lesson cannot be expressed consistently.
- Remove or rewrite only bullets that lack a field-role justification.
- Preserve all source facts in the narrative.
- Preserve every explicit uncertainty without resolving it.
- Preserve every requested action exactly.
- Do not turn observations into invented tasks.
- Do not use the remediation to add new attribution examples or unrelated curriculum coverage.

## 8. Proposed change budget

| Change class | Maximum | Notes |
|---|---:|---|
| New `multi_person_attribution` records | 4 | One implementation candidate for each of AT-C1 through AT-C4. |
| Existing target-only revisions | 2 | The two mapped `cross_field_completeness` additions only. |
| Existing source revisions | 0 expected | Any exception requires a separate, record-specific justification and Johnny's approval. |
| Existing record deletions | 0 | Rina/Marcus and probe-13 corrective records remain intact. |
| Benchmark/rubric/prompt changes | 0 | Out of scope. |

The intended future split membership for all four new attribution candidates is **training**, with no validation-set replacement or benchmark inclusion. This is a design requirement, not permission to derive a split. If the existing split policy cannot realize that membership without code or policy changes, work must stop for a separate decision.

## 9. Static acceptance gates

### Semantic gates

- Each candidate has exactly one agreed attribution policy outcome.
- AT-C1 and AT-C4 resolve Owen consistently despite name-order reversal.
- AT-C2 preserves Casey-or-Morgan uncertainty everywhere.
- AT-C3 resolves the earlier Joel reference and preserves the later Joel-or-courier uncertainty everywhere.
- No target relies on a second-named, nearest-name, or always-ambiguous shortcut.
- No target invents a person, answer, fact, or task.
- Every source-requested action appears once in `action_items` and is not merged with background content.

### Field-role gates

- Every proposed bullet has an explicit role: action, decision constraint, preserved uncertainty, or contract-required fact.
- Narrative completeness alone is not used as the reason for a bullet.
- Non-actionable follow-up, reported-speech, or observation clauses do not become standalone bullets by default.
- Every source fact remains recoverable from the full target even when it is removed from bullets.

### Preservation gates

- Rina/Marcus is byte-identical.
- Both effective `two_unrelated_tasks` additions are byte-identical.
- No unrelated corpus record changes.
- No protected benchmark, rubric, prompt, or contract changes.
- Expected regression implications are explicitly recorded for probes 06, 09, and 13.

### Repository and leakage gates

- Claude maps all six affected records to exact IDs and files.
- Near-duplicate checks cover the parent corpus, all candidate additions, protected probes, and acceptance probes.
- AT-C1/AT-C4 are permitted semantic counterparts but must not be accidental duplicates after normalization.
- AT-C3 must be reviewed especially carefully for excessive lexical or structural overlap with protected probe 06 and Rina/Marcus.
- Record schema, enums, chronology, target formatting, and category constraints pass existing static validators.
- Intended training membership is later confirmed against the realized processed split before any execution-package review.
- A record-level change manifest and exact hashes are produced before any corpus-edit approval.

Failure of any gate returns the work to design. It does not authorize training as a diagnostic shortcut.

## 10. Expected behavioral effects and regression risks

| Probe/behavior | Expected effect | Principal risk | Required protection |
|---|---|---|---|
| Protected 06 | Reduce forced Rowan attribution; preserve the stamped-copy ambiguity; suppress non-actionable "who asked" bullet | Overcorrecting to preserve every pronoun or selecting only gender-matching names | Balanced resolve/unresolved/order-swapped cases and exact pass-set gating |
| Protected 09 | No intended change | Field-role remediation could alter how incomplete or uncertain thoughts are surfaced | Preserve the existing probe-09 pass requirement; do not convert incomplete references into invented questions |
| Protected 13 | No intended change; retain repair | New curriculum composition could weaken two-task retention | Freeze both corrective examples and require both independent actions to survive |
| General attribution | Resolve only with evidence; preserve uncertainty otherwise | Replacing positional shortcut with gender-only or always-ambiguous shortcut | Contrast-set balance and unseen protected-set evaluation |
| General output shape | Fewer unjustified background bullets | Excessive bullet suppression and topic loss | Require all source facts to remain recoverable across the full target and all requested actions to survive |

## 11. Required independent cross-review output

Claude's read-only cross-review should return one bounded artifact containing:

1. exact repository IDs and paths for the frozen records and the two remediation targets;
2. a schema-level mapping from AT-C1 through AT-C4 to candidate record fields, without writing those records;
3. exact-current versus proposed field-role disposition for additions #9 and #10;
4. duplication, near-twin, and benchmark-leakage findings;
5. name-order, pronoun-cue, difficulty, and surface-form balance findings;
6. intended split feasibility under the unchanged split policy;
7. any disagreement with the semantic targets or change budget; and
8. a recommendation of **accept**, **revise**, or **reject** for corpus-edit authorization.

The review should not create corpus files, processed splits, tests, or execution artifacts.

## 12. Decision after cross-review

After Claude's review and ChatGPT's response, Johnny may choose one of three outcomes:

- **Accept design:** separately authorize exact corpus-record drafting and static implementation checks.
- **Revise design:** return specified cases or field-role decisions for another design pass.
- **Reject design:** close the proposed continuation with no corpus change or compute.

Even an accepted design does not authorize training or seed 73. Any future compute would require a separately reviewed and frozen experiment package, a new authorization chain, and new stop conditions.

## 13. Proposal disposition

**DESIGN COMPLETE FOR CROSS-REVIEW — FOUR ATTRIBUTION CASES, TWO TARGET-ROLE REMEDIATIONS, ZERO AUTHORIZED CORPUS CHANGES OR COMPUTE.**
