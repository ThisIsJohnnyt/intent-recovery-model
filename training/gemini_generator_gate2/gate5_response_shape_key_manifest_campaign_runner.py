"""Disabled-by-default bounded manual key-manifest campaign runner."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import gate2
import gate4_connectivity_runner as gate4
import gate5_flash_lite_compatibility_diagnostic_runner as bounded_error
import gate5_key_manifest_capture as manifest_capture
import gate5_paid_pilot_runner as pilot_runner
import gate5_redesign as redesign
import gate5_response_shape_key_manifest_campaign_gate as execution_gate
import gate5_response_shape_key_manifest_diagnostic_runner as first_consumed
import gate5_response_shape_key_manifest_retry_runner as second_consumed

PACKAGE = Path(__file__).resolve().parent
PROPOSAL_PATH = PACKAGE / "gate5_response_shape_key_manifest_campaign_proposal.md"
CONTRACT_PATH = PACKAGE / "gate5_provider_contract_draft.json"
SCHEMA_PATH = PACKAGE / "gate5_provider_response_schema.json"
SCHEDULE_PATH = PACKAGE / "schedule.json"
RATE_PATH = PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-16.json"
EXPECTED = execution_gate.EXPECTED
PER_ATTEMPT_CAP = execution_gate.PER_ATTEMPT_CAP
MAX_ATTEMPTS = execution_gate.MAX_ATTEMPTS
AGGREGATE_CAP = execution_gate.AGGREGATE_CAP
MAX_RESPONSE_BYTES = 1_024 * 1_024
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent"
LEDGER_NAME = "campaign_state.jsonl"
STATE_FIELDS = {
    "artifact", "event", "sequence", "attempts_reserved", "provider_requests",
    "cumulative_reserved_usd_millionths", "cumulative_booked_usd_millionths", "campaign_state",
    "attempt_lock_file_sha256", "receipt_file_sha256", "http_status", "previous_row_hash",
    "campaign_proposal_sha256", "attestation_sha256", "request_envelope_sha256",
    "execution_day_rate_snapshot_sha256", "maximum_provider_requests",
    "per_attempt_cap_usd_millionths", "aggregate_cap_usd_millionths", "row_hash",
}
TERMINAL_STATES = {"stopped_on_non_503", "attempt_cap_reached", "stopped_local_or_transport_failure"}


class Gate5KeyManifestCampaignStop(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_hash(path: Path) -> str:
    try:
        return pilot_runner.canonical_hash(path)
    except pilot_runner.Gate5PilotStop as exc:
        raise Gate5KeyManifestCampaignStop("canonical_input_invalid") from exc


def _new_file(path: Path, data: bytes) -> None:
    try:
        with path.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except (FileExistsError, OSError) as exc:
        raise Gate5KeyManifestCampaignStop("exclusive_output_unavailable") from exc


def _append_line(path: Path, row: dict[str, Any]) -> None:
    try:
        with path.open("ab") as handle:
            handle.write(gate2.canonical_json_bytes(row))
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise Gate5KeyManifestCampaignStop("campaign_state_append_failed") from exc


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line, object_pairs_hook=manifest_capture.reject_duplicate_keys) for line in lines if line]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, manifest_capture.KeyManifestError) as exc:
        raise Gate5KeyManifestCampaignStop("campaign_state_invalid") from exc


def verify_historical_evidence() -> dict[str, str]:
    try:
        first = first_consumed.verify_only()
        second = second_consumed.verify_only()
        first_receipt = gate2.load_json(first_consumed.RECEIPT_PATH)
        second_receipt = gate2.load_json(second_consumed.RECEIPT_PATH)
        first_consumed.verify_receipt(first_receipt)
        second_consumed.verify_receipt(second_receipt)
    except (first_consumed.Gate5KeyManifestStop, second_consumed.Gate5KeyManifestRetryStop, gate2.Gate2Error, OSError) as exc:
        raise Gate5KeyManifestCampaignStop("historical_evidence_invalid") from exc
    if not first["diagnostic_retired"] or not second["diagnostic_retired"] or first["historical_http_status"] != 503 or second["historical_http_status"] != 503:
        raise Gate5KeyManifestCampaignStop("historical_evidence_invalid")
    checks = {
        "campaign_proposal_sha256": canonical_hash(PROPOSAL_PATH),
        "first_receipt_file_sha256": canonical_hash(first_consumed.RECEIPT_PATH),
        "first_receipt_row_sha256": first_receipt["row_hash"],
        "first_attempt_lock_file_sha256": canonical_hash(first_consumed.ATTEMPT_LOCK_PATH),
        "first_attestation_sha256": canonical_hash(first_consumed.ATTESTATION_PATH),
        "second_receipt_file_sha256": canonical_hash(second_consumed.RECEIPT_PATH),
        "second_receipt_row_sha256": second_receipt["row_hash"],
        "second_reservation_file_sha256": canonical_hash(second_consumed.RESERVATION_PATH),
        "second_attempt_lock_file_sha256": canonical_hash(second_consumed.ATTEMPT_LOCK_PATH),
        "second_attestation_sha256": canonical_hash(second_consumed.ATTESTATION_PATH),
        "consumed_raw_response_sha256": first_receipt["response"]["sha256"],
        "provider_contract_sha256": canonical_hash(CONTRACT_PATH),
        "provider_schema_sha256": canonical_hash(SCHEMA_PATH),
        "execution_day_rate_snapshot_sha256": canonical_hash(RATE_PATH),
    }
    if first_receipt["response"]["sha256"] != second_receipt["response"]["sha256"] or checks != {key: EXPECTED[key] for key in checks}:
        raise Gate5KeyManifestCampaignStop("historical_evidence_invalid")
    return checks


def frozen_request() -> dict[str, Any]:
    try:
        slot = gate2.load_json(SCHEDULE_PATH)["slots"][0]
        request = redesign.build_request(slot)
    except (gate2.Gate2Error, redesign.Gate5DraftError, KeyError, IndexError, TypeError) as exc:
        raise Gate5KeyManifestCampaignStop("frozen_request_unavailable") from exc
    digest = gate2.sha256_bytes(gate2.canonical_json_bytes(request))
    if slot.get("slot") != 1 or slot.get("mechanism_id") != "M01" or slot.get("model") != "gemini-3.7-flash" or request.get("endpoint") != ENDPOINT or request.get("timeout_seconds") != 60 or digest != EXPECTED["request_envelope_sha256"]:
        raise Gate5KeyManifestCampaignStop("frozen_request_drift")
    return request


def load_rates(path: Path) -> int:
    try:
        rates = pilot_runner.load_execution_day_rates(path)
        reservation = gate2.reservation_cost("gemini-3.7-flash", rates)
    except (pilot_runner.Gate5PilotStop, gate2.Gate2Error) as exc:
        raise Gate5KeyManifestCampaignStop("execution_day_rate_snapshot_invalid") from exc
    if reservation != PER_ATTEMPT_CAP:
        raise Gate5KeyManifestCampaignStop("campaign_cost_cap_mismatch")
    return reservation


def verify_only() -> dict[str, Any]:
    evidence = verify_historical_evidence()
    request = frozen_request()
    request_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(request))
    if request_hash != EXPECTED["request_envelope_sha256"]:
        raise Gate5KeyManifestCampaignStop("frozen_request_drift")
    return {
        "artifact": "gemini_generator_gate5_response_shape_key_manifest_campaign_verify_only",
        "all_frozen_hashes_match": True,
        "evidence_count": len(evidence) + 1,
        "request_envelope_sha256": request_hash,
        "per_attempt_cap_usd_millionths": load_rates(RATE_PATH),
        "maximum_provider_requests": MAX_ATTEMPTS,
        "aggregate_cap_usd_millionths": AGGREGATE_CAP,
        "network_used": False,
        "credential_read": False,
        "file_output_created": False,
    }


def _state_row(
    event: str,
    sequence: int,
    attempts_reserved: int,
    provider_requests: int,
    cumulative_reserved: int,
    cumulative_booked: int,
    state: str,
    lock_hash: str | None,
    receipt_hash: str | None,
    status: int | None,
    previous_hash: str | None,
    attestation_hash: str,
) -> dict[str, Any]:
    row = {
        "artifact": "gemini_generator_gate5_response_shape_key_manifest_campaign_state",
        "event": event,
        "sequence": sequence,
        "attempts_reserved": attempts_reserved,
        "provider_requests": provider_requests,
        "cumulative_reserved_usd_millionths": cumulative_reserved,
        "cumulative_booked_usd_millionths": cumulative_booked,
        "campaign_state": state,
        "attempt_lock_file_sha256": lock_hash,
        "receipt_file_sha256": receipt_hash,
        "http_status": status,
        "previous_row_hash": previous_hash,
        "campaign_proposal_sha256": EXPECTED["campaign_proposal_sha256"],
        "attestation_sha256": attestation_hash,
        "request_envelope_sha256": EXPECTED["request_envelope_sha256"],
        "execution_day_rate_snapshot_sha256": EXPECTED["execution_day_rate_snapshot_sha256"],
        "maximum_provider_requests": MAX_ATTEMPTS,
        "per_attempt_cap_usd_millionths": PER_ATTEMPT_CAP,
        "aggregate_cap_usd_millionths": AGGREGATE_CAP,
    }
    row["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(row))
    return row


def _lock_path(root: Path, sequence: int) -> Path:
    return root / f"attempt_{sequence:03d}_lock.json"


def _receipt_path(root: Path, sequence: int) -> Path:
    return root / f"attempt_{sequence:03d}_receipt.json"


def _verify_lock(lock: Any, sequence: int, previous_hash: str, attestation_hash: str) -> None:
    fields = {"artifact", "sequence", "created_utc", "previous_state_row_hash", "campaign_proposal_sha256", "attestation_sha256", "request_envelope_sha256", "pre_request_cumulative_reservation_usd_millionths", "state", "row_hash"}
    if not isinstance(lock, dict) or set(lock) != fields:
        raise Gate5KeyManifestCampaignStop("campaign_attempt_lock_invalid")
    payload = {key: value for key, value in lock.items() if key != "row_hash"}
    if lock["row_hash"] != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)) or gate2.contains_secret(lock):
        raise Gate5KeyManifestCampaignStop("campaign_attempt_lock_invalid")
    if lock["artifact"] != "gemini_generator_gate5_response_shape_key_manifest_campaign_attempt_lock" or lock["sequence"] != sequence or lock["previous_state_row_hash"] != previous_hash or lock["campaign_proposal_sha256"] != EXPECTED["campaign_proposal_sha256"] or lock["attestation_sha256"] != attestation_hash or lock["request_envelope_sha256"] != EXPECTED["request_envelope_sha256"] or lock["pre_request_cumulative_reservation_usd_millionths"] != sequence * PER_ATTEMPT_CAP or lock["state"] != "attempt_reserved_before_credential_read":
        raise Gate5KeyManifestCampaignStop("campaign_attempt_lock_invalid")


def _receipt(
    attestation_hash: str,
    sequence: int,
    previous_state_hash: str,
    lock_file_hash: str,
    count: int,
    status: int | None,
    body: bytes | None,
    manifest_state: str,
    manifest: dict[str, Any] | None,
    error_state: str,
    message: str | None,
    disposition: str,
    stop_reason: str | None,
    campaign_state_after: str,
) -> dict[str, Any]:
    row = {
        "artifact": "gemini_generator_gate5_response_shape_key_manifest_campaign_receipt",
        "campaign_proposal_sha256": EXPECTED["campaign_proposal_sha256"],
        "attestation_sha256": attestation_hash,
        "attempt_number": sequence,
        "previous_state_row_hash": previous_state_hash,
        "attempt_lock_file_sha256": lock_file_hash,
        "execution_timestamp_utc": utc_now(),
        "transport": {"method": "POST", "endpoint": ENDPOINT, "request_envelope_sha256": EXPECTED["request_envelope_sha256"], "header_names": ["Content-Type", "x-goog-api-key"], "timeout_seconds": 60, "provider_request_count": count, "redirects_disabled": True, "retries_disabled": True},
        "response": {"http_status": status, "byte_count": len(body) if body is not None else None, "sha256": gate2.sha256_bytes(body) if body is not None else None},
        "cost": {"per_attempt_cap_usd_millionths": PER_ATTEMPT_CAP, "actual_usd_millionths": PER_ATTEMPT_CAP if count else None, "reconciliation_state": "reserved_pending_billing" if count else "not_requested"},
        "key_manifest_capture_state": manifest_state,
        "key_manifest": manifest,
        "non_200_error_capture_state": error_state,
        "non_200_provider_error_message": message,
        "redaction_scan": {"key_like_value_found": False, "raw_response_persisted": False, "response_value_persisted": False},
        "disposition": disposition,
        "stop_reason": stop_reason,
        "campaign_state_after": campaign_state_after,
    }
    if gate2.contains_secret(row):
        raise Gate5KeyManifestCampaignStop("secret_exposure")
    row["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(row))
    return row


def verify_receipt(receipt: dict[str, Any]) -> None:
    fields = {"artifact", "campaign_proposal_sha256", "attestation_sha256", "attempt_number", "previous_state_row_hash", "attempt_lock_file_sha256", "execution_timestamp_utc", "transport", "response", "cost", "key_manifest_capture_state", "key_manifest", "non_200_error_capture_state", "non_200_provider_error_message", "redaction_scan", "disposition", "stop_reason", "campaign_state_after", "row_hash"}
    if not isinstance(receipt, dict) or set(receipt) != fields or receipt["artifact"] != "gemini_generator_gate5_response_shape_key_manifest_campaign_receipt" or receipt["campaign_proposal_sha256"] != EXPECTED["campaign_proposal_sha256"] or not gate2.HEX64_RE.fullmatch(str(receipt["attestation_sha256"])) or type(receipt["attempt_number"]) is not int or not 1 <= receipt["attempt_number"] <= MAX_ATTEMPTS or not gate2.HEX64_RE.fullmatch(str(receipt["previous_state_row_hash"])) or not gate2.HEX64_RE.fullmatch(str(receipt["attempt_lock_file_sha256"])):
        raise Gate5KeyManifestCampaignStop("campaign_receipt_invalid")
    payload = {key: value for key, value in receipt.items() if key != "row_hash"}
    if receipt["row_hash"] != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)) or gate2.contains_secret(receipt):
        raise Gate5KeyManifestCampaignStop("campaign_receipt_invalid")
    transport = receipt["transport"]
    count = transport.get("provider_request_count") if isinstance(transport, dict) else None
    expected_transport = {"method": "POST", "endpoint": ENDPOINT, "request_envelope_sha256": EXPECTED["request_envelope_sha256"], "header_names": ["Content-Type", "x-goog-api-key"], "timeout_seconds": 60, "provider_request_count": count, "redirects_disabled": True, "retries_disabled": True}
    if transport != expected_transport or count not in {0, 1}:
        raise Gate5KeyManifestCampaignStop("campaign_receipt_invalid")
    response = receipt["response"]
    status = response.get("http_status") if isinstance(response, dict) else None
    if not isinstance(response, dict) or set(response) != {"http_status", "byte_count", "sha256"}:
        raise Gate5KeyManifestCampaignStop("campaign_receipt_invalid")
    if status is None:
        if response["byte_count"] is not None or response["sha256"] is not None:
            raise Gate5KeyManifestCampaignStop("campaign_receipt_invalid")
    elif type(status) is not int or not 100 <= status <= 599 or type(response["byte_count"]) is not int or not 0 <= response["byte_count"] <= MAX_RESPONSE_BYTES or not gate2.HEX64_RE.fullmatch(str(response["sha256"])):
        raise Gate5KeyManifestCampaignStop("campaign_receipt_invalid")
    cost = receipt["cost"]
    if not isinstance(cost, dict) or set(cost) != {"per_attempt_cap_usd_millionths", "actual_usd_millionths", "reconciliation_state"} or cost["per_attempt_cap_usd_millionths"] != PER_ATTEMPT_CAP:
        raise Gate5KeyManifestCampaignStop("campaign_receipt_invalid")
    if count == 0 and (cost["actual_usd_millionths"] is not None or cost["reconciliation_state"] != "not_requested") or count == 1 and (cost["actual_usd_millionths"] != PER_ATTEMPT_CAP or cost["reconciliation_state"] != "reserved_pending_billing"):
        raise Gate5KeyManifestCampaignStop("campaign_receipt_invalid")
    if receipt["redaction_scan"] != {"key_like_value_found": False, "raw_response_persisted": False, "response_value_persisted": False}:
        raise Gate5KeyManifestCampaignStop("campaign_receipt_invalid")
    ms, manifest = receipt["key_manifest_capture_state"], receipt["key_manifest"]
    es, message = receipt["non_200_error_capture_state"], receipt["non_200_provider_error_message"]
    if status == 200:
        valid = es == "not_applicable_http_200" and message is None and receipt["campaign_state_after"] == "stopped_on_non_503"
        if ms == "captured":
            try:
                manifest_capture.validate_manifest(manifest)
            except manifest_capture.KeyManifestError:
                valid = False
            valid = valid and receipt["disposition"] == "passed" and receipt["stop_reason"] == "campaign_terminal_http_200"
        else:
            valid = valid and manifest is None and ms in {"withheld_invalid_utf8", "withheld_invalid_json", "withheld_shape_or_count_invalid", "withheld_key_boundary_invalid"} and receipt["disposition"] == "stopped" and receipt["stop_reason"] == "manifest_capture_failed"
    elif status is not None:
        valid = ms == "not_applicable_non_200" and manifest is None and es in {"captured", "withheld_invalid_utf8", "withheld_invalid_json", "withheld_invalid_shape", "withheld_message_too_long", "withheld_secret_like"}
        valid = valid and ((es == "captured" and isinstance(message, str) and 0 < len(message) <= bounded_error.MAX_ERROR_MESSAGE_CODEPOINTS and not gate2.contains_secret({"provider_error_message": message})) or (es != "captured" and message is None))
        if status == 503:
            expected_state = "attempt_cap_reached" if receipt["attempt_number"] == MAX_ATTEMPTS else "active_after_503"
            expected_disposition = "stopped" if expected_state == "attempt_cap_reached" else "continue_after_503"
            expected_reason = "attempt_cap_reached" if expected_state == "attempt_cap_reached" else "transient_http_503"
            valid = valid and receipt["campaign_state_after"] == expected_state and receipt["disposition"] == expected_disposition and receipt["stop_reason"] == expected_reason
        else:
            valid = valid and receipt["campaign_state_after"] == "stopped_on_non_503" and receipt["disposition"] == "stopped" and receipt["stop_reason"] == "unexpected_http_status"
    else:
        valid = ms == es == "not_available_without_response" and manifest is message is None and receipt["campaign_state_after"] == "stopped_local_or_transport_failure" and receipt["disposition"] == "stopped" and receipt["stop_reason"] in ({"credential_unavailable"} if count == 0 else {"transport_or_response_invalid", "unexpected_local_error"})
    if not valid:
        raise Gate5KeyManifestCampaignStop("campaign_receipt_invalid")


def _validate_row_hash(row: Any, previous_hash: str | None) -> None:
    if not isinstance(row, dict) or set(row) != STATE_FIELDS or row["artifact"] != "gemini_generator_gate5_response_shape_key_manifest_campaign_state" or row["previous_row_hash"] != previous_hash:
        raise Gate5KeyManifestCampaignStop("campaign_state_invalid")
    payload = {key: value for key, value in row.items() if key != "row_hash"}
    if row["row_hash"] != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)) or gate2.contains_secret(row):
        raise Gate5KeyManifestCampaignStop("campaign_state_invalid")
    if row["campaign_proposal_sha256"] != EXPECTED["campaign_proposal_sha256"] or row["request_envelope_sha256"] != EXPECTED["request_envelope_sha256"] or row["execution_day_rate_snapshot_sha256"] != EXPECTED["execution_day_rate_snapshot_sha256"] or row["maximum_provider_requests"] != MAX_ATTEMPTS or row["per_attempt_cap_usd_millionths"] != PER_ATTEMPT_CAP or row["aggregate_cap_usd_millionths"] != AGGREGATE_CAP:
        raise Gate5KeyManifestCampaignStop("campaign_state_invalid")


def load_and_verify_campaign(root: Path, attestation_hash: str) -> list[dict[str, Any]]:
    rows = _read_jsonl(root / LEDGER_NAME)
    if not rows:
        raise Gate5KeyManifestCampaignStop("campaign_state_invalid")
    previous_hash: str | None = None
    previous: dict[str, Any] | None = None
    for index, row in enumerate(rows):
        _validate_row_hash(row, previous_hash)
        if row["attestation_sha256"] != attestation_hash:
            raise Gate5KeyManifestCampaignStop("campaign_state_invalid")
        if index == 0:
            if row["event"] != "campaign_authorized" or row["sequence"] != 0 or row["attempts_reserved"] != 0 or row["provider_requests"] != 0 or row["cumulative_reserved_usd_millionths"] != 0 or row["cumulative_booked_usd_millionths"] != 0 or row["campaign_state"] != "authorized_not_started" or row["attempt_lock_file_sha256"] is not None or row["receipt_file_sha256"] is not None or row["http_status"] is not None:
                raise Gate5KeyManifestCampaignStop("campaign_state_invalid")
        elif row["event"] == "attempt_reserved":
            assert previous is not None
            if previous["campaign_state"] not in {"authorized_not_started", "active_after_503"} or previous["event"] not in {"campaign_authorized", "attempt_completed"}:
                raise Gate5KeyManifestCampaignStop("campaign_state_invalid")
            sequence = previous["attempts_reserved"] + 1
            if row["sequence"] != sequence or row["attempts_reserved"] != sequence or row["provider_requests"] != previous["provider_requests"] or row["cumulative_reserved_usd_millionths"] != sequence * PER_ATTEMPT_CAP or row["cumulative_booked_usd_millionths"] != previous["cumulative_booked_usd_millionths"] or row["campaign_state"] != "attempt_reserved" or not gate2.HEX64_RE.fullmatch(str(row["attempt_lock_file_sha256"])) or row["receipt_file_sha256"] is not None or row["http_status"] is not None or sequence > MAX_ATTEMPTS:
                raise Gate5KeyManifestCampaignStop("campaign_state_invalid")
            lock_path = _lock_path(root, sequence)
            if canonical_hash(lock_path) != row["attempt_lock_file_sha256"]:
                raise Gate5KeyManifestCampaignStop("campaign_state_invalid")
            try:
                lock = gate2.load_json(lock_path)
            except (gate2.Gate2Error, OSError) as exc:
                raise Gate5KeyManifestCampaignStop("campaign_state_invalid") from exc
            _verify_lock(lock, sequence, previous["row_hash"], attestation_hash)
        elif row["event"] == "attempt_completed":
            assert previous is not None
            if previous["event"] != "attempt_reserved" or previous["campaign_state"] != "attempt_reserved" or row["sequence"] != previous["sequence"] or row["attempts_reserved"] != previous["attempts_reserved"] or row["cumulative_reserved_usd_millionths"] != previous["cumulative_reserved_usd_millionths"] or row["attempt_lock_file_sha256"] != previous["attempt_lock_file_sha256"] or not gate2.HEX64_RE.fullmatch(str(row["receipt_file_sha256"])):
                raise Gate5KeyManifestCampaignStop("campaign_state_invalid")
            receipt_path = _receipt_path(root, row["sequence"])
            if canonical_hash(receipt_path) != row["receipt_file_sha256"]:
                raise Gate5KeyManifestCampaignStop("campaign_state_invalid")
            try:
                receipt = gate2.load_json(receipt_path)
            except (gate2.Gate2Error, OSError) as exc:
                raise Gate5KeyManifestCampaignStop("campaign_state_invalid") from exc
            verify_receipt(receipt)
            count = receipt["transport"]["provider_request_count"]
            expected_requests = previous["provider_requests"] + count
            expected_booked = previous["cumulative_booked_usd_millionths"] + (PER_ATTEMPT_CAP if count else 0)
            if row["provider_requests"] != expected_requests or row["cumulative_booked_usd_millionths"] != expected_booked or row["http_status"] != receipt["response"]["http_status"] or row["campaign_state"] != receipt["campaign_state_after"] or receipt["attempt_number"] != row["sequence"] or receipt["previous_state_row_hash"] != previous["row_hash"] or receipt["attempt_lock_file_sha256"] != row["attempt_lock_file_sha256"]:
                raise Gate5KeyManifestCampaignStop("campaign_state_invalid")
            expected_state = "stopped_local_or_transport_failure" if row["http_status"] is None else ("attempt_cap_reached" if row["http_status"] == 503 and expected_requests == MAX_ATTEMPTS else ("active_after_503" if row["http_status"] == 503 else "stopped_on_non_503"))
            if row["campaign_state"] != expected_state:
                raise Gate5KeyManifestCampaignStop("campaign_state_invalid")
        else:
            raise Gate5KeyManifestCampaignStop("campaign_state_invalid")
        previous_hash = row["row_hash"]
        previous = row
    return rows


def initialize_campaign(root: Path, attestation_hash: str) -> None:
    try:
        root.mkdir(parents=False)
    except (FileExistsError, OSError) as exc:
        raise Gate5KeyManifestCampaignStop("campaign_directory_unavailable") from exc
    genesis = _state_row("campaign_authorized", 0, 0, 0, 0, 0, "authorized_not_started", None, None, None, None, attestation_hash)
    _new_file(root / LEDGER_NAME, gate2.canonical_json_bytes(genesis))


def reserve_attempt(root: Path, attestation_hash: str) -> tuple[int, dict[str, Any], str, Path]:
    rows = load_and_verify_campaign(root, attestation_hash)
    previous = rows[-1]
    if previous["campaign_state"] in TERMINAL_STATES:
        raise Gate5KeyManifestCampaignStop("campaign_already_terminal")
    if previous["campaign_state"] == "attempt_reserved":
        raise Gate5KeyManifestCampaignStop("campaign_incomplete_attempt")
    if previous["campaign_state"] not in {"authorized_not_started", "active_after_503"}:
        raise Gate5KeyManifestCampaignStop("campaign_state_invalid")
    sequence = previous["attempts_reserved"] + 1
    if sequence > MAX_ATTEMPTS or sequence * PER_ATTEMPT_CAP > AGGREGATE_CAP:
        raise Gate5KeyManifestCampaignStop("campaign_cap_reached")
    lock = {
        "artifact": "gemini_generator_gate5_response_shape_key_manifest_campaign_attempt_lock",
        "sequence": sequence,
        "created_utc": utc_now(),
        "previous_state_row_hash": previous["row_hash"],
        "campaign_proposal_sha256": EXPECTED["campaign_proposal_sha256"],
        "attestation_sha256": attestation_hash,
        "request_envelope_sha256": EXPECTED["request_envelope_sha256"],
        "pre_request_cumulative_reservation_usd_millionths": sequence * PER_ATTEMPT_CAP,
        "state": "attempt_reserved_before_credential_read",
    }
    lock["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(lock))
    lock_path = _lock_path(root, sequence)
    _new_file(lock_path, gate2.canonical_json_bytes(lock))
    lock_hash = canonical_hash(lock_path)
    reservation = _state_row("attempt_reserved", sequence, sequence, previous["provider_requests"], sequence * PER_ATTEMPT_CAP, previous["cumulative_booked_usd_millionths"], "attempt_reserved", lock_hash, None, None, previous["row_hash"], attestation_hash)
    _append_line(root / LEDGER_NAME, reservation)
    return sequence, reservation, lock_hash, _receipt_path(root, sequence)


def complete_attempt(root: Path, reservation: dict[str, Any], receipt: dict[str, Any], receipt_path: Path) -> dict[str, Any]:
    verify_receipt(receipt)
    _new_file(receipt_path, gate2.canonical_json_bytes(receipt))
    receipt_hash = canonical_hash(receipt_path)
    count = receipt["transport"]["provider_request_count"]
    completion = _state_row(
        "attempt_completed",
        reservation["sequence"],
        reservation["attempts_reserved"],
        reservation["provider_requests"] + count,
        reservation["cumulative_reserved_usd_millionths"],
        reservation["cumulative_booked_usd_millionths"] + (PER_ATTEMPT_CAP if count else 0),
        receipt["campaign_state_after"],
        reservation["attempt_lock_file_sha256"],
        receipt_hash,
        receipt["response"]["http_status"],
        reservation["row_hash"],
        receipt["attestation_sha256"],
    )
    _append_line(root / LEDGER_NAME, completion)
    load_and_verify_campaign(root, receipt["attestation_sha256"])
    return completion


def execute_once(
    credential_loader: Callable[[str], str],
    credential_target: str,
    transport: Any,
    attestation_path: Path,
    rate_snapshot_path: Path,
    campaign_directory: Path,
) -> dict[str, Any]:
    try:
        attestation = execution_gate.validate_attestation(attestation_path)
        evidence = verify_historical_evidence()
        request = frozen_request()
        reservation_cost = load_rates(rate_snapshot_path)
        attestation_hash = canonical_hash(attestation_path)
        actual = {**evidence, "request_envelope_sha256": gate2.sha256_bytes(gate2.canonical_json_bytes(request)), "execution_day_rate_snapshot_sha256": canonical_hash(rate_snapshot_path)}
        if actual != EXPECTED or any(attestation[name] != value for name, value in EXPECTED.items()) or reservation_cost != PER_ATTEMPT_CAP:
            raise Gate5KeyManifestCampaignStop("frozen_artifact_hash_mismatch")
        if not campaign_directory.exists():
            initialize_campaign(campaign_directory, attestation_hash)
        sequence, reservation, lock_hash, receipt_path = reserve_attempt(campaign_directory, attestation_hash)
    except (execution_gate.Gate5KeyManifestCampaignAttestationError, gate2.Gate2Error, pilot_runner.Gate5PilotStop, redesign.Gate5DraftError) as exc:
        raise Gate5KeyManifestCampaignStop("pre_execution_validation_failed") from exc

    count = 0
    status: int | None = None
    body: bytes | None = None
    manifest_state = error_state = "not_available_without_response"
    manifest: dict[str, Any] | None = None
    message: str | None = None
    disposition = "stopped"
    stop_reason: str | None = None
    state_after = "stopped_local_or_transport_failure"
    secret: str | None = None
    try:
        try:
            secret = credential_loader(credential_target)
            if not isinstance(secret, str) or not secret or any(character in secret for character in "\r\n\x00"):
                raise Gate5KeyManifestCampaignStop("credential_unavailable")
        except Exception:
            stop_reason = "credential_unavailable"
        if stop_reason is None:
            try:
                count = 1
                response = transport.post(request["endpoint"], gate2.canonical_json_bytes(request["body"]), {"Content-Type": "application/json", "x-goog-api-key": secret}, request["timeout_seconds"])
                response = pilot_runner.validate_provider_response(response)
                status, body = response.status, response.body
                if status == 200:
                    error_state = "not_applicable_http_200"
                    manifest_state, manifest = manifest_capture.capture(body)
                    state_after = "stopped_on_non_503"
                    if manifest_state == "captured":
                        disposition = "passed"
                        stop_reason = "campaign_terminal_http_200"
                    else:
                        stop_reason = "manifest_capture_failed"
                else:
                    manifest_state = "not_applicable_non_200"
                    error_state, message = bounded_error.capture_non_200_error_message(body)
                    if status == 503:
                        state_after = "attempt_cap_reached" if sequence == MAX_ATTEMPTS else "active_after_503"
                        disposition = "stopped" if state_after == "attempt_cap_reached" else "continue_after_503"
                        stop_reason = "attempt_cap_reached" if state_after == "attempt_cap_reached" else "transient_http_503"
                    else:
                        state_after = "stopped_on_non_503"
                        stop_reason = "unexpected_http_status"
            except Exception:
                state_after = "stopped_local_or_transport_failure"
                stop_reason = "transport_or_response_invalid" if status is None else "unexpected_local_error"
        receipt = _receipt(attestation_hash, sequence, reservation["row_hash"], lock_hash, count, status, body, manifest_state, manifest, error_state, message, disposition, stop_reason, state_after)
        complete_attempt(campaign_directory, reservation, receipt, receipt_path)
        return receipt
    finally:
        secret = None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--execute-campaign-attempt", action="store_true")
    parser.add_argument("--credential-target")
    parser.add_argument("--attestation", type=Path)
    parser.add_argument("--rate-snapshot", type=Path)
    parser.add_argument("--campaign-directory", type=Path)
    args = parser.parse_args()
    if args.verify_only == args.execute_campaign_attempt:
        parser.error("choose exactly one mode")
    if args.verify_only:
        print(json.dumps(verify_only(), sort_keys=True))
        return 0
    if not all((args.credential_target, args.attestation, args.rate_snapshot, args.campaign_directory)):
        parser.error("execution requires credential target, attestation, rate snapshot, and campaign directory")
    try:
        receipt = execute_once(gate4.load_windows_generic_credential, args.credential_target, pilot_runner.HTTPSPilotTransport(), args.attestation, args.rate_snapshot, args.campaign_directory)
    except Gate5KeyManifestCampaignStop as exc:
        print(json.dumps({"disposition": "stopped", "stop_reason": exc.code}, sort_keys=True))
        return 2
    except Exception:
        print(json.dumps({"disposition": "stopped", "stop_reason": "unexpected_local_error"}, sort_keys=True))
        return 2
    print(json.dumps({"disposition": receipt["disposition"], "http_status": receipt["response"]["http_status"], "attempt_number": receipt["attempt_number"], "campaign_state": receipt["campaign_state_after"], "receipt": str(_receipt_path(args.campaign_directory, receipt["attempt_number"]))}, sort_keys=True))
    return 0 if receipt["disposition"] in {"passed", "continue_after_503"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
