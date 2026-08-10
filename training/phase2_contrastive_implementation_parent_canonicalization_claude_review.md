# Phase-2 Contrastive Implementation — Parent-Canonicalization Fix: Review + Implementation

**Date:** 2026-08-10
**Scope:** Second addendum to `phase2_contrastive_implementation_claude_cross_review.md`. The first
addendum (`phase2_contrastive_implementation_autocrlf_fix_claude_review.md`) fixed the existing R2
validation split's checkout-vs-blob fragility; this document fixes the identical fragility found
independently, during staged-blob verification before the first proposed commit, in the R2 parent
corpus. Authorized under the standing Claude+ChatGPT agreement protocol (2026-08-10) — Claude found
the defect and stopped short of committing, ChatGPT independently agreed with the finding and
proposed the corrective design, Claude independently reviewed and implemented it. Commit/push remain
paused pending review of these corrected artifacts, per Johnny's disposition.

## 1. What was found, and how

Before running `git commit` on the previously-agreed 12-file scope, an extra check was run that
hadn't been run before: hashing what git would actually *store* for each staged file, not just what
was on disk. 11 of 12 matched. `gold_v1.2.2_phase2_contrastive_derived_candidate.jsonl` did not:
working-tree bytes hashed `9efa7d80...` (the hash both Claude and ChatGPT had reviewed and agreed on);
the staged blob hashed `7760f377...`.

Root cause, confirmed with evidence before proposing any fix:
- The R2 parent corpus's committed git blob is pure LF (101144 bytes, 0 CR): `62d1ea43...`.
- The local Windows working-tree checkout is CRLF (101210 bytes, 66 CR, one per record): `197adb35...`
  -- which is what `EXPECTED_PARENT_FINGERPRINT` had been pinned against since 2026-08-04, in both
  this script and the original `prepare_phase2_candidate_corpus.py`, undetected because every run to
  date happened on this same checkout.
- The candidate builder legitimately (by design) copies the parent's raw bytes forward verbatim and
  reuses its terminator for the appended records, so the working-tree candidate ends up CRLF
  throughout (82 CR = 66 + 16) -- exactly the bytes both reviewers had accepted.
- That candidate file is brand new, so `git add` -- with no prior blob or attribute to protect it --
  silently CRLF-normalizes it on staging. Confirmed the mismatch was pure line-ending drift, no other
  content change: stripping `\r` from the working file reproduces the staged blob's hash exactly.
- Checked whether this was already baked into history: the already-committed historical 78-record
  candidate's blob is clean LF (0 CR) -- not a pre-existing corruption, only a risk for committing
  this new file right now.

Reported this plainly rather than fixing it unilaterally; ChatGPT independently agreed and proposed
the corrective design below.

## 2. Design review

ChatGPT's proposed approach: generalize the val-split canonicalizer into a reusable pinned-LF
canonicalizer; correct `EXPECTED_PARENT_FINGERPRINT` to the canonical blob hash; parse parent records
from the already-verified canonical bytes rather than a second unverified read; build the candidate
from canonical LF parent bytes plus explicitly LF-terminated appended records; verify the candidate
prefix against the canonical parent, not a fresh raw read; remove checkout-dependent terminator
detection entirely; and update the "preserves working-tree raw bytes" documentation accordingly.

No gaps found. This is the same fix pattern as the val split, correctly generalized rather than
duplicated, and it correctly identifies that `detect_line_terminator()` -- which only existed to let
the candidate mirror whatever the parent's checkout happened to be -- is no longer needed once the
parent itself is canonicalized. **Verdict: agree.** Implemented as designed.

## 3. Implementation

`prepare_phase2_contrastive_candidate_corpus.py`:
- `canonicalize_val_split_bytes()` renamed to `canonicalize_pinned_lf_bytes()`; logic unchanged, now
  shared by both callers.
- `EXPECTED_PARENT_FINGERPRINT` corrected from `197adb35...` (CRLF checkout) to `62d1ea43...`
  (canonical git blob).
- Added `load_canonical_parent_bytes()`, mirroring `load_canonical_existing_val_bytes()`.
- Added `parse_jsonl_records_from_bytes()`; `main()` now parses the 66 parent records from the same
  canonical bytes whose fingerprint was just verified, not a second, independent read of the file.
- Candidate construction: parent-prefix is the canonical LF bytes directly (no terminator detection);
  appended records serialized with explicit `CANONICAL_LF`. `detect_line_terminator()` removed
  entirely -- no remaining callers.
- `verify_parent_preserved_byte_for_byte()` now receives canonical bytes, not a fresh raw read;
  docstring and error text updated to say so.
- Derivation-report item #7 rewritten from "the parent corpus's own raw bytes" to the pinned
  canonical LF representation, mirroring item #8's existing wording for the val split.

