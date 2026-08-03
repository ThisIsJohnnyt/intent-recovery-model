# Controlled Seed-17 R2 Replay — Claude Independent Verification

**Date:** 2026-08-03
**Scope:** Independent record-by-record re-verification of ChatGPT's semantic scoring
(`controlled_seed17_r2_replay_chatgpt_semantic_scoring_review.md`) against the raw replay outputs
and the frozen rubric. No training, inference, seed 73, export, deployment, or activation
performed. **Not committed** — held per Johnny's instruction pending this verification and any
disagreement being surfaced.

## 1. Artifact integrity — CONFIRMED, no discrepancy

- Both scored files, written to disk exactly as attached, hash to the values ChatGPT's review
  reported: `controlled_seed17_r2_replay_protected16_scored_chatgpt.json` →
  `2a887f4fa5de674ade0db735361486b19938dca1479f0b66127488c57f33bddd`;
  `controlled_seed17_r2_replay_acceptance10_scored_chatgpt.json` →
  `b3a43497cdec6e501118592808be0d750af7ccb818ae97738d7818a8f65238a3`. Exact match, both files.
- Programmatically confirmed against the raw replay result files
  (`controlled_seed17_r2_replay_run/{protected16,acceptance10}_results.json`): record order and
  IDs identical; `raw_output` byte-identical in every record (source evidence untouched); the
  *only* fields that differ from the raw scaffold are `scores`, `capability_checks`, and
  `failure_labels` — no other field was altered.
- Every `required_semantic_dimensions` entry is non-null in both scored files (no vacuous-pass
  gap). Every `capability_checks` value is a literal boolean (no stray nulls/strings).
- The real, unmodified `report_benchmark.py --contract=v2` accepts both files without error and
  independently re-verifies their full v2 structural package (this is what
  `verify_v2_structural_integrity` does on every call — confirmed by the reporter running to
  completion rather than raising).

## 2. Reporter aggregate table — INDEPENDENTLY RECOMPUTED, matches exactly

Ran the real reporter against all four scored files (replay ×2, baseline ×2). Every one of
ChatGPT's six claimed measures matches exactly:

| Measure | Baseline | R2 candidate | Change | Verified |
|---|---:|---:|---:|---|
| Protected format validity | 16/16 | 16/16 | — | ✓ exact |
| Acceptance format validity | 10/10 | 10/10 | — | ✓ exact |
| Acceptance count-rule conformance | 6/10 | 7/10 | +1 | ✓ exact |
| Acceptance combined strict pass | 4/10 | 6/10 | +2 | ✓ exact |
| Protected strict pass | 11/16 | 11/16 | — | ✓ exact |
| Protected regression guards passed | 10/12 | 9/12 | −1 | ✓ exact |

## 3. Same-seed pass-set diff (protected-16) — CONFIRMED, with one correction to the reporter's own generic warning

Computed the *actual* same-seed pass-set diff directly (`v2_result_passes()` per probe, baseline
vs. replay), not the reporter's generic "regression_guard status + currently failing" warning
line — which is known to over-flag (the exact same caveat the original seed-17 study's own
provenance already documented for probe 06 vs. Cell A).

- Reporter's generic warning line: `['10', '11', '13']` (3 IDs)
- **Actual same-seed regressions** (baseline passed, replay fails): `['10', '13']` — matches
  ChatGPT's specific claim exactly.
- **Actual same-seed new passes** (baseline failed, replay passes): `['06', '16']` — matches
  ChatGPT's specific claim exactly.
- Probe `11` is a false positive in the generic warning: it already failed in the baseline run too
  (confirmed: `11` is absent from the baseline pass set), so it is not a same-seed regression,
  exactly the same pattern the original study found for probe `06` against Cell A.

## 4. Acceptance-10 count-rule and combined-pass transitions — CONFIRMED exactly

- Count-rule conformance gain is `sdi2-06` only — confirmed.
- Combined strict-pass gains are `sdi2-03` and `sdi2-04` only, with zero combined-pass losses —
  confirmed. `sdi2-08` independently confirmed to fail its action-count rule in both baseline and
  replay (6/8 actual vs. 8 required in both), so it was never a candidate for a combined-pass
  change either direction.

## 5. Case-by-case semantic re-verification (all 26 cases read directly against raw_output + expected_behavior + primary_checks)

**25 of 26 scores/judgments independently confirmed correct and well-evidenced.** Spot detail on
the ones with the most riding on them:

- **Protected 13** (true regression, confirmed): baseline's `parsed_actions` genuinely contained
  both tasks (`["Pick up cat food after work", "Email the signed form to the school"]`); replay's
  contains only one. The email task is present in narrative/bullets but silently dropped from
  actions — a real, visible regression. `topic_completeness=1` justified.
- **Protected 06 / 16** (true new passes, confirmed): both read cleanly against their
  `expected_behavior` — ambiguity explicitly preserved in `06` ("does not make clear whether Tessa
  or the inspector..."), no invented referent in `16` ("someone"/"the other one" both stay
  unresolved, bullet even states "both references are unresolved"). Full-2 scores justified.
