# North Star

> The model should adapt to the person — not the person to the model.

The mission is to help people recover their own intent with as little
cognitive and emotional burden as possible.

Not "organize notes."
Not "summarize text."
Not "detect ADHD."

Every dataset, evaluation, and architecture decision should be checked
against one question:

**Does this make it easier for the user to recover what mattered, without
forcing them to relive more than they need to?**

If the answer is no, redesign it.

## The task: Intent Recovery

This project is defining a distinct supervised learning problem, not just
applying an existing one. Common NLP tasks — translation, summarization,
classification, named entity recognition, sentiment analysis — all take
well-formed text as input. Ours doesn't.

**Intent Recovery**

- **Input**: fragmented human cognition — scattered, interrupted,
  incomplete notes written under real-world conditions (time pressure,
  distraction, fatigue, excitement).
- **Output**: recovered intent — what the person was actually trying to
  capture, structured and readable, without inventing what wasn't there and
  without forcing them to re-enter the state they wrote it in.

The distinction matters: a generic summarizer optimizes for shorter text
that preserves meaning. Intent Recovery optimizes for recovering what the
person meant to preserve — including tasks they didn't finish writing,
topics interleaved without transition, and the difference between an
observation and an action item — while explicitly declining to invent
detail that isn't there (see [../datasets/REVIEW_GUIDE.md](../datasets/REVIEW_GUIDE.md)'s
"No Magic Examples" check) and while never assuming *why* a note is
fragmented (no diagnosis framing — see
[../../training/DATASET_SPEC.md](../../training/DATASET_SPEC.md)).

## Collaboration model

- **Product owner** (the user): owns the problem and the vision — the lived
  experience of what it's like to look at your own note and not want to
  mentally return to the state you wrote it in just to understand it.
- **Claude Code**: implementation engineer — repository, training scripts,
  ONNX export, quantization, inference, deployment, debugging.
- **ChatGPT**: dataset & evaluation architect (also "Dataset Curator" in
  [../decisions/](../decisions/)) — dataset specification, synthetic data
  generation rules, diversity/balance analysis, benchmark creation,
  evaluation methodology, difficulty progression.

Dataset-content decisions (exactly which examples, how many per category,
how evaluation is scored) come from the product owner + ChatGPT. Significant
project decisions are recorded in [../decisions/](../decisions/) as they're
made, not left to chat history.
