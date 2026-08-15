from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate4_connectivity_runner as runner


def valid_metadata() -> bytes:
    return json.dumps({
        "name": "models/gemini-3.7-flash",
        "baseModelId": "gemini-3.7-flash",
        "version": "3.7",
        "supportedGenerationMethods": ["generateContent"],
    }).encode("utf-8")


def valid_attestation() -> dict:
    return {
        "artifact": "gemini_generator_gate4_pre_execution_attestation",
        "execution_date": date.today().isoformat(),
        "attestor": "Johnny",
        "paid_tier_confirmed_that_day": True,
        "prepay_plan_confirmed_that_day": True,
        "positive_prepaid_balance_usd_millionths": 10_000_000,
        "auto_reload_off_that_day": True,
        "billing_account_currently_isolated_for_pilot": True,
        "no_unexpected_billing_activity_since_gate3": True,
        "no_other_activity_during_gate4_window": True,
        "exact_model_available_and_not_deprecated_that_day": True,
        "metadata_billing_ambiguity_reviewed": True,
        "one_request_cost_cap_usd_millionths": 1_000_000,
        "one_request_execution_authorized_by_johnny": True,
        "key_remains_in_user_controlled_encrypted_local_secret_store": True,
        "notes_without_identifiers_or_secrets": "",
        "prohibited_fields_notice": "Do not record API keys, headers, secret-store paths, or identifiers.",
    }


