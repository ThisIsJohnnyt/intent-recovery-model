# gold_v1.2.1 Design Notes

**Theme**: Segmentation Reinforcement
**Release type**: Additive corrective release
**Author**: ChatGPT, dataset and evaluation architect

Format follows [`docs/datasets/DESIGN_NOTES_TEMPLATE.md`](../../docs/datasets/DESIGN_NOTES_TEMPLATE.md).
Boundary Evidence and failure analysis are human-facing metadata and are not included in the trained JSONL.

## Stage 1 — Isolated reinforcement (Examples 01–05)

### 01 — `interrupted_thought_depth`

**Example_ID:** G1.2.1-001  
**Difficulty:** medium

**Lesson**

`interrupted_thought_depth`

**Author Intent**

Teach the model to preserve an unfinished account-related thought while separately recovering a reminder involving Eli.

**Scenario**

A quick note captured while one administrative thought is interrupted by a practical reminder.

**Reason each fragment exists**

- “Need to check whether the storage account—”: Creates a deliberately incomplete thought. The dash marks interruption; the missing condition must not be guessed.
- “also remind Eli to bring the spare key tomorrow”: Introduces a complete, independent reminder with a named person and explicit timing.

**Boundary Evidence**

- Boundary: storage-account thought -> reminder about Eli
  - Evidence: The unfinished clause stops at an em dash, and a new reminder verb introduces a different subject and obligation.
  - Confidence: High

**Failure Modes**

- Topic Loss: dropping the incomplete storage-account thought
- Topic Merge: folding the key reminder into the account issue
- Unsupported Addition: inventing what needs to be checked about the account
- Misattribution: assigning the reminder task to Eli rather than recognizing Eli as its recipient

**Hallucinations to watch for**

- A reason the storage account needs checking
- A claim that Eli already has or lost the key
- A deadline or action for the storage-account fragment

**Why this example is at this point in the curriculum**

This opens the release with one isolated interrupted thought and one clearly separate reminder, reinforcing the distinction before more realistic interruptions appear.

**Expected Recovery**

Preserve the storage-account fragment as incomplete and recover one action item: remind Eli to bring the spare key tomorrow.

### 02 — `buried_task_retention`

**Example_ID:** G1.2.1-002  
**Difficulty:** medium

**Lesson**

`buried_task_retention`

**Author Intent**

Teach the model to surface a short task embedded inside a longer meeting reflection.

**Scenario**

A post-meeting note that shifts briefly into an administrative obligation before returning to reflection.

**Reason each fragment exists**

- “The planning meeting felt more focused this time”: Establishes the main reflective narrative.
- “the shorter agenda probably helped”: Adds a tentative explanation that must remain uncertain.
- “send Nora the updated attendance sheet”: Creates the low-salience buried task.
- “the last ten minutes still wandered”: Returns to the meeting reflection after the task.

**Boundary Evidence**

- Boundary: meeting reflection -> task for Nora
  - Evidence: A new imperative verb introduces a concrete obligation and named recipient.
  - Confidence: High
- Boundary: task for Nora -> closing meeting observation
  - Evidence: The note returns to evaluation of the meeting rather than continuing the sending task.
  - Confidence: High

**Failure Modes**

- Topic Loss: omitting the attendance-sheet task
- Topic Merge: absorbing the task into the meeting summary
- Invented Causality: claiming the short agenda caused the improved focus
- Over-Summarization: preserving only that the meeting went better

**Hallucinations to watch for**

- That Nora attended the meeting
- That the attendance sheet is due by a particular time
- That the shorter agenda definitely caused the improved focus

**Why this example is at this point in the curriculum**

The task is short but clearly phrased, making this an early buried-task reinforcement example before longer and noisier notes.

**Expected Recovery**

Preserve the reflective observations and surface “Send Nora the updated attendance sheet” as the only action item.

### 03 — `nested_boundary_depth`

**Example_ID:** G1.2.1-003  
**Difficulty:** medium

**Lesson**

