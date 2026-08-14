# Training-tool checkpoint-safety design proposal

**Date:** 2026-08-14  
**Author:** ChatGPT  
**Status:** Independently verified by Claude with no disagreement; design accepted by Johnny; implementation proposal deferred  
**Milestone:** 3 — design only  

## 1. Decision summary

`run_benchmark.py` and `export_onnx.py` should have no implicit checkpoint selection. Both should require an explicit checkpoint directory and bind that directory to a machine-verifiable selection receipt before importing or loading model code.

The benchmark path should record what was evaluated without claiming the checkpoint is approved. The export path should be stricter: it should refuse to export unless the selection receipt identifies an explicit release candidate, contains complete provenance, and permits export. Neither receipt type substitutes for Johnny's authorization.

The existing `training/checkpoints/thoughtorganizer-flan-t5/final` directory must not be renamed, deleted, or repointed as part of this safety fix. It remains historical evidence for the rejected seed-42/checkpoint-680 lineage; removing the default is safer than assigning another mutable directory as the new default.

## 2. Authority boundary

Johnny authorized a design-only Milestone 3 on 2026-08-14. This document does not authorize:

- edits to benchmark, export, checkpoint, wrapper, test, or release code;
- checkpoint creation, deletion, copying, moving, renaming, mutation, or recovery attempts;
- model/tokenizer import or load, inference, benchmark execution, ONNX export, quantization, training, or evaluation;
- creation or publication of a model release;
- staging, commit, or push.

Independent review does not expand this authority. A selection receipt is provenance evidence, not execution, release, spending, or Git authorization.

## 3. Verified current state and hazard

At design time, DeepThoughts/model-repository `HEAD = main = origin/main = 8b8074bc52a092e78f1ba95c3e0768330bed596b`.

### `run_benchmark.py`

- Usage currently permits `python run_benchmark.py <benchmark.jsonl> [checkpoint_dir] [output.json] [--contract=v1|v2]`.
- `parse_args()` accepts one to three positional arguments.
- If the second positional argument is absent, line 184 selects `training/checkpoints/thoughtorganizer-flan-t5/final`.
- The script then imports Torch/Transformers and loads the tokenizer and model from that directory.
- Results do not carry a checkpoint fingerprint or selection-receipt identity.

### `export_onnx.py`

- Usage currently permits `python export_onnx.py [checkpoint_dir] [output_name]`.
- If no checkpoint is supplied, line 62 selects the same `.../final` directory.
- It checks only that the path exists before export begins.
- Its generated manifest contains human-replacement placeholders for release and contract identity.
- It imports model/export dependencies before any proposed identity preflight can occur.

### Actual default target

`training/checkpoints/thoughtorganizer-flan-t5/final/model.safetensors` has SHA-256:

`b964c7e77703b6a64f2cf88f2d6d1a6d80b43f3bacdc58dd0e2af94d8d654d4a`

`training/hash_sweep_results.json` maps this hash to both the final and step-680 weights of `gold_v1.2.3-seed42`, a rejected candidate. It is neither recovered production checkpoint-520 nor the accepted-historical-loss checkpoint-600 candidate.

The immediate safety defect is implicit selection. A secondary defect is that even an explicit path is not bound to a verified artifact identity, allowing directory reuse or mutation between planning and execution.

## 4. Safety principles

1. **No checkpoint default.** Absence is an error, never a fallback.
2. **Explicit path is necessary but insufficient.** Resolve and validate the artifact identity before model imports.
3. **Identity is content-based.** Directory names such as `final`, seed labels, and step numbers are descriptive, not proof.
4. **Weights and full artifact are distinct identities.** Record the weights-file hash and a canonical whole-directory fingerprint.
5. **Benchmarking is not promotion.** A benchmark receipt records what ran; it does not call the checkpoint approved.
6. **Export is release-sensitive.** Export requires stronger provenance and a declared release-candidate purpose.
7. **Existing controlled wrappers remain explicit.** Migration must update their safety metadata without changing checkpoint selection, training, or evaluation semantics.
8. **Preflight precedes expensive or mutating work.** CLI, receipt, path, content, and output checks finish before Torch, Transformers, Optimum, ONNX, or a checkpoint is loaded.
9. **No magic authorization field.** A JSON value such as `approved: true` cannot replace Johnny's direct authorization.

## 5. Canonical checkpoint identity

