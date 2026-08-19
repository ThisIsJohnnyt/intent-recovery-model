"""Local-only attestation gate for the Gate 5 paid-pilot v5 campaign."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import gate2
import gate5_paid_pilot_runner as pilot


PACKAGE = Path(__file__).resolve().parent
MAX_CAMPAIGN_ATTEMPTS = 3
ATTESTED_BASELINE_COST = 85_440
INITIAL_COMPONENT_COUNT = 10
INITIAL_COMPONENT_MANIFEST_SHA256 = "5294a3c58730769560b9f60e6982a3addda1b35606a5884cc5a1885c1ff3fa75"
HASH_RE = re.compile(r"[0-9a-f]{64}")
EXPECTED_V4 = {
    "v4_final_attestation_sha256": "0a67dc58f8c127a8886217e8adb8adfc204dd0b9fcbbf74cdbe1ecbf2058e010",
    "v4_terminal_campaign_state_sha256": "73b58f156aa46574206d81a26ef57269dbb29a2353e82effc61ec230a23595df",
    "v4_terminal_state_row_sha256": "d52e8c08fb76588e6b011b4fd9221c992df894ddcdc9ae0c9817dae9f2d8b863",
    "v4_terminal_component_row_sha256": "86e883d6f6c91b135c934a10ee306241f12a38d4be345a9277c67244fc94be24",
    "v4_terminal_historical_component_manifest_sha256": INITIAL_COMPONENT_MANIFEST_SHA256,
}
EXPECTED_BUILD = {
    "v5_scope_note_sha256": "abd8ef78ab78576e52db7865d398bceff1b19cfd490c26e2e02ef64002908f0f",
    "structured_schema_gate2_sha256": "d8de37186e0dbb7f33a4cca2e2e746f1c11bf34749c8a817b5db69751fac4da0",
    "schema_conformance_evidence_module_sha256": "a41669caccdbcabb10ff803b78152d8e0cf99e87580b8911dd3c3e1cc4d1bf9b",
    "schema_integrated_paid_runner_sha256": "4db43ab062f047640293b03e06b9841abb4c0c7432e09182d4eadc6bbc3043c0",
    "v5_campaign_runner_sha256": "d88d4602f507a2c3a79a7d316a686c7c1e480bd1e25215f93cfe4ea687a4cf9c",
    "v5_focused_tests_sha256": "da0abf683555409484287277996ab693f6465d9e9b326a71e7ae8c1a6d8fc21a",
}
TRUE_FIELDS = {
    "paid_tier_confirmed_that_day", "prepay_plan_confirmed_that_day", "auto_reload_off_that_day",
    "billing_account_currently_isolated_for_pilot", "no_unexpected_billing_activity_since_last_attempt",
    "no_other_activity_during_gate5_window", "key_remains_in_user_controlled_encrypted_local_secret_store",
    "both_exact_models_available_and_not_deprecated", "generate_content_endpoint_confirmed_for_both_models",
    "common_low_thinking_confirmed_for_both_models", "structured_output_field_confirmed_for_both_models",
    "response_usage_shape_confirmed", "fixed_24_slot_scope_confirmed", "v4_terminal_evidence_verified",
    "ten_initial_cost_components_confirmed", "three_attempt_campaign_bound_understood",
    "schema_diagnostic_text_exclusion_understood", "four_code_pause_whitelist_understood",
    "all_other_outcomes_hard_terminal_understood", "pause_requires_fresh_johnny_review_understood",
    "next_day_refresh_fail_closed_understood", "v5_campaign_execution_authorized_by_johnny",
}


class Gate5PaidPilotRetryCampaignV5AttestationError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5PaidPilotRetryCampaignV5AttestationError("duplicate attestation key")
        value[key] = item
    return value


def validate_attestation(path: Path, expected_execution_date: str | None = None) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
        template = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v5_attestation_template.json")
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignV5AttestationError("attestation unreadable") from exc
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5PaidPilotRetryCampaignV5AttestationError("attestation fields drifted")
    required_date = expected_execution_date or date.today().isoformat()
    if value.get("artifact") != "gemini_generator_gate5_paid_pilot_retry_campaign_v5_attestation" or value.get("attestor") != "Johnny" or value.get("execution_date") != required_date:
        raise Gate5PaidPilotRetryCampaignV5AttestationError("attestation identity or date invalid")
    if any(value.get(name) != expected for name, expected in {**EXPECTED_V4, **EXPECTED_BUILD}.items()):
        raise Gate5PaidPilotRetryCampaignV5AttestationError("v5 evidence mismatch")
    if any(value.get(name) is not True for name in TRUE_FIELDS):
        raise Gate5PaidPilotRetryCampaignV5AttestationError("required paid-pilot campaign v5 fact is unconfirmed")
    rate_hash = value.get("execution_day_rate_snapshot_sha256")
    if value.get("execution_day_rate_snapshot_status") != "execution_day_verified" or not isinstance(rate_hash, str) or not HASH_RE.fullmatch(rate_hash):
        raise Gate5PaidPilotRetryCampaignV5AttestationError("rate snapshot invalid")
    if type(value.get("positive_prepaid_balance_usd_millionths")) is not int or value["positive_prepaid_balance_usd_millionths"] < pilot.PILOT_CEILING:
        raise Gate5PaidPilotRetryCampaignV5AttestationError("prepaid balance insufficient")
    expected_numbers = {
        "pilot_ceiling_usd_millionths": pilot.PILOT_CEILING,
        "reconciliation_stop_usd_millionths": pilot.RECONCILIATION_STOP,
        "maximum_campaign_attempts": MAX_CAMPAIGN_ATTEMPTS,
        "initial_historical_component_count": INITIAL_COMPONENT_COUNT,
        "prior_pilot_booked_cost_usd_millionths": ATTESTED_BASELINE_COST,
        "v5_worst_case_aggregate_usd_millionths": 697_440,
    }
    if any(value.get(name) != expected for name, expected in expected_numbers.items()):
        raise Gate5PaidPilotRetryCampaignV5AttestationError("v5 campaign cost or count drifted")
    if gate2.contains_secret(value):
        raise Gate5PaidPilotRetryCampaignV5AttestationError("secret-like value in attestation")
    return value
