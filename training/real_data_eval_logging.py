"""Structured private generation-artifact logging (real-eval-generation-v1
schema), per training/real_data_scoring_lineage_withdrawal_design.md.

A generation artifact records only what a model actually produced and
whether its format parsed -- no semantic scores, review status, or
adjudication placeholders live here. Those are separate, later artifact
kinds (review, comparison, adjudication -- see real_data_lineage.py) that
reference a generation by ID and fingerprint. This supersedes the earlier
real-eval-v1 schema, which mixed raw output with unreachable score
placeholder fields (nothing could ever update them, since exclusive-create
is the only write mode) -- no real artifacts existed under that schema, so
this is a clean replacement, not a migration.

Every write is checked against the *specific* approved root for its
declared split (not "either root") and fails closed (raises, does not
write) if asked to go anywhere else. evaluation_id/milestone are
restricted to a safe character set before they ever reach a path, so a
crafted identifier can't traverse out of its intended subdirectory in
the first place -- the root check below is defense in depth on top of
that, not the only safeguard.
"""
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import real_data_manifest as rdm
import real_data_private as rdp

RESULTS_PRIVATE_DIR = Path(__file__).parent / "results" / "private"
VALIDATION_RESULTS_DIR = RESULTS_PRIVATE_DIR / "real_validation"
HOLDOUT_RESULTS_DIR = RESULTS_PRIVATE_DIR / "real_holdout"

SCHEMA_VERSION = "real-eval-generation-v1"
ARTIFACT_KIND = "generation"

_SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_GENERATION_ID_RE = re.compile(r"^eval_[0-9a-f]{32}$")

# Exact top-level field set -- reject unknown/missing fields on every
# load, not just on build (see the Phase E lineage/withdrawal
# implementation review's finding 4).
_GENERATION_FIELDS = frozenset(
    {
        "schema_version",
        "artifact_kind",
        "evaluation_id",
        "created_at_utc",
        "split",
        "release_milestone",
        "evaluation_reason",
        "git_commit",
        "checkpoint",
        "dataset",
        "prompt_contract",
        "generation_config",
        "results",
        "aggregate",
        "artifact_fingerprint",
    }
)
_GENERATION_RECORD_FIELDS = frozenset({"record_id", "source_fingerprint", "pair_fingerprint", "rubric_fingerprint", "raw_output", "raw_output_fingerprint", "format_valid"})


class ApprovedRootError(ValueError):
    pass


class UnsafeIdentifierError(ValueError):
    pass


class ArtifactExistsError(FileExistsError):
    pass


class GenerationValidationError(ValueError):
    pass


def new_evaluation_id() -> str:
    return f"eval_{uuid.uuid4().hex}"


def _validate_identifier(value: str, field_name: str) -> str:
    """Rejects anything but [A-Za-z0-9_-] before it ever reaches a path
    -- no '/', '\\', '..', or other path-shaped characters allowed. This
    is what actually prevents a crafted evaluation_id/milestone from
    traversing into a sibling directory; the root check in
    _validate_split_root is a second layer, not the first."""
    if not isinstance(value, str) or not _SAFE_IDENTIFIER_RE.match(value):
        raise UnsafeIdentifierError(
            f"{field_name} must match {_SAFE_IDENTIFIER_RE.pattern} (letters, digits, "
            f"underscore, hyphen only) -- got {value!r}"
        )
    return value


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _root_for_split(split: str) -> Path:
    if split == "real_validation":
        return VALIDATION_RESULTS_DIR
    if split == "real_holdout":
        return HOLDOUT_RESULTS_DIR
    raise ValueError(f"split must be 'real_validation' or 'real_holdout', got {split!r}")


def _validate_split_root(path: Path, split: str) -> None:
    """Checks the path lands under the root for *this specific* declared
    split -- not merely "one of the two approved roots" (a holdout
    result landing inside the validation tree, or vice versa, must be
    rejected even though both trees are individually "approved")."""
    expected_root = _root_for_split(split).resolve()
    if not _is_relative_to(path.resolve(), expected_root):
        raise ApprovedRootError(
            f"Refusing to write a {split!r} result outside its approved root "
            f"({expected_root}): {path}"
        )