Reuse the established `real_data_private.checkpoint_fingerprint()` algorithm as the starting point because it recursively fingerprints checkpoint contents, rejects symlinks, and fails on an empty directory. A later implementation proposal must either use that function directly or extract it into a neutral module without changing its canonical algorithm.

Record both:

- `artifact_sha256`: canonical whole-directory fingerprint;
- `weights`: filename, byte size, and SHA-256 for the single supported weights artifact.

For the current repository, the supported weights policy should require exactly one `model.safetensors` and reject ambiguous simultaneous weight formats unless a later design explicitly supports them. The structural preflight should also require the tokenizer/config files needed by the consuming operation and record their hashes through the whole-directory fingerprint.

The root checkpoint path and every descendant must be checked for symlink/junction/reparse indirection to the extent supported by the platform. If the implementation cannot reliably validate a Windows junction/reparse point, it must fail closed or document and test a narrower allowed-root rule; it must not silently treat unresolved indirection as a normal directory.

## 6. Selection receipt

Both tools should require a canonical JSON receipt created in a separate no-model inspection step. Proposed schema: `checkpoint-selection-v1`.

Required common fields:

```json
{
  "schema": "checkpoint-selection-v1",
  "checkpoint_id": "human-readable-stable-id",
  "artifact_sha256": "64 lowercase hex",
  "weights": {
    "filename": "model.safetensors",
    "size_bytes": 0,
    "sha256": "64 lowercase hex"
  },
  "source_commit": {
    "status": "known",
    "value": "40 lowercase hex"
  },
  "training_lineage": {
    "dataset": {"status": "known", "value": "declared-lineage"},
    "seed": {"status": "known", "value": 0},
    "global_step": {"status": "known", "value": 0},
    "prompt_contract": {"status": "known", "value": "declared-identity"}
  },
  "purposes": ["benchmark"],
  "provenance_status": "complete | historical-partial",
  "notes": "non-authorizing human context"
}
```

Canonicalization must use UTF-8, sorted object keys, compact separators, preserved array order, and no trailing newline before SHA-256. The tool should compute and report `selection_receipt_sha256`; it must not trust a stored self-hash.

Rules:

- unknown fields fail unless the schema explicitly allows an extension namespace;
- duplicate JSON keys fail;
- missing, empty, wrong-type, unsafe, or malformed identifiers fail;
- every provenance item uses `status: known | unknown`; `known` requires a correctly typed nonempty value and `unknown` requires `value: null` plus a nonempty explanation in `notes`, rather than a magic sentinel string;
- `purposes` is an allowlist and must include the operation being attempted;
- `historical-partial` may permit an ordinary benchmark if the exact artifact identity is complete, but it must block export;
- the receipt must not store secrets, user data, protected benchmark text, or checkpoint bytes;
- path is supplied independently on the CLI so a receipt remains portable; content fingerprints bind it to the selected directory.

## 7. No-model inspection step

A later implementation proposal should specify a small inspection command that:

- takes an explicit checkpoint directory;
- validates directory structure and indirection;
- calculates artifact and weights identities without importing model libraries;
- prints a draft `checkpoint-selection-v1` receipt to standard output or an explicitly named new file;
- refuses to overwrite an existing receipt;
- never marks a checkpoint approved, promoted, production, or exportable by inference;
- requires the human or governing experiment wrapper to supply lineage and purpose fields;
- clearly labels incomplete provenance as `historical-partial`.

Creating a receipt does not authorize benchmarking or export. For controlled training workflows, the governing wrapper may generate the receipt after training and before evaluation, using the already frozen run metadata and newly computed artifact identity. The receipt must then be included in the wrapper's execution receipt and passed explicitly to `run_benchmark.py`.

## 8. Proposed CLI contracts

Exact flag names remain subject to implementation review, but positional ambiguity and implicit selection should end.

### Benchmark

```text
python run_benchmark.py BENCHMARK.jsonl \
  --checkpoint-dir CHECKPOINT_DIR \
  --checkpoint-selection CHECKPOINT_SELECTION.json \
  [--output OUTPUT.json] \
  [--contract=v1|v2]
```

Required preflight, in order:

1. strict CLI parse; checkpoint path and receipt are mandatory;
2. select and verify prompt-contract adapter;
3. strictly parse benchmark and selection receipt without opening protected content beyond the requested benchmark;
4. resolve checkpoint path and validate allowed structure/indirection;
5. recompute artifact and weights hashes and compare with the receipt;
6. require `benchmark` purpose;
7. refuse an existing output unless an explicit, separately designed overwrite policy is authorized;
8. write a pre-execution receipt or prepare it atomically;
9. only then import/load model libraries.

