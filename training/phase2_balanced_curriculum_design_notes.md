# Phase-2 Balanced Curriculum Proposal - Design Notes

**Status:** Draft proposal for joint ChatGPT/Claude review. Separate from the canonical corpus and uncommitted.

**Scope:** These notes cover exactly the 12 records in `phase2_balanced_curriculum_proposal.jsonl`. The allocation follows the committed Phase-2 static-review package: two unresolved-state/decision-task contrast examples, two paraphrased-restatement deduplication examples, four high-count `simple_list` examples, two dense `cross_field_completeness` examples, and two `two_unrelated_tasks` examples.

## P2-001

Example_ID: P2-001

Lesson:
`open_question_preservation` - preserve an unresolved choice as unresolved rather than turning it into a decision task.

Author Intent:
Prove that the model can retain both named alternatives and a separate observation while producing no action item when the writer has not asked to choose.

Scenario:
A calm entryway-planning note recorded after noticing the afternoon light.

Reason each fragment exists:
- "I haven't picked the corkboard or the magnetic strip for the entryway": establishes an unresolved either/or state with two specific alternatives but no instruction to decide.
- "The afternoon light missed that wall completely": introduces a later observation that must remain separate and must not be treated as an answer to the choice.

Boundary Evidence:
- Boundary: unresolved entryway choice -> afternoon-light observation
  Evidence: Topic Shift from a furnishing choice to a factual lighting observation; the second sentence supplies no causal or decision language.
  Confidence: High

Failure Modes:
- Rewrites the unresolved state as an imperative to choose.
- Drops one of the two alternatives.
- Treats the lighting observation as a reason for or answer to the choice.
- Invents an action item.

Hallucinations to watch for:
- A selected wall fixture.
- A claim that the lack of afternoon light favors either alternative.
- A deadline, shopping step, or installation task.

Why this example is at this point in the curriculum:
It provides the zero-action side of the Phase-2 modality contrast before P2-002 supplies the explicit decision-task side.

Expected Recovery:
Preserve the choice as unresolved, preserve both alternatives and the separate light observation, and return no actions.

## P2-002

Example_ID: P2-002

Lesson:
`idea_action_boundary` - recognize an explicit request to choose as an action while keeping a nearby observation non-actionable.

Author Intent:
Prove that wording which directly instructs a choice produces one action, in contrast with P2-001's unresolved state.

Scenario:
A short preparation note written before leaving for a hike.

Reason each fragment exists:
- "Before leaving for the hike, choose either the paper trail map or the offline map": supplies an explicit decision task, two alternatives, a purpose, and an event-relative qualifier.
- "The thermos is already in the side pocket": supplies an unrelated completed-state observation that should not become a task or an answer.

Boundary Evidence:
- Boundary: map-choice task -> thermos observation
  Evidence: Intent Shift from an imperative future choice to a present-state observation about a different object.
  Confidence: High

Failure Modes:
- Treats the explicit choice as merely tentative and omits the action.
- Produces two actions, one for each alternative.
- Promotes the thermos observation into a packing task.
- Drops the before-leaving qualifier or hike purpose.

Hallucinations to watch for:
- A preferred map.
- A reason the thermos determines the map choice.
- A task to move, fill, or pack the thermos.

Why this example is at this point in the curriculum:
It completes the paired modality contrast begun by P2-001 without changing the surrounding two-fragment structure.

Expected Recovery:
Return two supported bullets and exactly one action to choose between the maps before leaving for the hike; keep the thermos sentence as an observation.

## P2-003

Example_ID: P2-003

Lesson:
`repeated_reminder` - deduplicate one task restated with different verbs and aliases.

Author Intent:
Prove that "send paperwork" and "file a claim" refer to one warranty task, not two separate obligations.

Scenario:
A hurried reminder about damage paperwork for a cracked display.

Reason each fragment exists:
- "Send the cracked display's warranty paperwork before Friday": states the task with an object and deadline.
- "Need to get that damage claim filed by Friday": restates the same task using a pronoun-like alias, a different verb, and the same deadline.

Boundary Evidence:
- Boundary: first wording -> second wording
  Evidence: Embedded Reminder rather than a new topic; the shared damaged display, warranty/claim meaning, and Friday deadline strongly identify one task.
  Confidence: High

Failure Modes:
- Produces two bullets or two actions.
- Drops the cracked-display identity or Friday deadline during deduplication.
- Treats sending paperwork and filing the claim as separate sequential tasks despite the aliasing evidence.

