# Seed-17 Phase-2 P2-D Postmortem — Evidence Supplement (Claude)

**Date:** 2026-08-07
**Scope:** The four bounded, read-only checks from ChatGPT's
`phase2_seed17_p2d_postmortem_framework_chatgpt.md` §5 (A–D), plus the two precision corrections
requested for the original evidence packet. No training, inference, corpus edits, seed 73, or any
other compute performed. Not a synthesis — candidate explanations remain flagged as such.

**Note on the framework document's hash:** I recomputed `phase2_seed17_p2d_postmortem_framework_chatgpt.md`
as saved from the pasted text and got `25ee5514a950c7f01474443f3824015d2e83dc7e6fdef586e1f0a88539704a0a`,
not the claimed `e3a8b6838855bd3173c010735b4c1dcb907aa2367fce9591e7bb2019cfd1d86f`. The source text as it
reached me contained visible mojibake (e.g. `â` where an em/en-dash or curly quote belongs, `Ã` for
`×`, `Â§` for `§`) — the same class of corruption this project has caught before in pasted documents.
I reconstructed clean punctuation rather than preserve the corrupted bytes, which is almost certainly
why the hash doesn't match ChatGPT's original. The content is unambiguous and I've worked from it
as intended, but I can't currently certify byte-identical provenance for that file the way I could
for the evidence packet (whose hash matched ChatGPT's claim exactly). Flagging this rather than
silently treating it as resolved.

## 0. Two precision corrections to the original evidence packet

1. **"Paired training-horizon comparison," not "same trajectory."** All uses of "sampled 120 steps
   earlier" / "same training trajectory" language in the original packet should be read as informal
   shorthand, not a proven claim. §3 below establishes exactly what can and can't be shown.
2. **Curriculum count bound to the realized train split.** Confirmed directly against
   `data/processed_gold_v1.2.2_phase2_v2contract_seed17/train.jsonl` (not just the frozen candidate
   corpus): all 12 curriculum additions — including both `two_unrelated_tasks` records — are present
   in `train.jsonl` and absent from `val.jsonl`. The `two_unrelated_tasks` 1→3 realized-train-split
   increase is now directly confirmed, not inferred from candidate-corpus membership.

## A. Attribution-label consistency audit

All three `multi_person_attribution` training records (unchanged, present in both R2's and Phase-2's
train split — confirmed by direct substring match against `train.jsonl`, none in `val.jsonl`):

| Difficulty | Source ambiguity | Gold resolution | Consistent with probe 06's rubric? |
|---|---|---|---|
| medium (Maya/Theo) | None genuine — "Ask Maya whether Theo already forwarded it" has no ambiguous referent; "it" clearly means the confirmation email. | N/A — nothing to resolve. | Not applicable; not a comparable case. |
| **hard (Rina/Marcus)** | The input contains *two* pronoun-resolution questions: (1) "after **he** asked about it" (unflagged), and (2) "**He** still needs the signed copy, but I can't tell whether 'he' means **Marcus or the client**" (explicitly flagged, and *not* a Rina-vs-Marcus question — its two named candidates are Marcus and an unmentioned "client"). | Gold resolves question (1) to Marcus via gender agreement ("he" ≠ Rina, a female-conventional name) — a separate, unflagged, reasonable resolution. Gold preserves question (2) correctly: *"does not make clear whether Marcus or the client still needs the signed copy."* | **Yes**, correctly labeled. Corrected from an earlier read of this packet, which had wrongly conflated the two pronoun questions and treated the flagged Marcus-or-client ambiguity as though it covered the earlier "who asked" resolution too. Probe 06's own input has the identical two-question structure — its flagged candidates are "Tessa **or the inspector**," not Tessa-or-Rowan — confirmed by direct comparison of the probe's own `input` field. |
| expert (Leah/Omar) | Input asks *"Did Leah photograph all of them or only the travel ones?"* — a scope ambiguity, not a who-said-what ambiguity. | Gold correctly preserves this as an unresolved question: *"It remains unclear whether Leah photographed all the receipts or only the travel receipts."* | Yes — this is the *correct* pattern (preserve, don't resolve), just applied to a different sub-question than probe 06 tests. |

**Corpus-wide sweep** (all 78 records — 66 parent + 12 curriculum, both input and gold output text):
only **one** record anywhere in the corpus combines an uncertainty phrase (`whether`, `unclear`,
`can't tell`, etc.) with a gendered pronoun in an identity-ambiguity context — the Rina/Marcus
record. A broader sweep for any identity/attribution-adjacent uncertainty phrasing (`unclear who`,
`not sure who`, `can't tell`, `ambiguous`, etc.) surfaces five additional records, but all five are
uncertainty about a *fact or action* (did a payment clear, was something sent-vs-saved, measured-vs-
photographed), not about *who a pronoun refers to*.

**Answer to the framework's question, corrected:** Rina/Marcus is **not a bad label** — both its
pronoun resolutions are correct once the two separate resolution questions in its source text are
read precisely, exactly mirroring probe 06's own two-question structure. It is, however, the *only*
structurally analogous example anywhere in the corpus for the "X told Y... after [pronoun] asked"
pattern, so it remains the leading candidate source of an **overgeneralized** pattern: the model may
have learned "resolve this construction's ambiguous pronoun to the second-named/most-recently-
mentioned person" from this one example, rather than the correct underlying rule (gender agreement),
and then misapplied that overgeneralization to probe 06 — where the gender-matching name (Tessa) and
the second-named/nearest-mentioned name (Rowan) happen to diverge, exposing the error. This is a
correctly-labeled-example-as-overgeneralization-source hypothesis, not a mislabeled-example-as-direct-
cause hypothesis. Confirmed there is no other training record from which the model could have drawn
this specific structural pattern.

## B. Added-curriculum output-style audit

All 12 additions, checked against the four listed style signals:

| Signal | Found? | Evidence |
|---|---|---|
| Narrative clause → standalone bullet, verbatim | **Yes**, in 2 of 12 (`cross_field_completeness`, both "expert") | #9: narrative "It is still unknown whether the west window was measured or only photographed" reappears as its own bullet. #10: narrative "It is still unknown whether the vendor tested the backup keypad" reappears as its own bullet; "Jae reported that the security vendor had changed the north gate code" also reappears as its own bullet. |
| Restating background/reported-speech as its own fact-bullet | **Yes**, same two records | #9: "Ren said Salma handed the spare clips to the installation lead" — a reported-speech clause — becomes a standalone bullet. #10: the Jae-reported clause above, same pattern. |
| Resolving a referent the input leaves uncertain | **No**, in any of the 12 | Both #9 and #10's uncertain items (`whether the west window was measured...`, `whether the vendor tested...`) are correctly preserved as unresolved bullets, not resolved. None of the 12 additions demonstrate resolving a flagged ambiguity. |
| Non-actionable bullet added | **Yes**, same two records | #9: "The folding screens looked uneven after setup" — a bare observation, not a task, gets its own bullet. #10: "The lobby smelled like fresh paint this morning" — same pattern. |

**Split membership** (per the framework's explicit ask): all 12 additions confirmed present in
`train.jsonl`, none in `val.jsonl` — table in §0 above; direct per-record confirmation available on
request.

**Interpretation offered as a candidate, not a conclusion:** the two `cross_field_completeness`
additions reinforce a *structural* style — "a reported/background clause in the narrative also gets
echoed as its own bullet, even when non-actionable" — without reinforcing referent-resolution. This
is a plausible second, independent contributor to probe 06's *new* bullet (which R2 never generated
at all): the model may have picked up the general "echo narrative clauses as bullets" pattern from
these two additions, and combined it with an overgeneralized version of Rina/Marcus's
(correctly-labeled) resolution pattern when applied to probe 06's own "after [pronoun] asked about
it" clause — supplying the bullet's *content* (who to name) while the style signal supplies the
*form* (that a bullet gets generated for this clause at all). Both pieces (style signal, and the
sole structurally-analogous training example) are independently confirmed present in the training
data; their *combination* as the actual mechanism is not proven by this reading alone.

## C. Training-horizon comparability check

**Checkpoint availability:** primary's saved checkpoints are at steps 702 and 720; control's are at
594 and 600. **No checkpoint exists at exactly step 600 for primary** — an exact state comparison at
the matching step is not possible from the artifacts on disk, and none was attempted.

**Determinism settings:** `train.py` sets `Seq2SeqTrainingArguments(seed=..., data_seed=...)` only
(confirmed by direct source read). No `torch.use_deterministic_algorithms`, no
`torch.backends.cudnn.deterministic`, no `cudnn.benchmark=False` setting appears anywhere in the
script. Given CUDA/bfloat16 is confirmed active for both runs, exact bit-for-bit reproducibility
across two separate subprocess invocations — even with matched seed, data, and config — is **not
guaranteed** by this training stack.

**What the logs actually show:** extracted every logged training-loss value from both runs and
matched them by epoch (both log at the same epoch fractions since both use the same
steps-per-epoch). Across all 120 matched logging points from epoch 0 through 33.33 (step 600):

- Mean absolute loss difference: **0.00404**
- Maximum absolute difference: **0.01890**
- Minimum: **0.00000** (several points match exactly)

The two runs track each other closely and consistently — never diverging into a different loss
regime — but are **not bit-identical**: small, persistent numerical differences of the size expected
from ordinary GPU/cuDNN non-determinism. The curves show no different loss regime, but cannot
establish state equivalence or exclude internal trajectory differences.

**Conclusion for the framework's decision rule:** exact equivalence through step 600 cannot be
established from available artifacts (no primary checkpoint at step 600, no deterministic-execution
guarantee in the code). The loss-curve evidence is consistent with — but does not prove — a shared
trajectory. Per the framework's own §6 decision rule, **"paired training-horizon comparison" should
be retained; "same trajectory" claims should not be made.** The step-effect *behavioral* observations
(probe 09 improving, probe 06's narrative field degrading, both between step 600 and 720) remain
valid as an association under matched declared conditions — they should not be read as proof of a
single continuous run.

## D. Probe-level field-by-field comparison (R2 / control / primary)

### Probe 06 (`multi_person_attribution`)

| Field | R2 | Control (600) | Primary (720) |
|---|---|---|---|
| Narrative "who asked" | ambiguous ("she") | ambiguous ("she") | **resolved to Rowan** |
| A "who asked" bullet at all | **not generated** | generated: "Rowan had asked about the permit" | generated: "Rowan had asked about the permit" (identical text to control) |
| Stamped-copy-need ambiguity | preserved | preserved | preserved |
| Action item | "Ask Rowan who needs the stamped copy" | same | same |

Mechanism: a wholly new bullet field appears in both Phase-2 runs that R2 never produced at all —
present already at step 600. A separate, narrative-level regression (a field that *existed* in R2 and
stayed correct through step 600) appears only by step 720. Two distinct defects, different fields,
different onset points, both landing on Rowan — the gender-ambiguous name — rather than Tessa, the
gender-matching one the rubric expects.

### Probe 09 (`open_question_preservation`)

| Field | R2 | Control (600) | Primary (720) |
|---|---|---|---|
| Volunteer-list reference | incomplete/uncertain ("it is unclear what yet") | **new invented question**: "whether the volunteer list was sent to Imani" | reverts to incomplete-thought framing, matching R2 |
| Schedule question | preserved unresolved | preserved unresolved | preserved unresolved |
| Action item | "Check sent mail" | same | same |

Mechanism: purely a narrative/bullet-content change (whether the volunteer-list reference stays a
dangling thought or gets converted into a fully-formed invented question); no field newly appears or
disappears the way probe 06's bullet does. Structural shape is stable; the semantic content of one
field regresses at 600 and recovers by 720.

### Probe 13 (`two_unrelated_tasks`)

| Field | R2 | Control (600) | Primary (720) |
|---|---|---|---|
| Bullets | both tasks present | both tasks present | both tasks present |
| Actions | **only one task** ("Pick up cat food after work") — email task silently dropped | both tasks present | both tasks present |

Mechanism: purely an actions-field omission in R2, already fully repaired by step 600 and stable
through 720 — the earliest-fixed of the three probes examined, consistent with direct, proportionate
curriculum support (§B/original packet §3).

## Summary against the framework's decision-rule table

| Framework condition | This supplement's finding |
|---|---|
| Attribution inconsistency systemic or policy-ambiguous | **No** — Rina/Marcus is correctly labeled, not a mislabel; no inconsistency found anywhere in a full-corpus sweep |
| Rina/Marcus isolated + added target style plausibly explains the bullet | **Consistent with this, reframed** — Rina/Marcus is the sole structurally-analogous *correctly-labeled* example (a plausible overgeneralization source, not a bad label), and the style signal (narrative-clause-to-bullet echoing) is found in 2 unrelated additions; combination is plausible, not proven |
| Realized primary/control trajectories differ before step 600 | **Cannot be ruled out** — no exact-state evidence exists either way; loss curves are close but not identical, consistent with ordinary non-determinism |
| Realized states match through step 600 | **Not established** — same caveat |

## Non-authorizations (unchanged)

No training, inference, corpus mutation, export, deployment, activation, or seed 73 occurred or is
proposed by this supplement. Not committed pending review.
