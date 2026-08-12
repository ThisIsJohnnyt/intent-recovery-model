# Model Release Notice

This file covers released model weights (`intent-recovery-model-*` GitHub
Releases) specifically. It is **not** a license, and nothing in this file is
an asserted, legally enforceable condition. See
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for what the released
files are actually made of, and [PDR-008](docs/decisions/PDR-008.md) for the
full reasoning behind this approach.

## Why this isn't a license

Whether trained model weights are copyrightable at all — and separately,
whether fine-tuned weights are a derivative of the base model or of the data
used to train it — is not a settled question. The U.S. Copyright Office's
May 2025 Part III report on AI and copyright discusses this directly: weights
that substantially memorize training data may themselves constitute
infringing copies of *someone else's* copyrighted work, independent of
whether the weights are original, copyrightable subject matter in their own
right. No blanket rule currently resolves either question.

Given that, asserting "these weights are licensed under [X]" would overstate
what this project can actually grant. Instead:

> To the extent ThisIsJohnnyt owns copyright or similar rights in
> project-created release material, those rights are made available under
> the terms below. No claim is made that the numerical model weights
> themselves are copyrightable or exclusively owned by ThisIsJohnnyt.

## Project request (not a license condition)

We ask — but do not represent as a legally enforceable license condition —
that anyone using these released weights:

1. **Acknowledge** the Intent Recovery Model project (this repository) as
   the creator of this implementation and its annotation/training framework.
2. **Use the weights noncommercially** — consistent with the rest of this
   project's licensing posture (see [PDR-006](docs/decisions/PDR-006.md) and
   [PDR-008](docs/decisions/PDR-008.md)).

This is a request about how we'd like the project treated, not a copyright
claim over ideas, methods, or the project name. Copyright doesn't protect
those regardless — if durable, enforceable name/brand protection ever
matters, that's a separate trademark question requiring its own review, not
something this file establishes.

## Third-party and provenance disclosure

- Model-weight copyright and derivative-work status varies by jurisdiction
  and remains legally unsettled generally, not specific to this project.
- The base model (`google/flan-t5-base`) and other upstream components
  retain their original terms (Apache 2.0) regardless of anything stated
  here — see `THIRD_PARTY_NOTICES.md`.
- This project makes no representation that it owns or can license
  third-party rights that may subsist in upstream components, or in any
  material a model output might reproduce.
- Training data provenance: fine-tuning used `datasets/gold/` — project-
  curated, hand-authored synthetic examples (see PDR-006 for its own
  license terms and the CC-BY-4.0 historical exception for early
  versions). This project's private validation/holdout notes
  (`datasets/real_validation.jsonl`, `datasets/real_holdout.jsonl`) were
  **not** used as training data and were never published — see
  [PDR-004](docs/decisions/PDR-004.md).
- No memorization or output-provenance audit has been performed on any
  released checkpoint. This is disclosed as a gap, not evidence of a
  specific problem — users remain responsible for evaluating their own use
  and any rights that may apply to particular outputs.
