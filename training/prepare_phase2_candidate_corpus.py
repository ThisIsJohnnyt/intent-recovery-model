"""Derives the Phase-2 balanced-curriculum candidate corpus and its v2
train/val split from the pinned, reviewed R2 parent corpus and the pinned,
reviewed 12-example Phase-2 proposal.

Authorized by Johnny 2026-08-04, scope exactly as ChatGPT proposed and
Claude restated back for confirmation: build this derivation script and
tests; pin the 66-record parent and reviewed 12-record proposal by
SHA-256; preserve all 66 parent records byte-for-byte and in order;
append the 12 proposal records in reviewed order using input hashes as
stable identities; fail closed on drift, duplicates, schema errors,
altered parent records, unexpected order, or unexpected counts; produce
exactly 78 candidate records; produce a 72-train/6-validation split
(original 60 train plus the 12 proposals, with the original 6-record
validation split staying byte-identical and ordered); exclude Gold v1.2.3
and all 26 benchmark cases; emit fingerprints, a derivation report, a
parent-vs-candidate comparison, and a split comparison. Everything this
script writes is left uncommitted for joint review. Does NOT perform
training, inference, benchmark execution, seed 73, export, or deployment.

Revised 2026-08-04 per ChatGPT's review of the first run: (1) byte
preservation and validation-split identity are now checked via genuine
read_bytes() comparison, not decoded/splitlines()-normalized text, which
could not detect CRLF/LF drift, terminal-newline drift, or blank-line
drift; the candidate's parent-prefix is now the parent file's own raw
bytes used unmodified, and val.jsonl is a direct byte copy of the
existing R2 val split rather than a reconstruction. (2) The 26-benchmark
collision check's two source files are now pinned by SHA-256 alongside
the other three inputs, with their 16/10 record counts explicitly
asserted, rather than trusting whatever currently exists at those paths.

Usage:
    python prepare_phase2_candidate_corpus.py [--output-dir DIR]
"""
import argparse
import hashlib
import json
from pathlib import Path

from prepare_data import SPLIT_MANIFEST_PATH, input_hash, load_val_hashes
import prompt_contract_v2_candidate as v2_candidate
from prompt_contract_v2_migrate import build_v1_target, build_v2_target
from prompt_contract_v2_parser import ParseError, parse_output

TRAINING_DIR = Path(__file__).parent
REPO_ROOT = TRAINING_DIR.parent

PARENT_PATH = TRAINING_DIR / "gold_v1.2.2_r2_derived_candidate.jsonl"
PROPOSAL_PATH = TRAINING_DIR / "phase2_balanced_curriculum_proposal.jsonl"
EXISTING_R2_VAL_PATH = TRAINING_DIR / "data" / "processed_gold_v1.2.2_r2_v2contract_seed17" / "val.jsonl"
PROTECTED_PROBES_PATH = REPO_ROOT / "datasets" / "benchmark" / "gold_v1.2.1_probes.jsonl"
ACCEPTANCE_PROBES_PATH = REPO_ROOT / "datasets" / "benchmark" / "source_determined_items_v2_acceptance_draft.jsonl"

OUTPUT_CORPUS_PATH = TRAINING_DIR / "gold_v1.2.2_phase2_derived_candidate.jsonl"
OUTPUT_REPORT_PATH = TRAINING_DIR / "gold_v1.2.2_phase2_corpus_derivation_report.md"
OUTPUT_COMPARISON_PATH = TRAINING_DIR / "gold_v1.2.2_phase2_original_vs_candidate_diff.json"
OUTPUT_SPLIT_COMPARISON_PATH = TRAINING_DIR / "gold_v1.2.2_phase2_split_comparison.json"
DEFAULT_OUTPUT_DATA_DIR = TRAINING_DIR / "data" / "processed_gold_v1.2.2_phase2_v2contract_seed17"

