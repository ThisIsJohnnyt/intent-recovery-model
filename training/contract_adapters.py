"""Contract adapters for run_benchmark.py / report_benchmark.py.

Lets the runner select between the live v1 prompt contract (default,
unchanged behavior) and the v2-candidate typed-marker contract (explicit
opt-in only), while the shared result schema and scoring-safety code in
report_benchmark.py stay completely unaware of which one produced a given
result. Per prompt_contract_vnext_static_final_review_and_branch_reconciliation.md's
Disagreement 2: one runner with an adapter, not a duplicated
run_benchmark_v2.py -- avoids the class of bug this project has hit more
than once, where a fix (e.g. required_semantic_dimensions' fail-open gap)
had to be propagated to more than one copy of similar logic.

The v2 adapter (module imports, build_prompt, parser) is constructed
lazily, only inside select_contract_adapter("v2") -- prompt_contract_v2_candidate.py
and prompt_contract_v2_parser.py are NOT imported at this module's import
time. This closes Finding 4 of
prompt_contract_vnext_adapter_structural_implementation_review.md: a fresh
process that only imports this module and selects "v1" must never see
either v2 module in sys.modules (see test_run_benchmark_contract_adapters.py's
fresh-subprocess test), so candidate-only code can never break the
default v1 path just by being imported, and prompt_contract_v2_candidate.py's
own "never imported by run_benchmark.py [when v1 is selected]" claim stays
true, not stale.

Selecting an unknown adapter name, or an adapter whose rendered fixture
fingerprint doesn't match its locked value, is a fatal ContractSelectionError
raised before any model is loaded or any count-rule operator is evaluated --
the same fail-closed principle used throughout this project's prompt-
contract work (ParseError, required_semantic_dimensions' unknown-name
check).

Not wired into train.py or any live training path -- only run_benchmark.py
(evaluation) and report_benchmark.py (scoring) use this module. The v1
adapter reuses prepare_data.build_prompt/check_format_valid directly, so
the live v1 contract's behavior is untouched by this module's existence.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import prepare_data
import real_data_private as rdp

_MISSING = object()


class ContractSelectionError(ValueError):
    """Raised before any model loading: unknown adapter name, a fingerprint
    that doesn't match the locked value for that contract, or (via
    preflight_validate_count_rules) a malformed count-rule/probe-id
    declaration in the benchmark file itself."""


@dataclass(frozen=True)
class ParsedStructure:
    narrative: str
    bullets: list[str]
    actions: list[str]


@dataclass(frozen=True)
class ContractAdapter:
    name: str
    version: str
    build_prompt: Callable[[str], str]
    check_format_valid: Callable[[str], bool]
    # None for contracts (v1) that don't define a structural parser. For
    # contracts that do (v2), returns the parsed structure on success or
    # None on a parse failure -- never raises, so callers don't need to
    # know about ParseError.
    parse: Optional[Callable[[str], Optional[ParsedStructure]]]
    # None for contracts with no structural parser.
    parser_version: Optional[str]
    expected_fingerprint: str


def _v1_adapter() -> ContractAdapter:
    return ContractAdapter(
        name="v1",
        version=prepare_data.PROMPT_CONTRACT_VERSION,
        build_prompt=prepare_data.build_prompt,
        check_format_valid=prepare_data.check_format_valid,
        parse=None,
        parser_version=None,
        # Locked in test_prepare_data.py -- must change together with that
        # file if the v1 prompt template is ever deliberately revised.
        expected_fingerprint="161661198071fd81310681f69381ec8e0287141e1e75b09d3a342414af31ccf1",
    )


_v2_adapter_cache: Optional[ContractAdapter] = None


def _v2_adapter() -> ContractAdapter:
    """Lazily imports and constructs the v2 adapter -- see this module's
    docstring for why. Cached after first build within a process (the
    import itself is already cached by Python's module system; this just
    avoids rebuilding the small closures/dataclass every call)."""
    global _v2_adapter_cache
    if _v2_adapter_cache is not None:
        return _v2_adapter_cache

    import prompt_contract_v2_candidate as v2_candidate
    from prompt_contract_v2_parser import PARSER_VERSION, ParseError, parse_output

    def _check_format_valid(generated: str) -> bool:
        try:
            parse_output(generated)
            return True
        except ParseError:
            return False

    def _parse(generated: str) -> Optional[ParsedStructure]:
        try:
            parsed = parse_output(generated)
        except ParseError:
            return None
        return ParsedStructure(narrative=parsed.narrative, bullets=parsed.bullets, actions=parsed.actions)

    _v2_adapter_cache = ContractAdapter(
        name="v2",
        version=v2_candidate.PROMPT_CONTRACT_VERSION,
        build_prompt=v2_candidate.build_prompt,
        check_format_valid=_check_format_valid,
        parse=_parse,
        parser_version=PARSER_VERSION,
        # Locked in test_prompt_contract_v2_fingerprint_parity.py and the
        # app repo's promptContractV2RuntimeParity.test.ts -- must change
        # together with both if the v2-candidate prompt template is ever
        # revised.
        expected_fingerprint="e691fd12ee51b322b93311cf483d2fbb4bb921ac8a1319e07420fae098ea0cb9",
    )
    return _v2_adapter_cache


_ADAPTER_BUILDERS: dict[str, Callable[[], ContractAdapter]] = {"v1": _v1_adapter, "v2": _v2_adapter}
DEFAULT_CONTRACT = "v1"

# Same fixture used by test_prepare_data.py (v1) and
# test_prompt_contract_v2_fingerprint_parity.py (v2) -- one shared source of
# truth for the preflight check below, not a third copy of the string.
# real_data_private is lightweight (hashlib/json/os only, no ML deps), safe
# to import eagerly.
PROMPT_CONTRACT_FIXTURE = rdp.PROMPT_CONTRACT_FIXTURE


def known_contract_names() -> list[str]:
    return sorted(_ADAPTER_BUILDERS)


def select_contract_adapter(name: str) -> ContractAdapter:
    """Fail-closed contract selection: raises ContractSelectionError, never
    returns a best-effort guess. Rendering and hashing the fixture is pure
    string/hash work -- no model loading, safe to call before any GPU/ML
    resource is touched. Building the v2 adapter (if selected) imports the
    v2 candidate/parser modules for the first time in this process -- v1
    selection never does."""
    if name not in _ADAPTER_BUILDERS:
        raise ContractSelectionError(
            f"unknown contract adapter {name!r} -- known adapters: {known_contract_names()}"
        )
    adapter = _ADAPTER_BUILDERS[name]()
    rendered = adapter.build_prompt(PROMPT_CONTRACT_FIXTURE)
    fingerprint = rdp.prompt_contract_fingerprint(rendered)
    if fingerprint != adapter.expected_fingerprint:
        raise ContractSelectionError(
            f"contract adapter {name!r} fingerprint mismatch: got {fingerprint}, "
            f"expected {adapter.expected_fingerprint} -- the prompt template may "
            "have changed without updating this lock; refusing to proceed."
        )
    return adapter


# The category that requires both count rules to be declared (never
# omitted, per source_determined_items_v2_acceptance_design_notes.md) --
# distinct from the protected 16-probe benchmark, which legitimately has no
# count rules at all and must keep working under v2 without acquiring them
# (per prompt_contract_vnext_adapter_structural_implementation_review.md's
# Finding 3).
V2_ACCEPTANCE_CATEGORY = "source_determined_items_v2"


def _validate_rule_shape(probe_id: object, rule_name: str, rule: object) -> None:
    if not isinstance(rule, dict):
        raise ContractSelectionError(f"{probe_id}: {rule_name} must be an object, got {type(rule).__name__}")
    extra_keys = set(rule) - {"operator", "value"}
    if extra_keys:
        raise ContractSelectionError(f"{probe_id}: {rule_name} has unrecognized keys: {sorted(extra_keys)}")
    if "operator" not in rule or "value" not in rule:
        raise ContractSelectionError(f"{probe_id}: {rule_name} must have exactly 'operator' and 'value'")
    operator = rule["operator"]
    if operator not in ("exact", "max"):
        raise ContractSelectionError(f"{probe_id}: {rule_name} has an unknown operator: {operator!r}")
    value = rule["value"]
    # isinstance(True, int) is True in Python -- bool must be excluded
    # explicitly, or a rule like {"operator": "exact", "value": true} would
    # silently be accepted as value=1.
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractSelectionError(
            f"{probe_id}: {rule_name}'s value must be a non-negative integer literal (not a bool), got {value!r}"
        )
    if value < 0:
        raise ContractSelectionError(f"{probe_id}: {rule_name}'s value must be non-negative, got {value!r}")


def probe_requires_v2_structural_verification(probe: dict) -> bool:
    """True if this probe's results must be routed through v2 structural
    verification (report_benchmark.py's verify_v2_structural_integrity) --
    driven entirely by the frozen, trusted probe definition, never by
    anything a result claims about itself (per
    prompt_contract_vnext_adapter_structural_implementation_review.md's
    Finding 2 reproduction #2: a result's own "contract" field must never
    be the thing that decides whether it gets checked). True whenever the
    probe is in the dedicated v2 acceptance category, or declares either
    count rule (covers any future non-acceptance probe that still opts
    into count checking).
    """
    return (
        probe.get("category") == V2_ACCEPTANCE_CATEGORY
        or probe.get("bullet_count_rule") is not None
        or probe.get("action_count_rule") is not None
    )


def preflight_validate_count_rules(probes: list[dict], adapter: ContractAdapter) -> None:
    """Design-notes requirement (source_determined_items_v2_acceptance_design_notes.md):
    duplicate case IDs, unknown count operators, malformed rule shapes, or
    a rule declared on only one of bullet_count_rule/action_count_rule
    must stop before model loading -- not surface as a confusing per-probe
    failure after an expensive generation run, and not silently default-
    pass. Every V2_ACCEPTANCE_CATEGORY case must declare both rules
    explicitly; the protected 16-probe benchmark is unaffected since it
    declares neither. No-op for adapters that don't support structural
    parsing (v1) -- called with the v1 adapter, this function does nothing
    at all, regardless of what the benchmark file contains.
    """
    if adapter.parse is None:
        return

    seen_ids: set = set()
    for probe in probes:
        pid = probe.get("id")
        if pid in seen_ids:
            raise ContractSelectionError(f"duplicate probe id in benchmark file: {pid!r}")
        seen_ids.add(pid)

        bullet_rule = probe.get("bullet_count_rule")
        action_rule = probe.get("action_count_rule")
        requires_rules = probe.get("category") == V2_ACCEPTANCE_CATEGORY

        if requires_rules and (bullet_rule is None or action_rule is None):
            raise ContractSelectionError(
                f"{pid}: {V2_ACCEPTANCE_CATEGORY} acceptance cases must declare both "
                "bullet_count_rule and action_count_rule (never omitted)"
            )
        if (bullet_rule is None) != (action_rule is None):
            raise ContractSelectionError(
                f"{pid}: declares only one of bullet_count_rule/action_count_rule -- "
                "both or neither is required"
            )
        for rule_name, rule in (("bullet_count_rule", bullet_rule), ("action_count_rule", action_rule)):
            if rule is not None:
                _validate_rule_shape(pid, rule_name, rule)


def evaluate_count_rule(rule: Optional[dict], actual: Optional[int]) -> Optional[dict]:
    """Single source of truth for "does this literal count satisfy this
    rule" -- used both at generation time (run_benchmark.py, writing
    bullet_count_result/action_count_result) and at report time
    (report_benchmark.py, independently recomputing the same thing to
    compare against what was stored). Keeping this in one place is the
    point: two independent copies of this logic would recreate exactly the
    class of drift bug (a fix landing in one copy but not the other) this
    project has already hit more than once.

    Returns None if no rule is declared (not applicable). `actual=None`
    (unparseable output) always fails a declared rule rather than raising,
    since a rule genuinely can't be satisfied by output with no countable
    structure -- distinct from a malformed operator, which does raise (and
    should already have been rejected by preflight_validate_count_rules
    long before this is ever called with a bad operator).
    """
    if rule is None:
        return None
    operator = rule.get("operator")
    value = rule.get("value")
    if operator == "exact":
        passed = actual is not None and actual == value
    elif operator == "max":
        passed = actual is not None and actual <= value
    else:
        raise ContractSelectionError(f"unknown count-rule operator: {operator!r}")
    return {"actual": actual, "rule": rule, "passed": passed}
