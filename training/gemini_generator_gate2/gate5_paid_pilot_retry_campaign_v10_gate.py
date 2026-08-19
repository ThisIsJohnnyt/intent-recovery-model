"""Local-only attestation gate for the Gate 5 paid-pilot V10 continue-past-schema_invalid campaign."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import gate2
import gate5_paid_pilot_v10_engine as v10_engine


PACKAGE = Path(__file__).resolve().parent
HASH_RE = re.compile(r"[0-9a-f]{64}")
ATTESTED_BASELINE_COST = 279_640
INITIAL_COMPONENT_COUNT = 26
INITIAL_COMPONENT_MANIFEST_SHA256 = "1165121d3d3f5a6a55f4dac29428c8ae451a3edb9647c463146a6badb4eb6de2"
# V9's own real terminal evidence, independently re-derived and pinned -- this
# is the campaign V10's historical baseline is built on top of, exactly as V9
# built on top of V8's.
EXPECTED_V9 = {
    "v9_final_attestation_sha256": "6296fbf8313baf5aa01091ba016148e2fc0cda0f423d0746a9ac1127ee7c6d3c",
    "v9_terminal_campaign_ledger_sha256": "a6909622721b6af246626c721fdcab4d88361cc371efeb54ca10f2b366eb9480",
    "v9_terminal_run_summary_sha256": "b870916707387fdedf0b080894dec2d0ca74bd678b178e276d9b1240a0e27124",
    "v9_terminal_state_row_sha256": "6bfdf9cb27aad3046eb410385bcd37511fcac16b670f8add8ff7c0f02baa77eb",
    "v9_terminal_historical_component_manifest_sha256": "66fe1aaf1c9d266412f8af4b76e9ec4484d5b32bcd4916b8f71730aceafa4878",
}
EXPECTED_BUILD = {
    "v10_proposal_sha256": "70d7777ff59f5b3a63ee78b373cabd2bc9b164c8ddd101489d050a0c1c398e45",
    "v10_first_request_sha256": v10_engine.EXPECTED_V10_FIRST_REQUEST_SHA256,
    "v10_reused_v8_schedule_sha256": v10_engine.EXPECTED_V8_SCHEDULE_SHA256,
}
BUILD_PATHS = {
    "v10_engine_sha256": PACKAGE / "gate5_paid_pilot_v10_engine.py",
    "v10_gate_sha256": Path(__file__).resolve(),
    "v10_attestation_template_sha256": PACKAGE / "gate5_paid_pilot_retry_campaign_v10_attestation_template.json",
    "v10_campaign_runner_sha256": PACKAGE / "gate5_paid_pilot_retry_campaign_v10_runner.py",
    "v10_focused_campaign_tests_sha256": PACKAGE / "test_gate5_paid_pilot_retry_campaign_v10.py",
}
TRUE_FIELDS = {
    "paid_tier_confirmed_that_day", "prepay_plan_confirmed_that_day", "auto_reload_off_that_day",
    "billing_account_currently_isolated_for_pilot", "no_unexpected_billing_activity_since_last_attempt",
    "no_other_activity_during_gate5_window", "key_remains_in_user_controlled_encrypted_local_secret_store",
    "both_exact_models_available_and_not_deprecated", "generate_content_endpoint_confirmed_for_both_models",
    "common_low_thinking_confirmed_for_both_models", "structured_output_field_confirmed_for_both_models",
    "response_usage_shape_confirmed", "v9_terminal_evidence_verified",
    "twenty_six_historical_cost_components_confirmed", "v10_full_schedule_single_pass_scope_understood",
    "v8_schedule_and_prompt_reused_unchanged_understood", "continue_past_collision_family_scope_understood",
    "continue_past_schema_invalid_scope_understood", "max_five_card_attempts_retry_scope_understood",
    "all_other_outcomes_hard_terminal_understood", "schema_diagnostic_text_exclusion_understood",
    "four_code_raw_diagnostic_whitelist_understood", "provider_safety_and_citation_withholding_understood",
    "raw_output_diagnostic_persistence_failure_terminal_understood",
    "live_progress_reporting_replaces_per_result_confirmation_understood",
    "v10_campaign_execution_authorized_by_johnny",
}


class Gate5PaidPilotRetryCampaignV10AttestationError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5PaidPilotRetryCampaignV10AttestationError("duplicate attestation key")
        value[key] = item
    return value


def current_build_hashes() -> dict[str, str]:
    try:
        return {name: v10_engine.canonical_hash(path) for name, path in BUILD_PATHS.items()}
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignV10AttestationError("V10 build unavailable") from exc


def validate_attestation(path: Path, expected_execution_date: str | None = None) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
        template = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v10_attestation_template.json")
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignV10AttestationError("attestation unreadable") from exc
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5PaidPilotRetryCampaignV10AttestationError("attestation fields drifted")
    required_date = expected_execution_date or date.today().isoformat()
    if value.get("artifact") != "gemini_generator_gate5_paid_pilot_retry_campaign_v10_attestation" or value.get("attestor") != "Johnny" or value.get("execution_date") != required_date:
        raise Gate5PaidPilotRetryCampaignV10AttestationError("attestation identity or date invalid")
    expected_evidence = {**EXPECTED_V9, **EXPECTED_BUILD, **current_build_hashes()}
    if any(value.get(name) != expected for name, expected in expected_evidence.items()):
        raise Gate5PaidPilotRetryCampaignV10AttestationError("V10 evidence mismatch")
    if any(value.get(name) is not True for name in TRUE_FIELDS):
        raise Gate5PaidPilotRetryCampaignV10AttestationError("required paid-pilot campaign V10 fact is unconfirmed")
    rate_hash = value.get("execution_day_rate_snapshot_sha256")
    if value.get("execution_day_rate_snapshot_status") != "execution_day_verified" or not isinstance(rate_hash, str) or not HASH_RE.fullmatch(rate_hash):
        raise Gate5PaidPilotRetryCampaignV10AttestationError("rate snapshot invalid")
    balance = value.get("positive_prepaid_balance_usd_millionths")
    if type(balance) is not int or balance < v10_engine.V10_PILOT_CEILING:
        raise Gate5PaidPilotRetryCampaignV10AttestationError("prepaid balance insufficient")
    expected_numbers = {
        "pilot_ceiling_usd_millionths": v10_engine.V10_PILOT_CEILING,
        "reconciliation_stop_usd_millionths": v10_engine.V10_RECONCILIATION_STOP,
        "max_card_attempts": v10_engine.MAX_CARD_ATTEMPTS,
        "initial_historical_component_count": INITIAL_COMPONENT_COUNT,
        "prior_pilot_booked_cost_usd_millionths": ATTESTED_BASELINE_COST,
        "v10_worst_case_aggregate_usd_millionths": 1_214_640,
    }
    if any(value.get(name) != expected for name, expected in expected_numbers.items()):
        raise Gate5PaidPilotRetryCampaignV10AttestationError("V10 campaign cost or count drifted")
    if gate2.contains_secret(value):
        raise Gate5PaidPilotRetryCampaignV10AttestationError("secret-like value in attestation")
    return value
