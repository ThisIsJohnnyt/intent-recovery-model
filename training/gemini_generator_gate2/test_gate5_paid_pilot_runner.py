from __future__ import annotations

import sys
import json
import shutil
import tempfile
import unittest
from datetime import date
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate5_paid_pilot_runner as runner
import gate2


class Gate5PaidPilotRunnerTests(unittest.TestCase):
    def test_verify_only_is_local_and_validates_all_frozen_slots(self) -> None:
        result = runner.verify_local_build()
        self.assertEqual(result["schedule_slot_count"], 24)
        self.assertEqual(result["unique_request_body_count"], 12)
        self.assertEqual(result["provider_schema_sha256"], runner.execution_gate.EXPECTED_PROVIDER_SCHEMA_SHA256)
        self.assertEqual(result["live_validated_request_envelope_sha256"], runner.execution_gate.EXPECTED_LIVE_REQUEST_SHA256)
        self.assertEqual(result["successful_diagnostic_receipt_row_sha256"], runner.execution_gate.EXPECTED_SUCCESS_RECEIPT_ROW_SHA256)
        self.assertEqual(result["flash_lite_live_validated_request_envelope_sha256"], runner.execution_gate.EXPECTED_FLASH_LITE_REQUEST_SHA256)
        self.assertEqual(result["successful_flash_lite_receipt_row_sha256"], runner.execution_gate.EXPECTED_FLASH_LITE_SUCCESS_RECEIPT_ROW_SHA256)
        self.assertEqual(result["corrected_response_parser_sha256"], runner.execution_gate.EXPECTED_FRESH["corrected_response_parser_sha256"])
        self.assertEqual(result["successful_response_shape_campaign_receipt_row_sha256"], runner.execution_gate.EXPECTED_FRESH["successful_response_shape_campaign_receipt_row_sha256"])
        self.assertEqual(result["completed_fresh_pilot_summary_file_sha256"], runner.execution_gate.EXPECTED_THIRD["completed_fresh_pilot_summary_file_sha256"])
        self.assertEqual(result["original_failed_pilot_booked_cost_usd_millionths"], 10_680)
        self.assertEqual(result["completed_fresh_pilot_booked_cost_usd_millionths"], 10_680)
        self.assertEqual(result["prior_pilot_booked_cost_usd_millionths"], 21_360)
        self.assertFalse(result["network_used"])
        self.assertFalse(result["credential_read"])
        self.assertFalse(result["file_output_created"])

    def test_relative_project_path_is_canonicalized(self) -> None:
        relative = Path("training/gemini_generator_gate2/gate5_provider_contract_draft.json")
        absolute = Path(__file__).resolve().parent / "gate5_provider_contract_draft.json"
        self.assertEqual(runner.canonical_hash(relative), runner.canonical_hash(absolute))

    def test_missing_paths_produce_specific_stop_codes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            missing = Path(temp) / "missing.json"
            with self.assertRaisesRegex(runner.Gate5PilotStop, "canonical_input_invalid"):
                runner.canonical_hash(missing)
            with self.assertRaisesRegex(runner.Gate5PilotStop, "execution_day_rate_snapshot_invalid"):
                runner.load_execution_day_rates(missing)

    def test_receipt_records_numeric_http_status_without_response_content(self) -> None:
        slot = gate2.load_json(gate2.PACKAGE / "schedule.json")["slots"][0]
        receipt = runner._receipt(1, slot, "a" * 64, "b" * 64, 400, None, "rejected", "unexpected_http_status", None)
        self.assertEqual(receipt["http_status"], 400)
        self.assertEqual(receipt["raw_response_hash"], "b" * 64)
        self.assertNotIn("response_body", receipt)
        self.assertNotIn("response_headers", receipt)

    def test_provider_response_shape_fails_closed(self) -> None:
        self.assertEqual(runner.validate_provider_response(runner.ProviderResponse(200, {}, b"{}" )).status, 200)
        for invalid in (
            runner.ProviderResponse("200", {}, b"{}"),
            runner.ProviderResponse(200, {"header": 1}, b"{}"),
            runner.ProviderResponse(200, {}, "{}"),
            runner.ProviderResponse(200, {}, b"x" * (runner.MAX_RESPONSE_BYTES + 1)),
        ):
            with self.assertRaisesRegex(runner.Gate5PilotStop, "transport_or_response_size_invalid"):
                runner.validate_provider_response(invalid)

    def test_invalid_attestation_stops_before_credential_or_transport(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            attestation = root / "invalid.json"
            attestation.write_text("{}\n", encoding="utf-8")
            calls = {"credential": 0, "transport": 0}

            def credential_loader(_target: str) -> str:
                calls["credential"] += 1
                raise AssertionError("credential must not be read")

            class Transport:
                def post(self, *_args: object, **_kwargs: object) -> runner.ProviderResponse:
                    calls["transport"] += 1
                    raise AssertionError("transport must not be used")

            with self.assertRaisesRegex(runner.Gate5PilotStop, "pre_execution_validation_failed"):
                runner.execute_pilot(credential_loader, "test-label", Transport(), attestation, root / "rates.json", root / "new-output")
            self.assertEqual(calls, {"credential": 0, "transport": 0})
            self.assertFalse((root / "new-output").exists())

    def test_output_directory_must_be_new(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "existing-output"
            root.mkdir()
            with self.assertRaisesRegex(runner.Gate5PilotStop, "output_directory_already_exists"):
                runner.prepare_output_directory(root, "a" * 64, "b" * 64, "c" * 64, "d" * 64, "e" * 64, "f" * 64, dict(runner.execution_gate.EXPECTED_FRESH), dict(runner.execution_gate.EXPECTED_THIRD))

    def test_reservation_pins_both_live_model_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "new-output"
            paths = runner.prepare_output_directory(root, "a" * 64, "b" * 64, "c" * 64, "d" * 64, runner.execution_gate.EXPECTED_SUCCESS_RECEIPT_ROW_SHA256, runner.execution_gate.EXPECTED_FLASH_LITE_SUCCESS_RECEIPT_ROW_SHA256, dict(runner.execution_gate.EXPECTED_FRESH), dict(runner.execution_gate.EXPECTED_THIRD))
            reservation = json.loads(paths["lock"].read_text(encoding="utf-8"))
            self.assertEqual(reservation["successful_diagnostic_receipt_row_sha256"], runner.execution_gate.EXPECTED_SUCCESS_RECEIPT_ROW_SHA256)
            self.assertEqual(reservation["successful_flash_lite_receipt_row_sha256"], runner.execution_gate.EXPECTED_FLASH_LITE_SUCCESS_RECEIPT_ROW_SHA256)
            self.assertEqual(reservation["flash_lite_live_validated_request_envelope_sha256"], runner.execution_gate.EXPECTED_FLASH_LITE_REQUEST_SHA256)
            self.assertEqual(reservation["corrected_response_parser_sha256"], runner.execution_gate.EXPECTED_FRESH["corrected_response_parser_sha256"])
            self.assertEqual(reservation["original_failed_pilot_actual_usd_millionths"], 10_680)
            self.assertEqual(reservation["completed_fresh_pilot_actual_usd_millionths"], 10_680)
            self.assertEqual(reservation["historical_pilot_actual_usd_millionths"], 21_360)

    def test_successful_live_diagnostic_evidence_is_required(self) -> None:
        self.assertEqual(runner.verify_successful_diagnostic_evidence(), runner.execution_gate.EXPECTED_SUCCESS_RECEIPT_ROW_SHA256)
        with patch.object(runner.success_diagnostic, "verify_receipt", side_effect=runner.success_diagnostic.Gate5AdditionalPropertiesDiagnosticStop("fixture")):
            with self.assertRaisesRegex(runner.Gate5PilotStop, "successful_diagnostic_evidence_invalid"):
                runner.verify_successful_diagnostic_evidence()

    def test_successful_flash_lite_evidence_is_required(self) -> None:
        self.assertEqual(runner.verify_successful_flash_lite_evidence(), runner.execution_gate.EXPECTED_FLASH_LITE_SUCCESS_RECEIPT_ROW_SHA256)
        with patch("gate5_flash_lite_compatibility_diagnostic_runner.verify_receipt", side_effect=gate2.Gate2Error("fixture")):
            with self.assertRaisesRegex(runner.Gate5PilotStop, "successful_flash_lite_evidence_invalid"):
                runner.verify_successful_flash_lite_evidence()

    def test_fresh_attempt_evidence_is_required(self) -> None:
        evidence = runner.verify_fresh_attempt_evidence()
        self.assertEqual(evidence, runner.execution_gate.EXPECTED_FRESH)
        with patch.object(runner, "RESPONSE_PARSER_PATH", Path(__file__).resolve().parent / "missing_parser.py"):
            with self.assertRaisesRegex(runner.Gate5PilotStop, "canonical_input_invalid"):
                runner.verify_fresh_attempt_evidence()

    def test_completed_fresh_attempt_evidence_and_third_proposal_are_required(self) -> None:
        self.assertEqual(runner.verify_completed_fresh_pilot_evidence(), {key: runner.execution_gate.EXPECTED_THIRD[key] for key in runner.execution_gate.EXPECTED_THIRD if key != "third_attempt_proposal_sha256"})
        self.assertEqual(runner.verify_third_attempt_evidence(), runner.execution_gate.EXPECTED_THIRD)
        with patch.object(runner, "COMPLETED_FRESH_PILOT_DIRECTORY", Path(__file__).resolve().parent / "missing_completed_run"):
            with self.assertRaisesRegex(runner.Gate5PilotStop, "completed_fresh_pilot_evidence_invalid"):
                runner.verify_completed_fresh_pilot_evidence()

    def test_completed_fresh_attempt_tampering_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate2.PACKAGE) as temp:
            copied = Path(temp) / "completed-run"
            shutil.copytree(runner.COMPLETED_FRESH_PILOT_DIRECTORY, copied)
            summary_path = copied / "run_summary.json"
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            summary["cumulative_actual_usd_millionths"] = 0
            payload = {key: value for key, value in summary.items() if key != "summary_sha256"}
            summary["summary_sha256"] = gate2.sha256_bytes(gate2.canonical_json_bytes(payload))
            summary_path.write_bytes(gate2.canonical_json_bytes(summary))
            with patch.object(runner, "COMPLETED_FRESH_PILOT_DIRECTORY", copied):
                with self.assertRaisesRegex(runner.Gate5PilotStop, "completed_fresh_pilot_evidence_invalid"):
                    runner.verify_completed_fresh_pilot_evidence()

    def test_live_observed_shape_reaches_mechanical_screen_and_carries_historical_cost(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate2.PACKAGE) as temp:
            root = Path(temp)
            attestation_value = gate2.load_json(gate2.PACKAGE / "gate5_pre_execution_attestation_template.json")
            attestation_value.update({
                "execution_date": date.today().isoformat(),
                "final_provider_contract_sha256": runner.execution_gate.EXPECTED_PROVIDER_CONTRACT_SHA256,
                "final_provider_schema_sha256": runner.execution_gate.EXPECTED_PROVIDER_SCHEMA_SHA256,
                "live_validated_request_envelope_sha256": runner.execution_gate.EXPECTED_LIVE_REQUEST_SHA256,
                "successful_corrected_schema_diagnostic_receipt_row_sha256": runner.execution_gate.EXPECTED_SUCCESS_RECEIPT_ROW_SHA256,
                "flash_lite_live_validated_request_envelope_sha256": runner.execution_gate.EXPECTED_FLASH_LITE_REQUEST_SHA256,
                "successful_flash_lite_receipt_row_sha256": runner.execution_gate.EXPECTED_FLASH_LITE_SUCCESS_RECEIPT_ROW_SHA256,
                "execution_day_rate_snapshot_sha256": runner.canonical_hash(gate2.PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-16.json"),
                "execution_day_rate_snapshot_status": "execution_day_verified",
                "positive_prepaid_balance_usd_millionths": 10_000_000,
            })
            attestation_value.update(runner.execution_gate.EXPECTED_FRESH)
            attestation_value.update(runner.execution_gate.EXPECTED_THIRD)
            for field in runner.execution_gate.TRUE_FIELDS:
                attestation_value[field] = True
            attestation = root / "attestation.json"
            attestation.write_bytes(gate2.canonical_json_bytes(attestation_value))
            fixture = runner.response_parser.load_fixtures()["valid_stop_with_usage"]
            response_body = gate2.canonical_json_bytes({key: value for key, value in fixture.items() if key != "id"})

            class Transport:
                def __init__(self) -> None:
                    self.calls = 0

                def post(self, *_args: object, **_kwargs: object) -> runner.ProviderResponse:
                    self.calls += 1
                    if self.calls == 1:
                        return runner.ProviderResponse(200, {}, response_body)
                    raise RuntimeError("synthetic stop")

            summary = runner.execute_pilot(lambda _target: "local-test-secret", "test", Transport(), attestation, gate2.PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-16.json", root / "output")
            self.assertEqual(summary["candidate_quarantine_count"], 0, summary)
            self.assertTrue(summary["global_stop"].startswith("proposed_output:"), summary)
            self.assertNotEqual(summary["global_stop"], "provider_response_shape_invalid")
            self.assertEqual(summary["original_failed_pilot_actual_usd_millionths"], 10_680)
            self.assertEqual(summary["completed_fresh_pilot_actual_usd_millionths"], 10_680)
            self.assertEqual(summary["historical_pilot_actual_usd_millionths"], 21_360)
            self.assertEqual(summary["aggregate_pilot_actual_usd_millionths"], 21_360 + summary["cumulative_actual_usd_millionths"])
            costs = [json.loads(line) for line in (root / "output" / "cost_ledger.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(costs[0]["original_failed_pilot_actual_usd_millionths"], 10_680)
            self.assertEqual(costs[0]["completed_fresh_pilot_actual_usd_millionths"], 10_680)
            self.assertEqual(costs[0]["historical_pilot_actual_usd_millionths"], 21_360)
            self.assertEqual(costs[0]["aggregate_pilot_actual_usd_millionths"], 21_360 + costs[0]["cumulative_actual_usd_millionths"])

    def test_historical_cost_changes_reconciliation_boundary(self) -> None:
        exact_fresh = runner.RECONCILIATION_STOP - runner.PRIOR_PILOT_BOOKED_COST - 100
        self.assertTrue(runner.reservation_fits_reconciliation_stop(exact_fresh, 100))
        self.assertFalse(runner.reservation_fits_reconciliation_stop(exact_fresh + 1, 100))
        self.assertEqual(runner.aggregate_pilot_cost(0), runner.PRIOR_PILOT_BOOKED_COST)

    def test_ordered_historical_component_manifest_is_recomputed_not_trusted(self) -> None:
        components = runner.legacy_historical_components()
        context = runner.validate_historical_components(components)
        self.assertEqual(context["historical_pilot_component_count"], 2)
        self.assertEqual(context["historical_pilot_actual_usd_millionths"], 21_360)
        changed = json.loads(json.dumps(components))
        changed[0]["booked_cost_usd_millionths"] = 0
        changed[0]["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes({key: value for key, value in changed[0].items() if key != "row_hash"}))
        with self.assertRaisesRegex(runner.Gate5PilotStop, "historical_component_manifest_invalid"):
            runner.validate_historical_components(changed)

    def test_cli_reports_safe_stop_without_traceback(self) -> None:
        output = StringIO()
        with patch.object(sys, "argv", [
            "gate5_paid_pilot_runner.py", "--execute-pilot", "--credential-target", "label",
            "--attestation", "attestation.json", "--rate-snapshot", "rates.json", "--output-directory", "output",
        ]), patch.object(runner, "execute_pilot", side_effect=runner.Gate5PilotStop("pre_execution_validation_failed")), redirect_stdout(output):
            self.assertEqual(runner.main(), 2)
        self.assertEqual(output.getvalue(), '{"disposition": "stopped", "stop_reason": "pre_execution_validation_failed"}\n')


if __name__ == "__main__":
    unittest.main()
