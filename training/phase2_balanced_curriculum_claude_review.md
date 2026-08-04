# Phase-2 Balanced Curriculum — Claude Independent Static Review

**Date:** 2026-08-04
**Scope:** Independent verification of `phase2_balanced_curriculum_static_review_chatgpt.md` against the
real repository — corpus counts, coverage claims, category proposal, split policy, and step math. No
example authoring, corpus mutation, derivation tooling, training, inference, seed 73, export, deployment,
or activation performed or authorized by this review.

## 0. Document integrity

The pasted document reproduces the same em-dash mojibake pattern already diagnosed twice earlier in this
project (`â` standing in for `--`/`--`) — 9 instances, all in the same unambiguous position (prose
separators). Normalized and saved to `training/phase2_balanced_curriculum_static_review_chatgpt.md`. As
with every prior pasted-document round, the resulting hash (`467be65b...`) does not match the claimed
`c6045cb0...` — this is the known paste-re-encoding artifact, not evidence of tampering, and there is no
byte-faithful source to check the claim against. Repository state independently confirmed: `HEAD` =
`4a7b892d58573b5e1253a3bf852e85eb0952897d`, matching the document's stated review target exactly, working
tree otherwise clean.

## 1. Corpus counts — CONFIRMED, exact match

Recomputed directly from `training/gold_v1.2.2_r2_derived_candidate.jsonl` (66 records, each with an
`output.bullets`/`output.action_items` list — no parsing required):

| Measure | ChatGPT's claim | Independently recomputed | Match |
|---|---|---|---|
| Total records | 66 | 66 | exact |
| Bullet distribution | 1:4, 2:13, 3:24, 4:18, 5:6, 6:1 | 1:4, 2:13, 3:24, 4:18, 5:6, 6:1 | exact |
| Action distribution | 0:8, 1:25, 2:19, 3:7, 4:7 | 0:8, 1:25, 2:19, 3:7, 4:7 | exact |
| Max bullets | 6 | 6 | exact |
| Max actions | 4 | 4 | exact |

No discrepancy anywhere in this table.

## 2. Coverage claims — CONFIRMED, in most cases with stronger evidence than cited

