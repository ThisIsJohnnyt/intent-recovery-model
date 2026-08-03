# Gold v1.2.3 Multi-Seed Stability Study (Phase A)

Per `gold_v1.2.3_stability_investigation.md`. Frozen inputs, environment,
and seed assignments recorded in `gold_v1.2.3_seed_study_manifest.md`.
`training/prepare_data.py` was not re-run; `train.jsonl`/`val.jsonl` are
byte-identical across all three seeds (hash-verified). Scores were
produced by Claude Code, one probe at a time across all three seeds in
the same sitting, applying identical criteria — "seed-masked and
order-randomized" rather than truly blinded, per the plan's own
correction: a single reviewer who also runs the pipeline cannot be fully
blind to which output came from which seed. No scores were revised after
initial recording.

## Headline result

**None of the three seeds is eligible to become the candidate**, under
the predeclared rule (format validity 16/16 AND every current
`regression_guard` passes). All three fail the guard requirement:

| Seed | Overall pass rate | Regression guards passed | Format validity |
|---|---|---|---|
| 42 (`checkpoint-680`) | 11/16 (69%) | 10/12 | 16/16 |
| 17 | 8/16 (50%) | 7/12 | 16/16 |
| 73 | 6/16 (38%) | 6/12 | 16/16 |

Per the plan's own rule: *"If no checkpoint passes all regression guards,
no Gold v1.2.3 checkpoint becomes the candidate."* That applies here,
cleanly, without needing any tie-break. `checkpoint-600` (`gold_v1.2.2`)
remains the best available checkpoint and the candidate/comparison
baseline. `checkpoint-520` remains production, unaffected.

**Path A (no curriculum change) is explicitly ruled out** by its own
trigger condition in the investigation plan: it requires "at least one
predeclared seed clears every regression guard." None did.

## Full per-probe stability matrix

| Probe | Seed 42 | Seed 17 | Seed 73 | Pass freq | Classification |
|---|---|---|---|---|---|
| 01 | Pass | Pass | Pass | 3/3 | Stable pass |
| 02 | Fail | **Pass** | Fail | 1/3 | Seed-sensitive failure |
| 03 | Fail | Fail | Fail | 0/3 | **Stable failure** |
| 04 | Pass | Pass | Pass | 3/3 | Stable pass |
| 05 | Pass | Fail | Fail | 1/3 | Seed-sensitive failure |
| 06 | Fail | Pass | Fail | 1/3 | Seed-sensitive failure |
| 07 | Pass | Pass | Pass | 3/3 | Stable pass |
| 08 | **Pass** | Fail | Fail | 1/3 | Seed-sensitive pass |
| 09 | Fail | Fail | Fail | 0/3 | **Stable failure** |
| 10 | Pass | Fail | Pass | 2/3 | Seed-sensitive pass |
| 11 | Pass | Fail | Fail | 1/3 | Seed-sensitive failure |
| 12 | Pass | Pass | Fail | 2/3 | Seed-sensitive pass |
| 13 | Pass | Fail | Pass | 2/3 | Seed-sensitive pass |
| 14 | Pass | Pass | Pass | 3/3 | Stable pass |
| 15 | Pass | Pass | Fail | 2/3 | Seed-sensitive pass |
| 16 | Fail | Fail | Fail | 0/3 | **Stable failure** (identical output text on all 3 seeds) |

## The most important finding: this release's two "wins" are not stable

