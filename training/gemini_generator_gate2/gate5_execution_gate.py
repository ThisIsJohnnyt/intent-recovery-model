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
EXPECTED_PROVIDER_SCHEMA_SHA256 = "b069fbf77d439030ee018f2a773bff07c06f0ded53108d8b98819ee0ba656812"
EXPECTED_LIVE_REQUEST_SHA256 = "8420c2d8360f4ffc96fb617dd8d4b081732cf2c87654a65d3ddc2ab8426297b4"
EXPECTED_SUCCESS_RECEIPT_ROW_SHA256 = "5d9c434994855bb81eaeb1fcbc4fce1746cd99a08b19715cbb3266bfd9ac0336"
EXPECTED_FLASH_LITE_REQUEST_SHA256 = "afc687a97d24cec20c2cc11fafe8a9b5802fff438b9a7e72cd2084dcf86c7285"
EXPECTED_FLASH_LITE_SUCCESS_RECEIPT_ROW_SHA256 = "ce51e891c2960edb91fbb67ac9fc210fa900609f1ffd1bcd8f91513d3c1c186b"
EXPECTED_PROVIDER_CONTRACT_SHA256 = "4312688168dd349f04bf4307816bded0b98edc9c358873f57fb5e347d2fe431c"
EXPECTED_SCHEDULE_SHA256 = "aff503c2dce8428cf83d6e25fa1e06e07d2ce9fedd06cc805f186b1be3e9b87a"
EXPECTED_FRESH = {
    "fresh_attempt_proposal_sha256": "22aea6a7b2286a4eaf547210f8d7279bcb105e404de4c2341e5e9ee8340f7a18",
    "corrected_response_parser_sha256": "aef817fa39e72591be92a27cfb577746605e004b8e2394f7b6ee3f2d50bae14e",
    "successful_response_shape_campaign_receipt_file_sha256": "9110781bdd431e66b13d465551893c8be7402c916afda285ff06d082d0b4ac22",
    "successful_response_shape_campaign_receipt_row_sha256": "2f4068298f4fbd65b586fb09584fbc733009bda77571d176c06d4029357732f0",
    "successful_response_shape_campaign_state_file_sha256": "aa8f77a2c3dd2d2c22105470219bf5d6a676afc4861e2511c19e780d61a26a78",
    "prior_failed_pilot_summary_file_sha256": "627ba8dfba9410a1201907f7d5eb2cce69b2d9f41111cd8c4e84f540f1c16050",
    "prior_failed_pilot_receipts_file_sha256": "b30e21d29868db74d9cee9719f2f8c1f002cc40ff1f5557224e658e3861e62c4",
    "prior_failed_pilot_cost_file_sha256": "0c39db795f4ff4a75a199af8b0f8a11ffe08663d67a8148015dd8bd0a47703ae",
    "prior_failed_pilot_rejection_file_sha256": "3b1cec5c6c37d0fce25b533a9ba890d3d44d7acc53e3bef9683ec13438634423",
    "schedule_sha256": EXPECTED_SCHEDULE_SHA256,
}
EXPECTED_THIRD = {
    "third_attempt_proposal_sha256": "c401bfa6e63fedf110c812f11f828be69439f47c0fd12469b5f376f28a74b2f8",
    "completed_fresh_pilot_reservation_file_sha256": "aa91f8d811adb31644b0d86021781bf7a97aa0658e1e03f2876fd8ccfc4cb970",
    "completed_fresh_pilot_summary_file_sha256": "16d624cc6b8d698bf3a34bce5f919eba38f9bc4babe7fc8ed50981568bcc9169",
    "completed_fresh_pilot_receipts_file_sha256": "fd290052ddeeec186b62d768f89122185509d94af72139ac85443bf79a8d4105",
    "completed_fresh_pilot_cost_file_sha256": "c90f5a8dd089d5a1e1e5f0b2a7c699346101ce24b84b1b47cc5713ca39f01413",
    "completed_fresh_pilot_rejection_file_sha256": "20db77f940829a50b4b06eae3bfe07f4e6539d89f4ea89f912444484341544d3",
    "completed_fresh_pilot_quarantine_file_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
}
ORIGINAL_FAILED_PILOT_BOOKED_COST = 10_680
COMPLETED_FRESH_PILOT_BOOKED_COST = 10_680
PRIOR_PILOT_BOOKED_COST = ORIGINAL_FAILED_PILOT_BOOKED_COST + COMPLETED_FRESH_PILOT_BOOKED_COST
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
    "corrected_schema_live_diagnostic_http_200_confirmed",
    "flash_lite_live_diagnostic_http_200_confirmed",
    "fixed_24_slot_scope_confirmed",
    "prior_failed_pilot_evidence_verified",
    "successful_campaign_response_shape_verified",
    "corrected_parser_verified",
    "historical_pilot_cost_carry_forward_confirmed",
    "completed_fresh_pilot_evidence_verified",
    "two_historical_cost_components_confirmed",
    "third_full_24_slot_attempt_confirmed",
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
    if value["final_provider_contract_sha256"] != EXPECTED_PROVIDER_CONTRACT_SHA256 or value["final_provider_schema_sha256"] != EXPECTED_PROVIDER_SCHEMA_SHA256 or value["live_validated_request_envelope_sha256"] != EXPECTED_LIVE_REQUEST_SHA256 or value["successful_corrected_schema_diagnostic_receipt_row_sha256"] != EXPECTED_SUCCESS_RECEIPT_ROW_SHA256 or value["flash_lite_live_validated_request_envelope_sha256"] != EXPECTED_FLASH_LITE_REQUEST_SHA256 or value["successful_flash_lite_receipt_row_sha256"] != EXPECTED_FLASH_LITE_SUCCESS_RECEIPT_ROW_SHA256:
        raise Gate5ExecutionGateError("live-validated provider evidence mismatch")
    if any(value[field] != expected for field, expected in EXPECTED_FRESH.items()):
        raise Gate5ExecutionGateError("fresh-attempt evidence mismatch")
    if any(value[field] != expected for field, expected in EXPECTED_THIRD.items()):
        raise Gate5ExecutionGateError("third-attempt evidence mismatch")
    if any(value[field] is not True for field in TRUE_FIELDS):
        raise Gate5ExecutionGateError("required execution fact is unconfirmed")
    balance = value["positive_prepaid_balance_usd_millionths"]
    if not isinstance(balance, int) or balance < PILOT_CEILING:
        raise Gate5ExecutionGateError("prepaid balance is insufficient")
    if value["pilot_ceiling_usd_millionths"] != PILOT_CEILING or value["reconciliation_stop_usd_millionths"] != RECONCILIATION_STOP or value["original_failed_pilot_booked_cost_usd_millionths"] != ORIGINAL_FAILED_PILOT_BOOKED_COST or value["completed_fresh_pilot_booked_cost_usd_millionths"] != COMPLETED_FRESH_PILOT_BOOKED_COST or value["prior_pilot_booked_cost_usd_millionths"] != PRIOR_PILOT_BOOKED_COST:
        raise Gate5ExecutionGateError("pilot cap drifted")
    for hash_field in ("final_provider_contract_sha256", "final_provider_schema_sha256", "live_validated_request_envelope_sha256", "successful_corrected_schema_diagnostic_receipt_row_sha256", "flash_lite_live_validated_request_envelope_sha256", "successful_flash_lite_receipt_row_sha256", "execution_day_rate_snapshot_sha256", *EXPECTED_FRESH, *EXPECTED_THIRD):
        if not isinstance(value[hash_field], str) or not gate2.HEX64_RE.fullmatch(value[hash_field]):
            raise Gate5ExecutionGateError("required final artifact hash missing")
    if value["execution_day_rate_snapshot_status"] != "execution_day_verified":
        raise Gate5ExecutionGateError("rate snapshot is not execution-day verified")
    if gate2.contains_secret(value):
        raise Gate5ExecutionGateError("secret-like value in attestation")
    return value