class FakeTransport:
    def __init__(self, response: runner.ProviderResponse | Exception):
        self.response = response
        self.calls = 0
        self.headers: dict[str, str] | None = None

    def get(self, headers: dict[str, str]) -> runner.ProviderResponse:
        self.calls += 1
        self.headers = headers
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class Gate4RunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.secret = "AIza" + "x" * 35
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.attestation_path = self.root / "attestation.json"
        self.ledger_path = self.root / "ledger.jsonl"
        self.attestation_path.write_text(json.dumps(valid_attestation()), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def execute(self, response: runner.ProviderResponse | Exception, loader=None) -> tuple[dict, FakeTransport]:
        transport = FakeTransport(response)
        receipt = runner.execute_once(
            loader or (lambda _target: self.secret), "local-label", transport,
            self.attestation_path, self.ledger_path,
        )
        return receipt, transport

    def test_verify_only_hash_matches_frozen_proposal(self) -> None:
        self.assertEqual(runner.canonical_file_sha256(runner.PROPOSAL_PATH), runner.EXPECTED_PROPOSAL_SHA256)

    def test_success_is_one_get_with_header_only_secret(self) -> None:
        receipt, transport = self.execute(runner.ProviderResponse(200, {}, valid_metadata()))
        self.assertEqual(receipt["disposition"], "passed")
        self.assertEqual(transport.calls, 1)
        self.assertEqual(set(transport.headers or {}), {"Accept", "x-goog-api-key"})
        self.assertNotIn(self.secret, json.dumps(receipt))
        self.assertEqual(receipt["transport"]["request_body_byte_count"], 0)
        self.assertEqual(receipt["cost"]["authorized_cap_usd_millionths"], 1_000_000)
        self.assertEqual(receipt["cost"]["reconciliation_state"], "unknown_pending_billing")
        runner.verify_receipt(receipt)

    def test_credential_failure_makes_no_request(self) -> None:
        receipt, transport = self.execute(runner.ProviderResponse(200, {}, valid_metadata()), lambda _target: (_ for _ in ()).throw(runner.Gate4Stop("credential_unavailable")))
        self.assertEqual(receipt["stop_reason"], "credential_unavailable")
        self.assertEqual(transport.calls, 0)
        self.assertEqual(receipt["cost"]["reconciliation_state"], "not_requested")
        self.assertFalse(self.ledger_path.exists())

    def test_incomplete_attestation_makes_no_request(self) -> None:
        attestation = valid_attestation()
        attestation["auto_reload_off_that_day"] = False
        self.attestation_path.write_text(json.dumps(attestation), encoding="utf-8")
        receipt, transport = self.execute(runner.ProviderResponse(200, {}, valid_metadata()))
        self.assertEqual(receipt["stop_reason"], "pre_execution_attestation_invalid")
        self.assertEqual(transport.calls, 0)
        self.assertFalse(self.ledger_path.exists())

    def test_non_200_stops_without_retry(self) -> None:
        receipt, transport = self.execute(runner.ProviderResponse(403, {}, b'{"error":"denied"}'))
        self.assertEqual(receipt["stop_reason"], "unexpected_http_status")
        self.assertEqual(transport.calls, 1)
        self.assertIsNone(receipt["metadata"])

    def test_transport_failure_stops_with_unknown_reconciliation(self) -> None:
        receipt, transport = self.execute(OSError("simulated"))
        self.assertEqual(receipt["stop_reason"], "transport_error")
        self.assertEqual(transport.calls, 1)
        self.assertEqual(receipt["cost"]["reconciliation_state"], "unknown_pending_billing")

    def test_model_identity_mismatch_stops(self) -> None:
        bad = json.dumps({"name": "models/gemini-3.5-flash-lite", "supportedGenerationMethods": ["generateContent"]}).encode()
        receipt, _ = self.execute(runner.ProviderResponse(200, {}, bad))
        self.assertEqual(receipt["stop_reason"], "metadata_validation_failed")

    def test_absent_generate_content_stops(self) -> None:
        bad = json.dumps({"name": "models/gemini-3.7-flash", "supportedGenerationMethods": ["embedContent"]}).encode()
        receipt, _ = self.execute(runner.ProviderResponse(200, {}, bad))
        self.assertEqual(receipt["stop_reason"], "metadata_validation_failed")

    def test_content_or_usage_fields_are_rejected(self) -> None:
        for forbidden_key in ("candidates", "usageMetadata", "contents"):
            with self.subTest(key=forbidden_key):
                self.ledger_path.unlink(missing_ok=True)
                bad = json.loads(valid_metadata())
                bad[forbidden_key] = []
                receipt, _ = self.execute(runner.ProviderResponse(200, {}, json.dumps(bad).encode()))
                self.assertEqual(receipt["stop_reason"], "metadata_validation_failed")

    def test_duplicate_json_keys_are_rejected(self) -> None:
        raw = b'{"name":"models/gemini-3.7-flash","name":"models/gemini-3.7-flash","supportedGenerationMethods":["generateContent"]}'
        receipt, _ = self.execute(runner.ProviderResponse(200, {}, raw))
        self.assertEqual(receipt["stop_reason"], "duplicate_json_key")

    def test_oversized_response_is_rejected(self) -> None:
        receipt, _ = self.execute(runner.ProviderResponse(200, {}, b"x" * (runner.MAX_RESPONSE_BYTES + 1)))
        self.assertEqual(receipt["stop_reason"], "response_too_large")

    def test_tampered_receipt_fails_verification(self) -> None:
        receipt, _ = self.execute(runner.ProviderResponse(200, {}, valid_metadata()))
        tampered = copy.deepcopy(receipt)
        tampered["transport"]["provider_request_count"] = 2
        with self.assertRaises(runner.Gate4Stop):
            runner.verify_receipt(tampered)

    def test_receipt_writer_is_append_only(self) -> None:
        receipt, _ = self.execute(runner.ProviderResponse(200, {}, valid_metadata()))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "receipt.json"
            runner.write_new_receipt(output, receipt)
            with self.assertRaises(runner.Gate4Stop):
                runner.write_new_receipt(output, receipt)

    def test_existing_reservation_prevents_another_request(self) -> None:
        first, first_transport = self.execute(runner.ProviderResponse(200, {}, valid_metadata()))
        self.assertEqual(first["disposition"], "passed")
        self.assertEqual(first_transport.calls, 1)
        second, second_transport = self.execute(runner.ProviderResponse(200, {}, valid_metadata()))
        self.assertEqual(second["stop_reason"], "gate4_attempt_already_reserved")
        self.assertEqual(second_transport.calls, 0)


if __name__ == "__main__":
    unittest.main()
