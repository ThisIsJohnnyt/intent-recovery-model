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

Consent is recorded in a private, gitignored manifest before the note is processed, under schema version `manifest_schema_version: "real-manifest-v1"` (see `training/real_data_manifest_schema_decision.md`, the canonical schema Claude implements against). Consent and provenance are not separate records -- one manifest entry accumulates consent, de-identification, annotation, split assignment, fingerprints, and withdrawal state over its lifecycle. At the moment consent is recorded, an entry must include:

| Field | Requirement |
|---|---|
| `manifest_schema_version` | Exact `real-manifest-v1` |
| `record_id` | Random, non-semantic stable identifier |
| `contributor_id` | Private pseudonymous contributor identifier |
| `consent_version` | Version of the approved consent language |
| `consented_at_utc` | UTC timestamp |
| `author_confirmed` | Must be literal `true`: contributor confirms they wrote the note |
| `consent_reviewer_id` | Pseudonymous actor who verified the consent record |
| `allowed_uses.private_annotation` | Explicit boolean |
| `allowed_uses.private_evaluation` | Explicit boolean |
| `allowed_uses.holdout_eligible` | Explicit boolean; must be `false` during the validation-only pilot |
| `allowed_uses.training` | Must always be `false` |
| `allowed_uses.publication` | Must always be `false` |
| `withdrawal_status` | `active`, `withdrawn`, or `expired`; one-way once `withdrawn`/`expired` |

`split` and all three fingerprints remain `null` at this stage; de-identification starts `pending` and annotation starts `not_started`, each with `null` timestamp/actor fields until that stage is reached.

Silence, prior participation, general project enthusiasm, or delivery of a note without the approved consent record does not count as consent.

This specification is a project safeguard, not a substitute for legal or institutional review. Any broader recruitment or research-like use requires separate review before it begins.

## Private provenance manifest

Provenance lives outside the model-facing `input`/`output` pair in a private, gitignored manifest. The manifest must not contain the raw original note.

An evaluation-ready record contains:

```json
{
  "manifest_schema_version": "real-manifest-v1",
  "record_id": "rv_<random-id>",
  "contributor_id": "contributor_<random-id>",
  "consent_version": "real-consent-v1",
  "consented_at_utc": "<timestamp>",
  "author_confirmed": true,
  "consent_reviewer_id": "actor_<random-id>",
  "allowed_uses": {
    "private_annotation": true,
    "private_evaluation": true,
    "holdout_eligible": false,
    "training": false,
    "publication": false
  },
  "source_kind": "author_supplied_personal_note",
  "split": "real_validation",
  "source_fingerprint": "sha256:<input-only-fingerprint>",
  "pair_fingerprint": "sha256:<input-output-fingerprint>",
  "rubric_fingerprint": "sha256:<private-rubric-fingerprint>",
  "deidentification_status": "approved",
  "deidentified_at_utc": "<timestamp>",
  "deidentified_by_id": "actor_<random-id>",
  "deidentification_reviewer_id": "actor_<random-id>",
  "annotation_status": "adjudicated",
  "adjudicated_at_utc": "<timestamp>",
  "annotation_author_id": "actor_<random-id>",
  "annotation_reviewer_id": "actor_<random-id>",
  "withdrawal_status": "active",
  "withdrawal_status_changed_at_utc": "<timestamp>"
}
```

There is no separate generic `status` field -- `withdrawal_status` alone carries the record's active/withdrawn/expired state, and the other status fields (`deidentification_status`, `annotation_status`, `split`) together describe lifecycle stage without redundancy. Unknown top-level fields are rejected under `real-manifest-v1`; adding a field requires a schema-version change, not silent extension. `record_id` and private metadata must never appear in the prompt sent to the model.

De-identification and annotation each record an independent author/reviewer pair (`deidentified_by_id` != `deidentification_reviewer_id`; `annotation_author_id` != `annotation_reviewer_id`) -- the approved consent-review step itself does not require the reviewer to be independent of the contributor.

`split` is assigned at most once and never changes between `real_validation` and `real_holdout` afterward. `withdrawal_status` moves from `active` to `withdrawn` or `expired` and never returns to `active`. After split assignment, an in-place edit to the de-identified source is rejected -- a separately governed replacement record is required instead.

Fingerprints are computed over canonical UTF-8 JSON. `source_fingerprint` covers the de-identified input; `pair_fingerprint` covers the de-identified input and approved expected output; `rubric_fingerprint` covers the adjudicated private rubric. An edit changes the relevant fingerprint and requires manifest review. A non-null `source_fingerprint` must be unique across the entire manifest, including withdrawn and expired rows -- a withdrawn source must not become reusable under a fresh `record_id`. The exact canonicalization and aggregate algorithms are defined in `training/REAL_DATA_EVALUATION_PROTOCOL.md`.

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
