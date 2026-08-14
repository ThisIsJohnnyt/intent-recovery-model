# Intent Recovery Model: Data-Fit and Model-Capability Discovery Plan

**Prepared:** 2026-08-11  
**Status:** Revised design only after Claude's independent review; proposed for Johnny's decision  
**Authority boundary:** This document does not authorize dataset access or download, acceptance of terms, account creation, sample inspection, corpus modification, model download or execution, training, evaluation execution, or repository commit/push.

## 1. Decision this discovery must support

The next authorized milestone, if any, should determine whether the highest-value investment is: (a) authentic external inputs plus project-specific re-annotation, (b) a more capable base model, (c) both, (d) continued custom data, or (e) architectural/output-pipeline redesign before either investment.

It must answer these questions independently:

1. Can an external source legally, ethically, and practically supply authentic language phenomena the custom corpus lacks?
2. Do its actual inputs cover the project's mechanisms, rather than merely sharing a broad label such as “dialogue” or “summarization”?
3. Can any existing targets be used without teaching smoothing, unsupported inference, task merging, or detail loss?
4. What re-annotation and double-review effort is required per usable input?
5. On the same frozen examples, does the current `google/flan-t5-base` fail where stronger untuned models succeed?
6. Are failures primarily semantic, structural, contextual-length related, or caused by the coupled output contract?
7. Would validation, constrained generation, or decomposition address the observed failures more directly than new data or a larger model?

## 2. Small dataset shortlist

The shortlist is intentionally heterogeneous. Inclusion here means “audit candidate,” not adoption. Johnny's settled project intent is public-benefit, attribution-required, and noncommercial throughout the downstream lineage: anyone should be able to access, use, fork, refine, and share the project for noncommercial purposes; downstream forks must remain noncommercial and credit Johnny for the original creation. Because a restriction on commercial use is incompatible with the Open Source Initiative's definition, project-facing materials should describe this as **source-available/noncommercial** (or another legally reviewed formulation), not OSI “open source.” The exact licenses and attribution notice for code, data/annotations, documentation, and model weights remain a separate decision requiring compatibility and rights review.

