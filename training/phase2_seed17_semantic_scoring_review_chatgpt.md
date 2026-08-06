# Controlled seed-17 Phase-2 replay — ChatGPT semantic scoring review

**Date:** 2026-08-06  
**Status:** Semantic scoring complete; pending Claude Code's independent verification.  
**Scope:** Four already-generated raw result files only. No training, inference, checkpoint selection, Gate-6 disposition, P2-A/B/C/D/X classification, seed 73, corpus change, export, deployment, or activation.

## 1. Scoring basis

Each record was scored against the benchmark definitions frozen at package commit `1ee8ad5976f3243269c7476000d49b1d8140205c`, using:

1. `expected_behavior`;
2. `required_semantic_dimensions`;
3. `primary_checks`, bound exactly to the result's `capability_checks`; and
4. the generic scale `2 = correct`, `1 = partially correct`, `0 = failed`.

Only an exact score of `2` on every required dimension and literal `true` on every capability check counts as a semantic strict pass. Acceptance-10 combined strict pass additionally requires both frozen count rules to pass.

The natural 720-step run is the sole decision-bearing primary. The 600-step run is diagnostic control only.

## 2. Raw-input identity and scored artifacts

The supplied SHA-256 values matched all five attachments exactly. The raw files remained byte-immutable. Scored copies change only `scores`, `capability_checks`, and `failure_labels`; every other record field, ID, ordering position, and `raw_output` is unchanged.

| Role | Raw SHA-256 | Scored artifact | Scored SHA-256 |
|---|---|---|---|
| Primary 720 / protected-16 | `024d9f20f92cd6340404fd29d7439cbd2b3eac65afe5c3d935e464c2966ea59f` | `phase2_seed17_primary720_protected16_scored_chatgpt.json` | `ea0864b26df3ea5d207d1f736a486ec1d3910728597a445334562a7f2b1dacc9` |
| Primary 720 / acceptance-10 | `6b90f54456c59330518608a6d23996e7b7c13804baf939cd549522e643ce4c69` | `phase2_seed17_primary720_acceptance10_scored_chatgpt.json` | `2b5cc737669487c1a05a361987a96adddabbb43f0eb3aab14205007244e269c2` |
| Control 600 / protected-16 | `f9ca51334414426255a6babf8f9d16375e2956acae516e1619d0214f8785a36f` | `phase2_seed17_control600_protected16_scored_chatgpt.json` | `8fb5829f2c472ef4c3ede234d68af2b2c57ecd89891d346db9ff8792417f129b` |
| Control 600 / acceptance-10 | `414e75468392cdde61f312b34117e09c37df7bf5324c4754d1dce54ade628cf4` | `phase2_seed17_control600_acceptance10_scored_chatgpt.json` | `900c6b44ee4fef50ffc06ef5011bdb213761d1bf91bfedd3bc6ef052026c2c29` |

Receipt SHA-256: `526f7d264e163d6e443ce2b4a0a3caa9b519b93d8e8e196b3d27becfcd48d875`.

## 3. Verified aggregates

The unchanged `report_benchmark.py --contract=v2` accepted all four scored files and revalidated the stored v2 structural package from each unchanged `raw_output`.

| Measure | Primary 720 | Control 600 |
|---|---:|---:|
| Protected format validity | 16/16 | 16/16 |
| Protected semantic strict pass | 12/16 | 11/16 |
| Acceptance format validity | 10/10 | 10/10 |
| Acceptance count-rule conformance | 6/10 | 5/10 |
| Acceptance semantic strict pass | 6/10 | 6/10 |
| Acceptance combined strict pass | 5/10 | 5/10 |

Primary protected pass set:

`{01, 03, 04, 05, 07, 09, 10, 12, 13, 14, 15, 16}`

Control protected pass set:

`{01, 03, 04, 05, 07, 10, 12, 13, 14, 15, 16}`

Both acceptance combined-pass sets:

`{sdi2-01, sdi2-02, sdi2-04, sdi2-05, sdi2-09}`

## 4. Primary 720 scoring notes

### Protected-16

