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
import gate5_execution_gate as execution_gate
import gate5_mock_pilot as mock_pilot
import gate5_mock_runner as response_parser
import gate5_redesign as redesign


PACKAGE = Path(__file__).resolve().parent
CONTRACT_PATH = PACKAGE / "gate5_provider_contract_draft.json"
SCHEDULE_PATH = PACKAGE / "schedule.json"
RECONCILIATION_STOP = 2_250_000
PILOT_CEILING = 3_000_000
MAX_RESPONSE_BYTES = 1_024 * 1_024


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


def verify_local_build() -> dict[str, Any]:
    """Exercise all frozen request construction with no credential, file output, or network."""
    redesign.load_contract()
    hashes = redesign.validate_schedule_requests()
    return {
        "artifact": "gemini_generator_gate5_paid_pilot_runner_verify_only",
        "contract_sha256": canonical_hash(CONTRACT_PATH),
        "schedule_slot_count": len(hashes),
        "unique_request_body_count": len(set(hashes)),
        "network_used": False,
        "credential_read": False,
        "file_output_created": False,
    }


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


def prepare_output_directory(root: Path, contract_hash: str, rate_hash: str, attestation_hash: str) -> dict[str, Path]:
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
        "cost": root / "cost_ledger.jsonl",
        "summary": root / "run_summary.json",
    }
    reservation = {
        "artifact": "gemini_generator_gate5_pre_execution_reservation",
        "created_utc": utc_now(),
        "contract_sha256": contract_hash,
        "rate_snapshot_sha256": rate_hash,
        "attestation_sha256": attestation_hash,
        "slot_count": 24,
        "pilot_ceiling_usd_millionths": PILOT_CEILING,
        "reconciliation_stop_usd_millionths": RECONCILIATION_STOP,
        "state": "reserved_before_credential_read",
    }
    reservation["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(reservation))
    _new_file(paths["lock"], gate2.canonical_json_bytes(reservation))
    for name in ("candidates", "receipts", "rejections", "cost"):
        _new_file(paths[name], b"")
    return paths


def _prompt_references(slots: list[dict[str, Any]]) -> list[tuple[str, str]]:
    result = []
    for slot in slots:
        system, user = gate2.render_messages(slot["mechanism_id"])
        result.append((f"prompt:{slot['slot']}", system + "\n" + user))
    return result


def _receipt(sequence: int, slot: dict[str, Any], request_hash: str, raw_hash: str | None, candidate_hash: str | None, disposition: str, stop_reason: str | None, prior: str | None) -> dict[str, Any]:
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
        "candidate_hash": candidate_hash,
        "disposition": disposition,
        "stop_reason": stop_reason,
        "no_corpus_mutation": True,
    }, prior)


def _cost_row(sequence: int, slot: dict[str, Any], request_hash: str, response_hash: str | None, receipt_hash: str, reservation: int, actual: int, cumulative: int, usage: dict[str, int] | None, disposition: str, stop_reason: str | None, rate_hash: str, prior: str | None) -> dict[str, Any]:
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
        "outstanding_reservations_usd_millionths": 0,
        "request_hash": request_hash,
        "response_hash": response_hash,
        "receipt_hash": receipt_hash,
        "usage": usage,
        "disposition": disposition,
        "stop_reason": stop_reason,
        "no_corpus_mutation": True,
    }, prior)


def _rejection(sequence: int, request_hash: str, raw_hash: str | None, reason: str, prior: str | None) -> dict[str, Any]:
    return gate2.chained_row({
        "artifact": "gemini_generator_gate5_paid_rejection_ledger_row",
        "sequence": sequence,
        "request_hash": request_hash,
        "raw_response_hash": raw_hash,
        "reason_code": reason,
        "disposition": "rejected",
        "no_corpus_mutation": True,
    }, prior)


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


