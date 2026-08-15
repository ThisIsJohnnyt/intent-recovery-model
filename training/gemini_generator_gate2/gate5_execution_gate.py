"""Local-only validation of a future Gate 5 pre-execution attestation.

This has no provider transport or credential handling. It only refuses an
incomplete, stale, malformed, or secret-bearing attestation before a separately
reviewed future execution runner could be considered.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import gate2


PACKAGE = Path(__file__).resolve().parent
EXPECTED_CLOSURE_SHA256 = "de88228ee171e5458fdfbf6686097a0ad2877876bd1de28080dfb9c154677d49"
PILOT_CEILING = 3_000_000
RECONCILIATION_STOP = 2_250_000
TRUE_FIELDS = {
    "paid_tier_confirmed_that_day",
    "prepay_plan_confirmed_that_day",
    "auto_reload_off_that_day",
    "billing_account_currently_isolated_for_pilot",
    "no_unexpected_billing_activity_since_gate4",
    "no_other_activity_during_gate5_window",
    "both_exact_models_available_and_not_deprecated",
    "generate_content_endpoint_confirmed_for_both_models",
    "common_low_thinking_confirmed_for_both_models",
    "structured_output_field_confirmed_for_both_models",
    "response_usage_shape_confirmed",
    "one_candidate_nonstreaming_no_tools_confirmed",
    "fixed_24_slot_scope_confirmed",
    "pilot_execution_authorized_by_johnny",
    "key_remains_in_user_controlled_encrypted_local_secret_store",
}


class Gate5ExecutionGateError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5ExecutionGateError("duplicate attestation key")
        value[key] = item
    return value


def validate_attestation(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Gate5ExecutionGateError) as exc:
        raise Gate5ExecutionGateError("attestation unreadable") from exc
    template = gate2.load_json(PACKAGE / "gate5_pre_execution_attestation_template.json")
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5ExecutionGateError("attestation fields drifted")
    if value["artifact"] != "gemini_generator_gate5_pre_execution_attestation" or value["attestor"] != "Johnny":
        raise Gate5ExecutionGateError("attestation identity invalid")
    if value["execution_date"] != date.today().isoformat():
        raise Gate5ExecutionGateError("attestation is not same-day")
    if value["gate4_reconciliation_closure_sha256"] != EXPECTED_CLOSURE_SHA256:
        raise Gate5ExecutionGateError("Gate 4 closure mismatch")
    if any(value[field] is not True for field in TRUE_FIELDS):
        raise Gate5ExecutionGateError("required execution fact is unconfirmed")
    balance = value["positive_prepaid_balance_usd_millionths"]
    if not isinstance(balance, int) or balance < PILOT_CEILING:
        raise Gate5ExecutionGateError("prepaid balance is insufficient")
    if value["pilot_ceiling_usd_millionths"] != PILOT_CEILING or value["reconciliation_stop_usd_millionths"] != RECONCILIATION_STOP:
        raise Gate5ExecutionGateError("pilot cap drifted")
    for hash_field in ("final_provider_contract_sha256", "execution_day_rate_snapshot_sha256"):
        if not isinstance(value[hash_field], str) or not gate2.HEX64_RE.fullmatch(value[hash_field]):
            raise Gate5ExecutionGateError("required final artifact hash missing")
    if value["execution_day_rate_snapshot_status"] != "execution_day_verified":
        raise Gate5ExecutionGateError("rate snapshot is not execution-day verified")
    if gate2.contains_secret(value):
        raise Gate5ExecutionGateError("secret-like value in attestation")
    return value
