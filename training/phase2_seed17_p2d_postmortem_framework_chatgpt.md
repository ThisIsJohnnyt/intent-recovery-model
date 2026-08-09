# Seed-17 Phase-2 P2-D Postmortem — Analysis Framework (ChatGPT)

**Date:** 2026-08-07  
**Status:** Cross-review framework; no corpus change or new compute authorized  
**Evidence packet reviewed:** `phase2_seed17_p2d_postmortem_evidence_packet_claude.md`  
**Evidence-packet SHA-256:** `4767c318d8933c8536e6a44dc658f46b7cc2f02a7211542726fc7a072134e8c2`

## 1. Decision question

The closed replay is P2-D. This postmortem must decide which of the following is justified by the
existing evidence:

1. stop Phase 2;
2. design another controlled curriculum experiment; or
3. perform a narrower, read-only diagnostic before deciding.

The current recommendation is **option 3**. The evidence explains probe 13 well, but it does not
yet isolate the cause of probe 06 strongly enough to justify another curriculum or training run.

## 2. Findings and causal confidence

| Finding | Evidence | Confidence | Interpretation |
|---|---|---:|---|
| Probe 13 was repaired by targeted curriculum coverage. | `two_unrelated_tasks` representation increased from 1 to 3; an added gold target explicitly preserves two independent actions; both Phase-2 runs repaired the exact prior omission. | High once actual train-split membership is mechanically bound | Direct, proportionate support for the intended curriculum effect. |
| Probe 06 exposed a contradictory attribution pattern already present in the parent gold data. | The Rina/Marcus gold target resolves an explicitly flagged ambiguous pronoun to the second-named person; both Phase-2 runs resolve probe 06 to the second-named person in the bullet. | Medium-high as a contributor; low as a sole cause | Strongest current explanation, but not causally isolated. |
| The probe-06 bullet defect was established by step 600. | Control and primary contain the identical incorrect bullet; only the primary additionally resolves the narrative to Rowan. | High | The final 120 steps did not create the core bullet error; they changed its expression in the narrative. |
| Step count has probe-specific, non-monotonic effects. | From 600 to 720, probe 09 changes from fail to pass while probe 06's narrative changes from ambiguous to incorrect. | High descriptively | "More steps" is not a generally safe remedy. It improves one protected behavior while degrading another. |
| Training loss is not a sufficient selection signal. | Both runs are near-converged, and the lower final-batch loss belongs to the weaker protected result. | High | Checkpoint choice must remain behavior-gated, not loss-gated. |

## 3. Important precision checks for the evidence packet

### 3.1 Realized trajectory

Primary and control used byte-identical processed data, the same declared seed, and the same shared
configuration, differing in training horizon. That makes them a strong **paired training-horizon
comparison**.

They were nevertheless executed as separate subprocesses. Matching inputs and seed do not, by
themselves, prove byte-identical optimizer/model states through step 600. Therefore the phrases
"the same training trajectory" and "sampled 120 steps earlier" should be treated as provisional
unless one of these is demonstrated:

- the primary step-600 checkpoint is byte/state-equivalent to the control final checkpoint;
- the complete per-step loss/state history through step 600 matches under documented deterministic
  execution; or
- the training stack provides a separately verified determinism guarantee sufficient for this
  comparison.

This does not invalidate the observed 600/720 output comparison. It narrows the inference: the
different behaviors are associated with the two training horizons under matched declared
conditions, but should not yet be described as changes along one proven-identical realized
trajectory.

### 3.2 Curriculum count versus actual train split

The packet says the `two_unrelated_tasks` count increased from 1 to 3 and cites the frozen candidate
corpus. For the causal claim, the final packet should also identify both added record IDs in the
actual processed `train.jsonl` used by the runs, or otherwise prove that neither entered validation.
Candidate-corpus membership alone is not training exposure. This is likely a documentation gap,
not a substantive defect, but the exact 3× statement should be bound to the realized train split.

## 4. Working causal model

The evidence currently supports this model:

1. The added `two_unrelated_tasks` examples supplied a direct corrective signal for probe 13.
2. Phase-2 also changed the overall optimization context and output behavior enough to expose a
   latent attribution rule already encoded inconsistently in an unchanged gold example.
3. That latent rule appears first in probe 06's generated bullet by step 600 and extends into the
   narrative by step 720.
