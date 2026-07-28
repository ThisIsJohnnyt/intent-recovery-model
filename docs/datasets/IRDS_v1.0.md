# Intent Recovery Dataset Specification (IRDS) — not yet written

This file is a placeholder. The full Intent Recovery Dataset Specification
— a versioned, RFC-style spec separating hidden generation data (metadata,
cognitive/emotional context, thought graph) from the input/output pairs a
model actually trains on — is a **v2/v3 effort**, deliberately deferred
until the current, simpler pipeline (v1: real dataset + fine-tune, v1.5:
richer output schema) is proven. See
[`training/ROADMAP.md`](../../training/ROADMAP.md)'s "v2/v3" section for the
current thinking on what this will eventually cover.

Writing a formal spec ahead of the architecture it's meant to describe risks
committing to details that don't survive contact with v1.5's real results.
This file exists so the intended eventual location is clear, not to
pre-declare a spec that doesn't exist yet.

Today's actual dataset format is documented in
[`training/DATASET_SPEC.md`](../../training/DATASET_SPEC.md).
