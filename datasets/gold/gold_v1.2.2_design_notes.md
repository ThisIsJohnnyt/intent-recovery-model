# Gold v1.2.2 Design Notes

**Theme:** Intent Fidelity and Evidence-Boundary Reinforcement  
**Release type:** Additive corrective release  
**Author:** ChatGPT, dataset and evaluation architect

These notes follow `docs/datasets/DESIGN_NOTES_TEMPLATE.md`. Boundary Evidence, failure analysis, and benchmark provenance are human-facing metadata only and are not included in the trained JSONL.

## Stage 1 — Isolated Intent-Type Fidelity

### 001 — `unsupported_content_resistance`

**Example_ID:** G1.2.2-001  
**Difficulty:** medium  
**Benchmark analogue:** 14

**Lesson**

`unsupported_content_resistance`

**Author Intent**

Teach the model to preserve one complete observation without adding a label, explanation, or implied repair task.

**Scenario**

A brief household observation captured for later recall.

**Reason each fragment exists**

- “The porch railing feels loose”: Provides a complete physical observation. It is not phrased as a request or commitment.
- “near the bottom step”: Adds location detail that must be preserved without being expanded into a diagnosis or repair plan.

**Boundary Evidence**

- Boundary: No topic boundary
  - Evidence: The note contains one complete observation with one location qualifier.
  - Confidence: High

**Expected field-by-field recovery**

- Narrative: The porch railing feels loose near the bottom step.
- Bullets:
  - The porch railing feels loose near the bottom step
- Action items:
  - None

**Failure Modes**

- Unsupported Addition: adding a generic label such as “railing problem” or inventing a repair action
- Over-Summarization: dropping the location near the bottom step
- Task Promotion: treating the observation as a committed task

**Hallucinations to watch for**

- A cause of the looseness
- A safety judgment not stated in the note
- An instruction to tighten, inspect, replace, or contact someone

**Why this example is at this point in the curriculum**

This opens the release with the simplest possible evidence-boundary test: one supported observation and no action items.

**Expected Recovery**

Repeat the observation and its location accurately. Keep action_items empty.

### 002 — `dangling_reference`

**Example_ID:** G1.2.2-002  
**Difficulty:** medium  
**Benchmark analogue:** 16

**Lesson**

`dangling_reference`

**Author Intent**

Teach the model to preserve a usable reminder while leaving both the person and object references unresolved.

**Scenario**

A quick memory prompt written with context known only to the writer.

**Reason each fragment exists**

- “Remember to ask her”: Creates a real reminder with an unresolved person reference.
- “about the earlier version”: Adds an unresolved object/version reference that must remain verbatim rather than being guessed.

**Boundary Evidence**

- Boundary: Reminder -> unresolved reference details
  - Evidence: The imperative-like reminder governs both pronoun phrases; they are missing context, not separate topics.
  - Confidence: High

**Expected field-by-field recovery**

- Narrative: There is a reminder to ask an unresolved female referent about an unresolved earlier version.
- Bullets:
  - Ask her about the earlier version; both references are unresolved
- Action items:
  - Ask her about the earlier version

**Failure Modes**

- Unsupported Addition: inventing who “her” is or what the version refers to
- Excessive Fragmentation: splitting the single reminder into separate actions
- Topic Loss: dropping either unresolved reference

**Hallucinations to watch for**

- A name or relationship for “her”
- A document, file, design, or product associated with “version”
- A reason the earlier version matters

**Why this example is at this point in the curriculum**

This follows the pure observation case by introducing one valid action whose key details must remain unresolved.

**Expected Recovery**

Preserve one reminder using the original unresolved wording. Do not add explanatory filler.

### 003 — `idea_action_boundary`

**Example_ID:** G1.2.2-003  
**Difficulty:** medium  
**Benchmark analogue:** 15

**Lesson**

`idea_action_boundary`

**Author Intent**

Teach the model that a tentative design idea is not a committed action.

**Scenario**

A spontaneous design thought recorded without a decision to implement it.

**Reason each fragment exists**

- “Maybe”: The primary intent-type signal. It marks the content as tentative.
- “use a quieter opening image with less text”: Provides the idea itself and two supported qualities that must remain attached.