4. Meanwhile, additional training helps probe 09, showing that the final 120 steps are neither
   uniformly harmful nor uniformly helpful.

Point 1 is well supported. Points 2-3 are the leading explanation, not a proven mechanism. In
particular, zero new examples in the `multi_person_attribution` category does not mean the new
curriculum cannot affect that behavior: cross-category interference, target-style changes, and
global optimization effects remain plausible.

## 5. Narrow diagnostic required before a new proposal

Claude should assemble a second, read-only evidence supplement with four bounded checks.

### A. Attribution-label consistency audit

Inspect all three `multi_person_attribution` training records and every other training record that
contains an ambiguous personal pronoun or an explicit uncertainty statement about identity.
For each record, report:

- source wording and candidate antecedents;
- whether ambiguity is preserved or resolved in each gold field;
- if resolved, which antecedent is selected and why;
- consistency with probe 06's `expected_behavior` and primary checks;
- train/validation membership in R2 and Phase 2.

The goal is to determine whether Rina/Marcus is an isolated bad label, one side of a genuine policy
conflict, or evidence of a broader attribution inconsistency.

### B. Added-curriculum output-style audit

Inspect all 12 Phase-2 additions for target patterns that may indirectly encourage the new probe-06
bullet or explicit resolution, including:

- converting narrative clauses into standalone bullets;
- restating background events as facts;
- resolving referents that the input leaves uncertain;
- adding a bullet whose content is not required for the user's actionable intent.

Also list each added record's processed split membership and explicitly confirm the realized
train-split count for `two_unrelated_tasks`.

This check tests the possibility that probe 06's new bullet arose from a general target-shape shift,
not only from the unchanged Rina/Marcus example.

### C. Training-horizon comparability check

Determine, without new training or inference, whether the artifacts permit an exact comparison of
the realized states through step 600:

- compare a primary step-600 checkpoint with the control final checkpoint if both exist;
- otherwise compare available per-step logs through step 600 and document what they can and cannot
  prove;
- report determinism settings and any known nondeterministic operations.

If exact equivalence cannot be established, retain "paired training-horizon comparison" in the
postmortem and remove "same trajectory" claims.

### D. Probe-level output-shape comparison

Compare R2, control, and primary protected outputs for probes 06, 09, and 13 at the field level:

- which facts moved among narrative, bullets, questions, and action items;
- which fields were newly generated or omitted;
- whether the change is semantic, structural, or both.

The packet already contains the core outcomes; this check should explain the output-shape mechanism
without broadening into full benchmark rescoring.

## 6. Decision rules after the supplement

| Result of narrow diagnostic | Recommended disposition |
|---|---|
| Attribution inconsistency is systemic or policy-ambiguous. | Stop experiment design; first produce a governed gold-label correction proposal and rubric-alignment review. |
| Rina/Marcus is isolated, and added target style clearly explains the probe-06 bullet. | Draft a narrow curriculum revision that removes the problematic style signal while retaining the probe-13 coverage; review before any compute. |
| Rina/Marcus is isolated, but no plausible pathway to the regression is found. | Do not guess at a curriculum fix; either stop Phase 2 or propose one minimal causal ablation under a new authorization. |
| Realized primary/control trajectories differ before step 600. | Treat step-effect conclusions as run-to-run variation; do not use 600-720 behavior deltas as checkpoint-timing evidence. |
| Realized states match through step 600. | Retain the conclusion that the final 120 steps repaired probe 09 while extending probe 06's defect into the narrative. |

## 7. Preliminary recommendation

Do **not** draft another 12-record curriculum or authorize another training run yet. The immediate
next action is the narrow read-only supplement in §5.

The likely design principle, if the supplement confirms the current causal model, is not merely
"add more probe-06 examples." The higher-value correction would be to make attribution policy
internally consistent across gold targets and rubrics, then preserve the successful
`two_unrelated_tasks` signal without encouraging unnecessary factual restatement. Any resulting
corpus proposal should be reviewed as a data-quality correction plus a controlled curriculum
change, not as a larger-volume retry.

## 8. Authorization boundary

This framework authorizes nothing. No corpus edit, gold-label correction, training, inference,
rerun, seed 73, export, deployment, activation, commit, or push follows from it. The evidence
supplement in §5 is read-only and should be independently cross-reviewed before a final
postmortem recommendation is issued.
