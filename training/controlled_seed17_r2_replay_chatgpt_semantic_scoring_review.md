# Controlled seed-17 R2 replay — ChatGPT semantic scoring review

**Date:** 2026-08-03  
**Status:** Independently verified by Claude Code; the sole disagreement on protected probe 10 is resolved in Claude's favor and incorporated here.  
**Commit status:** Do not commit these scoring artifacts until that independent verification is complete and any disagreement is surfaced to Johnny.

## Scope and rubric

This review scores only the two already-generated replay result files. It performs no training, inference, seed-73 work, export, deployment, or activation.

The confirmed canonical scoring basis is:

1. each probe's `expected_behavior`;
2. its `required_semantic_dimensions`;
3. its `primary_checks` (bound to the result's `capability_checks` keys); and
4. the generic scale `2 = correct`, `1 = partially correct`, `0 = failed`.

The unchanged reporter applies the strict aggregate rule: every required dimension must be exactly 2, every capability check must be true, format must be valid, and—on the v2 acceptance set—both count rules must pass.

## Artifact integrity

The two scored files were produced from the raw replay results by changing only `scores`, `capability_checks`, and `failure_labels`. Record order and IDs are unchanged; all required dimensions are non-null; all capability-check values are literal booleans. The unchanged `report_benchmark.py --contract=v2` accepted both files and independently revalidated their complete structural packages.

| Artifact | SHA-256 |
|---|---|
| `controlled_seed17_r2_replay_protected16_scored_chatgpt.json` | `240b4ce35a6df9352f3bc41749468b3d111041f9b910efa811ac41db36a4e4ca` (supersedes `2a887f...`) |
| `controlled_seed17_r2_replay_acceptance10_scored_chatgpt.json` | `b3a43497cdec6e501118592808be0d750af7ccb818ae97738d7818a8f65238a3` |

The three newly supplied supporting files were also read successfully:

| Supporting file | SHA-256 |
|---|---|
| `gold_v1.2.1_lessons_learned.md` | `2f387128ee2c3781a240bcd816bf8058a64bd7b357a785023477c1f99d345c49` |
| `prepare_data.py` | `2e620cf82a4dbfbc60fa71b9df914aab3086fdd4b2c33afde9685ec5a60480cc` |
| `real_data_private.py` | `8a5e20fe78846c8b1436c817e8cfa31e6c6564b1d72d8c8679d7a3140d23f47d` |

## Reporter results

| Measure | Baseline | R2 candidate | Change |
|---|---:|---:|---:|
| Protected format validity | 16/16 | 16/16 | — |
| Acceptance format validity | 10/10 | 10/10 | — |
| Acceptance count-rule conformance | 6/10 | 7/10 | +1 |
| Acceptance combined strict pass | 4/10 | 6/10 | +2 |
| Protected strict pass | 11/16 | 12/16 | +1 |
| Protected regression guards passed | 10/12 | 10/12 | — |

The acceptance count-rule improvement is `sdi2-06`. The combined strict-pass gains are `sdi2-03` and `sdi2-04`; there are no combined strict-pass losses because `sdi2-08` already failed its action-count rule in both runs.

On the protected set, strict gains on `06` and `16` outweigh the strict loss on `13`. The same-seed preservation check nevertheless fails because baseline-passing regression guard `13` no longer passes.

The canonical six-gate result is: gates 1, 2, and 5 pass; gates 3, 4, and 6 fail. This is **Outcome B — improvement without a full pass**. It does not authorize Phase 2, seed 73, export, deployment, or activation.

## Protected-16 scoring notes

| ID | Result | Required-dimension scores | Key judgment |
|---|---|---|---|
| 01 | Pass | topic 2; uncertainty 2; unsupported 2 | Incomplete freezer thought stays incomplete; Kira reminder survives. |
| 02 | Fail | topic 1; unsupported 1 | Tablet fragments reconnect, but the donation-box task is absent from actions and the output merges/fragments topics. |
| 03 | Pass | topic 2; unsupported 2 | Combined Celia task remains unsplit; clock remains a separate observation. |
| 04 | Pass | all four dimensions 2 | Roles, unresolved question, and ask-target are correct. |
| 05 | Pass | all four dimensions 2 | Roles, task, and unresolved photo-scope question survive; typo is cosmetic. |
| 06 | Pass | all four dimensions 2 | Stamped-copy ambiguity is explicitly preserved; Rowan ask is correct. |
| 07 | Pass | topic 2; uncertainty 2; unsupported 2 | Refund remains unresolved and save task survives. |
| 08 | Fail | topic 1; uncertainty 1; unsupported 1 | Source question and drying observation are merged; `put recycling outside` mutates into `check on recycling`. |
| 09 | Pass | topic 2; uncertainty 2; unsupported 2 | Schedule question, sent-mail check, and incomplete volunteer-list thought survive. |
| 10 | Pass | topic 2; unsupported 2 | The repeated narrative clause is a real quality defect, but it adds no unsupported proposition and does not fragment bullets or actions; the frozen semantic gate therefore passes. |
| 11 | Fail | topic 1; unsupported 2 | Both tasks exist, but the Thursday qualifier is dropped from the registration-fee action. |
| 12 | Pass | all four dimensions 2 | All six topics, both tasks, uncertainty, and names survive. |
| 13 | Fail | topic 1; unsupported 2 | Email task is present in narrative/bullets but missing from actions. |
| 14 | Pass | topic 2; unsupported 2 | Observation preserved; no task invented. |
| 15 | Pass | topic 2; unsupported 2 | Tentative idea stays tentative and is not promoted to an action. |
| 16 | Pass | topic 2; uncertainty 2; unsupported 2 | Both dangling references remain unresolved; supported reminder survives. |

## Acceptance-10 scoring notes

| ID | Combined result | Required-dimension scores | Key judgment |
|---|---|---|---|
| sdi2-01 | Pass | topic 2; unsupported 2 | One observation, no action, no added cause or advice. |
| sdi2-02 | Pass | topic 2; unsupported 2 | Task, deadline, and destination survive; counts are exact. |
| sdi2-03 | Pass | topic 2; unsupported 2 | Two observations remain distinct; no action is invented. |
| sdi2-04 | Pass | topic 2; unsupported 2 | Observation and Monday task remain separate; exact counts. |
| sdi2-05 | Pass | topic 2; uncertainty 2; unsupported 2 | Tentative idea remains tentative; no action. |
| sdi2-06 | Fail | topic 2; uncertainty 1; unsupported 1 | Counts now pass, but past-tense `was undecided` and imperative-like `Decide between` do not preserve a currently unresolved choice cleanly. |
| sdi2-07 | Fail | topic 2; unsupported 1 | Action deduplicates, but narrative/bullets repeat the same task and bullet count is 2 instead of 1. |
| sdi2-08 | Fail | topic 1; unsupported 0 | Berry-puree task is lost, library-form task is reassigned as being sent `to me`, and only 6/8 actions survive. |
| sdi2-09 | Pass | topic 2; uncertainty 2; unsupported 2 | Task and unresolved references survive; exact counts. |
| sdi2-10 | Fail | topic 1; attribution 2; uncertainty 2; unsupported 2 | Roles, tasks, idea, and question survive, but the Saturday deadline is lost and the question lacks its required sixth bullet. |

## Disagreement resolution and required next step

Claude Code independently verified 25/26 judgments and challenged only probe 10. ChatGPT accepts that correction: repetition of supported content is not an unsupported addition, and no bullet/action over-splitting occurred. The corrected score is `unsupported_addition_resistance = 2` with no failure label.

Before committing, Claude should re-hash this revised protected file, rerun the unchanged reporter, and update `training/controlled_seed17_r2_replay_claude_verification.md` to record the resolved disagreement and the corrected 12/16 protected result. Once those mechanical updates agree, the reviewed Outcome-B evidence package is ready to commit. The commit records the experiment; it does not authorize any next-phase compute or deployment action.
