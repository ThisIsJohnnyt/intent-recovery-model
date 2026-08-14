# Gemini generator readiness — auxiliary-span decoupling risk analysis

**Date:** 2026-08-14  
**Author:** ChatGPT  
**Status:** Independently verified; Option A accepted by Johnny  
**Repository baseline:** `cdc8e8a1c886132340b61f6fe210dc487d0914ff` on `main`  

## 1. Decision proposed

Retire validated auxiliary-span supervision as a prerequisite for the Gemini synthetic-candidate generator,
while preserving the entire auxiliary-span history as negative and diagnostic evidence.

Replace that prerequisite with a simpler candidate-level review contract that evaluates the only artifact the
generator is actually being asked to propose:

`messy source note -> narrative + bullets + action items`

This is a decoupling decision, not a claim that the auxiliary-span guide passed. It did not pass. It is also
not permission to generate data, create an account, spend money, mutate a corpus, train a model, or promote a
candidate to gold.

## 2. Evidence and pins

| Evidence | SHA-256 / commit |
|---|---|
| Current `main` | `cdc8e8a1c886132340b61f6fe210dc487d0914ff` |
| Final revision-3 closure | `72d6b4137c7605a68d584cf71029054b27e8774a086f070377e1317f145d9132` |
| Revision-3 annotation guide | `96311377b1caa4a3efccb901b557508f85e65b0ce18d1c239da902296d12df82` |
| Original validation manifest | `6314b4336e0fac4a52735f0072ce82a2d5ba44f65a90ef536628a7d34d70dcb5` |
| Supplemental validation manifest | `3e265857720cc48da6a618d9a534dfa3e69658c869858b1a65170e3bc0ff0467` |
| Discovery plan, including Track B | `f619a068a0f95ebecd02d5dd475fca7a38dab0612499ea69c3ced6297ac19c8d` |
| Previous-work handoff with generator workflow | `1418c2f67d32fe0bbac2d05f8a6facd2ad9809b8b7cce1dea4708dbc84a2613d` |

The auxiliary-span sequence improved exact agreement from 2/14 records to 12/15 but ended with seven
substantive decisions across three records and zero agreed fresh empty-field propositions. Both frozen
semantic gates failed. No further local correction or redraw remains.

## 3. What the auxiliary-span work proved and did not prove

### 3.1 Proven and retained

The process repeatedly demonstrated that ChatGPT and Claude can execute a strong sealed-review method:

- inputs and instructions can be frozen and fingerprinted;
- reviewers can work independently and seal hashes before comparison;
- schema and boundary checks can fail closed;
- disagreements can be preserved rather than harmonized;
- mechanical leakage checks and quarantine lists can be independently reproduced; and
- Johnny can adjudicate genuinely material policy decisions without either reviewer self-authorizing them.

That process evidence transfers directly to candidate review.

### 3.2 Failed and retired from this path

The work did not validate a proposition-span annotation contract. Therefore:

- do not annotate the full corpus with revision 1, 2, or 3;
- do not use auxiliary spans, states, roles, qualifiers, coreference labels, duplicate links, or per-
  proposition field obligations as generator outputs, prompt examples, gold labels, or acceptance gates;
- do not train an auxiliary-span head from these artifacts;
- do not claim the 12/15 result is a pass; and
- do not reopen the closed guide-correction sequence under a new filename while calling it the same milestone.

The history stays committed. Retirement means “not required or used for Gemini candidate readiness,” not
“deleted,” “wrong,” or “never useful diagnostically.”

## 4. Why decoupling is proportionate

The generator does not need to produce proposition spans or adjudicate latent structure. Its authority is
strictly narrower: propose synthetic input/output pairs for humans/independent reviewers to examine.

The final disagreements were finer-grained than the candidate decision:

- whether a paraphrastic bullet realizes one specific source clause;
- whether a cognition phrase receives `actor` or `experiencer`;
- whether an inferred task inherits target-side object/recipient roles; and
- whether `tonight` is time or a deadline on an inferred action.

Those distinctions matter if auxiliary labels become training truth. They are not necessary to decide whether
a candidate output preserves tasks, uncertainty, attribution, and source meaning without invention.

