# Seed-17 v2-Contract Study — Claude's Independent Verification

**Date:** 2026-08-03
**Verifying:** `gold_v1.2.2_seed17_v2contract_chatgpt_scoring_handoff.md` and its two scored artifacts
**Compute performed:** none. All verification done by re-running this project's own already-tested code (`report_benchmark.py`'s `probe_passes`, `verify_v2_structural_integrity`, `verify_rubric_binding`, `evaluate_v2_count_rules`, `v2_result_passes`) against the scored files, and by direct reading of raw outputs.

## Outcome

**Confirmed. No disagreement.** Every mechanical claim in the handoff reproduced exactly via independent recomputation, not just re-read. The one process point ChatGPT flagged for my judgment (semantic scoring's necessity given the count-rule result) — I agree with it.

## What was independently recomputed, not just trusted

Wrote the two scored files to disk, confirmed their SHA-256 hashes match the handoff's stated values exactly (`7e100351...`, `2828a838...`) -- confirms I'm verifying the exact bytes ChatGPT scored, not a paraphrase.

**Protected 16-probe benchmark**, via the real `report_benchmark.py --contract=v2` CLI and directly via its underlying functions:
- Pass count: **11/16**, exact same set (`01,03,04,05,07,09,10,12,13,14,15`) — matches the handoff exactly.
- Every record passed `verify_rubric_binding`/`require_format_valid_is_boolean`/`verify_v2_structural_integrity` without raising -- confirms ChatGPT's scoring pass never touched any protected structural field, only `scores`/`capability_checks`/`failure_labels`.

**Same-seed comparison with Cell A** -- this is the claim I weighted most heavily, since it's the one genuinely new analytical step (not just re-running existing code) and drives the headline "regression" verdict:
- Computed Cell A's actual pass/fail set directly from `gold_v1.2.2_seed17_oldprompt_reference_scored_chatgpt.json` via `probe_passes()`: **10/16**, matching the handoff's stated baseline exactly.
- Confirmed **probe 11 passes in Cell A** and fails in the v2 candidate -- a genuine same-seed regression.
- Confirmed **probe 06 already fails in Cell A** -- so it is *not* a same-seed regression, exactly as ChatGPT stated, contradicting the reporter's own generic warning (which flags both `06` and `11` as "REGRESSION" because that warning only checks "is this regression_guard-status probe currently failing," with no actual comparison to any specific baseline -- it doesn't know what "Cell A" is). Re-ran the real CLI and confirmed it does print both IDs in that warning, exactly as described. ChatGPT's distinction between the reporter's generic label and the study-specific correct comparison is accurate.

**10-case v2 acceptance set**, via the same real functions:
- Count-rule-only pass: **6/10**, exact same set (`sdi2-01,02,03,04,05,09`) — matches the raw provenance I recorded before scoring even happened.
- Semantic-only pass (`probe_passes` alone): **5/10**, exact same set (`sdi2-01,02,05,08,09`).
- Combined (`v2_result_passes`, structural AND semantic): **4/10**, exact same set (`sdi2-01,02,05,09`).
- `sdi2-08`'s semantic-pass-but-structural-fail split checked directly against its raw output: all 8 tasks do appear somewhere across bullets+actions combined (bullets carry 7 of them, actions carry 5, together covering all 8 with no invention or merge) -- so the semantic "nothing lost or invented" checks are correctly satisfied, while the case's own `action_count_rule: exact 8` is correctly failed since only 5 of the 8 appear specifically as actions. This is the layer distinction working as designed, not an inconsistency.

## Spot-checked semantic judgments against raw text directly (not just trusted)

- **Probe 11** (the regression): raw narrative reads "pay the registration fee, which includes the garage light... the garage light is flickering again and feels tired." Confirmed directly: this fabricates a relationship between the registration fee and the garage light that doesn't exist in the source, and attributes tiredness to a light fixture. Real, clear content bug -- Topic Merge/Misattribution/Unsupported Addition all correctly assigned.
- **sdi2-03, sdi2-04**: both narratives insert unearned connective language ("followed by," "so") between genuinely unrelated source facts -- confirmed directly against raw text, matches the Topic Merge / Invented Causality labels.
- **sdi2-06**: two fully invented actions ("Decide between the linen cover and the woven cover," "Finish the photo album") against a source that explicitly states the choice is unresolved -- confirmed, correctly scored 0 on unsupported-addition-resistance.
- **sdi2-10**: confirmed the "Before Saturday" deadline is completely absent from both narrative and actions in this generation (`DEADLINE_SURVIVED: false` is correct), and confirmed bullet 5 ("The two finished bowls are still unclear whether the courier counted the cracked tiles") is a genuinely garbled merge of two distinct source ideas (packing the bowls; the unresolved tile-count question) into one incoherent bullet. One score I'd call borderline rather than clearly right or wrong: `attribution_accuracy: 1` -- the surviving attribution phrasing itself ("the studio coordinator said...") reads correctly to me in isolation; the partial-credit score seems to reflect the surrounding confusion more than a specific attribution error I can independently pinpoint. Not raising this as a disagreement -- a defensible holistic call on a case that's already failing on multiple independently-confirmed grounds (count rule, dropped deadline, garbled bullet), not a load-bearing judgment.

## Process point: agreed

ChatGPT's flagged observation is correct: `v2_result_passes()` is `probe_passes(result) and evaluate_v2_count_rules(...)` -- a strict AND, so combined pass can never exceed count-rule pass. Once the raw (pre-semantic-scoring) provenance recorded 6/10 count-rule satisfaction, "all 10/10 v2 acceptance cases pass" was already mathematically foreclosed, independent of any semantic judgment. This doesn't make semantic scoring unnecessary overall -- the protected-benchmark-vs-Cell-A comparison and the regression-guard-preservation gate both genuinely required it, and the failure-mode detail (which of the ten cases fail on what basis) is exactly what makes this result useful for the next design decision rather than just a number. It specifically means the *acceptance-set* sub-gate's outcome was knowable earlier than it was formally confirmed. Agreed, no disagreement.

## Verdict

Seed 17 does not clear the frozen gate. Confirmed independently on every measurable dimension. Seed 73 remains blocked. Recommend proceeding to ChatGPT's proposed next step (no-compute coverage audit of the 66-example corpus against the observed failure families) once Johnny reviews this closure.
