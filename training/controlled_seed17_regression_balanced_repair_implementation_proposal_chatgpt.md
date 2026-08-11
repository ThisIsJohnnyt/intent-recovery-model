# Regression-Balanced Repair — Implementation Proposal

**Date:** 2026-08-11  
**Author:** ChatGPT  
**Evidence commit:** `43f4fc41264469ac2848340c8bea8e216dba8368` on `main`  
**Accepted design:** `training/controlled_seed17_regression_balanced_repair_design_chatgpt.md`, SHA-256 `8d803ab08228e7a359145568e73cfac2fa13bb5416bcf4a1bc53ff288684fe2a`  
**Reference baseline:** `training/gold_v1.2.2_phase2_derived_candidate.jsonl`, 78 records  
**Status:** Reviewable implementation proposal awaiting Claude's independent review.  
**Non-authorization:** This document does not create or authorize JSONL, corpus mutation or derivation, split generation, training, inference, seed 73, checkpoint work, benchmark/rubric/contract changes, export, deployment, activation, cleanup, commit, or push.

## 1. Proposal summary

The 78-record baseline already contains clean reusable coverage for nine of the twelve B–D abstract templates. The implementation proposal therefore uses a seven-record delta, not the design ceiling:

- four exact audited reuses: AT-C1 through AT-C4;
- three genuinely new records: B1 deadline+destination, B3 condition+quantity, and C3 dangling references plus a supported condition;
- zero target-only corrections;
- zero P2-009/P2-010 treatment revisions;
- zero structural-group additions.

If a later corpus-implementation milestone is separately authorized and all seven records survive independent review unchanged, the proposed logical corpus shape would be the 78-record baseline plus seven additions, for 85 records before split derivation. This count is descriptive only; no candidate or split is created here.

## 2. Audit method

ChatGPT read all 78 baseline records and inventoried category, difficulty, source text, narrative, bullets, action items, bullet count, and action count. Coverage was then evaluated against each abstract template in the accepted design.

Classification meanings:

- **Clean reusable:** an existing record already teaches the template without a discovered defect.
- **Near coverage; no change:** related coverage exists but should not be edited or counted as the full template.
- **Defective coverage:** an existing target has a demonstrated record-level defect that may justify target-only correction.
- **Genuine missing coverage:** no existing record teaches the complete governed combination.

No defective baseline target was found that is both necessary and justified for this proposal. In particular, the failed treatment's P2-009/P2-010 revisions are not carried forward.

## 3. Coverage audit

### Group A — Attribution and ambiguity

| Template | Baseline evidence | Classification | Proposed disposition |
|---|---|---|---|
| A1: resolvable to second-mentioned person | Baseline has attribution records, but none provides the reviewed order-balanced A1 control shape without other confounds. | Genuine missing coverage | Exact reuse of AT-C1. |
| A2: genuinely unresolved earlier reference | Baseline Rina/Marcus preserves a later ambiguity, not the same unresolved-earlier-reference contrast. | Genuine missing coverage | Exact reuse of AT-C2. |
| A3: earlier resolvable, later explicitly ambiguous | Rina/Marcus is semantically valid but is also a high-overlap structural analogue of protected 06. Claude's independent token screen measured 0.576 Jaccard with identical 34-token counts under that tokenizer; prior committed postmortem evidence had already identified it as the sole close analogue. Its standalone attribution bullet and lack of a balanced surrounding set make it near coverage rather than the complete design template. | Near coverage; no change; explicit evaluation-contamination flag | Preserve Rina/Marcus unchanged; exact reuse of AT-C3; never treat protected 06 alone as independent proof of Group-A benefit. |
| A4: order-swapped control | No baseline order-swapped counterpart defeats name-position shortcuts. | Genuine missing coverage | Exact reuse of AT-C4. |

### Group B — Action completeness

| Template | Baseline evidence | Classification | Proposed disposition |
|---|---|---|---|
| B1: deadline + destination, with non-action observation | Baseline has deadlines, destinations, and observations, but not the complete single-task combination with both qualifiers preserved in the action. | Genuine missing coverage | Add RB-B1. |
| B2: recipient + object | Multiple clean cases, including “Send Omar the corrected total” and “Send Niko the updated link before lunch.” | Clean reusable | Preserve existing records; no addition. |
| B3: condition + quantity, with non-action observation | Baseline has conditions and quantities separately, but no clean action frame combining an event condition with an explicit quantity. | Genuine missing coverage | Add RB-B3. |
| B4: dense two-task qualifier control | Existing cross-field records preserve two separate qualified actions amid observations, ideas, and questions. | Clean reusable | Preserve existing records; no addition. |

