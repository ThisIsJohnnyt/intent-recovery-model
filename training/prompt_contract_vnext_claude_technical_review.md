# Prompt Contract vNext — Claude's technical review

**Reviewing:** `prompt_contract_seed17_postmortem.md`, `prompt_contract_vnext_decision_proposal.md`,
`prompt_contract_vnext_evaluation_architecture.md`
**Date:** 2026-08-02
**Verdict: Aligned on the core direction (typed item markers), with two items flagged
before Layer 0 can be called complete.** No implementation or compute performed —
every finding below is a tokenizer/parser-level test or a direct data check, matching
the documents' own "no GPU training" scope.

## What I verified, and how

### Postmortem's factual claims — all confirmed exactly

- Zero newlines in every decoded output: checked all 53 records across all four
  seed-17 result files directly (`.count('\n')` on every `raw_output`). Confirmed:
  0/53 contain any newline. Matches the postmortem's claim exactly.
- Corpus distribution table: recomputed independently from
  `git show 8d7aa09:datasets/synthetic.jsonl` (the pinned 66-example gold_v1.2.2
  corpus). Bullet distribution `{1:4, 2:13, 3:24, 4:18, 5:6, 6:1}` and action
  distribution `{0:8, 1:24, 2:18, 3:8, 4:7, 5:1}` — both match the postmortem's table
  cell for cell, including the derived "17/66 have only 1-2 bullets" and the 1-6 /
  0-5 ranges.

### Decision proposal's feasibility gates — tested where testable without compute

**Gate 1 (Python tokenizer preserves exact number/spelling of typed markers): CONFIRMED.**
Tested the actual candidate shape from the proposal (`###BULLET###`/`###ACTION###`,
two of each, interleaved with narrative/section markers) through the real seed-17
checkpoint's tokenizer. Exact round-trip: 2/2 `###BULLET###`, 2/2 `###ACTION###`,
identical spelling. This is the same mechanism `###NARRATIVE###` etc. already rely on
successfully — not a new risk category.

**Gate 2 (browser tokenizer produces the same marker sequence): CONFIRMED for realistic
input, with one documented nuance.** Ran the identical test through the actual
production runtime (`@xenova/transformers`, loading the real deployed tokenizer files
from `thought-organizer-app/public/models/thoughtorganizer-flan-t5/`). The full-sequence
decode is byte-identical to the Python result — same marker counts, same text. One
real difference found and worth documenting: tokenizing `"###BULLET###"` in *complete
isolation* (not as part of a larger sequence) gives a different first token in Python
(includes a SentencePiece leading-space marker, `▁###...`) than in JS (no leading-space
marker). This doesn't affect the proposal, because the actual parsing approach operates
on *decoded text* (string-splitting on the literal delimiter), not on re-tokenized
substrings — but it's a sharp edge worth a one-line warning in the parser's own
comments, so nobody "fixes" a phantom discrepancy by testing isolated substrings later
and gets confused.