**Boundary Evidence**

- Boundary: No topic boundary
  - Evidence: The note contains one speculative idea.
  - Confidence: High

**Expected field-by-field recovery**

- Narrative: One tentative idea is to use a quieter opening image with less text.
- Bullets:
  - Possible idea: use a quieter opening image with less text
- Action items:
  - None

**Failure Modes**

- Unsupported Addition: promoting the idea to action_items
- Over-Summarization: removing the tentative qualifier
- Topic Loss: dropping either the quieter-image or less-text detail

**Hallucinations to watch for**

- A decision to implement the idea
- A deadline, owner, or design rationale
- A specific image subject

**Why this example is at this point in the curriculum**

This isolates the exact idea-to-action regression before combining ideas with real tasks.

**Expected Recovery**

Preserve the idea as tentative in narrative and bullets. Keep action_items empty.

### 004 — `idea_action_boundary`

**Example_ID:** G1.2.2-004  
**Difficulty:** hard  
**Benchmark analogue:** 15

**Lesson**

`idea_action_boundary`

**Author Intent**

Teach the model to keep a tentative interface idea out of action_items while retaining a neighboring explicit task.

**Scenario**

A product note combining a possible layout change with a real communication obligation.

**Reason each fragment exists**

- “Could move the FAQ below the examples”: Introduces a tentative idea through “could.”
- “Send Niko the updated link before lunch”: Introduces a separate explicit task with recipient and deadline.

**Boundary Evidence**

- Boundary: Tentative layout idea -> communication task
  - Evidence: A new imperative verb, named recipient, and deadline introduce an independent obligation.
  - Confidence: High

**Expected field-by-field recovery**

- Narrative: One possible idea is to move the FAQ below the examples. Separately, the updated link needs to be sent to Niko before lunch.
- Bullets:
  - Possible idea: move the FAQ below the examples
  - Send Niko the updated link before lunch
- Action items:
  - Send Niko the updated link before lunch

**Failure Modes**

- Unsupported Addition: promoting the FAQ idea into action_items
- Topic Merge: folding the link task into the layout idea
- Topic Loss: dropping the deadline or recipient

**Hallucinations to watch for**

- That the FAQ move was approved
- Why Niko needs the link
- What the link contains

**Why this example is at this point in the curriculum**

This is the first contrastive case: the model must classify two neighboring intents differently.

**Expected Recovery**

Preserve the FAQ content as a possibility and return exactly one action item: send Niko the updated link before lunch.

## Stage 2 — Boundary Precision in Realistic Notes

### 005 — `interrupted_thought_depth`

**Example_ID:** G1.2.2-005  
**Difficulty:** hard  
**Benchmark analogue:** 02

**Lesson**

`interrupted_thought_depth`

**Author Intent**

Teach the model to reconnect a sentence interrupted inside a repeated condition without turning the interruption marker into an extra action.

**Scenario**

A studio-facilities note where a troubleshooting detail is interrupted by an unrelated delivery task.

**Reason each fragment exists**

- “Need to understand the locker alarm”: Establishes the troubleshooting intention before the condition is stated.
- “it starts chirping when—”: Begins a conditional explanation and cuts off inside the sentence.
- “drop the spare cables at studio B”: Inserts a complete, unrelated delivery task.
- “when the door stays open longer than a minute”: Resumes and completes the interrupted condition through repeated syntax rather than an explicit “back to” phrase.

**Boundary Evidence**

- Boundary: Locker-alarm condition -> cable delivery
  - Evidence: An em dash interrupts the unfinished condition, and a new imperative introduces unrelated objects and a destination.
  - Confidence: High
- Boundary: Cable delivery -> resumed locker-alarm condition
  - Evidence: The repeated word “when” grammatically reconnects the final clause to “it starts chirping,” completing the original condition.
  - Confidence: High

**Expected field-by-field recovery**

- Narrative: The locker alarm needs to be investigated because it starts chirping when the door stays open longer than a minute. Separately, the spare cables need to be dropped at studio B.
- Bullets:
  - Investigate why the locker alarm chirps when the door stays open longer than a minute
  - Drop the spare cables at studio B
