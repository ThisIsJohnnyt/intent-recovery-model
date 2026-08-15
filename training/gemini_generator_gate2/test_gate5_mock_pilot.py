from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate2
import gate5_mock_pilot as pilot


class Gate5MockPilotTests(unittest.TestCase):
    def test_valid_fixture_has_chained_receipt_and_cost_rows(self) -> None:
        result = pilot.run_mock_pilot(["valid_stop_with_usage"])
        self.assertIsNone(result["global_stop"])
        self.assertEqual(result["completed_slots"], 1)
        self.assertFalse(result["network_used"])
        self.assertFalse(result["credential_read"])
        self.assertFalse(result["candidate_reviewed"])
        self.assertFalse(result["corpus_mutated"])
        gate2.verify_chain(result["receipts"])
        gate2.verify_chain(result["cost_ledger"])
        self.assertGreater(result["cost_ledger"][0]["actual_usd_millionths"], 0)

    def test_unknown_usage_leaves_full_reservation_and_stops(self) -> None:
        result = pilot.run_mock_pilot(["blocked_without_usage", "valid_stop_with_usage"])
        self.assertEqual(result["completed_slots"], 1)
        self.assertEqual(result["global_stop"], "finish_reason_invalid")
        row = result["cost_ledger"][0]
        self.assertEqual(row["actual_usd_millionths"], row["reserved_usd_millionths"])

    def test_duplicate_candidate_stops_second_slot_and_chains_remain_valid(self) -> None:
        result = pilot.run_mock_pilot(["valid_stop_with_usage", "valid_stop_with_usage"])
        self.assertEqual(result["completed_slots"], 2)
        self.assertEqual(result["global_stop"], "pilot_duplicate")
        self.assertEqual(result["receipts"][1]["stop_reason"], "pilot_duplicate")
        gate2.verify_chain(result["receipts"])
        gate2.verify_chain(result["cost_ledger"])

    def test_chain_tampering_is_detected(self) -> None:
        result = pilot.run_mock_pilot(["valid_stop_with_usage"])
        tampered = copy.deepcopy(result["cost_ledger"])
        tampered[0]["actual_usd_millionths"] += 1
        with self.assertRaises(gate2.Gate2Error):
            gate2.verify_chain(tampered)

    def test_result_validator_detects_field_drift_even_with_rehashed_row(self) -> None:
        result = pilot.run_mock_pilot(["valid_stop_with_usage"])
        altered = copy.deepcopy(result)
        altered["cost_ledger"][0]["unexpected"] = True
        payload = {key: value for key, value in altered["cost_ledger"][0].items() if key != "row_hash"}
        altered["cost_ledger"][0]["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(payload))
        with self.assertRaises(pilot.Gate5PilotMockError):
            pilot.validate_pilot_result(altered)


if __name__ == "__main__":
    unittest.main()
