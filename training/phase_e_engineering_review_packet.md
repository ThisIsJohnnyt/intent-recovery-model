# Phase E Engineering Review Packet

Prepared by Claude Code for the second joint readiness review, per
`training/phase_e_real_data_dummy_implementation_handoff.md`'s "Engineering
review packet" and "Joint readiness decision" sections. Everything below
reflects PR #12 (`00a861e..2c665f9` on `claude/ai-note-organization-luz6rk`).

## File and commit inventory

Single commit, `2c665f9`, 16 files changed:

**Documentation adopted** (Revision 2, hash-verified before import):
- `datasets/REAL_DATA_GOVERNANCE.md`
- `datasets/REAL_DATA_ANNOTATION_GUIDE.md`
- `datasets/REAL_DATA_SPLIT_AND_SEALING_PROTOCOL.md`
- `training/REAL_DATA_EVALUATION_PROTOCOL.md`
- `docs/decisions/PDR-005.md` (status: Accepted)
- `training/phase_e_real_data_dummy_implementation_handoff.md` (this phase's own handoff, saved for the record)

**Engineering, new:**
- `training/real_data_private.py` -- canonical JSON, all four SHA-256 fingerprint types, manifest/rubric I/O
- `training/real_data_eval_logging.py` -- `real-eval-v1` schema, approved-root enforcement
- `training/real_data_scoring.py` -- strict semantic-scoring scaffold
- `training/test_real_data_private.py`, `training/test_real_data_eval_logging.py` -- 41 dummy-data assertions

**Engineering, modified:**
- `training/prepare_data.py` -- no longer opens `real_holdout.jsonl` at all
- `training/evaluate_holdout.py` -- in-memory sealed loading, `--milestone` required, fail-closed manifest linking
- `datasets/.gitignore`, `training/.gitignore` -- new private-path rules

**Deliberately not in this commit**: the prompt-contract change (workstream 6) -- see its own section below.

## PDR-005 status and approval text

From `docs/decisions/PDR-005.md`, current committed state:

```
**Date**: 2026-08-01
**Status**: Accepted
...
## Alignment status
- Phase D four-gate review: Aligned between Claude Code and ChatGPT.
- Governance package architecture and rubric: Aligned (Claude Code, revision 2).
- Revision 2 content: Aligned -- verified by hash, marker presence, and full read
  of all five documents; no disagreement raised.
- Product owner: Approved (2026-08-01).
- Engineering lead (Claude Code): Aligned.
- Dataset/evaluation architect (ChatGPT): Aligned.
```

Archive verified: `real_data_governance_revision2_verified.zip`, SHA-256
`ca02364cd2d31553939986af2d6baffc56b4bd437bbcf89120a0417b36fcfac0` --
independently recomputed with `sha256sum`, matched exactly. All five
inner-file checksums in `REVISION2_SHA256SUMS.txt` also verified `OK`.

## aislop results and documented exception

First pass over the new modules: 8 warnings (1 code-quality, 7 AI-slop:
6 narrative comments + 1 chained `.get(...,{})` on a security-relevant
path). All fixed, not suppressed:
- 6 decorative section-divider comments in `real_data_private.py` removed.
- `evaluate_holdout.py`'s `entry.get("allowed_uses", {}).get("holdout_eligible")`
  replaced with an explicit check that distinguishes "malformed manifest
  entry" from "genuinely not eligible" -- this is on the fail-closed
  consent-verification path, worth the extra clarity.
- `build_result_artifact`'s 12 flat parameters regrouped into `checkpoint`/
  `dataset` dicts mirroring the schema's own nesting (12 -> 7).

Final: `0 errors, 1 warning` (98/100). Remaining warning: `build_result_artifact`
still has 7 params against aislop's max-6 guideline. Kept as a reviewed,
documented exception (comment inline in the function) rather than fragmented
further -- the two multi-field pieces are already grouped; the rest are
independent, schema-required top-level fields, not a growing ad hoc list.

Coverage caveat, stated plainly: `aislop`'s scan is Python-only. Confirmed
by checking scan scope directly (`7 of 14 .py files, 0 of 116 .md files`),
not assumed -- it did not review the five imported governance documents.

## Test commands and results

```
python training/test_real_data_private.py
```
21/22 pass. 1 skipped: symlink-rejection dynamic test (no symlink privilege
on this Windows host without elevation/Developer Mode). The `is_symlink()`
check itself is implemented in `checkpoint_fingerprint` and was code-reviewed;
only the dynamic exercise of that specific branch was unavailable here.

```
python training/test_real_data_eval_logging.py
```
19/19 pass, covering: initial null scoring state, holdout milestone
requirement, approved-root rejection, schema roundtrip, `compute_strict_pass`
across pass/fail/unscored/missing-dimension cases, `apply_scores` immutability,
aggregate strict-pass-rate null-until-fully-scored behavior.

## `git check-ignore` and clean-status evidence

All 10 declared private paths confirmed ignored (static):

```
datasets/real_validation.jsonl        -> datasets/.gitignore:5
datasets/real_holdout.jsonl           -> datasets/.gitignore:6
datasets/private/                     -> datasets/.gitignore:11
datasets/private/real_data_manifest.jsonl   -> datasets/.gitignore:11
datasets/private/real_data_rubrics.jsonl    -> datasets/.gitignore:11
training/results/private/                    -> training/.gitignore:11
training/results/private/real_validation/... -> training/.gitignore:11
training/results/private/real_holdout/...    -> training/.gitignore:11
training/data/processed/real_validation.jsonl    -> training/.gitignore:4
training/data/processed/real_holdout_eval.jsonl  -> training/.gitignore:4
```

Dynamic: created real dummy files at every path above (manifest, rubrics,
two evaluation results) -- `git status --porcelain` showed nothing. Repeated
again independently during the live drill (workstream 7) with real generated
content -- same result both times.

## Static and dynamic proof of routine holdout non-access

Static: `grep -n -i holdout training/prepare_data.py` -- every hit is a
comment, docstring, or a print string explicitly stating it's *not*
evaluating the holdout. No functional reference.

Dynamic: wrote deliberately invalid (non-JSON) content to
`datasets/real_holdout.jsonl`, ran `prepare_data.py`. It completed
successfully -- if it had opened and attempted to parse that file, it
would have crashed. It didn't.

## Sample result schemas (dummy content, plainly synthetic)

Unscored, immediately after generation:

```json
{
  "schema_version": "real-eval-v1",
  "evaluation_id": "eval_0b858b466b39",
  "split": "real_holdout",
  "release_milestone": "pilot-drill-test",
  "checkpoint": {"fingerprint": "sha256:edd2faf5...", "training_seed": -1, "run_id": "unspecified"},
  "dataset": {"fingerprint": "sha256:20ed0847...", "record_count": 1, "rubric_version": "real-rubric-v1"},
  "results": [{
    "record_id": "rv_drill0001",
    "raw_output": "###NARRATIVE### I need to call the plumber tomorrow morning. ###BULLETS### Unresolved question about calling the plumber tomorrow ###ACTIONS### Call the plumber tomorrow",
    "format_valid": true,
    "scores": {"topic_completeness": null, "attribution_accuracy": null, "uncertainty_preservation": null, "unsupported_addition_resistance": null},
    "strict_pass": null,
    "review_status": "unscored"
  }],
  "aggregate": {"format_valid": "1/1", "strict_pass": null}
}
```

After manual scoring (simulating independent review -- the raw output
invented "tomorrow morning" and an unsupported "unresolved question"
bullet not in the dummy input, a genuine unsupported-addition failure):

```json
"scores": {"topic_completeness": true, "attribution_accuracy": true, "uncertainty_preservation": true, "unsupported_addition_resistance": false},
"failure_labels": ["unsupported_commentary", "unsupported_qualifier"],
"strict_pass": false,
"review_status": "adjudicated"
```
Aggregate: `"strict_pass": "0/1"`. Saved as a separate `_adjudicated` evaluation
ID -- the raw generation artifact was left untouched, per the immutability
requirement.

## Fingerprint determinism and failure-case evidence

All from the automated test suite plus the live drill:
- `source_fingerprint`/`pair_fingerprint`: change only when their respective
  scope (input-only vs. input+output) changes -- verified both directions.
- `rubric_fingerprint`: correctly excludes its own field before hashing
  (avoids circularity) -- verified a stale embedded value doesn't affect the hash.
- `dataset_fingerprint`: identical for `[r1,r2,r3]` and `[r3,r1,r2]` (order-independent);
  changes when any active record is edited; `real_validation` and `real_holdout`
  never share a fingerprint for identical records (literal split value in the wrapper).
- `checkpoint_fingerprint`: identical across two runs on the same directory;
  changes when any file's bytes change; nested paths recorded POSIX-style
  (`nested/weights.bin`, not `nested\weights.bin`); empty directory raises
  `CheckpointFingerprintError`; symlink rejection implemented and reviewed,
  dynamic test skipped (host limitation, not a code gap).
- `prompt_contract_fingerprint`: deterministic for identical text; a bare
  trailing newline changes the hash (confirms no implicit normalization).

## Withdrawal-drill evidence

1. Manifest + rubric entries created for dummy record `rv_drill0001`.
2. Holdout evaluation ran successfully, structured result saved.
3. `withdraw_record("rv_drill0001")` called.
4. Manifest entry retained with `withdrawal_status: "withdrawn"` (audit trail
   kept, not deleted). Rubric entry removed entirely.
5. Re-ran `evaluate_holdout.py` against the same source content -- failed
   closed: `FAIL CLOSED: manifest entry rv_drill0001 is not active
   (withdrawal_status='withdrawn').`

Two additional fail-closed paths also exercised live: a holdout record with
no manifest entry at all, and one with an entry present but
`holdout_eligible: false`. Both refused to evaluate.

**Known gap, stated not hidden**: withdrawal correctly blocks *future*
evaluation and removes rubric access, but does not retroactively mark
*already-saved* evaluation artifacts from before the withdrawal as
invalid/superseded. Zero current risk -- no real evaluation history exists
yet -- but should be built before real pilot data does.

## Cross-repository prompt status

**Not committed in PR #12, intentionally.** Prepared and verified in the
working tree only:
- `PROMPT_CONTRACT_VERSION = "source-determined-bullets-v1"`
- Rendered acceptance-fixture prompt, hashed: `sha256:0716f3a3822a459a46c69e3fce25cb79376507e9a3031867b198134aac5a2a4f`
- `prepare_data.py` verified to still run correctly end-to-end with the new wording.
- The two documentation references (`docs/datasets/training_data.schema.json`,
  `training/DATASET_SPEC.md`) prepared identically, also uncommitted.
- Handoff for the paired `thought-organizer-app`-side change already
  delivered: `training/app_prompt_bullet_count_reconciliation.md` (committed
  in PR #12, since it's a coordination artifact, not the contract change itself).

No commit ID to report yet on either side -- neither half is merged. This
stays blocked until both are.

## Explicit confirmation: no real notes collected

`datasets/real_validation.jsonl` does not exist. `datasets/real_holdout.jsonl`
exists and is 0 bytes. Confirmed directly (`ls`, `wc -c`) immediately before
writing this packet, after all drill cleanup. `datasets/private/` and
`training/results/` do not exist. Every input used anywhere in this phase
was synthetic and marked with a `TESTMARKER_`-prefixed dummy string.

## Claude's alignment status

**Evidence alignment: Aligned.** Every claim in this packet is backed by a
command actually run and its actual output, not asserted from reading code.

**Implementation alignment: Aligned for workstreams 1-5 and 7.** Fully built,
tested (dummy data), and verified against the specific acceptance criteria
in `REAL_DATA_EVALUATION_PROTOCOL.md` and the Phase E handoff.

**Workstream 6: prepared, correctly not merged.** Blocked on the paired
app-repository change per PDR-005's own rule.

**Remaining gaps, both zero-current-risk given empty real-data files:**
1. No automated invalidation-marking of pre-withdrawal evaluation artifacts.
2. `aislop` doesn't cover the five imported Markdown governance documents --
   their accuracy relies on the verification I already did by hand (hash +
   marker + full read), not on this tool.

**Recommendation on the validation-only pilot**: the engineering
foundation is ready for review. I'd hold actual pilot population until (a)
this packet is reviewed and (b) the cross-repository prompt contract is
paired and merged on both sides -- per PDR-005's own gate, source-determined
bullet wording must be live on both repos before any real note is annotated
under this contract.
