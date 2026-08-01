# Real-Data Governance Specification

## Status

**Proposed, revision 2, for joint review. No real-note collection is authorized by this draft.**

This specification governs private real notes used to evaluate the Intent Recovery Model. It does not govern synthetic or gold curriculum examples.

## Purpose

Real notes exist to answer one question: does a model trained on synthetic examples recover intent from real, naturally fragmented writing without adding burden or unsupported meaning?

They are not used to diagnose contributors, infer conditions, build contributor profiles, or train the model. They are never published with the repository.

## Non-negotiable boundaries

- Real notes are evaluation-only and never enter training.
- `real_validation.jsonl` may support routine development after the pilot is approved.
- `real_holdout.jsonl` remains sealed for declared release milestones.
- No real note is collected before consent, provenance, de-identification, storage, and withdrawal mechanisms are operational.
- No diagnosis or clinical label is requested, recorded, inferred, or used for balancing.
- No note written by a third party, copied conversation, email, therapy record, school record, workplace record, or other document is accepted merely because the contributor possesses it.
- The contributor must be the note's author and must have authority to permit its use.
- Model outputs, annotations, rubrics, and evaluation logs are private because they may repeat sensitive details from the note.

## Pilot scope

The first pilot is validation-only:

- at most eight de-identified records;
- contributed by the project owner from notes they personally authored and deliberately selected;
- no sealed-holdout population;
- no outside-contributor collection;
- no claim of representativeness or statistical adequacy;
- no curriculum or release decision until the pilot records are strictly scored.

The cap limits privacy exposure while testing the workflow. It is not a minimum and may be reduced.

Outside contributors, group recruitment, contributor minors, and collection through therapists, teachers, employers, or institutions require a separate approved process and remain out of scope.

## Permitted uses

Each active record may be used only for the permissions explicitly recorded in its consent entry:

- private annotation;
- private real-validation evaluation;
- private human review of generated outputs; and
- if separately authorized, future sealed-holdout evaluation.

The following uses are prohibited by default:

- model training or fine-tuning;
- publication of the note, expected output, generated output, or rubric;
- public benchmark inclusion;
- sharing outside the approved project review path;
- contributor classification or diagnosis;
- commercial reuse unrelated to this project; and
- using a holdout record to author curriculum or tune a checkpoint.

Consent for validation does not imply consent for sealed-holdout use. Holdout eligibility must be explicit and recorded before assignment.

## Consent record

Consent is recorded in a private, gitignored manifest before the note is processed. A consent entry must include:

| Field | Requirement |
|---|---|
| `record_id` | Random, non-semantic stable identifier |
| `contributor_id` | Private pseudonymous contributor identifier |
| `consent_version` | Version of the approved consent language |
| `consented_at_utc` | Timestamp |
| `author_confirmed` | Contributor confirms they wrote the note |
| `private_annotation` | Explicit boolean |
| `private_evaluation` | Explicit boolean |
| `holdout_eligible` | Separate explicit boolean; false during pilot |
| `training_allowed` | Must be false |
| `publication_allowed` | Must be false |
| `withdrawal_status` | `active`, `withdrawn`, or `expired` |
| `reviewer` | Person who verified the record |

Silence, prior participation, general project enthusiasm, or delivery of a note without the approved consent record does not count as consent.

This specification is a project safeguard, not a substitute for legal or institutional review. Any broader recruitment or research-like use requires separate review before it begins.

## Private provenance manifest

Provenance lives outside the model-facing `input`/`output` pair in a private, gitignored manifest. The manifest must not contain the raw original note.

Each record contains:

```json
{
  "record_id": "rv_<random-id>",
  "contributor_id": "contributor_<random-id>",
  "split": "real_validation",
  "status": "active",
  "consent_version": "real-consent-v1",
  "consented_at_utc": "<timestamp>",
  "allowed_uses": {
    "private_annotation": true,
    "private_evaluation": true,
    "holdout_eligible": false,
    "training": false,
    "publication": false
  },
  "source_kind": "author_supplied_personal_note",
  "source_fingerprint": "sha256:<input-only-fingerprint>",
  "pair_fingerprint": "sha256:<input-output-fingerprint>",
  "rubric_fingerprint": "sha256:<private-rubric-fingerprint>",
  "deidentification_status": "approved",
  "deidentified_at_utc": "<timestamp>",
  "deidentification_reviewer": "<reviewer>",
  "annotation_status": "adjudicated",
  "withdrawal_status": "active"
}
```

The implementation may add fields, but it must preserve these semantics. `record_id` and private metadata must never appear in the prompt sent to the model.

