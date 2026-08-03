"""Derives candidate v2-serialized train/val data for the controlled
seed-17 R2 replay protocol (training/controlled_seed17_r2_replay_protocol.md),
authorized 2026-08-03. Scope: source
gold_v1.2.2_r2_derived_candidate.jsonl only; reuse the frozen seed-17
split membership/order (the same, unchanged split_manifest.json); write
new, exclusive candidate artifacts; do not train, run inference, evaluate,
touch seed 73, or modify any frozen baseline artifact.

Fails closed (raises SystemExit, writes nothing) if:
  - either input file's fingerprint drifts from its pinned expected value;
  - the corpus is not exactly 66 records in both files;
  - stable record identity (input hash) or order differs between the
    baseline and R2 candidate corpora -- a missing, extra, duplicated, or
    reordered record;
  - any record other than the three authorized ti-001/ti-002/ti-003
    corrections differs in any field, or one of those three changes a
    field other than output/v1_target/v2_target;
  - the changed-record set is not exactly {ti-001, ti-002, ti-003};
  - the resulting train/val split membership or order (recomputed
    independently for both corpora) differs;
  - the output directory already exists.

Gold v1.2.3 exclusion is structural, not a runtime scan: both source
files are pinned by fingerprint to their known, gold_v1.2.2-only,
66-record content -- neither ever references datasets/synthetic.jsonl,
which is the only file gold_v1.2.3 material could reach this pipeline
through.

Usage:
    python prepare_v2_r2_training_data.py [--output-dir DIR]
"""
import argparse
import hashlib
import json
from pathlib import Path

from prepare_data import SPLIT_MANIFEST_PATH, input_hash, load_val_hashes
from prepare_v2_training_data import (
    MIGRATED_TARGETS_PATH,
    build_v2_train_val_split,
    load_migrated_targets,
    verify_every_target_parses_and_matches_output,
)

TRAINING_DIR = Path(__file__).parent
R2_CANDIDATE_PATH = TRAINING_DIR / "gold_v1.2.2_r2_derived_candidate.jsonl"
DEFAULT_OUTPUT_DIR = TRAINING_DIR / "data" / "processed_gold_v1.2.2_r2_v2contract_seed17"
EXPECTED_RECORD_COUNT = 66

# Pinned fingerprints of the frozen baseline this replay must reuse
# unchanged. Each was independently recomputed against the real repository
# this session (see training/controlled_seed17_r2_replay_protocol_claude_verification.md
# and training/gold_v1.2.2_seed17_v2contract_study_provenance.md) before
# being pinned here -- not copied from either doc without re-derivation.
EXPECTED_BASELINE_TARGETS_FINGERPRINT = "1bef1b0476c372b35dd08a89f7e767e25c46ff1ace202d90ffbb5a3d7e4c0307"
EXPECTED_R2_CANDIDATE_FINGERPRINT = "197adb3578b27c8b76bdbb33b3dcb35398ccd980932f0f718a5fedd732b9c1ac"
EXPECTED_SPLIT_MANIFEST_FINGERPRINT = "24610be8c5b91be13b064acaaab4f8bbae59b0ec175e66d1fb8ccb94cd049485"
BASELINE_TRAINING_DATA_FINGERPRINT_FOR_COMPARISON = "e548e0b633ac1ca11b109adbf88ddbda95a42add38d93f524b700f4762092fd3"

# The exact three corrections this protocol authorizes, keyed by stable
# input-hash identity (not list position, which is only a secondary check).
# Any changed record whose input hash is not one of these three keys is
# out of authorized scope and fails closed.
EXPECTED_CHANGED_RECORDS = {
    "b314914e28568a4c38062a66c44e9813b0adede52ffe04ba1e662838407fad21": "ti-001",
    "0b778d450a85284bde042ebd21473c5da4070df191e5ccab90783209a8b80dca": "ti-002",
    "d465f20edc074b9536e6fcde489c22c93c3eb96c2b2573b22f909faf0ba4f2fb": "ti-003",
}


def file_fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def verify_pinned_fingerprints() -> None:
    checks = [
        (MIGRATED_TARGETS_PATH, EXPECTED_BASELINE_TARGETS_FINGERPRINT, "baseline migrated-targets corpus"),
        (R2_CANDIDATE_PATH, EXPECTED_R2_CANDIDATE_FINGERPRINT, "R2 derived candidate corpus"),
        (SPLIT_MANIFEST_PATH, EXPECTED_SPLIT_MANIFEST_FINGERPRINT, "frozen split manifest"),
    ]
    for path, expected, label in checks:
        if not path.exists():
            raise SystemExit(f"Missing required file for {label}: {path}")
        actual = file_fingerprint(path)
        if actual != expected:
            raise SystemExit(
                f"Fingerprint mismatch for {label} ({path.name}): expected {expected}, got "
                f"{actual}. Refusing to proceed -- this script only operates against the exact "
                "frozen baseline artifacts this protocol was verified against."
            )
        print(f"[fingerprint OK] {label}: {actual}")


