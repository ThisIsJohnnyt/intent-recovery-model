"""Local-only validator for a future error-message-capture diagnostic attestation."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import gate2

PACKAGE = Path(__file__).resolve().parent
EXPECTED = {
    "proposal_sha256": "4f2f8cacee4f316adf7c99e7842bfde7c4937c99204d298405da397a4dcd7aa5",
    "provider_contract_sha256": "fecaa69bbea4a0e16749e7537b0ab1720cd6d386a19cd4736cfb436bcb11f96d",
    "provider_schema_sha256": "f42d19f841aa95949ce075cd0ec80c63f1a930fbb023c5f3eb4543d5cdc376c9",
    "request_envelope_sha256": "ab9757d003cf09dd06ecf55b435c10bd676932d92f7989417baa6d17f4f29379",
    "prior_provider_schema_diagnostic_receipt_row_sha256": "64147baa85ca4e81e2aec7b065b36d35c046ba2f6c7f52f70e7312390eaeb981",
    "execution_day_rate_snapshot_sha256": "a8664d906d7ebdf0ad14d46498062ee9de7999154c4a451722294f17e23472fe",
}
CAP = 10_680
TRUE_FIELDS = {
    "paid_tier_confirmed_that_day",
    "prepay_plan_confirmed_that_day",
    "auto_reload_off_that_day",
    "billing_account_currently_isolated_for_pilot",
    "no_unexpected_billing_activity_since_provider_schema_diagnostic_retry",
    "no_other_gemini_api_activity_since_provider_schema_diagnostic_retry",
    "prior_failures_and_error_message_capture_plan_reviewed",
    "error_message_only_no_candidate_retention_confirmed",
    "one_request_authorized_by_johnny",
    "key_remains_in_user_controlled_encrypted_local_secret_store",
}


class Gate5ErrorMessageCaptureAttestationError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5ErrorMessageCaptureAttestationError("duplicate attestation key")
        value[key] = item
    return value


def validate_attestation(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Gate5ErrorMessageCaptureAttestationError) as exc:
        raise Gate5ErrorMessageCaptureAttestationError("attestation unreadable") from exc
    template = gate2.load_json(PACKAGE / "gate5_error_message_capture_diagnostic_attestation_template.json")
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5ErrorMessageCaptureAttestationError("attestation fields drifted")
    if value["artifact"] != "gemini_generator_gate5_error_message_capture_diagnostic_attestation" or value["attestor"] != "Johnny" or value["execution_date"] != date.today().isoformat():
        raise Gate5ErrorMessageCaptureAttestationError("attestation identity or date invalid")
    if any(value[name] != expected for name, expected in EXPECTED.items()):
        raise Gate5ErrorMessageCaptureAttestationError("attestation evidence hash mismatch")
    if value["execution_day_rate_snapshot_status"] != "execution_day_verified" or any(value[field] is not True for field in TRUE_FIELDS):
        raise Gate5ErrorMessageCaptureAttestationError("required error-message diagnostic fact is unconfirmed")
    if type(value["positive_prepaid_balance_usd_millionths"]) is not int or value["positive_prepaid_balance_usd_millionths"] < CAP or value["cost_cap_usd_millionths"] != CAP:
        raise Gate5ErrorMessageCaptureAttestationError("diagnostic cost or balance invalid")
    if gate2.contains_secret(value):
        raise Gate5ErrorMessageCaptureAttestationError("secret-like value in attestation")
    return value