- **Acceptance sdi2-03 / sdi2-04** (combined-pass gains, confirmed): both are genuine textual
  improvements over baseline, not scoring artifacts — baseline's `sdi2-03` used "followed by,"
  implying a spurious sequence between two unrelated observations; replay uses a flat "and."
  Baseline's `sdi2-04` used "so," implying a causal link between an observation and an unrelated
  task; replay uses "Separately." Both invented-relationship defects are visibly gone in the
  replay text.
- **Acceptance sdi2-08** (severe fail, confirmed and if anything under-flagged rather than
  over-flagged): direct comparison against the source's 8 explicit tasks shows two are actually
  corrupted — "mail the library donation form" becomes "the library donation form needs to be sent
  **to me**" (a genuine misattribution, reversing who sends the form to whom, and dropped from
  actions entirely), and "freeze the berry puree" is **completely absent** from the output — not
  in bullets, not in actions, not in narrative. `ALL_EIGHT_TASKS_SURVIVED=false`,
  `NO_INVENTED_TASK=false`, and the Misattribution/Topic Loss labels are all justified.

### One disagreement, flagged rather than silently accepted or overruled

**Protected probe 10** (`buried_task_retention`, `regression_guard`) — ChatGPT scored
`unsupported_addition_resistance=1` with an "Excessive Fragmentation" failure label, causing this
probe to fail (it is otherwise the only dimension keeping it from a full pass).

Raw output: *"...although the final scene still dragged. Separately, the shipping label needs to
be printed, **but the final scene still dragged**."* — the clause "final scene still dragged" is
stated twice in the narrative (confirmed by direct string count: appears 3 times total across the
whole output — twice in the narrative, once in its own bullet). This is a real, visible defect.

My disagreement is about *which* dimension/label it belongs to, not whether it's a defect:

- The repeated clause is **not new or unsupported content** — it's a literal duplicate of a fact
  that genuinely is in the source input and is already correctly present once in the bullets. It
  doesn't invent anything false. `unsupported_addition_resistance` scoring a 1 for a duplicate of
  already-supported content seems like the wrong dimension for this specific defect.
- "Excessive Fragmentation" — as used elsewhere in this exact scoring round (e.g., protected `02`)
  — describes splitting one coherent idea into multiple separate bullet/action items. Probe 10's
  bullets (4 items) and actions (1 item, correct) don't show that pattern; the repetition is
  confined to free-form narrative prose repeating itself, not structural over-splitting.

