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
        "final_provider_contract_sha256": execution_gate.EXPECTED_PROVIDER_CONTRACT_SHA256,
        "final_provider_schema_sha256": execution_gate.EXPECTED_PROVIDER_SCHEMA_SHA256,
        "live_validated_request_envelope_sha256": execution_gate.EXPECTED_LIVE_REQUEST_SHA256,
        "successful_corrected_schema_diagnostic_receipt_row_sha256": execution_gate.EXPECTED_SUCCESS_RECEIPT_ROW_SHA256,
        "flash_lite_live_validated_request_envelope_sha256": execution_gate.EXPECTED_FLASH_LITE_REQUEST_SHA256,
        "successful_flash_lite_receipt_row_sha256": execution_gate.EXPECTED_FLASH_LITE_SUCCESS_RECEIPT_ROW_SHA256,
        "execution_day_rate_snapshot_sha256": "b" * 64,
        "execution_day_rate_snapshot_status": "execution_day_verified",
        "positive_prepaid_balance_usd_millionths": 10_000_000,
    })
    value.update(execution_gate.EXPECTED_FRESH)
    value.update(execution_gate.EXPECTED_THIRD)
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

    def test_live_validated_provider_evidence_mismatch_fails(self) -> None:
        value = valid_attestation()
        value["successful_corrected_schema_diagnostic_receipt_row_sha256"] = "c" * 64
        with self.assertRaisesRegex(execution_gate.Gate5ExecutionGateError, "live-validated provider evidence mismatch"):
            self.write_and_validate(value)
        value = valid_attestation()
        value["successful_flash_lite_receipt_row_sha256"] = "d" * 64
        with self.assertRaisesRegex(execution_gate.Gate5ExecutionGateError, "live-validated provider evidence mismatch"):
            self.write_and_validate(value)

    def test_fresh_attempt_evidence_or_historical_cost_mismatch_fails(self) -> None:
        value = valid_attestation()
        value["corrected_response_parser_sha256"] = "e" * 64
        with self.assertRaisesRegex(execution_gate.Gate5ExecutionGateError, "fresh-attempt evidence mismatch"):
            self.write_and_validate(value)
        value = valid_attestation()
        value["prior_pilot_booked_cost_usd_millionths"] = 0
        with self.assertRaisesRegex(execution_gate.Gate5ExecutionGateError, "pilot cap drifted"):
            self.write_and_validate(value)
        value = valid_attestation()
        value["completed_fresh_pilot_booked_cost_usd_millionths"] = 0
        with self.assertRaisesRegex(execution_gate.Gate5ExecutionGateError, "pilot cap drifted"):
            self.write_and_validate(value)
        value = valid_attestation()
        value["original_failed_pilot_booked_cost_usd_millionths"] = 0
        with self.assertRaisesRegex(execution_gate.Gate5ExecutionGateError, "pilot cap drifted"):
            self.write_and_validate(value)

    def test_third_attempt_evidence_mismatch_fails(self) -> None:
        value = valid_attestation()
        value["completed_fresh_pilot_receipts_file_sha256"] = "f" * 64
        with self.assertRaisesRegex(execution_gate.Gate5ExecutionGateError, "third-attempt evidence mismatch"):
            self.write_and_validate(value)

    def test_prior_filled_attestation_cannot_pass_new_gate(self) -> None:
        for name in ("gate5_pre_execution_attestation_2026-08-16.json", "gate5_pre_execution_attestation_fresh_2026-08-16.json"):
            with self.assertRaisesRegex(execution_gate.Gate5ExecutionGateError, "attestation fields drifted"):
                execution_gate.validate_attestation(gate2.PACKAGE / name)


if __name__ == "__main__":
    unittest.main()
