# Controlled Seed-17 Regression-Balanced Repair — Diagnostic Postmortem

**Date:** 2026-08-12  
**Final governed outcome:** `RBR17-C` — valid treatment fail / valid comparator fail  
**Primary evidence:** `training/controlled_seed17_regression_balanced_repair_outcome.md` and the four committed scored result files under `training/controlled_seed17_regression_balanced_repair_run/`  
**Decision status:** Diagnostic draft for independent review; no downstream action authorized

## 1. Purpose and boundary

This postmortem explains the verified RBR17-C failure pattern at the level supported by one matched seed-17 comparison. It separates treatment-specific changes from failures shared by both arms, maps those observations back to the reviewed seven-record treatment delta, and recommends the smallest defensible next design milestone.

This document does **not** authorize corpus editing, new examples, benchmark or rubric changes, training, inference, seed 73, checkpoint selection or promotion, export, deployment, cleanup, commit, or push. It does not reopen the final `RBR17-C` classification.

## 2. Executive finding

The 85-record treatment did not produce a net repair. Relative to the freshly trained 78-record comparator, it exchanged one strict protected gain for one strict protected regression, added one acceptance semantic regression, and left every structural count failure unchanged.

The paired evidence supports four conclusions:

1. **The treatment is not a safe successor to the 78-record reference corpus.** Protected strict pass remained 10/16 in both arms, while acceptance combined strict pass fell from 7/10 in the comparator to 6/10 in the treatment.
2. **The intended record-to-mechanism transfer was not demonstrated.** The added deadline/destination record did not protect acceptance `sdi2-02`; the treatment alone dropped the destination. The added dangling-reference record did not repair protected 16; both arms emitted the same failing output. The four attribution controls did not repair protected 06.
3. **Most residuals are not treatment-specific.** Five protected failures and all three acceptance count failures were shared. They therefore diagnose limits of both 720-step arms under the frozen stack, not evidence that the seven-record delta uniquely caused them.
4. **More examples of the same abstract types are not yet justified.** Several failed mechanisms already had audited baseline coverage and, in two cases, purpose-built additions. The next useful work is a no-compute mechanism and representation audit, not an automatic corpus expansion or seed-73 run.

## 3. Paired outcome decomposition

### 3.1 Protected-16

| Paired class | Cases | Interpretation |
|---|---|---|
| Treatment-only strict gain | `{02}` | Interrupted tablet fragments were reconnected without the comparator's topic merge and unsupported addition. This is a real observed gain, but it is not the primary mechanism targeted by the seven-record delta. |
| Treatment-only strict regression | `{09}` | A previously passing open-question/incomplete-thought case became an invented answer/action and lost the volunteer-list fragment. |
| Shared strict failures | `{06,08,10,11,16}` | These cannot be attributed uniquely to the treatment. They expose residual attribution, question-state, buried-task, field-realization, and dangling-reference weaknesses present in both arms. |
| Shared strict passes | `{01,03,04,05,07,12,13,14,15}` | The treatment preserved these nine comparator passes, including protected 13. |

Both arms therefore finish at 10/16, but the equal totals conceal a non-equivalent pass set. The treatment did not merely reproduce the comparator; it traded protected 09 for protected 02.

### 3.2 Acceptance-10

| Paired class | Cases | Interpretation |
|---|---|---|
| Treatment-only semantic regression | `{sdi2-02}` | The treatment preserved the deadline but dropped “shared drive” from the recovered task; the comparator passed. Count conformance remained correct. |
| Treatment-only semantic gain | none | No acceptance case moved from comparator semantic failure to treatment semantic pass. |
| Shared semantic failures | `{sdi2-07,sdi2-10}` | Repeated-task deduplication and dense mixed-role/task decomposition remain unresolved in both arms. |
| Shared count failures | `{sdi2-07,sdi2-08,sdi2-10}` | The seven-record delta did not alter any acceptance count verdict. |

Comparator combined strict pass was 7/10. Treatment combined strict pass was 6/10 because `sdi2-02` changed from pass to fail. This is the clearest net treatment cost in the frozen gate system.

### 3.3 Scope correction relative to earlier design evidence

The gain/regression sets summarized in Section 2 of `controlled_seed17_regression_balanced_repair_design_chatgpt.md` describe the **earlier contrastive experiment that motivated RBR**, not the later RBR17-C paired outcome. They must not be copied forward as if they were RBR results. The tables above are derived from the final RBR17-C scored artifacts and outcome record.

## 4. Treatment-specific diagnostics

### 4.1 Protected 02: a genuine but non-targeted gain

The comparator split the interrupted tablet thought and introduced “back to the computer,” failing reconnection and unsupported-addition checks. The treatment correctly joined the opening fragment to the later charger/screen clause while retaining the donation-box task.

This is useful evidence that the corpus delta changed behavior beyond exact target families. It is not evidence that attribution, action completeness, or dangling-reference teaching succeeded. With one seed and a bundled seven-record delta, the responsible record or interaction is not identifiable.

