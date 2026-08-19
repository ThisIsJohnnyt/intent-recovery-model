"""Local-first v6 campaign with content-free schema evidence and reviewed resume."""
from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import gate2
import gate4_connectivity_runner as gate4
import gate5_output_collision_evidence as collision_evidence
import gate5_paid_pilot_retry_campaign_v5_runner as v5
import gate5_paid_pilot_retry_campaign_v6_gate as campaign_gate
import gate5_paid_pilot_v6_engine as pilot
import gate5_schema_conformance_evidence as schema_evidence
import gate5_v6_private_raw_diagnostic as raw_diagnostic


PACKAGE = Path(__file__).resolve().parent
SCOPE_NOTE_PATH = PACKAGE / "gate5_v6_scoped_extension_and_screened_raw_output_proposal.md"
V5_DIRECTORY = PACKAGE / "gate5_paid_pilot_retry_campaign_v5_2026-08-17"
V5_ATTESTATION = PACKAGE / "gate5_paid_pilot_retry_campaign_v5_attestation_2026-08-17.json"
ENGINE_ATTESTATION = PACKAGE / "gate5_paid_pilot_retry_campaign_v3_attestation_2026-08-17.json"
REFERENCE_RATE_PATH = PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-17.json"
LEDGER_NAME = "campaign_state.jsonl"
MAX_ATTEMPTS = campaign_gate.MAX_CAMPAIGN_ATTEMPTS
PAUSE_ELIGIBLE = {"schema_invalid", "extra_key", "finish_reason_invalid", "size_limit_failed"}
TERMINAL_STATES = {"attempt_cap_reached", "stopped_for_candidate_review", "stopped_completed", "stopped_nonretryable_outcome"}
ACTIVE_STATES = {"authorized_not_started", "active_after_clean_503", "active_after_review"}
STATE_FIELDS = {
    "artifact", "event", "sequence", "campaign_state", "attempts_reserved",
    "historical_pilot_component_count", "historical_pilot_components_sha256",
    "historical_pilot_actual_usd_millionths", "attempt_lock_file_sha256",
    "completion_file_sha256", "output_directory_name", "pause_stop_code",
    "schema_conformance_diagnostic_row_sha256", "review_artifact_sha256",
    "effective_rate_snapshot_sha256", "effective_rate_date", "prior_row_hash",
    "campaign_proposal_sha256", "attestation_sha256", "row_hash",
}
BUILD_PATHS = {"v6_proposal_sha256": SCOPE_NOTE_PATH}
V5_TOP_HASHES = {
    "gate5_paid_pilot_retry_campaign_v5_attestation_2026-08-17.json": campaign_gate.EXPECTED_V5["v5_final_attestation_sha256"],
    "gate5_paid_pilot_retry_campaign_v5_2026-08-17/campaign_state.jsonl": campaign_gate.EXPECTED_V5["v5_terminal_campaign_state_sha256"],
    "gate5_paid_pilot_retry_campaign_v5_2026-08-17/attempt_001_lock.json": "7ff8216f78035c718762199365269d4ac0b3a90a2eb68e13f41afa5c53aef0e4",
    "gate5_paid_pilot_retry_campaign_v5_2026-08-17/attempt_001_completion.json": "139cf084d55abdcbd3d13b9daad20c94e5f6cebcb15e8f9c701127a9f5ade864",
    "gate5_paid_pilot_retry_campaign_v5_2026-08-17/attempt_002_lock.json": "8e0cd93c4ad3831b405a397b2e950efb6fdfb231234e70c78f2cfac5f86ac360",
    "gate5_paid_pilot_retry_campaign_v5_2026-08-17/attempt_002_completion.json": "84f60291578e8ae6c62f3ad6f3259c9c786db9b926dfa69dbb52cb0c8d452c94",
    "gate5_paid_pilot_retry_campaign_v5_2026-08-17/attempt_003_lock.json": "b3f80e5030174971b45128202787f504257e428ecd15d9d336203511084d388a",
    "gate5_paid_pilot_retry_campaign_v5_2026-08-17/attempt_003_completion.json": "0cf51c580cd18cd17b50720fd93eee28ba35c04b5a11729b587211161e0d5bbd",
}
V5_OUTPUT_HASHES = {
    1: ["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "50565d2af80625eb9c99285a305f684aa7e99dda8a35504903e7c69556a143d0", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "a3f191e605847094b5eb0b7bc50260dfd9ab16a43f082f2c6f7b74fcb42a8631", "a0e8d6b9de821698dd585fbb87712316ccf284d70714bb45a3814fafffe4aa99", "6044b56813dbabdfc86a02acc8012ef17d513b2d7719eaae785df44b374f75d2", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"],
    2: ["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "a296b5079569e4d248728c97ae17142175a0d827e32c591dd01b19853a6d752b", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "a170a7d1ffe7dfb22055006dfec152af78ddab3c910b177cada2746e317c9f4d", "a0e8d6b9de821698dd585fbb87712316ccf284d70714bb45a3814fafffe4aa99", "6044b56813dbabdfc86a02acc8012ef17d513b2d7719eaae785df44b374f75d2", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"],
    3: ["e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "cbcd1a46cf567bc87ffa5f25a3b4fd007d6a1bcbd29218a31acf0ab909b13595", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "1901805fb9182d894613966a9d0c11d322d55aaf06c31a25dd27ea133a89f3ee", "a0e8d6b9de821698dd585fbb87712316ccf284d70714bb45a3814fafffe4aa99", "6044b56813dbabdfc86a02acc8012ef17d513b2d7719eaae785df44b374f75d2", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"],
}
V5_OUTPUT_NAMES = ("candidate_quarantine.jsonl", "cost_ledger.jsonl", "output_collision_diagnostics.jsonl", "pilot_reservation.json", "rejection_ledger.jsonl", "request_receipts.jsonl", "schema_conformance_diagnostics.jsonl")


