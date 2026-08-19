# Gate 5 V13: content-free collision-length metadata

## Decision this documents

Johnny reviewed V12 r2's real, complete 22/22-card run (`gate5_paid_pilot_retry_campaign_v12_2026-08-18_r2`, real aggregate spend $1.418181) and asked whether Gemini's one real V12 r2 acceptance batch was the norm or a fluke, and what to do about the remaining fan-out pattern in the real collision data. A retrospective, zero-cost, read-only audit of the pre-Gemini corpus was run the same day (`corpus_retro_audit_2026-08-18_report.md`) at Johnny's request, surfacing (among other findings) that nothing in this project had ever measured whether short compared text specifically drives spurious collisions. Johnny approved two follow-ups in order, explicitly ahead of any raw-content-capture work: "Let's go ahead and look at both points 1. and 2. These are solid ideas to expand on before something big like capturing rejected content." This is Point 1.

## Real evidence behind this change

From V12 r2's real structured collision diagnostics (similarity scores and reason codes only -- no raw candidate/reference text is ever persisted, by design):

- One real collision (M07, `output.bullets:01`) matched **19 distinct reference records simultaneously**, producing **22 identical character-5-gram Jaccard scores** (0.173913) across those matches -- a fan-out signature consistent with either genuine corpus repetition or the same short-string Jaccard effect this project has already proven twice in its own regression tests (V11's token side, V12's char-5-gram side: removing a stopword present on only one side shrinks the union without shrinking the intersection, which can raise rather than lower similarity for short strings).
- Aggregate similarity scores alone cannot distinguish those two explanations. The one piece of information that directly would -- how long the compared text actually was -- has never been recorded.

## Exact scope of this change

**Changed:** whenever a real protected-collision rejection happens, the persisted diagnostic row (a new schema_version, 2, alongside the unchanged schema_version 1 every V6-V12 real row already used) also carries:
- `candidate_field_length`: length metadata for the one candidate field that triggered the rejection.
- `reference_field_length`, attached to every entry in `reasons` and to both `maximum_token_jaccard`/`maximum_character_5gram_jaccard`: length metadata for the reference record each one points at.

Length metadata is exactly two non-negative integers, computed by a new, purely additive `gate2.field_length_metadata()` function using the same normalization and stopword-filtering primitives real scoring already runs (`normalize_for_collision`, `_stopword_filtered_tokens`): `normalized_char_length` (character count of the normalized text, spaces removed -- the same string `char_5grams`/`char_5grams_stopword_filtered` window over) and `stopword_filtered_token_count` (size of the same stopword-filtered token set token-Jaccard already scores). No text, substring, or anything reversible to content ever crosses into a persisted row -- `gate5_output_collision_evidence.py`'s stated invariant ("candidate and comparator text are deliberately absent from every public function signature used to build a persisted row") holds exactly as it did in V6-V12; the engine computes lengths itself, from text it already holds in memory for the single request being screened, and passes only integers into the evidence module.

**Unchanged, deliberately:**
- Candidate screening: still `gate2.screen_candidate_fully_stopword_filtered()`, byte-for-byte identical to V12. This build changes what gets *recorded* about a rejection, never what gets accepted or rejected. `TOKEN_JACCARD_THRESHOLD` (0.15) and `CHAR_5GRAM_JACCARD_THRESHOLD` (0.10) are untouched.
- Every real schema_version-1 diagnostic row already persisted across V6-V12's real campaigns keeps validating against the original, completely unmodified `build_row`/`validate_row`/`verify_chain`/`validate_rejection_links`. The new schema_version-2 path (`build_row_v2`/`validate_row_v2`/`verify_chain_v2`/`validate_rejection_links_v2`) is fully parallel, added alongside rather than replacing the original -- the same discipline V11/V12 used for `gate2.py`'s collision functions, applied here to the evidence module for the first time.
- The full continue-past / hard-terminal ruleset, schema validation, cost ceilings, schedule, prompts, retry limits -- all identical to V12 ($5.00 pilot ceiling equivalent scaled to the new baseline, same 22-card schedule, 5 max attempts per card, same models and rates).
- The 80-word schema floor stays explicitly deferred, per Johnny's own call.

**How it's implemented:** `gate2.py` gains one new, purely additive function (`field_length_metadata`) alongside V11/V12's existing additions, which are left completely untouched. `gate5_output_collision_evidence.py` gains a fully parallel schema_version-2 code path appended after the original, untouched code. Nothing in V6-V12 calls any of the new functions, so every prior version's frozen tests and hash-pinned artifacts -- including every real historical diagnostic row already on disk -- keep passing byte-for-byte unchanged, confirmed by re-running the full V6-V12 suites with zero regressions before this build was finalized.

## Historical baseline

V13 appends V12's real, complete terminal outcome (the successful r2 run; the first V12 attempt hard-stopped on a real, now-fixed production bug and was never chained forward, matching how V12 r2 itself was built on V11's unchanged 28-component baseline) as historical component 29, onto V11's 28-component chain:

- V12 r2 real terminal outcome: `completed_full_schedule`, real spend **$0.363232** (363,232 usd_millionths) on top of the same $1.054949 (1,054,949 usd_millionths) baseline V12's first attempt also used, evidence independently re-derived from V12 r2's real 8 output files.
- New historical baseline: **$1.418181** (1,418,181 usd_millionths) -- the same real aggregate independently verified after V12 r2's real run completed.

## Cost math for this version

Identical per-request costs to V12 (same schedule, same rates):
- Single-pass reservation: 187,000 usd_millionths ($0.187)
- Worst case (all 22 cards retry the full 5 attempts): 935,000 usd_millionths ($0.935)
- Worst-case aggregate with the new historical baseline: 1,418,181 + 935,000 = **2,353,181 usd_millionths ($2.353181)**

Comfortably inside the unchanged $5.00 pilot ceiling / $3.75 reconciliation stop.

## What this run is meant to answer

Whether real future protected-collision rejections that show the same broad, near-uniform-score fan-out signature V11 and V12 r2 both showed correlate with short candidate/reference text length -- directly testing the short-string Jaccard hypothesis against real data instead of reasoning from aggregate scores alone. Point 2 (threshold re-examination) is explicitly sequenced after this one: real length data from V13 may explain away some of the remaining fan-out without needing to touch `TOKEN_JACCARD_THRESHOLD`/`CHAR_5GRAM_JACCARD_THRESHOLD` at all.
