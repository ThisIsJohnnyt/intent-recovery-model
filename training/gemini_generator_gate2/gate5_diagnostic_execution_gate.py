"""Local-only validator for a future one-request Gate 5 diagnostic attestation."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import gate2


PACKAGE = Path(__file__).resolve().parent
EXPECTED_PROPOSAL_SHA256 = "b42a5d3a43893b53b17714abc1587f1a926270a9425e8b0fb285c9ff523830fb"
EXPECTED_PRIOR_SUMMARY_SHA256 = "47b3338740cbf04514f1223ce61fd20c57391779e68342819434b0a541be47ff"
EXPECTED_CONTRACT_SHA256 = "5a14775f67a520d0d80d6b55e23b46351ece4abd7afb3b389fff3e4752bc5d51"
EXPECTED_RATE_SHA256 = "a8664d906d7ebdf0ad14d46498062ee9de7999154c4a451722294f17e23472fe"
DIAGNOSTIC_CAP = 10_680
TRUE_FIELDS = {
    "paid_tier_confirmed_that_day",
    "prepay_plan_confirmed_that_day",
    "auto_reload_off_that_day",
    "billing_account_currently_isolated_for_pilot",
    "no_unexpected_billing_activity_since_prior_pilot",
    "no_other_gemini_api_activity_since_prior_pilot",
    "prior_pilot_failure_reviewed",
    "original_24_slot_pilot_not_resumed",
    "diagnostic_status_only_no_candidate_retention_confirmed",
    "diagnostic_one_request_authorized_by_johnny",
    "key_remains_in_user_controlled_encrypted_local_secret_store",
}


class Gate5DiagnosticAttestationError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5DiagnosticAttestationError("duplicate attestation key")
        value[key] = item
    return value


def validate_attestation(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Gate5DiagnosticAttestationError) as exc:
        raise Gate5DiagnosticAttestationError("attestation unreadable") from exc
    template = gate2.load_json(PACKAGE / "gate5_diagnostic_pre_execution_attestation_template.json")
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5DiagnosticAttestationError("attestation fields drifted")
    if value["artifact"] != "gemini_generator_gate5_diagnostic_pre_execution_attestation" or value["attestor"] != "Johnny":
        raise Gate5DiagnosticAttestationError("attestation identity invalid")
    if value["execution_date"] != date.today().isoformat():
        raise Gate5DiagnosticAttestationError("attestation is not same-day")
    expected_hashes = {
        "diagnostic_proposal_sha256": EXPECTED_PROPOSAL_SHA256,
        "prior_pilot_summary_sha256": EXPECTED_PRIOR_SUMMARY_SHA256,
        "final_provider_contract_sha256": EXPECTED_CONTRACT_SHA256,
        "execution_day_rate_snapshot_sha256": EXPECTED_RATE_SHA256,
    }
    if any(value[name] != expected for name, expected in expected_hashes.items()):
        raise Gate5DiagnosticAttestationError("attestation evidence hash mismatch")
    if value["execution_day_rate_snapshot_status"] != "execution_day_verified":
        raise Gate5DiagnosticAttestationError("rate snapshot is not execution-day verified")
    if any(value[field] is not True for field in TRUE_FIELDS):
        raise Gate5DiagnosticAttestationError("required diagnostic fact is unconfirmed")
    if type(value["positive_prepaid_balance_usd_millionths"]) is not int or value["positive_prepaid_balance_usd_millionths"] < DIAGNOSTIC_CAP:
        raise Gate5DiagnosticAttestationError("prepaid balance is insufficient")
    if value["diagnostic_cost_cap_usd_millionths"] != DIAGNOSTIC_CAP:
        raise Gate5DiagnosticAttestationError("diagnostic cost cap drifted")
    if gate2.contains_secret(value):
        raise Gate5DiagnosticAttestationError("secret-like value in attestation")
    return value
