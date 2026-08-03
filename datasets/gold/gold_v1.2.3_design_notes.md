# Gold v1.2.3 Design Notes

**Theme:** Discourse Reconnection and Clean Evidence Boundaries  
**Release type:** Compact additive corrective release  
**Author:** ChatGPT, dataset and evaluation architect

These notes follow `docs/datasets/DESIGN_NOTES_TEMPLATE.md`. Boundary Evidence, failure analysis, and benchmark provenance are human-facing metadata only and are not included in the trained JSONL.

## Stage 1 — Interruption and Resumption Across Surface Forms

### 001 — `interrupted_thought_depth`

**Example_ID:** G1.2.3-001  
**Difficulty:** hard  
**Benchmark analogue:** 02

**Lesson**

`interrupted_thought_depth`

**Author Intent**

Teach the model to reconnect two complete sentences about one upload problem across an explicitly labeled interruption, while keeping the inserted reservation reminder separate.

**Scenario**

A technical observation is paused for an unrelated scheduling reminder and then resumed with a condition that narrows when the problem occurs.

**Reason each fragment exists**

- “The archive upload stalls halfway through”: Establishes the main observation.
- “Quick interruption”: Marks a discourse boundary only. It is not recovered content.
- “reserve the small meeting room for Tuesday”: Inserts one independent task with an object and date.
- “Resuming the upload issue”: Explicitly points back to the first observation. It is structural language, not a separate intention.
- “the stall happens only when the folder contains videos”: Adds a supported condition to the original upload observation.

**Boundary Evidence**

- Boundary: Upload observation -> room-reservation task
  - Evidence: The interruption label and imperative introduce an unrelated object and schedule.
  - Confidence: High
- Boundary: Room-reservation task -> resumed upload observation
  - Evidence: The explicit resumption phrase names the earlier topic, and “the stall” refers back to the established upload failure.
  - Confidence: High

**Expected field-by-field recovery**

- Narrative: The archive upload stalls halfway through only when the folder contains videos. Separately, the small meeting room needs to be reserved for Tuesday.
- Bullets:
  - The archive upload stalls halfway through only when the folder contains videos
  - Reserve the small meeting room for Tuesday
- Action items:
  - Reserve the small meeting room for Tuesday

**Failure Modes**

- Excessive Fragmentation: treating the two upload statements as separate problems
- Topic Loss: dropping the halfway point, video condition, or room task
- Unsupported Addition: converting the upload observation into a diagnostic or repair task
- Structural Marker Promotion: extracting “Quick interruption” or “Resuming the upload issue”

**Hallucinations to watch for**

- A network, storage, file-size, or codec cause
- An owner or location for the meeting-room reservation
- A task to resume or revisit the upload issue

**Why this example is at this point in the curriculum**

This opens with the clearest sentence-level form: main topic, explicitly marked insertion, and explicit resumption. It teaches the relationship without relying on a broken clause.

**Expected Recovery**

Combine both supported upload details into one observation, preserve one room-reservation task, and omit both discourse markers from all output fields.

### 002 — `interrupted_thought_depth`

**Example_ID:** G1.2.3-002  
**Difficulty:** hard  
**Benchmark analogue:** 02

**Lesson**

`interrupted_thought_depth`

**Author Intent**

Teach the model to complete a diagnostic thought across a parenthetical task and then attach a second resumed detail to that same diagnosis.

**Scenario**

A rapid facilities note interrupts a monitor diagnosis with a key-delivery reminder before finishing the grammar and adding a duration detail.

**Reason each fragment exists**

- “Need to diagnose why the greenhouse monitor loses—”: Begins an explicit diagnostic action but leaves its object incomplete.
- “leave the spare key with Luis before noon”: Inserts a complete, unrelated delivery task.
- “its reading after the cable is bent”: Grammatically completes the monitor diagnosis and supplies the triggering condition.
- “To finish that thought”: Signals that the next clause continues the monitor topic. It is not semantic content.
- “the loss lasts until the monitor restarts”: Adds a supported duration to the same problem.

