from __future__ import annotations
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate2
import gate5_provider_schema_type_diagnostic_runner as runner

class ProviderSchemaTypeDiagnosticTests(unittest.TestCase):
    def test_verify_only_reports_retirement_without_network(self) -> None:
        value = runner.verify_only()
        self.assertTrue(value["proposal_matches_frozen"]); self.assertTrue(value["diagnostic_retired"])
        self.assertFalse(value["network_used"]); self.assertFalse(value["credential_read"]); self.assertFalse(value["file_output_created"])

    def test_retired_execution_stops_before_side_effects(self) -> None:
        with self.assertRaisesRegex(runner.Gate5ProviderSchemaDiagnosticStop, runner.RETIRED_STOP_REASON): runner.execute_once()

    def test_historical_receipt_verifies_and_tampering_fails(self) -> None:
        receipt = gate2.load_json(Path(__file__).resolve().parent / "gate5_provider_schema_diagnostic_retry_2026-08-15" / "provider_schema_diagnostic_receipt.json")
        runner.verify_receipt(receipt)
        receipt["response"]["sha256"] = None
        receipt["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes({key: value for key, value in receipt.items() if key != "row_hash"}))
        with self.assertRaisesRegex(runner.Gate5ProviderSchemaDiagnosticStop, "receipt_invalid"): runner.verify_receipt(receipt)

if __name__ == "__main__": unittest.main()
