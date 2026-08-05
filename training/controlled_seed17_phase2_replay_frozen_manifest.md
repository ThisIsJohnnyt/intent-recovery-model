# Controlled Seed-17 Phase-2 Replay — Frozen Manifest

**Status:** Draft package for joint ChatGPT/Claude review. Uncommitted. Authorizes no compute.
**Governing document:** `training/phase2_seed17_replay_interpretation_and_outcome_matrix_chatgpt.md` — this
manifest implements exactly the scope that document defines; where the two differ, the governing document is
authoritative and this manifest is wrong and needs correcting, not the other way around.
**Authorized by (package implementation only):** Johnny, 2026-08-04 — "I authorize Claude to author the
uncommitted seed-17 Phase-2 replay package defined by
`phase2_seed17_replay_interpretation_and_outcome_matrix_chatgpt.md`... Claude may perform static validation,
dummy-subprocess tests, and dry-run receipt generation only." Training, inference, benchmark execution,
semantic scoring, corpus mutation, derivation changes, seed 73, export, deployment, activation, commit, and
push are all explicitly excluded from this authorization.

## 1. What this replay tests

Two independent training runs from the Phase-2 candidate corpus (78 records: 66 immutable R2 parent + 12
reviewed proposal examples), both seed 17, both starting fresh from the same pinned base-model snapshot:

| Run | Role | Step policy | Expected steps |
|---|---|---|---|
| **Primary** | Sole decision-bearing Phase-2 candidate | Natural 40 epochs, `--max-steps` omitted | 720 |
| **Control** | Step-budget diagnostic only, never a substitute for the primary | `--max-steps=600` | 600 |

