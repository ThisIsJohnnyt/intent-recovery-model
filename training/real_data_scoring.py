"""Strict semantic-scoring scaffold for real-data evaluation records, per
training/REAL_DATA_EVALUATION_PROTOCOL.md's "Strict semantic rubric" and
"Strict pass rule" sections.

No automated semantic judge. This module only computes strict_pass from
already-recorded boolean scores -- the scores themselves come from
independent human (Claude Code / ChatGPT) review under the frozen
rubric, per the reviewer workflow, never from this code.
"""

SEMANTIC_DIMENSIONS = (
    "topic_completeness",
    "attribution_accuracy",
    "uncertainty_preservation",
    "unsupported_addition_resistance",
)


class ScoringStateError(ValueError):
    pass


def compute_strict_pass(result_record: dict) -> bool | None:
    """True/False once every required field is scored; None if any
    required field is still unscored (null) -- an unscored record must
    never silently read as pass or fail."""
    if not isinstance(result_record.get("format_valid"), bool):
        raise ScoringStateError("format_valid must be a bool, never null, for any generated record")

    scores = result_record.get("scores", {})
    for dim in SEMANTIC_DIMENSIONS:
        if dim not in scores:
            raise ScoringStateError(f"missing required semantic dimension: {dim}")
        if scores[dim] is None:
            return None

    capability_checks = result_record.get("capability_checks", {})
    if any(v is None for v in capability_checks.values()):
        return None

    if not result_record["format_valid"]:
        return False
    if not all(scores[dim] for dim in SEMANTIC_DIMENSIONS):
        return False
    if not all(capability_checks.values()):  # empty dict -> vacuously true, no extra checks required
        return False
    return True


def apply_scores(
    result_record: dict,
    *,
    scores: dict,
    capability_checks: dict,
    failure_labels: list[str],
    review_status: str = "scored",
) -> dict:
    """Returns a new result-record dict with scoring fields filled in --
    does not mutate the input, since the raw generation artifact must
    remain immutable per the reviewer workflow; adjudicated scoring is a
    new version, not an edit in place."""
    updated = {
        **result_record,
        "scores": {**result_record["scores"], **scores},
        "capability_checks": {**result_record.get("capability_checks", {}), **capability_checks},
        "failure_labels": list(failure_labels),
        "review_status": review_status,
    }
    updated["strict_pass"] = compute_strict_pass(updated)
    return updated


def aggregate_strict_pass_rate(results: list[dict]) -> str | None:
    """"X/Y" once every record has a non-null strict_pass, else None --
    a routine unscored log must never report an aggregate that looks
    decision-ready."""
    values = [r.get("strict_pass") for r in results]
    if any(v is None for v in values):
        return None
    passed = sum(1 for v in values if v)
    return f"{passed}/{len(values)}"
