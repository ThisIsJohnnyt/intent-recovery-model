from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import gate2
import gate5_v6_private_raw_diagnostic as diagnostic


PACKAGE = Path(__file__).resolve().parent


def candidate_text(invalid_schema: bool = False) -> str:
    value = {
        "source_input": " ".join(f"qzxword{index:03d}" for index in range(80)),
        "proposed_output": {
            "narrative": "Zzxqv lmrpt nvwxa qjksd.",
            "bullets": [] if invalid_schema else ["Fjornex caldium pivots duskward.", "Wexlora prismatic currents settle northward."],
            "action_items": ["Nvwxa three"],
        },
    }
    return json.dumps(value, separators=(",", ":"))


def response(text: str, finish_reason: str = "STOP", **candidate_fields: object) -> dict[str, object]:
    candidate: dict[str, object] = {
        "finishReason": finish_reason,
        "content": {"parts": [{"text": text, "thoughtSignature": "never-retained"}]},
    }
    candidate.update(candidate_fields)
    return {"candidates": [candidate]}


class Gate5V6PrivateRawDiagnosticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.references = gate2.build_quarantine()[1]
        self.prompt_references: list[tuple[str, str]] = []

    def consider(self, body: dict[str, object], code: str = "schema_invalid") -> dict[str, object]:
        return diagnostic.consider(body, code, self.references, [], self.prompt_references)

    def test_eligible_schema_failure_retains_only_screened_text_privately(self) -> None:
        text = candidate_text(invalid_schema=True)
        result = self.consider(response(text))
        self.assertEqual(result["state"], "persisted")
        self.assertEqual(result["text"], text)
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
            root = Path(temporary)
            row = diagnostic.persist(root, 1, "schema_invalid", "a" * 64, "b" * 64, "c" * 64, text)
            core = gate2.canonical_json_bytes(row)
            self.assertNotIn(text.encode("utf-8"), core)
            record = (root / "private_raw_diagnostics" / "attempt_001_raw_output.json").read_bytes()
            self.assertEqual(json.loads(record)["candidate_text"], text)
            self.assertNotIn(b"never-retained", record)
            verified = diagnostic.verify(root)
            self.assertEqual(verified[0]["rejection_row_sha256"], "c" * 64)
            value = json.loads(record)
            value["candidate_text"] = "tampered"
            value["record_sha256"] = gate2.sha256_bytes(gate2.canonical_json_bytes({key: item for key, item in value.items() if key != "record_sha256"}))
            (root / "private_raw_diagnostics" / "attempt_001_raw_output.json").write_bytes(gate2.canonical_json_bytes(value))
            with self.assertRaises(diagnostic.PrivateRawDiagnosticError):
                diagnostic.verify(root)

    def test_max_tokens_finish_reason_failure_retains_screened_text_privately(self) -> None:
        text = candidate_text()
        result = self.consider(response(text, "MAX_TOKENS"), "finish_reason_invalid")
        self.assertEqual(result["state"], "persisted")
        self.assertEqual(result["text"], text)

    def test_provider_safety_and_citation_controls_withhold_before_text(self) -> None:
        text = candidate_text(invalid_schema=True)
        for reason in ("SAFETY", "RECITATION", "SPII", "BLOCKLIST", "PROHIBITED_CONTENT", "OTHER", ""):
            with self.subTest(reason=reason):
                result = self.consider(response(text, reason))
                self.assertEqual(result["state"], "withheld_provider_finish_reason")
                self.assertIsNone(result["text"])
        blocked = self.consider(response(text, safetyRatings=[{"blocked": True}]))
        cited = self.consider(response(text, citationMetadata={"unexpected": "never stored"}))
        self.assertEqual(blocked["state"], "withheld_provider_safety_or_citation_signal")
        self.assertEqual(cited["state"], "withheld_provider_safety_or_citation_signal")

    def test_unknown_part_secret_and_collision_withhold(self) -> None:
        text = candidate_text(invalid_schema=True)
        body = response(text)
        body["candidates"][0]["content"]["parts"][0]["toolCall"] = {"value": "never retain"}  # type: ignore[index]
        self.assertEqual(self.consider(body)["state"], "withheld_unparseable_or_unscreenable")
        secret = candidate_text(invalid_schema=True) + "AIza" + "A" * 35
        self.assertEqual(self.consider(response(secret))["state"], "withheld_secret_like_content")
        protected_label, protected_text = self.references[0]
        collision = response(json.dumps({"source_input": protected_text, "proposed_output": {"narrative": "A neutral sentence.", "bullets": ["one", "two"], "action_items": ["act"]}}))
        result = self.consider(collision)
        self.assertEqual(result["state"], "withheld_protected_or_duplicate_collision")
        self.assertIsNone(result["text"])

    def test_only_pause_codes_and_byte_cap_are_eligible(self) -> None:
        text = candidate_text(invalid_schema=True)
        self.assertEqual(self.consider(response(text), "unexpected_http_status")["state"], "not_eligible_stop_code")
        huge = candidate_text(invalid_schema=True) + "x" * diagnostic.MAX_TEXT_BYTES
        self.assertEqual(self.consider(response(huge))["state"], "withheld_size_limit")


if __name__ == "__main__":
    unittest.main()
