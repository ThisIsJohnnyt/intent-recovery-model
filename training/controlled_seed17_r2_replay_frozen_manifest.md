# Controlled Seed-17 R2 Replay — Frozen Experiment Manifest

**Governing protocol:** `training/controlled_seed17_r2_replay_protocol.md` (SHA-256
`bcb72c22f19997f183312fdc4070acd086ebac8efe2b45799dd8ac494f2d759b`)
**Verification:** `training/controlled_seed17_r2_replay_protocol_claude_verification.md`
**§4.3 candidate-split derivation:** commit `54835eb` on `main`
**ChatGPT validity decision (design):** VALID ONE-VARIABLE REPLAY, no disagreement
**Manifest revision:** 4 (2026-08-03) — revision 2 resolved ChatGPT's four execution-readiness
findings on revision 1 (base-model/tokenizer pinning, raw log preservation, fail-closed outputs,
pre-execution receipt; revision 1's SHA-256 `942e77a1da1f3a3b159088396618395127cd21b509f2348b44de60733c1e06b4`
superseded). ChatGPT's review of revision 2's actual code (`run_seed17_r2_replay.py`) then found
two further substantive gaps, both fixed in revision 3: (1) fingerprints/dependency versions
were being *recorded* in the receipt but never *enforced* against a frozen expected value, and
both benchmark datasets were missing from the governing-input list entirely; (2) the log-capture
mechanism buffered everything in Python memory until the subprocess had already finished, so an
interruption of the wrapper itself would have lost all output, not just the tail. Revision 3's own
SHA-256 `c28b8dca958f7fb5c8386773035c17f8e5c9b9b2d451e9c4678b53352a83d4ae` is superseded by this
revision. ChatGPT's byte-level review of revision 3 found that §2.1 below still carried the same
overclaim its own top-of-file note said was already fixed elsewhere ("proven to match"/"Proof the
baseline checkpoint actually used this snapshot") — corrected in this revision to "strong
provenance evidence," consistent with the wording already used in `run_seed17_r2_replay.py`'s own
docstrings. Also corrected: this note previously claimed the file's own hash "is recorded in the
fingerprints table at the end" — false, since that table row explicitly cannot contain a
self-referential hash; the actual hash is reported externally, in chat and in the eventual commit
message, as the fingerprints table itself already correctly said.
**Manifest status:** Drafted for Johnny's review. **Does not itself authorize training,
inference, the 26-case evaluation, seed 73, or deployment** — those require Johnny naming this
replay specifically, per the protocol's §5 authorization gate.

This document exists so that, if and when Johnny authorizes execution, there is nothing left to
decide or improvise — every value below is either pinned to a fingerprint already verified against
the real repository, or is a literal, ready-to-run command. Execution itself is now driven by
`training/run_seed17_r2_replay.py` (see §3), not by hand-typed commands, so the four
execution-readiness gaps below are enforced by code, not by manifest prose alone.

## 1. The one authorized independent variable

| | Baseline (failed gate, commit `07de0d4`/`e37aeda`) | Candidate (this replay) |
|---|---|---|
| Training-target source | `training/data/processed_gold_v1.2.2_v2contract_seed17/{train,val}.jsonl` | `training/data/processed_gold_v1.2.2_r2_v2contract_seed17/{train,val}.jsonl` |
| `train.jsonl` fingerprint | `d947ed77da258312373a6f7eddbabff4d56a0e66f272facb822d3d7cbc748628` | `ed7989f7abb9df64162f26f3d331824770a86649b7587ec3644a969f6e965e68` |
| `val.jsonl` fingerprint | `83abbc796187860b511b2c18c964b0757df4bc343ace50862ea15bd590715294` | `83abbc796187860b511b2c18c964b0757df4bc343ace50862ea15bd590715294` (byte-identical) |
| Canonical training-data fingerprint | `e548e0b633ac1ca11b109adbf88ddbda95a42add38d93f524b700f4762092fd3` | `e294c29f0497800d85fc7a15fdd8341471413e98627b5b86ab202fb22e386abc` |

Only 3 of 66 records differ, only in `output`/`v1_target`/`v2_target`, exactly matching
`ti-001`/`ti-002`/`ti-003` — see `training/data/processed_gold_v1.2.2_r2_v2contract_seed17/
original_vs_r2_diff.json` for the full before/after content. Everything else below is identical
between baseline and candidate.

## 2. Frozen variables (recovered from the committed baseline, independently verified)

| Variable | Frozen value | Evidence |
|---|---|---|
| Base model | `google/flan-t5-base`, **pinned to Hugging Face snapshot revision `7bcac572ce56db69c1ea7c8af255c5d7c9672fc2`** | Located via `huggingface_hub.scan_cache_dir()` against the local cache — see §2.1 |
| Tokenizer | Bundled with the pinned model snapshot above; `spiece.model` (the raw SentencePiece vocabulary, never re-serialized by `save_pretrained`) confirmed **byte-identical** between the cached snapshot and the already-committed baseline checkpoint | see §2.1 |
| Prompt contract | v2 typed-marker (`###BULLET###`/`###ACTION###`), `prompt_contract_v2_candidate.py` | fixture fingerprint `e691fd12ee51b322b93311cf483d2fbb4bb921ac8a1319e07420fae098ea0cb9`, reconfirmed live via `contract_adapters.select_contract_adapter("v2")` |
| Preprocessing/serialization | `build_v2_train_val_split` (`prepare_v2_training_data.py`, reused unmodified by `prepare_v2_r2_training_data.py`) | both scripts unchanged since `07de0d4` |
| Train/val membership + order | 60/6, `split_manifest.json`, unchanged | fingerprint `24610be8c5b91be13b064acaaab4f8bbae59b0ec175e66d1fb8ccb94cd049485`; membership+order re-verified identical in §4.3 |
| Seed | **17** | — |
| Epochs / effective steps | 40 epochs → 600 optimizer steps at this train-set size | `train.py` `num_train_epochs=40`; baseline run logged exactly 600/600, epoch 40.0 |
| Batch size | `per_device_train_batch_size=4` | `train.py` |
| Learning rate | `3e-4` | `train.py` |
| Optimizer/scheduler | HF `Seq2SeqTrainingArguments` defaults (AdamW, linear schedule) — unchanged from baseline | `train.py` |
| Checkpoint-selection rule | `load_best_model_at_end=False` — final epoch used directly, no best-checkpoint search | `train.py` |
| Precision | `bf16=True` (CUDA) | `train.py` |
| Max input tokens | 512 | `train.py`/`run_benchmark.py` `MAX_INPUT_TOKENS` |
| Max target tokens (training) | 512 | `train.py` `MAX_TARGET_TOKENS` |
| Generation length | `max_new_tokens=300` | `train.py`/`run_benchmark.py` `GENERATION_MAX_NEW_TOKENS` |
| Decoding | Greedy (no `num_beams`/`do_sample` override anywhere in the generate() call or the checkpoint's `generation_config.json` → HF defaults to greedy), `repetition_penalty=1.3` | `run_benchmark.py:218-222`; baseline checkpoint's `generation_config.json` has no beam/sampling override |
| Runtime/dependencies | `torch==2.11.0+cu128`, `transformers==4.57.6`, `datasets==5.0.0`, `accelerate==1.14.0`, `sentencepiece==0.2.2` | `training/requirements.txt` (unchanged since `ed58cd0`, an ancestor of `07de0d4`); confirmed installed venv matches exactly |
| Evaluation set (26 cases) | 16 protected (`datasets/benchmark/gold_v1.2.1_probes.jsonl`) + 10 v2 acceptance (`datasets/benchmark/source_determined_items_v2_acceptance_draft.jsonl`) | fingerprints `044708641c8dd584f334f16bde21ed89550bb7c464160827433f825eb0c48e94` / `b8fe4d4178e5b508757db998eacb1ee979518697c8df759ba1739227c88d448e`; neither modified since before `07de0d4` |
| Evaluator/scorer | `run_benchmark.py --contract=v2`, `report_benchmark.py --contract=v2` | both unchanged since `07de0d4` (confirmed via `git log 07de0d4..HEAD`) |
| Acceptance gate | The exact 6-gate frozen structure from the baseline scoring (`e37aeda`): protected-16 format validity, v2-acceptance format validity, v2-acceptance count-rule conformance, v2-acceptance combined strict pass, protected-16 strict pass vs. Cell A, same-seed regression-guard preservation | `report_benchmark.py`'s unmodified `probe_passes`/`v2_result_passes`/etc. |
| Output/artifact schema | Identical result-JSON shape produced by `run_benchmark.py --contract=v2` | unchanged code |

### 2.1 Base-model/tokenizer snapshot pin (resolves finding 1)

`google/flan-t5-base` names a Hub repository, not immutable bytes — resolved here to the exact
cached snapshot, supported by strong provenance evidence that it matches what the baseline
checkpoint actually used:

- **Pinned revision (commit hash):** `7bcac572ce56db69c1ea7c8af255c5d7c9672fc2` (the local cache's
  only cached revision for this repo; `refs/main` also points here).
- **File-level fingerprints**, independently recomputed by hashing each file the snapshot's
  symlinks resolve to:

  | File | SHA-256 |
  |---|---|
  | `config.json` | `7c1853dbfa0e4aac093eb109a358b6ab25fe86b7c15185a91322f0ed26f0f940` |
  | `generation_config.json` | `f5a1c7e2be8092018d8835128987edf0111637dd98e90599cc80310fef75d95a` |
  | `model.safetensors` | `1dfb70afdcedceb9f9fae2f9b68e004ad934361fb35b9b2bd50b45ea90790fc8` |
  | `special_tokens_map.json` | `5c87151ef0f72a99d1f766a4c418bd2a1f90aaa30a8e22fe5eca9641daebb64f` |
  | `spiece.model` | `d60acb128cf7b7f2536e8f38a5b18a05535c9e14c7a355904270e15b0945ea86` |
  | `tokenizer.json` | `fe2ebbbbde2985be723e0ce18217853e4020c5e9d35bd07be2c27ab9d3ead57a` |
  | `tokenizer_config.json` | `4c55124402e4ce48c7125d04b9af152a125eda9e7c80829f8f99f2ec69f3f68d` |

- **Strong provenance evidence the baseline checkpoint used this snapshot** (not independent proof
  of base-model *weight* identity — see `verify_baseline_checkpoint_used_pinned_snapshot()`'s own
  docstring in `run_seed17_r2_replay.py` for why fine-tuning rules out a direct weight-level byte
  comparison): `spiece.model` — the raw SentencePiece vocabulary binary, never re-serialized by
  `save_pretrained` — is byte-identical between the cached snapshot and
  `training/checkpoints/gold_v1.2.2-v2contract-seed17/final/spiece.model`, direct proof of
  *tokenizer* identity specifically. `config.json`'s architecture parameters (`d_ff`, `d_kv`,
  `d_model`, layer/head counts, `vocab_size`, etc.) match exactly between the two; the only
  differences are `transformers_version` (4.23.1 in the originally-cached file vs. 4.57.6 in the
  checkpoint) and a few newer-library default fields (`classifier_dropout`, `dense_act_fn`,
  `dtype`, `is_gated_act`) that `save_pretrained` adds on write, not a different model.
  `tokenizer.json`/`tokenizer_config.json`/`special_tokens_map.json` differ only in the same
  transformers-version re-serialization (bare-string special tokens upgraded to structured
  `AddedToken` dicts) — same 100 `additional_special_tokens`, same content, not a different
  vocabulary.
- **Forcing the replay to use only this snapshot**: `run_seed17_r2_replay.py` runs both training
  and evaluation subprocesses with `HF_HUB_OFFLINE=1`/`TRANSFORMERS_OFFLINE=1` set, so no network
  fetch can occur regardless of what the Hub serves later, and it calls
  `verify_pinned_base_model_snapshot()` as a preflight step that fails closed if the local cache's
  revision or any file's fingerprint has drifted from the pinned values above.

## 3. Execution: `run_seed17_r2_replay.py` (resolves findings 2, 3, and 4)

Hand-typed commands (as in manifest revision 1) are superseded by a single wrapper script,
`training/run_seed17_r2_replay.py`, covered by `training/test_run_seed17_r2_replay.py` (27
dummy-subprocess/real-repository tests, all passing; the real `train.py`/`run_benchmark.py` are
never invoked by the tests). Its `main()` refuses to do anything beyond print the planned command
sequence unless invoked with `--confirm-execute` — passing that flag is not itself authorization;
running it for real still requires Johnny naming this replay specifically, per the protocol's own
§5 gate. No such run has been performed.

```
python run_seed17_r2_replay.py --confirm-execute
```

What it does, in order, all inside one atomically-created exclusive directory
(`training/controlled_seed17_r2_replay_run/`, `Path.mkdir(exist_ok=False)` — fails closed if it
already exists, closing the race between "confirmed the name is unused" and actual execution;
resolves finding 3):

1. **Preflight**, all before the experiment directory is even created:
   - `verify_clean_working_tree()` (fixes the second-review gap) — fails closed on any uncommitted
     diff. This necessarily means this round's own deliverables (this manifest, the wrapper, its
     tests, the lock file below) must be committed before a real run, not left uncommitted as they
     are right now.
   - `verify_pinned_dependency_versions()` (fixes the second-review gap) — fails closed if any of
     `torch`/`transformers`/`datasets`/`accelerate`/`sentencepiece` installed in the venv differs
     from the pinned versions.
   - `verify_frozen_executable_code()` and `verify_frozen_governing_inputs()` (fix the second-review
     gap) — each file listed is re-fingerprinted live and compared against
     `training/controlled_seed17_r2_replay_frozen_fingerprints.json`, an external lock file kept
     separate from the wrapper's own source specifically so the wrapper's own hash can be pinned
     there too, without the self-reference problem of a file asserting its own hash inside itself.
     Fails closed on any mismatch, missing file, or unexpected extra file — for either the 8
     executable-code files (including both scorer files and both contract files) or the 7 governing
     inputs (candidate/baseline corpora, split manifest, candidate train/val splits, **and now both
     benchmark datasets**, which the first wrapper draft omitted entirely).
   - `verify_pinned_base_model_snapshot()`, then `verify_baseline_checkpoint_used_pinned_snapshot()`
     against the real baseline checkpoint (resolves finding 1).