def execute_pilot(
    credential_loader: Callable[[str], str],
    credential_target: str,
    transport: Any,
    attestation_path: Path,
    rate_snapshot_path: Path,
    output_directory: Path,
) -> dict[str, Any]:
    """Execute the frozen 24-slot plan only after every local gate has passed."""
    try:
        attestation = execution_gate.validate_attestation(attestation_path)
        contract_hash = canonical_hash(CONTRACT_PATH)
        rate_hash = canonical_hash(rate_snapshot_path)
        if attestation["final_provider_contract_sha256"] != contract_hash or attestation["execution_day_rate_snapshot_sha256"] != rate_hash:
            raise Gate5PilotStop("attestation_artifact_hash_mismatch")
        rates = load_execution_day_rates(rate_snapshot_path)
        slots = load_schedule()
        redesign.load_contract()
        quarantine, references = gate2.build_quarantine()
        if quarantine.get("record_count") != 111:
            raise Gate5PilotStop("quarantine_manifest_invalid")
        prompt_references = _prompt_references(slots)
        attestation_hash = canonical_hash(attestation_path)
        paths = prepare_output_directory(output_directory, contract_hash, rate_hash, attestation_hash)
        secret = credential_loader(credential_target)
        if not isinstance(secret, str) or not secret or any(ch in secret for ch in "\r\n\x00"):
            raise Gate5PilotStop("credential_unavailable")
    except (execution_gate.Gate5ExecutionGateError, gate2.Gate2Error, redesign.Gate5DraftError) as exc:
        raise Gate5PilotStop("pre_execution_validation_failed") from exc
    except gate4.Gate4Stop as exc:
        raise Gate5PilotStop("credential_unavailable") from exc

    receipts: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    costs: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    prior_receipt = prior_rejection = prior_cost = prior_candidate = None
    earlier_candidates: list[tuple[str, str]] = []
    cumulative = 0
    global_stop: str | None = None
    try:
        for sequence, slot in enumerate(slots, 1):
            request = redesign.build_request(slot)
            reservation = gate2.reservation_cost(slot["model"], rates)
            if cumulative + reservation > RECONCILIATION_STOP:
                global_stop = "reconciliation_stop_before_request"
                break
            request_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(request))
            raw_hash = candidate_hash = None
            parsed: dict[str, Any] | None = None
            pending_candidate: dict[str, Any] | None = None
            disposition, stop_reason = "rejected", None
            try:
                body = gate2.canonical_json_bytes(request["body"])
                response = transport.post(request["endpoint"], body, {"Content-Type": "application/json", "x-goog-api-key": secret}, request["timeout_seconds"])
                if not isinstance(response, ProviderResponse) or len(response.body) > MAX_RESPONSE_BYTES:
                    raise Gate5PilotStop("transport_or_response_size_invalid")
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
                    raise Gate5PilotStop(screen["fatal_reasons"][0])
                pending_candidate = _candidate_row(sequence, slot, request_hash, raw_hash, candidate, screen, prior_candidate)
                disposition = "quarantined_pending_independent_review"
            except (Gate5PilotStop, response_parser.Gate5MockError, UnicodeDecodeError, json.JSONDecodeError, OSError, http.client.HTTPException, ssl.SSLError) as exc:
                stop_reason = exc.code if isinstance(exc, Gate5PilotStop) else str(exc)
                parsed = None
                disposition = "rejected"
            actual = gate2.calculate_cost(slot["model"], parsed["usage"]["promptTokenCount"], parsed["usage"]["candidatesTokenCount"], parsed["usage"]["thoughtsTokenCount"], rates) if parsed else reservation
            cumulative += actual
            if cumulative > PILOT_CEILING:
                disposition = "rejected"
                stop_reason = "pilot_ceiling_exceeded"
                pending_candidate = None
                candidate_hash = None
            receipt = _receipt(sequence, slot, request_hash, raw_hash, candidate_hash, disposition, stop_reason, prior_receipt)
            _append(paths["receipts"], receipt)
            receipts.append(receipt)
            prior_receipt = receipt["row_hash"]
            if stop_reason:
                rejection = _rejection(sequence, request_hash, raw_hash, stop_reason, prior_rejection)
                _append(paths["rejections"], rejection)
                rejections.append(rejection)
                prior_rejection = rejection["row_hash"]
            cost = _cost_row(sequence, slot, request_hash, raw_hash, receipt["row_hash"], reservation, actual, cumulative, parsed["usage"] if parsed else None, disposition, stop_reason, rate_hash, prior_cost)
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
        "cumulative_actual_usd_millionths": cumulative,
        "global_stop": global_stop,
        "network_used": bool(receipts),
        "credential_read": True,
        "candidate_review_performed": False,
        "corpus_mutation_performed": False,
        "receipt_chain_head": prior_receipt,
        "rejection_chain_head": prior_rejection,
        "cost_chain_head": prior_cost,
        "candidate_chain_head": prior_candidate,
    }
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
