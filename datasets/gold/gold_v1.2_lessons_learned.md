# gold_v1.2 Lessons Learned

**Date**: 2026-07-28
**Training run**: FLAN-T5-base fine-tuned on the consolidated
`datasets/synthetic.jsonl` (`gold_v1.0` + `gold_v1.1` + `gold_v1.2` = 40
examples, 36 train / 4 val), 40 epochs. `train_loss` 0.188, stable
(non-NaN) `eval_loss` ~2.5. Exported to ONNX, deployed to the running app,
tested against two genuinely novel inputs never seen in training.

This is the first "lessons learned" entry per
[`docs/datasets/REVIEW_GUIDE.md`](../../docs/datasets/REVIEW_GUIDE.md)'s
release bundle — what we actually discovered after training and
evaluating, not what we intended going in.

## Context: what this run was for

Per the product owner: primarily a pipeline validation exercise (data →
train → export → deploy → infer) using real, reviewed data instead of the
placeholder fixture, not a claim that 40 examples produces a
production-quality model. Findings below should be read with that in mind.

## Unexpected successes

- **Held-out validation held up better than the fixture-only run.** 3 of 4
  genuinely held-out val examples (drawn from the full 40-example pool,
  not just `v1.2`) produced well-formed marker output — a real improvement
  over the earlier smoke test's fragility on a much smaller, less diverse
  dataset.
- **Bullets and action-items can be correct even when the narrative is
  wrong.** On a novel 4-topic input (post office / coffee maker / quarterly
  review / texting Ben about Saturday), the `bullets` list correctly
  preserved all four topics, and `action_items` correctly excluded the
  coffee-maker observation (a non-task) — while the `narrative` field for
  the same generation was factually wrong (see below). The three output
  sections aren't learned with equal reliability; errors can be localized
  to one section rather than all-or-nothing.

## Unexpected failures

- **Narrative-level hallucination on a novel multi-topic input.** For the
  same 4-topic input above, the generated narrative was: *"I'm unsure
  whether the new coffee maker is really loud or not. I also noticed that
  the quarterly review is due on Saturday."* Two real errors: (1) the input
  states the coffee maker *is* loud, as a fact — the model invented
  uncertainty that isn't there; (2) "Saturday" belongs to the "text Ben
  back" fragment in the input, not the quarterly review — the model
  invented a relationship between two actually-unrelated fragments. This is
  exactly the failure mode `gold_v1.2`'s curriculum is designed to prevent,
  and it still occurred in the narrative field specifically.
- **Complete generation failure on a novel buried-reminder-style input.**
  "Been debating whether to switch gyms... oh also need to renew my
  library card, anyway still not sure about the gym" — structurally similar
  to `buried_reminder`/`nested_thought` (Level 3) but not a close match to
  any specific trained example — produced output missing one or more
  section markers entirely, and the app correctly surfaced an error rather
  than showing broken output. The error handling worked as designed; the
  underlying generation did not.

## Surprises

- Structural correctness (markers, bullets, action-item classification)
  generalized better than semantic correctness (accurate narrative
  content) from just 40 examples. This suggests the model has learned the
  *shape* of the task more reliably than the specific "don't merge
  unrelated fragments" discipline the curriculum is actually about —
  which is the harder, more specific skill.
- Level 3 ("buried"/"nested"/interrupted structural complexity) is the
  most fragile category under generalization, consistent with it having
  the fewest, most varied examples (6 across all of `gold_v1.2`, each
  demonstrating a different sub-skill) relative to Level 1/2's more
  repetitive, templated structure.

## Follow-up: real-world usage findings

The product owner hit "Failed to process notes" during real use (console:
`Model output is missing one or more section markers`), then provided four
of their own actual notes for testing. Re-running those same four inputs
did not reproduce a crash — all four produced schema-valid output (either
non-determinism in the WASM execution, or the original failure came from a
fifth, different input not among these four). But the *content* of all
four had real, concrete errors, worse in one sense than a crash: they look
confident and plausible rather than visibly broken.

*(Findings described abstractly, not quoted — these came from the product
owner's real personal notes, which per this project's own principles
[`datasets/gold/DATASET_CARD.md`](DATASET_CARD.md) stay out of version
control and out of this corpus.)*

- **Invented answer to an open question.** Input asked, unresolved, where
  a personal item had been left. Output asserted a specific, fabricated
  location never stated anywhere in the input. A separate list-style
  fragment in the same output also showed degenerate repetition — one item
  duplicated four times with inconsistent capitalization.
- **Dropped task entirely.** A standalone, unambiguous task (contacting a
  specific person) never appeared in narrative, bullets, or actions for
  its input.
- **Invented emotion.** Narrative attributed an anxious emotional framing
  to an input that was a plain factual task with no emotional language at
  all.
- **Invented merge between unrelated fragments.** Output fused two
  unrelated fragments (a technical status check and an unrelated shopping
  item) into one nonsensical combined instruction. A separate hobby-related
  fragment from the same input was also dropped entirely.
- **Misattributed ownership between two people.** Input had the *writer*
  wondering about their own unresolved task; output reassigned it to a
  different person mentioned earlier in the note in connection with an
  unrelated question. The actual resolved instruction was dropped from
  both bullets and actions; a separately mentioned task appeared in the
  narrative and bullets but not in action_items.

This adds two failure categories not seen in the earlier synthetic
testing above: **dropping an unambiguous task entirely** (not just
mis-merging or hallucinating), and **misattributing which person a
fragment belongs to** when a note mentions more than one person. Both are
more concerning for a real user than the marker-format crash, since wrong-
but-confident output is easier to miss than a visible error.

## Recommendations for the next release

1. **More Level 3 examples before more Level 1/2 examples.** The
   generalization gap is concentrated in structural complexity
   (interrupted/buried/nested), not simple topic counting — volume should
   go there first.
2. **Add narrative-specific non-merging reinforcement.** Consider examples
   where two topics share a superficially similar trailing detail (e.g. a
   day of the week, a name) attached to only one of them, specifically to
   train against the "attach the wrong topic's detail" failure seen here.
3. **Add explicit "don't invent an answer to an open question" examples.**
   Distinct from `unfinished_reference`/`dangling_reference` (which
   preserve uncertainty about *what something is*) — this is preserving
   uncertainty about *the answer to a question the note itself poses*.
4. **Add multi-person attribution examples.** None of `gold_v1.0`-`v1.2`
   test a note mentioning two different people with different associated
   tasks/questions — real notes do this often (per the product owner's
   examples) and it's an easy way to misattribute a fragment.
5. **Watch for dropped tasks, not just merged/invented ones.** Existing
   design notes mostly guard against invention; "lost topics" is already a
   named curriculum failure mode but wasn't well-represented in what
   actually got tested here — worth a dedicated review pass checking every
   fragment in an input actually appears somewhere in the output.
6. **40 examples is not enough to treat this as production-ready** — this
   result is consistent with (not contradicting) the plan to keep
   generating and reviewing more data with the dataset curator before a
   real production training run.
