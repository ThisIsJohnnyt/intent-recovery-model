"""Retired provider-schema-type diagnostic receipt verifier.

The one authorized diagnostic ran. Its request is superseded by the confirmed
removal of unsupported provider `additionalProperties`; this module has no
credential or network code and preserves historical receipt verification only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import gate2

PACKAGE = Path(__file__).resolve().parent
PROPOSAL = PACKAGE / "gate5_provider_schema_type_diagnostic_proposal.md"
EXPECTED_PROPOSAL = "a2a3300889e5d1cea53223d2ca56308d88cf23091438071336f1009d8f0dc3e2"
EXPECTED_CONTRACT = "fecaa69bbea4a0e16749e7537b0ab1720cd6d386a19cd4736cfb436bcb11f96d"
EXPECTED_SCHEMA = "f42d19f841aa95949ce075cd0ec80c63f1a930fbb023c5f3eb4543d5cdc376c9"
EXPECTED_REQUEST = "ab9757d003cf09dd06ecf55b435c10bd676932d92f7989417baa6d17f4f29379"
CAP = 10_680
MAX_RESPONSE_BYTES = 1_024 * 1_024
RETIRED_STOP_REASON = "provider_schema_diagnostic_superseded_by_additional_properties_correction"


class Gate5ProviderSchemaDiagnosticStop(RuntimeError):
    def __init__(self, code: str): self.code = code; super().__init__(code)


def proposal_hash() -> str:
    try: return gate2.sha256_bytes(gate2.canonical_file(PROPOSAL)[0])
    except (gate2.Gate2Error, OSError) as exc: raise Gate5ProviderSchemaDiagnosticStop("diagnostic_proposal_unavailable") from exc


def verify_only() -> dict[str, Any]:
    digest = proposal_hash()
    return {"artifact": "gemini_generator_gate5_provider_schema_diagnostic_verify_only", "proposal_sha256": digest, "proposal_matches_frozen": digest == EXPECTED_PROPOSAL, "historical_request_hash": EXPECTED_REQUEST, "diagnostic_retired": True, "stop_reason": RETIRED_STOP_REASON, "network_used": False, "credential_read": False, "file_output_created": False}


def verify_receipt(receipt: dict[str, Any]) -> None:
    required = {"artifact", "proposal_sha256", "contract_sha256", "provider_schema_sha256", "attestation_sha256", "execution_timestamp_utc", "transport", "response", "cost", "redaction_scan", "disposition", "stop_reason", "row_hash"}
    if set(receipt) != required or receipt["artifact"] != "gemini_generator_gate5_provider_schema_diagnostic_receipt" or receipt["proposal_sha256"] != EXPECTED_PROPOSAL or receipt["contract_sha256"] != EXPECTED_CONTRACT or receipt["provider_schema_sha256"] != EXPECTED_SCHEMA: raise Gate5ProviderSchemaDiagnosticStop("receipt_invalid")
    payload = {key: value for key, value in receipt.items() if key != "row_hash"}
    if receipt["row_hash"] != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)) or gate2.contains_secret(receipt): raise Gate5ProviderSchemaDiagnosticStop("receipt_invalid")
    transport = receipt["transport"]
    if transport != {"method": "POST", "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent", "request_hash": EXPECTED_REQUEST, "header_names": ["Content-Type", "x-goog-api-key"], "timeout_seconds": 60, "provider_request_count": 1, "redirects_disabled": True, "retries_disabled": True}: raise Gate5ProviderSchemaDiagnosticStop("receipt_invalid")
    response = receipt["response"]
    if set(response) != {"http_status", "byte_count", "sha256"} or type(response["http_status"]) is not int or not 100 <= response["http_status"] <= 599 or type(response["byte_count"]) is not int or not 0 <= response["byte_count"] <= MAX_RESPONSE_BYTES or not isinstance(response["sha256"], str) or not gate2.HEX64_RE.fullmatch(response["sha256"]): raise Gate5ProviderSchemaDiagnosticStop("receipt_invalid")
    if receipt["cost"] != {"authorized_cap_usd_millionths": CAP, "pre_request_reservation_usd_millionths": CAP, "actual_usd_millionths": CAP, "reconciliation_state": "reserved_pending_billing"} or receipt["redaction_scan"] != {"key_like_value_found": False, "raw_error_persisted": False}: raise Gate5ProviderSchemaDiagnosticStop("receipt_invalid")


def execute_once(*_args: Any, **_kwargs: Any) -> None:
    raise Gate5ProviderSchemaDiagnosticStop(RETIRED_STOP_REASON)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--verify-only", action="store_true"); parser.add_argument("--execute-provider-schema-diagnostic-once", action="store_true"); args = parser.parse_args()
    if args.verify_only == args.execute_provider_schema_diagnostic_once: parser.error("choose exactly one mode")
    if args.verify_only: print(json.dumps(verify_only(), sort_keys=True)); return 0
    try: execute_once()
    except Gate5ProviderSchemaDiagnosticStop as exc: print(json.dumps({"disposition": "stopped", "stop_reason": exc.code}, sort_keys=True)); return 2
    raise AssertionError("retired diagnostic unexpectedly returned")


if __name__ == "__main__": raise SystemExit(main())