Hallucinations to watch for:
- A recipient, claim number, replacement request, or approval state.
- A distinction between two documents that the source does not make.

Why this example is at this point in the curriculum:
It moves beyond literal repetition by changing both the governing verb and the object phrase while retaining strong identity evidence.

Expected Recovery:
Collapse the two phrasings into one bullet and one action for filing the cracked display's damage claim before Friday.

## P2-004

Example_ID: P2-004

Lesson:
`repeated_reminder` - deduplicate a service appointment restated through event and service aliases.

Author Intent:
Prove that arranging a piano tuning and booking the instrument service are one supported task even without literal phrase repetition.

Scenario:
A brief recital-preparation note written between other plans.

Reason each fragment exists:
- "Arrange a piano tuning before the recital": introduces the appointment task and its event-relative deadline.
- "Still need to book the instrument service ahead of the recital": paraphrases the same obligation with different verb and noun choices.

Boundary Evidence:
- Boundary: tuning reminder -> service reminder
  Evidence: Embedded Reminder; piano/instrument service and the shared recital qualifier identify one referent and one deadline.
  Confidence: High

Failure Modes:
- Creates separate tuning and service actions.
- Removes the recital qualifier.
- Over-deduplicates by returning no task because the second sentence sounds like commentary.

Hallucinations to watch for:
- A tuner, date, venue, cost, or confirmation state.
- A second instrument or a second service appointment.

Why this example is at this point in the curriculum:
It provides a second paraphrase pattern whose semantic identity depends on event context rather than on a repeated object phrase.

Expected Recovery:
Return one bullet and one action to book the piano tuning before the recital.

## P2-005

Example_ID: P2-005

Lesson:
`simple_list` - retain five explicit actions in a straightforward fragmented list.

Author Intent:
Extend the existing `simple_list` skill beyond the four-action corpus ceiling while preserving every task and the one time qualifier.

Scenario:
A compact event-preparation checklist typed with semicolon separators.

Reason each fragment exists:
- "return the borrowed projector": first independent task and borrowed-object qualifier.
- "order replacement name badges": second independent task.
- "post the room number in the group chat before the welcome table opens": third task with destination and event-relative qualifier in a middle position.
- "print the museum tickets": fourth independent task.
- "inspect the first-aid kit": fifth independent task and final-position retention check.

Boundary Evidence:
- Boundary: projector return -> badge order
  Evidence: Intent Shift marked by a semicolon and a new imperative verb with an unrelated object.
  Confidence: High
- Boundary: badge order -> room-number post
  Evidence: Intent Shift marked by a semicolon, new verb, and new destination.
  Confidence: High
- Boundary: room-number post -> ticket printing
  Evidence: Intent Shift marked by a semicolon and unrelated object.
  Confidence: High
- Boundary: ticket printing -> kit refill
  Evidence: Intent Shift marked by a semicolon and new imperative verb.
  Confidence: High

Failure Modes:
- Drops a middle or final task.
- Merges unrelated tasks.
- Loses "before the welcome table opens" or the group-chat destination.
- Adds an unsupported recipient to the projector or badges.

Hallucinations to watch for:
- A return location, badge names, ticket count, or first-aid inventory.
- Any dependency or order between the five tasks.

Why this example is at this point in the curriculum:
It is the first rung above the current four-action ceiling, so it is hard rather than expert and keeps the syntax mechanically clear.

Expected Recovery:
Return five bullets and five distinct actions, preserving the borrowed-projector detail and the room-number task's destination and event-relative qualifier.

## P2-006

Example_ID: P2-006

Lesson:
`simple_list` - retain six explicit actions in a comma-separated task run.

Author Intent:
Increase list length to six while varying punctuation and placing a condition on the fourth task.

Scenario:
A facilities-and-records checklist entered quickly before setup.

Reason each fragment exists:
- "renew parking permit": first administrative task.
- "launder reusable tablecloths": second maintenance task.
- "catalog the archive boxes": third organization task.
- "pair handheld radios before setup": fourth task with a condition/deadline.
- "deliver spare keys to the front desk": fifth task with a destination.
- "digitize the completed survey cards": sixth task and final-position retention check.

Boundary Evidence:
- Boundary: permit renewal -> tablecloth washing
  Evidence: Intent Shift marked by a comma and unrelated verb/object pair.
  Confidence: High
- Boundary: tablecloth washing -> box labeling
  Evidence: Intent Shift marked by a comma and unrelated object.
  Confidence: High
- Boundary: box labeling -> radio charging
  Evidence: Intent Shift marked by a comma, new object, and new condition.
  Confidence: High
