# A1 — Dataset Rights/Governance Evidence Sheet: QMSum

**Uses the template at** `discovery_audit_package_a1_rights_evidence_template.md`. Real candidate, real
findings, public-source research only — no account created, no term accepted, no sample examined.

**Revised 2026-08-13, same day, per ChatGPT's independent verification** — one material legal
mischaracterization and one now-resolved provenance gap, both confirmed by Claude fetching the actual
primary sources before accepting the correction: (1) the Canadian-committee-content finding stated no
permission existed at all; the House of Commons' own notice actually grants a specific, narrow reproduction
permission alongside its copyright reservation — materially different from "no permission," though still
not enough to clear this project's transformation/training use, so the *disposition* doesn't change, only
its precision. (2) The 36-vs-33 committee-meeting-count discrepancy is resolved: the paper's own Table 1
(fetched via its ar5iv HTML rendering after the PDF proved unreadable) gives 137 AMI + 59 ICSI + 25 Welsh +
11 Canadian = 232. Also corrected: the AMI/ICSI disposition language overstated "clear cleanly on every
dimension" when the sheet's own stop-checklist already left trained-weight distribution unresolved for
them too — fixed to stop contradicting itself.

**Candidate name / version-commit:** QMSum (`github.com/Yale-LILY/QMSum`, HEAD as viewed 2026-08-13)
**Preparer / date prepared:** Claude, 2026-08-13
**Reviewer (independent) / date reviewed:** pending — sent to ChatGPT for independent verification

## 1. Ownership and provenance

- **Owner/controller:** Yale-LILY lab; Zhong, Ming, et al., *QMSum: A New Benchmark for Query-based
  Multi-domain Meeting Summarization*, NAACL 2021.
