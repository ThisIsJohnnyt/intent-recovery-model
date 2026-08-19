from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate2
import gate5_flash_lite_compatibility_diagnostic_gate as execution_gate
import gate5_flash_lite_compatibility_diagnostic_runner as runner
import gate5_paid_pilot_runner as pilot_runner

PACKAGE = Path(__file__).resolve().parent
RATE_PATH = PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-16.json"


class FakeTransport:
    def __init__(self, response: pilot_runner.ProviderResponse | None = None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.calls = 0

    def post(self, endpoint: str, body: bytes, headers: dict[str, str], timeout_seconds: int) -> pilot_runner.ProviderResponse:
        self.calls += 1
        self.endpoint = endpoint
        self.body = body
        self.headers = headers
        self.timeout_seconds = timeout_seconds
        if self.error is not None:
            raise self.error
        assert self.response is not None
        return self.response


class FlashLiteCompatibilityDiagnosticTests(unittest.TestCase):
    def _attestation(self, root: Path, authorized: bool = True) -> Path:
        value = gate2.load_json(PACKAGE / "gate5_flash_lite_compatibility_diagnostic_attestation_template.json")
        value["execution_date"] = date.today().isoformat()
        value["execution_day_rate_snapshot_status"] = "execution_day_verified"
        value["positive_prepaid_balance_usd_millionths"] = 10_000_000
        for field in execution_gate.TRUE_FIELDS:
            value[field] = True
        value["one_request_authorized_by_johnny"] = authorized
        path = root / "attestation.json"
        path.write_bytes(gate2.canonical_json_bytes(value))
        return path

    def test_verify_only_pins_flash_lite_without_side_effects(self) -> None:
        value = runner.verify_only()
        self.assertTrue(value["proposal_matches_frozen"])
        self.assertTrue(value["contract_matches_frozen"])
        self.assertTrue(value["provider_schema_matches_frozen"])
        self.assertTrue(value["rate_snapshot_matches_frozen"])
        self.assertEqual(value["request_body_sha256"], runner.EXPECTED_BODY)
        self.assertEqual(value["request_envelope_sha256"], runner.EXPECTED_REQUEST)
        self.assertEqual(value["reservation_usd_millionths"], 6_320)
        self.assertFalse(value["network_used"])
        self.assertFalse(value["credential_read"])
        self.assertFalse(value["file_output_created"])

    def test_gate_requires_separate_authorization(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
            path = self._attestation(Path(temporary), authorized=False)
            with self.assertRaisesRegex(execution_gate.Gate5FlashLiteDiagnosticAttestationError, "unconfirmed"):
                execution_gate.validate_attestation(path)

    def test_http_200_body_is_not_decoded_or_retained(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
            root = Path(temporary)
            attestation = self._attestation(root)
            output = root / "output"
            transport = FakeTransport(pilot_runner.ProviderResponse(200, {"content-type": "application/json"}, b"not-json-and-must-not-be-parsed"))
            receipt = runner.execute_once(lambda _target: "local-test-secret", "test", transport, attestation, RATE_PATH, output)
            self.assertEqual(transport.calls, 1)
            self.assertEqual(transport.endpoint, runner.ENDPOINT)
            self.assertEqual(receipt["disposition"], "passed")
            self.assertEqual(receipt["error_message_capture_state"], "not_applicable_http_200")
            self.assertIsNone(receipt["non_200_provider_error_message"])
            self.assertNotIn("not-json", json.dumps(receipt))
            runner.verify_receipt(gate2.load_json(output / "flash_lite_diagnostic_receipt.json"))

    def test_non_200_captures_only_bounded_message(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
            root = Path(temporary)
            attestation = self._attestation(root)
            body = b'{"error":{"code":400,"message":"specific safe diagnostic","status":"INVALID_ARGUMENT"}}'
            transport = FakeTransport(pilot_runner.ProviderResponse(400, {"x-ignored": "header"}, body))
            receipt = runner.execute_once(lambda _target: "local-test-secret", "test", transport, attestation, RATE_PATH, root / "output")
            self.assertEqual(receipt["error_message_capture_state"], "captured")
            self.assertEqual(receipt["non_200_provider_error_message"], "specific safe diagnostic")
            serialized = json.dumps(receipt)
            self.assertNotIn("INVALID_ARGUMENT", serialized)
            self.assertNotIn("x-ignored", serialized)
            self.assertEqual(receipt["cost"]["actual_usd_millionths"], 6_320)

    def test_credential_failure_writes_zero_request_receipt(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
            root = Path(temporary)
            attestation = self._attestation(root)
            transport = FakeTransport(pilot_runner.ProviderResponse(200, {}, b"ignored"))

            def fail(_target: str) -> str:
                raise RuntimeError("must-not-persist")

            receipt = runner.execute_once(fail, "test", transport, attestation, RATE_PATH, root / "output")
            self.assertEqual(transport.calls, 0)
            self.assertEqual(receipt["transport"]["provider_request_count"], 0)
            self.assertIsNone(receipt["cost"]["actual_usd_millionths"])
            self.assertEqual(receipt["cost"]["reconciliation_state"], "not_requested")
            self.assertNotIn("must-not-persist", json.dumps(receipt))
            self.assertTrue((root / "output" / "flash_lite_diagnostic_reservation.json").is_file())

    def test_transport_failure_books_reservation_and_writes_evidence(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
            root = Path(temporary)
            attestation = self._attestation(root)
            transport = FakeTransport(error=RuntimeError("must-not-persist"))
            receipt = runner.execute_once(lambda _target: "local-test-secret", "test", transport, attestation, RATE_PATH, root / "output")
            self.assertEqual(transport.calls, 1)
            self.assertEqual(receipt["transport"]["provider_request_count"], 1)
            self.assertEqual(receipt["cost"]["actual_usd_millionths"], 6_320)
            self.assertEqual(receipt["stop_reason"], "transport_or_response_invalid")
            self.assertNotIn("must-not-persist", json.dumps(receipt))

    def test_rate_above_cap_is_rejected_locally(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
            path = Path(temporary) / "rates.json"
            value = gate2.load_json(RATE_PATH)
            value["rates"]["gemini-3.5-flash-lite"]["output_including_thinking"] = 2_500_001
            path.write_bytes(gate2.canonical_json_bytes(value))
            with self.assertRaisesRegex(runner.Gate5FlashLiteDiagnosticStop, "diagnostic_cost_cap_exceeded"):
                runner.load_rates(path)

    def test_existing_output_stops_before_credential(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
            root = Path(temporary)
            attestation = self._attestation(root)
            output = root / "output"
            output.mkdir()
            reads = []
            with self.assertRaisesRegex(runner.Gate5FlashLiteDiagnosticStop, "output_directory_already_exists"):
                runner.execute_once(lambda target: reads.append(target) or "secret", "test", FakeTransport(), attestation, RATE_PATH, output)
            self.assertEqual(reads, [])

    def test_receipt_tampering_is_rejected_even_after_rehash(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
            root = Path(temporary)
            attestation = self._attestation(root)
            receipt = runner.execute_once(lambda _target: "local-test-secret", "test", FakeTransport(pilot_runner.ProviderResponse(200, {}, b"opaque")), attestation, RATE_PATH, root / "output")
            receipt["transport"]["endpoint"] = "https://example.invalid"
            receipt["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes({key: value for key, value in receipt.items() if key != "row_hash"}))
            with self.assertRaisesRegex(runner.Gate5FlashLiteDiagnosticStop, "receipt_invalid"):
                runner.verify_receipt(receipt)


if __name__ == "__main__":
    unittest.main()
