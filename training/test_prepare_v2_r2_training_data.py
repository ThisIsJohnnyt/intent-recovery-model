"""Standalone assertion tests for prepare_v2_r2_training_data.py -- dummy
data only, except where noted. No pytest dependency: run directly with
`python test_prepare_v2_r2_training_data.py`, matching this repo's
existing script-based tooling convention (see test_prepare_data.py).

Covers every fail-closed condition listed in
prepare_v2_r2_training_data.py's own module docstring, plus a positive
check against the real, authorized R2 candidate and baseline corpora.
"""
import copy
import hashlib
import sys
import tempfile
from pathlib import Path

import prepare_v2_r2_training_data as p
from prepare_data import input_hash

FAILURES = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


def expect_system_exit(fn, *args, **kwargs) -> str | None:
    """Returns the SystemExit message if raised, else None."""
    try:
        fn(*args, **kwargs)
    except SystemExit as e:
        return str(e)
    return None


def make_record(text: str, output: dict, difficulty: str = "medium", category: str = "test_category") -> dict:
    return {
        "input": text,
        "output": output,
        "difficulty": difficulty,
        "category": category,
        "v1_target": "dummy-v1-target",
        "v2_target": "dummy-v2-target",
    }


OUT_A = {"narrative": "a", "bullets": ["a"], "action_items": []}
OUT_B = {"narrative": "b", "bullets": ["b"], "action_items": []}
OUT_C = {"narrative": "c", "bullets": ["c"], "action_items": []}
OUT_C2 = {"narrative": "c2", "bullets": ["c2"], "action_items": []}

REC_A = make_record("record A input", OUT_A)
REC_B = make_record("record B input", OUT_B)
REC_C = make_record("record C input", OUT_C)
REC_C_CHANGED = {**REC_C, "output": OUT_C2, "v1_target": "changed-v1", "v2_target": "changed-v2"}

HASH_A = input_hash(REC_A["input"])
HASH_B = input_hash(REC_B["input"])
HASH_C = input_hash(REC_C["input"])


def with_patched_constants(record_count: int, changed_records: dict):
    """Context manager-ish helper: patches module constants for the
    duration of a test, always restoring them afterward, even on
    failure -- so dummy-data tests never leak state into the real-data
    tests that run later in the same process."""

    class _Patched:
        def __enter__(self):
            self._orig_count = p.EXPECTED_RECORD_COUNT
            self._orig_changed = p.EXPECTED_CHANGED_RECORDS
            p.EXPECTED_RECORD_COUNT = record_count
            p.EXPECTED_CHANGED_RECORDS = changed_records
            return p

        def __exit__(self, *exc):
            p.EXPECTED_RECORD_COUNT = self._orig_count
            p.EXPECTED_CHANGED_RECORDS = self._orig_changed
            return False

    return _Patched()


def test_happy_path_dummy_diff_and_authorization():
    with with_patched_constants(3, {HASH_C: "dummy-ti-1"}):
        baseline = [REC_A, REC_B, REC_C]
        candidate = [REC_A, REC_B, REC_C_CHANGED]
        changed = p.diff_by_input_hash(baseline, candidate)
        check("happy path: exactly one changed record detected", set(changed) == {HASH_C}, changed)
        err = expect_system_exit(p.verify_changed_set_matches_authorization, changed)
        check("happy path: authorized single change passes with no SystemExit", err is None, err)


def test_wrong_record_count_fails_closed():
    with with_patched_constants(3, {HASH_C: "dummy-ti-1"}):
        baseline = [REC_A, REC_B, REC_C]
        candidate = [REC_A, REC_B]  # missing a record
        err = expect_system_exit(p.diff_by_input_hash, baseline, candidate)
        check("wrong record count fails closed", err is not None and "expected exactly 3" in err, err)


def test_duplicate_input_hash_fails_closed():
    with with_patched_constants(3, {HASH_C: "dummy-ti-1"}):
        baseline = [REC_A, REC_B, REC_C]
        candidate = [REC_A, REC_A, REC_C]  # REC_B replaced by a duplicate of REC_A
        err = expect_system_exit(p.diff_by_input_hash, baseline, candidate)
        check("duplicate input hash fails closed", err is not None and "Duplicate input hash" in err, err)


def test_identity_mismatch_fails_closed():
    with with_patched_constants(3, {HASH_C: "dummy-ti-1"}):
        rec_d = make_record("record D input -- not in baseline at all", OUT_A)
        baseline = [REC_A, REC_B, REC_C]
        candidate = [REC_A, rec_d, REC_C]  # REC_B's identity replaced outright
        err = expect_system_exit(p.diff_by_input_hash, baseline, candidate)
        check("stable-identity mismatch fails closed", err is not None and "identity differs" in err, err)


def test_reordering_fails_closed():
    with with_patched_constants(3, {HASH_C: "dummy-ti-1"}):
        baseline = [REC_A, REC_B, REC_C]
        candidate = [REC_A, REC_C, REC_B]  # same set, different order
        err = expect_system_exit(p.diff_by_input_hash, baseline, candidate)
        check("record reordering fails closed", err is not None and "order differs" in err, err)


def test_unauthorized_extra_change_fails_closed():
    with with_patched_constants(3, {HASH_C: "dummy-ti-1"}):
        rec_b_changed = {**REC_B, "output": OUT_C}  # B also changed, not just C
        baseline = [REC_A, REC_B, REC_C]
        candidate = [REC_A, rec_b_changed, REC_C_CHANGED]
        changed = p.diff_by_input_hash(baseline, candidate)
        err = expect_system_exit(p.verify_changed_set_matches_authorization, changed)
        check(
            "unauthorized extra changed record fails closed",
            err is not None and "Unexpected changes" in err,
            err,
        )


