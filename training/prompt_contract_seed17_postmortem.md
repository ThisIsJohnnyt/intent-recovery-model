# Prompt-Contract Seed-17 Study — Evaluation Postmortem

**Status:** ChatGPT design analysis for joint Claude/Johnny review  
**Date:** 2026-08-02  
**Compute authorized:** none  
**Implementation authorized:** none

## Executive conclusion

The seed-17 study falsified the narrow hypothesis that changing the prompt from a fixed 3–7 bullet request to source-determined bullets—and retraining on the same 66 examples—would produce the desired behavior without material regression.

It did not falsify the product goal. The desired behavior remains correct: output should contain the number of supported ideas and actions the source actually contains, without padding, duplication, loss, or invention.

The study instead exposed three separable problems:

1. **Prompt wording alone is behaviorally inert on the tested checkpoint.** Cell A and Cell B2 have the same strict pass set, 10/16. Fourteen of sixteen outputs are byte-identical; the other two differ cosmetically.
2. **Retraining under the new wording is unstable rather than corrective.** Cell C remains 10/16, fixes regression guard 10, and breaks regression guard 11.
3. **The output contract does not provide reliably observable list boundaries.** Training targets separate bullet and action entries with newline characters, while every decoded output in Cells A, C, and the acceptance run contains zero newline characters. The app parser constructs arrays by splitting section text on `\n`. This makes literal item counts and production list boundaries dependent on a delimiter that is absent from the observed decoded strings.

The correct next step is contract and evaluation redesign, not another narrow corrective dataset.

## Frozen study outcome

| Gate | Result |
|---|---|
| Cell C format validity: 16/16 | PASS |
| No Cell-A regression-guard pass becomes a Cell-C failure | FAIL — Probe 11 |
| Cell C strict passes >= Cell A | PASS — 10/16 each |
| All five source-determined-bullets acceptance gates pass | FAIL — 1/5 |

Seed 73 correctly remains unrun. The app prompt-contract PR correctly remains unmerged.

## What each comparison establishes

### A vs. B2: prompt-only effect

- Same seed-17 checkpoint and checkpoint fingerprint.
- Old prompt vs. new prompt.
- Same strict pass set: 01, 03, 04, 05, 07, 11, 12, 13, 14, 15.
- No pass/fail flips.

Conclusion: this prompt wording change alone does not produce a measurable protected-benchmark benefit or regression at this checkpoint. It also does not make the old model satisfy the new source-determined contract.

### A vs. C: retraining effect

- Same seed and same 66-example gold-v1.2.2 corpus.
- Cell C trained under the new prompt.
- Aggregate strict score remains 10/16.
- Probe 10 changes fail → pass.
- Probe 11 changes pass → fail by inventing garage-light actions.

Conclusion: retraining changes which capability fails, not the total capability level. The candidate fails the no-regression gate even though its aggregate is neutral.

### Acceptance behavior

Only sdb-03 passes. Failures are heterogeneous:

- sdb-01: unsupported trailing commentary;
- sdb-02: unsupported qualifier under the strict rubric;
- sdb-04: severe loss, reassignment, merge, and action-count failure;
- sdb-05: restated content remains duplicated instead of being cleanly collapsed.

Conclusion: the failure is not one narrow “bullet count” defect. It spans grounding, retention, grouping, deduplication, and output representation.

## Representation finding

The current training target is constructed as:

1. section marker;
2. narrative;
3. section marker;
4. each bullet as a separate newline-joined string;
5. section marker;
6. each action as a separate newline-joined string.

The production parser then uses `split('\n')` to recover bullet and action arrays.

Observed evidence from this study:

- all 16 Cell-A raw outputs contain zero newline characters;
- all 16 Cell-C raw outputs contain zero newline characters;
- all five Cell-C acceptance outputs contain zero newline characters.

Section markers survive decoding reliably, but item boundaries do not appear in the decoded strings. This creates two risks:

- evaluation must infer item counts semantically instead of reading actual boundaries;
- production may parse an entire bullet or action section as one array item even when the model intended several.

Claude’s tokenizer/runtime investigation should determine the exact mechanism and production impact. The design implication does not depend on assigning blame to a particular tokenizer: a contract whose required boundary is absent from observed outputs is not machine-verifiable as implemented.

## Corpus evidence

The frozen 66-example corpus already contains meaningful count diversity:

| Count | Bullet examples | Action examples |
|---:|---:|---:|
| 0 | 0 | 8 |
| 1 | 4 | 24 |
| 2 | 13 | 18 |
| 3 | 24 | 8 |
| 4 | 18 | 7 |
| 5 | 6 | 1 |
| 6 | 1 | 0 |

- 17/66 examples have only one or two bullets.
- Bullet targets range from 1–6.
- Action targets range from 0–5.

The eight-action acceptance case is therefore outside the observed action-count range of the 66-example training corpus. It remains a legitimate generalization stress case, but it should not be the only test of eight-item structural conformance because a failure cannot distinguish marker/count handling from semantic capacity. The vNext evaluation proposal separates those questions.

This confirms that the dataset did not simply teach a three-item floor. The failed study therefore should not be explained as “all old targets were padded.” The representation and broader semantic-learning problems remain.

## Evaluation-process finding

The study also exposed a runner/provenance flaw. Prompt worktrees were pinned correctly, but their copies of `run_benchmark.py` predated fail-closed `required_semantic_dimensions` propagation. All four raw result files therefore lacked the field.

The repair was deterministic and safe, but future studies must pin prompt construction separately from the current benchmark runner. Prompt reproducibility must not roll back evaluation-schema safety.

## What the study does not establish

- It does not show that source-determined output is the wrong product behavior.
- It does not show that the new prompt is intrinsically harmful; A vs. B2 is neutral.
- It does not prove that explicit item markers will fix unsupported additions or topic loss.
- It does not prove that seed 17 represents the mean behavior of retraining; the candidate already fails frozen gates, so seed 73 is unnecessary under this study’s decision rule.
- It does not justify patching only Probe 11, sdb-02, or sdb-05. The failure family is broader.

## Recommended decision

Retain the product goal, retire `source-determined-bullets-v1` as a deployment candidate, and evaluate a marker-delimited item contract before authoring another corrective curriculum.

No further compute should occur until:

1. Claude completes the tokenizer/parser feasibility investigation;
2. ChatGPT’s contract and evaluation proposals are jointly reviewed;
3. both sides agree on a machine-verifiable item representation;
4. Johnny approves the selected option and a new controlled-study manifest.

## Alignment status

This postmortem is a proposal, not a unilateral decision. Any disagreement from Claude—especially concerning tokenizer round-tripping, production parsing, or the feasibility of repeated item markers—should be brought to Johnny before contract or dataset changes.
