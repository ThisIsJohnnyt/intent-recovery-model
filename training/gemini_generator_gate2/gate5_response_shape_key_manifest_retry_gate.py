"""Local-only validator for the response-shape key-manifest retry attestation."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import gate2

PACKAGE = Path(__file__).resolve().parent
EXPECTED = {
    "retry_proposal_sha256": "403ee7c770893121ff6c70c82099365fa4823fa51a325060ea300b83a6287546",
    "original_proposal_sha256": "b361734c6fe329e96002237ea0b7babe671bd009f6b44297aa8f58f8fa3e41d5",
    "consumed_receipt_file_sha256": "4cf8be458dbc639d6336c9832a3538ad79f6423d10cb1069eb4b1612bf05711c",
    "consumed_receipt_row_sha256": "391215e0ee809e79f59bcceb636efb47acd1c50af37ff055471c3411ca151531",
    "consumed_raw_response_sha256": "01f5c7d4e4d8ec06c8098777e731b3d552ba518feb02b681f6c569edcd9c6f6d",
    "consumed_attempt_lock_file_sha256": "48dc28526a2ba5b4ce310e15467e6899e36aa6521bae338f377f60dfd86c065a",
    "consumed_attestation_sha256": "6407098105d1b57369cb68ca3d161e162be47fc9c0146db52b1a30db85aaba31",
    "incident_summary_file_sha256": "627ba8dfba9410a1201907f7d5eb2cce69b2d9f41111cd8c4e84f540f1c16050",
    "incident_receipt_row_sha256": "3db5178d10e4c5bfb556711bade9a25381ffffc5b63b78a9a3bef450546e3ee2",
    "incident_raw_response_sha256": "e349b43a5baa75dd3ce1890a2fea8973c7bdd8ec7bb9d40a04886c401a862d35",
    "prior_pilot_attestation_sha256": "a504ca4117a02613894f4244d9345c66cfc91a2b55489b2546a1bfcc0105673f",
    "provider_contract_sha256": "4312688168dd349f04bf4307816bded0b98edc9c358873f57fb5e347d2fe431c",
    "provider_schema_sha256": "b069fbf77d439030ee018f2a773bff07c06f0ded53108d8b98819ee0ba656812",
    "request_envelope_sha256": "8420c2d8360f4ffc96fb617dd8d4b081732cf2c87654a65d3ddc2ab8426297b4",
    "execution_day_rate_snapshot_sha256": "f24991917538caf8bcf4340f18ef0a78cbdeadce6e14845b5fe28e69720ddca2",
}
CAP = 10_680
TRUE_FIELDS = {
    "paid_tier_confirmed_that_day", "prepay_plan_confirmed_that_day", "auto_reload_off_that_day",
    "billing_account_currently_isolated_for_pilot", "no_unexpected_billing_activity_since_consumed_diagnostic",
    "no_other_gemini_api_activity_since_consumed_diagnostic", "model_and_rates_rechecked_that_day",
    "consumed_503_evidence_reviewed", "key_names_only_evidence_boundary_reviewed",
    "in_memory_response_structure_inspection_understood", "one_retry_request_authorized_by_johnny",
    "key_remains_in_user_controlled_encrypted_local_secret_store",
}


class Gate5KeyManifestRetryAttestationError(RuntimeError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5KeyManifestRetryAttestationError("duplicate attestation key")
        value[key] = item
    return value


def validate_attestation(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, Gate5KeyManifestRetryAttestationError) as exc:
        raise Gate5KeyManifestRetryAttestationError("attestation unreadable") from exc
    template = gate2.load_json(PACKAGE / "gate5_response_shape_key_manifest_retry_attestation_template.json")
    if not isinstance(value, dict) or set(value) != set(template):
        raise Gate5KeyManifestRetryAttestationError("attestation fields drifted")
    if value["artifact"] != "gemini_generator_gate5_response_shape_key_manifest_retry_attestation" or value["attestor"] != "Johnny" or value["execution_date"] != date.today().isoformat():
        raise Gate5KeyManifestRetryAttestationError("attestation identity or date invalid")
    if any(value[name] != expected for name, expected in EXPECTED.items()):
        raise Gate5KeyManifestRetryAttestationError("attestation evidence hash mismatch")
    if value["execution_day_rate_snapshot_status"] != "execution_day_verified" or any(value[field] is not True for field in TRUE_FIELDS):
        raise Gate5KeyManifestRetryAttestationError("required key-manifest retry fact is unconfirmed")
    balance = value["positive_prepaid_balance_usd_millionths"]
    if type(balance) is not int or balance < CAP or value["cost_cap_usd_millionths"] != CAP:
        raise Gate5KeyManifestRetryAttestationError("diagnostic cost or balance invalid")
    if gate2.contains_secret(value):
        raise Gate5KeyManifestRetryAttestationError("secret-like value in attestation")
    return value
