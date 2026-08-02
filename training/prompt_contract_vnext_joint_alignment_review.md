# Prompt Contract vNext — Joint Alignment Review

**Date:** 2026-08-02  
**Reviewer:** ChatGPT, dataset and evaluation architecture  
**Inputs reviewed:** `training/seed17_postmortem_claude_contribution.md`, corrected `training/prompt_contract_compatibility_study_manifest.md`, and the previously issued ChatGPT postmortem/contract/evaluation package  
**Implementation authorized:** none  
**Compute authorized:** none

## Outcome

Claude's direct tokenizer investigation confirms the central representation finding in ChatGPT's postmortem: newline characters do not survive the FLAN-T5 tokenizer round trip, while literal section markers do. Because newline was the only encoded distinction between adjacent bullet or action targets, the model was not trained on a mechanically recoverable item boundary.

The two reviews are aligned on the root representation defect, the need to separate structural and semantic evaluation, the corrected runner/prompt pinning method, and the decision not to add narrow corrective examples before selecting a verifiable output contract.

There is one contract choice on which ChatGPT is not aligned with Claude's stated preference: a dash prefix should not be selected as the preferred delimiter. Repeated, section-specific typed markers remain the recommendation.

There is also one causal-language correction: the tokenizer result proves the cause of missing item-boundary observability and learnability. It does not yet prove that this defect caused *most* seed-17 semantic failures.

## Findings accepted

### 1. Newline loss is directly established

Claude tested the actual project tokenizer rather than inferring behavior from decoded study outputs:

- newline-separated strings decode with their newlines removed;
- the behavior is independent of `skip_special_tokens=True`;
- existing section-marker strings survive;
- the same collapse occurs in real tokenized training targets.

This closes the mechanism question left open in ChatGPT's postmortem. The representation problem occurs before target tokens reach the model, not only during inference or app parsing.

### 2. The corpus contains item structure that the token stream erases

`prepare_data.py` correctly constructs distinct newline-separated target items, but tokenization removes those boundaries. The data's logical arrays are therefore richer than the sequence-level supervision presented to the model.

Claude's capitalization analysis supports—not proves—a mechanistic explanation for some observed topic merging, fragmentation, and loss. Capitalization is an ambiguous soft cue because proper nouns also occur inside items.

### 3. Explicit non-whitespace delimiters are feasible in principle

Dash, pipe, numbering, and marker-style candidates all survive the Python tokenizer test. This is sufficient to continue with static contract design. It is not yet sufficient to select a production delimiter; browser-runtime parity, parser behavior, malformed-output handling, and collision resistance still require testing.

### 4. Runner/prompt pinning correction is sound

Pinning only the prompt-building module while executing the current reviewed runner prevents prompt reproducibility from rolling back scoring-schema safeguards. The dry-run evidence supports the correction.

Future tooling should expose this as an explicit prompt-provider interface with a required contract fingerprint rather than relying indefinitely on an undocumented path-injection convention. That is an implementation-hardening note, not a disagreement with the corrected study mechanism.

### 5. Curriculum changes remain premature

The representation defect must be isolated before content examples are changed. Adding examples for individual seed-17 failures now would confound serialization, prompt wording, and curriculum content and would repeat a pattern already associated with collateral regressions at this data scale.

## Disagreement 1 — do not prefer dash prefixes

Claude identifies `- ` as the least visually disruptive candidate. ChatGPT does not recommend it as the contract delimiter.

After newline normalization, multiple dash-prefixed items become one inline string. A parser would have to interpret occurrences of `- ` within that string as boundaries. That sequence can also appear naturally in item content, punctuation, copied fragments, ranges, or model-generated prose. Without a surviving start-of-line concept, “prefix” is no longer a structurally privileged position.

Numbering and pipe separators have related collision and recovery ambiguities. They are adequate diagnostic controls, but weaker final contracts.

Recommended candidate:

```text
###NARRATIVE###
coherent narrative
###BULLETS###
###BULLET### first supported idea
###BULLET### second supported idea
###ACTIONS###
###ACTION### first explicit task
```

The newlines above are readability only. Repeated `###BULLET###` and `###ACTION###` strings carry the actual boundaries. Separate marker types also make cross-section leakage mechanically detectable.

This recommendation remains conditional on collision handling: marker-like source text must be escaped or isolated so copied input cannot be mistaken for output structure.

## Disagreement 2 — narrow the causal claim

The statement “the tokenizer is the root cause underneath most seed-17 failures” is stronger than the current evidence supports.

The investigation establishes that the tokenizer is the root cause of:

- absent item-boundary supervision;
- inability to mechanically recover item counts from current output;
- dependence on weak semantic/capitalization cues for splitting.

It makes topic merge, fragmentation, loss, and duplication more mechanistically understandable. It does not directly establish that delimiter loss caused unsupported qualifiers, trailing commentary, invented actions, attribution errors, or other semantic failures. A delimiter-preserving controlled candidate has not yet been trained, so the fraction of semantic failures attributable to representation remains unknown.

Claude's full document is mostly calibrated correctly—it says the defect “plausibly explains a meaningful share.” The narrower wording should be retained in project decisions and future reports.

## Static feasibility package required before a contract decision becomes executable

If Johnny selects typed markers as the design direction, Claude can prepare a dummy-only, no-GPU package for joint review containing:

1. Python tokenizer round trips for the exact proposed section and item markers.
2. Browser-tokenizer/runtime parity for the same frozen token and string fixtures.
3. Python and TypeScript parsers producing identical structured outputs from single-line and multiline forms.
4. Fail-closed fixtures for missing, duplicated, reordered, empty, and cross-section markers.
5. Fixtures proving that marker-like literal source text cannot alter parsed output structure.
6. Mechanical migration of the same 66 targets with byte-identical semantic text and identical pre/post item counts.
7. Cross-repository prompt rendering and contract-fingerprint parity.
8. A token-budget comparison measuring marker overhead.

This package should contain no new curriculum examples and should not train or run a model.

## Joint alignment status

| Question | Status |
|---|---|
| Is newline loss the current item-boundary defect? | Aligned |
| Should structure become explicitly machine-verifiable? | Aligned |
| Should structural and semantic gates remain separate? | Aligned |
| Is corrected prompt-only pinning preferable to old-runner worktrees? | Aligned |
| Should narrow corrective curriculum work begin now? | Aligned — no |
| Is `- ` the preferred final delimiter? | **Not aligned** |
| Are repeated typed item markers the leading candidate? | ChatGPT: yes; Claude confirmation requested |
| Has representation loss been proven to cause most semantic failures? | **Not aligned with that broad wording** |

## Decision requested from Johnny

No compute decision is needed yet. The next product-owner decision is whether to select repeated typed markers as the provisional vNext direction and authorize only the dummy/static feasibility package above.

If Claude disagrees with typed markers after considering collision resistance and cross-runtime parsing, Claude should return evidence and a concrete alternative before any implementation proceeds.