- **Every upstream source** — QMSum spans three domains, 232 meetings, 1,808 query-summary pairs:
  1. **AMI Meeting Corpus** — **137 meetings**, QMSum's "Product" domain. Confirmed directly against the
     paper's own Table 1 (§1 revision note above). Mix of scenario (elicited role-play) and naturally
     occurring meetings.
  2. **ICSI Meeting Corpus** — **59 meetings**, QMSum's "Academic" domain. Real weekly research-team
     meetings recorded at ICSI, Berkeley, 2000–2002. Confirmed against the same table.
  3. **Committee meetings — 36 total, confirmed split: 25 from the Welsh Parliament + 11 from the
     Parliament of Canada** (paper's Table 1, fetched directly). 137 + 59 + 36 = 232, matching the paper's
     stated total. The earlier 33-vs-36 discrepancy is resolved in favor of 36; "33" appears to have been
     an inaccurate secondary-source summary. Mapping the 25/11 to stable record IDs (which specific
     meetings are which) is the next-highest-value provenance task, not yet done this pass.
- **Original paper:** Zhong et al., *QMSum: A New Benchmark for Query-based Multi-domain Meeting
  Summarization*, NAACL-HLT 2021. https://aclanthology.org/2021.naacl-main.472/

## 2. Access method

- Direct download from GitHub (`github.com/Yale-LILY/QMSum`). No application or payment found.
- Registration required? **No.**
- Click-through/negotiated term acceptance required? **No** for the repository itself — but see §7: the
  underlying AMI/ICSI corpora each have their own separate license pages (not a click-through gate, but a
  distinct terms document each source publishes independently of QMSum's repo).
- Not stopped by the §2 rule for the repository access itself.

## 3. Use restrictions

- **QMSum repository:** states **MIT License** for the repository. Per this template's own governing rule,
  **a permissive code-repository license is not sufficient evidence for the embedded third-party meeting
  data** — MIT covers QMSum's own code/annotation-compilation layer, not necessarily the transcripts
  themselves, which each carry independent upstream terms (below).
- **AMI Meeting Corpus:** **CC BY 4.0** (fetched directly from `groups.inf.ed.ac.uk/ami/corpus/license.shtml`).
  No commercial-use restriction — the license text confirms "does not restrict commercial use." No
  distinction found in the license text between scenario/elicited and naturally-occurring meetings; both
  fall under the same terms.
- **ICSI Meeting Corpus:** **CC BY 4.0** (fetched directly from `groups.inf.ed.ac.uk/ami/icsi/license.shtml`,
  hosted on the same site as AMI's). Also no commercial-use restriction.
- **Committee meetings (Welsh Parliament + Parliament of Canada):** **mixed, and this is the real finding
  of this review.**
  - **Welsh Parliament content — flagging an internal inconsistency this pass found on its own re-check**:
    this bullet previously stated as settled fact that "Welsh Parliament data is released under the Open
    Government Licence," but that claim rests only on secondary search-result summaries — no Welsh
    Parliament licensing/copyright page was ever actually fetched and read directly in this review, unlike
    AMI's license page, ICSI's license page, and the Canadian House of Commons notice, all of which were.
    The rest of this sheet (the permission matrix, §8) already treats Welsh content as `Unclear`/"not
    independently confirmed to the same depth" — this bullet is corrected to match rather than stating a
    more confident claim than the evidence actually supports. Accurate statement: public search results
    are **consistent with** Welsh Parliament content being available under the Open Government Licence
    (attribution required, source + publication date), but this has not been verified against a primary
    Welsh Parliament source the way every other license claim in this sheet has been.
  - **Canadian Parliament content: copyright is reserved, but a specific reproduction permission also
    exists alongside that reservation — corrected 2026-08-13, fetched directly from the primary source**
    (House of Commons Committee Report No. 8,
    `ourcommons.ca/DocumentViewer/en/40-2/PROC/report-8/`). The notice states both:
    - **Reservation:** "The parliamentary privilege of the House of Commons to control the publication and
      broadcast of the proceedings of the House of Commons and its Committees is nonetheless reserved. All
      copyrights therein are also reserved."
    - **Permission, in the same notice:** "Reproduction of the proceedings of the House of Commons and its
      Committees, in whole or in part and in any medium, is hereby permitted provided that the reproduction
      is accurate and is not presented as official." With an explicit exclusion: "This permission does not
      extend to reproduction, distribution or use for commercial purpose of financial gain." Briefs
      submitted to committees may carry their own separate author copyright requiring further permission.

    **What this means for this project, precisely — not "no permission" and not "freely reusable" either:**
    the granted permission is scoped to *accurate reproduction*, not presented as official, noncommercial.
    It does not, on its own text, clearly extend to **modified/re-annotated derivatives, semantic
    transformation into this project's output contract, model training, or trained-weight distribution** —
    all of which go beyond "reproduction... accurate and not presented as official." This is genuinely
    different from both extremes: not "all rights reserved, zero permission" (the original, now-corrected
    characterization), and not CC BY 4.0-equivalent open reuse either. **Remains `Unclear`/blocked for this
    project's intended use specifically**, for a narrower and more precise reason than originally stated.

## 4. Permission matrix

Answered **per source**, since — unlike DialogSum, where one license claims to cover everything — QMSum's
three domains genuinely have three different rights regimes, and the committee domain itself splits again.

**Corrected 2026-08-13** per ChatGPT's second review: the template's field 4 requires **Yes / No / Unclear**
only — `Likely Yes` is not one of the sanctioned values, and using it let unconfirmed conclusions read as
more settled than the evidence supports (the template's own point: probability hedging is not a substitute
for actual rights clearance). Every Welsh cell below is now `Unclear` until OGL applicability is
independently confirmed to the same depth as AMI/ICSI, not just plausible. A new first row is added for
Canada specifically, because the one thing that *is* affirmatively `Yes` — accurate, unmodified,
non-official, noncommercial reproduction, exactly what the House of Commons permission actually grants —
was previously buried inside a hedged "illustrative examples" row and needs its own line so the genuine
clearance doesn't get lost in an otherwise-`Unclear` column.

| Permitted use | AMI / ICSI | Welsh committee | Canadian committee |
|---|---|---|---|
| Accurate, unmodified, non-official, noncommercial reproduction of the original proceedings text | N/A — already covered by the broader CC BY 4.0 grant below | **Unclear** — OGL applicability not independently confirmed to the same depth | **Yes**, within the express permission (§3, quoted directly from the primary source) — the one row this project's use plausibly satisfies as written |
| Model training on the raw data | **Yes** — CC BY 4.0 permits reproduction broadly, no field-of-use restriction found | **Unclear** | **Unclear** — the granted permission covers accurate, non-official, noncommercial *reproduction*; training is not reproduction in the sense the notice describes |
| Training on modified/re-annotated versions | **Yes** — CC BY 4.0 explicitly permits "Adapted Material," only requires attribution + change notice | **Unclear** | **Unclear** — the granted permission's text doesn't extend to modified/transformed derivatives, only accurate reproduction |
| Creating and retaining a derivative dataset | **Yes** | **Unclear** | **Unclear**, same reasoning |
| Internal project sharing | **Yes** | **Unclear** | **Unclear** — not tightly limited to the exact reproduction permission's own conditions, so not affirmatively covered |
| Publishing illustrative examples in project documentation | **Yes, with attribution** | **Unclear** | **Unclear** unless a specific excerpt is tightly limited to accurate, non-official, noncommercial reproduction (in which case it falls under the first row instead, not this general one) |
| Redistributing the data or a derivative of it | **Yes, with attribution + change notice** (CC BY 4.0 §3(a)) | **Unclear** | **Unclear for a derivative**; accurate unmodified reproduction is covered by the first row, a transformed derivative is not |
| Distributing trained model weights whose training set included this data | Unclear — CC BY 4.0 doesn't address weight-distribution explicitly, same generally-unsettled question as everywhere else in this project | **Unclear** | **Unclear**, and the reproduction-only permission makes this the least-supported row for the Canadian slice specifically |

## 5. Attribution / share-alike obligations

- **Required attribution (AMI/ICSI):** CC BY 4.0 §3(a), quoted directly from the license pages: must
  "retain the following if it is supplied by the Licensor with the Licensed Material: identification of the
  creator(s)... a copyright notice... a notice that refers to this Public License."
- **Share-alike/derivative-license obligations (AMI/ICSI):** **CC BY 4.0 has no ShareAlike clause** — unlike
  DialogSum's CC BY-NC-SA, AMI/ICSI's Adapted Material does **not** need to carry the same license forward.
  ICSI's license does add one constraint: "the Adapter's License You apply must not prevent recipients of
  the Adapted Material from complying with this Public License" — a floor, not a ShareAlike requirement.
  This means **AMI/ICSI content, once incorporated, does not itself force the project's CC BY-NC-SA 4.0
  downstream propagation** — the project's own noncommercial restriction would have to be applied by the
  project's choice, not because AMI/ICSI's license requires it. No conflict either way: a more restrictive
  downstream license is compatible with CC BY 4.0's permissive floor.
- **Welsh committee:** attribution stating source + publication date, per OGL.
- **Canadian committee — corrected 2026-08-13**: the prior version of this line said no attribution
  framework was found "because no general permission was found in the first place" — stale, and wrong
  after §3's correction: a general permission *was* found. The accurate statement: the House of Commons
  notice's quoted reproduction permission (§3) requires accuracy and non-official presentation but does not
  itself state a conventional attribution clause the way CC BY 4.0 or OGL do; briefs submitted to
  committees may separately require the original author's permission under the Copyright Act. Attribution
  is not the open question here — **scope** is (§3/§4): the permission covers reproduction, not the
  transformed/trained use this project would make of it, and satisfying an attribution convention (even if
  one existed) would not resolve that separate scope gap.

## 6. Consent, privacy, and retention

- **AMI:** confirmed via direct primary-source search — **"collected under informed consent."** A
  materially better starting position than DialogSum, where no consent statement was found for any source.
  **Extended 2026-08-13** — fetched AMI's own ethics/consent page
  (`groups.inf.ed.ac.uk/ami/corpus/ethicsandconsent.shtml`) directly: it links a real, named "blank copy of
  the consent form signed by the participants" and a separate ethics document from the original data-
  collection contract, confirming genuine formal consent process documentation exists (not just an
  assertion). The consent form's specific clauses (participant review/removal rights, contact-information
  handling, any censoring process) are in that linked PDF, which this pass could not successfully fetch —
  **their exact content is reported by ChatGPT's independent review, not independently re-verified by
  Claude against the primary document itself**; flagging that distinction rather than presenting it as
  equally confirmed.
- **ICSI:** confirmed via the original ICSI Meeting Corpus paper description — the corpus involved a
  **Consent Form** requesting participants' permission for inclusion, and participants were "fully
  cognizant of the recording." ChatGPT's independent review additionally reports the approval forms
  satisfied University of California human-subjects requirements and that participants could request
  review/deletion of their data — consistent with, but not independently re-fetched by Claude from, the
  Janin et al. paper this pass.
- **Welsh/Canadian committee meetings:** these are **public government proceedings**, not private research
  subjects — the privacy/consent framing that applies to AMI/ICSI (human-subjects research) doesn't
  transfer cleanly. The relevant question for these two is copyright/reuse permission (§3 above), not
  consent, since committee members are recorded performing public official duties, not participating in a
  research study.
- **De-identification:** not found explicitly stated for AMI/ICSI; likely not applicable/expected for
  named professional participants in an institutional research-meeting corpus, and not applicable at all
  to public parliamentary committee members. Not confirmed either way this pass.
- **Retention limits:** none found for any of the three domains.

## 7. Jurisdiction and institutional restrictions

- **AMI/ICSI:** hosted by the University of Edinburgh (`groups.inf.ed.ac.uk`); no jurisdiction-specific
  restriction found in the license text itself.
- **Committee meetings:** governed by UK/Welsh and Canadian parliamentary copyright regimes respectively —
  genuinely different jurisdictions and legal frameworks from the CC-licensed academic corpora, and from
  each other.
- **Other unresolved ambiguity:** the aggregate Welsh-vs-Canadian split is now resolved (25/11, §1), but
  **which specific meeting IDs in QMSum's committee domain are Welsh vs. Canadian is not yet mapped** —
  needed before a real A2 draw could correctly exclude just the Canadian-sourced slice, per the option
  raised in §10.

## 8. Project-policy compatibility

- **AMI/ICSI (Academic + part of Product domain):** CC BY 4.0's permissive terms are compatible with the
  project's settled noncommercial-downstream posture — the project can apply its own CC BY-NC-SA 4.0 to any
  re-annotated derivative without conflicting with AMI/ICSI's floor requirement. **This is a genuinely
  favorable, resolved finding for these two sources specifically.**
- **Welsh committee content:** likely similarly compatible under OGL, not independently confirmed to the
  same depth as AMI/ICSI this pass.
- **Canadian committee content:** **not compatible as currently understood, for a precise reason —
  corrected 2026-08-13.** The House of Commons grants a specific reproduction permission (accurate,
  non-official, noncommercial — §3), so this is not "no permission at all." But that permission's own text
  doesn't extend to the modified/transformed, trained-on, redistributed-as-derivative use this project
  would actually make of it. The block is real; the reason is narrower and more precise than originally
  stated. This remains the single most concrete blocking finding across both candidates reviewed this
  session.
- **Trained-weight distribution:** unresolved for all three domains, same as every other candidate — per
  the corrected rule, this stays open regardless.
- **Plan §8 decision table: not yet answerable as a whole-candidate compatibility verdict** — QMSum is not
  one rights profile, it's (at least) three, and the worst of the three (Canadian committee content) blocks
  a blanket "QMSum is cleared" conclusion even though two of the three sources (AMI, ICSI) are genuinely
  favorable and well-documented.

## 9. Stop-condition checklist

- [x] **Provenance is incomplete** — aggregate Welsh/Canadian split now resolved (25/11, §1), but mapping
      to specific meeting IDs within the committee domain is not yet done (§7).
- [x] **Training/derivative use is unclear** — specifically and precisely for the Canadian committee
      content (a narrow reproduction-only permission exists but doesn't cover this project's actual use,
      §3); AMI, ICSI, and (provisionally) Welsh content are clear on this point.
- [ ] **Required privacy controls undocumented** — **not checked for AMI/ICSI's core consent question**
      (informed consent is confirmed for both); but per the corrected §6, the *specific* controls
      (review/removal rights, contact-info handling, censoring) are only independently confirmed to the
      level of "documentation exists," not fully re-verified by Claude against primary text this pass —
      recorded honestly in §6 rather than either checking this box defensively or overclaiming completeness.
- [ ] Repository-license-only evidence — **not checked**; this review went beyond the MIT repo license and
      independently verified each underlying source's own terms, which is exactly what this box exists to
      require.
- [x] **Trained-weight distribution is `Unclear`/silent and unresolved**, same as every candidate —
      including AMI/ICSI, not just the Canadian slice; corrected 2026-08-13 to stop implying otherwise.
- [ ] ShareAlike scope — **not applicable/not checked**; AMI/ICSI's CC BY 4.0 has no ShareAlike clause to
      scope (§5).

## 10. Disposition

- [x] **Blocked — but unevenly, and that unevenness is itself the useful finding.** **Corrected 2026-08-13**:
      AMI and ICSI have a permissive license and confirmed informed consent, and are compatible with
      project policy — genuinely favorable — but do **not** "clear cleanly on every dimension": trained-
      weight distribution is unresolved for them too (§9), same as everywhere else in this project. The
      Canadian-sourced committee content is blocked for a precise reason (§3/§8: a narrow reproduction
      permission exists but doesn't cover this project's transformation/training use — not "no permission
      at all," as originally overstated). Welsh committee content is provisionally favorable but
      under-checked relative to AMI/ICSI.
- **This suggests a possible path QMSum's own all-or-nothing framing doesn't capture**: if the committee
  domain's Canadian-sourced meetings can be identified and excluded, the AMI+ICSI(+Welsh) portion may clear
  independently. That is a real design option for Johnny to weigh, not a decision this sheet makes — A1's
  job is to surface it, not resolve it.

## What would resolve this

1. **Meeting-ID-level mapping of the committee domain** — the aggregate Welsh/Canadian split (25/11) is now
   resolved (§1), but which specific meeting IDs belong to which is not yet mapped; the QMSum repository's
   own data files likely have this directly. Now the highest-value next step, narrower than before.
2. **Direct confirmation of Welsh OGL applicability** to the specific transcripts QMSum used, not just
   Welsh Parliament's general publishing policy.
3. **Canadian parliamentary copyright**: whether a specific permission or exception applies to QMSum's
   particular reuse (research/derivative-dataset use sometimes qualifies for exceptions reserved-copyright
   regimes still carve out) — this would need targeted legal-text research this pass didn't reach, or
   Johnny accepting the block as-is and excluding that slice.
