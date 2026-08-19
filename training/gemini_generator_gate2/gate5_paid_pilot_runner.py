"""Disabled-by-default Gate 5 paid-pilot runner.

Without ``--verify-only`` this module does nothing.  A future user-run
``--execute-pilot`` invocation is intentionally blocked unless a same-day
attestation validates, the current contract/rate hashes match that attestation,
and a brand-new output directory can be reserved before the credential is read.
The implementation has no retries, redirects, model substitution, candidate
promotion, or corpus mutation path.
"""

from __future__ import annotations

import argparse
import http.client
import json
import ssl
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

import gate2
import gate4_connectivity_runner as gate4
import gate5_additional_properties_diagnostic_runner as success_diagnostic
import gate5_execution_gate as execution_gate
import gate5_mock_runner as response_parser
import gate5_output_collision_evidence as collision_evidence
import gate5_schema_conformance_evidence as schema_evidence
import gate5_redesign as redesign


PACKAGE = Path(__file__).resolve().parent
CONTRACT_PATH = PACKAGE / "gate5_provider_contract_draft.json"
PROVIDER_SCHEMA_PATH = PACKAGE / "gate5_provider_response_schema.json"
FRESH_ATTEMPT_PROPOSAL_PATH = PACKAGE / "gate5_paid_pilot_fresh_attempt_proposal.md"
THIRD_ATTEMPT_PROPOSAL_PATH = PACKAGE / "gate5_paid_pilot_third_attempt_proposal.md"
RESPONSE_PARSER_PATH = PACKAGE / "gate5_mock_runner.py"
OUTPUT_COLLISION_PROPOSAL_PATH = PACKAGE / "gate5_output_collision_evidence_proposal.md"
OUTPUT_COLLISION_EVIDENCE_PATH = PACKAGE / "gate5_output_collision_evidence.py"
EXPECTED_OUTPUT_COLLISION_PROPOSAL_SHA256 = "dc5cf11c125d9618cafee13fd972ec41994679f4cd9c9afb6968dbb3f88c178c"
EXPECTED_OUTPUT_COLLISION_EVIDENCE_SHA256 = "69b1f5a2349922a18a844e276acdd25891803f386b71023870d13ca4184f8096"
RESPONSE_SHAPE_CAMPAIGN_DIRECTORY = PACKAGE / "gate5_key_manifest_campaign_2026-08-16"
RESPONSE_SHAPE_CAMPAIGN_RECEIPT_PATH = RESPONSE_SHAPE_CAMPAIGN_DIRECTORY / "attempt_001_receipt.json"
RESPONSE_SHAPE_CAMPAIGN_STATE_PATH = RESPONSE_SHAPE_CAMPAIGN_DIRECTORY / "campaign_state.jsonl"
PRIOR_FAILED_PILOT_DIRECTORY = PACKAGE / "gate5_pilot_run_2026-08-16"
COMPLETED_FRESH_PILOT_DIRECTORY = PACKAGE / "gate5_pilot_run_fresh_2026-08-16"
SUCCESS_DIAGNOSTIC_RECEIPT_PATH = PACKAGE / "gate5_additional_properties_diagnostic_2026-08-15" / "additional_properties_diagnostic_receipt.json"
FLASH_LITE_DIAGNOSTIC_RECEIPT_PATH = PACKAGE / "gate5_flash_lite_diagnostic_2026-08-16" / "flash_lite_diagnostic_receipt.json"
SCHEDULE_PATH = PACKAGE / "schedule.json"
RECONCILIATION_STOP = 2_250_000
PILOT_CEILING = 3_000_000
MAX_RESPONSE_BYTES = 1_024 * 1_024
PRIOR_PILOT_BOOKED_COST = execution_gate.PRIOR_PILOT_BOOKED_COST
ORIGINAL_FAILED_PILOT_BOOKED_COST = execution_gate.ORIGINAL_FAILED_PILOT_BOOKED_COST
COMPLETED_FRESH_PILOT_BOOKED_COST = execution_gate.COMPLETED_FRESH_PILOT_BOOKED_COST
HISTORICAL_COMPONENT_FIELDS = {"sequence", "attempt_id", "booked_cost_usd_millionths", "evidence_sha256", "terminal_disposition", "prior_component_hash", "row_hash"}


