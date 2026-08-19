# Gate 5 V8: M02-start breadth diagnostic campaign proposal

**Date:** 2026-08-17
**Status:** Proposal only. This document authorizes no V8 engine, gate, attestation, campaign state, credential access, provider request, spend, candidate handling, corpus mutation, staging, commit, or push.

## 1. Authority boundary

V7 is permanently terminal after six attempts and cannot be resumed. V8 would be a new, separately bounded diagnostic with its own schedule, engine, gate, attestation, campaign directory, attempt numbering, and explicit authorization. No V1-V7 prompt, schedule, request receipt, attestation, ledger, state, candidate record, protected reference, threshold, or control may be reinterpreted or mutated.

This proposal recommends a maximum of 15 V8 attempts, a V8-only aggregate hard ceiling of 5,000,000 USD-millionths ($5.00), and a V8-only aggregate reconciliation stop of 3,750,000 USD-millionths ($3.75). These are proposed limits, not execution authority. A reviewed local build, fresh same-day facts, execution-disabled draft attestation, independent validation, Johnny's later separate final authorization, and Johnny personally running any fully substituted command would each still be required.

## 2. Evidence and diagnostic question

All six real V7 requests used the reviewed diversified V7 prompt and the exact V7 slot-1 request pin `24dbeb008f4b2735d72ae0debe41729963e2adb3112cb1f9fb472120a63bfd94`. Attempts 1–5 stopped at clean HTTP 503 before parsing. Attempt 6 received HTTP 200 and correctly hard-stopped for a protected collision, with zero quarantined candidate records and no persisted candidate text.

The V7 terminal collision is content-free evidence at `proposed_output:output.bullets:02`, mechanism M01, model `gemini-3.7-flash`. It reported protected token-Jaccard matches against `comparator:040:output.bullets:05` (0.1875) and `comparator:067:output.bullets:01` (0.157895). This differs from V6's two `output.narrative` collisions. No V7 narrative collision occurred, which supports the narrow conclusion that V7's narrative wording diversification worked for its intended field; it does not establish that M01 is safe in adjacent fields.

The diagnostic question is therefore deliberately broader and falsifiable: when M01 is absent from the schedule, do M02–M12 proceed cleanly under the unchanged collision screen on both exact models? A clean completion of the full V8 schedule would support an M01-specific containment hypothesis. A protected collision outside M01 would instead be evidence that the risk is broader than that card and should change the remediation analysis. Neither outcome authorizes threshold changes, protected-reference edits, or candidate acceptance.

## 3. Re-derived V7 baseline and arithmetic

Any V8 build must call V7's own `load_and_verify_campaign()` and must not trust this prose. The current terminal anchors are:

| Fact | Value |
| --- | --- |
| V7 final attestation | `bd661065819a4db02fda73e781aa0f8ef2bbbd13c0fddac8780f491848e48be7` |
| V7 terminal campaign ledger | `e934d7038031120d63e15ed020a136aedf68f4146bd9295f2b47eb64a08d4f3f` |
| V7 terminal state | `stopped_nonretryable_outcome` |
| V7 attempts reserved | 6 |
| Historical component count | 24 |
| Historical component manifest | `fb806f9187b7942e15f58b0ce0fa62ccd09b35e4a48150d3e6235d4a1f4360f9` |
| Historical booked cost | 234,960 USD-millionths ($0.23496) |
| Final V7 state-row hash | `2802cb855c125db9460d310e9aacd4084e86ee14ee17a3bcf818bacb7c79f17c` |
| Final V7 completion | `5ab1ad2a500b2c76995a3aad40d3c236d51bf7d7c35508f3e1457d3a491c229c` |
| Final V7 component row | `29cbe3348a7ca2cb2db3bb3d4a1402837456f2bba90cb8e79bf8ed262b57cafb` |
| Final collision-diagnostic ledger | `138bbe3177fdcfff2c796ca6c74ee94507f42e8a39800d7edb259d383c854a78` |
| Final disposition | `proposed_output:output.bullets:02:protected_collision` |

The build must additionally pin all six V7 locks and completions, every per-attempt output artifact, the terminal attestation, and the exact V7 request/prompt/schedule artifacts. It must prove that terminal V7 cannot reserve another V7 attempt before any V8 action is considered.

At the verified 2026-08-17 rate snapshot, the 24-slot V7 schedule reserves 204,000 USD-millionths per full attempt. Its excluded M01 pair reserves 17,000, leaving a 22-slot M02–M12 schedule reservation of 187,000 USD-millionths. The proposed maximum aggregate is therefore:

`234,960 + (15 × 187,000) = 3,039,960` USD-millionths ($3.03996).

This is below both proposed V8 boundaries. A future V8 build must recompute reservation cost from its bound execution-day rate snapshot and its exact 22-slot schedule; this arithmetic is not a substitute for that check.

## 4. Dedicated M02-start schedule and prompt baseline

V8 must use the already reviewed V7 system instruction unchanged, not revert to the historical instruction and not add a second prompt edit. The V7 system prompt (`9f67d86da8b53e605f6c93a5fac2a23af333382640aba04ecd5a3ada34d3c68c`) and V7 prompt builder (`3bd73c896847b415cfa8def5b6a32906590c4c534ed3aa7beb89eae9c4811ac5`) remain mandatory baseline artifacts because the V7 change eliminated the observed narrative-field collision without weakening screening. Reverting would discard relevant positive evidence and confound the M01-exclusion diagnostic.

The V8 build must create a new hash-pinned 22-slot schedule derived only from V7 schedule entries whose source slots are 3 through 24:

- first retained source slot: 3, M02, `gemini-3.5-flash-lite`;
- second retained source slot: 4, M02, `gemini-3.7-flash`;
- retained mechanisms: M02 through M12, each on both exact models, in their existing source order;
- excluded source slots: 1 and 2 only, the M01 pair;
- unchanged retained bytes: model, mechanism card, rendered user message, request controls, endpoint construction, timeout, no-retry, no-stream, no-tools, schema, and usage limits;
- recomputed and pinned fields: the V8 schedule manifest, schedule-sequence metadata, and prompt-collision preflight evidence for every retained entry, using the V7 system instruction plus each unchanged user message.

The schedule must retain immutable `source_schedule_slot` values 3–24 and assign a separate contiguous `campaign_schedule_sequence` 1–22. That is a different campaign starting point, not a shortcut through validation: once V8 begins, it may advance only one retained sequence at a time after the normal parser, schema, safety, secret, collision, accounting, and receipt checks succeed. It may not skip a retained M02–M12 entry, reorder either model, selectively retry, or jump from an early 503/collision to a later mechanism.

Consequently, V8 does not guarantee reaching M03–M12: clean provider outcomes are still required for ordinary progression. That constraint is necessary to keep the diagnostic honest. It also means a clean full V8 schedule is meaningful breadth evidence, whereas another early M02 failure is an evidence-bearing result rather than a reason to bypass M02.

## 5. Dedicated V8 engine, gate, and lineage

Only after proposal approval may a dedicated V8 engine, campaign runner, gate, attestation template, review template, and tests be built. They must be separate from V1–V7 and must bind:

- the exact V8 proposal, V7 system instruction and prompt builder, V8 schedule, V8 engine, reused reviewed private-raw diagnostic module, V8 gate, V8 runner, and focused tests;
- the complete V7 terminal lineage described above, including its attestation, all locks/completions/output artifacts, final state, final component, and collision diagnostic;
- `V8_PILOT_CEILING = 5_000_000`, `V8_RECONCILIATION_STOP = 3_750_000`, maximum 15 attempts, initial 24 components, and the dynamically re-derived V7 booked cost;
- all V7 protections unchanged: one request per slot; no in-attempt retry, redirect, substitution, model change, tools, cache, streaming, corpus mutation, or automatic acceptance; strict parsing; schema checks; usage caps; secret scan; protected/prompt/duplicate collision screen; candidate quarantine; and text-free normal evidence.

The exact four-code pause whitelist remains `schema_invalid`, `extra_key`, `finish_reason_invalid`, and `size_limit_failed`. Same-day or immediate-next-day one-use human review, fail-closed N+2/rate-drift behavior, provider safety/citation withholding, and the V6 private raw-output diagnostic boundary remain unchanged. Every protected collision, including any M02–M12 collision, is hard-terminal.

## 6. Required local tests

Before any V8 attestation is considered, focused tests must prove:

1. V7 is re-derived through its own verifier as terminal with six attempts, 24 components, 234,960 USD-millionths, manifest `fb806f...`, final collision component `29cbe334...`, and zero candidate leakage.
2. V1–V7 files, prompt pins, request receipts, constants, schedules, attestations, state, locks, completions, ledgers, diagnostics, and output hashes remain unchanged.
3. V8 uses the exact V7 system prompt and V7 builder, with no prompt fallback to historical text and no new wording change.
4. The V8 schedule contains exactly 22 entries with source slots 3–24, M02–M12 twice each, both exact models, retained order/bytes, deterministic V7-prompt preflights, and a pinned manifest.
5. M01 cannot be smuggled into the V8 schedule, and no historical/V7 schedule or prompt hash can validate as a V8 request; tampered source-slot, mechanism, order, model, or manifest data fails closed.
6. V8 begins at M02 but never bypasses validation or normal progression: it cannot reach a later retained entry after a failed or blocked earlier retained entry.
7. V8 preserves V7's outcome, pause/review, schema, private-diagnostic, collision, concurrency, recovery, cost, attempt-cap, rate-refresh, and credential-failure protections.
8. Exact boundary arithmetic is enforced from the 22-slot schedule: 187,000 per full attempt, 3,039,960 proposed worst-case aggregate, $3.75 reconciliation stop, and $5.00 hard ceiling, while every earlier version's constants remain unchanged.
9. `--verify-only` performs no network activity, credential read, or file creation.
10. Canonical secret scans, `git diff --check`, and a V8 private-diagnostic `git check-ignore` boundary pass.

## 7. Explicit non-goals

V8 does not patch M01, relax collision thresholds, remove or rewrite protected references, use phrase-specific exemptions, recover candidate text, alter comparator pools, accept near misses, resume V7, create a retry within an attempt, or automatically accept candidates. It does not claim M01 is conclusively the root cause before evidence from the retained mechanisms exists.

Excluding M01 is a version-scoped experimental condition, not a safety bypass. Every retained slot stays under the same fail-closed screen; a collision outside M01 is a valid terminal diagnostic result.

## 8. Review and authorization sequence

1. Claude independently reviews this V8 proposal.
2. Only after proposal approval may Codex build the local V8 package.
3. Claude independently reviews all V8 source, hashes, tests, V7 re-derivation, and historical immutability.
4. Johnny re-confirms fresh same-day rate, account, activity, model, and control facts.
5. Codex prepares an execution-disabled V8 attestation draft; Claude validates it.
6. Johnny separately decides whether to authorize V8 execution.
7. Claude validates the final one-field authorization change.
8. Only then may Johnny personally run a fully substituted command.

No step authorizes the next one automatically.
