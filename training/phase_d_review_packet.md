# Phase D Review Packet — Real-Validation / Sealed-Holdout Separation

Prepared by Claude Code for joint review with ChatGPT before any real notes
are collected or assigned to either split. Nothing in this packet changes
release status or dataset content — it's a review artifact only.

## 1. `docs/decisions/PDR-004.md` (current, full text)

```markdown
# PDR-004: Split real-note evaluation into routine validation and sealed holdout

**Date**: 2026-07-30
**Status**: Accepted

## Decision

**Accepted**: split the single `datasets/real_holdout.jsonl` file and its
role into two files with two different roles:

- **`datasets/real_validation.jsonl`** — real personal notes used for
  routine development-time evaluation. May be consulted after every
  training run, used for checkpoint comparison and error analysis, and
  may inform future curriculum decisions. Never trained on.
- **`datasets/real_holdout.jsonl`** — real personal notes sealed for
  declared release milestones only. Must not be consulted to guide
  day-to-day development, curriculum authoring, seed selection, or
  checkpoint tuning. Never trained on. Evaluated only by a separate,
  explicit script (`training/evaluate_holdout.py`), never automatically.

`training/prepare_data.py` now reads and processes both files
independently (`real_validation.jsonl` → `real_validation.jsonl`,
`real_holdout.jsonl` → `real_holdout_eval.jsonl` in
`training/data/processed/`). `training/train.py` automatically evaluates
`real_validation.jsonl` after every run, exactly as it previously
evaluated the single `real_holdout.jsonl`/`real_eval.jsonl` — but no
longer touches the sealed holdout at all.

## Reasoning

The single-file design conflated two incompatible needs. Every prior
lessons-learned document (`gold_v1.2.1`, `gold_v1.2.2`, `gold_v1.2.3`)
recommended populating `real_holdout.jsonl` to get a real-note validation
signal, since the synthetic-only validation split (5-7 examples) is too
small for `eval_loss` to mean anything and — as the `gold_v1.2.3`
multi-seed stability study showed directly — too small to reliably
characterize a checkpoint's behavior at all. But `real_holdout.jsonl`'s
own stated purpose was "checking whether synthetic-only training
generalizes to real writing," which requires it to stay untouched until
a genuine release decision — a file that's evaluated after every routine
training run, the way `train.py` was doing automatically, stops
functioning as a holdout the moment it's populated and routinely
consulted. There was no file for the "check things during normal
development" need that the lessons-learned docs were actually asking for.

Splitting the file (not just the discipline) makes the boundary
mechanically enforced rather than a memory-dependent convention: routine
runs literally cannot see the sealed file's results unless
`evaluate_holdout.py` is deliberately invoked, and that script's own
docstring is written to make casual/curious invocation feel wrong.

## Approach

1. `datasets/real_validation.jsonl` and `datasets/real_holdout.jsonl`
   both gitignored, both empty until populated by hand (same format and
   process as before: write `input` from a real note, write or
   ChatGPT-draft-and-correct the `output`).
2. `training/prepare_data.py` processes both independently; neither ever
   contributes to `train.jsonl`.
3. `training/train.py` evaluates `real_validation.jsonl` automatically,
   same as before; no longer touches the holdout.
4. `training/evaluate_holdout.py` (new) is the only way to evaluate
   against the sealed holdout — explicit invocation, explicit checkpoint
   argument, a docstring and printed banner that both say plainly: don't
   run this unless a release milestone has actually been declared.
5. Data-size policy: no arbitrary minimum-example count required before
   either file starts being useful. Start with whatever real notes can
   be collected and reviewed responsibly; report coverage (category,
   difficulty, length, intent-type, duplicate rate) as it grows, same as
   any other dataset batch.
6. Provenance/consent metadata (if ever recorded) lives outside the
   trained `input`/`output` pair, same principle `prepare_data.py`
   already applies to `difficulty`/`category` — never fed to the model.

## Approved by

- Product Owner
- Engineering Lead (Claude Code)
```

## 2. Commit `ee4980c` — files touched and diffs

