"""Static, no-GPU regression tests for
source_determined_items_v2_acceptance_gold_targets_draft.jsonl (ChatGPT's
authored reference outputs for the 10 source_determined_items_v2
acceptance cases). No pytest dependency: run directly with
`python test_source_determined_items_v2_gold_targets.py`.

These targets are semantic scoring anchors and token-budget fixtures, NOT
exact-match acceptance criteria -- a generated paraphrase can and should
pass when it satisfies the frozen structure, semantic dimensions, and
capability checks, even if its wording differs from reference_output. This
file only enforces the MECHANICAL properties that must hold regardless of
wording: the reference itself parses under the real v2 parser, its counts
satisfy the frozen benchmark's count rules, it respects the hard bullet/
action ceilings, it doesn't leak protected-benchmark language, and it
survives a real tokenizer round-trip with its structure intact. None of
that constitutes or should be read as an exact-match gate on future model
output.

Status per source_determined_items_v2_gold_targets_chatgpt_handoff.md:
draft, not frozen. This test file exists so any future edit to the
targets file is caught immediately, not just verified once by hand.
"""
import json
import re
import sys
from pathlib import Path

from contract_adapters import evaluate_count_rule
from prompt_contract_v2_parser import ParseError, parse_output

FAILURES = []
TRAINING_DIR = Path(__file__).parent
BENCHMARK_DIR = TRAINING_DIR.parent / "datasets" / "benchmark"

TARGETS_PATH = TRAINING_DIR / "source_determined_items_v2_acceptance_gold_targets_draft.jsonl"
ACCEPTANCE_DRAFT_PATH = BENCHMARK_DIR / "source_determined_items_v2_acceptance_draft.jsonl"
PROTECTED_PROBES_PATH = BENCHMARK_DIR / "gold_v1.2.1_probes.jsonl"
HISTORICAL_ACCEPTANCE_PATH = BENCHMARK_DIR / "source_determined_bullets_acceptance.jsonl"

GENERATION_MAX_NEW_TOKENS = 300


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def ngrams(text: str, n: int = 4) -> set:
    words = re.findall(r"\w+", text.lower())
    return {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}


def test_ids_unique_and_match_benchmark_order():
    targets = load_jsonl(TARGETS_PATH)
    probes = load_jsonl(ACCEPTANCE_DRAFT_PATH)
    target_ids = [t["id"] for t in targets]
    probe_ids = [p["id"] for p in probes]
    check("10 target rows, unique IDs", len(target_ids) == len(set(target_ids)) == 10, str(target_ids))
    check("target IDs match the acceptance benchmark set, same order", target_ids == probe_ids, f"{target_ids} vs {probe_ids}")


def test_every_target_parses_and_matches_reference_output_exactly():
    targets = load_jsonl(TARGETS_PATH)
    probes = {p["id"]: p for p in load_jsonl(ACCEPTANCE_DRAFT_PATH)}
    for t in targets:
        tid = t["id"]
        probe = probes.get(tid)
        check(f"{tid}: has a matching benchmark probe", probe is not None)
        if probe is None:
            continue
        try:
            parsed = parse_output(t["v2_target"])
        except ParseError as e:
            check(f"{tid}: v2_target parses under the real v2 parser", False, str(e))
            continue
        check(f"{tid}: v2_target parses under the real v2 parser", True)
        ref = t["reference_output"]
        check(f"{tid}: parsed narrative == reference_output.narrative", parsed.narrative == ref["narrative"], parsed.narrative)
        check(f"{tid}: parsed bullets == reference_output.bullets", parsed.bullets == ref["bullets"], str(parsed.bullets))
        check(f"{tid}: parsed actions == reference_output.action_items", parsed.actions == ref["action_items"], str(parsed.actions))


def test_every_target_satisfies_its_frozen_count_rules_and_hard_ceilings():
    targets = load_jsonl(TARGETS_PATH)
    probes = {p["id"]: p for p in load_jsonl(ACCEPTANCE_DRAFT_PATH)}
    for t in targets:
        tid = t["id"]
        probe = probes.get(tid)
        if probe is None:
            continue
        try:
            parsed = parse_output(t["v2_target"])
        except ParseError:
            continue
        bullet_result = evaluate_count_rule(probe.get("bullet_count_rule"), len(parsed.bullets))
        action_result = evaluate_count_rule(probe.get("action_count_rule"), len(parsed.actions))
        check(f"{tid}: bullet_count_rule satisfied", bullet_result is None or bullet_result["passed"], str(bullet_result))
        check(f"{tid}: action_count_rule satisfied", action_result is None or action_result["passed"], str(action_result))
        check(f"{tid}: bullets <= 7 (hard ceiling)", len(parsed.bullets) <= 7, str(len(parsed.bullets)))
        check(f"{tid}: actions <= 8 (hard ceiling)", len(parsed.actions) <= 8, str(len(parsed.actions)))


