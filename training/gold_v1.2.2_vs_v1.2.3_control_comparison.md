# Gold v1.2.2 Control-Seed Study vs. Gold v1.2.3 Seed Study

Approved follow-up to `gold_v1.2.3_seed_stability_study.md`: two
additional checkpoints trained on the **`gold_v1.2.2`-only (66-example)
corpus**, at the same seeds (17, 73) used for the `gold_v1.2.3` seed
study, to separate "seed noise" from "`gold_v1.2.3`-specific data
effect." `training/prepare_data.py` was not modified; the control split
was reproduced by directly reusing its `load_jsonl`/`SEED`/`VAL_FRACTION`
against a 66-line extract of `datasets/synthetic.jsonl` (verified: 60
train / 6 val, matching the original `gold_v1.2.2` run's reported split
size exactly). The frozen `gold_v1.2.3` processed files were backed up
before this work (`training/data/processed_gold_v1.2.3_frozen/`) and were
not touched by it.

**Also corrected during this work**: `gold_v1.2.3_seed_study_manifest.md`'s
recorded file hashes were hand-transcribed incorrectly (each was missing
its last character). Re-verified by direct diff against freshly computed
hashes and fixed. The underlying files were never at risk — only the
written record was wrong.

## Overall pass rate across all six configurations

| Seed | `gold_v1.2.2`-only | `gold_v1.2.3` (+6 examples) |
|---|---|---|
| 42 | 13/16 (81%) — original `checkpoint-600` | 11/16 (69%) — `checkpoint-680` |
| 17 | 11/16 (69%) | 8/16 (50%) |
| 73 | 11/16 (69%) | 6/16 (38%) |
| **Average** | **~11.7/16 (73%)** | **~8.3/16 (52%)** |

At every one of the three tested seeds, adding `gold_v1.2.3`'s 6 examples
**reduced** the overall strict pass rate. This is a same-seed,
controlled comparison — the only thing that changes between the two
columns at a given row is whether `gold_v1.2.3`'s examples are in the
training set. This is meaningfully stronger evidence than the seed study
alone could produce.

## Full six-configuration probe grid

| Probe | v1.2.2-42 | v1.2.2-17 | v1.2.2-73 | v1.2.3-42 | v1.2.3-17 | v1.2.3-73 | v1.2.2 subtotal | v1.2.3 subtotal |
|---|---|---|---|---|---|---|---|---|
| 01 | P | P | P | P | P | P | 3/3 | 3/3 |
| 02 | F | F | F | F | **P** | F | 0/3 | 1/3 |
| 03 | P | P | P | F | F | F | **3/3** | **0/3** |
| 04 | P | P | P | P | P | P | 3/3 | 3/3 |
| 05 | P | P | P | P | F | F | **3/3** | **1/3** |
| 06 | P | P | F | F | P | F | 2/3 | 1/3 |
| 07 | P | P | P | P | P | P | 3/3 | 3/3 |
| 08 | F | F | F | **P** | F | F | 0/3 | 1/3 |
| 09 | P | F | F | F | F | F | 1/3 | 0/3 |
| 10 | P | F | P | P | F | P | 2/3 | 2/3 |
| 11 | P | P | P | P | F | F | **3/3** | **1/3** |
| 12 | P | P | P | P | P | F | **3/3** | **2/3** |
| 13 | P | P | P | P | F | P | **3/3** | **2/3** |
| 14 | P | P | P | P | P | P | 3/3 | 3/3 |
| 15 | P | P | P | P | P | F | **3/3** | **2/3** |
| 16 | F | F | F | F | F | F | 0/3 | 0/3 |

Bolded rows are the ones this comparison meaningfully re-classifies
relative to the original seed study.

## Revised classification, replacing the seed study's tentative one

**Probes with strong evidence of a `gold_v1.2.3`-specific negative
effect** (stable or near-stable pass under `gold_v1.2.2`-only at every
seed tested, degrading specifically once `gold_v1.2.3`'s examples are
added):

- **Probe 03**: 3/3 → 0/3. The single strongest signal in this whole
  study. `gold_v1.2.2`-only never fails this probe; `gold_v1.2.3` fails
  it every time.
- **Probe 05**: 3/3 → 1/3. Same seed (17, 73), different data, different
  outcome — a clean same-seed comparison, not just aggregate seed noise.
