"""Local-only validator for the corrected-provider-schema diagnostic attestation."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import gate2

PACKAGE = Path(__file__).resolve().parent
EXPECTED = {
    "proposal_sha256": "3cd13bcc10bccde89456858de61ef6625285ea9655cf0d1761b45fd98da5518d",
    "provider_contract_sha256": "4312688168dd349f04bf4307816bded0b98edc9c358873f57fb5e347d2fe431c",
    "provider_schema_sha256": "b069fbf77d439030ee018f2a773bff07c06f0ded53108d8b98819ee0ba656812",
    "request_envelope_sha256": "8420c2d8360f4ffc96fb617dd8d4b081732cf2c87654a65d3ddc2ab8426297b4",
    "prior_error_message_capture_receipt_row_sha256": "26c28a6a90761d68c7ce1b6d771387e9bc6e7ae0785d6028c6cdc2beb3cf6b20",
    "execution_day_rate_snapshot_sha256": "a8664d906d7ebdf0ad14d46498062ee9de7999154c4a451722294f17e23472fe",
}
CAP = 10_680
TRUE_FIELDS = {
    "paid_tier_confirmed_that_day",
    "prepay_plan_confirmed_that_day",
    "auto_reload_off_that_day",
    "billing_account_currently_isolated_for_pilot",
    "no_unexpected_billing_activity_since_error_message_capture_diagnostic",
    "no_other_gemini_api_activity_since_error_message_capture_diagnostic",
    "corrected_schema_and_evidence_boundary_reviewed",
    "error_message_only_no_candidate_retention_confirmed",
    "one_request_authorized_by_johnny",
    "key_remains_in_user_controlled_encrypted_local_secret_store",
}


class Gate5AdditionalPropertiesDiagnosticAttestationError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5AdditionalPropertiesDiagnosticAttestationError("duplicate attestation key")
        value[key] = item
    return value


def validate_attestation(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Gate5AdditionalPropertiesDiagnosticAttestationError) as exc:
        raise Gate5AdditionalPropertiesDiagnosticAttestationError("attestation unreadable") from exc
    template = gate2.load_json(PACKAGE / "gate5_additional_properties_diagnostic_attestation_template.json")
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5AdditionalPropertiesDiagnosticAttestationError("attestation fields drifted")
    if value["artifact"] != "gemini_generator_gate5_additional_properties_diagnostic_attestation" or value["attestor"] != "Johnny" or value["execution_date"] != date.today().isoformat():
        raise Gate5AdditionalPropertiesDiagnosticAttestationError("attestation identity or date invalid")
    if any(value[name] != expected for name, expected in EXPECTED.items()):
        raise Gate5AdditionalPropertiesDiagnosticAttestationError("attestation evidence hash mismatch")
    if value["execution_day_rate_snapshot_status"] != "execution_day_verified" or any(value[field] is not True for field in TRUE_FIELDS):
        raise Gate5AdditionalPropertiesDiagnosticAttestationError("required corrected-schema diagnostic fact is unconfirmed")
    if type(value["positive_prepaid_balance_usd_millionths"]) is not int or value["positive_prepaid_balance_usd_millionths"] < CAP or value["cost_cap_usd_millionths"] != CAP:
        raise Gate5AdditionalPropertiesDiagnosticAttestationError("diagnostic cost or balance invalid")
    if gate2.contains_secret(value):
        raise Gate5AdditionalPropertiesDiagnosticAttestationError("secret-like value in attestation")
    return value
