# Phase E — Real-Data Dummy-Workflow Implementation Handoff

## Authorization and status

**Authorized by the product owner on 2026-08-01.**
**Architecture alignment: Claude Code and ChatGPT aligned.**
**Implementation alignment: pending completed review packet.**

This phase implements and tests PDR-005 using synthetic dummy records only. It does not authorize real-note collection, real-validation population, sealed-holdout population, model training, checkpoint promotion, or a release change.

## Approved source package

Implementation must use the hash-verified Revision 2 archive:

`real_data_governance_revision2_verified.zip`

Archive SHA-256:

```text
ca02364cd2d31553939986af2d6baffc56b4bd437bbcf89120a0417b36fcfac0
```

Before importing the documents, verify `REVISION2_SHA256SUMS.txt`. Do not use the superseded five-file handoff.

## Documentation adoption

1. Import the five verified Revision 2 documents into their declared repository paths.
2. Apply the approved cosmetic correction in `REAL_DATA_ANNOTATION_GUIDE.md`: only the `hard` item, immediately before `expert`, should end with "; and."
3. Change PDR-005 status from `Proposed` to `Accepted` and record:
   - Product owner: approved;
   - Engineering lead, Claude Code: aligned; and
   - Dataset/evaluation architect, ChatGPT: aligned.
4. Record that document hashes changed after the approved status and punctuation edits.
5. Run the repository's `aislop` guard over every imported or modified Markdown file.
6. Resolve guard findings without changing approved semantics; document any intentional exception.

## Workstream 1 — Private paths and fail-safe ignore rules

Add explicit ignore coverage before any implementation writes a private-shaped artifact:

```gitignore
datasets/real_validation.jsonl
datasets/real_holdout.jsonl
datasets/private/
training/results/private/
training/data/processed/real_validation.jsonl
training/data/processed/real_holdout_eval.jsonl
```

The processed-holdout line remains defensive even though the implementation must stop creating that file.

Acceptance evidence:

- `git check-ignore` succeeds for every declared private path;
- temporary dummy files placed at those paths remain absent from `git status --porcelain`;
- cleanup restores the original empty/nonexistent state; and
- no private directory or source file is committed.

## Workstream 2 — Holdout least privilege

Modify routine preparation so `training/prepare_data.py`:

- does not open `datasets/real_holdout.jsonl`;
- does not validate or transform holdout records;
- does not write `real_holdout_eval.jsonl`; and
- continues to process synthetic train/validation and real validation as intended.

Modify `training/evaluate_holdout.py` so it:

- requires an explicit checkpoint and release-milestone identifier;
- opens `datasets/real_holdout.jsonl` only after validating the declared invocation;
- calls shared `load_jsonl`, `validate_record`, and `build_prompt` behavior directly;
- prepares the holdout in memory;
- writes no processed holdout dataset; and
- fails closed when the source is missing, empty, invalid, or fingerprint-mismatched.

Acceptance evidence:

- a routine `prepare_data.py` dummy test proves the holdout source was never opened;
- no processed holdout path exists after routine preparation or explicit evaluation;
- the explicit holdout path evaluates only its dummy holdout record; and
- cleanup removes all dummy private artifacts.

## Workstream 3 — Private manifests, rubrics, and deterministic fingerprints

Implement shared private-data utilities that support:

- `datasets/private/real_data_manifest.jsonl`;
- `datasets/private/real_data_rubrics.jsonl`;
- source, pair, and rubric fingerprints;
- split-level dataset fingerprints;
- checkpoint-directory fingerprints; and
- prompt-contract fingerprints.

Follow the exact canonical JSON and SHA-256 rules in `training/REAL_DATA_EVALUATION_PROTOCOL.md`.

Required behavior:

- manifest line order does not change a dataset fingerprint;
- a record, expected-output, rubric, split-name, or rubric-version change does;
- checkpoint traversal uses sorted POSIX relative paths;
- every regular checkpoint file contributes path, size, and file hash;
- symlinks fail closed;
- an empty checkpoint directory fails closed; and
- no raw note content is embedded in aggregate fingerprint manifests or logs.

## Workstream 4 — Structured private evaluation logging

Implement the `real-eval-v1` result structure for real validation and holdout.

Required output roots:

- `training/results/private/real_validation/<evaluation_id>.json`
- `training/results/private/real_holdout/<milestone>/<evaluation_id>.json`

Every generation record includes:

- evaluation ID, split, reason, and UTC timestamp;
- milestone for holdout;
- git commit;
- checkpoint metadata and fingerprint;
- seed and run ID;
- dataset fingerprint, rubric version, and record count;
- generation configuration;
- per-record stable ID, raw output, and format validity;
- four semantic fields initialized to `null`;
- capability checks, strict pass, labels, and review status; and
- aggregate and alignment sections.

The evaluator fails closed when asked to write outside the approved private result roots. Generated outputs are treated as private.