`test_prepare_phase2_contrastive_candidate_corpus.py`:
- All `canonicalize_val_split_bytes` call sites renamed to `canonicalize_pinned_lf_bytes`.
- The parent fingerprint-drift negative test, previously (and now incorrectly, since
  `verify_pinned_fingerprints()` no longer checks the parent) attached to that function, moved to a
  new `load_canonical_parent_bytes` section: uniform-CRLF checkout loads and normalizes; fingerprint
  drift fails closed; missing file fails closed.
- Added `parse_jsonl_records_from_bytes` coverage.
- Live checks now exercise `load_canonical_parent_bytes()` against the real, unmodified repository
  file and confirm the parsed record count from those exact bytes -- the same code path `main()` uses.

## 4. Independent verification

- Ran the corrected script cold, real checkout, zero manual normalization: `R2 parent corpus (66
  records): 62d1ea43... (uniform-CRLF checkout, normalized to canonical LF)`. Completed with no fatal
  errors.
- Ran the corrected test suite cold, same terms: `All checks passed.`, including the new live checks
  against the real parent file.
- Candidate corpus file: `7760f377...` -- matches the expected canonical fingerprint exactly.
- The 82 records were parsed from both the old (bundle-accepted) and new candidate files and compared
  for exact object equality: **identical**. The fix changes only the file's byte-serialization
  (CRLF-embedded prefix -> canonical LF prefix), never the record content.
- `train.jsonl` (`597b6120...`), `val.jsonl` (`8aa99a79...`), and `gold_v1.2.2_phase2_contrastive_split_comparison.json`
  (`1b91f788...`) are byte-identical to what was already reviewed -- unaffected, as expected, since
  none of them depend on the parent corpus's raw file bytes.
- `gold_v1.2.2_phase2_contrastive_original_vs_candidate_diff.json`: `parent_content_fingerprint` and
  `candidate_content_fingerprint` are unchanged (`42b250a9...` / `a35702c5...` -- both derived from
  parsed record content via canonical JSON re-serialization, never raw file bytes); only
  `candidate_corpus_file_fingerprint` changed, to `7760f377...`, exactly as required.
- Candidate training-data fingerprint: `62bbee12...` -- unchanged, confirmed live.
- Counts and split membership: 82 records, 76 train / 6 val -- unchanged, confirmed live.
- `phase2_contrastive_implementation_static_review_chatgpt.md`: the stale `9efa7d80...` citation for
  the candidate corpus corrected to `7760f377...`, with the prior value kept visible inline. Its other
  hash citations (script, test, derivation report) are *also* now stale, for the same underlying
  reason -- not edited beyond the one citation explicitly flagged, since this is ChatGPT's authored
  document; noting this transparently rather than silently rewriting further or silently leaving it
  as-is.
- Repository diff: not staged during this fix (everything unstaged after the finding, per the prior
  report); staging and staged-blob re-verification happen after this document, against the corrected
  13-file manifest.

## Updated artifact hashes (this fix)

| Artifact | SHA-256 |
|---|---|
| `prepare_phase2_contrastive_candidate_corpus.py` (twice-corrected) | `803e2e47386a4893d9e40fd2d02631c9c9e844cdeb9520e94b4ffdf601f7908c` |
| `test_prepare_phase2_contrastive_candidate_corpus.py` (twice-corrected) | `bdc51925a4eeced33835790dd489f6860f6bcaea4860ac9721a474b8b870efea` |
| `gold_v1.2.2_phase2_contrastive_derived_candidate.jsonl` (corrected) | `7760f377dcd7ab35b54fe6c2c274e6615a5641acaa73ec0a30da64d78db9df2d` |
| `gold_v1.2.2_phase2_contrastive_corpus_derivation_report.md` (regenerated) | `8e4fa110c1bb88877b4ba2aaca1ae46e4b455c2bd67b9776b5c82b75a5088439` |
| `gold_v1.2.2_phase2_contrastive_original_vs_candidate_diff.json` (regenerated) | `19c84d63e16fb3c04730d852ab925a2d826f17d3151823c1b2a9a5f879e9df6a` |
| `phase2_contrastive_implementation_static_review_chatgpt.md` (one citation corrected) | `ccfe55d5d1656ed21adeb088918481185170185d1e328fbd8a133fd9fac628e9` |

Unchanged from the prior report: `phase2_contrastive_attribution_composite_proposal.jsonl`
(`519823fa...`), `train.jsonl` (`597b6120...`), `val.jsonl` (`8aa99a79...`),
`gold_v1.2.2_phase2_contrastive_split_comparison.json` (`1b91f788...`), and both of Claude's prior
review documents (`ea05827d...`, `9051a360...` -- retained as historical evidence, not edited).

## Disposition

Defect confirmed, corrective design independently agreed, implemented, and verified end-to-end on the
exact checkout where it was found -- including the specific failure mode (a new file's embedded
line-endings silently mutated by `git add`) that made this worth stopping for rather than quietly
patching. The proposed commit scope is now 13 files. Commit and push remain paused pending review of
these corrected artifacts and independent verification of the actual staged blobs, next.