```
 datasets/.gitignore           |  7 ++--
 datasets/gold/DATASET_CARD.md |  8 +++--
 datasets/gold/LICENSE.md      |  8 +++--
 docs/decisions/PDR-004.md     | 78 +++++++++++++++++++++++++++++++
 training/DATASET_SPEC.md      | 18 ++++++--
 training/evaluate_holdout.py  | 59 +++++++++++++++++++++++
 training/prepare_data.py      | 31 ++++++++++---
 training/train.py             | 27 +++++++-----
 8 files changed, 212 insertions(+), 24 deletions(-)
```

`datasets/.gitignore` (new content, both files gitignored):
```
# Real personal notes used as held-out eval sets — not synthetic, not meant
# to be published alongside the code. real_validation.jsonl (routine
# dev-time eval) and real_holdout.jsonl (sealed, release-milestone-only
# eval) serve different roles — see docs/decisions/PDR-004.md.
real_validation.jsonl
real_holdout.jsonl
```

`datasets/gold/DATASET_CARD.md` diff:
```diff
- personal notes are kept in `datasets/real_holdout.jsonl`, used only as a
- held-out evaluation set, and are excluded from version control entirely
- (see `datasets/.gitignore`) — they are never trained on and never
+ personal notes are kept in `datasets/real_validation.jsonl` (routine
+ development-time evaluation) and `datasets/real_holdout.jsonl` (sealed,
+ release-milestone-only evaluation — see `docs/decisions/PDR-004.md` for
+ why these are two separate files), both excluded from version control
+ entirely (see `datasets/.gitignore`) — neither is ever trained on or
  published alongside this corpus.
```

`datasets/gold/LICENSE.md` diff:
```diff
- does **not** apply to `datasets/real_holdout.jsonl`, which contains the
- project owner's real personal notes, is excluded from version control, and
- is never published.
+ does **not** apply to `datasets/real_validation.jsonl` or
+ `datasets/real_holdout.jsonl`, both of which contain the project owner's
+ real personal notes (for routine development-time evaluation and sealed
+ release-milestone evaluation, respectively — see `docs/decisions/PDR-004.md`),
+ are excluded from version control, and are never published.
```

`training/evaluate_holdout.py` — new file as introduced by `ee4980c` (its
`DATA_DIR`/`OUTPUT_DIR` imports and `load_split("real_holdout_eval.jsonl")`
single-arg call were written against `train.py`'s state *before* this
branch's `--seed`/`--output-dir`/`--data-dir` refactor existed on `main`.
The merge (`ebf248d`) had to fix both — see section 4 for the corrected,
current version):

```python
"""Evaluate a checkpoint against the SEALED real_holdout.jsonl set.
...
from train import DATA_DIR, OUTPUT_DIR, evaluate_format_validity, load_split


def main() -> None:
    checkpoint_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT_DIR / "final"
    holdout_path = DATA_DIR / "real_holdout_eval.jsonl"
    ...
    holdout_ds = load_split("real_holdout_eval.jsonl")
    evaluate_format_validity(model, tokenizer, device, "real_holdout", holdout_ds)
```

