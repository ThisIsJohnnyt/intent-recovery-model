from __future__ import annotations
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate2
import gate5_additional_properties_diagnostic_runner as runner


class AdditionalPropertiesDiagnosticRunnerTests(unittest.TestCase):
    def receipt(self) -> dict:
        return gate2.load_json(Path(__file__).resolve().parent / "gate5_additional_properties_diagnostic_2026-08-15" / "additional_properties_diagnostic_receipt.json")

    def test_verify_only_reports_retirement_without_side_effects(self) -> None:
        value = runner.verify_only()
        self.assertTrue(value["proposal_matches_frozen"]); self.assertTrue(value["diagnostic_retired"])
        self.assertEqual(value["historical_receipt_row_hash"], runner.EXPECTED_RECEIPT_ROW)
        self.assertFalse(value["network_used"]); self.assertFalse(value["credential_read"]); self.assertFalse(value["file_output_created"])

    def test_retired_execution_stops_before_side_effects(self) -> None:
        with self.assertRaisesRegex(runner.Gate5AdditionalPropertiesDiagnosticStop, runner.RETIRED_STOP_REASON): runner.execute_once()

    def test_successful_historical_receipt_verifies_and_tampering_fails(self) -> None:
        receipt = self.receipt(); runner.verify_receipt(receipt)
        altered = copy.deepcopy(receipt); altered["response"]["http_status"] = 400
        altered["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes({key: value for key, value in altered.items() if key != "row_hash"}))
        with self.assertRaisesRegex(runner.Gate5AdditionalPropertiesDiagnosticStop, "receipt_invalid"): runner.verify_receipt(altered)


if __name__ == "__main__": unittest.main()