- **"Exact-word repeated reminders are represented"** — confirmed. Both `repeated_reminder` and
  `repeated_reminder_multi_topic` records dedupe a *literal* repeated phrase ("email dave" / "submit the
  timesheet"), never a paraphrase across different verbs. This directly supports the claimed gap
  ("semantic deduplication across paraphrased verbs and aliases is underrepresented") rather than merely
  being consistent with it.
- **"Several unresolved either/or examples exist"** — confirmed. 2 of the 4 `open_question_preservation`
  records are literally either/or framed ("vent or outside," "toaster or kettle").
- **"One action-oriented `Decide between` example"** — confirmed, found at record index 6
  (`rapid_branching_excitement`, not `idea_action_boundary` as the review's own family table might
  suggest — the claim itself didn't specify a category, so this is a confirmation, not a discrepancy):
  bullet `"Decide between weather.gov and OpenWeather APIs"` paired with action
  `"Compare OpenWeather and weather.gov APIs"`.
- **Stronger evidence than cited, found independently**: `buried_reminder` record index 30 contains the
  bullet `"Still undecided on the paint color"` — the *exact* modality phrase (`"Still undecided..."`)
  that opens `sdi2-06`'s real input (`"Still undecided between the linen cover and the woven cover..."`),
  correctly kept as a non-action. This means the corpus already demonstrates both halves of the needed
  contrast (an unresolved "still undecided" state with 0 actions, and an explicit "decide between" task
  with 1 action) individually — the sdi2-06 failure is specifically about applying that contrast when an
  *unrelated trailing observation* is also present, which is a genuinely narrow transfer gap, not an
  absent skill. This is worth citing explicitly in any future design notes for the family, since it's more
  precise than the cited evidence.
- **`two_unrelated_tasks`: exactly 1 record** — confirmed (`"Pick up dry cleaning. Renew the car
  registration..."`, 2 bullets/2 actions, no cross-field divergence).
- **`sdi2-10`'s exact target shape** — confirmed against the real probe definition: exactly 6 bullets,
  exactly 2 actions, attribution + deadline + unresolved question + a tentative idea that must stay out of
  actions. Matches the proposed family's required shape field-for-field.
- **One refinement, strengthens rather than weakens the claim**: the corpus's *single* 6-bullet record is
  actually category `buried_task_retention` (expert difficulty, 2 actions), not `cross_field_completeness`.
  All 3 `cross_field_completeness` records cap at 5 bullets (5, 4, 5). So the specific claim that matters —
  *no `cross_field_completeness`-style example has ever reached a 6-bullet/2-action shape* — is true and
  slightly stronger than "only one target reaches six bullets" implies on its own.

No coverage claim was found to be inaccurate.

## 3. Split and step math — CONFIRMED, with one precedent worth surfacing

- Current split confirmed directly from `training/data/processed_gold_v1.2.2_r2_v2contract_seed17/`:
  60 train / 6 val / 66 total. Matches.
- `train.py` confirmed: `per_device_train_batch_size=4`, `num_train_epochs=40`, no gradient accumulation
  set (defaults to 1). Step math is exact, not approximate: `ceil(60/4)=15` steps/epoch × 40 = **600**
  (matches every prior run this project has recorded), `ceil(72/4)=18` steps/epoch × 40 = **720** exactly
  (72 divides batch size 4 cleanly, so "approximately 720" in the reviewed document is actually exact, not
  an estimate).
- **Precedent worth surfacing explicitly**: this exact confound — corpus size change under fixed
  epochs/batch size silently changing total optimizer steps — was already identified and treated as
  *"operationally important, not merely theoretical"* in `training/gold_v1.2.3_groupscreen_seed17_scoring.md`
  (adding even the smallest group changed 600 steps to 640, all three groups shared a regression that
  couldn't be attributed to content alone until step count was isolated). That study's own required next
  step was a **dedicated step-matched control** run at the new step count using the *unchanged* baseline
  corpus, using `train.py`'s existing `--max-steps` flag (built specifically for this: its help text cites
  that exact confound by name), before attributing any Phase-2 outcome to curriculum content. The reviewed
  document's §6 correctly flags that a future manifest "must state explicitly whether per-example exposure
  or total optimizer steps is held constant and why," but given this project already has a directly
  analogous precedent that escalated to a required control experiment, I'd go further: **any future
  Phase-2 compute manifest should plan a 600-step control on the 72-record corpus (via `--max-steps=600`),
  not just document the choice**, mirroring the groupscreen study's resolution rather than re-deriving it
  from scratch. This is a recommendation for whoever eventually writes that manifest, not a blocker on this
  static review.

## 4. Category proposal — one flagged disagreement, not silently accepted or overridden

`docs/datasets/CATEGORY_REFERENCE.md` documents this project's own established convention for when a new
category is warranted versus reusing/extending one: new categories are introduced when a failure "names
the general recovery skill that failed across contexts" not already covered (e.g. `idea_action_boundary`,
`cross_field_completeness` in v1.2.2); otherwise existing categories are extended — including via
difficulty-tier escalation alone, as gold_v1.2.3 did by adding an `expert` tier to `interrupted_thought_depth`
*"without introducing a new category."*

Checked `simple_list`'s actual current representation: both existing records are `difficulty: easy`,
capping at exactly 4 actions each — the same number as the corpus-wide action ceiling. `simple_list`'s own
definition ("Recover tasks from a straightforward fragmented list") is generic to item count, and
`sdi2-08`'s real input (`"Sharpen the garden shears; refill the bird feeder; ...; charge the camera
batteries."` — eight semicolon-delimited imperative fragments) is structurally the same list-recovery
mechanic `simple_list` already names, just untested past `easy`/4-count.

**Disagreement**: rather than introducing `high_count_task_retention` as a new category, I'd lean toward
extending `simple_list` with `hard`/`expert`-difficulty, higher-count examples (5–8 actions) — matching
this project's own stated precedent of scaling an existing category via difficulty tier rather than
forking a parallel label for what is, at its core, the same recovery skill under more load.

**The counter-consideration, which is why I'm flagging rather than overriding**: `sdi2-08` specifically
stresses the *divergence* between the bullet ceiling (max 7) and action completeness (exactly 8) — the
existing `simple_list` records show only a mild version of that divergence (one record has 3 bullets vs. 4
actions, from combining "HDMI cable" and "2 surge protectors" into one bullet). A genuinely adversarial
7-bullet/8-action case, where the action section alone must carry every task the bullet ceiling cannot, is
a real step up in what's being tested, and reasonable people could call that a distinct-enough mechanical
skill to name explicitly. This is a real, evidence-based judgment call, not a formality — returning it for
Johnny/ChatGPT's decision rather than resolving it myself either direction.

## 5. Answers to ChatGPT's 7 questions

1. **Do the corpus counts and coverage claims reproduce from `main` at `4a7b892`?** Yes, exactly — see §1–2.
2. **Is `high_count_task_retention` justified, or should it reuse an existing category?** Genuine
   disagreement — see §4. I lean toward extending `simple_list`'s difficulty range instead, but the
   divergence-under-ceiling argument for a new category is not unreasonable. Returned for joint decision.
3. **Are 12 examples sufficient and balanced?** The 2/2/4/2/2 allocation tracks severity reasonably: the
   two hardest structural gaps (`sdi2-08`'s untrained 5–8 action range, and protected `13`'s fragile
   single-example regression guard) get proportionally more or dedicated slots. No family looks
   over- or under-weighted relative to the evidence in §2. No adjustment needed on the numbers themselves.
4. **Does appending all 12 to train while preserving the 6 val records give the cleanest comparison?** Yes
   under current tooling — `training/prepare_v2_r2_training_data.py` already established exactly this
   pattern (reuse frozen split membership/order, only `train.jsonl` changes) for the R2 corpus itself, so a
   Phase-2 derivation script could follow the identical, already-proven approach rather than inventing a
   new one.
5. **What exact epoch/step policy preserves the intended comparison?** 72 train records at the current
   `num_train_epochs=40`/`batch=4` config yields exactly 720 optimizer steps (not approximately — see §3).
   Given this project's own `gold_v1.2.3_groupscreen_seed17_scoring.md` precedent already escalated this
   exact confound to a required step-matched control, any future manifest should plan a 600-step control on
   the 72-record corpus via the existing `--max-steps` flag alongside the natural 720-step run.
6. **Are any proposed families too close to the frozen benchmarks or already adequately represented?** No
   family is already adequately represented — see §2's per-family gap evidence. No example text exists yet
   to run a literal overlap check against the 26 probes (correctly deferred to the proposal's own authoring
   constraint #10); nothing here suggests any family is redundant at the shape/level being proposed.
7. **What fail-closed derivation checks and artifact names should be frozen before authoring?** Following
   the exact pattern already proven in `training/prepare_v2_r2_training_data.py` (§4.3 tooling): pin the R2
   parent's fingerprint, require exactly 66 parent records byte-identical and in order, require exactly the
   12 new records appended in a declared stable order, fail closed on any duplicate input/stable-identity,
   any parent drift, any output-field mismatch, an unexpected total record count (must be 78), and require
   the 6 validation records to remain byte-identical to the current split. Artifact naming should follow
   the established `_r2_`/`_phase2_` convention this project already uses (e.g.
   `gold_v1.2.2_phase2_derived_candidate.jsonl`) rather than reusing the R2 filename.

## 6. Non-authorizations (unchanged)

This review authorizes nothing beyond itself. Example authoring, design-note creation, derivation tooling,
corpus mutation, training, inference, any benchmark run, seed 73, export, deployment, and activation all
remain unauthorized pending Johnny's decision on §4's category disagreement and any other direction he
wants to set.

## Addendum: both flagged items resolved (2026-08-04)

ChatGPT accepted both recommendations from this review in full:

1. **Category question (§4)**: reuse `simple_list`, extended into higher difficulty tiers, for the four
   high-count examples. `high_count_task_retention` will not be introduced as a new category. Confirmed
   agreement that high count is a scale/generalization challenge on an existing skill, not a genuinely new
   recovery skill — matching the reasoning in §4 above.
2. **Step-count confound (§3)**: any future Phase-2 compute manifest will include a 600-step control on the
   72-record corpus (via `train.py`'s existing `--max-steps` flag) alongside the natural 40-epoch/720-step
   run, mirroring the resolution `gold_v1.2.3_groupscreen_seed17_scoring.md` already established for the
   same confound.

The 12-example allocation and the proposed 72-train/6-validation split stand unchanged — no further
disagreement on either.

A related document-integrity question was raised and independently resolved: ChatGPT asserted a
byte-faithful copy of its own static-review document existed at hash `c6045cb0a5c08dd6a6344a7c0fbc12249009851352f686bcb68dc38389721d93`
and supplied a second attachment claiming to be that file. Directly hashing that attachment exactly as
received did **not** match the claimed value, and it still contained the identical `â`-for-em-dash mojibake
(7 occurrences) as the first attachment — proving the corruption happens somewhere in the relay pipeline
between ChatGPT and Claude, not in Claude's transcription, and that the second attachment was not actually
byte-faithful either. However, applying the exact same normalization already used for the first attachment
(replacing `â` with a real em-dash) to this second attachment's raw bytes reproduced the claimed hash
**exactly** — cryptographic proof the normalization is the correct reconstruction of ChatGPT's original
content, not just a reasonable guess. `training/phase2_balanced_curriculum_static_review_chatgpt.md` has
been rewritten to this fully byte-faithful reconstruction and now hashes to `c6045cb0...`, matching
ChatGPT's claim exactly.

With both substantive points resolved and the document-integrity question closed with cryptographic
certainty, this static-review package is ready for commit preparation. Example authoring, derivation
tooling, corpus mutation, training, inference, and all compute remain unauthorized until Johnny separately
authorizes each.
