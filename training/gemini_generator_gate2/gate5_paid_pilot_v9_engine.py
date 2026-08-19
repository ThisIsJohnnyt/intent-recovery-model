"""Disabled-by-default Gate 5 V9 full-schedule continue-past-collision engine.

This module exposes only local verification at its command line.  Any future
real use must enter through the dedicated V9 campaign runner, which supplies
the credential and transport only after validating the same-day attestation
and reserving a brand-new output directory.  The implementation has no
redirects, model substitution, candidate promotion, or corpus mutation path.

V9 reuses the corrected V8 engine's schedule, prompt builder, historical
legacy-tower verification, and per-row builders unchanged (imported directly,
not duplicated) -- the only new logic here is execute_pilot() itself: a
single full-schedule pass that continues past any protected-collision-family
outcome (protected_collision, pilot_duplicate, prompt_imitation) instead of
stopping the whole run, and retries a genuine HTTP 503 on the same card up to
five times before giving up on that card and moving on. Every other outcome
(secret exposure, schema_invalid, cost-ceiling breach, any unexpected local
error) remains hard-terminal for the whole run, unchanged from V8.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

import gate2
import gate5_execution_gate as execution_gate
import gate5_mock_runner as response_parser
import gate5_output_collision_evidence as collision_evidence
import gate5_paid_pilot_v8_engine as v8
import gate5_schema_conformance_evidence as schema_evidence
import gate5_v6_private_raw_diagnostic as raw_diagnostic


PACKAGE = Path(__file__).resolve().parent
# V9 reuses the corrected V8 build's own schedule/prompt/legacy-tower artifacts
# unchanged; it does not get its own schedule file. All of these are
# re-derived and pinned at load time, not trusted from this constant alone.
EXPECTED_V8_SCHEDULE_SHA256 = "a272c5e9406d81dc53891c1ad11ad5dda1a808d21f6d9e6964cb264a39bafdf4"
EXPECTED_V9_FIRST_REQUEST_SHA256 = "d3ea4942f0b476fe149b0394b6c7dd702bca820a57e8cf6959167458d16a7283"
V9_RECONCILIATION_STOP = 3_750_000
V9_PILOT_CEILING = 5_000_000
MAX_CARD_ATTEMPTS = 5
# Every other rejection reason stays hard-terminal for the whole run; only
# these three (the full output of gate2.screen_candidate's fatal path) let
# the run continue to the next card.
CONTINUE_PAST_REASON_SUFFIXES = (
    collision_evidence.REASON_SUFFIX,  # ":protected_collision"
    ":pilot_duplicate",
    ":prompt_imitation",
)

Gate5PilotStop = v8.Gate5PilotStop
ProviderResponse = v8.ProviderResponse
HTTPSPilotTransport = v8.HTTPSPilotTransport
canonical_hash = v8.canonical_hash
utc_now = v8.utc_now
validate_provider_response = v8.validate_provider_response
load_execution_day_rates = v8.load_execution_day_rates
legacy_historical_components = v8.legacy_historical_components
validate_historical_components = v8.validate_historical_components
_historical_m01_slots = v8._historical_m01_slots
_prompt_references = v8._prompt_references
_legacy_slot_view = v8._legacy_slot_view
_new_file = v8._new_file
_append = v8._append
verify_successful_diagnostic_evidence = v8.verify_successful_diagnostic_evidence
verify_successful_flash_lite_evidence = v8.verify_successful_flash_lite_evidence
verify_fresh_attempt_evidence = v8.verify_fresh_attempt_evidence
verify_third_attempt_evidence = v8.verify_third_attempt_evidence


def load_schedule() -> list[dict[str, Any]]:
    """Re-derive and pin the exact same 22-slot corrected-V8 schedule, unchanged."""
    slots = v8.load_schedule()
    if canonical_hash(v8.SCHEDULE_PATH) != EXPECTED_V8_SCHEDULE_SHA256:
        raise Gate5PilotStop("v9_schedule_source_mismatch")
    first_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(v8.v7_prompt.build_request(slots[0])))
    if first_hash != EXPECTED_V9_FIRST_REQUEST_SHA256:
        raise Gate5PilotStop("v9_request_pin_mismatch")
    return slots


def aggregate_pilot_cost(fresh_run_cost: int, historical_total: int) -> int:
    if type(fresh_run_cost) is not int or fresh_run_cost < 0 or type(historical_total) is not int or historical_total < 0:
        raise Gate5PilotStop("pilot_cost_invalid")
    return fresh_run_cost + historical_total


def reservation_fits_reconciliation_stop(fresh_run_cumulative: int, next_reservation: int, historical_total: int) -> bool:
    if type(next_reservation) is not int or next_reservation < 0:
        raise Gate5PilotStop("pilot_cost_invalid")
    return aggregate_pilot_cost(fresh_run_cumulative + next_reservation, historical_total) <= V9_RECONCILIATION_STOP


def _receipt(sequence: int, slot: dict[str, Any], request_hash: str, raw_hash: str | None, http_status: int | None, candidate_hash: str | None, disposition: str, stop_reason: str | None, card_attempt_number: int, prior: str | None) -> dict[str, Any]:
    return gate2.chained_row({
        "artifact": "gemini_generator_gate5_paid_request_receipt",
        "sequence": sequence,
        "schedule_slot": slot["campaign_schedule_sequence"],
        "card_attempt_number": card_attempt_number,
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


def _cost_row(sequence: int, slot: dict[str, Any], request_hash: str, response_hash: str | None, receipt_hash: str, reservation: int, actual: int, cumulative: int, usage: dict[str, int] | None, disposition: str, stop_reason: str | None, rate_hash: str, prior: str | None, historical_total: int) -> dict[str, Any]:
    return gate2.chained_row({
        "artifact": "gemini_generator_gate5_paid_cost_ledger_row",
        "sequence": sequence,
        "schedule_slot": slot["campaign_schedule_sequence"],
        "model": slot["model"],
        "mechanism_id": slot["mechanism_id"],
        "rate_snapshot_hash": rate_hash,
        "reserved_usd_millionths": reservation,
        "actual_usd_millionths": actual,
        "cumulative_actual_usd_millionths": cumulative,
        "historical_pilot_actual_usd_millionths": historical_total,
        "aggregate_pilot_actual_usd_millionths": historical_total + cumulative,
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
        "schedule_slot": slot["campaign_schedule_sequence"],
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


def prepare_output_directory(root: Path, contract_hash: str, provider_schema_hash: str, rate_hash: str, attestation_hash: str, success_receipt_row_hash: str, flash_lite_success_receipt_row_hash: str, fresh_evidence: dict[str, Any], third_evidence: dict[str, Any], historical_total: int) -> dict[str, Path]:
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
    reservation = {
        "artifact": "gemini_generator_gate5_paid_pilot_v9_reservation",
        "created_utc": utc_now(),
        "contract_sha256": contract_hash,
        "provider_schema_sha256": provider_schema_hash,
        "v9_first_request_sha256": EXPECTED_V9_FIRST_REQUEST_SHA256,
        "v9_reused_v8_schedule_sha256": EXPECTED_V8_SCHEDULE_SHA256,
        "successful_diagnostic_receipt_row_sha256": success_receipt_row_hash,
        "flash_lite_live_validated_request_envelope_sha256": execution_gate.EXPECTED_FLASH_LITE_REQUEST_SHA256,
        "successful_flash_lite_receipt_row_sha256": flash_lite_success_receipt_row_hash,
        **fresh_evidence,
        **third_evidence,
        "rate_snapshot_sha256": rate_hash,
        "attestation_sha256": attestation_hash,
        "slot_count": 22,
        "max_card_attempts": MAX_CARD_ATTEMPTS,
        "pilot_ceiling_usd_millionths": V9_PILOT_CEILING,
        "reconciliation_stop_usd_millionths": V9_RECONCILIATION_STOP,
        "historical_pilot_actual_usd_millionths": historical_total,
    }
    reservation["reservation_sha256"] = gate2.sha256_bytes(gate2.canonical_json_bytes(reservation))
    _new_file(paths["lock"], gate2.canonical_json_bytes(reservation))
    # Every evidence category gets its file created now, even if this run
    # never appends a row to it (e.g. a run that hard-stops before any
    # candidate is ever accepted) - matching V8's convention that the
    # presence of every evidence file is itself part of the evidence,
    # never silently absent. Caught by a direct test read of
    # candidate_quarantine.jsonl on a secret-exposure run that stops
    # before any candidate is ever accepted.
    for name in ("candidates", "receipts", "rejections", "collision_diagnostics", "schema_diagnostics", "cost"):
        _new_file(paths[name], b"")
    return paths


def _outcome_continues_past(stop_reason: str) -> bool:
    # A card that exhausts all MAX_CARD_ATTEMPTS retries on a genuine 503 is
    # recorded and the run moves on to the next card, same as a collision -
    # confirmed explicitly with Johnny. This isn't a screen.fatal_reasons
    # suffix (no "field_path:" prefix), so it's checked by exact match
    # rather than folded into CONTINUE_PAST_REASON_SUFFIXES.
    if stop_reason == "unexpected_http_status_retries_exhausted":
        return True
    return any(stop_reason.endswith(suffix) for suffix in CONTINUE_PAST_REASON_SUFFIXES)


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
    private_diagnostic_root: Path | None = None,
    progress: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Execute the full 22-card schedule in one pass: continue past any
    protected-collision-family outcome, retry a genuine 503 up to
    MAX_CARD_ATTEMPTS times on the same card, and stop the whole run
    immediately on any other exceptional outcome."""
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
        contract_hash = canonical_hash(v8.CONTRACT_PATH)
        provider_schema_hash = canonical_hash(v8.PROVIDER_SCHEMA_PATH)
        rate_hash = canonical_hash(rate_snapshot_path)
        expected_rate_hash = attestation["execution_day_rate_snapshot_sha256"] if effective_rate_snapshot_sha256 is None else effective_rate_snapshot_sha256
        if not isinstance(expected_rate_hash, str) or rate_hash != expected_rate_hash:
            raise Gate5PilotStop("attestation_artifact_hash_mismatch")
        success_receipt_row_hash = verify_successful_diagnostic_evidence()
        flash_lite_success_receipt_row_hash = verify_successful_flash_lite_evidence()
        fresh_evidence = verify_fresh_attempt_evidence()
        third_evidence = verify_third_attempt_evidence()
        historical_slot_one, historical_slot_two = _historical_m01_slots()
        first_request_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(v8.redesign.build_request(historical_slot_one)))
        flash_lite_request_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(v8.redesign.build_request(historical_slot_two)))
        if attestation["final_provider_contract_sha256"] != contract_hash or attestation["final_provider_schema_sha256"] != provider_schema_hash or attestation["live_validated_request_envelope_sha256"] != first_request_hash or attestation["successful_corrected_schema_diagnostic_receipt_row_sha256"] != success_receipt_row_hash or attestation["flash_lite_live_validated_request_envelope_sha256"] != flash_lite_request_hash or attestation["successful_flash_lite_receipt_row_sha256"] != flash_lite_success_receipt_row_hash or any(attestation[name] != value for name, value in fresh_evidence.items()) or any(attestation[name] != value for name, value in third_evidence.items()) or attestation["original_failed_pilot_booked_cost_usd_millionths"] != v8.ORIGINAL_FAILED_PILOT_BOOKED_COST or attestation["completed_fresh_pilot_booked_cost_usd_millionths"] != v8.COMPLETED_FRESH_PILOT_BOOKED_COST or attestation["prior_pilot_booked_cost_usd_millionths"] != attested_prior_cost:
            raise Gate5PilotStop("attestation_artifact_hash_mismatch")
        rates = load_execution_day_rates(rate_snapshot_path)
        slots = load_schedule()
        v8.redesign.load_contract()
        quarantine, references = gate2.build_quarantine()
        if quarantine.get("record_count") != 111:
            raise Gate5PilotStop("quarantine_manifest_invalid")
        # A real list, not a generator: collision_evidence.verify_chain() and
        # validate_rejection_links() iterate this once per row in the growing
        # collision_diagnostics list, and V9 can genuinely accumulate more
        # than one row (unlike every prior version, where at most one
        # collision could ever occur before the campaign stopped) - a
        # generator would silently exhaust after the first row and starve
        # every row after it of any allowed label, failing closed for the
        # wrong reason. Caught by directly exercising a real multi-collision
        # run before this was ever wired into the runner or tests.
        reference_labels = [label for label, _text in references]
        prompt_references = _prompt_references(slots)
        attestation_hash = canonical_hash(attestation_path)
        if canonical_hash(v8.RESPONSE_PARSER_PATH) != execution_gate.EXPECTED_FRESH["corrected_response_parser_sha256"]:
            raise Gate5PilotStop("corrected_response_parser_mismatch")
        if canonical_hash(v8.OUTPUT_COLLISION_PROPOSAL_PATH) != v8.EXPECTED_OUTPUT_COLLISION_PROPOSAL_SHA256 or canonical_hash(v8.OUTPUT_COLLISION_EVIDENCE_PATH) != v8.EXPECTED_OUTPUT_COLLISION_EVIDENCE_SHA256:
            raise Gate5PilotStop("output_collision_evidence_build_mismatch")
        paths = prepare_output_directory(output_directory, contract_hash, provider_schema_hash, rate_hash, attestation_hash, success_receipt_row_hash, flash_lite_success_receipt_row_hash, fresh_evidence, third_evidence, historical_context["historical_pilot_actual_usd_millionths"])
        try:
            secret = credential_loader(credential_target)
        except Exception as exc:
            raise Gate5PilotStop("credential_unavailable") from exc
        if not isinstance(secret, str) or not secret or any(ch in secret for ch in "\r\n\x00"):
            raise Gate5PilotStop("credential_unavailable")
    except (execution_gate.Gate5ExecutionGateError, gate2.Gate2Error, v8.redesign.Gate5DraftError) as exc:
        raise Gate5PilotStop("pre_execution_validation_failed") from exc

    historical_total = historical_context["historical_pilot_actual_usd_millionths"]
    receipts: list[dict[str, Any]] = []
    costs: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    collision_diagnostics: list[dict[str, Any]] = []
    schema_diagnostics: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    prior_receipt = prior_cost = prior_rejection = prior_collision_diagnostic = prior_schema_diagnostic = prior_candidate = None
    # Every real request gets a receipt/cost row, so request_sequence is dense
    # and safe to reuse as their own list-position sequence. Rejections (and,
    # when linked, their collision/schema diagnostic) are sparse - only some
    # cards produce one - so rejection_sequence is its own independent dense
    # counter, and a linked diagnostic row reuses that SAME value as its own
    # "sequence"/"schedule_slot": gate5_output_collision_evidence.build_row()
    # and gate5_schema_conformance_evidence.build_row() each internally
    # require schedule_slot == sequence, and validate_rejection_links()
    # separately requires the diagnostic's sequence to equal its linked
    # rejection's sequence - mechanism_id/model, recorded independently in
    # every row, remain the reliable "which card" identifier regardless.
    request_sequence = rejection_sequence = candidate_sequence = 0
    earlier_candidates: list[tuple[str, str]] = []
    cumulative = 0
    global_stop: str | None = None
    cards_completed = 0
    raw_output_diagnostic_state: str | None = None
    raw_output_diagnostic_record_sha256: str | None = None
    try:
        for card_index, slot in enumerate(slots, 1):
            if global_stop is not None:
                break
            card_outcome_label: str | None = None
            card_attempt_number = 0
            for card_attempt_number in range(1, MAX_CARD_ATTEMPTS + 1):
                request = v8.v7_prompt.build_request(slot)
                reservation = gate2.reservation_cost(slot["model"], rates)
                if not reservation_fits_reconciliation_stop(cumulative, reservation, historical_total):
                    global_stop = "reconciliation_stop_before_request"
                    card_outcome_label = global_stop
                    break
                request_sequence += 1
                request_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(request))
                raw_hash = candidate_hash = http_status = None
                parsed: dict[str, Any] | None = None
                accepted_candidate: dict[str, Any] | None = None
                accepted_screen: dict[str, Any] | None = None
                fatal_collision_reason: str | None = None
                fatal_collision_screen: dict[str, Any] | None = None
                fatal_collision_candidate: dict[str, Any] | None = None
                schema_error_obj: Any = None
                pending_raw_output_diagnostic: dict[str, Any] | None = None
                response_value: Any = None
                disposition, stop_reason = "rejected", None
                try:
                    body = gate2.canonical_json_bytes(request["body"])
                    response = transport.post(request["endpoint"], body, {"Content-Type": "application/json", "x-goog-api-key": secret}, request["timeout_seconds"])
                    response = validate_provider_response(response)
                    http_status = response.status
                    raw_hash = gate2.sha256_bytes(response.body)
                    if response.status != 200:
                        raise Gate5PilotStop("unexpected_http_status")
                    response_value = json.loads(response.body.decode("utf-8"), object_pairs_hook=response_parser.reject_duplicate_keys)
                    parsed = response_parser.parse_generate_content_response(response_value)
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
                            fatal_collision_reason, fatal_collision_screen, fatal_collision_candidate = fatal_reason, screen, candidate
                        raise Gate5PilotStop(fatal_reason)
                    accepted_candidate, accepted_screen = candidate, screen
                    disposition = "quarantined_pending_independent_review"
                except response_parser.Gate5MockError as exc:
                    stop_reason = str(exc)
                    if private_diagnostic_root is not None and raw_hash is not None:
                        pending_raw_output_diagnostic = raw_diagnostic.consider(
                            response_value, stop_reason, references, earlier_candidates, prompt_references,
                        )
                    if stop_reason == "schema_invalid":
                        schema_error_obj = exc.__cause__ if isinstance(exc.__cause__, gate2.ResponseSchemaError) else None
                        if schema_error_obj is None or raw_hash is None:
                            stop_reason = "schema_conformance_diagnostic_withheld"
                    parsed = None
                    disposition = "rejected"
                except (Gate5PilotStop, UnicodeDecodeError, json.JSONDecodeError, OSError) as exc:
                    stop_reason = exc.code if isinstance(exc, Gate5PilotStop) else str(exc)
                    parsed = None
                    disposition = "rejected"
                except Exception:
                    stop_reason = "unexpected_local_error"
                    parsed = None
                    disposition = "rejected"

                actual = gate2.calculate_cost(slot["model"], parsed["usage"]["promptTokenCount"], parsed["usage"]["candidatesTokenCount"], parsed["usage"]["thoughtsTokenCount"], rates) if parsed else reservation
                cumulative += actual
                if aggregate_pilot_cost(cumulative, historical_total) > V9_PILOT_CEILING:
                    disposition = "rejected"
                    stop_reason = "pilot_ceiling_exceeded"
                    accepted_candidate = accepted_screen = fatal_collision_candidate = None
                    fatal_collision_reason = fatal_collision_screen = schema_error_obj = None
                    candidate_hash = None

                receipt = _receipt(request_sequence, slot, request_hash, raw_hash, http_status, candidate_hash, disposition, stop_reason, card_attempt_number, prior_receipt)
                _append(paths["receipts"], receipt)
                receipts.append(receipt)
                prior_receipt = receipt["row_hash"]
                cost = _cost_row(request_sequence, slot, request_hash, raw_hash, receipt["row_hash"], reservation, actual, cumulative, parsed["usage"] if parsed else None, disposition, stop_reason, rate_hash, prior_cost, historical_total)
                _append(paths["cost"], cost)
                costs.append(cost)
                prior_cost = cost["row_hash"]
                gate2.verify_chain(receipts)
                gate2.verify_chain(costs)

                is_retryable_503 = stop_reason == "unexpected_http_status" and http_status is not None and http_status != 200
                if is_retryable_503 and card_attempt_number < MAX_CARD_ATTEMPTS:
                    continue  # same card, next attempt

                if accepted_candidate is not None:
                    candidate_sequence += 1
                    candidate_row = _candidate_row(candidate_sequence, slot, request_hash, raw_hash, accepted_candidate, accepted_screen, prior_candidate)
                    _append(paths["candidates"], candidate_row)
                    candidates.append(candidate_row)
                    prior_candidate = candidate_row["row_hash"]
                    earlier_candidates.extend(gate2.candidate_fields(candidate_row["candidate"]))
                    gate2.verify_chain(candidates)

                if stop_reason:
                    final_reason = stop_reason
                    if is_retryable_503 and card_attempt_number >= MAX_CARD_ATTEMPTS:
                        final_reason = "unexpected_http_status_retries_exhausted"
                    rejection_sequence += 1
                    diagnostic_hash = None
                    schema_diagnostic_hash = None
                    pending_collision_diagnostic = pending_schema_diagnostic = None

                    if fatal_collision_reason is not None:
                        try:
                            pending_collision_diagnostic = collision_evidence.build_row(
                                rejection_sequence,
                                {"slot": rejection_sequence, "model": slot["model"], "mechanism_id": slot["mechanism_id"]},
                                request_hash,
                                raw_hash,
                                fatal_collision_reason,
                                fatal_collision_screen,
                                reference_labels,
                                (field for field, _text in gate2.candidate_fields(fatal_collision_candidate)),
                                prior_collision_diagnostic,
                            )
                        except collision_evidence.OutputCollisionEvidenceError:
                            final_reason = "output_collision_diagnostic_withheld"
                    if final_reason == "schema_invalid" and schema_error_obj is not None:
                        try:
                            pending_schema_diagnostic = schema_evidence.build_row(rejection_sequence, {"slot": rejection_sequence, "model": slot["model"], "mechanism_id": slot["mechanism_id"]}, request_hash, raw_hash, schema_error_obj, prior_schema_diagnostic)
                        except schema_evidence.SchemaConformanceEvidenceError:
                            final_reason = "schema_conformance_diagnostic_withheld"

                    diagnostic_hash = pending_collision_diagnostic["row_hash"] if pending_collision_diagnostic is not None else None
                    schema_diagnostic_hash = pending_schema_diagnostic["row_hash"] if pending_schema_diagnostic is not None else None
                    rejection = _rejection(rejection_sequence, request_hash, raw_hash, final_reason, diagnostic_hash, prior_rejection, schema_diagnostic_hash)
                    _append(paths["rejections"], rejection)
                    rejections.append(rejection)
                    prior_rejection = rejection["row_hash"]
                    gate2.verify_chain(rejections)

                    if pending_collision_diagnostic is not None:
                        try:
                            _append(paths["collision_diagnostics"], pending_collision_diagnostic)
                        except Gate5PilotStop:
                            global_stop = "output_collision_diagnostic_persistence_failed"
                            card_outcome_label = global_stop
                            break
                        collision_diagnostics.append(pending_collision_diagnostic)
                        prior_collision_diagnostic = pending_collision_diagnostic["row_hash"]
                        collision_evidence.verify_chain(
                            collision_diagnostics,
                            reference_labels,
                            collision_evidence.EXPECTED_CANDIDATE_FIELD_PATHS,
                        )
                    if pending_schema_diagnostic is not None:
                        try:
                            _append(paths["schema_diagnostics"], pending_schema_diagnostic)
                        except Gate5PilotStop:
                            global_stop = "schema_conformance_diagnostic_persistence_failed"
                            card_outcome_label = global_stop
                            break
                        schema_diagnostics.append(pending_schema_diagnostic)
                        prior_schema_diagnostic = pending_schema_diagnostic["row_hash"]
                        schema_evidence.verify_chain(schema_diagnostics)
                    if pending_raw_output_diagnostic is not None:
                        raw_output_diagnostic_state = pending_raw_output_diagnostic["state"]
                        if raw_output_diagnostic_state == "persisted":
                            try:
                                private_row = raw_diagnostic.persist(
                                    private_diagnostic_root, request_sequence, final_reason, request_hash, raw_hash or "", rejection["row_hash"], pending_raw_output_diagnostic["text"],
                                )
                                raw_output_diagnostic_record_sha256 = private_row["record_sha256"]
                            except raw_diagnostic.PrivateRawDiagnosticError:
                                raw_output_diagnostic_state = "write_failed"
                                raw_output_diagnostic_record_sha256 = None
                                global_stop = "raw_output_diagnostic_persistence_failed"
                                card_outcome_label = global_stop
                                break

                    card_outcome_label = final_reason
                    if not _outcome_continues_past(final_reason):
                        global_stop = final_reason
                else:
                    card_outcome_label = "accepted"
                break  # this card is resolved; only a retryable 503 loops back above

            if progress is not None:
                progress({
                    "card_index": card_index,
                    "cards_total": len(slots),
                    "mechanism_id": slot["mechanism_id"],
                    "model": slot["model"],
                    "attempts_used": card_attempt_number,
                    "outcome": card_outcome_label,
                })
            if card_outcome_label == "accepted" or (card_outcome_label is not None and _outcome_continues_past(card_outcome_label)):
                cards_completed += 1
    finally:
        secret = None

    if global_stop is None:
        global_stop = "completed_full_schedule"

    summary = {
        "artifact": "gemini_generator_gate5_paid_pilot_v9_summary",
        "cards_completed": cards_completed,
        "cards_total": len(slots),
        "requests_made": len(receipts),
        "candidate_quarantine_count": len(candidates),
        "rejection_count": len(rejections),
        "output_collision_diagnostic_count": len(collision_diagnostics),
        "schema_conformance_diagnostic_count": len(schema_diagnostics),
        "raw_output_diagnostic_state": raw_output_diagnostic_state,
        "raw_output_diagnostic_record_sha256": raw_output_diagnostic_record_sha256,
        "cumulative_actual_usd_millionths": cumulative,
        "original_failed_pilot_actual_usd_millionths": v8.ORIGINAL_FAILED_PILOT_BOOKED_COST,
        "completed_fresh_pilot_actual_usd_millionths": v8.COMPLETED_FRESH_PILOT_BOOKED_COST,
        "historical_pilot_actual_usd_millionths": historical_total,
        "aggregate_pilot_actual_usd_millionths": aggregate_pilot_cost(cumulative, historical_total),
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
            v8._legacy_collision_rejection_view(rejections),
            collision_diagnostics,
            summary,
            reference_labels,
            collision_evidence.EXPECTED_CANDIDATE_FIELD_PATHS,
        )
    if global_stop != "schema_conformance_diagnostic_persistence_failed":
        schema_evidence.validate_rejection_links(rejections, schema_diagnostics, summary)
    summary["summary_sha256"] = gate2.sha256_bytes(gate2.canonical_json_bytes(summary))
    _new_file(paths["summary"], gate2.canonical_json_bytes(summary))
    return summary


