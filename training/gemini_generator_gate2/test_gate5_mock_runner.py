from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate2
import gate5_mock_runner as mock


class Gate5MockRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.slot = gate2.load_json(gate2.PACKAGE / "schedule.json")["slots"][0]

    def test_valid_current_shape_is_locally_validated_without_review(self) -> None:
        result = mock.run_mock_slot(self.slot, "valid_stop_with_usage")
        self.assertEqual(result["disposition"], "locally_validated_no_candidate_review")
        self.assertFalse(result["network_used"])
        self.assertFalse(result["credential_read"])
        self.assertFalse(result["candidate_reviewed"])
        self.assertFalse(result["corpus_mutated"])
        self.assertEqual(result["parsed"]["usage"]["thoughtsTokenCount"], 0)
        self.assertNotIn("thoughtSignature", result["parsed"])

    def test_blocked_or_missing_usage_stops(self) -> None:
        blocked = mock.run_mock_slot(self.slot, "blocked_without_usage")
        self.assertEqual(blocked["disposition"], "stopped")
        self.assertEqual(blocked["stop_reason"], "finish_reason_invalid")
        schema_invalid = mock.run_mock_slot(self.slot, "schema_invalid_before_usage")
        self.assertEqual(schema_invalid["stop_reason"], "schema_invalid")
        with self.assertRaisesRegex(mock.Gate5MockError, "budget_or_usage_unknown"):
            mock.parse_usage({"promptTokenCount": 4, "cachedContentTokenCount": 0, "candidatesTokenCount": 4, "thoughtsTokenCount": 4, "totalTokenCount": 4})
        with self.assertRaisesRegex(mock.Gate5MockError, "cached_usage_forbidden"):
            mock.parse_usage({"promptTokenCount": 4, "cachedContentTokenCount": 1, "candidatesTokenCount": 4, "thoughtsTokenCount": 4, "totalTokenCount": 13})
        with self.assertRaisesRegex(mock.Gate5MockError, "tool_usage_forbidden"):
            mock.parse_usage({"promptTokenCount": 4, "candidatesTokenCount": 4, "thoughtsTokenCount": 4, "toolUsePromptTokenCount": 1, "totalTokenCount": 13})
        with self.assertRaisesRegex(mock.Gate5MockError, "budget_or_usage_unknown"):
            mock.parse_usage({"promptTokenCount": 4, "candidatesTokenCount": 4, "thoughtsTokenCount": 4, "totalTokenCount": 12, "undocumentedField": 0})

    def test_live_observed_optional_signature_and_omitted_thought_count(self) -> None:
        fixture = mock.load_fixtures()["valid_stop_with_usage"]
        response = {key: value for key, value in fixture.items() if key != "id"}
        parsed = mock.parse_generate_content_response(response)
        self.assertEqual(parsed["usage"]["thoughtsTokenCount"], 0)
        self.assertNotIn("thoughtSignature", parsed)
        part = response["candidates"][0]["content"]["parts"][0]
        self.assertIn("thoughtSignature", part)
        for invalid in ("", 1, "x" * (mock.MAX_THOUGHT_SIGNATURE_CODEPOINTS + 1)):
            changed = json.loads(json.dumps(response))
            changed["candidates"][0]["content"]["parts"][0]["thoughtSignature"] = invalid
            with self.assertRaisesRegex(mock.Gate5MockError, "provider_response_shape_invalid"):
                mock.parse_generate_content_response(changed)
        present = dict(response["usageMetadata"], thoughtsTokenCount=3, totalTokenCount=573)
        self.assertEqual(mock.parse_usage(present)["thoughtsTokenCount"], 3)

    def test_duplicate_keys_are_rejected(self) -> None:
        with self.assertRaises(mock.Gate5MockError):
            json_text = '{"modelVersion":"a","modelVersion":"b"}'
            json.loads(json_text, object_pairs_hook=mock.reject_duplicate_keys)

    def test_documented_optional_response_metadata_is_allowed_but_retrieval_and_unknown_fields_stop(self) -> None:
        fixture = mock.load_fixtures()["valid_stop_with_usage"]
        response = {key: value for key, value in fixture.items() if key != "id"}
        self.assertEqual(mock.parse_generate_content_response(response)["model_version"], "gemini-3.7-flash-fixture")
        with_unknown = {**response, "undocumentedResponseField": 0}
        with self.assertRaisesRegex(mock.Gate5MockError, "provider_response_shape_invalid"):
            mock.parse_generate_content_response(with_unknown)
        with_retrieval = {**response, "candidates": [{**response["candidates"][0], "urlContextMetadata": {}}]}
        with self.assertRaisesRegex(mock.Gate5MockError, "unapproved_retrieval_or_url_context"):
            mock.parse_generate_content_response(with_retrieval)


if __name__ == "__main__":
    unittest.main()