class Gate5PilotStop(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class ProviderResponse:
    status: int
    headers: dict[str, str]
    body: bytes


class HTTPSPilotTransport:
    """One direct POST per caller invocation: no redirect or retry support."""

    def post(self, endpoint: str, body: bytes, headers: dict[str, str], timeout_seconds: int) -> ProviderResponse:
        prefix = "https://generativelanguage.googleapis.com"
        if not endpoint.startswith(prefix + "/"):
            raise Gate5PilotStop("endpoint_drift")
        connection = http.client.HTTPSConnection("generativelanguage.googleapis.com", timeout=timeout_seconds, context=ssl.create_default_context())
        try:
            connection.request("POST", endpoint[len(prefix):], body=body, headers=headers)
            response = connection.getresponse()
            payload = response.read(MAX_RESPONSE_BYTES + 1)
            return ProviderResponse(response.status, {key.lower(): value for key, value in response.getheaders()}, payload)
        finally:
            connection.close()


def validate_provider_response(response: Any) -> ProviderResponse:
    if not isinstance(response, ProviderResponse) or type(response.status) is not int or not 100 <= response.status <= 599 or not isinstance(response.headers, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in response.headers.items()) or not isinstance(response.body, bytes) or len(response.body) > MAX_RESPONSE_BYTES:
        raise Gate5PilotStop("transport_or_response_size_invalid")
    return response


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_hash(path: Path) -> str:
    try:
        return gate2.sha256_bytes(gate2.canonical_file(path.resolve())[0])
    except (gate2.Gate2Error, OSError) as exc:
        raise Gate5PilotStop("canonical_input_invalid") from exc


def load_schedule() -> list[dict[str, Any]]:
    try:
        slots = gate2.load_json(SCHEDULE_PATH)["slots"]
    except (gate2.Gate2Error, KeyError, TypeError) as exc:
        raise Gate5PilotStop("frozen_schedule_unavailable") from exc
    if not isinstance(slots, list) or len(slots) != 24 or [item.get("slot") for item in slots] != list(range(1, 25)):
        raise Gate5PilotStop("frozen_schedule_unavailable")
    return slots


def load_execution_day_rates(path: Path) -> dict[str, Any]:
    try:
        value = gate2.load_json(path.resolve())
    except (gate2.Gate2Error, OSError) as exc:
        raise Gate5PilotStop("execution_day_rate_snapshot_invalid") from exc
    expected = {"artifact", "status", "observed_date", "currency", "unit", "rates", "source_url"}
    if not isinstance(value, dict) or set(value) != expected:
        raise Gate5PilotStop("execution_day_rate_snapshot_invalid")
    if value["artifact"] != "gemini_generator_rate_snapshot" or value["status"] != "execution_day_verified":
        raise Gate5PilotStop("execution_day_rate_snapshot_invalid")
    if value["observed_date"] != date.today().isoformat() or value["currency"] != "USD" or value["unit"] != "usd_millionths_per_million_tokens":
        raise Gate5PilotStop("execution_day_rate_snapshot_invalid")
    rates = value["rates"]
    if not isinstance(rates, dict) or set(rates) != set(redesign.EXPECTED_MODELS):
        raise Gate5PilotStop("execution_day_rate_snapshot_invalid")
    for model in redesign.EXPECTED_MODELS:
        if not isinstance(rates[model], dict) or set(rates[model]) != {"input", "output_including_thinking"}:
            raise Gate5PilotStop("execution_day_rate_snapshot_invalid")
        if any(type(rate) is not int or rate < 0 for rate in rates[model].values()):
            raise Gate5PilotStop("execution_day_rate_snapshot_invalid")
    return value


def _historical_component(sequence: int, attempt_id: str, cost: int, evidence_sha256: str, disposition: str, prior: str | None) -> dict[str, Any]:
    row = {"sequence": sequence, "attempt_id": attempt_id, "booked_cost_usd_millionths": cost, "evidence_sha256": evidence_sha256, "terminal_disposition": disposition, "prior_component_hash": prior}
    row["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(row))
    return row


def legacy_historical_components() -> list[dict[str, Any]]:
    first = _historical_component(1, "original_failed_pilot", ORIGINAL_FAILED_PILOT_BOOKED_COST, execution_gate.EXPECTED_FRESH["prior_failed_pilot_summary_file_sha256"], "provider_response_shape_invalid", None)
    second = _historical_component(2, "completed_fresh_pilot", COMPLETED_FRESH_PILOT_BOOKED_COST, execution_gate.EXPECTED_THIRD["completed_fresh_pilot_summary_file_sha256"], "protected_collision", first["row_hash"])
    return [first, second]


def validate_historical_components(components: Any) -> dict[str, Any]:
    if not isinstance(components, list) or not components:
        raise Gate5PilotStop("historical_component_manifest_invalid")
    prior = None
    total = 0
    for sequence, row in enumerate(components, 1):
        if not isinstance(row, dict) or set(row) != HISTORICAL_COMPONENT_FIELDS or row["sequence"] != sequence or row["prior_component_hash"] != prior:
            raise Gate5PilotStop("historical_component_manifest_invalid")
        payload = {key: value for key, value in row.items() if key != "row_hash"}
        if row["row_hash"] != gate2.sha256_bytes(gate2.canonical_json_bytes(payload)) or not isinstance(row["attempt_id"], str) or not row["attempt_id"] or type(row["booked_cost_usd_millionths"]) is not int or row["booked_cost_usd_millionths"] < 0 or not gate2.HEX64_RE.fullmatch(str(row["evidence_sha256"])) or not isinstance(row["terminal_disposition"], str) or not row["terminal_disposition"] or gate2.contains_secret(row):
            raise Gate5PilotStop("historical_component_manifest_invalid")
        total += row["booked_cost_usd_millionths"]
        prior = row["row_hash"]
    return {"historical_pilot_component_count": len(components), "historical_pilot_components_sha256": gate2.sha256_bytes(gate2.canonical_json_bytes(components)), "historical_pilot_actual_usd_millionths": total}


def aggregate_pilot_cost(fresh_run_cost: int, historical_total: int = PRIOR_PILOT_BOOKED_COST) -> int:
    if type(fresh_run_cost) is not int or fresh_run_cost < 0:
        raise Gate5PilotStop("pilot_cost_invalid")
    if type(historical_total) is not int or historical_total < 0:
        raise Gate5PilotStop("pilot_cost_invalid")
    return historical_total + fresh_run_cost


def reservation_fits_reconciliation_stop(fresh_run_cumulative: int, next_reservation: int, historical_total: int = PRIOR_PILOT_BOOKED_COST) -> bool:
    if type(next_reservation) is not int or next_reservation < 0:
        raise Gate5PilotStop("pilot_cost_invalid")
    return aggregate_pilot_cost(fresh_run_cumulative + next_reservation, historical_total) <= RECONCILIATION_STOP


def verify_local_build() -> dict[str, Any]:
    """Exercise all frozen request construction with no credential, file output, or network."""
    redesign.load_contract()
    hashes = redesign.validate_schedule_requests()
    success_row = verify_successful_diagnostic_evidence()
    flash_lite_success_row = verify_successful_flash_lite_evidence()
    fresh_evidence = verify_fresh_attempt_evidence()
    third_evidence = verify_third_attempt_evidence()
    proposal_hash = canonical_hash(OUTPUT_COLLISION_PROPOSAL_PATH)
    evidence_hash = canonical_hash(OUTPUT_COLLISION_EVIDENCE_PATH)
    if proposal_hash != EXPECTED_OUTPUT_COLLISION_PROPOSAL_SHA256 or evidence_hash != EXPECTED_OUTPUT_COLLISION_EVIDENCE_SHA256:
        raise Gate5PilotStop("output_collision_evidence_build_mismatch")
    return {
        "artifact": "gemini_generator_gate5_paid_pilot_runner_verify_only",
        "contract_sha256": canonical_hash(CONTRACT_PATH),
        "provider_schema_sha256": canonical_hash(PROVIDER_SCHEMA_PATH),
        "live_validated_request_envelope_sha256": execution_gate.EXPECTED_LIVE_REQUEST_SHA256,
        "successful_diagnostic_receipt_row_sha256": success_row,
        "flash_lite_live_validated_request_envelope_sha256": execution_gate.EXPECTED_FLASH_LITE_REQUEST_SHA256,
        "successful_flash_lite_receipt_row_sha256": flash_lite_success_row,
        **fresh_evidence,
        **third_evidence,
        "output_collision_evidence_proposal_sha256": proposal_hash,
        "output_collision_evidence_module_sha256": evidence_hash,
        "original_failed_pilot_booked_cost_usd_millionths": ORIGINAL_FAILED_PILOT_BOOKED_COST,
        "completed_fresh_pilot_booked_cost_usd_millionths": COMPLETED_FRESH_PILOT_BOOKED_COST,
        "prior_pilot_booked_cost_usd_millionths": PRIOR_PILOT_BOOKED_COST,
        "schedule_slot_count": len(hashes),
        "unique_request_body_count": len(set(hashes)),
        "network_used": False,
        "credential_read": False,
        "file_output_created": False,
    }


def verify_successful_diagnostic_evidence() -> str:
    try:
        receipt = gate2.load_json(SUCCESS_DIAGNOSTIC_RECEIPT_PATH)
        success_diagnostic.verify_receipt(receipt)
    except (gate2.Gate2Error, success_diagnostic.Gate5AdditionalPropertiesDiagnosticStop, OSError) as exc:
        raise Gate5PilotStop("successful_diagnostic_evidence_invalid") from exc
    if receipt["row_hash"] != execution_gate.EXPECTED_SUCCESS_RECEIPT_ROW_SHA256 or receipt["response"]["http_status"] != 200 or receipt["transport"]["request_hash"] != execution_gate.EXPECTED_LIVE_REQUEST_SHA256 or receipt["error_message_capture_state"] != "not_applicable_http_200" or receipt["non_200_provider_error_message"] is not None:
        raise Gate5PilotStop("successful_diagnostic_evidence_invalid")
    return receipt["row_hash"]


def verify_successful_flash_lite_evidence() -> str:
    # Local import avoids a module-load cycle: the diagnostic reuses this
    # runner's already-reviewed transport and rate validators.
    import gate5_flash_lite_compatibility_diagnostic_runner as flash_lite_diagnostic

    try:
        receipt = gate2.load_json(FLASH_LITE_DIAGNOSTIC_RECEIPT_PATH)
        flash_lite_diagnostic.verify_receipt(receipt)
    except (gate2.Gate2Error, flash_lite_diagnostic.Gate5FlashLiteDiagnosticStop, OSError) as exc:
        raise Gate5PilotStop("successful_flash_lite_evidence_invalid") from exc
    if receipt["row_hash"] != execution_gate.EXPECTED_FLASH_LITE_SUCCESS_RECEIPT_ROW_SHA256 or receipt["response"]["http_status"] != 200 or receipt["transport"]["request_envelope_sha256"] != execution_gate.EXPECTED_FLASH_LITE_REQUEST_SHA256 or receipt["error_message_capture_state"] != "not_applicable_http_200" or receipt["non_200_provider_error_message"] is not None:
        raise Gate5PilotStop("successful_flash_lite_evidence_invalid")
    return receipt["row_hash"]


def _load_jsonl(path: Path, error_code: str = "historical_pilot_evidence_invalid") -> list[dict[str, Any]]:
    try:
        return [json.loads(line, object_pairs_hook=response_parser.reject_duplicate_keys) for line in path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, response_parser.Gate5MockError) as exc:
        raise Gate5PilotStop(error_code) from exc


def verify_prior_failed_pilot_evidence() -> dict[str, Any]:
    summary_path = PRIOR_FAILED_PILOT_DIRECTORY / "run_summary.json"
    receipts_path = PRIOR_FAILED_PILOT_DIRECTORY / "request_receipts.jsonl"
    cost_path = PRIOR_FAILED_PILOT_DIRECTORY / "cost_ledger.jsonl"
    rejection_path = PRIOR_FAILED_PILOT_DIRECTORY / "rejection_ledger.jsonl"
    candidate_path = PRIOR_FAILED_PILOT_DIRECTORY / "candidate_quarantine.jsonl"
    try:
        summary = gate2.load_json(summary_path)
        receipts = _load_jsonl(receipts_path)
        costs = _load_jsonl(cost_path)
        rejections = _load_jsonl(rejection_path)
        gate2.verify_chain(receipts)
        gate2.verify_chain(costs)
        gate2.verify_chain(rejections)
        candidate_bytes = candidate_path.read_bytes()
    except (gate2.Gate2Error, OSError) as exc:
        raise Gate5PilotStop("historical_pilot_evidence_invalid") from exc
    summary_payload = {key: value for key, value in summary.items() if key != "summary_sha256"}
    if summary.get("summary_sha256") != gate2.sha256_bytes(gate2.canonical_json_bytes(summary_payload)) or len(receipts) != 1 or len(costs) != 1 or len(rejections) != 1 or candidate_bytes != b"":
        raise Gate5PilotStop("historical_pilot_evidence_invalid")
    if summary.get("completed_slots") != 1 or summary.get("candidate_quarantine_count") != 0 or summary.get("cumulative_actual_usd_millionths") != ORIGINAL_FAILED_PILOT_BOOKED_COST or summary.get("global_stop") != "provider_response_shape_invalid":
        raise Gate5PilotStop("historical_pilot_evidence_invalid")
    if receipts[0].get("row_hash") != "3db5178d10e4c5bfb556711bade9a25381ffffc5b63b78a9a3bef450546e3ee2" or receipts[0].get("raw_response_hash") != "e349b43a5baa75dd3ce1890a2fea8973c7bdd8ec7bb9d40a04886c401a862d35" or costs[0].get("actual_usd_millionths") != ORIGINAL_FAILED_PILOT_BOOKED_COST:
        raise Gate5PilotStop("historical_pilot_evidence_invalid")
    return {
        "prior_failed_pilot_summary_file_sha256": canonical_hash(summary_path),
        "prior_failed_pilot_receipts_file_sha256": canonical_hash(receipts_path),
        "prior_failed_pilot_cost_file_sha256": canonical_hash(cost_path),
        "prior_failed_pilot_rejection_file_sha256": canonical_hash(rejection_path),
    }


def verify_response_shape_campaign_evidence() -> dict[str, Any]:
    # Local import avoids a module cycle: the campaign reuses this runner's transport validator.
    import gate5_response_shape_key_manifest_campaign_runner as campaign

    try:
        receipt = gate2.load_json(RESPONSE_SHAPE_CAMPAIGN_RECEIPT_PATH)
        campaign.verify_receipt(receipt)
        rows = campaign.load_and_verify_campaign(RESPONSE_SHAPE_CAMPAIGN_DIRECTORY, receipt["attestation_sha256"])
    except (gate2.Gate2Error, campaign.Gate5KeyManifestCampaignStop, OSError) as exc:
        raise Gate5PilotStop("response_shape_campaign_evidence_invalid") from exc
    expected_manifest = {
        "top_level_keys": ["candidates", "modelVersion", "responseId", "usageMetadata"],
        "candidate_count": 1,
        "candidates": [{"candidate_keys": ["content", "finishReason", "index"], "content_keys": ["parts", "role"], "part_count": 1, "part_key_sets": [["text", "thoughtSignature"]]}],
        "usage_metadata_keys": ["candidatesTokenCount", "promptTokenCount", "promptTokensDetails", "serviceTier", "totalTokenCount"],
        "model_status_keys": None,
    }
    if receipt.get("row_hash") != execution_gate.EXPECTED_FRESH["successful_response_shape_campaign_receipt_row_sha256"] or receipt.get("response", {}).get("http_status") != 200 or receipt.get("campaign_state_after") != "stopped_on_non_503" or receipt.get("key_manifest_capture_state") != "captured" or receipt.get("key_manifest") != expected_manifest or rows[-1].get("campaign_state") != "stopped_on_non_503" or rows[-1].get("provider_requests") != 1:
        raise Gate5PilotStop("response_shape_campaign_evidence_invalid")
    return {
        "successful_response_shape_campaign_receipt_file_sha256": canonical_hash(RESPONSE_SHAPE_CAMPAIGN_RECEIPT_PATH),
        "successful_response_shape_campaign_receipt_row_sha256": receipt["row_hash"],
        "successful_response_shape_campaign_state_file_sha256": canonical_hash(RESPONSE_SHAPE_CAMPAIGN_STATE_PATH),
    }


def verify_fresh_attempt_evidence() -> dict[str, Any]:
    evidence = {
        "fresh_attempt_proposal_sha256": canonical_hash(FRESH_ATTEMPT_PROPOSAL_PATH),
        "corrected_response_parser_sha256": canonical_hash(RESPONSE_PARSER_PATH),
        **verify_response_shape_campaign_evidence(),
        **verify_prior_failed_pilot_evidence(),
        "schedule_sha256": canonical_hash(SCHEDULE_PATH),
    }
    if evidence != execution_gate.EXPECTED_FRESH:
        raise Gate5PilotStop("fresh_attempt_evidence_invalid")
    return evidence


def verify_completed_fresh_pilot_evidence() -> dict[str, Any]:
    reservation_path = COMPLETED_FRESH_PILOT_DIRECTORY / "pilot_reservation.json"
    summary_path = COMPLETED_FRESH_PILOT_DIRECTORY / "run_summary.json"
    receipts_path = COMPLETED_FRESH_PILOT_DIRECTORY / "request_receipts.jsonl"
    cost_path = COMPLETED_FRESH_PILOT_DIRECTORY / "cost_ledger.jsonl"
    rejection_path = COMPLETED_FRESH_PILOT_DIRECTORY / "rejection_ledger.jsonl"
    candidate_path = COMPLETED_FRESH_PILOT_DIRECTORY / "candidate_quarantine.jsonl"
    try:
        reservation = gate2.load_json(reservation_path)
        summary = gate2.load_json(summary_path)
        receipts = _load_jsonl(receipts_path, "completed_fresh_pilot_evidence_invalid")
        costs = _load_jsonl(cost_path, "completed_fresh_pilot_evidence_invalid")
        rejections = _load_jsonl(rejection_path, "completed_fresh_pilot_evidence_invalid")
        gate2.verify_chain(receipts)
        gate2.verify_chain(costs)
        gate2.verify_chain(rejections)
        candidate_bytes = candidate_path.read_bytes()
    except (gate2.Gate2Error, OSError) as exc:
        raise Gate5PilotStop("completed_fresh_pilot_evidence_invalid") from exc
    summary_payload = {key: value for key, value in summary.items() if key != "summary_sha256"}
    expected_reason = "proposed_output:output.bullets:02:protected_collision"
    if reservation.get("artifact") != "gemini_generator_gate5_pre_execution_reservation" or reservation.get("historical_pilot_actual_usd_millionths") != ORIGINAL_FAILED_PILOT_BOOKED_COST:
        raise Gate5PilotStop("completed_fresh_pilot_evidence_invalid")
    if summary.get("summary_sha256") != gate2.sha256_bytes(gate2.canonical_json_bytes(summary_payload)) or summary.get("summary_sha256") != "312781bb40728c4e9cf0cdb756889b2d2be026db7d0736c04f2bb96944871821":
        raise Gate5PilotStop("completed_fresh_pilot_evidence_invalid")
    if len(receipts) != 1 or len(costs) != 1 or len(rejections) != 1 or candidate_bytes != b"":
        raise Gate5PilotStop("completed_fresh_pilot_evidence_invalid")
    if summary.get("completed_slots") != 1 or summary.get("candidate_quarantine_count") != 0 or summary.get("cumulative_actual_usd_millionths") != COMPLETED_FRESH_PILOT_BOOKED_COST or summary.get("historical_pilot_actual_usd_millionths") != ORIGINAL_FAILED_PILOT_BOOKED_COST or summary.get("aggregate_pilot_actual_usd_millionths") != PRIOR_PILOT_BOOKED_COST or summary.get("global_stop") != expected_reason:
        raise Gate5PilotStop("completed_fresh_pilot_evidence_invalid")
    receipt = receipts[0]
    cost = costs[0]
    rejection = rejections[0]
    if receipt.get("row_hash") != "34cb7d2f3ba34d5438b539f4d83581d7cc47c32203379d1d85616646f01453be" or receipt.get("raw_response_hash") != "3a5b4042346227912e83ba3a81945e3bc9e7d593f11518f7a65bdae7dbb3b86a" or receipt.get("http_status") != 200 or receipt.get("disposition") != "rejected" or receipt.get("stop_reason") != expected_reason:
        raise Gate5PilotStop("completed_fresh_pilot_evidence_invalid")
    if cost.get("actual_usd_millionths") != COMPLETED_FRESH_PILOT_BOOKED_COST or cost.get("cumulative_actual_usd_millionths") != COMPLETED_FRESH_PILOT_BOOKED_COST or cost.get("historical_pilot_actual_usd_millionths") != ORIGINAL_FAILED_PILOT_BOOKED_COST or cost.get("aggregate_pilot_actual_usd_millionths") != PRIOR_PILOT_BOOKED_COST or cost.get("stop_reason") != expected_reason or rejection.get("reason_code") != expected_reason:
        raise Gate5PilotStop("completed_fresh_pilot_evidence_invalid")
    evidence = {
        "completed_fresh_pilot_reservation_file_sha256": canonical_hash(reservation_path),
        "completed_fresh_pilot_summary_file_sha256": canonical_hash(summary_path),
        "completed_fresh_pilot_receipts_file_sha256": canonical_hash(receipts_path),
        "completed_fresh_pilot_cost_file_sha256": canonical_hash(cost_path),
        "completed_fresh_pilot_rejection_file_sha256": canonical_hash(rejection_path),
        "completed_fresh_pilot_quarantine_file_sha256": gate2.sha256_bytes(candidate_bytes),
    }
    expected = {key: execution_gate.EXPECTED_THIRD[key] for key in evidence}
    if evidence != expected:
        raise Gate5PilotStop("completed_fresh_pilot_evidence_invalid")
    return evidence


def verify_third_attempt_evidence() -> dict[str, Any]:
    evidence = {
        "third_attempt_proposal_sha256": canonical_hash(THIRD_ATTEMPT_PROPOSAL_PATH),
        **verify_completed_fresh_pilot_evidence(),
    }
    if evidence != execution_gate.EXPECTED_THIRD:
        raise Gate5PilotStop("third_attempt_evidence_invalid")
    return evidence


def _new_file(path: Path, data: bytes) -> None:
    try:
        with path.open("xb") as handle:
            handle.write(data)
    except (FileExistsError, OSError) as exc:
        raise Gate5PilotStop("output_path_unavailable") from exc


def _append(path: Path, row: dict[str, Any]) -> None:
    if gate2.contains_secret(row):
        raise Gate5PilotStop("secret_exposure")
    try:
        with path.open("ab") as handle:
            handle.write(gate2.canonical_json_bytes(row))
    except OSError as exc:
        raise Gate5PilotStop("output_path_unavailable") from exc


def prepare_output_directory(root: Path, contract_hash: str, provider_schema_hash: str, rate_hash: str, attestation_hash: str, success_receipt_row_hash: str, flash_lite_success_receipt_row_hash: str, fresh_evidence: dict[str, Any], third_evidence: dict[str, Any], historical_context: dict[str, Any] | None = None) -> dict[str, Path]:
    """Reserve a brand-new run directory before credential access or network."""
    if root.exists():
        raise Gate5PilotStop("output_directory_already_exists")
    try:
        root.mkdir(parents=False)
    except OSError as exc:
        raise Gate5PilotStop("output_path_unavailable") from exc
    paths = {
        "lock": root / "pilot_reservation.json",
        "candidates": root / "candidate_quarantine.jsonl",
        "receipts": root / "request_receipts.jsonl",
        "rejections": root / "rejection_ledger.jsonl",
        "collision_diagnostics": root / "output_collision_diagnostics.jsonl",
        "schema_diagnostics": root / "schema_conformance_diagnostics.jsonl",
        "cost": root / "cost_ledger.jsonl",
        "summary": root / "run_summary.json",
    }
    historical_context = historical_context or validate_historical_components(legacy_historical_components())
    reservation = {
        "artifact": "gemini_generator_gate5_pre_execution_reservation",
        "created_utc": utc_now(),
        "contract_sha256": contract_hash,
        "provider_schema_sha256": provider_schema_hash,
        "live_validated_request_envelope_sha256": execution_gate.EXPECTED_LIVE_REQUEST_SHA256,
        "successful_diagnostic_receipt_row_sha256": success_receipt_row_hash,
        "flash_lite_live_validated_request_envelope_sha256": execution_gate.EXPECTED_FLASH_LITE_REQUEST_SHA256,
        "successful_flash_lite_receipt_row_sha256": flash_lite_success_receipt_row_hash,
        **fresh_evidence,
        **third_evidence,
        "rate_snapshot_sha256": rate_hash,
        "attestation_sha256": attestation_hash,
        "slot_count": 24,
        "pilot_ceiling_usd_millionths": PILOT_CEILING,
        "reconciliation_stop_usd_millionths": RECONCILIATION_STOP,
        "original_failed_pilot_actual_usd_millionths": ORIGINAL_FAILED_PILOT_BOOKED_COST,
        "completed_fresh_pilot_actual_usd_millionths": COMPLETED_FRESH_PILOT_BOOKED_COST,
        **historical_context,
        "state": "reserved_before_credential_read",
    }
    reservation["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(reservation))
    _new_file(paths["lock"], gate2.canonical_json_bytes(reservation))
    for name in ("candidates", "receipts", "rejections", "collision_diagnostics", "schema_diagnostics", "cost"):
        _new_file(paths[name], b"")
    return paths


def _prompt_references(slots: list[dict[str, Any]]) -> list[tuple[str, str]]:
    result = []
    for slot in slots:
        system, user = gate2.render_messages(slot["mechanism_id"])
        result.append((f"prompt:{slot['slot']}", system + "\n" + user))
    return result


def _receipt(sequence: int, slot: dict[str, Any], request_hash: str, raw_hash: str | None, http_status: int | None, candidate_hash: str | None, disposition: str, stop_reason: str | None, prior: str | None) -> dict[str, Any]:
    return gate2.chained_row({
        "artifact": "gemini_generator_gate5_paid_request_receipt",
        "sequence": sequence,
        "schedule_slot": slot["slot"],
        "model": slot["model"],
        "mechanism_id": slot["mechanism_id"],
        "request_hash": request_hash,
        "prompt_hash": slot["prompt_hash"],
        "transport": "gemini_developer_api_rest",
        "network_used": True,
        "raw_response_hash": raw_hash,
        "http_status": http_status,
        "candidate_hash": candidate_hash,
        "disposition": disposition,
        "stop_reason": stop_reason,
        "no_corpus_mutation": True,
    }, prior)


def _cost_row(sequence: int, slot: dict[str, Any], request_hash: str, response_hash: str | None, receipt_hash: str, reservation: int, actual: int, cumulative: int, usage: dict[str, int] | None, disposition: str, stop_reason: str | None, rate_hash: str, prior: str | None, historical_context: dict[str, Any] | None = None) -> dict[str, Any]:
    historical_context = historical_context or validate_historical_components(legacy_historical_components())
    return gate2.chained_row({
        "artifact": "gemini_generator_gate5_paid_cost_ledger_row",
        "sequence": sequence,
        "schedule_slot": slot["slot"],
        "model": slot["model"],
        "mechanism_id": slot["mechanism_id"],
        "rate_snapshot_hash": rate_hash,
        "reserved_usd_millionths": reservation,
        "actual_usd_millionths": actual,
        "cumulative_actual_usd_millionths": cumulative,
        "original_failed_pilot_actual_usd_millionths": ORIGINAL_FAILED_PILOT_BOOKED_COST,
        "completed_fresh_pilot_actual_usd_millionths": COMPLETED_FRESH_PILOT_BOOKED_COST,
        **historical_context,
        "aggregate_pilot_actual_usd_millionths": historical_context["historical_pilot_actual_usd_millionths"] + cumulative,
        "outstanding_reservations_usd_millionths": 0,
        "request_hash": request_hash,
        "response_hash": response_hash,
        "receipt_hash": receipt_hash,
        "usage": usage,
        "disposition": disposition,
        "stop_reason": stop_reason,
        "no_corpus_mutation": True,
    }, prior)


def _rejection(sequence: int, request_hash: str, raw_hash: str | None, reason: str, collision_diagnostic_hash: str | None, prior: str | None, schema_diagnostic_hash: str | None = None) -> dict[str, Any]:
    payload = {
        "artifact": "gemini_generator_gate5_paid_rejection_ledger_row",
        "sequence": sequence,
        "request_hash": request_hash,
        "raw_response_hash": raw_hash,
        "reason_code": reason,
        "output_collision_diagnostic_row_hash": collision_diagnostic_hash,
        "disposition": "rejected",
        "no_corpus_mutation": True,
    }
    if reason == "schema_invalid" or schema_diagnostic_hash is not None:
        payload["schema_conformance_diagnostic_row_hash"] = schema_diagnostic_hash
    return gate2.chained_row(payload, prior)


def _candidate_row(sequence: int, slot: dict[str, Any], request_hash: str, raw_hash: str, candidate: dict[str, Any], screen: dict[str, Any], prior: str | None) -> dict[str, Any]:
    payload = {
        "artifact": "gemini_generator_gate5_quarantined_candidate",
        "sequence": sequence,
        "schedule_slot": slot["slot"],
        "model": slot["model"],
        "mechanism_id": slot["mechanism_id"],
        "request_hash": request_hash,
        "raw_response_hash": raw_hash,
        "candidate": candidate,
        "candidate_hash": gate2.sha256_bytes(gate2.canonical_json_bytes(candidate)),
        "mechanical_screen": screen,
        "disposition": "quarantined_pending_independent_review",
        "no_corpus_mutation": True,
    }
    return gate2.chained_row(payload, prior)


def _legacy_collision_rejection_view(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Project future rows into the already-reviewed collision-link schema."""
    result: list[dict[str, Any]] = []
    prior = None
    for row in rows:
        payload = {key: value for key, value in row.items() if key not in {"row_hash", "prior_row_hash", "schema_conformance_diagnostic_row_hash"}}
        result.append(gate2.chained_row(payload, prior))
        prior = result[-1]["row_hash"]
    return result


def execute_pilot(
    credential_loader: Callable[[str], str],
    credential_target: str,
    transport: Any,
    attestation_path: Path,
    rate_snapshot_path: Path,
    output_directory: Path,
    historical_components: list[dict[str, Any]] | None = None,
    attestation_validator: Callable[[Path], dict[str, Any]] | None = None,
    attested_prior_pilot_booked_cost_usd_millionths: int | None = None,
    effective_rate_snapshot_sha256: str | None = None,
) -> dict[str, Any]:
    """Execute the frozen 24-slot plan only after every local gate has passed."""
    try:
        components = historical_components if historical_components is not None else legacy_historical_components()
        historical_context = validate_historical_components(components)
        attested_prior_cost = historical_context["historical_pilot_actual_usd_millionths"] if attested_prior_pilot_booked_cost_usd_millionths is None else attested_prior_pilot_booked_cost_usd_millionths
        if type(attested_prior_cost) is not int or attested_prior_cost < 0 or attested_prior_cost > historical_context["historical_pilot_actual_usd_millionths"]:
            raise Gate5PilotStop("attested_historical_baseline_invalid")
        try:
            attestation = (attestation_validator or execution_gate.validate_attestation)(attestation_path)
        except Exception as exc:
            raise Gate5PilotStop("pre_execution_validation_failed") from exc
        contract_hash = canonical_hash(CONTRACT_PATH)
        provider_schema_hash = canonical_hash(PROVIDER_SCHEMA_PATH)
        rate_hash = canonical_hash(rate_snapshot_path)
        expected_rate_hash = attestation["execution_day_rate_snapshot_sha256"] if effective_rate_snapshot_sha256 is None else effective_rate_snapshot_sha256
        if not isinstance(expected_rate_hash, str) or rate_hash != expected_rate_hash:
            raise Gate5PilotStop("attestation_artifact_hash_mismatch")
        success_receipt_row_hash = verify_successful_diagnostic_evidence()
        flash_lite_success_receipt_row_hash = verify_successful_flash_lite_evidence()
        fresh_evidence = verify_fresh_attempt_evidence()
        third_evidence = verify_third_attempt_evidence()
        first_request_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(redesign.build_request(load_schedule()[0])))
        flash_lite_request_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(redesign.build_request(load_schedule()[1])))
        if attestation["final_provider_contract_sha256"] != contract_hash or attestation["final_provider_schema_sha256"] != provider_schema_hash or attestation["live_validated_request_envelope_sha256"] != first_request_hash or attestation["successful_corrected_schema_diagnostic_receipt_row_sha256"] != success_receipt_row_hash or attestation["flash_lite_live_validated_request_envelope_sha256"] != flash_lite_request_hash or attestation["successful_flash_lite_receipt_row_sha256"] != flash_lite_success_receipt_row_hash or any(attestation[name] != value for name, value in fresh_evidence.items()) or any(attestation[name] != value for name, value in third_evidence.items()) or attestation["original_failed_pilot_booked_cost_usd_millionths"] != ORIGINAL_FAILED_PILOT_BOOKED_COST or attestation["completed_fresh_pilot_booked_cost_usd_millionths"] != COMPLETED_FRESH_PILOT_BOOKED_COST or attestation["prior_pilot_booked_cost_usd_millionths"] != attested_prior_cost:
            raise Gate5PilotStop("attestation_artifact_hash_mismatch")
        rates = load_execution_day_rates(rate_snapshot_path)
        slots = load_schedule()
        redesign.load_contract()
        quarantine, references = gate2.build_quarantine()
        if quarantine.get("record_count") != 111:
            raise Gate5PilotStop("quarantine_manifest_invalid")
        prompt_references = _prompt_references(slots)
        attestation_hash = canonical_hash(attestation_path)
        if canonical_hash(RESPONSE_PARSER_PATH) != execution_gate.EXPECTED_FRESH["corrected_response_parser_sha256"]:
            raise Gate5PilotStop("corrected_response_parser_mismatch")
        if canonical_hash(OUTPUT_COLLISION_PROPOSAL_PATH) != EXPECTED_OUTPUT_COLLISION_PROPOSAL_SHA256 or canonical_hash(OUTPUT_COLLISION_EVIDENCE_PATH) != EXPECTED_OUTPUT_COLLISION_EVIDENCE_SHA256:
            raise Gate5PilotStop("output_collision_evidence_build_mismatch")
        paths = prepare_output_directory(output_directory, contract_hash, provider_schema_hash, rate_hash, attestation_hash, success_receipt_row_hash, flash_lite_success_receipt_row_hash, fresh_evidence, third_evidence, historical_context)
        secret = credential_loader(credential_target)
        if not isinstance(secret, str) or not secret or any(ch in secret for ch in "\r\n\x00"):
            raise Gate5PilotStop("credential_unavailable")
    except (execution_gate.Gate5ExecutionGateError, gate2.Gate2Error, redesign.Gate5DraftError) as exc:
        raise Gate5PilotStop("pre_execution_validation_failed") from exc
    except gate4.Gate4Stop as exc:
        raise Gate5PilotStop("credential_unavailable") from exc

    receipts: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    collision_diagnostics: list[dict[str, Any]] = []
    schema_diagnostics: list[dict[str, Any]] = []
    costs: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    prior_receipt = prior_rejection = prior_collision_diagnostic = prior_schema_diagnostic = prior_cost = prior_candidate = None
    earlier_candidates: list[tuple[str, str]] = []
    cumulative = 0
    global_stop: str | None = None
    try:
        for sequence, slot in enumerate(slots, 1):
            request = redesign.build_request(slot)
            reservation = gate2.reservation_cost(slot["model"], rates)
            if not reservation_fits_reconciliation_stop(cumulative, reservation, historical_context["historical_pilot_actual_usd_millionths"]):
                global_stop = "reconciliation_stop_before_request"
                break
            request_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(request))
            raw_hash = candidate_hash = http_status = None
            parsed: dict[str, Any] | None = None
            pending_candidate: dict[str, Any] | None = None
            pending_collision_diagnostic: dict[str, Any] | None = None
            pending_schema_diagnostic: dict[str, Any] | None = None
            disposition, stop_reason = "rejected", None
            try:
                body = gate2.canonical_json_bytes(request["body"])
                response = transport.post(request["endpoint"], body, {"Content-Type": "application/json", "x-goog-api-key": secret}, request["timeout_seconds"])
                response = validate_provider_response(response)
                http_status = response.status
                raw_hash = gate2.sha256_bytes(response.body)
                if response.status != 200:
                    raise Gate5PilotStop("unexpected_http_status")
                value = json.loads(response.body.decode("utf-8"), object_pairs_hook=response_parser.reject_duplicate_keys)
                parsed = response_parser.parse_generate_content_response(value)
                usage = parsed["usage"]
                if usage["promptTokenCount"] > gate2.MAX_INPUT_TOKENS or usage["candidatesTokenCount"] + usage["thoughtsTokenCount"] > gate2.MAX_OUTPUT_TOKENS:
                    raise Gate5PilotStop("provider_usage_exceeds_frozen_cap")
                candidate = parsed["candidate_payload"]
                if gate2.contains_secret(candidate):
                    raise Gate5PilotStop("secret_exposure")
                screen = gate2.screen_candidate(candidate, references, earlier_candidates, prompt_references)
                candidate_hash = parsed["candidate_payload_hash"]
                if screen["fatal"]:
                    fatal_reason = screen["fatal_reasons"][0]
                    if fatal_reason.endswith(collision_evidence.REASON_SUFFIX):
                        try:
                            pending_collision_diagnostic = collision_evidence.build_row(
                                sequence,
                                slot,
                                request_hash,
                                raw_hash,
                                fatal_reason,
                                screen,
                                (label for label, _text in references),
                                (field for field, _text in gate2.candidate_fields(candidate)),
                                prior_collision_diagnostic,
                            )
                        except collision_evidence.OutputCollisionEvidenceError:
                            raise Gate5PilotStop("output_collision_diagnostic_withheld")
                    raise Gate5PilotStop(fatal_reason)
                pending_candidate = _candidate_row(sequence, slot, request_hash, raw_hash, candidate, screen, prior_candidate)
                disposition = "quarantined_pending_independent_review"
            except response_parser.Gate5MockError as exc:
                stop_reason = str(exc)
                if stop_reason == "schema_invalid":
                    schema_error = exc.__cause__ if isinstance(exc.__cause__, gate2.ResponseSchemaError) else None
                    if schema_error is None or raw_hash is None:
                        stop_reason = "schema_conformance_diagnostic_withheld"
                    else:
                        try:
                            pending_schema_diagnostic = schema_evidence.build_row(sequence, slot, request_hash, raw_hash, schema_error, prior_schema_diagnostic)
                        except schema_evidence.SchemaConformanceEvidenceError:
                            stop_reason = "schema_conformance_diagnostic_withheld"
                parsed = None
                disposition = "rejected"
            except (Gate5PilotStop, UnicodeDecodeError, json.JSONDecodeError, OSError, http.client.HTTPException, ssl.SSLError) as exc:
                stop_reason = exc.code if isinstance(exc, Gate5PilotStop) else str(exc)
                parsed = None
                disposition = "rejected"
            except Exception:
                stop_reason = "unexpected_local_error"
                parsed = None
                disposition = "rejected"
            actual = gate2.calculate_cost(slot["model"], parsed["usage"]["promptTokenCount"], parsed["usage"]["candidatesTokenCount"], parsed["usage"]["thoughtsTokenCount"], rates) if parsed else reservation
            cumulative += actual
            if aggregate_pilot_cost(cumulative, historical_context["historical_pilot_actual_usd_millionths"]) > PILOT_CEILING:
                disposition = "rejected"
                stop_reason = "pilot_ceiling_exceeded"
                pending_candidate = None
                pending_collision_diagnostic = None
                pending_schema_diagnostic = None
                candidate_hash = None
            receipt = _receipt(sequence, slot, request_hash, raw_hash, http_status, candidate_hash, disposition, stop_reason, prior_receipt)
            _append(paths["receipts"], receipt)
            receipts.append(receipt)
            prior_receipt = receipt["row_hash"]
            if stop_reason:
                diagnostic_hash = pending_collision_diagnostic["row_hash"] if pending_collision_diagnostic is not None else None
                schema_diagnostic_hash = pending_schema_diagnostic["row_hash"] if pending_schema_diagnostic is not None else None
                rejection = _rejection(sequence, request_hash, raw_hash, stop_reason, diagnostic_hash, prior_rejection, schema_diagnostic_hash)
                _append(paths["rejections"], rejection)
                rejections.append(rejection)
                prior_rejection = rejection["row_hash"]
            cost = _cost_row(sequence, slot, request_hash, raw_hash, receipt["row_hash"], reservation, actual, cumulative, parsed["usage"] if parsed else None, disposition, stop_reason, rate_hash, prior_cost, historical_context)
            _append(paths["cost"], cost)
            costs.append(cost)
            prior_cost = cost["row_hash"]
            if pending_candidate is not None:
                _append(paths["candidates"], pending_candidate)
                candidates.append(pending_candidate)
                prior_candidate = pending_candidate["row_hash"]
                earlier_candidates.extend(gate2.candidate_fields(pending_candidate["candidate"]))
            gate2.verify_chain(receipts)
            gate2.verify_chain(costs)
            if rejections:
                gate2.verify_chain(rejections)
            if candidates:
                gate2.verify_chain(candidates)
            if pending_collision_diagnostic is not None:
                try:
                    _append(paths["collision_diagnostics"], pending_collision_diagnostic)
                except Gate5PilotStop:
                    global_stop = "output_collision_diagnostic_persistence_failed"
                    break
                collision_diagnostics.append(pending_collision_diagnostic)
                prior_collision_diagnostic = pending_collision_diagnostic["row_hash"]
                collision_evidence.verify_chain(
                    collision_diagnostics,
                    (label for label, _text in references),
                    (field for field, _text in gate2.candidate_fields(candidate)),
                )
            if pending_schema_diagnostic is not None:
                try:
                    _append(paths["schema_diagnostics"], pending_schema_diagnostic)
                except Gate5PilotStop:
                    global_stop = "schema_conformance_diagnostic_persistence_failed"
                    break
                schema_diagnostics.append(pending_schema_diagnostic)
                prior_schema_diagnostic = pending_schema_diagnostic["row_hash"]
                schema_evidence.verify_chain(schema_diagnostics)
            if stop_reason:
                global_stop = stop_reason
                break
    finally:
        secret = None
    summary = {
        "artifact": "gemini_generator_gate5_paid_pilot_summary",
        "completed_slots": len(receipts),
        "candidate_quarantine_count": len(candidates),
        "rejection_count": len(rejections),
        "output_collision_diagnostic_count": len(collision_diagnostics),
        "schema_conformance_diagnostic_count": len(schema_diagnostics),
        "cumulative_actual_usd_millionths": cumulative,
        "original_failed_pilot_actual_usd_millionths": ORIGINAL_FAILED_PILOT_BOOKED_COST,
        "completed_fresh_pilot_actual_usd_millionths": COMPLETED_FRESH_PILOT_BOOKED_COST,
        **historical_context,
        "aggregate_pilot_actual_usd_millionths": aggregate_pilot_cost(cumulative, historical_context["historical_pilot_actual_usd_millionths"]),
        "global_stop": global_stop,
        "network_used": bool(receipts),
        "credential_read": True,
        "candidate_review_performed": False,
        "corpus_mutation_performed": False,
        "receipt_chain_head": prior_receipt,
        "rejection_chain_head": prior_rejection,
        "output_collision_diagnostic_chain_head": prior_collision_diagnostic,
        "schema_conformance_diagnostic_chain_head": prior_schema_diagnostic,
        "cost_chain_head": prior_cost,
        "candidate_chain_head": prior_candidate,
    }
    if global_stop != "output_collision_diagnostic_persistence_failed":
        collision_evidence.validate_rejection_links(
            _legacy_collision_rejection_view(rejections),
            collision_diagnostics,
            summary,
            (label for label, _text in references),
            collision_evidence.EXPECTED_CANDIDATE_FIELD_PATHS,
        )
    if global_stop != "schema_conformance_diagnostic_persistence_failed":
        schema_evidence.validate_rejection_links(rejections, schema_diagnostics, summary)
    summary["summary_sha256"] = gate2.sha256_bytes(gate2.canonical_json_bytes(summary))
    _new_file(paths["summary"], gate2.canonical_json_bytes(summary))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--execute-pilot", action="store_true")
    parser.add_argument("--credential-target")
    parser.add_argument("--attestation", type=Path)
    parser.add_argument("--rate-snapshot", type=Path)
    parser.add_argument("--output-directory", type=Path)
    args = parser.parse_args()
    if args.verify_only == args.execute_pilot:
        parser.error("choose exactly one of --verify-only or --execute-pilot")
    if args.verify_only:
        print(json.dumps(verify_local_build(), sort_keys=True))
        return 0
    if not all((args.credential_target, args.attestation, args.rate_snapshot, args.output_directory)):
        parser.error("--credential-target, --attestation, --rate-snapshot, and --output-directory are required")
    try:
        summary = execute_pilot(gate4.load_windows_generic_credential, args.credential_target, HTTPSPilotTransport(), args.attestation, args.rate_snapshot, args.output_directory)
    except Gate5PilotStop as exc:
        print(json.dumps({"disposition": "stopped", "stop_reason": exc.code}, sort_keys=True))
        return 2
    except Exception:
        print(json.dumps({"disposition": "stopped", "stop_reason": "unexpected_local_error"}, sort_keys=True))
        return 2
    print(json.dumps({"completed_slots": summary["completed_slots"], "global_stop": summary["global_stop"], "output_directory": str(args.output_directory)}, sort_keys=True))
    return 0 if summary["global_stop"] is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