- Boundary: radio charging -> key delivery
  Evidence: Intent Shift marked by a comma and a destination-bearing imperative.
  Confidence: High
- Boundary: key delivery -> form scanning
  Evidence: Intent Shift marked by a comma and unrelated verb/object pair.
  Confidence: High

Failure Modes:
- Returns only five actions because of list length.
- Combines archive labeling with form scanning as one records task.
- Drops "before setup," "spare," "signed," or "front desk."
- Splits one task into multiple invented substeps.

Hallucinations to watch for:
- A permit deadline, box contents, radio owner, key recipient, or storage location.
- A claim that any task is complete.

Why this example is at this point in the curriculum:
It is the second hard rung: one task longer than P2-005, with weaker comma boundaries and varied qualifiers but no bullet-ceiling conflict.

Expected Recovery:
Return six bullets and six distinct actions with all qualifiers attached to the correct tasks.

## P2-007

Example_ID: P2-007

Lesson:
`simple_list` - retain seven explicit actions at the bullet ceiling.

Author Intent:
Prove that a seven-task list can populate both output fields completely without task loss or cross-task qualifier movement.

Scenario:
A workshop and field-trip checklist captured with slash separators.

Reason each fragment exists:
- "water rooftop planters": first task.
- "update the emergency contact sheet": second task.
- "request the van for the field trip": third task with purpose.
- "package the ceramic samples": fourth task with object detail.
- "copy workshop handouts": fifth task.
- "test the portable microphone": sixth task with object qualifier.
- "return the folding signs to storage by 3": seventh task with destination and final-position deadline.

Boundary Evidence:
- Boundary: planter watering -> contact-sheet update
  Evidence: Intent Shift marked by a slash and unrelated verb/object pair.
  Confidence: High
- Boundary: contact-sheet update -> van reservation
  Evidence: Intent Shift marked by a slash and a new purpose-bearing task.
  Confidence: High
- Boundary: van reservation -> sample packaging
  Evidence: Intent Shift marked by a slash and unrelated object.
  Confidence: High
- Boundary: sample packaging -> handout copying
  Evidence: Intent Shift marked by a slash and unrelated verb/object pair.
  Confidence: High
- Boundary: handout copying -> microphone testing
  Evidence: Intent Shift marked by a slash and new equipment object.
  Confidence: High
- Boundary: microphone testing -> sign return
  Evidence: Intent Shift marked by a slash and a new destination/deadline.
  Confidence: High

Failure Modes:
- Drops one task at the seven-item ceiling.
- Attaches "by 3" to microphone testing instead of sign return.
- Merges field-trip and workshop tasks into a single action.
- Reorders roles or invents recipients.

Hallucinations to watch for:
- A watering amount, contact names, van provider, package destination, copy count, test procedure, or storage location.

Why this example is at this point in the curriculum:
It is the first expert rung because it reaches the hard seven-bullet ceiling and tests complete alignment between two full seven-item fields.

Expected Recovery:
Return seven bullets and seven actions, with the field-trip purpose and the sign-return destination and deadline intact.

## P2-008

Example_ID: P2-008

Lesson:
`simple_list` - retain eight explicit actions when bullets are capped at seven.

Author Intent:
Prove that the bullet ceiling does not cause action loss or force two distinct tasks to be merged.

Scenario:
A mixed maintenance and archive checklist entered as eight semicolon-separated fragments.

Reason each fragment exists:
- "inventory the display easels": first task.
- "replenish packing paper": second task.
- "document the repaired frames": third task with repaired-state qualifier.
- "take the loan agreement to the archive": fourth task with destination; deliberately omitted from bullets, not from narrative or actions.
- "rinse the watercolor cups": fifth task.
- "pair the translation headsets": sixth task.
- "portion the soup into freezer containers": seventh task with quantity/plural detail and destination container.
- "secure the mailbox flag before pickup": eighth task with a final-position condition.

Boundary Evidence:
- Boundary: easel inventory -> paper replenishment
  Evidence: Intent Shift marked by a semicolon and unrelated object.
  Confidence: High
- Boundary: paper replenishment -> frame documentation
  Evidence: Intent Shift marked by a semicolon and a new verb/object pair.
  Confidence: High
- Boundary: frame documentation -> agreement transfer
  Evidence: Intent Shift marked by a semicolon and a destination-bearing task.
  Confidence: High
- Boundary: agreement transfer -> cup rinsing
  Evidence: Intent Shift marked by a semicolon and unrelated object.
  Confidence: High