`training/prepare_data.py` diff (against the pre-Phase-D version, before
this branch's split-manifest work existed on top of it):
```diff
-Reads datasets/synthetic.jsonl (trained on) and datasets/real_holdout.jsonl
-(held out, eval only) and writes training/data/processed/{train,val,real_eval}.jsonl,
+Reads datasets/synthetic.jsonl (trained on), datasets/real_validation.jsonl
+(held out, routine dev-eval), and datasets/real_holdout.jsonl (held out,
+sealed release-milestone eval only), and writes
+training/data/processed/{train,val,real_validation,real_holdout_eval}.jsonl,
 each record shaped {"prompt": ..., "target": ...} ready for tokenization.
+
+real_validation.jsonl and real_holdout.jsonl serve different roles ...
 """
@@ def main():
     synthetic_path = DATA_DIR / "synthetic.jsonl"
+    validation_path = DATA_DIR / "real_validation.jsonl"
     holdout_path = DATA_DIR / "real_holdout.jsonl"

     synthetic = load_jsonl(synthetic_path)
+    real_validation = load_jsonl(validation_path)
     real_holdout = load_jsonl(holdout_path)
@@
-    write("real_eval.jsonl", real_holdout)
+    write("real_validation.jsonl", real_validation)
+    write("real_holdout_eval.jsonl", real_holdout)
```

`training/train.py` diff (same baseline):
```diff
-model against val.jsonl and real_eval.jsonl and prints how many outputs
-contain all three well-formed section markers, so you can eyeball quality
-before exporting to ONNX.
+model against val.jsonl and real_validation.jsonl and prints how many
+outputs contain all three well-formed section markers, so you can eyeball
+quality before exporting to ONNX.
+
+Deliberately does NOT evaluate the sealed real_holdout.jsonl -- ...
 """
@@
-    real_eval_path = DATA_DIR / "real_eval.jsonl"
-    if real_eval_path.exists() and real_eval_path.read_text(encoding="utf-8").strip():
-        real_eval_ds = load_split("real_eval.jsonl")
-        evaluate_format_validity(model, tokenizer, device, "real_eval", real_eval_ds)
+    real_validation_path = DATA_DIR / "real_validation.jsonl"
+    if real_validation_path.exists() and real_validation_path.read_text(encoding="utf-8").strip():
+        real_validation_ds = load_split("real_validation.jsonl")
+        evaluate_format_validity(model, tokenizer, device, "real_validation", real_validation_ds)
     else:
-        print("\n(no real_eval.jsonl examples yet...)")
+        print("\n(no real_validation.jsonl examples yet...)")
+
+    print("\n(real_holdout.jsonl is not evaluated here...)")
```

## 3. Current `training/prepare_data.py` (post-merge, full file)

Full current content — see `training/prepare_data.py` in the repo at
commit `223e147` (latest pushed). Relevant excerpt for this review, the
full `main()`:

```python
def main() -> None:
    synthetic_path = DATA_DIR / "synthetic.jsonl"
    validation_path = DATA_DIR / "real_validation.jsonl"
    holdout_path = DATA_DIR / "real_holdout.jsonl"

    synthetic = load_jsonl(synthetic_path)
    real_validation = load_jsonl(validation_path)
    real_holdout = load_jsonl(holdout_path)

    if not synthetic:
        print(f"No usable examples found in {synthetic_path}.\n...", file=sys.stderr)
        sys.exit(1)

    val_hashes = load_val_hashes(SPLIT_MANIFEST_PATH)
    train_split, val_split = split_by_manifest(synthetic, val_hashes)
    print(f"Split manifest ({SPLIT_MANIFEST_PATH.name}): {len(val_split)} example(s) "
          f"pinned to val, {len(train_split)} default to train.")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    def write(name, records):
        ...

    write("train.jsonl", train_split)
    write("val.jsonl", val_split)
    write("real_validation.jsonl", [{k: v for k, v in r.items() if k != "_input"} for r in real_validation])
    write("real_holdout_eval.jsonl", [{k: v for k, v in r.items() if k != "_input"} for r in real_holdout])
    ...
```

Note the load-bearing fact for the leakage question: `train_split` and
`val_split` are produced by `split_by_manifest(synthetic, val_hashes)` —
called with the `synthetic` variable only. `real_validation` and
`real_holdout` are never passed into that function or referenced anywhere
near `train_split`/`val_split`'s construction.

## 4. Current `training/evaluate_holdout.py` (post-merge, full file)

```python
"""Evaluate a checkpoint against the SEALED real_holdout.jsonl set.

Usage:
    python evaluate_holdout.py [checkpoint_dir]

This is deliberately a separate, explicit script -- NOT run automatically
by train.py. datasets/real_holdout.jsonl is reserved for declared release
milestones (see docs/decisions/PDR-004.md): it must not be consulted to
guide day-to-day development, curriculum authoring, seed selection, or
checkpoint tuning. Routine development-time evaluation against real notes
belongs in datasets/real_validation.jsonl instead, which train.py already
evaluates automatically after every run.

Before running this: confirm a release milestone has actually been
declared. If you're just curious how a checkpoint is doing, that's
exactly the temptation this file exists to resist -- use
real_validation.jsonl for that instead.
"""
import sys
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from train import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR, evaluate_format_validity, load_split


def main() -> None:
    checkpoint_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT_DIR / "final"
    holdout_path = DEFAULT_DATA_DIR / "real_holdout_eval.jsonl"

    if not holdout_path.exists() or not holdout_path.read_text(encoding="utf-8").strip():
        print(f"{holdout_path} is empty -- nothing to evaluate. ...", file=sys.stderr)
        sys.exit(1)

    print("=== SEALED HOLDOUT EVALUATION ===\n"
          "This should only run at a declared release milestone. ...\n")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(str(checkpoint_dir))
    model = AutoModelForSeq2SeqLM.from_pretrained(str(checkpoint_dir)).to(device)

    holdout_ds = load_split(DEFAULT_DATA_DIR, "real_holdout_eval.jsonl")
    evaluate_format_validity(model, tokenizer, device, "real_holdout", holdout_ds)
```

This is corrected from `ee4980c`'s original: that version imported
`DATA_DIR`/`OUTPUT_DIR` (renamed to `DEFAULT_DATA_DIR`/`DEFAULT_OUTPUT_DIR`
by this branch's own refactor) and called `load_split("real_holdout_eval.jsonl")`
with one argument against a function that now requires
`load_split(data_dir, name)`. Fixed during the merge (`ebf248d`) and
verified to import and run correctly (test run in section 6).

## 5. Current `datasets/real_validation.jsonl` and `datasets/real_holdout.jsonl`

**Both are currently empty. No real notes have been collected or assigned
to either split.** `real_validation.jsonl` doesn't exist as a file yet;
`real_holdout.jsonl` exists (created 2026-07-28, before Phase D) but is
0 bytes. This review is happening before any real data risk exists —
there is nothing to leak yet, which is exactly why this is the right time
to review the mechanism before populating either file.

## 6. Test commands and results

All tests run against synthetic dummy content (never real notes), then
reverted to the exact original empty/nonexistent state afterward.

**Static check — does `train.py` ever functionally reference the holdout?**
```
$ grep -n -i holdout training/train.py
23:Deliberately does NOT evaluate the sealed real_holdout.jsonl -- ...   (docstring)
24:separate, explicit step (see evaluate_holdout.py) reserved for ...    (docstring)
145:      # its lower loss. Revisit once real_holdout.jsonl or a larger  (comment)
183:      "\n(real_holdout.jsonl is not evaluated here -- it's sealed... (print string)
184:      "release milestones; run evaluate_holdout.py explicitly...    (print string)
```
Zero functional references — every hit is a comment, docstring, or a
print statement telling the user it's *not* evaluating the holdout.

**Static check — what feeds `train_split`/`val_split`?**
```
$ grep -n "train_split\|val_split\|split_by_manifest(synthetic" training/prepare_data.py
174:    train_split, val_split = split_by_manifest(synthetic, val_hashes)
189:    write("train.jsonl", train_split)
190:    write("val.jsonl", val_split)
```
Only `synthetic` is ever passed into `split_by_manifest`.

**Dynamic leakage test** — populated both files with distinct, greppable
dummy content, ran the real pipeline, checked for cross-contamination:
```
$ echo '{"input": "TESTMARKER_VALIDATION_DUMMY ...", ...}' > datasets/real_validation.jsonl
$ echo '{"input": "TESTMARKER_HOLDOUT_DUMMY ...", ...}' > datasets/real_holdout.jsonl
$ python prepare_data.py
Split manifest (split_manifest.json): 6 example(s) pinned to val, 66 default to train.
.../train.jsonl: 66 examples
.../val.jsonl: 6 examples
.../real_validation.jsonl: 1 examples
.../real_holdout_eval.jsonl: 1 examples

$ grep -c "TESTMARKER" data/processed/train.jsonl data/processed/val.jsonl
data/processed/train.jsonl:0
data/processed/val.jsonl:0

$ grep -l "TESTMARKER_VALIDATION_DUMMY" data/processed/*.jsonl
data/processed/real_validation.jsonl
$ grep -l "TESTMARKER_HOLDOUT_DUMMY" data/processed/*.jsonl
data/processed/real_holdout_eval.jsonl
```
Neither dummy reached `train.jsonl` or `val.jsonl`. Each landed only in
its own designated output file — no cross-contamination between
validation and holdout either.

**Explicit-invocation test for the sealed holdout**:
```
$ python evaluate_holdout.py
=== SEALED HOLDOUT EVALUATION ===
This should only run at a declared release milestone. If that's not why
you're running this, stop and use real_validation.jsonl instead.

Using device: cuda
Checkpoint: .../checkpoints/thoughtorganizer-flan-t5/final

=== Evaluating on real_holdout (1 examples) ===
[0] valid_format=True
  generated: ###NARRATIVE### ...
real_holdout: 1/1 produced well-formed marker sections
```
Ran and imported cleanly (confirms the merge's fix to the constant
names/`load_split` signature actually works), printed the intended
warning banner, and evaluated only the holdout content — nothing from
`train.py`'s normal path triggers this.

**Cleanup** — reverted both files to their original state and regenerated
`training/data/processed/` from that state:
```
$ rm datasets/real_validation.jsonl
$ : > datasets/real_holdout.jsonl
$ python prepare_data.py
Note: .../real_validation.jsonl is empty. ...
Note: .../real_holdout.jsonl is empty. ...
.../real_validation.jsonl: 0 examples
.../real_holdout_eval.jsonl: 0 examples
```

## 7. Claude's alignment status

Going through each point requested:

- **Validation/holdout leakage**: No leakage found. Verified by both
  static analysis and a live dynamic test with distinct dummy content.
  **Aligned.**
- **Can routine evaluation access only `real_validation`?**: Yes.
  `train.py` has zero functional reference to the holdout file or
  `evaluate_holdout.py`. **Aligned.**
- **Does sealed holdout evaluation require an explicit command?**: Yes.
  It's a separate script with its own explicit invocation, a printed
  warning banner, and a refusal (`sys.exit(1)`) when the file is empty.
  Nothing calls it automatically. **Aligned.**
- **Can training preparation ever ingest either file accidentally?**:
  No. `train_split`/`val_split` trace to `synthetic` only, both
  statically and dynamically confirmed. **Aligned.**
- **Reproducibility and evaluation logging**: **Gap, not aligned.**
  Both `train.py`'s real-validation eval and `evaluate_holdout.py` only
  print to stdout — there's no structured, saved record of a real-data
  eval run (which checkpoint, which seed, what was generated, when).
  Every other evaluation artifact in this project's recent work
  (`run_benchmark.py`) writes a JSON results file; this real-data path
  doesn't have an equivalent. Fine today because both files are empty,
  but worth fixing before real evaluation runs start accumulating.
- **Provenance, consent, de-identification, sensitive content**:
  **Gap, not yet implemented — and not claimed to be.** PDR-004 itself
  only says provenance/consent metadata "lives outside the trained pair,
  if ever recorded" — there is no actual field, file, or process for
  this in the current code. That's consistent with the plan (ChatGPT's
  data-governance package is explicitly the next step, not something
  Phase D's code was meant to solve), but it means **no real notes
  should be collected until that package exists** — the current
  implementation has no mechanism to enforce consent or de-identification
  even if someone tried to follow a policy manually.
- **Compatibility with strict benchmark scoring**: **Partial gap.**
  Schema compatibility is solid — `real_validation.jsonl`/
  `real_holdout.jsonl` are validated by the exact same `validate_record()`
  function as every gold/synthetic file, so the `input`/`output` shape is
  identical. But the *evaluation* tooling isn't equivalent:
  `evaluate_format_validity` only checks marker presence/ordering, not
  the strict semantic rubric (`topic_completeness`, `attribution_accuracy`,
  etc.) that `run_benchmark.py` produces for the 16-probe suite. If
  real-validation/holdout outputs are meant to go through the same
  strict scoring process ChatGPT has been applying to benchmark probes,
  that wiring doesn't exist yet — would need a `run_benchmark.py`-style
  scaffold pointed at these files instead of ad hoc printed text.

**Net assessment**: the mechanical separation this review packet was
mainly asked to check — leakage, access boundaries, explicit-command
gating — is solid and independently verified, not just asserted from
reading the code. The three flagged items (logging, governance, strict-
scoring wiring) are real gaps, but none of them contradict PDR-004's own
stated scope, and two of the three (governance, and probably the
scoring scaffold) are explicitly what the next data-governance package is
for. Recommend: safe to merge Phase D as-is for the mechanical split, but
hold real-note collection until the governance package (and ideally the
logging gap) are addressed — matching the plan already agreed.
