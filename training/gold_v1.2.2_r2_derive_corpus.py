"""Derive the Revision-2 target-integrity-corrected candidate corpus from
the pinned, immutable gold_v1.2.2 (66-example) corpus, per the nine-step
safeguard list agreed in gold_v1.2.2_target_integrity_corrections_design_notes_r2.md
and authorized by Johnny on 2026-08-03.

This script does NOT touch datasets/synthetic.jsonl or datasets/gold/gold_v1.2.2.jsonl.
It loads the corpus from the pinned, immutable commit 8d7aa09 via `git show`,
applies exactly the three approved corrections from
gold_v1.2.2_target_integrity_corrections_proposal_r2.jsonl, and writes a
separately fingerprinted derived candidate corpus plus a provenance/
validation report. No model training or inference is performed here.

Usage: python gold_v1.2.2_r2_derive_corpus.py
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from prompt_contract_v2_migrate import build_v1_target, build_v2_target
from prompt_contract_v2_parser import ParseError, parse_output

REPO_ROOT = Path(__file__).parent.parent
PINNED_COMMIT = "8d7aa09"
CORRECTIONS_PATH = Path(__file__).parent / "gold_v1.2.2_target_integrity_corrections_proposal_r2.jsonl"
SPLIT_MANIFEST_PATH = Path(__file__).parent / "split_manifest.json"

OUTPUT_CORPUS_PATH = Path(__file__).parent / "gold_v1.2.2_r2_derived_candidate.jsonl"
OUTPUT_REPORT_PATH = Path(__file__).parent / "gold_v1.2.2_r2_corpus_derivation_report.md"


def input_hash(raw_input: str) -> str:
    return hashlib.sha256(raw_input.encode("utf-8")).hexdigest()


def canonical_json_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load_pinned_corpus() -> list[dict]:
    raw = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"{PINNED_COMMIT}:datasets/synthetic.jsonl"],
        capture_output=True, encoding="utf-8", check=True,
    ).stdout
    records = [json.loads(l) for l in raw.splitlines() if l.strip()]
    return records


def load_corrections() -> dict[str, dict]:
    corrections = []
    with open(CORRECTIONS_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                corrections.append(json.loads(line))

    ids = [c["proposal_id"] for c in corrections]
    hashes = [c["record_input_sha256"] for c in corrections]
    if len(ids) != len(set(ids)):
        raise SystemExit(f"FATAL: duplicate proposal_id in {CORRECTIONS_PATH.name}")
    if len(hashes) != len(set(hashes)):
        raise SystemExit(f"FATAL: duplicate record_input_sha256 in {CORRECTIONS_PATH.name}")

    return {c["record_input_sha256"]: c for c in corrections}


def load_val_hashes() -> set[str]:
    with open(SPLIT_MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)
    return {entry["input_sha256"] for entry in manifest["val"]}


def main() -> None:
    pinned = load_pinned_corpus()
    print(f"[1] Loaded {len(pinned)} records from pinned immutable commit {PINNED_COMMIT}:datasets/synthetic.jsonl")
    if len(pinned) != 66:
        raise SystemExit(f"FATAL: expected exactly 66 pinned records, got {len(pinned)}")
    unique_inputs = {r["input"] for r in pinned}
    if len(unique_inputs) != 66:
        raise SystemExit(f"FATAL: expected 66 unique inputs, got {len(unique_inputs)}")

    corrections_by_hash = load_corrections()
    print(f"    Loaded {len(corrections_by_hash)} correction(s) from {CORRECTIONS_PATH.name}")
    if len(corrections_by_hash) != 3:
        raise SystemExit(f"FATAL: expected exactly 3 corrections, got {len(corrections_by_hash)}")

    val_hashes = load_val_hashes()

    derived = []
    changed_ids = []
    for rec in pinned:
        ih = input_hash(rec["input"])
        entry = {
            "input": rec["input"],
            "output": rec["output"],
            "difficulty": rec.get("difficulty"),
            "category": rec.get("category"),
        }

        if ih in corrections_by_hash:
            corr = corrections_by_hash[ih]
            # [3] Fail closed if current_output has drifted from what the
            # correction proposal was reviewed against.
            if corr["current_output"] != rec["output"]:
                raise SystemExit(
                    f"FATAL: current_output drift detected for {corr['proposal_id']} "
                    f"-- refusing to apply a correction against stale state"
                )
            entry["output"] = corr["proposed_output"]
            changed_ids.append(corr["proposal_id"])

        derived.append(entry)

    print(f"[2-4] Applied corrections by exact input SHA-256; changed: {changed_ids}")

    # [7] Prove exactly three structured outputs changed, and nothing else did.
    diffs = [
        i for i, (old, new) in enumerate(zip(pinned, derived))
        if old["output"] != new["output"]
    ]
    if len(diffs) != 3:
        raise SystemExit(f"FATAL: expected exactly 3 changed outputs, found {len(diffs)} at indices {diffs}")

    # [5] Preserve input, category, difficulty, and record order exactly;
    # split membership is keyed by input hash in split_manifest.json and is
    # therefore automatically preserved since no input text changed.
    for old, new in zip(pinned, derived):
        if old["input"] != new["input"]:
            raise SystemExit("FATAL: input text drifted -- order/identity not preserved")
        if old.get("category") != new.get("category"):
            raise SystemExit("FATAL: category drifted")
        if old.get("difficulty") != new.get("difficulty"):
            raise SystemExit("FATAL: difficulty drifted")
    print("[5] Verified input/category/difficulty/order preserved for all 66 records")

    # [6] Regenerate v1 and v2 serializations mechanically -- never hand-edited.
    parse_failures = []
    for i, entry in enumerate(derived):
        narrative = entry["output"]["narrative"]
        bullets = entry["output"]["bullets"]
        actions = entry["output"]["action_items"]

        v1_target = build_v1_target(narrative, bullets, actions)
        v2_target = build_v2_target(narrative, bullets, actions)
        entry["v1_target"] = v1_target
        entry["v2_target"] = v2_target

        # [8] Parse every regenerated v2 target and require exact structural equality.
        try:
            parsed = parse_output(v2_target)
        except ParseError as e:
            parse_failures.append((i, f"does not parse: {e}"))
            continue
        if parsed.narrative != narrative.strip():
            parse_failures.append((i, "narrative mismatch after parse"))
        if parsed.bullets != bullets:
            parse_failures.append((i, "bullets mismatch after parse"))
        if parsed.actions != actions:
            parse_failures.append((i, "actions mismatch after parse"))

    print(f"[6] Regenerated v1_target and v2_target for all {len(derived)} records")
    if parse_failures:
        for i, reason in parse_failures:
            print(f"    PARSE FAILURE at index {i}: {reason}")
        raise SystemExit(f"FATAL: {len(parse_failures)} record(s) failed parse-verification -- refusing to write output")
    print(f"[8] Parse-verified all {len(derived)} regenerated v2_targets: exact structural equality confirmed")

    # Distribution tables, recomputed from the derived corpus itself.
    def action_dist(records, only_hashes=None):
        from collections import Counter
        c = Counter()
        for r in records:
            ih = input_hash(r["input"])
            if only_hashes is not None and ih in only_hashes:
                continue
            c[len(r["output"]["action_items"])] += 1
        return dict(sorted(c.items()))

    current_train = action_dist(pinned, only_hashes=val_hashes)
    derived_train = action_dist(derived, only_hashes=val_hashes)
    current_full = action_dist(pinned)
    derived_full = action_dist(derived)

    # [9] Fingerprints.
    old_content_fp = hashlib.sha256(canonical_json_bytes(
        [{"input": r["input"], "output": r["output"]} for r in pinned]
    )).hexdigest()
    new_content_fp = hashlib.sha256(canonical_json_bytes(
        [{"input": r["input"], "output": r["output"]} for r in derived]
    )).hexdigest()
    old_v2_fp = hashlib.sha256(canonical_json_bytes(
        [build_v2_target(r["output"]["narrative"], r["output"]["bullets"], r["output"]["action_items"]) for r in pinned]
    )).hexdigest()
    new_v2_fp = hashlib.sha256(canonical_json_bytes([r["v2_target"] for r in derived])).hexdigest()
    proposal_fp = hashlib.sha256(CORRECTIONS_PATH.read_bytes()).hexdigest()

    OUTPUT_CORPUS_PATH.write_text(
        "\n".join(json.dumps(d, ensure_ascii=False) for d in derived) + "\n",
        encoding="utf-8",
    )
    print(f"[9] Wrote derived candidate corpus: {OUTPUT_CORPUS_PATH.name}")

    report = f"""# Gold v1.2.2 Revision-2 Corpus Derivation -- Provenance & Validation Report

