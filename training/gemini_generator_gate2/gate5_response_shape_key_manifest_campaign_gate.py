"""Local-only validator for the bounded key-manifest campaign attestation."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import gate2

PACKAGE = Path(__file__).resolve().parent
EXPECTED = {
    "campaign_proposal_sha256": "bf557060226fff3377de22f4dce4df776f7925581b10a9c9a03d98a337ffb0e9",
    "first_receipt_file_sha256": "4cf8be458dbc639d6336c9832a3538ad79f6423d10cb1069eb4b1612bf05711c",
    "first_receipt_row_sha256": "391215e0ee809e79f59bcceb636efb47acd1c50af37ff055471c3411ca151531",
    "first_attempt_lock_file_sha256": "48dc28526a2ba5b4ce310e15467e6899e36aa6521bae338f377f60dfd86c065a",
    "first_attestation_sha256": "6407098105d1b57369cb68ca3d161e162be47fc9c0146db52b1a30db85aaba31",
    "second_receipt_file_sha256": "bee2e6cdface66cf0bdb46d535e410717806a371bb9d548e3e70d23cd3de3b6f",
    "second_receipt_row_sha256": "31b8e0010fd4ed16a931263e8e6f407fc1096b7a0b076dd48795ceee3b0ce96c",
    "second_reservation_file_sha256": "96c901826f6577ddfaf695470e9a82a9856457316a7936e2c37d3d9e16812512",
    "second_attempt_lock_file_sha256": "2c979648e8c3e868d243b18c6346ed8714c312c47e227f57f61e3d55285a3a0d",
    "second_attestation_sha256": "8218134dcb626e47ef881417f804e57503b1e441e477333a5a4f136a5be57117",
    "consumed_raw_response_sha256": "01f5c7d4e4d8ec06c8098777e731b3d552ba518feb02b681f6c569edcd9c6f6d",
    "provider_contract_sha256": "4312688168dd349f04bf4307816bded0b98edc9c358873f57fb5e347d2fe431c",
    "provider_schema_sha256": "b069fbf77d439030ee018f2a773bff07c06f0ded53108d8b98819ee0ba656812",
    "request_envelope_sha256": "8420c2d8360f4ffc96fb617dd8d4b081732cf2c87654a65d3ddc2ab8426297b4",
    "execution_day_rate_snapshot_sha256": "f24991917538caf8bcf4340f18ef0a78cbdeadce6e14845b5fe28e69720ddca2",
}
PER_ATTEMPT_CAP = 10_680
MAX_ATTEMPTS = 20
AGGREGATE_CAP = PER_ATTEMPT_CAP * MAX_ATTEMPTS
TRUE_FIELDS = {
    "paid_tier_confirmed_that_day", "prepay_plan_confirmed_that_day", "auto_reload_off_that_day",
    "billing_account_currently_isolated_for_pilot", "no_unexpected_billing_activity_since_second_503",
    "no_other_gemini_api_activity_since_second_503", "model_and_rates_rechecked_that_day",
    "both_consumed_503_records_reviewed", "manual_invocation_only_understood",
    "per_attempt_and_aggregate_caps_understood", "permanent_stop_on_first_non_503_understood",
    "key_names_only_evidence_boundary_reviewed", "in_memory_response_structure_inspection_understood",
    "campaign_execution_authorized_by_johnny", "key_remains_in_user_controlled_encrypted_local_secret_store",
}


class Gate5KeyManifestCampaignAttestationError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5KeyManifestCampaignAttestationError("duplicate attestation key")
        value[key] = item
    return value


def validate_attestation(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Gate5KeyManifestCampaignAttestationError) as exc:
        raise Gate5KeyManifestCampaignAttestationError("attestation unreadable") from exc
    template = gate2.load_json(PACKAGE / "gate5_response_shape_key_manifest_campaign_attestation_template.json")
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5KeyManifestCampaignAttestationError("attestation fields drifted")
    if value["artifact"] != "gemini_generator_gate5_response_shape_key_manifest_campaign_attestation" or value["attestor"] != "Johnny" or value["execution_date"] != date.today().isoformat():
        raise Gate5KeyManifestCampaignAttestationError("attestation identity or date invalid")
    if any(value[name] != expected for name, expected in EXPECTED.items()):
        raise Gate5KeyManifestCampaignAttestationError("attestation evidence hash mismatch")
    if value["execution_day_rate_snapshot_status"] != "execution_day_verified" or any(value[field] is not True for field in TRUE_FIELDS):
        raise Gate5KeyManifestCampaignAttestationError("required key-manifest campaign fact is unconfirmed")
    balance = value["positive_prepaid_balance_usd_millionths"]
    if type(balance) is not int or balance < AGGREGATE_CAP or value["per_attempt_cap_usd_millionths"] != PER_ATTEMPT_CAP or value["maximum_provider_requests"] != MAX_ATTEMPTS or value["aggregate_cap_usd_millionths"] != AGGREGATE_CAP:
        raise Gate5KeyManifestCampaignAttestationError("campaign cost, count, or balance invalid")
    if gate2.contains_secret(value):
        raise Gate5KeyManifestCampaignAttestationError("secret-like value in attestation")
    return value
