"""Local-only attestation gate for the bounded paid-pilot retry campaign."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import gate2
import gate5_execution_gate as base

PACKAGE = Path(__file__).resolve().parent
MAX_CAMPAIGN_ATTEMPTS = 10
INITIAL_HISTORICAL_COST = 32_040
INITIAL_COMPONENT_COUNT = 3
INITIAL_COMPONENT_MANIFEST_SHA256 = "39a3889e9db4e51e483d3d15ab344558ff16fefb56e1dadd3541e7a9102beb7d"
EXPECTED_CAMPAIGN = {
    "pilot_retry_campaign_proposal_sha256": "8236ecc8df2ae88023cfc0b96ec3682a691c7864ad9d171cfd80e586b334ce14",
    "third_pilot_final_attestation_sha256": "3a8078ec873a0b77c8848c431fef47453e8323bab8ba23dbf62b109a2a3d6671",
    "third_pilot_reservation_file_sha256": "14ae47b46b0263752757bfc10fa3bfef5581c61b83a4f4c3aeec05d5cb4fbf0a",
    "third_pilot_summary_file_sha256": "23fd84fd59ad9455e14429363617e3906e75802d78713da1ce67902dc2efd6e3",
    "third_pilot_receipts_file_sha256": "6044b56813dbabdfc86a02acc8012ef17d513b2d7719eaae785df44b374f75d2",
    "third_pilot_cost_file_sha256": "a74aad50c129660c0bd976b0586797e46c4c0a4ff0729894efcd42c46f854ca5",
    "third_pilot_rejection_file_sha256": "3137726f1b6ea7a5d50e517001cd93578bd9441a6d7c108db10ece7ddc216c65",
    "third_pilot_quarantine_file_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "third_pilot_receipt_row_sha256": "057b1138e8297ff7ceee61e172b349ea31a17499b47b4eca653e3a00b9918c02",
    "third_pilot_raw_response_sha256": "01f5c7d4e4d8ec06c8098777e731b3d552ba518feb02b681f6c569edcd9c6f6d",
    "initial_historical_component_manifest_sha256": INITIAL_COMPONENT_MANIFEST_SHA256,
}
TRUE_FIELDS = (base.TRUE_FIELDS - {"pilot_execution_authorized_by_johnny", "third_full_24_slot_attempt_confirmed"}) | {
    "third_pilot_evidence_verified", "three_initial_cost_components_confirmed",
    "manual_full_attempt_invocation_only_understood", "clean_503_only_continuation_understood",
    "all_other_outcomes_terminal_understood", "ten_attempt_campaign_bound_understood",
    "campaign_execution_authorized_by_johnny",
}


class Gate5PaidPilotRetryCampaignAttestationError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5PaidPilotRetryCampaignAttestationError("duplicate attestation key")
        value[key] = item
    return value


def validate_attestation(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Gate5PaidPilotRetryCampaignAttestationError) as exc:
        raise Gate5PaidPilotRetryCampaignAttestationError("attestation unreadable") from exc
    template = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_attestation_template.json")
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5PaidPilotRetryCampaignAttestationError("attestation fields drifted")
    if value["artifact"] != "gemini_generator_gate5_paid_pilot_retry_campaign_attestation" or value["attestor"] != "Johnny" or value["execution_date"] != date.today().isoformat():
        raise Gate5PaidPilotRetryCampaignAttestationError("attestation identity or date invalid")
    base_expected = {"gate4_reconciliation_closure_sha256": base.EXPECTED_CLOSURE_SHA256, "final_provider_contract_sha256": base.EXPECTED_PROVIDER_CONTRACT_SHA256, "final_provider_schema_sha256": base.EXPECTED_PROVIDER_SCHEMA_SHA256, "live_validated_request_envelope_sha256": base.EXPECTED_LIVE_REQUEST_SHA256, "successful_corrected_schema_diagnostic_receipt_row_sha256": base.EXPECTED_SUCCESS_RECEIPT_ROW_SHA256, "flash_lite_live_validated_request_envelope_sha256": base.EXPECTED_FLASH_LITE_REQUEST_SHA256, "successful_flash_lite_receipt_row_sha256": base.EXPECTED_FLASH_LITE_SUCCESS_RECEIPT_ROW_SHA256, **base.EXPECTED_FRESH, **base.EXPECTED_THIRD}
    if any(value[name] != expected for name, expected in {**base_expected, **EXPECTED_CAMPAIGN}.items()):
        raise Gate5PaidPilotRetryCampaignAttestationError("campaign evidence mismatch")
    if any(value[field] is not True for field in TRUE_FIELDS):
        raise Gate5PaidPilotRetryCampaignAttestationError("required paid-pilot campaign fact is unconfirmed")
    if value["execution_day_rate_snapshot_status"] != "execution_day_verified" or value["execution_day_rate_snapshot_sha256"] != "f24991917538caf8bcf4340f18ef0a78cbdeadce6e14845b5fe28e69720ddca2":
        raise Gate5PaidPilotRetryCampaignAttestationError("rate snapshot invalid")
    if type(value["positive_prepaid_balance_usd_millionths"]) is not int or value["positive_prepaid_balance_usd_millionths"] < base.PILOT_CEILING:
        raise Gate5PaidPilotRetryCampaignAttestationError("prepaid balance insufficient")
    if value["pilot_ceiling_usd_millionths"] != base.PILOT_CEILING or value["reconciliation_stop_usd_millionths"] != base.RECONCILIATION_STOP or value["maximum_campaign_attempts"] != MAX_CAMPAIGN_ATTEMPTS or value["initial_historical_component_count"] != INITIAL_COMPONENT_COUNT or value["original_failed_pilot_booked_cost_usd_millionths"] != 10_680 or value["completed_fresh_pilot_booked_cost_usd_millionths"] != 10_680 or value["third_pilot_booked_cost_usd_millionths"] != 10_680 or value["prior_pilot_booked_cost_usd_millionths"] != INITIAL_HISTORICAL_COST:
        raise Gate5PaidPilotRetryCampaignAttestationError("campaign cost or count drifted")
    if gate2.contains_secret(value):
        raise Gate5PaidPilotRetryCampaignAttestationError("secret-like value in attestation")
    return value
