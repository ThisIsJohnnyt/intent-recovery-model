"""Structured private evaluation result logging (real-eval-v1 schema),
per training/REAL_DATA_EVALUATION_PROTOCOL.md's "Structured result
schema" and "Concrete private paths" sections.

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

RESULTS_PRIVATE_DIR = Path(__file__).parent / "results" / "private"
VALIDATION_RESULTS_DIR = RESULTS_PRIVATE_DIR / "real_validation"
HOLDOUT_RESULTS_DIR = RESULTS_PRIVATE_DIR / "real_holdout"

SCHEMA_VERSION = "real-eval-v1"

_SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class ApprovedRootError(ValueError):
    pass


class UnsafeIdentifierError(ValueError):
    pass


class ArtifactExistsError(FileExistsError):
    pass


def new_evaluation_id() -> str:
    return f"eval_{uuid.uuid4().hex[:12]}"


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


def new_result_record(record_id: str, raw_output: str, format_valid: bool) -> dict:
    return {
        "record_id": record_id,
        "raw_output": raw_output,
        "format_valid": format_valid,
        "scores": {
            "topic_completeness": None,
            "attribution_accuracy": None,
            "uncertainty_preservation": None,
            "unsupported_addition_resistance": None,
        },
        "capability_checks": {},
        "strict_pass": None,
        "failure_labels": [],
        "review_status": "unscored",
    }


def _prefixed(fingerprint: str) -> str:
    return fingerprint if fingerprint.startswith("sha256:") else f"sha256:{fingerprint}"


def build_result_artifact(
    *,
    split: str,
    evaluation_reason: str,
    git_commit: str,
    checkpoint: dict,
    dataset: dict,
    generation_config: dict,
    results: list[dict],
    release_milestone: str | None = None,
    evaluation_id: str | None = None,
) -> dict:
    """checkpoint: {"path", "fingerprint", "training_seed", "run_id"}.
    dataset: {"fingerprint", "record_count", "rubric_version"}. Grouped
    to mirror the schema's own "checkpoint"/"dataset" nesting rather than
    a flat parameter list.

    Reviewed exception to aislop's max-6-parameter guideline: the two
    multi-field pieces are already grouped above; the remaining six are
    independent, atomically-required top-level fields of the schema
    (see training/REAL_DATA_EVALUATION_PROTOCOL.md), not a growing ad
    hoc parameter list -- further nesting them would reduce clarity
    rather than improve it.
    """
    if split == "real_holdout" and not release_milestone:
        raise ValueError("release_milestone is required and may not be null for holdout runs")

    evaluation_id = evaluation_id or new_evaluation_id()
    format_valid_count = sum(1 for r in results if r["format_valid"])
    strict_values = [r.get("strict_pass") for r in results]
    aggregate_strict = None if any(v is None for v in strict_values) else f"{sum(1 for v in strict_values if v)}/{len(strict_values)}"

    return {
        "schema_version": SCHEMA_VERSION,
        "evaluation_id": evaluation_id,
        "split": split,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
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
            "rubric_version": dataset["rubric_version"],
        },
        "generation_config": generation_config,
        "results": results,
        "aggregate": {
            "format_valid": f"{format_valid_count}/{len(results)}",
            "strict_pass": aggregate_strict,
        },
        "review": {
            "chatgpt_status": "pending",
            "claude_status": "pending",
            "alignment_status": "pending",
            "adjudication_status": "not_started",
        },
    }


def save_result_artifact(artifact: dict) -> Path:
    """Exclusive-create: raises ArtifactExistsError rather than silently
    overwriting if evaluation_id has already been used. Raw generation
    artifacts must be immutable -- a scored/adjudicated version needs a
    new evaluation_id, not a second write to the same path. (Lineage
    linking a scored artifact back to its raw one is a separate,
    joint-design piece, not implemented by this function.)"""
    path = result_path_for(artifact["split"], artifact["evaluation_id"], artifact.get("release_milestone"))
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(artifact, indent=2, ensure_ascii=False)
    try:
        with path.open("x", encoding="utf-8") as f:
            f.write(payload)
    except FileExistsError as e:
        raise ArtifactExistsError(
            f"Refusing to overwrite an existing evaluation artifact at {path}. "
            "Raw generation artifacts are immutable -- use a new evaluation_id "
            "for a rescored/adjudicated version instead of reusing this one."
        ) from e
    return path


def load_result_artifact(path: Path) -> dict:
    path = Path(path)
    _validate_any_approved_root(path)
    return json.loads(path.read_text(encoding="utf-8"))
