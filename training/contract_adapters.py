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

Each adapter bundles exactly what varies between contracts: how to build a
prompt, how to check structural (format) validity, and -- for contracts
that support per-item counting -- how to extract literal bullet/action
counts. Everything else (generation settings, result schema,
required_semantic_dimensions propagation, semantic scoring) is shared and
lives in run_benchmark.py/report_benchmark.py regardless of which adapter
is selected.

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
import prompt_contract_v2_candidate as v2_candidate
import real_data_private as rdp
from prompt_contract_v2_parser import ParseError, ParsedOutput, parse_output


class ContractSelectionError(ValueError):
    """Raised before any model loading: unknown adapter name, a fingerprint
    that doesn't match the locked value for that contract, or (via
    preflight_validate_count_rules) a malformed count-rule declaration in
    the benchmark file itself."""


@dataclass(frozen=True)
class CountExtraction:
    bullets: list[str]
    actions: list[str]


@dataclass(frozen=True)
class ContractAdapter:
    name: str
    version: str
    build_prompt: Callable[[str], str]
    check_format_valid: Callable[[str], bool]
    # None for contracts (v1) that don't define per-item structural counts.
    extract_counts: Optional[Callable[[str], CountExtraction]]
    expected_fingerprint: str


def _v2_check_format_valid(generated: str) -> bool:
    try:
        parse_output(generated)
        return True
    except ParseError:
        return False


def _v2_extract_counts(generated: str) -> CountExtraction:
    parsed: ParsedOutput = parse_output(generated)
    return CountExtraction(bullets=parsed.bullets, actions=parsed.actions)


# Same fixture used by test_prepare_data.py (v1) and
# test_prompt_contract_v2_fingerprint_parity.py (v2) -- one shared source of
# truth for the preflight check below, not a third copy of the string.
PROMPT_CONTRACT_FIXTURE = rdp.PROMPT_CONTRACT_FIXTURE

V1_ADAPTER = ContractAdapter(
    name="v1",
    version=prepare_data.PROMPT_CONTRACT_VERSION,
    build_prompt=prepare_data.build_prompt,
    check_format_valid=prepare_data.check_format_valid,
    extract_counts=None,
    # Locked in test_prepare_data.py -- must change together with that file
    # if the v1 prompt template is ever deliberately revised.
    expected_fingerprint="161661198071fd81310681f69381ec8e0287141e1e75b09d3a342414af31ccf1",
)

V2_ADAPTER = ContractAdapter(
    name="v2",
    version=v2_candidate.PROMPT_CONTRACT_VERSION,
    build_prompt=v2_candidate.build_prompt,
    check_format_valid=_v2_check_format_valid,
    extract_counts=_v2_extract_counts,
    # Locked in test_prompt_contract_v2_fingerprint_parity.py and the app
    # repo's promptContractV2RuntimeParity.test.ts -- must change together
    # with both if the v2-candidate prompt template is ever revised.
    expected_fingerprint="e691fd12ee51b322b93311cf483d2fbb4bb921ac8a1319e07420fae098ea0cb9",
)

CONTRACT_ADAPTERS: dict[str, ContractAdapter] = {"v1": V1_ADAPTER, "v2": V2_ADAPTER}
DEFAULT_CONTRACT = "v1"


def select_contract_adapter(name: str) -> ContractAdapter:
    """Fail-closed contract selection: raises ContractSelectionError, never
    returns a best-effort guess. Rendering and hashing the fixture is pure
    string/hash work -- no model loading, safe to call before any GPU/ML
    resource is touched."""
    if name not in CONTRACT_ADAPTERS:
        raise ContractSelectionError(
            f"unknown contract adapter {name!r} -- known adapters: {sorted(CONTRACT_ADAPTERS)}"
        )
    adapter = CONTRACT_ADAPTERS[name]
    rendered = adapter.build_prompt(PROMPT_CONTRACT_FIXTURE)
    fingerprint = rdp.prompt_contract_fingerprint(rendered)
    if fingerprint != adapter.expected_fingerprint:
        raise ContractSelectionError(
            f"contract adapter {name!r} fingerprint mismatch: got {fingerprint}, "
            f"expected {adapter.expected_fingerprint} -- the prompt template may "
            "have changed without updating this lock; refusing to proceed."
        )
    return adapter


def preflight_validate_count_rules(probes: list[dict], adapter: ContractAdapter) -> None:
    """Design-notes requirement (source_determined_items_v2_acceptance_design_notes.md):
    unknown count operators, or a rule declared on only one of
    bullet_count_rule/action_count_rule, must stop before model loading --
    not surface as a confusing per-probe failure after an expensive
    generation run. No-op for adapters that don't support counting (v1)."""
    if adapter.extract_counts is None:
        return
    for probe in probes:
        bullet_rule = probe.get("bullet_count_rule")
        action_rule = probe.get("action_count_rule")
        if (bullet_rule is None) != (action_rule is None):
            raise ContractSelectionError(
                f"{probe.get('id')}: declares only one of bullet_count_rule/"
                "action_count_rule -- both or neither is required"
            )
        for rule in (bullet_rule, action_rule):
            if rule is not None and rule.get("operator") not in ("exact", "max"):
                raise ContractSelectionError(
                    f"{probe.get('id')}: unknown count-rule operator {rule.get('operator')!r}"
                )


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
    structure -- distinct from a malformed operator, which does raise.
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
