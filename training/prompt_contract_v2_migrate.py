"""Static feasibility item 6: mechanically migrate the existing 66
gold_v1.2.2 targets to the v2-candidate typed-marker format, without
altering narrative/bullet/action text, and verify item counts survive
exactly. Writes a draft output only -- does not touch datasets/synthetic.jsonl
or training/data/processed*, and is not wired into prepare_data.py.

Usage: python prompt_contract_v2_migrate.py
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import prompt_contract_v2_candidate as v2
from prompt_contract_v2_parser import ParseError, parse_output

REPO_ROOT = Path(__file__).parent.parent
OUTPUT_PATH = Path(__file__).parent / "prompt_contract_v2_migrated_targets_DRAFT.jsonl"


def canonical_json_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def build_v1_target(narrative: str, bullets: list[str], actions: list[str]) -> str:
    """Reproduces prepare_data.py's current (v1) target construction
    exactly, for the before/after comparison."""
    lines = ["###NARRATIVE###", narrative.strip(), "###BULLETS###", *bullets, "###ACTIONS###", *actions]
    return "\n".join(lines)


def build_v2_target(narrative: str, bullets: list[str], actions: list[str]) -> str:
    lines = [
        v2.NARRATIVE_MARKER,
        narrative.strip(),
        v2.BULLETS_MARKER,
        *[f"{v2.BULLET_ITEM_MARKER} {b}" for b in bullets],
        v2.ACTIONS_MARKER,
        *[f"{v2.ACTION_ITEM_MARKER} {a}" for a in actions],
    ]
    return "\n".join(lines)


def main() -> None:
    raw = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", "8d7aa09:datasets/synthetic.jsonl"],
        capture_output=True, encoding="utf-8", check=True,
    ).stdout
    records = [json.loads(l) for l in raw.splitlines() if l.strip()]
    print(f"Loaded {len(records)} gold_v1.2.2 records from pinned commit 8d7aa09.")

    migrated = []
    mismatches = []
    for r in records:
        narrative = r["output"]["narrative"]
        bullets = r["output"]["bullets"]
        actions = r["output"]["action_items"]

        v1_target = build_v1_target(narrative, bullets, actions)
        v2_target = build_v2_target(narrative, bullets, actions)

        # Finding 4 fix (prompt_contract_vnext_static_package_chatgpt_review.md):
        # marker-count matching plus "does this string appear ANYWHERE in the
        # target" substring containment is logically weaker than actually
        # parsing the generated target and comparing structured output --
        # e.g. it can't catch a bullet landing in the wrong section, items
        # silently reordered, or an item's text getting truncated to a
        # substring that still happens to "contain" a shorter original
        # string. Parsing with the real fail-closed parser and requiring
        # exact structural equality subsumes both old checks (equal lists
        # implies equal counts) and additionally proves ordering and
        # section placement survived migration.
        try:
            parsed = parse_output(v2_target)
        except ParseError as e:
            mismatches.append((r["input"][:40], f"v2 target does not parse: {e}"))
        else:
            if parsed.narrative != narrative.strip():
                mismatches.append((r["input"][:40], f"narrative mismatch: {parsed.narrative!r} != {narrative.strip()!r}"))
            if parsed.bullets != bullets:
                mismatches.append((r["input"][:40], f"bullets mismatch: {parsed.bullets!r} != {bullets!r}"))
            if parsed.actions != actions:
                mismatches.append((r["input"][:40], f"actions mismatch: {parsed.actions!r} != {actions!r}"))

        migrated.append({
            "input": r["input"],
            "output": r["output"],  # unchanged -- migration only affects target serialization
            "difficulty": r.get("difficulty"),
            "category": r.get("category"),
            "v1_target": v1_target,
            "v2_target": v2_target,
        })

    OUTPUT_PATH.write_text(
        "\n".join(json.dumps(m, ensure_ascii=False) for m in migrated) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(migrated)} migrated records (draft, not live data) to {OUTPUT_PATH}")

    if mismatches:
        print(f"\n{len(mismatches)} MISMATCH(ES) FOUND:")
        for input_prefix, reason in mismatches:
            print(f"  {input_prefix!r}: {reason}")
    else:
        print(f"\nVerified via parse_output() exact-equality on all {len(records)} records -- "
              "narrative/bullets/actions structurally identical before/after migration.")

    # Fingerprints: hash the full record set's output (semantic content,
    # unaffected by migration) and, separately, the two target-serialization
    # variants, so a reviewer can confirm the *content* fingerprint is
    # unchanged while the *serialization* fingerprint differs (as expected --
    # only the wire format changed, not the underlying data).
    output_only = [{"input": r["input"], "output": r["output"]} for r in records]
    output_fingerprint = hashlib.sha256(canonical_json_bytes(output_only)).hexdigest()
    v1_targets_fingerprint = hashlib.sha256(
        canonical_json_bytes([m["v1_target"] for m in migrated])
    ).hexdigest()
    v2_targets_fingerprint = hashlib.sha256(
        canonical_json_bytes([m["v2_target"] for m in migrated])
    ).hexdigest()
    print(f"\nContent fingerprint (input+output, migration-invariant): sha256:{output_fingerprint}")
    print(f"v1-serialization fingerprint (bare newlines):              sha256:{v1_targets_fingerprint}")
    print(f"v2-serialization fingerprint (typed markers):               sha256:{v2_targets_fingerprint}")

    report_token_budget(migrated)

    # Finding 4 fix: fail closed. The old script printed mismatches but
    # always exited 0 -- a CI/manual run could miss a real regression
    # buried in scrollback. A migration script with unverified output is
    # worse than no migration script.
    if mismatches:
        print(f"\n{len(mismatches)} mismatch(es) -- exiting nonzero.")
        sys.exit(1)


def report_token_budget(migrated: list) -> None:
    """Finding 3 fix (prompt_contract_vnext_static_package_chatgpt_review.md):
    the original feasibility package only measured marker overhead in
    isolation, not complete v2 targets -- this tokenizes all 66 real
    migrated targets (narrative + bullets + actions together, exactly what
    train.py would hand the tokenizer as a label) and reports the actual
    generation-time token budget.
    """
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(
        str(Path(__file__).parent / "checkpoints" / "gold_v1.2.2-newprompt-seed17" / "final")
    )
    counts = [len(tok(m["v2_target"])["input_ids"]) for m in migrated]
    sorted_counts = sorted(counts)
    n = len(sorted_counts)
    median = sorted_counts[n // 2] if n % 2 else (sorted_counts[n // 2 - 1] + sorted_counts[n // 2]) / 2
    p95 = sorted_counts[min(n - 1, int(round(0.95 * (n - 1))))]
    max_count = max(counts)
    max_record = migrated[counts.index(max_count)]
    over_300 = sum(1 for c in counts if c >= 300)

    print(f"\nFull v2-target token budget across all {n} migrated records:")
    print(f"  min={sorted_counts[0]}  median={median}  p95={p95}  max={max_count}")
    print(f"  record producing max ({max_count} tokens): {max_record['input'][:60]!r}")
    print(f"  records >= 300 tokens: {over_300}/{n}")


if __name__ == "__main__":
    main()
