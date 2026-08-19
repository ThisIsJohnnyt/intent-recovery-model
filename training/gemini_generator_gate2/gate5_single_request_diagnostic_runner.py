"""Retired one-request HTTP-status diagnostic for Gate 5.

This artifact preserves its historical receipt-validation code, but its former
execution path is permanently disabled because it pinned a rejected request
shape. A corrected request needs a new proposal and authorization chain.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import gate2


PACKAGE = Path(__file__).resolve().parent
PROPOSAL_PATH = PACKAGE / "gate5_single_request_diagnostic_proposal.md"
EXPECTED_PROPOSAL_SHA256 = "b42a5d3a43893b53b17714abc1587f1a926270a9425e8b0fb285c9ff523830fb"
EXPECTED_REQUEST_HASH = "02007b81e50d846c5a6cf3d321650c8a6c4c83ec60647d346d8d73c6450e3a36"
DIAGNOSTIC_CAP = 10_680
MAX_RESPONSE_BYTES = 1_024 * 1_024
RETIRED_STOP_REASON = "diagnostic_superseded_by_generate_content_wire_format_correction"


class Gate5DiagnosticStop(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def proposal_hash() -> str:
    try:
        return gate2.sha256_bytes(gate2.canonical_file(PROPOSAL_PATH)[0])
    except (gate2.Gate2Error, OSError) as exc:
        raise Gate5DiagnosticStop("diagnostic_proposal_unavailable") from exc


def verify_only() -> dict[str, Any]:
    digest = proposal_hash()
    return {
        "artifact": "gemini_generator_gate5_single_request_diagnostic_verify_only",
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
    fields = {
        "artifact", "proposal_sha256", "attestation_sha256", "execution_timestamp_utc", "transport",
        "response", "cost", "redaction_scan", "disposition", "stop_reason", "row_hash",
    }
    if set(receipt) != fields or receipt["artifact"] != "gemini_generator_gate5_single_request_diagnostic_receipt":
        raise Gate5DiagnosticStop("receipt_invalid")
    if receipt["proposal_sha256"] != EXPECTED_PROPOSAL_SHA256 or not gate2.HEX64_RE.fullmatch(receipt["attestation_sha256"]):
        raise Gate5DiagnosticStop("receipt_invalid")
    payload = {key: value for key, value in receipt.items() if key != "row_hash"}
    if receipt["row_hash"] != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)) or gate2.contains_secret(receipt):
        raise Gate5DiagnosticStop("receipt_invalid")
    transport = receipt["transport"]
    if set(transport) != {"method", "endpoint", "request_hash", "header_names", "timeout_seconds", "provider_request_count", "redirects_disabled", "retries_disabled"}:
        raise Gate5DiagnosticStop("receipt_invalid")
    if transport["method"] != "POST" or transport["request_hash"] != EXPECTED_REQUEST_HASH or transport["header_names"] != ["Content-Type", "x-goog-api-key"]:
        raise Gate5DiagnosticStop("receipt_invalid")
    expected_endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent"
    if transport["endpoint"] != expected_endpoint or transport["timeout_seconds"] != 60 or transport["provider_request_count"] not in {0, 1} or transport["redirects_disabled"] is not True or transport["retries_disabled"] is not True:
        raise Gate5DiagnosticStop("receipt_invalid")
    response = receipt["response"]
    if set(response) != {"http_status", "byte_count", "sha256"}:
        raise Gate5DiagnosticStop("receipt_invalid")
    if response["http_status"] is None:
        if response["byte_count"] is not None or response["sha256"] is not None:
            raise Gate5DiagnosticStop("receipt_invalid")
    elif type(response["http_status"]) is not int or not 100 <= response["http_status"] <= 599 or type(response["byte_count"]) is not int or not 0 <= response["byte_count"] <= MAX_RESPONSE_BYTES or not isinstance(response["sha256"], str) or not gate2.HEX64_RE.fullmatch(response["sha256"]):
        raise Gate5DiagnosticStop("receipt_invalid")
    if set(receipt["cost"]) != {"authorized_cap_usd_millionths", "pre_request_reservation_usd_millionths", "actual_usd_millionths", "reconciliation_state"}:
        raise Gate5DiagnosticStop("receipt_invalid")
    if receipt["cost"]["authorized_cap_usd_millionths"] != DIAGNOSTIC_CAP or receipt["cost"]["pre_request_reservation_usd_millionths"] != DIAGNOSTIC_CAP:
        raise Gate5DiagnosticStop("receipt_invalid")
    if receipt["transport"]["provider_request_count"] == 0:
        if receipt["cost"]["actual_usd_millionths"] is not None or receipt["cost"]["reconciliation_state"] != "not_requested":
            raise Gate5DiagnosticStop("receipt_invalid")
    elif receipt["cost"]["actual_usd_millionths"] != DIAGNOSTIC_CAP or receipt["cost"]["reconciliation_state"] != "reserved_pending_billing":
        raise Gate5DiagnosticStop("receipt_invalid")


def execute_once() -> None:
    digest = proposal_hash()
    if digest != EXPECTED_PROPOSAL_SHA256:
        raise Gate5DiagnosticStop("diagnostic_proposal_hash_mismatch")
    # The previously authorized diagnostic already ran and pinned the rejected
    # pre-correction request. It may never be reused for a corrected request.
    raise Gate5DiagnosticStop(RETIRED_STOP_REASON)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--execute-diagnostic-once", action="store_true")
    args = parser.parse_args()
    if args.verify_only == args.execute_diagnostic_once:
        parser.error("choose exactly one of --verify-only or --execute-diagnostic-once")
    if args.verify_only:
        print(json.dumps(verify_only(), sort_keys=True))
        return 0
    try:
        execute_once()
    except Gate5DiagnosticStop as exc:
        print(json.dumps({"disposition": "stopped", "stop_reason": exc.code}, sort_keys=True))
        return 2
    except Exception:
        print(json.dumps({"disposition": "stopped", "stop_reason": "unexpected_local_error"}, sort_keys=True))
        return 2
    raise AssertionError("retired diagnostic unexpectedly returned")


if __name__ == "__main__":
    raise SystemExit(main())