If `unsupported_addition_resistance` were scored 2 instead (repetition-of-supported-content isn't
"addition" in the sense this dimension is designed to catch), probe 10 would pass, which would
change the same-seed regression set from `{10, 13}` to `{13}` only, and the protected strict-pass
count from 11/16 (unchanged vs. baseline) to 12/16 (an improvement over baseline's 11/16).

**This does not change the overall gate outcome** (see §6 below) — gate 6 (same-seed regression
preservation) still fails on probe `13` alone regardless of how probe `10` is resolved, since the
gate's rule is "no baseline-passing guard may newly fail," and even one violation fails it. I'm
recording this as a genuine, evidence-based disagreement to return per the project's standing
protocol, not silently accepting ChatGPT's label or silently overruling it in the scored file.

## 6. Six-gate application (using the protocol's own text, not summarized from memory)

Re-read `controlled_seed17_r2_replay_protocol.md` §8 directly rather than relying on a prior
summary. Applying the six frozen gates from the manifest's §2 "Acceptance gate" row to the
verified numbers above (using ChatGPT's scoring as recorded, since the probe-10 disagreement does
not change the outcome either way):

| # | Gate | Requirement | Result | Status |
|---|---|---|---|---|
| 1 | Protected-16 format validity | 16/16 | 16/16 | **PASS** |
| 2 | Acceptance-10 format validity | 10/10 | 10/10 | **PASS** |
| 3 | Acceptance-10 count-rule conformance | 10/10 | 7/10 | **FAIL** |
| 4 | Acceptance-10 combined strict pass | 10/10 | 6/10 | **FAIL** |
| 5 | Protected-16 strict pass vs. Cell A (baseline) | candidate ≥ baseline | 11/16 vs. 11/16 | **PASS** |
| 6 | Same-seed regression-guard preservation | no baseline pass may newly fail | probes 10, 13 regressed (13 alone survives the probe-10 disagreement) | **FAIL** |

Three of six gates fail. This is **not a full gate pass** (Outcome A requires all six).

## 7. Outcome classification: **Outcome B — Improvement without a full pass**

Distinguishing B from C per the protocol's own text: Outcome C is for a "neutral or worse result";
Outcome B is for genuine, measurable improvement that still falls short of a full pass. This run
shows real, verified improvement (acceptance count-rule +1, combined strict pass +2, two
genuinely-fixed invented-relationship defects on sdi2-03/04) with no *net* worsening on the
protected side (11/16 unchanged at minimum, arguably 12/16 under the probe-10 disagreement) — not
neutral-or-worse. **This is Outcome B, not C.**

Per the protocol's own Outcome B actions:
- Accept the result as evidence that the R2 target corrections mattered but were insufficient
  alone to clear the frozen gate.
- Use only the residual, evidence-supported failure classes (from this round's case-by-case
  reading — e.g., unresolved-choice framing on sdi2-06, restated-task deduplication on sdi2-07,
  high-count generalization on sdi2-08, deadline/bullet-count loss on sdi2-10, plus the protected
  set's persistent attribution/completeness misses) to design a Phase-2 balanced curriculum
  proposal, if that direction is chosen.
- **Do not begin Phase-2 training without a new static review and separate authorization** — this
  verification does not authorize anything beyond itself.

## 8. Explicit non-authorizations (unchanged)

This verification does not authorize: seed 73, a Phase-2 curriculum, scorer or gate changes, use
of Gold v1.2.3, export, deployment, activation, or production promotion. Nothing in this round has
been committed; the scored files, this verification, and the six-gate/outcome conclusion all await
Johnny's review, including the probe-10 disagreement above.

## Addendum: probe-10 disagreement resolved, revised figures mechanically confirmed (2026-08-03)

ChatGPT accepted the probe-10 correction from §5 in full: `unsupported_addition_resistance`
corrected `1` → `2`, `failure_labels` corrected `["Excessive Fragmentation"]` → `[]`. Independently
confirmed this is the *only* change between rounds — reconstructed the revised
`controlled_seed17_r2_replay_protected16_scored_chatgpt.json` by editing exactly those two fields
on probe `10` in the file already on disk, and its SHA-256 came out to
`240b4ce35a6df9352f3bc41749468b3d111041f9b910efa811ac41db36a4e4ca`, an exact match to ChatGPT's
claimed hash — not assumed from the review doc, computed directly.
`controlled_seed17_r2_replay_acceptance10_scored_chatgpt.json` is confirmed byte-identical
(`b3a43497...`, unchanged) since no disagreement touched it.

Reran the real, unmodified `report_benchmark.py --contract=v2` against both revised files (not
inferred algebraically from the probe-10 change):

- Protected strict pass: **12/16** (was 11/16 pre-resolution and at baseline; net +1 over baseline).
- Protected regression guards passed: **10/12** (was 9/12 pre-resolution; now equal to baseline's
  10/12).
- Reporter's generic REGRESSION warning line is now `['11', '13']` (probe `10` dropped out, as
  expected). `11` remains a false positive for the same reason established in §3 — it already
  failed in the baseline run, so it isn't a same-seed regression. **True same-seed regression:
  probe `13` only.**
- Acceptance-10 reconfirmed unchanged: combined strict pass **6/10**; count-rule-only conformance
  **7/10**, recomputed directly from each record's `bullet_count_result`/`action_count_result`
  fields (non-conforming: `sdi2-07`, `sdi2-08`, `sdi2-10` — matches the pre-resolution figure
  exactly, since probe 10's dimension isn't a count-rule field).

### Revised six-gate table

| # | Gate | Requirement | Result | Status |
|---|---|---|---|---|
| 1 | Protected-16 format validity | 16/16 | 16/16 | **PASS** |
| 2 | Acceptance-10 format validity | 10/10 | 10/10 | **PASS** |
| 3 | Acceptance-10 count-rule conformance | 10/10 | 7/10 | **FAIL** |
| 4 | Acceptance-10 combined strict pass | 10/10 | 6/10 | **FAIL** |
| 5 | Protected-16 strict pass vs. baseline | candidate ≥ baseline | 12/16 vs. 11/16 | **PASS** |
| 6 | Same-seed regression-guard preservation | no baseline pass may newly fail | probe 13 regressed | **FAIL** |

Still three of six gates fail (1, 2, 5 pass; 3, 4, 6 fail) — **Outcome classification unchanged:
Outcome B, improvement without a full pass**, now on slightly stronger evidence than the
pre-resolution reading (a clean net +1 protected strict-pass gain over baseline, not a wash).

This resolution is recorded in the revised `controlled_seed17_r2_replay_chatgpt_semantic_scoring_review.md`
and the revised `controlled_seed17_r2_replay_protected16_scored_chatgpt.json`. All non-authorizations
above remain unchanged. Per Johnny's explicit approval, this round — provenance, raw/scored
results, and both review records — is being committed. The checkpoint directory and the three raw
execution-log files are being deliberately excluded: no checkpoint or `.log`-pattern training
artifact has ever been committed anywhere in this repository's history (confirmed via `git ls-files`),
and `training/.gitignore` already encodes that intent (`checkpoints/`, `*.log`) even though this
run's specific paths (`controlled_seed17_r2_replay_run/checkpoint/`, `*_log.txt`) fall outside the
exact patterns by naming/path coincidence.
