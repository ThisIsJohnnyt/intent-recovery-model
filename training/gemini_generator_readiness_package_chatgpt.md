# Gemini synthetic-candidate generator readiness package

**Date:** 2026-08-14  
**Author:** ChatGPT  
**Status:** Independently verified; six decisions recorded; Gate 2 dummy-only implementation authorized  
**Repository baseline:** `cdc8e8a1c886132340b61f6fe210dc487d0914ff` on `main`  
**Governing decoupling analysis:** `training/gemini_generator_aux_span_decoupling_risk_analysis_chatgpt.md`  

## 1. Purpose and authority boundary

This package specifies a bounded, paid-tier Gemini pilot that may propose synthetic candidate pairs for
independent human/AI review:

`synthetic messy note -> narrative + bullets + action items`

Gemini is a candidate generator only. It is not a reviewer, adjudicator, gold authority, corpus editor,
trainer, benchmark authority, or deployment decision-maker.

This document is a readiness proposal. Drafting or accepting it does not authorize:

- creating or changing a Google Cloud project, billing account, payment method, prepaid balance, or quota;
- accepting provider terms;
- enabling an API, creating or exposing a key, or making a network request;
- spending, generation, retries, or model substitution;
- candidate acceptance, corpus mutation, training, benchmark changes, release, or deployment; or
- staging, commit, or push.

Setup, implementation, dry-run validation, and the paid pilot are separate gates in Section 17.

## 2. Governing project decision

Johnny accepted Option A of the independently verified decoupling analysis on 2026-08-14:

- auxiliary-span validation is retired as a Gemini generator-readiness prerequisite;
- the failed auxiliary-span history remains preserved as negative and diagnostic evidence;
- candidate review operates on observable source/output behavior rather than latent span labels; and
- Sections 5-12 of the decoupling analysis are binding minimum constraints here.

This package does not relabel the auxiliary-span result as a success and does not reopen that closed path.

## 3. Current official-provider facts

These facts were checked on 2026-08-14 and must be rechecked immediately before setup and again before the
first paid request. Google may change models, prices, terms, and billing behavior.

### 3.1 Models

Google currently lists both selected model IDs as stable generally available models with no announced
shutdown date:

| Pilot arm | Exact model ID | Purpose |
|---|---|---|
| Capability arm | `gemini-3.7-flash` | Latest, most capable stable Flash candidate generator |
| Efficiency arm | `gemini-3.5-flash-lite` | Lower-cost structured candidate generator |

`gemini-3.6-flash` was considered but not selected. Google released `gemini-3.7-flash` to general
availability on 2026-08-13, describes 3.7 as its latest and most capable Flash model, describes 3.6 as the
previous-generation Flash model, and currently prices their standard paid text inference identically. The
capability arm therefore uses 3.7. Its very recent release strengthens—not weakens—the requirements to pin
the exact ID, verify endpoint/control support in the dummy implementation package, recheck status immediately
before execution, and stop on any substitution or changed terms.

Do not use `latest`, preview, experimental, image, live, agent, search-grounded, or substituted aliases.
The returned model/version identity must be captured. A mismatch stops the pilot.

Official sources:

