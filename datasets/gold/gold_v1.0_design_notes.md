# gold_v1.0 Design Notes

## Purpose

These notes document why each example exists in the Gold Dataset. They are
for dataset authors only and are never used for model training.

## Example 001: simple_list

- **Purpose**: Recover tasks from a straightforward fragmented list.
- **Expected behavior**: Tests extraction without inventing tasks.
- **Design principle**: Every fragment is intentional and explainable (No Magic Examples).

## Example 002: interrupted_thought

- **Purpose**: Resume a thought after interruption.
- **Expected behavior**: Electric bill resumes after email reminder.
- **Design principle**: Every fragment is intentional and explainable (No Magic Examples).

## Example 003: topic_switching

- **Purpose**: Separate interleaved work and home topics.
- **Expected behavior**: Model should group by intent, not order.
- **Design principle**: Every fragment is intentional and explainable (No Magic Examples).

## Example 004: zero_action_items

- **Purpose**: Recognize observations are not tasks.
- **Expected behavior**: Action items must remain empty.
- **Design principle**: Every fragment is intentional and explainable (No Magic Examples).

## Example 005: unfinished_reference

- **Purpose**: Preserve uncertainty.
- **Expected behavior**: Do not invent what the blue folder is.
- **Design principle**: Every fragment is intentional and explainable (No Magic Examples).

## Dataset Principles

- One lesson per example.
- Preserve meaning without adding facts.
- Never invent action items.
- Preserve uncertainty when context is missing.
- Treat fragmented notes as normal human cognition under varying conditions, not as indicators of any diagnosis.
- Optimize for intent recovery with minimal cognitive burden.