`nested_boundary_depth`

**Author Intent**

Teach the model to keep a task and its required detail together while separating an unrelated observation.

**Scenario**

A building-maintenance note containing one qualified communication task and one separate security observation.

**Reason each fragment exists**

- “email the landlord about the hallway light”: Creates the main task.
- “include that it flickers mostly at night”: Qualifies what must be communicated; it is part of the same task, not a separate intention.
- “the package room door was propped open again”: Introduces an independent observation.

**Boundary Evidence**

- Boundary: qualified hallway-light task -> package-room observation
  - Evidence: The subject changes from the light and landlord communication to a separate door condition.
  - Confidence: High

**Failure Modes**

- Excessive Fragmentation: splitting “email the landlord” and “mention the nighttime flicker” into unrelated tasks
- Topic Merge: treating the package-room door as another detail for the hallway-light email
- Unsupported Addition: turning the door observation into a task to report or close it

**Hallucinations to watch for**

- A requirement to contact building security
- A claim that the same person caused both maintenance issues
- A deadline for emailing the landlord

**Why this example is at this point in the curriculum**

This is the first explicit over-segmentation check: one nested qualification must stay attached while a nearby observation remains separate.

**Expected Recovery**

Produce one combined landlord action item that includes the nighttime-flicker detail, plus a separate observation about the package-room door.

### 04 — `multi_person_attribution`

**Example_ID:** G1.2.1-004  
**Difficulty:** medium

**Lesson**

`multi_person_attribution`

**Author Intent**

Teach explicit attribution across two named people without inferring who sent the confirmation.

**Scenario**

A short scheduling note where one person reports a time change and another holds the confirmation email.

**Reason each fragment exists**

- “Maya said the reservation was moved to six”: Attributes the reported schedule change to Maya.
- “Theo has the confirmation email”: Attributes possession of the email to Theo.
- “Ask Maya whether Theo already forwarded it”: Creates the writer's action and preserves the forwarding question as unresolved.

**Boundary Evidence**

- Boundary: Maya's statement -> Theo's possession
  - Evidence: A new named subject is introduced with a different relation to the reservation.
  - Confidence: High
- Boundary: Theo's possession -> question to Maya
  - Evidence: The sentence changes from observation to an imperative directed by the writer.
  - Confidence: High

**Failure Modes**

- Misattribution: saying Theo reported the time change or Maya has the email
- Invented Answer: claiming Theo forwarded the email
- Topic Loss: dropping the ask-Maya action
- Unsupported Addition: claiming Maya or Theo made the reservation

**Hallucinations to watch for**

- Who moved the reservation
- Whether Theo forwarded the email
- Why Maya rather than Theo should be asked

**Why this example is at this point in the curriculum**

This introduces two-person attribution using explicit nouns and no ambiguous pronouns before later examples add ambiguity.

**Expected Recovery**

Keep Maya's statement, Theo's possession, and the action to ask Maya distinct and correctly attributed.

### 05 — `open_question_preservation`

**Example_ID:** G1.2.1-005  
**Difficulty:** medium

**Lesson**

`open_question_preservation`

**Author Intent**

Teach the model to preserve an unresolved payment question without answering it and to recover a separate download task.

**Scenario**

A brief financial-administration note written before an online portal closes.

**Reason each fragment exists**

- “Did the insurance payment actually clear?”: Creates a complete unresolved question.
- “Download the statement before the portal closes tonight”: Creates an independent, time-bounded task.

**Boundary Evidence**

- Boundary: payment question -> statement-download task
  - Evidence: The first clause asks for unknown status; the second is an explicit imperative with its own deadline.
  - Confidence: High

**Failure Modes**

- Invented Answer: claiming the payment cleared or failed
- Topic Merge: treating the statement download as evidence of payment status
- Topic Loss: dropping either the question or the task
- Unsupported Addition: adding a task to contact the insurer

**Hallucinations to watch for**

- The payment outcome
- That the statement will answer the question
- A reason the portal is closing

