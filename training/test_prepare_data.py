"""Standalone assertion tests for prepare_data.py's cross-repository prompt
contract -- dummy data only. No pytest dependency: run directly with
`python test_prepare_data.py`, matching this repo's existing script-based
tooling convention.

Covers the drift-prevention requirement from
training/REAL_DATA_EVALUATION_PROTOCOL.md's prompt-contract fingerprint
section: PROMPT_CONTRACT_VERSION and the rendered prompt text must not
change without deliberately updating this test, since
src/services/noteOrganizer.ts is expected to reproduce both exactly.
"""
import sys

import prepare_data as pd
import real_data_private as rdp

FAILURES = []

# Locked at PROMPT_CONTRACT_VERSION "source-determined-bullets-v1". If this
# test starts failing because the rendered prompt changed, that's either an
# accidental regression or a deliberate new contract version -- in the
# latter case, update PROMPT_CONTRACT_VERSION, this hash, and the paired
# app-repository fixture together, never one alone.
EXPECTED_PROMPT_CONTRACT_FINGERPRINT = (
    "161661198071fd81310681f69381ec8e0287141e1e75b09d3a342414af31ccf1"
)


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


def test_prompt_contract_version_matches_agreed_string():
    check(
        "PROMPT_CONTRACT_VERSION: matches the agreed cross-repository string",
        pd.PROMPT_CONTRACT_VERSION == "source-determined-bullets-v1",
        pd.PROMPT_CONTRACT_VERSION,
    )


def test_rendered_fixture_prompt_fingerprint_is_locked():
    rendered = pd.build_prompt(rdp.PROMPT_CONTRACT_FIXTURE)
    fingerprint = rdp.prompt_contract_fingerprint(rendered)
    check(
        "prompt fixture: rendered prompt hash matches the locked cross-repository fingerprint",
        fingerprint == EXPECTED_PROMPT_CONTRACT_FINGERPRINT,
        fingerprint,
    )


def test_bullets_instruction_has_no_fixed_lower_bound():
    check(
        "USER_PROMPT_TEMPLATE: bullets instruction does not require a minimum line count",
        "3 to 7" not in pd.USER_PROMPT_TEMPLATE and "3-7" not in pd.USER_PROMPT_TEMPLATE,
    )


def main() -> None:
    tests = [
        test_prompt_contract_version_matches_agreed_string,
        test_rendered_fixture_prompt_fingerprint_is_locked,
        test_bullets_instruction_has_no_fixed_lower_bound,
    ]
    for t in tests:
        t()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("All prepare_data.py tests passed.")


if __name__ == "__main__":
    main()
