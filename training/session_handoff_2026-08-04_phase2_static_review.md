# Session handoff — 2026-08-04 (Phase-2 balanced curriculum: static review round closed)

**Repo state at close**: `main` at `4a7b892d58573b5e1253a3bf852e85eb0952897d` (unchanged from the prior
handoff — this round produced review documents only, nothing was committed). Working tree has 2 new
uncommitted files from this round plus the carryover untracked artifacts from the prior session (see
below). No divergence from `origin/main`.

## What this session did

Per Outcome B's own rule (seed-17 R2 replay closed 2026-08-03 — see
`training/session_handoff_2026-08-03_r2_outcome_close.md`), any Phase-2 curriculum work requires a new
static review and separate authorization before compute. ChatGPT produced that static review; this
session's job was Claude's independent verification of it, per this project's standing collaboration
protocol (re-verify every claim against real data, flag disagreements rather than silently accepting or
resolving them).

1. **Saved `training/phase2_balanced_curriculum_static_review_chatgpt.md`** — ChatGPT's proposal, received
   as pasted chat text. Normalized the same em-dash mojibake pattern (`â` for `--`) already diagnosed twice
   earlier in this project before saving. Claimed hash (`c6045cb0...`) did not match the saved file's
   actual hash (`467be65b...`) — the known paste-re-encoding artifact, not evidence of tampering; no
   byte-faithful source exists to check the claim against, consistent with every prior pasted-document
   round this project has handled.
2. **Independently recomputed every quantitative claim directly from the repository** rather than trusting
   the review: corpus bullet/action-count distributions (exact match), category counts, split math (60/6
   current, 72/6 proposed), and optimizer-step math (`train.py`'s real `num_train_epochs=40`/`batch=4`
   config gives exactly 600 steps at 60 records and exactly 720 at 72 — not approximate, as the reviewed
   document hedged).
3. **Verified coverage claims by reading actual training records**, not taking labels at face value — found
   one piece of *stronger* evidence than ChatGPT cited: a `buried_reminder` record contains the literal
   phrase "Still undecided on the paint color," matching `sdi2-06`'s real input's opening almost verbatim,
   showing the corpus already teaches both halves of the needed unresolved-state/decision-task contrast
   individually.
4. **Surfaced a relevant precedent ChatGPT's document only gestured at**: the exact "corpus size silently
   changes optimizer steps under fixed epochs" confound was already escalated to a *required* step-matched
   control in `training/gold_v1.2.3_groupscreen_seed17_scoring.md`. Recommended any future Phase-2 compute
   manifest plan a 600-step control on the 72-record corpus (via `train.py`'s existing `--max-steps` flag),
   not just document the tradeoff in prose.
5. **Wrote and saved `training/phase2_balanced_curriculum_claude_review.md`** — full independent
   verification, all 7 of ChatGPT's review questions answered directly, one genuine disagreement flagged
   and returned (not resolved unilaterally).

## The one open disagreement (needs Johnny/ChatGPT's decision)

ChatGPT proposes a new category, `high_count_task_retention`, for the 4 high-action-count examples
(addressing `sdi2-08`'s untrained 5–8-action range). Claude leans toward extending the existing
`simple_list` category to `hard`/`expert` difficulty instead — checked that both current `simple_list`
records are `difficulty: easy` capping at exactly 4 actions (the corpus-wide ceiling), and that this
project's own documented convention (`docs/datasets/CATEGORY_REFERENCE.md`) favors difficulty-tier
extension over new categories unless the skill is genuinely new (precedent: gold_v1.2.3 added an `expert`
tier to `interrupted_thought_depth` without forking a category). The counter-case — that `sdi2-08`'s
bullet-ceiling-vs-action-completeness divergence at 7/8 is a real step up in mechanical difficulty — is not
unreasonable either. Full reasoning in §4 of the Claude review doc. **This is the one thing that needs a
decision before anything else in the proposal can move forward.**

## Everything else in the proposal: independently confirmed, no other disagreement

- 12-example count/family allocation: reasonable given the evidence, no adjustment needed.
- Appending all 12 to train while keeping the 6 validation records byte-identical: matches the pattern
  `training/prepare_v2_r2_training_data.py` already proved out for the R2 corpus itself — a Phase-2
  derivation script should reuse that same approach, not invent a new one.
- No proposed family is already adequately represented or redundant with frozen benchmark content, at the
  shape/level currently proposed (no example text exists yet to run a literal overlap check — correctly
  deferred to the proposal's own authoring constraint #10).
- Fail-closed derivation checks and artifact-naming recommendations given in §5, question 7 of the Claude
  review doc, following the same pattern as the existing `_r2_` tooling.

## Explicit non-authorizations (unchanged, restated every round)

Nothing beyond this review is authorized: no example authoring, no design-note creation, no derivation
tooling, no corpus mutation, no training, no inference, no benchmark run, no seed 73, no export, no
deployment, no activation. Both new documents from this round are uncommitted, pending Johnny's decision on
the category disagreement and whether/how to relay it back to ChatGPT.

## Uncommitted artifacts currently on disk (as of this handoff)

- `training/phase2_balanced_curriculum_static_review_chatgpt.md` (this round, new)
- `training/phase2_balanced_curriculum_claude_review.md` (this round, new)
- `training/session_handoff_2026-08-03_r2_outcome_close.md` (prior session's handoff, still uncommitted —
  disposition not yet decided)
- `training/controlled_seed17_r2_replay_run/checkpoint/` and its 3 `*_log.txt` siblings — intentionally
  local-only, per established repo policy (see the prior handoff), not a TODO.

## Open threads for the next session

- Johnny/ChatGPT to decide the `high_count_task_retention` vs. extended-`simple_list` question.
- Once resolved, decide whether to commit this round's two review documents (and the prior session's
  handoff doc) before or separately from any authoring authorization.
- No compute of any kind is authorized on any front. Seed 73 remains blocked.

Per [[session_handoff_workflow]]: Johnny starts a new chat after this milestone.

## Addendum: round closed, committed and pushed (2026-08-04)

Everything this handoff left open was resolved within the same session, before any new chat started:

- **Category disagreement**: ChatGPT accepted extending `simple_list` to higher difficulty tiers in full;
  `high_count_task_retention` will not be introduced.
- **Step-count precedent**: ChatGPT accepted requiring a 600-step control alongside the natural 720-step
  run in any future Phase-2 compute manifest.
- **Document-integrity question**: ChatGPT separately asserted a byte-faithful copy of its own review
  existed at hash `c6045cb0...` and supplied a second attachment. That attachment, hashed exactly as
  received, still carried the same `â`-for-em-dash mojibake and did not match the claimed hash — but
  normalizing it the same way used before reproduced `c6045cb0...` exactly, cryptographically confirming
  the fix reconstructs ChatGPT's original bytes precisely.
  `training/phase2_balanced_curriculum_static_review_chatgpt.md` was rewritten to that exact
  reconstruction and now hashes to `c6045cb0...`.
- Both review documents were committed together (`fdcf469753674c01829ceac3617944d56bac92b5`) and pushed to
  `origin/main`.

**Repo state at actual close of this thread**: `main` at `fdcf469753674c01829ceac3617944d56bac92b5`,
pushed, matching `origin/main`. This supersedes the "repo state at close" line at the top of this document,
which reflected the mid-round state before resolution.

Still true, unchanged: no example authoring, design-note creation, derivation tooling, corpus mutation,
training, inference, benchmark run, seed 73, export, deployment, or activation is authorized. This round
closed a static review only.
