"""Standalone assertion tests for real_data_manifest.py -- dummy data only,
no real notes. Run with `python test_real_data_manifest.py`. Exits 0 iff
every test passes. Deliberately has no torch/transformers dependency (see
test_duplicate_keys_in_source_record_fail, which replicates
evaluate_holdout.py's strict-parsing primitives directly rather than
importing that module, to keep this file fast and dependency-light).

Covers the 20 adversarial test groups required by
training/real_data_manifest_schema_decision.md's "Required adversarial
tests" section, plus the 9 additional groups from
training/phase_e_tier3_chatgpt_review.md's "Additional tests required"
(review test 10, the production holdout-invocation-without-a-seal check,
is exercised as a live CLI drill outside this file, not here). Each test
function's docstring names which group(s) it covers, so gaps are
traceable back to those lists.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

import real_data_manifest as rdm
import real_data_private as rdp

FAILURES = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


def _id(prefix: str, n: int) -> str:
    return f"{prefix}_{n:032x}"


RECORD = lambda n: _id("rv", n)
CONTRIB = lambda n: _id("contributor", n)
ACTOR = lambda n: _id("actor", n)

T0 = "2026-08-01T17:00:00Z"
T1 = "2026-08-01T17:10:00Z"
T2 = "2026-08-01T17:30:00Z"
T_BEFORE_T0 = "2026-07-01T00:00:00Z"


def _allowed_uses(**overrides) -> dict:
    base = {"private_annotation": True, "private_evaluation": True, "holdout_eligible": False, "training": False, "publication": False}
    base.update(overrides)
    return base


def consent_recorded_entry(n: int = 1, **overrides) -> dict:
    entry = {
        "manifest_schema_version": rdm.MANIFEST_SCHEMA_VERSION,
        "record_id": RECORD(n),
        "contributor_id": CONTRIB(1),
        "consent_version": "real-consent-v1",
        "consented_at_utc": T0,
        "author_confirmed": True,
        "consent_reviewer_id": ACTOR(9),
        "allowed_uses": _allowed_uses(),
        "source_kind": "author_supplied_personal_note",
        "split": None,
        "source_fingerprint": None,
        "pair_fingerprint": None,
        "rubric_fingerprint": None,
        "deidentification_status": "pending",
        "deidentified_at_utc": None,
        "deidentified_by_id": None,
        "deidentification_reviewer_id": None,
        "annotation_status": "not_started",
        "adjudicated_at_utc": None,
        "annotation_author_id": None,
        "annotation_reviewer_id": None,
        "withdrawal_status": "active",
        "withdrawal_status_changed_at_utc": T0,
    }
    entry.update(overrides)
    return entry


def deidentified_entry(n: int = 1, source_fp: str = "a" * 64, **overrides) -> dict:
    entry = consent_recorded_entry(n)
    entry.update(
        {
            "deidentification_status": "approved",
            "deidentified_at_utc": T1,
            "deidentified_by_id": ACTOR(1),
            "deidentification_reviewer_id": ACTOR(2),
            "source_fingerprint": f"sha256:{source_fp}",
        }
    )
    entry.update(overrides)
    return entry


def adjudicated_entry(n: int = 1, source_fp: str = "a" * 64, pair_fp: str = "b" * 64, rubric_fp: str = "c" * 64, **overrides) -> dict:
    entry = deidentified_entry(n, source_fp=source_fp)
    entry.update(
        {
            "annotation_status": "adjudicated",
            "adjudicated_at_utc": T2,
            "annotation_author_id": ACTOR(3),
            "annotation_reviewer_id": ACTOR(4),
            "pair_fingerprint": f"sha256:{pair_fp}",
            "rubric_fingerprint": f"sha256:{rubric_fp}",
        }
    )
    entry.update(overrides)
    return entry


def evaluation_ready_entry(
    n: int = 1, split: str = "real_validation", source_fp: str = "a" * 64, pair_fp: str = "b" * 64, rubric_fp: str = "c" * 64, **overrides
) -> dict:
    entry = adjudicated_entry(n, source_fp=source_fp, pair_fp=pair_fp, rubric_fp=rubric_fp)
    entry["split"] = split
    if split == "real_holdout":
        entry["allowed_uses"] = _allowed_uses(holdout_eligible=True)
    entry.update(overrides)
    return entry


def _expect_manifest_error(fn, *args, **kwargs) -> str | None:
    try:
        fn(*args, **kwargs)
        return None
    except rdm.ManifestValidationError as e:
        return str(e)


def _expect_eligibility_error(fn, *args, **kwargs) -> str | None:
    try:
        fn(*args, **kwargs)
        return None
    except rdm.EligibilityError as e:
        return str(e)


# --- Group 1: each lifecycle stage validates on its own terms ---


def test_lifecycle_stages_validate():
    """Group 1."""
    for label, entry in [
        ("consent_recorded", consent_recorded_entry()),
        ("deidentified", deidentified_entry()),
        ("adjudicated", adjudicated_entry()),
        ("evaluation_ready_validation", evaluation_ready_entry(split="real_validation")),
        ("evaluation_ready_holdout", evaluation_ready_entry(split="real_holdout")),
    ]:
        err = _expect_manifest_error(rdm.validate_entry, entry)
        check(f"validate_entry: valid {label} entry passes", err is None, err)


# --- Group 2: missing/extra/misspelled/duplicate keys ---


def test_field_set_violations():
    """Group 2 (missing/extra/misspelled fields; duplicate keys covered in test_strict_loader)."""
    base = adjudicated_entry()

    missing = {k: v for k, v in base.items() if k != "consent_version"}
    check("validate_entry: missing required field fails", _expect_manifest_error(rdm.validate_entry, missing) is not None)

    extra = {**base, "unexpected_field": "x"}
    check("validate_entry: unknown extra field fails", _expect_manifest_error(rdm.validate_entry, extra) is not None)

    misspelled = {k if k != "record_id" else "record_ib": v for k, v in base.items()}
    check("validate_entry: misspelled required field fails", _expect_manifest_error(rdm.validate_entry, misspelled) is not None)


# --- Group 3: duplicate record IDs rejected before dict construction ---


def test_strict_loader():
    """Groups 2 (duplicate keys, blank lines, non-object records) and 3 (duplicate record_id)."""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        dup_id_path = tmp_dir / "dup_id.jsonl"
        e1 = consent_recorded_entry(1)
        e2 = consent_recorded_entry(1)  # same record_id
        import json

        dup_id_path.write_text(json.dumps(e1) + "\n" + json.dumps(e2) + "\n", encoding="utf-8")
        err = _expect_manifest_error(rdm.load_manifest_strict, dup_id_path)
        check("load_manifest_strict: duplicate record_id rejected", err is not None and "duplicate record_id" in err, err)

        dup_key_path = tmp_dir / "dup_key.jsonl"
        dup_key_line = '{"record_id": "rv_' + "0" * 32 + '", "record_id": "rv_' + "1" * 32 + '", "manifest_schema_version": "real-manifest-v1"}'
        dup_key_path.write_text(dup_key_line + "\n", encoding="utf-8")
        err = _expect_manifest_error(rdm.load_manifest_strict, dup_key_path)
        check("load_manifest_strict: duplicate key inside one JSON object rejected", err is not None, err)

        blank_path = tmp_dir / "blank.jsonl"
        blank_path.write_text(json.dumps(consent_recorded_entry(2)) + "\n\n", encoding="utf-8")
        err = _expect_manifest_error(rdm.load_manifest_strict, blank_path)
        check("load_manifest_strict: blank line rejected", err is not None, err)

        non_object_path = tmp_dir / "non_object.jsonl"
        non_object_path.write_text('"just a string"\n', encoding="utf-8")
        err = _expect_manifest_error(rdm.load_manifest_strict, non_object_path)
        check("load_manifest_strict: non-object record rejected", err is not None, err)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# --- Group 4: duplicate source fingerprints, including inactive rows ---


def test_duplicate_source_fingerprint_rejected_including_inactive():
    """Group 4."""
    shared_fp = "d" * 64
    active1 = evaluation_ready_entry(1, source_fp=shared_fp)
    active2 = evaluation_ready_entry(2, source_fp=shared_fp)
    err = _expect_manifest_error(rdm.validate_manifest_collection, {active1["record_id"]: active1, active2["record_id"]: active2})
    check("validate_manifest_collection: duplicate source_fingerprint fails for two active rows", err is not None, err)

    withdrawn = {**active2, "withdrawal_status": "withdrawn"}
    err = _expect_manifest_error(rdm.validate_manifest_collection, {active1["record_id"]: active1, withdrawn["record_id"]: withdrawn})
    check("validate_manifest_collection: duplicate source_fingerprint still fails when one row is withdrawn", err is not None, err)

    expired = {**active2, "withdrawal_status": "expired"}
    err = _expect_manifest_error(rdm.validate_manifest_collection, {active1["record_id"]: active1, expired["record_id"]: expired})
    check("validate_manifest_collection: duplicate source_fingerprint still fails when one row is expired", err is not None, err)

    distinct = evaluation_ready_entry(3, source_fp="e" * 64)
    err = _expect_manifest_error(rdm.validate_manifest_collection, {active1["record_id"]: active1, distinct["record_id"]: distinct})
    check("validate_manifest_collection: distinct source_fingerprints across rows pass", err is None, err)


# --- Group 5: malformed fingerprints ---


def test_malformed_fingerprints():
    """Group 5."""
    cases = {
        "unprefixed": "a" * 64,
        "uppercase": "A" * 64,
        "too_short": "a" * 63,
        "too_long": "a" * 65,
        "non_hex": "g" * 64,
    }
    for label, bad in cases.items():
        entry = deidentified_entry(source_fp=None)
        entry["source_fingerprint"] = bad if label == "unprefixed" else f"sha256:{bad}"
        err = _expect_manifest_error(rdm.validate_entry, entry)
        check(f"validate_entry: malformed fingerprint ({label}) rejected", err is not None, err)


# --- Group 6: non-boolean substitutes for booleans ---


def test_non_boolean_substitutes_rejected():
    """Group 6."""
    for bad in ("true", 1, 0, "yes"):
        entry = adjudicated_entry()
        entry["author_confirmed"] = bad
        err = _expect_manifest_error(rdm.validate_entry, entry)
        check(f"validate_entry: author_confirmed={bad!r} (non-bool) rejected", err is not None, err)

    for bad in ("false", 0, "true"):
        entry = adjudicated_entry()
        entry["allowed_uses"] = {**entry["allowed_uses"], "training": bad}
        err = _expect_manifest_error(rdm.validate_entry, entry)
        check(f"validate_entry: allowed_uses.training={bad!r} (non-bool) rejected", err is not None, err)


# --- Group 7: eligibility -- authorship, permissions ---


def test_eligibility_authorship_and_permissions():
    """Group 7."""
    ready = evaluation_ready_entry(split="real_validation")

    unconfirmed = {**ready, "author_confirmed": False}
    err = _expect_eligibility_error(rdm.check_evaluation_eligibility, unconfirmed, expected_split="real_validation")
    check("check_evaluation_eligibility: author_confirmed=False fails", err is not None, err)

    no_eval_perm = {**ready, "allowed_uses": {**ready["allowed_uses"], "private_evaluation": False}}
    err = _expect_eligibility_error(rdm.check_evaluation_eligibility, no_eval_perm, expected_split="real_validation")
    check("check_evaluation_eligibility: missing private_evaluation permission fails", err is not None, err)

    malformed_perms = {**ready, "allowed_uses": None}
    err = _expect_eligibility_error(rdm.check_evaluation_eligibility, malformed_perms, expected_split="real_validation")
    check("check_evaluation_eligibility: malformed allowed_uses fails", err is not None, err)

    unsafe_training = {**ready, "allowed_uses": {**ready["allowed_uses"], "training": True}}
    err = _expect_eligibility_error(rdm.check_evaluation_eligibility, unsafe_training, expected_split="real_validation")
    check("check_evaluation_eligibility: training=True (unsafe permission) fails", err is not None, err)


# --- Group 8: de-identification gating and independence ---


def test_deidentification_gating_and_independence():
    """Group 8."""
    pending = consent_recorded_entry()
    err = _expect_eligibility_error(rdm.check_evaluation_eligibility, pending, expected_split="real_validation")
    check("check_evaluation_eligibility: pending de-identification fails", err is not None, err)

    rejected = deidentified_entry(deidentification_status="rejected", deidentified_at_utc=T1, deidentified_by_id=ACTOR(1), deidentification_reviewer_id=ACTOR(2), source_fingerprint=None)
    err = _expect_eligibility_error(rdm.check_evaluation_eligibility, rejected, expected_split="real_validation")
    check("check_evaluation_eligibility: rejected de-identification fails", err is not None, err)

    non_independent = deidentified_entry(deidentified_by_id=ACTOR(5), deidentification_reviewer_id=ACTOR(5))
    err = _expect_manifest_error(rdm.validate_entry, non_independent)
    check("validate_entry: non-independent de-identification review (same actor) rejected", err is not None, err)


# --- Group 9: annotation gating and independence ---


def test_annotation_gating_and_independence():
    """Group 9."""
    not_started = deidentified_entry()
    err = _expect_eligibility_error(rdm.check_evaluation_eligibility, not_started, expected_split="real_validation")
    check("check_evaluation_eligibility: not_started annotation fails", err is not None, err)

    excluded = deidentified_entry(annotation_status="excluded", annotation_author_id=ACTOR(3))
    err = _expect_eligibility_error(rdm.check_evaluation_eligibility, excluded, expected_split="real_validation")
    check("check_evaluation_eligibility: excluded annotation fails", err is not None, err)

    non_independent = adjudicated_entry(annotation_author_id=ACTOR(7), annotation_reviewer_id=ACTOR(7))
    err = _expect_manifest_error(rdm.validate_entry, non_independent)
    check("validate_entry: non-independent annotation review (same actor) rejected", err is not None, err)


# --- Group 10: timestamp validity and chronology ---


def test_timestamp_validity_and_chronology():
    """Group 10."""
    not_a_string = adjudicated_entry(consented_at_utc=12345)
    check("validate_entry: non-string consented_at_utc rejected", _expect_manifest_error(rdm.validate_entry, not_a_string) is not None)

    bad_format = adjudicated_entry(consented_at_utc="not-a-timestamp")
    check("validate_entry: malformed timestamp string rejected", _expect_manifest_error(rdm.validate_entry, bad_format) is not None)

    non_utc = adjudicated_entry(consented_at_utc="2026-08-01T17:00:00+05:00")
    check("validate_entry: non-UTC offset timestamp rejected", _expect_manifest_error(rdm.validate_entry, non_utc) is not None)

    impossible = adjudicated_entry(consented_at_utc=T2, deidentified_at_utc=T_BEFORE_T0)
    err = _expect_manifest_error(rdm.validate_entry, impossible)
    check("validate_entry: deidentified_at_utc before consented_at_utc (chronologically impossible) rejected", err is not None, err)


# --- Group 11: split mismatch and reassignment ---


def test_split_mismatch_and_reassignment():
    """Group 11."""
    ready = evaluation_ready_entry(split="real_validation")
    err = _expect_eligibility_error(rdm.check_evaluation_eligibility, ready, expected_split="real_holdout")
    check("check_evaluation_eligibility: split mismatch (validation entry used for holdout) fails", err is not None, err)

    reassigned = {**ready, "allowed_uses": _allowed_uses(holdout_eligible=True), "split": "real_holdout"}
    err = _expect_manifest_error(rdm.validate_transition, ready, reassigned)
    check("validate_transition: split reassignment (validation -> holdout) fails", err is not None, err)


# --- Group 12: holdout assignment without holdout permission ---


def test_holdout_assignment_without_permission():
    """Group 12."""
    bad = evaluation_ready_entry(split="real_holdout")
    bad["allowed_uses"] = _allowed_uses(holdout_eligible=False)
    err = _expect_manifest_error(rdm.validate_entry, bad)
    check("validate_entry: split='real_holdout' without holdout_eligible permission rejected", err is not None, err)


# --- Group 13: holdout assignment during the validation-only pilot ---


def test_holdout_forbidden_during_pilot():
    """Group 13."""
    holdout_entry = evaluation_ready_entry(split="real_holdout")
    err = _expect_manifest_error(rdm.validate_manifest_collection, {holdout_entry["record_id"]: holdout_entry}, pilot_mode=True)
    check("validate_manifest_collection: holdout split rejected during pilot (pilot_mode=True)", err is not None, err)

    eligible_but_unassigned = adjudicated_entry(1)
    eligible_but_unassigned["allowed_uses"] = _allowed_uses(holdout_eligible=True)
    err = _expect_manifest_error(rdm.validate_manifest_collection, {eligible_but_unassigned["record_id"]: eligible_but_unassigned}, pilot_mode=True)
    check("validate_manifest_collection: holdout_eligible=True rejected during pilot even without split assignment", err is not None, err)

    err = _expect_manifest_error(rdm.validate_manifest_collection, {holdout_entry["record_id"]: holdout_entry}, pilot_mode=False)
    check("validate_manifest_collection: holdout split permitted when pilot_mode=False (explicit opt-out)", err is None, err)


# --- Group 14: withdrawn/expired rows fail eligibility and cannot reactivate ---


def test_withdrawal_terminal():
    """Group 14."""
    ready = evaluation_ready_entry(split="real_validation")
    withdrawn = {**ready, "withdrawal_status": "withdrawn"}
    err = _expect_eligibility_error(rdm.check_evaluation_eligibility, withdrawn, expected_split="real_validation")
    check("check_evaluation_eligibility: withdrawn record fails eligibility", err is not None, err)

    expired = {**ready, "withdrawal_status": "expired"}
    err = _expect_eligibility_error(rdm.check_evaluation_eligibility, expired, expected_split="real_validation")
    check("check_evaluation_eligibility: expired record fails eligibility", err is not None, err)

    reactivated = {**withdrawn, "withdrawal_status": "active"}
    err = _expect_manifest_error(rdm.validate_transition, withdrawn, reactivated)
    check("validate_transition: withdrawn -> active reactivation rejected", err is not None, err)


# --- Group 15: source/pair/rubric mismatch detected independently ---


def test_fingerprint_mismatch_detected_independently():
    """Group 15."""
    entry = evaluation_ready_entry(split="real_holdout", source_fp="1" * 64, pair_fp="2" * 64, rubric_fp="3" * 64)

    def expect_mismatch(computed, declared, field):
        try:
            rdm.verify_fingerprint(computed=computed, declared=declared, field_name=field, record_id=entry["record_id"])
            return False
        except rdm.FingerprintMismatchError:
            return True

    check("verify_fingerprint: source mismatch detected", expect_mismatch("9" * 64, entry["source_fingerprint"], "source_fingerprint"))
    check("verify_fingerprint: pair mismatch detected", expect_mismatch("9" * 64, entry["pair_fingerprint"], "pair_fingerprint"))
    check("verify_fingerprint: rubric mismatch detected", expect_mismatch("9" * 64, entry["rubric_fingerprint"], "rubric_fingerprint"))
    check(
        "verify_fingerprint: matching value raises nothing",
        not expect_mismatch(entry["source_fingerprint"].removeprefix("sha256:"), entry["source_fingerprint"], "source_fingerprint"),
    )


# --- Groups 16-17: editing output/rubric changes the relevant recomputed fingerprint ---


def test_edited_output_and_rubric_change_fingerprints():
    """Groups 16, 17."""
    inp = "TESTDUMMY holdout note about the blue folder"
    out = {"narrative": "Review the blue folder.", "bullets": ["Review the blue folder"], "action_items": ["Review the blue folder"]}
    rubric = {"record_id": "rv_dummy", "must_preserve": ["blue folder"]}

    original_pfp = rdp.pair_fingerprint(inp, out)
    edited_out = {**out, "bullets": ["Review the blue folder tomorrow"]}
    edited_pfp = rdp.pair_fingerprint(inp, edited_out)
    check("editing only output changes the recomputed pair_fingerprint", original_pfp != edited_pfp)

    original_rfp = rdp.rubric_fingerprint(rubric)
    edited_rubric = {**rubric, "must_preserve": ["blue folder", "tomorrow"]}
    edited_rfp = rdp.rubric_fingerprint(edited_rubric)
    check("editing only the rubric changes the recomputed rubric_fingerprint", original_rfp != edited_rfp)

    r1 = {"record_id": "rv_a", "source_fingerprint": rdp.source_fingerprint(inp), "pair_fingerprint": original_pfp, "rubric_fingerprint": original_rfp}
    r1_edited = {**r1, "rubric_fingerprint": edited_rfp}
    ds_fp1 = rdp.dataset_fingerprint([r1], "real_validation")
    ds_fp2 = rdp.dataset_fingerprint([r1_edited], "real_validation")
    check("editing only the rubric changes the dataset_fingerprint", ds_fp1 != ds_fp2)


# --- Group 19: invalid updates leave prior manifest bytes unchanged ---


def test_invalid_update_leaves_manifest_bytes_unchanged():
    """Group 19."""
    tmp_dir = Path(tempfile.mkdtemp())
    original_manifest_path = rdp.MANIFEST_PATH
    rdp.MANIFEST_PATH = tmp_dir / "real_data_manifest.jsonl"
    try:
        good = evaluation_ready_entry(1, source_fp="7" * 64)
        rdm.upsert_manifest_entry_validated(good, pilot_mode=True)
        bytes_before = rdp.MANIFEST_PATH.read_bytes()

        conflicting = evaluation_ready_entry(2, source_fp="7" * 64)  # duplicate source_fingerprint
        raised = False
        try:
            rdm.upsert_manifest_entry_validated(conflicting, pilot_mode=True)
        except rdm.ManifestValidationError:
            raised = True
        check("upsert_manifest_entry_validated: invalid update (duplicate source_fingerprint) raises", raised)

        bytes_after = rdp.MANIFEST_PATH.read_bytes()
        check("upsert_manifest_entry_validated: prior manifest bytes unchanged after a rejected update", bytes_before == bytes_after)

        leftover_tmp_files = list(tmp_dir.glob("*.tmp"))
        check("upsert_manifest_entry_validated: no leftover temp files after a rejected update", leftover_tmp_files == [], str(leftover_tmp_files))
    finally:
        rdp.MANIFEST_PATH = original_manifest_path
        shutil.rmtree(tmp_dir, ignore_errors=True)


# --- Group 20: manifest metadata never reaches the model-facing prompt ---


def test_manifest_metadata_absent_from_prompt():
    """Group 20."""
    import prepare_data

    entry = evaluation_ready_entry(1)
    prompt = prepare_data.build_prompt("TESTDUMMY unrelated note content, nothing to do with the manifest")
    leaked = [
        field
        for field in (entry["record_id"], entry["contributor_id"], entry["consent_reviewer_id"], entry["source_fingerprint"], entry["pair_fingerprint"], entry["rubric_fingerprint"])
        if field in prompt
    ]
    check("build_prompt output contains no manifest record_id/contributor_id/reviewer/fingerprint values", leaked == [], str(leaked))


# --- Additional tests from training/phase_e_tier3_chatgpt_review.md ---


def test_private_annotation_permission_required_for_eligibility():
    """Review test 1: private_annotation:false fails eligibility even
    when every other field is evaluation-ready."""
    ready = evaluation_ready_entry(split="real_validation")
    no_annotation_perm = {**ready, "allowed_uses": {**ready["allowed_uses"], "private_annotation": False}}
    err = _expect_eligibility_error(rdm.check_evaluation_eligibility, no_annotation_perm, expected_split="real_validation")
    check("check_evaluation_eligibility: private_annotation=False fails despite every other field being ready", err is not None, err)


def test_every_pre_adjudicated_status_rejects_final_only_fields():
    """Review test 2: draft/in_review/excluded all reject adjudicated_at_utc,
    annotation_reviewer_id, pair_fingerprint, and rubric_fingerprint."""
    for status in ("draft", "in_review", "excluded"):
        base = deidentified_entry(annotation_status=status, annotation_author_id=ACTOR(3))
        for field, bad_value in (
            ("adjudicated_at_utc", T2),
            ("annotation_reviewer_id", ACTOR(4)),
            ("pair_fingerprint", f"sha256:{'b' * 64}"),
            ("rubric_fingerprint", f"sha256:{'c' * 64}"),
        ):
            tainted = {**base, field: bad_value}
            err = _expect_manifest_error(rdm.validate_entry, tainted)
            check(f"validate_entry: annotation_status={status!r} with final field {field}={bad_value!r} set rejected", err is not None, err)


def test_adjudication_before_deidentification_chronology():
    """Review test 3: adjudicated_at_utc before deidentified_at_utc fails,
    even when deidentification_status is legitimately 'approved'."""
    impossible = adjudicated_entry(deidentified_at_utc=T2, adjudicated_at_utc=T1)
    err = _expect_manifest_error(rdm.validate_entry, impossible)
    check("validate_entry: adjudicated_at_utc before deidentified_at_utc rejected", err is not None, err)


def test_withdrawal_timestamp_before_completed_processing_fails():
    """Review test 4: withdrawal_status_changed_at_utc before de-identification
    or adjudication fails once the record is actually withdrawn/expired --
    but not while it's merely still active (that field just reflects
    consent time until an actual withdrawal event happens)."""
    still_active = evaluation_ready_entry(split="real_validation")
    err = _expect_manifest_error(rdm.validate_entry, still_active)
    check("validate_entry: withdrawal_status_changed_at_utc == consented_at_utc is fine while still active", err is None, err)

    withdrawn_too_early = {**still_active, "withdrawal_status": "withdrawn", "withdrawal_status_changed_at_utc": T0}
    err = _expect_manifest_error(rdm.validate_entry, withdrawn_too_early)
    check("validate_entry: withdrawal_status_changed_at_utc before adjudicated_at_utc fails once actually withdrawn", err is not None, err)

    withdrawn_ok = {**still_active, "withdrawal_status": "withdrawn", "withdrawal_status_changed_at_utc": "2026-08-01T18:00:00Z"}
    err = _expect_manifest_error(rdm.validate_entry, withdrawn_ok)
    check("validate_entry: withdrawal_status_changed_at_utc after adjudicated_at_utc passes when actually withdrawn", err is None, err)


def test_production_write_path_rejects_pilot_forbidden_entry():
    """Review test 5: the one production write path
    (upsert_manifest_entry_validated) cannot persist a pilot-forbidden
    entry, and the unsafe legacy helpers no longer exist to bypass it."""
    check("real_data_private: upsert_manifest_entry no longer exists (removed, not just deprecated)", not hasattr(rdp, "upsert_manifest_entry"))
    check("real_data_private: withdraw_record no longer exists (removed, not just deprecated)", not hasattr(rdp, "withdraw_record"))
    check("real_data_private: load_manifest no longer exists as a public name", not hasattr(rdp, "load_manifest"))
    check("real_data_private: save_manifest no longer exists as a public name", not hasattr(rdp, "save_manifest"))

    tmp_dir = Path(tempfile.mkdtemp())
    original_manifest_path = rdp.MANIFEST_PATH
    rdp.MANIFEST_PATH = tmp_dir / "real_data_manifest.jsonl"
    try:
        forbidden = evaluation_ready_entry(split="real_holdout", source_fp="f" * 64)
        raised = False
        try:
            rdm.upsert_manifest_entry_validated(forbidden, pilot_mode=True)
        except rdm.ManifestValidationError:
            raised = True
        check("upsert_manifest_entry_validated: pilot-forbidden holdout entry raises under pilot_mode=True", raised)
        check("upsert_manifest_entry_validated: rejected pilot-forbidden entry left no manifest file behind", not rdp.MANIFEST_PATH.exists())
    finally:
        rdp.MANIFEST_PATH = original_manifest_path
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_strict_rubric_loader():
    """Review test 6: duplicate rubric record_ids and duplicate rubric
    object keys both fail, and a non-adjudicated rubric_status fails too."""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        dup_id_path = tmp_dir / "dup_id_rubrics.jsonl"
        r1 = {"record_id": RECORD(1), "must_preserve": ["x"], "rubric_status": "adjudicated"}
        r2 = {"record_id": RECORD(1), "must_preserve": ["y"], "rubric_status": "adjudicated"}
        dup_id_path.write_text(json.dumps(r1) + "\n" + json.dumps(r2) + "\n", encoding="utf-8")
        err = _expect_manifest_error(rdm.load_rubrics_strict, dup_id_path)
        check("load_rubrics_strict: duplicate record_id rejected", err is not None and "duplicate record_id" in err, err)

        dup_key_path = tmp_dir / "dup_key_rubrics.jsonl"
        dup_key_line = '{"record_id": "' + RECORD(2) + '", "record_id": "' + RECORD(3) + '", "rubric_status": "adjudicated"}'
        dup_key_path.write_text(dup_key_line + "\n", encoding="utf-8")
        err = _expect_manifest_error(rdm.load_rubrics_strict, dup_key_path)
        check("load_rubrics_strict: duplicate key inside one rubric object rejected", err is not None, err)

        not_adjudicated_path = tmp_dir / "draft_rubric.jsonl"
        draft = {"record_id": RECORD(4), "must_preserve": ["z"], "rubric_status": "draft"}
        not_adjudicated_path.write_text(json.dumps(draft) + "\n", encoding="utf-8")
        err = _expect_manifest_error(rdm.load_rubrics_strict, not_adjudicated_path)
        check("load_rubrics_strict: non-adjudicated rubric_status rejected", err is not None, err)

        good_path = tmp_dir / "good_rubrics.jsonl"
        good = {"record_id": RECORD(5), "must_preserve": ["ok"], "rubric_status": "adjudicated"}
        good_path.write_text(json.dumps(good) + "\n", encoding="utf-8")
        loaded = rdm.load_rubrics_strict(good_path)
        check("load_rubrics_strict: a well-formed adjudicated rubric loads cleanly", loaded.get(RECORD(5)) == good)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_duplicate_keys_in_source_record_fail():
    """Review test 7: duplicate JSON keys in a real source record fail
    before fingerprinting. Exercises the exact primitives
    evaluate_holdout._load_holdout_source_strict uses
    (rdm.reject_duplicate_keys as the object_pairs_hook, then
    prepare_data.validate_record) directly, so this file doesn't need to
    import evaluate_holdout.py's torch/transformers dependencies."""
    import prepare_data

    dup_key_line = '{"input": "TESTDUMMY a", "input": "TESTDUMMY b", "output": {"narrative": "x", "bullets": [], "action_items": []}}'
    raised = False
    try:
        json.loads(dup_key_line, object_pairs_hook=rdm.reject_duplicate_keys)
    except rdm.DuplicateJSONKeyError:
        raised = True
    check("reject_duplicate_keys: duplicate 'input' key in a source record raises before validate_record/fingerprinting ever runs", raised)

    clean_line = '{"input": "TESTDUMMY clean", "output": {"narrative": "x", "bullets": [], "action_items": []}}'
    parsed = json.loads(clean_line, object_pairs_hook=rdm.reject_duplicate_keys)
    validated = prepare_data.validate_record(parsed, "test.jsonl", 1)
    check("reject_duplicate_keys: a clean source record still parses and validates normally", validated["_input"] == "TESTDUMMY clean")


