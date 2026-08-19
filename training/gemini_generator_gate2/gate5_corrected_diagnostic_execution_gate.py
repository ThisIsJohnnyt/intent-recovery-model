"""Local-only validator for a future corrected-wire-format diagnostic attestation."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import gate2


PACKAGE = Path(__file__).resolve().parent
EXPECTED_PROPOSAL_SHA256 = "a7fb911034a15b8870adb88ed81beda7d5eb64e8ee8681dd6e1a08647da86dc5"
EXPECTED_CONTRACT_SHA256 = "5c47896310f9145ea62ec3fcea08d10038ff06f6125c632740222bd3d5f430ab"
EXPECTED_REQUEST_SHA256 = "0b0d3dfb09f428f6c447e3b97407f6aa966f6519f7ba2962a4cd15432b626e7b"
EXPECTED_PRIOR_SUMMARY_SHA256 = "47b3338740cbf04514f1223ce61fd20c57391779e68342819434b0a541be47ff"
EXPECTED_PRIOR_DIAGNOSTIC_ROW_SHA256 = "1264813444d9e846078bf766c0ddd46d63bfb3e4459bc58b32d24080eac7b86c"
EXPECTED_RATE_SHA256 = "a8664d906d7ebdf0ad14d46498062ee9de7999154c4a451722294f17e23472fe"
DIAGNOSTIC_CAP = 10_680
TRUE_FIELDS = {
    "paid_tier_confirmed_that_day",
    "prepay_plan_confirmed_that_day",
    "auto_reload_off_that_day",
    "billing_account_currently_isolated_for_pilot",
    "no_unexpected_billing_activity_since_prior_diagnostic",
    "no_other_gemini_api_activity_since_prior_diagnostic",
    "prior_failures_and_wire_correction_reviewed",
    "corrected_diagnostic_status_only_no_candidate_retention_confirmed",
    "corrected_diagnostic_one_request_authorized_by_johnny",
    "key_remains_in_user_controlled_encrypted_local_secret_store",
}


class Gate5CorrectedDiagnosticAttestationError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5CorrectedDiagnosticAttestationError("duplicate attestation key")
        value[key] = item
    return value


def validate_attestation(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Gate5CorrectedDiagnosticAttestationError) as exc:
        raise Gate5CorrectedDiagnosticAttestationError("attestation unreadable") from exc
    template = gate2.load_json(PACKAGE / "gate5_corrected_diagnostic_pre_execution_attestation_template.json")
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5CorrectedDiagnosticAttestationError("attestation fields drifted")
    if value["artifact"] != "gemini_generator_gate5_corrected_diagnostic_pre_execution_attestation" or value["attestor"] != "Johnny":
        raise Gate5CorrectedDiagnosticAttestationError("attestation identity invalid")
    if value["execution_date"] != date.today().isoformat():
        raise Gate5CorrectedDiagnosticAttestationError("attestation is not same-day")
    expected = {
        "diagnostic_proposal_sha256": EXPECTED_PROPOSAL_SHA256,
        "corrected_provider_contract_sha256": EXPECTED_CONTRACT_SHA256,
        "corrected_request_envelope_sha256": EXPECTED_REQUEST_SHA256,
        "prior_pilot_summary_sha256": EXPECTED_PRIOR_SUMMARY_SHA256,
        "prior_diagnostic_receipt_row_sha256": EXPECTED_PRIOR_DIAGNOSTIC_ROW_SHA256,
        "execution_day_rate_snapshot_sha256": EXPECTED_RATE_SHA256,
    }
    if any(value[name] != digest for name, digest in expected.items()):
        raise Gate5CorrectedDiagnosticAttestationError("attestation evidence hash mismatch")
    if value["execution_day_rate_snapshot_status"] != "execution_day_verified":
        raise Gate5CorrectedDiagnosticAttestationError("rate snapshot is not execution-day verified")
    if any(value[field] is not True for field in TRUE_FIELDS):
        raise Gate5CorrectedDiagnosticAttestationError("required corrected diagnostic fact is unconfirmed")
    if type(value["positive_prepaid_balance_usd_millionths"]) is not int or value["positive_prepaid_balance_usd_millionths"] < DIAGNOSTIC_CAP:
        raise Gate5CorrectedDiagnosticAttestationError("prepaid balance is insufficient")
    if value["corrected_diagnostic_cost_cap_usd_millionths"] != DIAGNOSTIC_CAP:
        raise Gate5CorrectedDiagnosticAttestationError("corrected diagnostic cap drifted")
    if gate2.contains_secret(value):
        raise Gate5CorrectedDiagnosticAttestationError("secret-like value in attestation")
    return value
