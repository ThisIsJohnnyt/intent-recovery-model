"""Local-only attestation gate for the Gate 5 paid-pilot V8 campaign."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import gate2
import gate5_paid_pilot_v8_engine as v8_engine


PACKAGE = Path(__file__).resolve().parent
MAX_CAMPAIGN_ATTEMPTS = 15
ATTESTED_BASELINE_COST = 234_960
INITIAL_COMPONENT_COUNT = 24
INITIAL_COMPONENT_MANIFEST_SHA256 = "fb806f9187b7942e15f58b0ce0fa62ccd09b35e4a48150d3e6235d4a1f4360f9"
HASH_RE = re.compile(r"[0-9a-f]{64}")
EXPECTED_V7 = {
    "v7_final_attestation_sha256": "bd661065819a4db02fda73e781aa0f8ef2bbbd13c0fddac8780f491848e48be7",
    "v7_terminal_campaign_state_sha256": "e934d7038031120d63e15ed020a136aedf68f4146bd9295f2b47eb64a08d4f3f",
    "v7_terminal_state_row_sha256": "2802cb855c125db9460d310e9aacd4084e86ee14ee17a3bcf818bacb7c79f17c",
    "v7_terminal_completion_sha256": "5ab1ad2a500b2c76995a3aad40d3c236d51bf7d7c35508f3e1457d3a491c229c",
    "v7_terminal_component_row_sha256": "29cbe3348a7ca2cb2db3bb3d4a1402837456f2bba90cb8e79bf8ed262b57cafb",
    "v7_terminal_historical_component_manifest_sha256": INITIAL_COMPONENT_MANIFEST_SHA256,
}
EXPECTED_BUILD = {
    "v8_proposal_sha256": "793b339d7ebed5d2a487d3b373795dc415c6b0833e7c2321e0fb6ad855d72166",
    "v8_first_request_sha256": "d3ea4942f0b476fe149b0394b6c7dd702bca820a57e8cf6959167458d16a7283",
}
BUILD_PATHS = {
    "v8_system_instruction_sha256": PACKAGE / "system_instruction_v7.txt",
    "v7_prompt_builder_sha256": PACKAGE / "gate5_v7_narrative_idiom_prompt.py",
    "v8_schedule_sha256": PACKAGE / "schedule_v8_m02_start.json",
    "v8_engine_sha256": PACKAGE / "gate5_paid_pilot_v8_engine.py",
    "v8_private_raw_diagnostic_sha256": PACKAGE / "gate5_v6_private_raw_diagnostic.py",
    "v8_gate_sha256": Path(__file__).resolve(),
    "v8_attestation_template_sha256": PACKAGE / "gate5_paid_pilot_retry_campaign_v8_attestation_template.json",
    "v8_review_template_sha256": PACKAGE / "gate5_paid_pilot_retry_campaign_v8_review_template.json",
    "v8_campaign_runner_sha256": PACKAGE / "gate5_paid_pilot_retry_campaign_v8_runner.py",
    "v8_focused_campaign_tests_sha256": PACKAGE / "test_gate5_paid_pilot_retry_campaign_v8.py",
    "v7_prompt_tests_sha256": PACKAGE / "test_gate5_v7_narrative_idiom_prompt.py",
}
TRUE_FIELDS = {
    "paid_tier_confirmed_that_day", "prepay_plan_confirmed_that_day", "auto_reload_off_that_day",
    "billing_account_currently_isolated_for_pilot", "no_unexpected_billing_activity_since_last_attempt",
    "no_other_activity_during_gate5_window", "key_remains_in_user_controlled_encrypted_local_secret_store",
    "both_exact_models_available_and_not_deprecated", "generate_content_endpoint_confirmed_for_both_models",
    "common_low_thinking_confirmed_for_both_models", "structured_output_field_confirmed_for_both_models",
    "response_usage_shape_confirmed", "fixed_22_slot_scope_confirmed", "v7_terminal_evidence_verified",
    "twenty_four_historical_cost_components_confirmed", "fifteen_attempt_v8_campaign_bound_understood",
    "v7_prompt_and_schedule_scope_understood", "schema_diagnostic_text_exclusion_understood",
    "four_code_pause_whitelist_understood", "all_other_outcomes_hard_terminal_understood",
    "pause_requires_fresh_johnny_review_understood", "next_day_refresh_fail_closed_understood",
    "screened_raw_output_diagnostic_boundary_understood", "provider_safety_and_citation_withholding_understood",
    "raw_output_diagnostic_persistence_failure_terminal_understood", "v8_campaign_execution_authorized_by_johnny",
}


class Gate5PaidPilotRetryCampaignV8AttestationError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5PaidPilotRetryCampaignV8AttestationError("duplicate attestation key")
        value[key] = item
    return value


def current_build_hashes() -> dict[str, str]:
    try:
        return {name: v8_engine.canonical_hash(path) for name, path in BUILD_PATHS.items()}
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignV8AttestationError("V8 build unavailable") from exc


def validate_attestation(path: Path, expected_execution_date: str | None = None) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
        template = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v8_attestation_template.json")
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignV8AttestationError("attestation unreadable") from exc
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5PaidPilotRetryCampaignV8AttestationError("attestation fields drifted")
    required_date = expected_execution_date or date.today().isoformat()
    if value.get("artifact") != "gemini_generator_gate5_paid_pilot_retry_campaign_v8_attestation" or value.get("attestor") != "Johnny" or value.get("execution_date") != required_date:
        raise Gate5PaidPilotRetryCampaignV8AttestationError("attestation identity or date invalid")
    expected_evidence = {**EXPECTED_V7, **EXPECTED_BUILD, **current_build_hashes()}
    if any(value.get(name) != expected for name, expected in expected_evidence.items()):
        raise Gate5PaidPilotRetryCampaignV8AttestationError("V8 evidence mismatch")
    if any(value.get(name) is not True for name in TRUE_FIELDS):
        raise Gate5PaidPilotRetryCampaignV8AttestationError("required paid-pilot campaign V8 fact is unconfirmed")
    rate_hash = value.get("execution_day_rate_snapshot_sha256")
    if value.get("execution_day_rate_snapshot_status") != "execution_day_verified" or not isinstance(rate_hash, str) or not HASH_RE.fullmatch(rate_hash):
        raise Gate5PaidPilotRetryCampaignV8AttestationError("rate snapshot invalid")
    balance = value.get("positive_prepaid_balance_usd_millionths")
    if type(balance) is not int or balance < v8_engine.V8_PILOT_CEILING:
        raise Gate5PaidPilotRetryCampaignV8AttestationError("prepaid balance insufficient")
    expected_numbers = {
        "pilot_ceiling_usd_millionths": v8_engine.V8_PILOT_CEILING,
        "reconciliation_stop_usd_millionths": v8_engine.V8_RECONCILIATION_STOP,
        "maximum_campaign_attempts": MAX_CAMPAIGN_ATTEMPTS,
        "initial_historical_component_count": INITIAL_COMPONENT_COUNT,
        "prior_pilot_booked_cost_usd_millionths": ATTESTED_BASELINE_COST,
        "v8_worst_case_aggregate_usd_millionths": 3_039_960,
    }
    if any(value.get(name) != expected for name, expected in expected_numbers.items()):
        raise Gate5PaidPilotRetryCampaignV8AttestationError("V8 campaign cost or count drifted")
    if gate2.contains_secret(value):
        raise Gate5PaidPilotRetryCampaignV8AttestationError("secret-like value in attestation")
    return value
