# Auxiliary span validation selection protocol

**Date:** 2026-08-14  
**Author:** ChatGPT  
**Status:** Portability correction frozen after one clean fail-closed attempt; expanded synthetic self-test passed; corrected real selection not executed; awaiting independent Claude re-review  
**Governing guide:** `training/controlled_seed17_aux_span_annotation_guide_r2_chatgpt.md`  

## 1. Scope and authority

This package freezes the model-free method for selecting the revision-2 guide's fresh sanity set. It
implements the user's authorization to prepare the bounded validation selection package while preserving a
review-before-selection boundary: the selector has not been run against the real comparator corpus.

This document and the selector do not authorize annotation, opening either reviewer's prior pass, tokenizer
or model use, Gemini setup or generation, implementation, training, evaluation, checkpoint operations,
staging, commit, or push. The first real selector run is separately gated on independent verification of
this frozen method. The resulting manifest freezes records only; beginning annotation remains a later step.

## 2. Why the method is frozen before the draw

The guide requires 3-5 previously unannotated records selected by a predeclared mechanical/stress-coverage
protocol. Editing thresholds, heuristics, exclusions, scoring, or tie-breaking after seeing which records
they choose would convert the process into outcome-guided sampling. Therefore the sequence is:

1. freeze this protocol and its selector;
2. run only synthetic verification;
3. obtain Claude's independent review;
4. if and only if there is agreement, execute the corrected real selector once;
5. preserve its manifest without replacement or discretionary swapping.

If the frozen selector stops because no eligible record covers a required feature, that is a real stop. It
must not be fixed by weakening leakage rules or hand-picking an alternative after inspecting candidates.

## 3. Pinned governing artifacts

Dataset hashes are canonical-LF SHA-256 values. The selector accepts only a uniformly LF or uniformly CRLF
checkout, converts uniform CRLF to LF in memory, and fails closed before parsing if the canonical content pin
differs. Guide, static-audit, and selector hashes are raw-file SHA-256 values.

| Artifact | Records | SHA-256 |
|---|---:|---|
| `training/gold_v1.2.2_phase2_derived_candidate.jsonl` | 78 | `6e9e5f1bea8fc3cbcb615376a1d055bd273605d0f8c1e40a8c120720c8cb836c` |
| `datasets/benchmark/gold_v1.2.1_probes.jsonl` | 16 | `767fe21a1097b51cef38728dcff0ff9ca4cf280bde8e65a7d885729f40990c0f` |
| `datasets/benchmark/source_determined_items_v2_acceptance_draft.jsonl` | 10 | `b8fe4d4178e5b508757db998eacb1ee979518697c8df759ba1739227c88d448e` |
| `training/regression_balanced_repair_proposal.jsonl` | 7 | `192372fd44fc87ea879d2ab7b751a3d54be100b447b886c213b26553284a747a` |
| `training/controlled_seed17_aux_span_annotation_guide_r2_chatgpt.md` | - | `d652cc02958e8575f24d20ab0ecc674f5ce7887f55fd0d8403d58d913dcd0923` |
| `training/build_rbr17c_static_audit_map.py` | - | `aee75d7ecd8db680056c8a8e9f11e9ff5cfb52a285fdb2d319d1ca2c6ea6cfca` |
| `training/select_aux_span_validation_records.py` | - | `e79d889dd9ab0c5ccc6e8e62be52625fd724786aea3a6095aea368870f88823b` |

The JSONL reader additionally requires UTF-8 without BOM, uniform LF or uniform CRLF line endings, a terminal
newline, no blank records, exact record count, object-valued rows, and no duplicate JSON keys. Mixed endings,
bare CR, missing terminal newline, and post-normalization content drift are fatal. This matches the project's
existing `canonical_sha()` precedent rather than making checkout materialization part of content identity.

## 4. Fixed population and exclusions

The validation set consists of:

- the same ten regression records: `007, 040, 042, 048, 053, 054, 056, 069, 074, 075`; and
- exactly four fresh comparator records, one assigned to each required stress feature.

The fresh candidate population starts with comparator line/record IDs 1-78 and excludes:

1. all ten regression IDs;
2. all comparator IDs already identified by the static audit as protected/acceptance analogues:
   `042, 048, 053, 054, 056, 061, 069, 070, 074, 075, 076`;
3. any record crossing any collision rule against any Protected-16, Acceptance-10, or failed seven-record
   treatment-delta input; and
4. during selection, any record crossing the same rule against a fresh record already selected.

The static analogue exclusion is intentionally broader than text similarity. It preserves the earlier
human-audited structural findings even where a lexical screen alone would pass.

## 5. Frozen leakage screen

The normalization and numeric thresholds reuse the project's previously ratified rules:

- Unicode NFKC;
- lowercase;
- replace everything outside `[a-z0-9 ]` with spaces;
- collapse whitespace;
- normalized exact equality: exclude;
- normalized containment where the shorter normalized string is at least 20 characters: exclude;
- token-set Jaccard at or above `0.15`: exclude;
- character-5-gram Jaccard at or above `0.10`: exclude.

Earlier packages treated the two Jaccard thresholds as review flags. Here they are conservatively fatal
because the selected records will be validation evidence, not training candidates. No waiver or manual
adjudication tier exists in this draw.

## 6. Mechanical stress features

These are sampling heuristics, not annotations or claims that a record's eventual gold labels are known.
They may inspect only the committed raw source and committed target, never reviewer outputs or adjudication.

### 6.1 Unfielded independent content

Split the source on terminal punctuation, semicolons, newlines, and spaced dash boundaries. Ignore segments
with fewer than two non-stopword content tokens. A segment is a stress hit when its maximum content-token
Jaccard against any committed narrative, bullet, or action string is below `0.20`. Its score is the number
of such segments.

