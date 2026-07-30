# Changelog

## v1.2.2 — 2026-07-29

12 examples, authored by ChatGPT (dataset and evaluation architect).
Additive corrective release, not a new theme: targets seven protected
benchmark failures surfaced by `gold_v1.2.1`'s strict scoring (probes `02`,
`03`, `08`, `12`, `14`, `15`, `16`) — unsupported filler around plain
observations and dangling references, tentative ideas promoted to
committed tasks, interrupted-thought reconnection, nested-boundary
completeness, open-question clarity, and cross-field completeness under
interleaving. See [`gold_v1.2.2_curriculum.md`](gold_v1.2.2_curriculum.md)
for the full rationale, including the "Decision Point Resolution" section
recording what was approved.

Prerequisite: benchmark probes `14` and `16` were reclassified from
`regression_guard` to `negative_example` under the stricter pass rule
`training/report_benchmark.py` introduced (both produced a minor, real
`Unsupported Addition` that `gold_v1.2.1`'s original informal review
missed) — see
[`datasets/benchmark/gold_v1.2.1_probes.md`](../benchmark/gold_v1.2.1_probes.md).

Difficulty distribution: 3 medium, 5 hard, 4 expert — no `easy` tier, since
these are corrective lessons applied after the base capabilities were
already introduced. 5 categories reused from `v1.1`/`v1.2.1`
(`interrupted_thought_depth`, `nested_boundary_depth`,
`open_question_preservation`, `buried_task_retention`,
`dangling_reference`) rather than introducing parallel labels, plus 3
genuinely new categories (see
[`gold_v1.2.2_design_notes.md`](gold_v1.2.2_design_notes.md) for the
rationale per example):

- `unsupported_content_resistance` — new: resist filler labels, invented
  context, and implied follow-up around a complete, plainly-stated
  observation
- `idea_action_boundary` — new: keep a tentative idea out of
  `action_items`, including when a real task appears right next to it
- `cross_field_completeness` — new: no supported topic disappears from
  narrative or bullets just because it survives in another field

Independent review
([`gold_v1.2.2_review_report.md`](gold_v1.2.2_review_report.md)) initially
found a borderline issue: 4 of the 12 examples (005, 006, 007, 012) reused
their benchmark analogue's wording or sentence pattern closely enough to
risk contaminating the very benchmark improvement this release is meant to
demonstrate — including one verbatim phrase, "that is one question,"
copied from probe `03`. All four were rewritten (same lesson, category,
and difficulty; new surface forms with no overlap against any of the 16
probes) and re-reviewed clean — zero remaining blocking or borderline
findings.

**Not yet trained on or evaluated** — next step is consolidating with
`gold_v1.0`-`v1.2.1` for a training run, then evaluating against
`datasets/benchmark/gold_v1.2.1_probes.jsonl`'s release gates and a
`gold_v1.2.2_lessons_learned.md` entry.

## v1.2.1 — 2026-07-29

14 examples, authored by ChatGPT (dataset and evaluation architect) — the
first release drafted using its GitHub connector's confirmed read access to
the live repo, rather than a manually relayed file bundle. Additive
corrective release, not a new theme: reinforces `gold_v1.2` segmentation
skills that `gold_v1.2_lessons_learned.md`'s real training run and
real-world usage testing showed were unreliable — deeper interrupted/
buried/nested Level 3 structures, multi-person attribution, open-question
preservation, and task retention. See
[`gold_v1.2.1_curriculum.md`](gold_v1.2.1_curriculum.md) for the full
rationale and [`gold_v1.2.1_review_report.md`](gold_v1.2.1_review_report.md)
for the review (zero blocking or borderline findings).

Difficulty distribution: 5 medium, 5 hard, 4 expert — no `easy` tier, since
this release reinforces already-advanced skills rather than introducing
basic ones. 6 new categories, one per lesson (see
[`gold_v1.2.1_design_notes.md`](gold_v1.2.1_design_notes.md) for the
rationale per example):

- `interrupted_thought_depth`, `buried_task_retention`,
  `nested_boundary_depth` — deeper Level 3 structural reinforcement
- `multi_person_attribution` — new: attribution across multiple named
  people, including deliberately unresolved pronoun ambiguity
- `open_question_preservation` — new: preserving an unanswered question
  instead of inventing a resolution
- `standalone_task_retention` — new: retaining a brief or repeatedly
  emphasized task under competing narrative/emotional salience