- Action items:
  - Investigate why the locker alarm chirps when the door stays open longer than a minute
  - Drop the spare cables at studio B

**Failure Modes**

- Excessive Fragmentation: treating the resumed “when” clause as a separate intention
- Topic Loss: dropping the cable-delivery task or the one-minute condition
- Unsupported Addition: inventing a technical cause for the alarm

**Hallucinations to watch for**

- A faulty sensor, low battery, or security problem
- A deadline or recipient for the spare cables beyond studio B
- A separate task to “return to” the alarm topic

**Why this example is at this point in the curriculum**

This begins realistic structural pressure using a syntactic interruption pattern that is deliberately unlike the protected benchmark’s explicit topic-return wording.

**Expected Recovery**

Reconnect the two halves of the alarm condition into one troubleshooting task and preserve one separate cable-delivery task.
### 006 — `nested_boundary_depth`

**Example_ID:** G1.2.2-006  
**Difficulty:** hard  
**Benchmark analogue:** 03

**Lesson**

`nested_boundary_depth`

**Author Intent**

Teach the model to recognize that messaging Omar and asking the embedded question form one communication task while preserving a nearby observation.

**Scenario**

An event-access note containing a direct-message prompt, a timing dependency, and an unrelated building observation.

**Reason each fragment exists**

- “Message Omar: did the venue code change?”: Uses a colon to embed the question inside one communication instruction.
- “Need the answer before leaving”: Adds a timing dependency to the same task rather than creating a second action.
- “The stairwell light is flickering again”: Introduces an independent observation that must survive without becoming a task.

**Boundary Evidence**

- Boundary: Omar communication task -> stairwell observation
  - Evidence: The first two sentences share one information need and timing context; the third introduces a new physical subject with no semantic connection.
  - Confidence: High

**Expected field-by-field recovery**

- Narrative: Omar needs to be messaged to ask whether the venue code changed, with the answer needed before leaving. Separately, the stairwell light is flickering again.
- Bullets:
  - Message Omar to ask whether the venue code changed before leaving
  - The stairwell light is flickering again
- Action items:
  - Message Omar to ask whether the venue code changed before leaving

**Failure Modes**

- Excessive Fragmentation: creating separate “message Omar” and “find out whether the code changed” tasks
- Topic Loss: dropping the timing dependency or stairwell observation
- Unsupported Addition: creating a task to repair or report the light

**Hallucinations to watch for**

- That the venue code changed
- A reason the answer is needed before leaving
- A cause or repair plan for the flickering light

**Why this example is at this point in the curriculum**

This tests governed-task unity through punctuation and shared purpose rather than repeating the benchmark’s explicit instruction not to split the task.

**Expected Recovery**

Return one Omar communication action with its timing context and preserve the stairwell-light observation only in narrative and bullets.
### 007 — `open_question_preservation`

**Example_ID:** G1.2.2-007  
**Difficulty:** hard  
**Benchmark analogue:** 08

**Lesson**

`open_question_preservation`

**Author Intent**

Teach the model to preserve two possible causes stated as uncertainty, while recognizing that a later temperature change does not answer the question.

**Scenario**

A kitchen observation followed by an unrelated library-return task.

**Reason each fragment exists**

- “I can’t tell if the warm patch on the counter came from the toaster or the kettle”: States uncertainty declaratively and supplies two explicit alternatives.
- “It was cool again when I came back”: Adds a later state that does not identify which appliance caused the warmth.
- “Drop the library bag at the return desk”: Introduces a separate explicit task in a different setting.

**Boundary Evidence**

- Boundary: Cause uncertainty -> later counter state
  - Evidence: The second sentence reports a temporal change in the same subject but provides no evidence selecting either possible cause.
  - Confidence: Medium
- Boundary: Counter topic -> library-return task
  - Evidence: A new imperative, object, and destination introduce an unrelated obligation.
  - Confidence: High

**Expected field-by-field recovery**

- Narrative: It remains unclear whether the warm patch on the counter came from the toaster or the kettle. The counter was cool again when the writer returned. Separately, the library bag needs to be dropped at the return desk.
- Bullets:
  - Unresolved question: whether the warm patch came from the toaster or the kettle
  - The counter was cool again when the writer returned
  - Drop the library bag at the return desk
