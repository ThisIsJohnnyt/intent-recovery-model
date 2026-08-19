"""Local-only attestation gate for the Gate 5 paid-pilot V7 campaign."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import gate2
import gate5_paid_pilot_v7_engine as v7_engine


PACKAGE = Path(__file__).resolve().parent
MAX_CAMPAIGN_ATTEMPTS = 15
ATTESTED_BASELINE_COST = 170_880
INITIAL_COMPONENT_COUNT = 18
INITIAL_COMPONENT_MANIFEST_SHA256 = "c0c73f2506b9f8350698007b0405b38423a061206d66a72bae3cbe66c1239f8b"
HASH_RE = re.compile(r"[0-9a-f]{64}")
EXPECTED_V6 = {
    "v6_final_attestation_sha256": "980c23dbe9308aa32aa48c15480bb64722993f71b6a4dfa7c8fbd0316d275839",
    "v6_terminal_campaign_state_sha256": "42222ea78f55aefc4f2364baf74c3a6f4ab1df8d57723ea87bbc4015559078ca",
    "v6_terminal_state_row_sha256": "8b670cc6b33d2f7506c6bbee56052a326ae6c9f6d696b407dd41a4ba74195ec4",
    "v6_terminal_completion_sha256": "0bc6d104decaae1075a77deb135ca39954293cc6969403931700b132203f789b",
    "v6_terminal_component_row_sha256": "322b691edd9be12016ec44ba96f9825e45f16d9bd37cfe2451b33054fa672a8c",
    "v6_terminal_historical_component_manifest_sha256": INITIAL_COMPONENT_MANIFEST_SHA256,
}
EXPECTED_BUILD = {
    "v7_proposal_sha256": "f316e0f6f4d7300d3bc9197eeddb273d557935d7c0a066a2fda22035a8950309",
    "v7_slot_one_request_sha256": "24dbeb008f4b2735d72ae0debe41729963e2adb3112cb1f9fb472120a63bfd94",
}
BUILD_PATHS = {
    "v7_system_instruction_sha256": PACKAGE / "system_instruction_v7.txt",
    "v7_prompt_builder_sha256": PACKAGE / "gate5_v7_narrative_idiom_prompt.py",
    "v7_schedule_sha256": PACKAGE / "schedule_v7.json",
    "v7_engine_sha256": PACKAGE / "gate5_paid_pilot_v7_engine.py",
    "v7_private_raw_diagnostic_sha256": PACKAGE / "gate5_v6_private_raw_diagnostic.py",
    "v7_gate_sha256": Path(__file__).resolve(),
    "v7_attestation_template_sha256": PACKAGE / "gate5_paid_pilot_retry_campaign_v7_attestation_template.json",
    "v7_review_template_sha256": PACKAGE / "gate5_paid_pilot_retry_campaign_v7_review_template.json",
    "v7_campaign_runner_sha256": PACKAGE / "gate5_paid_pilot_retry_campaign_v7_runner.py",
    "v7_focused_campaign_tests_sha256": PACKAGE / "test_gate5_paid_pilot_retry_campaign_v7.py",
    "v7_prompt_tests_sha256": PACKAGE / "test_gate5_v7_narrative_idiom_prompt.py",
}
TRUE_FIELDS = {
    "paid_tier_confirmed_that_day", "prepay_plan_confirmed_that_day", "auto_reload_off_that_day",
    "billing_account_currently_isolated_for_pilot", "no_unexpected_billing_activity_since_last_attempt",
    "no_other_activity_during_gate5_window", "key_remains_in_user_controlled_encrypted_local_secret_store",
    "both_exact_models_available_and_not_deprecated", "generate_content_endpoint_confirmed_for_both_models",
    "common_low_thinking_confirmed_for_both_models", "structured_output_field_confirmed_for_both_models",
    "response_usage_shape_confirmed", "fixed_24_slot_scope_confirmed", "v6_terminal_evidence_verified",
    "eighteen_historical_cost_components_confirmed", "fifteen_attempt_v7_campaign_bound_understood",
    "v7_prompt_and_schedule_scope_understood", "schema_diagnostic_text_exclusion_understood",
    "four_code_pause_whitelist_understood", "all_other_outcomes_hard_terminal_understood",
    "pause_requires_fresh_johnny_review_understood", "next_day_refresh_fail_closed_understood",
    "screened_raw_output_diagnostic_boundary_understood", "provider_safety_and_citation_withholding_understood",
    "raw_output_diagnostic_persistence_failure_terminal_understood", "v7_campaign_execution_authorized_by_johnny",
}


class Gate5PaidPilotRetryCampaignV7AttestationError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5PaidPilotRetryCampaignV7AttestationError("duplicate attestation key")
        value[key] = item
    return value


def current_build_hashes() -> dict[str, str]:
    try:
        return {name: v7_engine.canonical_hash(path) for name, path in BUILD_PATHS.items()}
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignV7AttestationError("V7 build unavailable") from exc


def validate_attestation(path: Path, expected_execution_date: str | None = None) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
        template = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v7_attestation_template.json")
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignV7AttestationError("attestation unreadable") from exc
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5PaidPilotRetryCampaignV7AttestationError("attestation fields drifted")
    required_date = expected_execution_date or date.today().isoformat()
    if value.get("artifact") != "gemini_generator_gate5_paid_pilot_retry_campaign_v7_attestation" or value.get("attestor") != "Johnny" or value.get("execution_date") != required_date:
        raise Gate5PaidPilotRetryCampaignV7AttestationError("attestation identity or date invalid")
    expected_evidence = {**EXPECTED_V6, **EXPECTED_BUILD, **current_build_hashes()}
    if any(value.get(name) != expected for name, expected in expected_evidence.items()):
        raise Gate5PaidPilotRetryCampaignV7AttestationError("V7 evidence mismatch")
    if any(value.get(name) is not True for name in TRUE_FIELDS):
        raise Gate5PaidPilotRetryCampaignV7AttestationError("required paid-pilot campaign V7 fact is unconfirmed")
    rate_hash = value.get("execution_day_rate_snapshot_sha256")
    if value.get("execution_day_rate_snapshot_status") != "execution_day_verified" or not isinstance(rate_hash, str) or not HASH_RE.fullmatch(rate_hash):
        raise Gate5PaidPilotRetryCampaignV7AttestationError("rate snapshot invalid")
    balance = value.get("positive_prepaid_balance_usd_millionths")
    if type(balance) is not int or balance < v7_engine.V7_PILOT_CEILING:
        raise Gate5PaidPilotRetryCampaignV7AttestationError("prepaid balance insufficient")
    expected_numbers = {
        "pilot_ceiling_usd_millionths": v7_engine.V7_PILOT_CEILING,
        "reconciliation_stop_usd_millionths": v7_engine.V7_RECONCILIATION_STOP,
        "maximum_campaign_attempts": MAX_CAMPAIGN_ATTEMPTS,
        "initial_historical_component_count": INITIAL_COMPONENT_COUNT,
        "prior_pilot_booked_cost_usd_millionths": ATTESTED_BASELINE_COST,
        "v7_worst_case_aggregate_usd_millionths": 3_230_880,
    }
    if any(value.get(name) != expected for name, expected in expected_numbers.items()):
        raise Gate5PaidPilotRetryCampaignV7AttestationError("V7 campaign cost or count drifted")
    if gate2.contains_secret(value):
        raise Gate5PaidPilotRetryCampaignV7AttestationError("secret-like value in attestation")
    return value
