# Ten-record aux-span dual-annotation pilot: comparison and disagreement record

**Date:** 2026-08-13
**Status:** Historical evidence record of the first pilot round. Preserves the round exactly as it occurred.
No piecemeal adjudication or silent harmonization was performed after the comparison was run.
**Compute performed:** None. Tokenizer/model were not invoked in either annotation pass or in this comparison.

## 1. Frozen inputs and receipts

- Frozen subset: comparator 007, 040, 042, 048, 053, 054, 056, 069, 074, 075 (10 records), fixed by
  `training/controlled_seed17_aux_span_annotation_guide.md`.
- Frozen comparator corpus: `training/gold_v1.2.2_phase2_derived_candidate.jsonl` (unmodified, pre-existing,
  committed `d90fc13`).

| Artifact | File | SHA-256 (independently recomputed from final bytes) |
|---|---|---|
| ChatGPT annotation pass | `training/controlled_seed17_aux_span_annotations_chatgpt.jsonl` | `ceddb5f2b9a174bd7a1f7636d065e26a19bceb74eca90a7f21a80de8a3f3908f` |
| ChatGPT token-offset map | `training/controlled_seed17_aux_span_token_offsets_chatgpt.jsonl` | `fea151217f041429a937b3de821a7dd8e51f409e3728719c8db77836fb0f7fb2` |
| Claude annotation pass (sealed before opening any ChatGPT file) | `training/controlled_seed17_aux_span_annotations_claude.jsonl` | `a9b7852e80caf98ad48bf786123758886cc0634aaf85566b1376bea7aafd3410` |

All three hashes above were recomputed directly from the files on disk as part of preparing this record, not
copied from either party's prior report.

Claude's pass was produced from the guide and the raw comparator source/targets only, and its hash was
reported to Johnny in-chat before any ChatGPT annotation artifact was opened. It is not fully blind at the
semantic-label layer: Claude had already reviewed and endorsed ChatGPT's compact-representation-pilot
state/role/qualifier/coreference labels for these same 10 records earlier the same day, before this guide
existed. The character-span layer under this guide's boundary rules was genuinely fresh. See
`training/controlled_seed17_aux_span_annotation_receipt_claude.json` for the full disclosure.

## 2. Agreement result

- ChatGPT: 47 propositions across 10 records (`controlled_seed17_aux_span_annotation_receipt.json`).
- Claude: 52 propositions across 10 records (`controlled_seed17_aux_span_annotation_receipt_claude.json`).
- 7/10 records matched exactly on proposition count and state sequence: comparator:042, 048, 053, 056, 069,
  074, 075.
- Within those 7 records, required output field obligations (`narrative`/`bullet`/`action`) matched on every
  single proposition -- no field-obligation disagreement anywhere in the matching set.