**Boundary Evidence**

- Boundary: Monitor diagnosis -> key-delivery task
  - Evidence: The dashes interrupt the diagnostic clause, while a new imperative, object, recipient, and deadline form an independent task.
  - Confidence: High
- Boundary: Key-delivery task -> completed monitor diagnosis
  - Evidence: “its reading” completes the verb phrase begun before the insertion.
  - Confidence: High
- Boundary: Completed diagnosis -> resumed duration detail
  - Evidence: “that thought” refers to the monitor problem, and “the loss” refers to the missing reading.
  - Confidence: High

**Expected field-by-field recovery**

- Narrative: The greenhouse monitor needs to be diagnosed because it loses its reading after the cable is bent, and the loss lasts until the monitor restarts. Separately, the spare key needs to be left with Luis before noon.
- Bullets:
  - Diagnose why the greenhouse monitor loses its reading after the cable is bent and why the loss lasts until the monitor restarts
  - Leave the spare key with Luis before noon
- Action items:
  - Diagnose why the greenhouse monitor loses its reading after the cable is bent and why the loss lasts until the monitor restarts
  - Leave the spare key with Luis before noon

**Failure Modes**

- Garbled Reconnection: attaching “its reading” or “the loss” to the key task
- Topic Loss: dropping the bent-cable trigger or restart duration
- Excessive Fragmentation: creating separate monitor actions from the two resumed details
- Structural Marker Promotion: adding “finish that thought” as content or action

**Hallucinations to watch for**

- A damaged cable, loose connector, or required replacement
- A reason the restart restores the reading
- A location or purpose for the spare key

**Why this example is at this point in the curriculum**

This adds grammatical pressure after the sentence-level example. The model must complete a broken verb phrase and then join a later anaphoric detail to the same action.

**Expected Recovery**

Return one complete monitor-diagnosis action with both supported details, one key-delivery action, and no action derived from the return phrase.

### 003 — `interrupted_thought_depth`

**Example_ID:** G1.2.3-003  
**Difficulty:** expert  
**Benchmark analogue:** 02

**Lesson**

`interrupted_thought_depth`

**Author Intent**

Teach the model to reconnect two observations under the same topic label when an unrelated reminder appears between them.

**Scenario**

An export-quality note uses topic labels rather than a broken sentence, with an inserted equipment-return reminder.

**Reason each fragment exists**

- “About the invoice export”: Establishes a named topic without asking for an action.
- “the columns shift after page three”: Supplies the first supported export observation.
- “Separate reminder”: Explicitly marks a new discourse segment and has no content of its own.
- “return the borrowed tripod”: Adds one independent action.
- “Coming back to the export”: Returns to the named topic without adding meaning.
- “the totals also move into the date column”: Adds a second supported observation to the same export issue.

**Boundary Evidence**

- Boundary: Export observation -> tripod reminder
  - Evidence: The explicit reminder label and imperative introduce an unrelated object.
  - Confidence: High
- Boundary: Tripod reminder -> export observation
  - Evidence: The return phrase repeats the earlier topic label, and “also” coordinates a second symptom with the first.
  - Confidence: High

**Expected field-by-field recovery**

- Narrative: In the invoice export, the columns shift after page three, and the totals move into the date column. Separately, the borrowed tripod needs to be returned.
- Bullets:
  - The invoice-export columns shift after page three, and the totals move into the date column
  - Return the borrowed tripod
- Action items:
  - Return the borrowed tripod

**Failure Modes**

- Excessive Fragmentation: presenting two unrelated export topics
- Task Promotion: converting the observations into an unsupported repair action
- Topic Loss: dropping the page threshold, totals, or date-column destination
- Structural Marker Promotion: extracting either discourse label as a bullet or action

**Hallucinations to watch for**

- A spreadsheet, PDF, printer, or software cause
- A requirement to fix or rerun the export
- A recipient, owner, or return deadline for the tripod

**Why this example is at this point in the curriculum**

