# Claude's Review: Source-Determined Items v2 Acceptance Schema

**Date:** 2026-08-02
**Reviewing:** `source_determined_items_v2_acceptance_design_notes.md`'s six review questions, against `datasets/benchmark/source_determined_items_v2_acceptance_draft.jsonl` (10 cases) and the actual current scoring code (`run_benchmark.py`, `report_benchmark.py`, `test_report_benchmark.py`).
**Compute authorized:** none. No implementation performed -- this is a design review only.

## Independent checks performed before answering

- Re-derived the current "result scaffold" and "scoring-safety code" directly from `run_benchmark.py`'s per-probe result dict and `report_benchmark.py`'s `probe_passes()` -- there is no separate formal schema file; the de facto schema is whatever these two functions read/write, pinned by `test_report_benchmark.py`'s integration tests against the real `gold_v1.2.1_probes.jsonl`.
- Independently re-checked the "no four-word input overlap with either the protected probes or historical acceptance cases" claim with a script (4-word shingles, case-insensitive, over `gold_v1.2.1_probes.jsonl`, `source_determined_bullets_acceptance.jsonl`, and the 10 draft cases): **confirmed, zero overlap**.
- Confirmed all `required_semantic_dimensions` values used in the draft (`topic_completeness`, `unsupported_addition_resistance`, `uncertainty_preservation`, `attribution_accuracy`) are exactly `report_benchmark.py`'s `KNOWN_SEMANTIC_DIMENSIONS` -- no new dimension name needed.
- Confirmed each case's declared `bullet_count_rule`/`action_count_rule` matches its own row in the design notes' coverage map (all 10, no mismatches).
- Built reasonable-effort full-target reconstructions for sdi2-08 and sdi2-10 (the two structurally densest cases) from their own `input`/`expected_behavior` text and tokenized them against the real seed-17 checkpoint tokenizer for Q6 -- see that answer for values and the caveat on what this does and doesn't prove.

## Answers

**1. Can the current result scaffold carry both required count rules without reusing human `capability_checks`?**

Yes, structurally clean, but not yet implemented. The draft's own `primary_checks` arrays never include a count-related check name (verified directly), so `capability_checks` is already correctly reserved for human/semantic judgments only -- no reuse conflict. But `run_benchmark.py`'s result dict has no field for count rules or their evaluated outcome today; it would need two additive fields, e.g. `bullet_count_result`/`action_count_result` (each holding the rule, the literal parsed count, and the pass/fail), populated the same way `required_semantic_dimensions` is already copied straight from the probe. This is new code, not a schema-compatibility problem.

**2. Can count-rule evaluation be computed immediately after parsing and stored immutably in each result?**

Yes for "computed immediately after parsing" -- this is the same point in the pipeline `format_valid` is already computed at (deterministic, no human judgment, written once by the runner). But "immutable" isn't actually enforced anywhere in the current scoring workflow -- nothing stops a human from hand-editing `format_valid` or a future count field while filling in `scores`/`capability_checks` during manual scoring; it works today by convention, not by a check. This project already has real immutability/lineage machinery elsewhere (`real_data_lineage.py`, the withdrawal protocol) for a similar reason. Recommend deciding explicitly whether count-rule results get that same treatment (a validator that re-derives the count from `raw_output` and fails if the stored value was hand-altered) or whether "immutable by convention" is accepted for this release -- the design notes don't say which, and I'd rather flag the gap than assume.

**3. Will all ten records validate under a dedicated v2 acceptance schema without weakening the protected benchmark schema?**

Yes, but only if implemented as an additive wrapper, not a modification of `probe_passes()`. Concrete recommendation: write a new function (e.g. `v2_acceptance_gate_passes()`) that calls the existing `probe_passes()` unchanged for the format/semantic/capability-check gate, then separately requires and evaluates `bullet_count_rule`/`action_count_rule` -- ANDing the two. Critically, this new function should follow the precedent `probe_passes()` already set for `required_semantic_dimensions` (raise loudly on a missing/unrecognized count rule rather than silently treating it as "not applicable" -- the same fail-open gap already found and fixed once this session for semantic dimensions would reappear here if count rules are allowed to default-pass when absent). Implemented this way, the protected 16-probe and 5-historical-case schema is untouched -- `probe_passes()` itself never changes.

**4. Are `exact` and `max` sufficient operators for this release?**

Sufficient for these ten cases as authored -- 9 use `exact` on both rules, sdi2-08 uses `max` for bullets (a deliberate ceiling with no stated floor) and `exact` for actions. No case needs a bounded-but-flexible count (a `min`+`max` range) that neither operator alone can express. Flagging for later, not now: a future case wanting "somewhere between 2 and 4 bullets" would need a range operator this vocabulary doesn't have yet. Not a blocker -- the design notes already specify (line 55) that an unrecognized operator must stop before model loading, so adding one later is a safe, forward-compatible extension, not a breaking change.

**5. Can a current runner inject the candidate prompt/parser while retaining current scoring-safety code?**

Yes, but it must be a separate script, not an in-place edit of `run_benchmark.py`. `run_benchmark.py` currently imports the live v1 contract directly (`from prepare_data import ... build_prompt`) and validates format with a marker-existence check, not full structural parsing -- editing it to import `prompt_contract_v2_candidate`/`prompt_contract_v2_parser` in place would contradict that module's own explicit boundary ("never imported by prepare_data.py, train.py, or run_benchmark.py"), the same boundary this session's entire static-feasibility phase has been built around not crossing. `report_benchmark.py`'s scoring-safety code (`probe_passes()`, the `required_semantic_dimensions` fail-open fix) operates purely on result-JSON fields, independent of which contract produced them -- so a new `run_benchmark_v2.py` that writes the same result shape (`format_valid` now computed via `parse_output()` success instead of the v1 marker check) is consumed by the existing `report_benchmark.py` unchanged. This is design-only confirmation of feasibility; no runner exists yet, and none should be built without separate compute authorization.

**6. Does full-target tokenization leave safe generation headroom for sdi2-08 and sdi2-10?**

Real evidence, not a guess, but bounded by a real limitation: sdi2-08 and sdi2-10 don't have authored full target text yet (only `expected_behavior` prose), so I built reasonable-effort reconstructions from each case's own stated content and tokenized them against the real seed-17 checkpoint tokenizer. Result: sdi2-08 (8 actions, minimal bullets) ≈ 164 tokens (136 of headroom under the 300-token `GENERATION_MAX_NEW_TOKENS` budget); sdi2-10 (6 bullets + 2 actions, the densest case) ≈ 217 tokens (83 of headroom). For calibration: this is consistent with the real 66-record migrated-target distribution from Finding 3's fix (min 51 / median 129.5 / p95 188 / max 244) -- sdi2-10's estimate sits just above that real max, which is expected since it's deliberately the single densest case in the new set. **This is my reconstruction, not ChatGPT's authored target** -- treat it as "comfortable headroom is plausible," not as a guarantee; the real answer depends on the actual target text once authored.

## Disagreements / open items

None of the six answers above are disagreements with the design notes -- all six are "yes, with an implementation detail the notes didn't specify." The one item I'd call an actual open decision rather than a yes/no: **Q2's immutability enforcement** -- convention-only vs. an active validator. I'd lean toward convention-only for this release (matches how `format_valid` already works, and adding lineage-grade enforcement here would be new scope not requested), but this is Johnny's call, not mine to decide silently.

No changes requested to the 10 draft cases themselves -- the count/coverage-table cross-check and the n-gram overlap check both came back clean.