**Why this example is at this point in the curriculum**

This is the cleanest isolated open-question case, establishing the behavior before questions are embedded in longer notes.

**Expected Recovery**

State that payment status is unresolved and list only the statement download as an action item.

## Stage 2 — Realistic context (Examples 06–10)

### 06 — `interrupted_thought_depth`

**Example_ID:** G1.2.1-006  
**Difficulty:** hard

**Lesson**

`interrupted_thought_depth`

**Author Intent**

Teach recovery of an interrupted thought that is later clarified, while preserving an inserted task.

**Scenario**

A note captured during troubleshooting when the writer interrupts themself to remember a household task.

**Reason each fragment exists**

- “Need to figure out why the calendar keeps—”: Begins an interrupted troubleshooting thought.
- “put the library books in the car”: Inserts an unrelated concrete task.
- “back to the calendar thing because meetings are duplicating”: Returns to and clarifies the original problem without inventing beyond the note.

**Boundary Evidence**

- Boundary: calendar interruption -> library-books task
  - Evidence: The dash and new imperative mark a strong interruption and topic change.
  - Confidence: High
- Boundary: library-books task -> resumed calendar problem
  - Evidence: “back to” explicitly signals return to the first topic.
  - Confidence: High

**Failure Modes**

- Topic Loss: dropping the interrupted calendar issue or the books task
- Topic Merge: connecting the books to the calendar problem
- Excessive Fragmentation: treating the opening and resumed calendar fragments as separate topics
- Unsupported Addition: inventing a calendar platform or cause

**Hallucinations to watch for**

- Why meetings are duplicating
- Which calendar application is involved
- A deadline for fixing the calendar

**Why this example is at this point in the curriculum**

This raises difficulty by requiring the model to join two separated fragments of one topic while preserving the interrupting task independently.

**Expected Recovery**

Recover two topics: investigate duplicated calendar meetings and put the library books in the car.

### 07 — `buried_task_retention`

**Example_ID:** G1.2.1-007  
**Difficulty:** hard

**Lesson**

`buried_task_retention`

**Author Intent**

Teach retention of a very short printing task buried inside a long, cohesive workshop-design reflection.

**Scenario**

A workshop facilitator thinking through presentation structure while remembering an unrelated return-label task.

**Reason each fragment exists**

- “workshop outline is too crowded”: Begins the main design reflection.
- “maybe the opening should breathe more because everyone looked lost last time”: Adds a tentative design change and stated observation.
- “print the return label”: Creates the buried independent task.
- “the examples probably need to come earlier”: Returns to the workshop-design thread.

**Boundary Evidence**

- Boundary: workshop reflection -> return-label task
  - Evidence: A bare imperative introduces a new object and unrelated obligation.
  - Confidence: High
- Boundary: return-label task -> workshop reflection
  - Evidence: The subject returns to ordering workshop examples.
  - Confidence: High

**Failure Modes**

- Topic Loss: omitting the return-label task
- Topic Merge: treating the label as a workshop label
- Over-Summarization: reducing the note to workshop concerns only
- Invented Causality: asserting that example order caused attendees to look lost

**Hallucinations to watch for**

- That the return label belongs to workshop materials
- A commitment to revise the workshop
- Who “everyone” refers to beyond attendees implied by context

**Why this example is at this point in the curriculum**

This is harder than Example 02 because the buried task is surrounded by a longer, semantically cohesive reflection and the word “label” could invite a false connection.

**Expected Recovery**

Keep the workshop possibilities as tentative observations/ideas and surface “Print the return label” as the sole action item.

### 08 — `multi_person_attribution`

**Example_ID:** G1.2.1-008  
**Difficulty:** hard

**Lesson**

`multi_person_attribution`

**Author Intent**

Teach the model to preserve explicit attribution while refusing to resolve an ambiguous pronoun.

**Scenario**

A project handoff note involving two named people and an unclear reference to who needs a signed copy.

**Reason each fragment exists**