**Generated by:** `gold_v1.2.2_r2_derive_corpus.py`
**Authorized by:** Johnny, 2026-08-03 -- "Revision 2 corpus derivation under the agreed nine-step safeguards. Gold v1.2.2 remains immutable. No training or inference is authorized."
**Compute performed:** none (model). **Training/inference performed:** none.
**Gold v1.2.2 (`datasets/synthetic.jsonl` / `datasets/gold/gold_v1.2.2.jsonl` / commit `{PINNED_COMMIT}`):** untouched.

## Safeguard-by-safeguard confirmation

1. Loaded from pinned immutable commit `{PINNED_COMMIT}:datasets/synthetic.jsonl` via `git show`, not the live working copy -- confirmed {len(pinned)} records, {len(unique_inputs)} unique inputs.
2. Corrections located by exact input SHA-256 against `{CORRECTIONS_PATH.name}` -- all 3 resolved uniquely.
3. `current_output` verified structurally identical, as parsed JSON (Python dict/list/value equality; not a raw-byte comparison of the source JSON text), to the pinned record's `output` before replacement for all 3 corrections -- no drift detected (would have failed closed otherwise).
4. Exactly the three `output` objects replaced: {changed_ids}.
5. Input text, category, difficulty, and record order verified identical between pinned and derived corpus for all 66 records. Split membership (keyed by input SHA-256 in `split_manifest.json`) is therefore unchanged by construction, since no input text changed.
6. `v1_target` and `v2_target` mechanically regenerated for all 66 records via `prompt_contract_v2_migrate.build_v1_target`/`build_v2_target` -- no hand-edited serialized text.
7. Exactly 3 structured outputs differ between pinned and derived corpus, confirmed by direct diff: indices {diffs}.
8. Every regenerated `v2_target` parsed via `prompt_contract_v2_parser.parse_output` and checked for exact structural equality (narrative/bullets/actions) against the structured output it was generated from -- **{len(derived)}/{len(derived)} pass, 0 parse failures**.
9. Fingerprints recorded below.

