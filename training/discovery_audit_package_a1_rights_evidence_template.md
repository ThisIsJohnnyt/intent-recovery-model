# A1 — Dataset Rights/Governance Evidence Sheet (blank template)

**Operationalizes:** `training/intent_recovery_data_model_discovery_plan_chatgpt.md` §3, "A1. Rights and
governance gate (before samples)".

**Status: template only.** No candidate's sheet has been filled in as part of this package. Per Johnny's
2026-08-12 scope decision, A1 is held to template-only alongside A2–A5, not completed for DialogSum, QMSum,
or AMI even though the plan's own stop rule only blocks *sample access*, not public-source license
research. Filling this in for a real candidate is a separate, later step.

**Boundary, restated:** completing this sheet never requires creating an account, accepting a license's
click-through terms, or opening a gated/paid record. If any field cannot be answered from a publisher's
public license text, data statement, README, or the original paper, the field is marked `UNRESOLVED —
requires action beyond public-source research`, not guessed.

---

## Sheet fields

**Candidate name / version-commit:**
**Preparer / date prepared:**
**Reviewer (independent) / date reviewed:**

### 1. Ownership and provenance

- Owner/controller:
- Every upstream source (list each; a dataset assembled from multiple corpora has one row per corpus):
- Original paper / official citation:

### 2. Access method

- How is the dataset obtained (direct download, application, gated request, paid license)?
- Is registration required? Y/N — detail:
- Is click-through or negotiated term acceptance required? Y/N — detail:
- **If Y to either:** this candidate cannot proceed past this sheet without Johnny separately approving the
  specific terms (plan §3 A1 "Stop" rule). Record the terms' location here for his review; do not accept
  them.

### 3. Use restrictions

- Commercial-use restriction (verbatim clause + citation):
- Research-only restriction, if any (verbatim clause + citation):
- License identifier (e.g. SPDX) if one applies to the data itself, as distinct from any code repository
  that hosts it — **a permissive repository license is not evidence about the embedded data** (plan §3 A1:
  "A permissive code/repository license is not sufficient evidence for embedded third-party data").

### 4. Permission matrix

For each row, answer **Yes / No / Unclear**, with the citation that supports the answer. `Unclear` is a
valid, expected answer — it is not filled in as `No` to be safe or `Yes` to be optimistic.

| Permitted use | Y/N/Unclear | Citation |
|---|---|---|
| Model training on the raw data | | |
| Training on modified/re-annotated versions of the data | | |
| Creating and retaining a derivative dataset | | |
| Internal project sharing (e.g. with a reviewer) | | |
| Publishing illustrative examples in project documentation | | |
| Redistributing the data or a derivative of it | | |
| Distributing trained model weights whose training set included this data | | |

### 5. Attribution / share-alike obligations

- Required attribution text or form, if any:
- Share-alike / same-license-propagation clause, if any (verbatim + citation):
- Does this clause's scope cover only "adapted material" as defined by the license, or does it reach
  further? Quote the license's own definition rather than assuming:

### 6. Consent, privacy, and retention

- Consent statement for original data subjects/speakers, if published:
- Withdrawal/right-to-erasure mechanism, if any:
- De-identification method used by the publisher, if disclosed:
- Sensitive-content statement (health, minors, criminal justice, etc.), if any:
- Retention limits the publisher imposes on downstream holders, if any:

### 7. Jurisdiction and institutional restrictions

- Governing jurisdiction, if stated:
- Any IRB/ethics-board or institutional-access restriction that could bind a downstream user:
- Any other unresolved ambiguity not captured above:

### 8. Project-policy compatibility

**Revised 2026-08-12:** the discovery plan's §2 states the project's noncommercial/attribution *intent*,
but licensing has since been concretely settled (PDR-006, PDR-008, both after the plan was written) into
three specific classes. Compatibility must be checked against the actual settled classes below, not just
the plan's general policy language — a candidate's data would most likely enter under the first class:

- **Dataset + docs** (this is the class a candidate's re-annotated data would join): **CC BY-NC-SA 4.0**
  (per PDR-006), subject to the historical CC BY 4.0 snapshot for anything released before `d3deeef`. Note
  ShareAlike's actual scope per the license's own definition of "Adapted Material" — do not assume it
  reaches further than that definition states.
- **Code**: **PolyForm Noncommercial 1.0.0** (per PDR-008, superseding PDR-007's CC BY-NC-SA choice for
  code specifically) — chosen over CC precisely because CC has no source-delivery clause and no patent
  grant. Any candidate-specific processing script would fall under this class, not the dataset's CC BY-NC-
  SA 4.0.
- **Model weights**: **corrected 2026-08-13** — "not licensed at all" (the 2026-08-12 wording) overstated
  it. The accurate posture: the project asserts **no separate copyright license** over released weights, and
  instead uses a **non-assertive acknowledgment/noncommercial-use request** (not a legal condition) per
  `MODEL_RELEASE_NOTICE.md`, given unsettled model-weight copyrightability — while still retaining and
  honoring the upstream Apache 2.0 compliance materials (`THIRD_PARTY_NOTICES.md`, vendored license texts,
  the required-notice line) that PDR-008 put in place. A candidate's terms on "trained-weight distribution"
  (permission-matrix row 7 above) must be checked against this actual posture, not against "no rights
  reserved at all."

Checks:

- Does this candidate's license permit a downstream noncommercial-only redistribution with a
  fork-propagating restriction, compatible with CC BY-NC-SA 4.0's ShareAlike scope (for the re-annotated
  data) without conflicting with the candidate's own terms? Explain:
- Can Johnny's attribution be added to project documentation without contradicting or duplicating the
  candidate's own required attribution?
