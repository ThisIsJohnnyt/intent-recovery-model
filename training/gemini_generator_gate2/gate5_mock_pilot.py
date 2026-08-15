"""In-memory, mock-only Gate 5 sequential pilot control plane.

No provider transport, credential read, file output, candidate review, or corpus
mutation exists here.  This code validates only the reservation/receipt/ledger
ordering that a later separately reviewed execution runner must preserve.
"""

from __future__ import annotations

from typing import Any

import gate2
import gate5_mock_runner as mock
import gate5_redesign as redesign


PACKAGE = gate2.PACKAGE
RECONCILIATION_STOP = 2_250_000
PILOT_CEILING = 3_000_000


class Gate5PilotMockError(RuntimeError):
    pass


def load_schedule() -> list[dict[str, Any]]:
    schedule = gate2.load_json(PACKAGE / "schedule.json")
    slots = schedule.get("slots") if isinstance(schedule, dict) else None
    if not isinstance(slots, list) or len(slots) != 24:
        raise Gate5PilotMockError("frozen schedule unavailable")
    if [slot.get("slot") for slot in slots] != list(range(1, 25)):
        raise Gate5PilotMockError("schedule order drifted")
    return slots


def make_receipt(sequence: int, slot: dict[str, Any], request: dict[str, Any], fixture_id: str, result: dict[str, Any], prior: str | None) -> dict[str, Any]:
    payload = {
        "artifact": "gemini_generator_gate5_mock_request_receipt",
        "sequence": sequence,
        "schedule_slot": slot["slot"],
        "model": slot["model"],
        "mechanism_id": slot["mechanism_id"],
        "request_hash": gate2.sha256_bytes(gate2.canonical_json_bytes(request)),
        "prompt_hash": slot["prompt_hash"],
        "fixture_id": fixture_id,
        "network_used": False,
        "credential_read": False,
        "candidate_reviewed": False,
        "corpus_mutated": False,
        "disposition": result["disposition"],
        "stop_reason": result["stop_reason"],
        "parsed_candidate_hash": result["parsed"]["candidate_payload_hash"] if result["parsed"] else None,
    }
    return gate2.chained_row(payload, prior)


def make_cost_row(
    sequence: int,
    slot: dict[str, Any],
    request_hash: str,
    receipt_hash: str,
    result: dict[str, Any],
    reservation: int,
    cumulative_actual: int,
    prior: str | None,
) -> tuple[dict[str, Any], int, bool]:
    """Return ledger row, updated cumulative charge, and whether the pilot must stop."""
    if result["parsed"] is None:
        actual = reservation
        usage: dict[str, int] | None = None
        stop = True
        reason = result["stop_reason"] or "budget_or_usage_unknown"
    else:
        usage = result["parsed"]["usage"]
        actual = gate2.calculate_cost(
            slot["model"], usage["promptTokenCount"], usage["candidatesTokenCount"], usage["thoughtsTokenCount"], gate2.load_json(gate2.RATE_PATH),
        )
        stop = False
        reason = None
    updated_cumulative = cumulative_actual + actual
    if updated_cumulative > PILOT_CEILING:
        raise Gate5PilotMockError("pilot ceiling exceeded")
    payload = {
        "artifact": "gemini_generator_gate5_mock_cost_ledger_row",
        "sequence": sequence,
        "schedule_slot": slot["slot"],
        "model": slot["model"],
        "mechanism_id": slot["mechanism_id"],
        "reserved_usd_millionths": reservation,
        "actual_usd_millionths": actual,
        "cumulative_actual_usd_millionths": updated_cumulative,
        "outstanding_reservations_usd_millionths": 0,
        "request_hash": request_hash,
        "receipt_hash": receipt_hash,
        "usage": usage,
        "disposition": result["disposition"],
        "stop_reason": reason,
        "network_used": False,
        "credential_read": False,
        "corpus_mutated": False,
    }
    return gate2.chained_row(payload, prior), updated_cumulative, stop