- [Models](https://ai.google.dev/gemini-api/docs/models)
- [Latest Gemini models](https://ai.google.dev/gemini-api/docs/latest-model)
- [Deprecations](https://ai.google.dev/gemini-api/docs/deprecations)
- [Release notes](https://ai.google.dev/gemini-api/docs/changelog)

### 3.2 Paid pricing observed on 2026-08-14

Use standard synchronous inference only. Do not use batch, flex, priority, caching, search grounding, Maps,
URL context, code execution, file search, or any other billable or tool-enabled feature.

| Model | Paid input / 1M tokens | Paid output / 1M tokens |
|---|---:|---:|
| `gemini-3.7-flash` | $0.75 through 2026-12-31 | $3.75 through 2026-12-31 |
| `gemini-3.5-flash-lite` | $0.30 | $2.50 |

Google's pricing page states that output pricing includes thinking tokens. The 3.7 promotional prices are
scheduled to rise on 2027-01-01, so the execution receipt must pin the rates actually observed on execution
day rather than relying on this table.

Official source: [Gemini Developer API pricing](https://ai.google.dev/gemini-api/docs/pricing)

### 3.3 Billing behavior

Google currently describes new paid accounts as generally using Prepay, with a $10 minimum purchase. Unused
prepaid credits expire after 12 months and ordinarily are non-refundable. Google also warns that a roughly
ten-minute billing-pipeline delay can permit overages beyond the visible prepaid balance.

Therefore:

- a visible prepaid balance is not a hard technical spend control;
- auto-reload must be off;
- the runner must enforce its own request, token, and estimated-cost limits before every request;
- no other project or API key may share the pilot billing account during the execution window; and
- an unexpected Prepay/Postpay assignment or existing shared usage stops setup for Johnny's review.

Official source: [Gemini API billing](https://ai.google.dev/gemini-api/docs/billing)

### 3.4 Data use and terms

Google's current terms distinguish unpaid and paid services. For unpaid services, submitted content and
responses may be used to improve Google products and may be reviewed by humans. For paid Gemini API use
through a project with active billing, Google says prompts and responses are not used to improve its products,
although limited logging may occur for abuse prevention, safety/security, and legal obligations.

This pilot must use paid-tier requests only. Even then, it sends only synthetic instructions and abstract
mechanism cards—never private notes, protected records, held-out text, or repository files.

Johnny must personally review and accept the then-current provider terms during setup. Neither AI may accept
terms on his behalf.

Official sources:

- [Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms)
- [Gemini API billing](https://ai.google.dev/gemini-api/docs/billing)

## 4. Pilot hypothesis and interpretation limit

The pilot asks one narrow question:

> Can two predeclared stable Gemini variants produce a useful yield of safe, reviewable synthetic candidate
> pairs under one frozen prompt, twelve frozen mechanism cards, strict structured output, and sealed
> independent review?

A successful pilot supports only a later candidate-adjudication/conversion proposal. It does not establish:

- that any candidate is gold;
- that the production model can learn the candidates;
- that Gemini is more trustworthy than project reviewers;
- that stronger base-model capacity is or is not needed;
- that auxiliary-span validation succeeded; or
- that larger-scale generation is warranted.

## 5. Frozen experimental design

### 5.1 Two-model paired design

Run the same twelve mechanism cards once against each exact model:

- 12 cards x `gemini-3.7-flash` = 12 raw responses;
- 12 cards x `gemini-3.5-flash-lite` = 12 raw responses;
- maximum total = 24 raw responses.

Each model/card pair has exactly one semantic attempt. Do not regenerate an unsatisfactory, refused,
malformed, blocked, or low-quality response. Record it and continue only if no global stop condition fired.

The order must be deterministically interleaved from a precommitted schedule so neither model receives all
early or late requests. The implementation package must freeze that schedule before any API call.

### 5.2 Twelve mechanism cards

Cards specify abstract construction constraints, not literal examples. The exact card text below is frozen.

| ID | Mechanism card |
|---|---|
| `M01` | A hurried morning note mixing one observation, two unrelated tasks, and an unresolved scheduling question. Include one corrected detail and one pronoun whose referent remains genuinely ambiguous. |
| `M02` | A work-meeting capture containing a decision, a tentative idea, a delegated follow-up, a personal reminder, and a deadline that applies to only one task. |
| `M03` | A home-maintenance note with a current condition, a past failed attempt, a vendor callback expectation, two next steps in order, and one uncertain cause that must stay uncertain. |
| `M04` | A caregiving coordination note with two people, one quoted request, one medication-free health observation, one conditional task, and one detail that must remain attributed to its speaker. |
| `M05` | A travel-planning note with alternatives, a quantity, a destination, a time window, one explicit booking task, and one open question that must not become a recommendation. |
| `M06` | A creative-project note that jumps between current state, desired outcome, discarded idea, concrete next action, and a dependency on another person's response. |
| `M07` | A household-shopping note with inventory facts, preferences, a budget constraint, two purchases, and one item explicitly marked as optional rather than required. |
| `M08` | A client-follow-up note with a factual recap, an unresolved interpretation, one promised action by the writer, one requested action by the client, and separate dates for each. |
| `M09` | A community-event note with location uncertainty, a confirmed responsibility, a possible volunteer, a quantity estimate, and a condition that would cancel one task. |
| `M10` | A learning/research note with a source claim, the writer's doubt, two questions, one experiment to run, and one finding that must not be upgraded into a general conclusion. |
| `M11` | A personal-finance administration note with no financial advice: include a statement to verify, a document to locate, a call to make, a due date, and one number whose meaning is explicitly uncertain. |
| `M12` | A dense end-of-day brain dump with three topic shifts, one incomplete fragment, one self-correction, one completed action, two future tasks, and one thought that belongs only in narrative context. |

Do not modify, replace, or redraw a card after responses are seen. A card that triggers a refusal or cannot be
rendered safely remains part of the result.

## 6. Literal prompt contract

The implementation package must render exactly two messages. Line endings are canonical LF and text is UTF-8
without BOM. The only substitution is the mechanism-card block in the user message.

### 6.1 System instruction

```text
You generate one synthetic training-candidate pair for a note-organization research pilot.

Your authority is limited to inventing a fictional messy source note and a faithful organized rendering of that same fictional note. Never claim the pair is approved, accepted, gold, safe, reviewed, or suitable for training.

Return only the JSON object required by the response schema.

The source_input must:
- be wholly fictional and contain no real private data;
- read like a plausible messy human note rather than polished prose;
- follow the supplied mechanism card without copying its wording;
- contain enough explicit evidence for the organized output;
- preserve genuine ambiguity, uncertainty, questions, corrections, and incomplete thoughts where requested;
- avoid medical advice, legal advice, financial advice, diagnosis, crisis content, sexual content, hate, wrongdoing instructions, secrets, credentials, and identifying personal data; and
- not mention this prompt, schemas, models, reviewers, datasets, benchmarks, protected sets, or training.

The proposed_output must:
- organize only information supported by source_input;
- use narrative for contextual state, observations, uncertainty, and incomplete thoughts;
- use bullets for concise non-action facts, decisions, questions, and reference details;
- use action_items only for explicit or strongly recoverable future actions;
- preserve attribution, ownership, chronology, conditions, quantities, destinations, and uncertainty;
- never invent facts, people, causes, certainty, recommendations, deadlines, recipients, or tasks;
- never resolve an ambiguous reference unless source_input resolves it;
- avoid accidental duplication across fields;
- use calm, respectful, non-diagnostic language; and
- contain no commentary outside the three required fields.

Before returning JSON, silently verify that every organized claim is supported by source_input and every explicit task in source_input survives in action_items. Do not reveal hidden reasoning or add confidence scores.
```

### 6.2 User message template

```text
Create exactly one synthetic candidate using this frozen mechanism card:

MECHANISM_ID: {{MECHANISM_ID}}
MECHANISM_CARD: {{MECHANISM_CARD}}

Keep source_input between 80 and 220 words. Keep narrative between 1 and 4 sentences. Return 2 to 8 bullets and 1 to 6 action_items. Each list item must be a plain string.
```

The renderer substitutes only a listed ID and its verbatim card. Unknown IDs, altered cards, unescaped
placeholders, noncanonical newlines, or prompt-hash drift stop before network use.

## 7. Exact structured-output schema

Use provider structured output with MIME type `application/json`. The schema is:

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "source_input": {
      "type": "string",
      "description": "A wholly fictional messy note containing only the evidence used by proposed_output."
    },
    "proposed_output": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "narrative": {
          "type": "string",
          "description": "Contextual state, observations, uncertainty, and incomplete thoughts faithfully organized from source_input."
        },
        "bullets": {
          "type": "array",
          "minItems": 2,
          "maxItems": 8,
          "items": { "type": "string" }
        },
        "action_items": {
          "type": "array",
          "minItems": 1,
          "maxItems": 6,
          "items": { "type": "string" }
        }
      },
      "required": ["narrative", "bullets", "action_items"]
    }
  },
  "required": ["source_input", "proposed_output"]
}
```

Google documents structured JSON output and `additionalProperties`, but also says schema-valid JSON still
requires application validation. The local parser must independently enforce every field, type, count,
length, control-character, and extra-key rule.

Official source: [Structured outputs](https://ai.google.dev/gemini-api/docs/structured-output)

## 8. Request configuration

The implementation package must pin the exact API surface and request serialization after a no-key local
fixture test. At minimum, every request must enforce:

- exact stable model ID from Section 3.1;
- one system instruction and one user message from Section 6;
- structured JSON schema from Section 7;
- standard synchronous text generation only;
- no tools, grounding, browsing, retrieval, URLs, file upload, caching, functions, or multi-turn history;
- one returned candidate only;
- `thinking_level: minimal` if supported by the selected exact endpoint/model combination;
- no explicit `temperature`, `top_p`, or `top_k` for Gemini 3.x;
- maximum output-token setting of 2,048;
- non-streaming response; and
- request timeout and transport behavior frozen before execution.

Google notes that `minimal` thinking does not guarantee zero reasoning and that output charges include
thinking tokens. Returned usage metadata therefore controls the ledger; no cost estimate may assume thinking
is free or absent.

If either exact model or endpoint rejects a common required control, stop before the paid pilot rather than
silently giving the two arms different settings.

## 9. Local validation before and after network use

### 9.1 Before each request

Fail closed unless all checks pass:

1. repository baseline and required artifact hashes match;
2. provider facts were rechecked and recorded that day;
3. paid project/tier, exact billing plan, positive prepaid balance, and auto-reload-off state were manually
   attested without recording account numbers or secrets;
4. no other key/project shares pilot spend during the window;
5. exact model remains available and not newly deprecated;
6. rendered prompt hash matches the precomputed model/card schedule;
7. protected/quarantine pool files, counts, and canonical hashes match;
8. prompt collision screening passes;
9. request number, token ceiling, and estimated worst-case charge fit every remaining cap; and
10. API key exists only in the approved local environment and is not printable by the runner.

### 9.2 After each response, before semantic review

Record the raw response and immutable receipt, then fail or quarantine as applicable:

- HTTP/API status, provider request ID if returned, model/version identity, finish/block reason;
- prompt hash, schema hash, mechanism ID, schedule position, and model arm;
- input, output, cached, and thinking token counts when returned;
- rate-snapshot identity and estimated charge;
- raw-response hash and parsed-payload hash;
- exact schema and local semantic-size validation;
- prompt-imitation and protected/quarantine collision results; and
- duplicate/similarity results against all earlier pilot candidates.

Never log the API key, authorization headers, billing identifiers, full environment, or secret-store paths.

## 10. Leakage and quarantine contract

### 10.1 Complete excluded pools

Never transmit or use as prompt examples:

- Protected-16;
- Acceptance-10 and other held-out acceptance texts;
- all 10 regression and 5 fresh records in the auxiliary-span validation manifests;
- the associated targets, annotations, receipts, disagreement records, and worked resolutions;
- treatment-delta records;
- benchmark/held-out candidates designated later;
- any real user/private note; or
- repository document/code contents.

The five fresh locators remain explicitly quarantined:

`comparator:012, comparator:073, comparator:008, comparator:030, comparator:018`.

### 10.2 Prompt-side collision preflight

Screen the fully rendered literal prompt against every quarantined source and target using the project's
frozen normalization:

- normalized exact equality: stop;
- normalized containment at 20+ characters: stop;
- token Jaccard `>= 0.15`: stop;
- character-5-gram Jaccard `>= 0.10`: stop.

Missing files, unexpected counts, hash drift, BOM, mixed line endings, bare CR, missing terminal newline, or
collision stops before network transmission.

### 10.3 Output-side screening

Apply the same checks to the generated source and every output field against the complete quarantine pool
and earlier candidates. A threshold crossing rejects and quarantines the response. Do not show it as normal
review evidence and do not regenerate it.

Log named-entity, quantity, temporal-phrase, clause-order, and role-combination similarities for human review
even below fatal lexical thresholds. Generated content never becomes a later same-pilot prompt example.

## 11. Cost and token ledger

### 11.1 Hard caps

- 24 raw response slots;
- 12 slots per exact model;
- 1 semantic attempt per model/card pair;
- maximum 2,048 configured output tokens per request;
- maximum 4,000 locally estimated input tokens per request;
- verified prepaid account balance at execution start: `$10.00` absolute account cap;
- hard cumulative pilot charge ceiling: `$3.00`;
- mandatory reconciliation stop before the next request at `$2.25` cumulative actual-plus-reserved cost;
- no auto-reload, quota increase, add-on, plan change, or manual credit purchase during the pilot.

At the observed 2026-08-14 standard rates and the extreme local ceilings of 4,000 input plus 2,048 output
tokens per call, all 24 scheduled calls estimate to exactly `$0.204`, below `$0.25`. The `$3.00` pilot ceiling
is contingency room, not permission for extra slots, models, semantic retries, redraws, or expanded token
limits. The remaining `$7.00` of the prepaid balance stays outside pilot authority. This is planning evidence
only; the runner must use execution-day prices and provider usage metadata.

### 11.2 Pre-request reservation

Requests execute strictly sequentially. Before each call, reserve worst-case cost using:

`estimated_input_tokens * current_input_rate + max_output_tokens * current_output_rate`

Do not send if cumulative actual charges plus outstanding reservations and the next reservation would exceed
`$2.25`. The runner never proceeds into the `$2.25`-to-`$3.00` band without a new, separately scoped decision.
It must never exceed `$3.00` under any circumstance. Unknown/missing usage or pricing data stops further
requests and conservatively leaves the full reservation charged to the local ledger.

The append-only local cost ledger stores monetary values as integer millionths of a US dollar, never binary
floating point. Each row records:

- model, mechanism ID, schedule slot, and execution-day rate snapshot hash;
- fixed maximum input/output tokens and pre-request reserved cost;
- provider-reported input, visible-output, thinking, cached, tool-use, and total tokens where returned;
- calculated actual cost, cumulative actual cost, outstanding reservations, and remaining pilot authority;
- response/request/receipt hashes, disposition, and stop or retry reason; and
- the prior ledger-row hash, creating a tamper-evident chain.

After each response, the runner writes and verifies the ledger row before another request can begin. It
prices billable output as visible-output plus thinking tokens unless the execution-day official pricing/API
contract states a stricter calculation. Missing or internally inconsistent usage fields stop the run. The
ledger contains no key, authorization header, account number, payment data, or billing identifier.

### 11.3 Retry policy

No semantic retry exists. A transport retry is allowed only if all are true:

- the provider confirms no usable response was produced;
- official billing guidance indicates the failed request is not charged;
- the same request body/hash is reused unchanged;
- the retry is separately logged;
- the raw slot and budget caps still hold; and
- ChatGPT and Claude agree the event is mechanical rather than outcome-guided.

Otherwise the slot remains failed. No replacement request is drawn.

## 12. Mechanical rejection ledger

Maintain an append-only record keyed by request and raw-response hash. Mechanical reason codes include:

- `provider_blocked`
- `transport_failed_no_retry`
- `model_identity_mismatch`
- `finish_reason_invalid`
- `schema_invalid`
- `extra_key`
- `size_limit_failed`
- `prompt_imitation`
- `protected_collision`
- `pilot_duplicate`
- `secret_exposure`
- `budget_or_usage_unknown`
- `manual_global_stop`

Every entry records disposition as exactly `rejected`, `quarantined`, or `candidate_pool`, with a statement
that no corpus mutation occurred. Mechanical rejection is evidence and is never erased or replaced.

## 13. Sealed independent candidate review

ChatGPT and Claude independently review every mechanically valid candidate. Claude seals its categorical
pass and hash before opening ChatGPT's verdict. Each dimension is `pass`, `fail`, or `not_applicable` with a
short candidate-local rationale:

1. schema validity;
2. source interpretability;
3. independent-content retention;
4. task fidelity;
5. uncertainty/question preservation;
6. attribution/reference fidelity;
7. chronology/qualifier fidelity;
8. unsupported-addition resistance;
9. field appropriateness;
10. duplication/control compliance; and
11. tone/safety.

Every applicable dimension and the final `accept` verdict must agree and pass for a candidate to enter the
reviewed candidate pool. Everyday words such as recipient, deadline, destination, speaker, or quantity may
appear in holistic rationales; they do not recreate formal per-proposition auxiliary labels.

Any categorical disagreement, escalation, or material rationale conflict quarantines the candidate and goes
to Johnny. No majority, average, reviewer override, or harmonization is permitted. Agreement creates only
candidate-pool status, never gold or corpus membership.

## 14. Batch decision gates

Freeze these gates before outputs:

1. **Integrity:** zero protected collisions, prompt leakage, secret exposure, pool-pin failure, model
   substitution, unlogged retry, or budget breach. One occurrence stops the pilot.
2. **Completion:** all 24 scheduled slots have an immutable result: raw response, provider-declared failure,
   or authorized mechanical transport outcome. No replacement slots.
3. **Reviewability:** every mechanically valid response receives two sealed reviews.
4. **Agreement:** at least 22 of 24 raw slots produce candidates with matching final reviewer verdicts.
   Quarantined disagreements still go to Johnny; the number does not override one.
5. **Yield:** at least 6 candidates enter the reviewed candidate pool, including at least 2 from each model
   arm if that arm completed its scheduled calls.
6. **Safety:** every pooled candidate passes every applicable dimension for both reviewers. One unsupported
   addition, falsely resolved uncertainty, lost explicit task, or attribution reversal rejects that
   candidate.
7. **No promotion:** success authorizes only a later adjudication/conversion proposal.

If a global integrity stop prevents 24 slots, report an incomplete failed pilot. Do not rescale thresholds.
Provider refusals and ordinary schema failures occupy their frozen slots and count against the batch gates.

## 15. Global stop conditions

Stop and return to Johnny on:

- unclear or changed provider terms, data use, privacy, retention, billing, pricing, or model behavior;
- unpaid-tier routing or inability to prove paid-tier routing;
- shared billing activity, Postpay surprise, auto-reload, or inability to isolate the `$10` prepaid account
  balance and `$3` pilot authority;
- any private/quarantined transmission attempt or collision;
- key/secret exposure;
- model ID/version substitution or new deprecation;
- prompt, schema, parser, schedule, pool, or artifact hash drift;
- unsupported request controls or asymmetric settings between model arms;
- usage metadata missing where required for cost control;
- request/token/spend cap risk or breach;
- temptation to tune cards/prompt after seeing output;
- reviewer unblinding before sealing;
- material ChatGPT/Claude disagreement; or
- proposal to promote candidates automatically.

A stop authorizes no workaround, replacement, retry, extra model, prompt edit, or additional spend.

## 16. Required frozen artifacts before any paid request

A later implementation package must create and independently verify, without network/model use:

1. exact prompt and schema files with canonical hashes;
2. twelve-card mechanism manifest and deterministic 24-slot schedule;
3. complete quarantine manifest with canonical hashes and counts;
4. prompt/output collision-screen implementation plus adversarial fixtures;
5. strict response parser/schema validator plus malformed fixtures;
6. cost calculator with execution-day rate snapshot and boundary fixtures;
7. secret-redacting request runner with mocked provider fixtures;
8. append-only request/rejection receipt formats;
9. sealed-review schema, validator, and comparison tool;
10. setup-attestation template that stores no sensitive identifiers; and
11. full dummy-only dry-run receipt proving zero network use.

No API key is required or permitted for this implementation/dry-run stage.

## 17. Separate authorization gates

### Gate 1 — accept this readiness design

Accepts the design only. No setup, implementation, or external action.

### Gate 2 — authorize dummy-only implementation package

Permits local code/artifact drafting and mocked validation. No key, network, billing, model call, or spend.

### Gate 3 — authorize guided provider setup

Johnny performs interactive account/project/billing/terms/key steps with guidance. This gate must name which
specific setup actions are authorized. No inference request is included unless separately explicit.

### Gate 4 — authorize one zero-content connectivity check, if still necessary

Only after setup verification. It must use no repository/private/held-out content, consume the minimum
possible tokens, and have a separately stated cost/request cap. Prefer official non-inference status/model
listing if it can verify connectivity without generation.

### Gate 5 — authorize the frozen paid pilot

Permits only the exact 24-slot schedule after all local artifacts, provider facts, billing state, and setup
attestations are verified. No candidate promotion follows automatically.

### Gate 6 — decide next direction from the sealed result

Options include stop, revise in a new proposal, adjudicate candidate-pool conversion, or prioritize Track B.
No outcome carries automatic authority forward.

## 18. Relationship to Track B

Track B remains a separate deferred no-training capability audit comparing model classes under a frozen
panel. Do not require it before this bounded generator pilot, and do not interpret generator yield as a
production/training base-model capacity result.

If reviewed candidates are strong but the pinned baseline cannot learn or execute the observable contract,
that would support separately proposing Track B. If Gemini candidates fail, conclude only that this frozen
generator setup was unproductive.

## 19. Decisions requested from Johnny after independent review

1. Accept or reject the two-model paired pilot (`gemini-3.7-flash` and
   `gemini-3.5-flash-lite`).
2. Accept or reject the twelve mechanism cards and one-attempt/no-redraw rule.
3. Accept or reject the literal prompt, schema, and no-tools request contract.
4. Accept or reject the leakage, ledger, sealed-review, and decision gates.
5. Accept or reject the cost controls and proposed monetary boundaries.
6. If 1-5 are accepted, decide whether to authorize Gate 2 only: a dummy-only implementation package.

Provider setup and paid execution must remain unselected at this decision point.

## 20. Requested independent review

Claude should verify against primary project artifacts and current official Google sources:

- governing decoupling decision and all authority boundaries;
- exact model status, model IDs, current standard paid prices, billing behavior, and data-use claims;
- whether the selected paired models answer a useful bounded question;
- mechanism-card coverage and absence of outcome-guided examples;
- prompt/schema completeness and provider support;
- collision screens and quarantine completeness;
- cost arithmetic, retry policy, and 24-slot gate consistency;
- whether the candidate review dimensions retain necessary semantic safety without recreating aux labels;
- whether the implementation artifact list is sufficient for a fail-closed dummy run; and
- whether setup, API use, spending, generation, and corpus mutation remain separately gated.

Material disagreement stops this package and returns to Johnny. Review agreement alone did not accept the
six decisions or authorize implementation; Johnny's subsequent decisions are recorded separately in Section
21. Review never permits Gemini activity, staging, commit, or push.

## 21. Decision record

On 2026-08-14, after independent review converged and the `gemini-3.7-flash` completeness finding was
corrected and re-verified, Johnny considered the six Section 19 decisions one at a time and decided:

1. **Accepted:** paired pilot using exact stable IDs `gemini-3.7-flash` and
   `gemini-3.5-flash-lite`.
2. **Accepted:** twelve frozen mechanism cards, one semantic attempt per model/card pair, no outcome-guided
   retry, redraw, or replacement.
3. **Accepted:** literal prompt, strict JSON schema, and no-tools request contract.
4. **Accepted:** leakage protections, append-only rejection ledger, sealed independent reviews, and
   fail-closed decision gates.
5. **Accepted with Johnny's modification:** treat the existing `$10.00` prepaid balance as the absolute
   account cap, enforce a `$3.00` hard pilot ceiling and `$2.25` mandatory reconciliation stop, keep
   auto-reload off, and permit no other billing-account activity during execution. The additional contingency
   does not expand the frozen request, model, retry, redraw, or token limits.
6. **Authorized:** Gate 2, the dummy-only local implementation package listed in Section 16.

Decision 6 permits local drafting and mocked validation of the eleven Section 16 artifacts without an API
key or network/model use. It does not authorize provider setup, terms acceptance, project or billing changes,
API enablement, key creation or handling, connectivity checks, spending, generation, candidate review,
candidate acceptance, corpus mutation, training, benchmark changes, release, deployment, staging, commit,
or push. Gates 3-6 remain separately gated exactly as written.
