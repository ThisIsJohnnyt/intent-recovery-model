"""Fail-closed parser for the compact typed-proposition feasibility pilot."""

from __future__ import annotations

from dataclasses import dataclass
import re

from prompt_contract_v2_parser import ParsedOutput, parse_output

PLAN = "@P"
OUTPUT = "@O"
STATES = {"F", "Q", "G", "I", "T"}  # fact, question, fragment, tentative idea, task
ROLE_KEYS = {"s", "a", "r", "o", "p", "e", "c"}
QUALIFIER_KEYS = {"tm", "dl", "ds", "tr", "cn", "qt", "pu", "om"}


class CompactPlanError(ValueError):
    pass


@dataclass(frozen=True)
class CompactProposition:
    id: int
    state: str
    predicate_ref: str
    field_refs: tuple[str, ...]
    roles: tuple[tuple[str, str], ...] = ()
    qualifiers: tuple[tuple[str, str], ...] = ()
    coreference: str = "-"
    duplicate_of: int | None = None


@dataclass(frozen=True)
class CompactOutput:
    propositions: tuple[CompactProposition, ...]
    rendered_text: str
    rendered: ParsedOutput


def _pairs(raw: str, allowed: set[str], label: str) -> tuple[tuple[str, str], ...]:
    pairs = []
    for item in raw.split(","):
        if "=" not in item:
            raise CompactPlanError(f"{label}: malformed pair {item!r}")
        key, value = item.split("=", 1)
        if key not in allowed or not value:
            raise CompactPlanError(f"{label}: invalid pair {item!r}")
        pairs.append((key, value))
    if len({k for k, _ in pairs}) != len(pairs):
        raise CompactPlanError(f"{label}: duplicate key")
    return tuple(pairs)


def _resolve(ref: str, rendered: ParsedOutput) -> str:
    if ref == "N":
        return rendered.narrative
    match = re.fullmatch(r"([BA])(\d+)", ref)
    if not match:
        raise CompactPlanError(f"invalid field reference {ref!r}")
    values = rendered.bullets if match.group(1) == "B" else rendered.actions
    index = int(match.group(2)) - 1
    if index < 0 or index >= len(values):
        raise CompactPlanError(f"out-of-range field reference {ref!r}")
    return values[index]


def parse_compact_output(text: str) -> CompactOutput:
    if text.count(PLAN) != 1 or not text.startswith(PLAN + "\n") or text.count(OUTPUT) != 1:
        raise CompactPlanError("expected exactly one leading @P and one @O")
    plan_text, rendered_text = text.split("\n" + OUTPUT + "\n", 1)
    try:
        rendered = parse_output(rendered_text)
    except Exception as exc:
        raise CompactPlanError(f"invalid rendered v2 suffix: {exc}") from exc
    propositions = []
    seen_action_refs = set()
    for expected, line in enumerate(plan_text.splitlines()[1:], 1):
        parts = line.split("|")
        head = re.fullmatch(r"(\d+)([FQGIT])", parts[0])
        if not head or int(head.group(1)) != expected:
            raise CompactPlanError(f"expected proposition {expected}, found {parts[0]!r}")
        predicate_ref = parts[1]
        _resolve(predicate_ref, rendered)
        fields = tuple(parts[2].split(","))
        if not fields or fields[0] != "N" or len(set(fields)) != len(fields):
            raise CompactPlanError(f"proposition {expected}: fields must start N and be unique")
        for ref in fields:
            _resolve(ref, rendered)
        state = head.group(2)
        action_refs = {r for r in fields if r.startswith("A")}
        if state != "T" and action_refs:
            raise CompactPlanError(f"proposition {expected}: non-task has action field")
        if seen_action_refs & action_refs:
            raise CompactPlanError(f"proposition {expected}: action linked more than once")
        seen_action_refs |= action_refs
        roles = qualifiers = ()
        coref = "-"
        duplicate = None
        for optional in parts[3:]:
            key, sep, value = optional.partition(":")
            if not sep or not value:
                raise CompactPlanError(f"proposition {expected}: malformed option {optional!r}")
            if key == "R": roles = _pairs(value, ROLE_KEYS, "roles")
            elif key == "Q": qualifiers = _pairs(value, QUALIFIER_KEYS, "qualifiers")
            elif key == "C":
                if not (value == "d" or value.startswith(("r=", "u="))):
                    raise CompactPlanError(f"proposition {expected}: invalid coreference")
                coref = value
            elif key == "D":
                duplicate = int(value)
                if duplicate >= expected or duplicate < 1:
                    raise CompactPlanError(f"proposition {expected}: duplicate must point backward")
            else: raise CompactPlanError(f"proposition {expected}: unknown option {key!r}")
        propositions.append(CompactProposition(expected, state, predicate_ref, fields, roles, qualifiers, coref, duplicate))
    expected_actions = {f"A{i}" for i in range(1, len(rendered.actions) + 1)}
    if seen_action_refs != expected_actions:
        raise CompactPlanError(f"action coverage mismatch: {seen_action_refs} != {expected_actions}")
    return CompactOutput(tuple(propositions), rendered_text, rendered)


def serialize_compact(lines: list[str], rendered_text: str) -> str:
    value = PLAN + "\n" + "\n".join(lines) + "\n" + OUTPUT + "\n" + rendered_text
    parse_compact_output(value)
    return value