- Boundary: cup rinsing -> headset pairing
  Evidence: Intent Shift marked by a semicolon and new equipment object.
  Confidence: High
- Boundary: headset pairing -> soup portioning
  Evidence: Intent Shift marked by a semicolon and unrelated verb/object pair.
  Confidence: High
- Boundary: soup portioning -> flag securing
  Evidence: Intent Shift marked by a semicolon and a new condition-bearing task.
  Confidence: High

Failure Modes:
- Produces fewer than eight action items.
- Merges the agreement transfer with a neighboring task to fit the bullet ceiling.
- Omits the agreement task from narrative or actions merely because it is omitted from bullets.
- Moves "before pickup" to soup freezing or invents a pickup recipient.

Hallucinations to watch for:
- Easel count, paper amount, frame owner, archive staff, cup contents, headset users, soup ingredients, or mailbox location.
- Any causal or chronological link between neighboring tasks.

Why this example is at this point in the curriculum:
It is the final expert rung. It is the first proposal record with more source-supported tasks than permitted bullets, making cross-field completeness and non-merging essential within the existing `simple_list` category.

Expected Recovery:
Preserve all eight tasks distinctly in narrative and actions, use no more than seven bullets, deliberately omit only the agreement-delivery task from bullets, and retain all qualifiers.

## P2-009

Example_ID: P2-009

Lesson:
`cross_field_completeness` - preserve six supported ideas and exactly two actions under mixed attribution, uncertainty, observation, suggestion, and deadline content.

Author Intent:
Prove that every source-supported idea survives in narrative and bullets while only the two explicit open-house tasks enter actions.

Scenario:
An installation-planning note assembled after a room setup check and a teammate's update.

Reason each fragment exists:
- "Before the open house doors unlock, upload the revised floor plan": first explicit task with shared event-relative deadline.
- "call the lighting supplier": second explicit task governed by the same deadline phrase.
- "I still don't know whether the west window was measured or only photographed": unresolved question with two possible states.
- "The folding screens looked uneven after setup": factual observation, not a task.
- "Maybe place the visitor cards near the exit": tentative idea, not a committed action.
- "Ren said Salma handed the spare clips to the installation lead": attributed report with distinct speaker, actor, object, and recipient.

Boundary Evidence:
- Boundary: floor-plan upload -> supplier call
  Evidence: Intent Shift between coordinated imperative verbs sharing one deadline phrase.
  Confidence: High
- Boundary: supplier call -> window uncertainty
  Evidence: Intent Shift from explicit task to first-person unresolved knowledge state.
  Confidence: High
- Boundary: window uncertainty -> screen observation
  Evidence: Topic Shift to a separate setup object and a definite observation.
  Confidence: High
- Boundary: screen observation -> visitor-card idea
  Evidence: Intent Shift from factual observation to tentative possibility marked by "Maybe."
  Confidence: High
- Boundary: visitor-card idea -> attributed clip report
  Evidence: Context Shift to named people and a reported completed event.
  Confidence: High

Failure Modes:
- Returns only five bullets by merging or dropping an idea.
- Omits the open-house-door qualifier from one or both actions.
- Converts the window question, screen observation, or card suggestion into an action.
- Misattributes Salma's act to Ren or the installation lead.

Hallucinations to watch for:
- Whether the window was measured.
- A reason the screens were uneven.
- A commitment to place the cards.
- A claim that Ren handled the clips or that the installation lead supplied them.

Why this example is at this point in the curriculum:
It directly targets the residual six-bullet/two-action gap with a different order, setting, roles, and syntax from the frozen dense benchmark case.

Expected Recovery:
Return six distinct bullets and two actions, retain the shared before-unlocking qualifier, preserve the unresolved window status and tentative card idea, and keep the attribution roles exact.

## P2-010

Example_ID: P2-010

Lesson:
`cross_field_completeness` - preserve six mixed ideas and two actions when attribution appears first and uncertainty appears last.

Author Intent:
Provide positional variation for the dense pattern while testing role preservation, one task deadline, a recipient, a non-task observation, a tentative idea, and a clean unresolved ending.

Scenario:
An event-access note combining a security update with setup reminders and room observations.

Reason each fragment exists:
- "Jae reported that the north gate code had been changed by the security vendor": attributed completed-state report with speaker and actor roles.
- "Before the staff briefing, pack the two blue banners": explicit task with event-relative deadline and quantity.
- "Send the access map to the event host": second task with recipient.
- "The lobby smelled like fresh paint this morning": time-qualified sensory observation, not a task.
- "It may help to place a bench near the coat rack": tentative suggestion, not a commitment.
- "Whether the vendor tested the backup keypad is still unknown": unresolved final question about a separate device.