EXPECTED_PARENT_FINGERPRINT = "197adb3578b27c8b76bdbb33b3dcb35398ccd980932f0f718a5fedd732b9c1ac"
EXPECTED_PROPOSAL_FINGERPRINT = "1f32f38d0288837eb439105bfe38d0e221b5c20f0f99de3e5ca9dbc5e79e0620"
EXPECTED_SPLIT_MANIFEST_FINGERPRINT = "24610be8c5b91be13b064acaaab4f8bbae59b0ec175e66d1fb8ccb94cd049485"
# Pinned per ChatGPT's finding (2026-08-04): the 26-benchmark collision
# check previously read whatever currently existed at these two paths,
# unpinned and uncounted -- a changed or shortened benchmark file could
# have silently weakened the guard while the report still claimed all 26
# frozen cases were checked. Both fingerprints recomputed fresh against
# the real files, not copied from an older doc.
EXPECTED_PROTECTED_PROBES_FINGERPRINT = "044708641c8dd584f334f16bde21ed89550bb7c464160827433f825eb0c48e94"
EXPECTED_ACCEPTANCE_PROBES_FINGERPRINT = "b8fe4d4178e5b508757db998eacb1ee979518697c8df759ba1739227c88d448e"

EXPECTED_PARENT_COUNT = 66
EXPECTED_PROPOSAL_COUNT = 12
EXPECTED_CANDIDATE_COUNT = 78
EXPECTED_PROTECTED_COUNT = 16
EXPECTED_ACCEPTANCE_COUNT = 10

# The exact 12 reviewed labels, in the proposal file's own line order --
# used only for human-readable reporting; the mechanism that actually
# governs identity and order throughout this script is input-hash and
# file position, never these labels.
PROPOSAL_LABELS_IN_FILE_ORDER = [f"P2-{n:03d}" for n in range(1, 13)]

PROPOSAL_RECORD_KEYS = {"input", "output", "difficulty", "category"}
PROPOSAL_OUTPUT_KEYS = {"narrative", "bullets", "action_items"}
FORBIDDEN_CATEGORY = "high_count_task_retention"


def file_fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load_raw_lines(path: Path) -> list[str]:
    """Decoded, logical JSON lines -- used only for *loading records*
    (load_jsonl_records below), never for proving byte identity.
    `str.splitlines()` normalizes away CRLF/LF differences, terminal-
    newline presence, and blank lines, so it cannot be used as evidence of
    byte-for-byte preservation -- that's what detect_line_terminator() /
    read_bytes() comparisons below are for (finding from ChatGPT's review,
    2026-08-04: the original version of this function was used for both
    purposes, which let "byte-identical" claims go unverified as bytes)."""
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_jsonl_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in load_raw_lines(path)]


def detect_line_terminator(data: bytes) -> bytes:
    return b"\r\n" if b"\r\n" in data else b"\n"


def verify_pinned_fingerprints() -> None:
    checks = [
        (PARENT_PATH, EXPECTED_PARENT_FINGERPRINT, "R2 parent corpus (66 records)"),
        (PROPOSAL_PATH, EXPECTED_PROPOSAL_FINGERPRINT, "reviewed Phase-2 proposal (12 records)"),
        (SPLIT_MANIFEST_PATH, EXPECTED_SPLIT_MANIFEST_FINGERPRINT, "frozen split manifest"),
        (PROTECTED_PROBES_PATH, EXPECTED_PROTECTED_PROBES_FINGERPRINT, "protected-16 benchmark"),
        (ACCEPTANCE_PROBES_PATH, EXPECTED_ACCEPTANCE_PROBES_FINGERPRINT, "acceptance-10 benchmark"),
    ]
    for path, expected, label in checks:
        if not path.exists():
            raise SystemExit(f"Missing required file for {label}: {path}")
        actual = file_fingerprint(path)
        if actual != expected:
            raise SystemExit(
                f"FATAL: fingerprint drift for {label} ({path.name}): expected {expected}, got "
                f"{actual}. Refusing to proceed against an unpinned or altered input."
            )
        print(f"[fingerprint OK] {label}: {actual}")


