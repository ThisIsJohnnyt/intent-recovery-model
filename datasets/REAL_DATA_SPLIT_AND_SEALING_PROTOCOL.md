# Real-Data Split Assignment and Sealing Protocol

## Status

**Proposed, revision 2, for joint review. The first approved pilot is validation-only; the holdout remains empty.**

## Roles

### Real validation

`datasets/real_validation.jsonl` is private, evaluation-only data that may be inspected after declared model runs. Its errors may inform curriculum, prompt, training-budget, and checkpoint decisions.

### Sealed holdout

`datasets/real_holdout.jsonl` is private, evaluation-only data used for a frozen release candidate at a declared milestone. Its contents and outputs do not guide routine development.

Neither split is trained on or published.

## Readiness sequence

1. Approve governance and annotation specifications.
2. Add and verify all private-path ignore rules before creating private artifacts.
3. Implement consent, provenance, de-identification, logging, scoring, and withdrawal mechanisms.
4. Remove routine holdout materialization from `prepare_data.py`.
5. Synchronize the source-determined bullet contract across the training and production repositories.
6. Validate the complete workflow using synthetic dummy records.
7. Complete a joint readiness review.
8. Populate a validation-only pilot of at most eight records.
9. Run and review the pilot.
10. Correct process defects using dummy or validation records.
11. Conduct a separate holdout-readiness review.
12. Only then collect and seal holdout records.

## Assignment prerequisites

Before a record can be assigned, it must have:

- active consent for the intended split;
- approved de-identification;
- stable source and pair fingerprints;
- an adjudicated expected output;
- an adjudicated private rubric;
- duplicate and near-duplicate review; and
- no prior model evaluation.

Assignment occurs before any model output for that record is generated or viewed.

## Grouping and leakage prevention

Records derived from the same underlying event, task, note thread, or near-duplicate wording form one assignment group. A group cannot be divided between validation and holdout.

Check candidate records against:

- synthetic training data;
- synthetic validation data;
- gold curricula;
- protected benchmark probes;
- real validation;
- current and retired holdouts; and
- prior rejected real records when their reuse would create leakage.

Use structural and semantic review, not noun matching alone. A note that is a near-structural twin of a protected probe is excluded or assigned to validation, never holdout.

## Coverage descriptors

Coverage describes notes and recovery operations, never contributor diagnoses. Track:

- input length;
- number of distinct ideas;
- explicit-action presence;
- open-question presence;
- uncertainty presence;
- attribution complexity;
- interruption or resumption structure;
- dangling-reference presence;
- repeated-task presence;
- temporal or causal relationships;
- difficulty; and
- primary capability category.

Coverage supports review but does not justify adding unsafe or low-quality records.

## Pilot assignment

All first-pilot records go to real validation. The holdout remains empty. The pilot tests:

- consent and manifest handling;
- de-identification quality;
- annotation and adjudication;
- structured evaluation logging;
- strict semantic scoring;
- deletion and withdrawal;
- privacy of generated outputs; and
- reviewer burden.

Pilot results may diagnose process defects. They must not be described as a population-level generalization estimate.

## Holdout construction

After the validation pilot is accepted, holdout construction requires a declared versioned plan specifying:

- target coverage;
- permitted source pool;
- assignment groups;
- annotation and review completion;
- planned seal date;
- access list;
- release-milestone rule; and
- retirement rule after unsealing.

The project may start with a small holdout, but must report its size and coverage without overstating confidence. No minimum size guarantees validity.

## Sealing event

A holdout becomes sealed only when:

- every record is consented, de-identified, annotated, and adjudicated;
- record IDs and fingerprints are locked;
- duplicate checks are complete;
- source, manifest, rubric, and evaluation paths are private and gitignored;
- cross-repository training and production prompt contracts have matching versions and rendered-prompt hashes;
- the sealed dataset fingerprint is recorded;
- routine `prepare_data.py` cannot open or copy it;
- only the explicit holdout evaluator can load it in memory;
- access and milestone rules are recorded; and
- Claude Code and ChatGPT report `Aligned`.

After sealing, no content inspection, rubric change, record substitution, or exploratory evaluation is allowed without breaking the seal.

## Declaring a holdout evaluation

Before invocation, record:

- release milestone identifier;
- single frozen release-candidate checkpoint;
- checkpoint fingerprint;
- git commit;
- training seed and configuration;
- frozen scoring rubric version;
- frozen dataset fingerprint;
- pass/fail release gates; and
- people authorized to view the results.

The holdout is a go/no-go check for the frozen candidate. It is not used to select among seeds or checkpoints.

## Evaluation and review

- The evaluator loads the sealed source directly in memory.
- No routine processed holdout file is written.
- A private structured result is saved under the declared milestone.
- ChatGPT and Claude Code score independently under the frozen rubric.
- Each reports evidence alignment and action alignment.
- Johnny decides only if alignment remains unresolved.

## After unsealing

Once record-level holdout outputs or errors are inspected, that holdout version is consumed. It cannot remain a sealed test for future fixes.

The project must choose one documented disposition:

- retire the records into a private used-holdout archive;
- with appropriate consent, move suitable records into real validation; or
- delete withdrawn or unnecessary records.

A future milestone requires a newly constructed and sealed holdout version. A failed holdout cannot be repeatedly evaluated while the project tunes against its errors.

## Seal-breaking events

The seal is broken by:

- exploratory evaluation;
- viewing content or rubrics outside the declared milestone;
- changing a record or expected output;
- withdrawal of a record;
- dataset-fingerprint mismatch;
- checkpoint or rubric substitution after declaration;
- unlogged access; or
- using results to choose among candidates.

When the seal breaks, stop evaluation, record the reason without quoting content, and retire or reseal the dataset as appropriate.

## Alignment status

**ChatGPT revision 2 for Claude verification.**