### 4.2 Protected 09: source-state preservation regressed

The comparator preserved all three source states: an unresolved schedule question, the supported “check sent mail” task, and an incomplete volunteer-list thought. The treatment instead asserted “Send the revised schedule to Imani,” converted uncertainty into action, and failed to preserve the incomplete volunteer-list thought.

This is not a formatting or count issue. It is a semantic state-transition error: question → asserted task, combined with fragment loss. It is especially relevant because the treatment included a new source-state record (`RB-C3`), yet the observed transfer moved in the wrong direction on a different source-state case.

### 4.3 Acceptance `sdi2-02`: targeted qualifier protection failed

`RB-B1` was explicitly designed to teach a task containing both a deadline and destination and named `sdi2-02`-type destination retention as expected protection. The treatment nevertheless dropped “shared drive” while the comparator preserved it.

This is stronger evidence than a merely unrelated miss: the intended abstract mechanism was represented in the new curriculum, but transfer to the frozen case was not obtained. It does not prove that `RB-B1` caused the regression. It does show that presence of one clean mechanism-matched example is insufficient evidence of learned qualifier binding under this setup.

### 4.4 Acceptance `sdi2-10`: treatment output is directionally worse, but both fail

Both arms merged roles and tasks, lost required ideas, and failed exact counts. The treatment additionally turned the already-delivered glaze-sample fact into an imperative bullet and received a lower unsupported-addition score than the comparator. Because both arms fail strict semantics and counts, this is a qualitative worsening inside a shared failure, not a treatment-only gate regression.

The pattern is consistent with the protected-09 regression: source facts or unresolved states can be over-promoted into action-like language. That is a mechanism hypothesis for audit, not a causal conclusion.

## 5. Shared residual mechanisms

### 5.1 Reference resolution and attribution are not solved by four balanced controls

- **Protected 06:** both arms mis-handle the two different pronoun decisions: an earlier locally resolvable reference and a later explicitly ambiguous reference.
- **Protected 08:** the treatment avoids the comparator's explicit invented causality, but still fails to express the window-versus-plant question faithfully. This is a partial change without strict repair.
- **Protected 16:** both arms produce the same unsupported reformulation of a one-line dangling-reference reminder. `RB-C3` did not change the decoded behavior on this frozen case.

The four AT-C records created a balanced attribution curriculum on paper, including an intentionally close analogue to protected 06. The lack of a protected-06 repair means the experiment does not demonstrate general acquisition of the resolve-versus-preserve rule. Because the treatment was bundled, it also cannot determine whether the attribution records had no effect, were counteracted by other additions, or changed cases not captured by the frozen gates.

### 5.2 Task survival and field realization remain unstable

- **Protected 10:** both arms omit the buried “print the shipping label” task and retain an unsupported rendering of the final-scene observation.
- **Protected 11:** the treatment preserves the fee deadline better than the comparator, but both fail strict output because the source is not realized faithfully across fields.
- **Acceptance `sdi2-02`:** only the treatment drops the destination.
- **Acceptance `sdi2-10`:** both arms merge two tasks and confuse sender, recipient, and completed-event roles.

These cases are not one uniform “task loss” defect. They distinguish at least: buried imperative detection, qualifier binding, role binding, completed-event versus requested-action classification, and consistent realization across narrative, bullets, and actions.

### 5.3 Structural failures are stable and likely not a simple coverage deficit

- **`sdi2-07`:** both arms fail to collapse a literal restatement to one bullet. The treatment reduces the comparator's three bullets to two, but invents a separate “reminder” framing and still fails deduplication.
- **`sdi2-08`:** both arms emit eight bullets and eight actions. Semantic preservation passes, but the hard seven-bullet ceiling fails. This is a field-budget/compression problem, not task recovery loss.
- **`sdi2-10`:** both arms emit four bullets instead of six and one merged action instead of two. This is simultaneous semantic decomposition and cardinality failure.

The pre-execution audit already found clean baseline exemplars for repeated-reminder deduplication, eight-task/seven-bullet behavior, and six-idea/two-task behavior. The shared failures therefore do not support “add one more structural example” as the next default. They support checking whether the current model, target representation, decoding process, and loss give those constraints enough learnable and enforceable signal.

## 6. What the experiment can and cannot establish

### Supported

- The 85-record candidate does not clear and is worse than the comparator on acceptance combined strict pass.
- The corpus delta changes semantic behavior nonlocally: protected 02 improves while protected 09 and `sdi2-02` regress.
- The expected transfer from `RB-B1` to destination retention, from `RB-C3` to protected 16, and from the AT-C set to protected 06 was not observed in the frozen gate results.
- Count failures are identical by case across arms.
- A single aggregate such as 10/16 obscures material exchanges and must not be used alone for future decisions.

### Not supported