def validate_proposal_schema(proposal: list[dict]) -> None:
    """Fails closed on any structural drift from the exact schema this
    proposal was reviewed against -- extra/missing top-level or output
    keys, wrong field types, or the explicitly-rejected
    high_count_task_retention category reappearing under any name."""
    errors = []
    for i, rec in enumerate(proposal):
        keys = set(rec)
        if keys != PROPOSAL_RECORD_KEYS:
            errors.append(f"record {i}: top-level keys {sorted(keys)} != expected {sorted(PROPOSAL_RECORD_KEYS)}")
            continue
        if not isinstance(rec["input"], str) or not rec["input"].strip():
            errors.append(f"record {i}: 'input' is not a non-empty string")
        if not isinstance(rec["difficulty"], str) or not rec["difficulty"]:
            errors.append(f"record {i}: 'difficulty' is not a non-empty string")
        if not isinstance(rec["category"], str) or not rec["category"]:
            errors.append(f"record {i}: 'category' is not a non-empty string")
        elif rec["category"] == FORBIDDEN_CATEGORY:
            errors.append(f"record {i}: category is the explicitly-rejected '{FORBIDDEN_CATEGORY}'")
        out = rec.get("output")
        if not isinstance(out, dict) or set(out) != PROPOSAL_OUTPUT_KEYS:
            errors.append(f"record {i}: 'output' keys {sorted(out) if isinstance(out, dict) else out!r} != expected {sorted(PROPOSAL_OUTPUT_KEYS)}")
            continue
        if not isinstance(out["narrative"], str) or not out["narrative"].strip():
            errors.append(f"record {i}: output.narrative is not a non-empty string")
        for field in ("bullets", "action_items"):
            val = out[field]
            if not isinstance(val, list) or not all(isinstance(x, str) and x.strip() for x in val):
                errors.append(f"record {i}: output.{field} is not a list of non-empty strings")
    if errors:
        raise SystemExit("FATAL: proposal schema validation failed:\n  " + "\n  ".join(errors))
    print(f"[schema OK] all {len(proposal)} proposal record(s) match the exact reviewed schema; no '{FORBIDDEN_CATEGORY}' category present.")


def verify_counts(parent: list[dict], proposal: list[dict]) -> None:
    if len(parent) != EXPECTED_PARENT_COUNT:
        raise SystemExit(f"FATAL: parent corpus has {len(parent)} records, expected exactly {EXPECTED_PARENT_COUNT}.")
    if len(proposal) != EXPECTED_PROPOSAL_COUNT:
        raise SystemExit(f"FATAL: proposal has {len(proposal)} records, expected exactly {EXPECTED_PROPOSAL_COUNT}.")
    print(f"[count OK] parent={len(parent)}, proposal={len(proposal)}")


def verify_no_duplicate_or_colliding_inputs(
    parent: list[dict], proposal: list[dict], benchmark_hashes: set[str]
) -> tuple[list[str], list[str]]:
    """Fails closed on: a duplicate input within the parent, within the
    proposal, a proposal input colliding with an existing parent input
    (would silently merge two training examples), or a proposal input
    colliding with any of the 26 frozen benchmark cases (would leak
    evaluation content into training -- the active, run-time half of
    benchmark isolation; the design-time half was already checked by hand
    and by n-gram sweep in the static review)."""
    parent_hashes = [input_hash(r["input"]) for r in parent]
    if len(set(parent_hashes)) != len(parent_hashes):
        raise SystemExit("FATAL: duplicate input hash within the parent corpus.")

    proposal_hashes = [input_hash(r["input"]) for r in proposal]
    if len(set(proposal_hashes)) != len(proposal_hashes):
        raise SystemExit("FATAL: duplicate input hash within the proposal.")

    collide_parent = set(proposal_hashes) & set(parent_hashes)
    if collide_parent:
        raise SystemExit(f"FATAL: {len(collide_parent)} proposal input(s) collide with an existing parent input: {sorted(collide_parent)}")

    collide_bench = set(proposal_hashes) & benchmark_hashes
    if collide_bench:
        raise SystemExit(f"FATAL: {len(collide_bench)} proposal input(s) collide with a frozen benchmark case: {sorted(collide_bench)}")

    print(f"[identity OK] no duplicates within parent, within proposal, or against parent/benchmark inputs.")
    return parent_hashes, proposal_hashes


