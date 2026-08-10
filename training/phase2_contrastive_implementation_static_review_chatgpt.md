# Phase-2 Contrastive Attribution Implementation - Static Review

Date: 2026-08-10
Repository evidence base: `ThisIsJohnnyt/intent-recovery-model` at commit `398874504f2ea3bc8a710a2de56225381ea3900f`
Authorization: Johnny - "Let's do this," after the corpus implementation and static-validation scope was restated.

## Disposition

IMPLEMENTATION COMPLETE - STATIC CHECKS PASS - READY FOR INDEPENDENT CROSS-REVIEW.

This phase performed deterministic corpus construction and static validation only. It did not perform model training, inference, benchmark execution, seed 73 work, export, deployment, activation, commit, or push.

## Preservation decision

The historical 12-record proposal, 78-record candidate, 72/6 processed split, derivation script, and replay evidence remain immutable. The follow-up uses new filenames and output paths.

The implementation pins and reads the immutable 66-record R2 parent plus the historical 12-record proposal as a reference. It creates a separate 16-record composite:

- P2-001 through P2-008: object-identical to the historical proposal.
- P2-009 and P2-010: only the four authorized background/reporting bullets are removed; input, difficulty, category, narrative, and action items remain exact.
- P2-011 and P2-012: object-identical to the historical proposal, preserving the probe-13 curriculum repair.
- AT-C1 through AT-C4: the four accepted `multi_person_attribution` records, in reviewed order and with difficulty sequence `hard`, `hard`, `expert`, `hard`.

## Derived counts

| Artifact | Count |
|---|---:|
| Immutable R2 parent | 66 |
| Historical proposal reference | 12 |
| New composite proposal | 16 |
| New candidate corpus | 82 |
| New training split | 76 |
| Frozen validation split | 6 |

## Fail-closed implementation checks

All checks passed:

1. Seven inputs are SHA-256 pinned: parent, historical proposal, composite proposal, split manifest, existing frozen R2 validation file, protected-16 benchmark, and acceptance-10 benchmark.
2. Composite schema, counts, label order, category values, and difficulty values are exact.
3. Ten historical proposal records are unchanged.
4. P2-009/P2-010 reject any non-bullet change, any addition, any reordering, or any removal beyond the four authorized bullets.
5. AT-C1 through AT-C4 reject category or difficulty drift.
6. No input duplicates or exact collisions exist within the parent, within the proposal, between parent and proposal, or against the 26 pinned benchmark inputs.
7. Every generated `v2_target` parses and round-trips exactly to its authored narrative, bullets, and actions.
8. The candidate begins with the exact 101,144 pinned canonical LF parent bytes (corrected 2026-08-10; was 101,210 CRLF-checkout bytes before the parent-canonicalization fix) and appends all 16 proposal records in reviewed input-hash order.
9. A fresh independent split reconstruction exactly equals the written 76-record train file and 6-record validation file.
10. Every proposal input is in training and none is in validation.
11. The written validation file is byte-identical to the pinned canonical-LF representation of the historical R2 validation split.
12. The standalone test script, including negative fail-closed cases, passes completely.

## Artifact hashes

| Artifact | SHA-256 |
|---|---|
| `phase2_contrastive_attribution_composite_proposal.jsonl` | `519823faf69bda2dcf74b816c63f15ecc16e5e902bc8f8bdee73a559326fba9c` |
| `prepare_phase2_contrastive_candidate_corpus.py` | `803e2e47386a4893d9e40fd2d02631c9c9e844cdeb9520e94b4ffdf601f7908c` (corrected 2026-08-10, twice: val-split then parent-corpus canonicalization; was `e89dbffb43e613a926e9552cde7cb1667bf5dc3e2355f23a1d01db9d39f26602`) |
| `test_prepare_phase2_contrastive_candidate_corpus.py` | `bdc51925a4eeced33835790dd489f6860f6bcaea4860ac9721a474b8b870efea` (corrected 2026-08-10, twice; was `9681647bc13a999111218d2b25fdd5e5fb323c717b668c31cd2da4aa346d301c`) |
| `gold_v1.2.2_phase2_contrastive_derived_candidate.jsonl` | `7760f377dcd7ab35b54fe6c2c274e6615a5641acaa73ec0a30da64d78db9df2d` (corrected 2026-08-10 per the parent-canonicalization fix; was `9efa7d80d13ec96207252024b3fe1d39c82c1f2885dcf57d69e9f682bf86f259`) |
| `processed_gold_v1.2.2_phase2_contrastive_v2contract_seed17/train.jsonl` | `597b61202b4cc805dfc9eb3376e15d10583c13f41d8a44b7d9d13139acd5c658` |
| `processed_gold_v1.2.2_phase2_contrastive_v2contract_seed17/val.jsonl` | `8aa99a794f495cf75e6904ee28789e06ac43c1f9ee424f0b2ce2f219527623c4` |
| `gold_v1.2.2_phase2_contrastive_corpus_derivation_report.md` | `8e4fa110c1bb88877b4ba2aaca1ae46e4b455c2bd67b9776b5c82b75a5088439` (regenerated 2026-08-10; was `c5128102d36e5c8cbededbc89174473f59620ffad9d66fd9ab48df7811fbf5ea`) |
| `gold_v1.2.2_phase2_contrastive_original_vs_candidate_diff.json` | `19c84d63e16fb3c04730d852ab925a2d826f17d3151823c1b2a9a5f879e9df6a` (regenerated 2026-08-10 -- candidate_corpus_file_fingerprint field changed; was `cc38619b2529c632aa488412b738c1eab3159b0290b3d9e22b1356a3ca1d543f`) |
| `gold_v1.2.2_phase2_contrastive_split_comparison.json` | `1b91f788275863b5ccbd17f7918ffb10a359066e50a59fcf33b96b7b82522a70` |

Canonical candidate training-data fingerprint: `62bbee12130ea54f6cae3777eb990a9d54a35411ceeba75030755569c44982ae` (unchanged by either fix).

## Requested independent review

The next reviewer should independently verify:

1. The new-file preservation decision is preferable to editing historical Phase-2 artifacts in place.
2. The 16-record composite is exactly the reviewed 12-to-16 transformation.
3. The new derivation script pins all intended inputs and preserves the split-membership algorithm.
4. The generated 82-record candidate and 76/6 split reproduce from the script.
5. No static guard or artifact-specific count, path, label, fingerprint, or report expectation was missed.

Any disagreement returns this work to implementation review. It does not authorize training/evaluation compute, seed 73, commit/push, export, deployment, or activation.