Keeping the failed span gate as a prerequisite would make a non-deliverable representation block evaluation
of a different, narrower hypothesis: whether an independent generator can propose useful candidate pairs
under strict review. Removing it does not lower the output-safety bar; it moves the bar to observable
candidate behavior.

## 5. New minimal candidate contract

The later generator-readiness package should freeze an exact JSON schema with no additional fields. At the
conceptual level, one candidate contains:

```json
{
  "source_input": "synthetic messy note",
  "proposed_output": {
    "narrative": "...",
    "bullets": ["..."],
    "action_items": ["..."]
  }
}
```

The execution wrapper—not Gemini—adds immutable provenance:

- `candidate_id` and `batch_id`;
- provider/model/version identifier returned by the API;
- prompt-template hash and request-mechanism ID;
- generation timestamp;
- input/output token counts and billed/estimated cost;
- raw-response hash; and
- parser/schema result.

Prohibit generator-authored reviewer labels, auxiliary spans, acceptance claims, confidence scores,
chain-of-thought, gold status, or mutation instructions. If extra keys appear, reject the candidate rather
than silently stripping them.

## 6. Candidate-level sealed review contract

ChatGPT and Claude review the same frozen candidate independently. Claude must seal its categorical pass
before opening ChatGPT's verdict. Review uses candidate-level dimensions, not proposition annotations.

Each dimension is exactly `pass`, `fail`, or `not_applicable`, with a short candidate-local rationale:

1. **Schema validity** — exact fields/types, output limits, no extra sections.
2. **Source interpretability** — messy is allowed; unrecoverable nonsense is not.
3. **Independent-content retention** — every meaningful source topic/state survives somewhere appropriate.
4. **Task fidelity** — explicit and recoverable tasks survive; no source fact/question is silently promoted.
5. **Uncertainty/question preservation** — ambiguity, alternatives, incomplete thoughts, and open questions
   are not falsely resolved.
6. **Attribution/reference fidelity** — people, speakers, recipients, ownership, and unresolved references
   are not reassigned or invented.
7. **Chronology/qualifier fidelity** — dates, timing, deadlines, conditions, destinations, quantities, and
   modifiers retain their observable meaning.
8. **Unsupported-addition resistance** — no new facts, tasks, causes, certainty, or specifics.
9. **Field appropriateness** — narrative/bullets/actions serve their contracted purpose without requiring
   agreement on latent span labels.
10. **Duplication/control compliance** — no accidental duplicates, instruction leakage, protected text, or
    prompt imitation.
11. **Tone/safety** — calm, respectful, non-diagnostic, non-patronizing.

Hard acceptance rule:

- every applicable dimension passes for both reviewers;
- both final verdicts are `accept`;
- any categorical disagreement, `escalate`, or material rationale conflict quarantines the candidate for
  Johnny; and
- reviewer agreement only places a candidate in a **reviewed candidate pool**, never directly in gold,
  training, acceptance, protected, benchmark, or release data.

No majority vote, average score, or one-reviewer override exists.

## 7. Leakage and quarantine protections

### 7.1 Never sent to Gemini

The literal prompt, examples, feedback, and retry context must exclude:

- Protected-16;
- Acceptance-10 and other held-out acceptance texts;
- all ten regression records and five fresh records from the auxiliary-span validation manifests;
- their committed targets, annotations, receipts, disagreements, and worked resolutions;
- failed treatment-delta records;
- private/user notes; and
- any benchmark or candidate designated held out later.

The five fresh locators remain quarantined exactly as committed:

`comparator:012, comparator:073, comparator:008, comparator:030, comparator:018`.

### 7.2 Input-side prompt preflight

Before an API request, hash and collision-screen the fully rendered literal prompt—not just the template—
against every quarantined source and target. Use the project's frozen normalization plus:

- normalized exact equality: stop;
- normalized containment at 20+ normalized characters: stop;
- token Jaccard `>=0.15`: stop;
- character-5-gram Jaccard `>=0.10`: stop.

The readiness package must pin the pool counts/content hashes and record the prompt hash. Missing pool files,
unexpected counts, hash drift, mixed line endings, or a collision stops before network transmission.

### 7.3 Output-side preflight

Apply the same screen to every generated source and proposed output against the complete quarantine pool and
against earlier candidates in the same pilot. Any threshold crossing rejects and quarantines the candidate;
no reviewer sees it as normal evidence and no regeneration is attempted from the rejected text.