## Fingerprints

| Artifact | SHA-256 |
|---|---|
| Old corpus content (input+output, 66 records) | `{old_content_fp}` |
| New corpus content (input+output, 66 records) | `{new_content_fp}` |
| Old corpus v2-serialization | `{old_v2_fp}` |
| New corpus v2-serialization | `{new_v2_fp}` |
| Correction proposal (`{CORRECTIONS_PATH.name}`) | `{proposal_fp}` |

## Exactly-three-changed proof

| proposal_id | current actions | derived actions | current bullets | derived bullets |
|---|---:|---:|---:|---:|
"""
    for pid in changed_ids:
        old_rec = next(r for r in pinned if input_hash(r["input"]) in corrections_by_hash and corrections_by_hash[input_hash(r["input"])]["proposal_id"] == pid)
        corr = corrections_by_hash[input_hash(old_rec["input"])]
        report += (
            f"| {pid} | {len(corr['current_output']['action_items'])} | "
            f"{len(corr['proposed_output']['action_items'])} | "
            f"{len(corr['current_output']['bullets'])} | "
            f"{len(corr['proposed_output']['bullets'])} |\n"
        )

    report += f"""
## Distribution comparison (recomputed directly from the derived corpus)

### Train split ({sum(current_train.values())} examples)

| Actions | Current | Derived |
|---:|---:|---:|
"""
    for k in sorted(set(current_train) | set(derived_train)):
        report += f"| {k} | {current_train.get(k, 0)} | {derived_train.get(k, 0)} |\n"

    report += f"""
### Full corpus ({sum(current_full.values())} examples)

| Actions | Current | Derived |
|---:|---:|---:|
"""
    for k in sorted(set(current_full) | set(derived_full)):
        report += f"| {k} | {current_full.get(k, 0)} | {derived_full.get(k, 0)} |\n"

    report += f"""
## Status

Derived candidate corpus written to `{OUTPUT_CORPUS_PATH.name}` ({len(derived)} records). This is a separately fingerprinted candidate, not a new numbered Gold release -- no release/version name has been chosen, per the design notes' explicit deferral of that decision. `datasets/synthetic.jsonl` and `datasets/gold/gold_v1.2.2.jsonl` were not modified.

**Stopping here for joint verification, as instructed. No training, inference, or further model compute has been performed.**
"""
    OUTPUT_REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"    Wrote provenance/validation report: {OUTPUT_REPORT_PATH.name}")

    print("\nDone. Stopping for joint verification -- no training or inference performed.")


if __name__ == "__main__":
    main()
