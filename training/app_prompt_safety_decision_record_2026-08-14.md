# App prompt-safety decision record

**Date:** 2026-08-14  
**Author:** ChatGPT  
**Status:** PR-state correction independently verified by Claude; no branch-disposition action remains
**Governing design:** `training/app_prompt_safety_design_proposal_chatgpt.md` at commit `8b8074bc52a092e78f1ba95c3e0768330bed596b`  

## 1. Purpose and boundary

This record resolves the four decisions requested in Section 12 of the independently verified Milestone 2 app prompt-safety design.

Johnny decided each item directly and sequentially on 2026-08-14. These decisions accept sequencing and disposition only. They do not authorize app edits, branch or pull-request operations, model execution, evaluation, deployment, Phase A/B implementation planning, implementation, staging, commit, or push.

## 2. Decision 1 — two-stage safety rule

**Accepted.**

Phase A/B will establish byte-preserving observability before any semantic reconciliation:

- extract and separately identify/fingerprint P1 single-pass, P2 chunk-first/context, and P3 merge renderers;
- preserve the exact bytes currently sent to the model;
- centralize the duplicated `6000` threshold without changing routing behavior;
- add build-time drift checks and exact model/prompt compatibility records;
- use static fixtures and fake model streams only unless model execution is separately authorized.

Phase C remains a later semantic-reconciliation phase. Extraction, versioning, or fingerprinting must not conceal a prompt rewrite or changed product behavior.

## 3. Decision 2 — reconciliation branch disposition already satisfied

**Accepted as a disposition; later verification established that no repository action remained.**

GitHub API verification on 2026-08-14 established that thought-organizer-app PR #4, `Prompt contract v1: source-determined bullets`, had already been closed without merge on 2026-08-03. Its `reconcile-bullet-count-prompt` branch remains intact at `cf76cd9f1fdd53bdc322e0e8084df679d09a78c4`, preserving the requested history. The app repository had no open pull requests at verification time. The linked model-repository PR #13 was merged on 2026-08-02.

The accepted disposition therefore matched an already-satisfied real-world state; nothing needed to be closed, merged, deleted, commented on, or otherwise changed.

Reasons:

- its unique activation is exact `source-determined-bullets-v1`, retired as a deployment candidate;
- its fingerprint covers the retired single-pass rendering, not the complete P1/P2/P3 live-path inventory;
- it predates the later v2 feasibility package;
- its pure-builder and build-time-fingerprint pattern remains useful design evidence;
- a future Phase A/B implementation should start fresh from verified current app `main`, not mechanically merge or cherry-pick the retired constants/hash.

A proper three-way merge would retain v2 files; possible v2 deletion is not the reason for closure.

Future merging, reopening, commenting, branch deletion, or other repository-state changes remain outside this record.

## 4. Decision 3 — Phase A/B implementation proposal

**Deferred until remaining documentation loops close.**

No exact app-code implementation proposal should begin yet. A later fresh authorization would scope a no-model proposal containing exact files, golden strings/hashes, manifest schemas, compatibility migration, route/fake-model tests, privacy controls, and rollout/rollback evidence.

Independent review must precede any app edit. Implementation, Git publication, pull-request creation, and deployment remain later distinct steps.

## 5. Decision 4 — Phase C gate

**Kept separately gated.**

Phase C includes product-semantic decisions such as:

- long-input bullet ceiling and retention policy;
- merge grounding, no-invention, uncertainty, attribution, and action-state rules;
- previous-output context propagation;
- whether intermediate P2 outputs remain user-visible;
- prompt/checkpoint compatibility;
- rollout, rollback, and activation gates.

Phase C must not be bundled with byte-preserving Phase A/B work. It requires a separate design step, independent review of exact semantic rules and fixtures, separate authorization before model evaluation/compute, and explicit rollout authorization before production activation.

## 6. Current result

Milestone 2's design decisions are resolved, and its branch-disposition item is closed as already satisfied. Remaining work is deliberately not started:

1. after documentation closure, consider a separately authorized Phase A/B implementation proposal;
2. keep Phase C dormant until separately designed and authorized.

No prior instruction or this decision record substitutes for the later action-specific authorization or the commit/push protocol.
