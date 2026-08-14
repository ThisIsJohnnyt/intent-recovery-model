# Session handoff — 2026-08-14 (three threads converged, all awaiting Johnny's authorization)

**Repo state at close:**
- `intent-recovery-model`: `main` at `a20bd9056363ec1aae2a940b999080d7a3de3ec7`, matches `origin/main` exactly (verified via fresh `git fetch` immediately before this handoff was written). Untracked: exactly 3 long-standing, deliberately-excluded files — `training/intent_recovery_data_model_discovery_plan_chatgpt.md`, `training/session_handoff_2026-08-11_rbr17_outcome_close.md`, `training/session_handoff_2026-08-12_rbr17_postmortem_close.md`. This handoff file itself is a fourth, also untracked, also not to be swept into a commit without Johnny's explicit scope.
- `thought-organizer-app` (`C:\Users\thisi\OneDrive\Desktop\thought-organizer-app`): `main` at `7710a00975128c2c538584751fe21528a0a6e381`, matches `origin/main` exactly, working tree completely clean.

Nothing is uncommitted that needs action. Nothing in this session created or modified any file in either repo except the RBR17-C thread's `a20bd90` commit (below) and this handoff.

## What this session did

Three largely independent threads ran this session, all converged to a decision point and all now waiting on Johnny.

### 1. RBR17-C / typed-representation thread — CLOSED for this round, committed

Under the already-approved typed-proposition representation comparison proposal, ran a full sequence of no-compute/tokenizer-only milestones, each independently re-verified end to end (hash recomputation, from-scratch re-derivation with independently-written scripts, primary-source cross-checks) before being reported or staged:

1. **Milestone 1** (verbose typed-plan, full markers): hard stop, self-triggered — 23/72 train targets exceed the 512-token limit, 54/72 exceed the 300-token generation budget.
2. **Compact 10-record pilot** (stress subset 007/040/042/048/053/054/056/069/074/075): FAIL — fits 512 but 4/10 records exceed the 300-token generation budget; comparator:074/:075's *unchanged v2 answers alone* are already 267/246 tokens.
3. **Non-emitted structural-supervision architecture study**: design-only proposal (training-only encoder heads, plan never emitted). Revised twice after Claude's review (attribution-limitation disclosure, per-head loss-normalization rule, exact parameter formula independently re-derived and confirmed — 1,205,788 + 768m at w=768). Zero outstanding objections.
4. **First aux-span dual-annotation pilot round** (same 10-record subset): ChatGPT and Claude each produced a fully independent annotation pass (Claude's sealed/hashed *before* opening ChatGPT's file, reusing the project's proven blind-review method). Real, honestly-reported disagreement: 7/10 records matched exactly (including the rare duplicate-relation stress case), 3/10 disagreed on proposition count. Per the guide's own exact-agreement requirement, this does **not** cleanly pass — flagged as a material disagreement, not adjudicated away. Both sealed passes and a full disagreement record (4 identified root causes in the annotation guide) are preserved as historical evidence.

All of the above — milestone 1's artifacts, the compact pilot (with ChatGPT's applied correction to comparator:007's mislabeled state), the architecture study, both sealed annotation passes, and the disagreement record — **committed and pushed as `a20bd90`** (29 files), verified three ways including raw GitHub content spot-checks. Authorized by Johnny's hand-typed "Git it done."

**Status: milestone closed.** Nothing further authorized. The disagreement record's own recommendation (fix the annotation guide's 4 root causes, then rerun the pilot) is **not yet authorized** — see next actions below.

### 2. Third-AI candidate-generator proposal (Gemini) — converged, not started

Johnny asked whether to add one external AI as a synthetic candidate generator (not a reviewer/adjudicator) rather than trying to integrate more external datasets directly. Full discussion with ChatGPT, then independent review by Claude (verified Google's and Anthropic's actual current pricing/terms pages directly rather than trusting either secondhand).

**Converged**: Gemini paid API (not the consumer Gemini Plus subscription) is the generator, workflow is `Gemini generates → ChatGPT first review → Claude sealed independent review → comparison → Johnny adjudicates disagreements/authorizes batches`. **Claude recommended against using Claude Opus 5 for this role** despite it being technically very capable — it shares lineage with Claude Sonnet 5 (the existing reviewer), which defeats the stated point of adding a *genuinely* independent source, and verified pricing puts it at roughly 11x Gemini Flash's per-generation cost at real scale (trivial difference at pilot scale, real difference if this scales).

ChatGPT then proposed, and Claude agreed to, a fully-scoped **generator-readiness package** (design/schema documents only, zero API calls, zero generation, zero spend) covering: the annotation-guide revision, a strict candidate JSON schema, a mechanical leakage/overlap protocol (including, per Claude's addition, an *input-side* preflight check on the literal generator prompt template — not just output-side), a rejected-candidate ledger, the sealed-review protocol (reusing the method proven in RBR17-C's aux-span pilot), numeric pilot gates, a bounded Gemini 2.5-vs-3.x comparison, and explicit boundaries/ceilings for a later separately-authorized paid pilot.

