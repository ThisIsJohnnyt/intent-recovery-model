"""Local-only attestation gate for the Gate 5 paid-pilot v4 campaign."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import gate2
import gate5_paid_pilot_runner as pilot


PACKAGE = Path(__file__).resolve().parent
MAX_CAMPAIGN_ATTEMPTS = 4
ATTESTED_BASELINE_COST = 85_440
INITIAL_COMPONENT_COUNT = 9
INITIAL_COMPONENT_MANIFEST_SHA256 = "17980710e16ddab4ed822fae8beebe21a2662df6f45317200efc977e6a6e0993"
HASH_RE = re.compile(r"[0-9a-f]{64}")
EXPECTED_V3 = {
    "v3_final_attestation_sha256": "d2b43f895b79e50fd7c268ae2d4ea7dc7b164f5dc30b838e39170ba955d5cc11",
    "v3_terminal_campaign_state_sha256": "b6ce772b8e924cfa2251a87f402bf8bc26807dc9d3570ac1b65c659b2967ce27",
    "v3_terminal_component_row_sha256": "c1643a53b1940517bdbec8beff4a286c68f7d477c5caf00357b502fd3e4ee16e",
    "v3_initial_historical_component_manifest_sha256": INITIAL_COMPONENT_MANIFEST_SHA256,
}
EXPECTED_BUILD = {
    "v4_proposal_sha256": "2fba9160bf75df3076ca23ece63a7af92d0542f076106aa3caadff6e48c8b30e",
    "structured_schema_gate2_sha256": "d8de37186e0dbb7f33a4cca2e2e746f1c11bf34749c8a817b5db69751fac4da0",
    "schema_conformance_evidence_module_sha256": "a41669caccdbcabb10ff803b78152d8e0cf99e87580b8911dd3c3e1cc4d1bf9b",
    "schema_integrated_paid_runner_sha256": "4db43ab062f047640293b03e06b9841abb4c0c7432e09182d4eadc6bbc3043c0",
    "v4_campaign_runner_sha256": "033830186086c5742b03d8b09aaaf9d363779c3fa1bd25d9ac32033fa54d5119",
    "v4_focused_tests_sha256": "80e39644da01a1ea7eb9f02976da379319f4fcfdd0f6490de2b433df1803a412",
}
TRUE_FIELDS = {
    "paid_tier_confirmed_that_day", "prepay_plan_confirmed_that_day", "auto_reload_off_that_day",
    "billing_account_currently_isolated_for_pilot", "no_unexpected_billing_activity_since_last_attempt",
    "no_other_activity_during_gate5_window", "key_remains_in_user_controlled_encrypted_local_secret_store",
    "both_exact_models_available_and_not_deprecated", "generate_content_endpoint_confirmed_for_both_models",
    "common_low_thinking_confirmed_for_both_models", "structured_output_field_confirmed_for_both_models",
    "response_usage_shape_confirmed", "fixed_24_slot_scope_confirmed", "v3_terminal_evidence_verified",
    "nine_initial_cost_components_confirmed", "four_attempt_campaign_bound_understood",
    "schema_diagnostic_text_exclusion_understood", "four_code_pause_whitelist_understood",
    "all_other_outcomes_hard_terminal_understood", "pause_requires_fresh_johnny_review_understood",
    "next_day_refresh_fail_closed_understood", "v4_campaign_execution_authorized_by_johnny",
}


class Gate5PaidPilotRetryCampaignV4AttestationError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5PaidPilotRetryCampaignV4AttestationError("duplicate attestation key")
        value[key] = item
    return value


def validate_attestation(path: Path, expected_execution_date: str | None = None) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
        template = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v4_attestation_template.json")
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignV4AttestationError("attestation unreadable") from exc
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5PaidPilotRetryCampaignV4AttestationError("attestation fields drifted")
    required_date = expected_execution_date or date.today().isoformat()
    if value.get("artifact") != "gemini_generator_gate5_paid_pilot_retry_campaign_v4_attestation" or value.get("attestor") != "Johnny" or value.get("execution_date") != required_date:
        raise Gate5PaidPilotRetryCampaignV4AttestationError("attestation identity or date invalid")
    if any(value.get(name) != expected for name, expected in {**EXPECTED_V3, **EXPECTED_BUILD}.items()):
        raise Gate5PaidPilotRetryCampaignV4AttestationError("v4 evidence mismatch")
    if any(value.get(name) is not True for name in TRUE_FIELDS):
        raise Gate5PaidPilotRetryCampaignV4AttestationError("required paid-pilot campaign v4 fact is unconfirmed")
    rate_hash = value.get("execution_day_rate_snapshot_sha256")
    if value.get("execution_day_rate_snapshot_status") != "execution_day_verified" or not isinstance(rate_hash, str) or not HASH_RE.fullmatch(rate_hash):
        raise Gate5PaidPilotRetryCampaignV4AttestationError("rate snapshot invalid")
    if type(value.get("positive_prepaid_balance_usd_millionths")) is not int or value["positive_prepaid_balance_usd_millionths"] < pilot.PILOT_CEILING:
        raise Gate5PaidPilotRetryCampaignV4AttestationError("prepaid balance insufficient")
    expected_numbers = {
        "pilot_ceiling_usd_millionths": pilot.PILOT_CEILING,
        "reconciliation_stop_usd_millionths": pilot.RECONCILIATION_STOP,
        "maximum_campaign_attempts": MAX_CAMPAIGN_ATTEMPTS,
        "initial_historical_component_count": INITIAL_COMPONENT_COUNT,
        "prior_pilot_booked_cost_usd_millionths": ATTESTED_BASELINE_COST,
        "v4_worst_case_aggregate_usd_millionths": 901_440,
    }
    if any(value.get(name) != expected for name, expected in expected_numbers.items()):
        raise Gate5PaidPilotRetryCampaignV4AttestationError("v4 campaign cost or count drifted")
    if gate2.contains_secret(value):
        raise Gate5PaidPilotRetryCampaignV4AttestationError("secret-like value in attestation")
    return value
