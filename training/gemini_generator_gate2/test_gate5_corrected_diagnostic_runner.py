from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate2
import gate5_corrected_diagnostic_runner as diagnostic


class Gate5CorrectedDiagnosticRunnerTests(unittest.TestCase):
    def test_verify_only_is_local_and_reports_retirement(self) -> None:
        value = diagnostic.verify_only()
        self.assertTrue(value["proposal_matches_frozen"])
        self.assertEqual(value["historical_request_hash"], diagnostic.EXPECTED_REQUEST_HASH)
        self.assertTrue(value["diagnostic_retired"])
        self.assertEqual(value["stop_reason"], diagnostic.RETIRED_STOP_REASON)
        self.assertFalse(value["network_used"])
        self.assertFalse(value["credential_read"])

    def test_retired_execution_stops_before_any_side_effect(self) -> None:
        with self.assertRaisesRegex(diagnostic.Gate5CorrectedDiagnosticStop, diagnostic.RETIRED_STOP_REASON):
            diagnostic.execute_once()

    def test_rehashed_malformed_historical_receipt_still_fails_validation(self) -> None:
        receipt = {
            "artifact": "gemini_generator_gate5_corrected_diagnostic_receipt",
            "proposal_sha256": diagnostic.EXPECTED_PROPOSAL_SHA256,
            "corrected_contract_sha256": diagnostic.EXPECTED_CONTRACT_SHA256,
            "attestation_sha256": "a" * 64,
            "execution_timestamp_utc": "2026-08-15T00:00:00Z",
            "transport": {"method": "POST", "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent", "request_hash": diagnostic.EXPECTED_REQUEST_HASH, "header_names": ["Content-Type", "x-goog-api-key"], "timeout_seconds": 60, "provider_request_count": 1, "redirects_disabled": True, "retries_disabled": True},
            "response": {"http_status": 400, "byte_count": 7, "sha256": "b" * 64},
            "cost": {"authorized_cap_usd_millionths": diagnostic.DIAGNOSTIC_CAP, "pre_request_reservation_usd_millionths": diagnostic.DIAGNOSTIC_CAP, "actual_usd_millionths": diagnostic.DIAGNOSTIC_CAP, "reconciliation_state": "reserved_pending_billing"},
            "redaction_scan": {"key_like_value_found": False, "raw_error_persisted": False},
            "disposition": "completed_status_observed",
            "stop_reason": "corrected_diagnostic_one_request_complete",
        }
        altered = copy.deepcopy(receipt)
        altered["response"]["sha256"] = None
        altered["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(altered))
        with self.assertRaisesRegex(diagnostic.Gate5CorrectedDiagnosticStop, "receipt_invalid"):
            diagnostic.verify_receipt(altered)


if __name__ == "__main__":
    unittest.main()
