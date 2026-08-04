# Phase-2 Balanced Curriculum — ChatGPT Static Review

**Project:** Intent Recovery Model  
**Date:** 2026-08-04  
**Repository state reviewed:** `main` at `4a7b892d58573b5e1253a3bf852e85eb0952897d`  
**Decision:** **STATICALLY RECOMMENDED FOR CLAUDE'S INDEPENDENT REVIEW**  
**Authorization status:** Proposal only. No example authoring, corpus mutation, derivation tooling, training, inference, seed 73, export, deployment, or activation is authorized by this document.

## 1. Question reviewed

Outcome B permits one next step: use only the residual, evidence-supported failure classes from the controlled seed-17 R2 replay to design a balanced Phase-2 curriculum proposal. This review asks:

> What is the smallest curriculum addition that directly addresses the remaining failures without copying benchmark cases, weakening existing coverage, changing the v2 contract, or introducing unrelated release themes?

The proposal is based on the committed R2 evidence package, the 66-record R2-derived corpus, the frozen protected-16 and acceptance-10 definitions, the category reference, the design-notes template, and the dataset review guide.

## 2. Repository evidence

The committed Outcome-B record reports:

- protected strict pass: **12/16**, compared with 11/16 for the same-seed baseline;
- acceptance count-rule conformance: **7/10**, compared with 6/10;
- acceptance combined strict pass: **6/10**, compared with 4/10;
- remaining acceptance failures: `sdi2-06`, `sdi2-07`, `sdi2-08`, and `sdi2-10`;
- one true same-seed protected regression: probe `13`.

Direct inspection of `training/gold_v1.2.2_r2_derived_candidate.jsonl` confirms 66 records and this structural distribution:

| Measure | Current R2 corpus |
|---|---:|
| Bullet counts | 1: 4; 2: 13; 3: 24; 4: 18; 5: 6; 6: 1 |
| Action counts | 0: 8; 1: 25; 2: 19; 3: 7; 4: 7 |
| Maximum bullets | 6 |
| Maximum actions | 4 |

The absence of any five-to-eight-action target is direct evidence that `sdi2-08` is outside the corpus's trained action-count range. The corpus does contain exact-word repeated reminders and several unresolved either/or questions, so `sdi2-06` and `sdi2-07` are narrower transfer gaps—not blanket absence of those skills. Probe `13` has one direct `two_unrelated_tasks` training example, but only one, and the replay preserved its second task in narrative/bullets while dropping it from actions.

## 3. Residual failure analysis

| Failure | Observable defect | Existing coverage | Supported gap |
|---|---|---|---|
| `sdi2-06` | `Still undecided` became past-tense `was undecided`; its bullet became imperative-like `Decide between` | Several unresolved either/or examples exist, plus one action-oriented `Decide between` example | Weak contrast between an unresolved state and an explicit decision task, especially when an unrelated later observation is present |
| `sdi2-07` | One task restated with `reserve`/`book` became two bullets | Exact or near-exact repeated reminders are represented | Semantic deduplication across paraphrased verbs and aliases is underrepresented |
| `sdi2-08` | Only 6/8 actions survived; one task disappeared and another acquired an unsupported recipient | No target contains more than four actions | High-count action retention is untrained; the bullet ceiling/action completeness interaction is also absent |
| `sdi2-10` | Saturday deadline disappeared and the unresolved question did not receive its sixth bullet | Dense mixed examples exist, but only one target reaches six bullets | Six-topic cross-field completeness with attribution, uncertainty, and task qualifiers has insufficient depth |
| Protected `13` | Both tasks survived in narrative/bullets, but only one survived in actions | One direct two-unrelated-task example exists | Two-task cross-field action completeness is too fragile to act as a regression guard |

### What the evidence does not establish

- It does not justify changing the prompt contract, parser, scorer, taxonomy, or frozen gates.
- It does not justify training on the benchmark probes themselves or close paraphrases.
- It does not justify using Gold v1.2.3.
- It does not show a need for a broad emotional-state release, real-note data, seed sweeping, or a larger base model.
- It does not establish that additional examples will clear the gate; it only supports a controlled curriculum candidate for review.

## 4. Recommended Phase-2 curriculum: 12 examples

The smallest balanced addition I recommend is **12 new training examples**, allocated by observed severity and coverage depth:

