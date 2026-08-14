# App prompt-safety design proposal

**Date:** 2026-08-14  
**Author:** ChatGPT  
**Status:** Independently verified by Claude with no disagreement; pending Johnny's decisions  
**Milestone:** 2 — design only  

## 1. Decision summary

The app should not begin by replacing either live prompt. The safe first implementation would make the current behavior explicit, byte-locked, path-aware, and compatible with a specific installed model release without changing the rendered bytes sent to the model.

After that observability-only foundation is verified, a separately reviewed semantic-reconciliation proposal can decide whether the single/chunk and merge paths should change. Any semantic prompt change must be evaluated as a coordinated app-and-model compatibility change, not bundled into extraction, versioning, branch cleanup, or deployment plumbing.

Recommended branch disposition: close the existing `reconcile-bullet-count-prompt` work as superseded without merging it, while retaining its commit history as evidence. Its exact `source-determined-bullets-v1` activation is retired. Its extraction/fingerprint pattern may inform a fresh implementation from current app `main`, but no code should be cherry-picked mechanically because its constants and golden hash encode the retired contract and it predates both the current v2 feasibility package and the discovered merge path.

## 2. Authority boundary

Johnny authorized a design-only Milestone 2 on 2026-08-14. This document does not authorize:

- edits in `thought-organizer-app`;
- merging, closing, deleting, or archiving a branch or pull request;
- prompt activation or production-semantic changes;
- model execution, evaluation, export, training, deployment, or release changes;
- implementation, staging, commit, or push in either repository.

Review agreement does not expand that authority. Each later step requires a fresh, directly scoped instruction from Johnny.

## 3. Verified current state

At design time:

- DeepThoughts/model repo: `main = origin/main = 64e797f039dfc75637149cf3e21c445dcb21072e`.
- App repo: clean `main = origin/main = 7710a00975128c2c538584751fe21528a0a6e381`.
- App reconciliation branch: local and remote `cf76cd9f1fdd53bdc322e0e8084df679d09a78c4`; merge base with app `main` is `41cbb4f6195ac16a154e2217e6974cd9072d8dfe`.
- The production organizer loads the local `thoughtorganizer-flan-t5` bundle and does not select a prompt contract dynamically.
- `scripts/fetch-model.mjs` checks checksums and rejects a declared inference-contract major version other than `1`, but it does not verify an exact prompt-set identity. A missing `contract_version` is currently accepted.
- The app build runs TypeScript and Vite only; no live-prompt fingerprint gate is in the build.
- Typed-marker `source-determined-items-v2-candidate` exists on app `main` as inactive feasibility code and is not imported by the live organizer path.

## 4. Current prompt-path inventory

### P1 — single-pass final path

Condition: `estimateTokens(rawInput) <= 6000`.

Renderer: the inlined `SYSTEM_PROMPT`, raw-input wrapper, and `USER_PROMPT_TEMPLATE` assembled at `src/services/noteOrganizer.ts:65`.

Current bullet rule:

`one bullet per source-supported key idea; use as many as the note supports, up to seven; do not duplicate or invent content to reach a minimum`

This path produces the user-visible final result directly.

### P2 — multi-chunk intermediate path

Condition: `estimateTokens(rawInput) > 6000`.

Each chunk uses the same system and user template as P1, but a distinct wrapper:

- the raw-input label includes `Section i/n`;
- chunks after the first receive a generated context prefix containing the first 100 characters of the previous model output plus `...`.

P2 is therefore not byte-identical to P1 and has a second subvariant for later chunks. Its outputs are intermediate inputs to P3, although they are also yielded incrementally by the current generator.

### P3 — multi-chunk merge/final path

After all P2 calls, the app builds a separately inlined merge prompt from the model-generated chunk outputs. P3:

- uses the same three section markers;
- requests consolidated bullets and actions with duplicates removed;
- does not state the seven-bullet ceiling;
- does not carry several no-invention, source-support, tone, attribution, or uncertainty-preservation requirements from P1/P2;
- has no version or fingerprint;
- sees processed chunk outputs, not the original raw input.

P3 produces the definitive long-input result. Production semantics are consequently path-dependent.

### V2 — inactive feasibility path

`src/services/promptContractV2Candidate.ts` and its parser/parity tests define typed bullet/action markers. They are not wired into P1, P2, or P3. V2 must remain inactive unless a later promotion gate is explicitly authorized and passed.

## 5. Contract model: separate four concepts

One overloaded `contract_version` cannot safely represent all relevant compatibility dimensions. A later implementation should distinguish:

1. **Output schema:** the structural parser contract (`###NARRATIVE###`, `###BULLETS###`, `###ACTIONS###`; typed item markers only if separately promoted).
2. **Semantic policy:** grounding, retention, uncertainty, attribution, bullet ceiling, deduplication, and action-state rules.
3. **Prompt renderer:** exact bytes for a particular path and fixture family.
4. **Model compatibility:** the reviewed pairing between a model-release fingerprint and a complete set of renderer/policy identities.

Provisional names in this proposal are descriptive placeholders, not authorized production constants:

- prompt set: `current-production-observed-prompt-set`;
- renderers: `single`, `chunk-first`, `chunk-context`, `merge`;
- compatibility state: `observed-production-pairing`, not `validated-compatible`.

The current production pairing may be recorded as observed without claiming that it passed a compatibility evaluation that never occurred.

## 6. Proposed implementation sequence

### Phase A — byte-preserving extraction and route observability

Goal: make current behavior inspectable without changing model input bytes or route selection.

A later implementation proposal should:

- extract P1/P2 and P3 builders from `noteOrganizer.ts` into a live-contract module owned by the app;
- centralize the `6000` threshold so the organizer and chunking utility cannot drift;
- expose a pure route selector and pure builders for P1, P2-first, P2-context, and P3;
- assign distinct renderer identities and one prompt-set identity;
- retain the exact current strings, whitespace, wrapper order, 100-character context truncation, ellipsis, section numbering, and merge serialization;
- emit or make inspectable the selected path and prompt-set identity without logging raw user text or model output;
- leave v2 imports and runtime wiring unchanged (inactive).

Hard gate: for frozen fixtures, old and extracted builders must render byte-for-byte identical UTF-8 text. The implementation must stop if parity cannot be established; “semantically equivalent” is not sufficient.

### Phase B — build-time fingerprints and compatibility record

Goal: prevent silent drift and prevent an unreviewed model/prompt pairing.

A later implementation proposal should define:

- one SHA-256 per frozen renderer fixture;
- a canonical prompt-set manifest containing renderer IDs, hashes, output-schema ID, semantic-policy ID, threshold, context-window rule, and merge serialization rule;
- a canonical SHA-256 of that manifest;
- build-time verification that actual renders match the pinned hashes;
- an app-owned compatibility record binding the installed model release fingerprint to the prompt-set manifest hash;
- a fail-closed rule for unknown or absent exact prompt compatibility after a migration path for the currently installed production release is established.

The existing inference-contract major-version check remains useful for broad schema compatibility but is not a substitute for exact prompt-set compatibility. The compatibility design must not rewrite an upstream release manifest after publication or infer exact prompt compatibility solely from `contract_version: 1...`.

Recommended migration: pin the current production release and checksummed model manifest to the observed prompt-set hash in a reviewed app-side compatibility table. Label it `observed-production-pairing`. Future model releases should declare or be accompanied by an exact prompt-set hash and an explicit review state.

### Phase C — semantic reconciliation, separately reviewed

Only after Phases A/B establish trustworthy observation should a proposal change semantics. That proposal must answer, explicitly:

- Does the seven-bullet ceiling apply to the final output of long inputs, and if so, what is the approved retention policy when more than seven source-supported ideas exist?
- Are intermediate P2 outputs required to obey the user-facing ceiling, or should they optimize lossless coverage for P3?
- Which grounding, no-invention, uncertainty, attribution, and action-state invariants must P3 preserve when its immediate source is model output rather than raw input?
- Is the previous-output context prefix allowed to influence the next chunk as if it were source text? How are hallucinations or unresolved ambiguity in that prefix prevented from propagating?
- Should intermediate P2 results continue to be yielded to the UI, or should only P3 be user-visible for long inputs?
- Can the deployed checkpoint satisfy the reconciled prompts, or does any semantic change require a separately evaluated checkpoint?

No answer should be smuggled into a refactor. A semantic change requires explicit acceptance fixtures, compatibility evaluation, rollout approval, and—if model behavior is tested—separate compute authorization.

## 7. Frozen no-model test design

All tests in this section are static or use fakes. They must not load the organizer model.

### 7.1 Golden render fixtures

At minimum, freeze:

1. P1 with the existing ASCII contract fixture.
2. P1 with marker-like literal source text, Unicode, CRLF input, and trailing whitespace to define whether raw bytes are preserved.
3. P2 first chunk with fixed `i/n` values.
4. P2 later chunk with a previous output shorter than 100 characters.
5. P2 later chunk with exactly 100 and more than 100 characters, locking truncation and ellipsis behavior.
6. P3 with two fixed chunk outputs, locking `SECTION`, separator, marker, whitespace, and ordering bytes.

Each fixture must assert the entire rendered string and SHA-256. Hash assertions without readable golden text are insufficient for review; readable text without hashes is insufficient for drift detection.

### 7.2 Routing boundary fixtures

Freeze route behavior at estimated token counts 5999, 6000, and 6001. Include newline-heavy and single-line inputs because the estimator and chunker use related but not identical accounting. Assert:

- selected path;
- number and order of chunks;
- no empty chunk;
- exact chunk text;
- stable behavior for a single line that requires forced character splitting.

### 7.3 Orchestration tests with a fake model stream

Inject a fake deterministic stream to prove:

- P1 calls exactly one renderer/model pass;
- the long path calls P2 once per chunk and P3 once;
- P3 receives all P2 outputs in order;
- later P2 context derives from the immediately preceding output exactly as specified;
- path/contract telemetry contains identifiers only, never raw input or output;
- errors fail closed without silently falling back to another prompt path.