def test_no_four_word_overlap_with_protected_or_historical_benchmark_language():
    targets = load_jsonl(TARGETS_PATH)
    protected_grams: set = set()
    for p in load_jsonl(PROTECTED_PROBES_PATH):
        protected_grams |= ngrams(p["input"])
        protected_grams |= ngrams(p.get("expected_behavior", ""))
    historical_grams: set = set()
    for p in load_jsonl(HISTORICAL_ACCEPTANCE_PATH):
        historical_grams |= ngrams(p["input"])
        historical_grams |= ngrams(p.get("expected_behavior", ""))

    for t in targets:
        ref = t["reference_output"]
        combined = " ".join([ref["narrative"], *ref["bullets"], *ref["action_items"]])
        target_grams = ngrams(combined)
        overlap_p = target_grams & protected_grams
        overlap_h = target_grams & historical_grams
        check(
            f"{t['id']}: no 4-word overlap with protected/historical benchmark language",
            not overlap_p and not overlap_h,
            f"protected={overlap_p} historical={overlap_h}",
        )


def test_tokenizer_round_trip_preserves_markers_and_reference_structure():
    from transformers import AutoTokenizer

    targets = load_jsonl(TARGETS_PATH)
    tok = AutoTokenizer.from_pretrained(str(TRAINING_DIR / "checkpoints" / "gold_v1.2.2-newprompt-seed17" / "final"))

    markers = ("###NARRATIVE###", "###BULLETS###", "###BULLET###", "###ACTIONS###", "###ACTION###")
    counts = []
    for t in targets:
        tid = t["id"]
        target_text = t["v2_target"]
        ids = tok(target_text)["input_ids"]
        counts.append((tid, len(ids)))
        decoded = tok.decode(ids, skip_special_tokens=True)

        markers_survive = all(target_text.count(m) == decoded.count(m) for m in markers)
        check(f"{tid}: marker counts survive the real tokenizer round-trip", markers_survive, decoded)

        try:
            reparsed = parse_output(decoded)
        except ParseError as e:
            check(f"{tid}: decoded round-tripped text still parses correctly", False, str(e))
            continue
        ref = t["reference_output"]
        structure_matches = (
            reparsed.narrative == ref["narrative"]
            and reparsed.bullets == ref["bullets"]
            and reparsed.actions == ref["action_items"]
        )
        check(f"{tid}: decoded round-tripped text still matches reference_output exactly", structure_matches, str(reparsed))

    sorted_counts = sorted(c for _, c in counts)
    n = len(sorted_counts)
    median = sorted_counts[n // 2] if n % 2 else (sorted_counts[n // 2 - 1] + sorted_counts[n // 2]) / 2
    p95 = sorted_counts[min(n - 1, int(round(0.95 * (n - 1))))]
    max_count = max(c for _, c in counts)
    max_id = next(tid for tid, c in counts if c == max_count)
    over_budget = [tid for tid, c in counts if c >= GENERATION_MAX_NEW_TOKENS]

    print(
        f"\nToken budget across all {n} gold targets: min={sorted_counts[0]} median={median} "
        f"p95={p95} max={max_count} (case {max_id}) -- {len(over_budget)}/{n} at or above "
        f"{GENERATION_MAX_NEW_TOKENS} tokens"
    )
    check(f"all {n} gold targets fit within the {GENERATION_MAX_NEW_TOKENS}-token generation budget", not over_budget, str(over_budget))


def main() -> None:
    tests = [
        test_ids_unique_and_match_benchmark_order,
        test_every_target_parses_and_matches_reference_output_exactly,
        test_every_target_satisfies_its_frozen_count_rules_and_hard_ceilings,
        test_no_four_word_overlap_with_protected_or_historical_benchmark_language,
        test_tokenizer_round_trip_preserves_markers_and_reference_structure,
    ]
    for t in tests:
        t()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILURE(S): {FAILURES}")
        sys.exit(1)
    print("All source_determined_items_v2 gold-target tests passed.")


if __name__ == "__main__":
    main()