def test_missing_expected_change_fails_closed():
    with with_patched_constants(3, {HASH_C: "dummy-ti-1"}):
        baseline = [REC_A, REC_B, REC_C]
        candidate = [REC_A, REC_B, REC_C]  # nothing changed at all
        changed = p.diff_by_input_hash(baseline, candidate)
        err = expect_system_exit(p.verify_changed_set_matches_authorization, changed)
        check(
            "missing an expected authorized change fails closed",
            err is not None and "Missing expected changes" in err,
            err,
        )


def test_unauthorized_field_change_fails_closed():
    with with_patched_constants(3, {HASH_C: "dummy-ti-1"}):
        rec_c_bad = {**REC_C_CHANGED, "category": "a_totally_different_category"}
        baseline = [REC_A, REC_B, REC_C]
        candidate = [REC_A, REC_B, rec_c_bad]
        changed = p.diff_by_input_hash(baseline, candidate)
        err = expect_system_exit(p.verify_changed_set_matches_authorization, changed)
        check(
            "changing a field other than output/v1_target/v2_target fails closed",
            err is not None and "changed unexpected field(s)" in err,
            err,
        )


def test_split_comparison_detects_reordering_independently():
    # Exercises build_split_comparison in isolation (defense in depth --
    # diff_by_input_hash's own order check would already catch this
    # upstream in the real pipeline, but this proves the split-comparison
    # step also independently guards against it).
    baseline = [REC_A, REC_B, REC_C]
    candidate = [REC_B, REC_A, REC_C]  # A and B swapped
    err = expect_system_exit(p.build_split_comparison, baseline, candidate, set())
    check("split comparison independently detects reordering", err is not None and "Split membership/order differs" in err, err)


def test_split_comparison_passes_when_identical():
    baseline = [REC_A, REC_B, REC_C]
    candidate = [REC_A, REC_B, REC_C_CHANGED]
    result = p.build_split_comparison(baseline, candidate, {HASH_B})
    check(
        "split comparison passes and reports correct train/val counts when membership/order match",
        result["train_count"] == 2 and result["val_count"] == 1
        and result["train_hashes_identical"] and result["val_hashes_identical"],
        result,
    )


def test_output_dir_already_exists_fails_closed():
    with tempfile.TemporaryDirectory() as tmp:
        existing = Path(tmp) / "already-here"
        existing.mkdir()
        err = expect_system_exit(p.ensure_output_dir_available, existing)
        check("existing output directory fails closed", err is not None and "already exists" in err, err)

        not_yet_created = Path(tmp) / "brand-new-exclusive-dir"
        err2 = expect_system_exit(p.ensure_output_dir_available, not_yet_created)
        check("nonexistent output directory passes", err2 is None, err2)


def test_canonical_fingerprint_matches_documented_baseline_convention():
    # Same 3-record dummy set as the happy-path test, just checking the
    # canonicalization is deterministic and order-independent on input,
    # not asserting a specific locked hash (that's only meaningful for the
    # real 66-record corpus, covered by the real-data test below).
    recs = [
        {"prompt": "zzz-last", "target": "t1"},
        {"prompt": "aaa-first", "target": "t2"},
    ]
    fp1 = p.canonical_training_data_fingerprint(recs)
    fp2 = p.canonical_training_data_fingerprint(list(reversed(recs)))
    check("canonical fingerprint is independent of input list order", fp1 == fp2, (fp1, fp2))


def test_real_pinned_fingerprints_match():
    err = expect_system_exit(p.verify_pinned_fingerprints)
    check("real baseline/R2-candidate/split-manifest fingerprints match pinned values", err is None, err)


def test_real_data_diff_matches_expected_ti_corrections():
    baseline = p.load_migrated_targets()
    candidate = p.load_jsonl_records(p.R2_CANDIDATE_PATH)
    changed = p.diff_by_input_hash(baseline, candidate)
    check(
        "real data: exactly 3 changed records, matching ti-001/ti-002/ti-003 hashes",
        set(changed) == set(p.EXPECTED_CHANGED_RECORDS),
        sorted(changed),
    )
    err = expect_system_exit(p.verify_changed_set_matches_authorization, changed)
    check("real data: changed set passes authorization check with no SystemExit", err is None, err)


def test_real_data_split_comparison_is_identical():
    from prepare_data import SPLIT_MANIFEST_PATH, load_val_hashes

    baseline = p.load_migrated_targets()
    candidate = p.load_jsonl_records(p.R2_CANDIDATE_PATH)
    val_hashes = load_val_hashes(SPLIT_MANIFEST_PATH)
    result = p.build_split_comparison(baseline, candidate, val_hashes)
    check(
        "real data: split membership/order identical between baseline and R2 candidate",
        result["train_count"] == 60 and result["val_count"] == 6
        and result["train_hashes_identical"] and result["val_hashes_identical"],
        result,
    )


def main() -> None:
    tests = [
        test_happy_path_dummy_diff_and_authorization,
        test_wrong_record_count_fails_closed,
        test_duplicate_input_hash_fails_closed,
        test_identity_mismatch_fails_closed,
        test_reordering_fails_closed,
        test_unauthorized_extra_change_fails_closed,
        test_missing_expected_change_fails_closed,
        test_unauthorized_field_change_fails_closed,
        test_split_comparison_detects_reordering_independently,
        test_split_comparison_passes_when_identical,
        test_output_dir_already_exists_fails_closed,
        test_canonical_fingerprint_matches_documented_baseline_convention,
        test_real_pinned_fingerprints_match,
        test_real_data_diff_matches_expected_ti_corrections,
        test_real_data_split_comparison_is_identical,
    ]
    for t in tests:
        t()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print(f"All {len(tests)} prepare_v2_r2_training_data.py tests passed.")


if __name__ == "__main__":
    main()
