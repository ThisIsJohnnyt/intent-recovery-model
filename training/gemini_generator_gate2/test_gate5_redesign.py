from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate2
import gate5_redesign as redesign


class Gate5RedesignTests(unittest.TestCase):
    def test_contract_preserves_pilot_shape_and_uses_common_low_thinking(self) -> None:
        contract = redesign.load_contract()
        self.assertEqual(contract["preserves"]["models"], list(redesign.EXPECTED_MODELS))
        self.assertEqual(contract["preserves"]["slot_count"], 24)
        self.assertEqual(contract["preserves"]["pilot_ceiling_usd_millionths"], 3_000_000)
        self.assertEqual(contract["request_controls"]["thinkingConfig"], {"thinkingLevel": "low"})

    def test_all_frozen_slots_build_without_network_or_credentials(self) -> None:
        hashes = redesign.validate_schedule_requests()
        self.assertEqual(len(hashes), 24)
        self.assertEqual(len(set(hashes)), 12)

    def test_request_has_only_the_frozen_rest_controls(self) -> None:
        slot = gate2.load_json(gate2.PACKAGE / "schedule.json")["slots"][0]
        request = redesign.build_request(slot)
        self.assertEqual(request["method"], "POST")
        self.assertEqual(request["header_names"], ["Content-Type", "x-goog-api-key"])
        self.assertEqual(request["body"]["generationConfig"]["thinkingConfig"], {"thinkingLevel": "low"})
        self.assertEqual(request["body"]["generationConfig"]["responseMimeType"], "application/json")
        self.assertEqual(request["body"]["generationConfig"]["responseSchema"], redesign.provider_response_schema())
        self.assertEqual(request["body"]["generationConfig"]["responseSchema"]["type"], "OBJECT")
        self.assertEqual(gate2.load_json(gate2.SCHEMA_PATH)["type"], "object")
        self.assertNotIn("responseFormat", request["body"]["generationConfig"])
        self.assertNotIn("temperature", request["body"]["generationConfig"])
        self.assertNotIn("tools", request["body"])
        self.assertFalse(gate2.contains_secret(request))

    def test_provider_schema_uses_uppercase_types_and_omits_unsupported_additional_properties(self) -> None:
        def lowercase_types(value: object) -> object:
            if isinstance(value, dict):
                return {key: item.lower() if key == "type" and isinstance(item, str) else lowercase_types(item) for key, item in value.items()}
            if isinstance(value, list):
                return [lowercase_types(item) for item in value]
            return value

        provider = redesign.provider_response_schema()
        self.assertNotIn("additionalProperties", provider)
        self.assertNotIn("additionalProperties", provider["properties"]["proposed_output"])
        expected = gate2.load_json(gate2.SCHEMA_PATH)
        del expected["additionalProperties"]
        del expected["properties"]["proposed_output"]["additionalProperties"]
        self.assertEqual(lowercase_types(provider), expected)

    def test_minimal_thinking_or_a_tool_is_rejected(self) -> None:
        slot = gate2.load_json(gate2.PACKAGE / "schedule.json")["slots"][0]
        request = redesign.build_request(slot)
        altered = copy.deepcopy(request)
        altered["body"]["generationConfig"]["thinkingConfig"] = {"thinkingLevel": "minimal"}
        with self.assertRaises(redesign.Gate5DraftError):
            redesign.validate_request(altered)
        altered = copy.deepcopy(request)
        altered["body"]["tools"] = []
        with self.assertRaises(redesign.Gate5DraftError):
            redesign.validate_request(altered)


if __name__ == "__main__":
    unittest.main()