### Group C — Source-state preservation

| Template | Baseline evidence | Classification | Proposed disposition |
|---|---|---|---|
| C1: incomplete thought plus separate task | Existing interrupted-thought records preserve the fragment and retain the separate task. | Clean reusable | No addition. |
| C2: open question plus supported check | Existing insurance-payment/shared-folder/venue-code records preserve questions and checks. | Clean reusable | No addition. |
| C3: dangling-reference task with a supported condition | “Ask her about the earlier version” cleanly preserves two references, but no baseline case also requires an unresolved condition/referent to survive intact in the action. | Genuine missing coverage | Add RB-C3; preserve existing dangling-reference records unchanged. |
| C4: tentative idea plus unrelated observation/task | Multiple clean idea/action and idea/observation records preserve tentativeness without promotion. | Clean reusable | No addition. |

### Group D — Structural behavior

| Template | Baseline evidence | Classification | Proposed disposition |
|---|---|---|---|
| D1: repeated reminder deduplicated | Two hard repeated-reminder records each produce one bullet and one complete action. | Clean reusable | No addition. |
| D2: eight tasks under seven-bullet ceiling | Existing expert simple-list record has seven bullets and eight distinct actions. | Clean reusable | No addition. |
| D3: six mixed ideas, exactly two tasks | Existing expert cross-field records contain six bullets and two separate complete actions. | Clean reusable | No addition. |
| D4: similar but distinct tasks | Existing equipment-crate/costume-box record preserves two actions with the same verb but different objects and destinations. | Clean reusable | No addition. |

### Audit conclusion

The structural failures observed in evaluation do not reflect an absence of clean baseline exemplars. Adding more D-group records now would be an unsupported volume response and would increase benchmark-mimicry risk. The proposal instead preserves the existing structural exemplars and requires any later execution design to evaluate their transfer explicitly.

### Protected-06 independence limitation

Rina/Marcus and protected 06 have clause-by-clause parallel structure. This was known qualitatively in the committed Phase-2 postmortem and is now quantified as high lexical overlap. The record is correctly labeled and must remain unchanged, but protected 06 is not a clean, structurally independent held-out test of whether the model learned the general attribution rule.

Consequences for this proposal:

- treatment's protected-06 gain remains an observed, intervention-aligned result, not causal proof;
- Group A is justified by the documented imbalance around a single close analogue and the need to defeat its positional shortcut, not by the protected-06 pass alone;
- no later outcome may claim general attribution improvement from protected 06 alone;
- any later execution design must predeclare structurally distinct attribution diagnostics, separately gated from the frozen benchmark, before compute; and
- Rina/Marcus must be flagged explicitly in every collision/leakage report rather than treated as an ordinary preserved record.

This limitation does not justify deleting or correcting Rina/Marcus, weakening the frozen benchmark, or treating new diagnostics as replacements for the complete governing gate set.

## 4. Exact reuse manifests — Group A

The four records below are proposed as byte-for-semantic-field reuse from `training/phase2_contrastive_attribution_composite_proposal.jsonl`. A later authorized implementation must copy `input`, `output`, `difficulty`, and `category` exactly and mechanically generate contract targets using the repository's existing migration code. No hand-edited target string is authorized by this proposal.

### RB-A1 — exact reuse of AT-C1

- **Primary mechanism:** `A_attribution`
- **Input SHA-256:** `c482efb9df7b65587f64683509ce94e34c82d968a6170259cb336d22eb1f4d2a`
- **Difficulty/category:** `hard` / `multi_person_attribution`
- **Input:** `Elena told Owen the exhibit plan was approved after he followed up with the museum. The final diagram is in the shared folder. Ask Elena to send Owen the access link.`
- **Narrative:** `Elena told Owen that the exhibit plan was approved after Owen followed up with the museum. The final diagram is in the shared folder. Elena should be asked to send Owen the access link.`
- **Bullets:**
  1. `The exhibit plan was approved.`
  2. `The final diagram is in the shared folder.`
  3. `Ask Elena to send Owen the access link.`
