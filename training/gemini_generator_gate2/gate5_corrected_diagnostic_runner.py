"""Retired corrected-wire-format diagnostic receipt verifier.

The one authorized corrected diagnostic already ran. Its request envelope is
now superseded by the separate provider-schema type correction, so this module
preserves local receipt verification but contains no credential or network code.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import gate2


PACKAGE = Path(__file__).resolve().parent
PROPOSAL_PATH = PACKAGE / "gate5_generate_content_wire_format_diagnostic_proposal.md"
EXPECTED_PROPOSAL_SHA256 = "a7fb911034a15b8870adb88ed81beda7d5eb64e8ee8681dd6e1a08647da86dc5"
EXPECTED_CONTRACT_SHA256 = "5c47896310f9145ea62ec3fcea08d10038ff06f6125c632740222bd3d5f430ab"
EXPECTED_REQUEST_HASH = "0b0d3dfb09f428f6c447e3b97407f6aa966f6519f7ba2962a4cd15432b626e7b"
DIAGNOSTIC_CAP = 10_680
MAX_RESPONSE_BYTES = 1_024 * 1_024
RETIRED_STOP_REASON = "corrected_diagnostic_superseded_by_provider_schema_type_correction"


class Gate5CorrectedDiagnosticStop(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def proposal_hash() -> str:
    try:
        return gate2.sha256_bytes(gate2.canonical_file(PROPOSAL_PATH)[0])
    except (gate2.Gate2Error, OSError) as exc:
        raise Gate5CorrectedDiagnosticStop("diagnostic_proposal_unavailable") from exc


def verify_only() -> dict[str, Any]:
    digest = proposal_hash()
    return {
        "artifact": "gemini_generator_gate5_corrected_diagnostic_verify_only",
        "proposal_sha256": digest,
        "proposal_matches_frozen": digest == EXPECTED_PROPOSAL_SHA256,
        "historical_request_hash": EXPECTED_REQUEST_HASH,
        "diagnostic_retired": True,
        "stop_reason": RETIRED_STOP_REASON,
        "network_used": False,
        "credential_read": False,
        "file_output_created": False,
    }


def verify_receipt(receipt: dict[str, Any]) -> None:
    expected_fields = {"artifact", "proposal_sha256", "corrected_contract_sha256", "attestation_sha256", "execution_timestamp_utc", "transport", "response", "cost", "redaction_scan", "disposition", "stop_reason", "row_hash"}
    if set(receipt) != expected_fields or receipt["artifact"] != "gemini_generator_gate5_corrected_diagnostic_receipt":
        raise Gate5CorrectedDiagnosticStop("receipt_invalid")
    if receipt["proposal_sha256"] != EXPECTED_PROPOSAL_SHA256 or receipt["corrected_contract_sha256"] != EXPECTED_CONTRACT_SHA256 or not isinstance(receipt["attestation_sha256"], str) or not gate2.HEX64_RE.fullmatch(receipt["attestation_sha256"]):
        raise Gate5CorrectedDiagnosticStop("receipt_invalid")
    payload = {key: value for key, value in receipt.items() if key != "row_hash"}
    if receipt["row_hash"] != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)) or gate2.contains_secret(receipt):
        raise Gate5CorrectedDiagnosticStop("receipt_invalid")
    transport = receipt["transport"]
    expected_transport = {"method", "endpoint", "request_hash", "header_names", "timeout_seconds", "provider_request_count", "redirects_disabled", "retries_disabled"}
    if set(transport) != expected_transport or transport["method"] != "POST" or transport["endpoint"] != "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent" or transport["request_hash"] != EXPECTED_REQUEST_HASH or transport["header_names"] != ["Content-Type", "x-goog-api-key"] or transport["timeout_seconds"] != 60 or transport["provider_request_count"] not in {0, 1} or transport["redirects_disabled"] is not True or transport["retries_disabled"] is not True:
        raise Gate5CorrectedDiagnosticStop("receipt_invalid")
    response = receipt["response"]
    if set(response) != {"http_status", "byte_count", "sha256"}:
        raise Gate5CorrectedDiagnosticStop("receipt_invalid")
    if response["http_status"] is None:
        if response["byte_count"] is not None or response["sha256"] is not None:
            raise Gate5CorrectedDiagnosticStop("receipt_invalid")
    elif type(response["http_status"]) is not int or not 100 <= response["http_status"] <= 599 or type(response["byte_count"]) is not int or not 0 <= response["byte_count"] <= MAX_RESPONSE_BYTES or not isinstance(response["sha256"], str) or not gate2.HEX64_RE.fullmatch(response["sha256"]):
        raise Gate5CorrectedDiagnosticStop("receipt_invalid")
    cost = receipt["cost"]
    if set(cost) != {"authorized_cap_usd_millionths", "pre_request_reservation_usd_millionths", "actual_usd_millionths", "reconciliation_state"} or cost["authorized_cap_usd_millionths"] != DIAGNOSTIC_CAP or cost["pre_request_reservation_usd_millionths"] != DIAGNOSTIC_CAP:
        raise Gate5CorrectedDiagnosticStop("receipt_invalid")
    if transport["provider_request_count"] == 0:
        if cost["actual_usd_millionths"] is not None or cost["reconciliation_state"] != "not_requested":
            raise Gate5CorrectedDiagnosticStop("receipt_invalid")
    elif cost["actual_usd_millionths"] != DIAGNOSTIC_CAP or cost["reconciliation_state"] != "reserved_pending_billing":
        raise Gate5CorrectedDiagnosticStop("receipt_invalid")
    scan = receipt["redaction_scan"]
    if set(scan) != {"key_like_value_found", "raw_error_persisted"} or scan["key_like_value_found"] is not False or scan["raw_error_persisted"] is not False:
        raise Gate5CorrectedDiagnosticStop("receipt_invalid")


def execute_once() -> None:
    if proposal_hash() != EXPECTED_PROPOSAL_SHA256:
        raise Gate5CorrectedDiagnosticStop("diagnostic_proposal_hash_mismatch")
    raise Gate5CorrectedDiagnosticStop(RETIRED_STOP_REASON)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--execute-corrected-diagnostic-once", action="store_true")
    args = parser.parse_args()
    if args.verify_only == args.execute_corrected_diagnostic_once:
        parser.error("choose exactly one of --verify-only or --execute-corrected-diagnostic-once")
    if args.verify_only:
        print(json.dumps(verify_only(), sort_keys=True))
        return 0
    try:
        execute_once()
    except Gate5CorrectedDiagnosticStop as exc:
        print(json.dumps({"disposition": "stopped", "stop_reason": exc.code}, sort_keys=True))
        return 2
    raise AssertionError("retired diagnostic unexpectedly returned")


if __name__ == "__main__":
    raise SystemExit(main())