Also adds two `TAXONOMY.md` failure categories (`Invented Answer`,
`Excessive Fragmentation` — the first over-segmentation failure named) and
a canonical-vs-descriptive wording table, so future reviews use consistent
terminology instead of parallel ad hoc labels for the same failure.

**Not yet trained on or evaluated** — next step is consolidating with
`gold_v1.0`-`v1.2` for a training run, then a `gold_v1.2.1_lessons_learned.md`
entry.

## v1.2 — 2026-07-28

20 examples, authored by Claude Code. Focus: multiple interleaved topics —
segmentation, not summarization (see
[`gold_v1.2_curriculum.md`](gold_v1.2_curriculum.md)).

An initial Gemini-generated draft was reviewed and rejected: schema
mismatch with `training/prepare_data.py` and a diagnosis reference in the
curriculum's coverage matrix. This release is a from-scratch replacement,
authored by Claude Code because the dataset curator (ChatGPT) was
unavailable. See
[gold_v1.2_review_report.md](gold_v1.2_review_report.md) for the full
review, including the process caveat: this release has not had independent
second-reviewer sign-off yet.

Difficulty distribution: 4 easy, 6 medium, 6 hard, 4 expert — matches the
curriculum's target exactly. 20 distinct categories, one per example (see
[`gold_v1.2_design_notes.md`](gold_v1.2_design_notes.md) for the full
rationale per example):

- Level 1 (easy): `two_unrelated_tasks`, `task_plus_observation`,
  `task_plus_idea`, `observation_plus_idea`
- Level 2 (medium): `three_independent_topics`, `four_independent_topics`,
  `five_independent_topics`, `topic_switch_and_return`,
  `observation_among_tasks`, `idea_among_tasks`
- Level 3 (hard): `buried_reminder`, `interrupted_thought_multi_topic`,
  `stream_of_consciousness_topics`, `nested_thought`,
  `long_rambling_multi_topic`, `reminder_inside_narrative`
- Level 4 (expert): `emotional_aside_multi_topic`,
  `repeated_reminder_multi_topic`,
  `rapid_topic_switching_incomplete_sentences`, `maximum_interleaving`

**Trained on**: consolidated with `gold_v1.0` and `gold_v1.1` into
`datasets/synthetic.jsonl` (40 examples total, replacing the old
placeholder fixture) and used for a real training run — see
[gold_v1.2_lessons_learned.md](gold_v1.2_lessons_learned.md) for what that
run found, including real-world usage findings from the product owner's
own testing (described abstractly there, per this corpus's privacy
principles).

## v1.1 — 2026-07-28

15 examples, generated by Gemini. Focus: authentic messiness and realistic
note styles — richer diversity than v1.0's cleaner set.

Categories introduced:
- `interleaved_work_personal` (medium)
- `rapid_branching_excitement` (hard) — first example of this cognitive state
- `voice_to_text_artifacts` (medium)
- `abrupt_topic_switching` (medium)
- `repeated_reminder` (easy)
- `half_finished_thoughts` (hard)
- `contradictory_statements` (hard) — see review report, category label may not
  perfectly match the example
- `short_note` (easy)
- `long_rambling` (hard)
- `dangling_reference` (medium)
- `anxious_task_dump` (medium) — first example of anxiety as a cognitive state
- `hyperfocus_details` (medium) — first example of hyperfocus as a cognitive state

Also adds a second `simple_list` and `interrupted_thought` example (already
covered by v1.0) and a second `zero_action_items` example.

Reviewed by Claude Code — see
[gold_v1.1_review_report.md](gold_v1.1_review_report.md). Two examples
(schedule-an-eye-exam, ask-daughter-about-Friday) flagged for possible
revision — action items assert a mechanism not literally stated in the
input. Not blocking; flagged for curator consideration.

No author design notes provided for this batch.

## v1.0 — 2026-07-28

Initial gold batch. 5 hand-curated examples, generated collaboratively with
ChatGPT following the "No Magic Examples" and "one lesson per example" rules
in [../../training/DATASET_SPEC.md](../../training/DATASET_SPEC.md).

Categories covered:
- `simple_list` (easy)
- `interrupted_thought` (easy)
- `topic_switching` (medium)
- `zero_action_items` (easy)
- `unfinished_reference` (hard)

See [gold_v1.0_design_notes.md](gold_v1.0_design_notes.md) for the rationale
behind each example.
