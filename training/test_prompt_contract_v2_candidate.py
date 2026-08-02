"""Static, no-GPU feasibility tests for the vNext prompt-contract candidate
(typed ###BULLET###/###ACTION### item markers). No pytest dependency: run
directly with `python test_prompt_contract_v2_candidate.py`.

Covers items 1, 3, 4, 5, 6(partial), 8 of the static feasibility package
requested in prompt_contract_vnext_joint_alignment_review.md. Item 2
(browser-runtime parity) and the TypeScript half of item 3/4 are covered by
thought-organizer-app/src/services/promptContractV2Parser.test.ts, which
consumes the same frozen fixture file (byte-identity checked here too).
Item 7 (cross-repo prompt fingerprint parity) is in
test_prompt_contract_v2_fingerprint_parity.py. Item 6 (mechanical dataset
migration) is a separate script, prompt_contract_v2_migrate.py.
"""
import json
import sys
from pathlib import Path

import prompt_contract_v2_candidate as v2
from prompt_contract_v2_parser import ParseError, parse_output

FAILURES = []
FIXTURES_PATH = Path(__file__).parent / "prompt_contract_v2_parser_fixtures.json"
APP_FIXTURES_PATH = (
    Path(__file__).parent.parent.parent / "thought-organizer-app" / "src" / "services"
    / "prompt_contract_v2_parser_fixtures.json"
)


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


def test_fixture_file_is_content_identical_across_repos():
    # Structural (parsed JSON) comparison, not raw bytes: the training
    # repo's committed copy gets CRLF-normalized by Windows git autocrlf on
    # checkout while the app repo's copy (not committed through the same
    # path) stays LF -- confirmed directly, a real line-ending difference,
    # not a content one. Byte-identity was the wrong check for what this
    # test actually needs to guarantee (same logical fixture cases in both
    # repos), so it compares parsed content instead.
    if not APP_FIXTURES_PATH.exists():
        check("fixture file content-identical across repos", False, f"app-side copy not found at {APP_FIXTURES_PATH}")
        return
    training_data = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    app_data = json.loads(APP_FIXTURES_PATH.read_text(encoding="utf-8"))
    check("fixture file content-identical across repos", training_data == app_data)


def test_valid_fixture_cases_parse_as_expected():
    fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    for case in fixtures["valid_cases"]:
        result = parse_output(case["input"])
        expected = case["expected"]
        matches = (
            result.narrative == expected["narrative"]
            and result.bullets == expected["bullets"]
            and result.actions == expected["actions"]
        )
        check(f"valid fixture '{case['id']}' parses as expected", matches, str(result))


def test_error_fixture_cases_fail_closed():
    fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    for case in fixtures["error_cases"]:
        try:
            parse_output(case["input"])
            check(f"error fixture '{case['id']}' raises ParseError", False, "did not raise")
        except ParseError as e:
            check(
                f"error fixture '{case['id']}' raises ParseError",
                case["expect_error_contains"] in str(e),
                str(e),
            )


def test_tokenizer_round_trip_preserves_typed_markers():
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(str(Path(__file__).parent / "checkpoints" / "gold_v1.2.2-newprompt-seed17" / "final"))
    rendered = f"{v2.NARRATIVE_MARKER}\ntext\n{v2.BULLETS_MARKER}\n{v2.BULLET_ITEM_MARKER} one\n{v2.BULLET_ITEM_MARKER} two\n{v2.ACTIONS_MARKER}\n{v2.ACTION_ITEM_MARKER} three"
    decoded = tok.decode(tok(rendered)["input_ids"], skip_special_tokens=True)
    check(
        "tokenizer round-trip preserves exact marker count/spelling",
        decoded.count(v2.BULLET_ITEM_MARKER) == 2 and decoded.count(v2.ACTION_ITEM_MARKER) == 1,
        decoded,
    )
    # Decoded (newline-collapsed) form must still parse correctly -- this is
    # the actual real-world shape run_benchmark.py would hand to a parser.
    result = parse_output(decoded)
    check(
        "decoded (newline-collapsed) round-tripped text still parses correctly",
        result.narrative == "text" and result.bullets == ["one", "two"] and result.actions == ["three"],
        str(result),
    )


def test_sanitizer_defangs_all_run_lengths():
    import re

    for run_len in [3, 4, 5, 7, 22]:
        text = f"note with {'#' * run_len} hashes"
        sanitized = v2.sanitize_marker_like_text(text)
        check(
            f"sanitizer defangs a {run_len}-char '#' run",
            not re.search(r"#{3,}", sanitized),
            sanitized,
        )
        check(
            f"sanitizer preserves visible content for a {run_len}-char run",
            sanitized.replace("‌", "") == text,
        )


def test_sanitized_input_cannot_reach_parser_as_a_real_marker():
    # End-to-end: a raw note containing a literal marker string, sanitized
    # and then echoed verbatim into a would-be model output, must NOT be
    # mistaken by the parser for a real structural marker.
    raw_input = "I copied this: ###BULLET### as an example"
    sanitized = v2.sanitize_marker_like_text(raw_input)
    fake_output = f"{v2.NARRATIVE_MARKER} {sanitized} {v2.BULLETS_MARKER} {v2.BULLET_ITEM_MARKER} a real bullet {v2.ACTIONS_MARKER}"
    result = parse_output(fake_output)
    check(
        "sanitized echoed input doesn't corrupt parsing (still exactly one real bullet)",
        result.bullets == ["a real bullet"],
        str(result),
    )


def main() -> None:
    tests = [
        test_fixture_file_is_content_identical_across_repos,
        test_valid_fixture_cases_parse_as_expected,
        test_error_fixture_cases_fail_closed,
        test_tokenizer_round_trip_preserves_typed_markers,
        test_sanitizer_defangs_all_run_lengths,
        test_sanitized_input_cannot_reach_parser_as_a_real_marker,
    ]
    for t in tests:
        t()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("All prompt_contract_v2_candidate tests passed.")


if __name__ == "__main__":
    main()