2. **Receipt** (resolves finding 4): `build_receipt()` writes `receipt.json` via exclusive file
   creation, before any subprocess starts. Contents: UTC timestamp; checked-out commit,
   `origin/main` commit, and working-tree cleanliness (`git status --porcelain`); the exact planned
   commands; the live environment (interpreter version, installed `torch`/`transformers`/
   `datasets`/`accelerate`/`sentencepiece`/`huggingface_hub` versions, CUDA availability); the
   resolved configuration (seed, data dir, checkpoint dir, contract, pointers to this manifest and
   the governing protocol); the pinned base-model snapshot info; and SHA-256 fingerprints of every
   piece of executable code this replay depends on and every governing input file. A dry-run sample
   demonstrating the exact shape (regenerated 2026-08-03 against the current code, not tied to any
   real execution) sits, uncommitted like everything else in this round, at
   `training/controlled_seed17_r2_replay_manifest_dryrun_receipt_sample.json` — the real receipt for
   an actual run is generated fresh at that time, since git state and timestamps will differ by then.
3. **Training**: `train.py --seed 17 --data-dir data/processed_gold_v1.2.2_r2_v2contract_seed17
   --output-dir controlled_seed17_r2_replay_run/checkpoint`, run via `run_logged_subprocess()`
   (resolves finding 2, corrected further after the second review found the first fix still
   buffered everything in Python memory until the subprocess finished — the log file is now opened
   exclusively *before* the subprocess starts and passed directly as its `stdout`
   (`stderr=subprocess.STDOUT`), so the OS writes output to disk as it's produced; a partial log
   survives even if the wrapper process itself is interrupted mid-run, and this is still never a
   shell pipe, so no `pipefail` concern either), with `HF_HUB_OFFLINE=1`/`TRANSFORMERS_OFFLINE=1`
   set. `require_success()` raises immediately on any nonzero exit code — a hard stop, never an
   improvised rerun.
