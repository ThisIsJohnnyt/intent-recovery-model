"""Static feasibility item 7: cross-repository prompt rendering and
contract-fingerprint parity for the v2-candidate contract. No pytest
dependency: run directly with `python test_prompt_contract_v2_fingerprint_parity.py`.

Renders the same shared fixture (real_data_private.PROMPT_CONTRACT_FIXTURE,
already the canonical cross-repo fixture used by the live v1 contract) on
both sides and requires an exact SHA-256 match. If this locked value ever
needs to change, it must change here and in
thought-organizer-app/src/services/promptContractV2Candidate.ts together --
see test_prepare_data.py for the same pattern applied to the live contract.

The JS side isn't re-invoked from here (no cross-language process spawn) --
its half of this parity check already ran once, live, when this fingerprint
was locked (see prompt_contract_v2_parser_fixtures.json's sibling
verification pattern). This test's job is to catch drift on the Python
side against that locked value, matching test_prepare_data.py's existing
convention exactly.
"""
import sys

import prompt_contract_v2_candidate as v2
import real_data_private as rdp

FAILURES = []

# Locked 2026-08-02 against thought-organizer-app's promptContractV2Candidate.ts
# buildPrompt() for the same fixture -- confirmed identical at lock time
# (see training/prompt_contract_vnext_static_feasibility_package.md).
EXPECTED_FINGERPRINT = "9ee6bc1673c885ee3fc341d4b7ac5dada24b7ce8a435a20103455ac07e88fb6e"
EXPECTED_VERSION = "source-determined-items-v2-candidate"


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


def test_version_matches_locked_candidate_string():
    check(
        "PROMPT_CONTRACT_VERSION matches the locked candidate string",
        v2.PROMPT_CONTRACT_VERSION == EXPECTED_VERSION,
        v2.PROMPT_CONTRACT_VERSION,
    )


def test_rendered_fixture_fingerprint_matches_locked_cross_repo_value():
    rendered = v2.build_prompt(rdp.PROMPT_CONTRACT_FIXTURE)
    fingerprint = rdp.prompt_contract_fingerprint(rendered)
    check(
        "rendered fixture SHA-256 matches the locked cross-repo value",
        fingerprint == EXPECTED_FINGERPRINT,
        fingerprint,
    )


def main() -> None:
    tests = [
        test_version_matches_locked_candidate_string,
        test_rendered_fixture_fingerprint_matches_locked_cross_repo_value,
    ]
    for t in tests:
        t()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("All prompt_contract_v2 fingerprint-parity tests passed.")


if __name__ == "__main__":
    main()