def load_benchmark_input_hashes() -> set[str]:
    """Fingerprints of both source files are verified by
    verify_pinned_fingerprints() before this is called; this function
    additionally asserts the exact expected record counts, so a benchmark
    file that somehow drifted in content but not in this run's cached
    fingerprint check (or was swapped for a same-hash-checked-elsewhere
    copy with a different count due to caller error) still fails closed
    rather than silently checking against fewer than 26 cases."""
    protected = load_jsonl_records(PROTECTED_PROBES_PATH)
    if len(protected) != EXPECTED_PROTECTED_COUNT:
        raise SystemExit(
            f"FATAL: protected benchmark has {len(protected)} record(s), expected exactly "
            f"{EXPECTED_PROTECTED_COUNT}. Refusing to run the collision check against an incomplete set."
        )
    acceptance = load_jsonl_records(ACCEPTANCE_PROBES_PATH)
    if len(acceptance) != EXPECTED_ACCEPTANCE_COUNT:
        raise SystemExit(
            f"FATAL: acceptance benchmark has {len(acceptance)} record(s), expected exactly "
            f"{EXPECTED_ACCEPTANCE_COUNT}. Refusing to run the collision check against an incomplete set."
        )
    hashes = {input_hash(r["input"]) for r in protected} | {input_hash(r["input"]) for r in acceptance}
    print(
        f"[benchmark isolation] loaded {len(protected)} protected + {len(acceptance)} acceptance = "
        f"{len(protected) + len(acceptance)} pinned, count-verified input hash(es) for the active collision check."
    )
    return hashes


def build_candidate(parent: list[dict], proposal: list[dict]) -> tuple[list[dict], list[str]]:
    """Builds the 78-record candidate: the 66 parent records completely
    untouched (not even re-serialized -- appended by reference), then the
    12 proposal records in file order with v1_target/v2_target mechanically
    generated and parse-verified, never hand-authored."""
    generated_targets: list[str] = []
    proposal_entries = []
    for i, rec in enumerate(proposal):
        narrative = rec["output"]["narrative"]
        bullets = rec["output"]["bullets"]
        actions = rec["output"]["action_items"]

        v1_target = build_v1_target(narrative, bullets, actions)
        v2_target = build_v2_target(narrative, bullets, actions)

        try:
            parsed = parse_output(v2_target)
        except ParseError as e:
            raise SystemExit(f"FATAL: proposal record {i} ({PROPOSAL_LABELS_IN_FILE_ORDER[i]}) v2_target does not parse: {e}")
        if parsed.narrative != narrative.strip() or parsed.bullets != bullets or parsed.actions != actions:
            raise SystemExit(f"FATAL: proposal record {i} ({PROPOSAL_LABELS_IN_FILE_ORDER[i]}) regenerated v2_target does not round-trip to the authored output.")

        entry = {
            "input": rec["input"],
            "output": rec["output"],
            "difficulty": rec["difficulty"],
            "category": rec["category"],
            "v1_target": v1_target,
            "v2_target": v2_target,
        }
        proposal_entries.append(entry)
        generated_targets.append(v2_target)

    print(f"[targets OK] generated and parse-verified v1_target/v2_target for all {len(proposal_entries)} proposal record(s).")
    candidate = list(parent) + proposal_entries
    return candidate, generated_targets


def verify_parent_preserved_byte_for_byte(parent_bytes: bytes, candidate_bytes: bytes) -> None:
    """Genuine byte comparison (fixes ChatGPT's 2026-08-04 finding): reads
    both files as raw bytes via read_bytes(), never decodes or splits
    into text lines first, so CRLF/LF drift, terminal-newline drift, and
    blank-line drift are all caught -- none of them can hide behind
    str.splitlines()'s normalization the way the original line-based
    version allowed."""
    prefix = candidate_bytes[: len(parent_bytes)]
    if prefix != parent_bytes:
        diff_at = next(
            (i for i in range(min(len(prefix), len(parent_bytes))) if prefix[i] != parent_bytes[i]),
            min(len(prefix), len(parent_bytes)),
        )
        raise SystemExit(
            f"FATAL: candidate's first {len(parent_bytes)} byte(s) are not byte-identical to the parent "
            f"corpus. First differing byte at offset {diff_at} (candidate prefix is {len(prefix)} byte(s), "
            f"parent is {len(parent_bytes)} byte(s))."
        )
    print(
        f"[byte-preservation OK] candidate's first {len(parent_bytes)} byte(s) are byte-identical to the "
        "parent corpus, verified via read_bytes() (not decoded/split text lines)."
    )


