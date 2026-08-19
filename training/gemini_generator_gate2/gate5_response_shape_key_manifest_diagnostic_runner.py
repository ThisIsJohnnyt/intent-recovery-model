"""Retired verifier for the consumed key-manifest diagnostic.

The one authorized request returned HTTP 503 and consumed its fixed attempt
lock. This module contains no credential or transport code. It only verifies
the immutable historical receipt and refuses every execution attempt.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import gate2

PACKAGE = Path(__file__).resolve().parent
PROPOSAL_PATH = PACKAGE / "gate5_response_shape_key_manifest_diagnostic_proposal.md"
RECEIPT_PATH = PACKAGE / "gate5_key_manifest_diagnostic_2026-08-16" / "key_manifest_diagnostic_receipt.json"
ATTEMPT_LOCK_PATH = PACKAGE / "gate5_response_shape_key_manifest_diagnostic_attempt.json"
ATTESTATION_PATH = PACKAGE / "gate5_response_shape_key_manifest_diagnostic_attestation_2026-08-16.json"
EXPECTED_PROPOSAL = "b361734c6fe329e96002237ea0b7babe671bd009f6b44297aa8f58f8fa3e41d5"
EXPECTED_RECEIPT_FILE = "4cf8be458dbc639d6336c9832a3538ad79f6423d10cb1069eb4b1612bf05711c"
EXPECTED_RECEIPT_ROW = "391215e0ee809e79f59bcceb636efb47acd1c50af37ff055471c3411ca151531"
EXPECTED_LOCK_FILE = "48dc28526a2ba5b4ce310e15467e6899e36aa6521bae338f377f60dfd86c065a"
EXPECTED_ATTESTATION = "6407098105d1b57369cb68ca3d161e162be47fc9c0146db52b1a30db85aaba31"
EXPECTED_REQUEST = "8420c2d8360f4ffc96fb617dd8d4b081732cf2c87654a65d3ddc2ab8426297b4"
EXPECTED_RESPONSE = "01f5c7d4e4d8ec06c8098777e731b3d552ba518feb02b681f6c569edcd9c6f6d"
EXPECTED_MESSAGE = "This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later."
CAP = 10_680
RETIRED_STOP_REASON = "key_manifest_diagnostic_consumed_by_http_503"


class Gate5KeyManifestStop(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _canonical_hash(path: Path) -> str:
    try:
        return gate2.sha256_bytes(gate2.canonical_file(path)[0])
    except (gate2.Gate2Error, OSError) as exc:
        raise Gate5KeyManifestStop("historical_evidence_invalid") from exc


def verify_receipt(receipt: dict[str, Any]) -> None:
    fields = {"artifact", "proposal_sha256", "incident_summary_file_sha256", "incident_receipt_row_sha256", "incident_raw_response_sha256", "prior_pilot_attestation_sha256", "provider_contract_sha256", "provider_schema_sha256", "request_envelope_sha256", "execution_day_rate_snapshot_sha256", "rate_snapshot_sha256", "attestation_sha256", "execution_timestamp_utc", "transport", "response", "cost", "key_manifest_capture_state", "key_manifest", "non_200_error_capture_state", "non_200_provider_error_message", "redaction_scan", "disposition", "stop_reason", "row_hash"}
    if not isinstance(receipt, dict) or set(receipt) != fields or receipt["artifact"] != "gemini_generator_gate5_response_shape_key_manifest_diagnostic_receipt" or receipt["proposal_sha256"] != EXPECTED_PROPOSAL or receipt["attestation_sha256"] != EXPECTED_ATTESTATION or receipt["row_hash"] != EXPECTED_RECEIPT_ROW:
        raise Gate5KeyManifestStop("historical_receipt_invalid")
    payload = {key: value for key, value in receipt.items() if key != "row_hash"}
    if receipt["row_hash"] != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)) or gate2.contains_secret(receipt):
        raise Gate5KeyManifestStop("historical_receipt_invalid")
    if receipt["transport"] != {"method": "POST", "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent", "request_envelope_sha256": EXPECTED_REQUEST, "header_names": ["Content-Type", "x-goog-api-key"], "timeout_seconds": 60, "provider_request_count": 1, "redirects_disabled": True, "retries_disabled": True}:
        raise Gate5KeyManifestStop("historical_receipt_invalid")
    if receipt["response"] != {"http_status": 503, "byte_count": 198, "sha256": EXPECTED_RESPONSE} or receipt["cost"] != {"authorized_cap_usd_millionths": CAP, "pre_request_reservation_usd_millionths": CAP, "actual_usd_millionths": CAP, "reconciliation_state": "reserved_pending_billing"}:
        raise Gate5KeyManifestStop("historical_receipt_invalid")
    if receipt["key_manifest_capture_state"] != "not_applicable_non_200" or receipt["key_manifest"] is not None or receipt["non_200_error_capture_state"] != "captured" or receipt["non_200_provider_error_message"] != EXPECTED_MESSAGE or receipt["disposition"] != "stopped" or receipt["stop_reason"] != "unexpected_http_status" or receipt["redaction_scan"] != {"key_like_value_found": False, "raw_response_persisted": False, "response_value_persisted": False}:
        raise Gate5KeyManifestStop("historical_receipt_invalid")


def verify_only() -> dict[str, Any]:
    try:
        receipt = gate2.load_json(RECEIPT_PATH)
    except (gate2.Gate2Error, OSError) as exc:
        raise Gate5KeyManifestStop("historical_evidence_invalid") from exc
    verify_receipt(receipt)
    if _canonical_hash(PROPOSAL_PATH) != EXPECTED_PROPOSAL or _canonical_hash(RECEIPT_PATH) != EXPECTED_RECEIPT_FILE or _canonical_hash(ATTEMPT_LOCK_PATH) != EXPECTED_LOCK_FILE or _canonical_hash(ATTESTATION_PATH) != EXPECTED_ATTESTATION:
        raise Gate5KeyManifestStop("historical_evidence_invalid")
    return {"artifact": "gemini_generator_gate5_response_shape_key_manifest_diagnostic_verify_only", "diagnostic_retired": True, "stop_reason": RETIRED_STOP_REASON, "historical_http_status": 503, "historical_receipt_row_sha256": receipt["row_hash"], "network_used": False, "credential_read": False, "file_output_created": False}


def execute_once(*_args: Any, **_kwargs: Any) -> None:
    raise Gate5KeyManifestStop(RETIRED_STOP_REASON)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--execute-key-manifest-diagnostic-once", action="store_true")
    args = parser.parse_args()
    if args.verify_only == args.execute_key_manifest_diagnostic_once:
        parser.error("choose exactly one mode")
    if args.verify_only:
        print(json.dumps(verify_only(), sort_keys=True))
        return 0
    try:
        execute_once()
    except Gate5KeyManifestStop as exc:
        print(json.dumps({"disposition": "stopped", "stop_reason": exc.code}, sort_keys=True))
        return 2
    raise AssertionError("retired diagnostic unexpectedly returned")


if __name__ == "__main__":
    raise SystemExit(main())