This completes the surface-form set with topic-label reconnection rather than interrupted causal grammar. It tests whether the model learned a discourse relationship rather than one punctuation template.

**Expected Recovery**

Join the two export observations, preserve the tripod task, keep action_items limited to that explicit task, and discard the structural labels.

## Stage 2 — Clear Unresolved Alternatives

### 004 — `open_question_preservation`

**Example_ID:** G1.2.3-004  
**Difficulty:** hard  
**Benchmark analogue:** 08

**Lesson**

`open_question_preservation`

**Author Intent**

Teach a clear direct either/or formulation when observations appear both before and after the question but neither observation identifies the answer.

**Scenario**

A reception-area note records a parcel's location, asks who left it, and adds a later conversation detail.

**Reason each fragment exists**

- “The parcel was already on the reception shelf this morning”: Establishes a supported state before the question without identifying who caused it.
- “Was it left there by Mara or by the courier?”: Introduces two explicit alternatives in a direct interrogative.
- “Nobody mentioned it during the afternoon check-in”: Adds a later observation that provides no answer.

**Boundary Evidence**

- Boundary: Parcel observation -> source question
  - Evidence: The interrogative changes the intent from a known location to an unknown actor.
  - Confidence: High
- Boundary: Source question -> later discussion observation
  - Evidence: The check-in detail concerns the parcel but supplies no statement about Mara or the courier.
  - Confidence: High

**Expected field-by-field recovery**

- Narrative: The parcel was already on the reception shelf this morning. It remains unresolved whether Mara or the courier left it there. Nobody mentioned the parcel during the afternoon check-in.
- Bullets:
  - The parcel was already on the reception shelf this morning
  - Unresolved question: whether Mara or the courier left the parcel there
  - Nobody mentioned the parcel during the afternoon check-in
- Action items:
  - None

**Failure Modes**

- Confusing Phrasing: repeating “parcel,” “shelf,” or “left” in a tautological construction
- Invented Answer: choosing Mara or the courier
- Invented Causality: treating silence at the check-in as evidence for either alternative
- Task Promotion: creating an unsupported ask, check, or follow-up action

**Hallucinations to watch for**

- What the parcel contains
- Why it was left on the shelf
- Whether either candidate attended the check-in

**Why this example is at this point in the curriculum**

The known observation precedes the question, unlike the protected benchmark structure. This forces the model to identify unresolved alternatives by meaning rather than sentence position.

**Expected Recovery**

State the two possible actors in one clear unresolved clause and preserve both surrounding observations without converting either into an answer or task.

### 005 — `open_question_preservation`

**Example_ID:** G1.2.3-005  
**Difficulty:** hard  
**Benchmark analogue:** 08

**Lesson**

`open_question_preservation`

**Author Intent**

Teach the model to preserve alternatives expressed declaratively and to state explicitly that a later condition does not settle the earlier source question.

**Scenario**

A brief sound observation names two possible sources, reports later quiet, and includes an unrelated rehearsal task.

**Reason each fragment exists**

- “The extra chirp may have come from the hallway sensor or the kitchen timer”: Supplies two alternatives through modal, declarative wording.
- “the note does not settle which”: Explicitly confirms that the source remains unresolved.
- “By evening, the room was quiet”: Adds a later state that does not identify the earlier source.
- “Bring the extension cord to rehearsal”: Adds one separate explicit task.

**Boundary Evidence**

- Boundary: Source alternatives -> later room state
  - Evidence: The later absence of sound provides timing information but no evidence selecting the sensor or timer.
  - Confidence: High
- Boundary: Sound topic -> rehearsal task
  - Evidence: A new imperative, object, and destination introduce an unrelated obligation.
  - Confidence: High

**Expected field-by-field recovery**

- Narrative: It remains unresolved whether the extra chirp came from the hallway sensor or the kitchen timer. The room was quiet by evening, which does not settle the source of the earlier chirp. Separately, the extension cord needs to be brought to rehearsal.
- Bullets:
  - Unresolved question: whether the extra chirp came from the hallway sensor or the kitchen timer
  - The room was quiet by evening; this does not identify the source of the earlier chirp
  - Bring the extension cord to rehearsal
