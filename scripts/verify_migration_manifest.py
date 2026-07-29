"""Verify migration-manifest.yaml classifies every tracked path exactly once.

Usage (PyYAML is already available via the training venv):
    training/venv/Scripts/python.exe scripts/verify_migration_manifest.py

Checks the top-level repo-root entries and docs/'s immediate subdirectories
(the granularity migration-manifest.yaml actually classifies at) against
every path listed under destinations.*.{keep,rewrite,copy,new} and
special_cases -- fails loudly if anything is unclassified, or classified
under both intent-recovery-model and thought-organizer-app without being an
explicit special case.
"""
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent


def tracked_top_level(subpath: str = "") -> set[str]:
    out = subprocess.run(
        ["git", "ls-tree", "--name-only", "HEAD", subpath] if subpath else ["git", "ls-tree", "--name-only", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return {line.strip() for line in out.splitlines() if line.strip()}


def normalize(paths: list) -> set[str]:
    result = set()
    for p in paths:
        if isinstance(p, dict):
            p = p.get("path", "")
        p = p.rstrip("/")
        result.add(p)
    return result


def main() -> None:
    manifest = yaml.safe_load((REPO_ROOT / "migration-manifest.yaml").read_text(encoding="utf-8"))
    dests = manifest["destinations"]

    model_paths = normalize(
        dests["intent-recovery-model"].get("keep", [])
        + dests["intent-recovery-model"].get("rewrite", [])
        + dests["intent-recovery-model"].get("new", [])
    )
    app_paths = normalize(
        dests["thought-organizer-app"].get("copy", [])
        + dests["thought-organizer-app"].get("rewrite", [])
        + dests["thought-organizer-app"].get("new", [])
    )
    special = {p.rstrip("/") for p in manifest.get("special_cases", {})}

    classified = model_paths | app_paths | special
    overlap = (model_paths & app_paths) - special

    # Root-level entries, minus files this migration introduces fresh
    # (migration-manifest.yaml, scripts/) which aren't "currently tracked"
    # in the sense this check cares about but do need to exist going forward.
    root_entries = tracked_top_level()
    doc_entries = tracked_top_level("docs/")  # already returns "docs/xxx"-prefixed paths
    all_entries = (root_entries - {"docs"}) | doc_entries

    unclassified = {e for e in all_entries if e not in classified}

    ok = True
    if unclassified:
        ok = False
        print(f"UNCLASSIFIED (in repo, not in manifest): {sorted(unclassified)}")
    if overlap:
        ok = False
        print(f"CLASSIFIED IN BOTH destinations without a special_case: {sorted(overlap)}")

    if ok:
        print(f"OK: all {len(all_entries)} tracked top-level/docs paths are classified exactly once.")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