4. **Evaluation**: both `run_benchmark.py --contract=v2` commands (protected 16, then acceptance
   10), same logging/exit-code/offline-env treatment, writing to
   `controlled_seed17_r2_replay_run/protected16_results.json` /
   `acceptance10_results.json` and their own log files. Both produce raw/unscored result
   scaffolds (`scores`/`capability_checks` null) — semantic scoring is a separate subsequent step
   (ChatGPT scores, Claude independently re-verifies), same as every prior round this project.

## 4. Execution-safety (protocol §4.4)

- Single exclusive experiment directory (`controlled_seed17_r2_replay_run/`) covers the receipt,
  checkpoint, both result files, and all three logs — one atomic existence check protects
  everything, rather than several independent checks that could race against each other.
- Every preflight check in §3 step 1 — clean tree, dependency versions, executable code, governing
  inputs (now including both benchmark datasets), base-model snapshot, baseline checkpoint
  provenance — runs and must pass before the experiment directory is even created.
- No baseline artifact (`checkpoints/gold_v1.2.2-v2contract-seed17/`, the two baseline result
  files, or anything under `training/data/processed_gold_v1.2.2_v2contract_seed17/`) is read for
  writing at any point — only for the comparison step afterward.
- No application export, deployment, or production path is invoked.

## 5. Comparison and decision rules