This identifies plausible source content with little target realization. It does not pre-decide that the
segment must receive empty field obligations; the reviewers decide that under the guide.

### 6.2 Implicit-actor task

A record is a hit when all three mechanical conditions hold:

- at least one frozen task cue is present;
- the committed target has at least one action item; and
- the frozen explicit-actor pattern does not match.

Its score is task-cue count plus committed-action count. This is a stress heuristic only; mandatory actor
annotation remains governed by Section 6 of the guide.

### 6.3 Referential expression

A record is a hit when the source contains a frozen pronoun, demonstrative, anaphoric alternative, or named
phrase such as `earlier version`. Its score is the number of matches. Resolution status remains entirely
unlabeled until independent annotation.

### 6.4 Qualifier precedence

A record is a hit when the source matches one or more frozen cue families: deadline, trigger, condition,
time, quantity, destination, purpose, or object modifier. Its score is the number of distinct cue families,
not the number of labels a reviewer must assign.

All exact regular expressions and stopwords are reviewable in the pinned selector; this prose is not an
independent second implementation.

## 7. Deterministic selection

Features are assigned in this fixed order:

1. unfielded independent content;
2. implicit-actor task;
3. referential expression;
4. qualifier precedence.

For each feature, choose one unused, leakage-clean candidate with a positive score. Sort candidates by:

1. assigned-feature score descending;
2. unused category before an already represented category;
3. maximum token Jaccard ascending;
4. maximum character-5-gram Jaccard ascending; and
5. comparator record ID ascending.

Before accepting each later record, apply the same collision screen against every already selected fresh
record. A record may exercise multiple features, but every required feature receives a distinct assigned
record, producing exactly four fresh records. Failure to fill all four positions stops the run.

## 8. Frozen manifest

The one corrected retry writes only
`training/controlled_seed17_aux_span_validation_manifest.json` and refuses to overwrite an existing file.
The manifest contains:

- every governing canonical input pin and frozen rule;
- each input's actual checkout line-ending style and raw checkout-byte SHA-256;
- an execution-history entry preserving the first clean preflight failure and distinguishing it from the
  first successful manifest generation;
- the exact source and committed target for all ten regression and four fresh records;
- a canonical per-record hash;
- feature scores/evidence and leakage maxima for each fresh record;
- the full mechanical exclusion audit;
- a combined validation-set fingerprint;
- a manifest payload fingerprint and raw-file hash receipt; and
- a `future_gemini_quarantine` list containing all fresh record locators.

The future Gemini generator-readiness package must load this quarantine list and fail closed if any listed
source is supplied in a prompt, candidate context, worked example, or evaluation-derived feedback. Merely
storing the manifest in the repository is not permission to expose it to Gemini.

## 9. Failed first attempt and corrected verification

The first authorized real attempt on 2026-08-14 stopped before parsing or selection because the original
reader required LF-only working-tree bytes. The comparator and Protected-16 hashes matched their original
pins, but this Windows checkout materialized those two Git-LF blobs as uniform CRLF under
`core.autocrlf=true`. Acceptance-10 and treatment-delta were LF-only. No manifest was written and no
repository file changed. That stop is preserved here as historical evidence; it is not relabeled as a
successful selection and does not consume or justify a discretionary record swap.

The corrected reader uses the repository's established canonical-LF identity rule while recording both the
checkout byte hash and canonical content hash. It does not normalize any semantic content or write back to
the datasets.

The expanded synthetic-only self-test passed using the bundled project runtime. It exercised identical LF
and CRLF acceptance, and rejection of mixed endings, bare CR, BOM, missing terminal newline, and
post-canonicalization content drift. It also exercised collision normalization, token and character
similarity, exact-collision rejection, and all four feature detectors, while the self-test entry point did
not open repository datasets. Python bytecode compilation also passed.

No corrected real selection was executed, no output manifest exists, and no fresh record was chosen by this
package.
During implementation, ChatGPT did open comparator row 001 to confirm the JSON field shape and computed an
aggregate category-frequency inventory to confirm that the category tie-break was structurally available.
That limited inspection exposed row 001's source/target and category names/counts, but no candidate feature
scores, leakage results, rankings, or selected IDs were computed or viewed. It is disclosed here rather than
being misdescribed as a no-inspection design. The frozen-before-annotation and review-before-real-selection
requirements remain intact.

## 10. Independent review checklist

Claude should independently verify:

- every pinned hash/count against primary sources;
- the canonical-LF pins reproduce from both LF and uniform-CRLF checkout forms;
- mixed endings, bare CR, BOM, missing terminal newline, and content drift remain fail-closed;
- the manifest records both checkout-byte and canonical-LF hashes;
- the real-data entry point cannot run accidentally and refuses overwrite;
- candidate exclusions include the regression set and every static protected analogue;
- Protected-16, Acceptance-10, and all seven failed treatment-delta inputs are screened;
- normalization and thresholds match the cited ratified precedent;
- making all threshold crossings fatal is proportionate for validation data;
- the four heuristics are mechanical, target-aware only where stated, and do not inspect reviewer output;
- deterministic ranking cannot silently substitute a hand-picked record;
- within-fresh-set collision screening and exact four-feature coverage fail closed;
- manifest hashing, exact record freezing, and Gemini quarantine are complete; and
- the synthetic self-test does not read real records.

Any material disagreement stops before the real run and returns to Johnny. Review agreement authorizes no
annotation, model/tokenizer use, Gemini activity, staging, commit, or push beyond the already authorized
one-time selection execution described in Section 2.