- **Actions:**
  1. `Ask Elena to send Owen the access link.`
- **Source-state inventory:** earlier `he` is resolvable to Owen; no unresolved question.
- **Task frame:** ask Elena / send / Owen / access link.
- **Forbidden:** assigning follow-up to Elena; leaving `he` unresolved; adding a standalone follow-up action/bullet; changing sender or recipient.
- **Control relationship:** order-balanced with RB-A4.
- **Expected protection:** attribution accuracy without name-position shortcut; action-role preservation.
- **Principal risk:** learning “second-mentioned person.”
- **Intended split membership:** training, subject to later unchanged-policy derivation verification.

### RB-A2 — exact reuse of AT-C2

- **Primary mechanism:** `A_attribution`
- **Input SHA-256:** `b7e5c42a67a8c3e35a0e41c713e41629fa01b9132e259595d4f10e8e4371c4a2`
- **Difficulty/category:** `hard` / `multi_person_attribution`
- **Input:** `Casey told Morgan the exhibit plan was approved after they followed up with the museum. The note does not say whether "they" means Casey or Morgan. The final diagram is in the shared folder. Ask Casey to send Morgan the access link.`
- **Narrative:** `Casey told Morgan that the exhibit plan was approved after one of them followed up with the museum. The note does not identify whether Casey or Morgan followed up. The final diagram is in the shared folder. Casey should be asked to send Morgan the access link.`
- **Bullets:**
  1. `The exhibit plan was approved.`
  2. `It is unclear whether Casey or Morgan followed up with the museum.`
  3. `The final diagram is in the shared folder.`
  4. `Ask Casey to send Morgan the access link.`
- **Actions:**
  1. `Ask Casey to send Morgan the access link.`
- **Source-state inventory:** `they` explicitly unresolved between Casey and Morgan.
- **Task frame:** ask Casey / send / Morgan / access link.
- **Forbidden:** resolving `they`; inventing a clarification task; losing either alternative; changing sender/recipient.
- **Control relationship:** unresolved counterpart to RB-A1/RB-A4.
- **Expected protection:** preserve genuine ambiguity without overgeneralizing to always-resolve.
- **Principal risk:** learning “they is always ambiguous.”
- **Intended split membership:** training, subject to later verification.

### RB-A3 — exact reuse of AT-C3

- **Primary mechanism:** `A_attribution`
- **Input SHA-256:** `82e96472d53e004233c5d99a77c100c0db772955744bc5b835f40fff880e5ab4`
- **Difficulty/category:** `expert` / `multi_person_attribution`
- **Input:** `After Joel called security, Priya told him the venue was unlocked. The next line says, "He still needs the access badge," but the writer cannot tell whether that means Joel or the courier. Ask Priya to clarify who needs the badge.`
- **Narrative:** `After Joel called security, Priya told Joel that the venue was unlocked. The note does not make clear whether Joel or the courier still needs the access badge. Priya should be asked who needs the badge.`
- **Bullets:**
  1. `The venue was unlocked.`
  2. `It is unclear whether Joel or the courier needs the access badge.`
  3. `Ask Priya who needs the access badge.`
- **Actions:**
  1. `Ask Priya who needs the access badge.`
- **Source-state inventory:** earlier `him` resolves to Joel; later `He` remains explicitly ambiguous between Joel and courier.
- **Task frame:** ask Priya / clarify / who needs access badge.
- **Forbidden:** carrying the earlier resolution into the later clause; assigning badge need; changing clarification target; background-only security action/bullet.
- **Control relationship:** mixed resolve/preserve case; complements existing Rina/Marcus without changing it.
- **Expected protection:** protected-06-style independent reference handling.
- **Principal risk:** lexical/structural proximity to protected 06. Independent review measured token Jaccard 0.318. This intentional analogy must be disclosed and must not be used to claim independent generalization from protected 06.
- **Intended split membership:** training, subject to later verification.

### RB-A4 — exact reuse of AT-C4