class Gate5PaidPilotRetryCampaignV6Stop(RuntimeError):
    def __init__(self, code: str): self.code = code; super().__init__(code)


def local_today() -> str: return date.today().isoformat()
def utc_now() -> str: return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_hash(path: Path) -> str:
    try: return pilot.canonical_hash(path)
    except Exception as exc: raise Gate5PaidPilotRetryCampaignV6Stop("canonical_input_invalid") from exc


def _new_file(path: Path, data: bytes) -> None:
    try:
        with path.open("xb") as handle: handle.write(data); handle.flush(); os.fsync(handle.fileno())
    except (FileExistsError, OSError) as exc: raise Gate5PaidPilotRetryCampaignV6Stop("exclusive_output_unavailable") from exc


def _append(path: Path, row: dict[str, Any]) -> None:
    if gate2.contains_secret(row): raise Gate5PaidPilotRetryCampaignV6Stop("secret_exposure")
    try:
        with path.open("ab") as handle: handle.write(gate2.canonical_json_bytes(row)); handle.flush(); os.fsync(handle.fileno())
    except OSError as exc: raise Gate5PaidPilotRetryCampaignV6Stop("campaign_state_append_failed") from exc


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    try: return [json.loads(line, object_pairs_hook=campaign_gate.reject_duplicate_keys) for line in path.read_text(encoding="utf-8").splitlines() if line]
    except Exception as exc: raise Gate5PaidPilotRetryCampaignV6Stop("campaign_state_invalid") from exc


def initial_components() -> list[dict[str, Any]]:
    digest = canonical_hash(V5_ATTESTATION)
    rows, components = v5.load_and_verify_campaign(V5_DIRECTORY, digest)
    context = pilot.validate_historical_components(components)
    if rows[-1].get("campaign_state") != "attempt_cap_reached" or rows[-1].get("attempts_reserved") != 3 or rows[-1].get("row_hash") != campaign_gate.EXPECTED_V5["v5_terminal_state_row_sha256"]:
        raise Gate5PaidPilotRetryCampaignV6Stop("v5_terminal_state_invalid")
    if context != {"historical_pilot_component_count": 13, "historical_pilot_components_sha256": campaign_gate.INITIAL_COMPONENT_MANIFEST_SHA256, "historical_pilot_actual_usd_millionths": 117_480}:
        raise Gate5PaidPilotRetryCampaignV6Stop("initial_component_manifest_invalid")
    if components[-1].get("row_hash") != campaign_gate.EXPECTED_V5["v5_terminal_component_row_sha256"] or components[-1].get("terminal_disposition") != "unexpected_http_status" or components[-1].get("booked_cost_usd_millionths") != 10_680:
        raise Gate5PaidPilotRetryCampaignV6Stop("v5_terminal_component_invalid")
    return components


def verify_initial_evidence() -> dict[str, Any]:
    for relative, expected in V5_TOP_HASHES.items():
        if canonical_hash(PACKAGE / relative) != expected: raise Gate5PaidPilotRetryCampaignV6Stop("v5_terminal_evidence_invalid")
    for sequence, expected_hashes in V5_OUTPUT_HASHES.items():
        directory = V5_DIRECTORY / f"attempt_{sequence:03d}_pilot_output"
        for name, expected in zip(V5_OUTPUT_NAMES, expected_hashes):
            path = directory / name
            actual = gate2.sha256_bytes(path.read_bytes()) if path.stat().st_size == 0 else canonical_hash(path)
            if actual != expected: raise Gate5PaidPilotRetryCampaignV6Stop("v5_terminal_evidence_invalid")
    return pilot.validate_historical_components(initial_components())


def verify_only() -> dict[str, Any]:
    context = verify_initial_evidence()
    for field, path in BUILD_PATHS.items():
        if campaign_gate.EXPECTED_BUILD[field] == "TO_BE_FILLED" or canonical_hash(path) != campaign_gate.EXPECTED_BUILD[field]:
            raise Gate5PaidPilotRetryCampaignV6Stop("v6_build_mismatch")
    rates = gate2.load_json(REFERENCE_RATE_PATH)
    worst = sum(gate2.reservation_cost(slot["model"], rates) for slot in pilot.load_schedule())
    if worst != 204_000 or context["historical_pilot_actual_usd_millionths"] + MAX_ATTEMPTS * worst != 3_177_480:
        raise Gate5PaidPilotRetryCampaignV6Stop("campaign_cost_math_invalid")
    build_hashes = campaign_gate.current_build_hashes()
    return {"artifact": "gemini_generator_gate5_paid_pilot_retry_campaign_v6_verify_only", **context, "maximum_campaign_attempts": MAX_ATTEMPTS, "worst_case_aggregate_usd_millionths": 3_177_480, **campaign_gate.EXPECTED_BUILD, **build_hashes, "network_used": False, "credential_read": False, "file_output_created": False}


