# PDR-003 Migration Plan: repository split

Companion to [`PDR-003.md`](PDR-003.md) — the actual step sequence, kept as
a permanent record since the split happens across two GitHub repositories
and a tool-local plan file doesn't survive that boundary.

**Status as of this writing**: all 13 steps complete. Migration done.

## Sequence

1. ✅ Commit all current work; confirm a clean working tree.
2. ✅ Tag and push `pre-repository-split`.
3. ✅ Add `docs/decisions/PDR-003.md` (this decision) before the split
   happens, so it exists in the preserved history.
4. ✅ Write and verify `migration-manifest.yaml` — a `keep`/`copy`/
   `special_case` classification of every currently-tracked path, checked
   by script against `git ls-tree -r --name-only HEAD` so nothing is
   silently omitted or double-assigned.
5. ✅ Write `docs/inference-contract.md` — the versioned, behavioral
   contract the application will depend on instead of the model's
   internal format.
6. ✅ Cut the first checksummed model release
   (`intent-recovery-model-v0.1.0`) with a release manifest (release name,
   contract version, each file's SHA-256 and size).
7. ✅ Create the new, empty `thought-organizer-app` GitHub repository
   (github.com/ThisIsJohnnyt/thought-organizer-app).
8. ✅ Copy the application-only paths into it (initial commit references
   `pre-repository-split` for traceability, local clone at
   `Desktop/thought-organizer-app`), add `scripts/fetch-model.mjs`
   (Node, checksum-verified, refuses incomplete/corrupt downloads), and
   test it against the release from step 6 — worked end-to-end on first
   real run except two real findings fixed along the way: GitHub release
   assets can't preserve the `onnx/` subdirectory prefix (script already
   handled this via `path.basename()` for the download URL), and the
   manifest asset kept its original upload filename rather than the
   generic `manifest.json` the script initially assumed.
9. ✅ **Gate**: confirmed `thought-organizer-app` runs end-to-end from a
   genuinely fresh clone (not the working copy that built it) — `npm
   install --ignore-scripts` → `npm run fetch-model` (downloads, size- and
   checksum-verifies, installs the real release) → `npm run build`
   (`tsc` + `vite build`, clean). Nothing has been removed from the
   original repo before this passed.
10. ✅ Rename the original GitHub repository `thoughtorganizer` →
    `intent-recovery-model`. Verified (not assumed): the renamed repo is
    reachable at its new URL, and the release cut in step 6 remains
    downloadable under the new name (confirmed via a direct request to the
    new release-asset URL, HTTP 302 to the actual asset). Local remote and
    `thought-organizer-app`'s `fetch-model.mjs` both updated and re-tested
    against the renamed repo.
11. ✅ Remove the now-migrated application-only paths from
    `intent-recovery-model` (`src/`, `public/`, `index.html`,
    `thoughtorganizer-mobile.html`, Vite/TypeScript config, `package.json`).
12. ✅ Rewrite both repositories' `README.md`s and roadmaps; add cross-repo
    links each direction. Also caught and fixed two pieces of unrelated
    staleness while rewriting: the old root `README.md` still had
    diagnosis-framing language ("helps people with ADHD, autism...") that
    predated this project's mission reframe, and `docs/vision/PROJECT_OVERVIEW.md`
    still described a "placeholder fixture" and `gold_v1.0` as current
    status, months out of date.
13. ✅ Final independent-clone validation on both repositories.
    `intent-recovery-model` (branch `claude/ai-note-organization-luz6rk`):
    fresh clone contains exactly the expected files (no leftover app
    paths), `prepare_data.py` runs and produces the same 49/5/0 split as
    before the split, `scripts/verify_migration_manifest.py` passes (13
    tracked paths, down from 22 once the app files were removed), and
    every spot-checked doc cross-link resolves. `thought-organizer-app`:
    fresh clone → `npm install --ignore-scripts` → `npm run fetch-model`
    → `npm run build`, all clean.

## Why steps 4-6 come before repository creation

Both the migration manifest and the inference contract are things a
mistake in would be expensive to unwind after files start moving between
repositories — better to get the classification and the contract right
while everything is still in one place and easy to change. The model
release (step 6) has to exist before step 8 can actually test the
application's fetch script against something real.

## Blocking note

Creating a new GitHub repository (step 7) and renaming this one (step 10)
are GitHub-account-level actions. The `gh` CLI isn't installed in this
environment, so steps 7 and 10 need either installing it or the product
owner performing those two specific actions via the GitHub web UI — see
the check-in in the conversation this plan came from for how that was
resolved.
