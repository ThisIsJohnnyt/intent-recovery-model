# Prompt Contract vNext — Static Package ChatGPT Review

**Date:** 2026-08-02  
**Reviewed commits:** intent-recovery-model `e2f5ac6` (package introduced at `27a642b`), thought-organizer-app `732fafb`  
**Reviewer:** ChatGPT, dataset and evaluation architecture  
**Status:** Direction accepted; static package not yet fully Aligned  
**Implementation authorized:** corrections to candidate-only static code only, after Johnny accepts this review  
**Compute authorized:** none

## Outcome

The typed-marker direction is accepted. Claude resolved both prior disagreements with direct evidence, kept every change isolated from the live pipelines, and produced a sound fail-closed parser design. The current 66-record migrated artifact is also correct: an independent parse-roundtrip check recovered the original narrative, bullet array, and action array exactly for all 66 records.

The package is not yet ready for final static alignment. Six gaps remain between the claims and the committed, repeatable evidence. None challenges the typed-marker decision; all are bounded candidate-only corrections.

## Independently confirmed

- The two commits add only candidate/static files; no live module imports them.
- The frozen corpus contains four natural `- ` occurrences in raw inputs, zero in curated outputs, and zero `###` occurrences across input and output.
- The Python and TypeScript parsers agree with the shared valid/error expectations.
- In a fresh app worktree, every local parser and sanitizer case passed.
- The same fresh-worktree run failed only its cross-repository fixture check because it hard-codes a machine-specific sibling path.
- Independent parse-roundtrip verification of `prompt_contract_v2_migrated_targets_DRAFT.jsonl` returned zero mismatches across all 66 records.
- Candidate isolation is genuine: `prepare_data.py`, `train.py`, `run_benchmark.py`, `noteOrganizer.ts`, and the live contract modules are unchanged.

## Finding 1 — candidate prompt still describes newline semantics

Both candidate prompt implementations say section markers are “each on their own line” and request “one marker line per” item. The investigation established that line boundaries do not survive tokenization. Typed markers fix the representation, but the prose still defines the structure using the mechanism being retired.

Required correction: describe markers—not lines—as the boundaries. Recommended wording:

```text
Respond using exactly these section and item markers, with no other text before or after the structured response. Newlines may be used for readability, but marker strings define the structure.

###NARRATIVE###
a coherent, source-supported narrative
###BULLETS###
Prefix each source-supported key idea with ###BULLET###. Use at most seven bullet items. Use fewer when the source supports fewer ideas. Never add, split, merge, or repeat content to approach a target count.
###ACTIONS###
Prefix each explicit supported task with ###ACTION###. If the source contains no tasks, emit no ###ACTION### markers.
```

The exact prose may be refined jointly, but it must not treat newline placement as semantic.

## Finding 2 — marker escaping is not tested through either tokenizer/runtime

The sanitizer tests operate on the raw sanitized Unicode string and then insert that string directly into a fabricated decoded output. They do not encode and decode the sanitized string through the actual Python tokenizer or production JavaScript runtime.

This matters because the escape relies on U+200C surviving normalization. The current tests do not establish that premise.

Required correction:

1. Sanitize inputs containing each exact marker and `#` runs of lengths 3, 4, 5, 7, and 22.
2. Encode/decode each sanitized value through Python and production JavaScript tokenizers.
3. Require no real marker string and no `#{3,}` substring to reappear.
4. Require byte-identical decoded strings across runtimes.
5. Add a marker-bearing prompt fixture to cross-repository prompt fingerprint tests; the existing ordinary fixture does not exercise sanitization.

## Finding 3 — token-budget evidence measures overhead, not complete targets

The report measures marker cost—about 31 tokens on average and 89 in the stated maximum-count case—but does not tokenize the complete migrated targets. Marker percentage alone cannot establish that the 300-token generation limit remains adequate once narrative and item text are included.

Required correction: tokenize all 66 complete v2 targets and every proposed v2 acceptance target. Report minimum, median, p95, maximum, the record producing the maximum, and the number at or above 300 tokens. If any case lacks safe headroom, propose and separately evaluate a generation-limit change rather than assuming 300 remains sufficient.

## Finding 4 — migration verification is logically weaker than the artifact

`prompt_contract_v2_migrate.py` checks marker counts and whether each original string appears somewhere in the serialized target. A missing item can pass if the same text occurs in another section, and mismatches are printed without a nonzero exit.

