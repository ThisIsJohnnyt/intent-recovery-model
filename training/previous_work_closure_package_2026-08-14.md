# Previous-work closure package

**Date:** 2026-08-14  
**Author:** ChatGPT  
**Status:** Independently verified by Claude after correction; pending Johnny's disposition decisions  
**Scope:** Documentation-only Milestone 1  

## 1. Purpose and authority boundary

This package closes the navigation and status gaps found in the 2026-08-14 previous-work audit. It does not rewrite historical evidence. It identifies later decisive records, separates current facts from proposed dispositions, and registers implementation-safety work for separately authorized milestones.

Johnny authorized drafting Milestone 1 on 2026-08-14. That authorization does **not** include code changes, repository cleanup, dataset access, corpus mutation, annotation, model execution, training, evaluation, checkpoint operations, deployment, staging, commit, or push. Claude verification does not expand this authority.

## 2. Verified repository baseline

Read-only verification at drafting time established:

- DeepThoughts: `main`, `HEAD = main = origin/main = a20bd9056363ec1aae2a940b999080d7a3de3ec7`.
- The earlier detached worktree commit `4f568e0` is an ancestor of current `main`; it is stale, not unique work that must be recovered.
- thought-organizer-app: clean `main`, `HEAD = main = origin/main = 7710a00975128c2c538584751fe21528a0a6e381`.
- App branch `reconcile-bullet-count-prompt` and its remote both point to `cf76cd9f1fdd53bdc322e0e8084df679d09a78c4` and diverge from current app `main`.

Safe start rule for later work: begin from a read-only-verified current `main`, preserve unrelated and untracked files, and create an explicitly scoped branch/worktree only after the relevant milestone is authorized. Never reset, clean, move, or delete files merely to make a stale detached worktree resemble `main`.

## 3. Current milestone standing

| Area | Decisive evidence | Current standing |
|---|---|---|
| RBR17-C outcome/postmortem | `f926505ad1147abb033a88d9ea443f4c39f8b164` | Treatment and comparator failed governing gates. The 78-record comparator remains the reference lineage; the 85-record treatment and seven-record delta are evidence only. No seed 73, promotion, or follow-up compute is authorized. |
| Discovery audit | `afa32b897b4a0c279b10f6c410e8a596fd6f5d0f`, `4d9a72c9589e5d43855411bf7dc4b8abaa0f65a5` | DialogSum and QMSum are blocked at A1. No A2 access or external dataset access is authorized. Optional rights research is deferred. |
| Mechanism/representation audit | `9f2226f1e2d052115631696069a6c32c3d433fc8`, `56a01b46134feaa76edb75cc3a5996ee4cd34e76` | Static evidence favors representation/objective investigation over broad corpus expansion or immediate capacity comparison. Comparator record 035 remains an unadjudicated possible policy inconsistency; no corpus correction is authorized. |
| Typed representation / auxiliary spans | `a20bd9056363ec1aae2a940b999080d7a3de3ec7` | Verbose emitted typed plans hit the capacity stop; the compact emitted pilot failed its decision gate; non-emitted auxiliary supervision remains conceptually viable. The first dual-annotation pilot failed exact agreement on 3/10 and triggered its hard stop. No guide revision, second pilot, full annotation, implementation, or compute is authorized. |

The four unresolved annotation conventions are:

1. whether clauses without their own output-field realization receive independent propositions;
2. consistent adoption or rejection of the implicit-writer actor convention;
3. the boundary of `coreference`, especially entity/pronoun reference versus unresolved event alternatives;
4. qualifier span/type rules, including when one phrase receives multiple qualifier types.

## 4. Cross-repository prompt and contract inventory

