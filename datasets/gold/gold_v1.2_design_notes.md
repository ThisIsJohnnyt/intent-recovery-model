# gold_v1.2 Design Notes

**Theme**: Multiple Interleaved Topics (segmentation, not summarization —
see [`gold_v1.2_curriculum.md`](gold_v1.2_curriculum.md))
**Author**: Claude Code, authoring this release directly because the
dataset curator (ChatGPT) was unavailable (rate-limited) when this release
was needed. See the review report's note on independent review.

Format per [`docs/datasets/DESIGN_NOTES_TEMPLATE.md`](../../docs/datasets/DESIGN_NOTES_TEMPLATE.md),
condensed for 20 examples.

## Level 1 — Basic segmentation (2 topics, easy)

**01 — two_unrelated_tasks**
Lesson: two unrelated tasks in one note, no relationship between them.
Fragments: "pick up dry cleaning" (task 1) / "renew car registration"
(task 2, unrelated). Failure modes: inventing a reason the two are
connected. Expected recovery: both listed as independent action items.

**02 — task_plus_observation**
Lesson: one actionable task alongside one non-actionable observation.
Fragments: "send the invoice" (task) / "coffee shop reopened" (pure
observation, not a task). Failure modes: turning the observation into a
fabricated action item. Expected recovery: one action item, one
observation-only bullet.

**03 — task_plus_idea**
Lesson: a task alongside a speculative idea ("what if...").
Fragments: "refill the prescription" (task) / "newsletter biweekly?"
(idea, not a commitment). Failure modes: treating the idea as a decided
action item. Expected recovery: idea appears in bullets, not action_items.

**04 — observation_plus_idea**
Lesson: two non-actionable fragments together — tests that action_items
correctly stays empty when nothing in the note is actually a task.
Fragments: "neighbors put up string lights" (observation) / "what if our
porch had some too" (idea, not a commitment to buy/install anything).
Failure modes: inventing "buy string lights" as an action item the note
never actually commits to. Expected recovery: empty action_items.

## Level 2 — Moderate segmentation (3-5 clean topics, medium)

**05 — three_independent_topics** / **06 — four_independent_topics** /
**07 — five_independent_topics**
Lesson: scaling topic count with no structural complexity — clean,
complete sentences, just more of them. Each fragment is a self-contained
statement with no interruption or ambiguity. Failure modes: dropping a
topic as the count increases, or merging two of the topics because they
happen to be adjacent. Expected recovery: every topic preserved as its own
bullet; task fragments become action items, observation fragments don't.

**08 — topic_switch_and_return**
Lesson: the note leaves a topic, inserts something unrelated, then returns
to the original topic. Fragments: "finish slide deck" → "did we get the
pool cleaned?" (unrelated aside, genuinely unresolved) → "slide deck needs
updated numbers" (same topic as the first fragment, resumed). Failure
modes: treating the resumed slide-deck detail as a third, separate topic
instead of recognizing it belongs with the first. The pool question is a
genuine open question with no resolution in the note, so surfacing it as
something to check is evidence-supported, not invented. Expected recovery:
two topics (slide deck, pool), not three.

**09 — observation_among_tasks** / **10 — idea_among_tasks**
Lesson: a single non-actionable fragment (observation / idea) placed
between two task fragments — tests that position in the note doesn't
change classification. Failure modes: assuming the middle fragment must
relate to its neighbors because of where it sits. Expected recovery: the
middle fragment stays independent regardless of position.

## Level 3 — Complex notes (interrupted / buried / stream-of-consciousness, hard)

**11 — buried_reminder**
Lesson: a genuine task hidden inside a much longer reflection on an
unrelated topic. Fragments: an extended, indecisive reflection on repainting
the living room / a single buried clause, "call the pharmacy about the
refill." Failure modes: losing the buried task entirely because it's
short relative to the surrounding text, or treating it as part of the
paint reflection. Expected recovery: the pharmacy call surfaces as its own
action item despite being a small fraction of the note's length.

**12 — interrupted_thought_multi_topic**
Lesson: a thought about one topic gets cut off mid-sentence, a second
unrelated topic is handled, then the note explicitly returns to the first.
Fragments: "I was going to tell Priya... but then—" (interrupted) /
"check if the conference room is booked" (unrelated, inserted) / "I'll
catch Priya later" (explicit return/deferral of the first). Failure modes:
inventing what caused the interruption, or dropping the Priya thought
since it never got finished. Expected recovery: Priya thought preserved as
still-pending, not invented or discarded.

