# Non-emitted structural-supervision architecture study

**Date:** 2026-08-13  
**Author:** ChatGPT  
**Status:** Draft no-compute design study; Claude independent review required  
**Compute authorized:** None  

## 1. Decision

If this research line continues, use **training-only span-pooled structural supervision over the shared
FLAN-T5 encoder**. Keep the existing v2 text target and decoder output unchanged. Do not emit a plan.

This study rejects token-level supervision as too weak for proposition identity and relations, and rejects
a learned proposition-slot decoder as unnecessarily large and difficult to isolate. The recommended design
adds small training-only prediction heads over gold source spans. Their gradients shape the shared encoder;
the normal decoder still produces only narrative, bullets, and actions.

This document does not authorize annotation, implementation, training, inference, benchmark execution,
checkpoint work, seed 73, corpus mutation, commit, or push.

## 2. Boundary and evidence

The governing evidence is the verified RBR17-C static audit and the two failed emitted-plan feasibility
studies. The verbose plan exceeded 512/300; the compact pilot fit 512 but four of ten stress targets exceeded
300. A non-emitted head removes plan tokens from the decoder target entirely, so its feasibility question is
annotation/alignment and objective isolation—not generation length.

The 78-record comparator remains the semantic corpus. The failed seven-record delta remains excluded. The
existing 72/6 split, v2 prompts/targets, model revision, tokenizer, text loss, decoding, and frozen
Protected-16/Acceptance-10 suites remain the reference controls.

## 3. Three candidate supervision levels

| Level | Mechanism | Strength | Fatal or material limitation | Decision |
|---|---|---|---|---|
| Token | classify each source token as state/role/qualifier/task | simplest alignment and smallest head | duplicates, shared qualifiers, candidate sets, and output-field obligations are relations, not token labels; subword/boundary ambiguity | reject as primary design |
| Span-pooled | gold proposition spans pool encoder states; multi-label heads predict structure and pair relations | directly represents audited mechanisms; modest training-only capacity; inspectable | requires explicit source spans and pair masks; discontinuous propositions need a rule | recommend |
| Proposition slots | learned queries discover propositions and predict structure | could avoid gold boundaries at inference | adds segmentation/matching/slot-count objectives and substantial architecture; Hungarian matching and empty slots create new variables | defer |

Token labels may be derived as a diagnostic from span annotations, but must not become another loss in the
recommended single-variable comparison.

## 4. Recommended span-pooled architecture

### 4.1 Inputs and ordinary output

The input prompt and 512-token limit remain byte-identical to the comparator. The decoder target remains
the current v2 narrative/bullets/actions, with the existing 512 training-target and 300 generation limits.
No plan markers or structural labels enter the prompt or generated output.

### 4.2 Gold span representation

Each training record receives an ordered set of source-grounded proposition annotations:

```text
proposition_id
source_character_spans[]
state
roles[]
qualifiers[]
coreference_status
duplicate_of
required_output_fields[]
```

`source_character_spans` may contain multiple non-overlapping intervals for an interrupted or discontinuous
proposition. Intervals must quote exact source bytes. They are mapped to tokenizer offsets before training;
special/prompt-instruction tokens are never eligible. A proposition with no nonempty mapped source token is
invalid.

The annotation does not contain rewritten predicate text, rationale, inferred answers, supplied referents,
or new actions.

### 4.3 Pooling