def _state_row(event: str, sequence: int, state: str, attempts: int, context: dict[str, Any], lock_hash: str | None, completion_hash: str | None, output_name: str | None, pause_code: str | None, schema_hash: str | None, review_hash: str | None, rate_hash: str, rate_date: str, prior: str | None, attestation_hash: str) -> dict[str, Any]:
    row = {"artifact": "gemini_generator_gate5_paid_pilot_retry_campaign_v6_state", "event": event, "sequence": sequence, "campaign_state": state, "attempts_reserved": attempts, **context, "attempt_lock_file_sha256": lock_hash, "completion_file_sha256": completion_hash, "output_directory_name": output_name, "pause_stop_code": pause_code, "schema_conformance_diagnostic_row_sha256": schema_hash, "review_artifact_sha256": review_hash, "effective_rate_snapshot_sha256": rate_hash, "effective_rate_date": rate_date, "prior_row_hash": prior, "campaign_proposal_sha256": campaign_gate.EXPECTED_BUILD["v6_proposal_sha256"], "attestation_sha256": attestation_hash}
    row["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(row)); return row


def _lock_path(root: Path, sequence: int) -> Path: return root / f"attempt_{sequence:03d}_lock.json"
def _completion_path(root: Path, sequence: int) -> Path: return root / f"attempt_{sequence:03d}_completion.json"
def _output_path(root: Path, sequence: int) -> Path: return root / f"attempt_{sequence:03d}_pilot_output"
def _review_lock_path(root: Path, sequence: int) -> Path: return root / f"pause_{sequence:03d}_review_lock.json"
def _review_path(root: Path, sequence: int) -> Path: return root / f"pause_{sequence:03d}_review.json"


def initialize_campaign(root: Path, attestation: dict[str, Any], attestation_hash: str) -> None:
    try: root.mkdir(parents=False)
    except (FileExistsError, OSError) as exc: raise Gate5PaidPilotRetryCampaignV6Stop("exclusive_output_unavailable") from exc
    context = pilot.validate_historical_components(initial_components())
    row = _state_row("campaign_authorized", 0, "authorized_not_started", 0, context, None, None, None, None, None, None, attestation["execution_day_rate_snapshot_sha256"], attestation["execution_date"], None, attestation_hash)
    _new_file(root / LEDGER_NAME, gate2.canonical_json_bytes(row))


def _file_hash_or_none(path: Path) -> str | None:
    if not path.exists(): return None
    return gate2.sha256_bytes(path.read_bytes()) if path.stat().st_size == 0 else canonical_hash(path)


def _load_output_rows(path: Path) -> list[dict[str, Any]]:
    try: return [json.loads(line, object_pairs_hook=campaign_gate.reject_duplicate_keys) for line in path.read_text(encoding="utf-8").splitlines() if line]
    except Exception as exc: raise Gate5PaidPilotRetryCampaignV6Stop("attempt_output_invalid") from exc


def _validate_attempt_output(output: Path, components: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], str]:
    try:
        summary = gate2.load_json(output / "run_summary.json")
        receipts = _load_output_rows(output / "request_receipts.jsonl"); costs = _load_output_rows(output / "cost_ledger.jsonl")
        rejections = _load_output_rows(output / "rejection_ledger.jsonl"); collisions = _load_output_rows(output / "output_collision_diagnostics.jsonl")
        schemas = _load_output_rows(output / "schema_conformance_diagnostics.jsonl"); candidates = _load_output_rows(output / "candidate_quarantine.jsonl")
        gate2.verify_chain(receipts); gate2.verify_chain(costs); gate2.verify_chain(rejections); gate2.verify_chain(candidates)
        payload = {key: value for key, value in summary.items() if key != "summary_sha256"}
        context = pilot.validate_historical_components(components)
        campaign_sequence = len(components) - campaign_gate.INITIAL_COMPONENT_COUNT + 1
        if summary.get("summary_sha256") != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)) or any(summary.get(key) != value for key, value in context.items()) or summary.get("aggregate_pilot_actual_usd_millionths") != context["historical_pilot_actual_usd_millionths"] + summary.get("cumulative_actual_usd_millionths", -1): raise ValueError
        if summary.get("completed_slots") != len(receipts) or len(receipts) != len(costs) or summary.get("rejection_count") != len(rejections) or summary.get("candidate_quarantine_count") != len(candidates) or summary.get("output_collision_diagnostic_count") != len(collisions) or summary.get("schema_conformance_diagnostic_count") != len(schemas) or (summary.get("global_stop") is not None and len(rejections) != 1): raise ValueError
        labels = [label for label, _text in gate2.build_quarantine()[1]]
        if summary.get("global_stop") == "output_collision_diagnostic_persistence_failed":
            if collisions or summary.get("output_collision_diagnostic_count") != 0: raise ValueError
        else:
            collision_evidence.validate_rejection_links(pilot._legacy_collision_rejection_view(rejections), collisions, summary, labels, collision_evidence.EXPECTED_CANDIDATE_FIELD_PATHS)
        if summary.get("global_stop") == "schema_conformance_diagnostic_persistence_failed":
            if schemas or summary.get("schema_conformance_diagnostic_count") != 0: raise ValueError
        else: schema_evidence.validate_rejection_links(rejections, schemas, summary)
        raw_state = summary.get("raw_output_diagnostic_state")
        raw_record_hash = summary.get("raw_output_diagnostic_record_sha256")
        allowed_raw_states = {None, "not_eligible_stop_code", "withheld_unparseable_or_unscreenable", "withheld_provider_finish_reason", "withheld_provider_safety_or_citation_signal", "withheld_protected_or_duplicate_collision", "withheld_secret_like_content", "withheld_size_limit", "persisted", "write_failed"}
        if raw_state not in allowed_raw_states: raise ValueError
        if raw_state == "persisted":
            if not isinstance(raw_record_hash, str): raise ValueError
            private_rows = raw_diagnostic.verify(output.parent)
            if len([row for row in private_rows if row["sequence"] == campaign_sequence and row["record_sha256"] == raw_record_hash and row["rejection_row_sha256"] == rejections[-1]["row_hash"]]) != 1: raise ValueError
        elif raw_record_hash is not None or raw_state == "write_failed" and summary.get("global_stop") != "raw_output_diagnostic_persistence_failed": raise ValueError
    except Exception as exc: raise Gate5PaidPilotRetryCampaignV6Stop("attempt_output_invalid") from exc
    status = receipts[-1].get("http_status") if receipts else None
    stop = summary.get("global_stop")
    clean_503 = summary.get("candidate_quarantine_count") == 0 and summary.get("output_collision_diagnostic_count") == 0 and summary.get("schema_conformance_diagnostic_count") == 0 and stop == "unexpected_http_status" and status == 503 and len(receipts) == len(costs) == len(rejections) == 1
    schema_hash = schemas[0]["row_hash"] if len(schemas) == 1 else None
    pause = stop in PAUSE_ELIGIBLE and summary.get("candidate_quarantine_count") == 0 and (stop != "schema_invalid" or schema_hash is not None)
    sequence = campaign_sequence
    if sequence == MAX_ATTEMPTS: state, disposition = "attempt_cap_reached", str(stop or "attempt_cap")
    elif clean_503: state, disposition = "active_after_clean_503", "transient_http_503"
    elif pause: state, disposition = "paused_pending_review", str(stop)
    elif summary.get("candidate_quarantine_count", 0) > 0: state, disposition = "stopped_for_candidate_review", "candidate_quarantined"
    elif summary.get("completed_slots") == 24 and stop is None: state, disposition = "stopped_completed", "full_pilot_completed"
    else: state, disposition = "stopped_nonretryable_outcome", str(stop or "nonretryable_outcome")
    names = ("pilot_reservation.json", "run_summary.json", "request_receipts.jsonl", "cost_ledger.jsonl", "rejection_ledger.jsonl", "output_collision_diagnostics.jsonl", "schema_conformance_diagnostics.jsonl", "candidate_quarantine.jsonl")
    evidence = {name: _file_hash_or_none(output / name) for name in names}
    evidence_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(evidence))
    component = pilot._historical_component(len(components) + 1, f"campaign_v6_attempt_{sequence:03d}", summary["cumulative_actual_usd_millionths"], evidence_hash, disposition, components[-1]["row_hash"])
    completion = {"artifact": "gemini_generator_gate5_paid_pilot_retry_campaign_v6_completion", "completion_kind": "pilot_output", "sequence": sequence, "output_directory_name": output.name, "output_evidence": evidence, "output_evidence_sha256": evidence_hash, "candidate_quarantine_count": summary["candidate_quarantine_count"], "completed_slots": summary["completed_slots"], "global_stop": stop, "pause_stop_code": stop if pause else None, "schema_conformance_diagnostic_row_sha256": schema_hash if stop == "schema_invalid" else None, "terminal_http_status": status, "booked_cost_usd_millionths": summary["cumulative_actual_usd_millionths"], "campaign_state_after": state, "component": component, "component_row_hash": component["row_hash"]}
    completion["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(completion)); return completion, component, state


def _zero_request_completion(output: Path, components: list[dict[str, Any]], sequence: int, stop: str) -> dict[str, Any]:
    if (output / "request_receipts.jsonl").exists() and (output / "request_receipts.jsonl").read_bytes(): raise Gate5PaidPilotRetryCampaignV6Stop("campaign_incomplete_attempt")
    names = ("pilot_reservation.json", "run_summary.json", "request_receipts.jsonl", "cost_ledger.jsonl", "rejection_ledger.jsonl", "output_collision_diagnostics.jsonl", "schema_conformance_diagnostics.jsonl", "candidate_quarantine.jsonl")
    evidence = {name: _file_hash_or_none(output / name) for name in names}; evidence_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(evidence))
    component = pilot._historical_component(len(components) + 1, f"campaign_v6_attempt_{sequence:03d}", 0, evidence_hash, "zero_request_local_failure", components[-1]["row_hash"])
    value = {"artifact": "gemini_generator_gate5_paid_pilot_retry_campaign_v6_completion", "completion_kind": "zero_request_local_failure", "sequence": sequence, "output_directory_name": output.name, "output_evidence": evidence, "output_evidence_sha256": evidence_hash, "candidate_quarantine_count": 0, "completed_slots": 0, "global_stop": stop, "pause_stop_code": None, "schema_conformance_diagnostic_row_sha256": None, "terminal_http_status": None, "booked_cost_usd_millionths": 0, "campaign_state_after": "stopped_nonretryable_outcome", "component": component, "component_row_hash": component["row_hash"]}
    value["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(value)); return value


def _validate_state_row(row: Any, prior: str | None, attestation_hash: str) -> None:
    if not isinstance(row, dict) or set(row) != STATE_FIELDS or row.get("prior_row_hash") != prior or row.get("attestation_sha256") != attestation_hash or row.get("campaign_proposal_sha256") != campaign_gate.EXPECTED_BUILD["v6_proposal_sha256"]: raise Gate5PaidPilotRetryCampaignV6Stop("campaign_state_invalid")
    payload = {key: value for key, value in row.items() if key != "row_hash"}
    if row.get("row_hash") != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)) or gate2.contains_secret(row): raise Gate5PaidPilotRetryCampaignV6Stop("campaign_state_invalid")


