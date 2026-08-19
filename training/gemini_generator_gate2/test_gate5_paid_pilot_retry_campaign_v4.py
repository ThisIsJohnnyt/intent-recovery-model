from __future__ import annotations

import copy
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import gate2
import gate5_paid_pilot_retry_campaign_v4_gate as gate
import gate5_paid_pilot_retry_campaign_v4_runner as runner
import gate5_paid_pilot_runner as pilot
import gate5_schema_conformance_evidence as schema_evidence
import gate5_mock_runner as response_parser


PACKAGE = Path(__file__).resolve().parent


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_bytes(b"".join(gate2.canonical_json_bytes(row) for row in rows))


class Gate5PaidPilotRetryCampaignV4Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.valid = {
            "source_input": " ".join(["word"] * 80),
            "proposed_output": {"narrative": "One sentence.", "bullets": ["one", "two"], "action_items": ["act"]},
        }

    def rates(self, root: Path, observed: str = "2026-08-17") -> Path:
        value = gate2.load_json(runner.REFERENCE_RATE_PATH); value["observed_date"] = observed
        path = root / ("rates-" + observed + ".json"); path.write_bytes(gate2.canonical_json_bytes(value)); return path

    def attestation_stub(self, root: Path, rate: Path, execution_date: str = "2026-08-17") -> tuple[Path, dict]:
        value = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v4_attestation_template.json")
        value.update({**gate.EXPECTED_BUILD, **gate.EXPECTED_V3})
        value["execution_date"] = execution_date; value["execution_day_rate_snapshot_sha256"] = runner.canonical_hash(rate); value["execution_day_rate_snapshot_status"] = "execution_day_verified"; value["positive_prepaid_balance_usd_millionths"] = 10_000_000
        for field in gate.TRUE_FIELDS: value[field] = True
        path = root / "attestation.json"; path.write_bytes(gate2.canonical_json_bytes(value)); return path, value

    def schema_error(self, changed: dict) -> gate2.ResponseSchemaError:
        with self.assertRaises(gate2.ResponseSchemaError) as caught: gate2.parse_response(gate2.canonical_json_bytes(changed))
        return caught.exception

    def fake_output(self, output: Path, components: list[dict], outcome: str) -> dict:
        output.mkdir(); context = pilot.validate_historical_components(components); slot = pilot.load_schedule()[0]
        request_hash, raw_hash = "a" * 64, "b" * 64
        status = 503 if outcome == "503" else 200
        stop = "unexpected_http_status" if outcome == "503" else outcome
        schema_row = None
        if outcome == "schema_invalid":
            changed = copy.deepcopy(self.valid); changed["unexpected-canary-key"] = "DO-NOT-PERSIST-CANDIDATE-CANARY"
            schema_row = schema_evidence.build_row(1, slot, request_hash, raw_hash, self.schema_error(changed), None)
        receipt = pilot._receipt(1, slot, request_hash, raw_hash, status, None, "rejected", stop, None)
        rejection = pilot._rejection(1, request_hash, raw_hash, stop, None, None, schema_row["row_hash"] if schema_row else None)
        cost = pilot._cost_row(1, slot, request_hash, raw_hash, receipt["row_hash"], 10_680, 10_680, 10_680, None, "rejected", stop, "f" * 64, None, context)
        (output / "pilot_reservation.json").write_bytes(gate2.canonical_json_bytes({"artifact": "synthetic"}))
        write_jsonl(output / "request_receipts.jsonl", [receipt]); write_jsonl(output / "rejection_ledger.jsonl", [rejection]); write_jsonl(output / "cost_ledger.jsonl", [cost]); write_jsonl(output / "output_collision_diagnostics.jsonl", []); write_jsonl(output / "schema_conformance_diagnostics.jsonl", [schema_row] if schema_row else []); write_jsonl(output / "candidate_quarantine.jsonl", [])
        summary = {"artifact": "gemini_generator_gate5_paid_pilot_summary", "completed_slots": 1, "candidate_quarantine_count": 0, "rejection_count": 1, "output_collision_diagnostic_count": 0, "schema_conformance_diagnostic_count": 1 if schema_row else 0, "cumulative_actual_usd_millionths": 10_680, **context, "aggregate_pilot_actual_usd_millionths": context["historical_pilot_actual_usd_millionths"] + 10_680, "global_stop": stop, "network_used": True, "credential_read": True, "candidate_review_performed": False, "corpus_mutation_performed": False, "receipt_chain_head": receipt["row_hash"], "rejection_chain_head": rejection["row_hash"], "output_collision_diagnostic_chain_head": None, "schema_conformance_diagnostic_chain_head": schema_row["row_hash"] if schema_row else None, "cost_chain_head": cost["row_hash"], "candidate_chain_head": None}
        summary["summary_sha256"] = gate2.sha256_bytes(gate2.canonical_json_bytes(summary)); (output / "run_summary.json").write_bytes(gate2.canonical_json_bytes(summary)); return summary

    def pause_campaign(self, root: Path, pause_date: str = "2026-08-17") -> tuple[Path, Path, Path, dict]:
        rates = self.rates(root, "2026-08-17"); attestation, value = self.attestation_stub(root, rates, pause_date); campaign = root / "campaign"; digest = runner.canonical_hash(attestation); runner.initialize_campaign(campaign, value, digest)
        components = runner.initial_components(); sequence = 1; output = campaign / "attempt_001_pilot_output"
        rows = runner._read_jsonl(campaign / runner.LEDGER_NAME); last = rows[-1]; context = pilot.validate_historical_components(components)
        lock = {"artifact": "gemini_generator_gate5_paid_pilot_retry_campaign_v4_attempt_lock", "sequence": 1, "created_utc": runner.utc_now(), "prior_state_row_hash": last["row_hash"], **context, "attestation_sha256": digest, "output_directory_name": output.name, "effective_rate_snapshot_sha256": last["effective_rate_snapshot_sha256"], "effective_rate_date": pause_date, "state": "reserved_before_credential_read"}; lock["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(lock)); runner._new_file(runner._lock_path(campaign, 1), gate2.canonical_json_bytes(lock)); lock_hash = runner.canonical_hash(runner._lock_path(campaign, 1))
        runner._append(campaign / runner.LEDGER_NAME, runner._state_row("attempt_reserved", 1, "attempt_reserved", 1, context, lock_hash, None, output.name, None, None, None, last["effective_rate_snapshot_sha256"], pause_date, last["row_hash"], digest))
        self.fake_output(output, components, "schema_invalid"); completion = runner._validate_attempt_output(output, components)[0]; runner.complete_attempt(campaign, sequence, components, digest, completion)
        return campaign, attestation, rates, completion

    def review(self, root: Path, campaign: Path, attestation: Path, mode: str, today: str, fresh_rate: Path | None = None) -> Path:
        rows, components = runner.load_and_verify_campaign(campaign, runner.canonical_hash(attestation)); paused = rows[-1]; completion = gate2.load_json(runner._completion_path(campaign, paused["sequence"])); context = pilot.validate_historical_components(components); prior_tuple = runner._rate_tuple(runner.REFERENCE_RATE_PATH)
        value = gate2.load_json(PACKAGE / "gate5_paid_pilot_retry_campaign_v4_review_template.json")
        value.update({"review_mode": mode, "pause_local_date": paused["effective_rate_date"], "review_local_date": today, "v4_final_attestation_sha256": runner.canonical_hash(attestation), "paused_campaign_state_row_sha256": paused["row_hash"], "paused_attempt_sequence": paused["sequence"], "paused_attempt_lock_sha256": paused["attempt_lock_file_sha256"], "paused_attempt_completion_sha256": paused["completion_file_sha256"], "paused_output_evidence_sha256": completion["output_evidence_sha256"], "pause_stop_code": paused["pause_stop_code"], "schema_conformance_diagnostic_row_sha256": paused["schema_conformance_diagnostic_row_sha256"], "current_attempts_reserved": paused["attempts_reserved"], "current_attempts_remaining": 4 - paused["attempts_reserved"], "current_historical_component_count": context["historical_pilot_component_count"], "current_historical_components_sha256": context["historical_pilot_components_sha256"], "current_historical_actual_usd_millionths": context["historical_pilot_actual_usd_millionths"], "prior_rate_snapshot_sha256": paused["effective_rate_snapshot_sha256"], "prior_rate_tuple": prior_tuple})
        if mode == "same_day": value.update({"effective_rate_snapshot_sha256": paused["effective_rate_snapshot_sha256"], "effective_rate_tuple": prior_tuple})
        else:
            fresh_fields = ("execution_day_rate_snapshot_verified", "paid_tier_confirmed_that_day", "prepay_plan_confirmed_that_day", "auto_reload_off_that_day", "billing_account_currently_isolated_for_pilot", "no_unexpected_billing_activity_since_pause", "no_other_gemini_api_activity_since_pause", "key_remains_in_windows_credential_manager", "both_exact_models_available_and_not_deprecated", "generate_content_endpoint_confirmed_for_both_models", "common_low_thinking_confirmed_for_both_models", "structured_output_confirmed_for_both_models")
            for field in fresh_fields: value[field] = True
            value["positive_prepaid_balance_usd_millionths"] = 10_000_000; value["effective_rate_snapshot_sha256"] = runner.canonical_hash(fresh_rate); value["effective_rate_tuple"] = runner._rate_tuple(fresh_rate)
        value["record_sha256"] = gate2.sha256_bytes(gate2.canonical_json_bytes({key: item for key, item in value.items() if key != "record_sha256"})); path = root / ("review-" + mode + ".json"); path.write_bytes(gate2.canonical_json_bytes(value)); return path

    def test_all_structured_reason_kinds_and_legacy_messages(self) -> None:
        cases = []
        cases.append((b"not json", "response_json_invalid"))
        changed = copy.deepcopy(self.valid); changed["x"] = "secret candidate value"; cases.append((gate2.canonical_json_bytes(changed), "top_level_keys_invalid"))
        changed = copy.deepcopy(self.valid); changed["source_input"] = 3; cases.append((gate2.canonical_json_bytes(changed), "source_input_not_plain_string"))
        changed = copy.deepcopy(self.valid); changed["source_input"] = "short"; cases.append((gate2.canonical_json_bytes(changed), "source_input_word_count_out_of_range"))
        changed = copy.deepcopy(self.valid); changed["proposed_output"]["x"] = "hidden"; cases.append((gate2.canonical_json_bytes(changed), "proposed_output_keys_invalid"))
        changed = copy.deepcopy(self.valid); changed["proposed_output"]["narrative"] = 3; cases.append((gate2.canonical_json_bytes(changed), "narrative_not_plain_string"))
        changed = copy.deepcopy(self.valid); changed["proposed_output"]["narrative"] = "no punctuation"; cases.append((gate2.canonical_json_bytes(changed), "narrative_sentence_count_out_of_range"))
        changed = copy.deepcopy(self.valid); changed["proposed_output"]["bullets"] = "not list"; cases.append((gate2.canonical_json_bytes(changed), "list_not_array"))
        changed = copy.deepcopy(self.valid); changed["proposed_output"]["bullets"] = []; cases.append((gate2.canonical_json_bytes(changed), "list_item_count_out_of_range"))
        changed = copy.deepcopy(self.valid); changed["proposed_output"]["bullets"][0] = 3; cases.append((gate2.canonical_json_bytes(changed), "list_item_not_plain_string"))
        for raw, kind in cases:
            with self.subTest(kind=kind), self.assertRaises(gate2.ResponseSchemaError) as caught: gate2.parse_response(raw)
            self.assertEqual(caught.exception.structured_reason["kind"], kind); self.assertIsInstance(caught.exception, gate2.Gate2Error); self.assertTrue(str(caught.exception))

    def test_schema_evidence_never_contains_candidate_or_key_name(self) -> None:
        changed = copy.deepcopy(self.valid); changed["UNIQUE-KEY-CANARY"] = "UNIQUE-CANDIDATE-TEXT-CANARY"
        row = schema_evidence.build_row(1, pilot.load_schedule()[0], "a" * 64, "b" * 64, self.schema_error(changed), None); encoded = gate2.canonical_json_bytes(row)
        self.assertNotIn(b"UNIQUE-KEY-CANARY", encoded); self.assertNotIn(b"UNIQUE-CANDIDATE-TEXT-CANARY", encoded); self.assertEqual(row["structured_reason"]["extra_key_count"], 1)

    def test_schema_reason_tampering_and_secret_are_rejected(self) -> None:
        changed = copy.deepcopy(self.valid); changed["x"] = "value"; row = schema_evidence.build_row(1, pilot.load_schedule()[0], "a" * 64, "b" * 64, self.schema_error(changed), None)
        tampered = copy.deepcopy(row); tampered["structured_reason"]["raw_key"] = "x"; tampered["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes({k: v for k, v in tampered.items() if k != "row_hash"}))
        with self.assertRaises(schema_evidence.SchemaConformanceEvidenceError): schema_evidence.validate_row(tampered)

    def test_real_paid_engine_persists_only_schema_reason_and_preserves_core_on_io_failure(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); rate_value = gate2.load_json(runner.REFERENCE_RATE_PATH); rate_value["observed_date"] = runner.local_today(); rates = root / "rates.json"; rates.write_bytes(gate2.canonical_json_bytes(rate_value))
            attestation = gate2.load_json(PACKAGE / "gate5_pre_execution_attestation_template.json")
            attestation.update({"final_provider_contract_sha256": pilot.canonical_hash(pilot.CONTRACT_PATH), "final_provider_schema_sha256": pilot.canonical_hash(pilot.PROVIDER_SCHEMA_PATH), "live_validated_request_envelope_sha256": gate2.sha256_bytes(gate2.canonical_json_bytes(pilot.redesign.build_request(pilot.load_schedule()[0]))), "successful_corrected_schema_diagnostic_receipt_row_sha256": pilot.verify_successful_diagnostic_evidence(), "flash_lite_live_validated_request_envelope_sha256": gate2.sha256_bytes(gate2.canonical_json_bytes(pilot.redesign.build_request(pilot.load_schedule()[1]))), "successful_flash_lite_receipt_row_sha256": pilot.verify_successful_flash_lite_evidence(), "execution_day_rate_snapshot_sha256": pilot.canonical_hash(rates), "original_failed_pilot_booked_cost_usd_millionths": pilot.ORIGINAL_FAILED_PILOT_BOOKED_COST, "completed_fresh_pilot_booked_cost_usd_millionths": pilot.COMPLETED_FRESH_PILOT_BOOKED_COST, "prior_pilot_booked_cost_usd_millionths": pilot.PRIOR_PILOT_BOOKED_COST}); attestation.update(pilot.verify_fresh_attempt_evidence()); attestation.update(pilot.verify_third_attempt_evidence()); attestation_path = root / "legacy-attestation.json"; attestation_path.write_bytes(gate2.canonical_json_bytes(attestation))
            fixture = copy.deepcopy(response_parser.load_fixtures()["valid_stop_with_usage"]); candidate = json.loads(fixture["candidates"][0]["content"]["parts"][0]["text"]); candidate["UNEXPECTED-KEY-CANARY"] = "UNIQUE-CANDIDATE-TEXT-CANARY"; fixture["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(candidate); body = gate2.canonical_json_bytes({key: value for key, value in fixture.items() if key != "id"})
            class Transport:
                calls = 0
                def post(self, *_args, **_kwargs): self.calls += 1; return pilot.ProviderResponse(200, {}, body)
            transport = Transport(); output = root / "success"; summary = pilot.execute_pilot(lambda _: "local-test-secret", "test", transport, attestation_path, rates, output, attestation_validator=lambda _: attestation)
            self.assertEqual(summary["global_stop"], "schema_invalid"); self.assertEqual(summary["schema_conformance_diagnostic_count"], 1)
            diagnostic_bytes = (output / "schema_conformance_diagnostics.jsonl").read_bytes(); self.assertNotIn(b"UNEXPECTED-KEY-CANARY", diagnostic_bytes); self.assertNotIn(b"UNIQUE-CANDIDATE-TEXT-CANARY", diagnostic_bytes)
            rejection = json.loads((output / "rejection_ledger.jsonl").read_text()); diagnostic = json.loads(diagnostic_bytes); self.assertEqual(rejection["schema_conformance_diagnostic_row_hash"], diagnostic["row_hash"])
            original_append = pilot._append
            def fail_schema(path, row):
                if path.name == "schema_conformance_diagnostics.jsonl": raise pilot.Gate5PilotStop("output_path_unavailable")
                original_append(path, row)
            transport.calls = 0; failed = root / "failed"
            with patch.object(pilot, "_append", side_effect=fail_schema): failed_summary = pilot.execute_pilot(lambda _: "local-test-secret", "test", transport, attestation_path, rates, failed, attestation_validator=lambda _: attestation)
            self.assertEqual(failed_summary["global_stop"], "schema_conformance_diagnostic_persistence_failed"); self.assertEqual(transport.calls, 1); self.assertEqual((failed / "schema_conformance_diagnostics.jsonl").read_bytes(), b"")
            self.assertTrue((failed / "request_receipts.jsonl").read_bytes()); self.assertTrue((failed / "rejection_ledger.jsonl").read_bytes()); self.assertTrue((failed / "cost_ledger.jsonl").read_bytes())

    def test_v3_is_rederived_and_immutable(self) -> None:
        before = {relative: runner.canonical_hash(PACKAGE / relative) for relative in runner.V3_TOP_HASHES}
        context = runner.verify_initial_evidence(); self.assertEqual(context["historical_pilot_actual_usd_millionths"], 85_440); self.assertEqual(context["historical_pilot_component_count"], 9)
        self.assertEqual(before, {relative: runner.canonical_hash(PACKAGE / relative) for relative in runner.V3_TOP_HASHES})

    def test_verify_only_and_attestation_remain_execution_gated(self) -> None:
        result = runner.verify_only(); self.assertFalse(result["network_used"] or result["credential_read"] or result["file_output_created"]); self.assertEqual(result["worst_case_aggregate_usd_millionths"], 901_440)
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); rates = self.rates(root); attestation, _ = self.attestation_stub(root, rates); value = gate2.load_json(attestation); value["v4_campaign_execution_authorized_by_johnny"] = False; attestation.write_bytes(gate2.canonical_json_bytes(value))
            with self.assertRaisesRegex(gate.Gate5PaidPilotRetryCampaignV4AttestationError, "unconfirmed"): gate.validate_attestation(attestation)

    def test_only_whitelist_pauses_and_schema_requires_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); components = runner.initial_components()
            for outcome, expected in (("schema_invalid", "paused_pending_review"), ("finish_reason_invalid", "paused_pending_review"), ("extra_key", "paused_pending_review"), ("size_limit_failed", "paused_pending_review"), ("unexpected_local_error", "stopped_nonretryable_outcome")):
                output = root / outcome; self.fake_output(output, components, outcome); self.assertEqual(runner._validate_attempt_output(output, components)[2], expected)
            schema_path = root / "schema_invalid" / "schema_conformance_diagnostics.jsonl"; schema_path.write_bytes(b"")
            with self.assertRaises(runner.Gate5PaidPilotRetryCampaignV4Stop): runner._validate_attempt_output(root / "schema_invalid", components)

    def test_same_day_review_is_one_use_and_no_credential(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); campaign, attestation, _rates, _ = self.pause_campaign(root); review = self.review(root, campaign, attestation, "same_day", "2026-08-17")
            with patch.object(runner, "local_today", return_value="2026-08-17"):
                row = runner.confirm_pause_review(review, attestation, campaign); self.assertEqual(row["campaign_state"], "active_after_review")
                with self.assertRaisesRegex(runner.Gate5PaidPilotRetryCampaignV4Stop, "pause_review_invalid"): runner.confirm_pause_review(review, attestation, campaign)

    def test_next_day_review_accepts_equal_rates_and_rejects_drift(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); campaign, attestation, _rates, _ = self.pause_campaign(root, "2026-08-16"); fresh = self.rates(root, "2026-08-17"); review = self.review(root, campaign, attestation, "next_day", "2026-08-17", fresh)
            with patch.object(runner, "local_today", return_value="2026-08-17"): self.assertEqual(runner.confirm_pause_review(review, attestation, campaign, fresh)["campaign_state"], "active_after_review")
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); campaign, attestation, _rates, _ = self.pause_campaign(root, "2026-08-16"); fresh = self.rates(root, "2026-08-17"); changed = gate2.load_json(fresh); changed["rates"]["gemini-3.7-flash"]["input"] += 1; fresh.write_bytes(gate2.canonical_json_bytes(changed)); review = self.review(root, campaign, attestation, "next_day", "2026-08-17", fresh)
            with patch.object(runner, "local_today", return_value="2026-08-17"), self.assertRaisesRegex(runner.Gate5PaidPilotRetryCampaignV4Stop, "pause_review_invalid"): runner.confirm_pause_review(review, attestation, campaign, fresh)

    def test_next_day_review_left_until_day_n_plus_2_fails_at_reservation(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); campaign, attestation, _rates, _ = self.pause_campaign(root, "2026-08-16"); fresh = self.rates(root, "2026-08-17"); review = self.review(root, campaign, attestation, "next_day", "2026-08-17", fresh)
            with patch.object(runner, "local_today", return_value="2026-08-17"): runner.confirm_pause_review(review, attestation, campaign, fresh)
            with patch.object(runner, "local_today", return_value="2026-08-18"), self.assertRaisesRegex(runner.Gate5PaidPilotRetryCampaignV4Stop, "execution_day_rate_snapshot_mismatch"): runner.reserve_attempt(campaign, runner.canonical_hash(attestation), fresh)
            self.assertFalse((campaign / "attempt_002_lock.json").exists())

    def test_two_day_gap_and_missing_fresh_fact_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); campaign, attestation, _rates, _ = self.pause_campaign(root, "2026-08-15"); fresh = self.rates(root, "2026-08-17"); review = self.review(root, campaign, attestation, "next_day", "2026-08-17", fresh)
            with patch.object(runner, "local_today", return_value="2026-08-17"), self.assertRaisesRegex(runner.Gate5PaidPilotRetryCampaignV4Stop, "pause_review_invalid"): runner.confirm_pause_review(review, attestation, campaign, fresh)

    def test_fourth_attempt_is_terminal_and_money_is_monotonic(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); components = runner.initial_components()
            for sequence in range(1, 4): components.append(pilot._historical_component(len(components) + 1, f"prior-v4-{sequence}", 204_000, "d" * 64, "transient_http_503", components[-1]["row_hash"]))
            output = root / "fourth"; self.fake_output(output, components, "503"); completion = runner._validate_attempt_output(output, components)[0]
            self.assertEqual(completion["campaign_state_after"], "attempt_cap_reached"); final = pilot.validate_historical_components([*components, completion["component"]]); self.assertEqual(final["historical_pilot_actual_usd_millionths"], 85_440 + 3 * 204_000 + 10_680); self.assertLessEqual(final["historical_pilot_actual_usd_millionths"], 901_440)

    def test_review_field_tampering_fails_without_state_mutation(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); campaign, attestation, _rates, _ = self.pause_campaign(root); review = self.review(root, campaign, attestation, "same_day", "2026-08-17"); before = (campaign / runner.LEDGER_NAME).read_bytes(); value = gate2.load_json(review); value["current_attempts_remaining"] += 1; value["record_sha256"] = gate2.sha256_bytes(gate2.canonical_json_bytes({k: v for k, v in value.items() if k != "record_sha256"})); review.write_bytes(gate2.canonical_json_bytes(value))
            with patch.object(runner, "local_today", return_value="2026-08-17"), self.assertRaisesRegex(runner.Gate5PaidPilotRetryCampaignV4Stop, "pause_review_invalid"): runner.confirm_pause_review(review, attestation, campaign)
            self.assertEqual((campaign / runner.LEDGER_NAME).read_bytes(), before); self.assertFalse(runner._review_lock_path(campaign, 1).exists())

    def test_two_pause_cycles_consume_attempts_and_preserve_live_cost(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); campaign, attestation, rates, _ = self.pause_campaign(root); digest = runner.canonical_hash(attestation); review1 = self.review(root, campaign, attestation, "same_day", "2026-08-17")
            with patch.object(runner, "local_today", return_value="2026-08-17"):
                runner.confirm_pause_review(review1, attestation, campaign); sequence, components = runner.reserve_attempt(campaign, digest, rates)
                self.assertEqual(sequence, 2); self.fake_output(runner._output_path(campaign, sequence), components, "finish_reason_invalid"); completion = runner._validate_attempt_output(runner._output_path(campaign, sequence), components)[0]; runner.complete_attempt(campaign, sequence, components, digest, completion)
                review2 = self.review(root, campaign, attestation, "same_day", "2026-08-17"); runner.confirm_pause_review(review2, attestation, campaign)
            rows, final_components = runner.load_and_verify_campaign(campaign, digest); self.assertEqual(rows[-1]["attempts_reserved"], 2); self.assertEqual(rows[-1]["campaign_state"], "active_after_review"); self.assertEqual(pilot.validate_historical_components(final_components)["historical_pilot_actual_usd_millionths"], 85_440 + 2 * 10_680)

    def test_recovery_uses_existing_evidence_and_never_resends(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); rates = self.rates(root); attestation, value = self.attestation_stub(root, rates); campaign = root / "campaign"; digest = runner.canonical_hash(attestation); runner.initialize_campaign(campaign, value, digest)
            with patch.object(runner, "local_today", return_value="2026-08-17"): sequence, components = runner.reserve_attempt(campaign, digest, rates)
            self.fake_output(runner._output_path(campaign, sequence), components, "503"); recovered = runner.recover_incomplete_attempt(attestation, campaign); self.assertEqual(recovered["campaign_state_after"], "active_after_clean_503")
            with self.assertRaisesRegex(runner.Gate5PaidPilotRetryCampaignV4Stop, "no_incomplete_attempt_to_recover"): runner.recover_incomplete_attempt(attestation, campaign)

    def test_concurrent_review_has_one_winner(self) -> None:
        with tempfile.TemporaryDirectory(dir=PACKAGE) as temp:
            root = Path(temp); campaign, attestation, _rates, _ = self.pause_campaign(root); review = self.review(root, campaign, attestation, "same_day", "2026-08-17"); outcomes = []
            def confirm():
                try: outcomes.append(runner.confirm_pause_review(review, attestation, campaign))
                except Exception as exc: outcomes.append(exc)
            with patch.object(runner, "local_today", return_value="2026-08-17"):
                a = threading.Thread(target=confirm); b = threading.Thread(target=confirm); a.start(); b.start(); a.join(5); b.join(5)
            rows = runner._read_jsonl(campaign / runner.LEDGER_NAME); self.assertEqual(sum(row["event"] == "pause_review_confirmed" for row in rows), 1)


if __name__ == "__main__": unittest.main()
