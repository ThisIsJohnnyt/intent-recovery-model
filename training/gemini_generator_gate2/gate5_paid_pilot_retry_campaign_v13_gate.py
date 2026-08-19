"""Local-only attestation gate for the Gate 5 paid-pilot V13 collision-length-metadata campaign."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import gate2
import gate5_paid_pilot_v13_engine as v13_engine


PACKAGE = Path(__file__).resolve().parent
HASH_RE = re.compile(r"[0-9a-f]{64}")
ATTESTED_BASELINE_COST = 1_418_181
INITIAL_COMPONENT_COUNT = 29
INITIAL_COMPONENT_MANIFEST_SHA256 = "9c8fe710e2112727fc9f03fb7951bef7b065fabeb70af2375aefeb0037ace69d"
# V12 r2's own real terminal evidence, independently re-derived and pinned --
# this is the campaign V13's historical baseline is built on top of, exactly
# as V12 built on top of V11's, V11 built on top of V10's, and so on. V12's
# FIRST attempt hard-stopped on a real, now-fixed production bug
# (output_collision_diagnostic_withheld) and was never chained forward --
# only the real, completed r2 run becomes historical component 29, the same
# way V12 r2 itself was built on V11's unchanged 28-component baseline
# rather than folding V12's own aborted first attempt in first.
EXPECTED_V12 = {
    "v12_final_attestation_sha256": "f98ba755a9439e14f0f406ebae8455b688308b53d0a85ccf157f206ce25a73bd",
    "v12_terminal_campaign_ledger_sha256": "b089a5622c596d2d64c9dcd8129a7c2999ee923fc1cae4e1e41b73ea2433348b",
    "v12_terminal_run_summary_sha256": "603094639a36df542c50fc4d8eb13faca0f6ec1dbbf0eb47d7d5ce9627cd341b",
    "v12_terminal_state_row_sha256": "f1481e812bd0f6480941e3caa873eeb370399738b070d4c6f05fabde467d0e70",
    "v12_terminal_historical_component_manifest_sha256": "2e395714d00fbac5e2109ed02287a42e4e498ec717e4a5fcf639bed9b3a4926f",
}
EXPECTED_BUILD = {
    "v13_proposal_sha256": "9cea98551bbb6e309c239e58b29e64cd21652c35f95f6630c5d21fa6133de0b3",
    "v13_first_request_sha256": v13_engine.EXPECTED_V13_FIRST_REQUEST_SHA256,
    "v13_reused_v8_schedule_sha256": v13_engine.EXPECTED_V8_SCHEDULE_SHA256,
}
BUILD_PATHS = {
    "v13_engine_sha256": PACKAGE / "gate5_paid_pilot_v13_engine.py",
    "v13_gate_sha256": Path(__file__).resolve(),
    "v13_attestation_template_sha256": PACKAGE / "gate5_paid_pilot_retry_campaign_v13_attestation_template.json",
    "v13_campaign_runner_sha256": PACKAGE / "gate5_paid_pilot_retry_campaign_v13_runner.py",
    "v13_focused_campaign_tests_sha256": PACKAGE / "test_gate5_paid_pilot_retry_campaign_v13.py",
    "v13_collision_evidence_sha256": PACKAGE / "gate5_output_collision_evidence.py",
}
TRUE_FIELDS = {
    "paid_tier_confirmed_that_day", "prepay_plan_confirmed_that_day", "auto_reload_off_that_day",
    "billing_account_currently_isolated_for_pilot", "no_unexpected_billing_activity_since_last_attempt",
    "no_other_activity_during_gate5_window", "key_remains_in_user_controlled_encrypted_local_secret_store",
    "both_exact_models_available_and_not_deprecated", "generate_content_endpoint_confirmed_for_both_models",
    "common_low_thinking_confirmed_for_both_models", "structured_output_field_confirmed_for_both_models",
    "response_usage_shape_confirmed", "v12_terminal_evidence_verified",
    "twenty_nine_historical_cost_components_confirmed", "v13_full_schedule_single_pass_scope_understood",
    "v8_schedule_and_prompt_reused_unchanged_understood", "continue_past_collision_family_scope_understood",
    "continue_past_schema_invalid_scope_understood", "max_five_card_attempts_retry_scope_understood",
    "all_other_outcomes_hard_terminal_understood", "schema_diagnostic_text_exclusion_understood",
    "four_code_raw_diagnostic_whitelist_understood", "provider_safety_and_citation_withholding_understood",
    "raw_output_diagnostic_persistence_failure_terminal_understood",
    "live_progress_reporting_replaces_per_result_confirmation_understood",
    "candidate_screening_decision_logic_unchanged_from_v12_understood",
    "collision_length_metadata_is_two_integers_no_text_understood",
    "schema_version_2_diagnostic_rows_additive_not_replacing_v1_understood",
    "schema_floor_deferred_understood",
    "thresholds_schema_and_continue_past_ruleset_unchanged_understood",
    "v13_campaign_execution_authorized_by_johnny",
}


class Gate5PaidPilotRetryCampaignV13AttestationError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5PaidPilotRetryCampaignV13AttestationError("duplicate attestation key")
        value[key] = item
    return value


def current_build_hashes() -> dict[str, str]:
    try:
        return {name: v13_engine.canonical_hash(path) for name, path in BUILD_PATHS.items()}
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignV13AttestationError("V13 build unavailable") from exc


def validate_attestation(path: Path, expected_execution_date: str | None = None) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
        template = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v13_attestation_template.json")
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignV13AttestationError("attestation unreadable") from exc
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5PaidPilotRetryCampaignV13AttestationError("attestation fields drifted")
    required_date = expected_execution_date or date.today().isoformat()
    if value.get("artifact") != "gemini_generator_gate5_paid_pilot_retry_campaign_v13_attestation" or value.get("attestor") != "Johnny" or value.get("execution_date") != required_date:
        raise Gate5PaidPilotRetryCampaignV13AttestationError("attestation identity or date invalid")
    expected_evidence = {**EXPECTED_V12, **EXPECTED_BUILD, **current_build_hashes()}
    if any(value.get(name) != expected for name, expected in expected_evidence.items()):
        raise Gate5PaidPilotRetryCampaignV13AttestationError("V13 evidence mismatch")
    if any(value.get(name) is not True for name in TRUE_FIELDS):
        raise Gate5PaidPilotRetryCampaignV13AttestationError("required paid-pilot campaign V13 fact is unconfirmed")
    rate_hash = value.get("execution_day_rate_snapshot_sha256")
    if value.get("execution_day_rate_snapshot_status") != "execution_day_verified" or not isinstance(rate_hash, str) or not HASH_RE.fullmatch(rate_hash):
        raise Gate5PaidPilotRetryCampaignV13AttestationError("rate snapshot invalid")
    balance = value.get("positive_prepaid_balance_usd_millionths")
    if type(balance) is not int or balance < v13_engine.V13_PILOT_CEILING:
        raise Gate5PaidPilotRetryCampaignV13AttestationError("prepaid balance insufficient")
    expected_numbers = {
        "pilot_ceiling_usd_millionths": v13_engine.V13_PILOT_CEILING,
        "reconciliation_stop_usd_millionths": v13_engine.V13_RECONCILIATION_STOP,
        "max_card_attempts": v13_engine.MAX_CARD_ATTEMPTS,
        "initial_historical_component_count": INITIAL_COMPONENT_COUNT,
        "prior_pilot_booked_cost_usd_millionths": ATTESTED_BASELINE_COST,
        "v13_worst_case_aggregate_usd_millionths": 2_353_181,
    }
    if any(value.get(name) != expected for name, expected in expected_numbers.items()):
        raise Gate5PaidPilotRetryCampaignV13AttestationError("V13 campaign cost or count drifted")
    if gate2.contains_secret(value):
        raise Gate5PaidPilotRetryCampaignV13AttestationError("secret-like value in attestation")
    return value
