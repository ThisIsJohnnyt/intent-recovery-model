# Narrative-idiom diversification: a version-scoped system-prompt revision

**Date:** 2026-08-17
**Author:** Claude (diagnostic analysis + drafted wording), for Codex to build and Johnny to authorize.
**Status:** Proposal only. No live file edited, no pinned hash changed, no request sent, no spend. v1-v6's
`EXPECTED_LIVE_REQUEST_SHA256` (`8420c2d8...297b4` in `gate5_execution_gate.py`) and the current
`system_instruction.txt` (hash `339b6f78...e215`) are both untouched by this document.

## 1. Motivation — what the evidence actually shows

This project has sent 12 real requests total across v1-v6. Every one used the same schedule slot (1) and
mechanism card (M01) — the retry-campaign design has never advanced past slot 1, so we have **zero real
evidence about mechanism cards M02-M12**. Of those 12 requests: 8 hit a transient `503`, 1 hit `schema_invalid`,
and **2 reached a real HTTP 200 with actual generated content — both of which collided**, both on the exact
same field:

- v2, 2026-08-16: `proposed_output:output.narrative:protected_collision`
- V6 attempt 5, 2026-08-17: `proposed_output:output.narrative:protected_collision`

(Correction to an earlier internal summary that described these as hitting "different fields" — direct
inspection of both raw rejection-ledger records confirms both cite the identical field path.)

**Root cause, traced directly:**

M01's mechanism card instructs: *"an unresolved scheduling question... a pronoun whose referent remains
genuinely ambiguous."* `system_instruction.txt` assigns exactly this kind of content to `narrative`: "use
narrative for contextual state, observations, **uncertainty**, and incomplete thoughts." V6 attempt 5's
matched reference (`comparator:052:output.narrative`) reads: *"It is unresolved whether the room change was
confirmed with Jules or merely considered..."* Of the 85 narrative-field records in the comparator/protected/
acceptance/treatment_delta quarantine pools, 4 open with the near-identical template *"It is unresolved
whether X was Y or merely Z"* / *"It remains unclear whether..."* — a real, countable pattern, not
over-reading a coincidence.

This looks like a **narrow-idiom collision risk**, not evidence of verbatim memorization: the instructed
content (an unresolved either/or state) has a small natural-language solution space in English, and the
comparator pool — which is itself drawn from the project's own prior phase-2 gold candidates for the same
task — is already densely populated with the single most obvious phrasing of it.

## 2. Why this is a system-prompt change, not an M01-only card edit

The uncertainty-narrative instruction lives in `system_instruction.txt`, not the M01 card, and applies to
*any* mechanism card that asks for an unresolved/ambiguous state. Since M02-M12 have never been tested for
real, fixing only M01's card would leave the same risk latent for whichever card is tried next. A system-level
instruction addresses the general risk once.

## 3. Proposed text (exact diff against the current, still-live `system_instruction.txt`)

Insert one new bullet immediately after the existing `narrative` line in the `proposed_output must:` list
(currently line 18):

```diff
 - use narrative for contextual state, observations, uncertainty, and incomplete thoughts;
+- when narrative expresses an unresolved or ambiguous state, vary sentence structure and word choice each
+  time rather than defaulting to a fixed opening (for example, avoid routinely starting with "It is
+  unresolved whether" or "It remains unclear whether"); express the same required uncertainty in different,
+  natural phrasings;
 - use bullets for concise non-action facts, decisions, questions, and reference details;
```

Nothing else changes: no semantic requirement is removed or weakened, `source_input` rules are untouched, and
the collision screen itself (thresholds, quarantine pools, fatal-match logic) is completely unmodified. This
targets the generation side, not the safety screen.

## 4. Scoping — mirrors the v6 pattern exactly

Per Johnny's explicit direction: this must not touch the pinned v1-v6 request-hash verification.

- `system_instruction.txt` and the resulting prompt/request hash are **frozen, historical facts** for v1-v6 —
  `EXPECTED_LIVE_REQUEST_SHA256` stays exactly `8420c2d8...297b4`, referring to what was actually sent.
- Any real use of the revised wording needs its **own dedicated prompt artifact and its own freshly computed,
  separately pinned expected-request-hash constant** (e.g. `EXPECTED_LIVE_REQUEST_SHA256_V7` or equivalent,
  analogous to how V6 got its own scoped `PILOT_CEILING`/`RECONCILIATION_STOP` instead of touching V1-V5's).
- A regression test proving v1-v6's existing pin still validates unchanged after this addition exists (same
  pattern as the V6 ceiling-scoping regression test) is a hard requirement before this is considered built,
  not just proposed.

## 5. What this does and doesn't do

- Does: give the model more phrasing room to satisfy the same instruction without converging on the one idiom
  already saturating the comparator pool's narrative field.
- Does not: touch collision thresholds, quarantine pool contents, or any safety-relevant screening logic.
- Does not: authorize any real request. This is local-only text/build work, same tier as every prior
  local-only proposal in this project.
- Does not: resolve the M02-M12 evidence gap — that's a separate, larger decision (see Section 1) about
  whether to spend real attempts finding out whether this risk generalizes beyond M01.

## 6. Next step

Send to Codex to build as a new version-dedicated artifact (new prompt file or override mechanism, freshly
computed hash, regression test proving v1-v6 stay unaffected). Claude will independently review the build the
same way as every prior artifact in this project — hash recompute, direct test execution, and confirming by
hand that `EXPECTED_LIVE_REQUEST_SHA256` for v1-v6 is provably untouched. No execution authorized by this
document.
