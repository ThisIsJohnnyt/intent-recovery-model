# Gate 5 bounded paid-pilot campaign: attempt-1 local recovery proposal

Date: 2026-08-16

## Incident

Campaign attempt 1 produced complete pilot evidence for one clean HTTP 503, but the campaign wrapper stopped before writing its completion artifact and `attempt_completed` state row. The existing campaign state remains append-only and untouched: its ledger ends with `attempt_reserved` for sequence 1.

## Frozen real evidence before recovery

- campaign state file SHA-256: `0295e9f6ea63f598771324549beaad54b9f03a453818df97a5a142c9537c9984`
- attempt lock SHA-256: `4673ee5de671d42e2f42ee62402b52f3da8ec489ea3296007190a5c698b9f84a`
- reservation SHA-256: `b2e9325d914528a57439a00d0fb1f92f1f738e6d815b5c201b69483cb48b33cd`
- run summary SHA-256: `b7e6fdb2c878fcdd504fd47a5e3fb3894e81aabdeb51ccc8365397d27a171136`
- request receipts SHA-256: `6044b56813dbabdfc86a02acc8012ef17d513b2d7719eaae785df44b374f75d2`
- cost ledger SHA-256: `c882c301bf1f4c7e7589cac4f841768e458cba737d4d6611f73714b629201226`
- rejection ledger SHA-256: `3137726f1b6ea7a5d50e517001cd93578bd9441a6d7c108db10ece7ddc216c65`
- candidate quarantine SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

The summary records one completed slot, zero quarantined candidates, `unexpected_http_status`, HTTP 503 in the terminal receipt, 10,680 USD-millionths for this attempt, and 42,720 USD-millionths aggregate historical cost after including it.

## Root robustness fixes

The deterministic incident cause is an unresolved relative path reaching `path.relative_to(ROOT)` after the file read. `gate2.canonical_file` now resolves its input path before both reading and constructing its project-relative receipt path, and rejects resolved paths outside the project root as `Gate2Error`. This covers both recovery and future paid-attempt validation at the shared boundary.

As separate filesystem hardening, `gate2.canonical_file` makes at most three immediate local read attempts. If all fail with `OSError`, it converts the failure to `Gate2Error("...: unreadable")`. This is local filesystem handling only; it does not retry any provider request. The earlier transient-read theory was synthetic and incomplete; it is retained only as defensive hardening, not described as the confirmed original cause.

## Recovery operation

The campaign runner gains an explicit `--recover-incomplete` mode. It:

1. validates the already-final campaign attestation and frozen local build;
2. verifies the append-only campaign ledger and lock;
3. requires the terminal state row to be exactly an unresolved `attempt_reserved`;
4. refuses to overwrite any existing completion artifact;
5. re-derives the completion solely from the existing attempt output using the same `_validate_attempt_output` path used during normal execution;
6. appends the completion artifact and `attempt_completed` state transition through the existing `complete_attempt` function;
7. re-verifies the complete campaign after writing.

The recovery mode accepts no credential target or rate-snapshot argument, instantiates no transport, and cannot make a provider request. It must be independently reviewed before Johnny runs it. Codex will not run it against the real campaign state during build or review.

Regression coverage must exercise repo-relative attestation and campaign paths through the real CLI-equivalent recovery surface and repo-relative paths through the future paid-attempt execution path.

## Stop boundary

Recovery is a distinct local mutation of the real append-only campaign record. Johnny must personally authorize and run the reviewed recovery command. A subsequent paid attempt remains a separate manual invocation under the already-authorized campaign and is forbidden until recovery has completed and both collaborators verify the recovered state.