- Action items:
  - Drop the library bag at the return desk

**Failure Modes**

- Invented Answer: choosing the toaster or kettle
- Invented Causality: treating the later cool state as evidence for one appliance
- Topic Loss: dropping an alternative, the later observation, or the library task

**Hallucinations to watch for**

- That either appliance was recently used
- Why the counter cooled
- An inspection, cleaning, or repair action

**Why this example is at this point in the curriculum**

This preserves the same uncertainty skill through declarative wording, different objects, and a different task structure than the protected either/or benchmark.

**Expected Recovery**

State both possible sources and preserve the uncertainty; retain the later observation and one library-return action.
### 008 — `idea_action_boundary`

**Example_ID:** G1.2.2-008  
**Difficulty:** hard  
**Benchmark analogue:** 15

**Lesson**

`idea_action_boundary`

**Author Intent**

Teach the model to preserve a tentative improvement idea inside reflection while extracting only the explicit upload task.

**Scenario**

A post-orientation reflection with one possible change and one administrative deadline.

**Reason each fragment exists**

- “The orientation felt rushed”: Establishes reflection, not a task.
- “the first slide was crowded”: Adds a supported observation.
- “Perhaps start with the schedule instead”: Introduces a tentative idea through “perhaps.”
- “Upload the attendance list before the portal closes”: Adds one explicit task with a deadline condition.

**Boundary Evidence**

- Boundary: Reflection -> tentative idea
  - Evidence: The modal cue “perhaps” shifts from observation to possibility.
  - Confidence: High
- Boundary: Tentative idea -> upload task
  - Evidence: An imperative verb and deadline condition introduce a committed action.
  - Confidence: High

**Expected field-by-field recovery**

- Narrative: The orientation felt rushed, and the first slide was crowded. One tentative idea is to start with the schedule instead. Separately, the attendance list needs to be uploaded before the portal closes.
- Bullets:
  - The orientation felt rushed
  - The first slide was crowded
  - Possible idea: start with the schedule instead
  - Upload the attendance list before the portal closes
- Action items:
  - Upload the attendance list before the portal closes

**Failure Modes**

- Unsupported Addition: placing the schedule idea in action_items
- Topic Loss: dropping either reflection detail
- Topic Merge: treating the upload as part of the orientation redesign

**Hallucinations to watch for**

- That the schedule-first idea was approved
- Why the portal closes
- Who attended

**Why this example is at this point in the curriculum**

This is the realistic embedded version of the isolated idea/action contrast.

**Expected Recovery**

Preserve two observations, one tentative idea, and exactly one upload action.

## Stage 3 — Controlled Combination

### 009 — `unsupported_content_resistance`

**Example_ID:** G1.2.2-009  
**Difficulty:** expert  
**Benchmark analogue:** 14 / 16

**Lesson**

`unsupported_content_resistance`

**Author Intent**

Teach the model to preserve a plain observation and a dangling-reference instruction without adding filler or inferred context.

**Scenario**

A quick facilities-and-admin note with context-dependent shorthand.

**Reason each fragment exists**

- “The supply cabinet smells damp”: A complete observation with no requested response.
- “Leave that note as-is”: A valid action whose object reference is unresolved.
- “not sure which one she meant”: Explicitly marks both object selection and person reference as uncertain.
- “Send the room count to Mateo”: A separate clear communication task.

**Boundary Evidence**

- Boundary: Cabinet observation -> unresolved note instruction
  - Evidence: A new imperative introduces a different topic.
  - Confidence: High
- Boundary: Unresolved note instruction -> room-count task
  - Evidence: A new imperative, object, and named recipient introduce another topic.
  - Confidence: High

**Expected field-by-field recovery**

- Narrative: The supply cabinet smells damp. There is also an unresolved instruction to leave an unspecified note as-is because it is unclear which one a female referent meant. Separately, the room count needs to be sent to Mateo.
- Bullets:
  - The supply cabinet smells damp
  - Leave an unspecified note as-is; which note and who “she” refers to are unresolved
  - Send the room count to Mateo
- Action items:
  - Leave that note as-is
  - Send the room count to Mateo