def _validate_any_approved_root(path: Path) -> None:
    """Looser check used only for loading a result whose split isn't
    already known from context -- accepts either approved root."""
    resolved = path.resolve()
    approved_roots = [VALIDATION_RESULTS_DIR.resolve(), HOLDOUT_RESULTS_DIR.resolve()]
    if not any(_is_relative_to(resolved, root) for root in approved_roots):
        raise ApprovedRootError(
            f"Refusing to read outside approved private result roots "
            f"({VALIDATION_RESULTS_DIR}, {HOLDOUT_RESULTS_DIR}): {path}"
        )


def result_path_for(split: str, evaluation_id: str, milestone: str | None = None) -> Path:
    evaluation_id = _validate_identifier(evaluation_id, "evaluation_id")
    root = _root_for_split(split)
    if split == "real_validation":
        path = root / f"{evaluation_id}.json"
    else:
        if not milestone:
            raise ValueError("milestone is required for real_holdout result paths")
        milestone = _validate_identifier(milestone, "milestone")
        path = root / milestone / f"{evaluation_id}.json"
    _validate_split_root(path, split)
    return path


def _prefixed(fingerprint: str) -> str:
    return fingerprint if fingerprint.startswith("sha256:") else f"sha256:{fingerprint}"


def new_generation_record(
    *, record_id: str, source_fingerprint: str, pair_fingerprint: str, rubric_fingerprint: str, raw_output: str, format_valid: bool
) -> dict:
    """One per-record slice of a generation artifact. No score/review
    fields -- a generation is evidence of what the model produced, never
    evidence that it was judged."""
    return {
        "record_id": record_id,
        "source_fingerprint": _prefixed(source_fingerprint),
        "pair_fingerprint": _prefixed(pair_fingerprint),
        "rubric_fingerprint": _prefixed(rubric_fingerprint),
        "raw_output": raw_output,
        "raw_output_fingerprint": f"sha256:{rdp.sha256_of_canonical({'raw_output': raw_output})}",
        "format_valid": format_valid,
    }


def build_generation_artifact(
    *,
    split: str,
    evaluation_reason: str,
    git_commit: str,
    checkpoint: dict,
    dataset: dict,
    generation_config: dict,
    results: list[dict],
    prompt_contract: dict | None = None,
    release_milestone: str | None = None,
    evaluation_id: str | None = None,
) -> dict:
    """checkpoint: {"path", "fingerprint", "training_seed", "run_id"}.
    dataset: {"fingerprint", "record_count", "rubric_schema_version"}.
    prompt_contract: {"version", "fingerprint"} once the cross-repository
    prompt contract is synchronized, else None -- that synchronization
    hasn't happened yet (see docs/decisions and the Phase E roadmap), so
    every generation artifact built today carries prompt_contract=None
    until it does.

    Reviewed exception to aislop's max-6-parameter guideline: the grouped
    pieces above are already grouped; the remaining fields are
    independent, atomically-required top-level fields of the schema, not
    a growing ad hoc parameter list.
    """
    if split == "real_holdout" and not release_milestone:
        raise ValueError("release_milestone is required and may not be null for holdout runs")

    evaluation_id = evaluation_id or new_evaluation_id()
    format_valid_count = sum(1 for r in results if r["format_valid"])

    artifact = {
        "schema_version": SCHEMA_VERSION,
        "artifact_kind": ARTIFACT_KIND,
        "evaluation_id": evaluation_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "split": split,
        "release_milestone": release_milestone,
        "evaluation_reason": evaluation_reason,
        "git_commit": git_commit,
        "checkpoint": {
            "path": checkpoint["path"],
            "fingerprint": _prefixed(checkpoint["fingerprint"]),
            "training_seed": checkpoint["training_seed"],
            "run_id": checkpoint["run_id"],
        },
        "dataset": {
            "fingerprint": _prefixed(dataset["fingerprint"]),
            "record_count": dataset["record_count"],
            "rubric_schema_version": dataset["rubric_schema_version"],
        },
        "prompt_contract": prompt_contract,
        "generation_config": generation_config,
        "results": results,
        "aggregate": {"format_valid": f"{format_valid_count}/{len(results)}"},
    }
    artifact["artifact_fingerprint"] = f"sha256:{rdp.artifact_fingerprint(artifact)}"
    _assert_generation_fields(artifact, evaluation_id)
    return artifact


