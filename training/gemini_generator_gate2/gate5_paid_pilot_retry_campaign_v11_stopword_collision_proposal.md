# Gate 5 V11: stopword-filtered token-Jaccard collision scoring

## Decision this documents

Johnny reviewed V10's real, complete 22/22-card run (`gate5_paid_pilot_retry_campaign_v10_2026-08-18_r2`, real aggregate spend $0.685501) and asked: is 1/22 acceptance the true capability of the generator, or an artifact of overly strict collision/schema checks? After reviewing the real structured diagnostic evidence from that run, Johnny approved a first, isolated fix: **remove stopwords from the token-Jaccard collision comparison, and reassess from there before touching anything else** -- not the thresholds, not schema, not the continue-past ruleset.

## Real evidence behind this change

From V10 r2's real structured diagnostics (similarity scores and reason codes only -- no raw candidate/reference text is ever persisted, by design):

- 14/22 cards (64%) were rejected for collision; 4/22 (18%) for schema; 3/22 (14%) exhausted retries on a 503; 1/22 (4.5%) was accepted.
- Of the individual token-Jaccard matches recorded across those 14 collision diagnostics, the overwhelming majority scored **0.153-0.20** -- just over the 0.15 threshold, not strong matches.
- Two of the 14 diagnostics show a single candidate simultaneously matching **20+ different, unrelated reference records** at once (26 references for one M09 card, 22 for one M12 card). A genuine near-duplicate typically shows one or two strong matches (the run's one clearly strong case, M05, scored 0.333 token / 0.304 char against a single reference) -- not two dozen weak matches spread across unrelated corpus entries. That fan-out pattern is the signature of shared common vocabulary inflating similarity, not real duplication.
- Token-Jaccard, as implemented, performs **no stopword removal** (`gate2.normalize_for_collision` + raw `.split()`). In a corpus where every candidate and every reference is short, similarly-structured task output (bullets/action items about comparable topics), ordinary function words alone can push unrelated texts past 0.15.

This is real, evidence-based grounds to suspect token-Jaccard is over-triggering. It is not proof any specific one of the 14 real collisions was a false positive -- raw text isn't retained, so that can't be checked retroactively. The only way to test the effect for real is a new run with the fix in place, which is what this version is for.

## Exact scope of this change

**Changed:** candidate screening now calls `gate2.screen_candidate_stopword_filtered()` instead of `gate2.screen_candidate()`. Internally, this strips a fixed, closed-set, ~174-word English stopword list (articles, pronouns, prepositions, conjunctions, auxiliary/modal verbs, common contractions, and a handful of generic quantifiers) from both sides of the token-Jaccard comparison before scoring.

**Unchanged, deliberately:**
- `TOKEN_JACCARD_THRESHOLD` (0.15) and `CHAR_5GRAM_JACCARD_THRESHOLD` (0.10) -- same numeric thresholds, applied to stopword-filtered tokens instead of raw tokens.
- Character-5-gram Jaccard scoring -- untouched, still computed over the full normalized text including stopwords. It is a separate, character-level signal and was not implicated by the evidence above (its matches showed smaller, tighter margins than token-Jaccard's, not the same many-reference fan-out).
- Exact-match and normalized-containment detection -- untouched, still computed over the full normalized text, not stopword-filtered. These are precise duplicate detectors, not fuzzy-similarity scores, and were not implicated by the evidence.
- Schema validation (the 80-220 word `source_input` floor/ceiling) -- untouched. That is a separate lever Johnny flagged as worth a smaller, later look, not part of this build.
- The full continue-past / hard-terminal ruleset -- byte-for-byte identical to V10 (schema_invalid and the collision family continue past; secret_exposure, both `*_diagnostic_withheld` reasons, cost-tier stops, and structural failures all remain hard-terminal).
- Cost ceilings, schedule, prompts, retry limits -- identical to V10 ($5.00 pilot ceiling, $3.75 reconciliation stop, same 22-card schedule, 5 max attempts per card).

**How it's implemented:** `gate2.py` gains new, purely additive functions (`STOPWORDS`, `collision_check_stopword_filtered`, `screen_candidate_stopword_filtered`) alongside the existing `collision_check`/`screen_candidate`, which are left completely untouched. Nothing in V6-V10 calls the new functions, so every prior version's frozen tests and hash-pinned artifacts keep passing byte-for-byte unchanged -- confirmed by re-running the full V6-V10 suites with zero regressions before this build was finalized.

## Historical baseline

V11 appends V10 r2's real, complete terminal outcome as historical component 27, onto V9's 26-component chain (which V10 itself already carried forward from V8's 25):

- V10 r2 real terminal outcome: `completed_full_schedule`, real spend **$0.405861** (405,861 usd_millionths), evidence independently re-derived from V10 r2's real 8 output files.
- New historical baseline: **$0.685501** (685,501 usd_millionths) -- the same real aggregate independently verified after the real run completed.

## Cost math for this version

Identical per-request costs to V10 (same schedule, same rates):
- Single-pass reservation: 187,000 usd_millionths ($0.187)
- Worst case (all 22 cards retry the full 5 attempts): 935,000 usd_millionths ($0.935)
- Worst-case aggregate with the new historical baseline: 685,501 + 935,000 = **1,620,501 usd_millionths ($1.620501)**

Both figures are comfortably inside the unchanged $5.00 pilot ceiling / $3.75 reconciliation stop.

## What this run is meant to answer

Whether the real acceptance rate improves once stopword-driven token-Jaccard false positives are removed, isolating that one variable from schema strictness and the threshold values themselves -- both of which stay exactly as they are in V10 pending this result.