**Gate 6 (ordinary words "bullet"/"action"/hyphens don't cause false splits): CONFIRMED.**
Tested `"###BULLET### remember the bullet-point action items for the action movie
review ###ACTION### call about the action figure"` — decoded output is character-for-
character identical to the input. The literal marker string is distinguishable from the
bare English words because of the surrounding `###`, and that survives.

**Gate 9 (token budget): quantified, not just asserted — worth being explicit about the
real cost.** `###BULLET###` costs 7 tokens, `###ACTION###` costs 5 (measured directly,
not estimated). Worst case per the proposal's own eight-action ceiling case (7 bullets +
8 actions) = **89 marker tokens, ~30% of the 300-token `GENERATION_MAX_NEW_TOKENS`
budget.** Average case (using the actual corpus's mean 3.2 bullets / 1.8 actions) is
much lighter, ~31 tokens (~10%). Not a blocker — 300 tokens still leaves headroom even
in the worst case — but the proposal should say this number out loud rather than leave
"generation-token budgeting remains adequate" as an unverified assertion. It's now
verified, and it's fine, but it's not free.

**Gates 3, 4, 5 (parser byte-equivalence, empty-array parsing, fail-closed malformed
input): not directly testable — no parser exists yet on either side.** These are sound
requirements in principle and straightforward to implement as a small state-machine
splitter, but I'm not claiming to have verified them, since there's nothing to run yet.
Flagging as still-open, not as failed.

### One gate I don't think is actually resolved: Gate 7

**"Source notes containing marker-like literal text are escaped or otherwise isolated
so they cannot alter output parsing"** is listed as a required gate, but neither
document proposes a concrete mechanism for it — it's asserted as a requirement, not
satisfied by anything in the design. If a user's raw note contains the literal string
`"###BULLET###"` (unlikely, but not impossible — a developer testing the app, or
someone copy-pasting a code snippet into a note) and the model reproduces any of that
text in its output, a naive parser that just splits on `"###BULLET###"` would
misinterpret it as a structural boundary. This needs one of:
- sanitizing/escaping marker-like substrings in the *input* before it reaches the
  model, or
- a stricter parser that validates structural position (e.g., a `###BULLET###` is only
  a real boundary if it appears at an expected position in an expected count), or
- switching to a delimiter that's astronomically less likely to appear in ordinary
  user text than `###BULLET###` is (see below).

This isn't a reason to reject typed markers — it's a genuine open item that Layer 0's
"100% of fixtures pass" gate can't actually claim to cover until one of these exists
and has its own test.

## A design alternative I checked and don't think should be adopted, but is worth recording

While testing the tokenizer, I found this model's tokenizer has 100 genuine reserved
special tokens (`<extra_id_0>` through `<extra_id_99>`, standard T5 span-corruption
tokens), each of which is a single atomic token (vs. `###BULLET###`'s 7) and is a truly
reserved token, not literal text a user could type. On paper this looks like a stronger
delimiter choice than repeated literal markers. I tested it and found a real gotcha:
`run_benchmark.py` (and every other decode call in this project) uses
`skip_special_tokens=True`, which **silently strips `<extra_id_N>` tokens from decoded
output entirely** — confirmed directly (`'<extra_id_0>' in decoded` is `False` under
the current decode setting). Adopting `<extra_id_N>` markers would require coordinated
`skip_special_tokens=False` changes across every decode call in both repos, which is a
larger, easier-to-get-wrong blast radius than the literal-marker approach recommended
in the proposal. I agree with recommending typed literal markers over this alternative,
but wanted the alternative on record with the reason it was set aside, rather than
silently unconsidered.

## On the evaluation architecture (four-layer proposal)

No disagreement with the layer separation itself — cleanly separating "did the
boundary survive" (Layer 0), "did the model produce the right structure" (Layer 1),
"did the model produce the right content" (Layer 2), and "did anything regress"
(Layer 3) directly addresses the actual problem the seed-17 acceptance set had: a
single mixed pass/fail couldn't distinguish representation failure from semantic
failure. The `action_count_rule` being required (including explicit zero) closes the
same class of fail-open gap Round 3/4 already fixed for `required_semantic_dimensions`
— consistent with that precedent, not a new pattern.

One implementation note for whoever builds Layer 1's automated structural checks:
they should reuse `report_benchmark.py`'s existing `probe_passes()` machinery
(`required_semantic_dimensions`, capability checks) rather than building a parallel
scoring path — the fail-open gap that took four review rounds to close on the current
acceptance set will resurface if Layer 1's "computed, not manually typed as true"
checks are implemented as a second, divergent system instead of an extension of the
first.

## Summary

| Claim | Status |
|---|---|
| Postmortem's factual claims (zero-newline, corpus table) | Confirmed exactly |
| Typed markers round-trip in Python tokenizer | Confirmed |
| Typed markers round-trip in the actual browser runtime | Confirmed (full-sequence); one documented isolated-substring nuance |
| Ordinary words "bullet"/"action" don't cause false splits | Confirmed |
| Token budget is adequate | Confirmed, quantified (~30% worst case, ~10% average) |
| Source-text marker-collision escaping (gate 7) | **Not yet resolved** — needs a concrete mechanism, not just a stated requirement |
| `<extra_id_N>` special tokens as an alternative | Considered, correctly rejected — would require a wider `skip_special_tokens` change |

**Aligned** on typed item markers as the contract direction and on the four-layer
evaluation architecture. Recommend closing Gate 7 with a concrete mechanism before
calling Layer 0 complete. No implementation or compute proposed here — this is
technical review only, per the documents' own scope.
