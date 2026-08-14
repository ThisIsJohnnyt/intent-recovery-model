"""Fail-closed typed-proposition representation parser and serializer.

Static milestone-1 module only. It does not load or invoke a model.
"""

from __future__ import annotations

from dataclasses import dataclass

from prompt_contract_v2_parser import ParsedOutput, parse_output

PLAN_MARKER = "###PROPOSITIONS###"
PROP_MARKER = "###PROP###"
STATE_MARKER = "###STATE###"
PREDICATE_MARKER = "###PREDICATE###"
ROLES_MARKER = "###ROLES###"
QUALIFIERS_MARKER = "###QUALIFIERS###"
COREFERENCE_MARKER = "###COREFERENCE###"
DUPLICATE_MARKER = "###DUPLICATE_OF###"
FIELDS_MARKER = "###FIELDS###"
RENDERED_MARKER = "###RENDERED_OUTPUT###"

STATES = {"fact", "question", "fragment", "tentative_idea", "task"}
ROLE_KEYS = {"speaker", "actor", "recipient", "object", "possessor", "experiencer", "candidate_set"}
QUALIFIER_KEYS = {"time", "deadline", "destination", "trigger", "condition", "quantity", "purpose", "object_modifier"}
COREFERENCE_VALUES = {"none", "dangling"}
FIELD_ORDER = ("narrative", "bullet", "action")


class TypedPlanError(ValueError):
    pass


@dataclass(frozen=True)
class Proposition:
    id: str
    state: str
    predicate: str
    roles: tuple[tuple[str, str], ...]
    qualifiers: tuple[tuple[str, str], ...]
    coreference: str
    duplicate_of: str | None
    fields: tuple[str, ...]


@dataclass(frozen=True)
class TypedOutput:
    propositions: tuple[Proposition, ...]
    rendered_text: str
    rendered: ParsedOutput


def _pairs(text: str, allowed: set[str], label: str) -> tuple[tuple[str, str], ...]:
    if text == "none":
        return ()
    values = []
    for part in text.split("; "):
        if "=" not in part:
            raise TypedPlanError(f"{label}: malformed pair {part!r}")
        key, value = part.split("=", 1)
        if key not in allowed or not value.strip():
            raise TypedPlanError(f"{label}: invalid {key!r}={value!r}")
        values.append((key, value))
    if values != sorted(values):
        raise TypedPlanError(f"{label}: pairs are not canonically sorted")
    if len({k for k, _ in values}) != len(values):
        raise TypedPlanError(f"{label}: duplicate key")
    return tuple(values)


def _single(lines: list[str], marker: str, prop_id: str) -> str:
    matches = [line[len(marker):].strip() for line in lines if line.startswith(marker)]
    if len(matches) != 1 or not matches[0]:
        raise TypedPlanError(f"{prop_id}: expected one nonempty {marker}")
    return matches[0]


def parse_typed_output(text: str) -> TypedOutput:
    if text.count(PLAN_MARKER) != 1 or not text.startswith(PLAN_MARKER):
        raise TypedPlanError("typed output must start with exactly one propositions marker")
    if text.count(RENDERED_MARKER) != 1:
        raise TypedPlanError("expected exactly one rendered-output marker")
    plan_text, rendered_text = text.split(RENDERED_MARKER, 1)
    rendered_text = rendered_text.lstrip("\n")
    blocks = plan_text[len(PLAN_MARKER):].split(PROP_MARKER)
    if blocks[0].strip() or len(blocks) == 1:
        raise TypedPlanError("missing or malformed proposition blocks")
    props = []
    for index, raw in enumerate(blocks[1:], 1):
        lines = [line.strip() for line in raw.strip().splitlines() if line.strip()]
        prop_id = lines.pop(0) if lines else ""
        expected_id = f"p{index:02d}"
        if prop_id != expected_id:
            raise TypedPlanError(f"expected {expected_id}, found {prop_id!r}")
        state = _single(lines, STATE_MARKER, prop_id)
        if state not in STATES:
            raise TypedPlanError(f"{prop_id}: invalid state {state!r}")
        predicate = _single(lines, PREDICATE_MARKER, prop_id)
        roles = _pairs(_single(lines, ROLES_MARKER, prop_id), ROLE_KEYS, f"{prop_id} roles")
        qualifiers = _pairs(_single(lines, QUALIFIERS_MARKER, prop_id), QUALIFIER_KEYS, f"{prop_id} qualifiers")
        coref = _single(lines, COREFERENCE_MARKER, prop_id)
        if coref not in COREFERENCE_VALUES and not coref.startswith(("resolved:", "unresolved:")):
            raise TypedPlanError(f"{prop_id}: invalid coreference {coref!r}")
        duplicate_raw = _single(lines, DUPLICATE_MARKER, prop_id)
        duplicate = None if duplicate_raw == "none" else duplicate_raw
        if duplicate is not None and duplicate not in {p.id for p in props}:
            raise TypedPlanError(f"{prop_id}: duplicate_of must name an earlier proposition")
        field_text = _single(lines, FIELDS_MARKER, prop_id)
        fields = tuple(field_text.split(","))
        if not fields or any(f not in FIELD_ORDER for f in fields) or fields != tuple(f for f in FIELD_ORDER if f in fields):
            raise TypedPlanError(f"{prop_id}: invalid/noncanonical fields {fields}")
        if state != "task" and "action" in fields:
            raise TypedPlanError(f"{prop_id}: non-task may not require action")
        props.append(Proposition(prop_id, state, predicate, roles, qualifiers, coref, duplicate, fields))
    try:
        rendered = parse_output(rendered_text)
    except Exception as exc:
        raise TypedPlanError(f"rendered v2 suffix invalid: {exc}") from exc
    return TypedOutput(tuple(props), rendered_text, rendered)


def serialize_plan(plan: list[dict], rendered_text: str) -> str:
    lines = [PLAN_MARKER]
    for p in plan:
        lines.extend([
            f"{PROP_MARKER} {p['id']}", f"{STATE_MARKER} {p['state']}",
            f"{PREDICATE_MARKER} {p['predicate']}",
            f"{ROLES_MARKER} {p.get('roles') or 'none'}",
            f"{QUALIFIERS_MARKER} {p.get('qualifiers') or 'none'}",
            f"{COREFERENCE_MARKER} {p.get('coreference', 'none')}",
            f"{DUPLICATE_MARKER} {p.get('duplicate_of') or 'none'}",
            f"{FIELDS_MARKER} {','.join(p['fields'])}",
        ])
    value = "\n".join(lines) + "\n" + RENDERED_MARKER + "\n" + rendered_text
    parse_typed_output(value)
    return value
