# Claude's Review: Source-Determined Items v2 Gold-Target Draft

**Date:** 2026-08-03
**Reviewing:** `source_determined_items_v2_gold_targets_chatgpt_handoff.md` and its companion artifact `source_determined_items_v2_acceptance_gold_targets_draft.jsonl`
**Compute performed:** none. No model, checkpoint, or training touched. Real tokenizer/parser code was used for static verification only (encode/decode + parse, no generation).

## Outcome

**Aligned.** All eight required review steps completed. No unsupported-content additions found in any of the 10 reference outputs. Every mechanical claim in the handoff was independently re-derived and matched exactly. Both explicitly-flagged authoring judgments (sdi2-08's bullet omission, sdi2-10's shared deadline) are correct on independent analysis -- no disagreement to raise. One discrepancy found and resolved (not a content problem): the design-notes hash in an earlier handoff didn't match my committed copy byte-for-byte, traced to Windows git `autocrlf` CRLF-normalizing my checkout -- confirmed identical content after LF-normalizing, consistent with a known, already-diagnosed pattern from earlier this session.

## 1-2. Content review: every reference output vs. source input and frozen rubric

Read all 10 cases side by side with their `input`/`expected_behavior`/`primary_checks` from the acceptance draft. Found no invented cause, answer, referent, emotion, task, or commentary in any case. Specific checks:

- **sdi2-01, 03**: pure observations stay observations; no repair-task or causal explanation added.
- **sdi2-05, 09**: tentative/dangling-reference language ("might try", "the smaller one", "theirs", "it") preserved verbatim -- no missing referent supplied, no commitment invented.
- **sdi2-06**: both named alternatives (linen, woven) survive; "unresolved"/"undecided" framing kept; the later craft-room observation is stated as a bare fact, never treated as an answer to the cover choice.
- **sdi2-10**: attribution preserved correctly through an active/passive voice change ("the glaze samples were delivered by the courier" -> "the courier delivered the glaze samples") -- same roles, same claim structure, still attributed to the studio coordinator's account, not asserted as a witnessed fact. Tentative framing ("maybe") and the unresolved tile-count question both survive without being resolved.
- Minor, non-blocking style note: narratives for task-only cases inconsistently prefix "I need to" (sdi2-02, 04, 07, 08 do; sdi2-09 doesn't, despite also being task-only). Doesn't affect any rubric dimension and doesn't warrant a rewrite -- flagging for awareness, not as a defect, since the reference is explicitly "not exact-match."

## 3. Structural re-verification (real parser, real count-rule logic)

Ran independently against the real `prompt_contract_v2_parser.parse_output()` and `contract_adapters.evaluate_count_rule()`:

- 10/10 valid JSONL rows, unique IDs, order matches the benchmark file.
- 10/10 `v2_target` strings parse without error.
- 10/10: parsed narrative/bullets/actions equal `reference_output` exactly.
- 10/10: `bullet_count_rule`/`action_count_rule` satisfied.
- 10/10: bullets <= 7, actions <= 8 (hard ceilings respected).

All matches ChatGPT's claimed local validation exactly.

## 4. Protected-language n-gram audit

Re-ran the established 4-word-shingle procedure, this time against the *reference output text* (narrative + bullets + actions, matching what the handoff claims to have checked) rather than the `input` text checked in the prior acceptance-draft review. Compared against both the protected 16-probe file and the historical 5-case file's `input` + `expected_behavior` fields. **0 matches**, confirming the handoff's claim.

## 5-6. Real tokenizer statistics and round-trip

Tokenized all 10 complete `v2_target` strings with the real seed-17 checkpoint tokenizer:

| Statistic | Tokens |
|---|---:|
| Minimum | 54 |
| Median | 76.0 |
| p95 | 244 |
| Maximum | 244 (sdi2-08) |
| At or above 300 | 0/10 |

Character counts cross-checked against the handoff's table for all 10 cases -- exact match (e.g. sdi2-08: 838 chars, sdi2-10: 934 chars). The max token count (244, sdi2-08) coincidentally equals the historical 66-record corpus's own previously-recorded max -- verified this wasn't a copy/paste or caching artifact by an independent fresh recompute; it's a genuine coincidence, not a bug.

For every case: marker counts survive the encode/decode round-trip exactly, the decoded text still parses under the real parser, and the re-parsed structure still matches `reference_output` exactly -- stronger than what was asked (which only required marker/parse-validity survival); I additionally verified full structural equality post-round-trip.

## 7. Cross-runtime (JS) parity

Ran a one-time verification script (same methodology as this session's earlier tokenizer-parity work: esbuild ESM bundle, `@xenova/transformers` left external, real deployed model files) that encoded/decoded all 10 targets through the actual production JS tokenizer and parsed the result with the real `promptContractV2Parser.ts`. Every case: **identical token count to Python**, markers survive, and the re-parsed structure matches `reference_output` exactly. Script and its scratch data file deleted after the run -- not left as a permanent artifact, since the fixture set is still explicitly draft/not frozen (matching the "don't build permanent infra around unfrozen content" judgment call from the schema review).

## sdi2-08 and sdi2-10: the two flagged authoring judgments

**sdi2-08 (7 bullets, camera-battery task omitted from bullets but present in narrative + actions):** agreed, no disagreement. With 8 distinct tasks and a hard 7-bullet ceiling, exactly one task's bullet must be sacrificed somehow -- the alternatives are merging two tasks into one bullet (risks `NO_TASK_MERGE`) or dropping a task from actions too (violates `ALL_EIGHT_TASKS_SURVIVED`). Keeping the omitted task fully present in the narrative and in actions, and dropping only its dedicated bullet line, is the least lossy resolution available. One clarification worth stating explicitly for future scoring: *which* of the 8 tasks loses its bullet is not itself a required behavior -- this reference picks the last one as one valid instantiation, not the only correct one. A real model output that instead dropped a different task's bullet (say, "sharpen the garden shears") while still fully preserving all 8 in the narrative and all 8 as actions should score identically. Worth a one-line note in the target file or scoring rubric so a future human/LLM judge doesn't over-fit to "must be the camera-battery bullet specifically."

**sdi2-10 (shared "Before Saturday" deadline applied to both coordinated tasks):** agreed, no disagreement. The input's syntax ("Before Saturday, send... and pack...") is a standard fronted adverbial scoping over the whole coordinated verb phrase -- there is no plausible reading where the deadline applies to only one of the two conjuncts. Given the rubric requires exactly 2 separate action items, distributing the shared deadline onto both is the only way both actions can independently satisfy `DEADLINE_SURVIVED`; this isn't an invented addition, it's the correct distribution of information already given once in the source.

## 8. Repository path and schema-integration recommendation

**Path:** keep it at `training/source_determined_items_v2_acceptance_gold_targets_draft.jsonl` (already copied there from the handoff). This matches the existing precedent of `training/prompt_contract_v2_migrated_targets_DRAFT.jsonl` -- a reference/target artifact, not itself a runner input, so it belongs alongside other training-side generated-reference data rather than in `datasets/benchmark/`, which is reserved for probe *definitions* `run_benchmark.py` loads directly.

**Schema integration:** built and committed `training/test_source_determined_items_v2_gold_targets.py`, a permanent static regression test (mirroring this project's established no-pytest script convention) that runs everything verified above as an automatic check: ID/order match, parse success, exact structural equality against `reference_output`, count-rule/ceiling satisfaction, the n-gram audit, and the tokenizer round-trip (including the token-budget report). This is the concrete integration point -- any future edit to the targets file, the parser, the count-rule logic, or the protected benchmark files will be caught automatically instead of requiring another manual review pass. Deliberately **not** wired into `run_benchmark.py`/`report_benchmark.py`'s live scoring path -- these targets are reference/scoring-anchor data, not benchmark probe definitions, and the "not exact-match" role is preserved by keeping this test purely structural (parse/count/ceiling/token-budget), never comparing generated model output text against `reference_output` for equality.

## Discrepancy noted, not a blocker

The design-notes SHA-256 in an earlier handoff (`a9b8614e...`) didn't match my committed file's raw bytes (`4523b878...`); LF-normalizing my file's CRLF line endings produces an exact match. Same root cause as a bug found and fixed earlier this session (Windows git `autocrlf`) -- confirms the content ChatGPT reviewed is identical to what's committed, just represented with different line endings locally. No action needed beyond noting it here for the record.

## Status

No target frozen yet, no compute requested or performed, matching the handoff's own stated gate. Recommend: once Johnny/ChatGPT are ready, this package can be marked Aligned on my side too -- I have no outstanding disagreement or required correction.
