from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate2
import gate5_paid_pilot_runner as pilot_runner
import gate5_response_shape_key_manifest_campaign_gate as execution_gate
import gate5_response_shape_key_manifest_campaign_runner as runner

PACKAGE = Path(__file__).resolve().parent
RATE_PATH = PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-16.json"
OVERLOAD_BODY = b'{"error":{"code":503,"message":"temporary overload","status":"UNAVAILABLE"}}'


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


class KeyManifestCampaignTests(unittest.TestCase):
    def _attestation(self, root: Path, authorized: bool = True) -> Path:
        value = gate2.load_json(PACKAGE / "gate5_response_shape_key_manifest_campaign_attestation_template.json")
        value["execution_date"] = date.today().isoformat()
        value["execution_day_rate_snapshot_status"] = "execution_day_verified"
        value["positive_prepaid_balance_usd_millionths"] = 10_000_000
        for field in execution_gate.TRUE_FIELDS:
            value[field] = True
        value["campaign_execution_authorized_by_johnny"] = authorized
        path = root / "attestation.json"
        path.write_bytes(gate2.canonical_json_bytes(value))
        return path

    def _execute(self, campaign: Path, attestation: Path, transport: FakeTransport, loader=lambda _target: "local-test-secret") -> dict:
        return runner.execute_once(loader, "test", transport, attestation, RATE_PATH, campaign)

    def _response(self, status: int, body: bytes) -> FakeTransport:
        return FakeTransport(pilot_runner.ProviderResponse(status, {"ignored": "header-private"}, body))

    def test_verify_only_pins_both_503_attempts_and_caps_without_side_effects(self) -> None:
        value = runner.verify_only()
        self.assertTrue(value["all_frozen_hashes_match"])
        self.assertEqual(value["per_attempt_cap_usd_millionths"], 10_680)
        self.assertEqual(value["maximum_provider_requests"], 20)
        self.assertEqual(value["aggregate_cap_usd_millionths"], 213_600)
        self.assertFalse(value["network_used"])
        self.assertFalse(value["credential_read"])
        self.assertFalse(value["file_output_created"])

    def test_gate_requires_separate_campaign_authorization(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
            path = self._attestation(Path(temporary), authorized=False)
            with self.assertRaisesRegex(execution_gate.Gate5KeyManifestCampaignAttestationError, "unconfirmed"):
                execution_gate.validate_attestation(path)

    def test_503_continues_then_http_200_captures_only_keys_and_terminates(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
            root = Path(temporary)
            attestation = self._attestation(root)
            campaign = root / "campaign"
            first = self._execute(campaign, attestation, self._response(503, OVERLOAD_BODY))
            self.assertEqual(first["disposition"], "continue_after_503")
            self.assertEqual(first["campaign_state_after"], "active_after_503")
            body = gate2.canonical_json_bytes({"candidates": [{"content": {"parts": [{"text": "private-candidate", "thoughtSignature": "private-signature"}], "role": "model"}, "finishReason": "STOP"}], "usageMetadata": {"totalTokenCount": 9}, "responseId": "private-id"})
            second = self._execute(campaign, attestation, self._response(200, body))
            self.assertEqual(second["attempt_number"], 2)
            self.assertEqual(second["campaign_state_after"], "stopped_on_non_503")
            self.assertEqual(second["key_manifest"]["candidates"][0]["part_key_sets"], [["text", "thoughtSignature"]])
            serialized = json.dumps(second)
            for forbidden in ("private-candidate", "private-signature", "private-id", "header-private"):
                self.assertNotIn(forbidden, serialized)
            reads: list[str] = []
            with self.assertRaisesRegex(runner.Gate5KeyManifestCampaignStop, "campaign_already_terminal"):
                self._execute(campaign, attestation, self._response(503, OVERLOAD_BODY), lambda target: reads.append(target) or "secret")
            self.assertEqual(reads, [])

    def test_other_non_503_uses_bounded_message_and_terminates(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
            root = Path(temporary)
            receipt = self._execute(root / "campaign", self._attestation(root), self._response(429, b'{"error":{"message":"slow down","details":["private"]}}'))
            self.assertEqual(receipt["campaign_state_after"], "stopped_on_non_503")
            self.assertEqual(receipt["non_200_provider_error_message"], "slow down")
            self.assertNotIn("private", json.dumps(receipt))

    def test_credential_and_transport_failures_are_terminal_and_evidenced(self) -> None:
        for kind in ("credential", "transport"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
                root = Path(temporary)
                attestation = self._attestation(root)
                campaign = root / "campaign"
                if kind == "credential":
                    transport = self._response(503, OVERLOAD_BODY)

                    def loader(_target: str) -> str:
                        raise RuntimeError("must-not-persist")
                else:
                    transport = FakeTransport(error=RuntimeError("must-not-persist"))
                    loader = lambda _target: "local-test-secret"
                receipt = self._execute(campaign, attestation, transport, loader)
                self.assertEqual(receipt["campaign_state_after"], "stopped_local_or_transport_failure")
                self.assertNotIn("must-not-persist", json.dumps(receipt))
                count = 0 if kind == "credential" else 1
                self.assertEqual(receipt["transport"]["provider_request_count"], count)
                self.assertEqual(receipt["cost"]["actual_usd_millionths"], None if count == 0 else 10_680)
                runner.load_and_verify_campaign(campaign, runner.canonical_hash(attestation))

    def test_twentieth_503_reaches_exact_attempt_and_aggregate_caps(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
            root = Path(temporary)
            attestation = self._attestation(root)
            campaign = root / "campaign"
            for attempt in range(1, 21):
                receipt = self._execute(campaign, attestation, self._response(503, OVERLOAD_BODY))
                self.assertEqual(receipt["attempt_number"], attempt)
            self.assertEqual(receipt["campaign_state_after"], "attempt_cap_reached")
            self.assertEqual(receipt["stop_reason"], "attempt_cap_reached")
            rows = runner.load_and_verify_campaign(campaign, runner.canonical_hash(attestation))
            final = rows[-1]
            self.assertEqual(final["provider_requests"], 20)
            self.assertEqual(final["cumulative_reserved_usd_millionths"], 213_600)
            self.assertEqual(final["cumulative_booked_usd_millionths"], 213_600)
            reads: list[str] = []
            with self.assertRaisesRegex(runner.Gate5KeyManifestCampaignStop, "campaign_already_terminal"):
                self._execute(campaign, attestation, self._response(503, OVERLOAD_BODY), lambda target: reads.append(target) or "secret")
            self.assertEqual(reads, [])

    def test_incomplete_reservation_blocks_all_later_invocations(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
            root = Path(temporary)
            attestation = self._attestation(root)
            attestation_hash = runner.canonical_hash(attestation)
            campaign = root / "campaign"
            runner.initialize_campaign(campaign, attestation_hash)
            runner.reserve_attempt(campaign, attestation_hash)
            reads: list[str] = []
            with self.assertRaisesRegex(runner.Gate5KeyManifestCampaignStop, "campaign_incomplete_attempt"):
                self._execute(campaign, attestation, self._response(503, OVERLOAD_BODY), lambda target: reads.append(target) or "secret")
            self.assertEqual(reads, [])

    def test_near_simultaneous_invocations_cannot_both_reach_transport(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
            root = Path(temporary)
            attestation = self._attestation(root)
            campaign = root / "campaign"
            first_at_credential = threading.Event()
            release_first = threading.Event()
            results: list[object] = []
            first_transport = self._response(503, OVERLOAD_BODY)
            second_transport = self._response(503, OVERLOAD_BODY)

            def blocking_loader(_target: str) -> str:
                first_at_credential.set()
                release_first.wait(5)
                return "local-test-secret"

            def first_call() -> None:
                try:
                    results.append(self._execute(campaign, attestation, first_transport, blocking_loader))
                except Exception as exc:  # pragma: no cover - asserted below
                    results.append(exc)

            thread = threading.Thread(target=first_call)
            thread.start()
            self.assertTrue(first_at_credential.wait(5))
            reads: list[str] = []
            with self.assertRaisesRegex(runner.Gate5KeyManifestCampaignStop, "campaign_incomplete_attempt"):
                self._execute(campaign, attestation, second_transport, lambda target: reads.append(target) or "secret")
            release_first.set()
            thread.join(5)
            self.assertFalse(thread.is_alive())
            self.assertEqual(first_transport.calls, 1)
            self.assertEqual(second_transport.calls, 0)
            self.assertEqual(reads, [])
            self.assertEqual(len(results), 1)
            self.assertIsInstance(results[0], dict)

    def test_two_reservers_racing_for_same_sequence_have_one_lock_winner(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
            root = Path(temporary)
            attestation = self._attestation(root)
            attestation_hash = runner.canonical_hash(attestation)
            campaign = root / "campaign"
            runner.initialize_campaign(campaign, attestation_hash)
            barrier = threading.Barrier(2)
            original_new_file = runner._new_file
            outcomes: list[object] = []

            def synchronized_new_file(path: Path, data: bytes) -> None:
                if path.name == "attempt_001_lock.json":
                    barrier.wait(5)
                original_new_file(path, data)

            def reserve() -> None:
                try:
                    outcomes.append(runner.reserve_attempt(campaign, attestation_hash))
                except Exception as exc:
                    outcomes.append(exc)

            with patch.object(runner, "_new_file", side_effect=synchronized_new_file):
                first = threading.Thread(target=reserve)
                second = threading.Thread(target=reserve)
                first.start()
                second.start()
                first.join(5)
                second.join(5)
            self.assertFalse(first.is_alive())
            self.assertFalse(second.is_alive())
            self.assertEqual(sum(isinstance(item, tuple) for item in outcomes), 1)
            errors = [item for item in outcomes if isinstance(item, runner.Gate5KeyManifestCampaignStop)]
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0].code, "exclusive_output_unavailable")
            self.assertEqual(len(list(campaign.glob("attempt_001_lock.json"))), 1)
            rows = runner._read_jsonl(campaign / runner.LEDGER_NAME)
            self.assertEqual([row["event"] for row in rows], ["campaign_authorized", "attempt_reserved"])

    def test_rehashed_state_tampering_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
            root = Path(temporary)
            attestation = self._attestation(root)
            campaign = root / "campaign"
            self._execute(campaign, attestation, self._response(503, OVERLOAD_BODY))
            ledger = campaign / runner.LEDGER_NAME
            rows = runner._read_jsonl(ledger)
            rows[-1]["cumulative_booked_usd_millionths"] = 1
            rows[-1]["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes({key: value for key, value in rows[-1].items() if key != "row_hash"}))
            ledger.write_bytes(b"".join(gate2.canonical_json_bytes(row) for row in rows))
            with self.assertRaisesRegex(runner.Gate5KeyManifestCampaignStop, "campaign_state_invalid"):
                runner.load_and_verify_campaign(campaign, runner.canonical_hash(attestation))

    def test_transient_lock_or_receipt_reopen_oserror_is_normalized(self) -> None:
        for target_name in ("attempt_001_lock.json", "attempt_001_receipt.json"):
            with self.subTest(target_name=target_name), tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
                root = Path(temporary)
                attestation = self._attestation(root)
                campaign = root / "campaign"
                self._execute(campaign, attestation, self._response(503, OVERLOAD_BODY))
                original_load_json = gate2.load_json

                def fail_target(path: Path):
                    if Path(path).name == target_name:
                        raise PermissionError("synthetic transient reopen failure")
                    return original_load_json(path)

                with patch.object(gate2, "load_json", side_effect=fail_target):
                    with self.assertRaisesRegex(runner.Gate5KeyManifestCampaignStop, "campaign_state_invalid"):
                        runner.load_and_verify_campaign(campaign, runner.canonical_hash(attestation))


if __name__ == "__main__":
    unittest.main()
