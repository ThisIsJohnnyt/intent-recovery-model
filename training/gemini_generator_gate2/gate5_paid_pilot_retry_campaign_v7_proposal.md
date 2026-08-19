# Gate 5 V7: version-scoped narrative-idiom diversification campaign proposal

**Date:** 2026-08-17
**Status:** Proposal only. This document authorizes no V7 engine, gate, attestation, campaign state, credential access, provider request, spend, candidate handling, corpus mutation, staging, commit, or push.

## 1. Authority boundary

V6 is permanently terminal at five attempts and cannot be resumed. V7 would be a new extension with its own prompt, request and schedule pins, engine, gate, attestation, campaign directory, attempt numbering, and explicit authorization. No V1-V6 file, hash, evidence row, prompt, schedule, attestation, or control may be reinterpreted or mutated.

This proposal recommends carrying forward V6's independently reviewed maximum of 15 V7 attempts, aggregate hard ceiling of 5,000,000 USD-millionths ($5.00), and aggregate reconciliation stop of 3,750,000 USD-millionths ($3.75). These are proposal values only. A reviewed build, fresh same-day facts, execution-disabled draft attestation, independent validation, Johnny's later explicit final authorization, and Johnny personally running any fully substituted command would still be required.

## 2. Purpose and evidence basis

The project's two genuine protected-content collisions both occurred in `proposed_output.narrative` while using schedule slot 1 / mechanism M01. The structured evidence identifies the V6 collision as `proposed_output:output.narrative:protected_collision` against `comparator:052:output.narrative`, with token-Jaccard 0.1515. Candidate text was neither quarantined nor privately retained, so the diagnosis relies only on the content-free collision evidence plus project-controlled prompt and comparator material.

The reviewed root-cause hypothesis is narrow-idiom convergence: M01 requests an unresolved ambiguous scheduling state, while several protected narratives use the obvious “It is/remains unresolved/unclear whether…” construction. V7 changes no collision threshold or protected content. It uses the independently reviewed one-bullet prompt revision to encourage varied natural phrasing while preserving the underlying uncertainty.

The V7 prompt package is already locally built and independently reviewed:

| Artifact or pin | SHA-256 |
| --- | --- |
| Narrative diversification proposal | `8f90fb3d341a641a0d847dfeddd9e6fea3c7132906b60ab286a279584453b0bb` |
| Historical `system_instruction.txt` | `339b6f7841248ce40dcd925518cd6cea8fe5c069b2e9cf88b1ab75cbefe7e215` |
| V7 `system_instruction_v7.txt` | `9f67d86da8b53e605f6c93a5fac2a23af333382640aba04ecd5a3ada34d3c68c` |
| Historical slot-1 request envelope | `8420c2d8360f4ffc96fb617dd8d4b081732cf2c87654a65d3ddc2ab8426297b4` |
| V7 slot-1 request envelope | `24dbeb008f4b2735d72ae0debe41729963e2adb3112cb1f9fb472120a63bfd94` |
| V7 local prompt builder/verifier | `3bd73c896847b415cfa8def5b6a32906590c4c534ed3aa7beb89eae9c4811ac5` |
| V7 focused prompt tests | `dc11578d3a808594c07fd32622535ddb6c53be2d265fbbd84b88160a2b5dbaaa` |

## 3. Re-derived V6 baseline and arithmetic

The V7 build must call V6's own `load_and_verify_campaign()` and must not trust this prose. The current independently verified terminal anchors are:

| Fact | Value |
| --- | --- |
| V6 final attestation | `980c23dbe9308aa32aa48c15480bb64722993f71b6a4dfa7c8fbd0316d275839` |
| V6 terminal campaign ledger | `42222ea78f55aefc4f2364baf74c3a6f4ab1df8d57723ea87bbc4015559078ca` |
| V6 terminal state | `stopped_nonretryable_outcome` |
| V6 attempts reserved | 5 |
| Historical component count | 18 |
| Historical component manifest | `c0c73f2506b9f8350698007b0405b38423a061206d66a72bae3cbe66c1239f8b` |
| Historical booked cost | 170,880 USD-millionths ($0.17088) |
| Final V6 state-row hash | `8b670cc6b33d2f7506c6bbee56052a326ae6c9f6d696b407dd41a4ba74195ec4` |
| Final V6 completion | `0bc6d104decaae1075a77deb135ca39954293cc6969403931700b132203f789b` |
| Final component row | `322b691edd9be12016ec44ba96f9825e45f16d9bd37cfe2451b33054fa672a8c` |
| Final disposition | `proposed_output:output.narrative:protected_collision` |