- **Probe 11**: 3/3 → 1/3. Same pattern.
- **Probe 12**: 3/3 → 2/3 (fails only at seed 73, only under `gold_v1.2.3`).
- **Probe 13**: 3/3 → 2/3 (fails only at seed 17, only under `gold_v1.2.3`).
- **Probe 15**: 3/3 → 2/3 (fails only at seed 73, only under `gold_v1.2.3`)
  — this is the flagship regression `gold_v1.2.2` fixed and that was
  promoted to `regression_guard`; this comparison shows it was
  genuinely stable under `gold_v1.2.2`-only training at all three tested
  seeds, and only becomes fragile once `gold_v1.2.3`'s examples are
  added.

This is now good evidence — not just a plausible hypothesis — that
`gold_v1.2.3`'s additions interact negatively with several capabilities
it wasn't targeting. **Path B's targeted audit should expand its scope**
to include probes 05, 11, 12, 13, and 15 as `gold_v1.2.3`-attributable,
alongside 03, rather than treating those as ordinary seed-sensitive
noise.

**Probes where the failure predates `gold_v1.2.3`** (fails comparably
under `gold_v1.2.2`-only, so `gold_v1.2.3` did not introduce this):

- **Probe 09**: fails on 2 of 3 `gold_v1.2.2`-only seeds (17, 73) with
  the *same* "incomplete thought reframed as needing action/review"
  pattern seen on all three `gold_v1.2.3` seeds. `checkpoint-600`'s own
  clean pass on this probe looks like it was itself a lucky-seed
  outcome, not a stable capability `gold_v1.2.3` broke.
- **Probe 16**: fails on all three `gold_v1.2.2`-only seeds too,
  including the exact phrase **"both are unrelated"** on the
  `gold_v1.2.2`-seed-17 control run — the identical fabricated clause
  originally documented as a `gold_v1.2.2`/`checkpoint-600` finding, now
  reproduced from a from-scratch retrain with no `gold_v1.2.3` data in
  it at all. **This substantially weakens the `gold_v1.2.2` example 002
  vs. `gold_v1.2.3` example 006 conflict hypothesis** that motivated
  auditing this probe in the first place — the behavior exists without
  example 006 in the training set. The targeted audit should still
  happen (per the standing instruction to audit probe 16 regardless of
  seed results), but should go in expecting a pre-existing pattern to
  explain, not a `gold_v1.2.3`-introduced one.

**Probes that are seed-driven, not data-driven** (same seed produces the
same outcome regardless of which corpus was used):

- **Probe 06**: fails specifically at seed 73 in both corpora, passes at
  seed 17 in both corpora. Seed 73 appears to reliably trigger this
  specific misattribution regardless of curriculum content.
- **Probe 10**: fails specifically at seed 17 in both corpora
  (differently each time — dropped from different fields — but seed 17
  destabilizes this probe's cross-field consistency either way).

**Probes `gold_v1.2.3` measurably helped, but not reliably**:

- **Probe 08**: fails on all three `gold_v1.2.2`-only seeds and two of
  three `gold_v1.2.3` seeds — but seed 42 with `gold_v1.2.3`'s data is
  the *only* one of six configurations where it resolves. `gold_v1.2.3`
  didn't fix this reliably, but it's the only training data that ever
  made resolution possible at all.
- **Probe 02**: same shape — fails everywhere except `gold_v1.2.3`-seed
  17. `gold_v1.2.3`'s data made one winning configuration exist where
  none did before, without making it robust.

## What this means for the four authorized paths

This changes the picture from the original seed study in one important
way: **Path B's case is now substantially stronger**, not weaker. Six
probes (03, 05, 11, 12, 13, 15) show a same-seed, controlled signal that
`gold_v1.2.3`'s specific examples are interacting negatively with
capabilities across at least three different categories
(`nested_boundary_depth`, `multi_person_attribution`,
`standalone_task_retention`/`buried_task_retention`/`task_plus_idea`) —
this is broader than the three probes (03/09/16) the original seed study
flagged, and includes the flagship probe 15 fix, which is a genuinely
important finding independent of `gold_v1.2.3`'s own fate.

Still true, and still important: this is evidence of a **correlation**
between adding `gold_v1.2.3`'s data and these regressions, at three
tested seeds. It is not yet a demonstrated **mechanism** — that's what
the targeted conflict inventory (Path B, no edits yet) is for. The
inventory's scope should now explicitly include probes 05, 11, 12, 13,
and 15's categories, not just 03/09/16.

Probe 09 and 16's audits should proceed as already instructed, but with
revised expectations: look for what's already wrong in `gold_v1.2.2`-era
training data (or an inherent model/architecture limitation at this
scale), not a `gold_v1.2.3`-introduced conflict.
