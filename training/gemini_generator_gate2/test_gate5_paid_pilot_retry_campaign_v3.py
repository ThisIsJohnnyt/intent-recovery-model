from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import threading
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import gate2
import gate5_output_collision_evidence as collision_evidence
import gate5_paid_pilot_retry_campaign_v2_runner as v2
import gate5_paid_pilot_retry_campaign_v3_gate as gate
import gate5_paid_pilot_retry_campaign_v3_runner as runner
import gate5_paid_pilot_runner as pilot

PACKAGE = Path(__file__).resolve().parent


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_bytes(b"".join(gate2.canonical_json_bytes(row) for row in rows))


class PaidPilotRetryCampaignV3Tests(unittest.TestCase):
    def rate_snapshot(self, root: Path) -> Path:
        value = gate2.load_json(PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-16.json")
        value["observed_date"] = date.today().isoformat()
        path = root / "rates.json"
        path.write_bytes(gate2.canonical_json_bytes(value))
        return path

    def attestation(self, root: Path, rate_path: Path, authorized: bool = True) -> Path:
        value = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v3_attestation_template.json")
        value["execution_date"] = date.today().isoformat()
        value["execution_day_rate_snapshot_status"] = "execution_day_verified"
        value["execution_day_rate_snapshot_sha256"] = runner.canonical_hash(rate_path)
        value["positive_prepaid_balance_usd_millionths"] = 10_000_000
        for field in gate.TRUE_FIELDS:
            value[field] = True
        value["v3_campaign_execution_authorized_by_johnny"] = authorized
        path = root / "v3-attestation.json"
        path.write_bytes(gate2.canonical_json_bytes(value))
        return path

    def diagnostic(self, slot: dict, request_hash: str, raw_hash: str) -> dict:
        label = "acceptance:009:expected_behavior"
        field = "proposed_output:output.narrative"
        screen = {
            "fatal": True,
            "fatal_reasons": [field + collision_evidence.REASON_SUFFIX],
            "fields": [{"field": field, "protected": {
                "fatal": True,
                "reasons": ["never persisted"],
                "structured_reasons": [{"kind": "token_jaccard_threshold", "reference": label, "score": 0.812345}],
                "maximum_token_jaccard": {"reference": label, "score": 0.812345678},
                "maximum_character_5gram_jaccard": {"reference": label, "score": 0.456789012},
            }}],
        }
        return collision_evidence.build_row(1, slot, request_hash, raw_hash, field + collision_evidence.REASON_SUFFIX, screen, [label], [field], None)

    def fake_output(self, output: Path, components: list[dict], outcome: str) -> dict:
        output.mkdir()
        context = pilot.validate_historical_components(components)
        slot = pilot.load_schedule()[0]
        request_hash, raw_hash = "a" * 64, "b" * 64
        status = 503 if outcome == "503" else 400 if outcome == "400" else 200
        protected_reason = "proposed_output:output.narrative:protected_collision"
        stop = "unexpected_http_status" if outcome in {"503", "400"} else protected_reason if outcome == "collision" else "output_collision_diagnostic_persistence_failed" if outcome == "diagnostic_failure" else None
        candidate_count = 1 if outcome == "candidate" else 0
        completed = 24 if outcome == "complete" else 1
        diagnostic = self.diagnostic(slot, request_hash, raw_hash) if outcome == "collision" else None
        diagnostic_hash = diagnostic["row_hash"] if diagnostic else "c" * 64 if outcome == "diagnostic_failure" else None
        receipt = pilot._receipt(1, slot, request_hash, raw_hash, status, None, "rejected" if stop else "quarantined_pending_independent_review", stop, None)
        rejection = pilot._rejection(1, request_hash, raw_hash, protected_reason if outcome == "diagnostic_failure" else stop, diagnostic_hash, None) if stop else None
        cost = pilot._cost_row(1, slot, request_hash, raw_hash, receipt["row_hash"], 10_680, 10_680, 10_680, None, "rejected" if stop else "quarantined_pending_independent_review", stop, "f" * 64, None, context)
        candidates = [gate2.chained_row({"sequence": 1, "candidate_hash": "d" * 64}, None)] if candidate_count else []
        (output / "pilot_reservation.json").write_bytes(gate2.canonical_json_bytes({"artifact": "synthetic"}))
        write_jsonl(output / "request_receipts.jsonl", [receipt])
        write_jsonl(output / "cost_ledger.jsonl", [cost])
        write_jsonl(output / "rejection_ledger.jsonl", [rejection] if rejection else [])
        write_jsonl(output / "output_collision_diagnostics.jsonl", [diagnostic] if diagnostic else [])
        write_jsonl(output / "candidate_quarantine.jsonl", candidates)
        summary = {
            "artifact": "gemini_generator_gate5_paid_pilot_summary",
            "completed_slots": completed,
            "candidate_quarantine_count": candidate_count,
            "rejection_count": 1 if rejection else 0,
            "output_collision_diagnostic_count": 1 if diagnostic else 0,
            "cumulative_actual_usd_millionths": 10_680,
            **context,
            "aggregate_pilot_actual_usd_millionths": context["historical_pilot_actual_usd_millionths"] + 10_680,
            "global_stop": stop,
            "network_used": True,
            "credential_read": True,
            "candidate_review_performed": False,
            "corpus_mutation_performed": False,
            "receipt_chain_head": receipt["row_hash"],
            "rejection_chain_head": rejection["row_hash"] if rejection else None,
            "output_collision_diagnostic_chain_head": diagnostic["row_hash"] if diagnostic else None,
            "cost_chain_head": cost["row_hash"],
            "candidate_chain_head": candidates[-1]["row_hash"] if candidates else None,
        }
        summary["summary_sha256"] = gate2.sha256_bytes(gate2.canonical_json_bytes(summary))
        (output / "run_summary.json").write_bytes(gate2.canonical_json_bytes(summary))
        return summary

    def execute_fake(self, campaign: Path, attestation: Path, rate_path: Path, outcome: str) -> dict:
        def fake_execute(_loader, _target, _transport, _attestation, _rates, output, historical_components=None, attestation_validator=None, attested_prior_pilot_booked_cost_usd_millionths=None):
            self.assertEqual(attested_prior_pilot_booked_cost_usd_millionths, 53_400)
            return self.fake_output(output, historical_components, outcome)
        with patch.object(pilot, "execute_pilot", side_effect=fake_execute):
            return runner.execute_once(lambda _: "secret", "label", object(), attestation, rate_path, campaign)

    def test_verify_only_and_gate_are_local_and_separately_authorized(self) -> None:
        result = runner.verify_only()
        self.assertEqual(result["initial_component_count"], 6)
        self.assertEqual(result["initial_historical_cost_usd_millionths"], 53_400)
        self.assertEqual(result["attested_baseline_usd_millionths"], 53_400)
        self.assertEqual(result["maximum_campaign_attempts"], 7)
        self.assertEqual(result["worst_case_aggregate_usd_millionths"], 1_481_400)
        self.assertEqual(result["output_collision_evidence_module_sha256"], gate.EXPECTED_V3["output_collision_evidence_module_sha256"])
        self.assertFalse(result["network_used"] or result["credential_read"] or result["file_output_created"])
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); rates = self.rate_snapshot(root)
            with self.assertRaisesRegex(gate.Gate5PaidPilotRetryCampaignV3AttestationError, "unconfirmed"):
                gate.validate_attestation(self.attestation(root, rates, False))

    def test_v2_is_terminal_and_rederived_as_six_component_prefix(self) -> None:
        components = runner.initial_components()
        context = pilot.validate_historical_components(components)
        self.assertEqual(context, {"historical_pilot_component_count": 6, "historical_pilot_components_sha256": gate.INITIAL_COMPONENT_MANIFEST_SHA256, "historical_pilot_actual_usd_millionths": 53_400})
        self.assertEqual([item["booked_cost_usd_millionths"] for item in components], [10_680, 10_680, 10_680, 10_680, 0, 10_680])
        digest = v2.canonical_hash(v2.PACKAGE / "gate5_paid_pilot_retry_campaign_v2_attestation_2026-08-16.json")
        with self.assertRaisesRegex(v2.Gate5PaidPilotRetryCampaignV2Stop, "campaign_already_terminal"):
            v2.reserve_attempt(v2.PACKAGE / "gate5_paid_pilot_retry_campaign_v2_2026-08-16", digest)

    def test_old_attestation_and_rate_drift_stop_before_campaign_state(self) -> None:
        with self.assertRaises(gate.Gate5PaidPilotRetryCampaignV3AttestationError):
            gate.validate_attestation(PACKAGE / "gate5_paid_pilot_retry_campaign_v2_attestation_2026-08-16.json")
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); rates = self.rate_snapshot(root); attestation = self.attestation(root, rates); campaign = root / "campaign"
            changed = gate2.load_json(rates); changed["rates"]["gemini-3.7-flash"]["input"] += 1; rates.write_bytes(gate2.canonical_json_bytes(changed))
            with self.assertRaisesRegex(runner.Gate5PaidPilotRetryCampaignV3Stop, "execution_day_rate_snapshot_mismatch"):
                runner.execute_once(lambda _: (_ for _ in ()).throw(AssertionError("credential")), "label", object(), attestation, rates, campaign)
            self.assertFalse(campaign.exists())

    def test_real_engine_uses_frozen_baseline_but_live_total_for_money(self) -> None:
        class Transport:
            def __init__(self): self.calls = 0
            def post(self, *_args, **_kwargs): self.calls += 1; return pilot.ProviderResponse(503, {}, b'{"error":{"message":"temporary"}}')
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); rates = self.rate_snapshot(root); attestation = self.attestation(root, rates); campaign = root / "campaign"; transport = Transport()
            result = runner.execute_once(lambda _: "local-test-secret", "label", transport, attestation, rates, campaign)
            self.assertEqual(transport.calls, 1)
            self.assertEqual(result["campaign_state_after"], "active_after_clean_503")
            summary = gate2.load_json(campaign / "attempt_001_pilot_output" / "run_summary.json")
            self.assertEqual(summary["historical_pilot_actual_usd_millionths"], 53_400)
            self.assertEqual(summary["aggregate_pilot_actual_usd_millionths"], 64_080)
            self.assertEqual(summary["output_collision_diagnostic_count"], 0)

    def test_clean_503_continues_and_seventh_reaches_cap(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); rates = self.rate_snapshot(root); attestation = self.attestation(root, rates); campaign = root / "campaign"
            for sequence in range(1, 8):
                result = self.execute_fake(campaign, attestation, rates, "503")
                self.assertEqual(result["sequence"], sequence)
                self.assertEqual(result["component"]["attempt_id"], f"campaign_v3_attempt_{sequence:03d}")
            self.assertEqual(result["campaign_state_after"], "attempt_cap_reached")
            rows, components = runner.load_and_verify_campaign(campaign, runner.canonical_hash(attestation))
            self.assertEqual(rows[-1]["attempts_reserved"], 7)
            self.assertEqual(pilot.validate_historical_components(components)["historical_pilot_actual_usd_millionths"], 53_400 + 7 * 10_680)

    def test_every_non_clean_503_outcome_is_terminal_and_collision_is_linked(self) -> None:
        for outcome in ("400", "collision", "candidate", "complete", "diagnostic_failure"):
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
                root = Path(temp); rates = self.rate_snapshot(root); attestation = self.attestation(root, rates); campaign = root / "campaign"
                result = self.execute_fake(campaign, attestation, rates, outcome)
                self.assertIn(result["campaign_state_after"], runner.TERMINAL_STATES)
                if outcome == "collision":
                    output = campaign / "attempt_001_pilot_output"
                    rejection = json.loads((output / "rejection_ledger.jsonl").read_text(encoding="utf-8"))
                    diagnostic_bytes = (output / "output_collision_diagnostics.jsonl").read_bytes()
                    self.assertNotIn(b"never persisted", diagnostic_bytes)
                    diagnostic = json.loads(diagnostic_bytes)
                    self.assertEqual(rejection["output_collision_diagnostic_row_hash"], diagnostic["row_hash"])

    def test_zero_request_local_failure_is_zero_cost_and_terminal(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); rates = self.rate_snapshot(root); attestation = self.attestation(root, rates); campaign = root / "campaign"
            with patch.object(pilot, "execute_pilot", side_effect=pilot.Gate5PilotStop("synthetic_precredential_stop")):
                completion = runner.execute_once(lambda _: (_ for _ in ()).throw(AssertionError("credential")), "label", object(), attestation, rates, campaign)
            self.assertEqual(completion["completion_kind"], "zero_request_local_failure")
            self.assertEqual(completion["booked_cost_usd_millionths"], 0)
            self.assertEqual(completion["campaign_state_after"], "stopped_nonretryable_outcome")

    def test_diagnostic_tampering_is_caught_even_after_rehash(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); rates = self.rate_snapshot(root); attestation = self.attestation(root, rates); campaign = root / "campaign"
            self.execute_fake(campaign, attestation, rates, "collision")
            path = campaign / "attempt_001_pilot_output" / "output_collision_diagnostics.jsonl"
            row = json.loads(path.read_text(encoding="utf-8")); row["protected_collision"]["reasons"][0]["score"] = 0.7; row["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes({k: v for k, v in row.items() if k != "row_hash"})); write_jsonl(path, [row])
            with self.assertRaisesRegex(runner.Gate5PaidPilotRetryCampaignV3Stop, "campaign_state_invalid"):
                runner.load_and_verify_campaign(campaign, runner.canonical_hash(attestation))

    def test_relative_recovery_and_incomplete_state_are_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); rates = self.rate_snapshot(root); attestation = self.attestation(root, rates); campaign = root / "campaign"; digest = runner.canonical_hash(attestation)
            runner.initialize_campaign(campaign, digest); _, components = runner.reserve_attempt(campaign, digest); self.fake_output(campaign / "attempt_001_pilot_output", components, "503")
            with patch.object(sys, "argv", ["runner", "--recover-incomplete", "--attestation", str(attestation.relative_to(gate2.ROOT)), "--campaign-directory", str(campaign.relative_to(gate2.ROOT))]), patch("builtins.print"):
                self.assertEqual(runner.main(), 0)
            with self.assertRaisesRegex(runner.Gate5PaidPilotRetryCampaignV3Stop, "no_incomplete_attempt_to_recover"):
                runner.recover_incomplete_attempt(attestation, campaign)
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); rates = self.rate_snapshot(root); attestation = self.attestation(root, rates); campaign = root / "campaign"; digest = runner.canonical_hash(attestation)
            runner.initialize_campaign(campaign, digest); runner.reserve_attempt(campaign, digest)
            with self.assertRaisesRegex(runner.Gate5PaidPilotRetryCampaignV3Stop, "campaign_incomplete_attempt"):
                runner.reserve_attempt(campaign, digest)

    def test_concurrent_reservations_have_one_winner(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); rates = self.rate_snapshot(root); attestation = self.attestation(root, rates); campaign = root / "campaign"; digest = runner.canonical_hash(attestation); runner.initialize_campaign(campaign, digest)
            barrier = threading.Barrier(2); outcomes = []; original = runner._new_file
            def synchronized(path, data):
                if path.name == "attempt_001_lock.json": barrier.wait(5)
                original(path, data)
            def reserve():
                try: outcomes.append(runner.reserve_attempt(campaign, digest))
                except Exception as exc: outcomes.append(exc)
            with patch.object(runner, "_new_file", side_effect=synchronized):
                a = threading.Thread(target=reserve); b = threading.Thread(target=reserve); a.start(); b.start(); a.join(5); b.join(5)
            self.assertEqual(sum(isinstance(item, tuple) for item in outcomes), 1)
            self.assertEqual(sum(isinstance(item, runner.Gate5PaidPilotRetryCampaignV3Stop) for item in outcomes), 1)

    def test_v2_evidence_tampering_is_rejected_without_touching_real_state(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            copied = Path(temp) / "v2"; shutil.copytree(runner.V2_DIRECTORY, copied)
            completion = copied / "attempt_001_completion.json"
            value = gate2.load_json(completion); value["global_stop"] = "different"; value["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes({k: v for k, v in value.items() if k != "row_hash"})); completion.write_bytes(gate2.canonical_json_bytes(value))
            with patch.object(runner, "V2_DIRECTORY", copied), self.assertRaises(runner.Gate5PaidPilotRetryCampaignV3Stop):
                runner.verify_initial_evidence()
        self.assertEqual(runner.canonical_hash(runner.V2_DIRECTORY / runner.v2.LEDGER_NAME), gate.EXPECTED_V3["v2_terminal_campaign_state_sha256"])


if __name__ == "__main__":
    unittest.main()
