"""Structured private evaluation result logging (real-eval-v1 schema),
per training/REAL_DATA_EVALUATION_PROTOCOL.md's "Structured result
schema" and "Concrete private paths" sections.

Every write is checked against the two approved private result roots and
fails closed (raises, does not write) if asked to go anywhere else.
"""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

RESULTS_PRIVATE_DIR = Path(__file__).parent / "results" / "private"
VALIDATION_RESULTS_DIR = RESULTS_PRIVATE_DIR / "real_validation"
HOLDOUT_RESULTS_DIR = RESULTS_PRIVATE_DIR / "real_holdout"

SCHEMA_VERSION = "real-eval-v1"


class ApprovedRootError(ValueError):
    pass


def new_evaluation_id() -> str:
    return f"eval_{uuid.uuid4().hex[:12]}"


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _validate_output_path(path: Path) -> None:
    resolved = path.resolve()
    approved_roots = [VALIDATION_RESULTS_DIR.resolve(), HOLDOUT_RESULTS_DIR.resolve()]
    if not any(_is_relative_to(resolved, root) for root in approved_roots):
        raise ApprovedRootError(
            f"Refusing to write outside approved private result roots "
            f"({VALIDATION_RESULTS_DIR}, {HOLDOUT_RESULTS_DIR}): {path}"
        )


def result_path_for(split: str, evaluation_id: str, milestone: str | None = None) -> Path:
    if split == "real_validation":
        return VALIDATION_RESULTS_DIR / f"{evaluation_id}.json"
    if split == "real_holdout":
        if not milestone:
            raise ValueError("milestone is required for real_holdout result paths")
        return HOLDOUT_RESULTS_DIR / milestone / f"{evaluation_id}.json"
    raise ValueError(f"split must be 'real_validation' or 'real_holdout', got {split!r}")


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
    path = result_path_for(artifact["split"], artifact["evaluation_id"], artifact.get("release_milestone"))
    _validate_output_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_result_artifact(path: Path) -> dict:
    path = Path(path)
    _validate_output_path(path)
    return json.loads(path.read_text(encoding="utf-8"))
