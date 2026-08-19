"""Disabled-by-default bounded manual campaign for full Gate 5 pilot attempts."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import gate2
import gate4_connectivity_runner as gate4
import gate5_paid_pilot_retry_campaign_gate as campaign_gate
import gate5_paid_pilot_runner as pilot

PACKAGE = Path(__file__).resolve().parent
PROPOSAL_PATH = PACKAGE / "gate5_paid_pilot_bounded_retry_campaign_proposal.md"
RATE_PATH = PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-16.json"
THIRD_DIRECTORY = PACKAGE / "gate5_pilot_run_third_2026-08-16"
THIRD_ATTESTATION = PACKAGE / "gate5_pre_execution_attestation_third_2026-08-16.json"
LEDGER_NAME = "campaign_state.jsonl"
MAX_ATTEMPTS = campaign_gate.MAX_CAMPAIGN_ATTEMPTS
TERMINAL_STATES = {"attempt_cap_reached", "stopped_for_candidate_review", "stopped_completed", "stopped_nonretryable_outcome"}
STATE_FIELDS = {"artifact", "event", "sequence", "campaign_state", "attempts_reserved", "historical_pilot_component_count", "historical_pilot_components_sha256", "historical_pilot_actual_usd_millionths", "attempt_lock_file_sha256", "completion_file_sha256", "output_directory_name", "prior_row_hash", "campaign_proposal_sha256", "attestation_sha256", "row_hash"}


class Gate5PaidPilotRetryCampaignStop(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_hash(path: Path) -> str:
    try:
        return pilot.canonical_hash(path)
    except pilot.Gate5PilotStop as exc:
        raise Gate5PaidPilotRetryCampaignStop("canonical_input_invalid") from exc


def _new_file(path: Path, data: bytes) -> None:
    try:
        with path.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except (FileExistsError, OSError) as exc:
        raise Gate5PaidPilotRetryCampaignStop("exclusive_output_unavailable") from exc


def _append(path: Path, row: dict[str, Any]) -> None:
    try:
        with path.open("ab") as handle:
            handle.write(gate2.canonical_json_bytes(row))
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise Gate5PaidPilotRetryCampaignStop("campaign_state_append_failed") from exc


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        return [json.loads(line, object_pairs_hook=campaign_gate.reject_duplicate_keys) for line in path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, campaign_gate.Gate5PaidPilotRetryCampaignAttestationError) as exc:
        raise Gate5PaidPilotRetryCampaignStop("campaign_state_invalid") from exc


def initial_components() -> list[dict[str, Any]]:
    first = pilot._historical_component(1, "original_failed_pilot", 10_680, pilot.execution_gate.EXPECTED_FRESH["prior_failed_pilot_summary_file_sha256"], "provider_response_shape_invalid", None)
    second = pilot._historical_component(2, "completed_fresh_pilot", 10_680, pilot.execution_gate.EXPECTED_THIRD["completed_fresh_pilot_summary_file_sha256"], "protected_collision", first["row_hash"])
    third = pilot._historical_component(3, "third_pilot_transient_503", 10_680, campaign_gate.EXPECTED_CAMPAIGN["third_pilot_summary_file_sha256"], "transient_http_503", second["row_hash"])
    components = [first, second, third]
    context = pilot.validate_historical_components(components)
    if context != {"historical_pilot_component_count": 3, "historical_pilot_components_sha256": campaign_gate.INITIAL_COMPONENT_MANIFEST_SHA256, "historical_pilot_actual_usd_millionths": 32_040}:
        raise Gate5PaidPilotRetryCampaignStop("initial_component_manifest_invalid")
    return components


def _load_rows(path: Path) -> list[dict[str, Any]]:
    try:
        return [json.loads(line, object_pairs_hook=campaign_gate.reject_duplicate_keys) for line in path.read_text(encoding="utf-8").splitlines() if line]
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignStop("historical_pilot_evidence_invalid") from exc


def _verify_summary(directory: Path, expected: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], bytes]:
    try:
        summary = gate2.load_json(directory / "run_summary.json")
        receipts = _load_rows(directory / "request_receipts.jsonl")
        costs = _load_rows(directory / "cost_ledger.jsonl")
        rejections = _load_rows(directory / "rejection_ledger.jsonl")
        quarantine = (directory / "candidate_quarantine.jsonl").read_bytes()
        gate2.verify_chain(receipts); gate2.verify_chain(costs)
        if rejections: gate2.verify_chain(rejections)
    except (gate2.Gate2Error, OSError) as exc:
        raise Gate5PaidPilotRetryCampaignStop("historical_pilot_evidence_invalid") from exc
    payload = {key: value for key, value in summary.items() if key != "summary_sha256"}
    if summary.get("summary_sha256") != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)):
        raise Gate5PaidPilotRetryCampaignStop("historical_pilot_evidence_invalid")
    if any(canonical_hash(directory / name) != digest for name, digest in expected.items() if name != "candidate_quarantine.jsonl") or gate2.sha256_bytes(quarantine) != expected["candidate_quarantine.jsonl"]:
        raise Gate5PaidPilotRetryCampaignStop("historical_pilot_evidence_invalid")
    return summary, receipts, costs, rejections, quarantine


def verify_initial_evidence() -> dict[str, Any]:
    pilot.verify_fresh_attempt_evidence()
    pilot.verify_third_attempt_evidence()
    expected = {
        "pilot_reservation.json": campaign_gate.EXPECTED_CAMPAIGN["third_pilot_reservation_file_sha256"],
        "run_summary.json": campaign_gate.EXPECTED_CAMPAIGN["third_pilot_summary_file_sha256"],
        "request_receipts.jsonl": campaign_gate.EXPECTED_CAMPAIGN["third_pilot_receipts_file_sha256"],
        "cost_ledger.jsonl": campaign_gate.EXPECTED_CAMPAIGN["third_pilot_cost_file_sha256"],
        "rejection_ledger.jsonl": campaign_gate.EXPECTED_CAMPAIGN["third_pilot_rejection_file_sha256"],
        "candidate_quarantine.jsonl": campaign_gate.EXPECTED_CAMPAIGN["third_pilot_quarantine_file_sha256"],
    }
    summary, receipts, costs, rejections, quarantine = _verify_summary(THIRD_DIRECTORY, expected)
    if canonical_hash(THIRD_ATTESTATION) != campaign_gate.EXPECTED_CAMPAIGN["third_pilot_final_attestation_sha256"] or summary.get("global_stop") != "unexpected_http_status" or summary.get("candidate_quarantine_count") != 0 or summary.get("cumulative_actual_usd_millionths") != 10_680 or not (len(receipts) == len(costs) == len(rejections) == 1) or quarantine != b"":
        raise Gate5PaidPilotRetryCampaignStop("third_pilot_evidence_invalid")
    if receipts[0].get("http_status") != 503 or receipts[0].get("row_hash") != campaign_gate.EXPECTED_CAMPAIGN["third_pilot_receipt_row_sha256"] or receipts[0].get("raw_response_hash") != campaign_gate.EXPECTED_CAMPAIGN["third_pilot_raw_response_sha256"]:
        raise Gate5PaidPilotRetryCampaignStop("third_pilot_evidence_invalid")
    return {**pilot.validate_historical_components(initial_components()), **campaign_gate.EXPECTED_CAMPAIGN}


def verify_only() -> dict[str, Any]:
    evidence = verify_initial_evidence()
    if canonical_hash(PROPOSAL_PATH) != campaign_gate.EXPECTED_CAMPAIGN["pilot_retry_campaign_proposal_sha256"]:
        raise Gate5PaidPilotRetryCampaignStop("campaign_proposal_mismatch")
    rates = pilot.load_execution_day_rates(RATE_PATH)
    worst_attempt = sum(gate2.reservation_cost(slot["model"], rates) for slot in pilot.load_schedule())
    if worst_attempt != 204_000 or pilot.aggregate_pilot_cost(MAX_ATTEMPTS * worst_attempt, evidence["historical_pilot_actual_usd_millionths"]) != 2_072_040:
        raise Gate5PaidPilotRetryCampaignStop("campaign_cost_math_invalid")
    return {"artifact": "gemini_generator_gate5_paid_pilot_retry_campaign_verify_only", "all_frozen_hashes_match": True, "initial_component_count": 3, "initial_historical_cost_usd_millionths": 32_040, "maximum_campaign_attempts": MAX_ATTEMPTS, "worst_case_aggregate_usd_millionths": 2_072_040, "network_used": False, "credential_read": False, "file_output_created": False}


def _state_row(event: str, sequence: int, state: str, attempts: int, context: dict[str, Any], lock_hash: str | None, completion_hash: str | None, output_name: str | None, prior: str | None, attestation_hash: str) -> dict[str, Any]:
    row = {"artifact": "gemini_generator_gate5_paid_pilot_retry_campaign_state", "event": event, "sequence": sequence, "campaign_state": state, "attempts_reserved": attempts, **context, "attempt_lock_file_sha256": lock_hash, "completion_file_sha256": completion_hash, "output_directory_name": output_name, "prior_row_hash": prior, "campaign_proposal_sha256": campaign_gate.EXPECTED_CAMPAIGN["pilot_retry_campaign_proposal_sha256"], "attestation_sha256": attestation_hash}
    row["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(row))
    return row


def _lock_path(root: Path, sequence: int) -> Path: return root / f"attempt_{sequence:03d}_lock.json"
def _completion_path(root: Path, sequence: int) -> Path: return root / f"attempt_{sequence:03d}_completion.json"
def _output_path(root: Path, sequence: int) -> Path: return root / f"attempt_{sequence:03d}_pilot_output"


def initialize_campaign(root: Path, attestation_hash: str) -> None:
    try:
        root.mkdir(parents=False)
    except (FileExistsError, OSError) as exc:
        raise Gate5PaidPilotRetryCampaignStop("exclusive_output_unavailable") from exc
    context = pilot.validate_historical_components(initial_components())
    _new_file(root / LEDGER_NAME, gate2.canonical_json_bytes(_state_row("campaign_authorized", 0, "authorized_not_started", 0, context, None, None, None, None, attestation_hash)))


def _validate_state_row(row: Any, prior: str | None, attestation_hash: str) -> None:
    if not isinstance(row, dict) or set(row) != STATE_FIELDS or row["prior_row_hash"] != prior or row["attestation_sha256"] != attestation_hash or row["campaign_proposal_sha256"] != campaign_gate.EXPECTED_CAMPAIGN["pilot_retry_campaign_proposal_sha256"]:
        raise Gate5PaidPilotRetryCampaignStop("campaign_state_invalid")
    payload = {key: value for key, value in row.items() if key != "row_hash"}
    if row["row_hash"] != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)) or gate2.contains_secret(row):
        raise Gate5PaidPilotRetryCampaignStop("campaign_state_invalid")


def load_and_verify_campaign(root: Path, attestation_hash: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = _read_jsonl(root / LEDGER_NAME)
    components = initial_components()
    if not rows:
        raise Gate5PaidPilotRetryCampaignStop("campaign_state_invalid")
    prior = None
    for index, row in enumerate(rows):
        _validate_state_row(row, prior, attestation_hash)
        if index == 0:
            if row["event"] != "campaign_authorized" or row["campaign_state"] != "authorized_not_started" or row["sequence"] != 0:
                raise Gate5PaidPilotRetryCampaignStop("campaign_state_invalid")
        elif row["event"] == "attempt_reserved":
            previous = rows[index - 1]
            if row["sequence"] != previous["attempts_reserved"] + 1 or row["attempts_reserved"] != row["sequence"] or row["campaign_state"] != "attempt_reserved" or row["completion_file_sha256"] is not None or row["output_directory_name"] != _output_path(root, row["sequence"]).name:
                raise Gate5PaidPilotRetryCampaignStop("campaign_state_invalid")
            if index != len(rows) - 1 and rows[index + 1].get("event") != "attempt_completed":
                raise Gate5PaidPilotRetryCampaignStop("campaign_state_invalid")
            lock = gate2.load_json(_lock_path(root, row["sequence"]))
            lock_fields = {"artifact", "sequence", "created_utc", "prior_state_row_hash", "historical_pilot_component_count", "historical_pilot_components_sha256", "historical_pilot_actual_usd_millionths", "attestation_sha256", "output_directory_name", "state", "row_hash"}
            lock_payload = {key: value for key, value in lock.items() if key != "row_hash"} if isinstance(lock, dict) else {}
            if not isinstance(lock, dict) or set(lock) != lock_fields or lock.get("row_hash") != gate2.sha256_bytes(gate2.canonical_json_bytes(lock_payload)) or canonical_hash(_lock_path(root, row["sequence"])) != row["attempt_lock_file_sha256"] or lock.get("artifact") != "gemini_generator_gate5_paid_pilot_retry_campaign_attempt_lock" or lock.get("sequence") != row["sequence"] or lock.get("prior_state_row_hash") != row["prior_row_hash"] or lock.get("historical_pilot_components_sha256") != row["historical_pilot_components_sha256"] or lock.get("historical_pilot_component_count") != row["historical_pilot_component_count"] or lock.get("historical_pilot_actual_usd_millionths") != row["historical_pilot_actual_usd_millionths"] or lock.get("attestation_sha256") != attestation_hash or lock.get("output_directory_name") != row["output_directory_name"] or lock.get("state") != "reserved_before_credential_read" or gate2.contains_secret(lock):
                raise Gate5PaidPilotRetryCampaignStop("campaign_state_invalid")
        elif row["event"] == "attempt_completed":
            reserved = rows[index - 1]
            if reserved.get("event") != "attempt_reserved" or row["sequence"] != reserved["sequence"] or row["attempts_reserved"] != reserved["attempts_reserved"] or row["attempt_lock_file_sha256"] != reserved["attempt_lock_file_sha256"] or row["output_directory_name"] != reserved["output_directory_name"]:
                raise Gate5PaidPilotRetryCampaignStop("campaign_state_invalid")
            completion = gate2.load_json(_completion_path(root, row["sequence"]))
            completion_payload = {key: value for key, value in completion.items() if key != "row_hash"}
            component = completion.get("component") if isinstance(completion, dict) else None
            if canonical_hash(_completion_path(root, row["sequence"])) != row["completion_file_sha256"] or completion.get("row_hash") != gate2.sha256_bytes(gate2.canonical_json_bytes(completion_payload)) or not isinstance(component, dict) or component.get("prior_component_hash") != components[-1]["row_hash"] or completion.get("component_row_hash") != component.get("row_hash") or gate2.contains_secret(completion):
                raise Gate5PaidPilotRetryCampaignStop("campaign_state_invalid")
            try:
                if completion.get("completion_kind") == "pilot_output":
                    derived, _, _ = _validate_attempt_output(root / completion["output_directory_name"], components)
                elif completion.get("completion_kind") == "zero_request_local_failure":
                    derived = _zero_request_failure_completion(root / completion["output_directory_name"], components, completion["sequence"], completion["global_stop"])
                else:
                    raise Gate5PaidPilotRetryCampaignStop("campaign_state_invalid")
            except Exception as exc:
                raise Gate5PaidPilotRetryCampaignStop("campaign_state_invalid") from exc
            if completion != derived:
                raise Gate5PaidPilotRetryCampaignStop("campaign_state_invalid")
            if row["campaign_state"] != completion["campaign_state_after"]:
                raise Gate5PaidPilotRetryCampaignStop("campaign_state_invalid")
        else:
            raise Gate5PaidPilotRetryCampaignStop("campaign_state_invalid")
        context = pilot.validate_historical_components(components)
        if row["historical_pilot_component_count"] != context["historical_pilot_component_count"] or row["historical_pilot_components_sha256"] != context["historical_pilot_components_sha256"] or row["historical_pilot_actual_usd_millionths"] != context["historical_pilot_actual_usd_millionths"]:
            if row["event"] != "attempt_completed":
                raise Gate5PaidPilotRetryCampaignStop("campaign_state_invalid")
        if row["event"] == "attempt_completed":
            completion = gate2.load_json(_completion_path(root, row["sequence"]))
            new_component = completion["component"]
            components.append(new_component)
            context = pilot.validate_historical_components(components)
            if any(row[key] != value for key, value in context.items()):
                raise Gate5PaidPilotRetryCampaignStop("campaign_state_invalid")
        prior = row["row_hash"]
    return rows, components


def reserve_attempt(root: Path, attestation_hash: str) -> tuple[int, list[dict[str, Any]]]:
    rows, components = load_and_verify_campaign(root, attestation_hash)
    last = rows[-1]
    if last["campaign_state"] in TERMINAL_STATES:
        raise Gate5PaidPilotRetryCampaignStop("campaign_already_terminal")
    if last["event"] == "attempt_reserved":
        raise Gate5PaidPilotRetryCampaignStop("campaign_incomplete_attempt")
    if last["campaign_state"] not in {"authorized_not_started", "active_after_clean_503"}:
        raise Gate5PaidPilotRetryCampaignStop("campaign_state_invalid")
    sequence = last["attempts_reserved"] + 1
    if sequence > MAX_ATTEMPTS:
        raise Gate5PaidPilotRetryCampaignStop("campaign_attempt_cap_reached")
    context = pilot.validate_historical_components(components)
    output_name = _output_path(root, sequence).name
    lock = {"artifact": "gemini_generator_gate5_paid_pilot_retry_campaign_attempt_lock", "sequence": sequence, "created_utc": utc_now(), "prior_state_row_hash": last["row_hash"], **context, "attestation_sha256": attestation_hash, "output_directory_name": output_name, "state": "reserved_before_credential_read"}
    lock["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(lock))
    _new_file(_lock_path(root, sequence), gate2.canonical_json_bytes(lock))
    lock_hash = canonical_hash(_lock_path(root, sequence))
    _append(root / LEDGER_NAME, _state_row("attempt_reserved", sequence, "attempt_reserved", sequence, context, lock_hash, None, output_name, last["row_hash"], attestation_hash))
    return sequence, components


def _file_hash_or_none(path: Path) -> str | None:
    if not path.exists(): return None
    if path.stat().st_size == 0: return gate2.sha256_bytes(b"")
    return canonical_hash(path)


def _validate_attempt_output(output: Path, components: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], str]:
    summary = gate2.load_json(output / "run_summary.json")
    receipts = _load_rows(output / "request_receipts.jsonl")
    costs = _load_rows(output / "cost_ledger.jsonl")
    rejections = _load_rows(output / "rejection_ledger.jsonl")
    candidates = _load_rows(output / "candidate_quarantine.jsonl")
    gate2.verify_chain(receipts); gate2.verify_chain(costs)
    if rejections: gate2.verify_chain(rejections)
    if candidates: gate2.verify_chain(candidates)
    payload = {k: v for k, v in summary.items() if k != "summary_sha256"}
    context = pilot.validate_historical_components(components)
    if summary.get("summary_sha256") != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)) or any(summary.get(k) != v for k, v in context.items()) or summary.get("aggregate_pilot_actual_usd_millionths") != context["historical_pilot_actual_usd_millionths"] + summary.get("cumulative_actual_usd_millionths", -1):
        raise Gate5PaidPilotRetryCampaignStop("attempt_output_invalid")
    status = receipts[-1].get("http_status") if receipts else None
    clean_503 = summary.get("candidate_quarantine_count") == 0 and summary.get("global_stop") == "unexpected_http_status" and status == 503
    if clean_503:
        state = "attempt_cap_reached" if len(components) - 3 + 1 == MAX_ATTEMPTS else "active_after_clean_503"
        disposition = "transient_http_503"
    elif summary.get("candidate_quarantine_count", 0) > 0:
        state, disposition = "stopped_for_candidate_review", "candidate_quarantined"
    elif summary.get("completed_slots") == 24 and summary.get("global_stop") is None:
        state, disposition = "stopped_completed", "full_pilot_completed"
    else:
        state, disposition = "stopped_nonretryable_outcome", str(summary.get("global_stop") or "nonretryable_outcome")
    evidence = {name: _file_hash_or_none(output / name) for name in ("pilot_reservation.json", "run_summary.json", "request_receipts.jsonl", "cost_ledger.jsonl", "rejection_ledger.jsonl", "candidate_quarantine.jsonl")}
    evidence_sha = gate2.sha256_bytes(gate2.canonical_json_bytes(evidence))
    component = pilot._historical_component(len(components) + 1, f"campaign_attempt_{len(components)-2:03d}", summary["cumulative_actual_usd_millionths"], evidence_sha, disposition, components[-1]["row_hash"])
    completion = {"artifact": "gemini_generator_gate5_paid_pilot_retry_campaign_completion", "completion_kind": "pilot_output", "sequence": len(components) - 2, "output_directory_name": output.name, "output_evidence": evidence, "candidate_quarantine_count": summary["candidate_quarantine_count"], "completed_slots": summary["completed_slots"], "global_stop": summary["global_stop"], "terminal_http_status": status, "booked_cost_usd_millionths": summary["cumulative_actual_usd_millionths"], "campaign_state_after": state, "component": component, "component_row_hash": component["row_hash"]}
    completion["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(completion))
    return completion, component, state


def _zero_request_failure_completion(output: Path, components: list[dict[str, Any]], sequence: int, stop_code: str) -> dict[str, Any]:
    receipts_path = output / "request_receipts.jsonl"
    if receipts_path.exists() and receipts_path.read_bytes() != b"":
        raise Gate5PaidPilotRetryCampaignStop("campaign_incomplete_attempt")
    evidence = {name: _file_hash_or_none(output / name) for name in ("pilot_reservation.json", "run_summary.json", "request_receipts.jsonl", "cost_ledger.jsonl", "rejection_ledger.jsonl", "candidate_quarantine.jsonl")}
    evidence_sha = gate2.sha256_bytes(gate2.canonical_json_bytes(evidence))
    component = pilot._historical_component(len(components) + 1, f"campaign_attempt_{sequence:03d}", 0, evidence_sha, "zero_request_local_failure", components[-1]["row_hash"])
    completion = {"artifact": "gemini_generator_gate5_paid_pilot_retry_campaign_completion", "completion_kind": "zero_request_local_failure", "sequence": sequence, "output_directory_name": output.name, "output_evidence": evidence, "candidate_quarantine_count": 0, "completed_slots": 0, "global_stop": stop_code, "terminal_http_status": None, "booked_cost_usd_millionths": 0, "campaign_state_after": "stopped_nonretryable_outcome", "component": component, "component_row_hash": component["row_hash"]}
    completion["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(completion))
    return completion


def complete_attempt(root: Path, sequence: int, components: list[dict[str, Any]], attestation_hash: str, completion: dict[str, Any]) -> dict[str, Any]:
    _new_file(_completion_path(root, sequence), gate2.canonical_json_bytes(completion))
    completion_hash = canonical_hash(_completion_path(root, sequence))
    components = [*components, completion["component"]]
    context = pilot.validate_historical_components(components)
    rows = _read_jsonl(root / LEDGER_NAME)
    reserved = rows[-1]
    _append(root / LEDGER_NAME, _state_row("attempt_completed", sequence, completion["campaign_state_after"], sequence, context, reserved["attempt_lock_file_sha256"], completion_hash, completion["output_directory_name"], reserved["row_hash"], attestation_hash))
    load_and_verify_campaign(root, attestation_hash)
    return completion


def recover_incomplete_attempt(attestation_path: Path, campaign_root: Path) -> dict[str, Any]:
    """Complete one reserved attempt strictly from its already-written pilot evidence."""
    try:
        campaign_gate.validate_attestation(attestation_path)
        verify_only()
        attestation_hash = canonical_hash(attestation_path)
        rows, components = load_and_verify_campaign(campaign_root, attestation_hash)
    except (campaign_gate.Gate5PaidPilotRetryCampaignAttestationError, gate2.Gate2Error) as exc:
        raise Gate5PaidPilotRetryCampaignStop("recovery_precondition_failed") from exc
    if not rows or rows[-1].get("event") != "attempt_reserved" or rows[-1].get("campaign_state") != "attempt_reserved":
        raise Gate5PaidPilotRetryCampaignStop("no_incomplete_attempt_to_recover")
    sequence = rows[-1]["sequence"]
    if _completion_path(campaign_root, sequence).exists():
        raise Gate5PaidPilotRetryCampaignStop("recovery_output_conflict")
    output = _output_path(campaign_root, sequence)
    try:
        completion, _, _ = _validate_attempt_output(output, components)
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignStop("recovery_evidence_invalid") from exc
    if completion.get("sequence") != sequence or completion.get("output_directory_name") != rows[-1].get("output_directory_name"):
        raise Gate5PaidPilotRetryCampaignStop("recovery_evidence_invalid")
    return complete_attempt(campaign_root, sequence, components, attestation_hash, completion)


def execute_once(credential_loader: Callable[[str], str], credential_target: str, transport: Any, attestation_path: Path, rate_path: Path, campaign_root: Path) -> dict[str, Any]:
    try:
        campaign_gate.validate_attestation(attestation_path)
        verify_only()
        attestation_hash = canonical_hash(attestation_path)
        if not campaign_root.exists(): initialize_campaign(campaign_root, attestation_hash)
        sequence, components = reserve_attempt(campaign_root, attestation_hash)
    except (campaign_gate.Gate5PaidPilotRetryCampaignAttestationError, gate2.Gate2Error) as exc:
        raise Gate5PaidPilotRetryCampaignStop("pre_execution_validation_failed") from exc
    output = _output_path(campaign_root, sequence)
    try:
        pilot.execute_pilot(credential_loader, credential_target, transport, attestation_path, rate_path, output, historical_components=components, attestation_validator=campaign_gate.validate_attestation)
        completion, _, _ = _validate_attempt_output(output, components)
    except Exception as exc:
        if output.exists() and (output / "run_summary.json").exists():
            try:
                completion, _, _ = _validate_attempt_output(output, components)
            except Exception:
                raise Gate5PaidPilotRetryCampaignStop("campaign_incomplete_attempt") from exc
        else:
            stop_code = exc.code if isinstance(exc, pilot.Gate5PilotStop) else "unexpected_local_error"
            completion = _zero_request_failure_completion(output, components, sequence, stop_code)
    return complete_attempt(campaign_root, sequence, components, attestation_hash, completion)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--execute-once", action="store_true")
    parser.add_argument("--recover-incomplete", action="store_true")
    parser.add_argument("--credential-target")
    parser.add_argument("--attestation", type=Path)
    parser.add_argument("--rate-snapshot", type=Path)
    parser.add_argument("--campaign-directory", type=Path)
    args = parser.parse_args()
    if sum((args.verify_only, args.execute_once, args.recover_incomplete)) != 1: parser.error("choose exactly one mode")
    if args.verify_only:
        print(json.dumps(verify_only(), sort_keys=True)); return 0
    if args.recover_incomplete:
        if not all((args.attestation, args.campaign_directory)): parser.error("recovery arguments required")
        try:
            result = recover_incomplete_attempt(args.attestation, args.campaign_directory)
            print(json.dumps({"attempt": result["sequence"], "campaign_state": result["campaign_state_after"], "recovered_from_existing_evidence": True}, sort_keys=True)); return 0
        except Gate5PaidPilotRetryCampaignStop as exc:
            print(json.dumps({"disposition": "stopped", "stop_reason": exc.code}, sort_keys=True)); return 2
        except Exception:
            print(json.dumps({"disposition": "stopped", "stop_reason": "unexpected_local_error"}, sort_keys=True)); return 2
    if not all((args.credential_target, args.attestation, args.rate_snapshot, args.campaign_directory)): parser.error("execution arguments required")
    try:
        result = execute_once(gate4.load_windows_generic_credential, args.credential_target, pilot.HTTPSPilotTransport(), args.attestation, args.rate_snapshot, args.campaign_directory)
        print(json.dumps({"attempt": result["sequence"], "campaign_state": result["campaign_state_after"], "output_directory": result["output_directory_name"]}, sort_keys=True)); return 0
    except Gate5PaidPilotRetryCampaignStop as exc:
        print(json.dumps({"disposition": "stopped", "stop_reason": exc.code}, sort_keys=True)); return 2
    except Exception:
        print(json.dumps({"disposition": "stopped", "stop_reason": "unexpected_local_error"}, sort_keys=True)); return 2


if __name__ == "__main__":
    raise SystemExit(main())
