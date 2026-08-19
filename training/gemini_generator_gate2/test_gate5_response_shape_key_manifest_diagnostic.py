from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate2
import gate5_response_shape_key_manifest_diagnostic_runner as runner


class RetiredKeyManifestDiagnosticTests(unittest.TestCase):
    def test_verify_only_confirms_retired_503_evidence(self) -> None:
        value = runner.verify_only()
        self.assertTrue(value["diagnostic_retired"])
        self.assertEqual(value["historical_http_status"], 503)
        self.assertEqual(value["historical_receipt_row_sha256"], runner.EXPECTED_RECEIPT_ROW)
        self.assertFalse(value["network_used"])
        self.assertFalse(value["credential_read"])
        self.assertFalse(value["file_output_created"])

    def test_execution_is_unconditionally_retired(self) -> None:
        with self.assertRaisesRegex(runner.Gate5KeyManifestStop, runner.RETIRED_STOP_REASON):
            runner.execute_once()

    def test_historical_receipt_verifies_and_tampering_fails(self) -> None:
        receipt = gate2.load_json(runner.RECEIPT_PATH)
        runner.verify_receipt(receipt)
        receipt["response"]["http_status"] = 200
        receipt["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes({key: value for key, value in receipt.items() if key != "row_hash"}))
        with self.assertRaisesRegex(runner.Gate5KeyManifestStop, "historical_receipt_invalid"):
            runner.verify_receipt(receipt)


if __name__ == "__main__":
    unittest.main()
