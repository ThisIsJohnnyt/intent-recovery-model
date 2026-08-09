# Seed-17 Phase-2 P2-D Postmortem — Evidence Packet (Claude)

**Date:** 2026-08-06
**Scope:** Read-only repository evidence for probes 06, 09, 13, and the primary/control (720/600)
relationship, per ChatGPT's proposed postmortem framework and Johnny's authorization to proceed
with evidence assembly. No training, inference, corpus edits, seed 73, or any other compute
performed to produce this packet — everything below is drawn from files already on disk: the
committed R2 replay's own scored results, the committed Phase-2 outcome record's artifacts, the
frozen corpus derivation files, and the actual processed training file.
**Not a synthesis.** Candidate explanations are flagged as such, for ChatGPT's postmortem to
evaluate, confirm, or challenge — not asserted conclusions.

## 1. Probe 06 (`multi_person_attribution`) — R2 baseline vs. Phase-2

| | Narrative resolves "who asked" to | Bullet "who asked" | Result |
|---|---|---|---|
| **R2 baseline** | ambiguous ("...after **she** asked about it") | *(no such bullet generated at all)* | **Pass** |
| **Phase-2 primary (720)** | **Rowan** ("...after **Rowan** asked about it") | "**Rowan** had asked about the permit" | **Fail** |
| **Phase-2 control (600)** | ambiguous ("...after **she** asked about it") | "**Rowan** had asked about the permit" | **Fail** |

R2 never generated a "who asked" bullet at all — the misattribution has no R2 precedent to
regress *from* in that field; it's new content in Phase-2's output shape. Both Phase-2 runs
independently produce the identical bullet text `"Rowan had asked about the permit"`, byte-for-byte
— confirmed by direct string comparison. This bullet-level defect is stable across the last 120
training steps (present at both step 600 and step 720); only the *narrative* field differs between
control and primary, and only primary's narrative additionally regresses.

### Candidate explanation: a structurally-analogous, correctly-labeled training example that may have been overgeneralized

The 66-record parent corpus (unchanged between R2 and Phase-2) contains three
`multi_person_attribution` examples. One, difficulty `hard`, is structurally near-identical to
probe 06 itself:

> **Input:** "Rina told Marcus the draft was approved after he asked about it. He still needs the
> signed copy, but I can't tell whether 'he' means Marcus or the client. Ask Rina who needs it."
>
> **Gold target narrative** (confirmed present byte-for-byte in the actual
> `data/processed_gold_v1.2.2_phase2_v2contract_seed17/train.jsonl` used for both runs): "Rina told
> Marcus that the draft was approved after **Marcus** asked about it. The note does not make clear
> whether Marcus or the client still needs the signed copy. Rina should be asked who needs it."
>
> **Gold target bullets** include: "**Marcus** had asked about the draft"

**Correction from cross-review, independently re-verified against both texts:** this is *not* a
mislabel. The explicit ambiguity flag ("I can't tell whether 'he' means Marcus or the client")
names its two candidates as **Marcus or the client** — not Rina or Marcus — so it attaches to the
second sentence ("He still needs the signed copy"), which the gold correctly preserves as unresolved
("does not make clear whether Marcus or the client..."). The *first* "he" ("after he asked about
it") is a separate, unflagged resolution question, and gender agreement makes Marcus (not Rina, a
female-conventional name) the only sensible referent — reasonably resolved, not confidently
misresolved. Probe 06's own input has the identical structure: its explicit flag names its two
candidates as **Tessa or the inspector** — not Tessa or Rowan — confirmed by direct comparison of
the probe's own `input` field. So the rubric's "may resolve the earlier 'she asked' to Tessa via
ordinary nearest-antecedent reading" is *also* a separate, gender-driven resolution (she → the
clearly-female name, Tessa; Rowan is gender-ambiguous), structurally parallel to Rina/Marcus, not
inconsistent with it.

