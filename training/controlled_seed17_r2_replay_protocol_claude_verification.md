# Controlled Seed-17 R2 Replay Protocol — Claude Repository Verification

**Date:** 2026-08-03
**Protocol reviewed:** `controlled_seed17_r2_replay_protocol.md` (received inline, claimed SHA-256
`909ca58d1b3f01bf8266f74403e32cda3095d8795bc420e3f09cd4d1ac277fc3`, proposed path
`training/controlled_seed17_r2_replay_protocol.md`)
**Compute performed:** none. Every check below is read-only (git diff/show/log, file hashing,
`report_benchmark.py`/`contract_adapters.py` invocations that stop before any model load).

## Readiness decision: **NOT READY** (updated 2026-08-03, see Addendum below — §1 and §2 now resolved)

Not because the frozen baseline evidence is defective — every substantive check below
independently confirmed the protocol's claims. Originally blocked on two process items (§1, §2);
both are now resolved per the Addendum. Remaining gap: one undone preflight step (§3.3).

## 1. BLOCKING — protocol document hash cannot be verified

The document was received as inline chat text, not a repository file or attachment. It does not
exist in this repository at any commit or in the working tree (`git log --all -- '*controlled_seed17*'`
and a working-tree search both came back empty). The pasted text itself shows visible mojibake
(`â` replacing em-dashes throughout, e.g. "Outcome A â Full gate pass") — the identical corruption
pattern already caught once before in this project's own r2-derivation review (lost em-dash/arrow/
curly-quote encoding from pasted text). Transcribing the text verbatim into a file and hashing it
gives `4954e60e21c2eb858b2ba5e0a4640a6479e81aa86d931ebf37b7c27de660f89c`, which does not match the
claimed `909ca58d...`.

This mismatch is **inconclusive, not a finding of tampering** — a re-encoded paste will not
reproduce an original file's bytes regardless of content fidelity. But it means I have no
byte-faithful copy of the governing document to check anything against, including the claimed
hash itself. Per the protocol's own §2 instruction ("If any reference is inaccurate, missing,
ambiguous, or insufficient... Claude must stop and return the discrepancy"), I'm stopping on this
point rather than treating my transcription as authoritative. **Request:** the actual file (added
to the repo at the proposed path, or shared in a way that preserves exact bytes) so the SHA-256 can
be checked directly, e.g. `git hash-object` against the real file.

## 2. BLOCKING (self-reported) — a real mistake in commit `2f7a101`'s characterization

While reconstructing the seed-17 baseline this protocol depends on (§3 below), I found that
commit `2f7a101` ("Commit gold_v1.2.3 body of work as historical record (net-negative, not
promoted)") — made earlier this session — bundled in three `training/data/processed_*`
directories that are **not** part of the superseded 2026-07-30 gold_v1.2.3 effort:

| Directory | Actual origin | Evidence |
|---|---|---|
| `processed_gold_v1.2.2_v2contract_seed17/` | **The live seed-17 v2-contract study's own training data** (this thread, commit `07de0d4`, 2026-08-03) | Named and described at `training/gold_v1.2.2_seed17_v2contract_study_provenance.md:18`; file mtime 2026-08-03 08:17, not 07-30 |
| `processed_gold_v1.2.2_control/` | The prompt-contract compatibility study (PR #14/#15, Cell A) | Referenced by already-committed `training/gold_v1.2.2_seed17_compatibility_study_provenance.md` |
| `processed_gold_v1.2.2_control_newprompt/` | Same compatibility study, Cell B2 | Same provenance doc; mtime 2026-08-02 |

Only the `processed_gold_v1.2.3_*`-named subdirectories (fixedsplit, frozen, groupscreen_seed17_
groupA/B/C, minus006 — all dated 2026-07-30/07-31) genuinely belong to the net-negative,
not-promoted gold_v1.2.3 body of work the commit message describes.

**This does not mean the files were wrongly committed** — quite the opposite: preserving
`processed_gold_v1.2.2_v2contract_seed17/{train,val}.jsonl` is exactly right, since it's the frozen
baseline artifact this replay protocol's §4.2 requires me to identify. The problem is only the
commit's message/categorization, which could mislead a future reader (including ChatGPT reviewing
this protocol) into treating it as disposable, superseded data. I have not rewritten or amended
`2f7a101` (per this project's own git-history norms — no rewriting pushed history without
explicit instruction). Flagging for a decision: leave as-is with this doc as the correction of
record, or take some other corrective action.

