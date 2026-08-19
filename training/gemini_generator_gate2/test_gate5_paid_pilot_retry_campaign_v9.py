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
import gate5_paid_pilot_retry_campaign_v9_gate as gate
import gate5_paid_pilot_retry_campaign_v9_runner as runner
import gate5_paid_pilot_v9_engine as engine


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


class Gate5PaidPilotRetryCampaignV9Tests(unittest.TestCase):
    class _FrozenFictionalDate(_dt_date):
        @classmethod
        def today(cls):
            return _dt_date(2099, 1, 1)

    FICTIONAL_DATE = "2099-01-01"

    def setUp(self) -> None:
        self.v8_components = runner.v8_terminal_components()
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

    def legacy_attestation(self) -> dict:
        return runner._v8_style_legacy_attestation(self.v8_components)

    def rates(self, root: Path, observed: str | None = None) -> Path:
        # Default to the REAL current date, not a hardcoded string: engine.
        # load_execution_day_rates() checks observed_date against the real
        # datetime.date.today(), not the fictional gate-level date some tests
        # patch elsewhere - a hardcoded default silently breaks the day after
        # it's written. Found the day after this suite was first written and
        # passing (2026-08-18), fixed the same way in V10's suite; this is a
        # test-only fix, V9's engine/gate/runner are untouched.
        if observed is None:
            observed = _dt_date.today().isoformat()
        value = gate2.load_json(runner.REFERENCE_RATE_PATH)
        value["observed_date"] = observed
        path = root / ("rates-" + observed + ".json")
        path.write_bytes(gate2.canonical_json_bytes(value))
        return path

    def attestation_stub(self, root: Path, rate: Path, execution_date: str = FICTIONAL_DATE) -> tuple[Path, dict]:
        value = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v9_attestation_template.json")
        value.update({**gate.EXPECTED_V8, **gate.EXPECTED_BUILD, **gate.current_build_hashes()})
        value["execution_date"] = execution_date
        value["execution_day_rate_snapshot_sha256"] = runner.canonical_hash(rate)
        value["execution_day_rate_snapshot_status"] = "execution_day_verified"
        value["positive_prepaid_balance_usd_millionths"] = 10_000_000
        value["pilot_ceiling_usd_millionths"] = engine.V9_PILOT_CEILING
        value["reconciliation_stop_usd_millionths"] = engine.V9_RECONCILIATION_STOP
        value["max_card_attempts"] = engine.MAX_CARD_ATTEMPTS
        value["initial_historical_component_count"] = gate.INITIAL_COMPONENT_COUNT
        value["prior_pilot_booked_cost_usd_millionths"] = gate.ATTESTED_BASELINE_COST
        value["v9_worst_case_aggregate_usd_millionths"] = 1_176_280
        for field in gate.TRUE_FIELDS:
            value[field] = True
        path = root / "attestation.json"
        path.write_bytes(gate2.canonical_json_bytes(value))
        return path, value

    def _fresh_named_campaign_dir(self) -> Path:
        path = PACKAGE / f"gate5_paid_pilot_retry_campaign_v9_{self.FICTIONAL_DATE}"
        self.assertFalse(path.exists(), "test fictional-date campaign directory must not already exist")
        self.addCleanup(lambda: __import__("shutil").rmtree(path, ignore_errors=True))
        return path

    # -- structural / re-derivation tests --------------------------------

    def test_v8_terminal_evidence_rederived_and_pinned(self) -> None:
        context = engine.validate_historical_components(self.v8_components)
        self.assertEqual(context, {
            "historical_pilot_component_count": 25,
            "historical_pilot_components_sha256": gate.INITIAL_COMPONENT_MANIFEST_SHA256,
            "historical_pilot_actual_usd_millionths": 241_280,
        })

    def test_v9_reuses_v8_schedule_unchanged(self) -> None:
        slots = engine.load_schedule()
        self.assertEqual(len(slots), 22)
        self.assertEqual(engine.canonical_hash(Path("schedule_v8_m02_start.json")), engine.EXPECTED_V8_SCHEDULE_SHA256)
        first_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(engine.v8.v7_prompt.build_request(slots[0])))
        self.assertEqual(first_hash, engine.EXPECTED_V9_FIRST_REQUEST_SHA256)

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
        self.assertEqual(value["historical_pilot_actual_usd_millionths"], 241_280)
        self.assertEqual(value["single_pass_reservation_usd_millionths"], 187_000)
        self.assertEqual(value["worst_case_aggregate_usd_millionths"], 1_176_280)
        self.assertEqual(value["max_card_attempts"], 5)
        self.assertFalse(value["network_used"])
        self.assertFalse(value["credential_read"])
        self.assertFalse(value["file_output_created"])

    def test_engine_has_no_standalone_credential_entrypoint(self) -> None:
        source = (PACKAGE / "gate5_paid_pilot_v9_engine.py").read_text(encoding="utf-8")
        self.assertNotIn("--execute-full-schedule", source)
        self.assertNotIn("gate4_connectivity_runner", source)
        self.assertIn("dedicated V9 campaign runner", source)

    def test_attestation_template_remains_execution_disabled(self) -> None:
        template = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v9_attestation_template.json")
        self.assertFalse(template["v9_campaign_execution_authorized_by_johnny"])
        self.assertEqual(gate.EXPECTED_BUILD["v9_first_request_sha256"], engine.EXPECTED_V9_FIRST_REQUEST_SHA256)

    def test_campaign_directory_naming(self) -> None:
        self.assertIsNotNone(runner.CAMPAIGN_DIRECTORY_RE.fullmatch("gate5_paid_pilot_retry_campaign_v9_2026-08-17"))
        self.assertIsNone(runner.CAMPAIGN_DIRECTORY_RE.fullmatch("gate5_paid_pilot_retry_campaign_v8_2026-08-17"))
        self.assertIsNone(runner.CAMPAIGN_DIRECTORY_RE.fullmatch("gate5_paid_pilot_retry_campaign_v9_2026-08-17_extra"))

    # -- engine loop behavior, direct (no runner/attestation overhead) ---

    def test_continue_past_collision_retry_then_succeed_and_retry_exhaustion(self) -> None:
        """The core new behavior, exercised directly through the real
        execute_pilot(): collisions on two different cards both continue the
        run (with correctly independent dense sequencing - this is exactly
        the bug class this build found and fixed: a shared generator being
        exhausted after the first row), a card that 503s twice then
        succeeds only uses 3 real attempts, and a card that 503s all 5
        times is recorded as retries-exhausted and the run continues to the
        next card rather than stopping. The schedule is bounded to exactly
        these four scripted cards (rather than left at the real 22) so the
        run reaches a genuine completed_full_schedule on its own, instead of
        the assertions depending on an incidental script-exhaustion error on
        an unscripted fifth card."""
        real_narrative_ref = next(text for label, text in self.references if "narrative" in label and len(text) > 40)
        accept_body = self.make_body()  # this fixture's own bullets text happens to collide - a real, valid outcome
        narrative_collision_body = self.make_body({"proposed_output": {**self.base_candidate["proposed_output"], "narrative": real_narrative_ref}})
        script = [
            (200, accept_body),                                                    # card1: collision, continue
            (503, b""), (503, b""), (200, accept_body),                            # card2: retry x2 then collision, continue
            (200, narrative_collision_body),                                       # card3: collision, continue
            (503, b""), (503, b""), (503, b""), (503, b""), (503, b""),            # card4: exhausted, continue
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
                    historical_components=self.v8_components,
                    attestation_validator=lambda _p: self.legacy_attestation(),
                    effective_rate_snapshot_sha256=runner.canonical_hash(rate_path),
                    progress=events.append,
                )
        self.assertEqual(len(transport.calls), 10)
        self.assertEqual(summary["requests_made"], 10)
        self.assertEqual(summary["rejection_count"], 4)
        self.assertEqual(summary["output_collision_diagnostic_count"], 3)
        self.assertEqual(summary["cards_completed"], 4)
        self.assertEqual([e["outcome"] for e in events], [
            "proposed_output:output.bullets:01:protected_collision",
            "proposed_output:output.bullets:01:protected_collision",
            "proposed_output:output.narrative:protected_collision",
            "unexpected_http_status_retries_exhausted",
        ])
        self.assertEqual(events[1]["attempts_used"], 3)
        self.assertEqual(events[3]["attempts_used"], 5)
        self.assertEqual(summary["global_stop"], "completed_full_schedule")

    def test_secret_exposure_hard_stops_the_whole_run(self) -> None:
        secret_body = self.make_body({"source_input": self.base_candidate["source_input"] + " AIzaFAKETESTKEYFAKETESTKEYFAKETESTKEY01"})
        transport = ScriptedTransport([(200, secret_body)])
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            output = Path(temp) / "output"
            rate_path = self.rates(Path(temp))
            summary = engine.execute_pilot(
                lambda _t: "local-test-secret", "test", transport,
                v8runner.ENGINE_ATTESTATION, rate_path, output,
                historical_components=self.v8_components,
                attestation_validator=lambda _p: self.legacy_attestation(),
                effective_rate_snapshot_sha256=runner.canonical_hash(rate_path),
            )
            # Must read the file before the TemporaryDirectory context exits
            # and deletes it - the read was previously (wrongly) dedented to
            # after the with-block, which always raised FileNotFoundError
            # regardless of whether the engine actually wrote the file.
            candidate_bytes = (output / "candidate_quarantine.jsonl").read_bytes()
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(summary["global_stop"], "secret_exposure")
        self.assertEqual(summary["cards_completed"], 0)
        self.assertEqual(candidate_bytes, b"")

    def test_natural_full_schedule_completion(self) -> None:
        """A short, monkeypatched two-card schedule that both accept cleanly
        proves the run reaches completed_full_schedule on its own rather
        than only ever stopping early - never exercised by the two tests
        above, which both stop before the schedule is exhausted."""
        real_slots = engine.load_schedule()
        short_slots = real_slots[:2]
        # Two bullets each: gate2's real response schema requires
        # proposed_output.bullets to have 2..8 items - the original one-item
        # lists here passed gate2.screen_candidate() (which only checks
        # collision, not schema shape) but failed real schema validation
        # inside execute_pilot() with a genuine schema_invalid, confirmed
        # directly against gate5_mock_runner.parse_generate_content_response
        # before adding the second bullet to each.
        gibberish_candidate_one = {
            "source_input": " ".join(f"qzxword{i:03d}" for i in range(80)),
            "proposed_output": {"narrative": "Zzxqv lmrpt nvwxa qjksd fyorbin gralket.", "bullets": ["Fjornex caldium pivots duskward.", "Grendol azimuth kelfor pinewrath."], "action_items": ["Nvwxa qjksd three."]},
        }
        gibberish_candidate_two = {
            # Deliberately NOT "wyzcard{i:03d}": that shape shares a trailing
            # "rd" + zero-padded-digits structure with "qzxword{i:03d}" above,
            # which is enough overlapping char-5-grams (e.g. "rd000", "d000 ")
            # across 80 repeats to trip a real protected/pilot-duplicate
            # collision between the two supposedly-distinct gibberish
            # candidates - confirmed directly against gate2.collision_check
            # before picking this replacement shape.
            "source_input": " ".join(f"plombuxfe{i}" for i in range(80)),
            "proposed_output": {"narrative": "Trelvox pindar humsley quockit varnem.", "bullets": ["Blenthar risko duven maplecrest.", "Ostrigal fenwick dromlet yarrow."], "action_items": ["Yendral zoop four."]},
        }
        body_one = self.make_body(gibberish_candidate_one)
        body_two = self.make_body(gibberish_candidate_two)
        screen_one = gate2.screen_candidate(gibberish_candidate_one, self.references, [], [])
        screen_two = gate2.screen_candidate(gibberish_candidate_two, self.references, [gate2.candidate_fields(gibberish_candidate_one)][0], [])
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
                    historical_components=self.v8_components,
                    attestation_validator=lambda _p: self.legacy_attestation(),
                    effective_rate_snapshot_sha256=runner.canonical_hash(rate_path),
                )
                # Must read before the TemporaryDirectory context exits and
                # deletes it (same class of mistake already fixed once above
                # in test_secret_exposure_hard_stops_the_whole_run).
                candidates = [json.loads(l) for l in (output / "candidate_quarantine.jsonl").read_text().splitlines() if l.strip()]
        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(summary["global_stop"], "completed_full_schedule")
        self.assertEqual(summary["cards_completed"], 2)
        self.assertEqual(summary["candidate_quarantine_count"], 2)
        self.assertEqual([c["sequence"] for c in candidates], [1, 2])

    # -- runner-level end-to-end tests -----------------------------------

    def test_real_v9_runner_clean_503_end_to_end(self) -> None:
        # card1 503s all MAX_CARD_ATTEMPTS times (retries-exhausted, continue);
        # card2 gets a genuinely unique, schema-valid, non-colliding candidate
        # (confirmed directly against gate2.screen_candidate() with the real
        # schedule's own prompt references before use here - self.make_body()
        # with no overrides reuses the fixture's own bullets text, which is
        # itself a real known collision against the corpus, not a clean
        # accept) so this test demonstrates a genuine accept through the real
        # runner after a card exhausts its retries, rather than a second
        # collision.
        clean_second_card = {
            "source_input": " ".join(f"zqvornex{i}" for i in range(80)),
            "proposed_output": {"narrative": "Vindrel osmara ketchwyn fallowbrit.", "bullets": ["Naskron velbit forgane trestwick.", "Umbrathil coxen darvello nimwreck."], "action_items": ["Plovenar six."]},
        }
        # NOT bounded to a short schedule here (unlike the direct-engine
        # tests above): runner.execute_full_schedule() calls verify_only()
        # internally, which hard-codes the real 22-slot cost math
        # (single_pass == 187_000 etc.) - patching load_schedule() to a
        # shorter list would make that check itself fail closed before the
        # per-card loop is ever reached. So this test runs against the real
        # schedule and, after its 6 scripted responses are consumed on
        # cards 1-2, legitimately continues into a real, unscripted card 3
        # and hits a genuine script-exhaustion "unexpected_local_error" -
        # the same documented, accepted pattern used in
        # test_continue_past_collision_retry_then_succeed_and_retry_exhaustion
        # before that test was changed to bound its own (direct-engine, no
        # verify_only()) schedule instead.
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp)
            rates = self.rates(root)
            attestation, _value = self.attestation_stub(root, rates)
            campaign = self._fresh_named_campaign_dir()
            transport = ScriptedTransport([(503, b"")] * engine.MAX_CARD_ATTEMPTS + [(200, self.make_body(clean_second_card))])
            events: list[dict] = []
            with patch("gate5_paid_pilot_retry_campaign_v9_gate.date", self._FrozenFictionalDate), patch.object(runner, "local_today", return_value=self.FICTIONAL_DATE):
                result = runner.execute_full_schedule(lambda _t: "local-test-secret", "test-target", transport, attestation, rates, campaign, events.append)
            self.assertGreaterEqual(len(transport.calls), engine.MAX_CARD_ATTEMPTS)
            # card1 (retries-exhausted) and card2 (accepted) both resolve and
            # continue; card3 never gets a scripted response and stops the
            # whole run with a genuine local error - it does not count as
            # "completed".
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
            with patch("gate5_paid_pilot_retry_campaign_v9_gate.date", self._FrozenFictionalDate), patch.object(runner, "local_today", return_value=self.FICTIONAL_DATE):
                with self.assertRaises(runner.Gate5PaidPilotRetryCampaignV9Stop):
                    runner.execute_full_schedule(lambda _t: (_ for _ in ()).throw(RuntimeError("missing local credential")), "test-target", object(), attestation, rates, campaign)
            rows = runner.load_and_verify_campaign(campaign, runner.canonical_hash(attestation))
            self.assertEqual(rows[-1]["campaign_state"], "stopped_nonretryable_outcome")
            self.assertEqual(rows[-1]["failure_code"], "credential_unavailable")
            # zero cost, not zero directory: the run_output directory and its
            # reservation lock ARE created before credential access (same
            # "reserve before touching the credential" convention V8 uses),
            # but no real request/cost row is ever written since the
            # credential read fails before the per-card loop starts - the
            # real invariant is an empty receipt/cost ledger, not a missing
            # directory (confirmed by direct reproduction before fixing this
            # assertion, which had wrongly assumed the directory itself
            # would be absent).
            output = campaign / "run_output"
            self.assertTrue(output.exists())
            self.assertEqual((output / "request_receipts.jsonl").read_bytes(), b"")
            self.assertEqual((output / "cost_ledger.jsonl").read_bytes(), b"")


if __name__ == "__main__":
    unittest.main()
