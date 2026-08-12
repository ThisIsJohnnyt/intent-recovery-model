# Intent Recovery Model — New Chat Handoff: Data Strategy and Model-Capability Discovery

**Prepared:** 2026-08-11  
**Purpose:** Start a new Codex/ChatGPT thread for a fresh, design-level examination of the project's training-data strategy and base-model capacity.  
**This handoff is contextual, not an authorization to acquire datasets, run models, train, modify the corpus, or change the repository.**

## 1. Repository and experiment state

- Repository: `intent-recovery-model`
- Local root: `C:\Users\thisi\OneDrive\Desktop\DeepThoughts`
- Branch: `main`
- `HEAD == origin/main == d178f69f838fe02012a0a87f2e73b6e04068f2b8`
- Latest commit: `Record seed-17 regression-balanced-repair outcome: RBR17-C, gates 3-6 fail both arms`
- Final outcome: **`RBR17-C`**
- Treatment and comparator were both valid, but both failed frozen gates 3–6.
- Seed 73, checkpoint selection or promotion, further training, export, deployment, and activation are not authorized.
- The raw execution worktree at `C:\swrbr17` contains preserved execution artifacts and checkpoints. Do not alter, clean up, or remove it without separate authorization.
- The main checkout contains known unrelated untracked historical artifacts. Do not modify, delete, stage, or include them in any proposed scope.

Key settled records:

- `training/controlled_seed17_regression_balanced_repair_outcome.md`
- `training/controlled_seed17_regression_balanced_repair_outcome_proposal_chatgpt.md`
- `training/seed17_regression_balanced_repair_execution_design_chatgpt.md`
- `training/controlled_seed17_regression_balanced_repair_design_chatgpt.md`
- `training/controlled_seed17_regression_balanced_repair_implementation_proposal_chatgpt.md`

Do not reopen the final scoring or `RBR17-C` classification unless the user explicitly asks and supplies a concrete reason.

## 2. Why this new conversation is happening

The project's foundation remains compelling: help recover useful intent from difficult, natural language while preserving uncertainty and avoiding invented facts or tasks.

The original motivation included language produced by people who may be stressed, neurodivergent, fatigued, distracted, aging, or experiencing cognitive difficulty. The refined principle is to model observable language phenomena rather than infer or diagnose why a person speaks or writes that way.

Relevant phenomena include:

- incomplete thoughts and dangling references;
- false starts, self-corrections, repetition, and restatement;
- ambiguous pronouns and multi-person attribution;
- rapid topic switching and mixed chronology;
- open questions and unresolved source states;
- emotionally compressed or hurried wording;
- tasks with deadlines, recipients, destinations, quantities, objects, and conditions;
- the distinction between an observation, question, idea, and actual action.

After multiple carefully controlled corpus experiments, the question is no longer simply, “What corrective records should we write next?” The broader question is:

> Should the project continue hand-authoring most training inputs, or use authentic external language sources and invest its proprietary effort in annotation, boundary examples, contrastive targets, and evaluation?

## 3. Current synthesis agreed by ChatGPT and Claude

The recommended direction is **hybrid and staged**, not a wholesale switch.

The model needs four distinct learning layers:

1. **Natural difficult language:** authentic disfluency, ambiguity, repetition, topic shifts, and emotional pressure.
2. **Intent recovery:** supported facts and actions survive; uncertainty remains unresolved; unsupported conclusions are not invented.
3. **Project output contract:** narrative, bullets, action items, structural limits, task separation, and survival of every supported task component.
4. **Safety and tone:** calm, useful, respectful, non-diagnostic, non-patronizing, and appropriately uncertain.

External datasets may supply substantial authentic input language and partial intent-recovery coverage. They generally do not supply the project's exact output contract or its uncertainty-preservation discipline.

Therefore, the project's most valuable proprietary asset may be its **annotation system**, not merely its hand-written source sentences. The likely future pattern is:

> authentic, appropriately licensed external input + targets re-annotated under the project's rules

Existing dataset targets must not be assumed suitable. Conventional summaries may reward smoothing ambiguity, inferring conclusions, merging statements, or omitting details that this project requires the model to preserve.

Continue hand-authoring where it is uniquely valuable:

- rare boundary distinctions;
- contrastive correct-versus-plausibly-wrong pairs;
- uncertainty and open-question preservation;
- adversarial structural cases;
- independent held-out evaluation.

## 4. Important additional question: model capacity

The project has kept the same pinned `google/flan-t5-base` model across controlled experiments. That consistency made corpus comparisons meaningful, but it does not prove that the model has enough capacity to learn all interacting semantic and structural requirements reliably.

Observed failures could arise from one or more of:

- insufficient or insufficiently varied training data;
- training dynamics that overweight a small number of records;
- limited base-model capacity;
- an output contract that couples too many tasks into one generation;
- behavior better handled by constrained decoding, validation, or post-processing.

Dataset strategy and model capacity should therefore be audited as separate investment questions.

## 5. Proposed next milestone: a small, design-only discovery plan

### Immediate owner

**ChatGPT is the primary researcher and plan author.** Claude independently reviews the resulting plan. Johnny is the decision authority.

The first deliverable should be a concise discovery-plan document only. It may research public information and primary sources, but it must not download controlled datasets, accept licenses, create accounts, run candidate models, train anything, mutate project data, or commit changes unless Johnny separately authorizes those actions.

### Track A — Dataset-fit audit design

Select a deliberately small shortlist—probably two or three candidate datasets—and define how a later authorized audit would:

