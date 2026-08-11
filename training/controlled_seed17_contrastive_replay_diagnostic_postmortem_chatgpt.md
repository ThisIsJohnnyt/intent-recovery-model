# Controlled Seed-17 Contrastive Replay — Diagnostic Postmortem

**Date:** 2026-08-11  
**Author:** ChatGPT  
**Evidence commit:** `43f4fc41264469ac2848340c8bea8e216dba8368` on `main`  
**Governing outcome:** `C17-C`, final and verified  
**Scope:** Static diagnostics only. No corpus mutation, derivation, training, inference, seed 73, checkpoint work, export, deployment, activation, cleanup, commit, or push is authorized by this document.  
**Status:** Initial diagnostic analysis awaiting Claude's independent review.

## 1. Executive finding

The contrastive treatment did not produce a generally stronger model. It exchanged two protected-set gains for two protected-set losses, produced no protected aggregate improvement, lost two acceptance cases that the comparator passed, and did not improve acceptance count-rule conformance.

The intervention nevertheless produced one important aligned signal: treatment passed protected probe 06 while comparator failed it. That is the principal target of the four new attribution records, so the result is consistent with the attribution contrast teaching some useful behavior. The same treatment did not retain enough adjacent capabilities to clear the frozen gates.

The evidence does **not** justify a new training run or an immediately derivable corpus. It supports one possible next step only: a new, design-only repair specification that preserves the likely attribution gain while explicitly protecting task qualifiers, buried tasks, incomplete thoughts, dangling references, and structural count behavior.

## 2. Exact intervention

Comparator training used the historical 78-record Phase-2 candidate: the 66-record parent plus the historical 12-record proposal. Treatment used an 82-record candidate: the same 66-record parent plus the reviewed 16-record composite.

The treatment/comparator curriculum delta is exactly six record-level changes, all realized in training while the six-record validation membership remained frozen:

1. Four new `multi_person_attribution` records, AT-C1 through AT-C4.
2. Target-only bullet revisions to historical P2-009.
3. Target-only bullet revisions to historical P2-010.

Ten historical proposal records were unchanged. The effective corpus intervention was therefore narrow in file count but not semantically isolated: it changed both attribution teaching and cross-field bullet-selection pressure in the same treatment arm.

### Intended lessons

- AT-C1/AT-C4: resolve supported pronouns consistently despite name-order reversal.
- AT-C2: preserve genuine pronoun uncertainty.
- AT-C3: resolve an earlier reference while preserving a later explicit ambiguity.
- P2-009/P2-010 revisions: preserve complete narrative content without forcing every background fact or observation into bullets.

Because attribution and field-role changes were bundled together, this single paired replay cannot identify their separate causal effects.

## 3. Behavioral comparison

### Protected-16

| Outcome relationship | Probe IDs | Interpretation |
|---|---|---|
| Treatment pass / comparator fail | `{02, 06}` | Treatment gains |
| Treatment fail / comparator pass | `{10, 16}` | Treatment regressions |
| Both fail | `{08, 09, 11}` | Shared unresolved failures, with arm-specific wording/failure modes |
| Both pass | `{01, 03, 04, 05, 07, 12, 13, 14, 15}` | Preserved common capabilities |

Both arms finish at 11/16. Treatment's gains on 02 and 06 are exactly offset by losses on 10 and 16.

### Acceptance-10

| Outcome relationship | Probe IDs | Interpretation |
|---|---|---|
| Treatment pass / comparator fail | none | No treatment-only acceptance gain |
| Treatment fail / comparator pass | `{sdi2-02, sdi2-09}` | Two treatment semantic regressions |
| Both fail | `{sdi2-07, sdi2-08, sdi2-10}` | Shared residual failures |
| Both pass | `{sdi2-01, sdi2-03, sdi2-04, sdi2-05, sdi2-06}` | Preserved common capabilities |