Named-entity, quantity, temporal-phrase, clause-order, and role-combination similarities must also be logged
for human review even when lexical thresholds do not fire. No generated candidate becomes an example in a
later prompt during the same pilot.

### 7.4 Rejection ledger

Maintain an append-only ledger keyed by candidate/raw-response hash with:

- mechanical rejection reason codes;
- reviewer categorical results and sealed pass hashes;
- Johnny adjudication, if any;
- disposition (`rejected`, `quarantined`, `candidate_pool`); and
- explicit statement that no corpus mutation occurred.

Do not store secrets or API keys in the ledger or repository.

## 8. Pilot limits and spending boundaries

This proposal performs no API activity. A later readiness package must verify current model availability,
official pricing, terms, data-use/privacy settings, regional availability, and billing behavior from current
official Google sources before recommending exact model IDs.

Recommended later pilot ceiling:

- at most 12 frozen mechanism requests;
- at most 2 predeclared Gemini model variants;
- one candidate per request/model, at most 24 raw candidates total;
- no automatic semantic retry or “try again” prompt;
- exact per-request input/output token ceilings frozen before execution;
- hard cumulative API charge ceiling of **$10 USD or the available prepaid balance, whichever is lower**;
- stop at 80% of the monetary ceiling for manual reconciliation before any remaining requests;
- no auto-recharge, quota increase, paid add-on, or billing-plan change; and
- transport retries only if the provider confirms no usable/billable response was produced, with every retry
  separately logged and still inside the request/count/cost ceilings.

Creating a cloud project, linking billing, accepting terms, enabling an API, creating a key, or making a test
request each remains separately authorized setup activity. Secrets must live in an approved local secret
store/environment, never chat, Git, bridge files, logs, screenshots, or prompt artifacts.

## 9. Recommended bounded-pilot decision gates

The later readiness package may tighten these values but must not loosen them after outputs are seen.

1. **Integrity gate:** zero protected/prompt collisions, secret exposure, pool-pin failure, model substitution,
   unlogged retry, or budget breach. Any occurrence stops the entire pilot.
2. **Reviewability gate:** all parsed candidates receive two sealed independent passes; missing reviews block
   batch conclusions.
3. **Agreement gate:** categorical agreement on at least 22 of 24 raw candidates. Any material disagreement
   still goes to Johnny; the numeric threshold does not override one.
4. **Yield gate:** at least 6 candidates enter the reviewed candidate pool, with at least 2 accepted from each
   model variant if both variants complete their frozen requests.
5. **Safety gate:** every accepted candidate passes all eleven applicable dimensions for both reviewers; one
   unsupported addition, falsely resolved uncertainty, lost explicit task, or attribution reversal rejects
   that candidate.
6. **No-promotion gate:** pilot success supports only a later proposal for candidate adjudication/conversion.
   It does not authorize gold insertion, training, benchmark changes, release, or deployment.

If fewer than 24 raw candidates are produced because an integrity stop fires, do not rescale percentages or
replace missing requests. Report the incomplete pilot.

## 10. Stop conditions

Stop and return to Johnny on:

- unclear Google terms, data retention/use, billing, privacy, or model-version behavior;
- any attempt to transmit private or quarantined text;
- prompt or output collision;
- secret/key exposure;
- schema/parser drift or extra model-authored authority fields;
- API model substitution or version drift after freeze;
- cost/token/request ceiling risk or breach;
- generator refusal patterns that tempt prompt tuning after outputs;
- reviewer unblinding before sealing;
- missing/changed artifacts or fingerprints;
- material ChatGPT/Claude disagreement;
- any proposal to turn candidate-pool status into gold automatically; or
- evidence that the simpler review contract cannot reliably detect meaning loss or invention.

No stop condition authorizes a workaround, new prompt, replacement candidate, extra model, or additional
spend.

## 11. Relationship to discovery-plan Track B

Track B remains valid and deferred. It asks whether stronger base models materially outperform the current
FLAN-T5 class under a frozen no-training capability audit. The Gemini generator asks whether an independent
source can propose usable synthetic candidates under review. These are different levers and must not be
conflated.

Recommendation:

- do not require the full 36-example Track B model panel before the bounded $10 generator pilot;
- do not use generator acceptance yield as evidence that the production/training base model has enough
  capacity;