**Status: scope and ownership fully converged (ChatGPT drafts, Claude independently reviews). Nothing started.** See `[[third_ai_generator_proposal_status]]` memory for full detail.

### 3. Previous-work closure audit (cross-repo) — converged, not started

Johnny asked to close loose ends before starting the generator-readiness work. ChatGPT drafted a read-only audit; Claude independently re-verified every claim against primary sources in **both** repos (not just the training-side docs), and the two went two full rounds until fully converged.

**Confirmed findings** (all independently verified, not taken on report):
- The training-side `source-determined-bullets-v1` prompt-contract handoff's "activation still pending" framing is genuinely stale (superseded same-day by a later postmortem recommending retirement).
- The live `thought-organizer-app` production code actually has **three** distinct, mostly-unversioned prompt shapes in play: the never-activated v1 canonical text, an undocumented single-pass variant (`noteOrganizer.ts`, unchanged since 2026-08-01), and a completely separate, unversioned multi-chunk merge prompt (`maxInputTokens = 6000` — any longer note goes through this path) with no bullet ceiling and no invention/duplication guard at all. A real, live release-safety gap, not just stale paperwork.
- A `promptContractV2Candidate.ts`/"vNext" typed-marker contract already exists in the app repo as an explicitly inactive feasibility candidate — relevant context any future closure notice needs to reflect accurately.
- Checkpoint-600 (`gold_v1.2.2`, epoch 40, evaluated candidate, never released) is a confirmed, accepted historical loss — no new recovery evidence found after a broad search.
- `training/run_benchmark.py` and `training/export_onnx.py` still default to `checkpoints/thoughtorganizer-flan-t5/final`, independently re-hashed and confirmed to still be the rejected `gold_v1.2.3` seed-42/checkpoint-680 run — a live footgun for anyone running either script without an explicit path.
- Two committed docs (`controlled_seed17_rbr17c_static_mechanism_audit_chatgpt.md`, `controlled_seed17_aux_span_annotation_pilot_status.md`) still literally say "Claude verification required" / "pending" despite both being resolved — agreed fix is a supersession index, not rewriting the historical record.
- The untracked discovery-plan document's Track B (model-capacity comparison, `flan-t5-base` vs. `Qwen3-4B`/`14B`) is **valid but deliberately deferred**, not superseded — directly relevant to whether a generator (more data) is even the right lever vs. base-model capacity, and hasn't been weighed against the Gemini proposal yet. Track A (external-dataset rights audit) is superseded in operational status by the already-committed A1 rights sheets (DialogSum/QMSum both blocked).

**Converged three-way milestone split**:
1. Documentation-only closure package (cross-repo inventory, supersession index, checkpoint-600 determination, disposition for the 3 untracked files, Track A/B disposition, register of unresolved safety work, a rule to start future work from current `main` not the stale detached Codex worktree at `4f568e0`). ChatGPT drafts, Claude independently reviews against both repos.
2. Separate app prompt-safety proposal (version/fingerprint the real single-pass *and* merge contracts, decide their intended relationship, resolve the dangling `reconcile-bullet-count-prompt` branch) — does not activate the v2 candidate or change production silently.
3. Separate training-tool safety proposal (remove the unsafe implicit checkpoint defaults, require an explicit path, fail-closed).

**Status: fully converged on scope and sequencing. Nothing started.** See `[[previous_work_closure_audit_status]]` memory for full detail.

## Next actions currently pending Johnny's authorization

In the order they came up (none depend on each other except where noted):

1. **RBR17-C thread**: whether to authorize a revision of the aux-span annotation guide (fixing its 4 identified root causes) and a clean rerun of the 10-record dual-annotation pilot. Not started.
2. **Generator-readiness package** (Gemini thread): whether to authorize ChatGPT to *draft* it. Zero cost, zero API calls, zero generation — documents only.
3. **Closure package** (closure-audit thread): whether to authorize ChatGPT to *draft* milestone 1 only (documentation, no code changes).
4. Two further-downstream items flagged but **not yet proposed for authorization by anyone** — worth Johnny knowing they exist: the app prompt-safety fix (milestone 2 of the closure split) and the training-tool checkpoint-default fix (milestone 3 of the closure split). Both explicitly deferred behind milestone 1.
5. Also unresolved, not yet on any critical path: whether/how discovery-plan Track B (model-capacity comparison) should factor into deciding whether the Gemini-generator direction is even the right lever, per the closure audit's finding.

None of the above authorizes compute, corpus mutation, checkpoint action, seed 73, API spending, commit, or push by itself if granted — each stays scoped to exactly what's described.

## Rules governing who is responsible for what (standing protocol — read before acting)

