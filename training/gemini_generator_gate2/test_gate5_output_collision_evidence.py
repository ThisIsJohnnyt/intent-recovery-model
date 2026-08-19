from __future__ import annotations

import copy
import json
import math
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import gate2
import gate5_mock_runner as response_parser
import gate5_output_collision_evidence as evidence
import gate5_paid_pilot_runner as pilot


LABEL = "acceptance:009:expected_behavior"
FIELD = "proposed_output:output.narrative"


def synthetic_screen(reasons: list[dict[str, object]] | None = None) -> dict[str, object]:
    reasons = reasons or [{"kind": "token_jaccard_threshold", "reference": LABEL, "score": 0.812345}]
    return {
        "fatal": True,
        "fatal_reasons": [FIELD + evidence.REASON_SUFFIX],
        "fields": [{
            "field": FIELD,
            "protected": {
                "fatal": True,
                "reasons": ["not persisted"],
                "structured_reasons": reasons,
                "maximum_token_jaccard": {"reference": LABEL, "score": 0.812345678},
                "maximum_character_5gram_jaccard": {"reference": LABEL, "score": 0.456789012},
            },
        }],
    }


def build(reasons: list[dict[str, object]] | None = None) -> dict[str, object]:
    return evidence.build_row(
        1,
        {"slot": 1, "model": "gemini-3.7-flash", "mechanism_id": "M01"},
        "a" * 64,
        "b" * 64,
        FIELD + evidence.REASON_SUFFIX,
        synthetic_screen(reasons),
        [LABEL],
        [FIELD],
        None,
    )


