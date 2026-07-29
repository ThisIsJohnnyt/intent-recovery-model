# PDR-003 Migration Plan: repository split

Companion to [`PDR-003.md`](PDR-003.md) — the actual step sequence, kept as
a permanent record since the split happens across two GitHub repositories
and a tool-local plan file doesn't survive that boundary.

**Status as of this writing**: steps 1-7 complete. Steps 8 onward are
in progress — see each step's status note.

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
8. Copy the application-only paths into it (commit message references
   `pre-repository-split` for traceability), add `scripts/fetch-model.*`,
   and test it against the release from step 6.
9. **Gate**: confirm `thought-organizer-app` runs end-to-end from a fresh
   clone (`fetch-model` downloads + verifies + installs the release,
   `npm run dev` produces valid output) before touching the original repo
   further. Nothing is removed from the original repo before this passes.
10. Rename the original GitHub repository `thoughtorganizer` →
    `intent-recovery-model` (GitHub auto-redirects the old URL; update it
    in docs anyway).
11. Remove the now-migrated application-only paths from
    `intent-recovery-model`.
12. Rewrite both repositories' `README.md`s and roadmaps; add cross-repo
    links each direction.
13. Final independent-clone validation on both repositories.

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
