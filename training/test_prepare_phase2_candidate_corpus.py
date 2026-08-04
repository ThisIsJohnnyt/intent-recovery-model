"""Standalone assertion tests for prepare_phase2_candidate_corpus.py --
dummy data only, except where explicitly noted as a live check against the
real repository. No pytest dependency: run directly with
`python test_prepare_phase2_candidate_corpus.py`, matching this repo's
existing script-based tooling convention.

Covers every fail-closed condition listed in
prepare_phase2_candidate_corpus.py's own module docstring, plus positive
checks against the real, pinned parent corpus and proposal.

Revised 2026-08-04 per ChatGPT's review: added genuine byte-level tests
(LF/CRLF drift, terminal-newline drift, blank-line drift) for the
byte-preservation and validation-identity checks, which the prior text-
line-based tests could not exercise; added negative tests for pinned-
fingerprint drift and a missing pinned file; added negative tests for
benchmark-file record-count drift; added negative tests for
build_candidate's parser-failure and round-trip-mismatch paths.
"""
import copy
import json
import sys
import tempfile
from pathlib import Path

import prepare_phase2_candidate_corpus as p
import prompt_contract_v2_parser
from prepare_data import input_hash
from prompt_contract_v2_parser import ParseError, ParsedOutput

FAILURES = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


def expect_system_exit(fn, *args, **kwargs) -> str | None:
    try:
        fn(*args, **kwargs)
    except SystemExit as e:
        return str(e)
    return None


def make_parent_record(text: str, output: dict, difficulty: str = "medium", category: str = "test_category") -> dict:
    return {
        "input": text,
        "output": output,
        "difficulty": difficulty,
        "category": category,
        "v1_target": "dummy-v1-target",
        "v2_target": "dummy-v2-target",
    }


def make_proposal_record(text: str, output: dict, difficulty: str = "hard", category: str = "simple_list") -> dict:
    return {"input": text, "output": output, "difficulty": difficulty, "category": category}


OUT_A = {"narrative": "a", "bullets": ["a"], "action_items": []}
OUT_B = {"narrative": "b", "bullets": ["b"], "action_items": []}
OUT_P = {"narrative": "p", "bullets": ["p"], "action_items": []}

PARENT_A = make_parent_record("parent record A", OUT_A)
PARENT_B = make_parent_record("parent record B", OUT_B)
PROPOSAL_P = make_proposal_record("proposal record P", OUT_P)


# ---------------------------------------------------------------------------
# validate_proposal_schema
# ---------------------------------------------------------------------------

print("=== validate_proposal_schema ===")

good = [make_proposal_record("x", {"narrative": "n", "bullets": ["b"], "action_items": ["a"]})]
msg = expect_system_exit(p.validate_proposal_schema, good)
check("valid proposal record passes", msg is None, detail=str(msg))

missing_key = [{"input": "x", "output": OUT_P, "difficulty": "hard"}]  # no 'category'
msg = expect_system_exit(p.validate_proposal_schema, missing_key)
check("missing top-level key fails closed", msg is not None)

extra_key = [{**make_proposal_record("x", OUT_P), "extra_field": "unexpected"}]
msg = expect_system_exit(p.validate_proposal_schema, extra_key)
check("extra top-level key fails closed", msg is not None)

bad_output_keys = [{**make_proposal_record("x", OUT_P), "output": {"narrative": "n", "bullets": []}}]  # missing action_items
msg = expect_system_exit(p.validate_proposal_schema, bad_output_keys)
check("missing output key fails closed", msg is not None)

wrong_type = [{**make_proposal_record("x", OUT_P), "output": {"narrative": "n", "bullets": "not-a-list", "action_items": []}}]
msg = expect_system_exit(p.validate_proposal_schema, wrong_type)
check("wrong field type fails closed", msg is not None)

forbidden_category = [make_proposal_record("x", OUT_P, category=p.FORBIDDEN_CATEGORY)]
msg = expect_system_exit(p.validate_proposal_schema, forbidden_category)
check("forbidden 'high_count_task_retention' category fails closed", msg is not None)

empty_string_field = [make_proposal_record("x", OUT_P, difficulty="")]
msg = expect_system_exit(p.validate_proposal_schema, empty_string_field)
check("empty-string difficulty fails closed", msg is not None)


