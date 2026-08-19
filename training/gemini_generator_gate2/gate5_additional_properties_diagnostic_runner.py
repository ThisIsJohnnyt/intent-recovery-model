"""Retired corrected-provider-schema diagnostic receipt verifier.

The one authorized diagnostic succeeded with HTTP 200. This module preserves
strict local verification of that immutable receipt but contains no credential,
HTTP, TLS, or provider execution path.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import gate2

PACKAGE = Path(__file__).resolve().parent
PROPOSAL = PACKAGE / "gate5_additional_properties_diagnostic_proposal.md"
EXPECTED_PROPOSAL = "3cd13bcc10bccde89456858de61ef6625285ea9655cf0d1761b45fd98da5518d"
EXPECTED_CONTRACT = "4312688168dd349f04bf4307816bded0b98edc9c358873f57fb5e347d2fe431c"
EXPECTED_SCHEMA = "b069fbf77d439030ee018f2a773bff07c06f0ded53108d8b98819ee0ba656812"
EXPECTED_REQUEST = "8420c2d8360f4ffc96fb617dd8d4b081732cf2c87654a65d3ddc2ab8426297b4"
EXPECTED_RECEIPT_ROW = "5d9c434994855bb81eaeb1fcbc4fce1746cd99a08b19715cbb3266bfd9ac0336"
CAP_USD_MILLIONTHS = 10_680
MAX_RESPONSE_BYTES = 1_024 * 1_024
RETIRED_STOP_REASON = "corrected_provider_schema_diagnostic_completed_and_retired"


class Gate5AdditionalPropertiesDiagnosticStop(RuntimeError):
    def __init__(self, code: str): self.code = code; super().__init__(code)


def proposal_hash() -> str:
    try: return gate2.sha256_bytes(gate2.canonical_file(PROPOSAL)[0])
    except (gate2.Gate2Error, OSError) as exc: raise Gate5AdditionalPropertiesDiagnosticStop("diagnostic_proposal_unavailable") from exc


def verify_only() -> dict[str, Any]:
    digest = proposal_hash()
    return {"artifact": "gemini_generator_gate5_additional_properties_diagnostic_verify_only", "proposal_sha256": digest, "proposal_matches_frozen": digest == EXPECTED_PROPOSAL, "historical_request_hash": EXPECTED_REQUEST, "historical_receipt_row_hash": EXPECTED_RECEIPT_ROW, "diagnostic_retired": True, "stop_reason": RETIRED_STOP_REASON, "network_used": False, "credential_read": False, "file_output_created": False}


def verify_receipt(receipt: dict[str, Any]) -> None:
    required = {"artifact", "proposal_sha256", "contract_sha256", "provider_schema_sha256", "attestation_sha256", "execution_timestamp_utc", "transport", "response", "cost", "redaction_scan", "error_message_capture_state", "non_200_provider_error_message", "disposition", "stop_reason", "row_hash"}
    if set(receipt) != required or receipt["artifact"] != "gemini_generator_gate5_additional_properties_diagnostic_receipt" or receipt["proposal_sha256"] != EXPECTED_PROPOSAL or receipt["contract_sha256"] != EXPECTED_CONTRACT or receipt["provider_schema_sha256"] != EXPECTED_SCHEMA or receipt["row_hash"] != EXPECTED_RECEIPT_ROW: raise Gate5AdditionalPropertiesDiagnosticStop("receipt_invalid")
    if not isinstance(receipt["attestation_sha256"], str) or not gate2.HEX64_RE.fullmatch(receipt["attestation_sha256"]): raise Gate5AdditionalPropertiesDiagnosticStop("receipt_invalid")
    payload = {key: value for key, value in receipt.items() if key != "row_hash"}
    if receipt["row_hash"] != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)) or gate2.contains_secret(receipt): raise Gate5AdditionalPropertiesDiagnosticStop("receipt_invalid")
    expected_transport = {"method": "POST", "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent", "request_hash": EXPECTED_REQUEST, "header_names": ["Content-Type", "x-goog-api-key"], "timeout_seconds": 60, "provider_request_count": 1, "redirects_disabled": True, "retries_disabled": True}
    if receipt["transport"] != expected_transport: raise Gate5AdditionalPropertiesDiagnosticStop("receipt_invalid")
    response = receipt["response"]
    if set(response) != {"http_status", "byte_count", "sha256"} or response["http_status"] != 200 or type(response["byte_count"]) is not int or not 0 <= response["byte_count"] <= MAX_RESPONSE_BYTES or not isinstance(response["sha256"], str) or not gate2.HEX64_RE.fullmatch(response["sha256"]): raise Gate5AdditionalPropertiesDiagnosticStop("receipt_invalid")
    if receipt["error_message_capture_state"] != "not_applicable_http_200" or receipt["non_200_provider_error_message"] is not None: raise Gate5AdditionalPropertiesDiagnosticStop("receipt_invalid")
    if receipt["cost"] != {"authorized_cap_usd_millionths": CAP_USD_MILLIONTHS, "pre_request_reservation_usd_millionths": CAP_USD_MILLIONTHS, "actual_usd_millionths": CAP_USD_MILLIONTHS, "reconciliation_state": "reserved_pending_billing"}: raise Gate5AdditionalPropertiesDiagnosticStop("receipt_invalid")
    if receipt["redaction_scan"] != {"key_like_value_found": False, "raw_error_persisted": False} or receipt["disposition"] != "completed_status_observed" or receipt["stop_reason"] != "additional_properties_diagnostic_one_request_complete": raise Gate5AdditionalPropertiesDiagnosticStop("receipt_invalid")


def execute_once(*_args: Any, **_kwargs: Any) -> None:
    raise Gate5AdditionalPropertiesDiagnosticStop(RETIRED_STOP_REASON)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--verify-only", action="store_true"); parser.add_argument("--execute-additional-properties-diagnostic-once", action="store_true"); args = parser.parse_args()
    if args.verify_only == args.execute_additional_properties_diagnostic_once: parser.error("choose exactly one mode")
    if args.verify_only: print(json.dumps(verify_only(), sort_keys=True)); return 0
    try: execute_once()
    except Gate5AdditionalPropertiesDiagnosticStop as exc: print(json.dumps({"disposition": "stopped", "stop_reason": exc.code}, sort_keys=True)); return 2
    raise AssertionError("retired diagnostic unexpectedly returned")


if __name__ == "__main__": raise SystemExit(main())
