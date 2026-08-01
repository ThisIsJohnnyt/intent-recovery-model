# Real-Data Evaluation and Strict-Scoring Protocol

## Status

**Proposed, revision 2, for joint review. Format-validity-only results cannot guide model or release decisions.**

## Evaluation modes

### Routine validation generation

After a declared training run, the system may generate outputs for real validation and save a structured private record. Automated format validity may be computed immediately.

An unscored generation record is evidence collection only. It cannot guide curriculum, checkpoint, seed, or release decisions.

### Candidate validation scoring

When a checkpoint comparison or curriculum decision is declared, selected validation outputs receive full semantic scoring under the frozen rubric.

### Sealed holdout evaluation

The holdout evaluator runs only for a declared release milestone and a single frozen candidate. It loads the source directly in memory and never relies on a routinely materialized processed copy.

## Required engineering boundary

- Routine `prepare_data.py` processes synthetic data and real validation only.
- It does not open, validate, transform, or copy `real_holdout.jsonl`.
- `evaluate_holdout.py` explicitly opens the sealed source only after milestone confirmation.
- It calls the shared validation and prompt-building functions directly in memory.
- It writes no persistent processed holdout JSONL.
- Validation and holdout result directories are private and gitignored.

## Concrete private paths

| Artifact | Required path |
|---|---|
| Consent and provenance manifest | `datasets/private/real_data_manifest.jsonl` |
| Private scoring rubrics | `datasets/private/real_data_rubrics.jsonl` |
| Validation evaluation records | `training/results/private/real_validation/<evaluation_id>.json` |
| Holdout evaluation records | `training/results/private/real_holdout/<milestone>/<evaluation_id>.json` |

All parent directories and files are private and gitignored before first creation. The evaluator must fail closed if an output path is outside the approved private result roots.

## Structured result schema

Every run saves one JSON artifact with this logical structure:

```json
{
  "schema_version": "real-eval-v1",
  "evaluation_id": "<unique-id>",
  "split": "real_validation|real_holdout",
  "started_at_utc": "<timestamp>",
  "release_milestone": null,
  "evaluation_reason": "<declared reason>",
  "git_commit": "<commit>",
  "checkpoint": {
    "path": "<private-or-relative-path>",
    "fingerprint": "sha256:<fingerprint>",
    "training_seed": 0,
    "run_id": "<run-id>"
  },
  "dataset": {
    "fingerprint": "sha256:<fingerprint>",
    "record_count": 0,
    "rubric_version": "real-rubric-v1"
  },
  "generation_config": {},
  "results": [
    {
      "record_id": "rv_<random-id>",
      "raw_output": "<generated text>",
      "format_valid": true,
      "scores": {
        "topic_completeness": null,
        "attribution_accuracy": null,
        "uncertainty_preservation": null,
        "unsupported_addition_resistance": null
      },
      "capability_checks": {},
      "strict_pass": null,
      "failure_labels": [],
      "review_status": "unscored"
    }
  ],
  "aggregate": {
    "format_valid": "0/0",
    "strict_pass": null
  },
  "review": {
    "chatgpt_status": "pending",
    "claude_status": "pending",
    "alignment_status": "pending",
    "adjudication_status": "not_started"
  }
}
```

For holdout runs, `release_milestone` is required and may not be null. Paths and metadata must not reveal contributor identity.

## Deterministic fingerprints

All fingerprints use SHA-256 and lowercase hexadecimal output.

### Canonical JSON

Canonical JSON is UTF-8 encoded, uses sorted object keys, no insignificant whitespace, and preserves array order. Newlines are not appended before hashing.

### Record fingerprints

- `source_fingerprint`: SHA-256 of canonical JSON containing only `{"input": <de-identified input>}`.
- `pair_fingerprint`: SHA-256 of canonical JSON containing only `{"input": <de-identified input>, "output": <approved output>}`.
- `rubric_fingerprint`: SHA-256 of the canonical private rubric after omitting its own `rubric_fingerprint` field.

### Dataset fingerprint

Build an array containing one object per active record with exactly these fields:

```json
{
  "record_id": "<id>",
  "source_fingerprint": "sha256:<hash>",
  "pair_fingerprint": "sha256:<hash>",
  "rubric_fingerprint": "sha256:<hash>"
}
```

Sort the array lexicographically by `record_id`, place it in exactly this wrapper, serialize the wrapper as canonical JSON, and hash the resulting bytes:

```json
{
  "rubric_schema_version": "real-rubric-v1",
  "split": "real_validation|real_holdout",
  "records": []
}
```

The literal split value replaces the example union string. This prevents validation and holdout from sharing a fingerprint accidentally.

### Checkpoint fingerprint

Walk the declared checkpoint directory recursively. Symlinks are rejected. For every regular file:

1. compute the file's SHA-256;
2. record its POSIX-style relative path, byte length, and file hash; and
3. sort entries lexicographically by relative path.

Serialize the ordered entry array as canonical JSON and hash it. No checkpoint file is excluded. Evaluation logs and other mutable artifacts must not be stored inside checkpoint directories. An empty checkpoint directory fails validation.

### Prompt-contract fingerprint