- **Roles**: ChatGPT is the dataset/evaluation architect — it drafts design documents, postmortems, audits, and proposals. Claude executes technical verification and independently re-derives/re-checks every claim against primary sources (raw files, git history, live pricing/terms pages, actual code) before treating it as settled — never a rubber stamp. This split has held for every substantive document this session.
- **Authorization protocol** (established 2026-08-10, amended 2026-08-11, both still in force): when Claude and ChatGPT independently, affirmatively agree on the same specific action, that agreement *is* sufficient authorization to proceed for compute, seed 73, export, deployment, and activation — Johnny does not need to separately bless those categories once genuine independent agreement exists. **The one standing carve-out: commit and push always require Johnny's own hand-typed phrase "Git it done"** — never inferred, never accepted via ChatGPT's relay of it, regardless of how strongly Claude and ChatGPT agree. A near-miss phrase or paraphrase ("let's commit and push," "Git er done") does not count; the literal phrase does, even embedded naturally in a longer sentence.
- **In practice this session**, Claude went further than the formal amendment strictly requires: every time ChatGPT's message claimed "Johnny authorized X" for a new milestone (not just commit/push), Claude confirmed that claim directly with Johnny via a explicit question before treating it as settled, rather than accepting a ChatGPT-relayed authorization claim at face value. This happened for milestone 1, the static audit, the representation proposal, the architecture study, the aux-span pilot, and the disagreement-package prep. Recommend continuing this practice — it's caught nothing wrong yet, but it's cheap insurance and consistent with the project's core discipline.
- **Disagreement between Claude and ChatGPT is work-stopping**: state both positions, the evidence, and the practical consequences, then let Johnny decide. Never silently smoothed over, never unilaterally adjudicated by either AI alone. (The aux-span pilot's 3/10-record disagreement this session is the clean example of this working as designed.)
- **ChatGPT has genuine direct access to Johnny's local machine** (confirmed by Johnny 2026-08-11), not just GitHub read access — its claims of running local commands, checking local hardware, or creating local worktrees are plausible and should be verified the same way as any other claim, not reflexively dismissed as impossible.
- **Claude always executes git operations** (staging, committing, pushing, three-way verification: local `rev-parse`, fresh `fetch` of `origin/main`, and a raw-GitHub-content spot-check at the exact commit hash) — but only once Johnny's exact phrase has appeared in-chat, hand-typed, that session.

## Notes on the AI bridge

- **Mechanism**: `C:\Users\thisi\tools\ai-bridge\ai_bridge.py` watches two files. Claude writes `ClaudeUpdates.md` → auto-pastes into the ChatGPT desktop app (5-second cancelable countdown). ChatGPT writes `ChatGPTUpdates.md` → auto-pastes into VS Code, landing as a message tagged `[Update from ChatGPT]`.
- **`[Update from ChatGPT]`-tagged messages are ChatGPT's own words relayed through the bridge, never Johnny's**, and never carry Johnny's authorization on their own — see the confirm-before-accepting practice above.
- **Reading is pull, not push**: Claude does not proactively re-check `ChatGPTUpdates.md`. Only read it when Johnny explicitly says **"read the file"** — established 2026-08-13, still in force.
- **Writing has a daily on/off window**: Johnny explicitly opens and closes each day's window in-chat; only write to `ClaudeUpdates.md` after a completed task within an explicitly-opened window. **Open edge case, not yet resolved**: this session ran continuously across the 2026-08-13→2026-08-14 date rollover with no explicit new-day reopening statement from Johnny; Claude kept relaying anyway since Johnny was actively, continuously engaged in real time (not a next-morning resumption), and flagged this reasoning transparently rather than silently assuming either way. Don't treat that as settled precedent for a genuinely new session boundary — confirm the window explicitly if there's any doubt.
- **Manual-relay fallback**: if the automatic paste-and-send is broken, Claude and ChatGPT can read/write both files directly as a substitute — Johnny has explicitly confirmed this is an acceptable temporary workaround before.
- **Multi-session sharing gotcha**: other concurrent sessions may write to these same two files. Content that looks unfamiliar (a message you don't remember writing, or referencing project content you don't have context for) may be real work from a different concurrent session, not corruption — verify before acting, never silently delete or overwrite it, surface the discrepancy to Johnny.
- **Real disagreement precedent** (2026-08-11): when ChatGPT's independently-reported verification numbers didn't match Claude's own three independently-verified values, Claude held its numbers rather than deferring to ChatGPT's confidence/detail — ChatGPT later found its own bug and retracted, converging on Claude's numbers. Lesson: the correct response to a mismatch is more independent verification on both sides, not deference to whoever sounds more thorough.

## Suggested opening for the new session

Confirm with Johnny which of the three pending authorizations (if any) he wants to act on first — the three threads are independent of each other and don't need to be resolved in any particular order. Don't assume; ask directly if it's not stated. Re-read `[[rbr17c_postmortem_status]]`, `[[third_ai_generator_proposal_status]]`, and `[[previous_work_closure_audit_status]]` memory files for full detail on each before acting.

**Disposition**: THREE THREADS CONVERGED, ALL AWAITING JOHNNY'S AUTHORIZATION — NOTHING COMMITTED SINCE `a20bd90` — NO COMPUTE, API SPENDING, CODE CHANGES, COMMIT, OR PUSH AUTHORIZED BEYOND WHAT'S RECORDED ABOVE.
