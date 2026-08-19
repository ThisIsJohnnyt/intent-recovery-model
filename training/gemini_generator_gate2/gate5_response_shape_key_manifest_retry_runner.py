"""Retired verifier for the consumed key-manifest retry diagnostic."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import gate2

PACKAGE = Path(__file__).resolve().parent
PROPOSAL_PATH = PACKAGE / "gate5_response_shape_key_manifest_retry_proposal.md"
RECEIPT_PATH = PACKAGE / "gate5_key_manifest_retry_2026-08-16" / "key_manifest_retry_receipt.json"
RESERVATION_PATH = PACKAGE / "gate5_key_manifest_retry_2026-08-16" / "key_manifest_retry_reservation.json"
ATTEMPT_LOCK_PATH = PACKAGE / "gate5_response_shape_key_manifest_retry_attempt.json"
ATTESTATION_PATH = PACKAGE / "gate5_response_shape_key_manifest_retry_attestation_2026-08-16.json"
EXPECTED_PROPOSAL = "403ee7c770893121ff6c70c82099365fa4823fa51a325060ea300b83a6287546"
EXPECTED_RECEIPT_FILE = "bee2e6cdface66cf0bdb46d535e410717806a371bb9d548e3e70d23cd3de3b6f"
EXPECTED_RECEIPT_ROW = "31b8e0010fd4ed16a931263e8e6f407fc1096b7a0b076dd48795ceee3b0ce96c"
EXPECTED_RESERVATION_FILE = "96c901826f6577ddfaf695470e9a82a9856457316a7936e2c37d3d9e16812512"
EXPECTED_LOCK_FILE = "2c979648e8c3e868d243b18c6346ed8714c312c47e227f57f61e3d55285a3a0d"
EXPECTED_ATTESTATION = "8218134dcb626e47ef881417f804e57503b1e441e477333a5a4f136a5be57117"
EXPECTED_REQUEST = "8420c2d8360f4ffc96fb617dd8d4b081732cf2c87654a65d3ddc2ab8426297b4"
EXPECTED_RESPONSE = "01f5c7d4e4d8ec06c8098777e731b3d552ba518feb02b681f6c569edcd9c6f6d"
EXPECTED_MESSAGE = "This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later."
CAP = 10_680
RETIRED_STOP_REASON = "key_manifest_retry_consumed_by_http_503"


class Gate5KeyManifestRetryStop(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _canonical_hash(path: Path) -> str:
    try:
        return gate2.sha256_bytes(gate2.canonical_file(path)[0])
    except (gate2.Gate2Error, OSError) as exc:
        raise Gate5KeyManifestRetryStop("historical_evidence_invalid") from exc


def verify_receipt(receipt: dict[str, Any]) -> None:
    if not isinstance(receipt, dict) or receipt.get("artifact") != "gemini_generator_gate5_response_shape_key_manifest_retry_receipt" or receipt.get("row_hash") != EXPECTED_RECEIPT_ROW:
        raise Gate5KeyManifestRetryStop("historical_receipt_invalid")
    payload = {key: value for key, value in receipt.items() if key != "row_hash"}
    if receipt["row_hash"] != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)) or gate2.contains_secret(receipt):
        raise Gate5KeyManifestRetryStop("historical_receipt_invalid")
    if receipt.get("attestation_sha256") != EXPECTED_ATTESTATION or receipt.get("retry_proposal_sha256") != EXPECTED_PROPOSAL:
        raise Gate5KeyManifestRetryStop("historical_receipt_invalid")
    expected_transport = {"method": "POST", "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent", "request_envelope_sha256": EXPECTED_REQUEST, "header_names": ["Content-Type", "x-goog-api-key"], "timeout_seconds": 60, "provider_request_count": 1, "redirects_disabled": True, "retries_disabled": True}
    if receipt.get("transport") != expected_transport or receipt.get("response") != {"http_status": 503, "byte_count": 198, "sha256": EXPECTED_RESPONSE}:
        raise Gate5KeyManifestRetryStop("historical_receipt_invalid")
    if receipt.get("cost") != {"authorized_cap_usd_millionths": CAP, "pre_request_reservation_usd_millionths": CAP, "actual_usd_millionths": CAP, "reconciliation_state": "reserved_pending_billing"}:
        raise Gate5KeyManifestRetryStop("historical_receipt_invalid")
    if receipt.get("key_manifest_capture_state") != "not_applicable_non_200" or receipt.get("key_manifest") is not None or receipt.get("non_200_error_capture_state") != "captured" or receipt.get("non_200_provider_error_message") != EXPECTED_MESSAGE:
        raise Gate5KeyManifestRetryStop("historical_receipt_invalid")
    if receipt.get("disposition") != "stopped" or receipt.get("stop_reason") != "unexpected_http_status" or receipt.get("redaction_scan") != {"key_like_value_found": False, "raw_response_persisted": False, "response_value_persisted": False}:
        raise Gate5KeyManifestRetryStop("historical_receipt_invalid")


def verify_only() -> dict[str, Any]:
    try:
        receipt = gate2.load_json(RECEIPT_PATH)
    except (gate2.Gate2Error, OSError) as exc:
        raise Gate5KeyManifestRetryStop("historical_evidence_invalid") from exc
    verify_receipt(receipt)
    expected_files = {
        PROPOSAL_PATH: EXPECTED_PROPOSAL,
        RECEIPT_PATH: EXPECTED_RECEIPT_FILE,
        RESERVATION_PATH: EXPECTED_RESERVATION_FILE,
        ATTEMPT_LOCK_PATH: EXPECTED_LOCK_FILE,
        ATTESTATION_PATH: EXPECTED_ATTESTATION,
    }
    if any(_canonical_hash(path) != expected for path, expected in expected_files.items()):
        raise Gate5KeyManifestRetryStop("historical_evidence_invalid")
    return {"artifact": "gemini_generator_gate5_response_shape_key_manifest_retry_verify_only", "diagnostic_retired": True, "stop_reason": RETIRED_STOP_REASON, "historical_http_status": 503, "historical_receipt_row_sha256": receipt["row_hash"], "network_used": False, "credential_read": False, "file_output_created": False}


def execute_once(*_args: Any, **_kwargs: Any) -> None:
    raise Gate5KeyManifestRetryStop(RETIRED_STOP_REASON)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--execute-key-manifest-retry-once", action="store_true")
    args = parser.parse_args()
    if args.verify_only == args.execute_key_manifest_retry_once:
        parser.error("choose exactly one mode")
    if args.verify_only:
        print(json.dumps(verify_only(), sort_keys=True))
        return 0
    try:
        execute_once()
    except Gate5KeyManifestRetryStop as exc:
        print(json.dumps({"disposition": "stopped", "stop_reason": exc.code}, sort_keys=True))
        return 2
    raise AssertionError("retired retry unexpectedly returned")


if __name__ == "__main__":
    raise SystemExit(main())