def test_pair_rubric_edit_before_assignment_requires_reset():
    """Review test 8: a direct adjudicated-fingerprint-A -> adjudicated-
    fingerprint-B swap is rejected pre-assignment, but the two-step reset
    path (adjudicated -> pre-adjudicated null state -> re-adjudicated with
    a new fingerprint) is explicitly permitted."""
    original = adjudicated_entry(pair_fp="1" * 64, rubric_fp="2" * 64)
    direct_swap = {**original, "pair_fingerprint": f"sha256:{'9' * 64}"}
    err = _expect_manifest_error(rdm.validate_transition, original, direct_swap)
    check("validate_transition: direct adjudicated pair_fingerprint swap (no reset) rejected pre-assignment", err is not None, err)

    reset_state = {
        **original,
        "annotation_status": "draft",
        "adjudicated_at_utc": None,
        "annotation_reviewer_id": None,
        "pair_fingerprint": None,
        "rubric_fingerprint": None,
    }
    err = _expect_manifest_error(rdm.validate_transition, original, reset_state)
    check("validate_transition: resetting adjudicated -> draft with nulled final fingerprints is permitted", err is None, err)

    re_adjudicated = adjudicated_entry(pair_fp="9" * 64, rubric_fp="2" * 64)
    err = _expect_manifest_error(rdm.validate_transition, reset_state, re_adjudicated)
    check("validate_transition: re-adjudicating from the reset state with a new pair_fingerprint is permitted", err is None, err)


