# Seed-17 v2 Study — No-Compute Corpus Coverage Audit

**Date:** 2026-08-03
**Corpus:** pinned Gold v1.2.2, 66 examples
**Split:** frozen 60 train / 6 validation
**Author:** ChatGPT
**Status:** Audit complete; Claude verification required
**Compute authorized:** None

## Executive finding

The seed-17 v2 failures do not have one common explanation.

- Typed-marker representation is learned: all 26 study outputs parse.
- Two acceptance failures expose clear training-distribution gaps.
- Several failures occur despite close or near-structural training support.
- Three existing targets deserve integrity review because their own wording can teach unsupported action promotion or attribution drift.

The evidence therefore does **not** support a six-case patch or an immediate seed-73 run. The next safe sequence is target-integrity review, then a balanced curriculum design, then a separately authorized fixed-split experiment.

## Corpus-wide structural distribution

### Train split: 60 examples

| Item count | Bullet targets | Action targets |
|---:|---:|---:|
| 0 | 0 | 7 |
| 1 | 4 | 22 |
| 2 | 13 | 16 |
| 3 | 20 | 7 |
| 4 | 16 | 7 |
| 5 | 6 | 1 |
| 6 | 1 | 0 |
| 7 | 0 | 0 |
| 8 | 0 | 0 |

The maximum training target contains six bullets, while the maximum action target contains five actions—and only one training example reaches five.

### Validation split: 6 examples

- Bullet counts: four examples with 3, two examples with 4.
- Action counts: one with 0, two with 1, two with 2, one with 3.

Validation adds no exposure to six-to-eight actions and cannot teach the model in any case.

## Failure-family coverage

| Observed family | Relevant train evidence | Coverage judgment | Interpretation |
|---|---|---|---|
| Unrelated observations without invented linkage | One direct train example: the three-observation `zero_action_items` record (fog, river, cardinals), B3/A0 | **Sparse** | sdi2-03's exact two-observation form is not absent, but neutral separation is represented only once. |
| Observation plus task without causal linking | Direct `task_plus_observation` and `observation_among_tasks` examples, plus several broader mixed notes | **Moderate** | sdi2-04's invented "so" is not explained by missing observation/task supervision alone. |
| Unresolved either/or with zero actions | Zero exact train examples. Closest train example is the warm-patch toaster-or-kettle case, but it includes a separate explicit action. A second close case is validation-only. | **Absent in the required zero-action form** | sdi2-06 exposes a real gap: the model has not been shown that an unresolved alternative plus observation can yield an empty action section. |
| Literal restatement deduplicated to B1/A1 | Three train examples explicitly deduplicate repeated reminders, but all include other topics/tasks; zero pure one-task restatement examples | **Partial** | sdi2-07 is not an absence failure. The missing piece is the minimal pure 1/1 form and surface variation. |
| Six-to-eight explicit actions | Training maximum is A5, represented once; A6/A7/A8 never occur | **Absent above five** | sdi2-08 produces exactly five actions. This is strong evidence of a learned distribution ceiling rather than marker failure or token truncation. |
| Dense B6/A2 note with attribution, uncertainty, tentativeness, and qualifiers | One B6/A2 near-structural twin exists in train (`buried_task_retention`: demo, tentative labels, Chris/Dana question, dentist, room, porch bulb). Multi-person records otherwise top out at B4/A1. | **Singleton / compositional gap** | sdi2-10 is not wholly unsupported, but one close example did not generalize across new roles and a shared deadline. |

## Strong counterevidence against "just add missing examples"

Several protected failures already have close training analogues:

- **Probe 02:** three `interrupted_thought_depth` training records exist; two explicitly reconnect a resumed causal fragment, including the locker-alarm example with an intervening task.
- **Probe 06:** the Rina/Marcus record is a close ambiguity-and-attribution analogue and is in train.
- **Probe 08:** the warm-patch toaster-or-kettle record is a close either/or-plus-later-observation analogue and is in train; another close example is validation-only.
- **Probe 16:** a clean simple dangling-reference record is in train.
- **sdi2-07:** three repeated-reminder/deduplication records are in train.
- **sdi2-10:** a B6/A2 dense near-twin is in train.

