# Prompt Contract vNext — Evaluation and Acceptance Architecture

**Status:** Proposed; no fixtures frozen  
**Implementation authorized:** none  
**Compute authorized:** none  
**Purpose:** Separate contract representation from semantic intent recovery

## Why the evaluation must change

The first source-determined-bullets acceptance set mixed several questions in the same five cases:

- Did item boundaries survive decoding?
- Did the model produce the correct number of items?
- Did every idea survive?
- Were restatements deduplicated?
- Was unsupported content added?
- Did the seven-bullet ceiling hold?

When a case failed, the result often could not identify which layer caused it. vNext should use independent evaluation layers with separate gates.

## Four-layer architecture

### Layer 0 — tokenizer and parser round-trip

No model generation and no GPU compute.

Frozen strings are encoded, decoded, and parsed through both Python and browser stacks. Required checks:

- section markers survive exactly;
- typed item markers survive exactly;
- item order survives;
- item counts survive;
- empty actions survive as an empty array;
- Python and TypeScript return identical parsed structures;
- source text containing marker-like literals cannot alter output parsing;
- malformed structures fail closed.

Gate: 100% of fixtures pass.

### Layer 1 — generated structural conformance

Automatically scored from parsed output:

- required section markers present and ordered;
- no text outside the contract;
- narrative nonempty;
- no empty bullet/action entries;
- no action marker inside bullets or bullet marker inside actions;
- bullet count satisfies its `exact` or `max` rule;
- action count satisfies its rule;
- bullet count never exceeds seven;
- parse result is identical in Python and TypeScript for the saved raw output.

These checks must be computed, not manually typed as true.

Gate: 100% structural conformance on the vNext acceptance set and 16/16 format/parse validity on the protected benchmark.

### Layer 2 — semantic acceptance

Human-scored under the existing strict dimensions:

- topic completeness;
- attribution accuracy when applicable;
- uncertainty preservation when applicable;
- unsupported-addition resistance.

Record-specific capability checks cover semantic grouping, deduplication, deadline survival, no topic merge, and no observation/idea-to-action conversion.

Gate: every required dimension is 2 and every declared capability check is true for every acceptance case. No partial aggregate credit.

### Layer 3 — protected regression benchmark

Use the existing 16 probes, frozen wording, frozen `required_semantic_dimensions`, and strict scoring.

Gate:

- no same-seed Cell-A regression-guard pass becomes a candidate failure;
- candidate overall strict passes are not lower than Cell A;
- format/parse validity is 16/16.

## Acceptance-family specification

Actual prose must be authored later without copying protected benchmark wording, nouns, or sentence skeletons. Freeze cases only after independent review.

| Family | Structural purpose | Semantic purpose |
|---|---|---|
| One supported observation | Exactly one bullet, zero actions | No invented task or commentary |
| One explicit task | Exactly one bullet, one action | Task and material qualifier survive |
| Two unrelated ideas | Exactly two bullets | No merge or fragmentation |
| Mixed observation + task | Source-determined bullets, exactly one action | Observation does not become an action |
| Tentative idea | One bullet, zero actions | Tentativeness preserved |
| Open either/or question + later observation | Separate supported items | Observation does not answer question |
| Restated single task | One bullet, one action | Deduplicate while preserving deadline/recipient |
| Eight explicit tasks | At most seven bullets, exactly eight actions | No loss, merge, reassignment, or invention |
| Dangling reference | Source-determined count | Stop after source-supported content |
| Dense mixed note | Multiple bullets/actions | Attribution and all material qualifiers survive |

The eight-task ceiling case should not be the only test of large counts. Add a simpler parser-only fixture with eight typed actions, so a semantic failure cannot be mistaken for marker/count failure.

## Required case fields

Each generated-model acceptance record should include:

```json
{
  "id": "candidate-id",
  "status": "acceptance_gate",
  "input": "dummy source note",
  "expected_behavior": "semantic ground truth",
  "bullet_count_rule": {"operator": "exact", "value": 1},
  "action_count_rule": {"operator": "exact", "value": 0},
  "required_semantic_dimensions": ["topic_completeness", "unsupported_addition_resistance"],
  "primary_checks": ["record-specific boolean checks"],
  "likely_failures": ["canonical taxonomy labels"]
}
```

Allowed count operators in this proposal are `exact` and `max`; each record stores one literal operator, as shown above.

`action_count_rule` should be required, including explicit zero, so an omitted field cannot silently mean “not scored.” The same principle should apply to bullet count.

## Results-schema requirements

Every result must be self-contained and include:

- benchmark record ID and status;
- raw output;
- parsed narrative, bullets, and actions;
- parser/contract version;
- prompt-contract fingerprint;
- benchmark/dataset fingerprint;
- automatically computed structural checks and item counts;
- `required_semantic_dimensions` copied from the benchmark;
- semantic score scaffold;
- capability-check scaffold;
- failure-label scaffold;
- checkpoint fingerprint and generation settings in the run-level provenance.

The runner must reject unknown required dimensions, missing count rules, duplicate IDs, unknown structural operators, or mismatched prompt/contract fingerprints before generation.

## Scoring-completeness rule

A report is decision-eligible only when:

- every required semantic dimension is an integer 0, 1, or 2;
- every capability check is a literal boolean;
- all structural checks are computed booleans;
- the result record’s copied rubric metadata matches the frozen benchmark record;
- no result is missing or duplicated.

Generic null warnings should distinguish intentionally non-applicable dimensions from required-but-unscored dimensions.

## Runner/prompt separation

The benchmark runner must remain current while the prompt builder is pinned. Recommended design:

- current runner accepts an explicit prompt-builder module/path and expected contract fingerprint;
- it loads only `build_prompt`, markers, and contract version from that pinned module;
- result schema, validation, parsing, metadata propagation, and logging come from current reviewed code;
- a mismatch stops before model loading.

Do not execute `run_benchmark.py` from an old prompt worktree again.

## Decision sequence

1. Claude returns tokenizer/parser investigation.
2. ChatGPT and Claude align on the contract option.
3. Johnny approves the selected contract.
4. Claude builds dummy-only parsers, round-trip fixtures, runner separation, and cross-repo prompt parity.
5. ChatGPT reviews actual acceptance prose and rubric bindings.
6. Both mark the static package Aligned.
7. Johnny separately authorizes one seed-17 compute study.
8. Seed 73 remains conditional on seed 17 passing every gate.

## Current gate state

- Seed 73: blocked.
- Cell B1 ONNX evaluator: deferred; not useful for deployment until a viable contract candidate exists.
- App prompt PR: remains unmerged.
- New curriculum examples: blocked until representation is selected and static feasibility passes.
- Production checkpoint: unchanged.

## Alignment status

This architecture is a proposal. Claude should flag any disagreement about typed markers, parser parity, automated count computation, results schema, or runner separation before implementation begins.
