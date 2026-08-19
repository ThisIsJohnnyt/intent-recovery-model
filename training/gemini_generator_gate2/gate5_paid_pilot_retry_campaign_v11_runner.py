"""Local-first V11 full-schedule campaign runner. Single authorized execution
processes the entire 22-card schedule; there is no multi-attempt reservation
or pause/review cycle, same shape as V9/V10. Live progress is printed per
card as the run proceeds. The one behavioral change from V10: candidate
screening uses stopword-filtered token-Jaccard collision scoring."""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Callable

import gate2
import gate4_connectivity_runner as gate4
import gate5_paid_pilot_retry_campaign_v8_runner as v8runner
import gate5_paid_pilot_retry_campaign_v10_runner as v10runner
import gate5_paid_pilot_retry_campaign_v11_gate as campaign_gate
import gate5_paid_pilot_v8_engine as v8_engine
import gate5_paid_pilot_v11_engine as pilot


PACKAGE = Path(__file__).resolve().parent
V10_CAMPAIGN_DIRECTORY = PACKAGE / "gate5_paid_pilot_retry_campaign_v10_2026-08-18_r2"
V10_ATTESTATION = PACKAGE / "gate5_paid_pilot_retry_campaign_v10_attestation_2026-08-18_r2.json"
REFERENCE_RATE_PATH = PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-18.json"
LEDGER_NAME = "campaign_state.jsonl"
CAMPAIGN_DIRECTORY_RE = re.compile(r"gate5_paid_pilot_retry_campaign_v11_(\d{4}-\d{2}-\d{2})(?:_r[2-9])?")
# The exact 8 evidence files V10 r2's real run_output directory wrote, in the
# same order used to build every prior version's historical-component
# evidence hash.
V10_EVIDENCE_FILE_NAMES = ("pilot_reservation.json", "run_summary.json", "request_receipts.jsonl", "cost_ledger.jsonl", "rejection_ledger.jsonl", "output_collision_diagnostics.jsonl", "schema_conformance_diagnostics.jsonl", "candidate_quarantine.jsonl")