**Failure Modes**

- Unsupported Addition: labeling the cabinet issue or inventing what “that note” means
- Invented Answer: resolving who “she” is or which note she meant
- Topic Loss: dropping the cabinet observation or either task

**Hallucinations to watch for**

- Mold, a leak, or a repair recommendation
- A document type for the note
- A relationship between Mateo and the unresolved referent

**Why this example is at this point in the curriculum**

This combines the two newly strict unsupported-addition failures with one clear task, testing restraint under multiple topics.

**Expected Recovery**

Preserve all three topics, keep both references unresolved, and return only the two explicit actions.

### 010 — `cross_field_completeness`

**Example_ID:** G1.2.2-010  
**Difficulty:** expert  
**Benchmark analogue:** 12

**Lesson**

`cross_field_completeness`

**Author Intent**

Teach the model to preserve every supported topic in narrative and bullets while extracting both a buried and final-fragment task.

**Scenario**

A post-rehearsal note mixing evaluation, logistics, a building observation, and a final reminder.

**Reason each fragment exists**

- “The rehearsal notes were useful”: Positive reflection that must not vanish.
- “the timing section is still confusing”: Contrasting unresolved observation.
- “send Imani the revised seating chart”: A brief task buried between reflection and observation.
- “the side entrance was locked again”: Independent observation with no stated action.
- “before I close this, book the projector for Friday”: Final-fragment task with an explicit date.

**Boundary Evidence**

- Boundary: Rehearsal reflection -> seating-chart task
  - Evidence: A new imperative and named recipient introduce an obligation.
  - Confidence: High
- Boundary: Seating-chart task -> entrance observation
  - Evidence: A new subject and past-state observation introduce a non-task topic.
  - Confidence: High
- Boundary: Entrance observation -> projector task
  - Evidence: A closing cue and imperative introduce the final obligation.
  - Confidence: High

**Expected field-by-field recovery**

- Narrative: The rehearsal notes were useful, but the timing section is still confusing. The revised seating chart needs to be sent to Imani. The side entrance was locked again. The projector needs to be booked for Friday.
- Bullets:
  - The rehearsal notes were useful
  - The timing section is still confusing
  - Send Imani the revised seating chart
  - The side entrance was locked again
  - Book the projector for Friday
- Action items:
  - Send Imani the revised seating chart
  - Book the projector for Friday

**Failure Modes**

- Topic Loss: dropping the seating task from narrative or the entrance observation from bullets
- Over-Summarization: collapsing the two rehearsal judgments
- Unsupported Addition: creating a task for the locked entrance

**Hallucinations to watch for**

- Why the entrance was locked
- A fix for the timing section
- Who needs the projector

**Why this example is at this point in the curriculum**

This is the first dedicated cross-field case and includes both buried-task and final-fragment pressure.

**Expected Recovery**

Represent all five supported points in narrative and bullets; action_items must contain exactly the seating-chart and projector tasks.

### 011 — `cross_field_completeness`

**Example_ID:** G1.2.2-011  
**Difficulty:** expert  
**Benchmark analogue:** 08 / 15

**Lesson**

`cross_field_completeness`

**Author Intent**

Teach the model to preserve an unresolved either/or question, its checking task, a tentative idea, and a plain observation across fields.

**Scenario**

A delivery-planning note with uncertainty, verification, a future idea, and environmental context.

**Reason each fragment exists**

- “Did Rowan send the final map or only save it?”: Open question with two explicit alternatives.
- “Check the shared folder”: Supported verification task connected to the question.
- “Maybe label the entrances more clearly next time”: Tentative future idea that must not become an action.
- “The loading area was noisy”: Independent observation with no implied response.

**Boundary Evidence**

- Boundary: Map question -> checking task
  - Evidence: The imperative provides a supported way to investigate without answering the question.
  - Confidence: High
- Boundary: Checking task -> tentative idea
  - Evidence: “Maybe” introduces a different intent type and future possibility.
  - Confidence: High
- Boundary: Tentative idea -> loading-area observation
  - Evidence: A new subject and descriptive statement introduce a separate topic.
  - Confidence: High

**Expected field-by-field recovery**

