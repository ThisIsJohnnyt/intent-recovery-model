"""Local-only attestation gate for the Gate 5 paid-pilot V9 full-schedule campaign."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import gate2
import gate5_paid_pilot_v9_engine as v9_engine


PACKAGE = Path(__file__).resolve().parent
HASH_RE = re.compile(r"[0-9a-f]{64}")
ATTESTED_BASELINE_COST = 241_280
INITIAL_COMPONENT_COUNT = 25
INITIAL_COMPONENT_MANIFEST_SHA256 = "66fe1aaf1c9d266412f8af4b76e9ec4484d5b32bcd4916b8f71730aceafa4878"
EXPECTED_V8 = {
    "v8_final_attestation_sha256": "748be2e56c097112063667092be5ab72f995913d1a8f2e8e0a83839fe3276a99",
    "v8_terminal_campaign_ledger_sha256": "c5b2a3372725a510604ffcf8ca41bfdfd92fc373d454ca644e28070bb8722288",
    "v8_terminal_state_row_sha256": "14978b5d07376dbd3edcfa40dd05e6dc5b7ea839b27adea73da77afd4c40d8ad",
    "v8_terminal_completion_sha256": "552c0d1d71cc2e3d53e653fa5b3ca0c5e606fffacd4e70feb944c6ca30884023",
    "v8_terminal_component_row_sha256": "0c5e4e2d0630e35cf00efff1a43f173fd45b2425554f8435fb876d46abf5965b",
    "v8_terminal_historical_component_manifest_sha256": INITIAL_COMPONENT_MANIFEST_SHA256,
}
EXPECTED_BUILD = {
    "v9_proposal_sha256": "d1b81b8dfa3e276ac71e67ba7873527bac49e7c03e41e28db399059ed9ffa589",
    "v9_first_request_sha256": v9_engine.EXPECTED_V9_FIRST_REQUEST_SHA256,
    "v9_reused_v8_schedule_sha256": v9_engine.EXPECTED_V8_SCHEDULE_SHA256,
}
BUILD_PATHS = {
    "v9_engine_sha256": PACKAGE / "gate5_paid_pilot_v9_engine.py",
    "v9_gate_sha256": Path(__file__).resolve(),
    "v9_attestation_template_sha256": PACKAGE / "gate5_paid_pilot_retry_campaign_v9_attestation_template.json",
    "v9_campaign_runner_sha256": PACKAGE / "gate5_paid_pilot_retry_campaign_v9_runner.py",
    "v9_focused_campaign_tests_sha256": PACKAGE / "test_gate5_paid_pilot_retry_campaign_v9.py",
}
TRUE_FIELDS = {
    "paid_tier_confirmed_that_day", "prepay_plan_confirmed_that_day", "auto_reload_off_that_day",
    "billing_account_currently_isolated_for_pilot", "no_unexpected_billing_activity_since_last_attempt",
    "no_other_activity_during_gate5_window", "key_remains_in_user_controlled_encrypted_local_secret_store",
    "both_exact_models_available_and_not_deprecated", "generate_content_endpoint_confirmed_for_both_models",
    "common_low_thinking_confirmed_for_both_models", "structured_output_field_confirmed_for_both_models",
    "response_usage_shape_confirmed", "v8_terminal_evidence_verified",
    "twenty_five_historical_cost_components_confirmed", "v9_full_schedule_single_pass_scope_understood",
    "v8_schedule_and_prompt_reused_unchanged_understood", "continue_past_collision_family_scope_understood",
    "max_five_card_attempts_retry_scope_understood", "all_other_outcomes_hard_terminal_understood",
    "schema_diagnostic_text_exclusion_understood", "four_code_raw_diagnostic_whitelist_understood",
    "provider_safety_and_citation_withholding_understood", "raw_output_diagnostic_persistence_failure_terminal_understood",
    "live_progress_reporting_replaces_per_result_confirmation_understood",
    "v9_campaign_execution_authorized_by_johnny",
}


class Gate5PaidPilotRetryCampaignV9AttestationError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5PaidPilotRetryCampaignV9AttestationError("duplicate attestation key")
        value[key] = item
    return value


def current_build_hashes() -> dict[str, str]:
    try:
        return {name: v9_engine.canonical_hash(path) for name, path in BUILD_PATHS.items()}
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignV9AttestationError("V9 build unavailable") from exc


def validate_attestation(path: Path, expected_execution_date: str | None = None) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
        template = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v9_attestation_template.json")
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignV9AttestationError("attestation unreadable") from exc
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5PaidPilotRetryCampaignV9AttestationError("attestation fields drifted")
    required_date = expected_execution_date or date.today().isoformat()
    if value.get("artifact") != "gemini_generator_gate5_paid_pilot_retry_campaign_v9_attestation" or value.get("attestor") != "Johnny" or value.get("execution_date") != required_date:
        raise Gate5PaidPilotRetryCampaignV9AttestationError("attestation identity or date invalid")
    expected_evidence = {**EXPECTED_V8, **EXPECTED_BUILD, **current_build_hashes()}
    if any(value.get(name) != expected for name, expected in expected_evidence.items()):
        raise Gate5PaidPilotRetryCampaignV9AttestationError("V9 evidence mismatch")
    if any(value.get(name) is not True for name in TRUE_FIELDS):
        raise Gate5PaidPilotRetryCampaignV9AttestationError("required paid-pilot campaign V9 fact is unconfirmed")
    rate_hash = value.get("execution_day_rate_snapshot_sha256")
    if value.get("execution_day_rate_snapshot_status") != "execution_day_verified" or not isinstance(rate_hash, str) or not HASH_RE.fullmatch(rate_hash):
        raise Gate5PaidPilotRetryCampaignV9AttestationError("rate snapshot invalid")
    balance = value.get("positive_prepaid_balance_usd_millionths")
    if type(balance) is not int or balance < v9_engine.V9_PILOT_CEILING:
        raise Gate5PaidPilotRetryCampaignV9AttestationError("prepaid balance insufficient")
    expected_numbers = {
        "pilot_ceiling_usd_millionths": v9_engine.V9_PILOT_CEILING,
        "reconciliation_stop_usd_millionths": v9_engine.V9_RECONCILIATION_STOP,
        "max_card_attempts": v9_engine.MAX_CARD_ATTEMPTS,
        "initial_historical_component_count": INITIAL_COMPONENT_COUNT,
        "prior_pilot_booked_cost_usd_millionths": ATTESTED_BASELINE_COST,
        "v9_worst_case_aggregate_usd_millionths": 1_176_280,
    }
    if any(value.get(name) != expected for name, expected in expected_numbers.items()):
        raise Gate5PaidPilotRetryCampaignV9AttestationError("V9 campaign cost or count drifted")
    if gate2.contains_secret(value):
        raise Gate5PaidPilotRetryCampaignV9AttestationError("secret-like value in attestation")
    return value