What both Phase-2 runs actually get wrong is resolving "she" to **Rowan** — the gender-ambiguous
name — rather than Tessa, the gender-matching one. Rina/Marcus is a plausible source of an
*overgeneralized* pattern (e.g. "resolve this kind of pronoun to the second-named/most-recently-
mentioned person") that the model may have picked up instead of the correct gender-agreement rule —
a real candidate contributor, but not because its own gold label was wrong. This training example is
present, unchanged, in both R2's and Phase-2's training data — R2's checkpoint did not exhibit this
generalization; Phase-2's did.

## 2. Probe 09 (`open_question_preservation`) — control-only regression

| | Behavior | Result |
|---|---|---|
| **R2 baseline** | volunteer list left as an unresolved/incomplete reference ("it is unclear what yet") | **Pass** |
| **Phase-2 primary (720)** | volunteer list stays an incomplete thought (`INCOMPLETE_THOUGHT_REMAINED_INCOMPLETE: true`) | **Pass** |
| **Phase-2 control (600)** | invents a specific new question ("whether the volunteer list was sent to Imani") not present in the source (`INCOMPLETE_THOUGHT_REMAINED_INCOMPLETE: false`) | **Fail** |

This is the inverse direction from probe 06's narrative: here, the step-600 checkpoint exhibits the
defect and the step-720 checkpoint has converged back to R2-matching, correct behavior. More
training steps helped probe 09 and hurt probe 06's narrative field in the same 600→720 stretch —
the relationship between step count and correctness is not monotonic across probes.

## 3. Probe 13 (`two_unrelated_tasks`) — repaired in both runs

| | Actions returned | Result |
|---|---|---|
| **R2 baseline** | only `["Pick up cat food after work"]` — the email task is silently dropped from actions despite appearing in narrative/bullets | **Fail** (`topic_completeness=1`) |
| **Phase-2 primary (720)** | `["Pick up cat food after work", "Email the signed form to the school"]` — both present | **Pass** |
| **Phase-2 control (600)** | same, both present | **Pass** |

### Curriculum coverage directly targets this exact category

The 12-record Phase-2 curriculum addition contains **zero** `multi_person_attribution` records and
**two** `two_unrelated_tasks` records (bringing that category from 1 parent-corpus example to 3
total — a 3× increase). Confirmed two ways: via the frozen, fingerprint-pinned candidate corpus, and
— since candidate-corpus membership alone isn't training exposure — by direct substring match of
both added records' input text against the **realized `train.jsonl` split actually used by both
runs**: both are present in `train.jsonl`, neither in `val.jsonl`. See the evidence supplement §0/§B
for the full per-record split membership of all 12 additions, not just these two.

| Category | Parent (66, R2 = Phase-2 unchanged) | New in 12-record curriculum | Total in Phase-2 training data |
|---|---:|---:|---:|
| `two_unrelated_tasks` | 1 | +2 | 3 |
| `multi_person_attribution` | 3 | +0 | 3 |

One added example directly demonstrates the fix pattern:

> **Input:** "Drop off the repaired headphones while the copy center is open; volunteer roster
> needs uploading before bed."
> **Gold action_items:** `["Drop off the repaired headphones while the copy center is open.", "Upload the volunteer roster before bed."]` — both tasks present, unmerged, undropped.

Probe 13's repair has direct, proportionate training-data support (its category's representation
tripled with examples demonstrating exactly the previously-missing behavior). Probe 06's regression
has no analogous direct cause in its own category (zero net change in `multi_person_attribution`
training data) — consistent with §1's candidate explanation being an indirect/interference effect
rather than a direct consequence of any new example.

## 4. Primary/control structural relationship

Confirmed via direct hash comparison: primary and control were trained on **byte-identical** data —
`data/processed_gold_v1.2.2_phase2_v2contract_seed17/train.jsonl` and `val.jsonl`, same seed (17),
same shared configuration (batch size 4, learning rate 3e-4, weight decay 0.01), per the receipt's
own `shared_configuration` block. The *only* declared difference is `--max-steps 600` on control vs.
natural (epoch-limited, reaching 720) on primary. 72 train records ÷ batch size 4 = 18 steps/epoch;
600 steps = 33.33 epochs, 720 steps = 40.0 epochs exactly. Control is not a differently-trained
model in the sense of different data, seed, or hyperparameters — matched declared conditions, run as
a separate subprocess each. **This is a paired training-horizon comparison, not a proven single
trajectory**: `train.py` sets only `Seq2SeqTrainingArguments(seed=..., data_seed=...)`, with no
deterministic-execution flags, and per-step loss comparison (evidence supplement §C) shows the two
runs track closely but are not bit-identical (mean abs. difference 0.004 across 120 matched points)
— consistent with ordinary GPU non-determinism under matched conditions, not proof of one continuous
run. Final-batch training loss: primary 0.0087, control 0.0076 (both near-converged); mean
`train_loss` over the full run: primary 0.102, control
0.121 — the expected direction for more steps, unremarkable.

## 5. What this packet does not establish

- Whether the "Rina/Marcus" gold-label pattern is the sole or dominant cause of probe 06's
  regression, versus a contributing factor among several (e.g. general effects of a differently
  composed/larger training set on generalization) — this packet found the pattern and confirmed its
  exact presence; it did not run any additional training or ablation to isolate its causal weight,
  which would require compute not authorized in this phase.
- Whether other `multi_person_attribution` probes (not part of gate 6's required set) show the same
  regression — not checked here since gate 6 is defined only over the 13-probe protected set;
  worth a targeted look if the postmortem wants it.
- Any claim about what a revised curriculum should contain — that is the postmortem's synthesis
  question, not this packet's.

## 6. Non-authorizations (unchanged)

No training, inference, corpus mutation, export, deployment, activation, or seed 73 occurred or is
proposed by this packet. This document is not committed pending Johnny's review.