Fingerprints are computed over canonical UTF-8 JSON. `source_fingerprint` covers the de-identified input; `pair_fingerprint` covers the de-identified input and approved expected output; `rubric_fingerprint` covers the adjudicated private rubric. An edit changes the relevant fingerprint and requires manifest review. The exact canonicalization and aggregate algorithms are defined in `training/REAL_DATA_EVALUATION_PROTOCOL.md`.

## Data minimization

Collect only the shortest source excerpt needed to preserve the fragmented note and its intent-recovery challenge. Remove surrounding journal material that is irrelevant to the selected example.

Do not collect:

- passwords, access tokens, security answers, or authentication details;
- financial account or payment information;
- exact home, school, workplace, or travel-location identifiers;
- personal contact information;
- official identification numbers;
- private records belonging to another person;
- highly sensitive medical, legal, intimate, or crisis-related content;
- detailed allegations or information whose retention could create material risk; or
- content that cannot be safely de-identified without changing the recovery problem.

If safe de-identification would destroy the attribution, uncertainty, chronology, or intent structure being evaluated, reject the note rather than weaken privacy.

## De-identification rules

De-identification happens before annotation, split assignment, or model evaluation.

Remove or consistently replace:

- names and usernames;
- phone numbers, email addresses, URLs, and account identifiers;
- precise dates when they are not essential temporal qualifiers;
- exact addresses and uniquely identifying locations;
- employer, school, clinician, institution, or organization names;
- unique project, product, case, or event names;
- third-party identifying details; and
- unusual combinations of facts that could reasonably re-identify someone.

Use consistent neutral substitutions within a record. Preserve roles only when they are necessary to the intent structure. Do not add demographic, diagnostic, or emotional descriptions during substitution.

The de-identified record receives a second-person review. The reviewer checks both privacy and meaning preservation. A record fails review if either is uncertain.

The raw original should be deleted after the contributor approves the de-identified source unless a separately approved private retention policy exists. The repository never stores the original.

## Sensitive-content review

Every candidate record receives a content-safety decision:

- `accept` — safe after de-identification;
- `revise` — a narrow, meaning-preserving transformation can remove risk; or
- `reject` — privacy or sensitivity cannot be reduced without changing the example.

When uncertain, reject. Dataset coverage never outweighs contributor or third-party privacy.

## Storage and access

- Private provenance and consent manifest: `datasets/private/real_data_manifest.jsonl`.
- Private rubric sidecar: `datasets/private/real_data_rubrics.jsonl`.
- Private validation results: `training/results/private/real_validation/`.
- Private holdout results: `training/results/private/real_holdout/`.
- Real-data source files, manifests, rubrics, outputs, and evaluation logs are gitignored.
- They are not placed in issue trackers, pull requests, commits, public build artifacts, chat excerpts, screenshots, or test fixtures.
- Access is limited to the minimum people and tools needed for the declared task.
- Dummy synthetic records are used for implementation tests.
- Backups, if used, follow the same private access and deletion rules.
- File names and record IDs must not encode contributor identity or note content.

Before any private file is created, ignore rules must cover at least:

```gitignore
datasets/real_validation.jsonl
datasets/real_holdout.jsonl
datasets/private/
training/results/private/
training/data/processed/real_validation.jsonl
training/data/processed/real_holdout_eval.jsonl
```

The final line is retained defensively even after routine holdout materialization is removed. Implementation tests must use `git check-ignore` on every private path and verify that `git status --porcelain` never lists a private artifact.

## Withdrawal and deletion

A contributor may withdraw an active record. Withdrawal requires:

1. removing the record from the source split;
2. removing its rubric and active manifest entry or marking it withdrawn without retaining sensitive content;
3. deleting private generated outputs and evaluation artifacts derived from that record when feasible;
4. regenerating dataset fingerprints;
5. marking affected aggregate evaluations invalid or superseded; and
6. documenting the deletion without quoting the note.

If a sealed holdout record is withdrawn, the seal is broken. The affected holdout version is retired and must be resealed before any milestone evaluation.

## Audit gates

Collection may begin only after all of these are true:

- governance package jointly approved;
- private manifest mechanism implemented and tested with dummy records;
- private storage paths and ignore rules verified;
- de-identification checklist implemented;
- withdrawal drill completed with dummy records;
- training and production prompt contracts synchronized and verified across repositories;
- structured evaluation logging implemented;
- strict semantic-scoring scaffold implemented; and
- alignment status recorded as `Aligned` by Claude Code and ChatGPT.

## Alignment status

**ChatGPT revision 2 for Claude verification.**