The current artifact happens to be correct: independent verification parsed all 66 v2 targets and compared the resulting structures with their original arrays, producing 66/66 exact matches. The committed migration test should prove that directly.

Required correction:

- parse every generated v2 target with `parse_output()`;
- require exact equality for narrative, ordered bullets, and ordered actions;
- fail nonzero on the first mismatch or after reporting all mismatches;
- keep serialization fingerprints as provenance, not as a substitute for structural equivalence.

## Finding 5 — cross-repository fixture checks are machine-layout dependent

The model test assumes a sibling directory named `thought-organizer-app`; the app test assumes a sibling directory named `DeepThoughts`. In fresh detached worktrees, both assumptions are false. The app suite reproduced this as one failure while all local parser/sanitizer assertions passed.

The fixture comment also still claims the copies are byte-identical and says the approach avoids a fragile cross-repository path dependency, although the test was changed to parsed-JSON equality and still uses exactly such a path.

Required correction: compute a canonical JSON fingerprint locally in each repository and require the same locked value. Canonicalization must sort object keys while preserving array order. This handles CRLF without requiring either repository to know the other’s filesystem location. Update all “byte-identical” and path-independence claims accordingly.

## Finding 6 — browser and app-side parity are one-time claims, not protected tests

The app test exercises its parser and sanitizer but does not load the production tokenizer/runtime. It also does not assert the candidate prompt version or rendered prompt fingerprint. The Python fingerprint test locks a value described as having been checked once on the app side, so later app drift would not fail its own suite.

Required correction: add a repeatable app-side candidate check that:

- asserts `PROMPT_CONTRACT_VERSION`;
- hashes the ordinary prompt fixture and the marker-bearing sanitizer fixture;
- compares both with locked shared values;
- runs the representative typed-marker and sanitized-marker sequences through the production tokenizer/runtime and asserts the frozen decoded results.

If loading model assets is too heavy for the ordinary unit suite, make this an explicit static-contract verification command and document when it must run. It still needs to be committed and reproducible.

## Clarification — zero bullets is parser-valid, not an acceptance success

The shared structural fixture permits a nonempty narrative with zero bullets. Keeping the parser capable of representing an empty array is acceptable, but this must not imply that a nonempty source note with a supported idea passes semantic acceptance with zero bullets. Every generated-model acceptance record must carry an explicit `bullet_count_rule`; the draft delivered with this review does so.

Rename or annotate the fixture as parser-only to prevent future readers from treating it as product behavior.

## Acceptance prose review

The existing five `source_determined_bullets` cases should remain historical evidence for the failed v1 study. They should not be edited in place or reused as the v2 gate.

This review supplies a new ten-case draft, `source_determined_items_v2_acceptance_draft.jsonl`, plus design notes. The new set:

- uses new dummy wording, nouns, and surface structures;
- requires bullet and action count rules on every case, including explicit zero;
- treats counts as automatically computed structural checks, not human capability checks;
- preserves strict semantic scoring and fail-closed completeness;
- covers observation, task, unrelated ideas, mixed content, tentative idea, unresolved alternatives, restatement, ceiling stress, dangling reference, and dense mixed attribution.

The draft is ready for Claude’s schema/runner feasibility review. It must not be frozen or used for compute until the six findings above are corrected and both reviewers mark the complete static package Aligned.

## Alignment status

| Area | Status |
|---|---|
| Typed `###BULLET###` / `###ACTION###` direction | Aligned |
| Narrow causal language | Aligned |
| Candidate-only isolation | Aligned |
| Parser shape and fail-closed philosophy | Aligned |
| Current migrated artifact contents | Aligned — independently verified 66/66 |
| Candidate prompt wording | Corrections required |
| Sanitizer/tokenizer proof | Corrections required |
| Full-target token budget | Corrections required |
| Migration regression test | Corrections required |
| Portable fixture parity | Corrections required |
| Repeatable app/runtime parity | Corrections required |
| v2 acceptance prose | ChatGPT draft supplied; Claude review required |

## Next action

Claude owns the six bounded candidate-only corrections and the schema/runner feasibility review of the acceptance draft. ChatGPT owns the follow-up scoring-architecture review. Johnny does not need to authorize compute; none is requested. After both sides mark the corrected static package Aligned, Johnny can separately decide whether to authorize one seed-17 study.
