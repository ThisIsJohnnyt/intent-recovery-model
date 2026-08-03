# Gold v1.2.2 Target-Integrity Correction Proposal — Claude's Independent Review

**Date:** 2026-08-03
**Reviewing:** `gold_v1.2.2_target_integrity_corrections_design_notes.md`
**Compute performed:** none. **Corpus edits performed:** none.
**Caveat on scope**: I was not given the companion `gold_v1.2.2_target_integrity_corrections_proposal.jsonl` artifact directly -- the exact proposed `output` objects below are reconstructed from the design notes' prose description, not hashed against a byte-exact file. If that JSONL is shared, I'd want to do one final byte-level check before anything is implemented. Everything else in this review (source hashes, current outputs, distribution math, semantic judgment) was checked directly.

## Outcome

**Mostly aligned, with one evidence-based counter-proposal for ti-002**, exactly the kind of disagreement the design notes asked me not to silently accept. ti-001 and ti-003 confirmed as proposed. Implementation safeguards and historical-versioning boundary confirmed sound.

## Hashes and current outputs: all three confirmed exactly

Looked up all three input hashes directly in the pinned corpus (`prompt_contract_v2_migrated_targets_DRAFT.jsonl`) via `prepare_data.input_hash`. All three resolve to exactly the three records I already identified and read in the prior no-compute-audit verification round -- same category, same input text, same current `output`:

- `ti-001` → `dangling_reference` (router firmware / blue folder / daughter's Friday), current B3/A3 -- matches.
- `ti-002` → `rapid_topic_switching_incomplete_sentences` (keys/wallet/phone... lunch with Dana), current B5/A5 -- matches.
- `ti-003` → `standalone_task_retention` (mileage form / sink / Bea), current B4/A2 -- matches.

All three also confirmed to be in the **train** split (not validation) via `split_manifest.json`.

## Distribution tables: confirmed by direct simulation, not just arithmetic-checking

Applied the proposed corrections' final action lists to the real corpus data and recomputed both histograms from scratch:

- Proposed train action-count: `{0:7, 1:22, 2:17, 3:7, 4:7, 5:0}` -- **matches exactly**.
- Proposed full-66 action-count: `{0:8, 1:24, 2:19, 3:8, 4:7, 5:0}` -- **matches exactly**.

Both tables are internally consistent with all three corrections being in the train split (a version where ti-001/ti-002 were in validation would have produced different train-only numbers, which I checked would NOT match the proposal's tables -- confirming the split-membership claim is load-bearing and correct, not just asserted).

## ti-001 (dangling reference): agreed, checked against corpus precedent

Searched the corpus for other bare self-directed questions to see how they're handled elsewhere, since the same "should an unresolved question become an action" issue is what's at stake here. Found a real, pre-existing inconsistency in the corpus: some bare questions get promoted to a "check if X" action (son's-application, pool-cleaning examples) while others are correctly left as unresolved bullets with no action (insurance-payment, vent-or-outside-noise, Rowan's-map, Leah's-photos examples -- four separate records). The "leave unresolved" treatment is the more common pattern, and it's also the one that matches this whole v2 study's own explicit uncertainty-preservation/unsupported-addition-resistance philosophy. "What did my daughter say about Friday?" fits the "leave unresolved" pattern far better than the promoted-question outliers. **Agreed with the proposed correction as described.** (The inconsistency itself, independent of this specific record, is worth carrying into the Phase-1 full 63-target scan -- noted below, not part of this proposal.)

## ti-003 (actor/reaction binding): agreed, no new checks needed beyond the prior round

Already confirmed in the prior verification that the current target's "the dripping sink feels exhausting" is a real, verbatim defect. The proposed fix (bind the reaction to the writer, preserve the sink observation, leave the mileage-form/Bea tasks untouched, B4/A2 unchanged) is exactly the minimal, targeted correction called for. No count changes, so nothing further to check arithmetically. Agreed.

## ti-002: agreed on two of the four action removals, counter-proposal on the other two

Agreed without reservation: removing "Get gas" (promoted from the bare observation "gas is low") and "Call the landlord" (promoted from the explicitly-incomplete fragment "call the landlord about.") from the action list. Both are clean, unambiguous unsupported-promotion fixes, independent of anything below.

**Counter-proposal on "Attend the meeting" and "Lunch with Dana at noon."** The design notes justify keeping both by saying this "follows the existing corpus treatment of terse commitments and scheduled events." I searched specifically for that treatment and did not find it supported:

- `topic_switching` ("printer paper / meeting moved 2 / cat litter / reply Sarah / light bulb kitchen"): the bullet "Meeting moved to 2 p.m." is **not** promoted to an action -- the action list only contains the four items with an actual task attached (buy X, reply to Sarah).
- `abrupt_topic_switching` ("meeting is at 3pm on tuesday bring the q3 report..."): the bare "Tuesday 3 PM meeting" bullet is **not** independently promoted -- only the explicitly-attached task ("bring the Q3 report to the meeting") becomes an action, folded into one item.
- A targeted search for any other "lunch/dinner/coffee with [person] at [time]" pattern anywhere in the 66-example corpus found **no other instance at all** -- ti-002 is the only example of this specific pattern, so there is no actual precedent to "follow" either way.

Both of the closest real precedents in this corpus treat a bare scheduled-event mention (no attached explicit task, no imperative verb) as bullet-only information, not an action. "No the meeting first" is a priority note about an existing commitment, not an instruction to attend; "lunch with Dana at noon" is a calendar entry, not phrased as "meet Dana" or "have lunch with Dana." Neither carries an explicit task the way "bring the Q3 report" or "email Zara the lunch count" do elsewhere in the corpus.

**Proposed stricter alternative**: reduce ti-002's action list to `["Grab keys, wallet, and phone"]` only (this one item does match an established corpus pattern -- bare checklist/shopping-style noun phrases consistently get a supplied minimal verb elsewhere, e.g. "printer paper" → "Buy printer paper," "cat litter" → "Buy cat litter"). This changes ti-002's count from the proposed **B5/A3** to **B5/A1**, which would also shift the corrected distribution tables: train `{0:7, 1:23, 2:17, 3:6, 4:7, 5:0}` and full-66 `{0:8, 1:25, 2:19, 3:7, 4:7, 5:0}` (computed by taking the already-confirmed proposed tables and moving one record from the "3" bucket to the "1" bucket).

This is a genuine disagreement, not a formality -- returning it rather than deciding it myself, per the design notes' own instruction.

## Secondary finding for the later Phase-1 scan (not part of this proposal)

The bare-question-promotion inconsistency found while checking ti-001 (son's-application and pool-cleaning questions promoted to "check if X" actions; insurance-payment, noise-source, map-status, and photo-count questions correctly left unresolved) is worth scanning for explicitly when the remaining 63 targets get their full policy read. Flagging for awareness only, matching this project's existing convention of not mutating anything based on an awareness-only note.

## Implementation safeguards and historical-versioning boundary: agreed

The 10-step safeguard list (load the pinned artifact not the live working copy, require exactly 66 unique inputs, locate by exact hash, require `current_output` match before replacement and fail closed on drift, replace only the three `output` objects, preserve input/category/difficulty/order/split, mechanically regenerate both v1 and v2 targets rather than hand-editing serialized text, parse-verify exact equality, prove exactly three changed, record fingerprints) matches this project's own established fail-closed philosophy exactly (the same pattern `prompt_contract_v2_migrate.py` and `report_benchmark.py`'s structural-integrity checks already use). No changes needed. The "derived candidate corpus, not an overwrite of Gold v1.2.2" boundary is the correct call and consistent with how the historical five-case v1 acceptance set has been treated as immutable evidence all along.

## Status

No corpus edits made. No compute performed. Recommend: Johnny/ChatGPT decide on the ti-002 counter-proposal (A1 vs. A3) before any implementation; everything else in the proposal is ready to proceed once that's settled.