| Contract/path | Repository state | Status and consequence |
|---|---|---|
| Historical exact `source-determined-bullets-v1` contract | `training/app_prompt_bullet_count_reconciliation.md` describes app activation as pending | **Superseded instruction. Do not activate.** `training/prompt_contract_seed17_postmortem.md` later explicitly retires this exact contract as a deployment candidate while retaining the product goal. |
| Live app single-pass/chunk prompt | app `src/services/noteOrganizer.ts`, lines 5-22 and assembly at lines 65/130 on `7710a00` | Active wording is a third variant: `one bullet per source-supported key idea; use as many as the note supports, up to seven; do not duplicate or invent content to reach a minimum`. It is neither the historical old wording nor the exact canonical v1 sentence. There is no live contract-version constant or fingerprint gate. |
| Live app long-input merge prompt | app `src/services/noteOrganizer.ts`, lines 157-170 on `7710a00` | Inputs above `maxInputTokens = 6000` are chunked and then passed through a separately inlined merge prompt. That prompt lacks the seven-bullet ceiling, several source-support/no-invention constraints, and a version identifier. Production prompt behavior is therefore path-dependent and unfingerprinted. This is a static risk finding, not proof of an observed production failure. |
| Typed-marker v2 candidate | app commit `732fafb`; `src/services/promptContractV2Candidate.ts` and related parser/tests on app `main` | `source-determined-items-v2-candidate` is feasibility-only and inactive. It is not wired into `streamOrganizedNotes` and must not be described as production behavior or promoted without separate authorization. |
| Divergent reconciliation branch | app `reconcile-bullet-count-prompt` at `cf76cd9` | Early reconciliation work reached `main`, while later canonical-version/fingerprint work remains only on this branch. A two-dot full-tree comparison makes the newer v2 feasibility files appear deleted because the branch forked before v2 landed on `main`; the merge-relevant three-dot diff shows the branch introduces no v2 deletions, so a proper three-way merge would retain those files. The branch still must not be merged or archived mechanically because the semantic relationship between its v1 `promptContract.ts` work, both current live prompt paths, and the later v2 candidate has not been designed or tested. Its disposition belongs in the separately gated app prompt-safety proposal. |

Authoritative interpretation: the exact v1 activation handoff is retired; current production has two live prompt paths that require inventory and safety design; v2 is inactive feasibility code.

## 5. Supersession index for stale historical status text

Historical artifacts remain unchanged. Readers should use this index to find later decisive evidence.

| Historical artifact / stale statement | Superseding or closing evidence | Current interpretation |
|---|---|---|
| `training/app_prompt_bullet_count_reconciliation.md`: app activation of exact v1 pending | `training/prompt_contract_seed17_postmortem.md`, especially the retirement decision | Exact `source-determined-bullets-v1` is retired as a deployment candidate; do not follow the old activation instructions. |
| `training/controlled_seed17_rbr17c_static_mechanism_audit_chatgpt.md`: Claude verification required | Commit `56a01b46134feaa76edb75cc3a5996ee4cd34e76` and the converged 2026-08-14 audit record | Verification occurred; the historical status line remains as written. |
| `training/controlled_seed17_aux_span_annotation_pilot_status.md`: Claude pass pending | Commit `a20bd9056363ec1aae2a940b999080d7a3de3ec7`, including the sealed Claude annotation and disagreement record | Claude's pass is complete; 3/10 exact disagreements triggered the hard stop. |
| `training/production_checkpoint_recovery_handoff.md`: checkpoint-600 still open/missing unless recovered | The two independent 2026-08-14 closure-audit rounds and this package's determination | Search is closed for present purposes; checkpoint-600 is an accepted historical loss, as defined below. |

## 6. Formal checkpoint-600 historical-loss determination

**Determination:** the original seed-42 `gold_v1.2.2` checkpoint-600 weights are an accepted historical loss.

- The historical benchmark result and provenance references remain valid historical evidence.
- No recoverable copy of the original weights was found in the verified repository/release lineage.
- Same-step seed-17 and seed-73 checkpoints are not substitutes for seed 42.
- This determination does not erase the benchmark record and does not claim that available weights reproduce it.
- Production checkpoint-520 is a separate, resolved case: it was recovered through the app release/tag lineage.
- No recovery attempt, checkpoint mutation, model execution, or promotion is authorized by this determination.

## 7. Benchmark/export checkpoint safety register

On current DeepThoughts `main`, both `training/run_benchmark.py` and `training/export_onnx.py` still document and implement an implicit default of `checkpoints/thoughtorganizer-flan-t5/final`.

The current `training/checkpoints/thoughtorganizer-flan-t5/final/model.safetensors` SHA-256 is:

`b964c7e77703b6a64f2cf88f2d6d1a6d80b43f3bacdc58dd0e2af94d8d654d4a`

`training/hash_sweep_results.json` identifies the same hash as the rejected `gold_v1.2.3` seed-42/checkpoint-680 final/terminal model. It is neither production checkpoint-520 nor the lost checkpoint-600 candidate. A bare invocation can therefore silently select the wrong lineage.

This package records the risk only. Removing the defaults, requiring explicit paths, adding fail-closed tests, or changing documentation belongs to Milestone 3 and is not authorized here.

## 8. Proposed disposition of current untracked files

These are proposals for Johnny's decision. Nothing in this section authorizes add, move, delete, stage, commit, or push.

