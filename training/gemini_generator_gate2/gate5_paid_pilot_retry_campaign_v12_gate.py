"""Local-only attestation gate for the Gate 5 paid-pilot V12 stopword-filtered-char5gram-collision campaign."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import gate2
import gate5_paid_pilot_v12_engine as v12_engine


PACKAGE = Path(__file__).resolve().parent
HASH_RE = re.compile(r"[0-9a-f]{64}")
ATTESTED_BASELINE_COST = 1_054_949
INITIAL_COMPONENT_COUNT = 28
INITIAL_COMPONENT_MANIFEST_SHA256 = "2e395714d00fbac5e2109ed02287a42e4e498ec717e4a5fcf639bed9b3a4926f"
# V11's own real terminal evidence, independently re-derived and pinned --
# this is the campaign V12's historical baseline is built on top of, exactly
# as V11 built on top of V10's, V10 built on top of V9's, and V9 built on
# top of V8's.
EXPECTED_V11 = {
    "v11_final_attestation_sha256": "66c8ad1cf0992651450300e6361007b0e33728ac013a736829c9c4207f5ccd74",
    "v11_terminal_campaign_ledger_sha256": "0dd59f39b444255e2c328df939f22fe22ec376bb2750c68c29784e15bb7d9fed",
    "v11_terminal_run_summary_sha256": "e05c14c6d3eba846cdcabf5e531f20d78385d4cf60d2856c3fd5369a3ef72a81",
    "v11_terminal_state_row_sha256": "389dc583410f5dc261b6357d7efadf8bac5cb76a9e6786cd3204df2a8366fbb6",
    "v11_terminal_historical_component_manifest_sha256": "cb38bb45030b571f4cbc045fe062fe439a4396b9fafa98c8a7505732daa782d1",
}
EXPECTED_BUILD = {
    "v12_proposal_sha256": "e6c6a7c63b9a0f9da5bcb5e6f4589ac7691ae3515d23d321c4402d5179b23844",
    "v12_first_request_sha256": v12_engine.EXPECTED_V12_FIRST_REQUEST_SHA256,
    "v12_reused_v8_schedule_sha256": v12_engine.EXPECTED_V8_SCHEDULE_SHA256,
}
BUILD_PATHS = {
    "v12_engine_sha256": PACKAGE / "gate5_paid_pilot_v12_engine.py",
    "v12_gate_sha256": Path(__file__).resolve(),
    "v12_attestation_template_sha256": PACKAGE / "gate5_paid_pilot_retry_campaign_v12_attestation_template.json",
    "v12_campaign_runner_sha256": PACKAGE / "gate5_paid_pilot_retry_campaign_v12_runner.py",
    "v12_focused_campaign_tests_sha256": PACKAGE / "test_gate5_paid_pilot_retry_campaign_v12.py",
}
TRUE_FIELDS = {
    "paid_tier_confirmed_that_day", "prepay_plan_confirmed_that_day", "auto_reload_off_that_day",
    "billing_account_currently_isolated_for_pilot", "no_unexpected_billing_activity_since_last_attempt",
    "no_other_activity_during_gate5_window", "key_remains_in_user_controlled_encrypted_local_secret_store",
    "both_exact_models_available_and_not_deprecated", "generate_content_endpoint_confirmed_for_both_models",
    "common_low_thinking_confirmed_for_both_models", "structured_output_field_confirmed_for_both_models",
    "response_usage_shape_confirmed", "v11_terminal_evidence_verified",
    "twenty_eight_historical_cost_components_confirmed", "v12_full_schedule_single_pass_scope_understood",
    "v8_schedule_and_prompt_reused_unchanged_understood", "continue_past_collision_family_scope_understood",
    "continue_past_schema_invalid_scope_understood", "max_five_card_attempts_retry_scope_understood",
    "all_other_outcomes_hard_terminal_understood", "schema_diagnostic_text_exclusion_understood",
    "four_code_raw_diagnostic_whitelist_understood", "provider_safety_and_citation_withholding_understood",
    "raw_output_diagnostic_persistence_failure_terminal_understood",
    "live_progress_reporting_replaces_per_result_confirmation_understood",
    "stopword_filtered_token_jaccard_scope_understood",
    "stopword_filtered_char5gram_scope_understood",
    "schema_floor_deferred_understood",
    "thresholds_schema_and_continue_past_ruleset_unchanged_understood",
    "v12_campaign_execution_authorized_by_johnny",
}


class Gate5PaidPilotRetryCampaignV12AttestationError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5PaidPilotRetryCampaignV12AttestationError("duplicate attestation key")
        value[key] = item
    return value


def current_build_hashes() -> dict[str, str]:
    try:
        return {name: v12_engine.canonical_hash(path) for name, path in BUILD_PATHS.items()}
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignV12AttestationError("V12 build unavailable") from exc


def validate_attestation(path: Path, expected_execution_date: str | None = None) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
        template = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v12_attestation_template.json")
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignV12AttestationError("attestation unreadable") from exc
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5PaidPilotRetryCampaignV12AttestationError("attestation fields drifted")
    required_date = expected_execution_date or date.today().isoformat()
    if value.get("artifact") != "gemini_generator_gate5_paid_pilot_retry_campaign_v12_attestation" or value.get("attestor") != "Johnny" or value.get("execution_date") != required_date:
        raise Gate5PaidPilotRetryCampaignV12AttestationError("attestation identity or date invalid")
    expected_evidence = {**EXPECTED_V11, **EXPECTED_BUILD, **current_build_hashes()}
    if any(value.get(name) != expected for name, expected in expected_evidence.items()):
        raise Gate5PaidPilotRetryCampaignV12AttestationError("V12 evidence mismatch")
    if any(value.get(name) is not True for name in TRUE_FIELDS):
        raise Gate5PaidPilotRetryCampaignV12AttestationError("required paid-pilot campaign V12 fact is unconfirmed")
    rate_hash = value.get("execution_day_rate_snapshot_sha256")
    if value.get("execution_day_rate_snapshot_status") != "execution_day_verified" or not isinstance(rate_hash, str) or not HASH_RE.fullmatch(rate_hash):
        raise Gate5PaidPilotRetryCampaignV12AttestationError("rate snapshot invalid")
    balance = value.get("positive_prepaid_balance_usd_millionths")
    if type(balance) is not int or balance < v12_engine.V12_PILOT_CEILING:
        raise Gate5PaidPilotRetryCampaignV12AttestationError("prepaid balance insufficient")
    expected_numbers = {
        "pilot_ceiling_usd_millionths": v12_engine.V12_PILOT_CEILING,
        "reconciliation_stop_usd_millionths": v12_engine.V12_RECONCILIATION_STOP,
        "max_card_attempts": v12_engine.MAX_CARD_ATTEMPTS,
        "initial_historical_component_count": INITIAL_COMPONENT_COUNT,
        "prior_pilot_booked_cost_usd_millionths": ATTESTED_BASELINE_COST,
        "v12_worst_case_aggregate_usd_millionths": 1_989_949,
    }
    if any(value.get(name) != expected for name, expected in expected_numbers.items()):
        raise Gate5PaidPilotRetryCampaignV12AttestationError("V12 campaign cost or count drifted")
    if gate2.contains_secret(value):
        raise Gate5PaidPilotRetryCampaignV12AttestationError("secret-like value in attestation")
    return value