- **Primary mechanism:** `A_attribution`
- **Input SHA-256:** `74bad267e917bc13a2a5b731c29778b86cc59f0922309ccc9cd128de3047c23e`
- **Difficulty/category:** `hard` / `multi_person_attribution`
- **Input:** `Owen told Elena the exhibit plan was approved after he followed up with the museum. The final diagram is in the shared folder. Ask Elena to send Owen the access link.`
- **Narrative:** `Owen told Elena that the exhibit plan was approved after Owen followed up with the museum. The final diagram is in the shared folder. Elena should be asked to send Owen the access link.`
- **Bullets:**
  1. `The exhibit plan was approved.`
  2. `The final diagram is in the shared folder.`
  3. `Ask Elena to send Owen the access link.`
- **Actions:**
  1. `Ask Elena to send Owen the access link.`
- **Source-state inventory:** earlier `he` resolves to Owen, now first-mentioned.
- **Task frame:** ask Elena / send / Owen / access link.
- **Forbidden:** changing resolution because name order changed; assigning follow-up to Elena; changing field shape without source basis.
- **Control relationship:** order-swapped counterpart to RB-A1.
- **Expected protection:** defeat first/second-name and object-of-`told` shortcuts.
- **Principal risk:** near-duplication with RB-A1; intentional relationship must be explicitly allowlisted only for this pair.
- **Intended split membership:** training, subject to later verification.

## 5. Exact new-record manifests

These are exact proposed semantic records for review, but they are not JSONL and must not be copied into a corpus without separate authorization after review.

### RB-B1 — deadline and destination survive into action

- **Primary mechanism:** `B_action_completeness`
- **Proposed input SHA-256:** `c7b99e21ee543b93a91ce7967f0505dadbf5309f6ab53d152878409949faa3f9`
- **Difficulty/category:** `hard` / `cross_field_completeness`
- **Input:** `Before the service counter closes on Thursday, take the sealed calibration packet to the north depot. The lobby clock was six minutes slow.`
- **Narrative:** `Before the service counter closes on Thursday, take the sealed calibration packet to the north depot. The lobby clock was six minutes slow.`
- **Bullets:**
  1. `Take the sealed calibration packet to the north depot before the service counter closes on Thursday.`
  2. `The lobby clock was six minutes slow.`
- **Actions:**
  1. `Take the sealed calibration packet to the north depot before the service counter closes on Thursday.`
- **Source-state inventory:** one explicit task; one unrelated observation.
- **Task frame:** take / sealed calibration packet / north depot / before service counter closes / Thursday.
- **Bullet rationale:** task and observation are two distinct source ideas.
- **Forbidden:** dropping Thursday, closing condition, destination, sealed qualifier, or object; promoting clock observation; inventing repair/advice.
- **Expected protection:** acceptance `sdi2-02`-type destination retention; protected 10/11 qualifier survival without benchmark wording reuse.
- **Principal risk:** model may treat the observation as a second task or retain deadline only in narrative.
- **Intended split membership:** training, subject to later verification.

### RB-B3 — condition and quantity survive into action

- **Primary mechanism:** `B_action_completeness`
- **Proposed input SHA-256:** `f8ca8503089de9eea28ad8d410247a8609f90f49d6d83badbdd812a0d62b9545`
- **Difficulty/category:** `hard` / `cross_field_completeness`
- **Input:** `When the projector cart returns, place three labeled adapters in the locked drawer. The hallway smelled like floor polish.`
- **Narrative:** `When the projector cart returns, place three labeled adapters in the locked drawer. The hallway smelled like floor polish.`
- **Bullets:**
  1. `Place three labeled adapters in the locked drawer when the projector cart returns.`
  2. `The hallway smelled like floor polish.`
- **Actions:**
  1. `Place three labeled adapters in the locked drawer when the projector cart returns.`
- **Source-state inventory:** one condition-governed task; one unrelated observation.
- **Task frame:** place / three / labeled adapters / locked drawer / when projector cart returns.
- **Bullet rationale:** task and observation are two distinct source ideas.
- **Forbidden:** dropping condition, quantity, labeled qualifier, object, or destination; promoting smell observation; inventing cleaning/inspection.
- **Expected protection:** complete task-frame transfer under condition and quantity pressure.
- **Principal risk:** condition may be recast as a separate task or quantity may be lost in action.
- **Intended split membership:** training, subject to later verification.

### RB-C3 — dangling references plus supported condition