## 3. Preflight verification performed (all independently reproduced, not read from any handoff)

### 3.1 Repository and source checks (protocol §4.1)

- Checked-out commit: `f205828720969800cc1108099496efa30e6551ed` (`f205828`). `origin/main`:
  `2f7a1011c56ac0b3104236cfd5d27431b44fd6a1` (`2f7a101`) — local is one commit ahead, not yet
  pushed (Johnny's explicit choice this session). Working tree: clean.
- **Naming ambiguity resolved**: "the pinned 66-record gold_v1.2.2 corpus" = `datasets/synthetic.jsonl`
  at `8d7aa09` (66 lines) — **not** `datasets/gold/gold_v1.2.2.jsonl`, a different, 12-record file
  that happens to exist at the same commit. Confirmed via `gold_v1.2.2_r2_derive_corpus.py`'s own
  header/constants, which load from `synthetic.jsonl` explicitly. Worth stating explicitly in any
  future document since the near-identical filenames invite exactly this confusion.
- `datasets/gold/gold_v1.2.2.jsonl` blob hash at `8d7aa09` and at current HEAD: both
  `1df5d15e9af803ef209728b3286f3ecc790a1f36` — byte-identical, confirmed immutable.
  `datasets/synthetic.jsonl` blob hash differs (`be1f0bf4...` → `e36da693...`) because of this
  session's `f205828` fold-in of 6 gold_v1.2.3 examples — expected and already correctly excluded
  by the protocol's own §3.1 clause ("must not load `datasets/synthetic.jsonl` implicitly").
- R2 candidate re-diffed at the JSON level directly (not trusting prior labels): 66/66 records
  present in both pinned original and candidate; **exactly 3 records differ, only in `output`**, at
  indices 15, 38, 52; all other 63 records' `input`/`difficulty`/`category`/`output` are identical;
  `input`/`difficulty`/`category` are identical across all 66 including the 3 changed ones. Read
  the actual changed content directly (not just the index/label):
  - index 15 (`dangling_reference`): "what did my daughter say about friday?" — original invents
    "her plans for this Friday" and an action "Ask daughter about Friday"; candidate reframes as an
    unresolved question and drops the invented action. Matches ti-001 exactly.
  - index 38 (`rapid_topic_switching_incomplete_sentences`): "keys, wallet, phone... gas is low...
    call the landlord about... lunch with Dana" — original has 5 action items, several unsupported
    (attending an unstated meeting, "getting gas" from a bare observation, an admittedly unfinished
    "call the landlord about."); candidate reduces to the single supported action, `["Grab keys,
    wallet, and phone"]`. Matches ti-002's counter-proposal (B5/A1) exactly, byte for byte.
  - index 52 (`standalone_task_retention`): "the kitchen sink is dripping again which is exhausting"
    — original attributes "feels exhausting" to the sink; candidate reattributes the feeling to the
    person ("the writer is tired of dealing with the dripping sink"). Matches ti-003 exactly.
  - Candidate additionally carries `v1_target`/`v2_target` fields (mechanically derived) absent
    from the original — this is why a naive whole-record equality check initially over-counted the
    diff; isolating the `output` field specifically gives the correct 3/66.
- File hashes recorded: `gold_v1.2.2_r2_derive_corpus.py` `e38581d9c938...`,
  `gold_v1.2.2_r2_derived_candidate.jsonl` `197adb3578b2...`,
  `gold_v1.2.2_r2_corpus_derivation_report.md` `8968c00703d5...`,
  `gold_v1.2.2_target_integrity_corrections_proposal_r2.jsonl` `dfb4a001d73c...` (matches the value
  already recorded in `phase_e_remaining_sequence` memory from the original r2 review).

### 3.2 Baseline reconstruction checks (protocol §4.2) — seed-17 v2-contract study

Everything below was independently recomputed from the real committed artifacts and code, not
read from `gold_v1.2.2_seed17_v2contract_study_provenance.md` and trusted:

- Source targets file: `training/prompt_contract_v2_migrated_targets_DRAFT.jsonl`, recomputed
  SHA-256 `1bef1b0476c372b35dd08a89f7e767e25c46ff1ace202d90ffbb5a3d7e4c0307` — exact match to the
  provenance doc's claim.
- Training-data fingerprint: reconstructed the canonicalization by trial (JSON array of all 66
  `{prompt, target}` pairs from `train.jsonl`+`val.jsonl`, sorted by `prompt`, `sort_keys=True`,
  compact separators) — reproduces `e548e0b633ac1ca11b109adbf88ddbda95a42add38d93f524b700f4762092fd3`
  exactly.
- Split: 60 train / 6 val (`wc -l` on the actual files) — matches claim.
- `split_manifest.json` current hash: `24610be8c5b91be13b064acaaab4f8bbae59b0ec175e66d1fb8ccb94cd049485`;
  confirmed unchanged between commit `07de0d4` and current HEAD (`git log 07de0d4..HEAD --
  split_manifest.json` empty).
- Checkpoint: `training/checkpoints/gold_v1.2.2-v2contract-seed17/final` still present on local
  disk (gitignored, as expected). Ran `real_data_private.checkpoint_fingerprint()` directly
  against it: `5687a7602d3ab79ff7f054b80c399738a9b27a959845c27bcf7aa918b638227c` — **exact match**
  to the provenance doc's claim. `checkpoint-600/trainer_state.json` confirms `epoch: 40.0`,
  consistent with "600/600 steps, no early stop."
- Evaluation inputs: `datasets/benchmark/gold_v1.2.1_probes.jsonl` SHA-256
  `044708641c8dd584f334f16bde21ed89550bb7c464160827433f825eb0c48e94`; `source_determined_items_v2_
  acceptance_draft.jsonl` SHA-256 `b8fe4d4178e5b508757db998eacb1ee979518697c8df759ba1739227c88d448e`.
  Both files' last modifying commits (`16a03da`, `83dba25` respectively) predate the study's
  compute commit `07de0d4` — neither was touched during or after the study.
- Scorer/contract code identity: `prompt_contract_v2_candidate.py`, `prompt_contract_v2_parser.py`,
  `contract_adapters.py`, `report_benchmark.py`, `run_benchmark.py`, `prepare_v2_training_data.py`
  all confirmed **unchanged** between commit `07de0d4` and current HEAD (`git log 07de0d4..HEAD --
  <each file>` empty for all six). Locked prompt-fixture fingerprints re-verified live via
  `contract_adapters.select_contract_adapter()`: v1 `161661198071fd81310681f69381ec8e0287141e1e75b09d3a342414af31ccf1`
  and v2 `e691fd12ee51b322b93311cf483d2fbb4bb921ac8a1319e07420fae098ea0cb9` both currently pass their
  fail-closed check (stops before any model load, per the code's own design — confirmed no model
  loading occurred by inspection, not just by the absence of an error).
- Runtime/dependency versions: `training/requirements.txt` (last touched `ed58cd0`, confirmed an
  ancestor of `07de0d4`, i.e. unchanged since) pins `torch==2.11.0+cu128`, `transformers==4.57.6`,
  `datasets==5.0.0`, `accelerate==1.14.0`, `sentencepiece==0.2.2`. Queried the actual training venv
  directly — installed versions match the pin exactly, CUDA available. `train.py` (last touched
  `fa25786`, also an ancestor of `07de0d4`) unchanged since the study ran.
- Base model: `train.py`'s `BASE_MODEL = "google/flan-t5-base"` — **no explicit HF revision/commit
  pin**, just the model name string. Stating this as a fact rather than treating it as a defect:
  every gold_v1.2.2/v1.2.3 run this whole project has used the same unpinned reference, so it's at
  least internally consistent; a genuinely hostile reproducibility audit would still flag it.
- **Rescoring reproduces the exact committed outcome**, run directly against the real committed
  result files with no modification:
  - Protected 16-probe: **11/16 (69%)**, format validity 16/16, regression-guard flags on probes
    `06` and `11` (matching the provenance doc's own clarification that only `11` is a genuine
    same-seed regression, since `06` already failed at the Cell-A baseline).
  - 10-case v2 acceptance set: format validity 10/10; **6/10** count-rule-only via the "Acceptance
    gates passed" figure's constituent check is not printed separately by `report_benchmark.py`'s
    default output, so I cross-checked directly — the tool's combined strict "Acceptance gates
    passed: 4/10" figure is consistent with the memory-recorded breakdown (6/10 count-rule, 5/10
    semantic, 4/10 both required simultaneously); failing IDs (`sdi2-03/04/06/07/08/10`) match
    memory's failure set exactly.
  - This directly satisfies protocol §4.2's "confirm the committed baseline result can be read and
    rescored without changing its recorded outcome" — confirmed, no drift.

