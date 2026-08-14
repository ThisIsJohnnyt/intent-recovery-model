# Gemini generator Gate 2 package

This directory is a local, dummy-only implementation of the eleven artifacts required by Section 16 of
`training/gemini_generator_readiness_package_chatgpt.md`. It has no provider SDK or network transport. The
only runner transport is `MockTransport`, and the dry run installs a socket guard.

Artifact mapping:

1. `system_instruction.txt`, `user_message_template.txt`, `response_schema.json`, and
   `artifact_manifest.json` freeze canonical hashes.
2. `mechanism_cards.json` and generated `schedule.json` freeze twelve cards and 24 interleaved slots.
3. Generated `quarantine_manifest.json` pins all 111 records in the comparator, Protected-16,
   Acceptance-10, and treatment-delta pools without copying their text into review surfaces.
4. `gate2.py` implements collision screens; `collision_fixtures.json` supplies adversarial cases.
5. `gate2.py` implements the strict parser; `response_parser_fixtures.json` supplies malformed cases.
6. `rate_snapshot.json`, `cost_ledger_schema.json`, and `cost_boundary_fixtures.json` implement integer
   micro-dollar arithmetic and boundaries. The planning rate snapshot must be replaced and verified on the
   execution day before any later paid gate.
7. `provider_contract.json`, `gate2.py`, and `mock_provider_fixtures.json` define the secret-redacting,
   mock-only request runner.
8. `request_receipt_schema.json`, `rejection_ledger_schema.json`, and `cost_ledger_schema.json` define the
   append-only chained formats.
9. `sealed_review_schema.json` plus `validate_review` and `compare_reviews` in `gate2.py` implement sealed
   review validation and comparison. Gate 2 does not perform candidate review.
10. `setup_attestation_template.json` stores no sensitive identifiers.
11. `dummy_dry_run_receipt.json` and the three `dummy_*.jsonl` chains prove the 24-slot mock run used no
    key, network, provider, model call, spend, review, or corpus mutation.

Local commands:

```text
python training/gemini_generator_gate2/gate2.py build
python -m unittest discover -s training/gemini_generator_gate2 -p "test_*.py" -v
python training/gemini_generator_gate2/gate2.py dummy-run
```

These commands do not authorize or perform provider setup, connectivity, generation, spending, candidate
review, corpus mutation, staging, commit, or push.
