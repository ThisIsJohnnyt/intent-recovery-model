# Compact typed-representation feasibility pilot decision

**Date:** 2026-08-13  
**Status:** FAIL under the frozen 512/300 limits; stop this compact representation family  
**Scope:** Frozen comparator records 007, 040, 042, 048, 053, 054, 056, 069, 074, 075  
**Model/benchmark execution:** None; pinned tokenizer only  

## Decision

The compact representation fits the 512-token prompt and training-target limits but fails the 300-token
generation limit on four of ten frozen stress records. Six records exceed the preferred 270-token safety
target. Under the predeclared decision rule, stop this representation family before all-78 authoring.

## Measured result

| Record | Prompt | Rendered v2 alone | Compact-plan overhead | Complete target | <=300 | <=270 |
|---|---:|---:|---:|---:|---|---|
| comparator:007 | 429 | 244 | 58 | 302 | no | no |
| comparator:040 | 426 | 212 | 103 | 315 | no | no |
| comparator:042 | 391 | 132 | 71 | 203 | yes | yes |
| comparator:048 | 403 | 140 | 120 | 260 | yes | yes |
| comparator:053 | 411 | 179 | 92 | 271 | yes | no |
| comparator:054 | 414 | 188 | 107 | 295 | yes | no |
| comparator:056 | 366 | 82 | 34 | 116 | yes | yes |
| comparator:069 | 378 | 71 | 34 | 105 | yes | yes |
| comparator:074 | 405 | 267 | 122 | 389 | no | no |
| comparator:075 | 422 | 246 | 155 | 401 | no | no |

Aggregate: prompt min/median/max 366/411/429; target 105/295/401; zero prompts over 512; zero targets
over 512; four targets over 300; six over 270.

## What the pilot established

The plan removes duplicated natural-language predicates by pointing to exact bullet/action spans in the
unchanged v2 suffix. It encodes proposition state, predicate/field references, roles, qualifiers,
coreference, and duplicate links. Its fail-closed parser requires ordered IDs, valid references, one-to-one
action coverage, legal state/action combinations, backward-only duplicate links, known role/qualifier
codes, a valid unchanged v2 suffix, and no generative repair.

All ten authored artifacts round-trip structurally, cover every rendered action exactly once, and preserve
the existing v2 suffix byte-for-byte. Ten negative parser tests pass. These are ChatGPT-authored pilot
annotations pending Claude's independent semantic review; they are not approved training data.

## Why another micro-compression pass is not justified here

Comparator:074's unchanged rendered v2 answer alone is 267 tokens. The 300-token ceiling leaves 33 tokens
for a plan representing eight distinct tasks, seven bullet links, eight action links, and the unmatched
bullet/action identity. The current compact plan overhead is 122 tokens. Comparator:075 leaves only 54
tokens for six propositions with state, two shared-trigger tasks, a question, an idea, roles, and
qualifiers; current overhead is 155.

The gap is structural, not a few removable marker tokens. Further shortening under this authorization would
either drop required distinctions, change the representation materially after measurement, or design
against the observed cases. The predeclared rule says to stop rather than iterate around a failed hard case.

## Artifacts

- `compact_typed_plan.py`
- `prepare_compact_typed_representation_pilot.py`
- `test_compact_typed_plan.py`
- `measure_compact_typed_representation_pilot.py`
- `controlled_seed17_compact_typed_representation_pilot.jsonl`
- `controlled_seed17_compact_typed_representation_pilot_receipt.json`
- `controlled_seed17_compact_typed_representation_token_receipt.json`
- this decision memo

## Next decision

Do not author the remaining 68 records. Do not run a model or benchmark. The next technically coherent path
is a new proposal whose sole primary variable is the generation/target token budget, using this compact
representation as fixed evidence; alternatively stop the typed-plan approach entirely. A materially
different representation that does not emit the plan at inference would change the training/evaluation
architecture and also requires its own proposal.

No path is authorized by this decision memo. No corpus, benchmark, checkpoint, seed, or committed artifact
was changed.

## Independent-review correction

Claude's independent review found one annotation error that did not affect length or disposition:
comparator:007 proposition 3, “Set app color palette to orange and purple,” is a settled `F` fact rather
than an `I` tentative idea. The pilot source and receipts were regenerated with that one-character state
correction. All token counts are unchanged; artifact hashes change as expected.