- preserve Track B for a separately authorized audit if downstream evidence points to capacity—for example,
  reviewed candidates are high quality but the pinned baseline consistently cannot learn or execute the
  observable contract; and
- if generator candidates repeatedly fail the same semantic dimensions despite prompt freeze, conclude only
  that this generator setup is unproductive. Do not infer a FLAN/Qwen capacity result.

The auxiliary-span plateau is relevant diagnostic evidence that representation precision can dominate
agreement, but it does not by itself prove either model capacity or data volume is the next lever.

## 12. Risks introduced by decoupling and mitigations

| Risk | Mitigation |
|---|---|
| Meaning errors hide without spans | Candidate-level semantic dimensions, two reviewers, hard rejection, local rationales |
| Lower-resolution review becomes vague | Exact categorical instrument and observable source/output evidence |
| Gemini imitates held-out data | Input/output collision screens, no held-out examples, quarantine pool pins |
| Generator becomes de facto gold authority | Candidate-pool-only status; separate Johnny authorization for any conversion |
| Reviewer lineage/bias | Gemini is generator only; ChatGPT and Claude independently review; disagreement escalates |
| Paid pilot expands silently | 24-candidate and $10 hard ceilings, no automatic semantic retries |
| Failed aux-span work is erased | Entire history stays committed and explicitly cited as failed evidence |
| Track B is accidentally superseded | Explicitly preserved as a different, deferred capability question |

## 13. Decision options for Johnny

### Option A — accept decoupling (recommended)

Retire auxiliary-span validation as a generator-readiness prerequisite, preserve its failed history, and
authorize a separate generator-readiness package using Sections 5-12 as binding minimum constraints.

Acceptance does not authorize project/API setup, billing, key creation, prompt submission, spending,
generation, candidate acceptance, corpus mutation, training, or deployment.

### Option B — reject decoupling

Keep Gemini generator readiness blocked. Do not restart the closed auxiliary-span correction sequence by
inference. A new representation milestone would require a new objective, evidence, gates, and authorization.

### Option C — prioritize Track B first

Keep Gemini paused and separately propose the no-training model-capability audit. This answers a different
question and carries materially greater compute/environment complexity than the prepaid bounded generator
pilot.

## 14. Requested independent review

Claude should verify against primary artifacts:

- the evidence pins and 2/14 -> 12/15 -> failed-gate history;
- that decoupling does not relabel failure as success;
- that retired labels are absent from the new candidate contract/review gate;
- that candidate-level dimensions cover the observable safety failures auxiliary spans were meant to expose;
- that quarantine includes all protected/acceptance and 15 validation records;
- that prompt-side and output-side checks are fail-closed;
- that the rejection ledger and candidate-pool status prevent automatic gold mutation;
- that numeric/cost ceilings are proportionate and cannot self-expand;
- that Track B remains distinct and valid; and
- that every external action remains separately authorized.

Material disagreement stops this proposal and returns to Johnny. Review agreement does not accept Option A
or authorize Gemini activity, staging, commit, or push.

## 15. Decision record

On 2026-08-14, Johnny asked Claude for an independent recommendation among Options A, B, and C before
deciding. Claude independently recommended Option A, concluding that the candidate-level contract preserves
the relevant safety properties, the sealed-review method had been proven repeatedly, and Options B and C
would respectively dead-end this path or answer a different question. After receiving both AIs' independent
recommendations and Claude's no-discrepancy verification of this analysis, Johnny accepted **Option A**
directly.

The resulting project decision is:

- validated auxiliary-span supervision is retired as a prerequisite for Gemini synthetic-candidate
  generator readiness;
- the complete failed auxiliary-span history remains preserved as negative and diagnostic evidence;
- the candidate-level contract, protections, ceilings, gates, and stop conditions in Sections 5-12 are
  binding minimum constraints for the next proposal; and
- drafting a separate Gemini generator-readiness package is authorized.

This decision does not authorize cloud-project creation, billing linkage or changes, acceptance of provider
terms, API enablement, key creation, secret handling, network requests, spending, generation, candidate
acceptance, corpus mutation, training, benchmark changes, release, deployment, staging, commit, or push.
Each remains governed by the readiness package and separately scoped authorization.
