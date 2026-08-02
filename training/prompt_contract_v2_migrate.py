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
from pathlib import Path

import prompt_contract_v2_candidate as v2

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

        # Verify: item counts identical before/after.
        if len(bullets) != v2_target.count(v2.BULLET_ITEM_MARKER):
            mismatches.append((r["input"][:40], "bullet count mismatch"))
        if len(actions) != v2_target.count(v2.ACTION_ITEM_MARKER):
            mismatches.append((r["input"][:40], "action count mismatch"))

        # Verify: narrative/bullet/action TEXT unaltered -- every original
        # string must appear verbatim in the v2 target.
        if narrative.strip() not in v2_target:
            mismatches.append((r["input"][:40], "narrative text altered"))
        for b in bullets:
            if b not in v2_target:
                mismatches.append((r["input"][:40], f"bullet text altered: {b!r}"))
        for a in actions:
            if a not in v2_target:
                mismatches.append((r["input"][:40], f"action text altered: {a!r}"))

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
        print(f"\nVerified: all {len(records)} records -- item counts identical before/after, "
              "narrative/bullet/action text unaltered.")

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


if __name__ == "__main__":
    main()
