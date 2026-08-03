# Controlled Seed-17 R2 Replay Protocol

**Project:** Intent Recovery Model  
**Protocol status:** Draft for independent repository verification and product-owner approval  
**Compute status:** Not authorized  
**Proposed repository path:** `training/controlled_seed17_r2_replay_protocol.md`

## 1. Decision this protocol supports

The seed-17 v2 typed-marker study established that the representation layer works: all 26 evaluated outputs were parse-valid. It nevertheless failed the frozen acceptance gate because of semantic defects, including unsupported action invention, deduplication failures, weak high-count generalization, and attribution drift.

The postmortem then found three incorrect targets in the pinned 66-record Gold v1.2.2 corpus. Those targets were corrected in the separately fingerprinted Revision-2 candidate without modifying the original corpus.

This protocol defines a controlled replay that answers one narrow question:

> With every other experimental variable held constant, how does replacing the three defective Gold v1.2.2 targets with their accepted Revision-2 corrections affect the seed-17 v2-contract result?

This is an attribution experiment, not a new curriculum, seed sweep, production candidate, or authorization to proceed with compute.

## 2. Governing evidence and fixed project state

The repository verifier must confirm these references against the actual repository before requesting authorization:

| Item | Governing reference | Required interpretation |
| --- | --- | --- |
| Original Gold v1.2.2 source | Immutable source at commit `8d7aa09` | Read-only control corpus; must remain untouched |
| Accepted R2 candidate | `training/gold_v1.2.2_r2_derived_candidate.jsonl`, committed at `1c91203` | 66 records; exactly three accepted target corrections |
| R2 derivation evidence | R2 derivation script, report, proposal, design notes, and independent reviews committed at `1c91203` | Provenance and integrity evidence for the only permitted corpus change |
| Failed seed-17 v2 study | Gate-failure artifacts associated with commit `e37aeda` | Supplies the frozen baseline configuration, outputs, scoring procedure, and acceptance gate |
| Gold v1.2.3 | Historical-only work committed at `2f7a101`; reviewed source changes committed locally at `f205828` | Explicitly excluded from this replay; not promoted and not an input source |

If any reference is inaccurate, missing, ambiguous, or insufficient to reconstruct the baseline, Claude must stop and return the discrepancy to Johnny and ChatGPT. It must not be silently repaired through best judgment.

## 3. Experimental design

### 3.1 Independent variable

Only the following variable may change:

- **Training-target source:** the three original defective targets are replaced by the three accepted Revision-2 targets.

The replay must use the accepted R2-derived candidate explicitly. It must not load `datasets/synthetic.jsonl` implicitly because that file now contains reviewed Gold v1.2.3 source changes that are outside this experiment.

### 3.2 Variables that must remain frozen

Claude must recover these values from the committed seed-17 baseline artifacts and record their exact values in the verification addendum:

- base model and exact model revision;
- tokenizer and tokenizer revision;
- typed-marker prompt contract, including `###BULLET###` and `###ACTION###` handling;
- preprocessing and serialization behavior;
- training/validation record membership;
- record order within each split;
- seed: **17**;
- training hyperparameters;
- optimizer and scheduler configuration;
- batch size and accumulation behavior;
- maximum input and output lengths;
- step count and checkpoint-selection rule;
- runtime and dependency versions that can affect determinism;
- decoding configuration;
- the same 26-case evaluation set and ordering;
- evaluator implementation and rubric;
- the complete frozen acceptance gate;
- output and artifact schema.

No value may be inferred from a current default when the baseline used an explicit or historical value.

### 3.3 Split-preservation rule

The replay must preserve baseline train/validation membership and order by stable record identity. The data-preparation process must not reshuffle or repartition the full 66-record corpus after substituting the corrected targets.

If the existing preparation tool cannot accept a frozen split manifest or equivalent stable-ID mapping, Claude must stop and propose a minimal, reviewable derivation method. That method must change target content only while preserving every baseline record's split and position.

### 3.4 No hidden additional variables

The replay must not include:

- Gold v1.2.3 records or source changes;
- newly authored Phase-2 curriculum examples;
- seed 73 or any other seed;
- altered prompts or marker syntax;
- new post-processing or deduplication;
- revised decoding parameters;
- gate, rubric, threshold, or scorer changes;
- dependency upgrades unless required to reconstruct the original environment and separately disclosed;
- production export, activation, or deployment work.

## 4. Mandatory preflight verification

Claude owns this verification. ChatGPT reviews the resulting evidence for experimental validity.