Routine unscored logs are evidence only. They cannot guide model, curriculum, seed, checkpoint, or release decisions.

## Workstream 5 — Strict semantic-scoring scaffold

Implement a scorer or scoring workflow that consumes a frozen raw generation artifact and a matching private rubric sidecar.

It must support the established fields:

- `topic_completeness`;
- `attribution_accuracy`;
- `uncertainty_preservation`;
- `unsupported_addition_resistance`;
- record-specific `capability_checks`;
- `failure_labels`; and
- `strict_pass`.

Strict pass is true only when format validity, all four semantic dimensions, and every capability check are true. One failure means strict failure. The raw generation artifact remains immutable; adjudicated scoring is written as a new version or separate artifact.

No automated semantic judge is authorized. Claude Code and ChatGPT continue to score independently, compare evidence, and escalate only unresolved disagreement to Johnny.

## Workstream 6 — Cross-repository prompt contract

The current 3–7 bullet minimum must be replaced by source-determined wording in both:

- intent-recovery-model: `training/prepare_data.py`; and
- thought-organizer-app: `src/services/noteOrganizer.ts`.

This is a paired dependency across deliberately separate repository/chat scopes.

Required coordination:

1. Define one shared prompt-contract version identifier.
2. Prepare the model-repository change without merging it alone.
3. Prepare the app-repository change in its proper session and repository.
4. Render the exact fixture `Prompt contract fixture: review the blue folder tomorrow?` through both prompt builders.
5. Require byte-identical UTF-8 output and matching SHA-256 hashes.
6. Record both commit hashes, contract versions, and the fixture hash.
7. Merge or release the paired changes together so main/prod never intentionally retains a train-serving contract mismatch.

Other Phase E work may proceed while this dependency is prepared. The real-validation pilot remains blocked until both sides are verified.

## Workstream 7 — Dummy workflow and withdrawal drill

Use obviously synthetic dummy records. Do not use real notes, copied communications, or realistic private identifiers.

The end-to-end drill covers:

1. dummy consent/provenance entry;
2. dummy de-identification status;
3. dummy expected output and rubric;
4. private-path ignore verification;
5. validation generation and structured logging;
6. initial unscored semantic fields;
7. manual scoring and strict aggregate calculation;
8. explicit holdout invocation with milestone gating;
9. proof that routine preparation never opened the holdout;
10. fingerprint change and mismatch failure cases;
11. dummy withdrawal and deletion; and
12. invalidation of affected aggregate results.

Afterward, restore real source files to their empty/nonexistent state and verify no dummy private artifact remains.

## Required tests

At minimum, automated tests cover:

- private-path ignore behavior;
- routine holdout non-access;
- absence of processed holdout output;
- direct in-memory holdout evaluation;
- required milestone and checkpoint arguments;
- manifest and rubric validation;
- every fingerprint algorithm and failure case;
- result-schema serialization;
- approved output-root enforcement;
- correct initial `null` scoring state;
- strict aggregate calculation;
- withdrawal invalidation;
- prompt fixture equality across repositories; and
- all existing repository tests and regression guards.

## Suggested commit boundaries

Keep reviewable concerns separate:

1. approved documentation, PDR status, punctuation fix, and `aislop` cleanup;
2. private ignore paths and tests;
3. holdout least-privilege refactor;
4. fingerprint and private-manifest utilities;
5. structured logging and scoring scaffold;
6. dummy end-to-end tests;
7. model-side prompt-contract change, held until the paired app change is ready.

Do not combine real data, training, curriculum, or release changes into these commits.

## Engineering review packet

Claude's handoff for joint readiness review must include:

- file and commit inventory;
- full PDR-005 status and approval text;
- `aislop` results and any documented exception;
- unit and integration test commands/results;
- `git check-ignore` and clean-status evidence;
- static and dynamic proof of routine holdout non-access;
- sample dummy validation and holdout result schemas with content redacted or plainly synthetic;
- fingerprint determinism and failure-case evidence;
- withdrawal-drill evidence;
- cross-repository prompt status, commit IDs, contract version, and fixture hash;
- explicit confirmation that no real notes were collected; and
- Claude's evidence-alignment and action-alignment status.

## Joint readiness decision

ChatGPT reviews the engineering packet against PDR-005 and this handoff. Claude Code and ChatGPT each report:

- evidence alignment;
- implementation alignment;
- any remaining collection blockers; and
- recommendation on whether the validation-only pilot may begin.

Johnny decides only if alignment remains unresolved. Product-owner approval of PDR-005 does not bypass the second readiness review.

## Release and data status

- `checkpoint-520` remains production.
- `checkpoint-600` remains the candidate/comparison baseline.
- Gold v1.2.3 remains rejected and unchanged.
- Real validation remains empty until the second readiness review authorizes the pilot.
- The sealed holdout remains empty throughout the pilot.
- No outside-contributor collection is authorized.