class Gate5PaidPilotRetryCampaignV11Stop(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def local_today() -> str:
    return date.today().isoformat()


def canonical_hash(path: Path) -> str:
    try:
        return pilot.canonical_hash(path)
    except Exception as exc:
        raise Gate5PaidPilotRetryCampaignV11Stop("canonical_input_invalid") from exc


def _rate_tuple(path: Path) -> dict[str, Any]:
    try:
        value = gate2.load_json(path)
    except (gate2.Gate2Error, OSError) as exc:
        raise Gate5PaidPilotRetryCampaignV11Stop("execution_day_rate_snapshot_invalid") from exc
    return {"rates": value.get("rates"), "currency": value.get("currency"), "unit": value.get("unit")}


def _file_hash_or_none(path: Path) -> str | None:
    if not path.exists():
        return None
    if path.stat().st_size == 0:
        return gate2.sha256_bytes(path.read_bytes())
    return canonical_hash(path)


def v10_terminal_components() -> list[dict[str, Any]]:
    """Re-derive V9's real 26-component historical list (unchanged, exactly
    as V10 itself used it), independently re-verify V10's own real terminal
    run (the corrected-build r2 attempt that actually completed all 22
    cards), and append V10's real spend as a new chained historical
    component -- the same "each version's real terminal outcome becomes the
    next version's historical component" pattern V9 and V10 both used."""
    v9_components = v10runner.v9_terminal_components()
    rows = v10runner.load_and_verify_campaign(V10_CAMPAIGN_DIRECTORY, canonical_hash(V10_ATTESTATION))
    last = rows[-1]
    if last.get("event") != "run_completed" or last.get("campaign_state") != "completed_full_schedule":
        raise Gate5PaidPilotRetryCampaignV11Stop("v10_terminal_evidence_invalid")
    if canonical_hash(V10_ATTESTATION) != campaign_gate.EXPECTED_V10["v10_final_attestation_sha256"]:
        raise Gate5PaidPilotRetryCampaignV11Stop("v10_terminal_evidence_invalid")
    if canonical_hash(V10_CAMPAIGN_DIRECTORY / LEDGER_NAME) != campaign_gate.EXPECTED_V10["v10_terminal_campaign_ledger_sha256"]:
        raise Gate5PaidPilotRetryCampaignV11Stop("v10_terminal_evidence_invalid")
    if last.get("run_summary_sha256") != campaign_gate.EXPECTED_V10["v10_terminal_run_summary_sha256"] or last.get("row_hash") != campaign_gate.EXPECTED_V10["v10_terminal_state_row_sha256"]:
        raise Gate5PaidPilotRetryCampaignV11Stop("v10_terminal_evidence_invalid")
    if last.get("historical_pilot_components_sha256") != campaign_gate.EXPECTED_V10["v10_terminal_historical_component_manifest_sha256"]:
        raise Gate5PaidPilotRetryCampaignV11Stop("v10_terminal_evidence_invalid")
    output = V10_CAMPAIGN_DIRECTORY / last["output_directory_name"]
    evidence = {name: _file_hash_or_none(output / name) for name in V10_EVIDENCE_FILE_NAMES}
    evidence_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(evidence))
    summary = gate2.load_json(output / "run_summary.json")
    if summary.get("cumulative_actual_usd_millionths") != 405_861 or summary.get("global_stop") != "completed_full_schedule":
        raise Gate5PaidPilotRetryCampaignV11Stop("v10_terminal_evidence_invalid")
    new_component = v8_engine._historical_component(
        len(v9_components) + 1,
        "campaign_v10_full_schedule_2026-08-18_r2",
        summary["cumulative_actual_usd_millionths"],
        evidence_hash,
        "completed_full_schedule",
        v9_components[-1]["row_hash"],
    )
    components = v9_components + [new_component]
    context = pilot.validate_historical_components(components)
    if context["historical_pilot_component_count"] != campaign_gate.INITIAL_COMPONENT_COUNT or context["historical_pilot_components_sha256"] != campaign_gate.INITIAL_COMPONENT_MANIFEST_SHA256 or context["historical_pilot_actual_usd_millionths"] != campaign_gate.ATTESTED_BASELINE_COST:
        raise Gate5PaidPilotRetryCampaignV11Stop("v10_terminal_evidence_invalid")
    return components


def verify_initial_evidence() -> dict[str, Any]:
    return pilot.validate_historical_components(v10_terminal_components())


def verify_only() -> dict[str, Any]:
    context = verify_initial_evidence()
    if context != {
        "historical_pilot_component_count": campaign_gate.INITIAL_COMPONENT_COUNT,
        "historical_pilot_components_sha256": campaign_gate.INITIAL_COMPONENT_MANIFEST_SHA256,
        "historical_pilot_actual_usd_millionths": campaign_gate.ATTESTED_BASELINE_COST,
    }:
        raise Gate5PaidPilotRetryCampaignV11Stop("v10_terminal_evidence_invalid")
    build_hashes = campaign_gate.current_build_hashes()
    rates = gate2.load_json(REFERENCE_RATE_PATH)
    slots = pilot.load_schedule()  # raises if EXPECTED_V11_FIRST_REQUEST_SHA256 / EXPECTED_V8_SCHEDULE_SHA256 drift
    single_pass = sum(gate2.reservation_cost(slot["model"], rates) for slot in slots)
    worst = single_pass * pilot.MAX_CARD_ATTEMPTS
    if single_pass != 187_000 or worst != 935_000 or context["historical_pilot_actual_usd_millionths"] + worst != 1_620_501:
        raise Gate5PaidPilotRetryCampaignV11Stop("campaign_cost_math_invalid")
    return {
        "artifact": "gemini_generator_gate5_paid_pilot_retry_campaign_v11_verify_only",
        **context,
        "single_pass_reservation_usd_millionths": single_pass,
        "worst_case_aggregate_usd_millionths": 1_620_501,
        "max_card_attempts": pilot.MAX_CARD_ATTEMPTS,
        **campaign_gate.EXPECTED_V10,
        **build_hashes,
        "network_used": False,
        "credential_read": False,
        "file_output_created": False,
    }


