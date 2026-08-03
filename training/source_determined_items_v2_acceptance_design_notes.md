# Source-Determined Items v2 — Acceptance Draft Design Notes

**Date:** 2026-08-02  
**Artifact:** `source_determined_items_v2_acceptance_draft.jsonl`  
**Status:** ChatGPT draft for Claude schema/runner review; not frozen  
**Compute authorized:** none

## Purpose

This set replaces neither the protected 16-probe benchmark nor the historical five-case `source_determined_bullets` acceptance set. It is a new gate for a future typed-item-marker candidate.

The old five cases remain immutable evidence for the failed `source-determined-bullets-v1` study. Editing them would damage that study’s provenance.

## Design rules

- Ten dummy cases cover distinct capability families rather than patching individual seed-17 outputs.
- Inputs use new nouns, surface structures, and phrasing rather than protected benchmark wording or skeletons.
- Every case declares both `bullet_count_rule` and `action_count_rule`, including explicit zero.
- Count rules are computed automatically from parsed `###BULLET###` and `###ACTION###` markers.
- Count checks do not appear in `primary_checks`; they are structural, not human judgments.
- Semantic dimensions remain strict: every required dimension must be scored exactly 2.
- Every declared capability check must be a literal `true`.
- A case passes only when structural parsing, counts, semantic dimensions, and capability checks all pass. There is no partial aggregate credit.
- Status remains `acceptance_gate`; none of these cases has a prior passing baseline.

## Coverage map

| ID | Structural target | Semantic target |
|---|---|---|
| sdi2-01 | 1 bullet, 0 actions | Observation remains an observation |
| sdi2-02 | 1 bullet, 1 action | Deadline and destination survive |
| sdi2-03 | 2 bullets, 0 actions | Unrelated observations stay separate |
| sdi2-04 | 2 bullets, 1 action | Observation does not become an action |
| sdi2-05 | 1 bullet, 0 actions | Tentative idea stays tentative |
| sdi2-06 | 2 bullets, 0 actions | Both alternatives and unresolved status survive; later observation is not an answer |
| sdi2-07 | 1 bullet, 1 action | Restated task is deduplicated with deadline intact |
| sdi2-08 | At most 7 bullets, exactly 8 actions | Eight tasks survive without merge or invention |
| sdi2-09 | 1 bullet, 1 action | Dangling references remain unresolved and output stops cleanly |
| sdi2-10 | 6 bullets, 2 actions | Dense attribution, uncertainty, tentativeness, qualifiers, and task boundaries |

## Structural scoring contract

The future runner should compute and store at least:

- `parse_valid`;
- required section-marker presence and order;
- no text before `###NARRATIVE###`;
- parsed narrative, bullets, and actions;
- literal bullet/action counts;
- bullet/action count-rule results;
- no empty parsed items;
- no typed-marker cross-section leakage;
- parser/contract version and fingerprint.

Unknown count operators, missing rules, duplicate case IDs, parser-version mismatches, or prompt-contract fingerprint mismatches must stop before model loading.

## Semantic rubric

All cases require:

- `topic_completeness`;
- `unsupported_addition_resistance`.

Cases add:

- `uncertainty_preservation` when alternatives, tentative language, questions, or unresolved references are central;
- `attribution_accuracy` when roles and sources must stay distinct.

Capability checks are case-specific binary claims. Their labels are intentionally semantic; the runner must not prefill them from count results.

## Layer separation

Marker escaping, tokenizer round trips, malformed-output rejection, parser parity, and marker-like literal source text belong to Layer 0 static fixtures. They should not be mixed into generated semantic acceptance cases.

The ten JSONL cases begin at generated structural conformance and continue into semantic scoring. This keeps a parser defect from being confused with an intent-recovery defect.

## Review questions for Claude

1. Can the current result scaffold carry both required count rules without reusing human `capability_checks`?
2. Can count-rule evaluation be computed immediately after parsing and stored immutably in each result?
3. Will all ten records validate under a dedicated v2 acceptance schema without weakening the protected benchmark schema?
4. Are `exact` and `max` sufficient operators for this release?
5. Can a current runner inject the candidate prompt/parser while retaining current scoring-safety code?
6. Does full-target tokenization leave safe generation headroom for sdi2-08 and sdi2-10?

Claude should flag any disagreement or ambiguity rather than silently adapting the prose. ChatGPT will revise the cases only after that review.