For each proposition, mean-pool the final encoder hidden states over the union of its annotated source
tokens. Concatenate a learned embedding of proposition order (bounded by the corpus's frozen maximum) and
pass through one shared projection:

```text
h_p = LayerNorm(GELU(W_pool [mean(H_span); order_embedding]))
```

`W_pool` is shared by all structural heads. Dropout equals the base model's existing 0.1. No extra encoder
or attention block is added.

### 4.4 Heads

| Head | Output | Loss |
|---|---|---|
| state | exactly one of fact/question/fragment/tentative-idea/task | cross-entropy |
| roles | multi-label role-presence vector for speaker/actor/recipient/object/possessor/experiencer/candidate-set | binary cross-entropy |
| qualifiers | multi-label type vector for time/deadline/destination/trigger/condition/quantity/purpose/object-modifier | binary cross-entropy |
| coreference | none/resolved/unresolved/dangling | cross-entropy |
| fields | multi-label narrative/bullet/action obligations | binary cross-entropy with illegal non-task/action pair masked as invalid |
| duplicate relation | for each ordered pair `(p_i,p_j), j<i`: duplicate or not-duplicate | binary cross-entropy on a shared pair scorer |

This first design predicts role and qualifier **types**, not open-vocabulary values. Predicting textual values
would require span extraction or generation heads and would be a materially different objective. Atomic
evaluation must therefore distinguish “type learned” from “value retained in rendered text.”

### 4.5 Training-only behavior

Gold spans and structural labels are supplied only while calculating auxiliary training/evaluation loss on
the frozen train/validation records. They are never required at production inference. At inference:

- the structural heads are not called;
- no span detector or second model runs;
- the normal decoder generates the unchanged v2 answer;
- the existing parser and evaluator operate unchanged.

The trained head parameters may remain in the experimental checkpoint for reproducibility, but promotion or
export is prohibited. A later production proposal would have to decide whether to strip them; this study
does not.

## 5. Objective isolation

Comparator objective:

```text
L_C = L_text
```

Treatment objective:

```text
L_T = L_text + lambda * L_struct
```

where each head loss is first averaged over its own valid propositions/pairs, then:

```text
L_struct = mean(L_state, L_roles, L_qualifiers, L_coreference, L_fields, L_duplicate)
```

The entire auxiliary package—annotations, pooling projection, six heads, and one frozen `lambda`—is the sole
primary treatment variable. It must not be combined with representation tokens, corpus changes, capacity
scaling, sampling changes, constrained decoding, or validation repair.

### Attribution limitation

This package-level comparison can answer only whether the combined six-head structural supervision package
clears the frozen gates. It cannot identify which head caused an effect. A head may be beneficial, neutral,
or harmful while the package's aggregate outcome moves in another direction. Per-head validation losses and
accuracies are diagnostic descriptions, not causal attribution. Removing, isolating, or reweighting one
head is a later ablation with its own design and authorization; no AS17 outcome supports a claim that any
individual head was responsible.

### Per-head normalization

Raw head losses are not averaged directly. They have different class counts, label densities, and numbers
of valid propositions or pairs. Freeze this outcome-independent reduction:

1. Compute each categorical head as the mean negative log-likelihood over valid propositions.
2. Compute each multi-label BCE head with `reduction=none`; first mean across that head's label columns for
   each valid proposition, then mean across valid propositions.
3. Compute duplicate BCE as the mean over valid ordered proposition pairs only. Records with no valid pair
   contribute no duplicate term, rather than a synthetic zero.
4. For a batch, include a head in `L_struct` only when it has at least one valid supervised element.
5. Average the available six per-head scalar means with equal head weight. Do not weight by label count,
   proposition count, pair count, class frequency, validation performance, or observed gradient magnitude.

Thus normalization equalizes reduction units—one mean scalar per available head—without outcome-guided
rescaling. It does not guarantee equal gradients, and the design makes no such claim. Class weighting,
inverse-frequency weighting, focal loss, learned uncertainty weights, gradient balancing, or per-head
coefficients are excluded from the first comparison because each introduces an additional tuning choice.

### Lambda gate

No value is selected here. Before implementation, a static proposal must choose exactly one lambda without
observing protected/acceptance outputs. Acceptable evidence is the frozen reduction rule above plus a
synthetic-tensor loss/gradient shape receipt; an empirical lambda sweep is not part of the first comparison.
If one defensible value cannot be frozen, stop.

## 6. Capacity accounting

The pinned model has `d_model=768`. A future package must publish exact parameter formulas and counts for:

- order embeddings;
- shared projection and layer norm;
- five proposition heads;
- duplicate pair scorer.

Report added trainable parameters as an absolute count and percentage of the unchanged base model. This is
an architecture addition inherent to the objective, not “free.” To keep it auxiliary rather than a capacity
study:

- projection width may not exceed 768;
- use one linear head per label family;
- duplicate scoring may use only `[h_i; h_j; |h_i-h_j|; h_i*h_j]` plus one linear classifier;
- no new transformer/attention/recurrent layer;
- no head output may feed the decoder logits or generation path directly.

If the exact addition exceeds 1% of base-model trainable parameters, stop and redesign before compute. The
1% ceiling is a design guard, not evidence that smaller capacity is causally irrelevant.

### Frozen parameter-count formula

Let shared projection width `w=768`, maximum proposition-order vocabulary `m`, and the schema sizes be state
5, roles 7, qualifiers 8, coreference 4, fields 3, duplicate 1. With biases on linear layers and affine layer
normalization:

| Component | Formula |
|---|---:|
| order embedding | `m * w` |
| shared projection from `[mean_span; order]` | `(2w * w) + w` |
| layer norm | `2w` |
| state head | `(w * 5) + 5` |
| roles head | `(w * 7) + 7` |
| qualifiers head | `(w * 8) + 8` |
| coreference head | `(w * 4) + 4` |
| fields head | `(w * 3) + 3` |
| duplicate scorer over `[h_i;h_j;absdiff;product]` | `(4w * 1) + 1` |

Total:

```text
P_added(m) = m*w + (2*w*w + w) + 2*w + (27*w + 27) + (4*w + 1)
           = m*w + 2*w*w + 34*w + 28
```

For `w=768`, `P_added(m) = 1,205,788 + 768m`. The later static package must derive `m` from the frozen
maximum proposition count, recompute the exact base-model trainable parameter count from the pinned config,
and publish the exact ratio. Claude's independent review estimates roughly 660K only under a narrower
single-width projection assumption; this formula exposes that the concatenated `2w -> w` projection as
written is approximately 1.2M before order embeddings. Both are below 1% of a roughly 223M base, but the
implementation must match one declared formula exactly rather than citing an estimate.

### Synthetic loss/gradient receipt required before annotation expansion

Using synthetic tensors only—no corpus examples, model weights, protected/acceptance cases, or forward pass
through FLAN-T5—the later static package must verify:

- all six heads produce finite scalar losses for valid shapes;
- categorical, multi-label, and pair masks exclude padded/invalid elements exactly;
- a batch with no duplicate pairs omits that head from the available-head mean;
- changing the number of role/qualifier label columns does not change the reduction unit from one
  per-proposition mean;
- every included head sends a nonzero finite gradient through its head, the shared projection, and a dummy
  encoder-state tensor;
- masked elements have exactly zero gradient;
- the combined normalized `L_struct` equals the arithmetic mean of the available head scalars;
- `L_text + lambda*L_struct` preserves `L_text` byte/numerical identity when `lambda=0`;
- no structural logit or label enters decoder logits or generation inputs.

Report per-head raw scalar loss and gradient norm for transparency, but do not use those values to rescale
heads or select lambda. This is a shape/masking/wiring test, not empirical balancing.

## 7. Annotation feasibility before full authoring

Do not annotate all 78 records first. Freeze the same ten comparator stress records used by the compact
pilot: 007, 040, 042, 048, 053, 054, 056, 069, 074, and 075.

Two reviewers independently annotate exact source spans and all structural labels. Required gates:

- 100% agreement on proposition count, state, coreference class, duplicate link, and field obligations;
- exact agreement on span boundaries or a predeclared boundary-equivalence rule;
- role/qualifier disagreements fully adjudicated;
- every action maps to exactly one task proposition;
- no non-task proposition requires an action;
- every annotation round-trips through a fail-closed schema validator;
- no Protected-16 or Acceptance-10 text is used as an annotation template.

If agreement cannot be reached without inventing structure or rewriting source meaning, stop the
architecture before full-corpus annotation.

## 8. Alignment rules

1. Annotate the smallest source span that carries the proposition while retaining required arguments and
   qualifiers.
2. Discontinuous spans are allowed only for interrupted propositions; preserve interval order.
3. Shared qualifiers may be linked to multiple proposition IDs without merging those propositions.
4. A restatement receives its own source span and `duplicate_of` link; it does not create a second action
   identity.
5. Implicit writer actor may be represented as role type `actor` without fabricating a text span, but this
   convention must be uniform.
6. Unresolved candidate sets are labeled as `candidate_set` plus `unresolved`; no candidate is selected.
7. Dangling references remain `dangling`; no value is supplied.
8. Output-field obligations are derived from the committed target, not from desired benchmark behavior.

## 9. Evaluation design

### 9.1 Structural validation on frozen validation annotations

Structural head scores are diagnostic and must be macro-reported per head plus exact proposition-level joint
accuracy. Because the validation set is only six records, no structural score alone can promote an outcome.
No checkpoint is selected by structural or text validation loss.

### 9.2 Governing semantic evaluation

The decoder still faces the full unchanged Protected-16 and Acceptance-10 suites. The RBR17-C audit's atomic
endpoints remain governing:

- resolved versus unresolved binding: 06, 08, 16;
- question/fragment/task separation: 09;
- cross-field fact/task realization: 10;
- experiencer/role/chronology: 11;
- qualifier value retention: sdi2-02;
- semantic identity: sdi2-07;
- B7/A8 budgeting: sdi2-08;
- dense state/role/action composition: sdi2-10.

The head predicts structural types, while the frozen semantic evaluator checks actual names, objects,
destinations, deadlines, and text realization. A structural-head win cannot override a decoder failure.

### 9.3 Outcome logic

| Outcome | Treatment | Comparator | Disposition |
|---|---|---|---|
| AS17-A | passes all frozen semantic/atomic gates and head-validity gates | fails one or more corresponding semantic/atomic gates | discriminating success; stop and propose replication only |
| AS17-B | both pass semantic/atomic gates | parity; no claim that head caused improvement |
| AS17-C | both fail one or more | auxiliary architecture does not clear; stop |
| AS17-D | treatment fails while comparator passes | reject architecture |

Training/validation loss, head accuracy, average score, or favorable subgroup cannot override a failed case.
No outcome authorizes seed 73.

## 10. Leakage and review controls

- Use only comparator records for structural training annotations.
- Keep the seven failed-treatment delta records excluded.
- Do not annotate protected or acceptance inputs for training; benchmark-side atomic scoring rubrics remain
  evaluator-only.
- Freeze annotation guidance before the ten-record pilot.
- Record every adjudication and prohibit post-output label changes.
- Fingerprint corpus, spans, labels, split membership, model/config, trainer changes, and evaluator closure.
- Claude independently reviews every pilot annotation, parameter count, loss formula, and proposed gate.

## 11. Implementation and execution separation

If the ten-record annotation pilot passes, Johnny may separately authorize full 78-record annotation and a
static implementation package. That package would need:

- schema and validator;
- tokenizer-offset alignment tests, including Unicode and truncated-input failures;
- model wrapper and custom trainer loss tests using synthetic tensors only;
- exact parameter-count receipt matching the frozen formula;
- synthetic per-head normalization, masking, and gradient-flow receipt described above;
- unchanged-decoder/generation equivalence tests with dummy objects;
- frozen data and execution manifests;
- a plan-only default with no accidental compute path.

Only after independent review could Johnny separately authorize a fresh two-arm seed-17 run. This study
does not authorize either later milestone.

## 12. Hard stops

Stop and return to Johnny if:

- span/label agreement gates fail;
- annotations require protected wording or invented source structure;
- tokenizer offsets cannot map every span losslessly;
- a task/action cannot be represented one-to-one;
- lambda cannot be frozen without outcome-guided tuning;
- added parameters exceed 1% or a new sequence-processing layer is required;
- the treatment alters v2 text targets, prompts, decoding, corpus, sampling, schedule, capacity class, or
  checkpoint rule beyond the declared auxiliary package;
- evaluator or scorer semantics would need to change;
- Claude finds a material disagreement.

## 13. Recommendation

The cheapest next evidence is a **ten-record, no-compute dual-annotation feasibility pilot** for the span
schema—not implementation. It should produce exact source spans, labels, agreement/adjudication receipts,
tokenizer-offset mappings, and a static parameter-count/loss-shape design. If and only if those pass, return
to Johnny before annotating the remaining 68 records.

No additional action is authorized by this recommendation.