### 4.1 Repository and source checks

- Record the checked-out commit and its relationship to `origin/main`.
- Confirm the working tree state and identify any local-only commit required for context.
- Verify that the immutable Gold v1.2.2 files remain unchanged through the checked-out revision.
- Re-run or independently reproduce the R2 candidate integrity checks.
- Confirm 66 records in both control and R2 candidate.
- Confirm identical stable record identities and ordering before split preparation.
- Confirm exactly three target-bearing records differ.
- Confirm all inputs and all non-target metadata are unchanged.
- Record cryptographic fingerprints for the original corpus, R2 candidate, proposal, derivation script, and derivation report.

### 4.2 Baseline reconstruction checks

- Identify the exact seed-17 training command or canonical manifest.
- Identify the exact processed train and validation artifacts used by the failed baseline.
- Record stable record identities and ordering for both splits.
- Identify the exact checkpoint evaluated.
- Identify the exact 26-case evaluation input and its fingerprint.
- Identify the exact scorer, rubric, and gate definition with fingerprints.
- Confirm that the committed baseline result can be read and rescored without changing its recorded outcome.

### 4.3 Candidate split checks

- Derive candidate train and validation artifacts using the frozen baseline membership and order.
- Demonstrate that the only semantic changes are the three accepted target corrections.
- Produce a machine-readable diff linking each changed record to `ti-001`, `ti-002`, or `ti-003`.
- Confirm that no Gold v1.2.3 record or source change is present.
- Record fingerprints for the candidate train and validation artifacts.

### 4.4 Execution-safety checks

- Use a new, exclusive experiment identifier and artifact directory.
- Fail closed if the identifier or output path already exists.
- Save configuration, environment, command, source revision, input fingerprints, and timestamps before training begins.
- Ensure interruption cannot overwrite the failed baseline or any accepted corpus artifact.
- Confirm that no application export, deployment, or production path is invoked.

## 5. Authorization gate

Completion of the preflight package does not authorize execution.

Claude must provide the completed verification addendum to ChatGPT. ChatGPT must report whether the experiment is a valid one-variable comparison. Any disagreement must be presented to Johnny explicitly.

Only Johnny may authorize the replay. Authorization must name this controlled seed-17 R2 replay specifically. It does not authorize seed 73, Phase-2 training, additional runs, export, activation, or deployment.

## 6. Execution requirements after authorization

If Johnny authorizes the replay, Claude executes exactly one seed-17 training and evaluation sequence using the verified configuration.

Claude must:

1. Reconfirm all preflight fingerprints immediately before execution.
2. Run the frozen training configuration with the R2-derived split artifacts.
3. Preserve raw logs and structured training metrics.
4. Preserve the selected checkpoint and checkpoint-selection evidence.
5. Run the frozen 26-case evaluation exactly once against that checkpoint.
6. Preserve raw model outputs before parsing or scoring.
7. Run the frozen parser and scorer without modification.
8. Produce an immutable comparison package without overwriting baseline artifacts.

Unexpected failures, nondeterministic configuration gaps, missing dependencies, or artifact mismatches require a stop. They do not authorize an improvised rerun.

## 7. Scoring and comparison plan

ChatGPT owns the primary evaluation architecture and scoring interpretation. Claude independently verifies every result against the stored outputs and code.

### 7.1 Frozen gate

The replay is judged by the exact acceptance gate used for the original seed-17 v2 study. No threshold, weighting, rubric interpretation, probe set, or pass rule may be changed after outputs are visible.

Parse validity remains a regression guard. Repeating the previous 26/26 result is necessary but not sufficient.

### 7.2 Case-level comparison

For each of the 26 cases, compare baseline and replay outputs and classify the result as:

- improved;
- unchanged pass;
- unchanged failure;
- regressed;
- changed but gate-neutral.

Every changed case must receive evidence-linked annotations for all applicable failure classes:

- unsupported action invention;
- failure to deduplicate repeated intent;
- high-count generalization failure;
- attribution or speaker drift;
- parse or contract-format failure;
- other, with a written justification tied to the frozen rubric.

The comparison must distinguish exact output change from rubric-relevant behavioral change.

### 7.3 Required aggregate reporting

The report must include:

- overall frozen-gate result;
- format-valid count out of 26;
- strict pass count out of 26, if that measure belongs to the frozen baseline gate;
- counts by failure class;
- baseline-to-replay transition matrix;
- list of regressions;
- list of resolved failures;
- list of persistent failures;
- any newly observed failure pattern;
- a statement of what the experiment does and does not establish causally.