### 3.3 Candidate split checks (protocol §4.3) — **not done**

Deriving R2-candidate train/val split artifacts (analogous to `prepare_v2_training_data.py`, but
sourcing `gold_v1.2.2_r2_derived_candidate.jsonl` instead of the unmodified migrated-targets file,
against the same frozen `split_manifest.json` membership) has **not been built or run**. This is
data preparation, not model compute, but per this project's own established pattern from the
original seed-17 study (gaps were flagged to Johnny and an explicit "Proceed" obtained *before*
writing `prepare_v2_training_data.py`, even though writing a script isn't itself compute), I'm
flagging this rather than building it unprompted. If the two blocking items above resolve in favor
of proceeding, building this derivation script is the natural next step, and it's a small,
reviewable addition mirroring an already-reviewed pattern (both `gold_v1.2.2_r2_derive_corpus.py`
and `prepare_v2_training_data.py` already exist as templates).

### 3.4 Execution-safety checks (protocol §4.4)

Not assessed — no experiment identifier or output path has been chosen yet since §3.3 isn't built.
Trivial to satisfy once that script exists, following the same "fail closed if path exists"
pattern already used by `gold_v1.2.2_r2_derive_corpus.py` and `prepare_v2_training_data.py`.

## Addendum (2026-08-03): §1 and §2 resolved

**§1 resolved.** ChatGPT supplied a re-encoded protocol document (ASCII-only, LF line endings,
mojibake em-dashes replaced with `--`), claimed SHA-256 `bcb72c22f19997f183312fdc4070acd086ebac8efe2b45799dd8ac494f2d759b`,
15,391 bytes, 314 lines. Independently verified by writing the received text to a file and
checking every claimed property directly, not just the hash: byte count `wc -c` → 15391 (exact
match), line count `wc -l` → 314 (exact match), `sha256sum` → `bcb72c22...` (exact match), `grep -P
'[^\x00-\x7F]'` → zero non-ASCII bytes (confirmed pure ASCII), CR count → zero (confirmed LF-only).
All five independent checks agree, not just the headline hash. Added to the repository unmodified
at the proposed path, `training/controlled_seed17_r2_replay_protocol.md`; hash re-confirmed
identical after the copy. The earlier `909ca58d...` hash and its inline/mojibake source text are
superseded and should not be cited going forward.

**§2 status unchanged**: commit `2f7a101`'s mischaracterization stands corrected by this document
(the main body above); `2f7a101` itself remains unrewritten, per Johnny's decision to treat this
doc as the correction of record rather than amend pushed history.

**Still open**: §3.3 (candidate-split derivation) has not been built. Per this project's
established pattern — flag before extending tooling even during preflight, even though writing a
data-prep script isn't itself compute — holding for explicit direction before building it.

## Summary for ChatGPT / Johnny

Every claim in the protocol's governing-evidence table (§2) and every frozen-variable value I
could check (§3.2) is independently confirmed correct against the real repository — no
discrepancies found in the substance of the baseline. Two process items need resolution before
this goes further: the protocol document itself needs to exist as a byte-verifiable repository
file (§1), and commit `2f7a101`'s mischaracterization of three still-relevant data directories as
"historical, net-negative, superseded" needs an explicit decision, not a silent correction (§2).
Candidate-split derivation (§3.3) is the one substantive preflight step not yet attempted, held
pending direction on the two items above.