- “Rina told Marcus the draft was approved”: Attributes the statement to Rina and the recipient to Marcus.
- “after he asked about it”: Uses a pronoun whose nearest supported referent is Marcus; the recovery may state Marcus asked, but should not add further detail.
- “He still needs the signed copy”: Introduces deliberate ambiguity between Marcus and the client, explicitly acknowledged by the writer.
- “Ask Rina who needs it”: Creates the resolution task.

**Boundary Evidence**

- Boundary: approval report -> ambiguous signed-copy need
  - Evidence: The note shifts from a completed communication to an unresolved ownership question.
  - Confidence: Medium
- Boundary: ambiguous need -> ask-Rina task
  - Evidence: An explicit imperative introduces the next action.
  - Confidence: High

**Failure Modes**

- Misattribution: assigning the signed-copy need definitively to Marcus or the client
- Invented Answer: resolving the ambiguous pronoun
- Topic Loss: omitting the ambiguity or ask-Rina task
- Unsupported Addition: claiming who approved the draft

**Hallucinations to watch for**

- The identity of the person needing the signed copy
- Who approved the draft
- Why the client is involved

**Why this example is at this point in the curriculum**

This follows the explicit two-person case by adding an ambiguity the model must preserve rather than solve.

**Expected Recovery**

Attribute the approval statement to Rina, preserve that Marcus asked about the draft, state that the signed-copy recipient is unclear, and list asking Rina as the action.

### 09 — `open_question_preservation`

**Example_ID:** G1.2.1-009  
**Difficulty:** hard

**Lesson**

`open_question_preservation`

**Author Intent**

Teach preservation of a two-option unresolved question alongside a related observation and unrelated household task.

**Scenario**

A nighttime note after hearing a brief unexplained sound.

**Reason each fragment exists**

- “Was the strange noise coming from the vent or outside?”: Creates an unresolved either/or question.
- “It stopped after a minute”: Adds an observation but does not answer the source question.
- “Move the laundry before bed”: Introduces an independent task.

**Boundary Evidence**

- Boundary: noise question/observation -> laundry task
  - Evidence: A new imperative and unrelated object mark the topic shift.
  - Confidence: High

**Failure Modes**

- Invented Answer: choosing the vent or outside
- Invented Causality: treating the noise stopping as evidence of its source
- Topic Loss: dropping the unresolved question
- Topic Merge: tying the laundry to the noise

**Hallucinations to watch for**

- The source of the noise
- A need to inspect or repair the vent
- That moving laundry is related to the sound

**Why this example is at this point in the curriculum**

This adds nearby evidence that could tempt the model to answer the question even though the evidence does not resolve it.

**Expected Recovery**

Preserve the source as unresolved, retain the one-minute observation, and recover the laundry task separately.

### 10 — `nested_boundary_depth`

**Example_ID:** G1.2.1-010  
**Difficulty:** hard

**Lesson**

`nested_boundary_depth`

**Author Intent**

Teach that a communication verb and the question it governs form one task, while an unrelated observation remains separate.

**Scenario**

An errand-planning note that explicitly warns against splitting one compound action.

**Reason each fragment exists**

- “Ask Devon whether the replacement badge is ready before going downtown”: Forms one complete information-gathering task.
- “not ask Devon and then separately figure out the badge, it’s one thing”: Provides explicit evidence against excessive fragmentation.
- “The lobby printer is low on paper”: Adds a separate observation.

**Boundary Evidence**

- Boundary: combined Devon/badge task -> printer observation
  - Evidence: The subject and intent shift from a communication task to equipment status.
  - Confidence: High

**Failure Modes**

- Excessive Fragmentation: splitting the ask and badge-status question
- Topic Merge: connecting the printer observation to the downtown trip
- Unsupported Addition: creating a task to refill the printer
- Topic Loss: dropping the before-downtown condition

**Hallucinations to watch for**

- That Devon owns or issued the badge
- That the printer must be refilled by the writer
- A scheduled time for going downtown

**Why this example is at this point in the curriculum**