## 8. Decision rules

### Outcome A -- Full gate pass

- Record the R2 replay as a passing seed-17 candidate result.
- Do not promote, export, activate, or deploy it automatically.
- Seed 73 remains blocked until ChatGPT and Claude complete a joint review and Johnny makes a separate decision.

### Outcome B -- Improvement without a full pass

- Accept the result as evidence that target integrity mattered but was insufficient.
- Use only the residual, evidence-supported failure classes to design a Phase-2 balanced curriculum proposal.
- Do not begin Phase-2 training without a new static review and separate authorization.

### Outcome C -- Neutral or worse result

- Preserve the result as evidence that the three corrections were necessary for corpus integrity but insufficient to improve this training outcome.
- Do not revert the accepted corrections merely because the model did not improve.
- Choose between a Phase-2 curriculum proposal, a learning-contract redesign, or freezing v2.

### Outcome D -- Structural or reproducibility failure

- Mark the replay inconclusive.
- Do not substitute a second run or different seed.
- Resolve the reproducibility defect through a separately reviewed proposal before requesting any new compute authorization.

## 9. Required deliverables

### Before compute

1. This protocol, reviewed by Claude.
2. A completed repository verification addendum containing exact paths, commands, versions, and fingerprints.
3. A frozen experiment manifest.
4. A machine-readable original-versus-R2 corpus diff.
5. A machine-readable baseline-versus-candidate split comparison.
6. Written ChatGPT validity review.
7. Johnny's explicit replay authorization.

### After authorized compute

1. Raw training logs and structured metrics.
2. Checkpoint manifest and fingerprints.
3. Raw 26-case outputs.
4. Frozen-scorer output.
5. Case-level comparison and failure annotations.
6. Claude's independent verification report.
7. ChatGPT's scoring and interpretation report.
8. Joint recommendation to Johnny, including any disagreement.

## 10. Ownership

| Work item | Primary owner | Required review or decision |
| --- | --- | --- |
| Protocol and evaluation design | ChatGPT | Claude verifies; Johnny approves scope |
| Repository verification addendum | Claude | ChatGPT reviews experimental validity |
| Frozen experiment manifest and split derivation | Claude | ChatGPT checks one-variable isolation |
| Compute authorization | Johnny | Requires completed preflight and joint readiness |
| Training and evaluation execution | Claude | Must match authorized manifest exactly |
| Primary scoring and failure classification | ChatGPT | Claude independently verifies |
| Disagreement resolution | Johnny | Both positions must be presented without silent compromise |
| Seed-73 unblock decision | Johnny | Separate decision after a seed-17 pass and joint review |

## 11. Explicit non-authorizations

Approval of this document alone does **not** authorize:

- training, inference, or benchmark execution;
- seed 73;
- a Phase-2 curriculum or additional examples;
- scorer or gate changes;
- use of Gold v1.2.3 as training input;
- app-side contract activation;
- model export, deployment, or production promotion;
- modification of immutable Gold v1.2.2 artifacts.

## 12. Claude verification addendum template

Claude should complete this section in a separate repository-backed review artifact or in a reviewed revision of this document.

| Verification field | Repository-backed value |
| --- | --- |
| Checked-out commit | |
| `origin/main` commit | |
| Working-tree state | |
| Baseline seed-17 study reference | |
| Baseline training command/manifest | |
| Base model and revision | |
| Tokenizer and revision | |
| Training configuration fingerprint | |
| Original corpus fingerprint | |
| R2 candidate fingerprint | |
| Baseline train split fingerprint | |
| Baseline validation split fingerprint | |
| Candidate train split fingerprint | |
| Candidate validation split fingerprint | |
| Evaluation-set fingerprint | |
| Prompt-contract fixture fingerprint | |
| Scorer fingerprint | |
| Rubric/gate fingerprint | |
| Exclusive experiment identifier | |
| Exclusive artifact path | |
| Reproducibility caveats | |
| Claude readiness decision | `READY`, `NOT READY`, or `DISAGREEMENT` |

## 13. ChatGPT validity decision template

After Claude supplies repository evidence, ChatGPT records one of:

- **VALID ONE-VARIABLE REPLAY:** preflight demonstrates that only the three accepted targets changed.
- **NOT YET VALID:** listed defects must be corrected before authorization can be considered.
- **DISAGREEMENT:** Claude's and ChatGPT's positions are both presented to Johnny for decision.

Until one of these decisions is recorded and Johnny separately authorizes compute, the replay remains blocked.