def test_pair_rubric_source_edit_after_assignment_fails():
    """Review test 9: source/pair/rubric fingerprints are all immutable
    in place once a split is assigned."""
    assigned = evaluation_ready_entry(split="real_validation", source_fp="a" * 64, pair_fp="b" * 64, rubric_fp="c" * 64)
    for field in ("source_fingerprint", "pair_fingerprint", "rubric_fingerprint"):
        tampered = {**assigned, field: f"sha256:{'9' * 64}"}
        err = _expect_manifest_error(rdm.validate_transition, assigned, tampered)
        check(f"validate_transition: {field} change after split assignment rejected", err is not None, err)


def test_approved_seal_declaration_always_fails_today():
    """Review test 10 (unit half -- the live CLI-ordering half is a
    separate drill outside this file): load_approved_seal has no seal
    format or storage mechanism yet, so it must always fail closed
    regardless of milestone name."""
    for milestone in ("dummy_milestone", "anything_at_all"):
        raised = False
        try:
            rdm.load_approved_seal(milestone)
        except rdm.SealNotApprovedError:
            raised = True
        check(f"load_approved_seal({milestone!r}): always fails closed (no seal mechanism exists yet)", raised)


def main() -> None:
    tests = [
        test_lifecycle_stages_validate,
        test_field_set_violations,
        test_strict_loader,
        test_duplicate_source_fingerprint_rejected_including_inactive,
        test_malformed_fingerprints,
        test_non_boolean_substitutes_rejected,
        test_eligibility_authorship_and_permissions,
        test_deidentification_gating_and_independence,
        test_annotation_gating_and_independence,
        test_timestamp_validity_and_chronology,
        test_split_mismatch_and_reassignment,
        test_holdout_assignment_without_permission,
        test_holdout_forbidden_during_pilot,
        test_withdrawal_terminal,
        test_fingerprint_mismatch_detected_independently,
        test_edited_output_and_rubric_change_fingerprints,
        test_invalid_update_leaves_manifest_bytes_unchanged,
        test_manifest_metadata_absent_from_prompt,
        test_private_annotation_permission_required_for_eligibility,
        test_every_pre_adjudicated_status_rejects_final_only_fields,
        test_adjudication_before_deidentification_chronology,
        test_withdrawal_timestamp_before_completed_processing_fails,
        test_production_write_path_rejects_pilot_forbidden_entry,
        test_strict_rubric_loader,
        test_duplicate_keys_in_source_record_fail,
        test_pair_rubric_edit_before_assignment_requires_reset,
        test_pair_rubric_source_edit_after_assignment_fails,
        test_approved_seal_declaration_always_fails_today,
    ]
    for t in tests:
        t()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("All real_data_manifest.py tests passed.")


if __name__ == "__main__":
    main()