This is a direct boundary-precision stress test after an earlier nested qualification example.

**Expected Recovery**

Return one action item containing the full Devon/badge question and a separate printer observation.

## Stage 3 — Controlled combination (Examples 11–14)

### 11 — `multi_person_attribution`

**Example_ID:** G1.2.1-011  
**Difficulty:** expert

**Lesson**

`multi_person_attribution`

**Author Intent**

Test attribution across two speakers, two reported actions, a buried task, and an unresolved question.

**Scenario**

A shared-expenses/project note involving a folder, photographed receipts, and a corrected total.

**Reason each fragment exists**

- “Leah said Omar left the blue folder with reception”: Attributes the report to Leah and the folder action to Omar.
- “Omar said Leah already photographed the receipts”: Reverses speaker and actor roles to test attribution tracking.
- “send Omar the corrected total”: Buries a concrete task inside the attribution sequence.
- “Did Leah photograph all of them or only the travel ones?”: Adds an unresolved question about Leah's action.

**Boundary Evidence**

- Boundary: Leah's report -> Omar's report
  - Evidence: The named speaker changes and the reported action changes.
  - Confidence: High
- Boundary: reported actions -> task for Omar
  - Evidence: A new imperative introduces the writer's obligation.
  - Confidence: High
- Boundary: task for Omar -> unresolved question about Leah
  - Evidence: The note shifts from action to unknown scope of a prior action.
  - Confidence: High

**Failure Modes**

- Misattribution: swapping who said or did each action
- Topic Loss: dropping the corrected-total task
- Invented Answer: deciding which receipts Leah photographed
- Topic Merge: treating the corrected total as part of the photography question

**Hallucinations to watch for**

- Who owns the folder
- Whether all receipts were photographed
- Why the total needed correction

**Why this example is at this point in the curriculum**

This begins controlled combination: multi-person attribution is primary, with buried-task retention and open-question preservation as secondary pressure.

**Expected Recovery**

Correctly preserve both reported statements, list sending Omar the corrected total as the only action item, and leave the receipt-scope question unresolved.

### 12 — `open_question_preservation`

**Example_ID:** G1.2.1-012  
**Difficulty:** expert

**Lesson**

`open_question_preservation`

**Author Intent**

Test an unresolved memory question, a task that can resolve it, and an interrupted secondary topic.

**Scenario**

A planning note where the writer is unsure whether a room-change communication happened.

**Reason each fragment exists**

- “Did I ever confirm the room change with Jules or did I only think about it”: Creates an unresolved question about whether an action occurred.
- “need to check the message thread”: Provides an evidence-supported resolution task.
- “also the catering count, no”: Introduces and immediately interrupts a secondary topic.
- “first find out whether the room change was confirmed”: Returns to the unresolved question and establishes priority without answering it.

**Boundary Evidence**

- Boundary: room-change question/task -> catering-count fragment
  - Evidence: A new noun phrase introduces another topic.
  - Confidence: Medium
- Boundary: catering-count fragment -> resumed room-change priority
  - Evidence: “no, first” explicitly abandons the catering thought and returns to the first topic.
  - Confidence: High

**Failure Modes**

- Invented Answer: claiming the room change was or was not confirmed
- Topic Loss: dropping the unfinished catering-count thought
- Excessive Fragmentation: splitting the room-change question and message-thread check into unrelated intentions
- Unsupported Addition: inventing what needs to happen with the catering count

**Hallucinations to watch for**

- The confirmation status
- The content of the message thread
- A specific catering task or number

**Why this example is at this point in the curriculum**

This combines open-question preservation with interruption handling and tests whether the model can keep an evidence-supported checking task connected to the question it resolves.

**Expected Recovery**

Preserve the confirmation question as unresolved, list checking the message thread as the action, and retain the catering count as an incomplete thought.

### 13 — `standalone_task_retention`

**Example_ID:** G1.2.1-013  
**Difficulty:** expert

**Lesson**

`standalone_task_retention`

