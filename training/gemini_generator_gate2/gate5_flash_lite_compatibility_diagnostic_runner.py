"""Disabled-by-default one-request Flash-Lite compatibility diagnostic.

``--verify-only`` performs local checks without files, credentials, or network.
The execution mode remains blocked unless a fresh same-day attestation and all
frozen hashes validate. Johnny, not an AI collaborator, supplies the local
credential target and runs the command.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import gate2
import gate4_connectivity_runner as gate4
import gate5_additional_properties_diagnostic_runner as successful_flash
import gate5_flash_lite_compatibility_diagnostic_gate as execution_gate
import gate5_paid_pilot_runner as pilot_runner
import gate5_redesign as redesign

PACKAGE = Path(__file__).resolve().parent
PROPOSAL_PATH = PACKAGE / "gate5_flash_lite_compatibility_diagnostic_proposal.md"
CONTRACT_PATH = PACKAGE / "gate5_provider_contract_draft.json"
PROVIDER_SCHEMA_PATH = PACKAGE / "gate5_provider_response_schema.json"
SCHEDULE_PATH = PACKAGE / "schedule.json"
SUCCESS_RECEIPT_PATH = PACKAGE / "gate5_additional_properties_diagnostic_2026-08-15" / "additional_properties_diagnostic_receipt.json"

EXPECTED_PROPOSAL = execution_gate.EXPECTED["proposal_sha256"]
EXPECTED_CONTRACT = execution_gate.EXPECTED["provider_contract_sha256"]
EXPECTED_SCHEMA = execution_gate.EXPECTED["provider_schema_sha256"]
EXPECTED_BODY = execution_gate.EXPECTED["request_body_sha256"]
EXPECTED_REQUEST = execution_gate.EXPECTED["request_envelope_sha256"]
EXPECTED_SUCCESS_ROW = execution_gate.EXPECTED["successful_flash_receipt_row_sha256"]
EXPECTED_RATE = execution_gate.EXPECTED["execution_day_rate_snapshot_sha256"]
CAP = execution_gate.CAP
MAX_RESPONSE_BYTES = 1_024 * 1_024
MAX_ERROR_MESSAGE_CODEPOINTS = 4_096
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent"


class Gate5FlashLiteDiagnosticStop(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_hash(path: Path) -> str:
    try:
        return pilot_runner.canonical_hash(path)
    except pilot_runner.Gate5PilotStop as exc:
        raise Gate5FlashLiteDiagnosticStop("canonical_input_invalid") from exc


def frozen_request() -> dict[str, Any]:
    try:
        slots = gate2.load_json(SCHEDULE_PATH)["slots"]
        slot = slots[1]
        request = redesign.build_request(slot)
    except (gate2.Gate2Error, redesign.Gate5DraftError, KeyError, IndexError, TypeError) as exc:
        raise Gate5FlashLiteDiagnosticStop("frozen_request_unavailable") from exc
    if slot.get("slot") != 2 or slot.get("mechanism_id") != "M01" or slot.get("model") != "gemini-3.5-flash-lite":
        raise Gate5FlashLiteDiagnosticStop("frozen_request_drift")
    if request.get("endpoint") != ENDPOINT or request.get("timeout_seconds") != 60:
        raise Gate5FlashLiteDiagnosticStop("frozen_request_drift")
    body_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(request["body"]))
    request_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(request))
    if body_hash != EXPECTED_BODY or request_hash != EXPECTED_REQUEST:
        raise Gate5FlashLiteDiagnosticStop("frozen_request_drift")
    if _contains_key(request["body"], "additionalProperties"):
        raise Gate5FlashLiteDiagnosticStop("unsupported_provider_schema_field_present")
    return request


def _contains_key(value: Any, target: str) -> bool:
    if isinstance(value, dict):
        return target in value or any(_contains_key(item, target) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, target) for item in value)
    return False


def verify_successful_flash_evidence() -> str:
    try:
        receipt = gate2.load_json(SUCCESS_RECEIPT_PATH)
        successful_flash.verify_receipt(receipt)
    except (gate2.Gate2Error, successful_flash.Gate5AdditionalPropertiesDiagnosticStop, OSError) as exc:
        raise Gate5FlashLiteDiagnosticStop("successful_flash_evidence_invalid") from exc
    if receipt["row_hash"] != EXPECTED_SUCCESS_ROW or receipt["response"]["http_status"] != 200 or receipt["transport"]["request_hash"] != "8420c2d8360f4ffc96fb617dd8d4b081732cf2c87654a65d3ddc2ab8426297b4" or receipt["error_message_capture_state"] != "not_applicable_http_200" or receipt["non_200_provider_error_message"] is not None:
        raise Gate5FlashLiteDiagnosticStop("successful_flash_evidence_invalid")
    return receipt["row_hash"]


def load_rates(path: Path) -> tuple[dict[str, Any], int]:
    try:
        value = pilot_runner.load_execution_day_rates(path)
        reservation = gate2.reservation_cost("gemini-3.5-flash-lite", value)
    except (pilot_runner.Gate5PilotStop, gate2.Gate2Error) as exc:
        raise Gate5FlashLiteDiagnosticStop("execution_day_rate_snapshot_invalid") from exc
    if reservation > CAP:
        raise Gate5FlashLiteDiagnosticStop("diagnostic_cost_cap_exceeded")
    return value, reservation


def verify_only() -> dict[str, Any]:
    request = frozen_request()
    success_row = verify_successful_flash_evidence()
    proposal = canonical_hash(PROPOSAL_PATH)
    contract = canonical_hash(CONTRACT_PATH)
    schema = canonical_hash(PROVIDER_SCHEMA_PATH)
    rate = canonical_hash(PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-16.json")
    _, reservation = load_rates(PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-16.json")
    return {
        "artifact": "gemini_generator_gate5_flash_lite_compatibility_diagnostic_verify_only",
        "proposal_sha256": proposal,
        "proposal_matches_frozen": proposal == EXPECTED_PROPOSAL,
        "contract_sha256": contract,
        "contract_matches_frozen": contract == EXPECTED_CONTRACT,
        "provider_schema_sha256": schema,
        "provider_schema_matches_frozen": schema == EXPECTED_SCHEMA,
        "rate_snapshot_sha256": rate,
        "rate_snapshot_matches_frozen": rate == EXPECTED_RATE,
        "request_body_sha256": gate2.sha256_bytes(gate2.canonical_json_bytes(request["body"])),
        "request_envelope_sha256": gate2.sha256_bytes(gate2.canonical_json_bytes(request)),
        "successful_flash_receipt_row_sha256": success_row,
        "reservation_usd_millionths": reservation,
        "network_used": False,
        "credential_read": False,
        "file_output_created": False,
    }


def _new_file(path: Path, data: bytes) -> None:
    try:
        with path.open("xb") as handle:
            handle.write(data)
    except (FileExistsError, OSError) as exc:
        raise Gate5FlashLiteDiagnosticStop("output_path_unavailable") from exc


def prepare_output(root: Path, attestation_hash: str, rate_hash: str, reservation: int) -> dict[str, Path]:
    if root.exists():
        raise Gate5FlashLiteDiagnosticStop("output_directory_already_exists")
    try:
        root.mkdir(parents=False)
    except OSError as exc:
        raise Gate5FlashLiteDiagnosticStop("output_path_unavailable") from exc
    paths = {"reservation": root / "flash_lite_diagnostic_reservation.json", "receipt": root / "flash_lite_diagnostic_receipt.json"}
    row = {
        "artifact": "gemini_generator_gate5_flash_lite_compatibility_diagnostic_reservation",
        "created_utc": utc_now(),
        "proposal_sha256": EXPECTED_PROPOSAL,
        "contract_sha256": EXPECTED_CONTRACT,
        "provider_schema_sha256": EXPECTED_SCHEMA,
        "request_body_sha256": EXPECTED_BODY,
        "request_envelope_sha256": EXPECTED_REQUEST,
        "successful_flash_receipt_row_sha256": EXPECTED_SUCCESS_ROW,
        "rate_snapshot_sha256": rate_hash,
        "attestation_sha256": attestation_hash,
        "authorized_cap_usd_millionths": CAP,
        "pre_request_reservation_usd_millionths": reservation,
        "state": "reserved_before_credential_read",
    }
    row["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(row))
    _new_file(paths["reservation"], gate2.canonical_json_bytes(row))
    return paths


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Gate5FlashLiteDiagnosticStop("duplicate_json_key")
        value[key] = item
    return value


def capture_non_200_error_message(body: bytes) -> tuple[str, str | None]:
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return "withheld_invalid_utf8", None
    try:
        value = json.loads(text, object_pairs_hook=reject_duplicate_keys)
    except (json.JSONDecodeError, Gate5FlashLiteDiagnosticStop):
        return "withheld_invalid_json", None
    if not isinstance(value, dict) or not isinstance(value.get("error"), dict):
        return "withheld_invalid_shape", None
    message = value["error"].get("message")
    if not isinstance(message, str) or not message:
        return "withheld_invalid_shape", None
    if len(message) > MAX_ERROR_MESSAGE_CODEPOINTS:
        return "withheld_message_too_long", None
    if gate2.contains_secret({"provider_error_message": message}):
        return "withheld_secret_like", None
    return "captured", message


def _receipt(attestation_hash: str, rate_hash: str, reservation: int, provider_request_count: int, response_status: int | None, response_body: bytes | None, capture_state: str, message: str | None, disposition: str, stop_reason: str | None) -> dict[str, Any]:
    row = {
        "artifact": "gemini_generator_gate5_flash_lite_compatibility_diagnostic_receipt",
        "proposal_sha256": EXPECTED_PROPOSAL,
        "contract_sha256": EXPECTED_CONTRACT,
        "provider_schema_sha256": EXPECTED_SCHEMA,
        "rate_snapshot_sha256": rate_hash,
        "attestation_sha256": attestation_hash,
        "execution_timestamp_utc": utc_now(),
        "transport": {
            "method": "POST",
            "endpoint": ENDPOINT,
            "request_body_sha256": EXPECTED_BODY,
            "request_envelope_sha256": EXPECTED_REQUEST,
            "header_names": ["Content-Type", "x-goog-api-key"],
            "timeout_seconds": 60,
            "provider_request_count": provider_request_count,
            "redirects_disabled": True,
            "retries_disabled": True,
        },
        "response": {
            "http_status": response_status,
            "byte_count": len(response_body) if response_body is not None else None,
            "sha256": gate2.sha256_bytes(response_body) if response_body is not None else None,
        },
        "cost": {
            "authorized_cap_usd_millionths": CAP,
            "pre_request_reservation_usd_millionths": reservation,
            "actual_usd_millionths": reservation if provider_request_count == 1 else None,
            "reconciliation_state": "reserved_pending_billing" if provider_request_count == 1 else "not_requested",
        },
        "redaction_scan": {"key_like_value_found": False, "raw_error_persisted": False},
        "error_message_capture_state": capture_state,
        "non_200_provider_error_message": message,
        "disposition": disposition,
        "stop_reason": stop_reason,
    }
    if gate2.contains_secret(row):
        raise Gate5FlashLiteDiagnosticStop("secret_exposure")
    row["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(row))
    return row


def verify_receipt(receipt: dict[str, Any]) -> None:
    fields = {"artifact", "proposal_sha256", "contract_sha256", "provider_schema_sha256", "rate_snapshot_sha256", "attestation_sha256", "execution_timestamp_utc", "transport", "response", "cost", "redaction_scan", "error_message_capture_state", "non_200_provider_error_message", "disposition", "stop_reason", "row_hash"}
    if set(receipt) != fields or receipt["artifact"] != "gemini_generator_gate5_flash_lite_compatibility_diagnostic_receipt":
        raise Gate5FlashLiteDiagnosticStop("receipt_invalid")
    if receipt["proposal_sha256"] != EXPECTED_PROPOSAL or receipt["contract_sha256"] != EXPECTED_CONTRACT or receipt["provider_schema_sha256"] != EXPECTED_SCHEMA or receipt["rate_snapshot_sha256"] != EXPECTED_RATE or not gate2.HEX64_RE.fullmatch(str(receipt["attestation_sha256"])):
        raise Gate5FlashLiteDiagnosticStop("receipt_invalid")
    payload = {key: value for key, value in receipt.items() if key != "row_hash"}
    if receipt["row_hash"] != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)) or gate2.contains_secret(receipt):
        raise Gate5FlashLiteDiagnosticStop("receipt_invalid")
    transport = receipt["transport"]
    if not isinstance(transport, dict):
        raise Gate5FlashLiteDiagnosticStop("receipt_invalid")
    count = transport.get("provider_request_count")
    expected_transport = {"method": "POST", "endpoint": ENDPOINT, "request_body_sha256": EXPECTED_BODY, "request_envelope_sha256": EXPECTED_REQUEST, "header_names": ["Content-Type", "x-goog-api-key"], "timeout_seconds": 60, "provider_request_count": count, "redirects_disabled": True, "retries_disabled": True}
    if transport != expected_transport or count not in {0, 1}:
        raise Gate5FlashLiteDiagnosticStop("receipt_invalid")
    response = receipt["response"]
    if set(response) != {"http_status", "byte_count", "sha256"}:
        raise Gate5FlashLiteDiagnosticStop("receipt_invalid")
    if response["http_status"] is None:
        if response["byte_count"] is not None or response["sha256"] is not None:
            raise Gate5FlashLiteDiagnosticStop("receipt_invalid")
    elif type(response["http_status"]) is not int or not 100 <= response["http_status"] <= 599 or type(response["byte_count"]) is not int or not 0 <= response["byte_count"] <= MAX_RESPONSE_BYTES or not isinstance(response["sha256"], str) or not gate2.HEX64_RE.fullmatch(response["sha256"]):
        raise Gate5FlashLiteDiagnosticStop("receipt_invalid")
    cost = receipt["cost"]
    if set(cost) != {"authorized_cap_usd_millionths", "pre_request_reservation_usd_millionths", "actual_usd_millionths", "reconciliation_state"} or cost["authorized_cap_usd_millionths"] != CAP or type(cost["pre_request_reservation_usd_millionths"]) is not int or not 0 <= cost["pre_request_reservation_usd_millionths"] <= CAP:
        raise Gate5FlashLiteDiagnosticStop("receipt_invalid")
    if count == 0 and (cost["actual_usd_millionths"] is not None or cost["reconciliation_state"] != "not_requested" or response["http_status"] is not None):
        raise Gate5FlashLiteDiagnosticStop("receipt_invalid")
    if count == 1 and (cost["actual_usd_millionths"] != cost["pre_request_reservation_usd_millionths"] or cost["reconciliation_state"] != "reserved_pending_billing"):
        raise Gate5FlashLiteDiagnosticStop("receipt_invalid")
    if receipt["redaction_scan"] != {"key_like_value_found": False, "raw_error_persisted": False}:
        raise Gate5FlashLiteDiagnosticStop("receipt_invalid")
    status, state, message = response["http_status"], receipt["error_message_capture_state"], receipt["non_200_provider_error_message"]
    if status == 200:
        valid = state == "not_applicable_http_200" and message is None and receipt["disposition"] == "passed" and receipt["stop_reason"] is None
    elif status is not None:
        valid = state in {"captured", "withheld_invalid_utf8", "withheld_invalid_json", "withheld_invalid_shape", "withheld_message_too_long", "withheld_secret_like"} and receipt["disposition"] == "stopped" and receipt["stop_reason"] == "unexpected_http_status"
        if state == "captured":
            valid = valid and isinstance(message, str) and 0 < len(message) <= MAX_ERROR_MESSAGE_CODEPOINTS and not gate2.contains_secret({"provider_error_message": message})
        else:
            valid = valid and message is None
    else:
        expected_reasons = {"credential_unavailable"} if count == 0 else {"transport_or_response_invalid", "unexpected_local_error"}
        valid = state == "not_available_without_response" and message is None and receipt["disposition"] == "stopped" and receipt["stop_reason"] in expected_reasons
    if not valid:
        raise Gate5FlashLiteDiagnosticStop("receipt_invalid")


def execute_once(credential_loader: Callable[[str], str], credential_target: str, transport: Any, attestation_path: Path, rate_snapshot_path: Path, output_directory: Path) -> dict[str, Any]:
    try:
        attestation = execution_gate.validate_attestation(attestation_path)
        request = frozen_request()
        proposal_hash = canonical_hash(PROPOSAL_PATH)
        contract_hash = canonical_hash(CONTRACT_PATH)
        schema_hash = canonical_hash(PROVIDER_SCHEMA_PATH)
        rate_hash = canonical_hash(rate_snapshot_path)
        success_row = verify_successful_flash_evidence()
        _, reservation = load_rates(rate_snapshot_path)
        attestation_hash = canonical_hash(attestation_path)
        if proposal_hash != EXPECTED_PROPOSAL or contract_hash != EXPECTED_CONTRACT or schema_hash != EXPECTED_SCHEMA or rate_hash != EXPECTED_RATE or success_row != EXPECTED_SUCCESS_ROW:
            raise Gate5FlashLiteDiagnosticStop("frozen_artifact_hash_mismatch")
        if any(attestation[name] != value for name, value in execution_gate.EXPECTED.items()):
            raise Gate5FlashLiteDiagnosticStop("attestation_artifact_hash_mismatch")
        paths = prepare_output(output_directory, attestation_hash, rate_hash, reservation)
    except (execution_gate.Gate5FlashLiteDiagnosticAttestationError, gate2.Gate2Error, redesign.Gate5DraftError, pilot_runner.Gate5PilotStop) as exc:
        raise Gate5FlashLiteDiagnosticStop("pre_execution_validation_failed") from exc

    provider_request_count = 0
    response_status: int | None = None
    response_body: bytes | None = None
    capture_state = "not_available_without_response"
    message = None
    disposition = "stopped"
    stop_reason: str | None = None
    secret: str | None = None
    try:
        try:
            secret = credential_loader(credential_target)
            if not isinstance(secret, str) or not secret or any(character in secret for character in "\r\n\x00"):
                raise Gate5FlashLiteDiagnosticStop("credential_unavailable")
        except Exception:
            stop_reason = "credential_unavailable"
        if stop_reason is None:
            try:
                body = gate2.canonical_json_bytes(request["body"])
                provider_request_count = 1
                response = transport.post(request["endpoint"], body, {"Content-Type": "application/json", "x-goog-api-key": secret}, request["timeout_seconds"])
                response = pilot_runner.validate_provider_response(response)
                response_status = response.status
                response_body = response.body
                if response.status == 200:
                    capture_state = "not_applicable_http_200"
                    disposition = "passed"
                else:
                    capture_state, message = capture_non_200_error_message(response.body)
                    stop_reason = "unexpected_http_status"
            except Exception:
                if response_status is None:
                    stop_reason = "transport_or_response_invalid"
                else:
                    stop_reason = "unexpected_local_error"
        receipt = _receipt(attestation_hash, rate_hash, reservation, provider_request_count, response_status, response_body, capture_state, message, disposition, stop_reason)
        verify_receipt(receipt)
        _new_file(paths["receipt"], gate2.canonical_json_bytes(receipt))
        return receipt
    finally:
        secret = None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--execute-flash-lite-diagnostic-once", action="store_true")
    parser.add_argument("--credential-target")
    parser.add_argument("--attestation", type=Path)
    parser.add_argument("--rate-snapshot", type=Path)
    parser.add_argument("--output-directory", type=Path)
    args = parser.parse_args()
    if args.verify_only == args.execute_flash_lite_diagnostic_once:
        parser.error("choose exactly one mode")
    if args.verify_only:
        print(json.dumps(verify_only(), sort_keys=True))
        return 0
    if not all((args.credential_target, args.attestation, args.rate_snapshot, args.output_directory)):
        parser.error("execution requires credential target, attestation, rate snapshot, and output directory")
    try:
        receipt = execute_once(gate4.load_windows_generic_credential, args.credential_target, pilot_runner.HTTPSPilotTransport(), args.attestation, args.rate_snapshot, args.output_directory)
    except Gate5FlashLiteDiagnosticStop as exc:
        print(json.dumps({"disposition": "stopped", "stop_reason": exc.code}, sort_keys=True))
        return 2
    except Exception:
        print(json.dumps({"disposition": "stopped", "stop_reason": "unexpected_local_error"}, sort_keys=True))
        return 2
    print(json.dumps({"disposition": receipt["disposition"], "http_status": receipt["response"]["http_status"], "receipt": str(args.output_directory / "flash_lite_diagnostic_receipt.json")}, sort_keys=True))
    return 0 if receipt["disposition"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
