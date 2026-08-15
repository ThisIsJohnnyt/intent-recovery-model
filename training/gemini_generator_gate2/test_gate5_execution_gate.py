from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate2
import gate5_execution_gate as execution_gate


def valid_attestation() -> dict:
    value = gate2.load_json(gate2.PACKAGE / "gate5_pre_execution_attestation_template.json")
    value.update({
        "execution_date": date.today().isoformat(),
        "final_provider_contract_sha256": "a" * 64,
        "execution_day_rate_snapshot_sha256": "b" * 64,
        "execution_day_rate_snapshot_status": "execution_day_verified",
        "positive_prepaid_balance_usd_millionths": 10_000_000,
    })
    for field in execution_gate.TRUE_FIELDS:
        value[field] = True
    return value


class Gate5ExecutionGateTests(unittest.TestCase):
    def write_and_validate(self, value: dict) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "attestation.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            return execution_gate.validate_attestation(path)

    def test_complete_same_day_attestation_passes_locally(self) -> None:
        value = valid_attestation()
        self.assertEqual(self.write_and_validate(value)["attestor"], "Johnny")

    def test_missing_current_fact_or_stale_rate_fails(self) -> None:
        value = valid_attestation()
        value["common_low_thinking_confirmed_for_both_models"] = False
        with self.assertRaises(execution_gate.Gate5ExecutionGateError):
            self.write_and_validate(value)
        value = valid_attestation()
        value["execution_day_rate_snapshot_status"] = "planning_only"
        with self.assertRaises(execution_gate.Gate5ExecutionGateError):
            self.write_and_validate(value)

    def test_secret_like_attestation_content_fails(self) -> None:
        value = valid_attestation()
        value["notes_without_identifiers_or_secrets"] = "AIza" + "x" * 30
        with self.assertRaises(execution_gate.Gate5ExecutionGateError):
            self.write_and_validate(value)

    def test_template_field_drift_fails(self) -> None:
        value = valid_attestation()
        value["extra"] = True
        with self.assertRaises(execution_gate.Gate5ExecutionGateError):
            self.write_and_validate(value)


if __name__ == "__main__":
    unittest.main()
