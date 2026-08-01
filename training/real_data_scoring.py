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

VALID_REVIEW_STATUSES = ("unscored", "scored", "adjudicated")


class ScoringStateError(ValueError):
    pass


def _require_bool_or_none(value, field_name: str):
    """Rejects anything that isn't literally True, False, or None --
    Python truthiness must never substitute for an actual boolean here.
    A stray string like "false" is truthy and would otherwise silently
    read as a pass; isinstance(x, bool) is the only correct check
    (note bool is a subclass of int, but int is not accepted -- 0/1 are
    rejected too, not just non-empty strings)."""
    if value is None:
        return None
    if not isinstance(value, bool):
        raise ScoringStateError(
            f"{field_name} must be a real bool (True/False) or None -- got {value!r} ({type(value).__name__}). "
            "Non-boolean truthy values (e.g. the string 'false') must never be accepted as scores."
        )
    return value


def compute_strict_pass(result_record: dict) -> bool | None:
    """True/False once every required field is scored; None if any
    required field is still unscored (null) -- an unscored record must
    never silently read as pass or fail. Every scored field is checked
    with isinstance(x, bool), not truthiness -- a typo'd string like
    "false" raises instead of silently passing."""
    format_valid = _require_bool_or_none(result_record.get("format_valid"), "format_valid")
    if format_valid is None:
        raise ScoringStateError("format_valid must be a bool, never null, for any generated record")

    review_status = result_record.get("review_status")
    if review_status not in VALID_REVIEW_STATUSES:
        raise ScoringStateError(f"review_status must be one of {VALID_REVIEW_STATUSES}, got {review_status!r}")

    scores = result_record.get("scores", {})
    checked_scores = {}
    any_unscored = False
    for dim in SEMANTIC_DIMENSIONS:
        if dim not in scores:
            raise ScoringStateError(f"missing required semantic dimension: {dim}")
        value = _require_bool_or_none(scores[dim], f"scores[{dim!r}]")
        checked_scores[dim] = value
        if value is None:
            any_unscored = True

    capability_checks = result_record.get("capability_checks", {})
    checked_checks = {}
    for name, value in capability_checks.items():
        checked_value = _require_bool_or_none(value, f"capability_checks[{name!r}]")
        checked_checks[name] = checked_value
        if checked_value is None:
            any_unscored = True

    if any_unscored:
        return None

    if not format_valid:
        return False
    if not all(checked_scores.values()):
        return False
    if not all(checked_checks.values()):  # empty dict -> vacuously true, no extra checks required
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
    decision-ready. Validates each strict_pass is a real bool or None,
    even if the record didn't come through apply_scores."""
    values = [_require_bool_or_none(r.get("strict_pass"), "strict_pass") for r in results]
    if any(v is None for v in values):
        return None
    passed = sum(1 for v in values if v)
    return f"{passed}/{len(values)}"
