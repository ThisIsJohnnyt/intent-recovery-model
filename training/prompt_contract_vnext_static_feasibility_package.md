# Prompt Contract vNext — static feasibility package (Claude)

**Date:** 2026-08-02
**Status:** Implementation complete for all 8 requested items. **No compute, no
training, no inference, no live-pipeline changes.** Everything here is new,
separately-named "candidate"/"v2" code, not wired into `prepare_data.py`,
`train.py`, `run_benchmark.py`, or `noteOrganizer.ts`.
**Responds to:** `prompt_contract_vnext_joint_alignment_review.md`'s two
disagreements and its 8-item static feasibility request.

## Both disagreements: agreed, with evidence

### Disagreement 1 — dash prefix withdrawn, typed markers confirmed as the leading candidate

Checked this empirically rather than just conceding on reasoning alone.
Searched the actual gold_v1.2.2 corpus for naturally-occurring `- `
(space-dash-space) patterns:

- **Curated gold *output* text**: 0 occurrences.
- **Raw *input* notes**: 4 occurrences — real examples from this project's
  own corpus include `"- hdmi cable"`, `"- gym"`, i.e. people genuinely
  write dash-bulleted shopping-list-style notes.
- **`"###"` anywhere in the corpus (input or output)**: 0 occurrences.

This confirms the collision risk concretely, not just in the abstract: a
dash-prefix delimiter would collide with an ad hoc formatting convention
real users already use in raw notes, while `"###"` essentially never
occurs naturally. Combined with the "no surviving start-of-line privilege
after newline collapse" reasoning, **agreed: dash prefix is withdrawn,
typed `###BULLET###`/`###ACTION###` markers are the confirmed leading
candidate.**

### Disagreement 2 — narrower causal language accepted

Agreed. My document's own body already used the hedged framing ("plausibly
explains a meaningful share of the semantic failures... not as an excuse
for them, but as a mechanistic account of why... would fail in exactly
these ways") — but my own chat summary in this conversation used a
stronger headline ("the tokenizer is the root cause underneath most of the
seed-17 failures") that overstated what the evidence supports. The
narrower framing is correct and is what should be carried forward: the
tokenizer investigation establishes the mechanism of the *representation*
defect (absent boundary supervision, unrecoverable counts, weak
capitalization-only cues) — it does not establish what fraction of the
*semantic* failures (invented content, misattribution, deduplication
failures) that defect caused. That remains unknown until a
delimiter-preserving candidate is actually trained and compared.

## The 8-item static feasibility package

All items implemented and tested; nothing here requires a GPU.

### 1 & 8. Python tokenizer round-trip + token-budget comparison

`training/test_prompt_contract_v2_candidate.py`. Confirmed against the real
seed-17 checkpoint's tokenizer: the exact candidate shape (`###BULLET###`/
`###ACTION###`, both section and item markers) round-trips with exact
count and spelling preserved, including in **decoded (newline-collapsed)**
form — the actual shape a real generation would produce — which still
parses correctly. Token cost (measured earlier this session, reused here):
`###BULLET###` = 7 tokens, `###ACTION###` = 5 tokens; worst case (7
bullets + 8 actions) = 89 marker tokens, ~30% of the 300-token generation
budget; average case (actual corpus mean) ~31 tokens, ~10%. Adequate, not
free.

### 2. Browser-runtime parity

Verified directly against the **actual production JS runtime**
(`@xenova/transformers`, loaded from `thought-organizer-app/public/models/`,
not a mock). Full-sequence decode is byte-identical to Python for the
candidate shape. (One pre-existing, documented nuance from the earlier
review: isolated-substring tokenization differs by a leading-space token
between the two runtimes — irrelevant here too, since parsing operates on
decoded text.)

### 3 & 4. Python/TypeScript parser parity, empty-array parsing

New: `training/prompt_contract_v2_parser.py` and
`thought-organizer-app/src/services/promptContractV2Parser.ts`, plus a
**shared, byte-identical fixture file**
(`prompt_contract_v2_parser_fixtures.json`, duplicated in both repos with a
dedicated test in each confirming the copies match — avoids both
independently-authored test data that could silently drift, and a fragile
cross-repo relative-path dependency at runtime). 13 fixture cases (4 valid,
9 error), run through both parsers, produce identical structured output or
identical error triggers in every case — confirmed by actually running
both, not by inspection. Zero-item sections (`###BULLETS### ###ACTIONS###`
with nothing between) correctly parse as empty arrays in both languages.