These cases point to sparse variation, compositional generalization, or target conflict—not simple category absence.

## Existing target-integrity concerns

These are audit findings, not unilateral rewrite decisions. Claude should verify them against the source and project policy.

### 1. `standalone_task_retention` near Probe 11

Source meaning: the kitchen sink is dripping, and the writer finds dealing with it exhausting.

Current target narrative says the dripping sink "feels exhausting." That construction weakens the actor/emotion boundary. The v2 Probe-11 output then says the garage light "feels tired," an analogous object-emotion drift.

This is a plausible curriculum interaction, not established causation. It warrants review before adding new Probe-11 examples.

### 2. First `dangling_reference` record

The source asks what the writer's daughter said about Friday. The target supplies "her plans for this Friday" and turns it into "Ask daughter about Friday." Both the "plans" referent and the action framing go beyond the source.

This conflicts with the project's dangling-reference and unsupported-addition policy. The later simple dangling-reference record is clean, so the category currently contains mixed supervision.

### 3. `rapid_topic_switching_incomplete_sentences`

The source contains fragments such as low gas, an unfinished landlord thought, and lunch at noon. The target action list promotes these into "Get gas," "Call the landlord," and "Lunch with Dana at noon." This is aggressive action promotion from observation, incomplete thought, and calendar information.

That behavior conflicts with the v2 acceptance contract's rule that observations and incomplete thoughts must not become actions.

## Representation versus curriculum conclusions

| Evidence | Best-supported conclusion |
|---|---|
| 26/26 outputs parse | Typed markers solve the observable item-boundary problem. |
| sdi2-08 emits 7 bullets despite train max B6 | The model can generalize marker repetition beyond the bullet-count support by at least one. |
| sdi2-08 emits 5 actions, exactly the training maximum | High action-count failure is likely distribution/capacity related, not parser related. |
| sdi2-06 invents actions with zero exact zero-action analogue | Genuine curriculum-form gap. |
| sdi2-07 fails despite three dedup examples | Existing support is not sufficiently minimal or varied; absence alone is not the explanation. |
| sdi2-10 fails despite one near-twin | One dense example is insufficient for compositional transfer. |
| Probe 11 resembles a questionable training target | At least one regression may involve target-quality conflict. |

## Recommendation

### Phase 1 — target integrity, no compute

1. Independently review the three flagged targets above.
2. Scan the remaining 63 targets for the same policy conflicts:
   - actor or emotion reassignment;
   - incomplete thought or observation promoted to action;
   - supplied dangling referent;
   - invented causal connective;
   - task qualifier loss.
3. Decide whether corrections create a revised base corpus or must be evaluated as a separate controlled variable.

### Phase 2 — balanced curriculum design, still no compute

Only after Phase 1 aligns, design a balanced set rather than a narrow four-failure patch. Candidate coverage should include:

- multiple neutral-separation forms for unrelated observations;
- multiple unresolved either/or notes with **zero** actions;
- pure B1/A1 restatement-dedup examples plus multi-topic variants;
- an action-count ladder rather than a single jump: A5, A6, A7, A8;
- several dense composites with varied role structures and qualifier positions;
- explicit counterexamples to unsupported "so," "therefore," or temporal-link insertions.

No example count is recommended yet. The count should follow the integrity audit and balance analysis, not be chosen first.

### Phase 3 — future controlled study

If a revised corpus is approved:

- retain the typed-marker contract;
- retain the frozen split mechanism;
- use same-seed A/B comparison;
- isolate target corrections from newly added examples where feasible;
- freeze acceptance and protected scoring before compute;
- require separate Johnny authorization.

## Immediate gates

- Seed 73: **blocked**.
- App activation/export/deployment: **blocked**.
- New corrective examples: **not yet authorized**.
- Existing-target edits: **not yet authorized**.
- Further model compute: **not authorized**.

## Alignment status

**ChatGPT audit complete. Claude should independently verify the counts, coverage classifications, and three target-integrity concerns. Any disagreement must be returned to Johnny before corpus changes are made.**