Per Johnny's accepted Decision 4, `--output` is mandatory and the tool must fail closed if either the requested result or its sibling execution receipt already exists.

### Export

```text
python export_onnx.py \
  --checkpoint-dir CHECKPOINT_DIR \
  --checkpoint-selection CHECKPOINT_SELECTION.json \
  --output-name OUTPUT_NAME
```

Required additional gates:

- `provenance_status` must be `complete`;
- `purposes` must include `export`;
- release name, prompt/inference contract, base-model revision, training datasets, and source commit must be non-placeholder values before a release-ready manifest can be produced;
- destination must not already exist or contain files;
- export must stage into a fresh temporary directory and publish atomically only after all required files, ONNX checks, quantization checks, and manifest hashes pass;
- the export manifest must embed the selection-receipt hash, source artifact fingerprint, and weights hash;
- no release upload is performed by this command.

An `export` purpose states intended use and enables the code path; it is not authorization to execute or release.

## 9. Benchmark provenance output

Keep the existing benchmark result JSON array stable for `report_benchmark.py`. Add a sibling receipt rather than silently changing the result schema:

`<output-stem>.execution-receipt.json`

Required fields:

- selection-receipt hash and full validated selection metadata;
- resolved checkpoint path for local audit, clearly marked machine-local;
- recomputed artifact and weights hashes;
- benchmark file fingerprint;
- contract adapter name/version/fingerprint;
- runner source fingerprint and repository commit;
- generation constants and device class;
- output file fingerprint after successful write;
- start/end timestamps and success/failure state without raw generated text duplication.

The result file remains the source for generated outputs and scoring. The execution receipt proves which inputs and code produced it.

## 10. Controlled-wrapper migration

Current controlled wrappers already pass explicit checkpoint paths. Do not change those paths or silently rerun historical work.

For future authorized runs, each wrapper should:

1. create or validate the post-training checkpoint selection receipt;
2. bind it to frozen run metadata and the wrapper's main receipt;
3. pass both required checkpoint flags to every benchmark invocation;
4. verify the benchmark execution receipt matches the intended treatment/control arm;
5. stop before evaluation if any path, artifact, weights, seed, step, contract, or source-commit value disagrees.

Historical command receipts remain historical evidence and should not be rewritten. Documentation may point to this new requirement as superseding the old CLI for future runs.

Migration inventory must include at least:

- `run_seed17_r2_replay.py`;
- `run_seed17_phase2_replay.py`;
- `run_seed17_contrastive_replay.py`;
- `run_seed17_regression_balanced_repair.py`;
- their tests, frozen-manifest templates, and future command examples;
- `docs/benchmarks/benchmark_suite.md`, `training/ROADMAP.md`, and other live usage documentation.

No archived receipt or outcome artifact should be mechanically edited.

## 11. Fail-closed no-model test matrix

The implementation test suite must prove failure occurs before model-library import or output mutation. Use temporary synthetic checkpoint directories and stub/fake dependencies only.

### CLI and default removal

- bare `run_benchmark.py` fails;
- benchmark-only invocation fails for missing checkpoint selection;
- checkpoint path without receipt fails;
- receipt without checkpoint path fails;
- bare `export_onnx.py` fails;
- unknown, duplicated, empty, or conflicting flags fail;
- extra positional arguments fail rather than being guessed.

### Receipt validation

- valid canonical receipt passes static validation;
- duplicate keys, unknown fields, missing fields, invalid types, unsafe IDs, invalid hashes, duplicate purposes, and placeholder values fail;
- receipt purpose mismatch fails;
- `historical-partial` benchmark policy behaves as declared and always blocks export;
- receipt canonical hash is stable across supported platforms.

### Artifact identity

- missing directory, file instead of directory, empty directory, missing weights, multiple weights, wrong weights filename, size mismatch, weights-hash mismatch, and whole-artifact mismatch fail;
- changing a config/tokenizer file while leaving weights unchanged fails the artifact check;
- changing weights while leaving directory name unchanged fails both relevant checks;
- symlinked files and resolvable directory indirection fail;
- the rejected `.../thoughtorganizer-flan-t5/final` path receives no special treatment: it may be used only when explicitly selected and correctly identified, never by omission.