| Candidate | Layer it could test | Verified primary-source facts | Main uncertainty / exclusion risk |
|---|---|---|---|
| **Switchboard-1 Release 2 (`LDC97S62`) — considered, excluded from the initial audit** | Natural difficult language: spontaneous speech, disfluency, backchannels, repairs, dangling references | LDC describes about 260 hours, roughly 2,400 two-sided telephone conversations and 543 speakers; access is through LDC membership/non-member licensing and an LDC user agreement. [LDC catalog](https://catalog.ldc.upenn.edu/LDC97S62) | The paid/licensed access channel conflicts with Johnny's current criterion that project inputs be freely available/open to the intended community, so Switchboard is not an active candidate. This is a project-policy exclusion, not a legal conclusion about whether an access fee would constrain trained weights. Topic-prompted 1990–91 US telephone speech and non-project dialog-act labels are additional fit limitations. Reconsideration requires an explicit policy change and separate rights review. |
| **DialogSum — active candidate subject to rights clearance** | Short daily-life dialogue, intent recovery, and comparison with conventional summaries | The project reports 13,460 dialogues with human summaries/topics and says inputs come from three public corpora plus an English-speaking-practice website. Its README states that the dataset is under **CC BY-NC-SA 4.0** and separately states that copyright in the dialogue data belongs to the users who created it. Its summaries prioritize salience, brevity, named entities, observer voice, and formal language. [Official README](https://github.com/cylnlp/dialogsum) [CC BY-NC-SA 4.0 legal code](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en) [ACL paper](https://aclanthology.org/2021.findings-acl.449/) | NC is directionally compatible with the settled noncommercial-lineage policy; SA applies to shared adapted material under the license's definitions. This does **not** clear the source. The precise treatment of annotations, training, and trained weights requires qualified rights analysis rather than assumption. Each upstream corpus, the practice-site material, and the original-speaker copyright statement form additional provenance/rights layers. Existing targets remain presumed **re-annotation-only** unless sample evidence proves otherwise. |
| **QMSum** | Multi-party attribution, topic shifts, decisions/tasks, query-focused retrieval, and long context | The official repository reports 1,808 query-summary pairs over 232 meetings in academic, product, and committee domains and displays an MIT repository license. [Official repository](https://github.com/Yale-LILY/QMSum) [NAACL paper](https://aclanthology.org/2021.naacl-main.472/) | Repository licensing must not be assumed to supersede rights or conditions on the underlying AMI, ICSI, and committee transcripts. Source-by-source terms, speaker consent/privacy, redistribution, and derivative-training rights must be resolved. Long meetings may exceed the current model's input budget and confound capacity with truncation. |

**Reserve, not an initial fourth candidate:** AMI may replace QMSum if QMSum's provenance chain cannot be cleared. The AMI site states that signals, transcriptions, and some annotations are public under CC BY 4.0, while about two-thirds of meetings are elicited role-play and the remainder naturally occurring. [AMI corpus](https://groups.inf.ed.ac.uk/ami/corpus/)

The initial active shortlist is therefore **QMSum plus DialogSum**, with AMI as the reserve. Switchboard remains documented as a useful phenomenon benchmark that was rejected by the current sourcing policy, preventing repeated reconsideration without a policy change.

Clinical/diagnostic corpora, emotion-label datasets, and synthetic “disfluent” rewrites are excluded from the initial audit. They introduce governance or construct-validity questions that are not necessary to answer the first investment decision.

## 3. Track A — later dataset-fit audit

### A1. Rights and governance gate (before samples)

For each candidate, create a dated evidence sheet using the publisher, license text, data statement/consent documentation, and original paper. Record:

- owner/controller and every upstream source;
- access method and whether registration or term acceptance is required;
- commercial/research restrictions;
- permission for model training, modified annotations, derivative datasets, internal sharing, publication of examples, redistribution, and trained-weight distribution;
- attribution/share-alike obligations;
- consent, withdrawal, de-identification, sensitive content, and retention statements;
- jurisdiction or institutional restrictions and unresolved ambiguity.
- compatibility with the project's settled source-available/noncommercial distribution goal, including attribution to Johnny for the original creation and propagation of the noncommercial restriction to downstream forks.

**Stop:** do not access samples when rights depend on accepting terms Johnny has not approved, provenance is incomplete, training/derivative use is unclear, or required privacy controls are unavailable. A permissive code/repository license is not sufficient evidence for embedded third-party data.

**DialogSum rights stop:** its NC term is directionally compatible with Johnny's settled policy, but NC compatibility alone does not clear the dataset. Do not access samples until ShareAlike scope, upstream rights, speaker copyright, privacy, and model-training/weight-distribution implications are resolved.

### A2. Frozen sample design

Only after authorization and rights clearance, draw a reproducible **24-record audit sample per candidate** without examining targets during selection:

- freeze candidate version/commit, eligible split(s), record identifiers, random seed, and selection script hash;
- stratify across source/domain, conversation length quartile, speaker count, and available non-target metadata;
- cap repeated speakers/scenarios where identifiers permit;
- exclude records found by normalized or semantic collision checks against protected/acceptance evaluations;
- quarantine targets until input mapping is complete.

This is a fit audit, not a performance estimate. Twenty-four records are sufficient for a bounded rejection/adoption decision but not a population claim.

### A3. Input-only mechanism mapping

Two reviewers independently mark spans, not inferred diagnoses, for:

- false starts/repairs, repetition/restatement, incomplete thoughts;
- ambiguous references and speaker/multi-person attribution;
- topic shifts and mixed chronology;
- questions, uncertainty, unresolved source states, conditions, and alternatives;
- candidate actions and components: actor/recipient, object, destination, quantity, deadline/time, and condition;
- observation-versus-question-versus-idea-versus-action distinctions;
- emotionally compressed/hurried wording when textually observable;
- privacy/sensitivity, transcription artifacts, and context dependencies.

Record prevalence, co-occurrence, span-level reviewer agreement, and adjudication. Do not infer disability, diagnosis, age, stress, or cognitive status from language.

### A4. Target audit and conversion estimate

After input labels freeze, reveal existing targets and classify each:

1. **Usable:** satisfies the project contract without unsupported additions or loss.
2. **Re-annotation required:** input is useful, but target smooths uncertainty, omits supported details, merges tasks/speakers, or violates structure/tone.
3. **Incompatible:** input lacks relevant mechanisms, provenance/rights fail, or conversion requires reconstructing unavailable context.

Score supported-fact survival, supported-task-component survival, uncertainty/open-question preservation, invented facts/tasks, task separation, attribution, chronology, and structural-contract compliance. Time blind re-annotation and independent review on a small subset to estimate median minutes and disagreement—not just record count.

### A5. Dataset-fit decision rules

A candidate can proceed to a bounded conversion proposal only if:

- the rights/governance gate has no unresolved material issue;
- at least **8 of 24** inputs contain one or more priority mechanisms and at least **4 of 24** contain interacting mechanisms under independent adjudication;
- no collision with protected/acceptance evaluations remains after quarantine;
- at least **75%** of sampled inputs are usable as inputs without reconstructing missing context;
- the estimated re-annotation burden is recorded and judged affordable by Johnny.

Existing targets need not pass; a high re-annotation rate is an expected, decision-relevant result. Failure of these thresholds rejects that source for the next milestone, not the overall hybrid strategy.

## 4. Track B — later no-training capability audit

### B1. Predeclared model panel

1. **Current baseline:** exact pinned `google/flan-t5-base` revision already used by the project (about 0.2B parameters; Apache 2.0). [Model card](https://huggingface.co/google/flan-t5-base)
2. **Realistic stronger class:** `Qwen/Qwen3-4B`, exact revision to be frozen before execution (4.0B parameters, native 32,768-token context, Apache 2.0). [Model card](https://huggingface.co/Qwen/Qwen3-4B) [License](https://huggingface.co/Qwen/Qwen3-4B/blob/main/LICENSE)
3. **Capability ceiling:** `Qwen/Qwen3-14B`, exact revision to be frozen before execution (14B class; Apache 2.0). [Model card](https://huggingface.co/Qwen/Qwen3-14B) [License](https://huggingface.co/Qwen/Qwen3-14B/blob/main/LICENSE)

These are candidates, not execution authorization. Before freezing them, record hardware fit, quantization/precision, local-versus-hosted privacy, model and dependency licenses, context limits, reproducibility, fine-tuning suitability, and known data provenance/contamination disclosures. If 14B cannot run under an approved reproducible/privacy-preserving setup, replace it **before seeing outputs** using the same written criteria: open weights, instruction-tuned, at least 2× the stronger candidate's parameter count, adequate context, disclosed license, and feasible approved execution.

The cross-family comparison measures practical capability, not parameter scaling alone. If causal attribution to size is later important, propose a separately authorized same-family comparison; do not expand this first panel during execution.

### B2. Frozen examples and conditions

Use **36 private, independently selected examples**: 12 protected-style semantic cases, 12 acceptance-style structural/task-survival cases, and 12 newly hand-authored adversarial interaction cases. Keep all examples out of prompts and training. Freeze IDs/hashes, selection rationale, reference annotations, scorer instructions, model revisions, chat templates, maximum input/output lengths, precision/quantization, and software versions before inference.

Run two predeclared conditions for every model:

- **zero-example:** the identical contract and no demonstrations;
- **fixed few-example:** the identical, independently selected demonstrations, with no evaluation overlap.

Use deterministic decoding where supported (`temperature=0`/greedy, one output). Disable Qwen thinking/reasoning output and score only the requested contract. Inputs must fit every model without truncation; long-context capability is a separate test. Do not tune prompts, demonstrations, parsers, or decoding after viewing results.

Because model families tokenize and format prompts differently, semantic instructions and demonstrations remain byte-identical while only the documented wrapper/chat template may differ. Record this as a controlled implementation difference.

### B3. Scoring

Blind reviewers score outputs without model identity. Reuse the frozen project rubrics where applicable and report per-example paired results:

- supported facts and task components retained;
- unsupported facts/tasks introduced;
- uncertainty, questions, alternatives, attribution, chronology, and task separation;
- output-contract validity (narrative/bullets/actions and limits);
- tone: respectful, calm, non-diagnostic, non-patronizing;
- repairability by a deterministic validator/formatter without semantic regeneration.

Report exact counts and paired differences; do not claim statistical generalization from 36 examples. Adjudicate disagreements before unblinding. A model “succeeds” for this discovery only if it passes all existing safety/non-invention gates and improves at least **6 paired examples** over baseline with no more than **1 paired regression** on protected semantic cases.

### B4. Interpretation

| Frozen observation | Supported next decision |
|---|---|
| Stronger and ceiling models succeed; baseline fails | Capacity is material; propose deployment/finetuning feasibility work. |
| All models fail the same semantic cases | Prioritize specification, annotation, or task decomposition. |
| Semantic content survives but structure fails across models | Prototype deterministic validation/formatting or constrained generation before adding data. |
| Few-example condition succeeds where zero-example fails | Annotation examples carry value; consider distillation or retrieval of demonstrations. |
| Untuned baseline succeeds where current fine-tuned checkpoint fails | Audit training-induced regression before more training. |
| Ceiling alone succeeds | Capability exists but may be impractical; assess distillation/decomposition rather than automatic scale-up. |
| Results are mixed below the declared threshold | No capacity conclusion; inspect predeclared error strata and redesign a later audit. |

## 5. Privacy, contamination, and work-stopping conditions

- Never send private, licensed, or sensitive text to a hosted model without explicit approval and terms/privacy review.
- Store no raw external samples in the repository during discovery. A later audit must define encrypted/restricted storage, minimum retention, deletion, and access roles first.
- Do not quote identifiable or sensitive source text in reports; use record IDs and aggregate mechanism counts.
- Hash and compare normalized text/scenarios against all protected and acceptance sets; quarantine suspected collisions. Do not “repair” evaluation sets after seeing model outputs.
- Stop on unclear provenance/license, unexpected personal data, required unapproved term acceptance, evaluation leakage, inaccessible reproducibility information, hardware-driven model substitution after outputs, scorer unblinding, prompt changes after outputs, or material reviewer disagreement.
- Any stop returns to Johnny. It does not authorize a workaround or substitute source/model.

## 6. What remains hand-authored

Regardless of dataset outcome, retain hand-authored material for rare boundary distinctions, minimal contrastive correct/plausibly-wrong pairs, uncertainty/open-question preservation, adversarial task-component interactions, and independent held-out evaluation. External targets are never accepted merely because they are human-written.

## 7. Deliverables of a later authorized audit

1. Dated rights/provenance evidence sheets (no copied dataset content).
2. Frozen sampling manifest and contamination report.
3. Input mechanism matrix, adjudication record, target-compatibility matrix, and annotation-effort estimate.
4. Frozen model-evaluation protocol and environment manifest.
5. Blind paired score report and error-stratum analysis.
6. A recommendation using the decision table below; no acquisition, training, or deployment recommendation may self-authorize execution.

## 8. Final decision table

| Evidence | Decision supported |
|---|---|
| One or more datasets clear rights/governance and input-fit thresholds; capacity panel does not show a material baseline gap | Authorize a bounded dataset-sampling/conversion design. |
| Dataset candidates fail or are costly, while stronger models meet the capability threshold | Authorize a bounded model-capability/deployment feasibility evaluation; retain custom data meanwhile. |
| Dataset fit clears and stronger models materially outperform | Pursue both as separately gated milestones; do not infer that external targets are usable. |
| No dataset clears and model differences are immaterial | Retain primarily custom inputs and strengthen annotation/contrastive coverage. |
| Structure fails while semantics survives across models | Redesign validation, constrained generation, or output decomposition before adding data. |
| Rights/privacy/consent issues dominate, or intended users' preferences remain underspecified | Pause acquisition and conduct governance and/or participatory-design work. |
| Candidate terms permit attribution-required, noncommercial use and enforce compatible downstream restrictions, with all provenance/privacy/weight questions cleared | Candidate is policy-compatible and may proceed to the otherwise-authorized bounded sampling audit. |
| Candidate terms require or permit downstream commercial use in a way that prevents the project's intended noncommercial restriction, or attribution cannot be preserved | Reject the candidate or redesign the separable licensing architecture before any sample access. |
| Evidence is mixed or protocol integrity is breached | Make no investment conclusion; stop, document the limitation, and seek a new bounded authorization. |

## 9. Proposed authorization sequence

1. Johnny reviews this design.
2. Claude independently checks every dataset/license claim, provenance-chain warning, model fact, fairness control, leakage protection, threshold, and decision rule.
3. Material disagreement stops work and returns to Johnny.
4. Only after resolution may Johnny authorize a **metadata-and-sample audit package design**; access/download remains separately gated.
5. Model download/execution, external service use, compute, training, corpus mutation, and commit/push each remain outside this plan and require explicit later authorization.
