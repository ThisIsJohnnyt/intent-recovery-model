from __future__ import annotations

import json
import shutil
import sys
import tempfile
import threading
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate2
import gate5_paid_pilot_retry_campaign_v2_gate as gate
import gate5_paid_pilot_retry_campaign_v2_runner as runner
import gate5_paid_pilot_retry_campaign_runner as v1
import gate5_paid_pilot_runner as pilot

PACKAGE = Path(__file__).resolve().parent


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_bytes(b"".join(gate2.canonical_json_bytes(row) for row in rows))


class PaidPilotRetryCampaignV2Tests(unittest.TestCase):
    def attestation(self, root: Path, authorized: bool = True) -> Path:
        value = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v2_attestation_template.json")
        value["execution_date"] = date.today().isoformat()
        value["execution_day_rate_snapshot_status"] = "execution_day_verified"
        value["positive_prepaid_balance_usd_millionths"] = 10_000_000
        for field in gate.TRUE_FIELDS:
            value[field] = True
        value["v2_campaign_execution_authorized_by_johnny"] = authorized
        path = root / "v2-attestation.json"
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
        rejections = [gate2.chained_row({"sequence": 1, "reason_code": stop}, None)] if stop else []
        candidates = [gate2.chained_row({"sequence": 1, "candidate": {"private": "synthetic"}}, None)] if candidate_count else []
        (output / "pilot_reservation.json").write_bytes(gate2.canonical_json_bytes({"artifact": "synthetic"}))
        write_jsonl(output / "request_receipts.jsonl", [receipt])
        write_jsonl(output / "cost_ledger.jsonl", [cost])
        write_jsonl(output / "rejection_ledger.jsonl", rejections)
        write_jsonl(output / "candidate_quarantine.jsonl", candidates)
        summary = {
            "artifact": "gemini_generator_gate5_paid_pilot_summary",
            "completed_slots": completed,
            "candidate_quarantine_count": candidate_count,
            "rejection_count": len(rejections),
            "cumulative_actual_usd_millionths": 10_680,
            **context,
            "aggregate_pilot_actual_usd_millionths": context["historical_pilot_actual_usd_millionths"] + 10_680,
            "global_stop": stop,
            "network_used": True,
            "credential_read": True,
            "candidate_review_performed": False,
            "corpus_mutation_performed": False,
            "receipt_chain_head": receipt["row_hash"],
            "rejection_chain_head": rejections[-1]["row_hash"] if rejections else None,
            "cost_chain_head": cost["row_hash"],
            "candidate_chain_head": candidates[-1]["row_hash"] if candidates else None,
        }
        summary["summary_sha256"] = gate2.sha256_bytes(gate2.canonical_json_bytes(summary))
        (output / "run_summary.json").write_bytes(gate2.canonical_json_bytes(summary))
        return summary

    def execute_fake(self, campaign: Path, attestation: Path, outcome: str) -> dict:
        def fake_execute(_loader, _target, _transport, _attestation, _rates, output, historical_components=None, attestation_validator=None, attested_prior_pilot_booked_cost_usd_millionths=None):
            self.assertEqual(attested_prior_pilot_booked_cost_usd_millionths, 32_040)
            return self.fake_output(output, historical_components, outcome)
        with patch.object(pilot, "execute_pilot", side_effect=fake_execute):
            return runner.execute_once(lambda _: "secret", "label", object(), attestation, PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-16.json", campaign)

    def test_verify_only_and_gate_are_local_and_separately_authorized(self) -> None:
        result = runner.verify_only()
        self.assertEqual(result["initial_component_count"], 5)
        self.assertEqual(result["initial_historical_cost_usd_millionths"], 42_720)
        self.assertEqual(result["attested_baseline_usd_millionths"], 32_040)
        self.assertEqual(result["maximum_campaign_attempts"], 8)
        self.assertEqual(result["worst_case_aggregate_usd_millionths"], 1_674_720)
        self.assertFalse(result["network_used"] or result["credential_read"] or result["file_output_created"])
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            with self.assertRaisesRegex(gate.Gate5PaidPilotRetryCampaignV2AttestationError, "unconfirmed"):
                gate.validate_attestation(self.attestation(Path(temp), False))

    def test_v1_is_terminal_and_rederived_as_five_component_prefix(self) -> None:
        components = runner.initial_components()
        context = pilot.validate_historical_components(components)
        self.assertEqual(context, {"historical_pilot_component_count": 5, "historical_pilot_components_sha256": gate.INITIAL_COMPONENT_MANIFEST_SHA256, "historical_pilot_actual_usd_millionths": 42_720})
        self.assertEqual([item["booked_cost_usd_millionths"] for item in components], [10_680, 10_680, 10_680, 10_680, 0])
        with self.assertRaisesRegex(v1.Gate5PaidPilotRetryCampaignStop, "campaign_already_terminal"):
            v1.reserve_attempt(v1.PACKAGE / "gate5_paid_pilot_retry_campaign_2026-08-16", v1.canonical_hash(v1.PACKAGE / "gate5_paid_pilot_retry_campaign_attestation_2026-08-16.json"))

    def test_real_engine_uses_frozen_baseline_but_live_total_for_money(self) -> None:
        class Transport:
            def __init__(self): self.calls = 0
            def post(self, *_args, **_kwargs):
                self.calls += 1
                return pilot.ProviderResponse(503, {}, b'{"error":{"message":"temporary"}}')
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); attestation = self.attestation(root); campaign = root / "v2-campaign"; transport = Transport()
            result = runner.execute_once(lambda _: "local-test-secret", "label", transport, attestation, PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-16.json", campaign)
            self.assertEqual(transport.calls, 1)
            self.assertEqual(result["campaign_state_after"], "active_after_clean_503")
            summary = gate2.load_json(campaign / "attempt_001_pilot_output" / "run_summary.json")
            self.assertEqual(summary["historical_pilot_actual_usd_millionths"], 42_720)
            self.assertEqual(summary["aggregate_pilot_actual_usd_millionths"], 53_400)
            reservation = gate2.load_json(campaign / "attempt_001_pilot_output" / "pilot_reservation.json")
            self.assertEqual(reservation["historical_pilot_actual_usd_millionths"], 42_720)

    def test_invalid_or_mismatched_attested_baseline_stops_before_credential(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); attestation = self.attestation(root); calls = []
            for invalid in (-1, 42_721, True):
                with self.subTest(invalid=invalid), self.assertRaisesRegex(pilot.Gate5PilotStop, "attested_historical_baseline_invalid"):
                    pilot.execute_pilot(lambda _: calls.append("credential"), "label", object(), attestation, PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-16.json", root / f"output-{invalid}", historical_components=runner.initial_components(), attestation_validator=gate.validate_attestation, attested_prior_pilot_booked_cost_usd_millionths=invalid)
            value = gate2.load_json(attestation); value["prior_pilot_booked_cost_usd_millionths"] = 42_720; attestation.write_bytes(gate2.canonical_json_bytes(value))
            with self.assertRaises(pilot.Gate5PilotStop):
                pilot.execute_pilot(lambda _: calls.append("credential"), "label", object(), attestation, PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-16.json", root / "mismatch", historical_components=runner.initial_components(), attestation_validator=gate.validate_attestation, attested_prior_pilot_booked_cost_usd_millionths=32_040)
            self.assertEqual(calls, [])

    def test_v1_evidence_tampering_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            copied = Path(temp) / "v1"; shutil.copytree(runner.V1_DIRECTORY, copied)
            completion = copied / "attempt_002_completion.json"
            value = gate2.load_json(completion); value["global_stop"] = "different"; value["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes({k: v for k, v in value.items() if k != "row_hash"})); completion.write_bytes(gate2.canonical_json_bytes(value))
            with patch.object(runner, "V1_DIRECTORY", copied), self.assertRaises(runner.Gate5PaidPilotRetryCampaignV2Stop):
                runner.verify_initial_evidence()

    def test_clean_503_continues_and_eighth_reaches_cap(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); attestation = self.attestation(root); campaign = root / "campaign"
            for sequence in range(1, 9):
                result = self.execute_fake(campaign, attestation, "503")
                self.assertEqual(result["sequence"], sequence)
                self.assertEqual(result["component"]["attempt_id"], f"campaign_v2_attempt_{sequence:03d}")
            self.assertEqual(result["campaign_state_after"], "attempt_cap_reached")
            with self.assertRaisesRegex(runner.Gate5PaidPilotRetryCampaignV2Stop, "campaign_already_terminal"):
                runner.reserve_attempt(campaign, runner.canonical_hash(attestation))

    def test_every_non_clean_503_outcome_is_terminal(self) -> None:
        for outcome in ("400", "collision", "candidate", "complete"):
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
                root = Path(temp); attestation = self.attestation(root); campaign = root / "campaign"
                result = self.execute_fake(campaign, attestation, outcome)
                self.assertIn(result["campaign_state_after"], runner.TERMINAL_STATES)

    def test_relative_paths_and_recovery_remain_valid(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); attestation = self.attestation(root); campaign = root / "campaign"; digest = runner.canonical_hash(attestation)
            runner.initialize_campaign(campaign, digest); _, components = runner.reserve_attempt(campaign, digest); self.fake_output(campaign / "attempt_001_pilot_output", components, "503")
            rel_attestation = attestation.relative_to(gate2.ROOT); rel_campaign = campaign.relative_to(gate2.ROOT)
            with patch.object(sys, "argv", ["runner", "--recover-incomplete", "--attestation", str(rel_attestation), "--campaign-directory", str(rel_campaign)]), patch("builtins.print"):
                self.assertEqual(runner.main(), 0)
            rows, _ = runner.load_and_verify_campaign(rel_campaign, runner.canonical_hash(rel_attestation))
            self.assertEqual(rows[-1]["campaign_state"], "active_after_clean_503")

    def test_concurrent_reservations_have_one_winner(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); attestation = self.attestation(root); campaign = root / "campaign"; digest = runner.canonical_hash(attestation); runner.initialize_campaign(campaign, digest)
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
            self.assertEqual(sum(isinstance(item, runner.Gate5PaidPilotRetryCampaignV2Stop) for item in outcomes), 1)


if __name__ == "__main__":
    unittest.main()