def load_and_verify_campaign(root: Path, attestation_hash: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = _read_jsonl(root / LEDGER_NAME); components = initial_components(); prior = None
    if not rows: raise Gate5PaidPilotRetryCampaignV6Stop("campaign_state_invalid")
    for index, row in enumerate(rows):
        _validate_state_row(row, prior, attestation_hash)
        previous = rows[index - 1] if index else None
        if index == 0:
            if row["event"] != "campaign_authorized" or row["campaign_state"] != "authorized_not_started" or row["sequence"] != 0 or row["attempts_reserved"] != 0: raise Gate5PaidPilotRetryCampaignV6Stop("campaign_state_invalid")
        elif row["event"] == "attempt_reserved":
            if previous["campaign_state"] not in ACTIVE_STATES or row["sequence"] != previous["attempts_reserved"] + 1 or row["attempts_reserved"] != row["sequence"] or row["campaign_state"] != "attempt_reserved" or row["effective_rate_snapshot_sha256"] != previous["effective_rate_snapshot_sha256"] or row["effective_rate_date"] != previous["effective_rate_date"]: raise Gate5PaidPilotRetryCampaignV6Stop("campaign_state_invalid")
            lock = gate2.load_json(_lock_path(root, row["sequence"]))
            if canonical_hash(_lock_path(root, row["sequence"])) != row["attempt_lock_file_sha256"] or lock.get("prior_state_row_hash") != row["prior_row_hash"] or lock.get("effective_rate_snapshot_sha256") != row["effective_rate_snapshot_sha256"] or lock.get("effective_rate_date") != row["effective_rate_date"]: raise Gate5PaidPilotRetryCampaignV6Stop("campaign_state_invalid")
        elif row["event"] == "attempt_completed":
            if previous["event"] != "attempt_reserved" or row["sequence"] != previous["sequence"]: raise Gate5PaidPilotRetryCampaignV6Stop("campaign_state_invalid")
            completion = gate2.load_json(_completion_path(root, row["sequence"])); payload = {key: value for key, value in completion.items() if key != "row_hash"}
            if canonical_hash(_completion_path(root, row["sequence"])) != row["completion_file_sha256"] or completion.get("row_hash") != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)): raise Gate5PaidPilotRetryCampaignV6Stop("campaign_state_invalid")
            derived = _validate_attempt_output(root / completion["output_directory_name"], components)[0] if completion.get("completion_kind") == "pilot_output" else _zero_request_completion(root / completion["output_directory_name"], components, completion["sequence"], completion["global_stop"])
            if completion != derived or row["campaign_state"] != completion["campaign_state_after"] or row["pause_stop_code"] != completion["pause_stop_code"] or row["schema_conformance_diagnostic_row_sha256"] != completion["schema_conformance_diagnostic_row_sha256"]: raise Gate5PaidPilotRetryCampaignV6Stop("campaign_state_invalid")
            components.append(completion["component"])
        elif row["event"] == "pause_review_confirmed":
            if previous["campaign_state"] != "paused_pending_review" or row["campaign_state"] != "active_after_review" or row["sequence"] != previous["sequence"] or row["attempts_reserved"] != previous["attempts_reserved"] or not isinstance(row["review_artifact_sha256"], str): raise Gate5PaidPilotRetryCampaignV6Stop("campaign_state_invalid")
            review_lock = gate2.load_json(_review_lock_path(root, row["sequence"])); lock_payload = {key: value for key, value in review_lock.items() if key != "row_hash"}
            if review_lock.get("row_hash") != gate2.sha256_bytes(gate2.canonical_json_bytes(lock_payload)) or review_lock.get("paused_state_row_sha256") != previous["row_hash"] or review_lock.get("review_artifact_sha256") != row["review_artifact_sha256"]: raise Gate5PaidPilotRetryCampaignV6Stop("campaign_state_invalid")
            if canonical_hash(_review_path(root, row["sequence"])) != row["review_artifact_sha256"]: raise Gate5PaidPilotRetryCampaignV6Stop("campaign_state_invalid")
            review = gate2.load_json(_review_path(root, row["sequence"])); review_payload = {key: value for key, value in review.items() if key != "record_sha256"}; template = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v6_review_template.json")
            if set(review) != set(template) or review.get("record_sha256") != gate2.sha256_bytes(gate2.canonical_json_bytes(review_payload)) or review.get("paused_campaign_state_row_sha256") != previous["row_hash"] or review.get("paused_attempt_sequence") != row["sequence"] or review.get("reviewed_by") != "Johnny" or review.get("pause_evidence_reviewed") is not True or review.get("resume_one_next_manual_attempt_authorized_by_johnny") is not True or review.get("effective_rate_snapshot_sha256") != row["effective_rate_snapshot_sha256"] or review.get("review_local_date") != row["effective_rate_date"] or review.get("effective_rate_tuple") != _rate_tuple(REFERENCE_RATE_PATH): raise Gate5PaidPilotRetryCampaignV6Stop("campaign_state_invalid")
        else: raise Gate5PaidPilotRetryCampaignV6Stop("campaign_state_invalid")
        context = pilot.validate_historical_components(components)
        if any(row.get(key) != value for key, value in context.items()): raise Gate5PaidPilotRetryCampaignV6Stop("campaign_state_invalid")
        prior = row["row_hash"]
    return rows, components


