# Typed-proposition milestone 1 token-feasibility hard stop

**Date:** 2026-08-13  
**Status:** Hard stop triggered; milestone 1 must not continue under the approved proposal  
**Compute performed:** None; tokenizer-only static measurement  

## Result

The typed-plan-augmented representation does not fit the frozen target and generation limits.

| Split | Records | Input max | Target max | Targets >512 | Targets >300 |
|---|---:|---:|---:|---:|---:|
| Train | 72 | 382 | 941 | 23 | 54 |
| Validation | 6 | 345 | 488 | 0 | 6 |

All prompts fit the frozen 512-token input limit. The treatment targets fail both the 512-token training
target limit and the unchanged 300-token generation budget. The exact per-record failures and tokenizer
revision are recorded in `controlled_seed17_typed_proposition_token_feasibility.json`.

## Governing stop condition

Section 6 of the approved proposal requires complete token histograms and says: “If any record exceeds a
frozen token limit, stop. Do not shorten, omit, compress, or selectively exclude records after seeing
benchmark behavior. A larger token budget would be a second changed variable and needs a new proposal.”

Section 12 independently stops if any prompt, target, or generated output would truncate, or if
implementation would require a schedule/token-budget adjustment.

Therefore milestone 1 stops here. No schema compression, record omission, token-limit increase, schedule
change, model execution, benchmark execution, or compute proposal is authorized.

## Draft artifacts produced before the stop

The parser, static builder, 78 draft plans, draft split, and receipts are diagnostic feasibility artifacts
only. They are not frozen or approved training data. Independent semantic review was not completed and must
not be implied. They may be inspected to design a new bounded proposal, but cannot be executed.

## Decision required

Return to Johnny. A future proposal must choose and isolate one materially different representation design
that fits the existing limits, or explicitly treat a token-limit/budget change as its sole primary variable.
Neither path is authorized by this milestone.