1. independently verify access, licensing, consent, permitted use, redistribution, derivative-work, and model-training terms from primary sources;
2. inspect actual sample records rather than rely on dataset descriptions;
3. map samples to the project's observable-phenomena and mechanism taxonomy;
4. classify existing targets as usable, requiring re-annotation, or incompatible;
5. estimate coverage across the four learning layers;
6. assess demographic, diagnostic, genre, elicitation-task, transcription, and privacy bias;
7. detect wording or scenario collision with protected and acceptance evaluations;
8. identify the human annotation and double-review effort needed to convert useful inputs into the project contract.

Candidate families previously discussed, not yet selected or adopted:

- Switchboard or other spontaneous-conversation/disfluency corpora;
- DialogSum or SAMSum for dialogue summarization;
- AMI or QMSum for multi-party meetings, decisions, and tasks;
- DementiaBank or ADReSS only if access, consent, governance, and permitted-use requirements can be satisfied;
- WASSA-style emotion or distress datasets for emotionally loaded language, with the recognition that emotion classification is not intent recovery.

Clinical or sensitive corpora require especially strict review. No plan should depend on them until their current terms are independently verified.

### Track B — Model-capability audit design

Define a fair, no-training comparison that a later authorized milestone could run on the same frozen, independently selected examples:

- the current FLAN-T5-base baseline;
- a stronger model in a realistic deployment class;
- a larger reference model used as a capability ceiling.

The plan should specify candidate-selection criteria rather than choosing a model merely because it performs well after results are seen. It should freeze prompts, output contract, inference settings where comparable, evaluation examples, scoring rules, and decision interpretations before execution.

The audit should distinguish at least these patterns:

| Observation | Possible implication to test—not an automatic conclusion |
|---|---|
| Stronger models succeed while FLAN-T5-base fails | Model capacity may be a material bottleneck |
| All models fail similarly | Specification, decomposition, prompting, or data may be the main bottleneck |
| Content survives but structure fails | Constrained generation or post-processing may deserve priority |
| A larger model succeeds only with examples | The annotation system is valuable; distillation may be viable |
| The current base model succeeds before fine-tuning | Existing fine-tuning may be degrading some base capability |

This track must also address deployment constraints, licensing, privacy, context length, reproducibility, hardware feasibility, and whether a model is appropriate for fine-tuning or only for reference evaluation.

## 6. Real-user involvement is a separate future program

Keep three stages distinct:

1. **Participatory design:** people with relevant lived experience help define useful and respectful outputs.
2. **Consented data collection:** participants contribute language samples under explicit privacy, retention, withdrawal, and usage rules.
3. **Clinical research:** any attempt to associate language or outputs with health or cognitive status, requiring substantially stronger governance and expertise.

Participatory design may be valuable before sensitive data collection. Do not collapse these stages or frame the system as diagnosing stress, neurodivergence, or cognitive decline.

## 7. Required characteristics of the discovery plan

The new thread should produce a plan that is:

- small, reversible, and decision-oriented;
- based on current primary-source research for unstable facts;
- explicit about licenses, privacy, consent, and contamination risk;
- careful to separate authentic inputs from potentially unsuitable existing targets;
- explicit about what remains hand-authored;
- designed to compare data limitations with model-capacity limitations;
- bounded by predeclared inclusion, exclusion, scoring, and stop rules;
- clear about what later actions require separate authorization;
- useful even if the conclusion is that none of the shortlisted datasets fit.

The plan should conclude with a concrete decision table describing which evidence would support:

- proceeding to a bounded dataset-sampling audit;
- proceeding to a bounded model-capability evaluation;
- pursuing both;
- retaining a primarily custom-data strategy;
- redesigning the architecture or output pipeline before adding data;
- pausing for participatory-design or governance work.

## 8. Established responsibility protocol

1. ChatGPT researches and drafts the discovery plan.
2. Claude independently verifies dataset claims, licenses, audit fairness, leakage protections, and decision rules.
3. Any material disagreement is work-stopping and returns to Johnny.
4. Johnny decides whether to authorize implementation of an audit package.
5. If authorized, Claude ordinarily implements the bounded package without execution.
6. ChatGPT independently reviews the implementation.
7. Johnny separately authorizes any acquisition, model execution, or compute.
8. ChatGPT produces the primary analysis; Claude independently reproduces or challenges it.
9. Johnny decides the training-data and model direction.

Agreement between ChatGPT and Claude never substitutes for Johnny's authorization.

## 9. Communication and scope instructions for the new thread

- Treat this as a real planning and research conversation, not a continuation of automatic experiment execution.
- Do not update `ChatGPTUpdates.md`, `ClaudeUpdates.md`, or project documentation unless Johnny explicitly restarts that process in the new thread.
- Do not modify the repository while merely reviewing this handoff.
- Do not create goals, acquire data, accept external terms, run models, train, stage, commit, push, clean worktrees, or alter preserved artifacts without explicit authorization.
- Use web research for current dataset terms, model availability, licenses, and technical claims; prefer official dataset pages, licenses, model cards, and original papers.
- Clearly separate verified facts, reasoned inferences, and open questions.

## 10. Suggested opening request

> Review this handoff and draft a small, design-only discovery plan for the Intent Recovery Model's next direction. Research current primary sources as needed. Cover both dataset fit and base-model capability, but do not download datasets, run models, train, modify the repository, or update the Claude bridge. Present the plan for my review before creating any project artifact or authorizing any implementation.

