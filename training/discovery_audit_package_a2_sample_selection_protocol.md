# A2 — Frozen Sample Selection Protocol

**Operationalizes:** `training/intent_recovery_data_model_discovery_plan_chatgpt.md` §3, "A2. Frozen sample
design".

**Status: protocol + reference implementation, self-test only, revision 5.** Nothing in this document or
its companion script (`training/discovery_audit_package_a2_sample_selection_script.py`) has been run
against any real candidate dataset. The script has been run repeatedly during development — including
after four rounds of ChatGPT's independent review, each finding real defects (listed below) — always in
`--selftest` mode against a fabricated in-memory fixture, never against real data. The receipt from the
final, corrected version is on disk alongside it (`training/discovery_audit_package_a2_selftest_receipt.json`,
SHA-256 `c0c4aff2535eb8150bfd31b217f677a3c82409d95eb083525d3f7fd5aacaecdd`) and reproduced byte-identically
across two separate process invocations (`cmp`, not just `diff` — genuinely identical bytes, not merely
line-ending-insensitive equal), confirmed directly.

**Post-approval fix, same day, after ChatGPT's five-round approval, before push:** the hash above replaces
`18f7209e...`, which every round of review (both Claude's and ChatGPT's, including ChatGPT's own
independent re-verification) had cited. `18f7209e...` was real and correctly computed at the time — it was
never a fabricated or careless number — but it described the working-tree file as Python's default
text-mode write produced it on Windows (CRLF), not what `git add`/`commit` actually stores in this repo
(`core.autocrlf=true` normalizes the committed blob to LF, a different hash despite identical content).
Caught by directly hashing the committed blob rather than assuming the commit step preserved bytes
unchanged. Fixed at the source: `main()`'s receipt-writing now opens the file explicitly with
`newline="\n"`, so the file is LF on every platform independent of Python's or Windows' default
translation — the working-tree file, the git blob, and a hash computed on any OS now all agree, permanently
closing the gap rather than leaving a hash that quietly stops matching once committed. Both files are now
committed (previously untracked pending Johnny's "Git it done," now provided).

Per Johnny's 2026-08-12 disposition: running this self-test is not "compute" in the gated sense (that term
covers real dataset/model compute); it is ordinary static verification of a design artifact, consistent
with existing project precedent (`training/prepare_regression_balanced_repair_candidate_corpus.py`'s
fail-closed validators run freely during design work too).

## What this protocol governs

Once Johnny separately authorizes actually drawing a sample for a specific candidate (DialogSum, QMSum, or
AMI-reserve, per the plan's shortlist), this is the exact procedure that run must follow — not a procedure
invented after seeing real records.

## Defects two rounds of ChatGPT's independent review found, and how they were fixed

Recorded here in full rather than quietly folded into the procedure below, because the pattern (not just
the fixes) matters for future review rounds.

**Round 1 (2026-08-12):**

1. **Silent underfill.** A seed could return 7 records for an 8-record target while the self-test's only
   size check (`achieved <= target`) still passed. Fixed: an explicit top-up phase pulls from every
   stratum's unconsumed leftovers before giving up; a non-null `shortfall_reason` (and `must_stop: true`,
   added round 2) records it when the pool is genuinely insufficient.
2. **Discarded non-fatal collision evidence.** `screen_collisions()` computed non-fatal findings that
   `select_sample()` only ever logged when fatal. Fixed: every selected record's non-fatal flags are now
   recorded in the manifest's `collision_review_flags_requiring_adjudication` list.
3. **The speaker cap couldn't fire** — no speaker-identity field existed, only a count bucket. Fixed round
   1 with a single `speaker_id`; superseded round 2 (finding 6 below) once multi-party records turned out
   to need more than one.
4. **Cap-consumption order bias** — strata processed in fixed alphabetical order, so a shared identifier
   was always claimed by whichever stratum sorted first. Fixed: stratum processing order is now drawn from
   the same seeded RNG as everything else.