- Assigning any changed output to one of the seven added records.
- Claiming that an individual added record is harmful or useless.
- Claiming a general treatment gain from protected 02 or a general treatment loss from one seed.
- Treating protected 06 as independent proof of attribution generalization; its known training analogue limits that inference.
- Assuming seed 73 would rescue the candidate.
- Weakening frozen gates, changing scoring, or promoting either checkpoint because both arms failed.

## 7. Root-cause hypotheses, ranked for no-compute review

| Priority | Hypothesis | Evidence | What would distinguish it without training |
|---:|---|---|---|
| 1 | **The task is under-specified in the output representation/loss.** Semantic roles, source state, field counts, and field-specific constraints are encoded only as target text, so several objectives compete token by token. | Stable count failures; facts/questions promoted to actions; qualifier and role loss despite clean examples. | Map every failure to the exact target tokens and fields carrying its supervision; identify conflicts where faithful narrative, compressed bullets, and exhaustive actions demand different transformations. |
| 2 | **Capacity or decoding limits dominate some dense cases.** | `sdi2-08` preserves all eight actions but ignores the bullet ceiling; `sdi2-10` collapses roles and ideas in both arms; additions do not move exact outputs on some cases. | Conduct a design-only architecture/decoding audit: model size, maximum output behavior, deterministic decoding, constraint visibility, and whether post-decoding validation could enforce syntax/counts without altering semantics. |
| 3 | **Mechanism coverage exists but has too little effective weight or contrast.** | Purpose-built B1/C3 and four AT controls do not transfer to their named frozen mechanisms. | Count and compare mechanism-bearing tokens/records, contrast balance, and target-form consistency across the full 85 records; do not infer adequacy from record count alone. |
| 4 | **Bundled objectives interfere.** | Non-targeted protected gain plus source-state/qualifier regressions; one combined arm prevents attribution to A/B/C additions. | Static cross-record conflict audit and a predeclared future ablation design. An ablation design is not authorization to run it. |
| 5 | **Some failures are evaluator-visible symptoms of distinct mechanisms.** | “Topic loss” spans buried tasks, dropped qualifiers, merged roles, and missing ideas. | Reclassify each failed capability check into atomic mechanisms while leaving frozen verdicts unchanged. |

These hypotheses are compatible, not mutually exclusive. The current evidence does not justify selecting one as the proven root cause.

## 8. Recommended next milestone

The next logical milestone is a **bounded, no-compute RBR17-C mechanism audit and representation/capacity comparison design**, not another corpus implementation.

It should produce:

1. an atomic failure ledger for the ten distinct failing cases across the pair (`06,08,09,10,11,16,sdi2-02,sdi2-07,sdi2-08,sdi2-10`, with paired cases grouped rather than double-counted);
2. a record-to-mechanism coverage map for the 78-record baseline and seven-record delta, including effective target-token and field-form evidence rather than category labels alone;
3. a conflict map for fact/question/fragment/task state, role binding, qualifier binding, deduplication, bullet budgeting, and action cardinality;
4. a design-only comparison of three remedy classes:
   - corpus/contrast changes,
   - representation or training-objective changes,
   - constrained decoding or deterministic post-validation for structural requirements;
5. explicit criteria for deciding whether any later proposal should be an ablation, a representation change, a model-capacity comparison, or a stop; and
6. leakage controls that keep protected and acceptance text out of new training records and prevent protected 06's close analogue from being treated as independent generalization evidence.

The audit should begin from the preserved 78-record comparator as the reference lineage. The failed 85-record treatment must not silently become the new baseline. It may be analyzed as evidence, and its seven records may be reconsidered individually, but none should be carried forward automatically.

## 9. Stop conditions

Stop the next design phase and return for Johnny's decision if any of the following occurs:

- the proposed diagnosis requires changing a frozen benchmark, rubric, score, or accepted outcome;
- a claimed repair depends on copying or closely paraphrasing protected/acceptance inputs;
- the mechanism audit cannot distinguish corpus coverage from representation or capacity limits;
- a remedy would require new data, corpus mutation, model execution, checkpoint use, or seed 73;
- a future comparison cannot isolate its variable without bundling unrelated changes; or
- the evidence supports only “try more examples” without a falsifiable mechanism claim.

## 10. Decision recommendation

Keep `RBR17-C` closed. Do not run seed 73, promote either checkpoint, or append another broad repair bundle. Treat the comparator as the reference lineage and authorize, only if Johnny chooses, the bounded no-compute audit defined in Section 8.

**Disposition:** POSTMORTEM DRAFTED — TREATMENT NOT A SAFE SUCCESSOR — ONE PROTECTED GAIN EXCHANGED FOR ONE PROTECTED REGRESSION, PLUS ONE ACCEPTANCE REGRESSION — SHARED STRUCTURAL AND SEMANTIC RESIDUALS REQUIRE MECHANISM/REPRESENTATION AUDIT — NO COMPUTE OR CORPUS ACTION AUTHORIZED.