def verify_proposal_appended_in_order(proposal_hashes: list[str], candidate: list[dict]) -> None:
    appended = candidate[EXPECTED_PARENT_COUNT:]
    if len(appended) != EXPECTED_PROPOSAL_COUNT:
        raise SystemExit(f"FATAL: expected {EXPECTED_PROPOSAL_COUNT} appended record(s), found {len(appended)}.")
    appended_hashes = [input_hash(r["input"]) for r in appended]
    if appended_hashes != proposal_hashes:
        raise SystemExit("FATAL: appended records are not in the proposal file's own order (by input hash).")
    print(f"[order OK] all {len(appended)} proposal record(s) appended in exact reviewed file order.")


def build_split(candidate: list[dict], val_hashes: set[str]) -> tuple[list[dict], list[dict]]:
    train_pairs: list[dict] = []
    val_pairs: list[dict] = []
    for rec in candidate:
        h = input_hash(rec["input"])
        pair = {"prompt": v2_candidate.build_prompt(rec["input"]), "target": rec["v2_target"]}
        (val_pairs if h in val_hashes else train_pairs).append(pair)
    return train_pairs, val_pairs


def verify_val_byte_identical_to_existing(written_val_bytes: bytes, val_count: int) -> dict:
    """Genuine byte comparison (fixes ChatGPT's 2026-08-04 finding), and
    verified against what was actually written to disk -- val.jsonl is
    written as a direct byte-for-byte copy of the existing R2 val split
    (see main()), so this check confirms the copy is exact rather than
    trusting the copy step implicitly."""
    if not EXISTING_R2_VAL_PATH.exists():
        raise SystemExit(f"FATAL: cannot compare -- existing R2 val split not found at {EXISTING_R2_VAL_PATH}")
    existing_bytes = EXISTING_R2_VAL_PATH.read_bytes()
    identical = existing_bytes == written_val_bytes
    if not identical:
        raise SystemExit(
            "FATAL: newly-written val split is not byte-identical to the existing "
            f"{EXISTING_R2_VAL_PATH}. Refusing to proceed -- validation must stay frozen."
        )
    print(f"[val byte-identity OK] {val_count} validation record(s) byte-identical to the existing R2 val split, verified via read_bytes().")
    return {"val_count": val_count, "byte_identical_to_existing_r2_val": identical}


