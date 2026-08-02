# Prompt-contract compatibility study — frozen design manifest

**Status: design and commands only. No training or inference has been run.**
`intent-recovery-model` PR #13 and this manifest's original version (PR #14)
were both merged to `main` on 2026-08-02 before joint review of the design
completed. `thought-organizer-app` PR #4 remains open. This revision
corrects a seed confound ChatGPT caught in the merged version, three
further rounds of review since (a working-directory/gate-sequencing fix,
a fail-open scoring gap in the new acceptance set, and the same fail-open
gap found in the shared 16-probe legacy benchmark this study's Cell
A/B/C actually run against) — see below, in order — treat this version
as current, not PR #14's. **Not yet aligned**: Round 4's per-probe
`required_semantic_dimensions` mapping was corrected once already (from a
self-authored heuristic to match two existing historical scored
benchmarks exactly) and a lightweight-test import bug was fixed in the
same round — pending review before this is considered settled.

**Compute waits for this design to be marked Aligned, full stop.** The
previous wording here also said compute waits for `thought-organizer-app`
PR #4 to land, which directly contradicted the release gate elsewhere in
this document (PR #4 stays unmerged *until* compute passes) — ChatGPT
caught this circularity. Corrected sequence: (1) this design gets
reviewed and accepted, (2) the study runs, (3) `thought-organizer-app`
PR #4 merges/activates only after a compatible checkpoint clears every
gate. PR #4's own state (open, mergeable, cross-verified) is not a
precondition for starting compute.

## Correction (2026-08-02): seed confound in the original screening plan

The version merged as PR #14 set Cell A's reference to the seed-17/73
`checkpoint-600` replicas (the only ones with surviving weights, per
finding #2 below) but had Cell C **screen seed 42 first**. Comparing a
freshly-trained seed-42 candidate against a seed-17/73 reference conflates
the prompt-contract change with seed variation — exactly the kind of
second variable this study exists to rule out. Caught by ChatGPT, verified
here, and corrected: **the comparison cells below are structured as one
same-seed A/B/C triplet at a time**, screening seed 17 or 73 first (both
have real Cell A references), never seed 42 alone. The historical seed-42
`checkpoint-600` result (13/16, old prompt) stays on record as context
only — it is not part of the controlled comparison, and no new seed-42
candidate is trained as part of this study.

## Round 2 correction (2026-08-02): ChatGPT's review of the seed-confound fix

ChatGPT reviewed the seed-confound fix above and found it correct, but
raised four further issues before compute can start, plus fixture-specific
revisions. All addressed in this revision:

1. **Circular PR #4 dependency** — fixed above (top of document).
2. **Commands didn't share a valid working directory.** The original
   commands mixed `python run_benchmark.py ...` (implicitly run from
   `training/`) with `git checkout <ref> -- training/prepare_data.py`
   (implicitly run from the repo root) — neither convention works for
   both. Fixed by switching to pinned Git worktrees for the two prompt
   versions and absolute paths throughout (see Setup, below), so no
   command depends on which directory it's launched from, and
   `training/prepare_data.py` is never repeatedly swapped in the main
   working tree.
3. **`acceptance_gate`, not `regression_guard`.** The five new
   source-determined-bullets cases have no established prior-passing
   baseline — labeling them `regression_guard` would make
   `report_benchmark.py` describe a first-time failure as a "regression."
   Fixed: `datasets/benchmark/source_determined_bullets_acceptance.jsonl`
   now uses `"status": "acceptance_gate"`, and `report_benchmark.py` has a
   dedicated "Acceptance gates passed" section, separate from the
   regression-guard and negative-example counts.
4. **Score semantic correctness, not count alone.** A response with the
   right bullet count can still omit, merge, misattribute, or invent
   content. Fixed: each case now declares a `bullet_count_rule`
   (`{"operator": "exact"|"max", "value": N}`, replacing the old
   `expected_bullet_count` field) as one capability check among the
   others `run_benchmark.py` already scaffolds from `primary_checks` --
   a case only passes when format is valid, every scored semantic
   dimension is `2`, and every capability check (including the bullet/
   action-count rule) is `true`. No shortcut that checks count alone.

**Fixture-specific revisions**, per ChatGPT's case-by-case review:
- `sdb-01`, `sdb-02`: accepted as originally written, schema fields
  updated only.
- `sdb-03`: minor cleanup — removed a proper name ("Sam") that wasn't
  necessary for the test and risked incidental overlap with other
  fixtures' cast of names.
- `sdb-04`: revised. The original self-contradicted (`expected_bullet_count:
  7` implied an exact match while the prose said "at most seven"; it both
  forbade merging ideas and permitted "combining" them, which is the same
  thing) and reused "Priya," a name already used in
  `gold_v1.2.1_probes.jsonl` probe 05 -- a real collision, not just a
  style nit. Now uses `bullet_count_rule: {"operator": "max", "value": 7}`,
  drops the name, and requires all eight source ideas to survive
  somewhere across the combined output even though at most seven get
  their own bullet line.
- `sdb-05`: revised. The original's two restated ideas ("worried about
  the rent" / "rent increase is stressing me out") differ enough in
  content — one factual, one emotional — that whether it's one idea or
  two was genuinely debatable, undermining the test. Replaced with one
  literal, concrete task restated in different wording, and added an
  `action_count_rule` alongside `bullet_count_rule` since the same
  restated-task risk applies to `action_items`, not only `bullets`.

## Round 3 correction (2026-08-02): a fail-open scoring gap in the acceptance gate

ChatGPT found, and Claude independently reproduced, a real bug in
`report_benchmark.py`'s `probe_passes()`: it rejects a semantic score only
when it's non-null *and* not 2, so a result with every score left null
(never actually scored) still passed, as long as `format_valid` was true
and every `capability_check` was already true. Reproduced directly:
`format_valid=True`, all four `scores` null, `BULLET_COUNT_RULE_SATISFIED:
True` → `probe_passes()` returned `True`. That means an acceptance case
could show as passing without anyone having actually scored its semantic
correctness at all.

Fixed: each acceptance case now declares `required_semantic_dimensions`
(`["topic_completeness", "unsupported_addition_resistance"]` for all five
-- the minimum ChatGPT specified). `run_benchmark.py` copies this field
into its result scaffold, so the results file is self-contained.
`probe_passes()` now requires every listed dimension to be scored exactly
`2` (missing or null fails, matching how a wrong score already failed),
and raises on an unrecognized dimension name rather than silently
ignoring a typo. Existing probes without `required_semantic_dimensions`
(all 16 in `gold_v1.2.1_probes.jsonl`) are unaffected -- confirmed by
test and by construction, since an empty required-dimensions list can
never fail the new check.

`training/test_report_benchmark.py` (new) proves: all-null-required
dimensions fails; one required dimension null (others scored) fails; one
required dimension missing from `scores` entirely fails; all required
dimensions scored 2 with format valid and checks true passes; a required
dimension scored 1 (partial credit) fails; an unknown dimension name
raises; format-invalid fails regardless of scores; and a probe with no
`required_semantic_dimensions` keeps the original lenient behavior.
Directly re-verified against the acceptance set with two synthetic
results files: everything null now reports 0/5 acceptance gates passed
(previously would have shown 5/5); everything correctly scored reports
5/5.

Two fixture clarifications from the same review: `sdb-04` now also
requires `action_count_rule: {"operator": "exact", "value": 8}`, since
all eight source ideas are genuine tasks -- makes "all eight survive"
objectively checkable via the action-item count instead of a subjective
"survives somewhere" judgment. `sdb-05` now explicitly requires the
supported "before Friday" deadline to survive (plus a `DEADLINE_SURVIVED`
check), since the prior wording could be read as allowing that qualifier
to quietly disappear as long as the core task remained.

## Round 4 correction (2026-08-02): the same fail-open gap in the legacy 16-probe benchmark

ChatGPT found a broader instance of the Round 3 gap: `datasets/benchmark/gold_v1.2.1_probes.jsonl`
-- the actual benchmark this study's Cell A/B/C comparisons run against --
had no `required_semantic_dimensions` on any of its 16 probes. Reproduced
independently: an entirely-unscored scaffold (format valid, every score
null, every declared capability check null) reported **4/16 passing**
(probes 13-16 specifically, since those four have empty `primary_checks`
lists -- no capability check to fail on, either). That directly
contradicts this study's own "16/16 format validity" and "no reduction in
overall strict passes" material-regression gates: those numbers are only
meaningful if 0/16 is possible on an unscored run, and it wasn't.

**Fixed**: added `required_semantic_dimensions` to all 16 probes
(input/expected_behavior/primary_checks/likely_failures/notes untouched --
confirmed byte-identical except the one new field, per-probe, before
committing). `run_benchmark.py` already propagates
`required_semantic_dimensions` generically (added in Round 3), so no
further code change was needed there. `training/test_report_benchmark.py`
gained three integration tests against the real file: all 16 probes
declare at least one required dimension; an unscored scaffold now
reports 0/16 (not 4/16); a fully and correctly scored scaffold still
reports 16/16 (confirming the added requirements are satisfiable, not an
over-constraint).

**Round 4a correction (same day): the first per-probe mapping was a
self-authored heuristic, not the established rubric.** The initial
version of this mapping was derived from each probe's own
`likely_failures` list and `expected_behavior` text -- a reasonable
starting point, but a guess, not a match to any existing standard.
ChatGPT pointed out the project already has two independent, authoritative
scored benchmarks that encode a real historical rubric:
`training/gold_v1.2.1_benchmark_results_epoch40.json` and
`training/gold_v1.2.2_benchmark_results_checkpoint600.json`. Verified
directly: both files score the *identical* set of dimensions per probe
(confirmed programmatically, not assumed), and diffing that pattern
against the heuristic mapping surfaced exactly nine probes missing a
dimension the historical rubric actually required -- eight missing
`unsupported_addition_resistance` (02, 04, 05, 07, 08, 10, 12, 13) and one
missing `uncertainty_preservation` (01). The heuristic mapping was never
wrong in the other direction (no probe had an extra, unsupported
dimension) -- it just under-weighted `unsupported_addition_resistance`,
which the historical rubric requires on all 16 probes universally, not
just where "Unsupported Addition" happened to be the headline
`likely_failures` entry. Corrected to match the historical rubric exactly
on all 16 probes; the other seven (03, 06, 09, 11, 14, 15, 16) already
matched and needed no change.

**Round 4b correction (same day): a real, unrelated engineering bug in
the new tests.** `training/test_report_benchmark.py` imported
`run_benchmark.load_probes` -- but `run_benchmark.py` imports `torch`/
`transformers` at module level, so a "lightweight reporter test" would
fail in any environment without those installed, even though the
function it needed is a one-line JSONL reader with no ML dependency.
Fixed by importing the equivalent `report_benchmark.load_jsonl` instead
(aliased to the same local name, identical implementation). Verified with
the base system Python (confirmed to lack `torch` entirely, unlike the
project's `venv`): the old import path fails with
`ModuleNotFoundError: No module named 'torch'`; the fixed test suite runs
clean.

**Alignment status carried forward from this round's review: not yet
aligned on the complete study gate**, pending this round's corrections
being accepted.

## Round 5 (2026-08-02): seed-17 result and a runner/prompt-contract pinning fix

**The seed-17 triplet ran under this manifest and does not clear the
gate** (full record: `training/gold_v1.2.2_seed17_compatibility_study_provenance.md`,
`training/gold_v1.2.2_seed17_compatibility_study_chatgpt_scoring_handoff.md`).
Gate 2 (no Cell-A regression-guard pass becomes a Cell-C failure) and
Gate 4 (all 5 acceptance gates pass) both failed; independently verified,
not just taken on ChatGPT's word. Johnny is treating this as closed and
directed a design-only postmortem before any further compute -- not a
retry of this same design. See the two documents above for the full
outcome; this manifest's comparison-cell design is not being iterated on
directly, pending that postmortem.

**A real bug was found and is fixed here for future reference**: pinning
a whole worktree at an old commit pins *every* file in it, not just
`prepare_data.py`. Both `8d7aa09` and `80062bc` predate the
`required_semantic_dimensions` propagation added later to
`run_benchmark.py` (commit `8a23316`, this same PR #15) -- so every cell
in the seed-17 run produced result files missing that field. ChatGPT
caught it; the raw outputs and format-validity numbers were unaffected
(that field has no effect on generation), and the missing metadata was
safely hydrated post-hoc without rerunning any compute. Root-caused and
confirmed via `git log`/`git diff` against both pin points, not assumed.

**Fix**: pin only `prepare_data.py` (the one file that actually
constitutes "the prompt contract") via `sys.path` injection, and always
run the *current* `run_benchmark.py`/`train.py` from `main` -- so future
benchmark-runner improvements are never silently pinned away. Verified
this mechanism works exactly as intended: the executed code is current
`run_benchmark.py`, but the `build_prompt` it calls is provably the
pinned worktree's object, not main's. See the `run_pinned` helper in
Setup, below, and the updated cell commands. `train.py` happened to be
byte-identical between `80062bc` and current `main` this time (confirmed
by diff) -- this run wasn't actually affected there, but the same fix
applies to it too, since that was luck, not a guarantee.

## Two findings that update the premise before this can be finalized

### 1. Resolved: production `checkpoint-520` is not lost

Earlier in this session, `training/checkpoints_disk_usage_findings.md`
flagged `checkpoint-520` (the currently-deployed production model,
`gold_v1.2.1`, epoch 40) as apparently gone from local storage, with no
`.onnx` file anywhere in this repo, and handed the question to the
app-side chat. Now that both repos are directly accessible from one
session:

- `thought-organizer-app/scripts/fetch-model.mjs` installs the deployed
  model from a **GitHub Release on `intent-recovery-model` itself**
  (`intent-recovery-model-v0.1.0`, tag `pre-repository-split`, commit
  `2cd31dd`), not from anywhere app-side-only.
- Confirmed via `gh release view intent-recovery-model-v0.1.0 --repo
  ThisIsJohnnyt/intent-recovery-model`: quantized ONNX encoder + merged
  decoder, tokenizer/config files, and a checksummed manifest. Release
  body confirms `google/flan-t5-base`, `gold-v1.0`+`v1.1`+`v1.2`+`v1.2.1`
  (54 examples), 40 epochs — matches checkpoint-520's known provenance
  exactly.
- **This resolves open item #1** in `checkpoints_disk_usage_findings.md`.
  `training/production_checkpoint_recovery_handoff.md`'s recovery framing
  is now obsolete for this item; the checkpoint isn't missing, only
  absent from local `training/checkpoints/` in raw (non-ONNX) form. That
  file should be corrected in a follow-up (not done as part of this
  manifest, to keep this change scoped).

**Caveat this creates**: `run_benchmark.py` loads checkpoints via
`AutoModelForSeq2SeqLM.from_pretrained` (safetensors/HF format only) — it
cannot load the ONNX files directly. Confirmed the training venv already
has `optimum` (2.1.0) and `onnxruntime` (1.28.0) installed, and
`optimum.onnxruntime.ORTModelForSeq2SeqLM` imports successfully — so a
small variant of `run_benchmark.py` using `ORTModelForSeq2SeqLM.from_pretrained`
(pointed at the two release `.onnx` files) instead of `AutoModelForSeq2SeqLM`
can run the strict benchmark harness against checkpoint-520 directly. This
is arguably the *more* faithful "deployment-risk check" than a safetensors
checkpoint would be, since the ONNX-quantized export is exactly what
production actually serves — not a stand-in for it.

### 2. Still open: `checkpoint-600`'s original weights

`checkpoint-600` (`gold_v1.2.2`'s original candidate, seed 42, never
released) was never published anywhere the way checkpoint-520 was — there
is no release, no ONNX export, nothing to recover from the app side. It
remains gone under its original identity. What exists instead:
`checkpoints/gold_v1.2.2-seed17-control/checkpoint-600` and
`.../gold_v1.2.2-seed73-control/checkpoint-600` — real `model.safetensors`
weights, same corpus and step count, but seeds 17/73, not the original 42.
`checkpoints_disk_usage_findings.md` already flags these as **not
confirmed equivalent** to the lost original.

**This needs an explicit decision in joint review**, not something to
resolve unilaterally here: either (a) accept the seed-17/73 replicas as
the working stand-in for "old-trained checkpoint" in the comparisons
below, with that caveat attached to every result, or (b) treat
checkpoint-600 as permanently gone and rely on its recorded historical
benchmark number (13/16 pass rate at seed 42, old prompt) as a read-only
reference that can't be re-run under the new prompt. This manifest
proceeds under option (a) below, since it's the only one that produces a
number rather than an assumption, but flags it plainly wherever it
applies.

### 3. Checked: existing gold_v1.2.2 bullets are not artificially padded

A real risk for "the prompt change is the only experimental variable": if
the existing gold_v1.2.2 ground-truth `bullets` were hand-padded to the
old prompt's "3 to 7" floor, training a new checkpoint on that data under
the *new* prompt wording would train the model to imitate padded targets
while being told not to pad — a second variable, not a clean ablation.
Checked directly: bullet-count distribution across all 66 gold_v1.2.2
examples (`git show HEAD:datasets/synthetic.jsonl`, current committed
state, before the pending uncommitted gold_v1.2.3 hunk) —

| bullets | examples |
|---|---|
| 1 | 4 |
| 2 | 13 |
| 3 | 24 |
| 4 | 18 |
| 5 | 6 |
| 6 | 1 |

17 of 66 examples (26%) already have fewer than 3 bullets. The existing
ground truth was never rigidly padded to a 3-bullet floor despite the old
prompt's wording — training on it unchanged, under the new prompt, is a
clean single-variable change, not a second confound.

## Frozen parameters

- **Corpus**: gold_v1.2.2-only, 66 examples, 60 train / 6 val by
  `split_manifest.json` (existing, frozen, unaffected by the pending
  gold_v1.2.3 hunk since that's a strict append). Old-prompt processed
  copy already exists at `training/data/processed_gold_v1.2.2_control/`.
  New-prompt copy needs regenerating (command below) — not yet done.
- **Seeds**: 17 (screen first), 73 (only if 17 clears the bar below).
  Seed 42 is excluded from the controlled comparison — its original
  `checkpoint-600` reference no longer exists (see finding #2), so there
  is no valid same-seed Cell A to compare a new seed-42 candidate
  against. The historical seed-42 result stays as context only.
- **Steps**: 600 (40 epochs x ceil(60/4)=15 steps/epoch — `train.py`'s
  `num_train_epochs=40` and `per_device_train_batch_size=4` are hardcoded,
  not CLI-configurable, so this falls out automatically from the existing
  corpus size; no `--max-steps` override needed or wanted). Matches the
  step count already implied by "checkpoint-600."
- **Base model / decoding**: `google/flan-t5-base`, `learning_rate=3e-4`,
  `weight_decay=0.01`, `predict_with_generate=True`,
  `generation_max_length=512`, `GENERATION_MAX_NEW_TOKENS=300` at
  benchmark time — all hardcoded in `train.py`/`run_benchmark.py`, not
  touched by `--seed`/`--output-dir`/`--data-dir`, so "unchanged base
  model and decoding settings" holds automatically as long as those three
  flags are the only ones passed.
- **Fingerprints** (both computed via `real_data_private.prompt_contract_fingerprint`
  against the shared fixture `Prompt contract fixture: review the blue
  folder tomorrow?`):
  - Old contract (pre-versioning, no `PROMPT_CONTRACT_VERSION` existed):
    `b325c0640db95f238ac97cc4b254db6347df78144fed0ddb2e6a084bba20e4c5`
  - New contract (`source-determined-bullets-v1`, PR #13 / PR #4):
    `161661198071fd81310681f69381ec8e0287141e1e75b09d3a342414af31ccf1`

## Setup: pinned worktrees + recorded provenance (run once)

Two immutable, side-by-side checkouts instead of repeatedly swapping
`training/prepare_data.py` inside one working tree. Everything below uses
absolute paths, so no command depends on which directory it's launched
from.

```bash
# Run from the repo root, once, first. `pwd -W` (not plain `pwd`), since
# this repo's Python is a native Windows binary invoked from Git Bash --
# plain `pwd`'s POSIX-style path (/c/Users/...) isn't a path Windows
# Python can resolve; `pwd -W` gives the Windows-style equivalent it needs.
export REPO_ROOT="$(pwd -W)"
export PY="$REPO_ROOT/training/venv/Scripts/python.exe"
export OLD_WT="$REPO_ROOT/../irm-study-old-prompt"
export NEW_WT="$REPO_ROOT/../irm-study-new-prompt"

# Must print nothing -- don't proceed on a dirty tree.
git -C "$REPO_ROOT" status --porcelain

# 8d7aa09 = last commit before PR #13 merged (old "3 to 7 lines" prompt).
# 80062bc = PR #13's merge commit (source-determined-bullets-v1 prompt).
git -C "$REPO_ROOT" worktree add "$OLD_WT" 8d7aa09
git -C "$REPO_ROOT" worktree add "$NEW_WT" 80062bc

# Record commit + fingerprint for both, before running anything. Save this
# output alongside the results -- it's the provenance record for every
# cell below.
git -C "$OLD_WT" rev-parse HEAD
"$PY" -c "
import sys; sys.path.insert(0, r'$OLD_WT/training')
import prepare_data as pd, real_data_private as rdp
print('old contract fingerprint:', rdp.prompt_contract_fingerprint(pd.build_prompt(rdp.PROMPT_CONTRACT_FIXTURE)))
"
git -C "$NEW_WT" rev-parse HEAD
"$PY" -c "
import sys; sys.path.insert(0, r'$NEW_WT/training')
import prepare_data as pd, real_data_private as rdp
print('PROMPT_CONTRACT_VERSION:', pd.PROMPT_CONTRACT_VERSION)
print('new contract fingerprint:', rdp.prompt_contract_fingerprint(pd.build_prompt(rdp.PROMPT_CONTRACT_FIXTURE)))
"
```

Expected fingerprints (both already independently verified earlier this
session -- the setup output above should match exactly, or stop and
investigate before running anything else):
- old: `b325c0640db95f238ac97cc4b254db6347df78144fed0ddb2e6a084bba20e4c5`
- new: `161661198071fd81310681f69381ec8e0287141e1e75b09d3a342414af31ccf1`

Remove the worktrees only after every cell below has run and all result
files/provenance are saved: `git -C "$REPO_ROOT" worktree remove "$OLD_WT"`
and same for `$NEW_WT`.

### The corrected pinning pattern (Round 5 fix)

Pins **only** `prepare_data.py` (the prompt contract) to the given
worktree; the script that actually executes is always the *current* one
on `main`, so future benchmark-runner/trainer improvements are never
silently pinned away by an old worktree commit again. Verified directly
(see Round 5, above): the executed code is current `run_benchmark.py`,
but the `build_prompt` it resolves via `import prepare_data` is provably
the pinned worktree's object, not main's.

```bash
"$PY" -c "
import sys
sys.path.insert(0, r'\$OLD_WT/training')   # or \$NEW_WT -- whichever prompt version this cell needs
sys.argv = ['run_benchmark.py', '<benchmark.jsonl>', '<checkpoint_dir>', '<output.json>']
exec(compile(open(r'\$REPO_ROOT/training/run_benchmark.py').read(), 'run_benchmark.py', 'exec'), {'__name__': '__main__'})
"
```

Substitute real absolute paths for the three `sys.argv` entries. The cell
commands below apply this pattern directly (not via a shell-function
wrapper, to keep every command's actual arguments visible and greppable).

## Comparison cells — one same-seed triplet at a time

Screen the seed-17 triplet (A/B/C) first. Only run the seed-73 triplet if
seed 17 clears the material-regression bar defined below. Seed 42 never
gets its own triplet in this study (no valid Cell A, see the correction
above); its historical result is quoted for context only.

Checkpoints and datasets are read from `$REPO_ROOT` throughout (not
duplicated into the worktrees, which only hold the pinned *code*).
`$OLD_WT`/`$NEW_WT` supply `prepare_data.py`'s wording only -- every
`run_benchmark.py`/`train.py` invocation below runs the *current*
`$REPO_ROOT/training/` script via the corrected pinning pattern above,
not the worktree's own possibly-stale copy (Round 5 fix).

### Seed-17 triplet

**A. old-trained + old prompt — reference**
```bash
git -C "$REPO_ROOT" status --porcelain   # must be clean before every cell
"$PY" -c "
import sys
sys.path.insert(0, r'$OLD_WT/training')
sys.argv = ['run_benchmark.py',
    r'$REPO_ROOT/datasets/benchmark/gold_v1.2.1_probes.jsonl',
    r'$REPO_ROOT/training/checkpoints/gold_v1.2.2-seed17-control/checkpoint-600',
    r'$REPO_ROOT/training/gold_v1.2.2_seed17_oldprompt_reference_results.json']
exec(compile(open(r'$REPO_ROOT/training/run_benchmark.py').read(), 'run_benchmark.py', 'exec'), {'__name__': '__main__'})
"
```

**B. old-trained + new prompt — deployment-risk check** (two variants,
both cheap: inference only, no training)

B1, the actual production model (checkpoint-520, ONNX — not seed-specific,
run once total, not once per triplet):

**Not yet implemented** — `run_benchmark_onnx.py` doesn't exist. It needs
writing: a variant of `run_benchmark.py` that loads via
`optimum.onnxruntime.ORTModelForSeq2SeqLM.from_pretrained` (pointed at the
downloaded checkpoint-520 release assets) instead of
`AutoModelForSeq2SeqLM`, and imports `build_prompt` from `$NEW_WT/training`
(checkpoint-520 would be served the new prompt in production, per the
deployment-risk question this cell answers). Not sketching a fake CLI for
it here since it isn't built -- writing it is separate follow-up work, not
required before the seed-17 A/B2/C cells below can run.

B2, the seed-17 `checkpoint-600` replica (safetensors, direct):
```bash
"$PY" -c "
import sys
sys.path.insert(0, r'$NEW_WT/training')
sys.argv = ['run_benchmark.py',
    r'$REPO_ROOT/datasets/benchmark/gold_v1.2.1_probes.jsonl',
    r'$REPO_ROOT/training/checkpoints/gold_v1.2.2-seed17-control/checkpoint-600',
    r'$REPO_ROOT/training/gold_v1.2.2_seed17_newprompt_deployment_risk_results.json']
exec(compile(open(r'$REPO_ROOT/training/run_benchmark.py').read(), 'run_benchmark.py', 'exec'), {'__name__': '__main__'})
"
```

**C. new-trained + new prompt — compatibility candidate, seed 17**
```bash
# Regenerate the gold_v1.2.2-only split under the new prompt (writes a new
# directory, does not touch the existing old-prompt copy). Run once --
# reused by both seed triplets, since the split itself isn't seed-dependent.
# Written into $NEW_WT/training/ so its own `import prepare_data as pd`
# resolves to the pinned new-contract copy.
cat > "$NEW_WT/training/_regen_gold_v1.2.2_newprompt.py" <<'PY'
import os, subprocess, json
from pathlib import Path
import prepare_data as pd

repo_root = os.environ["REPO_ROOT"]
synthetic_66 = subprocess.run(
    ["git", "-C", repo_root, "show", "8d7aa09:datasets/synthetic.jsonl"],
    capture_output=True, encoding="utf-8", check=True,
).stdout
records = [pd.validate_record(json.loads(l), "synthetic.jsonl", i)
           for i, l in enumerate(synthetic_66.splitlines(), 1) if l.strip()]
val_hashes = pd.load_val_hashes(pd.SPLIT_MANIFEST_PATH)
train_split, val_split = pd.split_by_manifest(records, val_hashes)

out = Path(repo_root) / "training" / "data" / "processed_gold_v1.2.2_control_newprompt"
out.mkdir(parents=True, exist_ok=True)
for name, split in [("train.jsonl", train_split), ("val.jsonl", val_split)]:
    with (out / name).open("w", encoding="utf-8") as f:
        for r in split:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(name, len(split))
PY
"$PY" "$NEW_WT/training/_regen_gold_v1.2.2_newprompt.py"
rm "$NEW_WT/training/_regen_gold_v1.2.2_newprompt.py"

# train.py: current $REPO_ROOT code, pinned prompt contract. train.py
# happened to be byte-identical between 80062bc and main this round
# (confirmed by diff), but pin it the same way anyway -- that was luck,
# not a guarantee for a future run.
"$PY" -c "
import sys
sys.path.insert(0, r'$NEW_WT/training')
sys.argv = ['train.py', '--seed', '17',
    '--output-dir', r'$REPO_ROOT/training/checkpoints/gold_v1.2.2-newprompt-seed17',
    '--data-dir', r'$REPO_ROOT/training/data/processed_gold_v1.2.2_control_newprompt']
exec(compile(open(r'$REPO_ROOT/training/train.py').read(), 'train.py', 'exec'), {'__name__': '__main__'})
"
"$PY" -c "
import sys
sys.path.insert(0, r'$NEW_WT/training')
sys.argv = ['run_benchmark.py',
    r'$REPO_ROOT/datasets/benchmark/gold_v1.2.1_probes.jsonl',
    r'$REPO_ROOT/training/checkpoints/gold_v1.2.2-newprompt-seed17/final',
    r'$REPO_ROOT/training/gold_v1.2.2_seed17_newprompt_candidate_results.json']
exec(compile(open(r'$REPO_ROOT/training/run_benchmark.py').read(), 'run_benchmark.py', 'exec'), {'__name__': '__main__'})
"
"$PY" -c "
import sys
sys.path.insert(0, r'$NEW_WT/training')
sys.argv = ['run_benchmark.py',
    r'$REPO_ROOT/datasets/benchmark/source_determined_bullets_acceptance.jsonl',
    r'$REPO_ROOT/training/checkpoints/gold_v1.2.2-newprompt-seed17/final',
    r'$REPO_ROOT/training/gold_v1.2.2_seed17_newprompt_candidate_bullets_acceptance_results.json']
exec(compile(open(r'$REPO_ROOT/training/run_benchmark.py').read(), 'run_benchmark.py', 'exec'), {'__name__': '__main__'})
"
```

### Seed-73 triplet — only if the seed-17 triplet clears the bar

Identical structure and identical `$OLD_WT`/`$NEW_WT`/split, seed 73
throughout: Cell A against
`$REPO_ROOT/training/checkpoints/gold_v1.2.2-seed73-control/checkpoint-600`
via `$OLD_WT`; Cell B2 against the same checkpoint via `$NEW_WT` (B1,
checkpoint-520, doesn't repeat — it's not seed-specific); Cell C trains
`$REPO_ROOT/training/checkpoints/gold_v1.2.2-newprompt-seed73` from the
already-regenerated `data/processed_gold_v1.2.2_control_newprompt` split
(no need to regenerate it again), `--seed 73`, then runs both probe files
against it exactly as in the seed-17 triplet.

`train.py --output-dir` defaults to refusing a non-empty target directory
(`--force` is off by default, specifically because this is the mechanism
that silently pruned the original checkpoint-520 and checkpoint-600 via
`save_total_limit` output-dir reuse) — every command above uses a fresh,
never-before-used directory name, so this protection shouldn't even need
to trigger.

## Material regression — pinned definition (per ChatGPT's 2026-08-02 correction)

Evaluated same-seed (Cell C vs. that seed's own Cell A), not against the
other seed or the historical seed-42 number. A candidate avoids material
regression only if **all four** hold:

1. **16/16 format validity** — every one of the 16 `gold_v1.2.1_probes.jsonl`
   outputs parses as well-formed (narrative/bullets/actions markers
   present, correctly ordered).
2. **No regression-guard pass becomes a failure** — every probe marked
   `"status": "regression_guard"` that passed under that seed's Cell A
   must still pass under Cell C.
3. **No reduction in overall strict passes** — Cell C's total pass count
   across all 16 probes must be >= that seed's Cell A pass count.
4. **Passes the source-determined-bullets acceptance set** —
   `datasets/benchmark/source_determined_bullets_acceptance.jsonl` (5
   draft dummy cases, `"status": "acceptance_gate"`, covering the floor, a
   natural count, the 7-line ceiling, and the "don't repeat content to
   hit a target count" failure mode for both bullets and action items).
   Reported separately via `report_benchmark.py`'s "Acceptance gates
   passed" section, never folded into the regression-guard or
   negative-example counts. A case passes only under the full strict
   rule: format valid, every dimension in that case's
   `required_semantic_dimensions` (`topic_completeness`,
   `unsupported_addition_resistance`) scored exactly `2` -- not merely
   non-null-or-2, which would fail-open on an unscored result, see Round 3
   correction below -- and every capability check exactly `true`,
   including `BULLET_COUNT_RULE_SATISFIED`/`ACTION_COUNT_RULE_SATISFIED`,
   evaluated against that case's `bullet_count_rule`/`action_count_rule`
   (`operator`: `exact` or `max`, `value`: N), not just checked as a raw
   count match. This is the one check with no Cell A equivalent, since
   Cell A ran under the old contract and wouldn't be expected to satisfy
   the new rule -- it's evaluated as a standalone pass/fail against the
   candidate only.

This acceptance set is a draft proposal (revised once already per
ChatGPT's fixture-by-fixture review — see Round 2 correction, above),
still not independently re-reviewed after that revision — flagging that
explicitly rather than treating it as settled.

## Release gate

`intent-recovery-model` PR #13 merged to `main` on 2026-08-02 (ahead of
joint design review completing, along with this manifest's original,
confound-containing version as PR #14). That doesn't change the substance
of the gate: nothing deploys, and `thought-organizer-app` PR #4 stays
open/unmerged, until a same-seed-controlled Cell C checkpoint passes all
four material-regression checks above. This manifest only prepares the
comparison; it doesn't authorize running it. Compute starts once this
design itself -- not PR #4 -- is reviewed and marked Aligned (see the
circular-dependency fix at the top of this document).
