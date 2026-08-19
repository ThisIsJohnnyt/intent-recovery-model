"""Local-only attestation gate for paid-pilot retry campaign v3."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import gate2
import gate5_execution_gate as base
import gate5_paid_pilot_retry_campaign_v2_gate as v2_gate

PACKAGE = Path(__file__).resolve().parent
MAX_CAMPAIGN_ATTEMPTS = 7
ATTESTED_BASELINE_COST = 53_400
INITIAL_HISTORICAL_COST = 53_400
INITIAL_COMPONENT_COUNT = 6
INITIAL_COMPONENT_MANIFEST_SHA256 = "568ec00a1a7ad2d9c73ed91a6800f676e1ece4ff0bdd950540503c0531434b80"
HASH_RE = re.compile(r"[0-9a-f]{64}")
EXPECTED_V3 = {
    "v3_campaign_proposal_sha256": "c13b7ea7a6486b4f9eb8c7dc5abe224b343a6201a9f5ea75e985efb36a9ba2db",
    "output_collision_evidence_proposal_sha256": "dc5cf11c125d9618cafee13fd972ec41994679f4cd9c9afb6968dbb3f88c178c",
    "structured_collision_gate2_sha256": "65e5808fb6891f70a7e15e13eaf3360d81d2dffd35fc120c37dc3cdad7bf6391",
    "output_collision_evidence_module_sha256": "f58e189e3cb28d7437758ff497801cefc1a37eaa9cb82488f4992094b20de00a",
    "output_collision_integrated_paid_runner_sha256": "1e751fbed0f33fbae2caa0bc6a657d7135e55bb836233bfa5ac636013e169787",
    "output_collision_focused_tests_sha256": "0aa639782bced398778b1747b531b43516f96a2a2b98b41bd34dc3d26d80993f",
    "v3_campaign_runner_sha256": "9ce3b0b41a15ae4ec19fde3581e5abfa3aa1e5a3ca3884484f119d0fcb46afcd",
    "v3_campaign_tests_sha256": "e79c0a664cfa6ba360b33bab4ac66e7b3c812129b0efbe8d3f59e4671895fdb2",
    "v2_final_attestation_sha256": "b1e70f5d177c262932e9018b6352483974401397004011e652ac5850669a3e58",
    "v2_terminal_campaign_state_sha256": "842e12e5d77e6329e4b0da4e565bae2dfbbfdaaf210056a19f8810fcba0c75b8",
    "v2_attempt_1_lock_sha256": "3b63928fce7ed78d0f6f0021ce9ca0ead903f8f274294cd10b27ec745ea893e5",
    "v2_attempt_1_completion_sha256": "383638a9eab8aa7ae5df981603e927af4effc81c216d07171441fb18c70888cd",
    "v2_attempt_1_reservation_sha256": "34383815f8d080f9a605ce232497f861510291961738dbe662f15e4857bfa1ef",
    "v2_attempt_1_receipts_sha256": "2d37648f9c64f0fe2a1467ffe4d9b577d9c99341ab64002fc7a311ce129d7cbe",
    "v2_attempt_1_rejection_sha256": "b4daa64e3061cddb17d3e49642e29321e9e67477ef6fc307ce6c95482a8ab646",
    "v2_attempt_1_cost_sha256": "48c7fbbb28d7c4a11e18a5f3a79468f333c0848ca45793020a0d19f5bcd2826f",
    "v2_attempt_1_quarantine_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "v2_attempt_1_summary_sha256": "5f4583791f91e2d65f6a492a542c59b36802dc1af96c21574d87f4950c8b32ca",
    "v3_initial_historical_component_manifest_sha256": INITIAL_COMPONENT_MANIFEST_SHA256,
}
TRUE_FIELDS = (v2_gate.TRUE_FIELDS - {
    "v2_campaign_execution_authorized_by_johnny",
    "v1_terminal_campaign_evidence_verified",
    "five_initial_cost_components_confirmed",
    "eight_attempt_campaign_bound_understood",
}) | {
    "v2_terminal_campaign_evidence_verified",
    "six_initial_cost_components_confirmed",
    "seven_attempt_campaign_bound_understood",
    "output_collision_evidence_build_verified",
    "output_collision_text_exclusion_understood",
    "diagnostic_persistence_failure_terminal_understood",
    "v3_campaign_execution_authorized_by_johnny",
}


class Gate5PaidPilotRetryCampaignV3AttestationError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5PaidPilotRetryCampaignV3AttestationError("duplicate attestation key")
        value[key] = item
    return value


def validate_attestation(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Gate5PaidPilotRetryCampaignV3AttestationError) as exc:
        raise Gate5PaidPilotRetryCampaignV3AttestationError("attestation unreadable") from exc
    template = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v3_attestation_template.json")
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5PaidPilotRetryCampaignV3AttestationError("attestation fields drifted")
    if value["artifact"] != "gemini_generator_gate5_paid_pilot_retry_campaign_v3_attestation" or value["attestor"] != "Johnny" or value["execution_date"] != date.today().isoformat():
        raise Gate5PaidPilotRetryCampaignV3AttestationError("attestation identity or date invalid")
    expected = {
        "gate4_reconciliation_closure_sha256": base.EXPECTED_CLOSURE_SHA256,
        "final_provider_contract_sha256": base.EXPECTED_PROVIDER_CONTRACT_SHA256,
        "final_provider_schema_sha256": base.EXPECTED_PROVIDER_SCHEMA_SHA256,
        "live_validated_request_envelope_sha256": base.EXPECTED_LIVE_REQUEST_SHA256,
        "successful_corrected_schema_diagnostic_receipt_row_sha256": base.EXPECTED_SUCCESS_RECEIPT_ROW_SHA256,
        "flash_lite_live_validated_request_envelope_sha256": base.EXPECTED_FLASH_LITE_REQUEST_SHA256,
        "successful_flash_lite_receipt_row_sha256": base.EXPECTED_FLASH_LITE_SUCCESS_RECEIPT_ROW_SHA256,
        **base.EXPECTED_FRESH,
        **base.EXPECTED_THIRD,
        **v2_gate.v1_gate.EXPECTED_CAMPAIGN,
        **v2_gate.EXPECTED_V2,
        **EXPECTED_V3,
    }
    if any(value.get(name) != item for name, item in expected.items()):
        raise Gate5PaidPilotRetryCampaignV3AttestationError("v3 evidence mismatch")
    if any(value.get(field) is not True for field in TRUE_FIELDS):
        raise Gate5PaidPilotRetryCampaignV3AttestationError("required paid-pilot campaign v3 fact is unconfirmed")
    rate_hash = value.get("execution_day_rate_snapshot_sha256")
    if value.get("execution_day_rate_snapshot_status") != "execution_day_verified" or not isinstance(rate_hash, str) or not HASH_RE.fullmatch(rate_hash):
        raise Gate5PaidPilotRetryCampaignV3AttestationError("rate snapshot invalid")
    if type(value.get("positive_prepaid_balance_usd_millionths")) is not int or value["positive_prepaid_balance_usd_millionths"] < base.PILOT_CEILING:
        raise Gate5PaidPilotRetryCampaignV3AttestationError("prepaid balance insufficient")
    expected_costs = (
        value.get("pilot_ceiling_usd_millionths") == base.PILOT_CEILING,
        value.get("reconciliation_stop_usd_millionths") == base.RECONCILIATION_STOP,
        value.get("maximum_campaign_attempts") == MAX_CAMPAIGN_ATTEMPTS,
        value.get("initial_historical_component_count") == INITIAL_COMPONENT_COUNT,
        value.get("original_failed_pilot_booked_cost_usd_millionths") == 10_680,
        value.get("completed_fresh_pilot_booked_cost_usd_millionths") == 10_680,
        value.get("third_pilot_booked_cost_usd_millionths") == 10_680,
        value.get("prior_pilot_booked_cost_usd_millionths") == ATTESTED_BASELINE_COST,
        value.get("v1_campaign_attempt_1_booked_cost_usd_millionths") == 10_680,
        value.get("v1_campaign_attempt_2_booked_cost_usd_millionths") == 0,
        value.get("v2_campaign_attempt_1_booked_cost_usd_millionths") == 10_680,
        value.get("v3_initial_historical_actual_usd_millionths") == INITIAL_HISTORICAL_COST,
        value.get("v3_worst_case_aggregate_usd_millionths") == 1_481_400,
    )
    if not all(expected_costs):
        raise Gate5PaidPilotRetryCampaignV3AttestationError("v3 campaign cost or count drifted")
    if gate2.contains_secret(value):
        raise Gate5PaidPilotRetryCampaignV3AttestationError("secret-like value in attestation")
    return value