def _assert_generation_fields(artifact: dict, context_id) -> None:
    extra = set(artifact.keys()) - _GENERATION_FIELDS
    if extra:
        raise GenerationValidationError(f"{context_id}: unknown generation field(s) not permitted: {sorted(extra)}")
    missing = _GENERATION_FIELDS - set(artifact.keys())
    if missing:
        raise GenerationValidationError(f"{context_id}: generation missing required field(s): {sorted(missing)}")
    own_id = artifact.get("evaluation_id")
    if not isinstance(own_id, str) or not _GENERATION_ID_RE.match(own_id):
        raise GenerationValidationError(f"{context_id}: evaluation_id is malformed: {own_id!r}")
    for record in artifact.get("results", []):
        extra_r = set(record.keys()) - _GENERATION_RECORD_FIELDS
        if extra_r:
            raise GenerationValidationError(f"{context_id}: unknown generation result field(s) not permitted: {sorted(extra_r)}")
        missing_r = _GENERATION_RECORD_FIELDS - set(record.keys())
        if missing_r:
            raise GenerationValidationError(f"{context_id}: generation result missing required field(s): {sorted(missing_r)}")


def save_generation_artifact(artifact: dict) -> Path:
    """Exclusive-create: raises ArtifactExistsError rather than silently
    overwriting if evaluation_id has already been used. Generation
    artifacts are immutable -- a review/comparison/adjudication is a
    separate artifact that references this one, never a second write to
    the same path."""
    path = result_path_for(artifact["split"], artifact["evaluation_id"], artifact.get("release_milestone"))
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(artifact, indent=2, ensure_ascii=False)
    try:
        with path.open("x", encoding="utf-8") as f:
            f.write(payload)
    except FileExistsError as e:
        raise ArtifactExistsError(
            f"Refusing to overwrite an existing generation artifact at {path}. "
            "Generation artifacts are immutable -- a review/comparison/adjudication "
            "is a separate artifact that references this one by ID and fingerprint."
        ) from e
    return path


def load_generation_artifact(path: Path) -> dict:
    """Loads and verifies: duplicate-key-free JSON, schema/kind match,
    exact field set (reject unknown or missing top-level/result fields),
    and that the recomputed artifact_fingerprint matches the stored one --
    a generation artifact that has been tampered with on disk must never
    be trusted just because it parses as JSON."""
    path = Path(path)
    _validate_any_approved_root(path)
    try:
        artifact = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=rdm.reject_duplicate_keys)
    except (json.JSONDecodeError, rdm.DuplicateJSONKeyError) as e:
        raise GenerationValidationError(f"{path}: invalid JSON ({e})") from e
    if not isinstance(artifact, dict):
        raise GenerationValidationError(f"{path}: artifact is not a JSON object")
    if artifact.get("schema_version") != SCHEMA_VERSION:
        raise GenerationValidationError(f"{path}: schema_version is {artifact.get('schema_version')!r}, expected {SCHEMA_VERSION!r}")
    if artifact.get("artifact_kind") != ARTIFACT_KIND:
        raise GenerationValidationError(f"{path}: artifact_kind is {artifact.get('artifact_kind')!r}, expected {ARTIFACT_KIND!r}")
    _assert_generation_fields(artifact, path)
    declared_fp = artifact.get("artifact_fingerprint", "")
    computed_fp = f"sha256:{rdp.artifact_fingerprint(artifact)}"
    if declared_fp != computed_fp:
        raise GenerationValidationError(f"{path}: artifact_fingerprint mismatch -- generation artifact may have been altered on disk")
    return artifact