The control exists solely to explain whether any Phase-2 result is sensitive to the extra 120 optimizer steps
the larger (72-record, vs. R2's 60-record) train split creates under a fixed epoch count — the same
optimizer-step confound `gold_v1.2.3_groupscreen_seed17_scoring.md` identified and required a step-matched
control for previously. It can never be relabeled as primary after the fact; a 600-step regimen would need
its own new proposal and authorization.

## 2. Pinned evidence (all independently re-verified against the real repository before being pinned here)

| Artifact | SHA-256 |
|---|---|
| Candidate corpus (`training/gold_v1.2.2_phase2_derived_candidate.jsonl`, 78 records) | `f738f9eba2e85086bf6019bffdd27410b7add5c566c086a1b3627703e14ad52b` |
| Training split (`.../train.jsonl`, 72 records) | `02d81b3891a517a41cf3261b733f70f5268710b79b18e3b3819e8dbbcdd7cafb` |
| Validation split (`.../val.jsonl`, 6 records) | `83abbc796187860b511b2c18c964b0757df4bc343ace50862ea15bd590715294` |
| Canonical training-data fingerprint (72 train + 6 val) | `9d6817152087685b653830ad671f9304e4226b095a202ca57f5ca52bc3a14c1f` |
| Protected benchmark (16 records) | `044708641c8dd584f334f16bde21ed89550bb7c464160827433f825eb0c48e94` |
| Acceptance benchmark (10 records) | `b8fe4d4178e5b508757db998eacb1ee979518697c8df759ba1739227c88d448e` |
| `datasets/real_validation.jsonl` (must be byte-empty) | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (the well-known empty-input hash) |
| Base model snapshot | `google/flan-t5-base` @ `7bcac572ce56db69c1ea7c8af255c5d7c9672fc2` (unchanged from the R2 replay, re-verified against the local HF cache this round, not carried forward without re-checking) |
| Pinned commit this package was built against | `d90fc13add15be1ce67ea7b2bb4429e978305e74` |

Every one of these values was recomputed fresh from the real files during this session, not copied from the
governing document without independent re-derivation. The gate-6 pass set below was independently reproduced
via `report_benchmark.v2_result_passes()` against the real, committed R2 scored file — not merely transcribed
from the governing document's own claim — and matched exactly: `PASS = {01,03,04,05,06,07,09,10,12,14,15,16}`,
`FAIL = {02,08,11,13}`.

## 3. What must be identical between the two runs, and what must differ

Identical: seed/data seed (17), `train.jsonl`/`val.jsonl`, model and tokenizer snapshot, prompt contract and
serialization, batch size 4, learning rate `3e-4`, weight decay `0.01`, optimizer family, precision (bf16 on
CUDA), token limits, generation settings (`max_new_tokens=300`, `repetition_penalty=1.3`), checkpoint-selection
behavior (`load_best_model_at_end=False`), executable code and dependency versions, both benchmark definitions
and scorer, hardware/runtime environment.

Different: only the step policy (`--max-steps` omitted vs. `=600`) and the output paths that keep every
artifact separate (`primary/` vs. `control/` subdirectories of one experiment root).

Neither run initializes from, resumes from, or reuses optimizer/scheduler state from the other — both call
`train.py`'s own `AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL)` independently. Per the governing
document's §3: since `max_steps` also determines the default linear LR scheduler's total-step count, the two
runs can differ in scheduler trajectory before step 600 as well as in total updates — this is a step-budget
diagnostic, not a claim that the control reproduces the first 600 updates of the primary.

## 4. Preflight (all must pass before the experiment root is created)

**Revision note (2026-08-04):** ChatGPT's review of the first draft found that requiring `HEAD` to equal the
commit this package was built against (`d90fc13`) would make the *committed* package permanently unable to
pass its own preflight, since committing it necessarily advances `HEAD` past that commit. Fixed below — `d90fc13`
is now `PINNED_PARENT_COMMIT`, the required parent of `HEAD`, not a value `HEAD` itself must equal.

1. `HEAD` matches `origin/main` (no diverged local branch), **and** `HEAD` is a *direct* child of the pinned
   parent commit `d90fc13add15be1ce67ea7b2bb4429e978305e74` whose commit delta contains **exactly** the six
   reviewed package files listed in §8 — no more (an unreviewed file riding along in the same commit) and no
   less (an incompletely-committed package). The pre-execution receipt records the resolved commit as an
   explicit top-level `package_commit` field, which is what the later execution authorization must name.
2. Working tree is clean.
3. Installed dependency versions exactly match the lock (`torch==2.11.0+cu128`, `transformers==4.57.6`,
   `datasets==5.0.0`, `accelerate==1.14.0`, `sentencepiece==0.2.2`).
4. The full local executable import closure — computed by statically parsing the AST of
   `run_seed17_phase2_replay.py`, `train.py`, `run_benchmark.py`, and `report_benchmark.py`, then recursively
   following every repo-local `import`/`from` statement found — matches the lock's frozen file *set* exactly,
   and every file in it matches its pinned fingerprint. This is not a manually curated list: the closure
   currently resolves to 12 files, two of which (`real_data_manifest.py`, `real_data_eval_logging.py`) were
   *not* named in the governing document's own minimum list and were only discovered by actually walking the
   graph — direct evidence the automated approach catches more than manual enumeration would have.
5. All five governing inputs (candidate corpus, both splits, both benchmarks) match their pinned fingerprints
   and required record counts (78/72/6/16/10).
6. `datasets/real_validation.jsonl` is byte-empty (both by size and by fingerprint) — `train.py` always calls
   `evaluate_real_validation.run_real_validation_evaluation` after training, which reads this exact file; a
   populated file would let undeclared private-data inference into a replay whose authorized evaluation scope
   is only the frozen 26 benchmark cases.
7. The 72/6 split and canonical training-data fingerprint recompute exactly from the pinned inputs.
8. Neither `primary/` nor `control/` (nor the experiment root itself) already exists.
9. `torch.cuda.is_available()` matches the frozen expectation (`True`, independently confirmed from the R2
   replay's own receipt rather than assumed).
10. Both commands resolve to seed 17 and the pinned Phase-2 data directory; the primary command has no
    `--max-steps` argument at all; the control command has exactly one `--max-steps=600` argument — checked
    by directly inspecting the constructed argument lists, not just trusted from the construction code.
11. The pinned base-model snapshot's revision and every file's SHA-256 match, read from the local HF cache
    only, never the network.

## 5. Execution and artifact isolation

Order: primary train → primary protected-16 → primary acceptance-10 → control train → control protected-16 →
control acceptance-10. The experiment root and both `primary/`/`control/` subdirectories are created via
`Path.mkdir(exist_ok=False)` — atomic, never reused. Each run has its own `checkpoint/`, `protected16_results.json`,
`acceptance10_results.json`, and three log files (`train_log.txt`, `protected16_log.txt`, `acceptance10_log.txt`).
The pre-execution receipt (git state, both full command sequences, environment, shared configuration, declared
differences, the gate-6 pass set, and every live fingerprint) is written with exclusive creation before any
subprocess starts.

Every subprocess writes stdout/stderr directly to an exclusively-opened log file (never a shell pipe, never
buffered in memory) and its true exit code is checked immediately — any nonzero exit stops the sequence hard,
with partial artifacts and logs left in place, exactly as `run_seed17_r2_replay.py`'s already-reviewed logging
design requires.

After each training step, `verify_completed_steps()` reads the highest-numbered `checkpoint-N/trainer_state.json`
Trainer itself writes and requires `global_step` to equal exactly 720 (primary) or 600 (control) — a clean
subprocess exit code alone does not prove the intended step count ran; a mismatch is an invalid experiment
(P2-X) regardless of exit status.

The wrapper produces raw benchmark result scaffolds only. It never fills semantic scores and never selects a
preferred checkpoint.

**Revision note (2026-08-04):** ChatGPT's review also found that a benchmark subprocess exiting 0 was never
followed by any check that the result file it wrote is actually valid — the governing document's §6.1
explicitly classifies a missing or invalid raw result as an invalid experiment (P2-X). Fixed: after each of
the four evaluation subprocesses, `verify_raw_result_artifact()` fails closed unless the result file exists,
parses as a JSON array, has exactly the expected record count (16 or 10), its IDs appear in exactly the
benchmark file's own order, every record has a non-empty `raw_output`, and no record's semantic score fields
are filled.

**Second revision note (2026-08-04):** ChatGPT's second-pass review found the first version of this check only
validated `scores` — a record with `capability_checks` already filled in and a non-empty `failure_labels`
still passed as "no semantic scores filled." Reproduced directly against a real protected-16 raw artifact
before fixing. Now also requires: `scores` has exactly the four expected dimension keys (confirmed identical
across every protected and acceptance probe); `capability_checks` keys exactly match that specific probe's own
`primary_checks` from the benchmark file (some probes, e.g. protected `13`–`16`, legitimately have zero
`primary_checks` and an empty `capability_checks` dict — confirmed directly against the real benchmark file,
not assumed), every value null; and `failure_labels` is exactly `[]`.

## 6. Frozen gates and the outcome matrix (encoded for later use, not applied by this package)

The same six gates from `phase2_seed17_replay_interpretation_and_outcome_matrix_chatgpt.md` §5 apply
independently to each run's semantic scoring once that happens — a separate, later, separately-authorized
step. Gate 6's pass set is pinned in code as `GATE6_REQUIRED_PASS_SET` (13 probes: the 12 R2-passing probes
plus repaired probe 13), so future scoring-verification tooling can import it directly rather than re-deriving
or re-typing it. The P2-A/B/C/D/X outcome cells from the governing document's §6 are not evaluated by this
package — they require ChatGPT scoring and Claude verification of both runs' real outputs, neither of which
this authorization covers.

## 7. Explicit non-authorizations (unchanged from the governing document)

This package, once built, authorizes nothing beyond its own existence as a reviewable draft. Training,
inference, benchmark execution, semantic scoring, corpus mutation, derivation changes, seed 73, export,
deployment, activation, commit, and push all remain separately unauthorized. Running the wrapper with
`--confirm-execute` requires Johnny to separately name this exact replay after joint review of the committed
package — possessing the flag is not authorization, exactly as the R2 replay's own gate required.

## 8. Deliverables in this package

**Revision note (2026-08-04):** ChatGPT's review found the governing document's first save had silently
stripped trailing markdown hard-line-break spaces on four header lines (a `Write`-tool artifact, not a
content change) — the "saved verbatim" claim below was not true as originally saved. Confirmed by hashing a
fresh re-paste of the document, which matched ChatGPT's independently-computed hash exactly; the file was
then restored to that exact byte-faithful content.

| File | Role | SHA-256 |
|---|---|---|
| `training/phase2_seed17_replay_interpretation_and_outcome_matrix_chatgpt.md` | Governing document (ChatGPT-authored, now genuinely byte-faithful) | `1a80176849941a3a0582b82f31978d2285644ec99af489fbefa16488183585f9` |
| `training/controlled_seed17_phase2_replay_frozen_manifest.md` | This file | (recomputed after each revision, not pinned here to avoid self-reference) |
| `training/controlled_seed17_phase2_replay_frozen_fingerprints.json` | External fingerprint lock | (regenerated whenever any locked file changes) |
| `training/run_seed17_phase2_replay.py` | Plan-only-by-default execution wrapper | (pinned inside the lock file itself) |
| `training/test_run_seed17_phase2_replay.py` | Dummy-subprocess test suite | (not lock-pinned; verified by running it) |
| `training/controlled_seed17_phase2_replay_manifest_dryrun_receipt_sample.json` | Labeled dry-run receipt sample | (regenerated alongside the wrapper) |
