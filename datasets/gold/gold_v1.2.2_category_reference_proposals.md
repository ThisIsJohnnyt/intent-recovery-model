# Gold v1.2.2 Category Reference Proposals

Gold v1.2.2 reuses these existing categories:

- `interrupted_thought_depth`
- `nested_boundary_depth`
- `open_question_preservation`
- `buried_task_retention`
- `dangling_reference`

Only the following three categories are new.

## Proposed rows for `docs/datasets/CATEGORY_REFERENCE.md`

| Category | Teaches | Difficulty seen | Introduced in | Deprecated |
|---|---|---|---|---|
| `unsupported_content_resistance` | Preserve only source-supported content across narrative, bullets, and actions; resist filler labels, invented context, implied follow-up, and other plausible but ungrounded additions | medium, expert | v1.2.2 | — |
| `idea_action_boundary` | Preserve tentative ideas as possibilities rather than committed tasks, including when a real task appears nearby | medium, hard | v1.2.2 | — |
| `cross_field_completeness` | Preserve every meaningful supported topic across narrative and bullets while limiting action_items to explicit tasks, especially under heavy interleaving | expert | v1.2.2 | — |

## Category-design notes

- `unsupported_content_resistance` is broader than `zero_action_items`. `zero_action_items` teaches that an observation is not a task; this category targets unsupported additions in any output field, including filler bullets, invented labels, implied context, and fabricated referents.
- `idea_action_boundary` extends the behavior represented by `task_plus_idea`, `observation_plus_idea`, and `idea_among_tasks`. Those categories describe particular topic combinations; this category names the general recovery skill that failed across contexts: preserving tentative modality and keeping ideas out of action_items.
- `cross_field_completeness` is not a synonym for `buried_task_retention` or `long_rambling_multi_topic`. It targets consistency across the three output fields: supported content must not disappear from narrative or bullets merely because it survives elsewhere.
- `dangling_reference` is deliberately reused rather than creating a parallel `dangling_reference_restraint` label.