**Author Intent**

Teach deduplicated retention of a repeatedly emphasized task while preserving another task and an emotional aside.

**Scenario**

A high-load note in which an administrative deadline competes with a frustrating home problem and a lateness message.

**Reason each fragment exists**

- “Submit the mileage form” / “mileage form before Friday” / “don’t let the mileage form disappear”: Repeats one task in different forms to emphasize retention, not create multiple tasks.
- “the kitchen sink is dripping again which is exhausting”: Adds an observation and emotional aside, neither of which explicitly creates a task.
- “text Bea that I’ll be ten minutes late”: Adds a second independent task.

**Boundary Evidence**

- Boundary: mileage-form task -> sink observation/emotion
  - Evidence: The object and intent shift from administrative action to home observation and feeling.
  - Confidence: High
- Boundary: sink observation/emotion -> text-Bea task
  - Evidence: A new imperative and named recipient introduce another obligation.
  - Confidence: High

**Failure Modes**

- Topic Loss: dropping the mileage form despite repetition or dropping the brief text task
- Excessive Fragmentation: listing the mileage form multiple times
- Unsupported Addition: inventing a sink-repair task
- Invented Causality: claiming the sink caused the lateness

**Hallucinations to watch for**

- A requirement to contact a plumber
- Why the writer will be late
- That Friday is the date of the lateness

**Why this example is at this point in the curriculum**

This controlled-combination example tests retention under repetition, emotional salience, and a second brief task.

**Expected Recovery**

Return one mileage-form action due before Friday, one text-Bea action, and preserve the sink observation/emotional reaction without inventing a repair task.

### 14 — `buried_task_retention`

**Example_ID:** G1.2.1-014  
**Difficulty:** expert

**Lesson**

`buried_task_retention`

**Author Intent**

Test whether two brief tasks, including the final fragment, survive a long interleaved note with an open question and observations.

**Scenario**

A post-demo capture containing project reflection, a speculative idea, a two-person question, an errand, an environmental observation, and a final home task.

**Reason each fragment exists**

- “The demo ran long and I lost the thread around the permissions screen”: Creates a project reflection.
- “maybe the examples need labels”: Adds a tentative idea, not a committed task.
- “did Chris ever send Dana the access list” / “access list question still open”: Creates and repeats an unresolved multi-person question.
- “call the dentist”: Buries a short standalone task.
- “the room was freezing”: Adds a non-actionable observation.
- “before I close this: replace the porch bulb”: Places a second task at the final-fragment position to test retention.

**Boundary Evidence**

- Boundary: demo reflection -> labeling idea
  - Evidence: The note moves from what happened to a tentative design possibility.
  - Confidence: Medium
- Boundary: labeling idea -> access-list question
  - Evidence: A new two-person subject and interrogative form mark a topic shift.
  - Confidence: High
- Boundary: access-list question -> dentist task
  - Evidence: A bare imperative introduces an unrelated obligation.
  - Confidence: High
- Boundary: dentist task -> room observation
  - Evidence: The note changes from action to environmental description.
  - Confidence: High
- Boundary: room observation -> final porch-bulb task
  - Evidence: A closing cue and imperative introduce the final obligation.
  - Confidence: High

**Failure Modes**

- Topic Loss: dropping the dentist or final porch-bulb task
- Invented Answer: claiming Chris sent or did not send Dana the access list
- Unsupported Addition: turning the label idea into a committed task
- Misattribution: reversing Chris and Dana
- Over-Summarization: compressing the note into a vague demo summary

**Hallucinations to watch for**

- The access-list status
- A decision to add labels
- A relationship between the freezing room and any other topic
- A deadline for the dentist or bulb tasks

**Why this example is at this point in the curriculum**

This is the release's maximum controlled interleaving case and specifically tests the known tendency for brief and final tasks to disappear.

**Expected Recovery**

Preserve all six meaningful topics, leave the access-list question unresolved, and return exactly two action items: call the dentist and replace the porch bulb.
