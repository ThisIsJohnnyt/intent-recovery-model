from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import gate2
import gate5_execution_gate as historical_gate
import gate5_paid_pilot_retry_campaign_v6_runner as v6_runner
import gate5_redesign as redesign
import gate5_v7_narrative_idiom_prompt as v7


PACKAGE = Path(__file__).resolve().parent


class Gate5V7NarrativeIdiomPromptTests(unittest.TestCase):
    def test_revision_is_exactly_one_added_bullet(self) -> None:
        historical = v7.HISTORICAL_SYSTEM_PATH.read_text(encoding="utf-8")
        revised = v7.load_v7_system_instruction()
        self.assertEqual(revised, historical.replace(v7.NARRATIVE_LINE + "\n", v7.NARRATIVE_LINE + "\n" + v7.DIVERSIFICATION_BULLET + "\n", 1))
        self.assertEqual(v7.canonical_hash(v7.HISTORICAL_SYSTEM_PATH), v7.EXPECTED_HISTORICAL_SYSTEM_SHA256)
        self.assertEqual(v7.canonical_hash(v7.V7_SYSTEM_PATH), v7.EXPECTED_V7_SYSTEM_SHA256)

    def test_v7_request_has_a_separate_pin_and_only_system_text_changes(self) -> None:
        slot = gate2.load_json(PACKAGE / "schedule.json")["slots"][0]
        historical = redesign.build_request(slot)
        revised = v7.build_request(slot)
        expected = copy.deepcopy(historical)
        expected["body"]["systemInstruction"]["parts"][0]["text"] = v7.load_v7_system_instruction()
        self.assertEqual(revised, expected)
        self.assertEqual(gate2.sha256_bytes(gate2.canonical_json_bytes(historical)), v7.EXPECTED_HISTORICAL_LIVE_REQUEST_SHA256)
        self.assertEqual(gate2.sha256_bytes(gate2.canonical_json_bytes(revised)), v7.EXPECTED_LIVE_REQUEST_SHA256_V7)
        self.assertNotEqual(v7.EXPECTED_LIVE_REQUEST_SHA256_V7, v7.EXPECTED_HISTORICAL_LIVE_REQUEST_SHA256)

    def test_v1_through_v6_pins_and_terminal_evidence_remain_valid(self) -> None:
        before_prompt = v7.canonical_hash(v7.HISTORICAL_SYSTEM_PATH)
        before_pin = historical_gate.EXPECTED_LIVE_REQUEST_SHA256
        initial = v6_runner.verify_initial_evidence()
        attestation = PACKAGE / "gate5_paid_pilot_retry_campaign_v6_attestation_2026-08-17.json"
        campaign = PACKAGE / "gate5_paid_pilot_retry_campaign_v6_2026-08-17"
        rows, components = v6_runner.load_and_verify_campaign(campaign, v6_runner.canonical_hash(attestation))
        self.assertEqual(initial["historical_pilot_component_count"], 13)
        self.assertEqual(rows[-1]["campaign_state"], "stopped_nonretryable_outcome")
        self.assertEqual(rows[-1]["attempts_reserved"], 5)
        self.assertEqual(len(components), 18)
        for output in sorted(campaign.glob("attempt_*_pilot_output")):
            receipts = [json.loads(line) for line in (output / "request_receipts.jsonl").read_text(encoding="utf-8").splitlines() if line]
            self.assertTrue(receipts)
            self.assertTrue(all(row["request_hash"] == v7.EXPECTED_HISTORICAL_LIVE_REQUEST_SHA256 for row in receipts))
        self.assertEqual(v7.canonical_hash(v7.HISTORICAL_SYSTEM_PATH), before_prompt)
        self.assertEqual(historical_gate.EXPECTED_LIVE_REQUEST_SHA256, before_pin)
        self.assertEqual(v7.historical_slot_one_request_hash(), before_pin)

    def test_verify_only_is_complete_and_has_no_side_effect_claims(self) -> None:
        result = v7.verify_only()
        self.assertEqual(result["request_count"], 24)
        self.assertEqual(result["unique_request_count"], 24)
        self.assertFalse(result["network_used"] or result["credential_read"] or result["file_output_created"])


if __name__ == "__main__":
    unittest.main()