- comparator:069 (the duplicate-relation stress case, the rarest/most fragile mechanism at 1/108 positive
  pairs in ChatGPT's pass) matched cleanly on both propositions and the duplicate link in both passes.

## 3. Count disagreements

### comparator:007 -- Claude 7 propositions vs. ChatGPT 5

- Claude split "openweather cheaper" out as its own `fact` proposition (narrative-only field obligation, no
  bullet/action); ChatGPT folded it into the same `task` proposition as the API-decision clause
  ("weather.gov or openweather? openweather cheaper", one span, bullet+action obligations).
- Claude split "free tier azure? heroku?" out as its own `question` proposition (narrative-only); ChatGPT
  joined it via a discontinuous span into the same `task` proposition as "need to move backend to free tier
  for vacation testing" (bullet+action obligations, qualifiers destination+purpose).

### comparator:040 -- Claude 9 propositions vs. ChatGPT 7

- Same root pattern as 007: Claude split "still stressed about that" and the mail-piling-up clause as
  fact-only propositions adjacent to task propositions; ChatGPT's proposition boundaries differ correspondingly.
- Claude annotated "client call notes" as its own `fragment` proposition with zero field obligations (dropped
  from the target entirely). ChatGPT's pass has no entry for this clause at all.
- Claude annotated the trailing "plumber never called back." as a `duplicate_of`-linked restatement
  proposition of the earlier plumber clause. ChatGPT instead used a single discontinuous-span proposition
  joining the early and late plumber mentions into one `task` proposition with both bullet and action
  obligations -- no separate fact proposition and no duplicate link for this content.

### comparator:054 -- Claude 7 propositions vs. ChatGPT 6

- Claude annotated "access list question still open" as a `duplicate_of`-linked restatement of the earlier
  Chris/Dana access-list `question` proposition, with zero field obligations. ChatGPT's pass has no entry for
  this clause; its access-list question proposition instead uses a discontinuous span joining "did Chris ever
  send Dana the access list" and "access list question still open" into one proposition.

## 4. Other disagreements (within the 7 count-matching records)

### Coreference (3 instances)

- comparator:048 proposition 1: Claude `none`, ChatGPT `resolved`. Scope-dependent -- ChatGPT's proposition 1
  spans the wider clause "Rina told Marcus the draft was approved after he asked about it" (through the first
  "he"), so its coreference marking follows from a different proposition-boundary choice than Claude's
  narrower split.
- comparator:048 proposition 4 ("Ask Rina who needs it"): Claude `none`, ChatGPT `unresolved`.
- comparator:075 proposition 3 ("I still don't know whether the west window was measured or only
  photographed"): Claude `none`, ChatGPT `unresolved`. Open definitional question: does "coreference" cover a
  which-of-two-events-happened ambiguity, or only pronoun/entity referential ambiguity? The guide does not
  say.

### Roles -- one systematic convention gap, not many independent disagreements

ChatGPT consistently applied the guide's optional "implicit writer actor" convention plus object-role tagging
to nearly every task proposition (e.g. all 8 of comparator:074's propositions carry `actor`+`object` roles in
ChatGPT's pass with none in Claude's). Claude did not apply this convention at all in this pass. This single
gap in convention application accounts for the large majority of individual role-set differences across the
matching records.

### Qualifiers -- minor, isolated

A handful of instances where ChatGPT captured an additional qualifier type Claude did not: comparator:042
proposition 4 (ChatGPT added `time` alongside `quantity`), comparator:053 proposition 4 (same pattern),
comparator:069 proposition 1 (ChatGPT added `object_modifier` alongside `deadline`), comparator:074
proposition 3 (ChatGPT added `object_modifier`). No instance of the reverse (Claude capturing a qualifier type
ChatGPT missed).

## 5. Root causes requiring future guide revision

1. **Unfielded-clause proposition policy.** The guide does not say whether a source clause with no dedicated
   bullet/action obligation of its own must receive an independent proposition, must be folded into an
   adjacent proposition's span, or may be silently omitted. This single open question is the root cause of
   all three count disagreements (007, 040, 054).
2. **Implicit-actor/object role convention.** The guide permits ("may be represented... uniformly") but does
   not require the implicit-writer-actor convention, and says nothing about a parallel implicit-object
   convention for simple imperative tasks. One annotator applying it and the other not applying it at all
   produces a large, systematic role-set mismatch that is not evidence of semantic disagreement.
3. **Coreference scope definition.** The guide does not define whether "coreference" is restricted to
   pronoun/entity referential ambiguity or also covers general unresolved-event-alternative content (as in
   075's west-window case), nor does it fix proposition-boundary conventions that would make coreference
   scope reproducible across annotators (as in 048's case).
4. **Qualifier boundary/type convention.** No rule governs when a single source phrase should be tagged with
   more than one qualifier type (e.g. a duration phrase as both `time` and `quantity`).

## 6. Disposition

- The first pilot round **fails** the annotation guide's own required exact-agreement gate ("agreement
  requires exact proposition count/order, state, coreference, duplicate link, and fields") on 3 of 10 records
  at the count level, plus 3 coreference mismatches within the matching set.
- Per the architecture study (`training/controlled_seed17_non_emitted_structural_supervision_architecture_study_chatgpt.md`),
  section 12's hard-stop condition "span/label agreement gates fail" is triggered.
- No piecemeal adjudication or silent harmonization occurred: this record preserves both passes and their
  disagreements exactly as produced, with no post-hoc edits to either sealed annotation file to improve
  apparent agreement.
- **Not authorized by this record:** annotation of the remaining 68 comparator records, any guide revision,
  any second annotation pilot, implementation, model or benchmark execution, corpus mutation, checkpoint
  action, or seed 73.
- **Recommended future milestone** (not authorized here, requires its own separate authorization): a guide
  revision addressing the four root causes in section 5, followed by a clean rerun of the same ten-record
  blind dual-annotation pilot.

This record and both sealed annotation files are intended as historical evidence of the first pilot round,
preserved for the commit under consideration, regardless of what a future guide revision or rerun produces.