- Narrative: It remains unclear whether Rowan sent the final map or only saved it. The shared folder needs to be checked. One tentative idea is to label the entrances more clearly next time. The loading area was noisy.
- Bullets:
  - Unresolved question: whether Rowan sent the final map or only saved it
  - Check the shared folder
  - Possible idea: label the entrances more clearly next time
  - The loading area was noisy
- Action items:
  - Check the shared folder

**Failure Modes**

- Invented Answer: claiming the map was sent or merely saved
- Unsupported Addition: promoting the entrance-label idea or noise observation to action_items
- Topic Loss: dropping any of the four topics from narrative or bullets

**Hallucinations to watch for**

- What the folder contains
- Why the loading area was noisy
- A commitment to redesign labels

**Why this example is at this point in the curriculum**

This combines the release’s three central intent types under expert cross-field pressure.

**Expected Recovery**

Preserve all four topics; return only the shared-folder check as an action.

### 012 — `cross_field_completeness`

**Example_ID:** G1.2.2-012  
**Difficulty:** expert  
**Benchmark analogue:** 02 / 12 / 15

**Lesson**

`cross_field_completeness`

**Author Intent**

Teach maximum controlled interleaving through an interruption embedded inside a noun phrase, plus a real communication task, a tentative idea, a plain observation, and a separate final sentence task.

**Scenario**

A rapid end-of-day facilities note containing several unrelated intent types.

**Reason each fragment exists**

- “The badge reader flashes red after the first—”: Begins an observation and interrupts it inside the phrase “first scan.”
- “email Zara the lunch count before I forget”: Inserts a complete communication task inside the interrupted sentence.
- “scan, so I need to understand what is happening”: Grammatically completes the observation and converts it into a supported investigation task.
- “Perhaps the sign could sit closer”: Adds a tentative idea marked twice by modal language.
- “The hallway was cold”: Adds a complete non-actionable observation.
- “Replace the conference-room batteries tomorrow morning”: Adds a final explicit task as its own sentence, without a benchmark-like closing cue.

**Boundary Evidence**

- Boundary: Badge-reader observation -> lunch-count task
  - Evidence: The em dashes interrupt a noun phrase, and the inserted imperative introduces a named recipient and unrelated object.
  - Confidence: High
- Boundary: Lunch-count task -> completed badge-reader observation
  - Evidence: The word “scan” completes “after the first,” and the following causal connector returns to the reader issue.
  - Confidence: High
- Boundary: Reader topic -> sign idea
  - Evidence: “Perhaps” and “could” introduce a tentative possibility with a new subject.
  - Confidence: High
- Boundary: Sign idea -> hallway observation
  - Evidence: A new declarative subject introduces unrelated environmental information.
  - Confidence: High
- Boundary: Hallway observation -> battery task
  - Evidence: A separate imperative sentence introduces a new object and explicit timing.
  - Confidence: High

**Expected field-by-field recovery**

- Narrative: The badge reader needs to be investigated because it flashes red after the first scan. Separately, the lunch count needs to be emailed to Zara. One tentative idea is to place the sign closer. The hallway was cold. The conference-room batteries need to be replaced tomorrow morning.
- Bullets:
  - Investigate why the badge reader flashes red after the first scan
  - Email Zara the lunch count
  - Possible idea: place the sign closer
  - The hallway was cold
  - Replace the conference-room batteries tomorrow morning
- Action items:
  - Investigate why the badge reader flashes red after the first scan
  - Email Zara the lunch count
  - Replace the conference-room batteries tomorrow morning

**Failure Modes**

- Excessive Fragmentation: treating the two halves of “first scan” as separate reader topics
- Topic Loss: dropping any task, idea, or observation from narrative or bullets
- Unsupported Addition: promoting the sign idea or hallway observation to action_items

**Hallucinations to watch for**

- A cause for the red light
- A relationship between sign placement and the reader problem
- A task to address the cold hallway

**Why this example is at this point in the curriculum**

This closes the release with all major corrective pressures using discourse and sentence forms that do not reproduce the protected benchmark templates.

**Expected Recovery**

Represent all five recovered topics in narrative and bullets; action_items must contain exactly reader investigation, lunch-count email, and battery replacement.