def _rate_tuple(path: Path) -> dict[str, Any]:
    value = pilot.load_execution_day_rates(path)
    return {model: {"input": value["rates"][model]["input"], "output_including_thinking": value["rates"][model]["output_including_thinking"]} for model in gate2.MODELS}


def reserve_attempt(root: Path, attestation_hash: str, rate_path: Path) -> tuple[int, list[dict[str, Any]]]:
    rows, components = load_and_verify_campaign(root, attestation_hash); last = rows[-1]
    if last["campaign_state"] in TERMINAL_STATES: raise Gate5PaidPilotRetryCampaignV6Stop("campaign_already_terminal")
    if last["campaign_state"] == "paused_pending_review": raise Gate5PaidPilotRetryCampaignV6Stop("pause_review_required")
    if last["event"] == "attempt_reserved": raise Gate5PaidPilotRetryCampaignV6Stop("campaign_incomplete_attempt")
    if last["campaign_state"] not in ACTIVE_STATES: raise Gate5PaidPilotRetryCampaignV6Stop("campaign_state_invalid")
    if local_today() != last["effective_rate_date"] or canonical_hash(rate_path) != last["effective_rate_snapshot_sha256"]: raise Gate5PaidPilotRetryCampaignV6Stop("execution_day_rate_snapshot_mismatch")
    if _rate_tuple(rate_path) != _rate_tuple(REFERENCE_RATE_PATH): raise Gate5PaidPilotRetryCampaignV6Stop("execution_day_rate_snapshot_mismatch")
    sequence = last["attempts_reserved"] + 1
    if sequence > MAX_ATTEMPTS: raise Gate5PaidPilotRetryCampaignV6Stop("campaign_attempt_cap_reached")
    context = pilot.validate_historical_components(components); output_name = _output_path(root, sequence).name
    lock = {"artifact": "gemini_generator_gate5_paid_pilot_retry_campaign_v6_attempt_lock", "sequence": sequence, "created_utc": utc_now(), "prior_state_row_hash": last["row_hash"], **context, "attestation_sha256": attestation_hash, "output_directory_name": output_name, "effective_rate_snapshot_sha256": last["effective_rate_snapshot_sha256"], "effective_rate_date": last["effective_rate_date"], "state": "reserved_before_credential_read"}
    lock["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(lock)); _new_file(_lock_path(root, sequence), gate2.canonical_json_bytes(lock)); lock_hash = canonical_hash(_lock_path(root, sequence))
    _append(root / LEDGER_NAME, _state_row("attempt_reserved", sequence, "attempt_reserved", sequence, context, lock_hash, None, output_name, None, None, None, last["effective_rate_snapshot_sha256"], last["effective_rate_date"], last["row_hash"], attestation_hash))
    return sequence, components


def complete_attempt(root: Path, sequence: int, components: list[dict[str, Any]], attestation_hash: str, completion: dict[str, Any]) -> dict[str, Any]:
    _new_file(_completion_path(root, sequence), gate2.canonical_json_bytes(completion)); completion_hash = canonical_hash(_completion_path(root, sequence)); rows = _read_jsonl(root / LEDGER_NAME); reserved = rows[-1]
    context = pilot.validate_historical_components([*components, completion["component"]])
    row = _state_row("attempt_completed", sequence, completion["campaign_state_after"], sequence, context, reserved["attempt_lock_file_sha256"], completion_hash, completion["output_directory_name"], completion["pause_stop_code"], completion["schema_conformance_diagnostic_row_sha256"], None, reserved["effective_rate_snapshot_sha256"], reserved["effective_rate_date"], reserved["row_hash"], attestation_hash)
    _append(root / LEDGER_NAME, row); load_and_verify_campaign(root, attestation_hash); return completion


def _validate_review_artifact(path: Path, root: Path, attestation_path: Path, fresh_rate_path: Path | None) -> tuple[dict[str, Any], str, str]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=campaign_gate.reject_duplicate_keys); template = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v6_review_template.json")
    except Exception as exc: raise Gate5PaidPilotRetryCampaignV6Stop("pause_review_invalid") from exc
    if not isinstance(value, dict) or set(value) != set(template): raise Gate5PaidPilotRetryCampaignV6Stop("pause_review_invalid")
    supplied_hash = value.get("record_sha256"); payload = {key: item for key, item in value.items() if key != "record_sha256"}
    if supplied_hash != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)) or gate2.contains_secret(value): raise Gate5PaidPilotRetryCampaignV6Stop("pause_review_invalid")
    attestation_hash = canonical_hash(attestation_path); rows, components = load_and_verify_campaign(root, attestation_hash); paused = rows[-1]
    if paused["campaign_state"] != "paused_pending_review" or value.get("artifact") != "gemini_generator_gate5_paid_pilot_retry_campaign_v6_pause_review" or value.get("schema_version") != 1 or value.get("reviewed_by") != "Johnny" or value.get("pause_evidence_reviewed") is not True or value.get("resume_one_next_manual_attempt_authorized_by_johnny") is not True: raise Gate5PaidPilotRetryCampaignV6Stop("pause_review_invalid")
    completion_path = _completion_path(root, paused["sequence"]); completion = gate2.load_json(completion_path); context = pilot.validate_historical_components(components)
    fixed = {
        "v6_final_attestation_sha256": attestation_hash, "v6_proposal_sha256": campaign_gate.EXPECTED_BUILD["v6_proposal_sha256"], "paused_campaign_state_row_sha256": paused["row_hash"], "paused_attempt_sequence": paused["sequence"], "paused_attempt_lock_sha256": paused["attempt_lock_file_sha256"], "paused_attempt_completion_sha256": paused["completion_file_sha256"], "paused_output_evidence_sha256": completion["output_evidence_sha256"], "pause_stop_code": paused["pause_stop_code"], "schema_conformance_diagnostic_row_sha256": paused["schema_conformance_diagnostic_row_sha256"], "current_attempts_reserved": paused["attempts_reserved"], "current_attempts_remaining": MAX_ATTEMPTS - paused["attempts_reserved"], "current_historical_component_count": context["historical_pilot_component_count"], "current_historical_components_sha256": context["historical_pilot_components_sha256"], "current_historical_actual_usd_millionths": context["historical_pilot_actual_usd_millionths"], "maximum_campaign_attempts": MAX_ATTEMPTS, "reconciliation_stop_usd_millionths": pilot.V6_RECONCILIATION_STOP, "pilot_ceiling_usd_millionths": pilot.V6_PILOT_CEILING, "prior_rate_snapshot_sha256": paused["effective_rate_snapshot_sha256"], "pause_local_date": paused["effective_rate_date"],
    }
    if any(value.get(key) != item for key, item in fixed.items()): raise Gate5PaidPilotRetryCampaignV6Stop("pause_review_invalid")
    mode = value.get("review_mode"); today = local_today()
    if value.get("review_local_date") != today or mode not in {"same_day", "next_day"}: raise Gate5PaidPilotRetryCampaignV6Stop("pause_review_invalid")
    prior_tuple = _rate_tuple(REFERENCE_RATE_PATH)
    if value.get("prior_rate_tuple") != prior_tuple: raise Gate5PaidPilotRetryCampaignV6Stop("pause_review_invalid")
    fresh_fields = ("execution_day_rate_snapshot_verified", "paid_tier_confirmed_that_day", "prepay_plan_confirmed_that_day", "auto_reload_off_that_day", "billing_account_currently_isolated_for_pilot", "no_unexpected_billing_activity_since_pause", "no_other_gemini_api_activity_since_pause", "key_remains_in_windows_credential_manager", "both_exact_models_available_and_not_deprecated", "generate_content_endpoint_confirmed_for_both_models", "common_low_thinking_confirmed_for_both_models", "structured_output_confirmed_for_both_models")
    if mode == "same_day":
        if today != paused["effective_rate_date"] or fresh_rate_path is not None or value.get("effective_rate_snapshot_sha256") != paused["effective_rate_snapshot_sha256"] or value.get("effective_rate_tuple") != prior_tuple or any(value.get(name) is not None for name in fresh_fields) or value.get("positive_prepaid_balance_usd_millionths") is not None: raise Gate5PaidPilotRetryCampaignV6Stop("pause_review_invalid")
        return value, paused["effective_rate_snapshot_sha256"], today
    expected_next = (date.fromisoformat(paused["effective_rate_date"]) + timedelta(days=1)).isoformat()
    if today != expected_next or fresh_rate_path is None: raise Gate5PaidPilotRetryCampaignV6Stop("pause_review_invalid")
    fresh_hash = canonical_hash(fresh_rate_path); fresh_tuple = _rate_tuple(fresh_rate_path)
    if value.get("effective_rate_snapshot_sha256") != fresh_hash or value.get("effective_rate_tuple") != fresh_tuple or fresh_tuple != prior_tuple or any(value.get(name) is not True for name in fresh_fields) or type(value.get("positive_prepaid_balance_usd_millionths")) is not int or value["positive_prepaid_balance_usd_millionths"] < pilot.V6_PILOT_CEILING: raise Gate5PaidPilotRetryCampaignV6Stop("pause_review_invalid")
    return value, fresh_hash, today


