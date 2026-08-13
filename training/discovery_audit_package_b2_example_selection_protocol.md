# B2 — Frozen Example Selection Protocol

**Operationalizes:** `training/intent_recovery_data_model_discovery_plan_chatgpt.md` §4, "B2. Frozen
examples and conditions".

**Status: protocol only.** No examples have been selected, authored, or frozen. Authoring the 36 examples
this protocol describes is itself a form of corpus creation and is out of scope for this package — this
document specifies how that later, separately authorized step must be carried out, not the examples
themselves.

**Revised 2026-08-12** per ChatGPT's independent review: the first version said the 36 examples are "never
placed in any prompt," which is actually self-contradictory — B3 requires running each example *as the
evaluation input* through every model/condition, which means it necessarily appears in that inference
call's prompt. What the plan (and this protocol) actually mean is narrower: none of the 36 may be reused as
a **few-shot demonstration**, and none may leak into any model's **training data** — clarified explicitly
below. The first version also gave category counts with no actual reproducible selection procedure; fixed
below too.

## Composition (fixed by the plan, not re-derived here)

**36 private, independently selected examples**, each used only as a scored evaluation input, never reused
as a few-shot demonstration and never present in any model's training data:

- 12 protected-style semantic cases
- 12 acceptance-style structural/task-survival cases
- 12 newly hand-authored adversarial interaction cases

"Private" means these must be genuinely new — not the actual protected-16 or acceptance-benchmark records
themselves (using those directly would make this a re-run of an existing benchmark, not an independent
capability probe, and would also violate the no-evaluation-overlap requirement below).

## Reproducible selection method (added 2026-08-12, tightened 2026-08-13 across two same-day reviews)

Johnny's 2026-08-13 disposition confirmed: **all 36 examples are newly authored** (not drawn from an
existing eligible universe) — the composition below is unchanged.

**Third-review correction (2026-08-13, same day):** the prior version of this section said the seeded draw
picks 12 from "whichever candidates clear the mechanism-coverage quota" — but coverage (≥8 of 11 subtypes,
≤3 repeats) is a property of the *drawn 12-set as a whole*, not of any individual candidate, so no
candidate can "clear" it alone, and nothing specified what happens when a straightforward draw doesn't
happen to satisfy it. Fixed below with an actual constrained-selection algorithm: deterministic retry with
a fixed cap, and an explicit stop when no valid subset exists — not silent relaxation of the quota and not
an infinite/unbounded search.

1. **Oversubscribe before drawing, for every one of the three 12-example categories.** At least two
   independent authors each draft an **equal-sized** candidate set larger than the 12 needed — e.g. 2
   authors × 9 candidates each = 18 candidates competing for 12 slots.
2. **Canonical, stable ordering.** Every candidate gets a stable ID at authoring time
   (`<category>-<author-initial>-<sequence>`, e.g. `protected-jd-03`), sorted lexicographically by that ID
   before anything else runs — mirroring A2's `record_id` sort — so every later step is reproducible
   independent of authoring or file order.