### Import/order guarantees

- every preflight failure occurs before Torch/Transformers/Optimum/ONNX imports;
- benchmark output and execution-receipt paths remain absent on preflight failure;
- export destination remains absent on preflight failure;
- existing outputs/destinations are never overwritten by default.

### Positive static paths

- a synthetic valid benchmark selection reaches a fake loader with the exact resolved directory;
- a complete export selection reaches a fake exporter with the exact resolved directory;
- execution/export receipts contain the expected fingerprints and never contain checkpoint bytes, benchmark source content, or secrets;
- current v1/v2 contract-adapter behavior remains unchanged after CLI refactoring.

## 12. Rollout and rollback

### Implementation rollout

1. Start from freshly verified current `main` on a new scoped branch.
2. Land pure receipt/identity validation and dummy-only tests first.
3. Refactor both tools so heavy imports occur only after shared preflight.
4. Update future-facing wrappers and live documentation in the same reviewed change or a predeclared sequence that never leaves an authorized wrapper silently invoking the wrong CLI.
5. Run static/dummy tests only unless Johnny separately authorizes model execution.
6. Independently verify the implementation and migration inventory.
7. Commit/push requires fresh authorization.

Rollback should restore the prior code and usage documentation together. It must not restore permission to use implicit defaults in a partially migrated wrapper. If rollback is necessary before wrappers can be reverted safely, stop future execution instead of creating a compatibility shim that silently selects a model.

## 13. Explicit non-goals

- Do not choose a new production or candidate checkpoint.
- Do not recover or recreate checkpoint-600.
- Do not repoint `final` to checkpoint-520 or any other artifact.
- Do not delete the rejected checkpoint-680 evidence.
- Do not promote seed 17, seed 73, the 78-record comparator, or any treatment.
- Do not change prompt-contract selection or scoring semantics.
- Do not run benchmarks merely to test the new CLI.
- Do not upload or deploy an ONNX export.

## 14. Acceptance gates for a later implementation proposal

Before implementation can be authorized, a separate proposal must provide:

1. exact file-level scope;
2. final `checkpoint-selection-v1` JSON schema and canonicalization algorithm;
3. a decision on shared-module placement without creating import cycles or forcing heavy dependencies into no-model tests;
4. exact CLI grammar and exit behavior for both tools;
5. exact required checkpoint file policy;
6. Windows indirection handling and tested limitations;
7. benchmark execution-receipt and export-manifest schemas;
8. controlled-wrapper migration diff inventory;
9. output collision and atomic-write rules;
10. the complete dummy-only test list with expected outcomes;
11. proof that planned tests do not import or load a model;
12. explicit boundaries excluding execution, export, checkpoint mutation, release, deployment, staging, commit, and push.

## 15. Decisions requested from Johnny after independent review

Johnny decided each item directly and sequentially on 2026-08-14:

1. **Accepted:** remove both implicit checkpoint defaults; no replacement default.
2. **Accepted:** require content-bound selection receipts for benchmark and export.
3. **Accepted:** require `provenance_status: complete` plus explicit `export` purpose for export eligibility, without treating eligibility as execution or release authorization.
4. **Accepted:** require an explicit benchmark output path and fail closed on an existing result or sibling receipt; no derived output default.
5. **Deferred:** do not begin the dummy-only implementation proposal until the remaining documentation loops are closed. It will require fresh authorization.

These decisions accept the design only. They do not authorize implementation, model execution, export, checkpoint operations, release, deployment, staging, commit, or push.

## 16. Claude independent-review checklist

Claude should verify from primary files:

- current repository hash, CLI grammar, default-selection lines, import order, and output behavior of both tools;
- current default model weights hash and lineage mapping;
- exact behavior and portability of `checkpoint_fingerprint()`;
- all live direct callers, controlled wrappers, tests, and documentation requiring migration;
- compatibility of a sibling execution receipt with `report_benchmark.py`'s current result-array contract;
- feasibility of strict receipt parsing/canonicalization and Windows indirection checks;
- whether benchmark and export need different provenance gates;
- whether any proposed field overclaims authorization or historical knowledge;
- whether the rollout can be tested without model imports or checkpoint mutation.

Material disagreement stops this milestone and returns to Johnny. Agreement does not authorize implementation, model execution, export, checkpoint operations, release, deployment, staging, commit, or push.
