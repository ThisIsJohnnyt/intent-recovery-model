from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate2
import gate5_corrected_diagnostic_execution_gate as gate


class Gate5CorrectedDiagnosticExecutionGateTests(unittest.TestCase):
    def valid_value(self) -> dict[str, object]:
        value = gate2.load_json(gate.PACKAGE / "gate5_corrected_diagnostic_pre_execution_attestation_template.json")
        value["execution_date"] = date.today().isoformat()
        value["execution_day_rate_snapshot_status"] = "execution_day_verified"
        value["positive_prepaid_balance_usd_millionths"] = 10_000_000
        value["notes_without_identifiers_or_secrets"] = "local test attestation"
        for field in gate.TRUE_FIELDS:
            value[field] = True
        return value

    def test_complete_attestation_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "attestation.json"
            value = self.valid_value()
            path.write_text(json.dumps(value) + "\n", encoding="utf-8")
            self.assertEqual(gate.validate_attestation(path)["attestor"], "Johnny")

    def test_false_authorization_or_secret_stops(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "attestation.json"
            value = self.valid_value()
            value["corrected_diagnostic_one_request_authorized_by_johnny"] = False
            path.write_text(json.dumps(value) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(gate.Gate5CorrectedDiagnosticAttestationError, "required corrected diagnostic fact"):
                gate.validate_attestation(path)
            value = self.valid_value()
            value["notes_without_identifiers_or_secrets"] = "AIza" + "x" * 35
            path.write_text(json.dumps(value) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(gate.Gate5CorrectedDiagnosticAttestationError, "secret-like"):
                gate.validate_attestation(path)


if __name__ == "__main__":
    unittest.main()