def _validate_campaign_root(root: Path, execution_date: str) -> None:
    try:
        resolved = root.resolve()
    except OSError as exc:
        raise Gate5PaidPilotRetryCampaignV11Stop("campaign_directory_invalid") from exc
    match = CAMPAIGN_DIRECTORY_RE.fullmatch(resolved.name)
    if resolved.parent != PACKAGE.resolve() or match is None or match.group(1) != execution_date:
        raise Gate5PaidPilotRetryCampaignV11Stop("campaign_directory_invalid")


def _state_row(event: str, sequence: int, state: str, context: dict[str, Any], rate_hash: str, rate_date: str, run_summary_hash: str | None, output_directory_name: str | None, prior: str | None, attestation_hash: str) -> dict[str, Any]:
    row = {
        "artifact": "gemini_generator_gate5_paid_pilot_retry_campaign_v11_state",
        "event": event,
        "sequence": sequence,
        "campaign_state": state,
        **context,
        "effective_rate_snapshot_sha256": rate_hash,
        "effective_rate_date": rate_date,
        "run_summary_sha256": run_summary_hash,
        "output_directory_name": output_directory_name,
        "prior_row_hash": prior,
        "attestation_sha256": attestation_hash,
    }
    row["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(row))
    return row


def _new_file(path: Path, data: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(data)


def _append(path: Path, row: dict[str, Any]) -> None:
    with path.open("ab") as handle:
        handle.write(gate2.canonical_json_bytes(row))


def load_and_verify_campaign(root: Path, attestation_hash: str) -> list[dict[str, Any]]:
    try:
        text = (root / LEDGER_NAME).read_text(encoding="utf-8")
    except OSError as exc:
        raise Gate5PaidPilotRetryCampaignV11Stop("campaign_state_missing") from exc
    rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    if not rows:
        raise Gate5PaidPilotRetryCampaignV11Stop("campaign_state_invalid")
    prior = None
    for sequence, row in enumerate(rows):
        expected = dict(row)
        stored_hash = expected.pop("row_hash", None)
        if row.get("sequence") != sequence or row.get("prior_row_hash") != prior or row.get("attestation_sha256") != attestation_hash:
            raise Gate5PaidPilotRetryCampaignV11Stop("campaign_state_invalid")
        if stored_hash != gate2.sha256_bytes(gate2.canonical_json_bytes(expected)):
            raise Gate5PaidPilotRetryCampaignV11Stop("campaign_state_invalid")
        prior = stored_hash
    return rows


def execute_full_schedule(credential_loader: Callable[[str], str], credential_target: str, transport: Any, attestation_path: Path, rate_path: Path, campaign_root: Path, print_progress: Callable[[dict[str, Any]], None] | None = None) -> dict[str, Any]:
    if campaign_root.exists():
        raise Gate5PaidPilotRetryCampaignV11Stop("campaign_directory_already_exists")
    try:
        attestation = campaign_gate.validate_attestation(attestation_path)
        _validate_campaign_root(campaign_root, attestation["execution_date"])
        verify_only()
        components = v10_terminal_components()
        attestation_hash = canonical_hash(attestation_path)
        rate_hash = canonical_hash(rate_path)
        if rate_hash != attestation["execution_day_rate_snapshot_sha256"]:
            raise Gate5PaidPilotRetryCampaignV11Stop("execution_day_rate_snapshot_mismatch")
    except Exception as exc:
        if isinstance(exc, Gate5PaidPilotRetryCampaignV11Stop):
            raise
        raise Gate5PaidPilotRetryCampaignV11Stop("pre_execution_validation_failed") from exc

    campaign_root.mkdir(parents=False)
    context = pilot.validate_historical_components(components)
    authorized_row = _state_row("campaign_authorized", 0, "authorized_not_started", context, rate_hash, attestation["execution_date"], None, None, None, attestation_hash)
    _new_file(campaign_root / LEDGER_NAME, gate2.canonical_json_bytes(authorized_row))

    output_directory_name = "run_output"
    output = campaign_root / output_directory_name
    private_root = campaign_root / "private_raw_diagnostics"
    try:
        summary = pilot.execute_pilot(
            credential_loader, credential_target, transport, attestation_path, rate_path, output,
            historical_components=components,
            attestation_validator=lambda _p: _v10_style_legacy_attestation(components),
            effective_rate_snapshot_sha256=rate_hash,
            private_diagnostic_root=private_root,
            progress=print_progress,
        )
    except Exception as exc:
        code = exc.code if isinstance(exc, pilot.Gate5PilotStop) else "unexpected_local_error"
        completion_row = _state_row("run_failed_before_evidence", 1, "stopped_nonretryable_outcome", context, rate_hash, attestation["execution_date"], None, None, authorized_row["row_hash"], attestation_hash)
        completion_row["failure_code"] = code
        completion_row["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes({k: v for k, v in completion_row.items() if k != "row_hash"}))
        _append(campaign_root / LEDGER_NAME, completion_row)
        raise Gate5PaidPilotRetryCampaignV11Stop(code) from exc

    run_summary_hash = canonical_hash(output / "run_summary.json")
    final_row = _state_row("run_completed", 1, summary["global_stop"], context, rate_hash, attestation["execution_date"], run_summary_hash, output_directory_name, authorized_row["row_hash"], attestation_hash)
    _append(campaign_root / LEDGER_NAME, final_row)
    load_and_verify_campaign(campaign_root, attestation_hash)
    return {"campaign_state": summary["global_stop"], "output_directory": output_directory_name, "cards_completed": summary["cards_completed"], "cards_total": summary["cards_total"], "aggregate_pilot_actual_usd_millionths": summary["aggregate_pilot_actual_usd_millionths"]}


def _v10_style_legacy_attestation(components: list[dict[str, Any]]) -> dict[str, Any]:
    """Same substitution pattern V8/V9/V10 use: validate the real V11
    attestation (already done by the caller), then expose the
    already-reviewed legacy engine fields the shared execute_pilot()
    pre-flight check requires."""
    value = gate2.load_json(v8runner.ENGINE_ATTESTATION)
    value = dict(value)
    value["prior_pilot_booked_cost_usd_millionths"] = campaign_gate.ATTESTED_BASELINE_COST
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--execute-full-schedule", action="store_true")
    parser.add_argument("--credential-target")
    parser.add_argument("--attestation", type=Path)
    parser.add_argument("--rate-snapshot", type=Path)
    parser.add_argument("--campaign-directory", type=Path)
    args = parser.parse_args()
    if sum((args.verify_only, args.execute_full_schedule)) != 1:
        parser.error("choose exactly one mode")
    try:
        if args.verify_only:
            print(json.dumps(verify_only(), sort_keys=True))
            return 0
        if not all((args.credential_target, args.attestation, args.rate_snapshot, args.campaign_directory)):
            parser.error("--execute-full-schedule requires --credential-target, --attestation, --rate-snapshot, and --campaign-directory")

        def print_progress(event: dict[str, Any]) -> None:
            print(json.dumps({"progress": event}, sort_keys=True), flush=True)

        result = execute_full_schedule(
            gate4.load_windows_generic_credential, args.credential_target, pilot.HTTPSPilotTransport(),
            args.attestation, args.rate_snapshot, args.campaign_directory, print_progress,
        )
        print(json.dumps(result, sort_keys=True))
        return 0
    except Gate5PaidPilotRetryCampaignV11Stop as exc:
        print(json.dumps({"stop": exc.code}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
