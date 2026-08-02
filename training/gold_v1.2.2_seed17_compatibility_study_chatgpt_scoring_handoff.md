# Gold v1.2.2 Seed-17 Prompt-Contract Compatibility Study — ChatGPT Scoring Handoff

**Scoring date:** 2026-08-02  
**Scorer:** ChatGPT, independent first pass  
**Engineering verification owner:** Claude Code  
**Decision owner:** Johnny

## Outcome

The seed-17 candidate does **not** clear the frozen compatibility-study bar.

| Gate | Result | Evidence |
|---|---|---|
| 1. Cell C format validity | **PASS** | 16/16 |
| 2. No Cell-A regression-guard pass becomes a Cell-C failure | **FAIL** | Probe 11 passes in A and fails in C |
| 3. Cell C overall strict passes >= same-seed Cell A | **PASS** | C 10/16; A 10/16 |
| 4. All source-determined-bullets acceptance gates pass | **FAIL** | 1/5 pass; 5/5 required |

Only two of four gates pass. Seed 73 should not start under the approved conditional plan, and `thought-organizer-app` PR #4 should remain unmerged.

## Strict results

| Cell | Format | Strict passes | Regression guards | Negative examples resolved |
|---|---:|---:|---:|---:|
| A — old-trained + old prompt | 16/16 | 10/16 | 9/12 | 1/4 (Probe 03) |
| B2 — old-trained + new prompt | 16/16 | 10/16 | 9/12 | 1/4 (Probe 03) |
| C — new-trained + new prompt | 16/16 | 10/16 | 9/12 | 1/4 (Probe 03) |
| C acceptance set | 5/5 | 1/5 | n/a | n/a |

### Pass sets

- **A:** 01, 03, 04, 05, 07, 11, 12, 13, 14, 15
- **B2:** 01, 03, 04, 05, 07, 11, 12, 13, 14, 15
- **C:** 01, 03, 04, 05, 07, 10, 12, 13, 14, 15
- **Acceptance:** sdb-03 only

## Controlled comparisons

### Cell A vs. Cell B2 — prompt change on identical weights

There are no strict pass/fail flips. Fourteen of sixteen raw outputs are byte-identical. Probe 06 changes only “Tell Rowan” to “Tessa told Rowan,” while retaining the same failing unsupported “Rowan needs the stamped copy” bullet. Probe 16 changes only terminal punctuation. At this seed/checkpoint, the new prompt alone is neutral on the protected benchmark: 10/16 to 10/16.

### Cell A vs. Cell C — retraining under the new prompt

The aggregate remains 10/16, but the composition changes:

- **Probe 10 improves:** A omits the shipping-label task from bullets/actions; C restores it and passes.
- **Probe 11 regresses:** A preserves the two supported actions without inventing a repair task; C adds unsupported “renew the garage light” / “pay garage light” content and fails.

Because Probe 11 is a regression guard that passes in Cell A, this single swap fails gate 2 even though the overall count stays equal.

## Failed-probe rationale

### Cell A and Cell B2

| Probe | Reason for failure |
|---|---|
| 02 | The interruption/resumption relationship is garbled as the tablet “returning to the tablet”; the real screen/charger cause is not reconnected to the investigation. |
| 06 | A bullet states that Rowan needs the stamped copy, contradicting the preserved Tessa-or-inspector ambiguity and adding an unsupported resolution. |
| 08 | The either/or source question remains confusingly malformed and the later drying observation is incorrectly assigned to the plant. |
| 09 | “The volunteer list needs to be checked” converts an explicitly incomplete thought into an unsupported task-like conclusion. |
| 10 | The shipping-label task appears only in narrative and disappears from bullets and action items; `TASK_SURVIVED` fails. |
| 16 | “Two men” invents a referent and “both are unrelated” adds unsupported commentary. |

### Cell C

