from __future__ import annotations

import copy
import json
import tempfile
import unittest
from datetime import date as _dt_date
from pathlib import Path
from unittest.mock import patch

import gate2
import gate5_mock_runner as response_parser
import gate5_paid_pilot_retry_campaign_v7_runner as v7
import gate5_paid_pilot_retry_campaign_v8_gate as gate
import gate5_paid_pilot_retry_campaign_v8_runner as runner
import gate5_paid_pilot_v8_engine as engine


PACKAGE = Path(__file__).resolve().parent


class Gate5PaidPilotRetryCampaignV8Tests(unittest.TestCase):
    def rates(self, root: Path, observed: str | None = None) -> Path:
        # Default to the REAL current date, not a hardcoded string: engine.
        # load_execution_day_rates() checks observed_date against the real
        # datetime.date.today(), not any fictional gate-level date some tests
        # patch elsewhere - a hardcoded default silently breaks once the day
        # it was written has passed. Same class of bug already found and
        # fixed in V9's and V10's test suites this same session.
        if observed is None:
            observed = _dt_date.today().isoformat()
        value = gate2.load_json(runner.REFERENCE_RATE_PATH); value["observed_date"] = observed
        path = root / ("rates-" + observed + ".json"); path.write_bytes(gate2.canonical_json_bytes(value)); return path

    def attestation_stub(self, root: Path, rate: Path, execution_date: str = "2026-08-17") -> tuple[Path, dict]:
        value = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v8_attestation_template.json")
        value.update({**gate.EXPECTED_V7, **gate.EXPECTED_BUILD, **gate.current_build_hashes()})
        value["execution_date"] = execution_date
        value["execution_day_rate_snapshot_sha256"] = runner.canonical_hash(rate)
        value["execution_day_rate_snapshot_status"] = "execution_day_verified"
        value["positive_prepaid_balance_usd_millionths"] = 10_000_000
        value["pilot_ceiling_usd_millionths"] = engine.V8_PILOT_CEILING
        value["reconciliation_stop_usd_millionths"] = engine.V8_RECONCILIATION_STOP
        value["maximum_campaign_attempts"] = gate.MAX_CAMPAIGN_ATTEMPTS
        value["initial_historical_component_count"] = gate.INITIAL_COMPONENT_COUNT
        value["prior_pilot_booked_cost_usd_millionths"] = gate.ATTESTED_BASELINE_COST
        value["v8_worst_case_aggregate_usd_millionths"] = 3_039_960
        for field in gate.TRUE_FIELDS:
            value[field] = True
        path = root / "attestation.json"; path.write_bytes(gate2.canonical_json_bytes(value)); return path, value

    def test_v7_is_rederived_as_terminal_and_immutable(self) -> None:
        attestation = PACKAGE / "gate5_paid_pilot_retry_campaign_v7_attestation_2026-08-17.json"
        root = PACKAGE / "gate5_paid_pilot_retry_campaign_v7_2026-08-17"
        rows, components = v7.load_and_verify_campaign(root, engine.canonical_hash(attestation))
        self.assertEqual(rows[-1]["campaign_state"], "stopped_nonretryable_outcome")
        self.assertEqual(rows[-1]["attempts_reserved"], 6)
        self.assertEqual(runner.initial_components(), components)
        self.assertEqual(engine.validate_historical_components(components), {
            "historical_pilot_component_count": 24,
            "historical_pilot_components_sha256": gate.INITIAL_COMPONENT_MANIFEST_SHA256,
            "historical_pilot_actual_usd_millionths": 234_960,
        })

    def test_m02_start_schedule_is_exactly_retained_source_slots(self) -> None:
        slots = engine.load_schedule()
        self.assertEqual(len(slots), 22)
        self.assertEqual([slot["campaign_schedule_sequence"] for slot in slots], list(range(1, 23)))
        self.assertEqual([slot["source_schedule_slot"] for slot in slots], list(range(3, 25)))
        self.assertEqual([slot["mechanism_id"] for slot in slots], sum(([f"M{i:02d}"] * 2 for i in range(2, 13)), []))
        self.assertEqual({slot["model"] for slot in slots}, {"gemini-3.7-flash", "gemini-3.5-flash-lite"})
        self.assertEqual(slots[0]["model"], "gemini-3.5-flash-lite")
        self.assertEqual(slots[1]["model"], "gemini-3.7-flash")
        self.assertTrue(all(slot["prompt_collision_preflight"]["fatal"] is False for slot in slots))

    def test_m01_or_order_smuggling_fails_closed(self) -> None:
        baseline = gate2.load_json(PACKAGE / "schedule_v8_m02_start.json")
        original_path = engine.SCHEDULE_PATH
        try:
            with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
                tampered_path = Path(temporary) / "schedule.json"
                tampered = json.loads(json.dumps(baseline))
                tampered["slots"][0]["source_schedule_slot"] = 1
                tampered["slots"][0]["mechanism_id"] = "M01"
                tampered["manifest_sha256"] = gate2.sha256_bytes(gate2.canonical_json_bytes({key: value for key, value in tampered.items() if key != "manifest_sha256"}))
                tampered_path.write_bytes(gate2.canonical_json_bytes(tampered))
                engine.SCHEDULE_PATH = tampered_path
                with self.assertRaisesRegex(engine.Gate5PilotStop, "v8_schedule_(unavailable|historical_fallback)"):
                    engine.load_schedule()
        finally:
            engine.SCHEDULE_PATH = original_path

    def test_cost_math_and_verify_only_have_no_side_effects(self) -> None:
        value = runner.verify_only()
        self.assertEqual(value["historical_pilot_actual_usd_millionths"], 234_960)
        self.assertEqual(value["historical_pilot_component_count"], 24)
        self.assertEqual(value["worst_case_aggregate_usd_millionths"], 3_039_960)
        self.assertEqual(value["v8_first_request_sha256"], engine.EXPECTED_V8_FIRST_REQUEST_SHA256)
        self.assertFalse(value["network_used"])
        self.assertFalse(value["credential_read"])
        self.assertFalse(value["file_output_created"])

    def test_v8_engine_has_no_standalone_credential_entrypoint(self) -> None:
        source = (PACKAGE / "gate5_paid_pilot_v8_engine.py").read_text(encoding="utf-8")
        self.assertNotIn("--execute-pilot", source)
        self.assertNotIn("gate4_connectivity_runner", source)
        self.assertIn("dedicated V8 campaign runner", source)

    def test_attestation_template_remains_execution_disabled(self) -> None:
        template = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v8_attestation_template.json")
        self.assertFalse(template["v8_campaign_execution_authorized_by_johnny"])
        self.assertEqual(set(template), set(gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v8_attestation_template.json")))
        self.assertEqual(gate.EXPECTED_BUILD["v8_first_request_sha256"], engine.EXPECTED_V8_FIRST_REQUEST_SHA256)

    def test_historical_m01_slots_are_independent_of_v8_schedule_and_reproduce_legacy_pins(self) -> None:
        """Regression test for the 2026-08-17 zero-cost real-attempt defect: execute_pilot()'s
        legacy compatibility check was deriving its comparison hashes from V8's own M02-start
        load_schedule() output (mechanism M02) instead of the true historical M01 pair, so the
        check could never pass. This proves the two sources are deliberately different and that
        the historical source reproduces the immutable legacy pins."""
        v8_slot_zero, v8_slot_one = engine.load_schedule()[0], engine.load_schedule()[1]
        historical_slot_one, historical_slot_two = engine._historical_m01_slots()
        self.assertEqual(historical_slot_one["mechanism_id"], "M01")
        self.assertEqual(historical_slot_two["mechanism_id"], "M01")
        self.assertNotEqual(v8_slot_zero["mechanism_id"], historical_slot_one["mechanism_id"])
        self.assertNotEqual(v8_slot_one["mechanism_id"], historical_slot_two["mechanism_id"])
        live_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(engine.redesign.build_request(historical_slot_one)))
        flash_lite_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(engine.redesign.build_request(historical_slot_two)))
        self.assertEqual(live_hash, engine.execution_gate.EXPECTED_LIVE_REQUEST_SHA256)
        self.assertEqual(flash_lite_hash, engine.execution_gate.EXPECTED_FLASH_LITE_REQUEST_SHA256)

    def test_historical_schedule_tamper_fails_closed(self) -> None:
        original_path = engine.HISTORICAL_SCHEDULE_PATH
        try:
            with tempfile.TemporaryDirectory(dir=PACKAGE) as temporary:
                tampered_path = Path(temporary) / "schedule.json"
                tampered_path.write_bytes(gate2.canonical_json_bytes({"artifact": "tampered", "slots": []}))
                engine.HISTORICAL_SCHEDULE_PATH = tampered_path
                with self.assertRaisesRegex(engine.Gate5PilotStop, "historical_schedule_hash_mismatch"):
                    engine._historical_m01_slots()
        finally:
            engine.HISTORICAL_SCHEDULE_PATH = original_path

    class _FrozenFictionalDate(_dt_date):
        """A safely-fictional date (never a real calendar day this project has used) so the
        campaign directory naming test below never collides with, reuses, or risks the real
        terminal gate5_paid_pilot_retry_campaign_v8_2026-08-17 directory."""
        @classmethod
        def today(cls):
            return _dt_date(2099, 1, 1)

    FICTIONAL_DATE = "2099-01-01"

    def _fresh_named_campaign_dir(self) -> Path:
        path = PACKAGE / f"gate5_paid_pilot_retry_campaign_v8_{self.FICTIONAL_DATE}"
        self.assertFalse(path.exists(), "test fictional-date campaign directory must not already exist")
        self.addCleanup(lambda: __import__("shutil").rmtree(path, ignore_errors=True))
        return path

    def test_real_v8_engine_clean_503_through_corrected_legacy_tower(self) -> None:
        """The corrected legacy-tower check must pass (proving the fix) and the real per-attempt
        loop must still use V8's own M02-start schedule/prompt builder, book exactly one
        reservation, and persist no candidate/diagnostic content - all through the real,
        unmodified campaign runner end-to-end (including its real campaign-directory naming
        check), not a hand-rolled or bypassed shortcut."""
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp)
            rates = self.rates(root)
            attestation, _value = self.attestation_stub(root, rates, execution_date=self.FICTIONAL_DATE)
            campaign = self._fresh_named_campaign_dir()

            class Transport:
                calls = 0
                def post(self, *_args, **_kwargs):
                    self.calls += 1
                    return engine.ProviderResponse(503, {}, b"")

            transport = Transport()
            with patch("gate5_paid_pilot_retry_campaign_v8_gate.date", self._FrozenFictionalDate), patch.object(runner, "local_today", return_value=self.FICTIONAL_DATE):
                result = runner.execute_once(lambda _target: "local-test-secret", "test-target", transport, attestation, rates, campaign)

            self.assertEqual(transport.calls, 1)
            self.assertEqual(result["global_stop"], "unexpected_http_status")
            self.assertEqual(result["campaign_state_after"], "active_after_clean_503")
            self.assertEqual(result["booked_cost_usd_millionths"], gate2.reservation_cost("gemini-3.5-flash-lite", gate2.load_json(rates)))
            output = campaign / result["output_directory_name"]
            receipt = json.loads((output / "request_receipts.jsonl").read_text())
            v8_slot_zero = engine.load_schedule()[0]
            self.assertEqual(receipt["request_hash"], gate2.sha256_bytes(gate2.canonical_json_bytes(engine.v7_prompt.build_request(v8_slot_zero))))
            self.assertEqual(receipt["request_hash"], engine.EXPECTED_V8_FIRST_REQUEST_SHA256)
            self.assertEqual((output / "candidate_quarantine.jsonl").read_bytes(), b"")
            self.assertEqual((output / "output_collision_diagnostics.jsonl").read_bytes(), b"")
            rows, components = runner.load_and_verify_campaign(campaign, runner.canonical_hash(attestation))
            self.assertEqual(rows[-1]["campaign_state"], "active_after_clean_503")
            self.assertEqual(engine.validate_historical_components(components)["historical_pilot_actual_usd_millionths"], 234_960 + result["booked_cost_usd_millionths"])

    def test_real_v8_engine_clean_200_through_corrected_legacy_tower(self) -> None:
        """A genuine HTTP 200 through V8's own M02 schedule/prompt binding must progress through
        the corrected legacy checks, proving the fix does not merely happen to work for the
        failure path. Uses a schema-invalid 200 (extra key), the same proven pattern V7's own
        suite uses, deliberately rather than a fully-accepted candidate: a fully-accepted first
        slot causes execute_pilot() to continue on to a second schedule slot within the same
        call, which is a separate, pre-existing, never-exercised-in-real-usage code path (every
        real V1-V8 attempt to date has stopped on its very first slot) - not something this V8
        M01-vs-M02 fix should also start exercising for the first time. Noted for Codex
        separately; out of scope here."""
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp)
            rates = self.rates(root)
            attestation, _value = self.attestation_stub(root, rates, execution_date=self.FICTIONAL_DATE)
            campaign = self._fresh_named_campaign_dir()
            fixture = copy.deepcopy(response_parser.load_fixtures()["valid_stop_with_usage"])
            candidate = json.loads(fixture["candidates"][0]["content"]["parts"][0]["text"])
            candidate["UNEXPECTED-KEY-CANARY"] = "UNIQUE-CANDIDATE-TEXT-CANARY"
            fixture["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(candidate)
            body = gate2.canonical_json_bytes({key: value for key, value in fixture.items() if key != "id"})

            class Transport:
                calls = 0
                def post(self, *_args, **_kwargs):
                    self.calls += 1
                    return engine.ProviderResponse(200, {}, body)

            transport = Transport()
            with patch("gate5_paid_pilot_retry_campaign_v8_gate.date", self._FrozenFictionalDate), patch.object(runner, "local_today", return_value=self.FICTIONAL_DATE):
                result = runner.execute_once(lambda _target: "local-test-secret", "test-target", transport, attestation, rates, campaign)

            self.assertEqual(transport.calls, 1)
            self.assertEqual(result["global_stop"], "schema_invalid")
            self.assertEqual(result["pause_stop_code"], "schema_invalid")
            self.assertEqual(result["campaign_state_after"], "paused_pending_review")
            self.assertIsInstance(result["schema_conformance_diagnostic_row_sha256"], str)
            output = campaign / result["output_directory_name"]
            receipt = json.loads((output / "request_receipts.jsonl").read_text())
            self.assertEqual(receipt["request_hash"], engine.EXPECTED_V8_FIRST_REQUEST_SHA256)
            self.assertEqual(receipt["http_status"], 200)
            self.assertEqual(receipt["disposition"], "rejected")
            diagnostic_bytes = (output / "schema_conformance_diagnostics.jsonl").read_bytes()
            self.assertNotIn(b"UNEXPECTED-KEY-CANARY", diagnostic_bytes)
            self.assertNotIn(b"UNIQUE-CANDIDATE-TEXT-CANARY", diagnostic_bytes)
            self.assertNotEqual(diagnostic_bytes, b"")
            diagnostic = json.loads(diagnostic_bytes)
            self.assertEqual(diagnostic["schedule_slot"], 1)
            self.assertEqual(diagnostic["model"], "gemini-3.5-flash-lite")
            self.assertEqual(diagnostic["mechanism_id"], "M02")

    def test_real_v8_engine_protected_collision_builds_diagnostic_not_withheld(self) -> None:
        """Regression test for a second real defect this correction pass found via the added
        coverage above: gate5_output_collision_evidence.build_row() and
        gate5_schema_conformance_evidence.build_row() are shared V1-era modules that require
        slot["slot"] == sequence; V8's own retained-schedule slots have no "slot" key at all
        (only source_schedule_slot/campaign_schedule_sequence), so every real V8 protected
        collision would previously have silently downgraded to
        output_collision_diagnostic_withheld and lost the reference-label/similarity-score
        evidence the whole M02-start diagnostic campaign exists to produce - exactly the
        outcome this campaign is most likely to actually hit. Proves the _legacy_slot_view()
        adapter fixes this for the collision path too, not just schema_invalid, through the
        real end-to-end campaign runner with a genuine collision against the real quarantine
        pool (not a hand-built fixture)."""
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp)
            rates = self.rates(root)
            attestation, _value = self.attestation_stub(root, rates, execution_date=self.FICTIONAL_DATE)
            campaign = self._fresh_named_campaign_dir()
            _quarantine, references = gate2.build_quarantine()
            real_reference_text = next(text for label, text in references if "narrative" in label and len(text) > 40)
            fixture = copy.deepcopy(response_parser.load_fixtures()["valid_stop_with_usage"])
            candidate = json.loads(fixture["candidates"][0]["content"]["parts"][0]["text"])
            candidate["proposed_output"]["narrative"] = real_reference_text
            fixture["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(candidate)
            body = gate2.canonical_json_bytes({key: value for key, value in fixture.items() if key != "id"})

            class Transport:
                calls = 0
                def post(self, *_args, **_kwargs):
                    self.calls += 1
                    return engine.ProviderResponse(200, {}, body)

            transport = Transport()
            with patch("gate5_paid_pilot_retry_campaign_v8_gate.date", self._FrozenFictionalDate), patch.object(runner, "local_today", return_value=self.FICTIONAL_DATE):
                result = runner.execute_once(lambda _target: "local-test-secret", "test-target", transport, attestation, rates, campaign)

            self.assertEqual(transport.calls, 1)
            self.assertEqual(result["global_stop"], "proposed_output:output.narrative:protected_collision")
            self.assertNotEqual(result["global_stop"], "output_collision_diagnostic_withheld")
            self.assertEqual(result["campaign_state_after"], "stopped_nonretryable_outcome")
            output = campaign / result["output_directory_name"]
            self.assertEqual((output / "candidate_quarantine.jsonl").read_bytes(), b"")
            diagnostic_bytes = (output / "output_collision_diagnostics.jsonl").read_bytes()
            self.assertNotIn(real_reference_text.encode("utf-8"), diagnostic_bytes)
            diagnostic = json.loads(diagnostic_bytes)
            self.assertEqual(diagnostic["schedule_slot"], 1)
            self.assertEqual(diagnostic["model"], "gemini-3.5-flash-lite")
            self.assertEqual(diagnostic["mechanism_id"], "M02")
            self.assertEqual(diagnostic["field_path"], "proposed_output:output.narrative")
            rows, components = runner.load_and_verify_campaign(campaign, runner.canonical_hash(attestation))
            self.assertEqual(rows[-1]["campaign_state"], "stopped_nonretryable_outcome")

    def test_campaign_directory_naming_allows_same_day_retry_after_a_dead_campaign(self) -> None:
        """Regression test for a mechanical blocker found while preparing a corrected V8 draft
        attestation on the same real calendar day the original V8 campaign went permanently
        terminal: the campaign-directory regex required an exact bare-date match, so a corrected
        build could never get a fresh directory on the same day the original died (a novel
        situation - no prior version has needed a second same-day campaign start). Widened to
        accept an optional _r2..._r9 suffix, sharing the same date group used everywhere else;
        the original bare-date form remains valid and unchanged for every existing campaign
        (V8's real terminal directory included), and arbitrary/unbounded suffixes still fail
        closed."""
        cases = [
            ("gate5_paid_pilot_retry_campaign_v8_2026-08-17", "2026-08-17"),
            ("gate5_paid_pilot_retry_campaign_v8_2026-08-17_r2", "2026-08-17"),
            ("gate5_paid_pilot_retry_campaign_v8_2026-08-17_r9", "2026-08-17"),
        ]
        for name, expected_date in cases:
            with self.subTest(name=name):
                match = runner.CAMPAIGN_DIRECTORY_RE.fullmatch(name)
                self.assertIsNotNone(match)
                self.assertEqual(match.group(1), expected_date)
        for name in (
            "gate5_paid_pilot_retry_campaign_v8_2026-08-17_r1",
            "gate5_paid_pilot_retry_campaign_v8_2026-08-17_r10",
            "gate5_paid_pilot_retry_campaign_v8_2026-08-17_corrected",
            "gate5_paid_pilot_retry_campaign_v9_2026-08-17",
        ):
            with self.subTest(name=name):
                self.assertIsNone(runner.CAMPAIGN_DIRECTORY_RE.fullmatch(name))

    def test_credential_failure_is_zero_cost_and_no_network(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp)
            rates = self.rates(root)
            attestation, _value = self.attestation_stub(root, rates)
            campaign = root / "campaign"
            with patch.object(runner, "local_today", return_value="2026-08-17"), patch.object(runner, "_validate_campaign_root"):
                result = runner.execute_once(lambda _target: (_ for _ in ()).throw(RuntimeError("missing local credential")), "test-target", object(), attestation, rates, campaign)
            self.assertEqual(result["completion_kind"], "zero_request_local_failure")
            self.assertEqual(result["booked_cost_usd_millionths"], 0)
            self.assertEqual(result["campaign_state_after"], "stopped_nonretryable_outcome")
            rows, components = runner.load_and_verify_campaign(campaign, runner.canonical_hash(attestation))
            self.assertEqual(rows[-1]["campaign_state"], "stopped_nonretryable_outcome")
            self.assertEqual(engine.validate_historical_components(components)["historical_pilot_actual_usd_millionths"], 234_960)


if __name__ == "__main__":
    unittest.main()
