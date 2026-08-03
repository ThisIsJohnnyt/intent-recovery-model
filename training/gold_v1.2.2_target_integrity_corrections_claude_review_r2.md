# Gold v1.2.2 Target-Integrity Correction Proposal — Revision 2 — Claude Final Review (File Hash + Structural Verification)

**Date:** 2026-08-03
**Reviewing:** `gold_v1.2.2_target_integrity_corrections_design_notes_r2.md` + companion `gold_v1.2.2_target_integrity_corrections_proposal_r2.jsonl`
**Compute performed:** none (model). **Corpus edits performed:** none.
**Scope:** this closes the byte-level gap flagged in the prior review — the companion JSONL is now in hand and was checked directly, not reconstructed from prose.

## Outcome

**Fully confirmed, no remaining disagreement.** Every mechanical and semantic claim in Revision 2 checks out against the pinned corpus. Ready for implementation sign-off from Johnny; no further review-side blockers.

## File integrity

- SHA-256 of `gold_v1.2.2_target_integrity_corrections_proposal_r2.jsonl` = `dfb4a001d73c49714fb72f02574c5b00120262cb032251e3e3e232992dde8097` — matches the value declared in the r2 design notes exactly.

## Hash resolution and current-output equality (direct simulation, not spot-check)

Loaded `prompt_contract_v2_migrated_targets_DRAFT.jsonl` (confirmed 66 records, 66 unique `input` strings) and `split_manifest.json`, then resolved all three `record_input_sha256` values by recomputing `sha256(input)` over every pinned record:

| ID | Resolves to (index, category) | Split | `current_output` structurally equal (parsed JSON) to pinned `output` |
|---|---|---|---|
| ti-001 | idx 15, `dangling_reference` | train | **True** |
| ti-002 | idx 38, `rapid_topic_switching_incomplete_sentences` | train | **True** |
| ti-003 | idx 52, `standalone_task_retention` | train | **True** |

No drift between the `current_output` recorded in the proposal and the actual pinned corpus content. All three confirmed outside `split_manifest.json`'s `val` list (train split), consistent with both prior rounds.

## ti-002 resolution: confirmed applied as I proposed

`proposed_output.action_items` = `["Grab keys, wallet, and phone"]` exactly — matches my counter-proposal from the prior review verbatim, not the original ChatGPT A3 proposal. Also confirmed directly against the parsed JSON: `narrative` and all 5 `bullets` are value-identical (Python equality on the parsed structures, not a raw-byte comparison of source text) between `current_output` and `proposed_output` for ti-002 — only the action list was narrowed, as the design notes claimed.

## Count deltas: recomputed independently, all match

| ID | current B/A | proposed B/A | declared Δ | recomputed Δ |
|---|---:|---:|---:|---:|
| ti-001 | 3/3 | 3/2 | b=0, a=−1 | b=0, a=−1 ✓ |
| ti-002 | 5/5 | 5/1 | b=0, a=−4 | b=0, a=−4 ✓ |
| ti-003 | 4/2 | 4/2 | b=0, a=0 | b=0, a=0 ✓ |

## Distribution tables: reproduced by full corpus simulation

Applied all three corrections to the actual 66-record pinned corpus in memory (not arithmetic-checking the claimed tables) and recomputed both histograms from scratch:

- **Train (60) proposed:** `{0:7, 1:23, 2:17, 3:6, 4:7, 5:0}` — matches r2 table exactly.
- **Full (66) proposed:** `{0:8, 1:25, 2:19, 3:7, 4:7, 5:0}` — matches r2 table exactly.

Current-state baselines from the same simulation (`train {0:7,1:22,2:16,3:7,4:7,5:1}`, `full {0:8,1:24,2:18,3:8,4:7,5:1}`) also match the "Current" columns in both prior rounds' tables, confirming no unrelated corpus drift crept in between rounds.

## Structural sanity checks

- Exactly 3 corrections resolved and applied — no silent 4th match, no missed match.
- 3 unique `proposal_id`s, 3 unique input hashes — no duplicates within the r2 file.
- Corpus confirmed at exactly 66 unique inputs (safeguard #2 precondition satisfied).

## Status

All three corrections (ti-001, ti-002 at A1, ti-003) are verified against the pinned Gold v1.2.2 corpus via exact file-hash checking (companion JSONL) and structural/value equality checking on parsed JSON (current/proposed outputs, count deltas, distribution tables). No corpus edits or compute performed in this review. The only remaining step is Johnny's explicit authorization to run the corpus-derivation tool per the 9-step safeguard list already agreed in both prior rounds — nothing in this review changes or adds to those safeguards.