Governed entirely by `controlled_seed17_r2_replay_protocol.md` §7 (scoring/comparison plan) and
§8 (decision rules A–D) — not restated here to avoid a second copy drifting from the canonical
one. Summary of what happens after evaluation, for reference only:

1. ChatGPT scores both raw result files semantically (as with every prior round).
2. Claude independently re-verifies every score against the raw generated text and the frozen
   rubric before accepting.
3. All 6 frozen gates (§2 above) are recomputed directly via `report_benchmark.py`, not
   re-derived logic.
4. Outcome classified as A (full pass) / B (improvement, no full pass) / C (neutral or worse) / D
   (structural/reproducibility failure) per the protocol's own definitions.
5. Joint recommendation returned to Johnny, including any disagreement — no silent resolution
   either direction.

## 6. Explicit non-authorizations (unchanged)

Approving/reviewing this manifest, its wrapper script, or its tests does **not** authorize:
training, inference, or benchmark execution; seed 73; a Phase-2 curriculum; scorer or gate
changes; use of Gold v1.2.3 as training input; app-side activation; export/deployment; or
modification of any frozen baseline artifact. Only Johnny, naming this controlled seed-17 R2
replay specifically, authorizes execution.

## 7. Fingerprints of this round's deliverables

| Artifact | SHA-256 |
|---|---|
| `run_seed17_r2_replay.py` | `a5ec073371bf821b420d4dddbf1936db516b0697ffb78f2cc56bed5948b7d6eb` |
| `test_run_seed17_r2_replay.py` | `0b203ad92c22435ee54355c4959385053931de23ab595a1f3c99d459ae0142e0` |
| `controlled_seed17_r2_replay_frozen_fingerprints.json` (new, external lock file) | `3accd2bb95d940310c7e362372a8e7da953e5ccd9691304b7e0386661289676a` |
| `controlled_seed17_r2_replay_manifest_dryrun_receipt_sample.json` (regenerated) | `e5c14f6a23ed86683973aea27bfb103d51900429ee978563163db1440ab95abf` |
| This manifest (revision 4) | *(reported externally, in chat and in the eventual commit message — hashing this file while editing this same row would be self-referential, so this table cannot and does not contain it)* |

All 27 tests in `test_run_seed17_r2_replay.py` pass (up from 15 in the first draft), including new
coverage for every fail-closed condition this round added: frozen executable-code/governing-input
mismatch, missing pin, dependency-version drift, dirty-tree refusal (via synthetic git state, since
this round's own deliverables are legitimately uncommitted right now), and log-content survival
when a subprocess is killed before completing normally.