Both arms conform to count rules on the same 7/10 probes. Treatment combined strict pass is 5/10; comparator is 7/10. Comparator `sdi2-08` is semantically acceptable but fails the bullet-count ceiling, so it remains outside the combined pass set.

## 4. Findings by mechanism

### 4.1 Attribution contrast shows an aligned but non-isolated gain

Protected 06 is the clearest aligned result. Treatment explicitly preserves the stamped-copy ambiguity and passes every required dimension/check. Comparator includes the contradictory bullet “She still needs the stamped copy” and fails ambiguity preservation.

This direction matches the intended AT-C2/AT-C3 lesson: do not resolve a later explicitly ambiguous referent merely because an earlier reference can be resolved. Confidence that the treatment result is **aligned with** the attribution intervention is high. Confidence that the four AT records **caused** the gain is only medium because:

- there is one treatment run and one separately trained comparator run;
- exact deterministic state equivalence is unavailable;
- the treatment also changed P2-009/P2-010 targets;
- no attribution-only ablation was run.

Protected 02 also improves, but its tablet-fragment reconnection is not an intended attribution effect. Treat it as an observed treatment gain without a supported mechanism attribution.

### 4.2 Field-role remediation did not generalize safely

The P2-009/P2-010 revisions deliberately removed nonessential background facts from bullets while retaining full narratives and all explicit actions. That local field-role rule is defensible. The replay does not show safe generalization of that rule:

- Treatment protected 10 mentions “print the shipping label” in narrative but drops the task from both bullets and actions.
- Treatment acceptance `sdi2-02` retains the shared-drive destination only in narrative; the bullet and action both drop it.
- Treatment acceptance `sdi2-09` retains “after it arrives” in narrative but drops the arrival condition from the bullet/action and adds the unsupported judgment “is a good idea.”

These are not identical to the intended P2-009/P2-010 lesson, and they do not prove those revisions caused the regressions. They do expose a design weakness: the curriculum states when background content may be omitted from bullets, but it does not teach an equally explicit invariant that every supported task, recipient, destination, deadline, condition, and quantity must survive intact in `action_items`.

The next design must define field roles in both directions:

- selective bullets are allowed where the contract allows them;
- action completeness is mandatory for every explicit task and its governing qualifiers.

### 4.3 Source-state preservation remains brittle

Treatment fails two required protected source-state cases:

- Protected 09 corrupts the incomplete volunteer-list thought by tying it to Imani/sending.
- Protected 16 preserves the base reminder but invents that “them” means two people and that the references are unrelated.

Treatment acceptance `sdi2-09` preserves the unresolved referents in narrative but adds an unsupported opinion and loses the arrival qualifier from action/bullet fields.

These failures span incomplete thoughts, dangling references, and unsupported evaluation. The attribution contrasts did not provide a broad enough “preserve unknowns without embellishment” signal to protect neighboring source-state behaviors.

### 4.4 Task and qualifier retention remains brittle in both arms

- Treatment protected 10 loses the shipping-label task from actionable fields.
- Both arms protected 11 lose “by Thursday” from the registration-fee action.
- Treatment acceptance `sdi2-02` loses the shared-drive destination from actionable fields.
- Both arms acceptance `sdi2-10` merge two explicit tasks into one action and fail exact structural requirements.

The historical two-unrelated-task repair remains intact at protected 13, which both arms pass. The remaining problem is not simply “recover multiple tasks.” It is preservation of complete task semantics under interruption, density, and field constraints.

### 4.5 Count behavior did not improve

Both arms count-conform on exactly 7/10 acceptance probes and fail the same structural cases:

- `sdi2-07`: repeated task not deduplicated to the required one bullet.
- `sdi2-08`: bullet ceiling violated; treatment additionally loses one action.
- `sdi2-10`: six required bullet ideas and two actions collapse to four bullets and one merged action.

This is strong descriptive evidence that the six-record treatment delta did not repair the acceptance contract's count behavior. It is not evidence that more examples alone will fix it.

## 5. What the replay supports and does not support

### Supported with high confidence