# ---------------------------------------------------------------------------
# verify_counts
# ---------------------------------------------------------------------------

print("\n=== verify_counts ===")

right_parent = [PARENT_A] * p.EXPECTED_PARENT_COUNT
right_proposal = [PROPOSAL_P] * p.EXPECTED_PROPOSAL_COUNT
msg = expect_system_exit(p.verify_counts, right_parent, right_proposal)
check("exact expected counts pass", msg is None, detail=str(msg))

msg = expect_system_exit(p.verify_counts, right_parent[:-1], right_proposal)
check("parent count off by one fails closed", msg is not None)

msg = expect_system_exit(p.verify_counts, right_parent, right_proposal + [PROPOSAL_P])
check("proposal count off by one fails closed", msg is not None)


# ---------------------------------------------------------------------------
# verify_no_duplicate_or_colliding_inputs
# ---------------------------------------------------------------------------

print("\n=== verify_no_duplicate_or_colliding_inputs ===")

parent2 = [PARENT_A, PARENT_B]
proposal2 = [PROPOSAL_P, make_proposal_record("proposal record Q", OUT_P)]
bench_hashes = {input_hash("some benchmark input")}

result = None
try:
    result = p.verify_no_duplicate_or_colliding_inputs(parent2, proposal2, bench_hashes)
except SystemExit as e:
    result = str(e)
check("clean, non-colliding inputs pass", isinstance(result, tuple), detail=str(result))

dup_within_parent = [PARENT_A, PARENT_A]
msg = expect_system_exit(p.verify_no_duplicate_or_colliding_inputs, dup_within_parent, proposal2, bench_hashes)
check("duplicate input within parent fails closed", msg is not None)

dup_within_proposal = [PROPOSAL_P, PROPOSAL_P]
msg = expect_system_exit(p.verify_no_duplicate_or_colliding_inputs, parent2, dup_within_proposal, bench_hashes)
check("duplicate input within proposal fails closed", msg is not None)

collide_with_parent = [make_proposal_record(PARENT_A["input"], OUT_P)]
msg = expect_system_exit(p.verify_no_duplicate_or_colliding_inputs, parent2, collide_with_parent, bench_hashes)
check("proposal input colliding with parent fails closed", msg is not None)

bench_input = "a benchmark case's exact input text"
collide_with_bench = [make_proposal_record(bench_input, OUT_P)]
msg = expect_system_exit(
    p.verify_no_duplicate_or_colliding_inputs, parent2, collide_with_bench, {input_hash(bench_input)}
)
check("proposal input colliding with a benchmark case fails closed", msg is not None)


# ---------------------------------------------------------------------------
# verify_parent_preserved_byte_for_byte -- genuine bytes, per ChatGPT's
# 2026-08-04 finding that the original list-of-decoded-lines version could
# not detect CRLF/LF drift, terminal-newline drift, or blank-line drift.
# Every case below is a byte-level construction, not text lines.
# ---------------------------------------------------------------------------

print("\n=== verify_parent_preserved_byte_for_byte (bytes) ===")

parent_bytes = b'{"input": "a"}\n{"input": "b"}\n'

msg = expect_system_exit(p.verify_parent_preserved_byte_for_byte, parent_bytes, parent_bytes + b'{"input": "c"}\n')
check("identical byte prefix passes", msg is None, detail=str(msg))

altered_byte = b'{"input": "a"}\n{"input": "B-ALTERED"}\n{"input": "c"}\n'
msg = expect_system_exit(p.verify_parent_preserved_byte_for_byte, parent_bytes, altered_byte)
check("single altered byte within the prefix fails closed", msg is not None)

# LF/CRLF drift: same logical two lines, but the second line's terminator
# is CRLF instead of the parent's LF -- must be caught, unlike the old
# splitlines()-based version which would have silently normalized this.
crlf_drift = b'{"input": "a"}\n{"input": "b"}\r\n{"input": "c"}\n'
msg = expect_system_exit(p.verify_parent_preserved_byte_for_byte, parent_bytes, crlf_drift)
check("LF-vs-CRLF terminator drift fails closed", msg is not None)

