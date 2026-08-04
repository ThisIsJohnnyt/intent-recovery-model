# Phase-2 Balanced Curriculum Proposal — Claude Independent Static Review

**Date:** 2026-08-04
**Scope:** Independent verification of `phase2_balanced_curriculum_proposal.jsonl` (12 authored records) and
`phase2_balanced_curriculum_design_notes.md` against the authorized static-review package (`fdcf469`/`a8b608d`
on `main`) and the frozen benchmark/corpus. No corpus mutation, derivation tooling, training, inference, or
compute performed. Authoring itself was separately authorized (correcting an earlier typo that read as a
decline); this review is the required independent check before any further step.

## 1. Artifact integrity — CONFIRMED, byte-exact

`phase2_balanced_curriculum_proposal.jsonl` was read directly from `C:\Users\thisi\Downloads\` — the local
filesystem, not the chat-paste relay pipeline that has produced mojibake in three prior documents this
project — and hashed to `1f32f38d0288837eb439105bfe38d0e221b5c20f0f99de3e5ca9dbc5e79e0620`, an exact match to
the claimed value. `phase2_balanced_curriculum_design_notes.md` was transcribed from the pasted document and
hashed to `737a2c2d4790d2419b376ffbd09d9276385e2c3ca56b2bf2e349d84bbcab013b`, also an exact match on the first
attempt — this document uses plain hyphens rather than em-dashes throughout, which avoids the known
relay-corruption class entirely.

## 2. Structural fidelity — CONFIRMED, exact match on every count

Recomputed directly from the JSONL (not the design notes' claims about itself):

| ID | Category | Difficulty | Bullets | Actions | Matches design notes? |
|---|---|---|---:|---:|---|
| P2-001 | `open_question_preservation` | hard | 2 | 0 | yes |
| P2-002 | `idea_action_boundary` | hard | 2 | 1 | yes |
| P2-003 | `repeated_reminder` | hard | 1 | 1 | yes |
| P2-004 | `repeated_reminder` | hard | 1 | 1 | yes |
| P2-005 | `simple_list` | hard | 5 | 5 | yes |
| P2-006 | `simple_list` | hard | 6 | 6 | yes |
| P2-007 | `simple_list` | expert | 7 | 7 | yes |
| P2-008 | `simple_list` | expert | 7 | 8 | yes |
| P2-009 | `cross_field_completeness` | expert | 6 | 2 | yes |
| P2-010 | `cross_field_completeness` | expert | 6 | 2 | yes |
| P2-011 | `two_unrelated_tasks` | easy | 2 | 2 | yes |
| P2-012 | `two_unrelated_tasks` | medium | 2 | 2 | yes |

Exactly 12 records, exactly the committed 2/2/4/2/2 family allocation. **`high_count_task_retention` is
confirmed absent everywhere** — all four high-count examples correctly use `category: simple_list`, matching
the resolution both reviewers agreed to. No other category was introduced.

## 3. Content read — every specific claim independently checked against the actual `output` fields, not just the design notes' description of itself

- **P2-001/P2-002 modality contrast**: P2-001 preserves both alternatives (corkboard/magnetic strip) and the
  light observation, returns zero actions. P2-002 produces exactly one action carrying the full "before
  leaving for the hike" qualifier, keeps the thermos sentence a pure observation. Confirmed as the intended
  paired contrast.
- **P2-003/P2-004 deduplication**: both collapse cleanly to one bullet/one action, correctly retain the
  Friday deadline (P2-003) and the recital qualifier (P2-004), no invented recipient/tuner/claim-number.
- **P2-005 through P2-007 (5, 6, 7 actions)**: every task present in both fields, all qualifiers attached to
  the correct task (the room-number/group-chat qualifier stays on the right item in P2-005; "by 3" stays on
  sign return, not microphone testing, in P2-007).
- **P2-008 — the hardest structural claim, verified directly**: bullets list has exactly 7 items and is
  missing "take the loan agreement to the archive"; actions list has exactly 8 items and *includes* that
  exact task; the narrative also states it in full. This is precisely the claimed behavior — one task
  deliberately omitted from bullets only, never merged with a neighbor, still fully present in narrative and
  actions. This is a genuinely nontrivial constraint to satisfy correctly and it's satisfied exactly.
- **P2-009/P2-010 dense completeness**: both return exactly 6 bullets / 2 actions. Attribution roles read
  correctly in both directions (P2-009: Ren reports, Salma acts, installation lead receives — no swap; P2-010:
  Jae reports, the vendor acts — not assigned to Jae). Shared deadline qualifiers land on the correct
  action(s) only (P2-010's "before the staff briefing" attaches to banner-packing alone, not the access-map
  task, exactly as required). Tentative ideas (visitor cards, bench) stay non-actions; unresolved questions
  (window, keypad) stay unresolved.
- **P2-011/P2-012 regression guards**: P2-011 keeps both qualifiers on the correct task, no swap. P2-012
  deliberately does *not* merge two same-verb ("Label...") tasks despite the shared verb, keeping the
  correct object/destination pairing for each — this is the intended guard against over-deduplication,
  distinct from and complementary to P2-003/004's dedup lesson.

No hallucinated content was found in any of the 12 records against their own design notes' "Hallucinations
to watch for" lists.

## 4. Overlap check (constraint #10) — independently run, not taken on the "manual surface review" claim

Ran an automated 4-gram overlap check (same method this project used for the original v2 acceptance schema's
overlap claim) across all 12 proposed records' full text (input + narrative + bullets + actions) against all
66 R2-corpus records and all 26 frozen benchmark probes (protected-16 + acceptance-10, using each probe's
`input` and `expected_behavior`).

- **Zero 4-gram overlap with any of the 26 benchmark probes.** This is the constraint that matters most —
  benchmark isolation is fully intact.
- Three 4-gram overlaps with the 66-record corpus, all generic passive-voice scaffolding this dataset uses
  throughout (`"is already in the"`, `"needs to be booked"`, `"needs to be called"`, `"needs to be uploaded"`)
  — not shared scenario content, objects, or names. Not a concern.
- Separately cross-checked all proper-noun-like tokens across the 12 records (`Ren`, `Salma`) against both
  the corpus's and the benchmark's people — zero collisions.

The design notes' own claim ("Manual surface review removed reused benchmark deadlines, objects, and
distinctive high-count wording") is confirmed true by this independent, automated check, not merely accepted.

## 5. Design-notes template compliance — CONFIRMED programmatically

Checked all 10 fields required by `docs/datasets/DESIGN_NOTES_TEMPLATE.md` (`Example_ID`, `Lesson`, `Author
Intent`, `Scenario`, `Reason each fragment exists`, `Boundary Evidence`, `Failure Modes`, `Hallucinations to
watch for`, `Why this example is at this point in the curriculum`, `Expected Recovery`) are present in all 12
entries — no entry is missing any section. Separately cross-checked every entry's `Lesson` field against the
JSONL's actual `category` field: **12/12 exact matches**, including confirming all four `simple_list` entries
say `simple_list` in both places, not a stray `high_count_task_retention` reference anywhere in the prose.

## 6. Two minor, non-blocking notes

1. **No explicit `id`/`example_id` field in the JSONL itself** — records are only matched to `P2-001`...`P2-012`
   by position, unlike the design notes' own labeling. This is fine for the current draft, but whoever builds
   Phase-2 derivation tooling later should either add stable IDs or key strictly by input-hash (the same
   approach `training/prepare_v2_r2_training_data.py` already used for the R2 corrections) — flagging now so
   it isn't rediscovered as a blocker later.
2. **P2-006's `Boundary Evidence` labels use loose paraphrases** ("box labeling," "radio charging," "form
   scanning") that don't match the actual task wording ("catalog the archive boxes," "pair handheld radios,"
   "digitize the completed survey cards"). This is a documentation wording slip in the design notes' prose
   only — the actual JSONL content is correct and was independently verified in §3. Worth a one-line polish,
   not a defect.

## 7. Verdict

**No disagreement.** Every structural claim, every content claim, and the overlap claim all reproduce
independently and exactly. This is a clean, high-fidelity authoring round with no hallucinations, no category
drift, no benchmark leakage, and full template compliance. The two notes in §6 are cosmetic and don't require
rework before the next decision.

## 8. Non-authorizations (unchanged)

This review authorizes nothing beyond itself. Derivation tooling, corpus mutation (deriving an actual
Phase-2 candidate corpus from these 12 records plus the 66-record R2 parent), training, inference, any
benchmark run, seed 73, export, deployment, and activation all remain separately unauthorized, per the
ownership table in the original ChatGPT proposal (§9).
