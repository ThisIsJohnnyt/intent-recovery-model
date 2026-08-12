# Seed-17 Phase-2 P2-D Postmortem — Final Decision Memo

**Date:** 2026-08-09  
**Author:** ChatGPT  
**Status:** Final postmortem recommendation; awaiting Johnny's decision  
**Evidence commit:** `398874504f2ea3bc8a710a2de56225381ea3900f` on `main`  
**Decision recommended:** Proceed to a minimal, design-only contrastive attribution proposal. Do not authorize compute.

## 1. Executive decision

The seed-17 Phase-2 replay should remain closed as **P2-D**. It should not be rerun unchanged, extended to seed 73, or revived through checkpoint selection.

The evidence does, however, justify one narrowly scoped next step: design a **minimal contrastive attribution and field-role proposal** for static review. The proposal should preserve the curriculum signal that repaired protected probe 13, add balanced coverage around the attribution boundary exposed by protected probe 06, and remove unintended pressure for non-actionable background clauses to become standalone bullets.

The valid Rina/Marcus example must not be corrected or deleted.

This memo recommends that Johnny authorize proposal design. It does not itself authorize corpus edits, derivation, training, inference, a rerun, seed 73, checkpoint selection, export, deployment, activation, commit, or push.

## 2. Evidence disposition

### Established findings

| Finding | Confidence | Decision consequence |
|---|---:|---|
| Probe 13 was repaired in both the 600-step control and 720-step primary after realized training-split coverage for `two_unrelated_tasks` increased from one example to three. | High | Preserve the two effective additions and protect this repair in every later review. |
| Probe 06 acquired a new incorrect attribution bullet by step 600; the narrative attribution also became incorrect only in the 720-step run. | High | Treat the bullet and narrative failures as distinct field-level defects with different observed onset points. |
| Rina/Marcus is correctly labeled and is the corpus's sole close structural analogue for this two-pronoun pattern. | High | Do not perform a gold-label correction. Add contrasts that prevent positional overgeneralization. |
| Two added `cross_field_completeness` examples teach a style in which reported or background clauses are echoed as bullets, including non-actionable observations. | High that the signal exists; medium that it contributed to probe 06 | Audit those targets and constrain field roles in the next design. |
| Probe 09 fails at 600 steps but passes at 720, while probe 06's narrative moves in the opposite direction. | High descriptively | Do not treat a longer training horizon as a general remedy. |
| The two runs used matched declared conditions but separate subprocesses; their losses were close, not identical, and exact state equivalence at step 600 cannot be established. | High | Use "paired training-horizon comparison," never "same trajectory." |

### Plausible but unproven mechanism

The best current explanation for probe 06 is a two-part interaction:

1. The correctly labeled Rina/Marcus example may have supplied a positional shortcut: resolve the earlier pronoun to the second-named or most-recent person.
2. The new `cross_field_completeness` targets may have supplied the output-shape pressure to echo that resolved background clause as a standalone bullet.

This mechanism fits the observed output, corpus structure, and field-level timing. It has not been causally isolated by ablation, so it must guide a minimal contrastive design rather than be presented as proven fact.

## 3. Explanations ruled out or unsupported

- **A defective Rina/Marcus gold label:** ruled out. Its earlier pronoun is reasonably resolved by gender agreement, while its separately flagged Marcus-or-client ambiguity is correctly preserved.
- **A systemic attribution-label inconsistency:** not found in the 78-record corpus sweep.
- **A direct new `multi_person_attribution` curriculum effect:** unsupported; no examples in that category were added.
- **A proven single 600-to-720 trajectory:** unsupported; exact state equivalence is unavailable and deterministic execution was not enforced.
- **"More steps will fix it":** contradicted as a general strategy by the opposite movements of probes 06 and 09.
- **Another broad 12-record curriculum expansion:** not justified by the bounded evidence and would weaken causal interpretability.
- **Reopening the closed replay or advancing seed 73:** prohibited by the P2-D outcome.

## 4. Required shape of the design-only proposal

### A. Preserve the successful probe-13 signal

Retain both effective `two_unrelated_tasks` additions unchanged unless a separate record-level defect is discovered. The proposal must explain how every change avoids weakening two-task retention.

### B. Build a four-case attribution contrast

The smallest defensible core is four semantically paired examples:

1. **Resolvable earlier pronoun:** strong textual evidence supports one antecedent; the target resolves it.
2. **Unresolvable earlier pronoun:** the same surface construction lacks sufficient evidence; the target preserves uncertainty.
3. **Mixed boundary:** an earlier pronoun is resolvable while a later, explicitly flagged identity question remains unresolved.
4. **Order-swapped control:** names or clause order are reversed so "choose the second-named person" cannot succeed as a shortcut.

Across the set, names, ordering, and surface form must be balanced. The intended lesson is evidence-based resolution — not gender alone, recency alone, name position, or nearest-mention heuristics.

These are semantic requirements, not authorization to author or add the records yet.

