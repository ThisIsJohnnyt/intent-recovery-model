# Split-Delta Report: What Actually Changed Between Train/Val Partitions

Required before any curriculum edits, per the approved investigation
sequence. Answers a question the control-seed comparison did not check:
does adding `gold_v1.2.3`'s 6 examples to the 72-example corpus *only*
add 6 new training examples, or does `prepare_data.py`'s
`random.Random(42).shuffle()` over a longer list also reassign some of
the original 66 examples between train and val?

## Method

Reproduced `prepare_data.py`'s exact shuffle/split logic (same `SEED`,
same `VAL_FRACTION`) against both the 66-example (`gold_v1.2.2`-only) and
72-example (`gold_v1.2.3`) corpora, identifying each record by its
`input` text (stable, unique per example) rather than list position, and
diffing train/val membership directly.

## Headline finding: it's not just +6

```
66-example corpus: 60 train, 6 val
72-example corpus: 65 train, 7 val
```

All 6 new `gold_v1.2.3` examples landed in **train** (none in val) — that
part is as expected. But the longer list reshuffles differently, and **9
of the original 66 examples changed train/val role**:

### Moved OUT of training (train → val-only under `gold_v1.2.3`)

| Example (category, difficulty) | Relevance |
|---|---|
| `nested_boundary_depth`, hard — "Ask Devon whether the replacement badge is ready before going downtown, not ask Devon and then separately figure out the badge, it's one thing. The lobby printer is low on paper." | **Direct structural twin of probe 03** — same category, same "ask X whether Y, not ask X and separately [check/figure out] Z, that's one [thing/question]" template, same difficulty tier. |
| `two_unrelated_tasks`, easy — "Pick up dry cleaning. Renew the car registration before it expires." | **Exact category match to probe 13.** |
| `buried_reminder`, hard — "Been thinking a lot about whether to repaint the living room..." | Adjacent category to probe 12's `buried_task_retention` (per `CATEGORY_REFERENCE.md`, `buried_task_retention` explicitly generalizes `buried_reminder`). |
| `dangling_reference`, medium — "update the router firmware. check the thing in the blue folder..." | No direct match to any probe showing a `gold_v1.2.3`-attributable regression. |
| `hyperfocus_details`, medium — "if f-stop is 8 then shutter speed should be 1/250..." | No direct match. |

### Moved INTO training (val → train under `gold_v1.2.3`)

| Example (category, difficulty) | Relevance |
|---|---|
| `open_question_preservation`, hard — "Was the strange noise coming from the vent or outside? It stopped after a minute. Move the laundry before bed." | Same category as probes 08/09. Newly trained on for the first time under `gold_v1.2.3` (previously held out). |
| `idea_among_tasks`, medium — "Order more filing folders. What if we color-coded the folders by client instead of by month?..." | Thematically adjacent to probe 15's `task_plus_idea`, but *added*, not removed — doesn't explain a regression. |
| `four_independent_topics`, medium — "Return the rental car by noon..." | No direct match. |
| `unsupported_content_resistance`, expert — "The supply cabinet smells damp. Leave that note as-is; not sure which one she meant..." | No direct match to a regressed probe. |

## What this means for the six probes flagged as `gold_v1.2.3`-attributable

| Probe | Prior explanation (control comparison) | Revised, given this delta |
|---|---|---|
| **03** | Negative transfer from `gold_v1.2.3`'s new interruption examples | **Better explanation available**: the training set lost its most directly relevant existing example (the Devon example above) to the reshuffle. This isn't a curriculum *conflict* — it's a reduction in relevant training signal that has nothing to do with what `gold_v1.2.3` actually added. |
| **13** | Unclear collateral effect | **Better explanation available**: same mechanism — the training set lost its only `two_unrelated_tasks` reinforcement example. |
| **12** | Unclear collateral effect | **Plausible partial explanation**: lost a category-adjacent (`buried_reminder`) example, though less directly than 03/13. |
| **05, 11, 15** | Negative transfer from `gold_v1.2.3`'s new examples | **Not explained by this mechanism** — no reassigned example matches these probes' categories (`multi_person_attribution`, `standalone_task_retention`, `task_plus_idea`). These three remain open questions for the Tier 1 audit; a genuine curriculum-interaction explanation is still on the table for them specifically, not ruled in or out by this report. |

## Implication for how the audit should proceed

For probes 03 and 13 specifically, the most parsimonious explanation is
**not** "`gold_v1.2.3`'s new examples conflict with existing training" —
it's "a consolidation side effect accidentally shrank the effective
training set for these categories." That points toward a different fix
entirely (restoring the dropped examples, or checking category coverage
explicitly after every consolidation) rather than revising or removing
anything in `gold_v1.2.3` itself. Recommend the Tier 1 audit check this
"lost training example" angle for 03/13 (and partially 12) *before*
looking for a content conflict between old and new examples — the two
explanations aren't mutually exclusive, but the lost-example one is
simpler, already has direct evidence, and should be ruled in or out
first.

For probes 05, 11, and 15, this mechanism doesn't apply — nothing
category-relevant was reassigned. These remain the strongest candidates
for an actual `gold_v1.2.3` content interaction, and should be the
audit's real focus.

No curriculum edits made. This report only establishes what changed in
the trained-vs-validated composition; it doesn't yet recommend a fix.
