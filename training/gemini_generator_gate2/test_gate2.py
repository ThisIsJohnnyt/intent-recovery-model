from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import gate2


class Gate2Tests(unittest.TestCase):
    def test_canonical_file_retries_transient_oserror_and_maps_persistent_failure(self) -> None:
        target = gate2.PACKAGE / "system_instruction.txt"
        original = Path.read_bytes
        calls = 0

        def transient(path: Path) -> bytes:
            nonlocal calls
            calls += 1
            if calls <= 2:
                raise PermissionError("synthetic transient read denial")
            return original(path)

        with patch.object(Path, "read_bytes", transient):
            canonical, _ = gate2.canonical_file(target)
        self.assertTrue(canonical)
        self.assertEqual(calls, 3)

        with patch.object(Path, "read_bytes", side_effect=PermissionError("synthetic persistent read denial")) as mocked:
            with self.assertRaisesRegex(gate2.Gate2Error, "unreadable"):
                gate2.canonical_file(target)
        self.assertEqual(mocked.call_count, 3)

    def test_canonical_file_resolves_repo_relative_path_before_receipt(self) -> None:
        relative = Path("training/gemini_generator_gate2/system_instruction.txt")
        canonical, receipt = gate2.canonical_file(relative)
        self.assertTrue(canonical)
        self.assertEqual(receipt["path"], relative.as_posix())

        with self.assertRaisesRegex(gate2.Gate2Error, "outside the project root"):
            gate2.canonical_file(Path(Path(__file__).resolve().anchor) / "outside-project.json")

    def test_frozen_prompt_and_schema_hashes(self) -> None:
        expected = {
            "system_instruction.txt": "339b6f7841248ce40dcd925518cd6cea8fe5c069b2e9cf88b1ab75cbefe7e215",
            "user_message_template.txt": "df417f36214b3f9a589ae39dbbfb8f64ce773fa5333682c9b8a876d04d2ffcb6",
            "response_schema.json": "44442b6cd641e6b5ef7360b7d0ade83aaa519c19ed5ce7962c9624b79970a464",
            "mechanism_cards.json": "03d7397db9d62f41ed73dd9a0a9bc209e1e5fdf8b9f3407ef4b5559f143f2072",
        }
        for name, digest in expected.items():
            self.assertEqual(gate2.sha256_bytes(gate2.canonical_file(gate2.PACKAGE / name)[0]), digest)

    def test_cards_and_renderer_fail_closed(self) -> None:
        cards = gate2.load_cards()
        self.assertEqual(len(cards), 12)
        system, user = gate2.render_messages("M01")
        self.assertIn(cards["M01"], user)
        self.assertNotIn("{{", system + user)
        with self.assertRaises(gate2.Gate2Error):
            gate2.render_messages("M99")
        with self.assertRaises(gate2.Gate2Error):
            gate2.render_messages("M01", "altered")

    def test_complete_quarantine_and_schedule(self) -> None:
        manifest, references = gate2.build_quarantine()
        self.assertEqual(manifest["record_count"], 111)
        self.assertGreater(manifest["screened_field_count"], 111)
        self.assertEqual(set(manifest["pools"]), set(gate2.QUARANTINE_INPUTS))
        self.assertTrue(set(gate2.VALIDATION_LOCATORS) <= {e["record_locator"] for e in manifest["pools"]["comparator"]["entries"]})
        schedule = gate2.build_schedule(references)
        self.assertEqual(schedule["slot_count"], 24)
        self.assertTrue(all(not slot["prompt_collision_preflight"]["fatal"] for slot in schedule["slots"]))
        self.assertEqual([s["model"] for s in schedule["slots"][:4]], [gate2.MODELS[0], gate2.MODELS[1], gate2.MODELS[1], gate2.MODELS[0]])

    def test_collision_adversarial_fixtures(self) -> None:
        fixtures = gate2.load_json(gate2.PACKAGE / "collision_fixtures.json")
        refs = [("fixture", fixtures["reference"])]
        for case in fixtures["cases"]:
            with self.subTest(case=case["id"]):
                self.assertEqual(gate2.collision_check(case["text"], refs)["fatal"], case["fatal"])

    def test_output_screen_distinguishes_collision_classes(self) -> None:
        candidate = {
            "source_input": "Protected source phrase with enough length",
            "proposed_output": {"narrative": "Prompt phrase with enough length.", "bullets": ["Earlier candidate phrase long enough", "Clean quartz item"], "action_items": ["Complete cedar task"]},
        }
        result = gate2.screen_candidate(
            candidate,
            [("protected:001", "Protected source phrase with enough length")],
            [("prior:001", "Earlier candidate phrase long enough")],
            [("prompt", "Prompt phrase with enough length")],
        )
        self.assertTrue(result["fatal"])
        self.assertTrue(any(reason.endswith("protected_collision") for reason in result["fatal_reasons"]))
        self.assertTrue(any(reason.endswith("pilot_duplicate") for reason in result["fatal_reasons"]))
        self.assertTrue(any(reason.endswith("prompt_imitation") for reason in result["fatal_reasons"]))

    def test_response_parser_fixtures(self) -> None:
        fixtures = gate2.load_json(gate2.PACKAGE / "response_parser_fixtures.json")
        for case in fixtures["cases"]:
            with self.subTest(case=case["id"]):
                if case["valid"]:
                    parsed = gate2.parse_response(case["raw"])
                    self.assertIn("source_input", parsed)
                else:
                    with self.assertRaises(gate2.Gate2Error):
                        gate2.parse_response(case["raw"])

    def test_cost_boundary_fixtures(self) -> None:
        fixtures = gate2.load_json(gate2.PACKAGE / "cost_boundary_fixtures.json")
        rates = gate2.load_json(gate2.RATE_PATH)
        for case in fixtures["cases"]:
            with self.subTest(case=case["id"]):
                actual = gate2.calculate_cost(case["model"], case["input_tokens"], case["visible_output_tokens"], case["thinking_tokens"], rates)
                self.assertEqual(actual, case["expected_usd_millionths"])
        total = 12 * gate2.reservation_cost(gate2.MODELS[0], rates) + 12 * gate2.reservation_cost(gate2.MODELS[1], rates)
        self.assertEqual(total, fixtures["expected_24_slot_worst_case_usd_millionths"])
        with self.assertRaises(gate2.Gate2Error):
            gate2.calculate_cost(gate2.MODELS[0], 4001, 0, 0, rates)
        with self.assertRaises(gate2.Gate2Error):
            gate2.calculate_cost(gate2.MODELS[0], 0, 2048, 1, rates)

    def test_secret_redaction_and_request_contract(self) -> None:
        fixture = gate2.load_json(gate2.PACKAGE / "mock_provider_fixtures.json")["fixtures"][1]
        self.assertEqual(gate2.redact_secrets(fixture["input"]), fixture["expected"])
        body = gate2.request_body({"model": gate2.MODELS[0], "mechanism_id": "M01"})
        self.assertFalse(gate2.contains_secret(body))
        self.assertEqual(body["body"]["generation_config"]["thinking_level"], "minimal")
        self.assertNotIn("temperature", body["body"]["generation_config"])
        self.assertEqual(body["body"]["contents"][0]["role"], "user")

    def test_append_only_chain_detects_tampering(self) -> None:
        rows = []
        prior = None
        for sequence in (1, 2):
            row = gate2.chained_row({"sequence": sequence, "value": sequence}, prior)
            rows.append(row)
            prior = row["row_hash"]
        gate2.verify_chain(rows)
        tampered = copy.deepcopy(rows)
        tampered[0]["value"] = 99
        with self.assertRaises(gate2.Gate2Error):
            gate2.verify_chain(tampered)

    def _review(self, reviewer: str, verdict: str = "pass") -> dict:
        dimensions = {name: {"verdict": verdict, "rationale": f"Candidate-local rationale for {name}."} for name in gate2.DIMENSIONS}
        review = {
            "artifact": "gemini_generator_sealed_review",
            "candidate_hash": "a" * 64,
            "reviewer": reviewer,
            "dimensions": dimensions,
            "final_verdict": "accept" if verdict == "pass" else "reject",
        }
        review["sealed_payload_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(review))
        return review

    def test_sealed_review_validation_and_comparison(self) -> None:
        left = self._review("chatgpt")
        right = self._review("claude")
        comparison = gate2.compare_reviews(left, right)
        self.assertTrue(comparison["candidate_pool_eligible"])
        changed = copy.deepcopy(right)
        changed["dimensions"][gate2.DIMENSIONS[0]]["verdict"] = "fail"
        changed["final_verdict"] = "reject"
        changed["sealed_payload_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes({k: v for k, v in changed.items() if k != "sealed_payload_hash"}))
        comparison = gate2.compare_reviews(left, changed)
        self.assertFalse(comparison["candidate_pool_eligible"])

    def test_zero_network_guard_blocks_and_counts(self) -> None:
        counter = {"attempts": 0}
        with gate2.zero_network_guard(counter):
            with self.assertRaises(gate2.Gate2Error):
                gate2.socket.create_connection(("example.invalid", 443))
        self.assertEqual(counter["attempts"], 1)

    def test_generated_artifact_hashes_and_dry_run_chains(self) -> None:
        manifest = gate2.load_json(gate2.PACKAGE / "artifact_manifest.json")
        for item in manifest["artifacts"]:
            canonical, _ = gate2.canonical_file(gate2.ROOT / item["path"])
            self.assertEqual(gate2.sha256_bytes(canonical), item["canonical_lf_sha256"])
        manifest_payload = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
        self.assertEqual(manifest["manifest_sha256"], gate2.sha256_bytes(gate2.canonical_json_bytes(manifest_payload)))

        for name in ("dummy_request_receipts.jsonl", "dummy_rejection_ledger.jsonl", "dummy_cost_ledger.jsonl"):
            rows = [json.loads(line) for line in (gate2.PACKAGE / name).read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 24)
            gate2.verify_chain(rows)
        receipt = gate2.load_json(gate2.PACKAGE / "dummy_dry_run_receipt.json")
        receipt_payload = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        self.assertEqual(receipt["receipt_sha256"], gate2.sha256_bytes(gate2.canonical_json_bytes(receipt_payload)))
        self.assertEqual(receipt["network_attempt_count"], 0)
        self.assertEqual(receipt["model_calls"], 0)
        self.assertEqual(receipt["spend_usd_millionths"], 0)


if __name__ == "__main__":
    unittest.main()