**13 — stream_of_consciousness_topics**
Lesson: run-on, no punctuation, several unrelated topics blurred together
by the writing style alone (not by actual relatedness). Fragments: cold
weather observation / firewood task / uncertain package status / cold
hands observation. Failure modes: inventing a connection between "cold"
and "firewood" (plausible-sounding but not asserted by the text) beyond the
natural one already explicit in the note. Expected recovery: firewood and
package tracked as separate, unresolved items; the two "cold" mentions can
reasonably be treated as one observation.

**14 — nested_thought**
Lesson: a parenthetical aside nested inside one topic (not a second,
separate topic). Fragments: "finishing the budget spreadsheet" with a
nested reconsideration ("double check... actually maybe redo") followed by
a real deadline. Failure modes: treating the nested aside as an unrelated
third topic rather than a qualification of the spreadsheet task. Expected
recovery: one coherent spreadsheet topic, not two.

**15 — long_rambling_multi_topic**
Lesson: a long note with several unrelated topics and no clear structure,
testing that length alone doesn't cause topics to be merged or dropped.
Failure modes: over-summarizing into a vague single sentence that loses
individual topics; assuming the printer jam caused the report to be
unfinished (a plausible but unstated causal link — the note states both
facts adjacently but never says one caused the other). Expected recovery:
four distinct items preserved, no invented causality between the printer
and the report.

**16 — reminder_inside_narrative**
Lesson: a task remembered in passing during an unrelated story, and
recognizing when the note describes something outside the writer's
control (waiting on a callback) versus something actually actionable by
them. Fragments: a narrative about an unresolved insurance call / a task
remembered mid-story (move the car). Failure modes: inventing a "follow up
with insurance" action item when the note says *they* said they'd call
back — the ball isn't in the writer's court. Expected recovery: only the
car-moving task appears in action_items.

## Level 4 — High cognitive load (rapid changes, incomplete sentences, emotional asides, repeated reminders, expert)

**17 — emotional_aside_multi_topic**
Lesson: two genuine tasks interleaved with an emotional reflection that
isn't itself a task and shouldn't be treated as connected to either one.
Failure modes: inventing a causal link between feeling burnt out and the
passport/pickup tasks (e.g. "burnt out because of the trip"). Expected
recovery: the burnout reflection stands alone, connected to nothing.

**18 — repeated_reminder_multi_topic**
Lesson: the same task stated three ways ("do not forget," "Timesheet!,"
"seriously, submit") alongside two unrelated tasks — tests deduplication
under emphasis/repetition rather than under simple restatement.
Failure modes: listing the timesheet as three separate action items.
Expected recovery: one timesheet action item, noted as emphasized/repeated;
Wilson account and plants remain separate.

**19 — rapid_topic_switching_incomplete_sentences**
Lesson: very rapid topic changes with sentence fragments and one
genuinely unfinished thought. Fragments: keys/wallet/phone / a
prioritization note (meeting before report) / gas / an incomplete
"call the landlord about—" / lunch plan. Failure modes: inventing what the
landlord call is about. Expected recovery: "call the landlord" preserved
as a valid action item without inventing its subject — the topic (a call
needs to happen) is clear even though the reason isn't.

**20 — maximum_interleaving**
Lesson: combines rapid topic changes, an emotional aside (stress about the
leak), and a repeated mention (plumber never called back, stated twice) —
the hardest example in the release, deliberately combining several Level 4
traits at once rather than introducing a new one. Failure modes: treating
the repeated plumber mention as two separate facts; inventing a
relationship between the stress and the trash-day uncertainty just because
they're adjacent. Expected recovery: five distinct items, plumber mention
deduplicated, stress reflection kept as its own item.

## Note on scope

This release intentionally does not use the app's `narrative`/`bullets`/
`action_items` schema's topic-clustering (that's a `v1.5` feature, not yet
built — see `training/ROADMAP.md`). Multiple topics are demonstrated
through non-causal narrative construction (neutral connectors like
"separately," never "because"/"so"/"which meant" between unrelated
fragments) and clean bullet separation, not through a new schema field.