def diff_by_input_hash(baseline: list[dict], candidate: list[dict]) -> dict[str, tuple[dict, dict]]:
    """Returns {input_hash: (baseline_record, candidate_record)} for every
    stable-identity record whose content differs between the two corpora.
    Fails closed on any identity mismatch (missing/extra/duplicate/
    reordered input hash in either corpus) before comparing content."""
    if len(baseline) != EXPECTED_RECORD_COUNT:
        raise SystemExit(f"Baseline corpus has {len(baseline)} records, expected exactly {EXPECTED_RECORD_COUNT}.")
    if len(candidate) != EXPECTED_RECORD_COUNT:
        raise SystemExit(f"R2 candidate corpus has {len(candidate)} records, expected exactly {EXPECTED_RECORD_COUNT}.")

    baseline_by_hash: dict[str, dict] = {}
    for r in baseline:
        h = input_hash(r["input"])
        if h in baseline_by_hash:
            raise SystemExit(f"Duplicate input hash in baseline corpus: {h}")
        baseline_by_hash[h] = r

    candidate_by_hash: dict[str, dict] = {}
    for r in candidate:
        h = input_hash(r["input"])
        if h in candidate_by_hash:
            raise SystemExit(f"Duplicate input hash in R2 candidate corpus: {h}")
        candidate_by_hash[h] = r

    baseline_hashes = set(baseline_by_hash)
    candidate_hashes = set(candidate_by_hash)
    if baseline_hashes != candidate_hashes:
        only_baseline = sorted(baseline_hashes - candidate_hashes)
        only_candidate = sorted(candidate_hashes - baseline_hashes)
        raise SystemExit(
            "Stable record identity differs between baseline and R2 candidate corpora -- "
            f"{len(only_baseline)} input hash(es) only in baseline, {len(only_candidate)} only in "
            f"candidate. Refusing to proceed: {only_baseline[:3]} / {only_candidate[:3]}"
        )

    baseline_order = [input_hash(r["input"]) for r in baseline]
    candidate_order = [input_hash(r["input"]) for r in candidate]
    if baseline_order != candidate_order:
        raise SystemExit(
            "Record order differs between baseline and R2 candidate corpora -- refusing to "
            "proceed. The candidate must be the baseline with only ti-001/ti-002/ti-003's "
            "outputs replaced, in the same order."
        )

    changed = {}
    for h in baseline_hashes:
        if baseline_by_hash[h] != candidate_by_hash[h]:
            changed[h] = (baseline_by_hash[h], candidate_by_hash[h])
    return changed


def verify_changed_set_matches_authorization(changed: dict[str, tuple[dict, dict]]) -> None:
    changed_hashes = set(changed)
    expected_hashes = set(EXPECTED_CHANGED_RECORDS)
    if changed_hashes != expected_hashes:
        unexpected = sorted(changed_hashes - expected_hashes)
        missing = sorted(expected_hashes - changed_hashes)
        raise SystemExit(
            "Changed-record set does not match the authorized ti-001/ti-002/ti-003 corrections -- "
            f"refusing to proceed. Unexpected changes: {unexpected}. Missing expected changes: "
            f"{missing}."
        )

    allowed_changed_fields = {"output", "v1_target", "v2_target"}
    for h, (base_rec, cand_rec) in changed.items():
        changed_fields = {k for k in base_rec if base_rec.get(k) != cand_rec.get(k)}
        if not changed_fields <= allowed_changed_fields:
            raise SystemExit(
                f"Record {EXPECTED_CHANGED_RECORDS[h]} ({h}) changed unexpected field(s) "
                f"{sorted(changed_fields - allowed_changed_fields)} -- only output (and its "
                "mechanically derived v1_target/v2_target) may change."
            )

    print(
        f"[changed-record check OK] exactly {len(changed)} records differ, mapped to "
        f"{sorted(EXPECTED_CHANGED_RECORDS.values())}, each only in output/v1_target/v2_target."
    )


def build_split_comparison(baseline: list[dict], candidate: list[dict], val_hashes: set[str]) -> dict:
    """Recomputes train/val membership+order for both corpora independently
    and confirms they're identical. Given diff_by_input_hash already proved
    identical input-hash sets and order, this should always hold -- this
    function produces the explicit, machine-readable proof rather than
    leaving it as an unstated consequence."""

    def split_hashes(records: list[dict]) -> tuple[list[str], list[str]]:
        train, val = [], []
        for r in records:
            h = input_hash(r["input"])
            (val if h in val_hashes else train).append(h)
        return train, val

    baseline_train, baseline_val = split_hashes(baseline)
    candidate_train, candidate_val = split_hashes(candidate)

    if baseline_train != candidate_train or baseline_val != candidate_val:
        raise SystemExit(
            "Split membership/order differs between baseline and R2 candidate corpora -- "
            "refusing to proceed."
        )

    return {
        "train_count": len(baseline_train),
        "val_count": len(baseline_val),
        "train_hashes_identical": baseline_train == candidate_train,
        "val_hashes_identical": baseline_val == candidate_val,
        "train_hash_order": baseline_train,
        "val_hash_order": baseline_val,
    }