| Family | Count | Category plan | Required target shape | Failure addressed |
|---|---:|---|---|---|
| Unresolved-state versus decision-task contrast | 2 | Reuse `open_question_preservation` and `idea_action_boundary` | One unresolved choice with 0 actions; one explicitly requested choice with 1 action; unrelated observations remain non-answers | `sdi2-06` |
| Paraphrased restatement deduplication | 2 | Reuse `repeated_reminder` | One supported task expressed twice using different verbs or aliases; exactly 1 bullet and 1 action | `sdi2-07` |
| High-count task ladder | 4 | Introduce `high_count_task_retention` only if Claude agrees no existing category is precise enough | Targets with 5/5, 6/6, 7/7, and 7-bullet/8-action shapes; every explicit task survives in actions | `sdi2-08` |
| Dense mixed cross-field completeness | 2 | Reuse `cross_field_completeness` | Exactly 6 source-supported bullets and 2 actions; include a qualifier/deadline, uncertainty, non-task content, and varied attribution without copying `sdi2-10`'s sentence pattern | `sdi2-10` |
| Two unrelated task retention | 2 | Reuse `two_unrelated_tasks` | Exactly 2 bullets and 2 actions; vary punctuation, order, and qualifier placement | Protected `13` |

This changes the corpus from 66 to **78 records**. If the frozen six-record validation split remains byte-identical and all 12 additions are appended to train in declared order, the proposed split becomes **72 train / 6 validation**.

### Category decision requiring Claude's review

I recommend one new category, `high_count_task_retention`, because the gap is specifically the survival of every supported task above the corpus's four-action ceiling. `simple_list` describes uncomplicated fragmented lists, while `cross_field_completeness` currently emphasizes field consistency under heavy interleaving. Reusing either would make later diagnosis less precise. Claude should challenge this recommendation if repository convention favors extending an existing category instead.

No other new category is justified.

## 5. Authoring constraints

These constraints are mandatory if Johnny later authorizes authoring:

1. **Benchmark isolation:** none of the 26 benchmark inputs or outputs enters training. New examples must not reuse their people, objects, deadlines, sentence order, or distinctive verb pairs.
2. **No close paraphrases:** lexical substitution over `sdi2-06/07/08/10` or probe `13` is insufficient and must be rejected.
3. **One lesson per example:** each example's complications exist only to exercise its named family. Dense examples may combine components only where `cross_field_completeness` is itself the lesson.
4. **Contrast, not repetition:** the unresolved-choice family must include both sides of the modality boundary—an unresolved state that is not an action and an explicit request to decide that is an action.
5. **High-count positional balance:** across the four high-count targets, vary which task appears last, which carries a qualifier, and—in the eight-action case—which supported item is omitted from bullets because of the seven-bullet ceiling. All actions remain distinct.
6. **No arbitrary merging:** the eight-action target must not combine separate tasks merely to satisfy the bullet ceiling. The action section carries all eight.
7. **Qualifier survival:** deadlines, destinations, recipients, quantities, and conditions must appear wherever their omission would materially change the recovered task.
8. **Evidence first:** outputs may normalize wording but may not invent causes, chronology, recipients, completion state, emotions, or missing referents.
9. **Full design notes:** every example must use `docs/datasets/DESIGN_NOTES_TEMPLATE.md`, including fragment rationale, boundary evidence, likely failures, hallucinations to watch for, curriculum placement, and expected recovery.
10. **Static overlap check:** Claude must compare every proposed input and target against the 26 frozen probes and the 66-record R2 corpus before acceptance.

## 6. Candidate construction recommendation

If the examples pass independent review, preserve the R2 corpus as an immutable parent and construct a separately named Phase-2 candidate:

- author the 12 examples in an independent proposal JSONL with design notes;
- do not edit `gold_v1.2.2_r2_derived_candidate.jsonl` in place;
- derive a new candidate deterministically by verifying the parent fingerprint, preserving all 66 parent records byte-for-byte and in order, then appending the 12 accepted records in a declared stable order;
- fail closed on duplicate inputs, duplicate stable identities, parent drift, output-field mismatch, or an unexpected record count;
- keep the existing six validation records byte-identical for comparison; append all 12 Phase-2 examples to train only;
- exclude Gold v1.2.3 and every benchmark case.

The expected 72/6 split and resulting step count must be computed and pinned by Claude from the actual training code before any compute manifest is reviewed. Holding 40 epochs would likely increase updates from 600 to approximately 720; that is an inference from the current split size, not an authorized or yet-verified command. A future manifest must state explicitly whether per-example exposure or total optimizer steps is held constant and why.

## 7. Frozen evaluation recommendation

Any later seed-17 Phase-2 experiment should use the same v2 contract, 26 cases, scorer, and strict semantics. The Phase-2 gate should be frozen before outputs exist:

1. protected format validity: 16/16;
2. acceptance format validity: 10/10;
3. acceptance count-rule conformance: 10/10;
4. acceptance combined strict pass: 10/10;
5. protected strict pass: candidate must be at least the R2 replay's 12/16;
6. same-seed preservation: no protected probe passed by the R2 replay may newly fail.

Probe `13` must pass to clear gate 6, but the gate must remain set-based rather than special-cased to that probe. Seed 73 remains blocked unless a separately authorized seed-17 Phase-2 run clears the frozen gate and receives joint review.

## 8. Risk controls

| Risk | Control |
|---|---|
| Benchmark memorization | Surface-form distance review; benchmark remains evaluation-only |
| Action overproduction after adding long lists | Preserve zero-action/one-action contrast examples and run all existing protected cases |
| Positional bias in long lists | Vary task order, qualifiers, and the bullet-ceiling omission position |
| Deduplication overreach | Include an explicit contrast where two similar-looking instructions are genuinely separate |
| New examples crowd out earlier skills | Append rather than replace; preserve parent order and frozen validation; require no R2-pass regression |
| Hidden compute variable | Pin split, record order, epochs/steps, dependencies, and every executable fingerprint before authorization |
| Curriculum creep | Limit content to the five residual failure classes; exclude future emotional-state themes and real data |

## 9. Recommended ownership and next gate

| Work item | Owner | Authorization status |
|---|---|---|
| Independent corpus-count and overlap verification | Claude | Authorized as static review only |
| Challenge or accept the 12-example distribution and category plan | Claude | Authorized as static review only |
| Resolve any ChatGPT/Claude disagreement | Johnny | Decision only |
| Author proposal JSONL and design notes | ChatGPT | **Not yet authorized** |
| Build derivation/validation tooling | Claude | **Not yet authorized** |
| Commit a reviewed static proposal | Johnny decides | Does not authorize compute |
| Training, inference, scoring run, or seed 73 | Johnny only, through a later named authorization | **Unauthorized** |

## 10. Questions Claude must answer

1. Do the corpus counts and coverage claims reproduce from `main` at `4a7b892`?
2. Is `high_count_task_retention` a justified new category, or should those four examples reuse an existing category?
3. Are 12 examples sufficient and balanced, or does any family need a static adjustment before authoring?
4. Does appending all 12 to train while preserving the six validation records give the cleanest comparison under current tooling?
5. What exact epoch/step policy preserves the intended comparison, based on `train.py` rather than inference?
6. Are any proposed families too close to the frozen benchmarks or already adequately represented?
7. What fail-closed derivation checks and artifact names should be frozen before authoring or implementation is authorized?

## 11. Static-review verdict

**Proceed to Claude's independent static verification of this 12-example curriculum design.**

Do not author the examples, extend tooling, alter the corpus, or run compute yet. If Claude agrees—or returns a clearly documented disagreement for Johnny—the next product decision is whether to authorize Phase-2 example authoring and design-note creation only.

## Repository references

- [Outcome-B commit](https://github.com/ThisIsJohnnyt/intent-recovery-model/commit/4a7b892d58573b5e1253a3bf852e85eb0952897d)
- [R2-derived 66-record corpus](https://github.com/ThisIsJohnnyt/intent-recovery-model/blob/main/training/gold_v1.2.2_r2_derived_candidate.jsonl)
- [Controlled replay protocol](https://github.com/ThisIsJohnnyt/intent-recovery-model/blob/main/training/controlled_seed17_r2_replay_protocol.md)
- [Claude replay verification](https://github.com/ThisIsJohnnyt/intent-recovery-model/blob/main/training/controlled_seed17_r2_replay_claude_verification.md)
- [ChatGPT scoring review](https://github.com/ThisIsJohnnyt/intent-recovery-model/blob/main/training/controlled_seed17_r2_replay_chatgpt_semantic_scoring_review.md)
- [Protected-16 benchmark](https://github.com/ThisIsJohnnyt/intent-recovery-model/blob/main/datasets/benchmark/gold_v1.2.1_probes.jsonl)
- [Acceptance-10 benchmark](https://github.com/ThisIsJohnnyt/intent-recovery-model/blob/main/datasets/benchmark/source_determined_items_v2_acceptance_draft.jsonl)
- [Category reference](https://github.com/ThisIsJohnnyt/intent-recovery-model/blob/main/docs/datasets/CATEGORY_REFERENCE.md)
- [Dataset review guide](https://github.com/ThisIsJohnnyt/intent-recovery-model/blob/main/docs/datasets/REVIEW_GUIDE.md)
- [Design-notes template](https://github.com/ThisIsJohnnyt/intent-recovery-model/blob/main/docs/datasets/DESIGN_NOTES_TEMPLATE.md)
