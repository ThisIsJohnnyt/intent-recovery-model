# Seed-17 v2 No-Compute Corpus Coverage Audit — Claude's Independent Verification

**Date:** 2026-08-03
**Verifying:** `seed17_v2_no_compute_corpus_coverage_audit.md`
**Compute performed:** none. Verification done by direct computation against the real, already-migrated 66-example corpus (`prompt_contract_v2_migrated_targets_DRAFT.jsonl`) and by reading cited examples' actual text.

## Outcome

**Confirmed. No disagreement.** Every quantitative claim reproduced exactly; every specific example cited was located and its content matches the description; all three flagged target-integrity concerns hold up under direct reading. My own independent scans for additional instances of the same violation classes turned up one minor additional borderline case, not a new class of problem.

## Corpus-wide structural distribution: exact match

Recomputed directly from the corpus (split by the real `split_manifest.json`, counts from the real `output.bullets`/`output.action_items`, not re-derived logic):

- Train (60): bullet histogram `{1:4, 2:13, 3:20, 4:16, 5:6, 6:1}`, action histogram `{0:7, 1:22, 2:16, 3:7, 4:7, 5:1}` — **matches the audit's table exactly**, including the zero counts at 7/8 bullets and 6/7/8 actions.
- Val (6): bullet counts four-at-3/two-at-4; action counts one-at-0/two-at-1/two-at-2/one-at-3 — **exact match**.
- Max training action count: 5, represented exactly once (the "keys, wallet, phone... no the meeting first" record) — **confirmed**. This is the single strongest quantitative point in the audit: sdi2-08 needed 8 actions and produced exactly 5, matching the training ceiling precisely, not some other number -- strong, direct evidence for "distribution ceiling" over "parser failure."

## Every cited example located and confirmed

- **zero_action_items (fog/river/cardinals)**: found, B3/A0, narrative correctly separates three unrelated observations with no invented relationship. Matches "neutral separation... represented only once" (the corpus's only other `zero_action_items` record is the Zesto-commercial one, a single-topic case, not multi-observation).
- **Toaster/kettle either-or**: found (`open_question_preservation`), B3/A1 -- the either-or plus later observation *does* carry an explicit action (library-bag drop), confirming the audit's specific point that this closest analogue still isn't the required *zero*-action form sdi2-06 needed.
- **Rina/Marcus** (Probe 06 analogue): found (`multi_person_attribution`) -- ambiguous "he" resolved between two named people, structurally close to Probe 06's Tessa/Rowan/inspector ambiguity. Confirmed as a real, close analogue already in train.
- **Three restatement-dedup examples**: found all three -- `repeated_reminder` ("email dave" ×3 → deduped to one task, plus one unrelated movie-time question), `repeated_reminder_multi_topic` ("timesheet" ×3 → deduped, plus two unrelated tasks), and `standalone_task_retention` ("mileage form" ×3 → deduped, plus two unrelated items -- this is also target-integrity concern #1, see below). All three genuinely deduplicate a restated task while mixing in other topics, exactly as described -- **confirms "three examples exist, none in pure 1/1 form."**
- **B6/A2 dense composite** (sdi2-10 analogue): found (`buried_task_retention`, "demo... Chris... Dana... dentist... porch bulb"), exactly B6/A2 as claimed, with observation/tentative-idea/unresolved-attribution-question/two-tasks composition matching the structural shape of sdi2-10 -- but with a simpler two-party attribution and no shared deadline, consistent with "one dense example did not generalize across new roles and a shared deadline."

## All three target-integrity concerns confirmed by direct reading

1. **`standalone_task_retention` (mileage form / sink)**: input says "the kitchen sink is dripping again which is exhausting"; the committed target's narrative *and* one of its bullets both say the sink itself "feels exhausting" ("The dripping sink feels exhausting"). Confirmed verbatim -- the target genuinely attributes an emotional state to an inanimate object, structurally identical to the v2 study's own Probe-11 output ("the garage light... feels tired"). This is a real property of the currently-committed gold_v1.2.2 corpus (the `output` field is unchanged by the v1→v2 migration), not an artifact of this study.
2. **First `dangling_reference` record (blue folder / daughter / Friday)**: input asks "what did my daughter say about friday?" with zero specification of subject matter. The target's narrative says "her plans for this Friday" and the action says "Ask daughter about Friday" -- confirmed, the target invents "plans" as the referent content, which is not in the source. Also confirmed: the corpus's *second* `dangling_reference` record ("Remember to ask her about the earlier version") correctly preserves both ambiguities ("both references are unresolved") -- confirms the audit's "mixed supervision within one category" characterization exactly.
3. **`rapid_topic_switching_incomplete_sentences`**: input has "gas is low" (bare observation) and "call the landlord about." (incomplete, trails off). The target's action list includes "Get gas" and "Call the landlord" -- both promoted to complete, actionable items with the source's incompleteness/observational framing dropped entirely. Confirmed exactly as described.

## My own additional scans (not requested, done to check the audit isn't under-reporting)

- **Invented-causality scan**: searched all 66 targets for "so/because/which means/therefore/since" appearing in the narrative but not the input. Found 5 candidates; read each in full. All 5 turned out to be legitimate paraphrases of causal/purpose language already present (if tersely or implicitly) in the source -- e.g. "shorter agenda probably helped" → "possibly because the agenda was shorter"; "free tier for vacation testing" → "so I can test it remotely during my vacation." No additional invented-causality violations found beyond what's already known from the acceptance-set failures.
- **Object/emotion-attribution scan**: searched all 66 targets for emotion words (tired, exhausted, frustrated, stressed, etc.). Found 6 occurrences; all but the already-flagged sink case correctly attribute the emotion to the first-person writer, matching the source exactly. No new instances of the Probe-11-style object/emotion pattern found.
- **One minor additional observation, not elevated to the same severity**: the `unfinished_reference` record ("blue folder / NOT the old one / after lunch maybe") has no stated verb for the blue-folder fragment and hedges with "maybe" -- the target's action ("Check for the blue folder after lunch") supplies a specific verb and drops the hedge entirely. Milder than the three confirmed concerns (supplying a minimal, neutral verb to an otherwise-verbless fragment is a smaller inference than inventing a whole missing topic like "her plans"), but worth Johnny/ChatGPT being aware of if a full Phase-1 scan of the remaining 63 targets happens -- flagging for completeness, not asking to act on it now.

## Assessment of the audit's conclusions

Agree with the audit's central claim: the failures do not have one common explanation. The evidence supports treating this as (a) genuine curriculum gaps (zero-action either-or, action counts above five), (b) compositional-transfer gaps despite close analogues (dedup, dense composite), and (c) a small number of real target-quality defects that may be contributing to specific regressions (Probe 11) independent of the representation change. Agree with not patching narrowly and not authorizing seed 73 yet.

## Status

No target edits made. No compute performed. No new example authored. Recommend proceeding to a full Phase-1 read of the remaining 63 targets (this verification checked all 66 for the two scanned violation classes, but a full manual policy read akin to the three flagged cases hasn't been done end-to-end) before Phase 2 curriculum design begins.