3. **Predeclared subtype tag(s) per candidate, fixed at authoring time.** Every protected-style and
   acceptance-style candidate is tagged by its author with the one or more A3 priority-mechanism subtypes
   (the corrected set — A3's 2026-08-13 revision) it targets. Every adversarial candidate is tagged with
   exactly one **specific, named pair** of subtypes meeting A3's corrected interacting-mechanism dependency
   test — declared *before* the reviewer sees the candidate, not inferred after the fact. This tagging is
   what makes the quota in step 5 mechanically checkable rather than a judgment call made during selection.
4. **Collision screen every oversubscribed candidate first**, before the constrained draw, with
   `screen_collisions()` (`training/discovery_audit_package_a2_sample_selection_script.py`) against the
   protected/acceptance benchmark pool and against every other candidate in the same oversubscribed pool.
   Fatal collisions are removed from the candidate pool entirely (not replaced automatically — see step 6);
   non-fatal flags are recorded for adjudication. Only candidates that survive this screen are eligible for
   the draw in step 5, so the draw never has to discover a collision after already satisfying the quota.
5. **Mechanism-coverage quota (a property of the selected 12, not of any one candidate).** For the 12
   protected-style and 12 acceptance-style categories: the *union* of the selected 12 candidates' tagged
   subtypes (step 3) must cover at least **8 of A3's 11 priority-mechanism subtypes**, and no single subtype
   may be tagged by more than 3 of the 12. For the 12 adversarial cases: the 12 selected pairings must cover
   at least **6 distinct subtype-pairs** (out of the 12 — allows some repeated pairings, but not all 12
   targeting the same one).
6. **Deterministic constrained-selection algorithm.** From the canonically-ordered, collision-cleared
   candidate pool (steps 2 and 4):
   - `attempt = 0`
   - Loop: draw a candidate 12-subset using `random.Random(AUDIT_SEED + attempt)` (the same seed constant
     A2 uses, offset by the attempt number) applied to the canonically-ordered pool.
   - Check the drawn 12 against step 5's quota.
   - If it satisfies the quota: **accept, stop** — this is the selected 12 for that category.
   - If not: `attempt += 1`. Repeat, up to a fixed cap of **500 attempts**.
   - If no attempt within the cap satisfies the quota: **stop — this is evidence the candidate pool itself
     may not contain a valid 12-subset**, not an unlucky draw to keep retrying past the cap. Return to the
     insufficient-candidate procedure in step 7 rather than relaxing the quota to force an accept.
7. **Insufficient-candidate stop/top-up.** Triggered either by fewer than 12 collision-cleared candidates
   existing in a category, or by step 6 exhausting its 500-attempt cap with no qualifying subset. Authors
   draft additional candidates specifically targeting the missing subtypes or pairings — not generically
   "more of the same" — under the same author/selector-independence rule (step 8), then steps 4–6 repeat
   against the enlarged pool. If two such top-up rounds still don't produce a qualifying 12-set, this stops
   and returns to Johnny rather than relaxing the quota to fit what exists.
8. **Selector independence.** Whoever authors a candidate example does not also serve as the final selector
   for that category, mirroring A3's two-reviewer-plus-adjudicator structure. The selector's role is
   running steps 4–6 mechanically, not hand-picking beyond what those steps produce.
9. **Few-shot demonstrations: exactly 4, selected by the identical algorithm (steps 1–6) at N=4** instead
   of 12, with a quota of **at least 2 distinct A3 priority-mechanism subtypes** covered among the 4 (steps
   5–6 scale down accordingly — same deterministic-retry structure, smaller target and quota). Used only in
   the fixed few-example condition, never as evaluation inputs; fixed at 4 because that's small enough to
   fit every B1 model's context window alongside the longest B2 example while still constituting genuine
   few-shot conditioning; authored fresh under the same rules as the 36 (never reused from any existing
   benchmark); collision-screened (step 4) against both the benchmarks and the 36 frozen evaluation
   examples specifically — this is the concrete mechanism behind the "no evaluation overlap" requirement
   below, not just an assertion of it.

## What must be frozen before any inference runs

For every one of the 36 examples:

- a stable ID and a content hash (so later claims of "we didn't touch these" are checkable, not just
  asserted — consistent with this project's general practice of hashing frozen artifacts, e.g. the
  `_frozen_fingerprints.json` files already used elsewhere in `training/`);
- the selection rationale (why this example belongs in its category);
- the reference annotation (what a correct recovery looks like, in this project's own output contract —
  see `training/DATASET_SPEC.md`);
- scorer instructions (see B3);
- the exact model revision each of the four B1-frozen models will be evaluated at;
- the chat template / prompt wrapper used per model family;
- maximum input/output length settings;
- precision/quantization settings;
- software/library versions (inference stack, tokenizer version).

None of this may change after any model's output has been seen. A change discovered to be necessary after
seeing output is a stop condition (see the privacy/stop-conditions checklist), not a silent correction.

## Two conditions, both required, for every one of the four B1-frozen models

1. **Zero-example:** the identical contract, no demonstrations.
2. **Fixed few-example:** the identical, independently selected demonstrations, with **no evaluation
   overlap** — the few-shot demonstrations must not be drawn from the 36 frozen examples themselves, nor
   from the project's protected/acceptance benchmark files, nor from each other's targets.

## Cross-family control

Model families tokenize and format prompts differently. Per the plan: semantic instructions and
demonstrations stay **byte-identical** across all four models (arms 1 and 2 share a family already, so the disclosed
wrapper difference is really only between the FLAN-T5 pair and the Qwen3 pair); only the documented wrapper/chat template
may differ per family. Record every such wrapper difference explicitly as a controlled implementation
detail in the freeze manifest — the point is that a difference exists and is disclosed, not that it is
eliminated (it cannot be, across genuinely different model families).

## Inference-condition rules

- **Deterministic decoding** where supported: `temperature=0` / greedy, single output per example per
  condition per model. No sampling, no best-of-N.
- **Disable Qwen's thinking/reasoning output** and score only the requested contract output — a model
  should not get credit (or blame) for reasoning tokens outside the actual deliverable.
- **No truncation:** every one of the 36 examples must fit every one of the four models' context window
  without truncation. If one doesn't fit, that is a separate finding about long-context capability, not a
  silently-truncated data point folded into the main result.
- **No post-hoc tuning:** prompts, demonstrations, parsers, and decoding settings are frozen before
  inference and may not be adjusted after viewing any result.

## Freeze manifest schema

```json
{
  "frozen_at": "<timestamp>",
  "frozen_by": "<who>",
  "examples": [
    {
      "id": "b2-protected-01",
      "category": "protected_semantic",
      "content_sha256": "...",
      "selection_rationale": "...",
      "reference_annotation": {"narrative": "...", "bullets": ["..."], "action_items": ["..."]}
    }
  ],
  "few_shot_demonstrations": {
    "content_sha256_list": ["..."],
    "overlap_check": "no overlap with the 36 frozen examples or the project's protected/acceptance benchmarks"
  },
  "models": [
    {"name": "google/flan-t5-base (untuned baseline)", "revision": "...", "chat_template": "...", "max_input_tokens": 0, "max_output_tokens": 0, "precision": "...", "software_versions": {}},
    {"name": "project current fine-tuned checkpoint", "revision": "...", "chat_template": "...", "max_input_tokens": 0, "max_output_tokens": 0, "precision": "...", "software_versions": {}},
    {"name": "Qwen/Qwen3-4B", "revision": "...", "chat_template": "...", "max_input_tokens": 0, "max_output_tokens": 0, "precision": "...", "software_versions": {}},
    {"name": "Qwen/Qwen3-14B", "revision": "...", "chat_template": "...", "max_input_tokens": 0, "max_output_tokens": 0, "precision": "...", "software_versions": {}}
  ]
}
```

## What remains gated

Selecting real examples, authoring their reference annotations, and running any of the two conditions
against any of the four models all require Johnny's separate authorization (protocol step 7). This
document only fixes the method those later steps must follow.
