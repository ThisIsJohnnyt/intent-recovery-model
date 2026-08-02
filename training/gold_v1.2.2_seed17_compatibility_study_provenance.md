# Seed-17 prompt-contract compatibility study — provenance record

**Run date:** 2026-08-02
**Authorization:** `seed17_prompt_contract_compute_authorization_handoff.md` (Johnny, seed-17 A/B2/C triplet only)

## Repository state

- `main` at merge commit `ee4774654c400014fd027aab0f4c24910f907b1a` (PR #15, reviewed head `16a03dafac1bdbc652b760b545206faed7342c1e`)
- Old-prompt code pin: `8d7aa0924b61b2a4c583728413994c792b75708f` (worktree `../irm-study-old-prompt`)
- New-prompt code pin: `80062bcfbb4cc5f3c788a22454f7ec24b69e3b2f` (worktree `../irm-study-new-prompt`)
- Both pins verified as the exact commit checked out in their respective worktrees before any cell ran.

## Prompt-contract fingerprints (recomputed, not assumed)

- Old contract: `b325c0640db95f238ac97cc4b254db6347df78144fed0ddb2e6a084bba20e4c5` — matched expected exactly.
- New contract: `161661198071fd81310681f69381ec8e0287141e1e75b09d3a342414af31ccf1` — matched expected exactly.
- New `PROMPT_CONTRACT_VERSION`: `source-determined-bullets-v1` — matched expected exactly.

## Dataset / split identity

- Source: `git show 8d7aa09:datasets/synthetic.jsonl` (gold_v1.2.2-complete, 66 lines, pinned — not the working tree's copy, which carries an unrelated pending gold_v1.2.3 hunk).
- Split: `training/split_manifest.json` (unmodified, on merged main) → **60 train / 6 val**, confirmed exactly.
- New-prompt processed copy written to `training/data/processed_gold_v1.2.2_control_newprompt/` (fresh, not overwriting the existing old-prompt copy at `training/data/processed_gold_v1.2.2_control/`).

## Seed / training

- Seed: **17**
- Hyperparameters: unchanged from `train.py` defaults (40 epochs, batch size 4, `google/flan-t5-base`, lr 3e-4) — only `--seed`/`--output-dir`/`--data-dir` passed.
- Terminal step: **600/600** (`100%|##########| 600/600`, `epoch: 40.0`) — exact match to the frozen expectation, no early stop, no truncation.
- `train_loss`: 0.1489946226713558; `train_runtime`: 803.7s (~13.4 min).
- Val-set (6 examples) format check at save time: 6/6 well-formed marker sections.
- Output directory `training/checkpoints/gold_v1.2.2-newprompt-seed17/` did not exist before this run — created fresh, `--force` never needed/used.

## Checkpoints

| Role | Path | `checkpoint_fingerprint` |
|---|---|---|
| Cell A/B2 (existing, seed-17 control) | `training/checkpoints/gold_v1.2.2-seed17-control/checkpoint-600` | `ec33ea1fb684c2b6f3854ef7261bfc141fd00185f82da2d5c8e1efcc02241044` |
| Cell C (new, seed-17 candidate) | `training/checkpoints/gold_v1.2.2-newprompt-seed17/final` | `86689b18d21f734c3a41414b379d4ce5ec3623dd1c8e007cb7ccf26f3d761f3c` |

**Cell A and Cell B2 used the identical checkpoint** — same path, same fingerprint, only the prompt code (old vs. new worktree) differed between the two runs.

## Cells run and results

| Cell | Command | Checkpoint | Prompt | Result file | Format validity |
|---|---|---|---|---|---|
| A | `run_benchmark.py` (old-prompt worktree) | seed-17 control (existing) | old | `training/gold_v1.2.2_seed17_oldprompt_reference_results.json` | 16/16 |
| B2 | `run_benchmark.py` (new-prompt worktree) | seed-17 control (existing, same as A) | new | `training/gold_v1.2.2_seed17_newprompt_deployment_risk_results.json` | 16/16 |
| C (16-probe) | `run_benchmark.py` (new-prompt worktree) | seed-17 candidate (new) | new | `training/gold_v1.2.2_seed17_newprompt_candidate_results.json` | 16/16 |
| C (acceptance) | `run_benchmark.py` (new-prompt worktree) | seed-17 candidate (new) | new | `training/gold_v1.2.2_seed17_newprompt_candidate_bullets_acceptance_results.json` | 5/5 |

**All four format-validity numbers are automatic structural checks only** (marker presence/ordering) — not semantic pass rates and not a release decision. Every score/capability-check field in all four result files is still `null`, exactly as `run_benchmark.py` scaffolds them, ready for independent semantic scoring (ChatGPT) and Claude's independent verification per the handoff doc.

## Out of scope, not run

Per the authorization: Cell B1/`run_benchmark_onnx.py` (checkpoint-520), seed-73, seed-42 training or use as a controlled comparator, merging `thought-organizer-app` PR #4, any export/quantization/release/deployment, and any wording/rubric/prompt-contract change.

## Deviations / warnings

**Correction (2026-08-02, after ChatGPT's scoring pass): one real deviation, found and fixed post-hoc.** All four raw result files were missing `required_semantic_dimensions`. Root cause, independently confirmed: `run_benchmark.py` at both pinned commits (`8d7aa09` and `80062bc`) predates the `required_semantic_dimensions` propagation code, which was added later in commit `8a23316` (PR #15's own Round 3 fix) — after both pin points existed. The worktree design pins `training/prepare_data.py`'s prompt wording correctly, but since each cell invoked `run_benchmark.py` *from the same worktree*, it also inadvertently pinned that file to a version that predates a later, unrelated improvement to the same repo. This is a gap in the manifest's runner/prompt-contract pinning boundary, not a command-execution error — the authorized commands were followed exactly.

**Repair applied, verified safe**: ChatGPT hydrated `required_semantic_dimensions` into scored copies of all four result files, by probe ID, from the frozen merged benchmark files (`gold_v1.2.1_probes.jsonl`, `source_determined_bullets_acceptance.jsonl`). Independently confirmed programmatically: (1) every hydrated value matches the canonical committed mapping exactly, for all 53 records across all four files; (2) `id`/`category`/`kind`/`status`/`raw_output`/`format_valid`/capability-check key sets are byte-identical to the original unscored files — no raw model output or structural field was altered, only metadata and score values were added. No re-run of any cell was needed or performed; this field has no effect on generation, only on scoring.

**Recommended fix for future runs** (not yet implemented, deferred pending the next-design decision): separate the pinned prompt-contract builder from the benchmark runner in the manifest, or add an explicit metadata-hydration step, so pinning an old commit for prompt wording can't silently pin away current benchmark-runner behavior again.

All other preflight/execution checks held with no deviation: both worktrees created cleanly at the exact pinned commits; both fingerprints matched expected values exactly; the existing seed-17 checkpoint was present; the Cell C output directory was new and empty; the regenerated split was exactly 60/6; training finished at exactly 600/600 steps; no cell errored; no retries were needed.

One pre-existing condition noted for transparency, not treated as a stop condition: the repository has long-standing, unrelated uncommitted work (`datasets/synthetic.jsonl`'s pending gold_v1.2.3 hunk, `docs/datasets/CATEGORY_REFERENCE.md`, and several untracked gold_v1.2.3 files) that has been present throughout this entire session. Every file this study actually reads or writes (`split_manifest.json`, `prepare_data.py`, the manifest, the two benchmark files, `train.py`, `report_benchmark.py`, `run_benchmark.py`) was confirmed clean. Cell C's data-regeneration step reads `datasets/synthetic.jsonl` via a pinned `git show 8d7aa09:...` reference, not the live working-tree file, so the pending hunk could not have contaminated this run regardless.

## Worktree cleanup

Both `../irm-study-old-prompt` and `../irm-study-new-prompt` removed after this record was written and all four result files confirmed on disk.

## Outcome (added 2026-08-02, after independent scoring and verification)

**The seed-17 candidate does not clear the compatibility-study bar.** ChatGPT scored all four result files independently; Claude independently re-verified the scoring rather than accepting it at face value -- see `gold_v1.2.2_seed17_compatibility_study_chatgpt_scoring_handoff.md` and the four `*_scored_chatgpt.json` files (all now in this directory) for the full record.

| Gate | Result |
|---|---|
| 1. Cell C 16/16 format validity | PASS |
| 2. No Cell-A regression-guard pass becomes a Cell-C failure | **FAIL** (probe 11: passes in A, fails in C -- invents "pay garage light" as an unsupported action) |
| 3. Cell C overall strict passes >= Cell A | PASS (10/16 both) |
| 4. All 5 acceptance gates pass | **FAIL** (1/5 -- only sdb-03) |

**Independent verification performed, not just the arithmetic taken on faith**: recomputed all four gate results via `report_benchmark.py` directly against ChatGPT's scored files (exact match: A=10/16, B2=10/16, C=10/16, acceptance=1/5); recomputed the exact pass sets and confirmed the probe-11 flip is the only regression-guard flip; confirmed the claimed "14/16 byte-identical, 2 cosmetic diffs" between Cell A and B2 raw outputs by direct string comparison; independently re-read the raw outputs against each probe's `expected_behavior` for every gate-critical and self-flagged-as-judgment-sensitive item (probe 11, all 5 acceptance cases, probes 06/08/16) and reached the same conclusions ChatGPT did in every case, including confirming that even reversing the two most debatable acceptance calls (sdb-02, sdb-05) would still leave the acceptance gate at 3/5, short of the required 5/5. No disagreement found.

**Recommendation carried forward, not yet acted on**: do not run seed-73 under this design; do not merge/deploy `thought-organizer-app` PR #4; next-design decision (address the specific failures exposed here, or revise the prompt-contract approach) still needs Johnny's call before further compute.
