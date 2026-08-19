# Gate 5 V12: stopword-filtered character-5-gram collision scoring

## Decision this documents

Johnny reviewed V11's real, complete 22/22-card run (`gate5_paid_pilot_retry_campaign_v11_2026-08-18`, real aggregate spend $1.054949; V11 itself was fully verified via direct re-scoring of the real accepted candidates, proving V11's fix caused all 3 real V11 acceptances) and, when asked for a recommendation, was told the real V11 data showed a new, structurally identical problem on the character-5-gram side. Johnny approved the same isolated-variable treatment for character-5-gram scoring next, deferring the 80-word schema floor to later if needed.

## Real evidence behind this change

From V11's real structured collision diagnostics (similarity scores and reason codes only -- no raw candidate/reference text is ever persisted, by design):

- One real collision (M12, `output.bullets:01`) matched **28 different, unrelated reference records simultaneously** on character-5-gram Jaccard, all clustered at **0.102-0.109** -- just over the unchanged 0.10 threshold.
- This is the identical fan-out signature that justified fixing token-Jaccard in V11: many weak, near-threshold matches spread across unrelated corpus entries, rather than one or two strong matches to a genuinely similar record (V11's own real data also had a clean example of a genuine strong match: M05 scored 0.333 token / 0.304 char against a single reference -- exactly what real duplication should look like).
- Character-5-gram Jaccard, as implemented, is computed over the full normalized text with no stopword removal at all -- the same methodological gap V11 closed on the token side. Common short words ("the", "and", "for", "on", "with") contribute disproportionately to character-level n-gram overlap in short, similarly-templated task output, the same way they inflated word-level overlap.

A synthetic, real-corpus-verified example built during this build's own self-review reproduces the mechanism directly: a stopword-dense synthetic bullet ("Follow up with the group on this for the team on the following day.") scores 0.142857 token-Jaccard (already non-fatal under V11's fix) but 0.166667 character-5-gram Jaccard against a real corpus reference -- fatal under V11, clean under V12.

## Exact scope of this change

**Changed:** candidate screening now calls `gate2.screen_candidate_fully_stopword_filtered()` instead of `gate2.screen_candidate_stopword_filtered()`. Internally, this adds stopword-filtered character-5-gram scoring alongside V11's already-stopword-filtered token-Jaccard scoring: the same fixed, closed-set ~174-word English stopword list is removed from the text (preserving original word order -- character 5-grams span word boundaries, so *where* stopwords are removed matters, not just which words remain) before computing 5-character sliding windows.

**Unchanged, deliberately:**
- `TOKEN_JACCARD_THRESHOLD` (0.15) and `CHAR_5GRAM_JACCARD_THRESHOLD` (0.10) -- same numeric thresholds as V11, applied to stopword-filtered character n-grams instead of the full text's n-grams.
- Token-Jaccard scoring -- already fixed in V11, byte-for-byte unchanged here (V11's `collision_check_stopword_filtered`/`screen_candidate_stopword_filtered` stay completely frozen; V12 adds new functions rather than modifying them).
- Exact-match and normalized-containment detection -- untouched, still computed over the full normalized text. These are precise duplicate detectors, not fuzzy-similarity scores, and were not implicated by the evidence.
- Schema validation (the 80-220 word `source_input` floor/ceiling) -- untouched, explicitly deferred by Johnny.
- The full continue-past / hard-terminal ruleset -- byte-for-byte identical to V11 (schema_invalid and the collision family continue past; secret_exposure, both `*_diagnostic_withheld` reasons, cost-tier stops, and structural failures all remain hard-terminal).
- Cost ceilings, schedule, prompts, retry limits -- identical to V11 ($5.00 pilot ceiling, $3.75 reconciliation stop, same 22-card schedule, 5 max attempts per card).

**How it's implemented:** `gate2.py` gains new, purely additive functions (`_stopword_filtered_normalized_text_ordered`, `char_5grams_stopword_filtered`, `collision_check_fully_stopword_filtered`, `screen_candidate_fully_stopword_filtered`) alongside V11's existing additions, which are left completely untouched. Nothing in V6-V11 calls the new functions, so every prior version's frozen tests and hash-pinned artifacts keep passing byte-for-byte unchanged -- confirmed by re-running the full V6-V11 suites with zero regressions before this build was finalized.

## A known, considered risk carried forward from V11

V11's own self-review found a real, narrow edge case: for very short strings, removing a stopword present on only one side of a comparison (not shared) shrinks the Jaccard union without shrinking the intersection, which can *raise* rather than lower the score. That property is generic to Jaccard similarity, not specific to tokens -- it applies to character-5-gram scoring the same way. V12's test suite includes a dedicated regression test for this on the character-5-gram side, mirroring V11's.

## Historical baseline

V12 appends V11's real, complete terminal outcome as historical component 28, onto V10's 27-component chain (which V11 itself already carried forward from V9's 26 and V8's 25):

- V11 real terminal outcome: `completed_full_schedule`, real spend **$0.369448** (369,448 usd_millionths), evidence independently re-derived from V11's real 8 output files.
- New historical baseline: **$1.054949** (1,054,949 usd_millionths) -- the same real aggregate independently verified after V11's real run completed.

## Cost math for this version

Identical per-request costs to V11 (same schedule, same rates):
- Single-pass reservation: 187,000 usd_millionths ($0.187)
- Worst case (all 22 cards retry the full 5 attempts): 935,000 usd_millionths ($0.935)
- Worst-case aggregate with the new historical baseline: 1,054,949 + 935,000 = **1,989,949 usd_millionths ($1.989949)**

Comfortably inside the unchanged $5.00 pilot ceiling / $3.75 reconciliation stop.

## What this run is meant to answer

Whether the real acceptance rate improves further once the same char-5-gram fan-out pattern V11 fixed on the token side is closed on the character side too -- isolating this one additional variable from the schema floor, which stays exactly as it is pending Johnny's later review.