def verify_local_build() -> dict[str, Any]:
    """Exercise all frozen request construction with no credential, file output, or network."""
    slots = load_schedule()
    hashes = [gate2.sha256_bytes(gate2.canonical_json_bytes(v8.v7_prompt.build_request(slot))) for slot in slots]
    success_row = verify_successful_diagnostic_evidence()
    flash_lite_success_row = verify_successful_flash_lite_evidence()
    fresh_evidence = verify_fresh_attempt_evidence()
    third_evidence = verify_third_attempt_evidence()
    historical_slot_one, historical_slot_two = _historical_m01_slots()
    live_request_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(v8.redesign.build_request(historical_slot_one)))
    flash_lite_request_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(v8.redesign.build_request(historical_slot_two)))
    if live_request_hash != execution_gate.EXPECTED_LIVE_REQUEST_SHA256 or flash_lite_request_hash != execution_gate.EXPECTED_FLASH_LITE_REQUEST_SHA256:
        raise Gate5PilotStop("historical_envelope_mismatch")
    return {
        "artifact": "gemini_generator_gate5_paid_pilot_v9_engine_verify_only",
        "contract_sha256": canonical_hash(v8.CONTRACT_PATH),
        "provider_schema_sha256": canonical_hash(v8.PROVIDER_SCHEMA_PATH),
        "live_validated_request_envelope_sha256": live_request_hash,
        "successful_diagnostic_receipt_row_sha256": success_row,
        "flash_lite_live_validated_request_envelope_sha256": flash_lite_request_hash,
        "successful_flash_lite_receipt_row_sha256": flash_lite_success_row,
        **fresh_evidence,
        **third_evidence,
        "original_failed_pilot_booked_cost_usd_millionths": v8.ORIGINAL_FAILED_PILOT_BOOKED_COST,
        "completed_fresh_pilot_booked_cost_usd_millionths": v8.COMPLETED_FRESH_PILOT_BOOKED_COST,
        "v9_reused_v8_schedule_sha256": canonical_hash(v8.SCHEDULE_PATH),
        "v9_first_request_sha256": hashes[0],
        "v9_request_count": len(hashes),
        "v9_unique_request_count": len(set(hashes)),
        "max_card_attempts": MAX_CARD_ATTEMPTS,
        "network_used": False,
        "credential_read": False,
        "file_output_created": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if not args.verify_only:
        parser.error("--verify-only is required; V9 execution is available only through the campaign runner")
    print(json.dumps(verify_local_build(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