class OutputCollisionEvidenceTests(unittest.TestCase):
    def test_verify_only_pins_proposal_and_capture_module_without_side_effects(self) -> None:
        result = pilot.verify_local_build()
        self.assertEqual(result["output_collision_evidence_proposal_sha256"], pilot.EXPECTED_OUTPUT_COLLISION_PROPOSAL_SHA256)
        self.assertEqual(result["output_collision_evidence_module_sha256"], pilot.EXPECTED_OUTPUT_COLLISION_EVIDENCE_SHA256)
        self.assertFalse(result["network_used"])
        self.assertFalse(result["credential_read"])
        self.assertFalse(result["file_output_created"])
        with patch.object(pilot, "OUTPUT_COLLISION_EVIDENCE_PATH", gate2.PACKAGE / "missing-output-collision-module.py"):
            with self.assertRaisesRegex(pilot.Gate5PilotStop, "canonical_input_invalid"):
                pilot.verify_local_build()

    def test_real_screen_yields_content_free_structured_evidence(self) -> None:
        canary = "UNIQUE-CANDIDATE-CONTENT-DO-NOT-PERSIST-7e56f9f9"
        candidate = {
            "source_input": "A separate clean source input.",
            "proposed_output": {"narrative": canary, "bullets": ["Clean bullet"], "action_items": ["Clean action"]},
        }
        screen = gate2.screen_candidate(candidate, [(LABEL, canary)], [], [])
        row = evidence.build_row(1, {"slot": 1, "model": "gemini-3.7-flash", "mechanism_id": "M01"}, "a" * 64, "b" * 64, FIELD + evidence.REASON_SUFFIX, screen, [LABEL], [name for name, _text in gate2.candidate_fields(candidate)], None)
        encoded = gate2.canonical_json_bytes(row)
        self.assertNotIn(canary.encode(), encoded)
        self.assertNotIn(b"not persisted", encoded)
        self.assertEqual(row["schedule_slot"], 1)
        self.assertTrue(row["protected_collision"]["reasons"])
        evidence.validate_row(row, [LABEL], [FIELD, "source_input", "proposed_output:output.bullets:01", "proposed_output:output.action_items:01"])

    def test_secret_shaped_candidate_value_never_crosses_boundary(self) -> None:
        secret_canary = "AIza" + "A" * 35
        candidate = {
            "source_input": "A separate clean source input.",
            "proposed_output": {"narrative": secret_canary, "bullets": ["Clean bullet"], "action_items": ["Clean action"]},
        }
        screen = gate2.screen_candidate(candidate, [(LABEL, secret_canary)], [], [])
        row = evidence.build_row(1, {"slot": 1, "model": "gemini-3.7-flash", "mechanism_id": "M01"}, "a" * 64, "b" * 64, FIELD + evidence.REASON_SUFFIX, screen, [LABEL], [name for name, _text in gate2.candidate_fields(candidate)], None)
        encoded = gate2.canonical_json_bytes(row)
        self.assertNotIn(secret_canary.encode(), encoded)
        self.assertFalse(gate2.contains_secret(row))

    def test_all_reason_kinds_and_score_rules(self) -> None:
        exact_text = "A sufficiently long protected sentence with stable wording for every similarity metric."
        exact = gate2.collision_check(exact_text, [(LABEL, exact_text)])
        exact_kinds = {item["kind"] for item in exact["structured_reasons"]}
        self.assertTrue({"normalized_exact_match", "token_jaccard_threshold", "character_5gram_jaccard_threshold"} <= exact_kinds)
        contained = gate2.collision_check(exact_text, [(LABEL, exact_text + " Additional protected context makes this a strict containment case.")])
        self.assertIn("normalized_containment", {item["kind"] for item in contained["structured_reasons"]})
        reasons = [
            {"kind": "normalized_exact_match", "reference": LABEL, "score": None},
            {"kind": "normalized_containment", "reference": LABEL, "score": None},
            {"kind": "token_jaccard_threshold", "reference": LABEL, "score": 0.9},
            {"kind": "character_5gram_jaccard_threshold", "reference": LABEL, "score": 0.8},
        ]
        row = build(reasons)
        self.assertEqual([item["kind"] for item in row["protected_collision"]["reasons"]], [item["kind"] for item in reasons])
        for bad in (
            {"kind": "unknown", "reference": LABEL, "score": 0.5},
            {"kind": "token_jaccard_threshold", "reference": "unknown:001", "score": 0.5},
            {"kind": "token_jaccard_threshold", "reference": LABEL, "score": True},
            {"kind": "token_jaccard_threshold", "reference": LABEL, "score": math.nan},
            {"kind": "token_jaccard_threshold", "reference": LABEL, "score": math.inf},
            {"kind": "token_jaccard_threshold", "reference": LABEL, "score": -0.1},
            {"kind": "token_jaccard_threshold", "reference": LABEL, "score": 1.1},
            {"kind": "normalized_exact_match", "reference": LABEL, "score": 1.0},
        ):
            with self.subTest(bad=bad), self.assertRaisesRegex(evidence.OutputCollisionEvidenceError, "output_collision_diagnostic_withheld"):
                build([bad])

    def test_count_byte_unknown_field_and_duplicate_boundaries_fail_closed(self) -> None:
        kinds = list(evidence.KINDS)
        labels = ["acceptance:001:expected_behavior", "acceptance:002:expected_behavior"]
        eight = []
        for label in labels:
            for kind in kinds:
                eight.append({"kind": kind, "reference": label, "score": None if kind in evidence.NULL_SCORE_KINDS else 0.5})
        screen = synthetic_screen(eight)
        screen["fields"][0]["protected"]["maximum_token_jaccard"]["reference"] = labels[0]
        screen["fields"][0]["protected"]["maximum_character_5gram_jaccard"]["reference"] = labels[1]
        evidence.build_row(1, {"slot": 1, "model": "gemini-3.7-flash", "mechanism_id": "M01"}, "a" * 64, "b" * 64, FIELD + evidence.REASON_SUFFIX, screen, labels, [FIELD], None)
        nine = eight + [{"kind": "token_jaccard_threshold", "reference": labels[0], "score": 0.6}]
        screen["fields"][0]["protected"]["structured_reasons"] = nine
        with self.assertRaises(evidence.OutputCollisionEvidenceError):
            evidence.build_row(1, {"slot": 1, "model": "gemini-3.7-flash", "mechanism_id": "M01"}, "a" * 64, "b" * 64, FIELD + evidence.REASON_SUFFIX, screen, labels, [FIELD], None)
        row = build()
        row["protected_collision"]["unexpected"] = "x"
        with self.assertRaises(evidence.OutputCollisionEvidenceError):
            evidence.validate_row(row, [LABEL], [FIELD])
        huge_label = "safe-label-" + "x" * evidence.MAX_CANONICAL_ROW_BYTES
        huge_reason = [{"kind": "token_jaccard_threshold", "reference": huge_label, "score": 0.5}]
        huge_screen = synthetic_screen(huge_reason)
        huge_screen["fields"][0]["protected"]["maximum_token_jaccard"]["reference"] = huge_label
        huge_screen["fields"][0]["protected"]["maximum_character_5gram_jaccard"]["reference"] = huge_label
        with self.assertRaises(evidence.OutputCollisionEvidenceError):
            evidence.build_row(1, {"slot": 1, "model": "gemini-3.7-flash", "mechanism_id": "M01"}, "a" * 64, "b" * 64, FIELD + evidence.REASON_SUFFIX, huge_screen, [huge_label], [FIELD], None)

    def test_cross_links_and_rehashed_tampering_are_rejected(self) -> None:
        diagnostic = build()
        rejection = pilot._rejection(1, "a" * 64, "b" * 64, FIELD + evidence.REASON_SUFFIX, diagnostic["row_hash"], None)
        summary = {"output_collision_diagnostic_count": 1, "output_collision_diagnostic_chain_head": diagnostic["row_hash"]}
        evidence.validate_rejection_links([rejection], [diagnostic], summary, [LABEL], [FIELD])
        changed = copy.deepcopy(diagnostic)
        changed["field_path"] = "proposed_output:output.bullets:01"
        payload = {key: value for key, value in changed.items() if key != "row_hash"}
        changed["row_hash"] = gate2.sha256_bytes(gate2.canonical_json_bytes(payload))
        changed_rejection = pilot._rejection(1, "a" * 64, "b" * 64, FIELD + evidence.REASON_SUFFIX, changed["row_hash"], None)
        with self.assertRaises(evidence.OutputCollisionEvidenceError):
            evidence.validate_rejection_links([changed_rejection], [changed], {"output_collision_diagnostic_count": 1, "output_collision_diagnostic_chain_head": changed["row_hash"]}, [LABEL], [FIELD])
        for bad_rejections, bad_diagnostics in (([rejection], []), ([], [diagnostic]), ([rejection], [diagnostic, diagnostic])):
            with self.assertRaises(evidence.OutputCollisionEvidenceError):
                evidence.validate_rejection_links(bad_rejections, bad_diagnostics, summary, [LABEL], [FIELD])

    def test_non_protected_rejection_has_null_link(self) -> None:
        rejection = pilot._rejection(1, "a" * 64, "b" * 64, "unexpected_http_status", None, None)
        summary = {"output_collision_diagnostic_count": 0, "output_collision_diagnostic_chain_head": None}
        evidence.validate_rejection_links([rejection], [], summary, [LABEL], [FIELD])
        rejection = pilot._rejection(1, "a" * 64, "b" * 64, "unexpected_http_status", "c" * 64, None)
        with self.assertRaises(evidence.OutputCollisionEvidenceError):
            evidence.validate_rejection_links([rejection], [], summary, [LABEL], [FIELD])

    def test_output_reservation_includes_empty_diagnostic_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            paths = pilot.prepare_output_directory(Path(temp) / "output", "a" * 64, "b" * 64, "c" * 64, "d" * 64, pilot.execution_gate.EXPECTED_SUCCESS_RECEIPT_ROW_SHA256, pilot.execution_gate.EXPECTED_FLASH_LITE_SUCCESS_RECEIPT_ROW_SHA256, dict(pilot.execution_gate.EXPECTED_FRESH), dict(pilot.execution_gate.EXPECTED_THIRD))
            self.assertEqual(paths["collision_diagnostics"].read_bytes(), b"")

    def test_runner_persists_only_safe_collision_evidence_and_io_failure_preserves_core(self) -> None:
        with tempfile.TemporaryDirectory(dir=gate2.PACKAGE) as temp:
            root = Path(temp)
            rate_value = gate2.load_json(gate2.PACKAGE / "gate5_execution_day_rate_snapshot_2026-08-16.json")
            rate_value["observed_date"] = date.today().isoformat()
            rate_path = root / "rates.json"
            rate_path.write_bytes(gate2.canonical_json_bytes(rate_value))
            attestation = gate2.load_json(gate2.PACKAGE / "gate5_pre_execution_attestation_template.json")
            attestation.update({
                "final_provider_contract_sha256": pilot.canonical_hash(pilot.CONTRACT_PATH),
                "final_provider_schema_sha256": pilot.canonical_hash(pilot.PROVIDER_SCHEMA_PATH),
                "live_validated_request_envelope_sha256": gate2.sha256_bytes(gate2.canonical_json_bytes(pilot.redesign.build_request(pilot.load_schedule()[0]))),
                "successful_corrected_schema_diagnostic_receipt_row_sha256": pilot.verify_successful_diagnostic_evidence(),
                "flash_lite_live_validated_request_envelope_sha256": gate2.sha256_bytes(gate2.canonical_json_bytes(pilot.redesign.build_request(pilot.load_schedule()[1]))),
                "successful_flash_lite_receipt_row_sha256": pilot.verify_successful_flash_lite_evidence(),
                "execution_day_rate_snapshot_sha256": pilot.canonical_hash(rate_path),
                "original_failed_pilot_booked_cost_usd_millionths": pilot.ORIGINAL_FAILED_PILOT_BOOKED_COST,
                "completed_fresh_pilot_booked_cost_usd_millionths": pilot.COMPLETED_FRESH_PILOT_BOOKED_COST,
                "prior_pilot_booked_cost_usd_millionths": pilot.PRIOR_PILOT_BOOKED_COST,
            })
            attestation.update(pilot.verify_fresh_attempt_evidence())
            attestation.update(pilot.verify_third_attempt_evidence())
            attestation_path = root / "attestation.json"
            attestation_path.write_bytes(gate2.canonical_json_bytes(attestation))
            fixture = copy.deepcopy(response_parser.load_fixtures()["valid_stop_with_usage"])
            candidate = json.loads(fixture["candidates"][0]["content"]["parts"][0]["text"])
            _manifest, references = gate2.build_quarantine()
            label, protected_text = next((label, text) for label, text in references if 80 <= len(text) <= 400 and not gate2.contains_secret(text))
            candidate["proposed_output"]["narrative"] = protected_text
            fixture["candidates"][0]["content"]["parts"][0]["text"] = json.dumps(candidate, ensure_ascii=False, separators=(",", ":"))
            body = gate2.canonical_json_bytes({key: value for key, value in fixture.items() if key != "id"})

            class Transport:
                calls = 0

                def post(self, *_args: object, **_kwargs: object) -> pilot.ProviderResponse:
                    self.calls += 1
                    return pilot.ProviderResponse(200, {}, body)

            transport = Transport()
            successful_output = root / "successful-output"
            successful_summary = pilot.execute_pilot(lambda _target: "local-test-secret", "test", transport, attestation_path, rate_path, successful_output, attestation_validator=lambda _path: attestation)
            successful_rejections = [json.loads(line) for line in (successful_output / "rejection_ledger.jsonl").read_text(encoding="utf-8").splitlines()]
            successful_diagnostics = [json.loads(line) for line in (successful_output / "output_collision_diagnostics.jsonl").read_text(encoding="utf-8").splitlines()]
            evidence.validate_rejection_links(successful_rejections, successful_diagnostics, successful_summary, [name for name, _text in references], evidence.EXPECTED_CANDIDATE_FIELD_PATHS)
            self.assertEqual(successful_summary["candidate_quarantine_count"], 0)
            self.assertEqual(successful_summary["output_collision_diagnostic_count"], 1)
            self.assertEqual(len(successful_diagnostics), 1)
            for path in successful_output.iterdir():
                if path.name != "candidate_quarantine.jsonl":
                    self.assertNotIn(protected_text.encode("utf-8"), path.read_bytes(), path.name)
            transport.calls = 0
            original_append = pilot._append

            def fail_diagnostic(path: Path, row: dict[str, object]) -> None:
                if path.name == "output_collision_diagnostics.jsonl":
                    raise pilot.Gate5PilotStop("output_path_unavailable")
                original_append(path, row)

            output = root / "output"
            with patch.object(pilot, "_append", fail_diagnostic):
                summary = pilot.execute_pilot(lambda _target: "local-test-secret", "test", transport, attestation_path, rate_path, output, attestation_validator=lambda _path: attestation)
            self.assertEqual(transport.calls, 1)
            self.assertEqual(summary["global_stop"], "output_collision_diagnostic_persistence_failed")
            self.assertEqual(summary["candidate_quarantine_count"], 0)
            self.assertEqual(summary["output_collision_diagnostic_count"], 0)
            self.assertEqual((output / "output_collision_diagnostics.jsonl").read_bytes(), b"")
            self.assertEqual(len((output / "request_receipts.jsonl").read_text(encoding="utf-8").splitlines()), 1)
            self.assertEqual(len((output / "rejection_ledger.jsonl").read_text(encoding="utf-8").splitlines()), 1)
            self.assertEqual(len((output / "cost_ledger.jsonl").read_text(encoding="utf-8").splitlines()), 1)
            for path in output.iterdir():
                if path.name != "candidate_quarantine.jsonl":
                    self.assertNotIn(protected_text.encode("utf-8"), path.read_bytes(), path.name)


if __name__ == "__main__":
    unittest.main()
