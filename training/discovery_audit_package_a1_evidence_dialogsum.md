# A1 — Dataset Rights/Governance Evidence Sheet: DialogSum

**Uses the template at** `discovery_audit_package_a1_rights_evidence_template.md`. **Real candidate, real
findings** — this is the first sheet filled in against an actual candidate, per Johnny's 2026-08-13
authorization to begin A1 rights research. Public-source research only: no account created, no term
accepted, no sample examined — only license text, README, and paper content, consistent with the
template's stated boundary.

**Candidate name / version-commit:** DialogSum (`github.com/cylnlp/dialogsum`, HEAD as viewed 2026-08-13;
also mirrored at `huggingface.co/datasets/knkarthick/dialogsum`)
**Preparer / date prepared:** Claude, 2026-08-13
**Reviewer (independent) / date reviewed:** ChatGPT, 2026-08-13 — found the permission matrix overstated
confidence relative to §7's own upstream-uncertainty findings, and that §5's Adapted-Material conclusion
was stated too categorically. Both corrected below; the block disposition itself does not change, only its
precision (confirmed: MuTual's license genuinely could not be independently verified either, and the
2019/2020 MuTual-year note was confirmed correct as "plausibly the preprint year").

## 1. Ownership and provenance

- **Owner/controller:** the DialogSum project authors — Yulong Chen, Yang Liu, Liang Chen, Yue Zhang,
  "DialogSum: A Real-Life Scenario Dialogue Summarization Dataset," *Findings of ACL-IJCNLP 2021*.