5. **Tie-break fairness test was too narrow** — checked only one previously-biased key across 30 seeds.
   Fixed: the self-test now computes every stratum key's selection frequency and asserts none is stuck at
   0/30 or 30/30.

Also added round 1: an intra-sample self-collision check (each new candidate screened against every
already-selected record's input, closing part of plan §5's "scenario" requirement without needing a shared
identifier), and a pool fingerprint recorded in the manifest.

**Round 2 (2026-08-13), all confirmed by Claude re-reading the code before fixing:**

6. **`speaker_id: str | None` couldn't represent a multi-party record.** QMSum specifically is a
   multi-party meeting corpus — a real gap, not an edge case. Fixed: replaced with `speaker_ids: tuple[str,
   ...]`; the cap now checks and increments every identity present in a record, not just one. The self-test
   fixture now deliberately includes multi-speaker records and asserts they exist.
7. **`_pool_fingerprint()` couldn't prove which sources contributed.** It hashed one flat sorted list of
   normalized texts, so it could confirm *a* pool was supplied but not that all three required benchmark
   files specifically were. Fixed: fingerprint is now broken out per source (see `screen_collisions()`'s
   `"<source>:<record_id>"` labeling convention), each with its own record count and content hash, plus an
   aggregate. The self-test confirms both fake sources appear with correct counts.
8. **Manifest recorded only bare selected IDs.** Requested in round 1's "manifest completeness" correction,
   missed in the round-1 fix. Fixed: added `selected_records`, a per-record list with `stratum` and
   `content_sha256`, verified by the self-test against the actual record content.
9. **A mutable field inside a "frozen" manifest.** `collision_review_flags_requiring_adjudication` entries
   carried `adjudicated: false` — resolving a flag would mean editing the frozen manifest in place, with no
   tamper record. Fixed: that field is removed. Adjudication now lives in a **separate artifact** — see
   "Collision adjudication artifact" below.
10. **No preflight validation.** Structurally malformed metadata (duplicate IDs, empty text, out-of-range
    fields) was silently accepted — fail-open, against this project's usual convention. Fixed:
    `_validate_metadata()` runs first and raises `ValueError`; the self-test proves it fires on a
    deliberately duplicated ID.

Also fixed round 2: the script's own docstring said the receipt was "committed alongside" it, which was
simply wrong (nothing here is committed) — now says "on disk."

**Round 3 (2026-08-13, same day):**

11. **`_pool_fingerprint()` made omissions visible but not enforced.** A missing or partial pool still
    produced a normal-looking manifest — nothing failed, a reviewer just had to notice the counts looked
    wrong. Fixed: `_validate_pool()` fails closed when a caller-supplied `required_pool_sources` mapping
    isn't met (missing source, under-count, or an unexpected source outside the mapping), and
    unconditionally rejects malformed/duplicate pool labels regardless of whether that mapping is supplied.
12. **Leftover candidates were discarded, not preserved for post-adjudication review.** See "Post-
    adjudication completeness" below — resolving an adjudication flag as `"exclude"` can drop the retained
    count below 24 after the fact. Fixed: the manifest now records `unused_leftover_record_ids` as
    informational context for that situation.

**Round 4 (2026-08-13, same day, fourth review):**

13. **`required_pool_sources` was optional and caller-defined.** The round-3 fix added fail-closed
    validation, but `select_sample(..., required_pool_sources=None)` still succeeded with zero enforcement
    if a caller simply omitted the argument — and even when supplied, it was arbitrary caller-chosen
    minimums, not a frozen, reviewed specification, and checked count only (a source with the right count
    but substituted content would pass). Fixed: `required_pool_sources` has no default anymore — every
    call, including the self-test's own, must supply a real mapping — and each source's `PoolSourceSpec`
    may additionally pin an exact expected content hash, not just a minimum count. The self-test's own two
    fake sources now carry hardcoded, pre-computed hashes (not re-derived at test time), so the check is a
    real frozen-spec comparison, not a tautology. See "Frozen pool source specification" below for the real
    three-file equivalent.