| Probe | Reason for failure |
|---|---|
| 02 | The tablet fragments remain garbled; the real causal relationship is not restored, and the donation box is spuriously placed “on the tablet” in bullets. |
| 06 | The model changes “she asked” to Rowan and also asserts that Rowan needs the stamped copy, producing both misattribution and an invented resolution. |
| 08 | The original window-or-plant question is replaced with an invented “lack of water” cause. |
| 09 | The incomplete volunteer-list thought becomes “still alive,” and the sent-mail action is replaced with an unsupported mailbox/volunteer-list action. |
| 11 | The model invents “renew the garage light” and “pay garage light” as actions. |
| 16 | The referents remain unresolved, but the bullet adds trailing commentary (“both references are unresolved”) instead of stopping after the final source-supported clause. Under the established strict treatment of Probe 16, this is a minor Unsupported Addition and still fails. |

## Acceptance-set scoring

| Case | Result | Rationale |
|---|---|---|
| sdb-01 | **FAIL** | Correct one-item structure, but invents “both references are unresolved” where the source contains no references. |
| sdb-02 | **FAIL** | Correct two-item structure, but adds the unsupported qualifier “upcoming appointment.” Strict unsupported-addition resistance is 1, not 2. |
| sdb-03 | **PASS** | Exactly three supported ideas, with no loss, merge, or addition. |
| sdb-04 | **FAIL** | Severe loss and reassignment: roof inspection becomes an oil change, the callback disappears, router/drill content merges, and only two of eight required actions remain. |
| sdb-05 | **FAIL** | Bullet/action counts and deadline preservation pass, but the output retains both restatements inside one bullet instead of deduplicating them into one clean expression; `NO_DUPLICATE_FOR_RESTATED_TASK` fails. |

The two most judgment-sensitive calls are sdb-02 and sdb-05. Even if both were reversed during independent review, the acceptance set would reach only 3/5 because sdb-01 and sdb-04 are unambiguous failures. The 5/5 gate therefore cannot pass under any reasonable resolution of those two calls.

## Scaffold repair and provenance correction

All four raw result files lacked `required_semantic_dimensions`. The study used `run_benchmark.py` from the pinned prompt worktrees (`8d7aa09` and `80062bc`), both of which predate PR #15’s result-metadata propagation. This is a flaw in the jointly reviewed manifest’s runner pinning, not a compute-execution error.

No training or inference rerun is required. The scored copies in this handoff hydrate `required_semantic_dimensions` deterministically by probe ID from the frozen merged benchmark files:

- `gold_v1.2.1_probes.jsonl` for Cells A, B2, and C;
- `source_determined_bullets_acceptance.jsonl` for the acceptance results.

Raw outputs, automatic format-validity values, identity fields, and capability-check key sets remain unchanged. Only the missing required-dimension metadata and human scoring fields are populated. Every required dimension has a non-null score, and every declared capability check has a literal boolean.

`report_benchmark.py` still prints a generic note that records contain null fields because non-applicable semantic dimensions intentionally remain null. That note is not evidence of incomplete scoring here: validation confirms every dimension listed in each record's `required_semantic_dimensions` is scored and every declared capability check is boolean.

The provenance record’s statement that there were no deviations should be amended to record this scaffold-metadata deviation and deterministic repair. Before any future compatibility run, the manifest should separate the pinned prompt builder from the current benchmark runner, or define an explicit metadata-hydration step, so prompt pinning cannot silently restore a fail-open results schema.

## Artifacts for Claude verification

- `gold_v1.2.2_seed17_oldprompt_reference_scored_chatgpt.json`
- `gold_v1.2.2_seed17_newprompt_deployment_risk_scored_chatgpt.json`
- `gold_v1.2.2_seed17_newprompt_candidate_scored_chatgpt.json`
- `gold_v1.2.2_seed17_newprompt_candidate_bullets_acceptance_scored_chatgpt.json`
- This scoring handoff

Claude should independently review every score and capability check, paying particular attention to sdb-02, sdb-05, Probe 06, Probe 08, and Probe 16. Any disagreement should be reported to Johnny before the study is closed or a next experiment is authorized.

## Current recommendation

1. Do not run seed 73 under the present study plan.
2. Do not merge or deploy `thought-organizer-app` PR #4.
3. Correct the manifest’s runner/prompt pinning boundary and provenance record.
4. Have Claude independently verify this scoring package.
5. After alignment, decide whether the next design should address the broad failures exposed here or revise the prompt-contract approach before spending more compute.
