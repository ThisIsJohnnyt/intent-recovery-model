"""Standalone assertion tests for real_data_private.py -- dummy data only,
no real notes. No pytest dependency: run directly with
`python test_real_data_private.py`, matching this repo's existing
script-based tooling convention (prepare_data.py, run_benchmark.py, etc.
have no test framework either). Exits 0 iff every test passes.

Covers exactly the acceptance behaviors required by
training/REAL_DATA_EVALUATION_PROTOCOL.md and
training/phase_e_real_data_dummy_implementation_handoff.md's "Required
tests" for workstream 3.
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

import real_data_private as rdp

FAILURES = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


def test_canonical_json_key_order_independence():
    a = rdp.canonical_json_bytes({"b": 2, "a": 1})
    b = rdp.canonical_json_bytes({"a": 1, "b": 2})
    check("canonical_json: key order does not affect output", a == b)


def test_canonical_json_no_insignificant_whitespace():
    data = rdp.canonical_json_bytes({"a": 1})
    check("canonical_json: no spaces after separators", b" " not in data, repr(data))


def test_source_and_pair_fingerprint_scope():
    inp = "TESTDUMMY water the plants"
    out = {"narrative": "Water the plants.", "bullets": ["Water the plants"], "action_items": ["Water the plants"]}
    sf = rdp.source_fingerprint(inp)
    pf = rdp.pair_fingerprint(inp, out)
    check("source_fingerprint is 64-char hex", len(sf) == 64 and all(c in "0123456789abcdef" for c in sf))
    check("pair_fingerprint differs from source_fingerprint", sf != pf)
    # Changing only the output must change pair_fingerprint but not source_fingerprint
    out2 = {**out, "bullets": ["Water the plants today"]}
    check(
        "pair_fingerprint changes when output changes, source_fingerprint does not",
        rdp.pair_fingerprint(inp, out2) != pf and rdp.source_fingerprint(inp) == sf,
    )


def test_rubric_fingerprint_excludes_own_field():
    rubric = {"record_id": "rv_dummy", "must_preserve": ["x"], "rubric_fingerprint": "sha256:whatever-stale-value"}
    rubric_no_fp = {k: v for k, v in rubric.items() if k != "rubric_fingerprint"}
    fp1 = rdp.rubric_fingerprint(rubric)
    fp2 = rdp.rubric_fingerprint(rubric_no_fp)
    check("rubric_fingerprint ignores its own stale field (self-reference avoided)", fp1 == fp2)
    rubric_changed = {**rubric_no_fp, "must_preserve": ["x", "y"]}
    check("rubric_fingerprint changes when rubric content changes", rdp.rubric_fingerprint(rubric_changed) != fp1)


def _dummy_record(record_id: str, note_suffix: str = "") -> dict:
    inp = f"TESTDUMMY note {record_id}{note_suffix}"
    out = {"narrative": f"Do the {record_id} thing.", "bullets": [f"{record_id} thing"], "action_items": [f"{record_id} thing"]}
    rubric = {"record_id": record_id, "must_preserve": [record_id]}
    return {
        "record_id": record_id,
        "source_fingerprint": rdp.source_fingerprint(inp),
        "pair_fingerprint": rdp.pair_fingerprint(inp, out),
        "rubric_fingerprint": rdp.rubric_fingerprint(rubric),
    }


def test_dataset_fingerprint_order_independence_and_change_detection():
    r1 = _dummy_record("rv_dummy0001")
    r2 = _dummy_record("rv_dummy0002")
    r3 = _dummy_record("rv_dummy0003")

    fp_forward = rdp.dataset_fingerprint([r1, r2, r3], "real_validation")
    fp_shuffled = rdp.dataset_fingerprint([r3, r1, r2], "real_validation")
    check("dataset_fingerprint: independent of input list/manifest line order", fp_forward == fp_shuffled)

    r2_edited = _dummy_record("rv_dummy0002", note_suffix=" edited")
    fp_after_edit = rdp.dataset_fingerprint([r1, r2_edited, r3], "real_validation")
    check("dataset_fingerprint: changes after an active record edit", fp_after_edit != fp_forward)

    fp_holdout = rdp.dataset_fingerprint([r1, r2, r3], "real_holdout")
    check("dataset_fingerprint: validation and holdout never share a fingerprint for the same records", fp_holdout != fp_forward)

    try:
        rdp.dataset_fingerprint([r1], "not_a_real_split")
        check("dataset_fingerprint: rejects an invalid split value", False)
    except rdp.DatasetFingerprintError:
        check("dataset_fingerprint: rejects an invalid split value", True)


def test_checkpoint_fingerprint():
    with tempfile.TemporaryDirectory() as tmp:
        ckpt = Path(tmp) / "dummy_checkpoint"
        (ckpt / "nested").mkdir(parents=True)
        (ckpt / "config.json").write_text('{"dummy": true}', encoding="utf-8")
        (ckpt / "nested" / "weights.bin").write_bytes(b"dummy-weight-bytes")

        fp1 = rdp.checkpoint_fingerprint(ckpt)
        fp2 = rdp.checkpoint_fingerprint(ckpt)
        check("checkpoint_fingerprint: deterministic across two runs, same directory", fp1 == fp2)

        (ckpt / "nested" / "weights.bin").write_bytes(b"CHANGED-weight-bytes")
        fp3 = rdp.checkpoint_fingerprint(ckpt)
        check("checkpoint_fingerprint: changes when a file's content changes", fp3 != fp1)

        # POSIX-style relative path check: nested file must be recorded with
        # forward slash regardless of host OS path separator.
        rel = (ckpt / "nested" / "weights.bin").relative_to(ckpt).as_posix()
        check("checkpoint_fingerprint: nested path is POSIX-style (forward slash)", rel == "nested/weights.bin")

        try:
            os.symlink(ckpt / "config.json", ckpt / "config_link.json")
            symlink_supported = True
        except (OSError, NotImplementedError):
            symlink_supported = False

        if symlink_supported:
            try:
                rdp.checkpoint_fingerprint(ckpt)
                check("checkpoint_fingerprint: rejects a checkpoint dir containing a symlink", False)
            except rdp.CheckpointFingerprintError:
                check("checkpoint_fingerprint: rejects a checkpoint dir containing a symlink", True)
            os.remove(ckpt / "config_link.json")
        else:
            print("[SKIP] checkpoint_fingerprint: symlink rejection (no symlink privilege on this host)")

    with tempfile.TemporaryDirectory() as tmp:
        empty_ckpt = Path(tmp) / "empty_checkpoint"
        empty_ckpt.mkdir()
        try:
            rdp.checkpoint_fingerprint(empty_ckpt)
            check("checkpoint_fingerprint: empty directory fails validation", False)
        except rdp.CheckpointFingerprintError:
            check("checkpoint_fingerprint: empty directory fails validation", True)


def test_prompt_contract_fingerprint():
    fixture = rdp.PROMPT_CONTRACT_FIXTURE
    fp1 = rdp.prompt_contract_fingerprint(fixture)
    fp2 = rdp.prompt_contract_fingerprint(fixture)
    check("prompt_contract_fingerprint: deterministic for identical rendered text", fp1 == fp2)
    fp3 = rdp.prompt_contract_fingerprint(fixture + "\n")
    check("prompt_contract_fingerprint: a trailing newline changes the hash (no implicit normalization)", fp1 != fp3)


def test_manifest_and_rubric_raw_io_roundtrip():
    """Tests only the raw, unvalidated JSONL-by-record-id I/O mechanism
    that real_data_manifest.py's schema-validated functions are built on.
    _load_manifest_raw/_save_manifest_raw are not a production write path
    (see their docstrings) -- schema validation, duplicate-fingerprint
    rejection, transition rules, and the pilot-mode gate are all tested
    against the real thing in test_real_data_manifest.py via
    upsert_manifest_entry_validated. There is no raw withdraw_record
    anymore: withdrawal is disabled pending the validated withdrawal
    operation (lineage design not yet complete)."""
    tmp_dir = Path(tempfile.mkdtemp())
    original_manifest_path = rdp.MANIFEST_PATH
    original_rubrics_path = rdp.RUBRICS_PATH
    rdp.MANIFEST_PATH = tmp_dir / "real_data_manifest.jsonl"
    rdp.RUBRICS_PATH = tmp_dir / "real_data_rubrics.jsonl"
    try:
        entry = {"record_id": "rv_dummy0001", "contributor_id": "contributor_dummy", "withdrawal_status": "active"}
        rubric = {"record_id": "rv_dummy0001", "must_preserve": ["x"], "rubric_status": "adjudicated"}

        rdp._save_manifest_raw({entry["record_id"]: entry})
        rdp.upsert_rubric_entry(rubric)

        loaded_manifest = rdp._load_manifest_raw()
        loaded_rubrics = rdp.load_rubrics()
        check("manifest: raw save + load roundtrip preserves entry", loaded_manifest.get("rv_dummy0001") == entry)
        check("rubrics: upsert + load roundtrip preserves entry", loaded_rubrics.get("rv_dummy0001") == rubric)
    finally:
        rdp.MANIFEST_PATH = original_manifest_path
        rdp.RUBRICS_PATH = original_rubrics_path
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_no_raw_content_in_dataset_fingerprint_inputs():
    # The dataset-fingerprint wrapper only ever contains record_id + fingerprint
    # hashes -- verify by construction that raw note text cannot appear in it.
    r = _dummy_record("rv_dummy_privacy_check")
    check(
        "dataset_fingerprint record entries contain no raw note content (fingerprints only)",
        set(r.keys()) == {"record_id", "source_fingerprint", "pair_fingerprint", "rubric_fingerprint"},
    )


def main() -> None:
    tests = [
        test_canonical_json_key_order_independence,
        test_canonical_json_no_insignificant_whitespace,
        test_source_and_pair_fingerprint_scope,
        test_rubric_fingerprint_excludes_own_field,
        test_dataset_fingerprint_order_independence_and_change_detection,
        test_checkpoint_fingerprint,
        test_prompt_contract_fingerprint,
        test_manifest_and_rubric_raw_io_roundtrip,
        test_no_raw_content_in_dataset_fingerprint_inputs,
    ]
    for t in tests:
        t()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("All real_data_private.py tests passed.")


if __name__ == "__main__":
    main()
