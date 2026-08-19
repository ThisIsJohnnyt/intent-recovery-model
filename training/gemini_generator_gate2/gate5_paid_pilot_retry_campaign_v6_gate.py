"""Local-only attestation gate for the Gate 5 paid-pilot v6 campaign."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import gate2
import gate5_paid_pilot_v6_engine as v6_engine


PACKAGE = Path(__file__).resolve().parent
MAX_CAMPAIGN_ATTEMPTS = 15
ATTESTED_BASELINE_COST = 117_480
INITIAL_COMPONENT_COUNT = 13
INITIAL_COMPONENT_MANIFEST_SHA256 = "42aa31db451e7e9f9d191f2ad88d18227730ba14d4b78c4da86ca3c17cac8e87"
HASH_RE = re.compile(r"[0-9a-f]{64}")
EXPECTED_V5 = {
    "v5_final_attestation_sha256": "1365385852a3182a73e133680625d49842fe71d6e85ff2f8caf37d65d2047bf3",
    "v5_terminal_campaign_state_sha256": "300431df17fc7a70cf310afc8f8df3046a2310698809ba6cb618b5f1d19e9b7c",
    "v5_terminal_state_row_sha256": "e7b0d8880a51e6a8512a61e89f39b0784ecad3f164b5acb626948ab787df2bad",
    "v5_terminal_component_row_sha256": "a219a3ecb8cf24a564681ac51edda802eda0050dc97ed24ef793013cba0fd29d",
    "v5_terminal_historical_component_manifest_sha256": INITIAL_COMPONENT_MANIFEST_SHA256,
}
EXPECTED_BUILD = {
    "v6_proposal_sha256": "0c94b7b8d8eee973b6949e28514beceb69fa03a0ce80237094155e4b4e626162",
}
BUILD_PATHS = {
    "v6_engine_sha256": PACKAGE / "gate5_paid_pilot_v6_engine.py",
    "v6_private_raw_diagnostic_sha256": PACKAGE / "gate5_v6_private_raw_diagnostic.py",
    "v6_gate_sha256": Path(__file__).resolve(),
    "v6_campaign_runner_sha256": PACKAGE / "gate5_paid_pilot_retry_campaign_v6_runner.py",
    "v6_focused_campaign_tests_sha256": PACKAGE / "test_gate5_paid_pilot_retry_campaign_v6.py",
    "v6_private_diagnostic_tests_sha256": PACKAGE / "test_gate5_v6_private_raw_diagnostic.py",
}
TRUE_FIELDS = {
    "paid_tier_confirmed_that_day", "prepay_plan_confirmed_that_day", "auto_reload_off_that_day",
    "billing_account_currently_isolated_for_pilot", "no_unexpected_billing_activity_since_last_attempt",
    "no_other_activity_during_gate5_window", "key_remains_in_user_controlled_encrypted_local_secret_store",
    "both_exact_models_available_and_not_deprecated", "generate_content_endpoint_confirmed_for_both_models",
    "common_low_thinking_confirmed_for_both_models", "structured_output_field_confirmed_for_both_models",
    "response_usage_shape_confirmed", "fixed_24_slot_scope_confirmed", "v5_terminal_evidence_verified",
    "thirteen_historical_cost_components_confirmed", "fifteen_attempt_v6_campaign_bound_understood",
    "schema_diagnostic_text_exclusion_understood", "four_code_pause_whitelist_understood",
    "all_other_outcomes_hard_terminal_understood", "pause_requires_fresh_johnny_review_understood",
    "next_day_refresh_fail_closed_understood", "screened_raw_output_diagnostic_boundary_understood",
    "provider_safety_and_citation_withholding_understood",
    "raw_output_diagnostic_persistence_failure_terminal_understood",
    "v6_campaign_execution_authorized_by_johnny",
}


class Gate5PaidPilotRetryCampaignV6AttestationError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5PaidPilotRetryCampaignV6AttestationError("duplicate attestation key")
        value[key] = item
    return value


def current_build_hashes() -> dict[str, str]:
    try:
        return {name: v6_engine.canonical_hash(path) for name, path in BUILD_PATHS.items()}
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignV6AttestationError("v6 build unavailable") from exc


def validate_attestation(path: Path, expected_execution_date: str | None = None) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
        template = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v6_attestation_template.json")
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignV6AttestationError("attestation unreadable") from exc
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5PaidPilotRetryCampaignV6AttestationError("attestation fields drifted")
    required_date = expected_execution_date or date.today().isoformat()
    if value.get("artifact") != "gemini_generator_gate5_paid_pilot_retry_campaign_v6_attestation" or value.get("attestor") != "Johnny" or value.get("execution_date") != required_date:
        raise Gate5PaidPilotRetryCampaignV6AttestationError("attestation identity or date invalid")
    if any(value.get(name) != expected for name, expected in {**EXPECTED_V5, **EXPECTED_BUILD, **current_build_hashes()}.items()):
        raise Gate5PaidPilotRetryCampaignV6AttestationError("v6 evidence mismatch")
    if any(value.get(name) is not True for name in TRUE_FIELDS):
        raise Gate5PaidPilotRetryCampaignV6AttestationError("required paid-pilot campaign v6 fact is unconfirmed")
    rate_hash = value.get("execution_day_rate_snapshot_sha256")
    if value.get("execution_day_rate_snapshot_status") != "execution_day_verified" or not isinstance(rate_hash, str) or not HASH_RE.fullmatch(rate_hash):
        raise Gate5PaidPilotRetryCampaignV6AttestationError("rate snapshot invalid")
    if type(value.get("positive_prepaid_balance_usd_millionths")) is not int or value["positive_prepaid_balance_usd_millionths"] < v6_engine.V6_PILOT_CEILING:
        raise Gate5PaidPilotRetryCampaignV6AttestationError("prepaid balance insufficient")
    expected_numbers = {
        "pilot_ceiling_usd_millionths": v6_engine.V6_PILOT_CEILING,
        "reconciliation_stop_usd_millionths": v6_engine.V6_RECONCILIATION_STOP,
        "maximum_campaign_attempts": MAX_CAMPAIGN_ATTEMPTS,
        "initial_historical_component_count": INITIAL_COMPONENT_COUNT,
        "prior_pilot_booked_cost_usd_millionths": ATTESTED_BASELINE_COST,
        "v6_worst_case_aggregate_usd_millionths": 3_177_480,
    }
    if any(value.get(name) != expected for name, expected in expected_numbers.items()):
        raise Gate5PaidPilotRetryCampaignV6AttestationError("v6 campaign cost or count drifted")
    if gate2.contains_secret(value):
        raise Gate5PaidPilotRetryCampaignV6AttestationError("secret-like value in attestation")
    return value