- Action items:
  - Bring the extension cord to rehearsal

**Failure Modes**

- Invented Answer: selecting the sensor or timer
- Alternative Loss: dropping one possible source
- Invented Causality: treating later quiet as proof about the source
- Topic Loss: dropping the later observation or rehearsal task

**Hallucinations to watch for**

- A fault, alert, battery issue, or safety meaning for the chirp
- Why the room became quiet
- Who needs the extension cord

**Why this example is at this point in the curriculum**

This contrasts with the direct question by expressing uncertainty as a declarative proposition. It also models a clear non-answer relation rather than merely placing the later observation nearby.

**Expected Recovery**

Preserve both sources and unresolved status, keep the later quiet state explicitly non-answering, and extract only the extension-cord task.

## Stage 3 — Clean Stop With Dangling References

### 006 — `dangling_reference`

**Example_ID:** G1.2.3-006  
**Difficulty:** medium  
**Benchmark analogue:** 16

**Lesson**

`dangling_reference`

**Author Intent**

Teach the model to preserve a valid action containing unresolved references and stop exactly when the source-supported reminder ends.

**Scenario**

A context-dependent reminder whose object and recipient are meaningful to the writer but not recoverable from the note alone.

**Reason each fragment exists**

- “Send it back”: Creates a complete return action while leaving the object unresolved.
- “to the person from before”: Supplies a recipient description that remains context-dependent.

**Boundary Evidence**

- Boundary: No topic boundary
  - Evidence: The note contains one action governed by one verb.
  - Confidence: High
- Stop boundary: End of source
  - Evidence: No clause after “before” supports an explanation, relationship, status, or follow-up.
  - Confidence: High

**Expected field-by-field recovery**

- Narrative: Send it back to the person from before.
- Bullets:
  - Send it back to the person from before
- Action items:
  - Send it back to the person from before

**Failure Modes**

- Unsupported Addition: appending an explanation, editorial label, or follow-up instruction
- Invented Referent: naming or describing the object or person beyond the source
- Excessive Fragmentation: splitting the return and recipient into separate actions
- Topic Loss: dropping either unresolved reference

**Hallucinations to watch for**

- What “it” is
- Who “the person from before” is
- Why the item should be returned
- Whether the two references are related, unrelated, confirmed, or pending
- Any text after the final source-supported recipient phrase

**Why this example is at this point in the curriculum**

This closes the release with a minimal exact-boundary example. Unlike prior dangling-reference training, the outputs do not append explanatory commentary about the unresolved references; the clean stop itself is the lesson.

**Expected Recovery**

Repeat the supported reminder as one action in all three fields. Do not resolve the references and do not append any clause after “the person from before.”

## Bundle-level review notes

### Benchmark separation

- No training input copies protected benchmark nouns.
- No training input reproduces a protected benchmark sentence verbatim.
- The three interruption inputs distribute the target relationship across sentence-level resumption, parenthetical grammatical completion, and topic-label return.
- The direct-question example changes information order and omits the protected question-observation-task sequence.
- The declarative uncertainty example uses a different grammatical form.
- The dangling-reference example uses a return action and recipient description rather than the protected ask-about construction.

### Cross-field invariants

- Structural return phrases appear in no expected output.
- All supported interruption details survive in narrative and bullets.
- Only explicit actions appear in `action_items`.
- Both alternatives appear in narrative and bullets for both uncertainty examples.
- Later observations remain observations, not answers.
- The dangling-reference outputs end at the last supported source clause.

### Evaluation focus

Use the unchanged strict benchmark. A superficially improved response still fails if it:

- preserves a main topic but loses a supported cause, condition, or duration;
- reconnects the thought but creates a return-marker action;
- retains both alternatives in confusing or tautological wording;
- attributes an ambiguous later observation to one alternative;
- preserves dangling references but appends any unsupported commentary.