Both repositories expose the same prompt-contract version. Render the exact ASCII fixture `Prompt contract fixture: review the blue folder tomorrow?` through the training and production prompt builders, encode the complete rendered prompt as UTF-8 without normalization or an appended newline, and compute SHA-256. The pilot is blocked unless version identifiers and rendered-prompt hashes match.

A mismatch between any declared and computed fingerprint stops evaluation. Any record, rubric, checkpoint, or prompt edit creates a new fingerprint and supersedes earlier comparisons.

## Strict semantic rubric

### Format validity

The output contains all required sections in the correct order and can be parsed into narrative, bullets, and action items.

### Topic completeness

Pass when every source-supported idea, explicit task, unresolved question, and material qualifier required by the private rubric survives somewhere appropriate in the output. Important content may not disappear merely because another field preserves part of the note.

### Attribution accuracy

Pass when people, entities, pronouns, recipients, actions, observations, temporal relationships, and causal relationships remain correctly attributed across every field. If the source is ambiguous, the output preserves ambiguity rather than choosing.

### Uncertainty preservation

Pass when open questions, alternatives, tentative ideas, incomplete thoughts, and dangling references remain at the same certainty level. Later observations are not treated as answers unless the source explicitly connects them.

### Unsupported-addition resistance

Pass when the output adds no unsupported fact, action, emotion, explanation, cause, resolution, referent, commentary, or task qualifier. Plausibility is not support.

When a dimension has no special challenge in a record, it passes only if the output introduces no violation of that dimension. The score is still boolean rather than `not_applicable`.

## Capability checks

Each private rubric defines record-specific boolean checks, such as:

- explicit task and deadline survived;
- question remained unresolved;
- both alternatives survived;
- attribution remained correct;
- dangling reference remained unresolved;
- tentative idea did not become an action;
- repeated task was deduplicated; or
- later observation was not treated as an answer.

Capability checks supplement rather than replace the four semantic dimensions.

## Strict pass rule

A record passes strictly only when:

1. `format_valid` is true;
2. all four semantic dimensions are true; and
3. every record-specific capability check is true.

One failure makes the record fail. Aggregate strict pass rate is passed records divided by all records. No partial credit changes the strict rate.

## Reviewer workflow

1. Freeze the raw output artifact before scoring.
2. ChatGPT and Claude Code independently compare each output with the de-identified source, expected output, and private rubric.
3. Each records booleans, concise failure rationales, and failure labels.
4. Each reports an alignment status without seeing or rewriting the other's evidence when practical.
5. Matching scores become provisionally accepted.
6. Disagreements are reviewed against source-supported evidence.
7. Johnny decides only if alignment remains unresolved.
8. The adjudicated result is saved as a new version; the raw generation artifact remains unchanged.

Reviewers distinguish evidence alignment from action alignment. Agreement about scores does not automatically authorize a release or curriculum change.

## Validation decision rule

- Routine unscored or format-only outputs do not guide decisions.
- A declared checkpoint or curriculum comparison must identify the compared runs before semantic scoring.
- The same real-validation records and rubric version are used across compared runs.
- Report strict pass rate, per-dimension failures, per-record changes, format validity, and coverage.
- Do not select a seed after inspecting undeclared alternatives.
- Real-validation results supplement rather than replace the protected probe suite.

## Holdout decision rule

- One frozen candidate is declared before unsealing.
- Release gates are declared before generation.
- Strict semantic scoring is completed before the release decision.
- The holdout is used for go/no-go, not candidate selection.
- Once record-level results are inspected, the holdout version is consumed and cannot guide iterative retesting.

## Privacy and retention

- Evaluation logs are private and gitignored.
- Raw inputs and expected outputs need not be duplicated into the result artifact; `record_id` and fingerprints provide linkage.
- Generated outputs are treated as sensitive.
- Transient validation logs not used in a decision may be deleted under a documented retention rule.
- Decision-relevant validation logs and milestone holdout logs remain private and versioned.
- Withdrawal invalidates or redacts affected logs according to the governance specification.

## Failure labels

Use existing labels when available. New labels describe model behavior, not contributor traits. Examples include attribution error, unsupported action, unsupported commentary, dropped qualifier, unresolved-question loss, dangling-reference completion, task split, task merge, and format failure.

## Implementation acceptance tests

Before real evaluation begins, synthetic dummy tests must demonstrate:

- routine preparation never opens or creates a processed holdout;
- routine validation produces a structured JSON log;
- holdout evaluation requires an explicit milestone and checkpoint;
- holdout content is loaded only during that command;
- no persistent processed holdout remains afterward;
- dataset and checkpoint fingerprint mismatches fail closed;
- semantic score fields begin unscored;
- adjudicated scores produce the correct strict aggregate;
- private result paths are gitignored; and
- `git check-ignore` succeeds for every private source, sidecar, processed-validation, legacy processed-holdout, and results path;
- `git status --porcelain` does not list any dummy private artifact;
- training and production prompt-contract versions and rendered-prompt hashes match;
- checkpoint fingerprinting is deterministic across two runs and fails on symlinks or file changes;
- dataset fingerprinting is independent of manifest line order but changes after any active record or rubric change;
- withdrawal removes a dummy record and invalidates affected results.

## Alignment status

**ChatGPT revision 2 for Claude verification.**