# Terminal-newline drift: candidate's corresponding region is missing the
# parent's own trailing newline byte.
no_trailing_newline = b'{"input": "a"}\n{"input": "b"}'  # exactly len(parent_bytes)-1, no final \n
msg = expect_system_exit(p.verify_parent_preserved_byte_for_byte, parent_bytes, no_trailing_newline)
check("terminal-newline drift fails closed", msg is not None)

# Blank-line drift: an extra blank line inserted inside what should be the
# byte-identical prefix region.
blank_line_drift = b'{"input": "a"}\n\n{"input": "b"}\n'
msg = expect_system_exit(p.verify_parent_preserved_byte_for_byte, parent_bytes, blank_line_drift)
check("inserted blank-line drift fails closed", msg is not None)

# Re-serialization drift (e.g. whitespace changes) must also be caught.
whitespace_drift = b'{"input": "a"}\n{"input":  "b"}\n'
msg = expect_system_exit(p.verify_parent_preserved_byte_for_byte, parent_bytes, whitespace_drift)
check("whitespace-only re-serialization drift fails closed", msg is not None)


# ---------------------------------------------------------------------------
# verify_val_byte_identical_to_existing -- genuine bytes, both positive and
# negative (the original version had no dedicated test at all).
# ---------------------------------------------------------------------------

print("\n=== verify_val_byte_identical_to_existing (bytes) ===")

with tempfile.TemporaryDirectory() as tmp:
    fake_val_path = Path(tmp) / "val.jsonl"
    fake_val_bytes = b'{"prompt": "p1", "target": "t1"}\r\n{"prompt": "p2", "target": "t2"}\r\n'
    fake_val_path.write_bytes(fake_val_bytes)

    _orig_existing_val_path = p.EXISTING_R2_VAL_PATH
    p.EXISTING_R2_VAL_PATH = fake_val_path
    try:
        result = None
        try:
            result = p.verify_val_byte_identical_to_existing(fake_val_bytes, 2)
        except SystemExit as e:
            result = str(e)
        check("byte-identical val split passes", isinstance(result, dict), detail=str(result))

        msg = expect_system_exit(p.verify_val_byte_identical_to_existing, fake_val_bytes + b"extra", 2)
        check("val split byte mismatch fails closed", msg is not None)

        msg = expect_system_exit(p.verify_val_byte_identical_to_existing, fake_val_bytes.replace(b"\r\n", b"\n"), 2)
        check("val split CRLF-vs-LF drift fails closed", msg is not None)

        p.EXISTING_R2_VAL_PATH = Path(tmp) / "does_not_exist.jsonl"
        msg = expect_system_exit(p.verify_val_byte_identical_to_existing, fake_val_bytes, 2)
        check("missing existing val file fails closed", msg is not None)
    finally:
        p.EXISTING_R2_VAL_PATH = _orig_existing_val_path


# ---------------------------------------------------------------------------
# verify_pinned_fingerprints -- negative tests for fingerprint drift and a
# missing file, on top of the existing live "current files verify clean"
# check further down. Patches an EXPECTED_* constant (not the file itself)
# so the real pinned files are never touched.
# ---------------------------------------------------------------------------

print("\n=== verify_pinned_fingerprints (drift) ===")

_orig_expected_parent_fp = p.EXPECTED_PARENT_FINGERPRINT
p.EXPECTED_PARENT_FINGERPRINT = "0" * 64
try:
    msg = expect_system_exit(p.verify_pinned_fingerprints)
    check("parent fingerprint drift fails closed", msg is not None)
finally:
    p.EXPECTED_PARENT_FINGERPRINT = _orig_expected_parent_fp

_orig_protected_probes_path = p.PROTECTED_PROBES_PATH
p.PROTECTED_PROBES_PATH = Path(tempfile.gettempdir()) / "definitely_does_not_exist_phase2_test.jsonl"
try:
    msg = expect_system_exit(p.verify_pinned_fingerprints)
    check("missing pinned file fails closed", msg is not None)
finally:
    p.PROTECTED_PROBES_PATH = _orig_protected_probes_path


# ---------------------------------------------------------------------------
# load_benchmark_input_hashes -- negative tests for benchmark-file drift
# (wrong count) per ChatGPT's 2026-08-04 finding that this dependency was
# previously unpinned and uncounted.
# ---------------------------------------------------------------------------