def canonical_training_data_fingerprint(records: list[dict]) -> str:
    """Matches the canonicalization independently reverse-engineered and
    confirmed against the seed-17 baseline's own recorded fingerprint (see
    training/controlled_seed17_r2_replay_protocol_claude_verification.md):
    a single JSON array of all {prompt, target} pairs, sorted by prompt,
    sort_keys=True, compact separators -- so the candidate fingerprint is
    directly comparable to the already-documented baseline one."""
    sortable = sorted(records, key=lambda r: r["prompt"])
    blob = json.dumps(sortable, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def ensure_output_dir_available(output_dir: Path) -> None:
    if output_dir.exists():
        raise SystemExit(
            f"Output directory already exists: {output_dir}. This script must write to a new, "
            "exclusive artifact directory -- refusing to overwrite or reuse an existing one."
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=str, default=None, help="Overrides the default candidate-data output dir")
    args = parser.parse_args()
    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR

    ensure_output_dir_available(output_dir)

    print("=== Step 1: pinned fingerprint verification ===")
    verify_pinned_fingerprints()

    print("\n=== Step 2: load both corpora ===")
    baseline = load_migrated_targets()
    candidate = load_jsonl_records(R2_CANDIDATE_PATH)
    print(f"Loaded {len(baseline)} baseline record(s), {len(candidate)} R2-candidate record(s).")
    print(
        "Gold v1.2.3 exclusion: structural, not scanned -- both source files are pinned above to "
        "their known gold_v1.2.2-only content and neither ever reads datasets/synthetic.jsonl."
    )

    print("\n=== Step 3: stable-identity diff (baseline vs. R2 candidate) ===")
    changed = diff_by_input_hash(baseline, candidate)
    verify_changed_set_matches_authorization(changed)

    print("\n=== Step 4: re-verify all 66 candidate targets parse and match output ===")
    verify_every_target_parses_and_matches_output(candidate)

    print("\n=== Step 5: split derivation (frozen membership/order) ===")
    val_hashes = load_val_hashes(SPLIT_MANIFEST_PATH)
    split_comparison = build_split_comparison(baseline, candidate, val_hashes)
    print(
        f"Split manifest ({SPLIT_MANIFEST_PATH.name}): {split_comparison['val_count']} val, "
        f"{split_comparison['train_count']} train -- membership and order confirmed identical to "
        "the frozen seed-17 baseline."
    )
    train_split, val_split = build_v2_train_val_split(candidate, val_hashes)

    print("\n=== Step 6: write exclusive candidate artifacts ===")
    output_dir.mkdir(parents=True, exist_ok=False)

    def write(name: str, recs: list[dict]) -> None:
        path = output_dir / name
        with path.open("w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{path}: {len(recs)} examples")

    write("train.jsonl", train_split)
    write("val.jsonl", val_split)

    training_data_fingerprint = canonical_training_data_fingerprint(train_split + val_split)

    print("\n=== Step 7: machine-readable evidence ===")
    changed_record_report = {
        EXPECTED_CHANGED_RECORDS[h]: {
            "input_hash": h,
            "input_excerpt": base_rec["input"][:80],
            "baseline_output": base_rec["output"],
            "candidate_output": cand_rec["output"],
        }
        for h, (base_rec, cand_rec) in sorted(changed.items(), key=lambda kv: EXPECTED_CHANGED_RECORDS[kv[0]])
    }
    diff_path = output_dir / "original_vs_r2_diff.json"
    diff_path.write_text(json.dumps(changed_record_report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{diff_path}: {len(changed_record_report)} changed record(s) mapped to ti-001/ti-002/ti-003")

    split_comparison_path = output_dir / "split_comparison.json"
    split_comparison_path.write_text(json.dumps(split_comparison, indent=2), encoding="utf-8")
    print(f"{split_comparison_path}: split membership/order comparison")

    print("\n=== Summary ===")
    print(f"Candidate training-data fingerprint (train+val, canonical): {training_data_fingerprint}")
    print(f"Baseline training-data fingerprint for comparison:          {BASELINE_TRAINING_DATA_FINGERPRINT_FOR_COMPARISON}")
    print(f"Output directory: {output_dir}")
    print(
        "\nNo training, inference, or evaluation performed. This produces data-preparation "
        "artifacts only, per the authorized scope."
    )


if __name__ == "__main__":
    main()
