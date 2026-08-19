# Gate 5 bounded paid-pilot retry campaign v2 proposal

Date: 2026-08-16

Status: proposal only. This document authorizes no credential access, provider request, spend, candidate handling, parser or threshold change, real-state mutation, staging, commit, or push.

## 1. Incident and confirmed design defect

The first bounded campaign is terminal after two reserved attempts:

1. Attempt 1 made one real request, received a clean HTTP 503, booked 10,680 USD-millionths, retained zero candidates, and was recovered append-only after a local path-handling failure.
2. Attempt 2 stopped before credential access and before any provider request. It booked zero cost and produced no output directory because the paid-pilot engine compared the attestation's frozen `prior_pilot_booked_cost_usd_millionths` value (32,040) with the live, growing historical component total (42,720).

That comparison is structurally invalid for a multi-invocation campaign. The attestation value describes the frozen pre-campaign baseline accepted at authorization time. The live historical total includes completed campaign attempts and must grow after every completion. These are different facts and must be validated separately.

The terminal v1 campaign remains immutable. It will not be reopened, edited, recovered again, or reused for execution.

## 2. Frozen v1 terminal evidence

- final v1 attestation SHA-256: `db6b6bec994cf707919d5a7b68d175aff45868ff7911485bc1af5201b2fb898b`
- terminal campaign state SHA-256: `642e27695f12d62a07d227a0a027ebe9c2f4e88b2c3d0bb783ffe8e4313f9e04`
- attempt-1 lock SHA-256: `4673ee5de671d42e2f42ee62402b52f3da8ec489ea3296007190a5c698b9f84a`
- attempt-1 completion SHA-256: `ae620a732a49680e1f6cf071e37e01de480593776df27c5ff5b33adc8201b5c6`
- attempt-1 summary SHA-256: `b7e6fdb2c878fcdd504fd47a5e3fb3894e81aabdeb51ccc8365397d27a171136`
- attempt-1 receipts SHA-256: `6044b56813dbabdfc86a02acc8012ef17d513b2d7719eaae785df44b374f75d2`
- attempt-1 cost ledger SHA-256: `c882c301bf1f4c7e7589cac4f841768e458cba737d4d6611f73714b629201226`
- attempt-1 rejection ledger SHA-256: `3137726f1b6ea7a5d50e517001cd93578bd9441a6d7c108db10ece7ddc216c65`
- attempt-1 empty quarantine SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- attempt-2 lock SHA-256: `a4eaea187cbe58b0b6d7eae6ba3eabda7c812ef2d148727250160e15790da909`
- attempt-2 completion SHA-256: `9aae7ee9ed94bac94734515674b93b842023adf61e338baccfb3c7daf8c7cd5d`

The v1 verifier must be run directly against this evidence. It must yield exactly five chained historical components, a terminal `stopped_nonretryable_outcome` state, two attempts reserved, and a recomputed total of 42,720 USD-millionths. The fifth component must be the zero-cost `zero_request_local_failure` with `global_stop: attestation_artifact_hash_mismatch`.

## 3. Paid-pilot engine correction

The engine will distinguish:

- **attested pre-campaign baseline:** the frozen cost value in the reviewed attestation; and
- **live historical context:** the current validated component chain supplied for this invocation.

`execute_pilot` may receive an explicit, internally supplied `attested_prior_pilot_booked_cost_usd_millionths` for a campaign invocation. Its default remains the live historical total, preserving the legacy direct-run behavior byte-for-byte in meaning.

When an explicit value is supplied, the engine must require all of the following before credential access:

1. it is an integer and nonnegative;
2. it is no greater than the validated live historical total;
3. the attestation's `prior_pilot_booked_cost_usd_millionths` equals it exactly;
4. the campaign's own gate and verifier independently pin the associated frozen prefix manifest, component count, and baseline total.

For campaign v2, the explicit attested baseline remains 32,040 USD-millionths because that is the frozen pre-v1-campaign fact Johnny reviewed. The separately verified live starting history is five components totaling 42,720 USD-millionths. All reservation, reconciliation-stop, hard-ceiling, receipt, cost-ledger, and summary calculations continue to use the live 42,720 total, never the smaller attested baseline.

No parser, request, model, schedule, transport, safety screen, collision rule, cost rate, $2.25 reconciliation stop, or $3.00 hard ceiling changes.

## 4. New campaign instance, not a v1 patch

A separate v2 gate, template, runner, state ledger, locks, completion files, output directories, and tests will be created. The v1 runner remains a verifier for its historical evidence and must refuse any further v1 reservation because its real state is terminal.

The v2 initial historical component list is the exact five-component result re-derived from the terminal v1 campaign. It is never manually reconstructed from scalar totals. The initial component manifest hash, count (5), and total (42,720) will be pinned in the v2 gate and attestation.

New component identifiers use a distinct `campaign_v2_attempt_NNN` namespace so they cannot collide semantically with v1 component identifiers.

## 5. Remaining campaign scope

The original authorization bounded the campaign at ten reserved attempts. V1 consumed two, including the zero-request second attempt. V2 therefore permits at most eight new manually invoked attempts.

Each invocation still launches at most one fixed 24-slot pilot attempt. It may continue only after a fully validated, zero-candidate, clean HTTP 503 outcome. A candidate, protected collision, completed 24-slot pilot, any non-503 status, any local ambiguity, any credential/transport failure, or the eighth v2 reservation makes v2 terminal for review.

No automation, background polling, timer, provider retry, slot retry, substitution, tool use, caching, or streaming is permitted.

Worst-case sizing:

- verified historical total entering v2: 42,720 USD-millionths;
- maximum reservation per full 24-slot attempt: 204,000 USD-millionths;
- eight-attempt worst case: `42,720 + (8 * 204,000) = 1,674,720` USD-millionths ($1.67472).

This remains below the existing $2.25 reconciliation stop and $3.00 hard ceiling. Those existing controls remain authoritative on every slot and invocation.

## 6. Required tests before attestation

The build must prove:

1. legacy direct execution still compares the attestation cost to its live static history when no explicit baseline is supplied;
2. v2 accepts frozen baseline 32,040 with independently verified live history 42,720;
3. v2 rejects a baseline above the live total, a wrong attestation baseline, a wrong five-component manifest, any dropped/reordered/duplicated/rehashed component, or any v1 evidence drift;
4. all monetary controls use the live total, never the frozen baseline;
5. the real terminal v1 evidence is independently re-derived rather than trusted from stored scalar fields;
6. v1 remains terminal and cannot reserve another attempt;
7. v2 attempts 1-7 continue only on clean zero-candidate 503; attempt 8 clean 503 caps; every other outcome is terminal;
8. concurrency, incomplete-attempt, recovery, evidence-tamper, relative-path CLI, secret-redaction, and no-credential-before-local-validation properties remain intact;
9. the full package suite passes and `--verify-only` uses no credential, network, or file output.

## 7. Required authorization sequence

1. Codex builds the local v2 package only after independent approval of this proposal.
2. Claude independently reads the source, recomputes hashes, runs all tests, and adversarially verifies the frozen-baseline/live-history separation.
3. Fresh same-day facts are confirmed directly with Johnny.
4. A new v2 attestation is drafted with execution authorization `false` and independently reviewed.
5. Johnny separately authorizes the v2 bounded campaign.
6. Johnny personally invokes each v2 attempt. Neither AI touches the credential or triggers a request.

Nothing in this proposal authorizes build-external mutation, a provider request, spend, candidate review, corpus mutation, staging, commit, or push.