### 7.4 Parser and structural checks

Preserve current v1 parsing behavior byte-for-byte during Phases A/B. Add path-independent fixtures for missing, duplicate, and reordered section markers, empty narrative, empty bullet/action sections, and marker-like text. Any parser semantic change belongs to a separate proposal.

### 7.5 Build and compatibility checks

The build must fail before bundling when:

- a live prompt byte changes without a renderer ID/hash update;
- a renderer changes without the prompt-set manifest changing;
- a prompt-set manifest names a missing renderer fixture;
- the installed/release model identity has no accepted compatibility record after migration;
- v2 candidate code becomes reachable from the live organizer without a separately authorized promotion record.

## 8. Branch disposition

### Recommendation

After Johnny separately authorizes the repository action, close the reconciliation pull request/branch as superseded without merging and preserve its history.

Reasons:

- its unique contract activation is exact `source-determined-bullets-v1`, which the seed-17 postmortem retired as a deployment candidate;
- its fingerprint is correct only for that retired rendered prompt;
- it knows only the single-pass builder and does not inventory/fingerprint P2/P3 as distinct live paths;
- it predates v2 feasibility work;
- a fresh implementation from current `main` can reuse the architectural lesson—pure builders plus build-time drift checks—without reviving obsolete semantics.

A proper three-way merge would not delete v2 files; deletion is not the reason for this recommendation. No branch close, delete, merge, or cherry-pick is authorized by this document.

## 9. Rollout and rollback design

### Observability-only release (Phases A/B)

Required evidence before deployment authorization:

- byte parity for every live renderer fixture;
- unchanged route selection and chunk serialization fixtures;
- no model load in the verification suite;
- exact app commit, prompt-set manifest hash, installed model release, and model manifest fingerprint recorded together;
- a clean production build;
- an explicit statement that the change adds identity/drift protection but intentionally does not claim improved model behavior.

Rollback unit: the app bundle, prompt-set manifest, compatibility record, and model release must be treated as one recorded pairing. Rollback should restore the last recorded pairing, not independently roll back only the prompt or only the model.

### Later semantic release (Phase C)

Required evidence before deployment authorization:

- approved semantic policy and exact prompt renderers;
- static structural gates;
- separately authorized model compatibility evaluation with declared numeric and semantic gates;
- no regression on the short-input path;
- dedicated long-input fixtures covering retention, invention, uncertainty, attribution, deduplication, and action state;
- a predeclared rollback trigger and the exact prior pairing to restore.

Do not use a silent runtime fallback from a new prompt to an old prompt after model load. A compatibility failure should stop before user input is processed and surface a non-sensitive diagnostic.

## 10. Security and privacy constraints

- Never log raw notes, rendered prompts, chunk outputs, merge inputs, or model outputs for contract telemetry.
- Fingerprints must be computed from frozen synthetic fixtures or canonical manifests, not user content.
- Marker-like source fixtures must be synthetic and contain no protected benchmark/corpus text.
- Compatibility diagnostics may include renderer ID, prompt-set hash, app commit, model release, and model manifest hash only.
- A test failure must not dump a real user's rendered prompt.

## 11. Acceptance gates for a later implementation proposal

An implementation proposal is ready for Johnny's decision only if it provides:

1. exact file-level change scope from current app `main`;
2. old-versus-new rendered bytes and hashes for every P1/P2/P3 golden fixture;
3. a named prompt-set manifest schema and canonicalization algorithm;
4. an exact model/prompt compatibility-record schema and migration for the current production release;
5. static/fake test cases with expected outcomes;
6. evidence that v2 remains unreachable;
7. branch/PR disposition steps kept separate from code implementation;
8. rollout and rollback manifests;
9. an explicit stop if any supposedly byte-preserving fixture differs;
10. explicit boundaries excluding model execution, deployment, commit, and push unless separately authorized.

## 12. Decisions requested from Johnny after independent review

1. Accept or reject the two-stage rule: byte-preserving observability first, semantic reconciliation later.
2. Accept or reject closing `reconcile-bullet-count-prompt` as superseded while preserving history.
3. If accepted, decide whether to authorize a separately scoped, no-model implementation proposal for Phases A/B.
4. Keep Phase C semantic decisions and any model compatibility evaluation separately gated.

## 13. Claude independent-review checklist

Claude should verify from primary app/model repository files:

- all repository and branch hashes;
- P1/P2/P3 routing, exact wrappers, threshold, context truncation, and merge serialization;
- current build scripts, model loader, release installer, and inference-contract check;
- absence of exact live prompt-set verification;
- v2 runtime inactivity;
- exact contents and merge-relevant delta of `reconcile-bullet-count-prompt`;
- accuracy of the retired-v1 conclusion;
- whether the proposed compatibility separation and no-model gates are sufficient and implementable;
- whether any recommendation would silently change current production bytes or semantics.

Material disagreement stops this milestone and returns to Johnny. Agreement does not authorize implementation, branch operations, model execution, deployment, staging, commit, or push.