Boundary Evidence:
- Boundary: gate-code report -> banner task
  Evidence: Context Shift from reported past security change to a direct future setup obligation.
  Confidence: High
- Boundary: banner task -> access-map task
  Evidence: Intent Shift to a second imperative with a distinct object and recipient.
  Confidence: High
- Boundary: access-map task -> lobby observation
  Evidence: Intent Shift from imperative to time-qualified sensory observation.
  Confidence: High
- Boundary: lobby observation -> bench suggestion
  Evidence: Intent Shift from fact to tentative possibility marked by "may help."
  Confidence: High
- Boundary: bench suggestion -> keypad uncertainty
  Evidence: Intent Shift from tentative proposal to explicitly unresolved information.
  Confidence: High

Failure Modes:
- Drops the final unresolved question or another idea from bullets.
- Assigns the security-vendor action to Jae.
- Applies the staff-briefing qualifier to the access-map task or removes it from banner packing.
- Promotes the lobby observation or bench suggestion into actions.
- Omits "two," "blue," or "event host."

Hallucinations to watch for:
- The new gate code.
- Confirmation that the keypad was tested.
- A task to ventilate or repaint the lobby.
- A committed bench placement or a person responsible for it.

Why this example is at this point in the curriculum:
It balances P2-009 by reversing the positions of attribution and uncertainty and by limiting the deadline to only one of the two tasks.

Expected Recovery:
Return six bullets and exactly two actions, preserve Jae as reporter and the vendor as actor, attach the staff-briefing qualifier only to banner packing, and leave the keypad question unresolved.

## P2-011

Example_ID: P2-011

Lesson:
`two_unrelated_tasks` - retain two plainly unrelated tasks across both bullets and actions.

Author Intent:
Reinforce the regression guard with two short tasks whose different objects, verbs, and time qualifiers make their independence unambiguous.

Scenario:
A compact checklist combining a copy-center errand with a later roster upload.

Reason each fragment exists:
- "Drop off the repaired headphones while the copy center is open": first task with destination context, repaired-state detail, and an availability condition.
- "before bed, upload the volunteer roster": second unrelated task with a front-position time qualifier after a semicolon.

Boundary Evidence:
- Boundary: headphone drop-off -> roster upload
  Evidence: Topic Shift and Intent Shift marked by a semicolon, a new verb and object, and a different time qualifier.
  Confidence: High

Failure Modes:
- Drops one task from action_items while retaining it elsewhere.
- Merges the tasks into one compound bullet or action.
- Swaps the copy-center condition and "before bed."
- Removes "repaired," "volunteer," or the copy-center context.

Hallucinations to watch for:
- A copy-center address, roster recipient, upload portal, completion state, or causal connection between the tasks.

Why this example is at this point in the curriculum:
It is a clean, easy regression guard after the dense cases and varies punctuation and qualifier placement from the frozen two-task benchmark.

Expected Recovery:
Return two bullets and two actions, preserving the copy-center availability condition on the headphone drop-off and "before bed" on the roster upload.

## P2-012

Example_ID: P2-012

Lesson:
`two_unrelated_tasks` - retain two similar-looking instructions as separate tasks instead of over-deduplicating them.

Author Intent:
Balance the paraphrase-deduplication examples by proving that a shared verb does not make tasks duplicates when objects and recipients differ.

Scenario:
A concise packing-area note with two labels needed for different offices.

Reason each fragment exists:
- "Label the equipment crate for the rental desk": first task with a specific object and destination context.
- "Label the costume box for the theater office": second task sharing the verb but carrying a different object and destination context.

Boundary Evidence:
- Boundary: equipment-crate label -> costume-box label
  Evidence: Intent Shift despite the repeated verb; distinct objects and destination contexts provide strong evidence for two independent obligations.
  Confidence: High

Failure Modes:
- Over-deduplicates the two labeling tasks into one action.
- Combines both objects or destination contexts into one unsupported label.
- Swaps the equipment/rental-desk or costume/theater-office pairings.
- Drops one task from action_items.

Hallucinations to watch for:
- Label text, delivery instructions, deadlines, contents of either container, or a relationship between the rental and theater contexts.

Why this example is at this point in the curriculum:
It closes the proposal with an explicit guard against the opposite error from P2-003 and P2-004: semantic deduplication must not erase genuinely separate but syntactically similar tasks.

Expected Recovery:
Return two bullets and two separate labeling actions, preserving the correct object-destination pairing for each.
