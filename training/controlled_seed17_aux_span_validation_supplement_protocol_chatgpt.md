# Auxiliary span validation supplemental fresh-record protocol

**Date:** 2026-08-14  
**Author:** ChatGPT  
**Status:** Frozen proposal; synthetic self-test passed; no real supplemental draw executed; awaiting Claude review  

## 1. Decision and boundary

Johnny chose the disagreement record's recommended Option 1: preserve the initial 14-record run and add
exactly one fifth fresh record through a newly predeclared selection method. The existing selector, manifest,
sealed annotations, receipts, and disagreement record remain unchanged.

This protocol authorizes a method only. The real draw waits for independent review. A successful draw freezes
one record but does not authorize semantic annotation, guide revision, a correction rerun, model/tokenizer
use, Gemini activity, staging, commit, or push.

## 2. Why this is not repeated outcome tuning

The original low-overlap heuristic honestly selected comparator 012, but both sealed passes assigned every
one of its propositions at least one target field. This supplement does not lower thresholds, manually pick a
record, or repeatedly draw until a desired label appears. It declares one materially stronger omission
signature, one deterministic ranking, and one draw before any remaining candidate is scored or inspected.

If no candidate satisfies the frozen signature, the selector stops. If the chosen fifth record later receives
no agreed empty-field proposition, the fresh-coverage requirement fails and the project returns to Johnny.
There is no sixth record under this design because the guide permits at most five fresh records.

## 3. Pinned evidence

| Artifact | SHA-256 |
|---|---|
| `training/select_aux_span_validation_records.py` | `e79d889dd9ab0c5ccc6e8e62be52625fd724786aea3a6095aea368870f88823b` |
| `training/controlled_seed17_aux_span_validation_manifest.json` | `6314b4336e0fac4a52735f0072ce82a2d5ba44f65a90ef536628a7d34d70dcb5` |
| `training/controlled_seed17_aux_span_validation_disagreement_record.md` | `cd4bc970eaa165f82785e5e5d3bf464a9cef415d877d8004c2c002bd2c17547f` |
| ChatGPT sealed pass | `55e688425a0e2cd5c409af58e4403ce117d8fe373014a4fed223e3805ce86e37` |
| Claude sealed pass | `d7b1d73f14406b4b81da9327f26a79ea8fd6e8c32fa92fcdc27e5c5b57dc6943` |
| `training/select_aux_span_validation_supplement.py` | `95b8522eb1af40ce8b7e702a2b59a594c958ccac10c99ea87d17116574016688` |

The supplement imports the exact pinned original selector so canonical-LF input identity, JSON validation,
collision normalization, thresholds, source parsing, target extraction, and static protected-analogue
exclusions cannot silently drift into a second implementation.

## 4. Candidate population and exclusions

Start from the same pinned 78-record comparator corpus. Exclude:

1. all 14 records in the frozen initial validation manifest;
2. every comparator ID in the static protected-analogue register;
3. any record crossing exact, containment, token-Jaccard, or character-5-gram thresholds against
   Protected-16, Acceptance-10, or the failed treatment-delta records; and
4. any record crossing the same thresholds against any of the existing 14 validation records.

The collision thresholds remain exact/containment fatal, token Jaccard `>=0.15` fatal, and character-5-gram
Jaccard `>=0.10` fatal. No waiver tier exists.

## 5. Strong omission signature

Split source text using the original selector's frozen clause splitter. Strip only surrounding whitespace,
commas, and colons. A segment is eligible only when all conditions hold:

1. it contains at least three non-stopword content tokens under the original selector's tokenization;
2. it contains at least one verb/state cue from the new selector's frozen regular expression; and
3. its content-token intersection with the union of the committed narrative, bullets, and action items is
   exactly empty.

This is stronger than the original maximum-Jaccard-below-`0.20` rule: not one content token may survive into
any committed target field. The predicate requirement reduces the chance of selecting a topic label that
lacks an independently classifiable state.

It remains a selection heuristic, not a semantic annotation. Paraphrase can still produce zero lexical
overlap, so success is not claimed until both reviewers independently annotate the fifth record after the
guide correction. That residual risk is accepted as the reason this is a one-draw test rather than a
guarantee.

## 6. Deterministic rank and one draw

Rank all eligible candidates by:

1. qualifying omission-segment count descending;
2. longest qualifying segment's content-token count descending;
3. total qualifying content-token count descending;
4. category not already represented in the four-record fresh set first;
5. maximum token Jaccard ascending;
6. maximum character-5-gram Jaccard ascending; and
7. comparator record ID ascending.

Select exactly the first record. No reserve substitution, manual review tier, or second draw is permitted.

## 7. Supplemental manifest

The real entry point requires the literal `--execute-frozen-supplement` flag and refuses to overwrite
`training/controlled_seed17_aux_span_validation_supplement_manifest.json`.

The manifest records:

- all governing pins and checkout/canonical input receipts;
- the exact selected source and committed target plus canonical record hash;
- every qualifying omission signature and its content tokens/predicate cues;
- leakage maxima and full exclusion audit;
- a combined 15-record fingerprint; and
- a five-record future-Gemini quarantine list.

The fifth record remains unavailable to any future Gemini prompt, candidate context, example, or feedback.

## 8. Synthetic verification

The synthetic self-test passed without opening a corpus or manifest. It proves that:

- a predicate-bearing, three-content-token clause with zero target overlap is selected as a signature;
- an exactly represented clause is rejected; and
- a noun-only topic phrase without a frozen predicate cue is rejected.

Python bytecode compilation also passed. No real candidate was scored, ranked, or selected.

## 9. Claude review checklist

Claude should independently verify:

- every pin and the original selector import boundary;
- the candidate/exclusion population is complete;
- the stronger signature is predeclared, mechanical, and not annotation-by-proxy;
- predicate-cue coverage is adequate without becoming a semantic model;
- target comparison uses the complete committed narrative/bullet/action union;
- the rank is deterministic and cannot redraw;
- all old leakage and canonicalization protections remain active;
- the synthetic entry point cannot open real data;
- the output freezes exactly one fifth record and a combined quarantine; and
- failure behavior returns to Johnny rather than retuning.

Material disagreement stops before the draw. Agreement authorizes no annotation, guide correction,
staging, commit, push, model/tokenizer use, or Gemini activity.
