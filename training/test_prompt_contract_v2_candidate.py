"""Static, no-GPU feasibility tests for the vNext prompt-contract candidate
(typed ###BULLET###/###ACTION### item markers). No pytest dependency: run
directly with `python test_prompt_contract_v2_candidate.py`.

Covers items 1, 3, 4, 5, 6(partial), 8 of the static feasibility package
requested in prompt_contract_vnext_joint_alignment_review.md. Item 2
(browser-runtime parity) and the TypeScript half of item 3/4 are covered by
thought-organizer-app/src/services/promptContractV2Parser.test.ts, which
consumes the same frozen fixture file (canonical-JSON fingerprint checked
against a locked shared hash here too, not a cross-repo path read).
Item 7 (cross-repo prompt fingerprint parity) is in
test_prompt_contract_v2_fingerprint_parity.py. Item 6 (mechanical dataset
migration) is a separate script, prompt_contract_v2_migrate.py.
"""
import hashlib
import json
import sys
from pathlib import Path

import prompt_contract_v2_candidate as v2
from prompt_contract_v2_parser import ParseError, parse_output

FAILURES = []
FIXTURES_PATH = Path(__file__).parent / "prompt_contract_v2_parser_fixtures.json"

# Finding 5 fix (prompt_contract_vnext_static_package_chatgpt_review.md): a
# cross-repo relative-path read (../../thought-organizer-app/...) breaks
# under any machine layout or worktree where the two repos aren't checked
# out as siblings with matching names -- confirmed by ChatGPT reproducing
# exactly this failure. Fixed by comparing a canonical-JSON SHA-256
# fingerprint (sorted object keys, preserved array order, matching
# separators/encoding across both languages) against a single locked value,
# computed independently in each repo -- no path dependency at all.
EXPECTED_FIXTURES_FINGERPRINT = "52867b1c6920a00b835cab1c8bc4bf495a4f54b8cf6d80df401b5a5f39969948"


def canonical_json_fingerprint(data) -> str:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


def test_fixture_file_matches_locked_canonical_fingerprint():
    data = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    fingerprint = canonical_json_fingerprint(data)
    check(
        "fixture file matches locked canonical cross-repo fingerprint",
        fingerprint == EXPECTED_FIXTURES_FINGERPRINT,
        fingerprint,
    )


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


MARKER_COLLISION_MARKERS = (
    v2.NARRATIVE_MARKER, v2.BULLETS_MARKER, v2.BULLET_ITEM_MARKER,
    v2.ACTIONS_MARKER, v2.ACTION_ITEM_MARKER,
)
MARKER_COLLISION_HASH_RUN_LENGTHS = (3, 4, 5, 7, 22)
MARKER_COLLISION_RAW = " | ".join(
    [f"copied literally: {m}" for m in MARKER_COLLISION_MARKERS]
    + [f"hash run: {'#' * n} end" for n in MARKER_COLLISION_HASH_RUN_LENGTHS]
)

# Locked 2026-08-02 against the actual production JS runtime
# (@xenova/transformers, thoughtorganizer-flan-t5's real deployed tokenizer
# files) decoding the same sanitized MARKER_COLLISION_RAW string -- confirmed
# byte-identical to this Python decode at lock time. If either tokenizer's
# vocabulary/normalization ever changes, both this value and the app-side
# copy in promptContractV2RuntimeParity.test.ts must change together.
EXPECTED_MARKER_COLLISION_DECODED = (
    "copied literally: ## #NARRATIVE## # | copied literally: ## #BULLETS## # "
    "| copied literally: ## #BULLET## # | copied literally: ## #ACTIONS## # "
    "| copied literally: ## #ACTION## # | hash run: ## # end | hash run: ## ## end "
    "| hash run: ## ## # end | hash run: ## ## ## # end "
    "| hash run: ## ## ## ## ## ## ## ## ## ## ## end"
)


def test_sanitized_marker_collisions_survive_real_tokenizer_round_trip():
    # Finding 2 fix (prompt_contract_vnext_static_package_chatgpt_review.md):
    # the sanitizer tests above only ever operated on raw strings -- this
    # closes the gap by actually encoding/decoding the sanitized text
    # through the real seed-17 checkpoint tokenizer, for every marker
    # literal plus every tested '#' run length in one combined string.
    import re

    from transformers import AutoTokenizer

    sanitized = v2.sanitize_marker_like_text(MARKER_COLLISION_RAW)
    tok = AutoTokenizer.from_pretrained(
        str(Path(__file__).parent / "checkpoints" / "gold_v1.2.2-newprompt-seed17" / "final")
    )
    decoded = tok.decode(tok(sanitized)["input_ids"], skip_special_tokens=True)

    # A real, non-obvious tokenizer behavior found by running this, not
    # assumed: the SentencePiece tokenizer does not preserve the ZWNJ
    # (U+200C) separator byte-for-byte -- it decodes as a plain space. The
    # anti-collision property still holds (a space is just as effective a
    # separator as a ZWNJ at breaking up a '#' run), so this is checked as
    # an invariant on the decoded text, not as decoded == sanitized.
    check(
        "no real marker substring survives sanitized-input tokenizer round-trip",
        not any(m in decoded for m in MARKER_COLLISION_MARKERS),
        decoded,
    )
    check(
        "no 3+ '#' run survives sanitized-input tokenizer round-trip",
        not re.search(r"#{3,}", decoded),
        decoded,
    )
    check(
        "decoded sanitized text matches the locked cross-runtime value (Python/JS parity)",
        decoded == EXPECTED_MARKER_COLLISION_DECODED,
        decoded,
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
        test_fixture_file_matches_locked_canonical_fingerprint,
        test_valid_fixture_cases_parse_as_expected,
        test_error_fixture_cases_fail_closed,
        test_tokenizer_round_trip_preserves_typed_markers,
        test_sanitized_marker_collisions_survive_real_tokenizer_round_trip,
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
