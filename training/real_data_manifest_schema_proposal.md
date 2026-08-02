# Canonical Consent/Provenance Manifest Schema — Proposal for ChatGPT's Reconciliation

Submitted as input to the schema-reconciliation step in the agreed ownership
split (ChatGPT: define the canonical schema; Claude: implement the validator
against it once agreed). Not a unilateral resolution — a concrete starting
point so the round-trip doesn't start from a blank page.

## The ambiguity, precisely

`datasets/REAL_DATA_GOVERNANCE.md` describes what should be one manifest
entry in two places with two different field sets:

**"Consent record" table** (the fields required at the moment consent is
recorded):
`record_id`, `contributor_id`, `consent_version`, `consented_at_utc`,
`author_confirmed`, `private_annotation`, `private_evaluation`,
`holdout_eligible`, `training_allowed`, `publication_allowed`,
`withdrawal_status`, `reviewer`.

**"Private provenance manifest" JSON example** (the fields shown on the
full, ongoing record):
`record_id`, `contributor_id`, `split`, `status`, `consent_version`,
`consented_at_utc`, `allowed_uses` (nesting `private_annotation`,
`private_evaluation`, `holdout_eligible`, `training`, `publication`),
`source_kind`, `source_fingerprint`, `pair_fingerprint`,
`rubric_fingerprint`, `deidentification_status`, `deidentified_at_utc`,
`deidentification_reviewer`, `annotation_status`, `withdrawal_status`.

`author_confirmed` and `reviewer` exist only in the table.
`split`, `status`, `source_kind`, fingerprints, de-identification fields,
and `annotation_status` exist only in the JSON example.

## Proposed reconciliation

The two sections are describing the **same record at different points in
its life**, not two different schemas: the table is the fields known at
the consent-recording moment (before de-identification/annotation/
assignment happen); the JSON is the full record after the record has
progressed further. The fix is one canonical schema that is the union of
both, not a choice between them:

```json
{
  "record_id": "rv_<random-id>",
  "contributor_id": "contributor_<random-id>",
  "split": "real_validation",
  "status": "active",
  "consent_version": "real-consent-v1",
  "consented_at_utc": "<timestamp>",
  "author_confirmed": true,
  "consent_reviewer": "<person who verified the consent record>",
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
  "deidentification_reviewer": "<person who verified de-identification>",
  "annotation_status": "adjudicated",
  "withdrawal_status": "active"
}
```

Changes from the JSON example currently in the doc:

1. **Added `author_confirmed`** (boolean) — from the consent table, absent
   from the JSON example. Non-negotiable per governance: "the contributor
   must be the note's author."
2. **Added `consent_reviewer`** — the table's generic `reviewer` field,
   renamed to disambiguate from `deidentification_reviewer` (two different
   review steps, two different reviewers, should never share a bare
   `reviewer` key).
3. **Training/publication field names**: the table calls them
   `training_allowed`/`publication_allowed`; the JSON's `allowed_uses`
   calls them `training`/`publication`. Recommend keeping the shorter
   `allowed_uses.training`/`allowed_uses.publication` (matches the nesting
   already used for the other three permission booleans) and updating the
   table to use the same names, rather than the reverse.
4. Everything else is unchanged from the existing JSON example.

## Validation rules the schema should make explicit

For the validator I'll build once this is agreed:

- `record_id`: required, unique across the manifest (reject duplicates —
  currently silently last-write-wins).
- `source_fingerprint`: required, unique across active (non-withdrawn)
  entries (reject duplicate/ambiguous source fingerprints — currently
  silently collapses).
- Every fingerprint field: must match `^sha256:[0-9a-f]{64}$` (reject
  malformed or missing prefix).
- `split`: must be exactly `"real_validation"` or `"real_holdout"`.
- `author_confirmed`: must be `true` (not merely present) for an entry to
  be usable.
- `allowed_uses.holdout_eligible`: must be `true` for holdout linking;
  `allowed_uses.training`/`allowed_uses.publication`: must always be
  `false` — no valid manifest should ever have these `true`, and the
  validator should reject an entry that has either set.
- `deidentification_status`: must be `"approved"` for an entry to be
  usable in any evaluation.
- `withdrawal_status`: must be `"active"` for an entry to be usable;
  `"withdrawn"`/`"expired"` are valid states but block use.
- Every string enum field (`status`, `deidentification_status`,
  `annotation_status`, `withdrawal_status`) validated against its
  documented allowed values, not accepted as any string.

## What I'm not deciding here

Whether `consent_reviewer` and `deidentification_reviewer` may be the same
person, exact timestamp formats, and any additional fields ChatGPT wants
for the annotation/adjudication workflow are left open — this proposal is
scoped to resolving the specific table-vs-JSON contradiction, not
redesigning the schema beyond that.