def confirm_pause_review(review_path: Path, attestation_path: Path, campaign_root: Path, fresh_rate_path: Path | None = None) -> dict[str, Any]:
    value, rate_hash, rate_date = _validate_review_artifact(review_path, campaign_root, attestation_path, fresh_rate_path); attestation_hash = canonical_hash(attestation_path); rows, components = load_and_verify_campaign(campaign_root, attestation_hash); paused = rows[-1]
    review_hash = canonical_hash(review_path); context = pilot.validate_historical_components(components)
    review_lock = {"artifact": "gemini_generator_gate5_paid_pilot_retry_campaign_v6_pause_review_lock", "sequence": paused["sequence"], "paused_state_row_sha256": paused["row_hash"], "review_artifact_sha256": review_hash, "created_utc": utc_now()}
    review_lock["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(review_lock))
    _new_file(_review_lock_path(campaign_root, paused["sequence"]), gate2.canonical_json_bytes(review_lock))
    _new_file(_review_path(campaign_root, paused["sequence"]), gate2.canonical_json_bytes(value))
    row = _state_row("pause_review_confirmed", paused["sequence"], "active_after_review", paused["attempts_reserved"], context, paused["attempt_lock_file_sha256"], paused["completion_file_sha256"], paused["output_directory_name"], paused["pause_stop_code"], paused["schema_conformance_diagnostic_row_sha256"], review_hash, rate_hash, rate_date, paused["row_hash"], attestation_hash)
    _append(campaign_root / LEDGER_NAME, row); load_and_verify_campaign(campaign_root, attestation_hash); return row


def _pilot_attestation_view(path: Path, execution_date: str) -> dict[str, Any]:
    """Validate v6, then expose the already-reviewed legacy engine fields."""
    campaign_gate.validate_attestation(path, execution_date)
    value = gate2.load_json(ENGINE_ATTESTATION)
    value["prior_pilot_booked_cost_usd_millionths"] = campaign_gate.ATTESTED_BASELINE_COST
    return value


def execute_once(credential_loader: Callable[[str], str], credential_target: str, transport: Any, attestation_path: Path, rate_path: Path, campaign_root: Path) -> dict[str, Any]:
    try:
        if not campaign_root.exists():
            attestation = campaign_gate.validate_attestation(attestation_path); verify_only(); attestation_hash = canonical_hash(attestation_path); initialize_campaign(campaign_root, attestation, attestation_hash)
        else:
            attestation_hash = canonical_hash(attestation_path); rows, _ = load_and_verify_campaign(campaign_root, attestation_hash); campaign_gate.validate_attestation(attestation_path, rows[0]["effective_rate_date"])
        sequence, components = reserve_attempt(campaign_root, attestation_hash, rate_path)
    except Exception as exc:
        if isinstance(exc, Gate5PaidPilotRetryCampaignV6Stop): raise
        raise Gate5PaidPilotRetryCampaignV6Stop("pre_execution_validation_failed") from exc
    output = _output_path(campaign_root, sequence)
    try:
        first_date = _read_jsonl(campaign_root / LEDGER_NAME)[0]["effective_rate_date"]
        current_rate_hash = _read_jsonl(campaign_root / LEDGER_NAME)[-1]["effective_rate_snapshot_sha256"]
        validator = lambda path: _pilot_attestation_view(path, first_date)
        pilot.execute_pilot(credential_loader, credential_target, transport, attestation_path, rate_path, output, historical_components=components, attestation_validator=validator, attested_prior_pilot_booked_cost_usd_millionths=campaign_gate.ATTESTED_BASELINE_COST, effective_rate_snapshot_sha256=current_rate_hash, private_diagnostic_root=campaign_root, private_diagnostic_sequence=sequence)
        completion = _validate_attempt_output(output, components)[0]
    except Exception as exc:
        if output.exists() and (output / "run_summary.json").exists():
            try: completion = _validate_attempt_output(output, components)[0]
            except Exception: raise Gate5PaidPilotRetryCampaignV6Stop("campaign_incomplete_attempt") from exc
        else: completion = _zero_request_completion(output, components, sequence, exc.code if isinstance(exc, pilot.Gate5PilotStop) else "unexpected_local_error")
    return complete_attempt(campaign_root, sequence, components, attestation_hash, completion)


def recover_incomplete_attempt(attestation_path: Path, campaign_root: Path) -> dict[str, Any]:
    """Complete a reserved attempt only from evidence already present on disk."""
    try:
        attestation_hash = canonical_hash(attestation_path); rows, components = load_and_verify_campaign(campaign_root, attestation_hash); campaign_gate.validate_attestation(attestation_path, rows[0]["effective_rate_date"])
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignV6Stop("recovery_precondition_failed") from exc
    last = rows[-1]
    if last.get("event") != "attempt_reserved" or last.get("campaign_state") != "attempt_reserved": raise Gate5PaidPilotRetryCampaignV6Stop("no_incomplete_attempt_to_recover")
    sequence = last["sequence"]
    if _completion_path(campaign_root, sequence).exists(): raise Gate5PaidPilotRetryCampaignV6Stop("recovery_output_conflict")
    try: completion = _validate_attempt_output(_output_path(campaign_root, sequence), components)[0]
    except Exception as exc: raise Gate5PaidPilotRetryCampaignV6Stop("recovery_evidence_invalid") from exc
    if completion.get("sequence") != sequence or completion.get("output_directory_name") != last.get("output_directory_name"): raise Gate5PaidPilotRetryCampaignV6Stop("recovery_evidence_invalid")
    return complete_attempt(campaign_root, sequence, components, attestation_hash, completion)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--verify-only", action="store_true"); parser.add_argument("--execute-once", action="store_true"); parser.add_argument("--confirm-pause-review", action="store_true"); parser.add_argument("--recover-incomplete", action="store_true"); parser.add_argument("--credential-target"); parser.add_argument("--attestation", type=Path); parser.add_argument("--rate-snapshot", type=Path); parser.add_argument("--fresh-rate-snapshot", type=Path); parser.add_argument("--review-artifact", type=Path); parser.add_argument("--campaign-directory", type=Path); args = parser.parse_args()
    if sum((args.verify_only, args.execute_once, args.confirm_pause_review, args.recover_incomplete)) != 1: parser.error("choose exactly one mode")
    try:
        if args.verify_only: print(json.dumps(verify_only(), sort_keys=True)); return 0
        if args.confirm_pause_review:
            if not all((args.attestation, args.review_artifact, args.campaign_directory)): parser.error("review arguments required")
            row = confirm_pause_review(args.review_artifact, args.attestation, args.campaign_directory, args.fresh_rate_snapshot); print(json.dumps({"campaign_state": row["campaign_state"], "review_confirmed": True}, sort_keys=True)); return 0
        if args.recover_incomplete:
            if not all((args.attestation, args.campaign_directory)): parser.error("recovery arguments required")
            result = recover_incomplete_attempt(args.attestation, args.campaign_directory); print(json.dumps({"attempt": result["sequence"], "campaign_state": result["campaign_state_after"], "recovered_from_existing_evidence": True}, sort_keys=True)); return 0
        if not all((args.credential_target, args.attestation, args.rate_snapshot, args.campaign_directory)): parser.error("execution arguments required")
        result = execute_once(gate4.load_windows_generic_credential, args.credential_target, pilot.HTTPSPilotTransport(), args.attestation, args.rate_snapshot, args.campaign_directory); print(json.dumps({"attempt": result["sequence"], "campaign_state": result["campaign_state_after"], "output_directory": result["output_directory_name"]}, sort_keys=True)); return 0
    except Gate5PaidPilotRetryCampaignV6Stop as exc: print(json.dumps({"disposition": "stopped", "stop_reason": exc.code}, sort_keys=True)); return 2
    except Exception: print(json.dumps({"disposition": "stopped", "stop_reason": "unexpected_local_error"}, sort_keys=True)); return 2


if __name__ == "__main__": raise SystemExit(main())