- **Primary mechanism:** `C_source_state`
- **Proposed input SHA-256:** `840ce909d62abef7df19ca10a732735c5f764c24d838938be5d41397804d16d1`
- **Difficulty/category:** `expert` / `dangling_reference`
- **Input:** `When they bring it back, give her the earlier one.`
- **Narrative:** `The earlier one should be given to her when they bring it back.`
- **Bullets:**
  1. `Give her the earlier one when they bring it back; the references are unresolved.`
- **Actions:**
  1. `When they bring it back, give her the earlier one.`
- **Source-state inventory:** unresolved `they`, `it`, `her`, and `earlier one`; supported conditional task.
- **Task frame:** give / unresolved recipient / unresolved earlier object / when unresolved actor brings unresolved object back.
- **Bullet rationale:** exactly one supported task; unresolved references are properties of that task, not additional topics.
- **Forbidden:** inventing people, plurality beyond the source grammar, object identity, ownership, relationship, location, answer, evaluation, or extra clarification task; dropping the condition from action.
- **Expected protection:** protected 16 and acceptance `sdi2-09`-type reference/condition preservation without copying their objects or syntax.
- **Principal risk:** the model may omit the condition, invent referents, or learn the bullet's scoped uncertainty tag as stock content rather than preserving the source state.
- **Intended split membership:** training, subject to later verification.

## 6. Provisional collision and leakage results

The three new inputs were checked read-only against:

- all 78 baseline inputs;
- all 16 protected inputs;
- all 10 acceptance inputs; and
- all 16 prior composite-proposal inputs.

No exact normalized input collision was found. Claude independently extended the token-Jaccard sweep to all seven records and the complete stated pool. The full findings are:

| Proposed ID | Maximum token Jaccard | Nearest reference class | Disposition |
|---|---:|---|---|
| RB-A1 | 1.000 token-set identity | RB-A4 intentional order-swapped control | Pair-specific disclosed relationship; never a broad allowlist |
| RB-A2 | 0.629 | RB-A1/AT-C family | Intended contrast-family similarity; requires phrase/structure audit |
| RB-A3 | 0.318 | protected 06 | Material evaluation-independence concern; explicitly limited above |
| RB-A4 | 1.000 token-set identity | RB-A1 intentional order-swapped control | Pair-specific disclosed relationship; never a broad allowlist |
| RB-B1 | 0.132 | protected 03 | Low provisional overlap; supersedes the earlier incomplete-sweep value 0.129 |
| RB-B3 | 0.079 | baseline/composite simple-list record | Low provisional overlap; rounded from Claude's independently recomputed 0.0789 |
| RB-C3 | 0.200 | baseline dangling-reference record | Intentional category-level similarity; requires stronger independent review |

Separately, the preserved baseline Rina/Marcus record measured 0.576 against protected 06 under Claude's tokenizer. A simpler ASCII-token screen produced a slightly different value because tokenization and mojibake handling were not identical; this reinforces the design requirement that normalization and tokenization be frozen before later checks.

These results are preliminary evidence only. They are not sufficient to authorize wording. A later static implementation must run predeclared exact, normalized, n-gram, token, and semantic-near-duplicate checks across the full collision universe, including prior rejected candidates.

## 7. Required static checker specification

A later corpus-implementation package must specify and test the following before writing a candidate:

### 7.1 Identity and schema

- Pin the 78-record baseline by canonical bytes and content fingerprint.
- Require exactly the reviewed top-level and output key sets.
- Validate category/difficulty enums.
- Generate `v1_target` and `v2_target` mechanically; parse both back to exact semantic equality.
- Reject duplicate inputs and duplicate full records.

### 7.2 Collision and leakage

- Normalize Unicode, case, whitespace, punctuation, and line endings using predeclared rules.
- Check exact normalized equality and containment.
- Check token and character n-gram similarity with thresholds fixed before execution.
- Check named entities, task objects, quantities, temporal phrases, clause order, and distinctive role combinations.
- Cover baseline, parent, historical/composite proposals, protected/acceptance benchmarks, prior candidates, and all seven proposed records.
- Permit only the intentional RB-A1/RB-A4 control relationship through an exact pair-specific review entry, never a broad allowlist.
- Always report Rina/Marcus versus protected 06 and RB-A3 versus protected 06 as named comparisons, regardless of generic threshold outcome.

