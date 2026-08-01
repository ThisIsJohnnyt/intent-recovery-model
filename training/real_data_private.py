"""Private-data utilities for real-note evaluation: canonical JSON, the
four deterministic SHA-256 fingerprint types, and manifest/rubric I/O.

Implements the algorithms exactly as specified in
training/REAL_DATA_EVALUATION_PROTOCOL.md's "Deterministic fingerprints"
section. Do not change the canonicalization or fingerprint construction
without updating that document and re-verifying every existing fingerprint
comparison -- any change here silently invalidates prior comparisons.

Nothing in this module ever writes de-identified note content into a log
or fingerprint manifest -- only fingerprints, IDs, and metadata. Manifest
and rubric paths point under datasets/private/, which is gitignored (see
datasets/.gitignore and docs/decisions/PDR-005.md).
"""
import hashlib
import json
import os
import uuid
from pathlib import Path

DATASETS_DIR = Path(__file__).parent.parent / "datasets"
PRIVATE_DIR = DATASETS_DIR / "private"
MANIFEST_PATH = PRIVATE_DIR / "real_data_manifest.jsonl"
RUBRICS_PATH = PRIVATE_DIR / "real_data_rubrics.jsonl"

RUBRIC_SCHEMA_VERSION = "real-rubric-v1"


# Canonical JSON
#
# UTF-8 encoded, sorted object keys, no insignificant whitespace, array
# order preserved, no newline appended before hashing. ensure_ascii=False
# so non-ASCII content is genuinely UTF-8-encoded rather than \uXXXX
# escaped -- this is a fixed convention, not a free choice per call site.


def canonical_json_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_of_canonical(obj) -> str:
    return sha256_hex(canonical_json_bytes(obj))


# Record fingerprints


def source_fingerprint(deidentified_input: str) -> str:
    """SHA-256 of canonical JSON containing only {"input": <text>}."""
    return sha256_of_canonical({"input": deidentified_input})


def pair_fingerprint(deidentified_input: str, approved_output: dict) -> str:
    """SHA-256 of canonical JSON containing only {"input":..., "output":...}."""
    return sha256_of_canonical({"input": deidentified_input, "output": approved_output})


def rubric_fingerprint(rubric: dict) -> str:
    """SHA-256 of the canonical rubric after omitting its own
    rubric_fingerprint field (a fingerprint can't include itself)."""
    stripped = {k: v for k, v in rubric.items() if k != "rubric_fingerprint"}
    return sha256_of_canonical(stripped)


# Dataset fingerprint


class DatasetFingerprintError(ValueError):
    pass


def dataset_fingerprint(records: list[dict], split: str) -> str:
    """records: one dict per active record, each with record_id,
    source_fingerprint, pair_fingerprint, rubric_fingerprint (bare hex,
    with or without a "sha256:" prefix -- normalized to prefixed form
    here). Sorted by record_id before hashing, so manifest line order
    never affects the result; any record/rubric edit changes that
    record's fingerprint and therefore this one."""
    if split not in ("real_validation", "real_holdout"):
        raise DatasetFingerprintError(f"split must be 'real_validation' or 'real_holdout', got {split!r}")

    def prefixed(h: str) -> str:
        return h if h.startswith("sha256:") else f"sha256:{h}"

    entries = [
        {
            "record_id": r["record_id"],
            "source_fingerprint": prefixed(r["source_fingerprint"]),
            "pair_fingerprint": prefixed(r["pair_fingerprint"]),
            "rubric_fingerprint": prefixed(r["rubric_fingerprint"]),
        }
        for r in records
    ]
    entries.sort(key=lambda e: e["record_id"])
    wrapper = {
        "rubric_schema_version": RUBRIC_SCHEMA_VERSION,
        "split": split,
        "records": entries,
    }
    return sha256_of_canonical(wrapper)


# Checkpoint fingerprint


class CheckpointFingerprintError(ValueError):
    pass


