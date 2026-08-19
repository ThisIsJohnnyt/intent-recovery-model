"""Local-only attestation gate for the Gate 5 paid-pilot V11 stopword-filtered-collision campaign."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import gate2
import gate5_paid_pilot_v11_engine as v11_engine


PACKAGE = Path(__file__).resolve().parent
HASH_RE = re.compile(r"[0-9a-f]{64}")
ATTESTED_BASELINE_COST = 685_501
INITIAL_COMPONENT_COUNT = 27
INITIAL_COMPONENT_MANIFEST_SHA256 = "cb38bb45030b571f4cbc045fe062fe439a4396b9fafa98c8a7505732daa782d1"
# V10's own real terminal evidence (the corrected-build r2 run that actually
# completed all 22 cards), independently re-derived and pinned -- this is the
# campaign V11's historical baseline is built on top of, exactly as V10 built
# on top of V9's and V9 built on top of V8's.
EXPECTED_V10 = {
    "v10_final_attestation_sha256": "ed6a617b9ccce80cf497299a9fde2527a9c8dbf39dc16949df0110af41570bda",
    "v10_terminal_campaign_ledger_sha256": "1fbe816abff5a1f05181420da0f1b64f33e3218b2b0c2591a6e41005731e52ca",
    "v10_terminal_run_summary_sha256": "0482c9da7fb7d235cb04c11291f3481f826ceac7c80bb7ccfd0d459106531419",
    "v10_terminal_state_row_sha256": "e0847fd91f728febd97551a542158cca6f7629f4f85e811ca59301cbbddbfd6d",
    "v10_terminal_historical_component_manifest_sha256": "1165121d3d3f5a6a55f4dac29428c8ae451a3edb9647c463146a6badb4eb6de2",
}
EXPECTED_BUILD = {
    "v11_proposal_sha256": "d685f62bb28f477d2160036c499ec2b03a1bcfdbcebb3022794b2c7691033947",
    "v11_first_request_sha256": v11_engine.EXPECTED_V11_FIRST_REQUEST_SHA256,
    "v11_reused_v8_schedule_sha256": v11_engine.EXPECTED_V8_SCHEDULE_SHA256,
}
BUILD_PATHS = {
    "v11_engine_sha256": PACKAGE / "gate5_paid_pilot_v11_engine.py",
    "v11_gate_sha256": Path(__file__).resolve(),
    "v11_attestation_template_sha256": PACKAGE / "gate5_paid_pilot_retry_campaign_v11_attestation_template.json",
    "v11_campaign_runner_sha256": PACKAGE / "gate5_paid_pilot_retry_campaign_v11_runner.py",
    "v11_focused_campaign_tests_sha256": PACKAGE / "test_gate5_paid_pilot_retry_campaign_v11.py",
}
TRUE_FIELDS = {
    "paid_tier_confirmed_that_day", "prepay_plan_confirmed_that_day", "auto_reload_off_that_day",
    "billing_account_currently_isolated_for_pilot", "no_unexpected_billing_activity_since_last_attempt",
    "no_other_activity_during_gate5_window", "key_remains_in_user_controlled_encrypted_local_secret_store",
    "both_exact_models_available_and_not_deprecated", "generate_content_endpoint_confirmed_for_both_models",
    "common_low_thinking_confirmed_for_both_models", "structured_output_field_confirmed_for_both_models",
    "response_usage_shape_confirmed", "v10_terminal_evidence_verified",
    "twenty_seven_historical_cost_components_confirmed", "v11_full_schedule_single_pass_scope_understood",
    "v8_schedule_and_prompt_reused_unchanged_understood", "continue_past_collision_family_scope_understood",
    "continue_past_schema_invalid_scope_understood", "max_five_card_attempts_retry_scope_understood",
    "all_other_outcomes_hard_terminal_understood", "schema_diagnostic_text_exclusion_understood",
    "four_code_raw_diagnostic_whitelist_understood", "provider_safety_and_citation_withholding_understood",
    "raw_output_diagnostic_persistence_failure_terminal_understood",
    "live_progress_reporting_replaces_per_result_confirmation_understood",
    "stopword_filtered_token_jaccard_scope_understood",
    "thresholds_schema_and_continue_past_ruleset_unchanged_understood",
    "v11_campaign_execution_authorized_by_johnny",
}


class Gate5PaidPilotRetryCampaignV11AttestationError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5PaidPilotRetryCampaignV11AttestationError("duplicate attestation key")
        value[key] = item
    return value


def current_build_hashes() -> dict[str, str]:
    try:
        return {name: v11_engine.canonical_hash(path) for name, path in BUILD_PATHS.items()}
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignV11AttestationError("V11 build unavailable") from exc


def validate_attestation(path: Path, expected_execution_date: str | None = None) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
        template = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v11_attestation_template.json")
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignV11AttestationError("attestation unreadable") from exc
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5PaidPilotRetryCampaignV11AttestationError("attestation fields drifted")
    required_date = expected_execution_date or date.today().isoformat()
    if value.get("artifact") != "gemini_generator_gate5_paid_pilot_retry_campaign_v11_attestation" or value.get("attestor") != "Johnny" or value.get("execution_date") != required_date:
        raise Gate5PaidPilotRetryCampaignV11AttestationError("attestation identity or date invalid")
    expected_evidence = {**EXPECTED_V10, **EXPECTED_BUILD, **current_build_hashes()}
    if any(value.get(name) != expected for name, expected in expected_evidence.items()):
        raise Gate5PaidPilotRetryCampaignV11AttestationError("V11 evidence mismatch")
    if any(value.get(name) is not True for name in TRUE_FIELDS):
        raise Gate5PaidPilotRetryCampaignV11AttestationError("required paid-pilot campaign V11 fact is unconfirmed")
    rate_hash = value.get("execution_day_rate_snapshot_sha256")
    if value.get("execution_day_rate_snapshot_status") != "execution_day_verified" or not isinstance(rate_hash, str) or not HASH_RE.fullmatch(rate_hash):
        raise Gate5PaidPilotRetryCampaignV11AttestationError("rate snapshot invalid")
    balance = value.get("positive_prepaid_balance_usd_millionths")
    if type(balance) is not int or balance < v11_engine.V11_PILOT_CEILING:
        raise Gate5PaidPilotRetryCampaignV11AttestationError("prepaid balance insufficient")
    expected_numbers = {
        "pilot_ceiling_usd_millionths": v11_engine.V11_PILOT_CEILING,
        "reconciliation_stop_usd_millionths": v11_engine.V11_RECONCILIATION_STOP,
        "max_card_attempts": v11_engine.MAX_CARD_ATTEMPTS,
        "initial_historical_component_count": INITIAL_COMPONENT_COUNT,
        "prior_pilot_booked_cost_usd_millionths": ATTESTED_BASELINE_COST,
        "v11_worst_case_aggregate_usd_millionths": 1_620_501,
    }
    if any(value.get(name) != expected for name, expected in expected_numbers.items()):
        raise Gate5PaidPilotRetryCampaignV11AttestationError("V11 campaign cost or count drifted")
    if gate2.contains_secret(value):
        raise Gate5PaidPilotRetryCampaignV11AttestationError("secret-like value in attestation")
    return value