print("\n=== load_benchmark_input_hashes (drift/count) ===")

with tempfile.TemporaryDirectory() as tmp:
    short_protected = Path(tmp) / "short_protected.jsonl"
    short_protected.write_text('\n'.join(json.dumps({"input": f"p{i}"}) for i in range(5)) + '\n', encoding="utf-8")

    _orig_protected_path = p.PROTECTED_PROBES_PATH
    p.PROTECTED_PROBES_PATH = short_protected
    try:
        msg = expect_system_exit(p.load_benchmark_input_hashes)
        check("protected benchmark wrong count fails closed", msg is not None)
    finally:
        p.PROTECTED_PROBES_PATH = _orig_protected_path

    short_acceptance = Path(tmp) / "short_acceptance.jsonl"
    short_acceptance.write_text('\n'.join(json.dumps({"input": f"a{i}"}) for i in range(3)) + '\n', encoding="utf-8")

    _orig_acceptance_path = p.ACCEPTANCE_PROBES_PATH
    p.ACCEPTANCE_PROBES_PATH = short_acceptance
    try:
        msg = expect_system_exit(p.load_benchmark_input_hashes)
        check("acceptance benchmark wrong count fails closed", msg is not None)
    finally:
        p.ACCEPTANCE_PROBES_PATH = _orig_acceptance_path

msg = expect_system_exit(p.load_benchmark_input_hashes)
check("real, correctly-counted benchmark files load cleanly", msg is None, detail=str(msg))


# ---------------------------------------------------------------------------
# verify_proposal_appended_in_order
# ---------------------------------------------------------------------------

print("\n=== verify_proposal_appended_in_order ===")

parent_stub = [make_parent_record(f"parent {i}", OUT_A) for i in range(p.EXPECTED_PARENT_COUNT)]
prop_x = make_proposal_record("proposal x", OUT_P)
prop_y = make_proposal_record("proposal y", OUT_P)
prop_hashes_in_order = [input_hash(prop_x["input"]), input_hash(prop_y["input"])]

# Build a fake 78-slot candidate (66 parent stand-ins + our 2 test proposals,
# padded to the expected proposal count so length checks inside the function
# don't trip on unrelated arithmetic -- only order/hash matters here).
padding = [make_parent_record(f"pad {i}", OUT_A, category="pad") for i in range(p.EXPECTED_PROPOSAL_COUNT - 2)]
candidate_in_order = parent_stub + [
    {**prop_x, "v1_target": "x1", "v2_target": "x2"},
    {**prop_y, "v1_target": "y1", "v2_target": "y2"},
] + padding
full_hashes_in_order = prop_hashes_in_order + [input_hash(r["input"]) for r in padding]

msg = expect_system_exit(p.verify_proposal_appended_in_order, full_hashes_in_order, candidate_in_order)
check("correctly-ordered appended records pass", msg is None, detail=str(msg))

candidate_reordered = parent_stub + [
    {**prop_y, "v1_target": "y1", "v2_target": "y2"},
    {**prop_x, "v1_target": "x1", "v2_target": "x2"},
] + padding
msg = expect_system_exit(p.verify_proposal_appended_in_order, full_hashes_in_order, candidate_reordered)
check("reordered appended records fail closed", msg is not None)


# ---------------------------------------------------------------------------
# ensure_output_paths_available
# ---------------------------------------------------------------------------

print("\n=== ensure_output_paths_available ===")

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)
    fresh_dir = tmp_path / "does_not_exist_yet"
    orig_paths = (p.OUTPUT_CORPUS_PATH, p.OUTPUT_REPORT_PATH, p.OUTPUT_COMPARISON_PATH, p.OUTPUT_SPLIT_COMPARISON_PATH)
    p.OUTPUT_CORPUS_PATH = tmp_path / "corpus.jsonl"
    p.OUTPUT_REPORT_PATH = tmp_path / "report.md"
    p.OUTPUT_COMPARISON_PATH = tmp_path / "comparison.json"
    p.OUTPUT_SPLIT_COMPARISON_PATH = tmp_path / "split.json"
    try:
        msg = expect_system_exit(p.ensure_output_paths_available, fresh_dir)
        check("all-fresh output paths pass", msg is None, detail=str(msg))

        p.OUTPUT_CORPUS_PATH.write_text("already here", encoding="utf-8")
        msg = expect_system_exit(p.ensure_output_paths_available, fresh_dir)
        check("pre-existing output file fails closed", msg is not None)
    finally:
        (p.OUTPUT_CORPUS_PATH, p.OUTPUT_REPORT_PATH, p.OUTPUT_COMPARISON_PATH, p.OUTPUT_SPLIT_COMPARISON_PATH) = orig_paths

    fresh_dir.mkdir()
    msg = expect_system_exit(p.ensure_output_paths_available, fresh_dir)
    check("pre-existing output dir fails closed", msg is not None)