### 5. Fail-closed malformed-input handling

Same fixture set's 9 error cases, all correctly rejected with specific
reasons in both languages: missing marker, duplicated marker, reordered
markers, text before the first marker, empty narrative, cross-section
leakage (an `###ACTION###` inside the bullets span or vice versa), bare
content with no item marker, and an empty item. No malformed case is
silently accepted or misparsed.

### 6. Marker-collision escaping (closes the gap flagged in the prior review)

New: `sanitize_marker_like_text()` (Python) / `sanitizeMarkerLikeText()`
(TypeScript), byte-identical algorithms. Defangs any run of 3+ literal `#`
characters in raw input by inserting a zero-width non-joiner (U+200C)
*every 2 characters throughout the run* — not just once at the start,
which a real bug in the first draft revealed is insufficient for runs
longer than 4 characters (a 7-`#` run still contained a matchable 3+
substring after a single insertion point; caught by testing, not
assumed). Verified end-to-end: a raw input containing the literal string
`"###BULLET###"`, sanitized and then echoed into a fabricated model
output, no longer corrupts parsing — the parser still finds exactly the
one real bullet, not a phantom boundary from the echoed text.

### 7. Mechanical dataset migration

New: `training/prompt_contract_v2_migrate.py`. Migrated all 66
gold_v1.2.2 targets from the current bare-newline serialization to the
typed-marker serialization. Verified programmatically for every record:
bullet/action counts identical before and after; narrative, bullet, and
action text unaltered (every original string still appears verbatim in
the migrated target). Zero mismatches across all 66. Recorded three SHA-256
fingerprints: one over the semantic content (input+output, migration-
invariant — proves the migration didn't touch the underlying data) and one
each over the v1 and v2 target serializations (which differ, as expected,
since only the wire format changed). Draft output written to
`prompt_contract_v2_migrated_targets_DRAFT.jsonl` — not live data, not
read by `prepare_data.py`.

### Cross-repo prompt fingerprint parity (part of item 2/7's spirit)

`training/test_prompt_contract_v2_fingerprint_parity.py`. Rendered the
same fixture (`real_data_private.PROMPT_CONTRACT_FIXTURE`, the same one
the live v1 contract already uses) through both `build_prompt`
implementations and got the **identical SHA-256**,
`9ee6bc1673c885ee3fc341d4b7ac5dada24b7ce8a435a20103455ac07e88fb6e`, on both
sides. `PROMPT_CONTRACT_VERSION` on both sides:
`source-determined-items-v2-candidate` (candidate-suffixed, matching the
review's instruction not to adopt a final identifier yet).

## Files added (all new, none touching the live pipeline)

Training repo: `prompt_contract_v2_candidate.py`, `prompt_contract_v2_parser.py`,
`prompt_contract_v2_migrate.py`, `prompt_contract_v2_parser_fixtures.json`,
`test_prompt_contract_v2_candidate.py`,
`test_prompt_contract_v2_fingerprint_parity.py`,
`prompt_contract_v2_migrated_targets_DRAFT.jsonl` (generated artifact).

App repo: `src/services/promptContractV2Candidate.ts`,
`src/services/promptContractV2Parser.ts`,
`src/services/prompt_contract_v2_parser_fixtures.json` (byte-identical copy),
`src/services/promptContractV2Parser.test.ts`.

## What this package does not do

Does not change `PROMPT_CONTRACT_VERSION`, `prepare_data.py`,
`noteOrganizer.ts`, or any live file. Does not train or run a model. Does
not migrate real data (only a draft file, from the pinned 66-example
corpus). Does not decide the final marker naming or wording — per the
review, `source-determined-items-v2` (without "-candidate") "must not be
adopted until cross-repository review is complete," and that review is
this document, not yet a final sign-off.

## Requested next step

Per the vNext decision sequence: this closes step 4 ("Claude builds
dummy-only parsers, round-trip fixtures, runner separation, and cross-repo
prompt parity" — runner separation was already closed in the prior round).
Step 5 is ChatGPT reviewing the actual acceptance prose and rubric
bindings; step 6 is both sides marking the static package Aligned; step 7
is Johnny separately authorizing one seed-17 compute study under the
selected contract. No compute is requested here.