The build must additionally pin all five V6 locks and completions plus every per-attempt output artifact. The current lock/completion anchors are:

| Attempt | Lock SHA-256 | Completion SHA-256 |
| --- | --- | --- |
| 1 | `3fed5d0d8518f01f6407699cf48cfe1c34512859c9b49ad0fc7e7ad3926f8379` | `2457c790bb4286a4242f49b095e9a45a6c1779d1da79853bc5a35514ed2bf5ea` |
| 2 | `c54ab00abb21c88213af4a67a6aea02cd4a4753111773a54139ed49adc6617f6` | `5f7094900a376de876953319b02a23252c10096dbeebbe4b3558e0a0f28ccab2` |
| 3 | `e08d7d70992ba8e610371fd4dbee5a715de1338df9dbf4c806539760f92483bc` | `f26a269d05a11dc21d307519d726eee129d71dd6c8ddd8e79545f5ba7b055f76` |
| 4 | `e34b3176d76a0c5494d9c58e4877be4a87e606190a772f8109bc6e821231a9c7` | `1599e3d3222fc0db7075e72f4a1a830c7fd70b7890da4c1122b75ae7f1d7fffa` |
| 5 | `b93ea1f06d47d76212ed03c38023a46b68fe608d698c218734c76cb7497d3ff9` | `0bc6d104decaae1075a77deb135ca39954293cc6969403931700b132203f789b` |

At the verified 2026-08-17 rates, one complete 24-slot schedule still reserves at most 204,000 USD-millionths. The proposed worst-case aggregate is:

`170,880 + (15 × 204,000) = 3,230,880 USD-millionths ($3.23088)`

That remains below both proposed V7 boundaries. The build must recompute this from the bound rate snapshot and the V7 schedule rather than trust the scalar.

## 4. Dedicated V7 prompt and schedule scope

V7 must not edit `system_instruction.txt`, `schedule.json`, `gate5_execution_gate.EXPECTED_LIVE_REQUEST_SHA256`, or any historical request receipt. It must use `system_instruction_v7.txt` only through the reviewed `gate5_v7_narrative_idiom_prompt.py` builder and must pin that module and prompt by hash.

Because every historical schedule `prompt_hash` was computed from the historical system instruction plus its user message, V7 must have a dedicated derived schedule artifact. That schedule must preserve exactly:

- 24 slots and their existing order;
- the two exact models and 12 slots per model;
- the M01-M12 mechanism-card mapping;
- every user-template and mechanism-card byte;
- all request controls, endpoint construction, timeout, and no-retry/no-stream/no-tool behavior.

It must recompute only the prompt-dependent fields using the V7 system instruction: each slot's `prompt_hash` and prompt-collision preflight. The V7 prompt plus each of the 12 rendered user messages has already been locally probed against the current quarantine references with no fatal preflight result; the build must turn that into deterministic tests and a pinned schedule hash.

The V7 engine's prompt-imitation references must likewise use the exact V7 system instruction plus the unchanged rendered user message. Reusing V6's historical prompt references would be a scoping bug. Receipts must carry the V7 schedule's prompt hash, while V1-V6 receipts remain bound to their historical hashes.

No slot may be skipped, reordered, substituted, or selectively retried. The absence of real M02-M12 evidence is acknowledged, not bypassed: V7 begins at slot 1 and reaches later slots only if the normal engine safely progresses there.

## 5. Dedicated V7 engine, gate, and lineage

The build should add a dedicated V7 engine rather than edit or monkey-patch the V6 engine. It may reuse reviewed pure helpers, but its request construction must call the V7 builder explicitly. It must carry forward unchanged:

- `V7_PILOT_CEILING = 5_000_000` and `V7_RECONCILIATION_STOP = 3_750_000`, without changing V1-V6 constants;
- maximum 15 V7 attempts;
- one provider request per slot, zero retry within an attempt;
- the strict parser, schema checks, usage caps, secret scan, protected/prompt/duplicate collision screen, candidate quarantine, and no automatic candidate acceptance;
- the exact four-code pause whitelist: `schema_invalid`, `extra_key`, `finish_reason_invalid`, `size_limit_failed`;
- one-use human review, same-day or immediate-next-day rate/fact refresh, and fail-closed N+2/rate-drift behavior;
- V6's private raw-output diagnostic boundary, including `STOP`/`MAX_TOKENS` only, provider safety/citation withholding, collision withholding, secret withholding, 65,536-byte cap, hash-linked private storage, and hard-terminal persistence failure;
- all non-whitelisted outcomes as hard-terminal, including every protected collision.

V7 starts a new component sequence after the verified 18-component V6 history and starts its own attempt numbering at 1. Every reservation and actual-cost decision uses the growing live component chain. The V6 terminal collision remains immutable history and supplies no execution authority.

The V7 attestation gate must bind the exact proposal, V7 prompt, V7 prompt builder, V7 schedule, engine, private diagnostic module, campaign runner, gate, and focused tests. It must also bind the complete terminal V6 lineage described above. Build review must occur before any attestation is drafted.

## 6. Required local tests

Before any V7 attestation may be considered, focused tests must prove:

1. V6 is re-derived through its own verifier as terminal with 18 components, 170,880 USD-millionths, manifest `c0c73f...`, five attempts, and the protected-collision final component.
2. All V1-V6 prompt files, schedules, constants, request pins, attestations, state, receipts, ledgers, diagnostics, locks, completions, and output hashes remain unchanged.
3. `system_instruction_v7.txt` is exactly the historical prompt plus the one reviewed bullet, and its prompt builder has no credential or transport capability.
4. The V7 schedule preserves all non-prompt-dependent slot data, has 24 slots / 12 mechanisms / two exact models, recomputes every prompt hash from V7 system plus unchanged user text, and has no fatal prompt preflight.
5. Slot 1 rebuilds to the separate V7 request-envelope pin `24dbeb...`; the historical slot rebuilds to `8420c2d8...`; neither can validate as the other.
6. The V7 engine uses V7 schedule prompt hashes and V7 prompt-imitation references end to end. A deliberate fallback to historical prompt or schedule data fails.
7. The same outcome, pause/review, collision, schema, private-diagnostic, concurrency, recovery, cost, attempt-cap, rate-refresh, and credential-failure protections covered by V6 remain passing under V7.
8. Exact boundary arithmetic is enforced: 15 attempts, 3,230,880 worst-case aggregate, $3.75 pre-request stop, and $5.00 hard ceiling, with all earlier constants untouched.
9. `--verify-only` performs no network, credential read, or file creation.
10. Canonical secret scans, `git diff --check`, and the private-diagnostic `git check-ignore` boundary pass.

## 7. Explicit non-goals

V7 does not weaken collision thresholds, remove or rewrite protected references, recover V6 candidate text, create phrase-specific exemptions, accept near misses, mutate the corpus, add retries within attempts, reorder M01-M12, change models, add tools/caching/streaming, or automatically accept generated candidates.

It does not guarantee that the revised prompt avoids collision; it makes a narrow, testable generation-side change while preserving the same fail-closed detector. A new real collision remains a correct terminal outcome.

## 8. Review and authorization sequence

1. Claude independently reviews this proposal.
2. Only after proposal approval may Codex build the local V7 package.
3. Claude independently reviews all source, hashes, tests, V6 re-derivation, and historical immutability.
4. Johnny re-confirms fresh same-day rate/account/activity facts.
5. Codex prepares an execution-disabled V7 attestation draft; Claude validates it.
6. Johnny separately decides whether to authorize V7 execution.
7. Claude validates the final one-field authorization change.
8. Only then may Johnny personally run a fully substituted command.

No step in this proposal authorizes the next one automatically.