def checkpoint_fingerprint(checkpoint_dir: Path) -> str:
    """Recursively walks checkpoint_dir. Symlinks are rejected (fail
    closed). Every regular file contributes its POSIX-style relative
    path, byte length, and SHA-256; entries are sorted lexicographically
    by relative path before hashing, so the result is deterministic
    regardless of filesystem iteration order. An empty directory fails."""
    checkpoint_dir = Path(checkpoint_dir)
    if not checkpoint_dir.is_dir():
        raise CheckpointFingerprintError(f"{checkpoint_dir} is not a directory")

    entries = []
    for path in checkpoint_dir.rglob("*"):
        if path.is_symlink():
            raise CheckpointFingerprintError(f"Symlinks are rejected: {path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise CheckpointFingerprintError(f"Not a regular file: {path}")
        rel_posix = path.relative_to(checkpoint_dir).as_posix()
        data = path.read_bytes()
        entries.append(
            {
                "path": rel_posix,
                "size": len(data),
                "sha256": sha256_hex(data),
            }
        )

    if not entries:
        raise CheckpointFingerprintError(f"Empty checkpoint directory fails validation: {checkpoint_dir}")

    entries.sort(key=lambda e: e["path"])
    return sha256_of_canonical(entries)


# Prompt-contract fingerprint

PROMPT_CONTRACT_FIXTURE = "Prompt contract fixture: review the blue folder tomorrow?"


def prompt_contract_fingerprint(rendered_prompt: str) -> str:
    """SHA-256 of the complete rendered prompt, UTF-8 encoded, with no
    normalization and no appended newline -- the raw prompt bytes as
    produced by the prompt builder, not wrapped in any JSON envelope."""
    return sha256_hex(rendered_prompt.encode("utf-8"))


# Private manifest / rubric I/O
#
# Both files are private, gitignored JSONL keyed by record_id. Loaded as
# a dict for lookup/update (e.g. withdrawal); saved back sorted by
# record_id for determinism, matching the dataset-fingerprint ordering.


def _load_jsonl_by_record_id(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    entries = {}
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if "record_id" not in record:
                raise ValueError(f"{path.name}:{line_no}: missing 'record_id'")
            entries[record["record_id"]] = record
    return entries


def _save_jsonl_by_record_id(path: Path, entries: dict[str, dict]) -> None:
    """Atomic: writes to a sibling temp file and renames it into place, so a
    crash or failed validation mid-write can never leave the prior committed
    file truncated or partially overwritten -- the rename is the only step
    that touches the real path, and it's a single filesystem operation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    with tmp_path.open("w", encoding="utf-8") as f:
        for record_id in sorted(entries.keys()):
            f.write(json.dumps(entries[record_id], ensure_ascii=False) + "\n")
    os.replace(tmp_path, path)


def _load_manifest_raw() -> dict[str, dict]:
    """Raw, unvalidated manifest I/O -- no schema, no duplicate-fingerprint
    check, no transition/eligibility check, no pilot-mode gate. Not a
    production write or read path: real_data_manifest.py's
    load_manifest_strict()/upsert_manifest_entry_validated() are the only
    schema-validated entry points, and are what any real code (or a human)
    should call. This function exists for that module's internal use and
    for tests of the underlying raw-JSONL-by-record-id mechanism itself --
    calling it directly on a real manifest bypasses every real-manifest-v1
    guarantee."""
    return _load_jsonl_by_record_id(MANIFEST_PATH)


def _save_manifest_raw(entries: dict[str, dict]) -> None:
    """See _load_manifest_raw -- same caveat, same restricted audience."""
    _save_jsonl_by_record_id(MANIFEST_PATH, entries)


def load_rubrics() -> dict[str, dict]:
    return _load_jsonl_by_record_id(RUBRICS_PATH)


def save_rubrics(entries: dict[str, dict]) -> None:
    _save_jsonl_by_record_id(RUBRICS_PATH, entries)


def upsert_rubric_entry(entry: dict) -> None:
    entries = load_rubrics()
    entries[entry["record_id"]] = entry
    save_rubrics(entries)


# A validated upsert_manifest_entry and a withdraw_record used to live here.
# Both are removed: upsert_manifest_entry bypassed real-manifest-v1 schema
# validation, duplicate-fingerprint rejection, transition rules, and the
# pilot-mode gate entirely -- real_data_manifest.upsert_manifest_entry_validated
# is the one production write path now. withdraw_record mutated
# withdrawal_status without updating withdrawal_status_changed_at_utc and
# without any of the future withdrawal-lineage behavior (invalidating
# derived evaluation artifacts, regenerating dataset fingerprints) --
# leaving a half-correct version in place would be worse than an explicit
# gap. A validated withdrawal operation is pending that lineage design;
# see real_data_manifest_schema_decision.md's "Remaining project gates."
