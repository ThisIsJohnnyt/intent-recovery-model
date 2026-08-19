# Gate 5 third paid-pilot attempt proposal after protected-collision stop

**Date:** 2026-08-16  
**Status:** Proposal only. Johnny chose to prepare another separately reviewed fresh attempt with no design,
parser, threshold, schedule, or safety-control change. This document authorizes no credential access, provider
request, spend, candidate handling, staging, commit, or push.

## 1. Reason for a new attempt

The first fresh attempt successfully exercised the corrected request and parser against live Gemini output.
Slot 1 returned HTTP 200 and produced a structurally valid candidate. The unchanged mechanical screen then
rejected it for a protected-content collision at the persisted field path
`proposed_output:output.bullets:02:protected_collision`. The system stopped after one request, retained no
candidate, and did not expose candidate text.

This is not a parser, transport, model, schema, or infrastructure failure. Johnny chose to try the same frozen
pilot again to obtain an independently generated candidate. No collision threshold, protected corpus,
mechanical-screen rule, or fail-closed behavior may be weakened or bypassed.

The proposed run is a brand-new execution of the unchanged fixed 24-slot schedule starting at slot 1. It does
not append to, resume, or modify either earlier pilot directory.

## 2. Immutable historical pilot evidence

### Original failed pilot

- directory: `gate5_pilot_run_2026-08-16`
- summary file SHA-256: `627ba8dfba9410a1201907f7d5eb2cce69b2d9f41111cd8c4e84f540f1c16050`
- receipts file SHA-256: `b30e21d29868db74d9cee9719f2f8c1f002cc40ff1f5557224e658e3861e62c4`
- cost file SHA-256: `0c39db795f4ff4a75a199af8b0f8a11ffe08663d67a8148015dd8bd0a47703ae`
- rejection file SHA-256: `3b1cec5c6c37d0fce25b533a9ba890d3d44d7acc53e3bef9683ec13438634423`
- receipt row: `3db5178d10e4c5bfb556711bade9a25381ffffc5b63b78a9a3bef450546e3ee2`
- one request, zero candidates, 10,680 USD millionths conservatively booked

### Completed fresh attempt

- directory: `gate5_pilot_run_fresh_2026-08-16`
- reservation file SHA-256: `aa91f8d811adb31644b0d86021781bf7a97aa0658e1e03f2876fd8ccfc4cb970`
- summary file SHA-256: `16d624cc6b8d698bf3a34bce5f919eba38f9bc4babe7fc8ed50981568bcc9169`
- receipts file SHA-256: `fd290052ddeeec186b62d768f89122185509d94af72139ac85443bf79a8d4105`
- cost file SHA-256: `c90f5a8dd089d5a1e1e5f0b2a7c699346101ce24b84b1b47cc5713ca39f01413`
- rejection file SHA-256: `20db77f940829a50b4b06eae3bfe07f4e6539d89f4ea89f912444484341544d3`
- empty quarantine SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- receipt row: `34cb7d2f3ba34d5438b539f4d83581d7cc47c32203379d1d85616646f01453be`
- raw-response SHA-256: `3a5b4042346227912e83ba3a81945e3bc9e7d593f11518f7a65bdae7dbb3b86a`
- internally verified summary SHA-256:
  `312781bb40728c4e9cf0cdb756889b2d2be026db7d0736c04f2bb96944871821`
- exact terminal reason: `proposed_output:output.bullets:02:protected_collision`
- one HTTP-200 request, zero candidates retained, 10,680 USD millionths conservatively booked
- candidate text or response values persisted: none

All three fresh-attempt ledgers independently pass their hash chains, and the summary hash recomputes. These
files and the original failed run must remain byte-identical.

## 3. Historical cost carry-forward

The aggregate historical pilot cost is now exactly:

- original failed pilot: 10,680 USD millionths
- completed fresh attempt: 10,680 USD millionths
- total carried forward: **21,360 USD millionths ($0.02136)**

The third-attempt runner must represent these as two explicit immutable components and a checked total. Neither
component may be omitted, reset, or silently collapsed without retaining its evidence link.

Every pre-request reservation decision must use:

`21,360 historical pilot cost + third-run cumulative cost + next worst-case reservation`

Every hard-ceiling decision and output summary must also use the 21,360 historical total. The $2.25
reconciliation stop and $3.00 hard ceiling remain unchanged. The frozen 24-slot worst-case reservation remains
204,000, so historical plus fresh worst case is 225,360 USD millionths ($0.22536), below both controls.

Diagnostic and compatibility-check spending remains outside the pilot ledger under its separately authorized
budget, exactly as previously recorded.

## 4. Unchanged execution and safety surface

- exactly the existing 24-slot two-model schedule, beginning at slot 1
- corrected response parser unchanged and still pinned
- one candidate, nonstreaming, low thinking, structured output
- no retries, redirects, substitutions, fallback, tools, caching, or automatic resume
- protected/collision corpus and all exact, containment, token-Jaccard, and character-5gram thresholds unchanged
- first fatal mechanical-screen finding stops the run
- candidates can enter only the brand-new quarantine pending later independent review
- no candidate promotion, review decision, corpus mutation, staging, commit, or push during execution
- original failed run, completed fresh run, and response-shape campaign remain immutable

## 5. Required build changes

Before any third attempt, the gate, template, runner, and tests must be hardened so that:

1. this proposal and all completed-fresh-attempt artifact hashes above are pinned;
2. the completed fresh attempt is independently revalidated: all chains, internal summary hash, reservation,
   exact HTTP-200/collision result, zero-byte quarantine, no retained candidate, and 10,680 booked cost;
3. the existing original failed-pilot verifier remains required;
4. historical cost is represented as original 10,680 + completed-fresh 10,680 = checked total 21,360;
5. every reconciliation and hard-ceiling calculation uses 21,360 plus third-run cost;
6. reservation, cost rows, and summary separately report both historical components, total historical cost,
   third-run cumulative cost, and aggregate pilot cost;
7. corrected parser, terminal response-shape campaign, contract, schema, schedule, rate snapshot, and both
   model-success receipts remain pinned and verified;
8. the output directory is new and reserved before credential access;
9. any evidence, cost-total, parser, attestation, or output-path mismatch stops before credential access and
   provider use.

Tests must adversarially prove that either historical component cannot be changed/dropped, the 21,360 total
changes the exact reconciliation boundary, old filled attestations fail, the completed fresh attempt remains
immutable, and the unchanged protected-collision screen still stops a colliding synthetic candidate.

## 6. Review and authorization sequence

1. Claude independently reviews this proposal and its historical pins/cost math.
2. Codex builds the local-only gate/runner/template/test hardening.
3. Claude independently reviews source, hashes, tests, evidence immutability, cost boundaries, and tamper cases.
4. Fresh same-day setup/activity/evidence/scope facts are confirmed directly with Johnny.
5. Codex drafts a new attestation with execution authorization set to `false`; Claude verifies it.
6. Johnny separately and explicitly authorizes the real third attempt after the reviewed build and draft are
   available.
7. Codex finalizes the attestation; Claude verifies it.
8. Johnny alone runs the command using the locally stored credential. Neither AI touches the credential or
   triggers execution.
9. Both agents verify all resulting evidence before any candidate review or later decision.

No request, threshold change, parser change, candidate review, corpus mutation, staging, commit, or push is
authorized by this proposal.