### C. Constrain field roles

Audit the two identified `cross_field_completeness` additions. Revise or replace only target content that teaches a non-actionable background or reported-speech clause to become its own bullet. Preserve the records' intended cross-field completeness lesson.

Every proposed bullet must have an explicit justification: actionable content, a required decision constraint, a preserved uncertainty, or another contract-required role. Narrative completeness alone is not sufficient reason to create a bullet.

### D. Avoid scope expansion

Do not add broad paraphrase variety, increase unrelated categories, change the prompt contract, change the benchmark rubric, or choose a new training horizon during this design phase. Any such change would require its own evidence and authorization.

## 5. Static gates before any corpus-edit or compute decision

A proposal should not advance unless all of the following are demonstrated:

- Every proposed target passes independent record-level semantic review.
- The attribution set includes both resolve and preserve-uncertainty outcomes.
- Swapped ordering and varied surface forms defeat positional shortcuts.
- No example resolves an explicitly preserved ambiguity.
- No non-actionable background clause becomes a bullet without a contract-based justification.
- Both probe-13 corrective examples remain intact.
- Expected effects and regression risks are named for protected probes 06, 09, and 13.
- Intended split membership is specified, then later confirmed against the realized processed split.
- Split drift, benchmark overlap, duplication, contract changes, and unrelated corpus changes are absent or separately justified.
- Exact file hashes and a record-level change manifest are produced before any execution-package review.
- ChatGPT and Claude independently review the design and explicitly report agreement or disagreement.

Failure of any static gate returns the work to design. It does not justify compute as a diagnostic shortcut.

## 6. Risks of another curriculum attempt

| Risk | Required mitigation |
|---|---|
| Replacing one shortcut with another, such as always choosing the gender-matching or nearest name | Balanced resolve/unresolved cases plus order-swapped controls |
| Overcorrecting by preserving every pronoun as ambiguous | Include cases with genuinely sufficient resolution evidence |
| Repairing probe 06 while losing probe 13 again | Freeze the effective `two_unrelated_tasks` examples and make probe 13 an identity-level preservation gate |
| Reintroducing probe 09's invented-question behavior | Include probe 09 in the explicit protected regression set |
| Confounding attribution changes with output-style changes | Record each target change by mechanism and keep the candidate set minimal |
| Mistaking run variation for a training-horizon effect | Use a newly sealed control plan and behavior gates; do not select by loss alone |

## 7. Evaluation principle for any future experiment

If a later proposal clears static review and Johnny separately authorizes a new experiment package, success must be judged by protected-set identity rather than aggregate count alone.

At minimum, a future candidate must:

- restore protected probe 06;
- retain the probe-13 repair;
- preserve every other protected pass required by the governing baseline;
- avoid the probe-09 invented-question regression; and
- satisfy the complete, newly frozen gate matrix for that experiment.

The closed P2-D run cannot be converted into seed-73 eligibility. A future experiment would require a new reviewed hypothesis, new frozen artifacts, a new authorization chain, and explicit stop conditions.

## 8. Ownership and next decision

| Owner | Next action after authorization |
|---|---|
| ChatGPT | Draft the semantic design specification and four-case contrast templates. |
| Claude | Cross-review the design against repository evidence and produce a read-only mapping to affected records. Corpus edits and static implementation tests require Johnny's separate authorization. |
| Johnny | Accept, reject, or revise this recommendation; separately authorize design, corpus edits, package construction, and compute at their respective gates. |

The immediate decision requested from Johnny is only:

> **Authorize or decline design of the minimal contrastive attribution and field-role proposal.**

## 9. Final disposition

**POSTMORTEM COMPLETE — RECOMMEND A MINIMAL, DESIGN-ONLY CONTRASTIVE ATTRIBUTION PROPOSAL.**

Preserve the probe-13 training signal. Do not modify Rina/Marcus. Address probe 06 through balanced attribution contrasts and explicit field-role constraints. Treat training-horizon effects as descriptive evidence, not the intervention.

No compute or downstream action is authorized by this memo.

## 10. Provenance and precedence

The evidence base is committed on `main` at `398874504f2ea3bc8a710a2de56225381ea3900f`:

- `training/phase2_seed17_p2d_postmortem_framework_chatgpt.md` — Git blob `53d45a6551e64c9b88a7977d136cb91f664fd8fe`
- `training/phase2_seed17_p2d_postmortem_evidence_packet_claude.md` — Git blob `1916b1e1fff98c1dac0186a02a754f4ba81cf209`
- `training/phase2_seed17_p2d_postmortem_evidence_supplement_claude.md` — Git blob `e9348e52b10ba1d4fc06058459d0942d90fef084`

The corrected packet and supplement govern the final factual interpretation. Where the earlier framework's preliminary Rina/Marcus hypothesis conflicts with those corrections, the corrected packet and supplement supersede it. The framework remains the historical record of the diagnostic questions and decision rules that led to this memo.