| ID | Result | Required-dimension scores | Key judgment |
|---|---|---|---|
| 01 | Pass | topic 2; uncertainty 2; unsupported 2 | Incomplete freezer thought and Kira reminder are preserved. |
| 02 | Fail | topic 1; unsupported 1 | Invents "the computer," breaks the tablet cause/reconnection, and fragments the screen-black condition away from the tablet task. |
| 03 | Pass | topic 2; unsupported 2 | Celia task remains combined; clock remains a separate observation. |
| 04 | Pass | all four dimensions 2 | Roles, ask-target, and unresolved question are correct. |
| 05 | Pass | all four dimensions 2 | Speaker/actor/recipient roles, folder-link task, and photo-scope question survive. |
| 06 | Fail | topic 2; attribution 1; uncertainty 2; unsupported 1 | Stamped-copy ambiguity survives, but the earlier "she asked" clause is incorrectly assigned to Rowan. |
| 07 | Pass | topic 2; uncertainty 2; unsupported 2 | Refund remains unresolved; save task survives. |
| 08 | Fail | topic 1; uncertainty 1; unsupported 0 | Rewrites the source question around "dry weather," assigns the lunchtime dryness to the plant, and invents causality. Recycling task survives. |
| 09 | Pass | topic 2; uncertainty 2; unsupported 2 | Schedule question, sent-mail check, and incomplete volunteer-list thought survive. |
| 10 | Pass | topic 2; unsupported 2 | All rehearsal observations and the shipping-label task survive across the structured output; no unsupported proposition is added. |
| 11 | Fail | topic 1; unsupported 1 | Invents "register the garage light" in narrative and drops Thursday from the fee action, though the two supported actions remain present. |
| 12 | Pass | all four dimensions 2 | All six topics, both tasks, uncertainty, and names survive. |
| 13 | Pass | topic 2; unsupported 2 | Both unrelated tasks survive as separate actions; this repairs the R2 replay's probe-13 loss. |
| 14 | Pass | topic 2; unsupported 2 | Observation preserved; no action invented. |
| 15 | Pass | topic 2; unsupported 2 | Tentative idea remains tentative and is not promoted. |
| 16 | Pass | topic 2; uncertainty 2; unsupported 2 | Reminder survives and both references remain unresolved. |

### Acceptance-10 failures and structural-only miss

| ID | Semantic result | Count result | Key judgment |
|---|---|---|---|
| sdi2-03 | Fail | Fail | Preserves both observations but invents a merged purchase/placement action. |
| sdi2-06 | Fail | Pass | Both alternatives and the non-answer observation survive, but narrative "was undecided" conflicts with bullet "Still undecided"; uncertainty scored 1 pending independent review. |
| sdi2-07 | Fail | Fail | One action is retained, but the restated task becomes three bullets instead of one. |
| sdi2-08 | Pass | Fail | All eight tasks survive with no invention, but eight bullets exceed the hard maximum of seven. |
| sdi2-10 | Fail | Fail | The prose contains the six source ideas, but bullets compress them to four and actions merge two tasks into one; topic completeness is partial. |

## 5. Diagnostic control distinctions

- Control protected probe `09` fails because the incomplete volunteer-list thought becomes an invented question about whether the list was sent to Imani. The primary preserves the incomplete thought and passes.
- Both runs fail protected probe `06` on the Rowan attribution, though the exact conflict appears in different fields.
- Both runs repair protected probe `13` relative to the earlier R2 replay.
- Control `sdi2-06` adds an unsupported "Decide between…" action, so its count rules fail; the primary avoids the action and passes the count rules but retains the narrative/bullet tense inconsistency.
- Both runs preserve all eight `sdi2-08` tasks semantically but violate the hard seven-bullet ceiling.

## 6. Independent-verification focus

Claude should independently verify every record and all mechanical invariants. The most judgment-sensitive item is primary `sdi2-06`: this scoring treats the conflict between past-tense "was undecided" and present-tense "Still undecided" as partial uncertainty preservation (`1`), even though the capability check `CHOICE_REMAINED_UNRESOLVED` is `true` because the bullet explicitly preserves the unresolved choice.

Any disagreement must be surfaced to Johnny. This document does not apply the frozen six gates or assign P2-A/B/C/D/X; those remain separately gated after independent scoring verification.
