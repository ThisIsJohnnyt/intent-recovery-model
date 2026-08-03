# Session Handoff — 2026-08-03 (post Gold v1.2.2 Revision-2 closure)

Written at Johnny's request to bridge to a new chat session, following his
stated preference to start a fresh session after each major milestone
closes. This is a snapshot, not a replacement for `training/phase_e_remaining_sequence.md`,
which has the full blow-by-blow history — read that for detail on anything
summarized here.

## What just closed (no further action needed)

**Gold v1.2.2 target-integrity audit + Revision-2 corpus derivation — fully closed.**

- Three real target defects in the pinned 66-example `gold_v1.2.2` corpus
  were found (no-compute audit), corrected via a two-round proposal
  (ti-001, ti-002, ti-003), and derived into a separately-fingerprinted
  candidate corpus — never overwriting the original.
- Claude's evidence-based counter-proposal on ti-002 (reduce to a single
  supported action, B5/A1, not ChatGPT's original B5/A3) was accepted
  outright in Revision 2.
- The derivation tool (`training/gold_v1.2.2_r2_derive_corpus.py`) applies
  the 3 corrections to the pinned corpus (loaded read-only from immutable
  commit `8d7aa09`) under a 9-step safeguard list, produces
  `training/gold_v1.2.2_r2_derived_candidate.jsonl` (66 records, exactly 3
  changed), and a provenance report. ChatGPT independently re-derived and
  confirmed every fingerprint; one wording overstatement ("byte-identical"
  where the code actually does parsed-JSON structural equality) was
  caught, fixed at the source, and re-verified.
- Johnny confirmed closure: **Gold v1.2.2 remains immutable, the derived
  candidate is accepted for future evaluation, no training/inference/benchmark
  is authorized by that confirmation.**
- **Committed and pushed**: commit `1c9120322c50d8f95ca5e82820be08fac77fa98a`
  (`1c91203`) on `main`, confirmed present on `origin/main`. 8 files, pure
  addition (678 insertions, 0 deletions to any existing tracked file).
  Gold v1.2.2 immutability verified two ways: `git diff 8d7aa09 HEAD --
  datasets/synthetic.jsonl datasets/gold/gold_v1.2.2.jsonl` is empty, and
  both files' git blob hashes are identical at `8d7aa09` and `1c91203`.

**Nothing further is owed on this thread.** The derived candidate exists
and is accepted, but has not been used for anything yet — no training run,
no inference, no benchmark against it. Using it for anything is a new,
separate authorization decision.

## Repo state right now

- Branch: `main`, HEAD = `1c91203`, matches `origin/main` exactly (verified
  by fetch).
- **Pre-existing, unrelated uncommitted changes** (not touched by the r2
  work, not part of any thread in this handoff's living memory):
  - `datasets/synthetic.jsonl` — modified (+6 lines), predates this
    session by several days (confirmed via file mtime).
  - `docs/datasets/CATEGORY_REFERENCE.md` — modified (+8/-1 lines).
  - A substantial **untracked `gold_v1.2.3` body of work** sitting in the
    working tree: `datasets/gold/gold_v1.2.3.jsonl` and its
    curriculum/design-notes/lessons-learned/review-report quartet, plus
    `training/gold_v1.2.3_seed_stability_study.md`,
    `gold_v1.2.3_seed_study_manifest.md`, `gold_v1.2.3_split_delta_report.md`,
    `gold_v1.2.3_probe02_reduced_diagnostic.md`,
    `gold_v1.2.2_vs_v1.2.3_control_comparison.md`, several benchmark-result
    JSON files (seed17/seed73/checkpoint680), `training/phase_d_review_packet.md`
    (real-validation/sealed-holdout PDR-004 review artifact), and a large
    `training/data/processed_gold_v1.2.3_*`/`processed_gold_v1.2.2_*` tree
    of prepared train/val splits.
  - This work is dated **2026-07-30** (per its own lessons-learned doc) —
    it predates the entire v2 typed-marker prompt-contract effort and this
    conversation's involvement. Its own conclusion was **net-negative and
    not promoted** (`gold_v1.2.3`/checkpoint-680 dropped to 11/16 vs.
    `gold_v1.2.2`/checkpoint-600's 13/16) — already documented in its own
    `gold_v1.2.3_lessons_learned.md`.
  - **This has never been reviewed, committed, or explicitly disposed of
    in this conversation.** A new session should ask Johnny directly
    whether it should be committed as historical record, or whether it's
    intentionally being left uncommitted/superseded. Do not delete or
    silently commit it without asking.

## Active thread: v2 typed-marker prompt contract

- Typed `###BULLET###`/`###ACTION###` markers replaced bare newlines as
  the item-boundary representation, motivated by an empirically-confirmed
  root cause (FLAN-T5's SentencePiece tokenizer destroys all newline
  information on encode/decode — 0/N survive round-trip).
- Seed-17 v2-contract study (first real compute of the whole vNext
  effort) ran and was **scored as a gate failure** (commit `e37aeda`):
  representation itself works (26/26 outputs parse-valid), but content
  behavior (unsupported action invention, dedup failures, high-count
  generalization, attribution drift) still falls short of the frozen
  acceptance gate. **Seed 73 remains explicitly blocked.**
- The just-closed target-integrity thread (above) grew directly out of
  this seed-17 postmortem — 3 of the corpus's own targets were teaching
  some of the exact failure patterns observed.
- **Not yet decided**: whether the next step is a Phase-2 balanced
  curriculum design (adding genuinely-supported A5–A8 examples, more
  zero-action either/or forms, etc.) built against the now-accepted r2
  corrected corpus, or something else. No further v2 compute is
  authorized.

## Phase E overall status (see `phase_e_remaining_sequence.md` for full detail)

Steps 1–3 (scoring-lineage/withdrawal design + implementation + review)
are done and merged (`8d7aa09`). Step 4 (prompt-contract sync) is the v2
typed-marker effort above — still open, not resolved. Steps 5–7 (joint
Phase E readiness review, Johnny approval, validation-only real-data
pilot) are **not started**.

## thought-organizer-app (companion repo)

- PR #4 (v1 prompt-contract activation) was **closed as superseded**.
- The v2-candidate static feasibility package landed directly on `main`
  (commit `732fafb`), bypassing PR #4 — flagged, not resolved as a git
  hygiene issue, but confirmed non-production-impacting (no deployment
  pipeline exists yet per the app's own `ROADMAP.md`).
- No new app-side work has happened since; nothing currently blocks this
  chat's other threads on the app side.

## Collaboration protocol, unchanged

Claude independently re-verifies every claim ChatGPT makes against the
actual code/data before agreeing or fixing anything — never trusts a
line number, hash, or description at face value. Disagreements get
returned to Johnny explicitly, never silently resolved or overruled in
either direction. This pattern held through every round of the
just-closed thread (multiple real ChatGPT findings confirmed accurate,
one Claude counter-proposal accepted, one Claude reporting error
self-corrected).

## Gates currently in force (nothing here has changed)

- Gold v1.2.2 (`datasets/synthetic.jsonl`, `datasets/gold/gold_v1.2.2.jsonl`):
  immutable, confirmed untouched through `1c91203`.
- Seed 73: blocked.
- `thought-organizer-app` v2 activation / export / deployment: blocked.
- Any further model training, inference, or benchmark execution: not
  authorized by anything in this handoff — each compute step in this
  project has required Johnny's explicit, separate authorization every
  time, no exceptions so far.
