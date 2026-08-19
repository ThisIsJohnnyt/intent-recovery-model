# Corpus retrospective audit — 2026-08-18

**Findings-only.** Nothing in this document is a proposed fix, and nothing
was mutated, gated, or flagged for remediation by running it. It exists to
answer one question: *now that Gemini candidates get real rigor before they
can touch the corpus, does the corpus that rigor is measured against hold up
to the same rigor, given none was applied to it at the time it was built?*

**Cost: $0.** Zero API calls, zero network access, zero corpus mutation —
this is `gate2.py`'s own already-tested collision/secret-scan logic applied,
read-only, to files that already exist. Script:
[`corpus_retro_audit_2026-08-18.py`](corpus_retro_audit_2026-08-18.py). Raw
data: [`corpus_retro_audit_2026-08-18_findings.json`](corpus_retro_audit_2026-08-18_findings.json).

## Scope

| Target | File | Records | Flattened fields |
|---|---|---|---|
| Bulk training pool | `datasets/synthetic.jsonl` | 72 | 490 |
| `comparator` pool | `training/gold_v1.2.2_phase2_derived_candidate.jsonl` | 78 | — |
| `protected` pool (held-out) | `datasets/benchmark/gold_v1.2.1_probes.jsonl` | 16 | — |
| `acceptance` pool | `datasets/benchmark/source_determined_items_v2_acceptance_draft.jsonl` | 10 | — |
| `treatment_delta` pool | `training/regression_balanced_repair_proposal.jsonl` | 7 | — |
| **Combined reference pool (gate2.py's own)** | — | **111** | **1,007** |

**Scoping note surfaced by the audit itself:** the `comparator` pool is not
independent content — it's the same 72 synthetic records restated with
extra `v1_target`/`v2_target` fields, plus 6 more. Auditing "the comparator
pool" and "the bulk training pool" turned out to be almost the same
exercise, not two separate ones. That's fine for its actual job (screening
Gemini output for duplication), but worth knowing before reading the
duplicate-count numbers below.

## Finding 1 — Schema contract mismatch (quantified, real)

`DATASET_SPEC.md` and `response_schema.json` (the live Gemini structured-
output contract) actively disagree, and the existing corpus is full of
records that prove it:

- **9 of 72 synthetic records (12.5%)** have `action_items: []` — explicitly
  correct per `DATASET_SPEC.md` ("empty array when the input has none —
  never invent one"). Every one of them would fail `response_schema.json`'s
  `action_items.minItems: 1` if ever validated against it.
- **5 of 72 synthetic records (~7%)** have exactly 1 bullet — explicitly
  correct per `DATASET_SPEC.md` ("a one-idea input gets one bullet"). Every
  one would fail `response_schema.json`'s `bullets.minItems: 2`.
- 2 comparator-only records (`comparator:073`, `comparator:074`) have 7 and
  8 action_items respectively, exceeding `response_schema.json`'s max of 6.
- Zero records violate `DATASET_SPEC.md`'s own stated bounds (bullets ≤ 7).

This isn't a corpus defect — the corpus is internally consistent with its
own documented contract. It's a **latent schema gap between the training
contract and the Gemini generator's output contract**, sitting there
unnoticed until this check ran. Roughly a fifth of the existing corpus
(14/72 records) would never have passed through the Gemini pilot's own
validator if it had been generated that way.

## Finding 2 — Secret/PII exposure: clean

Zero hits across all ~1,500 combined text fields for the same
`SECRET_KEY_RE` / `BEARER_RE` / `GOOGLE_KEY_RE` patterns that hard-stop a
live paid Gemini run. No further action indicated.

## Finding 3 — Internal near-duplicate audit

Raw pairwise count: **14,431 hits** across 1,497 combined fields. That
number is not directly meaningful — most of it is boilerplate/categorical
label overlap (`likely_failures` vs. `required_semantic_dimensions`,
`primary_checks`, `status`, `id`, etc. — short enum-like strings that are
*supposed* to repeat across probes) and the already-noted comparator≈
synthetic overlap. Restricting to genuine content fields
(`input`/`narrative`/`bullets`/`action_items` on both sides) brings it to
**7,760**, and breaking that down by what it actually contains changes the
picture substantially:

- **`comparator` vs `synthetic`: 5,263 hits.** Expected — same content,
  restated (see scoping note above). Not a new finding.
- **`synthetic` vs `synthetic`: 1,025 hits, but on inspection nearly all
  are short common-task phrase coincidences**, not duplicated examples —
  e.g. `"Pick up dry cleaning"` / `"Pick up dry cleaning before six"`
  (0.79 char-5-gram), `"Call dentist Tuesday"` / `"Call the dentist"`
  (0.67 token-Jaccard), `"Buy milk"` appearing verbatim in two unrelated
  grocery-list examples. Only **4 exact-text matches** exist in the whole
  72-record pool, and all 4 are the same two-word phrase (`"Buy milk"`)
  reused across two different mundane list examples — not concerning for a
  domain that's inherently full of common errands.
- **`protected` (held-out) vs `synthetic`/`comparator`: 36 + 31 = 67 hits,
  and this is the one genuinely new, non-trivial finding.** At least 3
  specific held-out probes are near-template paraphrases of specific
  training records — same sentence skeleton, swapped nouns:
  - `protected:006` ↔ `synthetic:048`/`comparator:048` — 0.476 token-Jaccard.
    *"Rina told Marcus the draft was approved after he asked about it..."*
    vs. *"Tessa told Rowan the permit was approved after she asked about
    it..."* — identical clause structure, swapped names/objects.
  - `protected:005` ↔ `synthetic:051` — 0.214 token-Jaccard, same pattern
    (two-party attribution + ambiguous pronoun + photo/document task).
  - `protected:016` ↔ `synthetic:056` — 0.4 token-Jaccard, shorter but same
    templated skeleton (*"Remember to ask her/them about the earlier
    version/other one."*).
  
  Exact-match / containment level: **zero** — these are structural/template
  matches, not verbatim leaks. But `protected` exists specifically as a
  *held-out* set for evaluating generalization independent of what the
  model trained on. A probe built from the same sentence template as a
  training example tests pattern-matching on that template more than it
  tests genuine recovery skill — worth knowing about for at least these 3
  of the 16 protected probes.
- All other pool-pairs (`acceptance`, `treatment_delta` cross-comparisons):
  low counts (≤99 each), dominated by the same short-phrase-coincidence
  pattern as the synthetic-internal numbers above — nothing flagged as
  noteworthy on inspection.

## Finding 4 — Diversity stats (descriptive only)

`synthetic.jsonl` (72 records): 45 distinct categories (mostly 1–3 examples
each; `interrupted_thought_depth` and `open_question_preservation` are the
largest at 6 each, ~8% of the corpus apiece — mild concentration, not
alarming at this scale). Difficulty spread: easy 12 / medium 22 / hard 25 /
expert 13 — reasonably even, skewed toward harder examples if anything.
Input length: 3–56 words, median 25. No distribution here looks skewed
enough to flag as a real problem; full numbers are in the JSON if useful.

## Bottom line

- No corpus-invalidating defect. Nothing here supports "start over."
- One concrete, fixable **contract gap**: `response_schema.json` vs.
  `DATASET_SPEC.md` disagree on `action_items` (0 vs. ≥1) and `bullets`
  (1 vs. ≥2), and it's not hypothetical — 14/72 real corpus records sit in
  the gap.
- One concrete, non-obvious **methodology finding**: at least 3 of the 16
  `protected` held-out probes are template-level paraphrases of specific
  training records, which softens their value as an independent
  generalization check for those specific 3.
- Everything else checked (secrets, internal duplication, diversity) came
  back clean or benign on inspection, not just on raw counts.

No action taken on any of this — reporting only, as scoped.