| File | Proposed disposition | Reason |
|---|---|---|
| `training/intent_recovery_data_model_discovery_plan_chatgpt.md` | Preserve. If later tracked, add a clear status note or companion index that splits Track A from Track B; do not delete as debris. | Track A's operational state is superseded by the committed discovery package and blocked A1 candidates. Track B's model-capability comparison remains valid but deliberately deferred because representation/compositional-transfer explanations are not exhausted. Track B is separate from the Gemini generator proposal. |
| `training/session_handoff_2026-08-11_rbr17_outcome_close.md` | Preserve as an accurate historical relay; tracking is optional and lower priority. | Useful provenance, but later committed outcome/postmortem records are authoritative. |
| `training/session_handoff_2026-08-12_rbr17_postmortem_close.md` | Preserve as an accurate historical relay; tracking is optional and lower priority. | Useful provenance, but later committed postmortem records are authoritative. |
| `training/session_handoff_2026-08-14_chatgpt_previous_work_closure.md` | Preserve until this package is independently verified and Johnny decides whether handoff history should be tracked; thereafter retain or deliberately archive, never silently delete. | It is the authority/navigation record for this closure sequence. |
| `training/session_handoff_2026-08-14_pending_authorizations.md` | Preserve pending a separate accuracy/disposition decision. | It may remain useful as an authority ledger, but this package does not infer its final archival status. |
| `training/previous_work_closure_package_2026-08-14.md` | Keep untracked while under Claude review. Consider tracking only after review convergence and fresh, explicit commit authorization. | This is the Milestone 1 deliverable, not self-authorizing repository history. |

## 9. Discovery-plan split disposition

### Track A: data-source discovery

Operational status is superseded by the committed bounded discovery package and the DialogSum/QMSum A1 evidence. Both current candidates remain blocked, neither is cleared for A2, and no access or rights-research follow-up is implied. Preserve the original plan as historical design context if retained.

### Track B: model-capability comparison

Still conceptually valid but deliberately deferred. The RBR17-C static audit did not establish that model capacity is the next justified variable; representation, objective, binding, and compositional-transfer explanations remain live. Track B must not be conflated with the proposed paid Gemini synthetic-candidate generator, which has a different role and authority model.

## 10. Unresolved implementation-safety register

| ID | Work item | Proposed milestone | Current gate |
|---|---|---|---|
| APP-1 | Version and fingerprint the actual single-pass/chunk prompt | Milestone 2: app prompt-safety proposal | Proposal not yet authorized |
| APP-2 | Version and fingerprint the long-input merge prompt | Milestone 2 | Proposal not yet authorized |
| APP-3 | Define and test the intended semantic relationship between the two live prompt paths | Milestone 2 | Proposal not yet authorized |
| APP-4 | Decide whether to reconcile or archive `reconcile-bullet-count-prompt`; verify the semantic interaction of its v1 contract/versioning work with both live prompt paths and the later v2 feasibility code, without silently changing production behavior | Milestone 2 | Proposal not yet authorized |
| APP-5 | Keep typed-marker v2 inactive unless separately evaluated and promoted | Separate promotion gate | No promotion authorized |
| TOOL-1 | Remove misleading implicit checkpoint defaults and require explicit checkpoint paths | Milestone 3: training-tool checkpoint-safety proposal | Proposal not yet authorized |
| TOOL-2 | Add fail-closed tests proving bare or ambiguous checkpoint selection stops before model load/export | Milestone 3 | Proposal not yet authorized |
| DATA-1 | Adjudicate comparator record 035 before any corpus correction | Separate corpus-governance decision | No correction authorized |
| ANN-1 | Resolve the four annotation-guide conventions before another pilot | Later generator/annotation readiness | Drafting and annotation not authorized |

## 11. Recommended gated sequence after closure review

1. Claude independently verifies this package against both repositories.
2. Johnny adjudicates any material disagreement and decides the untracked-file dispositions.
3. If desired, Johnny separately authorizes a design-only Milestone 2 app prompt-safety proposal.
4. If desired, Johnny separately authorizes a design-only Milestone 3 checkpoint-safety proposal.
5. Generator-readiness work remains paused until the closure sequence is decided; it then begins with annotation-guide conventions and a bounded design package, not API setup or candidate generation.

No prior authorization or commit wording carries forward between these steps.

## 12. Review checklist for Claude

Claude should independently verify, from primary files in both repositories:

- the two repository heads and app branch position;
- the exact live single-pass/chunk wording and separate merge prompt;
- absence of a live v1 version/fingerprint gate;
- inactive status of typed-marker v2;
- retirement of exact `source-determined-bullets-v1` as a deployment candidate;
- the checkpoint default paths, current model hash, and hash-to-lineage mapping;
- the supersession mappings;
- the Track A/Track B split and all authority boundaries.

Material disagreement stops closure and returns to Johnny. Agreement does not authorize staging, commit, push, implementation, compute, cleanup, or any later milestone.