- Does the candidate's permission-matrix answer on "trained-weight distribution" (row 7 above) conflict
  with the project's non-assertive, request-only posture on model weights? **Corrected 2026-08-13**: the
  2026-08-12 version of this check said a merely-silent answer "does not" conflict — that was wrong. Per
  field 4's own governing rule, `Unclear`/silent is not a clearance; it stays an **open, unresolved item**
  that must be actively resolved (by contacting the publisher, finding a fuller statement, or Johnny
  accepting the residual ambiguity in writing) before this gate can be marked cleared. Only an *explicit*
  permission compatible with the project's posture clears this check; silence does not.
- Per plan §8 decision table: does this candidate's terms permit attribution-required, noncommercial use
  and enforce compatible downstream restrictions, with all provenance/privacy/weight questions cleared
  against the three classes above? If not yet answerable, mark `UNRESOLVED` rather than assuming
  compatibility.

### 9. Stop-condition checklist

Check any that apply. **Any checked box stops this candidate at this sheet** — do not proceed to A2 sample
selection for this candidate until Johnny resolves it.

- [ ] Rights depend on accepting terms Johnny has not approved
- [ ] Provenance is incomplete (an upstream source is unidentified or unverifiable)
- [ ] Training/derivative use is unclear after checking primary sources
- [ ] Required privacy controls (de-identification, consent, retention limits) are undocumented or
      unavailable
- [ ] The only evidence found is a repository/code license, with no separate statement about the data
      itself
- [ ] **Trained-weight distribution (permission-matrix row 7) is `Unclear`/silent and has not been actively
      resolved** — added 2026-08-13; per the corrected §8 check above, silence never clears this on its own
- [ ] **ShareAlike (or equivalent) scope is not confirmed against the license's own "Adapted Material"
      definition** — added 2026-08-13, so this can't be assumed compatible by reading only the license name
- [ ] **DialogSum-specific (if this candidate is DialogSum):** the plan's own DialogSum rights-stop (plan
      §3 A1: "Do not access samples until ShareAlike scope, upstream rights, speaker copyright, privacy, and
      model-training/weight-distribution implications are resolved") remains unresolved — added 2026-08-13
      as its own named checkbox rather than left implicit in the plan citation alone, since this is the one
      active candidate the plan itself singles out with an extra rights stop

### 10. Disposition

- [ ] **Cleared** — no unresolved material issue; may proceed to A2 for this candidate once separately
      authorized
- [ ] **Blocked** — one or more stop conditions checked; returns to Johnny
- [ ] **Rejected by policy** — e.g. paid/gated access conflicts with the project's freely-available-access
      criterion (compare the plan's own treatment of Switchboard-1, plan §2, as the precedent for this
      disposition)

---

## Worked illustrative example (fictitious placeholder — not a real dataset)

To confirm every field above is answerable in practice, here is one fully filled sheet for a fabricated
placeholder candidate. None of the facts below describe any real dataset; this section exists only to
pressure-test the template's mechanics.

**Candidate name / version-commit:** *"Example Corpus X" v0.9 (illustrative only)*
**Preparer / date prepared:** Claude, 2026-08-12
**Reviewer (independent) / date reviewed:** *(not yet reviewed — illustrative only)*

1. **Ownership/provenance:** Owner/controller: *Fictional University NLP Lab*. Upstream sources: one
   synthetic source, "elicited role-play transcripts." Citation: *fictitious, no real paper.*
2. **Access:** Direct download from a public archive. Registration: No. Term acceptance: No.
3. **Use restrictions:** License identifier: *CC BY-NC 4.0 (fictitious assignment for this example)*.
   Commercial-use restriction: "may not be used, in whole or in part, for commercial purposes" *(fabricated
   clause text)*.
4. **Permission matrix (fabricated answers):**

   | Permitted use | Y/N/Unclear | Citation |
   |---|---|---|
   | Training | Yes | fabricated §2 |
   | Modified/re-annotated training | Unclear | license silent |
   | Derivative dataset | Yes | fabricated §3 |
   | Internal sharing | Yes | fabricated §3 |
   | Publishing illustrative examples | Yes | fabricated §4 |
   | Redistribution | No | fabricated §5 (redistribution reserved to publisher) |
   | Trained-weight distribution | Unclear | license silent |

5. **Attribution:** "Cite Example Corpus X, Fictional University NLP Lab, 2026" *(fabricated)*. No
   share-alike clause.
6. **Consent/privacy:** Consent statement present (fabricated: "all speakers signed a release"). No
   sensitive-content flag.
7. **Jurisdiction:** None stated.
8. **Project-policy compatibility:** NC term directionally compatible; redistribution restriction (`No`
   above) is a real conflict with the project's downstream-sharing goal and would need resolution before
   this fictitious candidate could clear.
9. **Stop-condition checklist:** **updated 2026-08-13** — the trained-weight-distribution box is now
   checked, consistent with row 7's `Unclear` answer above and the corrected rule that silence never
   auto-clears (previously this section said "none checked," which was inconsistent with the sheet's own
   `Unclear` answer once that rule was fixed). ShareAlike-scope and DialogSum-specific boxes remain
   unchecked (not applicable to this fictitious, non-DialogSum candidate).
10. **Disposition:** Blocked — two independent reasons now, not one: the redistribution restriction
    (fabricated conflict, kept unresolved deliberately) and the newly-checked trained-weight-distribution
    stop. Shows the template correctly accumulates multiple real blocking issues rather than stopping at
    the first one found.

This illustrative pass used no real dataset content and required no access, account, or term acceptance —
consistent with the boundary stated above.
