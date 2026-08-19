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
import gate5_paid_pilot_retry_campaign_v8_runner as v8runner
import gate5_paid_pilot_retry_campaign_v10_gate as gate
import gate5_paid_pilot_retry_campaign_v10_runner as runner
import gate5_paid_pilot_v10_engine as engine


PACKAGE = Path(__file__).resolve().parent


class ScriptedTransport:
    """Returns pre-programmed (status, body) pairs in call order, one per real request."""

    def __init__(self, script: list[tuple[int, bytes]]):
        self.script = script
        self.calls: list[int] = []

    def post(self, *_args, **_kwargs):
        idx = len(self.calls)
        if idx >= len(self.script):
            raise IndexError("scripted transport exhausted")
        status, body = self.script[idx]
        self.calls.append(status)
        return engine.ProviderResponse(status, {}, body)


class Gate5PaidPilotRetryCampaignV10Tests(unittest.TestCase):
    class _FrozenFictionalDate(_dt_date):
        @classmethod
        def today(cls):
            return _dt_date(2099, 1, 1)

    FICTIONAL_DATE = "2099-01-01"

    def setUp(self) -> None:
        self.v9_components = runner.v9_terminal_components()
        self.quarantine, self.references = gate2.build_quarantine()
        self.fixture = response_parser.load_fixtures()["valid_stop_with_usage"]
        self.base_candidate = json.loads(self.fixture["candidates"][0]["content"]["parts"][0]["text"])

    def make_body(self, overrides: dict | None = None) -> bytes:
        fixture = copy.deepcopy(self.fixture)
        candidate = copy.deepcopy(self.base_candidate)
        if overrides:
            candidate.update(overrides)
        fixture["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(candidate)
        return gate2.canonical_json_bytes({key: value for key, value in fixture.items() if key != "id"})

    def make_short_source_input_body(self, word_count: int = 78) -> bytes:
        """A genuine schema_invalid: source_input under the real 80-word floor,
        with an otherwise-valid proposed_output so the failure is isolated to
        the one field, matching the real V9 failure exactly (78 words)."""
        return self.make_body({"source_input": " ".join(f"word{i}" for i in range(word_count))})

    def legacy_attestation(self) -> dict:
        return runner._v9_style_legacy_attestation(self.v9_components)

    def rates(self, root: Path, observed: str | None = None) -> Path:
        # Default to the REAL current date, not a hardcoded string: engine.
        # load_execution_day_rates() checks observed_date against the real
        # datetime.date.today() (not the fictional gate-level date some
        # tests patch elsewhere), so a stale hardcoded default silently
        # breaks the day after it's written. Confirmed directly: this test
        # suite was first run a day after V9's, and every test using a
        # hardcoded date failed with execution_day_rate_snapshot_invalid.
        if observed is None:
            observed = _dt_date.today().isoformat()
        value = gate2.load_json(runner.REFERENCE_RATE_PATH)
        value["observed_date"] = observed
        path = root / ("rates-" + observed + ".json")
        path.write_bytes(gate2.canonical_json_bytes(value))
        return path

    def attestation_stub(self, root: Path, rate: Path, execution_date: str = FICTIONAL_DATE) -> tuple[Path, dict]:
        value = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v10_attestation_template.json")
        value.update({**gate.EXPECTED_V9, **gate.EXPECTED_BUILD, **gate.current_build_hashes()})
        value["execution_date"] = execution_date
        value["execution_day_rate_snapshot_sha256"] = runner.canonical_hash(rate)
        value["execution_day_rate_snapshot_status"] = "execution_day_verified"
        value["positive_prepaid_balance_usd_millionths"] = 10_000_000
        value["pilot_ceiling_usd_millionths"] = engine.V10_PILOT_CEILING
        value["reconciliation_stop_usd_millionths"] = engine.V10_RECONCILIATION_STOP
        value["max_card_attempts"] = engine.MAX_CARD_ATTEMPTS
        value["initial_historical_component_count"] = gate.INITIAL_COMPONENT_COUNT
        value["prior_pilot_booked_cost_usd_millionths"] = gate.ATTESTED_BASELINE_COST
        value["v10_worst_case_aggregate_usd_millionths"] = 1_214_640
        for field in gate.TRUE_FIELDS:
            value[field] = True
        path = root / "attestation.json"
        path.write_bytes(gate2.canonical_json_bytes(value))
        return path, value

    def _fresh_named_campaign_dir(self) -> Path:
        path = PACKAGE / f"gate5_paid_pilot_retry_campaign_v10_{self.FICTIONAL_DATE}"
        self.assertFalse(path.exists(), "test fictional-date campaign directory must not already exist")
        self.addCleanup(lambda: __import__("shutil").rmtree(path, ignore_errors=True))
        return path

    # -- structural / re-derivation tests --------------------------------

    def test_v9_terminal_evidence_rederived_and_pinned(self) -> None:
        context = engine.validate_historical_components(self.v9_components)
        self.assertEqual(context, {
            "historical_pilot_component_count": 26,
            "historical_pilot_components_sha256": gate.INITIAL_COMPONENT_MANIFEST_SHA256,
            "historical_pilot_actual_usd_millionths": 279_640,
        })

    def test_v10_reuses_v8_schedule_unchanged(self) -> None:
        slots = engine.load_schedule()
        self.assertEqual(len(slots), 22)
        self.assertEqual(engine.canonical_hash(Path("schedule_v8_m02_start.json")), engine.EXPECTED_V8_SCHEDULE_SHA256)
        first_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(engine.v8.v7_prompt.build_request(slots[0])))
        self.assertEqual(first_hash, engine.EXPECTED_V10_FIRST_REQUEST_SHA256)

    def test_schedule_source_tamper_fails_closed(self) -> None:
        original = engine.v8.SCHEDULE_PATH
        try:
            with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
                tampered_path = Path(temp) / "schedule.json"
                baseline = gate2.load_json(Path("schedule_v8_m02_start.json"))
                tampered = json.loads(json.dumps(baseline))
                tampered["slots"][0]["mechanism_id"] = "M99"
                tampered["manifest_sha256"] = gate2.sha256_bytes(gate2.canonical_json_bytes({k: v for k, v in tampered.items() if k != "manifest_sha256"}))
                tampered_path.write_bytes(gate2.canonical_json_bytes(tampered))
                engine.v8.SCHEDULE_PATH = tampered_path
                with self.assertRaises(engine.Gate5PilotStop):
                    engine.load_schedule()
        finally:
            engine.v8.SCHEDULE_PATH = original

    def test_cost_math_and_verify_only_have_no_side_effects(self) -> None:
        value = runner.verify_only()
        self.assertEqual(value["historical_pilot_actual_usd_millionths"], 279_640)
        self.assertEqual(value["single_pass_reservation_usd_millionths"], 187_000)
        self.assertEqual(value["worst_case_aggregate_usd_millionths"], 1_214_640)
        self.assertEqual(value["max_card_attempts"], 5)
        self.assertFalse(value["network_used"])
        self.assertFalse(value["credential_read"])
        self.assertFalse(value["file_output_created"])

    def test_engine_has_no_standalone_credential_entrypoint(self) -> None:
        source = (PACKAGE / "gate5_paid_pilot_v10_engine.py").read_text(encoding="utf-8")
        self.assertNotIn("--execute-full-schedule", source)
        self.assertNotIn("gate4_connectivity_runner", source)
        self.assertIn("dedicated V10 campaign runner", source)

    def test_attestation_template_remains_execution_disabled(self) -> None:
        template = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v10_attestation_template.json")
        self.assertFalse(template["v10_campaign_execution_authorized_by_johnny"])
        self.assertEqual(gate.EXPECTED_BUILD["v10_first_request_sha256"], engine.EXPECTED_V10_FIRST_REQUEST_SHA256)

    def test_campaign_directory_naming(self) -> None:
        self.assertIsNotNone(runner.CAMPAIGN_DIRECTORY_RE.fullmatch("gate5_paid_pilot_retry_campaign_v10_2026-08-17"))
        self.assertIsNone(runner.CAMPAIGN_DIRECTORY_RE.fullmatch("gate5_paid_pilot_retry_campaign_v9_2026-08-17"))
        self.assertIsNone(runner.CAMPAIGN_DIRECTORY_RE.fullmatch("gate5_paid_pilot_retry_campaign_v10_2026-08-17_extra"))

    # -- engine loop behavior, direct (no runner/attestation overhead) ---

    def test_continue_past_collision_and_schema_invalid_but_not_secret_exposure(self) -> None:
        """The core new V10 behavior: a genuine schema_invalid now continues
        the run (same as a collision), but everything else Johnny did not
        move -- exercised here with secret_exposure -- still hard-stops the
        whole run immediately."""
        accept_body = self.make_body()  # this fixture's own bullets text happens to collide - a real, valid outcome
        schema_invalid_body = self.make_short_source_input_body(78)
        secret_body = self.make_body({"source_input": self.base_candidate["source_input"] + " AIzaFAKETESTKEYFAKETESTKEYFAKETESTKEY01"})
        script = [
            (200, accept_body),         # card1: collision, continue (unchanged from V9)
            (200, schema_invalid_body), # card2: genuine schema_invalid, NOW continues (V10's new behavior)
            (200, secret_body),         # card3: secret_exposure, still hard-stops the whole run
        ]
        four_slots = engine.load_schedule()[:4]
        transport = ScriptedTransport(script)
        with patch.object(engine, "load_schedule", return_value=four_slots):
            with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
                output = Path(temp) / "output"
                rate_path = self.rates(Path(temp))
                events: list[dict] = []
                summary = engine.execute_pilot(
                    lambda _t: "local-test-secret", "test", transport,
                    v8runner.ENGINE_ATTESTATION, rate_path, output,
                    historical_components=self.v9_components,
                    attestation_validator=lambda _p: self.legacy_attestation(),
                    effective_rate_snapshot_sha256=runner.canonical_hash(rate_path),
                    progress=events.append,
                )
        self.assertEqual(len(transport.calls), 3)
        self.assertEqual(summary["requests_made"], 3)
        self.assertEqual(summary["rejection_count"], 3)
        self.assertEqual(summary["output_collision_diagnostic_count"], 1)
        self.assertEqual(summary["schema_conformance_diagnostic_count"], 1)
        # card1 and card2 both resolve and continue; card3 (secret_exposure)
        # hard-stops before ever being counted as completed.
        self.assertEqual(summary["cards_completed"], 2)
        self.assertEqual(summary["global_stop"], "secret_exposure")
        self.assertEqual([e["outcome"] for e in events], [
            "proposed_output:output.bullets:01:protected_collision",
            "schema_invalid",
            "secret_exposure",
        ])

    def test_schema_invalid_alongside_collision_continuation_uses_independent_sequencing(self) -> None:
        """Regression guard for the exact bug class V9's build caught: collision
        and schema diagnostics must each get correctly independent dense
        sequencing when both accumulate in the same run, not just when only
        one diagnostic type is ever produced."""
        collision_body = self.make_body()
        schema_body = self.make_short_source_input_body(78)
        script = [(200, collision_body), (200, schema_body), (200, collision_body)]
        three_slots = engine.load_schedule()[:3]
        transport = ScriptedTransport(script)
        with patch.object(engine, "load_schedule", return_value=three_slots):
            with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
                output = Path(temp) / "output"
                rate_path = self.rates(Path(temp))
                summary = engine.execute_pilot(
                    lambda _t: "local-test-secret", "test", transport,
                    v8runner.ENGINE_ATTESTATION, rate_path, output,
                    historical_components=self.v9_components,
                    attestation_validator=lambda _p: self.legacy_attestation(),
                    effective_rate_snapshot_sha256=runner.canonical_hash(rate_path),
                )
        self.assertEqual(summary["global_stop"], "completed_full_schedule")
        self.assertEqual(summary["cards_completed"], 3)
        self.assertEqual(summary["output_collision_diagnostic_count"], 2)
        self.assertEqual(summary["schema_conformance_diagnostic_count"], 1)

    def test_two_schema_invalid_cards_in_one_run_does_not_crash(self) -> None:
        """Direct regression test for the real crash: gate5_schema_conformance_
        evidence.verify_chain() hard-coded 'at most 1 row', silently correct
        through V9 (schema_invalid was always hard-terminal there) and a real
        defect the moment V10 let a run accumulate a second one. This is the
        exact scenario a real paid V10 campaign hit on 2026-08-18 (card 5 then
        card 10, both genuine source_input-too-short failures) - reproduced
        here with two distinct word counts, matching the real 73/77 case."""
        schema_body_one = self.make_short_source_input_body(73)
        schema_body_two = self.make_short_source_input_body(77)
        script = [(200, schema_body_one), (200, schema_body_two)]
        two_slots = engine.load_schedule()[:2]
        transport = ScriptedTransport(script)
        with patch.object(engine, "load_schedule", return_value=two_slots):
            with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
                output = Path(temp) / "output"
                rate_path = self.rates(Path(temp))
                summary = engine.execute_pilot(
                    lambda _t: "local-test-secret", "test", transport,
                    v8runner.ENGINE_ATTESTATION, rate_path, output,
                    historical_components=self.v9_components,
                    attestation_validator=lambda _p: self.legacy_attestation(),
                    effective_rate_snapshot_sha256=runner.canonical_hash(rate_path),
                )
                schema_rows = [json.loads(l) for l in (output / "schema_conformance_diagnostics.jsonl").read_text().splitlines() if l.strip()]
        self.assertEqual(summary["global_stop"], "completed_full_schedule")
        self.assertEqual(summary["cards_completed"], 2)
        self.assertEqual(summary["schema_conformance_diagnostic_count"], 2)
        self.assertEqual([row["structured_reason"]["actual_count"] for row in schema_rows], [73, 77])

    def test_secret_exposure_hard_stops_the_whole_run(self) -> None:
        secret_body = self.make_body({"source_input": self.base_candidate["source_input"] + " AIzaFAKETESTKEYFAKETESTKEYFAKETESTKEY01"})
        transport = ScriptedTransport([(200, secret_body)])
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            output = Path(temp) / "output"
            rate_path = self.rates(Path(temp))
            summary = engine.execute_pilot(
                lambda _t: "local-test-secret", "test", transport,
                v8runner.ENGINE_ATTESTATION, rate_path, output,
                historical_components=self.v9_components,
                attestation_validator=lambda _p: self.legacy_attestation(),
                effective_rate_snapshot_sha256=runner.canonical_hash(rate_path),
            )
            candidate_bytes = (output / "candidate_quarantine.jsonl").read_bytes()
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(summary["global_stop"], "secret_exposure")
        self.assertEqual(summary["cards_completed"], 0)
        self.assertEqual(candidate_bytes, b"")

    def test_natural_full_schedule_completion(self) -> None:
        """A short, monkeypatched two-card schedule that both accept cleanly
        proves the run reaches completed_full_schedule on its own rather
        than only ever stopping early."""
        real_slots = engine.load_schedule()
        short_slots = real_slots[:2]
        gibberish_candidate_one = {
            "source_input": " ".join(f"qzxword{i:03d}" for i in range(80)),
            "proposed_output": {"narrative": "Zzxqv lmrpt nvwxa qjksd fyorbin gralket.", "bullets": ["Fjornex caldium pivots duskward.", "Grendol azimuth kelfor pinewrath."], "action_items": ["Nvwxa qjksd three."]},
        }
        gibberish_candidate_two = {
            "source_input": " ".join(f"plombuxfe{i}" for i in range(80)),
            "proposed_output": {"narrative": "Trelvox pindar humsley quockit varnem.", "bullets": ["Blenthar risko duven maplecrest.", "Ostrigal fenwick dromlet yarrow."], "action_items": ["Yendral zoop four."]},
        }
        body_one = self.make_body(gibberish_candidate_one)
        body_two = self.make_body(gibberish_candidate_two)
        screen_one = gate2.screen_candidate(gibberish_candidate_one, self.references, [], [])
        screen_two = gate2.screen_candidate(gibberish_candidate_two, self.references, gate2.candidate_fields(gibberish_candidate_one), [])
        self.assertFalse(screen_one["fatal"], screen_one.get("fatal_reasons"))
        self.assertFalse(screen_two["fatal"], screen_two.get("fatal_reasons"))
        transport = ScriptedTransport([(200, body_one), (200, body_two)])
        with patch.object(engine, "load_schedule", return_value=short_slots):
            with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
                output = Path(temp) / "output"
                rate_path = self.rates(Path(temp))
                summary = engine.execute_pilot(
                    lambda _t: "local-test-secret", "test", transport,
                    v8runner.ENGINE_ATTESTATION, rate_path, output,
                    historical_components=self.v9_components,
                    attestation_validator=lambda _p: self.legacy_attestation(),
                    effective_rate_snapshot_sha256=runner.canonical_hash(rate_path),
                )
                candidates = [json.loads(l) for l in (output / "candidate_quarantine.jsonl").read_text().splitlines() if l.strip()]
        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(summary["global_stop"], "completed_full_schedule")
        self.assertEqual(summary["cards_completed"], 2)
        self.assertEqual(summary["candidate_quarantine_count"], 2)
        self.assertEqual([c["sequence"] for c in candidates], [1, 2])

    # -- runner-level end-to-end tests -----------------------------------

    def test_real_v10_runner_clean_503_end_to_end(self) -> None:
        clean_second_card = {
            "source_input": " ".join(f"zqvornex{i}" for i in range(80)),
            "proposed_output": {"narrative": "Vindrel osmara ketchwyn fallowbrit.", "bullets": ["Naskron velbit forgane trestwick.", "Umbrathil coxen darvello nimwreck."], "action_items": ["Plovenar six."]},
        }
        # NOT bounded to a short schedule: runner.execute_full_schedule() calls
        # verify_only() internally, which hard-codes the real 22-slot cost math
        # (single_pass == 187_000 etc.) - so this test runs against the real
        # schedule and, after its 6 scripted responses are consumed on cards
        # 1-2, legitimately continues into a real, unscripted card 3 and hits
        # a genuine script-exhaustion "unexpected_local_error" - same
        # documented pattern used in V9's equivalent test.
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp)
            rates = self.rates(root)
            attestation, _value = self.attestation_stub(root, rates)
            campaign = self._fresh_named_campaign_dir()
            transport = ScriptedTransport([(503, b"")] * engine.MAX_CARD_ATTEMPTS + [(200, self.make_body(clean_second_card))])
            events: list[dict] = []
            with patch("gate5_paid_pilot_retry_campaign_v10_gate.date", self._FrozenFictionalDate), patch.object(runner, "local_today", return_value=self.FICTIONAL_DATE):
                result = runner.execute_full_schedule(lambda _t: "local-test-secret", "test-target", transport, attestation, rates, campaign, events.append)
            self.assertGreaterEqual(len(transport.calls), engine.MAX_CARD_ATTEMPTS)
            self.assertEqual(result["cards_completed"], 2)
            self.assertEqual(result["campaign_state"], "unexpected_local_error")
            self.assertEqual([e["outcome"] for e in events], ["unexpected_http_status_retries_exhausted", "accepted", "unexpected_local_error"])
            rows = runner.load_and_verify_campaign(campaign, runner.canonical_hash(attestation))
            self.assertEqual(rows[0]["campaign_state"], "authorized_not_started")
            self.assertEqual(rows[-1]["event"], "run_completed")
            output = campaign / result["output_directory"]
            self.assertTrue((output / "run_summary.json").exists())

    def test_credential_failure_is_zero_cost_and_no_network(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp)
            rates = self.rates(root)
            attestation, _value = self.attestation_stub(root, rates)
            campaign = self._fresh_named_campaign_dir()
            with patch("gate5_paid_pilot_retry_campaign_v10_gate.date", self._FrozenFictionalDate), patch.object(runner, "local_today", return_value=self.FICTIONAL_DATE):
                with self.assertRaises(runner.Gate5PaidPilotRetryCampaignV10Stop):
                    runner.execute_full_schedule(lambda _t: (_ for _ in ()).throw(RuntimeError("missing local credential")), "test-target", object(), attestation, rates, campaign)
            rows = runner.load_and_verify_campaign(campaign, runner.canonical_hash(attestation))
            self.assertEqual(rows[-1]["campaign_state"], "stopped_nonretryable_outcome")
            self.assertEqual(rows[-1]["failure_code"], "credential_unavailable")
            output = campaign / "run_output"
            self.assertTrue(output.exists())
            self.assertEqual((output / "request_receipts.jsonl").read_bytes(), b"")
            self.assertEqual((output / "cost_ledger.jsonl").read_bytes(), b"")


if __name__ == "__main__":
    unittest.main()