def run_mock_pilot(fixture_ids: list[str]) -> dict[str, Any]:
    """Run at most the supplied fixture count, stopping at the first global failure."""
    slots = load_schedule()
    if not fixture_ids or len(fixture_ids) > len(slots):
        raise Gate5PilotMockError("fixture count must be in 1..24")
    rates = gate2.load_json(gate2.RATE_PATH)
    receipts: list[dict[str, Any]] = []
    ledger: list[dict[str, Any]] = []
    prior_receipt = prior_ledger = None
    cumulative = 0
    seen_candidate_hashes: set[str] = set()
    global_stop = None
    for sequence, (slot, fixture_id) in enumerate(zip(slots, fixture_ids), 1):
        request = redesign.build_request(slot)
        reservation = gate2.reservation_cost(slot["model"], rates)
        if cumulative + reservation > RECONCILIATION_STOP:
            global_stop = "reconciliation_stop_before_request"
            break
        result = mock.run_mock_slot(slot, fixture_id)
        if result["parsed"] and result["parsed"]["candidate_payload_hash"] in seen_candidate_hashes:
            result = {**result, "disposition": "stopped", "stop_reason": "pilot_duplicate", "parsed": None}
        receipt = make_receipt(sequence, slot, request, fixture_id, result, prior_receipt)
        receipts.append(receipt)
        prior_receipt = receipt["row_hash"]
        cost_row, cumulative, must_stop = make_cost_row(sequence, slot, receipt["request_hash"], receipt["row_hash"], result, reservation, cumulative, prior_ledger)
        ledger.append(cost_row)
        prior_ledger = cost_row["row_hash"]
        gate2.verify_chain(receipts)
        gate2.verify_chain(ledger)
        if result["parsed"]:
            seen_candidate_hashes.add(result["parsed"]["candidate_payload_hash"])
        if must_stop:
            global_stop = cost_row["stop_reason"]
            break
    result = {
        "artifact": "gemini_generator_gate5_mock_pilot",
        "network_used": False,
        "credential_read": False,
        "candidate_reviewed": False,
        "corpus_mutated": False,
        "requested_slots": len(fixture_ids),
        "completed_slots": len(receipts),
        "global_stop": global_stop,
        "cumulative_actual_usd_millionths": cumulative,
        "receipts": receipts,
        "cost_ledger": ledger,
    }
    validate_pilot_result(result)
    return result


def validate_pilot_result(result: dict[str, Any]) -> None:
    """Validate complete mock receipt/ledger semantics in addition to row hashes."""
    expected_result = {
        "artifact", "network_used", "credential_read", "candidate_reviewed", "corpus_mutated",
        "requested_slots", "completed_slots", "global_stop", "cumulative_actual_usd_millionths",
        "receipts", "cost_ledger",
    }
    if not isinstance(result, dict) or set(result) != expected_result:
        raise Gate5PilotMockError("pilot result fields drifted")
    if result["artifact"] != "gemini_generator_gate5_mock_pilot":
        raise Gate5PilotMockError("pilot result artifact drifted")
    if any(result[field] is not False for field in ("network_used", "credential_read", "candidate_reviewed", "corpus_mutated")):
        raise Gate5PilotMockError("mock safety field drifted")
    receipts, ledger = result["receipts"], result["cost_ledger"]
    if not isinstance(receipts, list) or not isinstance(ledger, list) or len(receipts) != len(ledger) or result["completed_slots"] != len(receipts):
        raise Gate5PilotMockError("receipt and ledger cardinality drifted")
    gate2.verify_chain(receipts)
    gate2.verify_chain(ledger)
    receipt_fields = {
        "artifact", "sequence", "schedule_slot", "model", "mechanism_id", "request_hash", "prompt_hash",
        "fixture_id", "network_used", "credential_read", "candidate_reviewed", "corpus_mutated",
        "disposition", "stop_reason", "parsed_candidate_hash", "prior_row_hash", "row_hash",
    }
    ledger_fields = {
        "artifact", "sequence", "schedule_slot", "model", "mechanism_id", "reserved_usd_millionths",
        "actual_usd_millionths", "cumulative_actual_usd_millionths", "outstanding_reservations_usd_millionths",
        "request_hash", "receipt_hash", "usage", "disposition", "stop_reason", "network_used",
        "credential_read", "corpus_mutated", "prior_row_hash", "row_hash",
    }
    if result["cumulative_actual_usd_millionths"] != (ledger[-1]["cumulative_actual_usd_millionths"] if ledger else 0):
        raise Gate5PilotMockError("cumulative total drifted")
    for receipt, cost in zip(receipts, ledger):
        if set(receipt) != receipt_fields or set(cost) != ledger_fields:
            raise Gate5PilotMockError("receipt or ledger fields drifted")
        if receipt["artifact"] != "gemini_generator_gate5_mock_request_receipt" or cost["artifact"] != "gemini_generator_gate5_mock_cost_ledger_row":
            raise Gate5PilotMockError("receipt or ledger artifact drifted")
        if receipt["sequence"] != cost["sequence"] or receipt["schedule_slot"] != cost["schedule_slot"]:
            raise Gate5PilotMockError("receipt ledger slot mismatch")
        if receipt["request_hash"] != cost["request_hash"] or receipt["row_hash"] != cost["receipt_hash"]:
            raise Gate5PilotMockError("receipt ledger hash linkage drifted")
        if receipt["network_used"] is not False or receipt["credential_read"] is not False or receipt["candidate_reviewed"] is not False or receipt["corpus_mutated"] is not False or cost["network_used"] is not False or cost["credential_read"] is not False or cost["corpus_mutated"] is not False:
            raise Gate5PilotMockError("row safety field drifted")
        if cost["reserved_usd_millionths"] < 0 or cost["actual_usd_millionths"] < 0 or cost["actual_usd_millionths"] > PILOT_CEILING:
            raise Gate5PilotMockError("row cost bounds drifted")
