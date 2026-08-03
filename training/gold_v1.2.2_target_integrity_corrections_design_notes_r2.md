# Gold v1.2.2 Target-Integrity Corrections — Revision 2

**Date:** 2026-08-03  
**Companion artifact:** `gold_v1.2.2_target_integrity_corrections_proposal_r2.jsonl`  
**Companion SHA-256:** `dfb4a001d73c49714fb72f02574c5b00120262cb032251e3e3e232992dde8097`  
**Status:** Revised design-only proposal; final byte-level Claude review required  
**Corpus edits authorized:** None  
**Compute authorized:** None

## Resolution of the ti-002 disagreement

Claude’s counter-proposal is accepted.

The original ChatGPT proposal retained `Attend the meeting` and `Lunch with Dana at noon` as actions based on a claimed corpus convention for terse commitments and scheduled events. Direct inspection showed that claim was wrong:

- the `meeting moved to 2 p.m.` record keeps the scheduled-event mention in bullets and does not promote it to an action;
- the `Tuesday 3 PM meeting` record likewise keeps the meeting itself in bullets, while only the attached instruction to bring the Q3 report becomes an action;
- no other corpus record establishes that `lunch with [person] at [time]` should be treated as an action.

The source therefore supports only the checklist action with sufficient confidence. Revision 2 keeps:

- narrative: unchanged;
- five bullets: unchanged;
- actions: only `Grab keys, wallet, and phone`.

ti-002 changes from **B5/A5 to B5/A1**, an action delta of **−4**.

## Final proposed corrections

| ID | Category | Current | Revision-2 proposal | Status |
|---|---|---:|---:|---|
| ti-001 | `dangling_reference` | B3/A3 | B3/A2 | Agreed by both reviewers |
| ti-002 | `rapid_topic_switching_incomplete_sentences` | B5/A5 | B5/A1 | Claude counter-proposal accepted by ChatGPT |
| ti-003 | `standalone_task_retention` | B4/A2 | B4/A2 | Agreed by both reviewers |

The exact current and proposed structured outputs are in the companion JSONL. That file—not this prose summary—is the byte-level review target.

## Revised structural impact

### Train split: 60 examples

| Actions | Current | Revision-2 derived corpus |
|---:|---:|---:|
| 0 | 7 | 7 |
| 1 | 22 | 23 |
| 2 | 16 | 17 |
| 3 | 7 | 6 |
| 4 | 7 | 7 |
| 5 | 1 | 0 |

### Full corpus: 66 examples

| Actions | Current | Revision-2 derived corpus |
|---:|---:|---:|
| 0 | 8 | 8 |
| 1 | 24 | 25 |
| 2 | 18 | 19 |
| 3 | 8 | 7 |
| 4 | 7 | 7 |
| 5 | 1 | 0 |

No bullet-count changes are proposed. The corrected train corpus has a truthful maximum of four actions. Later A5–A8 coverage must come from newly authored, fully supported examples—not from retaining unsupported promotions.

## Mechanical verification completed

Against the pinned 66-example corpus:

- all three source hashes resolve uniquely;
- all three `source_input` fields match exactly;
- all three `current_output` objects match exactly;
- all three declared count deltas match the proposed structures;
- applying the proposal in memory reproduces both distribution tables above.

## Historical and implementation boundary

Gold v1.2.2 remains immutable. If Revision 2 is accepted, implementation must create a separately fingerprinted derived candidate corpus and must:

1. load the pinned 66-example source, not live `synthetic.jsonl`;
2. locate records by exact input SHA-256;
3. fail if the current output differs from the companion JSONL;
4. replace only the three structured `output` objects;
5. preserve inputs, categories, difficulties, order, and split membership;
6. regenerate v1 and v2 serializations mechanically;
7. prove exactly three structured outputs changed;
8. parse all v2 targets back to exact structured equality;
9. record old/new corpus and proposal fingerprints.

No implementation or compute follows automatically from alignment on this revision.

## Requested final review

Claude should perform the previously requested hash-level review against the attached Revision-2 JSONL, with particular attention to ti-002’s exact action array and the revised distributions.

**ChatGPT alignment status: Aligned with Claude’s counter-proposal. No disagreement remains from my side.**
