from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate2
import gate5_paid_pilot_retry_campaign_gate as gate
import gate5_paid_pilot_retry_campaign_runner as runner
import gate5_paid_pilot_runner as pilot

PACKAGE = Path(__file__).resolve().parent


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_bytes(b"".join(gate2.canonical_json_bytes(row) for row in rows))


class PaidPilotRetryCampaignTests(unittest.TestCase):
    def attestation(self, root: Path, authorized: bool = True) -> Path:
        value = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_attestation_template.json")
        value["execution_date"] = date.today().isoformat()
        value["execution_day_rate_snapshot_status"] = "execution_day_verified"
        value["positive_prepaid_balance_usd_millionths"] = 10_000_000
        for field in gate.TRUE_FIELDS:
            value[field] = True
        value["campaign_execution_authorized_by_johnny"] = authorized
        path = root / "attestation.json"
        path.write_bytes(gate2.canonical_json_bytes(value))
        return path

    def fake_output(self, output: Path, components: list[dict], outcome: str) -> dict:
        output.mkdir()
        context = pilot.validate_historical_components(components)
        status = 503 if outcome == "503" else 400 if outcome == "400" else 200
        stop = "unexpected_http_status" if outcome in {"503", "400"} else "proposed_output:output.bullets:02:protected_collision" if outcome == "collision" else None
        candidate_count = 1 if outcome == "candidate" else 0
        completed = 24 if outcome == "complete" else 1
        receipt = gate2.chained_row({"sequence": 1, "http_status": status, "stop_reason": stop}, None)
        cost = gate2.chained_row({"sequence": 1, "actual_usd_millionths": 10_680}, None)
        rejection_rows = [gate2.chained_row({"sequence": 1, "reason_code": stop}, None)] if stop else []
        candidate_rows = [gate2.chained_row({"sequence": 1, "candidate": {"private": "synthetic"}}, None)] if candidate_count else []
        (output / "pilot_reservation.json").write_bytes(gate2.canonical_json_bytes({"artifact": "synthetic"}))
        write_jsonl(output / "request_receipts.jsonl", [receipt])
        write_jsonl(output / "cost_ledger.jsonl", [cost])
        write_jsonl(output / "rejection_ledger.jsonl", rejection_rows)
        write_jsonl(output / "candidate_quarantine.jsonl", candidate_rows)
        summary = {"artifact": "gemini_generator_gate5_paid_pilot_summary", "completed_slots": completed, "candidate_quarantine_count": candidate_count, "rejection_count": len(rejection_rows), "cumulative_actual_usd_millionths": 10_680, **context, "aggregate_pilot_actual_usd_millionths": context["historical_pilot_actual_usd_millionths"] + 10_680, "global_stop": stop, "network_used": True, "credential_read": True, "candidate_review_performed": False, "corpus_mutation_performed": False, "receipt_chain_head": receipt["row_hash"], "rejection_chain_head": rejection_rows[-1]["row_hash"] if rejection_rows else None, "cost_chain_head": cost["row_hash"], "candidate_chain_head": candidate_rows[-1]["row_hash"] if candidate_rows else None}
        summary["summary_sha256"] = gate2.sha256_bytes(gate2.canonical_json_bytes(summary))
        (output / "run_summary.json").write_bytes(gate2.canonical_json_bytes(summary))
        return summary

    def execute(self, campaign: Path, attestation: Path, outcome: str) -> dict:
        def fake_execute(_loader, _target, _transport, _attestation, _rates, output, historical_components=None, attestation_validator=None):
            assert historical_components is not None
            return self.fake_output(output, historical_components, outcome)
        with patch.object(pilot, "execute_pilot", side_effect=fake_execute):
            return runner.execute_once(lambda _: "secret", "label", object(), attestation, PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-16.json", campaign)

    def test_verify_only_and_gate_are_local_and_separately_authorized(self) -> None:
        value = runner.verify_only()
        self.assertEqual(value["initial_historical_cost_usd_millionths"], 32_040)
        self.assertEqual(value["maximum_campaign_attempts"], 10)
        self.assertEqual(value["worst_case_aggregate_usd_millionths"], 2_072_040)
        self.assertFalse(value["network_used"] or value["credential_read"] or value["file_output_created"])
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            with self.assertRaisesRegex(gate.Gate5PaidPilotRetryCampaignAttestationError, "unconfirmed"):
                gate.validate_attestation(self.attestation(Path(temp), False))

    def test_manifest_rejects_drop_reorder_duplicate_and_rehashed_cost_tampering(self) -> None:
        components = runner.initial_components()
        for changed in ([*components[1:]], [components[1], components[0], components[2]], [components[0], components[1], components[1]]):
            with self.assertRaisesRegex(pilot.Gate5PilotStop, "historical_component_manifest_invalid"):
                pilot.validate_historical_components(changed)
        changed = json.loads(json.dumps(components))
        changed[1]["booked_cost_usd_millionths"] = 1
        changed[1]["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes({k: v for k, v in changed[1].items() if k != "row_hash"}))
        with self.assertRaisesRegex(pilot.Gate5PilotStop, "historical_component_manifest_invalid"):
            pilot.validate_historical_components(changed)

    def test_clean_503_continues_but_collision_and_other_status_are_terminal(self) -> None:
        for terminal in ("collision", "400", "candidate", "complete"):
            with self.subTest(terminal), tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
                root = Path(temp); attestation = self.attestation(root); campaign = root / "campaign"
                first = self.execute(campaign, attestation, "503")
                self.assertEqual(first["campaign_state_after"], "active_after_clean_503")
                second = self.execute(campaign, attestation, terminal)
                self.assertIn(second["campaign_state_after"], runner.TERMINAL_STATES)
                reads = []
                with self.assertRaisesRegex(runner.Gate5PaidPilotRetryCampaignStop, "campaign_already_terminal"):
                    runner.reserve_attempt(campaign, runner.canonical_hash(attestation))
                self.assertEqual(reads, [])

    def test_tenth_clean_503_reaches_cap(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); attestation = self.attestation(root); campaign = root / "campaign"
            for sequence in range(1, 11):
                result = self.execute(campaign, attestation, "503")
                self.assertEqual(result["sequence"], sequence)
            self.assertEqual(result["campaign_state_after"], "attempt_cap_reached")
            with self.assertRaisesRegex(runner.Gate5PaidPilotRetryCampaignStop, "campaign_already_terminal"):
                runner.reserve_attempt(campaign, runner.canonical_hash(attestation))

    def test_incomplete_attempt_and_output_tampering_block(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); attestation = self.attestation(root); campaign = root / "campaign"; digest = runner.canonical_hash(attestation)
            runner.initialize_campaign(campaign, digest)
            runner.reserve_attempt(campaign, digest)
            with self.assertRaisesRegex(runner.Gate5PaidPilotRetryCampaignStop, "campaign_incomplete_attempt"):
                runner.reserve_attempt(campaign, digest)
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); attestation = self.attestation(root); campaign = root / "campaign"
            self.execute(campaign, attestation, "503")
            summary = campaign / "attempt_001_pilot_output" / "run_summary.json"
            value = json.loads(summary.read_text(encoding="utf-8")); value["cumulative_actual_usd_millionths"] = 1
            value["summary_sha256"] = gate2.sha256_bytes(gate2.canonical_json_bytes({k: v for k, v in value.items() if k != "summary_sha256"}))
            summary.write_bytes(gate2.canonical_json_bytes(value))
            with self.assertRaisesRegex(runner.Gate5PaidPilotRetryCampaignStop, "campaign_state_invalid"):
                runner.load_and_verify_campaign(campaign, runner.canonical_hash(attestation))

    def test_recovery_rederives_clean_503_without_credential_or_transport(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); attestation = self.attestation(root); campaign = root / "campaign"; digest = runner.canonical_hash(attestation)
            runner.initialize_campaign(campaign, digest)
            sequence, components = runner.reserve_attempt(campaign, digest)
            self.fake_output(campaign / "attempt_001_pilot_output", components, "503")
            with patch.object(pilot, "execute_pilot", side_effect=AssertionError("recovery must not execute provider transport")) as execute:
                result = runner.recover_incomplete_attempt(attestation, campaign)
            execute.assert_not_called()
            self.assertEqual(sequence, 1)
            self.assertEqual(result["campaign_state_after"], "active_after_clean_503")
            rows, recovered_components = runner.load_and_verify_campaign(campaign, digest)
            self.assertEqual([row["event"] for row in rows], ["campaign_authorized", "attempt_reserved", "attempt_completed"])
            self.assertEqual(len(recovered_components), 4)

    def test_relative_cli_paths_recover_and_future_execution_paths_validate(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); attestation = self.attestation(root); campaign = root / "campaign"; digest = runner.canonical_hash(attestation)
            runner.initialize_campaign(campaign, digest)
            _, components = runner.reserve_attempt(campaign, digest)
            self.fake_output(campaign / "attempt_001_pilot_output", components, "503")
            relative_attestation = attestation.relative_to(gate2.ROOT)
            relative_campaign = campaign.relative_to(gate2.ROOT)
            with patch.object(sys, "argv", ["runner", "--recover-incomplete", "--attestation", str(relative_attestation), "--campaign-directory", str(relative_campaign)]), patch("builtins.print") as printed:
                self.assertEqual(runner.main(), 0)
            self.assertIn('"recovered_from_existing_evidence": true', printed.call_args.args[0])
            runner.load_and_verify_campaign(relative_campaign, runner.canonical_hash(relative_attestation))

        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); attestation = self.attestation(root); campaign = root / "campaign"
            relative_attestation = attestation.relative_to(gate2.ROOT)
            relative_campaign = campaign.relative_to(gate2.ROOT)
            result = self.execute(relative_campaign, relative_attestation, "503")
            self.assertEqual(result["campaign_state_after"], "active_after_clean_503")
            runner.load_and_verify_campaign(relative_campaign, runner.canonical_hash(relative_attestation))

    def test_recovery_rejects_invalid_or_already_completed_evidence(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); attestation = self.attestation(root); campaign = root / "campaign"; digest = runner.canonical_hash(attestation)
            runner.initialize_campaign(campaign, digest)
            with self.assertRaisesRegex(runner.Gate5PaidPilotRetryCampaignStop, "no_incomplete_attempt_to_recover"):
                runner.recover_incomplete_attempt(attestation, campaign)
            _, components = runner.reserve_attempt(campaign, digest)
            self.fake_output(campaign / "attempt_001_pilot_output", components, "503")
            summary_path = campaign / "attempt_001_pilot_output" / "run_summary.json"
            summary = gate2.load_json(summary_path)
            summary["cumulative_actual_usd_millionths"] = 1
            summary["summary_sha256"] = gate2.sha256_bytes(gate2.canonical_json_bytes({k: v for k, v in summary.items() if k != "summary_sha256"}))
            summary_path.write_bytes(gate2.canonical_json_bytes(summary))
            with self.assertRaisesRegex(runner.Gate5PaidPilotRetryCampaignStop, "recovery_evidence_invalid"):
                runner.recover_incomplete_attempt(attestation, campaign)

    def test_zero_request_local_failure_is_evidenced_and_terminal(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); attestation = self.attestation(root); campaign = root / "campaign"
            with patch.object(pilot, "execute_pilot", side_effect=pilot.Gate5PilotStop("credential_unavailable")):
                result = runner.execute_once(lambda _: "unused", "label", object(), attestation, PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-16.json", campaign)
            self.assertEqual(result["completion_kind"], "zero_request_local_failure")
            self.assertEqual(result["booked_cost_usd_millionths"], 0)
            self.assertEqual(result["campaign_state_after"], "stopped_nonretryable_outcome")
            runner.load_and_verify_campaign(campaign, runner.canonical_hash(attestation))
            with self.assertRaisesRegex(runner.Gate5PaidPilotRetryCampaignStop, "campaign_already_terminal"):
                runner.reserve_attempt(campaign, runner.canonical_hash(attestation))

    def test_real_engine_adapter_uses_three_component_cost_and_clean_503_predicate(self) -> None:
        class Transport:
            def __init__(self): self.calls = 0
            def post(self, *_args, **_kwargs):
                self.calls += 1
                return pilot.ProviderResponse(503, {}, b'{"error":{"message":"temporary"}}')
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); attestation = self.attestation(root); campaign = root / "campaign"; transport = Transport()
            result = runner.execute_once(lambda _: "local-test-secret", "label", transport, attestation, PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-16.json", campaign)
            self.assertEqual(transport.calls, 1)
            self.assertEqual(result["campaign_state_after"], "active_after_clean_503")
            summary = gate2.load_json(campaign / "attempt_001_pilot_output" / "run_summary.json")
            self.assertEqual(summary["historical_pilot_component_count"], 3)
            self.assertEqual(summary["historical_pilot_actual_usd_millionths"], 32_040)
            self.assertEqual(summary["aggregate_pilot_actual_usd_millionths"], 42_720)

    def test_concurrent_full_invocation_cannot_both_reach_engine(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); attestation = self.attestation(root); campaign = root / "campaign"
            entered = threading.Event(); release = threading.Event(); calls = []
            def blocking_execute(_loader, _target, _transport, _attestation, _rates, output, historical_components=None, attestation_validator=None):
                calls.append(output.name); entered.set(); release.wait(5)
                return self.fake_output(output, historical_components, "503")
            result = []
            def first():
                try:
                    with patch.object(pilot, "execute_pilot", side_effect=blocking_execute):
                        result.append(runner.execute_once(lambda _: "secret", "label", object(), attestation, PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-16.json", campaign))
                except Exception as exc: result.append(exc)
            thread = threading.Thread(target=first); thread.start(); self.assertTrue(entered.wait(5))
            with self.assertRaisesRegex(runner.Gate5PaidPilotRetryCampaignStop, "campaign_incomplete_attempt"):
                runner.execute_once(lambda _: "must-not-run", "label", object(), attestation, PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-16.json", campaign)
            release.set(); thread.join(5)
            self.assertFalse(thread.is_alive()); self.assertEqual(calls, ["attempt_001_pilot_output"]); self.assertEqual(len(result), 1)

    def test_rehashed_state_transition_tampering_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); attestation = self.attestation(root); campaign = root / "campaign"
            self.execute(campaign, attestation, "503")
            ledger = campaign / runner.LEDGER_NAME; rows = runner._read_jsonl(ledger)
            rows[-1]["campaign_state"] = "stopped_completed"
            rows[-1]["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes({k: v for k, v in rows[-1].items() if k != "row_hash"}))
            write_jsonl(ledger, rows)
            with self.assertRaisesRegex(runner.Gate5PaidPilotRetryCampaignStop, "campaign_state_invalid"):
                runner.load_and_verify_campaign(campaign, runner.canonical_hash(attestation))

    def test_two_simultaneous_reservations_have_one_winner(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); attestation = self.attestation(root); campaign = root / "campaign"; digest = runner.canonical_hash(attestation)
            runner.initialize_campaign(campaign, digest)
            barrier = threading.Barrier(2); outcomes = []; original = runner._new_file
            def synchronized(path, data):
                if path.name == "attempt_001_lock.json": barrier.wait(5)
                original(path, data)
            def reserve():
                try: outcomes.append(runner.reserve_attempt(campaign, digest))
                except Exception as exc: outcomes.append(exc)
            with patch.object(runner, "_new_file", side_effect=synchronized):
                a=threading.Thread(target=reserve); b=threading.Thread(target=reserve); a.start(); b.start(); a.join(5); b.join(5)
            self.assertEqual(sum(isinstance(item, tuple) for item in outcomes), 1)
            self.assertEqual(sum(isinstance(item, runner.Gate5PaidPilotRetryCampaignStop) for item in outcomes), 1)

    def test_n_component_cost_boundaries(self) -> None:
        total = pilot.validate_historical_components(runner.initial_components())["historical_pilot_actual_usd_millionths"]
        exact = pilot.RECONCILIATION_STOP - total - 100
        self.assertTrue(pilot.reservation_fits_reconciliation_stop(exact, 100, total))
        self.assertFalse(pilot.reservation_fits_reconciliation_stop(exact + 1, 100, total))
        self.assertEqual(pilot.aggregate_pilot_cost(pilot.PILOT_CEILING - total, total), pilot.PILOT_CEILING)
        self.assertGreater(pilot.aggregate_pilot_cost(pilot.PILOT_CEILING - total + 1, total), pilot.PILOT_CEILING)


if __name__ == "__main__": unittest.main()
