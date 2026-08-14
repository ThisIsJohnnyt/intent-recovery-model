# Session handoff — 2026-08-12 (RBR17-C postmortem closed; next milestone awaiting authorization)

**Repository:** `intent-recovery-model`  
**Branch / current commit:** `main` at `4f568e0cdb9164d6f2881dcf8cfb8b7d15efa960`, pushed to and verified against `origin/main` by Claude  
**Postmortem commit:** `f926505`  
**Session boundary:** RBR17-C outcome and diagnostic postmortem are closed. The proposed no-compute mechanism/representation audit is a new milestone and is not yet authorized.

## 1. What closed in this session

### RBR17-C diagnostic postmortem

Johnny authorized ChatGPT to draft a diagnostic-only postmortem of the settled `RBR17-C` fail/fail outcome. ChatGPT created:

- `training/controlled_seed17_regression_balanced_repair_postmortem_chatgpt.md`
- reviewed SHA-256: `5dc0bcfe273bbffbb4461b9ad341ce33a35df73f8a478d17f82592e5463195e4`
- committed by Claude, on Johnny's commit-only authorization, as `f926505`

The postmortem was reconstructed from the accepted paired result artifacts, not from aggregate totals alone. Claude independently recomputed the paired sets from the outcome record, reran `report_benchmark.py` against all four result files, inspected the load-bearing raw outputs and capability checks, verified the intended record-to-mechanism mappings, and reported full agreement with no discrepancy.

### Settled diagnostic findings

- Protected treatment-only strict gain: `{02}`.
- Protected treatment-only strict regression: `{09}`.
- Shared protected strict failures: `{06,08,10,11,16}`.
- Acceptance treatment-only semantic/combined regression: `{sdi2-02}`.
- Acceptance treatment-only semantic gains: none.
- Shared acceptance semantic failures: `{sdi2-07,sdi2-10}`.
- Shared acceptance count failures: `{sdi2-07,sdi2-08,sdi2-10}`.
- Comparator acceptance combined strict pass: 7/10; treatment: 6/10.
- Both arms remain 10/16 on protected strict semantics, but with different pass sets.

The 85-record treatment is therefore not a safe successor to the 78-record comparator. It exchanged one protected gain for one protected regression, added one acceptance regression, and left every structural count failure unchanged.

The postmortem also corrected a potential lineage confusion: the `{02,06}` / `{10,16}` / `{sdi2-02,sdi2-09}` exchange described in the earlier RBR design document belongs to the prior contrastive experiment that motivated RBR. It is not the later RBR17-C paired outcome.

### Intervention-transfer findings

- `RB-B1` explicitly targeted deadline-plus-destination retention and named `sdi2-02`-type protection, but the treatment alone dropped the shared-drive destination on `sdi2-02`.
- `RB-C3` targeted dangling-reference preservation, but protected 16 remained an identical failing output in both arms.
- The four AT-C attribution controls did not repair protected 06.
- These results do not establish that any individual record caused a regression or is useless. The seven-record delta was bundled in one arm at one seed, so record-level causal attribution is unavailable.
- Because structural mechanisms already had audited baseline exemplars and all three count failures were shared, automatically adding more D-group examples is unsupported.

## 2. Recommended next milestone — not yet authorized

The postmortem recommends a **bounded, no-compute RBR17-C mechanism audit and representation/capacity comparison design**.

If Johnny separately authorizes it, the milestone should produce:

1. an atomic failure ledger for the ten distinct cases failing in at least one arm: `06,08,09,10,11,16,sdi2-02,sdi2-07,sdi2-08,sdi2-10`;
2. a record-to-mechanism coverage map for the 78-record baseline and seven-record treatment delta, including effective target-token and field-form evidence rather than category labels alone;
3. a conflict map for fact/question/fragment/task state, role binding, qualifier binding, deduplication, bullet budgeting, and action cardinality;
4. a design-only comparison of corpus/contrast changes, representation or training-objective changes, and constrained decoding or deterministic structural post-validation;
5. explicit decision criteria for a later ablation, representation change, model-capacity comparison, or stop; and
6. leakage controls, especially for protected 06's known close training analogue.

The 78-record comparator remains the reference lineage. The failed 85-record treatment must not silently become the new baseline. Its seven records may be analyzed individually but are not automatically carried forward.

## 3. Separate open strategy track

The training-data/model discovery plan remains a separate, uncommitted design artifact:

- `training/intent_recovery_data_model_discovery_plan_chatgpt.md`

It covers external-dataset discovery, licensing/access gates, sampling and mechanism mapping, model-capacity comparison design, evaluation criteria, privacy/contamination controls, and explicit prohibitions on dataset download or model execution without later authorization.

Johnny chose the project-wide policy direction of permanent noncommercial use, attribution, and downstream sharing. The later licensing work is now recorded through PDR-006/PDR-007/PDR-008 and subsequent corrections: dataset/docs use CC BY-NC-SA 4.0 subject to the historical CC-BY-4.0 dataset snapshot; software uses PolyForm Noncommercial 1.0.0; model weights carry a non-assertive acknowledgment and noncommercial-use request plus Apache 2.0 compliance materials.

The discovery plan and the RBR17-C mechanism audit are related strategically but remain distinct milestones. Starting one does not authorize the other.

## 4. Repository and cleanup state

After the postmortem commit, Johnny authorized Claude to clean long-standing untracked material. Claude:

- removed local checkpoint directories and raw log files from the old Phase-2 replay run, freeing about 13 GB while preserving the committed results JSON, receipt, frozen evidence, and outcome record;
- committed previously untracked Phase-2 attribution design/review documents, the P2-D postmortem memo, and the training-data-strategy new-chat handoff without content changes; and
- pushed cleanup commit `4f568e0`.

Claude reported that no scientific, decision, dataset, execution, or licensing content was changed by the cleanup.

At this handoff, the working tree has two known untracked files:

- `training/intent_recovery_data_model_discovery_plan_chatgpt.md`
- `training/session_handoff_2026-08-11_rbr17_outcome_close.md`

This new handoff file is also untracked unless and until separately authorized for commit. Do not sweep any of these files into a commit without Johnny's explicit scope.

## 5. Standing boundaries

No current authorization exists for:

- the proposed RBR17-C mechanism/representation audit;
- dataset acquisition, download, sampling, or inspection beyond already authorized work;
- corpus mutation or new record authoring;
- benchmark, rubric, scoring, or accepted-outcome changes;
- training, inference, retries, seed 73, or any other compute;
- checkpoint selection, substitution, promotion, export, or deployment; or
- committing or pushing this handoff or the discovery plan.

`RBR17-C` remains closed. The postmortem is diagnostic evidence, not an execution authorization.

## 6. Suggested opening for the new session

Begin by confirming which new milestone Johnny wants to authorize:

1. the bounded no-compute RBR17-C mechanism/representation audit recommended by the committed postmortem; or
2. continued review/decision work on the separate training-data/model discovery plan.

Do not merge the two scopes by assumption. If Johnny selects the mechanism audit, restate its design-only/no-compute boundary before beginning.

**Disposition:** RBR17-C OUTCOME AND POSTMORTEM CLOSED — POSTMORTEM COMMITTED AT `f926505` — REPOSITORY CLEANUP AT `4f568e0` — NEXT MILESTONE REQUIRES A NEW, EXPLICIT AUTHORIZATION — NO COMPUTE OR CORPUS ACTION AUTHORIZED.