## Frozen pool source specification (real three-file spec, computed 2026-08-13)

Per round-4 defect 13, a real run's `required_pool_sources` must not be an arbitrary caller-chosen mapping
— it is this frozen specification. These counts and hashes were computed directly from the actual files
already in this repository (`datasets/benchmark/`, the project's own existing benchmark suite — not
external candidate data, so reading them for this is not "dataset access" in the gated sense), using the
exact same `normalize_for_collision()` + sort + join + SHA-256 procedure `_source_content_hash()`
implements, over each record's `input` field:

| Source name | File | Record count | `content_sha256` |
|---|---|---|---|
| `gold_v1.2.1_probes` | `datasets/benchmark/gold_v1.2.1_probes.jsonl` | 16 | `75c1c14131ae125fee7732f46d3eba7fdafd1768c859d30f5dc283130ecc958c` |
| `source_determined_bullets_acceptance` | `datasets/benchmark/source_determined_bullets_acceptance.jsonl` | 5 | `ef73016f84663c84a49bf4ba1e15eb07204aa7bc99d9ee58f40973568542e2ce` |
| `source_determined_items_v2_acceptance_draft` | `datasets/benchmark/source_determined_items_v2_acceptance_draft.jsonl` | 10 | `b0068d46962e032ef67bdb792062d047124207419ac0a73f67b6ec3e6ac3c915` |

A real A2 run must pool-label every record from these files as `"<source name above>:<record id>"` (e.g.
`"gold_v1.2.1_probes:01"`) and pass `required_pool_sources` as:

```python
{
    "gold_v1.2.1_probes": PoolSourceSpec(16, "75c1c14131ae125fee7732f46d3eba7fdafd1768c859d30f5dc283130ecc958c"),
    "source_determined_bullets_acceptance": PoolSourceSpec(5, "ef73016f84663c84a49bf4ba1e15eb07204aa7bc99d9ee58f40973568542e2ce"),
    "source_determined_items_v2_acceptance_draft": PoolSourceSpec(10, "b0068d46962e032ef67bdb792062d047124207419ac0a73f67b6ec3e6ac3c915"),
}
```

If any of these three files changes before a real run (a new probe added, wording corrected, etc.), this
table must be recomputed and re-pinned deliberately — a hash mismatch here is exactly the fail-closed
signal working as intended, not a bug to route around.

## Semantic collision protocol (predeclared, not executed)

Plan §3 A2 requires exclusion by "normalized **or semantic** collision checks." Round 1 left this as an
open question for whoever runs a real audit to decide. ChatGPT's round-2 review correctly pushed back: that
leaves a load-bearing methodology choice undecided until real candidate text is already in hand, which is
exactly the "decide the rule after seeing the data" sequencing this project's own collision-threshold
precedent (`prepare_regression_balanced_repair_candidate_corpus.py`'s ratified thresholds) was designed to
prevent.

Two named options are predeclared now instead. **Before any real A2 run may proceed past the lexical screen
in step 5 below, Johnny must select one of these (or explicitly document a waiver with a stated reason) —
this is a hard stop, not a runner's discretionary call:**

- **Option A — blind human semantic-similarity review.** Every candidate input, once it survives the
  lexical screen, is read (by a reviewer Johnny separately approves, per the same privacy-review
  requirement A3's adjudicator now carries) alongside the full protected/acceptance set, blind to which
  benchmark record it's being compared against, and rated on a fixed 3-point scale (no paraphrase overlap /
  possible paraphrase, flag for adjudication / clear paraphrase, exclude). Requires the same separate
  approval as any other raw-text access to a real candidate.
- **Option B — embedding-based similarity.** A named, disclosed sentence-embedding model and revision,
  frozen before any real candidate text is embedded, with a fixed cosine-similarity threshold set the same
  way A2's lexical thresholds were (reasoned about and pinned before real records exist, not tuned after
  seeing a result). This is real model execution against real data and requires its own separate
  authorization under protocol step 7 — it is not covered by this package's "no compute" scope.

