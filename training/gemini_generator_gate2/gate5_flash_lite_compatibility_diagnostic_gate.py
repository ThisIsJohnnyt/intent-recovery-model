"""Local-only validator for the Flash-Lite compatibility diagnostic attestation."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import gate2

PACKAGE = Path(__file__).resolve().parent
EXPECTED = {
    "proposal_sha256": "d5293b51622d55a9a060c752a489ca66bc8998a9abc4a1540c5fd335e9bfc9fe",
    "provider_contract_sha256": "4312688168dd349f04bf4307816bded0b98edc9c358873f57fb5e347d2fe431c",
    "provider_schema_sha256": "b069fbf77d439030ee018f2a773bff07c06f0ded53108d8b98819ee0ba656812",
    "request_body_sha256": "f940966f6d94654787e7185b30cd98f9d82e0806b7bf6a3a4c12a8cf85747559",
    "request_envelope_sha256": "afc687a97d24cec20c2cc11fafe8a9b5802fff438b9a7e72cd2084dcf86c7285",
    "successful_flash_receipt_row_sha256": "5d9c434994855bb81eaeb1fcbc4fce1746cd99a08b19715cbb3266bfd9ac0336",
    "execution_day_rate_snapshot_sha256": "f24991917538caf8bcf4340f18ef0a78cbdeadce6e14845b5fe28e69720ddca2",
}
CAP = 6_320
TRUE_FIELDS = {
    "paid_tier_confirmed_that_day",
    "prepay_plan_confirmed_that_day",
    "auto_reload_off_that_day",
    "billing_account_currently_isolated_for_pilot",
    "no_unexpected_billing_activity_since_successful_flash_diagnostic",
    "no_other_gemini_api_activity_since_successful_flash_diagnostic",
    "flash_lite_model_and_rates_rechecked_that_day",
    "flash_lite_request_and_evidence_boundary_reviewed",
    "status_only_no_candidate_retention_confirmed",
    "one_request_authorized_by_johnny",
    "key_remains_in_user_controlled_encrypted_local_secret_store",
}


class Gate5FlashLiteDiagnosticAttestationError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5FlashLiteDiagnosticAttestationError("duplicate attestation key")
        value[key] = item
    return value


def validate_attestation(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Gate5FlashLiteDiagnosticAttestationError) as exc:
        raise Gate5FlashLiteDiagnosticAttestationError("attestation unreadable") from exc
    template = gate2.load_json(PACKAGE / "gate5_flash_lite_compatibility_diagnostic_attestation_template.json")
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5FlashLiteDiagnosticAttestationError("attestation fields drifted")
    if value["artifact"] != "gemini_generator_gate5_flash_lite_compatibility_diagnostic_attestation" or value["attestor"] != "Johnny" or value["execution_date"] != date.today().isoformat():
        raise Gate5FlashLiteDiagnosticAttestationError("attestation identity or date invalid")
    if any(value[name] != expected for name, expected in EXPECTED.items()):
        raise Gate5FlashLiteDiagnosticAttestationError("attestation evidence hash mismatch")
    if value["execution_day_rate_snapshot_status"] != "execution_day_verified" or any(value[field] is not True for field in TRUE_FIELDS):
        raise Gate5FlashLiteDiagnosticAttestationError("required Flash-Lite diagnostic fact is unconfirmed")
    if type(value["positive_prepaid_balance_usd_millionths"]) is not int or value["positive_prepaid_balance_usd_millionths"] < CAP or value["cost_cap_usd_millionths"] != CAP:
        raise Gate5FlashLiteDiagnosticAttestationError("diagnostic cost or balance invalid")
    if gate2.contains_secret(value):
        raise Gate5FlashLiteDiagnosticAttestationError("secret-like value in attestation")
    return value