- Treatment and comparator are valid matched arms and both fail four frozen gates.
- Treatment produces an aligned protected-06 gain.
- Treatment produces protected regressions on 10 and 16 and acceptance regressions on `sdi2-02` and `sdi2-09`.
- Acceptance count-rule conformance is identical at 7/10 with the same failing IDs.
- Protected 13's two-task repair survives in both arms.
- No currently reviewed corpus is eligible for another training run.

### Plausible but unproven

- The four attribution contrasts contributed to treatment's protected-06 repair.
- P2-009/P2-010 bullet pruning contributed to overgeneralized omission pressure.
- The combined curriculum created interference between selective field roles and complete task preservation.

### Not supported

- That one specific added/revised record caused any individual failure.
- That a longer or shorter training horizon would resolve the pattern.
- That adding more attribution examples alone would produce a passing candidate.
- That seed 73 would clarify the failed candidate; `C17-C` prohibits that path.
- That benchmark, rubric, or contract changes should be used to make the result pass.

## 6. Diagnostic conclusion

The treatment taught at least part of the intended attribution boundary but did not preserve a sufficiently broad set of neighboring invariants. The central design problem is now better stated as:

> Teach evidence-based attribution and selective field roles without weakening source-state preservation or the complete transfer of explicit task semantics into action items.

This is broader than the prior attribution-only defect but narrower than a general corpus expansion. A future candidate should not be assembled by simply adding more examples to the existing 82-record treatment.

## 7. Recommended next milestone

Recommend a **design-only regression-balanced repair specification**, with no JSONL or compute yet. It should define the minimum semantic contrast families needed to protect four boundaries:

1. **Attribution and ambiguity:** retain the useful resolve-versus-preserve contrast demonstrated by AT-C1 through AT-C4.
2. **Action completeness:** explicit tasks must carry every supported deadline, destination, recipient, condition, quantity, and object into `action_items`.
3. **Source-state preservation:** incomplete thoughts, open questions, and dangling references must remain unresolved without invented answers, relationships, or evaluations.
4. **Structural behavior:** deduplication, bullet ceilings, and multi-action separation must be taught without merging or dropping task semantics.

The design should use balanced minimal pairs and mechanism-specific change groups so later static group screening can distinguish attribution, field-role, source-state, and structural interventions. It must preserve the two effective `two_unrelated_tasks` records and must not alter benchmarks, rubrics, prompt contract, validation membership, or the committed `C17-C` evidence.

### Required static gates before any corpus proposal

- Every proposed example has one named mechanism and one explicit regression risk.
- Action qualifiers are checked field-by-field, not accepted merely because they appear in narrative.
- Resolve/preserve-uncertainty cases are balanced against positional and always-ambiguous shortcuts.
- Incomplete and dangling references are represented without lexical overlap with protected/acceptance probes.
- Count-target cases distinguish semantic completeness from structural ceilings.
- Attribution, field-role, source-state, and structural groups can be reviewed separately.
- Near-duplicate and benchmark-overlap checks are specified before authoring final records.
- No new training candidate, split, or execution package is created until the design passes independent review and Johnny separately authorizes implementation.

## 8. Requested independent review

Claude should independently check:

1. the exact six-record curriculum delta and realized training membership;
2. all protected and acceptance pass/fail transition sets;
3. the record-level descriptions of each failure;
4. the separation between observed evidence and causal hypothesis;
5. whether the proposed four-boundary framing is the narrowest adequate explanation; and
6. whether the recommended design-only milestone follows from the evidence without silently authorizing corpus work or compute.

Any material disagreement is work-stopping and returns to Johnny with both positions and evidence.

**Disposition:** DIAGNOSTIC POSTMORTEM DRAFTED — MIXED TREATMENT EFFECT IDENTIFIED — NO TRAINING CANDIDATE READY — DESIGN-ONLY REGRESSION-BALANCED REPAIR SPECIFICATION RECOMMENDED — AWAITING CLAUDE INDEPENDENT REVIEW.
