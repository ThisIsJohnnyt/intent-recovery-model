from __future__ import annotations

import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate5_paid_pilot_runner as runner


class Gate5PaidPilotRunnerTests(unittest.TestCase):
    def test_verify_only_is_local_and_validates_all_frozen_slots(self) -> None:
        result = runner.verify_local_build()
        self.assertEqual(result["schedule_slot_count"], 24)
        self.assertEqual(result["unique_request_body_count"], 12)
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
                runner.prepare_output_directory(root, "a" * 64, "b" * 64, "c" * 64)

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