**If neither is authorized before real sampling begins, A2 proceeds on lexical screening only, and that
limitation must be stated plainly in the resulting manifest and in any downstream A5 report** — not silently
treated as full "normalized or semantic" coverage.

## Collision adjudication artifact

Added 2026-08-13 (defect 9 above). A2's manifest is frozen at write time and never edited afterward — that
is what makes it trustworthy as a record of what was actually drawn. Resolving a non-fatal collision flag
therefore cannot happen by editing the manifest. Instead:

- A separate file, e.g. `<candidate>_a2_adjudications.json`, records: `manifest_sha256` (from
  `compute_manifest_hash()` in the script, computed once right after `select_sample()` returns), and one
  entry per flag in the manifest's `collision_review_flags_requiring_adjudication`: `{"record_id":...,
  "flag_index":..., "disposition": "accept"|"exclude", "rationale":..., "adjudicator":..., "date":...}`.
- A5's collision gate (see the A5 checklist) verifies: the adjudication artifact's `manifest_sha256`
  matches the actual frozen manifest being evaluated (proving it adjudicates *this* sample, not a
  different or later one), and every flagged record_id has a resolved entry.
- If a flag's disposition is `"exclude"`, that record does not count toward A5's usability/coverage
  gates even though it remains listed in the immutable manifest — the manifest records what was *drawn*,
  the adjudication artifact records what was *kept*. The two together, not either alone, are what a real
  audit report cites.

**Post-adjudication completeness — added 2026-08-13, third review; simplified 2026-08-13, fourth review.**
`must_stop` in the frozen manifest reflects only the state at *selection* time, before adjudication runs.
If adjudication later excludes any record, the *retained* count (selected minus adjudication-excluded) can
drop below 24 even though the manifest's own `must_stop` still reads `false`.

The third-review fix described an automatic top-up from the recorded leftovers. ChatGPT's fourth review
correctly found that incomplete: a top-up record would have nowhere to live in an immutable manifest (no
stratum, content hash, or collision-flag entry for it), the existing adjudication artifact is keyed to the
*original* manifest's hash with no provision for a second linked round, the gate-0 formula never actually
added accepted top-up records back into its count, and "same seed continuation rule" wasn't a real,
reconstructible mechanism. Building a fully correct second adjudication lifecycle to support automatic
top-up is real complexity for a rare edge case.

**Adopted instead — the simpler, safer rule ChatGPT itself proposed:** any adjudication `"exclude"`
disposition that would drop the retained count below 24 is **a hard stop, full stop — no automatic
top-up is attempted.** Compute retained count = `len(selected_records)` − count of `"exclude"`
dispositions in the adjudication artifact. If retained count < 24, stop and return to Johnny, exactly as
A2's own pre-adjudication shortfall does (see "Shortfall is a hard stop" below) — this is now literally
the same rule applied at a second point in the lifecycle, not a separate mechanism. `must_stop` in the
manifest and this post-adjudication check are two checkpoints for the identical policy: never let A3/A5
run against fewer than 24 records, silently or otherwise.

`unused_leftover_record_ids` is retained in the manifest as informational context only — if Johnny wants to
authorize a manual follow-up round using those candidates after a post-adjudication stop, that is a fresh,
explicitly-authorized decision at that time, not something this protocol pre-builds an automatic path for.

## Shortfall is a hard stop, not a disclosed inconvenience

Added 2026-08-13 (round 2 finding 4). Round 1's fix reported `shortfall_reason` truthfully but only called
it "decision-relevant," not work-stopping. A5's gates are explicitly denominated over 24 — running them
against a smaller achieved count would silently redefine what the threshold means. **If `select_sample()`
returns `must_stop: true` (equivalently, a non-null `shortfall_reason`), the run stops there. A3 does not
begin, A5 is not computed, and the outcome returns to Johnny** — a small candidate population or heavy
collision/cap exclusion is real, disclosed, decision-relevant information, but it is Johnny's call whether
to accept a smaller sample, pick a different candidate, or adjust the design, not something this protocol
resolves by quietly changing the denominator. This is also recorded as an explicit stop condition in
`discovery_audit_package_privacy_stop_conditions_checklist.md`.

## Procedure

1. **Freeze inputs before drawing anything.** Record, in the run's manifest: candidate name, exact
   version/commit or snapshot date, eligible split(s) actually used, the metadata index's location, the
   pinned random seed, and the SHA-256 hash of the exact selection script version used. `AUDIT_SEED = 24`
   is the pinned default in the current script; a different seed may be substituted only before real
   metadata is loaded for that run, and the substitution itself must be recorded with a reason. Also
   record which semantic-collision option (A, B, or documented waiver) applies to this run, per the section
   above.

2. **Build a metadata-only index — never load target/reference fields at this stage.** Per record: a stable
   `record_id`, `source`/domain, a conversation-length bucket (quartile, computed over the candidate's own
   population), a speaker-count bucket, `speaker_ids` (plural — every speaker identity present in that
   record, when the candidate exposes actual identity, not just a count; may be more than one for a
   multi-party record), a scenario/dialogue identifier if the candidate exposes one, and the input text
   itself. Target quarantine (plan §3 A2: "quarantine targets until input mapping is complete") begins
   here, at intake — not as a later redaction step. `_validate_metadata()` runs first and fails closed on
   duplicate IDs or structurally malformed records (defect 10 above).

3. **Stratify** by `(source, length_quartile, speaker_count_bucket)`. Compute each stratum's quota out of
   the fixed **24-record** total via largest-remainder proportional allocation
   (`_largest_remainder_quotas()` in the script), weighted by stratum population, with the seeded tie-break
   described in round-1 defect 5 above.

4. **Cap repeated speakers and scenarios separately**, each at 2 occurrences in the final sample
   (`SPEAKER_SCENARIO_CAP = 2`), wherever the candidate's identifiers permit determining either at all. A
   multi-party record's cap check applies to *every* speaker identity it carries — one over-cap speaker is
   enough to exclude the record (defect 6 above). Strata are processed in a seeded, non-alphabetical order
   (round-1 defect 4) so no stratum systematically wins a contested identifier.

5. **Screen every candidate's input for collision**, against the full protected+acceptance pool **and**
   against every record already selected earlier in the same draw, before it can be selected:
   - `datasets/benchmark/gold_v1.2.1_probes.jsonl` (protected)
   - `datasets/benchmark/source_determined_bullets_acceptance.jsonl` (acceptance)
   - `datasets/benchmark/source_determined_items_v2_acceptance_draft.jsonl` (acceptance)
   - every already-selected record in this draw (self-collision)
   - **plus** whichever semantic-collision option applies per the section above, if one has been authorized

   Using the same normalization and thresholds already reviewed and ratified for this project in
   `training/prepare_regression_balanced_repair_candidate_corpus.py` (`normalize_for_collision()`: Unicode
   NFKC, lowercase, strip to `[a-z0-9 ]`, collapse whitespace):

   | Check | Threshold | Effect |
   |---|---|---|
   | Normalized exact match | — | **Fatal** — excluded |
   | Normalized containment | ≥20 normalized chars shared | **Fatal** — excluded |
   | Token-set Jaccard | ≥0.15 | Non-fatal — recorded for adjudication |
   | Character-5-gram Jaccard | ≥0.10 | Non-fatal — recorded for adjudication |

   A fatal collision excludes the record; the run continues drawing from the same shuffled stratum list. A
   non-fatal flag does not exclude the record, but its reasons are recorded in the frozen manifest — see
   "Collision adjudication artifact" above for how those get resolved without mutating the manifest.

6. **Top up if any stratum underfilled its quota.** After all strata are processed, if the total selected
   is below the 24-record target, draw from the combined, seed-shuffled leftovers of every stratum until
   the target is reached or the entire pool is exhausted. **If `must_stop: true` results, stop — see
   "Shortfall is a hard stop" above.**

7. **Freeze the manifest, then hash it.** Record: target/achieved sample size, shortfall reason and
   `must_stop` flag, seed, cap, thresholds, the per-source pool fingerprint, per-stratum quotas, both
   `selected_record_ids` and the richer `selected_records` (with per-record stratum and content hash), the
   full exclusion log, and the full non-fatal collision-review-flag list. Immediately call
   `compute_manifest_hash()` on the result and record that hash wherever the manifest is stored — it is
   what any later adjudication artifact must cite. This manifest is what later gets reviewed by ChatGPT
   (protocol step 6) before A3 begins, and it is never edited after this point.

8. **Only after the manifest freezes** may a separate "input-only view" be produced for A3 reviewers.
   Target/reference fields stay quarantined until A4.

## Reference implementation

`training/discovery_audit_package_a2_sample_selection_script.py` implements steps 2–7 as
`select_sample()`, `screen_collisions()`, `_largest_remainder_quotas()`, `_validate_metadata()`,
`_validate_pool()`, `_pool_fingerprint()`, and `compute_manifest_hash()`. It has no filesystem or network
dependency of its own — a real run supplies `metadata` (built separately, by whatever authorized process
reads the candidate's actual metadata index), `pool` (the three benchmark files above, read by the caller,
labeled `"<source>:<record_id>"`), and `required_pool_sources` (a **required** argument as of round 4 — see
"Frozen pool source specification" above; there is no default that skips validation) as plain Python
values. This keeps the script honest: it cannot accidentally reach out to a real dataset on its own,
because it never contains a path to one, and it cannot silently run with an unverified pool either.

Run it yourself: `python training/discovery_audit_package_a2_sample_selection_script.py --selftest
--receipt-out <path>`. The only supported mode is `--selftest`; there is no flag that points this script at
a real dataset, by design — wiring it to a real metadata source is a separate, later, separately-authorized
step.

### Self-test coverage (all 20 checks pass, receipt hash above)

- Same seed → byte-identical manifest across repeated calls, and across separate process invocations.
- Different seed → different selection.
- Achieved sample size equals target exactly when the pool can support it, with no shortfall and
  `must_stop: false`.
- Speaker cap and scenario cap both hold, counting every identity in a multi-party record's `speaker_ids`
  tuple — and the fixture is confirmed to actually contain multi-party records, not just unreachable code
  for the multi-speaker path.
- Direct unit checks: a forced normalized-exact duplicate is flagged fatal; an unrelated record is not; a
  record sharing every token with a pool entry (reordered, so neither exact nor containment) is flagged
  non-fatal, not silently dropped.
- The manifest's non-fatal review-flag entries are well-formed and carry no mutable `adjudicated` field.
- `selected_records` entries carry the correct stratum and content hash for every selected record.
- The pool fingerprint reports correct per-source counts for both fake sources, not just one flat total.
- A pool missing a required source, or short on the required count, raises via `_validate_pool()`.
- A pool containing a source outside the caller's `required_pool_sources` mapping also raises.
- A pool source matching on count but mismatching a pinned `expected_content_sha256` also raises — checked
  against hardcoded hashes computed once from the fixture, not re-derived at test time.
- `unused_leftover_record_ids` contains only valid, never-selected record IDs.
- Quota tie-break varies across 30 seeds, and no stratum key is stuck always-selected or always-excluded.
- A deliberately undersized fixture reports its shortfall explicitly and sets `must_stop: true`.
- A deliberately duplicated record ID triggers `_validate_metadata()`'s `ValueError`.
- `compute_manifest_hash()` is deterministic for identical content and differs across different runs.

## What remains gated

Actually calling `select_sample()` with a real candidate's metadata, and reading the three real benchmark
pool files, both require Johnny's separate authorization to access that candidate's metadata index in the
first place (plan §3 A1's stop rule, plan's authority boundary). This document and script only ever produce
a *method*; running that method against a real candidate is execution, not design, and is out of scope for
this package.