# ---------------------------------------------------------------------------
# build_candidate: real target generation + parse-verification (uses the
# real prompt_contract_v2_migrate/parser modules, not reimplemented logic)
# ---------------------------------------------------------------------------

print("\n=== build_candidate (real target generation, dummy records) ===")

real_parent = [make_parent_record(f"parent input {i}", {"narrative": f"n{i}", "bullets": [f"b{i}"], "action_items": []}) for i in range(3)]
real_proposal = [
    make_proposal_record("A clean two-bullet one-action input.", {
        "narrative": "A clean two-bullet one-action input.",
        "bullets": ["First supported idea.", "Second supported idea."],
        "action_items": ["Do the one supported task."],
    })
]
candidate, generated = p.build_candidate(real_parent, real_proposal)
check("build_candidate returns parent count + proposal count", len(candidate) == len(real_parent) + len(real_proposal))
check("generated v2_target list matches proposal count", len(generated) == len(real_proposal))
check("appended record has non-empty v1_target/v2_target", bool(candidate[-1]["v1_target"]) and bool(candidate[-1]["v2_target"]))
check("parent records untouched by build_candidate", candidate[:3] == real_parent)

# Parser/round-trip failure paths -- ChatGPT's 2026-08-04 finding that
# these fail-closed branches (ParseError raised, or a parsed result that
# doesn't match the authored output) had no negative test. parse_output
# is monkeypatched, not reimplemented, so this exercises build_candidate's
# own error handling rather than the real parser's internals.
_orig_parse_output = p.parse_output

p.parse_output = lambda decoded_text: (_ for _ in ()).throw(ParseError("simulated parse failure"))
try:
    msg = expect_system_exit(p.build_candidate, real_parent, real_proposal)
    check("build_candidate fails closed on ParseError", msg is not None)
finally:
    p.parse_output = _orig_parse_output

p.parse_output = lambda decoded_text: ParsedOutput(narrative="WRONG", bullets=["wrong"], actions=[])
try:
    msg = expect_system_exit(p.build_candidate, real_parent, real_proposal)
    check("build_candidate fails closed on round-trip mismatch", msg is not None)
finally:
    p.parse_output = _orig_parse_output


# ---------------------------------------------------------------------------
# Live checks against the real, pinned repository files
# ---------------------------------------------------------------------------

print("\n=== live checks against real pinned files ===")

msg = expect_system_exit(p.verify_pinned_fingerprints)
check("real pinned fingerprints (parent/proposal/split-manifest/both benchmarks) verify clean", msg is None, detail=str(msg))

real_parent_records = p.load_jsonl_records(p.PARENT_PATH)
check("real parent corpus has exactly 66 records", len(real_parent_records) == p.EXPECTED_PARENT_COUNT)

real_proposal_records = p.load_jsonl_records(p.PROPOSAL_PATH)
check("real proposal has exactly 12 records", len(real_proposal_records) == p.EXPECTED_PROPOSAL_COUNT)

msg = expect_system_exit(p.validate_proposal_schema, real_proposal_records)
check("real proposal passes schema validation", msg is None, detail=str(msg))

real_categories = {r["category"] for r in real_proposal_records}
check("real proposal never uses the forbidden category", p.FORBIDDEN_CATEGORY not in real_categories)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print(f"\n{'='*60}")
if FAILURES:
    print(f"{len(FAILURES)} check(s) FAILED: {FAILURES}")
    sys.exit(1)
else:
    print("All checks passed.")
