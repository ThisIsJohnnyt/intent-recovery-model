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
import gate5_paid_pilot_retry_campaign_v11_gate as gate
import gate5_paid_pilot_retry_campaign_v11_runner as runner
import gate5_paid_pilot_v11_engine as engine


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


class Gate5PaidPilotRetryCampaignV11Tests(unittest.TestCase):
    class _FrozenFictionalDate(_dt_date):
        @classmethod
        def today(cls):
            return _dt_date(2099, 1, 1)

    FICTIONAL_DATE = "2099-01-01"

    def setUp(self) -> None:
        self.v10_components = runner.v10_terminal_components()
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
        the one field."""
        return self.make_body({"source_input": " ".join(f"word{i}" for i in range(word_count))})

    def legacy_attestation(self) -> dict:
        return runner._v10_style_legacy_attestation(self.v10_components)

    def rates(self, root: Path, observed: str | None = None) -> Path:
        # Default to the REAL current date, not a hardcoded string -- see
        # V9's/V10's identical fix: engine.load_execution_day_rates() checks
        # observed_date against the real datetime.date.today(), so a stale
        # hardcoded default silently breaks the day after it's written.
        if observed is None:
            observed = _dt_date.today().isoformat()
        value = gate2.load_json(runner.REFERENCE_RATE_PATH)
        value["observed_date"] = observed
        path = root / ("rates-" + observed + ".json")
        path.write_bytes(gate2.canonical_json_bytes(value))
        return path

    def attestation_stub(self, root: Path, rate: Path, execution_date: str = FICTIONAL_DATE) -> tuple[Path, dict]:
        value = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v11_attestation_template.json")
        value.update({**gate.EXPECTED_V10, **gate.EXPECTED_BUILD, **gate.current_build_hashes()})
        value["execution_date"] = execution_date
        value["execution_day_rate_snapshot_sha256"] = runner.canonical_hash(rate)
        value["execution_day_rate_snapshot_status"] = "execution_day_verified"
        value["positive_prepaid_balance_usd_millionths"] = 10_000_000
        value["pilot_ceiling_usd_millionths"] = engine.V11_PILOT_CEILING
        value["reconciliation_stop_usd_millionths"] = engine.V11_RECONCILIATION_STOP
        value["max_card_attempts"] = engine.MAX_CARD_ATTEMPTS
        value["initial_historical_component_count"] = gate.INITIAL_COMPONENT_COUNT
        value["prior_pilot_booked_cost_usd_millionths"] = gate.ATTESTED_BASELINE_COST
        value["v11_worst_case_aggregate_usd_millionths"] = 1_620_501
        for field in gate.TRUE_FIELDS:
            value[field] = True
        path = root / "attestation.json"
        path.write_bytes(gate2.canonical_json_bytes(value))
        return path, value

    def _fresh_named_campaign_dir(self) -> Path:
        path = PACKAGE / f"gate5_paid_pilot_retry_campaign_v11_{self.FICTIONAL_DATE}"
        self.assertFalse(path.exists(), "test fictional-date campaign directory must not already exist")
        self.addCleanup(lambda: __import__("shutil").rmtree(path, ignore_errors=True))
        return path

    # -- structural / re-derivation tests --------------------------------

    def test_v10_terminal_evidence_rederived_and_pinned(self) -> None:
        context = engine.validate_historical_components(self.v10_components)
        self.assertEqual(context, {
            "historical_pilot_component_count": 27,
            "historical_pilot_components_sha256": gate.INITIAL_COMPONENT_MANIFEST_SHA256,
            "historical_pilot_actual_usd_millionths": 685_501,
        })

    def test_v11_reuses_v8_schedule_unchanged(self) -> None:
        slots = engine.load_schedule()
        self.assertEqual(len(slots), 22)
        self.assertEqual(engine.canonical_hash(Path("schedule_v8_m02_start.json")), engine.EXPECTED_V8_SCHEDULE_SHA256)
        first_hash = gate2.sha256_bytes(gate2.canonical_json_bytes(engine.v8.v7_prompt.build_request(slots[0])))
        self.assertEqual(first_hash, engine.EXPECTED_V11_FIRST_REQUEST_SHA256)

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
        self.assertEqual(value["historical_pilot_actual_usd_millionths"], 685_501)
        self.assertEqual(value["single_pass_reservation_usd_millionths"], 187_000)
        self.assertEqual(value["worst_case_aggregate_usd_millionths"], 1_620_501)
        self.assertEqual(value["max_card_attempts"], 5)
        self.assertFalse(value["network_used"])
        self.assertFalse(value["credential_read"])
        self.assertFalse(value["file_output_created"])

    def test_engine_has_no_standalone_credential_entrypoint(self) -> None:
        source = (PACKAGE / "gate5_paid_pilot_v11_engine.py").read_text(encoding="utf-8")
        self.assertNotIn("--execute-full-schedule", source)
        self.assertNotIn("gate4_connectivity_runner", source)
        self.assertIn("dedicated V11 campaign runner", source)

    def test_attestation_template_remains_execution_disabled(self) -> None:
        template = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v11_attestation_template.json")
        self.assertFalse(template["v11_campaign_execution_authorized_by_johnny"])
        self.assertEqual(gate.EXPECTED_BUILD["v11_first_request_sha256"], engine.EXPECTED_V11_FIRST_REQUEST_SHA256)

    def test_campaign_directory_naming(self) -> None:
        self.assertIsNotNone(runner.CAMPAIGN_DIRECTORY_RE.fullmatch("gate5_paid_pilot_retry_campaign_v11_2026-08-18"))
        self.assertIsNone(runner.CAMPAIGN_DIRECTORY_RE.fullmatch("gate5_paid_pilot_retry_campaign_v10_2026-08-18"))
        self.assertIsNone(runner.CAMPAIGN_DIRECTORY_RE.fullmatch("gate5_paid_pilot_retry_campaign_v11_2026-08-18_extra"))

    # -- the stopword-filtering fix itself, in isolation ------------------

    def test_stopword_only_overlap_no_longer_collides_on_token_jaccard(self) -> None:
        """Direct proof the fix does what it claims: two texts that share
        nothing but common function words score 0.0 stopword-filtered
        token-Jaccard (down from a real, threshold-crossing 0.3 unfiltered),
        while character-5-gram scoring -- deliberately untouched -- is
        unaffected by the fix either way."""
        candidate = "the cat sat on the mat and then it went to the door for the food"
        reference = "the truck drove to the depot and then it waited at the gate for the driver"
        old = gate2.collision_check(candidate, [("ref", reference)])
        new = gate2.collision_check_stopword_filtered(candidate, [("ref", reference)])
        self.assertAlmostEqual(old["maximum_token_jaccard"]["score"], 0.3)
        self.assertEqual(new["maximum_token_jaccard"]["score"], 0.0)
        self.assertEqual(old["maximum_character_5gram_jaccard"], new["maximum_character_5gram_jaccard"])

    def test_genuine_content_overlap_still_collides_under_stopword_filtering(self) -> None:
        """The fix must not become so lax it stops catching real duplication:
        two texts sharing genuine content words (not just function words)
        still trigger token-Jaccard collision under stopword-filtered
        scoring, at an unchanged or only mildly reduced score."""
        candidate = "schedule a follow up call with the vendor about the invoice discrepancy next Tuesday"
        reference = "schedule a follow up call with the vendor regarding the invoice discrepancy next Tuesday afternoon"
        new = gate2.collision_check_stopword_filtered(candidate, [("ref", reference)])
        self.assertTrue(new["fatal"])
        self.assertGreaterEqual(new["maximum_token_jaccard"]["score"], gate2.TOKEN_JACCARD_THRESHOLD)

    def test_core_new_v11_behavior_real_corpus_flip_from_rejected_to_accepted(self) -> None:
        """The core new V11 behavior, exercised directly through the real
        111-record corpus (not a synthetic two-sentence pair): a candidate
        engineered to share mostly function words with the real reference
        corpus is a real, threshold-crossing collision under
        gate2.screen_candidate() (V10's scoring) and a real, clean accept
        under gate2.screen_candidate_stopword_filtered() (V11's scoring) --
        both computed here from the same live-loaded quarantine corpus."""
        candidate = {
            "source_input": " ".join(f"zqfwordinput{i:03d}" for i in range(80)),
            "proposed_output": {
                "narrative": "The plombicorn hazelwrenith kestraline was noted and then it was reviewed for the tuvalquin.",
                "bullets": [
                    "It was the case that the plombicorn was reviewed and then it was noted for the tuvalquin at the meeting.",
                    "The kestraline was set up for the northern hazelwrenith on the following day for the review.",
                ],
                "action_items": ["Circle back regarding plombicorn concerning tuvalquin near the northerly kestraline zone."],
            },
        }
        old = gate2.screen_candidate(candidate, self.references, [], [])
        new = gate2.screen_candidate_stopword_filtered(candidate, self.references, [], [])
        self.assertTrue(old["fatal"], "fixture must be a real collision under V10's unfiltered scoring")
        self.assertFalse(new["fatal"], new.get("fatal_reasons"))

    def test_short_string_stopword_removal_can_raise_not_only_lower_token_jaccard(self) -> None:
        """A real, narrow edge case found during this build's own
        self-review, kept here permanently as documented, intentional
        behavior rather than silently avoided: for very short strings,
        stopword removal does not only ever lower token-Jaccard. Removing a
        stopword present on only one side of a comparison (not shared)
        shrinks the Jaccard union without shrinking the intersection, which
        can *raise* the score. Real example: "Plovenar six." (a fabricated
        2-token bullet) scores 0.142857 (non-fatal, just under the 0.15
        threshold) against a real corpus reference under V10's unfiltered
        scoring, and 0.2 (fatal) against that same reference under V11's
        stopword-filtered scoring -- the opposite direction from what
        stopword filtering is intended to do on typical, longer text. This
        does not undermine the fix's real-world effect (see the dominant,
        many-reference fan-out pattern this version's proposal documents
        from V10's real run), but it is real and worth keeping visible."""
        text = "Plovenar six."
        old = gate2.collision_check(text, self.references)
        new = gate2.collision_check_stopword_filtered(text, self.references)
        self.assertAlmostEqual(old["maximum_token_jaccard"]["score"], 0.142857143, places=6)
        self.assertFalse(old["fatal"])
        self.assertAlmostEqual(new["maximum_token_jaccard"]["score"], 0.2, places=6)
        self.assertTrue(new["fatal"])

    # -- engine loop behavior, direct (no runner/attestation overhead) ---

    def test_continue_past_collision_and_schema_invalid_but_not_secret_exposure(self) -> None:
        """Same continue-past ruleset as V10, unchanged: a collision and a
        genuine schema_invalid both continue the run; secret_exposure still
        hard-stops it immediately. The only thing different from V10's
        equivalent test is that collision scoring is now stopword-filtered
        -- this fixture's own bullets text still collides under it (fewer
        reasons than under V10, but still fatal), so the outcome sequence is
        unchanged."""
        accept_body = self.make_body()  # still a real collision under stopword-filtered scoring too
        schema_invalid_body = self.make_short_source_input_body(78)
        secret_body = self.make_body({"source_input": self.base_candidate["source_input"] + " AIzaFAKETESTKEYFAKETESTKEYFAKETESTKEY01"})
        script = [
            (200, accept_body),         # card1: collision, continue
            (200, schema_invalid_body), # card2: genuine schema_invalid, continue
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
                    historical_components=self.v10_components,
                    attestation_validator=lambda _p: self.legacy_attestation(),
                    effective_rate_snapshot_sha256=runner.canonical_hash(rate_path),
                    progress=events.append,
                )
        self.assertEqual(len(transport.calls), 3)
        self.assertEqual(summary["requests_made"], 3)
        self.assertEqual(summary["rejection_count"], 3)
        self.assertEqual(summary["output_collision_diagnostic_count"], 1)
        self.assertEqual(summary["schema_conformance_diagnostic_count"], 1)
        self.assertEqual(summary["cards_completed"], 2)
        self.assertEqual(summary["global_stop"], "secret_exposure")
        self.assertEqual([e["outcome"] for e in events], [
            "proposed_output:output.bullets:01:protected_collision",
            "schema_invalid",
            "secret_exposure",
        ])

    def test_schema_invalid_alongside_collision_continuation_uses_independent_sequencing(self) -> None:
        """Regression guard for the exact bug class V9's build caught and
        V10's real crash confirmed: collision and schema diagnostics must
        each get correctly independent dense sequencing when both accumulate
        in the same run."""
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
                    historical_components=self.v10_components,
                    attestation_validator=lambda _p: self.legacy_attestation(),
                    effective_rate_snapshot_sha256=runner.canonical_hash(rate_path),
                )
        self.assertEqual(summary["global_stop"], "completed_full_schedule")
        self.assertEqual(summary["cards_completed"], 3)
        self.assertEqual(summary["output_collision_diagnostic_count"], 2)
        self.assertEqual(summary["schema_conformance_diagnostic_count"], 1)

    def test_two_schema_invalid_cards_in_one_run_does_not_crash(self) -> None:
        """Regression guard carried forward from V10: gate5_schema_conformance_
        evidence.verify_chain() must accept an arbitrary-length chain, not
        just one row."""
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
                    historical_components=self.v10_components,
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
                historical_components=self.v10_components,
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
        screen_one = gate2.screen_candidate_stopword_filtered(gibberish_candidate_one, self.references, [], [])
        screen_two = gate2.screen_candidate_stopword_filtered(gibberish_candidate_two, self.references, gate2.candidate_fields(gibberish_candidate_one), [])
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
                    historical_components=self.v10_components,
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

    def test_real_v11_runner_clean_503_end_to_end(self) -> None:
        clean_second_card = {
            "source_input": " ".join(f"zqvornex{i}" for i in range(80)),
            # action_items intentionally longer/more distinctive than V10's
            # equivalent fixture ("Plovenar six.") -- that 2-token bullet was
            # found, during this build's own self-review, to be a real,
            # narrow edge case: for very short strings, removing a stopword
            # that appears on only one side (not shared) shrinks the
            # Jaccard union without shrinking the intersection, which can
            # *raise* the score rather than lower it (real example found:
            # "Plovenar six." scored 0.142857 unfiltered, non-fatal, against
            # a real corpus reference -- and 0.2 stopword-filtered, fatal,
            # against that same reference). This is a real, inherent
            # property of Jaccard similarity on short strings, not a code
            # defect; documented in the V11 proposal. Avoided here by using
            # a longer, fully invented action item so this test exercises
            # 503-retry-then-accept behavior, not a collision-scoring edge
            # case that has its own dedicated tests above.
            "proposed_output": {"narrative": "Vindrel osmara ketchwyn fallowbrit.", "bullets": ["Naskron velbit forgane trestwick.", "Umbrathil coxen darvello nimwreck."], "action_items": ["Plovenar quintessa harkonwyn drendal fivex."]},
        }
        # NOT bounded to a short schedule: runner.execute_full_schedule() calls
        # verify_only() internally, which hard-codes the real 22-slot cost math
        # -- so this test runs against the real schedule and, after its 6
        # scripted responses are consumed on cards 1-2, legitimately continues
        # into a real, unscripted card 3 and hits a genuine script-exhaustion
        # "unexpected_local_error" -- same documented pattern used in V9's and
        # V10's equivalent tests.
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp)
            rates = self.rates(root)
            attestation, _value = self.attestation_stub(root, rates)
            campaign = self._fresh_named_campaign_dir()
            transport = ScriptedTransport([(503, b"")] * engine.MAX_CARD_ATTEMPTS + [(200, self.make_body(clean_second_card))])
            events: list[dict] = []
            with patch("gate5_paid_pilot_retry_campaign_v11_gate.date", self._FrozenFictionalDate), patch.object(runner, "local_today", return_value=self.FICTIONAL_DATE):
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
            with patch("gate5_paid_pilot_retry_campaign_v11_gate.date", self._FrozenFictionalDate), patch.object(runner, "local_today", return_value=self.FICTIONAL_DATE):
                with self.assertRaises(runner.Gate5PaidPilotRetryCampaignV11Stop):
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
