# B1 — Model Panel Freeze Criteria

**Operationalizes:** `training/intent_recovery_data_model_discovery_plan_chatgpt.md` §4, "B1. Predeclared
model panel".

**Status: freeze checklist, blank.** No model has been downloaded, no execution environment provisioned, no
revision hash frozen. This is the checklist a future authorized freeze step would complete, for each of the
four predeclared candidates, **before** any inference is run — completing this document is itself the
"freeze," and nothing after it may change without triggering the pre-declared replacement rule below.

**Revised 2026-08-12** per Johnny's explicit disposition: B4's interpretation table (see B3) has a row —
"Untuned baseline succeeds where current fine-tuned checkpoint fails → Audit training-induced regression
before more training" — that the plan's original 3-model panel cannot test, since none of the three
declared models is the project's own actual trained checkpoint. Johnny chose to add a fourth panel arm
rather than drop the row, so that interpretation becomes testable.

## Predeclared panel (plan §4 B1, plus one added arm per Johnny's 2026-08-12 disposition)

1. **Baseline (untuned):** the project's own exact pinned `google/flan-t5-base` revision, evaluated in its
   pretrained-but-not-fine-tuned form (~0.2B parameters, Apache 2.0).
2. **Current fine-tuned checkpoint (added arm) — identity determined 2026-08-13.** Same base architecture
   as arm 1, with the project's own fine-tuning applied. This is the arm the B4 "training-induced
   regression" row actually needs; without it that row is uninterpretable, not just under-evidenced.

   **2026-08-13, ChatGPT's second review and Johnny's disposition:** the original "e.g. the most recent
   `gold_v1.2.x` release checkpoint at freeze time" wording was dangerously underspecified — `ROADMAP.md`
   alone could be stale, and Claude did not guess. Johnny delegated identifying the exact checkpoint to
   ChatGPT's determination, per the standing collaboration model.

   **ChatGPT's determination (2026-08-13, third review), independently verified by Claude before accepting
   it:** arm 2 is `checkpoint-520` / `gold_v1.2.1` — the actual currently-deployed production model —
   represented by the checksummed quantized ONNX encoder/decoder artifacts attached to GitHub Release
   `intent-recovery-model-v0.1.0` (tag `pre-repository-split`, commit `2cd31dd`). Claude confirmed this
   directly against `training/production_checkpoint_recovery_handoff.md` (this project's own prior, already
   -settled investigation into exactly this question) and against the actual repo: the tag
   `pre-repository-split` and commit `2cd31dd` both exist; that handoff document states plainly that
   `checkpoint-520`/`gold_v1.2.1` is what `training/ROADMAP.md` and `datasets/gold/CHANGELOG.md` both
   record as the currently-deployed model, that it is **not recoverable from any directory under
   `training/checkpoints/`**, and that it was resolved via that exact release/tag/commit — quantized ONNX,
   checksummed manifest, provenance confirmed (`google/flan-t5-base`, `gold-v1.0`..`v1.2.1`, 40 epochs)
   matching checkpoint-520 exactly.

   **Hard exclusions, independently confirmed, not just asserted:**
   - **Never `training/checkpoints/thoughtorganizer-flan-t5/final`.** Claude confirmed directly: this local
     directory is a misleading default (both `run_benchmark.py` and `export_onnx.py` default here when no
     path is given) that currently holds a **hash-verified rejected** `gold_v1.2.3` seed-42/checkpoint-680
     run — not production, and explicitly not recommended even as the standing candidate/comparison
     baseline (`gold_v1.2.3_lessons_learned.md`: "Do not prefer `checkpoint-680` over `checkpoint-600`").
   - **Never `checkpoint-600`** (the `gold_v1.2.2` candidate) — evaluated, never promoted past checkpoint-
     520, and itself not recoverable from any current local directory under an established identity.
   - **Never any RBR17-C treatment or comparator artifact** — both arms failed frozen gates 3–6 and neither
     was promoted; the settled postmortem is explicit that the 78-record comparator remains the reference
     lineage and the 85-record treatment must not silently become baseline.

   The freeze record below still stays otherwise blank (exact ONNX component hashes, precision, hardware
   fit, etc.) — identity is settled; the mechanical freeze paperwork is a later step, not authorization to
   download or execute anything now.
3. **Stronger class:** `Qwen/Qwen3-4B` (4.0B parameters, native 32,768-token context, Apache 2.0).
4. **Capability ceiling:** `Qwen/Qwen3-14B` (14B-class, Apache 2.0).

Arm 2 is evaluated on the same B2-frozen 36 examples under the same two conditions as the other three arms
(zero-example, fixed few-example) — it is not exempted from any B2/B3 rule by virtue of being the project's
own checkpoint. In particular, its outputs on the 36 examples must not be assumed from prior benchmark runs
on *different* examples; B3's paired comparison requires fresh, identically-conditioned outputs from all
four arms on the same frozen set.

## Per-model freeze record (complete one of these for each of the four, before any inference)

**Model:** _______________ **Exact revision/commit hash:** _______________ **Frozen by / date:**
_______________

| Item | Recorded value | Notes |
|---|---|---|
| Hardware fit (VRAM/compute available vs. required) | | |
| Quantization / precision used | | |
| Local vs. hosted execution, and privacy implication of that choice | | |
| Model license (exact identifier + link) | | |
| Dependency licenses (inference stack, tokenizer, etc.) | | |
| Context limit (tokens) | | |
| Reproducibility (deterministic decoding available? seed/settings that guarantee it?) | | |
| Fine-tuning suitability (in case a later milestone wants it, separate from this audit) | | |
| Known data-provenance / contamination disclosures from the model card | | |

## 14B replacement rule (predeclared, per plan §4 B1)

If the ceiling model cannot run under an approved reproducible, privacy-preserving setup, it must be
replaced **before seeing any output** — not after a disappointing or inconvenient result — using this same
written criteria set:

- open weights;
- instruction-tuned;
- at least **2×** the stronger candidate's parameter count (i.e. ≥8B, since the stronger candidate is
  4.0B);
- adequate context length for the frozen examples (see B2);
- disclosed license;
- feasible under an approved execution setup.

Record any replacement here, with the reason and the date, before that model's freeze record above is
filled in. The plan is explicit that this substitution must happen pre-output; a substitution made after
seeing any model's output on the frozen examples is a protocol violation, not a normal adjustment, and is
itself one of the work-stopping conditions in the privacy/stop-conditions checklist.

## Scope boundary, restated

The cross-family panel (FLAN-T5 baseline and fine-tuned checkpoint vs. Qwen3) measures **practical
capability**, not parameter scaling in isolation. Per plan §4 B1: "If causal attribution to size is later
important, propose a separately authorized same-family comparison; do not expand this first panel during
execution." This document freezes four models and four only — arms 1 and 2 are the same architecture by
design (that comparison is the entire point of the added arm, per Johnny's disposition above), and arms 3–4
are the cross-family stronger/ceiling comparison the plan originally specified. Adding a fifth arm mid-run,
or substituting a different family for arms 3–4, requires a new, separately authorized freeze, not an
amendment to this one.

## What remains gated

Nothing in this checklist authorizes downloading any of the four models, provisioning an execution
environment, or running inference. It is the record that gets filled in at the moment Johnny separately
authorizes that step (protocol step 7: "Johnny separately authorizes any acquisition, model execution, or
compute").