### 7.3 Field-role and task-frame checks

- Compare every action with its manifest task frame.
- Require every supported predicate, object, recipient, destination, deadline, condition, quantity, and constraining purpose.
- Reject promotion of observations, ideas, questions, or incomplete fragments.
- Require exact intended action count and justified bullet count.

### 7.4 Source-state checks

- Require all unresolved alternatives/references to remain unresolved in every field.
- Reject invented identity, plurality, ownership, relationship, answer, evaluation, cause, chronology, confidence, or task.
- Require supported conditions to survive in actions.
- Verify cross-field non-contradiction.

### 7.5 Change-scope and split checks

- Derive from the reviewed 78-record baseline only.
- Append exactly the independently accepted records in reviewed order.
- Make no target correction unless separately accepted.
- Keep validation membership and split policy unchanged.
- Confirm intended training membership after derivation.
- Produce a record-level diff, canonical hashes, counts, and training-data fingerprint.
- Fail on any unreviewed path, record, field, count, membership, or fingerprint change.

## 8. Fifteen-gate disposition

| Design gate | Proposal status |
|---|---|
| Baseline/preserved records pinned | Defined; exact pins required in later package |
| Existing coverage audit | Completed in this proposal; requires independent re-audit |
| Delta within ceiling | PASS: 3 new + 4 reused, below 12 new + 4 reused |
| One primary mechanism per record | PASS by manifest |
| Group-A balance | Proposed via exact AT-C1–AT-C4 reuse |
| Group-B complete action frames | Proposed field-by-field; requires review |
| Group-C no invention | Proposed field-by-field; requires review |
| Group-D semantics and counts | Reuse existing clean coverage; no new records |
| Probe-13 repair records unchanged | Required; no proposed change |
| P2-009/P2-010 revisions excluded | PASS: no proposed carry-forward |
| Validation membership/split policy unchanged | Required |
| Benchmark/rubric/prompt/parser unchanged | Required |
| Collision/leakage/schema checks | Specified; later implementation required |
| Exact paths/counts/fingerprints declared before implementation | Deferred to later package by scope |
| Independent record-level agreement | Pending Claude review |

No gate marked “defined,” “proposed,” “required,” “deferred,” or “pending” is a pass for corpus implementation. Only a later reviewed package can close those gates.

## 9. Expected future delta if separately authorized

| Mechanism | Reused records | New records | Target corrections |
|---|---:|---:|---:|
| A attribution | 4 | 0 | 0 |
| B action completeness | 0 | 2 | 0 |
| C source state | 0 | 1 | 0 |
| D structural | 0 | 0 | 0 |
| **Total** | **4** | **3** | **0** |

The proposed seven-record delta is intentionally smaller than the twelve-new-record ceiling. It is also smaller and more mechanism-explicit than the failed treatment's six record-level changes because the four AT reuses are already independently authored artifacts and the three new records each fill one audited gap.

## 10. Requested independent review

Claude should independently:

1. re-audit the actual 78-record baseline and challenge every coverage classification;
2. verify the exact AT-C reuse bytes and input hashes;
3. review every new input/output field and manifest statement for semantic correctness;
4. challenge whether B1, B3, and C3 are genuinely missing rather than redundant;
5. run independent collision/leakage analysis, especially RB-C3 and AT-C3;
6. verify the seven-record delta, zero-correction claim, and 85-record descriptive count;
7. assess whether the checker specification closes all accepted design gates without hidden allowlists; and
8. identify any language that crosses into unauthorized JSONL, derivation, or compute.

Any material disagreement is work-stopping and returns to Johnny with both positions and evidence. Non-blocking wording or precision findings should still be corrected before the proposal advances.

## 11. Decision after review

If Claude independently agrees, this proposal becomes ready for Johnny's separate decision on a **corpus-implementation package**. That future package could create exact JSONL and static derivation artifacts only if explicitly authorized. Training and execution would remain separately prohibited until another reviewed package and authorization.

**Disposition:** BASELINE AUDITED — SEVEN-RECORD DELTA PROPOSED — FOUR EXACT REUSES, THREE GENUINELY NEW RECORDS, ZERO TARGET CORRECTIONS — NO JSONL CREATED — AWAITING CLAUDE INDEPENDENT REVIEW.
