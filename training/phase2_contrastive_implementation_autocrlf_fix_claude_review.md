# Phase-2 Contrastive Implementation — autocrlf Fix: Review + Implementation

**Date:** 2026-08-10
**Scope:** Addendum to `phase2_contrastive_implementation_claude_cross_review.md`. Corrects the
autocrlf fragility that review flagged (existing R2 validation split reads CRLF on a stock Windows
checkout, failing the script's own pinned-fingerprint check even though `git status` reports it
clean). Authorized under the standing Claude+ChatGPT agreement protocol (confirmed 2026-08-10,
full scope including this design/implementation layer) — ChatGPT proposed the corrective design,
Claude independently reviewed it, agreed, and implemented it. No training, seed 73, commit, or
push performed or implied.

## 1. Design review

ChatGPT's proposed approach: canonicalize the existing R2 validation split on read (accept only
already-canonical LF bytes, or a uniform CRLF re-encoding of exactly those bytes; normalize to LF;
re-verify the normalized result against the pinned fingerprint), reject every other deviation
(mixed endings, bare CR, missing terminal newline, blank-line/whitespace/content drift, BOM) with a
specific diagnostic, and force deterministic LF on every artifact this script writes — rather than
relying on `.gitattributes` alone, which can't repair an already-checked-out copy.

Before agreeing, independently characterized the actual bytes involved (not assumed): the real
working-tree file is 10426 bytes, 6 CRLF terminators, 0 bare CR, ends in CRLF (terminal newline
present); the canonical git blob is 10420 bytes, 6 LF, ends in LF, no BOM — a clean, uniform
conversion, consistent with the design's core assumption. No gaps found in the design. One
non-blocking observation: the same fragility class (a pinned fingerprint computed in a
different-line-ending environment than a Windows checkout) could recur for the other four pinned
inputs (parent, historical proposal, composite proposal, split manifest) if their pins are ever
recomputed elsewhere — not currently a problem (all four match cleanly on this checkout today), not
in scope for this fix, but worth being aware of.

**Verdict: agree.** Implemented as designed.

## 2. Implementation

`prepare_phase2_contrastive_candidate_corpus.py`:
- Added `canonicalize_val_split_bytes()` — accepts LF or uniform-CRLF, rejects everything else with
  a specific diagnostic, and only trusts the result once its SHA-256 matches the pinned fingerprint.
- Added `load_canonical_existing_val_bytes()` — owns reading + canonicalizing the existing R2 val
  split; the existing R2 val split fingerprint check was removed from the generic flat-hash loop in
  `verify_pinned_fingerprints()` and replaced by this.
- `verify_val_byte_identical_to_existing()` now compares the write step's output against the
  already-verified canonical bytes (passed in), not a fresh raw re-read of the checkout.
- `val.jsonl`, `train.jsonl`, the derivation report, and both comparison JSONs are now written via
  `write_bytes()` with explicit LF, never `write_text()`'s platform-dependent newline translation.
- Derivation-report item #8 rewritten from "a direct byte-for-byte copy of the existing R2 val
  split's own bytes" to the precise canonical-LF-representation claim, per the instruction.

`test_prepare_phase2_contrastive_candidate_corpus.py`: added full coverage for
`canonicalize_val_split_bytes` (LF passes; uniform CRLF passes and normalizes to the same LF output;
LF and CRLF inputs produce identical output; mixed endings, bare CR, content drift, whitespace
drift, blank-line drift, missing terminal newline in both forms, and a BOM all fail closed) and for
`load_canonical_existing_val_bytes` (missing file fails closed; a live check against the real,
unmodified repository file, with no manual normalization).

## 3. Verification (independent, not self-reported)

- Ran the corrected script cold, on this actual Windows checkout, **with zero manual
  normalization** — the exact gap flagged in the prior review. Output: `existing frozen R2
  validation split (val.jsonl): 8aa99a79... (uniform-CRLF checkout, normalized to canonical LF)`.
  Completed with no fatal errors. Confirmed via `git status --porcelain` before and after that the
  real R2 val split source file was never written to (script only reads it).
- Ran the corrected test suite cold, same checkout, zero manual normalization: `All checks passed.`,
  including the new live check against the real file.
- Candidate corpus, `train.jsonl`, and `val.jsonl`: byte-for-byte identical to the previously
  reviewed bundle artifacts (unchanged content, as required).
- Both comparison JSONs: now byte-for-byte identical to the bundle too (previously only matched
  after CRLF normalization; the deterministic-LF-write fix closed that gap).
- Derivation report: diffs from the bundle in exactly one place — item #8's rewritten claim, exactly
  as instructed. Nothing else differs.
- Candidate training-data fingerprint: `62bbee12130ea54f6cae3777eb990a9d54a35411ceeba75030755569c44982ae`
  — unchanged, confirmed via live run.
- Repository diff: `git diff --stat` empty (no tracked file modified), HEAD unchanged at `3988745`,
  untracked-file set identical in scope to the prior repository-integration report (same 9 new
  files, now with corrected content for the script/test/regenerated outputs). Nothing committed.

## Updated artifact hashes

| Artifact | SHA-256 |
|---|---|
| `prepare_phase2_contrastive_candidate_corpus.py` (corrected) | `5e290de30bcf7fd3b9d539cdf5cdc64e7c126ac38ec6d1a830532fe363eeed4f` |
| `test_prepare_phase2_contrastive_candidate_corpus.py` (corrected) | `3304bed3f1280ee7a3239c9fb3845fd0019e65ee4965647fbb50176e433fe559` |

Candidate corpus, `train.jsonl`, `val.jsonl`, and the split-comparison/diff JSONs are unchanged from
the hashes already on record in the prior cross-review — only the derivation report's item #8
prose and the two source files above changed.

## Disposition

Fix agreed, implemented, and independently verified end-to-end on the exact checkout where the
original problem was found. No composite-record, corpus-content, count, membership, or algorithm
change. Everything remains uncommitted in `training/`.
