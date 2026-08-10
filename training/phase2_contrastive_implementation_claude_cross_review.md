# Phase-2 Contrastive Attribution Implementation — Claude Cross-Review

**Date:** 2026-08-10
**Scope:** Independent, from-scratch verification of the implementation claimed in
`phase2_contrastive_implementation_static_review_chatgpt.md` and
`gold_v1.2.2_phase2_contrastive_corpus_derivation_report.md`
(bundle: `C:\Users\thisi\Downloads\phase2_contrastive_implementation_review_bundle`).
Nothing in the actual repository was modified by this review — all reproduction ran in an
isolated scratch mirror outside the repo, and this document itself is uncommitted.

## 0. Authorization provenance

This is design/implementation work I was not present for. Its authorization ("Johnny —
'Let's do this,' after the implementation scope and exclusions were restated") happened directly
in the parallel ChatGPT-side conversation, which I only saw because its full page export was
pasted into this conversation. I did not independently witness Johnny's authorization inside
*this* conversation before the work was done. Noting this transparently rather than silently
treating it as equivalent to an in-thread authorization: it is Johnny's prerogative to authorize
ChatGPT's actions directly without routing every step through me, and the resulting artifacts are
now independently verified below — but the record should show the authorization for actual
corpus/script construction (as opposed to design or drafting) originated outside this thread.

## 1. Bundle integrity

Both independently checkable top-level hashes matched exactly:

| Artifact | Claimed | Verified |
|---|---|---|
| `phase2_contrastive_implementation_review_bundle.zip` | `926c09cc...6d8dcf` | Match |
| `phase2_contrastive_implementation_static_review_chatgpt.md` | `4eaa205e...4be774` | Match |

All nine files inside the bundle were hashed; every artifact-hash claim in the two report
documents matched the actual bundle file it described.

## 2. Composite proposal (16 records) — verified programmatically, not by eye

Loaded the historical 12-record proposal, the new 16-record composite, the accepted P2-009/P2-010
remediation drafts, and the accepted AT-C1–AT-C4 exact drafts, and checked object equality
field-by-field (script, not manual inspection):

- `composite[0:8]` (P2-001…P2-008): object-identical to the historical proposal.
- `composite[8]` (P2-009): object-identical to the accepted remediation draft; `input`,
  `difficulty`, `category`, `narrative`, `action_items` unchanged from historical; bullets reduced
  6→4 by removing exactly the two authorized background/reporting lines, none added.
- `composite[9]` (P2-010): same result, the other two authorized bullets removed, none added.
- `composite[10:12]` (P2-011, P2-012 — the probe-13 curriculum repair): object-identical to the
  historical proposal.
- `composite[12:16]` (AT-C1…AT-C4): object-identical to the exact drafts I already cross-reviewed
  and accepted in the prior turn, in the same order.
- Difficulty sequence `hard, hard, expert, hard` — matches the claim exactly.
- Schema exact on all 16 records; no duplicate inputs; no `high_count_task_retention` category.

No drift, no silent change, no reordering.

## 3. Derivation script — diffed line-by-line against the original

`prepare_phase2_contrastive_candidate_corpus.py` vs. the original
`prepare_phase2_candidate_corpus.py`: the actual construction logic
(`build_candidate`, `build_split`, `verify_no_duplicate_or_colliding_inputs`, the byte-preservation
checks) is untouched. The diff is confined to:

- new pinned paths/fingerprints for the composite proposal and its new output filenames;
- an added `EXISTING_R2_VAL_PATH` fingerprint pin (a new safety check, not present in the original);
- updated count constants (12→16, 78→82, 72→76);
- a new `verify_composite_construction()` function — an active, fail-closed runtime re-check of
  exactly the delta in §2 above, not just a claim in a report; and
- docstring/report text updates.

This matches what my own R1 design cross-review anticipated would be needed ("a script constant
change... to a currently frozen, fingerprint-pinned file") and nothing more.

## 4. Independent from-scratch reproduction

Rather than trust the report, I rebuilt the minimum dependency set (`prepare_data.py`,
`prompt_contract_v2_candidate.py`, `prompt_contract_v2_migrate.py`, `prompt_contract_v2_parser.py`,
the frozen split manifest, the R2 parent, the historical proposal, the existing R2 val split, and
both benchmark files — all copied read-only from the real repo at HEAD `3988745...`) in an isolated
scratch mirror outside the repository, dropped in the bundle's script and composite proposal
unmodified, and ran it myself.

One real hiccup, fully diagnosed: my first run failed the existing-R2-val-split fingerprint check.
Cause: my Windows working-tree checkout of that file carries `autocrlf`-converted CRLF line
endings (`git status` shows it clean; `git show HEAD:<path> | sha256sum` matches the pinned
fingerprint exactly) — the same benign class of discrepancy already diagnosed earlier in this
project, this time on my side rather than ChatGPT's. Substituting the actual git-blob bytes
resolved it; the run then completed cleanly end-to-end with **zero fatal errors**.

Byte-for-byte comparison of my reproduction against the bundle's delivered files:

| Output | Result |
|---|---|
| `gold_v1.2.2_phase2_contrastive_derived_candidate.jsonl` (82 records) | Byte-identical |
| `data/.../train.jsonl` (76 records) | Byte-identical |
| `data/.../val.jsonl` (6 records) | Byte-identical |
| `gold_v1.2.2_phase2_contrastive_corpus_derivation_report.md` | Identical after CRLF normalization |
| `gold_v1.2.2_phase2_contrastive_original_vs_candidate_diff.json` | Identical after CRLF normalization |
| `gold_v1.2.2_phase2_contrastive_split_comparison.json` | Identical after CRLF normalization |

The three "after CRLF normalization" cases are Python's `Path.write_text()` emitting
platform-default line endings (CRLF on my Windows run vs. LF on whatever environment produced the
bundle) — confirmed by byte-for-byte identity once `\r` is stripped from both sides, and by the
markdown report's CRLF-stripped hash matching the bundle's claimed hash for that file exactly
(`c5128102d36e5c8cbededbc89174473f59620ffad9d66fd9ab48df7811fbf5ea`). Not a content discrepancy.

The printed candidate training-data fingerprint from my independent run —
`62bbee12130ea54f6cae3777eb990a9d54a35411ceeba75030755569c44982ae` — matches the claimed fingerprint
exactly.

## 5. Standalone test suite — run independently, not just read

Ran `test_prepare_phase2_contrastive_candidate_corpus.py` directly (no pytest dependency, matches
this repo's convention) against the scratch mirror. Every positive and fail-closed negative case
passed, including the live checks against the real pinned files:

```
All checks passed.
```

## 6. Real repository confirmed untouched

`git status --porcelain` at HEAD `398874504f2ea3bc8a710a2de56225381ea3900f`: unchanged from before
this review — only the pre-existing untracked design/postmortem docs already in the tree, no new
`phase2_contrastive_*` files, no modified tracked files. The historical Phase-2 78-record candidate,
its derivation report, its 72/6 split, and the original derivation script are all still present and
were never at risk of collision — the new script writes to entirely differently-named output paths.

## 7. Targeted re-checks of prior findings

- AT-C1–AT-C4 input hashes in the delivered diff report match, byte-for-byte, the hashes I
  independently verified during the exact-draft cross-review — same four records, no substitution.
- "Maya" (my R1 name-reuse finding): zero occurrences in both the composite proposal and the
  82-record candidate — confirms the R2 rename actually made it into the implementation.
- "Elena has zero prior occurrences" (claimed in the exact-draft report): confirmed zero occurrences
  in the real 66-record parent corpus.

## 8. Disagreements

None found. Every checkable claim in both report documents reproduced exactly, independently, from
the pinned inputs — not merely re-read.

## Recommendation

**ACCEPT.** The 16-record composite, the derivation script's changes, the 82-record candidate, and
the 76/6 split all reproduce exactly from scratch in an isolated environment. No defect, no
unauthorized drift, no silent change to the historical Phase-2 evidence.

## Non-authorizations (unchanged)

This review authorizes nothing further. The bundle's artifacts remain outside the repository
(`C:\Users\thisi\Downloads\...`); nothing has been copied into the repo, committed, or pushed by
this review. No training, inference, benchmark execution, seed 73, export, deployment, or
activation was performed or is authorized by this document. Whether and when to bring these
artifacts into the repository is Johnny's decision.
