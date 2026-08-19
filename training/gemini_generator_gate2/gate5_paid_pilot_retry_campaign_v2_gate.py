"""Local-only attestation gate for bounded paid-pilot retry campaign v2."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import gate2
import gate5_execution_gate as base
import gate5_paid_pilot_retry_campaign_gate as v1_gate

PACKAGE = Path(__file__).resolve().parent
MAX_CAMPAIGN_ATTEMPTS = 8
ATTESTED_BASELINE_COST = 32_040
INITIAL_HISTORICAL_COST = 42_720
INITIAL_COMPONENT_COUNT = 5
INITIAL_COMPONENT_MANIFEST_SHA256 = "da3e8f2022e1e0c444b9457d9e8333cdfaf6300f6fc1587bc9988ba5ed838be2"
EXPECTED_V2 = {
    "v2_campaign_proposal_sha256": "90d4d97a3a4085711b26be9040beed38555c06bb7d5aad451f1c2e5586574b06",
    "v1_final_attestation_sha256": "db6b6bec994cf707919d5a7b68d175aff45868ff7911485bc1af5201b2fb898b",
    "v1_terminal_campaign_state_sha256": "642e27695f12d62a07d227a0a027ebe9c2f4e88b2c3d0bb783ffe8e4313f9e04",
    "v1_attempt_1_lock_sha256": "4673ee5de671d42e2f42ee62402b52f3da8ec489ea3296007190a5c698b9f84a",
    "v1_attempt_1_completion_sha256": "ae620a732a49680e1f6cf071e37e01de480593776df27c5ff5b33adc8201b5c6",
    "v1_attempt_1_reservation_sha256": "b2e9325d914528a57439a00d0fb1f92f1f738e6d815b5c201b69483cb48b33cd",
    "v1_attempt_1_summary_sha256": "b7e6fdb2c878fcdd504fd47a5e3fb3894e81aabdeb51ccc8365397d27a171136",
    "v1_attempt_1_receipts_sha256": "6044b56813dbabdfc86a02acc8012ef17d513b2d7719eaae785df44b374f75d2",
    "v1_attempt_1_cost_sha256": "c882c301bf1f4c7e7589cac4f841768e458cba737d4d6611f73714b629201226",
    "v1_attempt_1_rejection_sha256": "3137726f1b6ea7a5d50e517001cd93578bd9441a6d7c108db10ece7ddc216c65",
    "v1_attempt_1_quarantine_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "v1_attempt_2_lock_sha256": "a4eaea187cbe58b0b6d7eae6ba3eabda7c812ef2d148727250160e15790da909",
    "v1_attempt_2_completion_sha256": "9aae7ee9ed94bac94734515674b93b842023adf61e338baccfb3c7daf8c7cd5d",
    "v2_initial_historical_component_manifest_sha256": INITIAL_COMPONENT_MANIFEST_SHA256,
}
TRUE_FIELDS = (v1_gate.TRUE_FIELDS - {
    "campaign_execution_authorized_by_johnny",
    "three_initial_cost_components_confirmed",
    "ten_attempt_campaign_bound_understood",
}) | {
    "v1_terminal_campaign_evidence_verified",
    "five_initial_cost_components_confirmed",
    "frozen_attested_baseline_separate_from_live_total_understood",
    "eight_attempt_campaign_bound_understood",
    "v2_campaign_execution_authorized_by_johnny",
}


class Gate5PaidPilotRetryCampaignV2AttestationError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5PaidPilotRetryCampaignV2AttestationError("duplicate attestation key")
        value[key] = item
    return value


def validate_attestation(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Gate5PaidPilotRetryCampaignV2AttestationError) as exc:
        raise Gate5PaidPilotRetryCampaignV2AttestationError("attestation unreadable") from exc
    template = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v2_attestation_template.json")
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5PaidPilotRetryCampaignV2AttestationError("attestation fields drifted")
    if value["artifact"] != "gemini_generator_gate5_paid_pilot_retry_campaign_v2_attestation" or value["attestor"] != "Johnny" or value["execution_date"] != date.today().isoformat():
        raise Gate5PaidPilotRetryCampaignV2AttestationError("attestation identity or date invalid")
    base_expected = {
        "gate4_reconciliation_closure_sha256": base.EXPECTED_CLOSURE_SHA256,
        "final_provider_contract_sha256": base.EXPECTED_PROVIDER_CONTRACT_SHA256,
        "final_provider_schema_sha256": base.EXPECTED_PROVIDER_SCHEMA_SHA256,
        "live_validated_request_envelope_sha256": base.EXPECTED_LIVE_REQUEST_SHA256,
        "successful_corrected_schema_diagnostic_receipt_row_sha256": base.EXPECTED_SUCCESS_RECEIPT_ROW_SHA256,
        "flash_lite_live_validated_request_envelope_sha256": base.EXPECTED_FLASH_LITE_REQUEST_SHA256,
        "successful_flash_lite_receipt_row_sha256": base.EXPECTED_FLASH_LITE_SUCCESS_RECEIPT_ROW_SHA256,
        **base.EXPECTED_FRESH,
        **base.EXPECTED_THIRD,
        **v1_gate.EXPECTED_CAMPAIGN,
        **EXPECTED_V2,
    }
    if any(value.get(name) != expected for name, expected in base_expected.items()):
        raise Gate5PaidPilotRetryCampaignV2AttestationError("v2 evidence mismatch")
    if any(value.get(field) is not True for field in TRUE_FIELDS):
        raise Gate5PaidPilotRetryCampaignV2AttestationError("required paid-pilot campaign v2 fact is unconfirmed")
    if value["execution_day_rate_snapshot_status"] != "execution_day_verified" or value["execution_day_rate_snapshot_sha256"] != "f24991917538caf8bcf4340f18ef0a78cbdeadce6e14845b5fe28e69720ddca2":
        raise Gate5PaidPilotRetryCampaignV2AttestationError("rate snapshot invalid")
    if type(value["positive_prepaid_balance_usd_millionths"]) is not int or value["positive_prepaid_balance_usd_millionths"] < base.PILOT_CEILING:
        raise Gate5PaidPilotRetryCampaignV2AttestationError("prepaid balance insufficient")
    expected_costs = (
        value["pilot_ceiling_usd_millionths"] == base.PILOT_CEILING,
        value["reconciliation_stop_usd_millionths"] == base.RECONCILIATION_STOP,
        value["maximum_campaign_attempts"] == MAX_CAMPAIGN_ATTEMPTS,
        value["initial_historical_component_count"] == INITIAL_COMPONENT_COUNT,
        value["original_failed_pilot_booked_cost_usd_millionths"] == 10_680,
        value["completed_fresh_pilot_booked_cost_usd_millionths"] == 10_680,
        value["third_pilot_booked_cost_usd_millionths"] == 10_680,
        value["prior_pilot_booked_cost_usd_millionths"] == ATTESTED_BASELINE_COST,
        value["v1_campaign_attempt_1_booked_cost_usd_millionths"] == 10_680,
        value["v1_campaign_attempt_2_booked_cost_usd_millionths"] == 0,
        value["v2_initial_historical_actual_usd_millionths"] == INITIAL_HISTORICAL_COST,
    )
    if not all(expected_costs):
        raise Gate5PaidPilotRetryCampaignV2AttestationError("v2 campaign cost or count drifted")
    if gate2.contains_secret(value):
        raise Gate5PaidPilotRetryCampaignV2AttestationError("secret-like value in attestation")
    return value
