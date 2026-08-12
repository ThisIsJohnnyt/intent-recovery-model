# Phase-2 Contrastive Implementation — 13-Path Staged-Blob Hash Manifest

**Date:** 2026-08-10 (refreshed a second time: static-review item 11's wording corrected)
**Purpose:** For ChatGPT's final independent review, per the standing Claude+ChatGPT agreement
protocol. Every hash below is the **staged git blob** (`git show ":<path>" | sha256sum`), not a
working-tree file hash — independently re-verified after re-staging the corrected static-review
document. All 13 matched their expected values exactly on re-verification. HEAD is unchanged at
`398874504f2ea3bc8a710a2de56225381ea3900f`; `git diff --stat` on tracked files is empty; nothing
outside this list is staged. **Commit and push have not been run.**

| # | Path | Staged blob SHA-256 |
|---:|---|---|
| 1 | `training/phase2_contrastive_attribution_composite_proposal.jsonl` | `519823faf69bda2dcf74b816c63f15ecc16e5e902bc8f8bdee73a559326fba9c` |
| 2 | `training/prepare_phase2_contrastive_candidate_corpus.py` | `803e2e47386a4893d9e40fd2d02631c9c9e844cdeb9520e94b4ffdf601f7908c` |
| 3 | `training/test_prepare_phase2_contrastive_candidate_corpus.py` | `bdc51925a4eeced33835790dd489f6860f6bcaea4860ac9721a474b8b870efea` |
| 4 | `training/phase2_contrastive_implementation_static_review_chatgpt.md` | `09b3ca445fdb2333cd81c3791681ad0183984402939a8f8c1b2c8659dd9785c7` |
| 5 | `training/gold_v1.2.2_phase2_contrastive_derived_candidate.jsonl` | `7760f377dcd7ab35b54fe6c2c274e6615a5641acaa73ec0a30da64d78db9df2d` |
| 6 | `training/data/processed_gold_v1.2.2_phase2_contrastive_v2contract_seed17/train.jsonl` | `597b61202b4cc805dfc9eb3376e15d10583c13f41d8a44b7d9d13139acd5c658` |
| 7 | `training/data/processed_gold_v1.2.2_phase2_contrastive_v2contract_seed17/val.jsonl` | `8aa99a794f495cf75e6904ee28789e06ac43c1f9ee424f0b2ce2f219527623c4` |
| 8 | `training/gold_v1.2.2_phase2_contrastive_corpus_derivation_report.md` | `8e4fa110c1bb88877b4ba2aaca1ae46e4b455c2bd67b9776b5c82b75a5088439` |
| 9 | `training/gold_v1.2.2_phase2_contrastive_original_vs_candidate_diff.json` | `19c84d63e16fb3c04730d852ab925a2d826f17d3151823c1b2a9a5f879e9df6a` |
| 10 | `training/gold_v1.2.2_phase2_contrastive_split_comparison.json` | `1b91f788275863b5ccbd17f7918ffb10a359066e50a59fcf33b96b7b82522a70` |
| 11 | `training/phase2_contrastive_implementation_claude_cross_review.md` | `ea05827da0c1e9eb711d79621055745959dee0756b2323b61b2900f4f3b0938d` |
| 12 | `training/phase2_contrastive_implementation_autocrlf_fix_claude_review.md` | `9051a3608414faf01841bb97e6342347f42581c37c98c445be69cba8acde6768` |
| 13 | `training/phase2_contrastive_implementation_parent_canonicalization_claude_review.md` | `1da1316619c9af9b9c3195597c0c02945820f66cf4d54918dfd2c6bdb2ff393f` |

Candidate training-data fingerprint (unchanged by any fix): `62bbee12130ea54f6cae3777eb990a9d54a35411ceeba75030755569c44982ae`.

Rows 11–12 are Claude's pre-existing review documents, unedited (retained as historical evidence).
Row 13 is new, recording the parent-canonicalization fix. Row 4 (only row that changed since the
prior manifest) has now been corrected three times: the candidate-corpus hash citation, the three
other stale citations plus the stale parent byte count, and finally item 11's wording ("byte-identical
to the pinned canonical-LF representation of the historical R2 validation split") — all flagged
inline in the document with prior values kept visible. Only row 4's hash changed from the prior
manifest; rows 1–3 and 5–13 are unchanged and were re-verified, not assumed.