def canonical_training_data_fingerprint(records: list[dict]) -> str:
    sortable = sorted(records, key=lambda r: r["prompt"])
    blob = json.dumps(sortable, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def ensure_output_paths_available(output_data_dir: Path) -> None:
    for p in (OUTPUT_CORPUS_PATH, OUTPUT_REPORT_PATH, OUTPUT_COMPARISON_PATH, OUTPUT_SPLIT_COMPARISON_PATH, output_data_dir):
        if p.exists():
            raise SystemExit(f"FATAL: output path already exists, refusing to overwrite: {p}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=str, default=None, help="Overrides the default candidate train/val data output dir")
    args = parser.parse_args()
    output_data_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DATA_DIR

    ensure_output_paths_available(output_data_dir)

    print("=== Step 1: pinned fingerprint verification ===")
    verify_pinned_fingerprints()

    print("\n=== Step 2: load parent + proposal, count + schema checks ===")
    parent = load_jsonl_records(PARENT_PATH)
    proposal = load_jsonl_records(PROPOSAL_PATH)
    verify_counts(parent, proposal)
    validate_proposal_schema(proposal)
    print(
        "Gold v1.2.3 exclusion: structural, not scanned -- both source files are pinned above to "
        "their known content and neither ever reads datasets/synthetic.jsonl."
    )

    print("\n=== Step 3: identity checks (duplicates, parent/benchmark collisions) ===")
    benchmark_hashes = load_benchmark_input_hashes()
    parent_hashes, proposal_hashes = verify_no_duplicate_or_colliding_inputs(parent, proposal, benchmark_hashes)

    print("\n=== Step 4: build candidate (66 parent + 12 proposal, targets generated + parse-verified) ===")
    candidate, generated_targets = build_candidate(parent, proposal)
    if len(candidate) != EXPECTED_CANDIDATE_COUNT:
        raise SystemExit(f"FATAL: candidate has {len(candidate)} records, expected exactly {EXPECTED_CANDIDATE_COUNT}.")
    print(f"[count OK] candidate={len(candidate)}")

    print("\n=== Step 5: split derivation (frozen val membership; 12 proposals appended to train) ===")
    val_hashes = load_val_hashes(SPLIT_MANIFEST_PATH)
    train_pairs, val_pairs = build_split(candidate, val_hashes)
    if len(train_pairs) != 72:
        raise SystemExit(f"FATAL: train split has {len(train_pairs)} records, expected exactly 72.")
    if len(val_pairs) != 6:
        raise SystemExit(f"FATAL: val split has {len(val_pairs)} records, expected exactly 6.")
    print(f"[split count OK] train={len(train_pairs)}, val={len(val_pairs)}")

    print("\n=== Step 6: write exclusive candidate + split artifacts (genuine byte operations) ===")
    # The candidate's parent-prefix is the parent file's own raw bytes,
    # used completely unmodified -- never reconstructed via json.dumps,
    # which would only be *semantically* equivalent, not byte-identical.
    parent_bytes = PARENT_PATH.read_bytes()
    terminator = detect_line_terminator(parent_bytes)
    parent_prefix = parent_bytes if parent_bytes.endswith(terminator) else parent_bytes + terminator
    appended_bytes = b"".join(
        json.dumps(r, ensure_ascii=False).encode("utf-8") + terminator for r in candidate[EXPECTED_PARENT_COUNT:]
    )
    OUTPUT_CORPUS_PATH.write_bytes(parent_prefix + appended_bytes)
    print(f"{OUTPUT_CORPUS_PATH.name}: {len(candidate)} records")

    verify_parent_preserved_byte_for_byte(parent_bytes, OUTPUT_CORPUS_PATH.read_bytes())
    verify_proposal_appended_in_order(proposal_hashes, load_jsonl_records(OUTPUT_CORPUS_PATH))

    output_data_dir.mkdir(parents=True, exist_ok=False)

    # val.jsonl is not reconstructed at all -- it is the existing R2 val
    # split's own bytes, copied verbatim, since no proposal record can
    # ever belong to val by construction. This makes "byte-identical to
    # the existing split" true by direct copy, not by hoping a
    # re-serialization happens to match; the check below still actively
    # confirms it against what's actually on disk.
    existing_val_bytes = EXISTING_R2_VAL_PATH.read_bytes()
    (output_data_dir / "val.jsonl").write_bytes(existing_val_bytes)
    val_comparison = verify_val_byte_identical_to_existing((output_data_dir / "val.jsonl").read_bytes(), len(val_pairs))
    print(f"{output_data_dir / 'val.jsonl'}: {len(val_pairs)} examples (byte-copied from the existing R2 split)")

    train_terminator = detect_line_terminator(existing_val_bytes)
    train_bytes = b"".join(
        json.dumps(p, ensure_ascii=False).encode("utf-8") + train_terminator for p in train_pairs
    )
    (output_data_dir / "train.jsonl").write_bytes(train_bytes)
    print(f"{output_data_dir / 'train.jsonl'}: {len(train_pairs)} examples")

    print("\n=== Step 7: fingerprints and machine-readable comparisons ===")
    parent_content_fp = hashlib.sha256(canonical_json_bytes(
        [{"input": r["input"], "output": r["output"]} for r in parent]
    )).hexdigest()
    candidate_content_fp = hashlib.sha256(canonical_json_bytes(
        [{"input": r["input"], "output": r["output"]} for r in candidate]
    )).hexdigest()
    candidate_corpus_fp = file_fingerprint(OUTPUT_CORPUS_PATH)
    new_training_data_fp = canonical_training_data_fingerprint(train_pairs + val_pairs)

    existing_parent_train_pairs, existing_parent_val_pairs = build_split(parent, val_hashes)
    parent_training_data_fp = canonical_training_data_fingerprint(existing_parent_train_pairs + existing_parent_val_pairs)

    comparison = {
        "parent_record_count": len(parent),
        "proposal_record_count": len(proposal),
        "candidate_record_count": len(candidate),
        "parent_content_fingerprint": parent_content_fp,
        "candidate_content_fingerprint": candidate_content_fp,
        "candidate_corpus_file_fingerprint": candidate_corpus_fp,
        "appended_records_in_order": [
            {
                "label": PROPOSAL_LABELS_IN_FILE_ORDER[i],
                "input_hash": proposal_hashes[i],
                "input_excerpt": proposal[i]["input"][:80],
                "category": proposal[i]["category"],
                "difficulty": proposal[i]["difficulty"],
                "bullets": len(proposal[i]["output"]["bullets"]),
                "actions": len(proposal[i]["output"]["action_items"]),
            }
            for i in range(EXPECTED_PROPOSAL_COUNT)
        ],
    }
    OUTPUT_COMPARISON_PATH.write_text(json.dumps(comparison, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{OUTPUT_COMPARISON_PATH.name}: parent-vs-candidate comparison")

    split_comparison = {
        "train_count": len(train_pairs),
        "val_count": len(val_pairs),
        **val_comparison,
        "parent_training_data_fingerprint": parent_training_data_fp,
        "candidate_training_data_fingerprint": new_training_data_fp,
    }
    OUTPUT_SPLIT_COMPARISON_PATH.write_text(json.dumps(split_comparison, indent=2), encoding="utf-8")
    print(f"{OUTPUT_SPLIT_COMPARISON_PATH.name}: split comparison")

    print("\n=== Step 8: derivation report ===")
    report = f"""# Gold v1.2.2 Phase-2 Corpus Derivation -- Provenance & Validation Report

**Generated by:** `prepare_phase2_candidate_corpus.py`
**Authorized by:** Johnny, 2026-08-04 -- "I am authorizing this as GPT has scoped it," covering derivation
tooling and generation of one uncommitted candidate, exactly as proposed and restated back for confirmation.
**Compute performed:** none (model). **Training/inference performed:** none.
**Parent corpus (`{PARENT_PATH.name}`):** untouched -- read-only, fingerprint-pinned.
**Gold v1.2.2 / v1.2.3 (`datasets/synthetic.jsonl`, `datasets/gold/`):** untouched, never read by this script.

## Pinned inputs

| Input | SHA-256 |
|---|---|
| Parent corpus (`{PARENT_PATH.name}`, {len(parent)} records) | `{EXPECTED_PARENT_FINGERPRINT}` |
| Reviewed proposal (`{PROPOSAL_PATH.name}`, {len(proposal)} records) | `{EXPECTED_PROPOSAL_FINGERPRINT}` |
| Split manifest (`{SPLIT_MANIFEST_PATH.name}`) | `{EXPECTED_SPLIT_MANIFEST_FINGERPRINT}` |
| Protected-16 benchmark (`{PROTECTED_PROBES_PATH.name}`) | `{EXPECTED_PROTECTED_PROBES_FINGERPRINT}` |
| Acceptance-10 benchmark (`{ACCEPTANCE_PROBES_PATH.name}`) | `{EXPECTED_ACCEPTANCE_PROBES_FINGERPRINT}` |

## Fail-closed checks performed, all passed

**Revision note (2026-08-04):** ChatGPT's review of the first run found two real gaps, both fixed and
reflected below, before any commit: (1) the byte-identity checks compared decoded, `splitlines()`-normalized
text, which cannot detect CRLF/LF drift, terminal-newline drift, or blank-line drift -- rewritten to compare
`read_bytes()` output directly; (2) the 26-benchmark collision check read whatever currently existed at the
two benchmark paths without pinning their fingerprints or asserting the 16/10 counts -- both are now pinned
above and count-asserted below.

1. All five pinned inputs (parent, proposal, split manifest, both benchmark files) matched their expected
   fingerprint exactly -- no drift.
2. Parent corpus is exactly {EXPECTED_PARENT_COUNT} records; proposal is exactly {EXPECTED_PROPOSAL_COUNT}.
3. Every proposal record matched the exact reviewed schema (`{sorted(PROPOSAL_RECORD_KEYS)}` at the top
   level, `{sorted(PROPOSAL_OUTPUT_KEYS)}` in `output`) -- no missing, extra, or mistyped fields, and
   `category` is never `{FORBIDDEN_CATEGORY}`.
4. The protected benchmark is exactly {EXPECTED_PROTECTED_COUNT} records and the acceptance benchmark is
   exactly {EXPECTED_ACCEPTANCE_COUNT} records ({EXPECTED_PROTECTED_COUNT + EXPECTED_ACCEPTANCE_COUNT} total)
   -- asserted at load time, not assumed.
5. No duplicate input hash within the parent, within the proposal, between the proposal and the parent, or
   between the proposal and any of the {EXPECTED_PROTECTED_COUNT + EXPECTED_ACCEPTANCE_COUNT} pinned, count-
   verified benchmark cases -- an active run-time check, not just the design-time overlap review.
6. The candidate's first {len(parent_bytes)} bytes are byte-identical to the parent corpus's own raw bytes --
   verified via `read_bytes()` on both files, never decoded text or `splitlines()`.
7. The written `val.jsonl` is a direct byte-for-byte copy of the existing R2 val split's own bytes (not a
   reconstruction), independently re-verified via `read_bytes()` against what's actually on disk.
8. The 12 proposal records were appended in exactly the proposal file's own order, confirmed by input-hash
   sequence.
9. `v1_target`/`v2_target` mechanically generated for all 12 proposal records via
   `prompt_contract_v2_migrate.build_v1_target`/`build_v2_target` (never hand-authored), each parse-verified
   via `prompt_contract_v2_parser.parse_output` for exact structural equality against the authored output.
10. Candidate corpus is exactly {EXPECTED_CANDIDATE_COUNT} records; split is exactly 72 train / 6 val.

## Fingerprints

| Artifact | SHA-256 |
|---|---|
| Parent content (input+output, {len(parent)} records) | `{parent_content_fp}` |
| Candidate content (input+output, {len(candidate)} records) | `{candidate_content_fp}` |
| Candidate corpus file (`{OUTPUT_CORPUS_PATH.name}`) | `{candidate_corpus_fp}` |
| Parent training-data fingerprint (canonical, 60 train + 6 val, for comparison) | `{parent_training_data_fp}` |
| Candidate training-data fingerprint (canonical, 72 train + 6 val) | `{new_training_data_fp}` |

## Appended records (in candidate order, positions {EXPECTED_PARENT_COUNT}-{EXPECTED_CANDIDATE_COUNT - 1})

| Label | Category | Difficulty | Bullets | Actions | Input excerpt |
|---|---|---|---:|---:|---|
"""
    for entry in comparison["appended_records_in_order"]:
        report += f"| {entry['label']} | `{entry['category']}` | {entry['difficulty']} | {entry['bullets']} | {entry['actions']} | {entry['input_excerpt']}... |\n"

    report += f"""
## Status

Candidate corpus written to `{OUTPUT_CORPUS_PATH.name}` ({len(candidate)} records) -- a separately
fingerprinted candidate, not a modification of the immutable parent. Candidate train/val split written to
`{output_data_dir.relative_to(TRAINING_DIR).as_posix()}/` ({len(train_pairs)} train / {len(val_pairs)} val). Gold v1.2.3
and all 26 frozen benchmark cases are excluded both structurally (this script never reads
`datasets/synthetic.jsonl` or the benchmark files as a data source) and by active, pinned collision check
(checks 4-5 above).

**Stopping here for joint review, as instructed. Everything this script wrote remains uncommitted. No
training, inference, benchmark execution, seed 73, export, or deployment has been performed or authorized.**
"""
    OUTPUT_REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"{OUTPUT_REPORT_PATH.name}: derivation report")

    print("\n=== Summary ===")
    print(f"Candidate corpus: {len(candidate)} records ({len(parent)} parent + {len(proposal_hashes)} proposal)")
    print(f"Split: {len(train_pairs)} train / {len(val_pairs)} val")
    print(f"Candidate training-data fingerprint: {new_training_data_fp}")
    print("\nDone. Stopping for joint verification -- no training or inference performed. Nothing committed.")


if __name__ == "__main__":
    main()