- **Every upstream source** (DialogSum's own README: "Our dialogues are collected from the following
  three public dialogue corpora... and an English speaking practice website"):
  1. **DailyDialog** (Li et al., *IJCNLP 2017*) — per public description, crawled from English-learning
     websites to simulate everyday two-speaker conversation.
  2. **DREAM** (Sun et al., *TACL 2019*) — English-as-a-foreign-language exam dialogues, collected from
     websites the repo itself lists in a `websites.txt` file (`github.com/nlpdata/dream`).
  3. **MuTual** (Cui et al.; ACL Anthology lists this as *ACL 2020*, `2020.acl-main.130` — the discovery
     plan's own shortlist table cited "Cui et al., 2019," which appears to be the arXiv preprint year, not
     the venue year; noting the discrepancy rather than silently picking one) — "modified from Chinese high
     school English listening comprehension test data" (`github.com/Nealcly/MuTual` README, quoted).
  4. **An English-speaking-practice website** — DialogSum's own README names this as a fourth source but
     does not identify the website by name in anything found; **unresolved**, not guessed.
- **Original paper:** Chen, Liu, Chen, Zhang, *DialogSum: A Real-Life Scenario Dialogue Summarization
  Dataset*, Findings of ACL-IJCNLP 2021. https://aclanthology.org/2021.findings-acl.449/

## 2. Access method

- Direct download from GitHub or Hugging Face. No application, gating, or payment found.
- Registration required? **No** — public repositories, no login wall encountered.
- Click-through or negotiated term acceptance required? **No** — plain file download.
- Since both are No, this candidate is **not stopped** by the §2 rule — accessing the repository/README
  itself (as opposed to the actual dialogue *samples*, which remain untouched here) required no term
  acceptance.

## 3. Use restrictions

- **Commercial-use restriction:** DialogSum's own README states the license as **CC BY-NC-SA 4.0** — the
  "NC" element prohibits commercial use. Citation: `github.com/cylnlp/dialogsum` README, and
  https://creativecommons.org/licenses/by-nc-sa/4.0/.
- **Research-only restriction:** DialogSum itself states none beyond NC/SA. However, upstream source
  **DREAM**'s actual `license.txt` (fetched directly, quoted verbatim) states: **"DREAM dataset is intended
  for non-commercial research purpose only."** This is narrower and less formal than DialogSum's own CC
  BY-NC-SA 4.0 claim over the same underlying dialogue content — DREAM's text doesn't use CC's defined
  terms and doesn't explicitly address redistribution, adaptation, or third-party incorporation into
  another compiled dataset at all.
- **License identifier:** CC BY-NC-SA 4.0, per DialogSum's own README — but **this describes DialogSum's
  own compilation/annotation layer, not an independently verified grant over each upstream source's
  underlying text.** Per this template's own governing rule ("a permissive repository license is not
  sufficient evidence for embedded third-party data"), DialogSum's CC BY-NC-SA claim is not itself proof
  that DREAM's or MuTual's content may be relicensed this way — see §7 for the resulting gap.

## 4. Permission matrix

**Corrected 2026-08-13** per ChatGPT's review: the first version answered several rows `Yes`/`Likely Yes`
by reading only DialogSum's own umbrella CC BY-NC-SA 4.0 claim, while §7 separately (and correctly) found
that claim's authority over the MuTual and practice-website content specifically is unverified. **An
umbrella grant cannot clear rights the grantor may not hold.** Every row now shows both DialogSum's own
claimed grant *and* the net answer once upstream provenance gaps are factored in — the candidate-level
answer that actually governs is the net column, not the claim column alone.

| Permitted use | DialogSum's own claimed grant | Net, given upstream gaps (§7) | Citation |
|---|---|---|---|
| Model training on the raw data | Unclear even on its own terms | **Unclear** | CC BY-NC-SA 4.0's reproduction/adaptation grant plausibly covers training in general, but no source here states this explicitly; DREAM's narrower "research purpose only" text adds independent doubt for its ~6,444 dialogues specifically |
| Training on modified/re-annotated versions | **Corrected 2026-08-13** (this cell repeated the exact categorical phrasing §5 was fixed to remove): *if* the modification legally constitutes "Adapted Material" under CC BY-NC-SA §1, permitted in form — not a settled classification | **Unclear** | Permitted *if* DialogSum's grantors hold the rights they purport to license — unverified for MuTual and the practice website (§7) — and *if* the modification actually crosses the Adapted-Material threshold in the first place (§5) |
| Creating and retaining a derivative dataset | Yes, ShareAlike-bound, in form | **Unclear as a whole-candidate answer** | Same authority gap — a derivative built from all four sources inherits MuTual's and the practice website's unverified status; a derivative built only from the DailyDialog/DREAM-sourced portion would rest on firmer (though still not fully resolved) ground, but this sheet does not attempt that record-level split |
| Internal project sharing (e.g. with a reviewer) | Yes, in form | **Unclear**, same reasoning — not assumed low-risk-therefore-clear without basis | CC BY-NC-SA's own sharing permission inherits the same authority question |
| Publishing illustrative examples in project documentation | Yes with attribution, in form | **Unclear** for examples that could be MuTual- or website-sourced; firmer for identifiably DailyDialog/DREAM-sourced examples specifically | Same reasoning; record-level sourcing isn't determined here |
| Redistributing the data or a derivative of it | Yes, in form | **Unclear**, not resolved-except-MuTual as the first version implied | MuTual's own redistribution terms could not be found at all (no LICENSE file, no README license section at `github.com/Nealcly/MuTual`), and the practice-website source's terms are entirely unknown |
| Distributing trained model weights whose training set included this data | Not addressed | **Unclear** | No source here addresses trained-weight distribution explicitly — the same generally-unsettled question this project's own `MODEL_RELEASE_NOTICE.md` posture already anticipates |

## 5. Attribution / share-alike obligations

- **Required attribution:** DialogSum's README provides a specific BibTeX citation (Chen et al. 2021) that
  must be used.
- **Share-alike clause, verbatim** (CC BY-NC-SA 4.0 §3(b), fetched directly from
  `creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en`): *"The Adapter's License You apply must be a
  Creative Commons license with the same License Elements, this version or later, or a BY-NC-SA Compatible
  License."*
- **Scope, per the license's own definition of "Adapted Material"** (§1, quoted directly): *"Material
  subject to Copyright and Similar Rights that is derived from or based upon the Licensed Material and in
  which the Licensed Material is translated, altered, arranged, transformed, or otherwise modified in a
  manner requiring permission under the Copyright and Similar Rights held by the Licensor."* **Corrected
  2026-08-13, per ChatGPT's review**: the first version stated categorically that a project re-annotation
  "would qualify" as Adapted Material. That overstates it — the definition applies only where the
  alteration *requires permission under applicable Copyright and Similar Rights*, and whether a given
  annotation/metadata operation actually crosses that threshold can be jurisdiction- and fact-dependent, not
  a settled classification this sheet can make in the abstract. The accurate framing: **if** a project
  re-annotation of DialogSum inputs is legally an adaptation requiring permission, **then** its scope is
  compatible in form with the project's own settled dataset license (CC BY-NC-SA 4.0 per PDR-006) — a
  conditional finding, confirmed against the actual legal text rather than assumed from the license names
  matching, but conditional nonetheless, not a closed question.

## 6. Consent, privacy, and retention

- **Consent statement for original data subjects/speakers:** **none found**, despite specific searching,
  for any of the four upstream sources. DialogSum's own README states only that "the copyright of dialogue
  data in DialogSum dataset belongs to users who created them" — this is an **ownership** disclaimer, not a
  statement that those users consented to inclusion in a public research dataset.
- **Withdrawal/right-to-erasure mechanism:** none found.
- **De-identification method:** none found disclosed for any of the four sources.
- **Sensitive-content statement:** informal only — a DialogSum repository discussion/contributor comment
  notes "some source dialogues can contain unsatisfying contents." Not a governance-level disclosure with
  defined scope or handling procedure.
- **Retention limits:** none found.

## 7. Jurisdiction and institutional restrictions

- **Governing jurisdiction:** none stated by DialogSum or any upstream source.
- **IRB/ethics-board restriction:** none found.
- **Other unresolved ambiguity:**
  - **MuTual's license status is entirely unresolved** — no LICENSE file and no README license section
    found at its repository. DialogSum incorporates MuTual dialogues under its own CC BY-NC-SA 4.0 claim
    without MuTual's own terms being independently verifiable as consistent with that.
  - **DREAM's license is a narrow, informal restriction**, not a standard grant — it doesn't address
    redistribution, derivative works, or incorporation into a compiled dataset, all of which DialogSum's
    umbrella CC BY-NC-SA 4.0 claims to cover for the same underlying content.
  - **The practice-website source is unidentified**, so its own terms cannot be checked at all.

## 8. Project-policy compatibility

Per PDR-006/PDR-008's three settled classes:

- **ShareAlike compatibility (dataset+docs class):** DialogSum's CC BY-NC-SA 4.0 is the *same license* the
  project already uses for `datasets/gold/` (PDR-006) — if ShareAlike is actually triggered (§5's now-
  conditional finding), the license it would require matches what the project already uses; this specific
  same-license comparison is not itself conditional, only whether re-annotation counts as Adapted Material
  in the first place is.
- **Attribution:** Johnny's attribution could be added to project documentation alongside DialogSum's
  required citation without contradiction — no conflict found.
- **Trained-weight distribution:** row 7 of §4 is `Unclear` — per the corrected rule (silence is not
  clearance), this **stays open**.
- **Plan §8 decision table:** **not yet answerable as compatible.** Real provenance and privacy questions
  remain open (MuTual's license, no consent/de-identification statement for any of the four sources) — mark
  `UNRESOLVED`, not cleared.

## 9. Stop-condition checklist

- [x] **Provenance is incomplete** — MuTual's license/rights status could not be verified from any public
      source found; the practice-website source is unidentified.
- [x] **Required privacy controls are undocumented** — no consent, de-identification, or retention
      statement found for any of the four upstream sources.
- [x] **Trained-weight distribution is `Unclear`/silent and unresolved.**
- [ ] ShareAlike scope — **not checked, but corrected 2026-08-13 to stop overclaiming**: the earlier
      rationale here said this sub-question was "actually resolved," which no longer matches §5's now-
      conditional finding. What's actually settled: *if* Adapted Material status is triggered, *which*
      license would then apply (§5's legal-text comparison). What's *not* settled: *whether* a given
      re-annotation operation actually triggers that status in the first place — that's fact/jurisdiction-
      dependent, not resolved. Left unchecked because there's no live conflict to flag, not because the
      question is closed.
- [x] **DialogSum-specific stop** (plan §3 A1's named stop: "ShareAlike scope, upstream rights, speaker
      copyright, privacy, and model-training/weight-distribution implications") — **partially clarified, not
      fully resolved**: ShareAlike's license-comparison question has a conditional answer (§5); upstream
      rights (MuTual), speaker copyright (DialogSum disclaims owning the dialogue copyright itself, without
      evidence of a valid sublicense from "the users who created" it), privacy, and weight-distribution
      implications remain open. The box stays checked because the plan requires *all* of these resolved, not
      some, and none of them is fully resolved — ShareAlike included, once stated accurately.

## 10. Disposition

- [x] **Blocked** — concrete, specific open issues (MuTual provenance, undocumented consent/privacy across
      all four sources, the unresolved speaker-copyright/sublicense question, unresolved trained-weight
      posture), not generic caution. Returns to Johnny.
- Not "Rejected by policy": access itself is free and ungated (unlike Switchboard-1's paid/membership
  model), so no policy-level rejection applies here — this is a "more evidence needed, or Johnny accepts
  specific residual risk in writing" situation, a different kind of stop than an access-model rejection.

## What would resolve this

In descending order of how likely public research alone could resolve them:
1. **MuTual's license** — might be resolvable by checking the ACL 2020 paper itself for a stated license,
   or a data-statement/ethics section, not yet done here (time-bounded this pass; worth a follow-up).
2. **The practice-website's identity** — might be findable in the paper's appendix or supplementary
   material, not yet checked.
3. **Speaker consent/de-identification** — likely genuinely undocumented by the original publishers rather
   than merely hard to find; may require Johnny accepting this as a known, disclosed gap rather than
   something further searching resolves.
4. **Trained-weight distribution** — not something any of these datasets' terms will likely ever address
   explicitly; this is really a question of the project's own posture (already settled: non-assertive,
   request-only) being judged sufficient by Johnny for candidate data specifically, not just for
   project-authored data.
