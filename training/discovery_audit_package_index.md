# Discovery Audit Package — Index

**Prepared:** 2026-08-12, by Claude, on Johnny's authorization of this session.
**Implements:** step 4 of `training/intent_recovery_data_model_discovery_plan_chatgpt.md` §9 ("Only after
resolution may Johnny authorize a metadata-and-sample audit package design; access/download remains
separately gated"), assigned to Claude per step 5 of the responsibility protocol in
`intent_recovery_data_strategy_new_chat_handoff_2026-08-11.md` §8 ("If authorized, Claude ordinarily
implements the bounded package without execution").
**Status:** Revision 5 (2026-08-13), after four full rounds of ChatGPT's independent review, each finding
real, confirmed defects. Sent back for a fifth independent review per protocol step 6.

## Scope decisions and delegated determinations (Johnny's explicit choices)

1. **Both tracks included** — Track A (dataset-fit) and Track B (model-capability), not Track A alone.
2. **Everything held to template/protocol-only** — including A1's rights-evidence sheets.
3. **All 36 B2 examples are newly authored** — confirmed, not just the 12 adversarial cases.
4. **B1's added checkpoint arm's identity was delegated to ChatGPT's determination**, then independently
   verified by Claude against this project's own prior settled investigation: `checkpoint-520` /
   `gold_v1.2.1`, via GitHub Release `intent-recovery-model-v0.1.0` (tag `pre-repository-split`, commit
   `2cd31dd`).

## Revision history

**Revision 1**: first draft, all 12 files written, self-tested, sent for review.

**Revision 2** (2026-08-12): ChatGPT's first review found five real defects in the A2 script plus gaps
across A1/A3/A4/A5/B2/B3, all confirmed by Claude before fixing. Two items went to Johnny: self-tests
aren't gated "compute"; B1 gained a fourth panel arm. A3's default AI adjudicator was removed.

**Revision 3** (2026-08-13): ChatGPT's second review found nine more items — including a genuine
self-contradiction Claude introduced while editing B3, and the round's most serious finding: A3's "priority
mechanism" redefinition was itself broken, making A5's gates nearly trivial. Both corrected. Checkpoint
identity was delegated to ChatGPT; B2's all-36-newly-authored reading was confirmed.

**Revision 4** (2026-08-13, same day): ChatGPT's third review found four more issues after itself
independently re-running the A2 self-test: A3's interaction test still let bare proximity qualify as
"dependency"; post-adjudication exclusions could silently drop the retained sample below 24; pool
fingerprinting was observable but not fail-closed; B2's quota had no actual selection algorithm. All fixed.
ChatGPT also determined the B1 checkpoint identity, independently verified by Claude against
`training/production_checkpoint_recovery_handoff.md` before being accepted.

**Revision 5** (2026-08-13, same day): ChatGPT's fourth review found two more real issues in A2
specifically, both confirmed by Claude before fixing:

1. **The post-adjudication top-up mechanism from revision 4 was itself incomplete.** A top-up record had
   nowhere documented to live in an immutable manifest (no stratum, content hash, or collision-flag entry),
   the adjudication artifact had no provision for a second linked round, the gate-0 formula never actually
   added accepted top-up records back into its count, and "same seed continuation rule" wasn't a
   reconstructible mechanism. **Simplified per ChatGPT's own proposed fix rather than building a full
   second adjudication lifecycle**: any post-adjudication exclusion that drops retained count below 24 is
   now a hard stop, full stop — no automatic top-up attempted. `unused_leftover_record_ids` stays in the
   manifest as informational context only.
2. **Pool source validation was optional and caller-defined.** `required_pool_sources` defaulted to `None`,
   so a caller could simply omit it and get zero enforcement; even when supplied, it was arbitrary
   caller-chosen minimums, not a frozen specification, and checked count only. Fixed: `required_pool_sources`
   is now a required parameter with no default anywhere, including the self-test's own calls, and each
   source may pin an exact expected content hash via `PoolSourceSpec`, not just a minimum count. A real
   run's frozen three-file specification (source names, exact record counts, exact content hashes) was
   computed directly from the actual benchmark files in this repo and is now pinned in the A2 protocol doc
   — this is public, already-committed project benchmark data, not external candidate access.

A2's self-test grew from 19 to 20 checks, all passing, reproduced byte-identical across two process
invocations — SHA-256 `c0c4aff2535eb8150bfd31b217f677a3c82409d95eb083525d3f7fd5aacaecdd`.

**Post-approval fix (2026-08-13, same day, after ChatGPT's approval and before push):** committing the
package (on Johnny's "Git it done") surfaced a real defect the review process itself never touched, since
it lived entirely between the working tree and the git blob. The receipt's `18f7209e...` hash — cited
throughout all five revisions by both Claude and ChatGPT, including ChatGPT's own independent
re-verification — was of the file as Python's default text-mode write produced it on Windows (CRLF line
endings). `git add`/`commit` under this repo's `core.autocrlf=true` silently normalized the committed blob
to LF, which hashes differently despite byte-for-byte identical content — the exact species of defect
already caught once before in this project's Phase-2 contrastive-corpus work. Caught here by directly
hashing the committed blob (`git show <commit>:<path> | sha256sum`) rather than assuming the commit step
couldn't have changed anything. Fixed at the root: the script now opens the receipt file explicitly with
`newline="\n"`, so it's LF on every platform regardless of Python's default translation — no future
mismatch between what gets hashed locally and what git actually stores. Receipt regenerated
(`c0c4aff2535eb8150bfd31b217f677a3c82409d95eb083525d3f7fd5aacaecdd`, confirmed byte-identical via `cmp`,
not just `diff`, across separate process invocations) and every citation in this package updated to match.

## File map

| File | Plan section | What it is |
|---|---|---|
| `discovery_audit_package_a1_rights_evidence_template.md` | §3 A1 | Rights/governance evidence-sheet template; PDR-006/008-grounded; silence-is-not-clearance fixed |
| `discovery_audit_package_a2_sample_selection_protocol.md` | §3 A2 | Selection procedure; frozen real pool-source spec; semantic-collision options; hard-stop-on-shortfall (pre- and post-adjudication); four-round defect log |
| `discovery_audit_package_a2_sample_selection_script.py` | §3 A2 | Reference implementation — multi-speaker caps, mandatory fail-closed pool validation with content hashes, per-record manifest hashes, preflight validation |
| `discovery_audit_package_a2_selftest_receipt.json` | §3 A2 | 20/20 checks passed, reproduced byte-identically across two process invocations, SHA-256 `c0c4aff2535eb8150bfd31b217f677a3c82409d95eb083525d3f7fd5aacaecdd` |
| `discovery_audit_package_a3_mechanism_mapping_manual.md` | §3 A3 | Coding manual; priority/interacting definitions corrected across two same-day rounds (action components excluded; dependency requires adjudicator judgment, not proximity alone) |
| `discovery_audit_package_a4_target_audit_rubric.md` | §3 A4 | Target classification rubric; predeclared seeded timing-subset draw |
| `discovery_audit_package_a5_dataset_fit_checklist.md` | §3 A5 | Decision checklist; gate 0 now a strict hard-stop prerequisite covering both pre- and post-adjudication completeness, no automatic recovery |
| `discovery_audit_package_b1_model_panel_freeze_criteria.md` | §4 B1 | 4-model panel freeze checklist; arm 2 identity determined and independently verified: `checkpoint-520`/`gold_v1.2.1` |
| `discovery_audit_package_b2_example_selection_protocol.md` | §4 B2 | Reproducible selection procedure with a real deterministic constrained-selection algorithm (seeded retry + capped no-valid-subset stop) |
| `discovery_audit_package_b3_blind_scoring_instrument.md` | §4 B3–B4 | Scoring rubric; corrected paired-verdict threshold scoping; split schema fields; 4-arm reporting |
| `discovery_audit_package_privacy_stop_conditions_checklist.md` | §5 | Work-stopping checklist; A2-shortfall stop added |
| `discovery_audit_package_index.md` | — | This file |

## What this package does NOT do

- No dataset has been accessed, downloaded, or sampled.
- No account has been created, no license term has been accepted.
- No candidate's rights evidence sheet has been filled in for a real candidate.
- No model has been downloaded or run.
- No corpus has been mutated; no new training record has been authored.
- No adjudicator has been assigned for any real candidate's disputed tags — Johnny's separate call.
- No semantic-collision method has been chosen — two options predeclared, picking one is a hard stop.
- B1's arm 2 checkpoint identity is determined but not downloaded, executed, or otherwise acted upon.
- Reading `datasets/benchmark/`'s three existing files to pin their real counts/hashes is the project's own
  already-committed benchmark data, not external dataset access — done openly, not silently.
- Nothing here has been committed or pushed — gated on Johnny's hand-typed "Git it done."

## What happens next, per the established sequence

1. ChatGPT independently reviews this revision (protocol step 6) — specifically whether the simplified
   post-adjudication hard-stop rule actually closes the lifecycle gap (rather than reintroducing it in a
   new form), and whether the mandatory pool-validation fix is sound.
2. Any material disagreement is work-stopping and returns to Johnny, per protocol step 3.
3. Johnny separately authorizes any acquisition, model execution, or compute (protocol step 7) — this
   package's existence is not that authorization, and does not request it.