**Probe 08** — the clean resolution reported for `checkpoint-680` — only
resolves on seed 42. Seeds 17 and 73 both revert to the same confusing,
tautological wording ("whether the wet spot from the window or the plant
was dry again by lunchtime") that plagued every prior checkpoint, and
seed 73 drops the question from the narrative field entirely. This is a
**seed-sensitive pass** (1/3), not the robust fix it looked like from a
single run.

**Probe 15** — the flagship regression fixed in `gold_v1.2.2` and
promoted to `regression_guard` on the strength of that single clean run
— fails on seed 73, reverting to the exact original failure (a tentative
idea wrongly promoted into `action_items`). This is genuinely concerning
independent of this release: it means the `gold_v1.2.2` promotion
decision was made on one data point, and this study shows that data point
wasn't representative of every seed. Recommend not treating any single
"resolved" run as conclusive going forward without at least this kind of
check.

## Second major finding: several probes assumed rock-solid are seed-sensitive

Probes **05**, **10**, **11**, and **13** had never failed on *any*
checkpoint across this project's entire history before this study. All
four fail on at least one of the two new seeds:

- **05**: both seed 17 and seed 73 misattribute the folder-link recipient
  to "Cole" in the narrative field specifically, while bullets/actions
  correctly say "Priya" — a genuine cross-field inconsistency, not a
  cosmetic typo like the long-standing "backped up" issue.
- **10**: seed 17 drops "print the shipping label" from both narrative
  and bullets (survives only in `action_items`).
- **11**: seed 17 invents "Feeling exhausted from dealing with the fee"
  (misattributing the input's "tired of dealing with it," which refers
  to the garage light, to the registration fee instead); seed 73 invents
  an unsupported repair task, "renew the garage light," in the narrative.
- **13**: seed 17 invents an entire unrelated fact in the narrative
  ("I noticed that my colleague was late for work") with zero basis in
  the input.

None of these are `gold_v1.2.3` target probes. This is the clearest
demonstration yet that a single evaluation run — even a careful,
strictly-scored one — cannot be treated as characterizing "the
checkpoint's" behavior at this data scale. The whole premise of Phase A
is validated by this result, independent of what it says about
`gold_v1.2.3` specifically.

## Stable failures (0/3) — not seed noise, but the cause is not yet established

Per the investigation plan's own framework, a 0/3 result across
identical data and only-seed-varying runs rules out pure seed noise as
the explanation. **It does not, by itself, prove a `gold_v1.2.3`
curriculum conflict is the cause** — a failure stable across all three
seeds trained on the 72-example corpus is equally consistent with (a) a
real interaction introduced by `gold_v1.2.3`'s specific new examples, or
(b) something already present after `gold_v1.2.2` (or earlier) that has
nothing to do with this release's additions, and that this seed study
can't distinguish from (a) on its own — that's exactly what the
approved `gold_v1.2.2`-only control-seed runs are for. The three probes
below warrant the targeted conflict audit (Phase B) as an
**investigation**, not as confirmation of what the audit will find:

- **Probe 03**: fails differently on all three seeds (bullets-only split
  on 42, clock reframed as a task on 17, a full two-item action-list
  split on 73) but fails every time. One hypothesis worth auditing:
  negative transfer from `gold_v1.2.3`'s interruption-splitting examples
  into a probe that requires the opposite behavior (keeping one governed
  task together) — but this is a hypothesis to test, not an established
  mechanism, and the control-seed results may show this probe was already
  unstable before `gold_v1.2.3` existed.
- **Probe 09**: all three seeds reframe the volunteer-list "not sure what
  yet" incomplete thought into something task-flavored — outright
  emotional fabrication on seed 42, milder "needs to be considered"/"needs
  to be checked" framing on seeds 17/73. Same underlying issue, three
  different severities. Relevant to Phase B's audit area C (unresolved
  question vs. unsupported interpretation), pending the same
  control-seed caveat above.
- **Probe 16**: **identical output text on all three seeds**, including
  the added "both references are unresolved" commentary. This is strong
  evidence that this specific behavior is deterministic given the
  current 72-example training corpus, not seed noise — but whether it
  traces to `gold_v1.2.3` example 006 specifically or was already present
  after `gold_v1.2.2` (e.g. from `gold_v1.2.2` example 002) is exactly
  what the targeted audit and control-seed comparison need to establish
  before drawing that conclusion.

## Seed-sensitive failure warranting the reduced Probe 02 diagnostic

Probe 02 passes cleanly on seed 17 (no fabricated content, correct causal
attribution) but fails on seeds 42 and 73 (different failure mode each
time — a fabricated noun on 42, a garbled-but-not-fabricated preamble on
73). Per the investigation plan's own dispatch rule ("Probe 02 passes
only 1/3 or 2/3: run a reduced diagnostic focused on the variants that
test punctuation and interruption interference"), this calls for the
**reduced** Phase C diagnostic, not the full seven-variant battery.

## What this means for the four authorized paths

- **Path A (no curriculum change)**: ruled out by its own trigger
  condition — no seed cleared every guard.
- **Path B (curriculum conflict investigation)**: **warranted as an
  investigation, not yet proven as the corrective action.** Probes `03`,
  `09`, and `16` are stable (0/3) failures, which rules out pure seed
  noise, but not whether a `gold_v1.2.3`-specific curriculum conflict is
  the cause versus something already present after `gold_v1.2.2`. The
  targeted conflict inventory (no curriculum edits yet) and the
  `gold_v1.2.2`-only control-seed runs are both required before this
  path could turn into an actual revision decision.
- **Path C (engineering/model-strategy investigation), reduced**:
  warranted for probe `02` now — punctuation/interruption-interference
  variants only, since it's a seed-sensitive 1/3 failure, not a stable
  3/3 one.
- **Path D (pause for evaluation infrastructure)**: proceeding
  separately, isolated on its own branch/worktree — this study's own
  findings (rock-solid probes turning out to be seed-sensitive) reinforce
  why a larger, more representative validation signal matters, separate
  from whatever else is decided here.

Approved next steps: begin the Path B targeted inventory (03/09/16, no
edits yet) and the reduced Path C diagnostic now, run the two
`gold_v1.2.2` control seeds to establish whether the stable failures
above predate `gold_v1.2.3`, and continue Phase D in parallel. The
combined evidence from all of this — not the seed study alone — is what
decides between curriculum revision and broader training-strategy work.
