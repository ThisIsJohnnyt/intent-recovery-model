# Phase-2 Contrastive Attribution / Field-Role Design — Claude Cross-Review

**Date:** 2026-08-09
**Scope:** Read-only cross-review of `phase2_contrastive_attribution_field_role_design_proposal_chatgpt.md`
§11's eight required items. No corpus records created, no processed splits derived, no compute, no
commit/push. This is analysis of a design, not an implementation.

**Provenance note:** both new documents from this round hash differently on my end than the
citations given — same pattern as the framework document earlier in this postmortem (visible `â`
mojibake in the pasted text, indicating typographic Unicode I couldn't reconstruct byte-for-byte).
Proposal: mine hashes `bbd02091c896016a302929f9ec2ac53b8f1d04d7d5f0710a999033e141ed8477`, cited
`1bce18134...`. Decision memo (saved now since it was never written to disk in my prior turn):
mine hashes `82575badb491e1b767740314af985dd460ea6716065c8572e7b760b3ade2396c`, cited `0c6260b08...`.
Flagging per established practice; treating as the same benign, already-resolved class of
discrepancy as before, and proceeding on content.

## 1. Exact repository IDs for frozen records and remediation targets

Neither corpus file carries an explicit `id` field (schema is `['input', 'output', 'difficulty',
'category', ...]`), so identity is by file + line number + content, matching how this project has
always disambiguated these records. All five located and confirmed present in both the human-readable
corpus file and (for the two that matter for training) the actual processed `train.jsonl`:

| Record | `phase2_balanced_curriculum_proposal.jsonl` line | `gold_v1.2.2_phase2_derived_candidate.jsonl` line | In `train.jsonl`? |
|---|---:|---:|---|
| Rina/Marcus (`multi_person_attribution`, hard) | — (parent corpus, not a proposal addition) | 48 | Yes (confirmed earlier this postmortem) |
| `two_unrelated_tasks` addition #1 (headphones/roster) | 11 | 77 | Yes |
| `two_unrelated_tasks` addition #2 (equipment crate/costume box) | 12 | 78 | Yes |
| `cross_field_completeness` addition #9 (open house) | 9 | 75 | Yes |
| `cross_field_completeness` addition #10 (gate code) | 10 | 76 | Yes |

All five confirmed present, unchanged, in `train.jsonl`; none in `val.jsonl` — re-verified this
session, not carried forward from memory.

## 2. Schema-level mapping, AT-C1 through AT-C4 (no records written)

The reviewed schema (confirmed in `prepare_phase2_candidate_corpus.py`'s own static check) is
`['category', 'difficulty', 'input', 'output']` at the top level, with `output` itself an object
containing `narrative`, `bullets`, `action_items`.

| Field | AT-C1 | AT-C2 | AT-C3 | AT-C4 |
|---|---|---|---|---|
| `category` | `multi_person_attribution` | same | same | same |
| `difficulty` | **not specified anywhere in the proposal** | same gap | same gap | same gap |
| `input` | given as prose | given as prose | given as prose | given as prose |
| `output.narrative` | described by required-behavior table, not literal text | same | same | same |
| `output.bullets` | described, not literal | same | same | same |
| `output.action_items` | described, not literal | same | same | same |

**Gap found:** none of the four candidates specifies a `difficulty` value. The existing schema
requires one (the prior 12-record proposal's own static review explicitly checked this field), and
the three existing `multi_person_attribution` records span `medium`/`hard`/`expert` — no `easy`
example exists in that category today. This is a concrete, fixable gap for the next design pass, not
a blocker: AT-C1–AT-C4's own descriptions suggest at least `medium`–`hard` (two named people, one
pronoun, gender-cue reasoning) up to `hard`–`expert` for AT-C3 (two separate pronoun-resolution
decisions in one item, the same shape as Rina/Marcus's `hard` rating and probe 06 itself).

## 3. Exact current vs. proposed disposition, additions #9 and #10

Pulled directly from the corpus (not summarized from the earlier evidence supplement):

### Addition #9 (open house)

| Content | Current disposition | Proposed disposition |
|---|---|---|
| "Ren said Salma handed the spare clips to the installation lead" | Present in narrative **and** as its own bullet | Narrative only, unless a decision-relevant role is established |
| "It is still unknown whether the west window was measured or only photographed" | Present in narrative **and** as its own bullet | Bullet retained only if review establishes a required uncertainty/decision role; otherwise narrative only |
| "The folding screens looked uneven after setup" | Present in narrative **and** as its own bullet | Narrative only; not eligible for a standalone bullet as a bare observation |
| Actionable content (upload floor plan, call lighting supplier) | Bullets + actions | Unchanged |

### Addition #10 (gate code)

| Content | Current disposition | Proposed disposition |
|---|---|---|
| "Jae reported that the security vendor changed the north gate code" | Present in narrative **and** as its own bullet | Narrative only, unless decision-relevant |
| "It is still unknown whether the vendor tested the backup keypad" | Present in narrative **and** as its own bullet | Bullet retained only with a contract-based uncertainty role; otherwise narrative only |
| "The lobby smelled like fresh paint this morning" | Present in narrative **and** as its own bullet | Narrative only |
| Actionable content (pack banners, send access map) | Bullets + actions | Unchanged |

Both records' proposed dispositions are internally consistent with the stated field-role rule
(§3.2 of the proposal) and with each other — same three-pattern shape in both.

## 4. Duplication, near-twin, and benchmark-leakage findings

4-gram lexical overlap sweep (candidate `input` text vs. all 78 existing corpus records, all 16
protected probes, all 10 acceptance probes):

- **Zero overlap** with protected-16 or acceptance-10 in all four candidates — no leakage risk.
- **AT-C1, AT-C3, AT-C4** each share exactly one 4-gram with the corpus (`"was approved after he"`,
  from Rina/Marcus) — a short structural echo consistent with intentional analogy, not duplication.
- **AT-C2** shares zero 4-grams with anything in the corpus or either benchmark.
- **AT-C1 vs. AT-C4** (the intentional order-swapped pair): 25 of 28 4-grams shared, confirmed **not
  byte-identical** (different name order changes the opening and several downstream spans). This
  satisfies the proposal's own gate ("permitted semantic counterparts but must not be accidental
  duplicates after normalization") — the near-total overlap is the intended design, not a defect.

**AT-C3 vs. Rina/Marcus and probe 06, checked with the extra scrutiny the proposal itself calls
for:** only the same single 4-gram as the other candidates. AT-C3's actual structural risk isn't
lexical — it's that it reintroduces the *same* two-pronoun-with-a-later-flagged-ambiguity shape as
both Rina/Marcus and probe 06 itself, by design (that's the "mixed boundary" case the contrast set
needs). This is intended, not accidental leakage, but worth naming explicitly: AT-C3 is the
candidate most structurally similar to the actual probe it's meant to help fix, which is exactly
why it needs the most careful semantic review in static review (per the proposal's own §9 gate).

## 5. Name-order, pronoun-cue, difficulty, and surface-form balance

- **Name reuse found:** "Maya" (AT-C1, AT-C4) already appears in the existing Maya/Theo
  `multi_person_attribution` record. Not a duplication (different scenario, different resolution
  target), but three `multi_person_attribution` examples using "Maya" (existing Maya/Theo, new
  AT-C1, new AT-C4) risks the model associating the *name itself* with "gets resolved" rather than
  learning the general gender/evidence rule the design intends. A different name for AT-C1/AT-C4
  would remove this ambiguity at no cost to the design.
- "Priya" (AT-C3) also exists elsewhere in the corpus, but in an unrelated category
  (`interrupted_thought_multi_topic`) — much lower concern, likely fine.
- Gender-cue balance across the four cases is real, not merely claimed: AT-C1/AT-C4 use a clear
  male/female pair (Owen/Maya), AT-C2 deliberately uses a gender-neutral pronoun ("they") with two
  non-disambiguating names (Casey/Morgan — both usable for any gender), and AT-C3 uses a clear
  male/female pair (Joel/Priya) for its resolvable pronoun. This does exercise different resolution
  cues, not just repeats of the same gender-matching trick — consistent with the proposal's own
  claim in §6.
- Difficulty balance cannot be assessed — see §2's gap. No stated difficulty for any candidate.

## 6. Split feasibility under the unchanged split policy

**Not feasible without a code change**, and the proposal's own §8 anticipates exactly this case
("If the existing split policy cannot realize that membership without code or policy changes, work
must stop for a separate decision").

`prepare_phase2_candidate_corpus.py` hard-pins, and fail-closed asserts on:

```
EXPECTED_PROPOSAL_FINGERPRINT = "1f32f38d..."   # hash of the exact 12-record proposal file
EXPECTED_PROPOSAL_COUNT = 12
EXPECTED_CANDIDATE_COUNT = 78                    # 66 + 12
```

with `raise SystemExit(...)` if the proposal file's record count or fingerprint don't match exactly.
A 4-record proposal would fail this script's own preflight immediately, by design — it cannot append
"4 new records" without those three constants (and the derived candidate/split fingerprints
downstream) being deliberately updated for the new proposal. This is a **script constant change**,
not a change to the underlying split *algorithm* (append new records to train only, keep the R2 val
split frozen) — that algorithm itself would handle 4 records the same way it handled 12. But it is,
concretely, a code change to a currently frozen, fingerprint-pinned file, which the proposal's own
§4 table lists as "no changes... during design." Recommend this be named explicitly as an accepted,
narrowly-scoped exception (updating three pinned constants and the corresponding fingerprints to
match a new, smaller, separately-reviewed proposal file) rather than left implicit, when this design
moves to implementation.

## 7. Disagreements with the semantic targets or change budget

No disagreement with the four-case design's semantic logic, the field-role remediation design, or
the change budget's limits (4 new records, 2 target-only revisions, 0 deletions, 0 benchmark
changes) — all consistent with the corrected postmortem findings this proposal is built on.

Two concrete, fixable gaps, not disagreements with the approach:

1. **Missing `difficulty` field** on all four candidates (§2) — required by the existing schema,
   absent from the design.
2. **"Maya" name reuse** across three `multi_person_attribution` examples (§5) — recommend a
   different name for AT-C1/AT-C4 to avoid a name-specific (rather than rule-general) association.

One precision item, not a disagreement:

3. **Split-policy language should be qualified** (§6) — "no split-policy changes" is correct at the
   algorithm level but the derivation script's pinned constants will need updating for any
   differently-sized proposal file. Worth stating explicitly rather than leaving as an implicit
   exception when implementation is authorized.

## 8. Recommendation

**REVISE — not reject.** The core design (four-case attribution contrast, field-role constraints on
additions #9/#10, frozen invariants, change budget, gate structure) is sound, evidence-consistent,
and requires no further architectural rework. The three items in §7 are small, mechanical fixes
(add a difficulty field to each candidate; rename one person in two candidates; state the
split-derivation-script exception explicitly) that a revised draft can resolve without another full
design cycle. Recommend returning these three items for the next design pass before advancing to
corpus-record drafting.

## Non-authorizations (unchanged)

No corpus records, processed splits, tests, or execution artifacts were created by this review. No
training, inference, corpus edits, seed 73, commit, or push. Not committed pending review.
