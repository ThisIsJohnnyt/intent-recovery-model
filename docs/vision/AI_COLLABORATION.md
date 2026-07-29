# AI Collaboration Protocol

An entry point for how this project is actually built, not a second copy of
it. Each topic below is defined once, in one canonical place — this doc
summarizes and links rather than restates, so it can't drift out of sync
with the source. The one genuinely new piece here is "Conflict resolution,"
which hadn't been written down anywhere before this.

## Roles

See [`NORTH_STAR.md`](NORTH_STAR.md)'s "Collaboration model" for the full
definition. Summary: product owner (the user, owns the problem/vision and
has final decision authority), Claude Code (engineering lead — repo,
pipeline, review, commits), ChatGPT (dataset curator — dataset spec,
curriculum design, review, evaluation methodology).

**Historical note**: Gemini generated the `gold_v1.0`/`gold_v1.1` example
batches early in the project. It is not an ongoing collaborator with a
standing role — its contribution is fully captured in
[`datasets/gold/CHANGELOG.md`](../../datasets/gold/CHANGELOG.md) and the
corresponding review reports. If that ever changes, update `NORTH_STAR.md`'s
collaboration model first — this doc follows that one, not the other way
around.

## Stable principles

See [`GOLD_PHILOSOPHY.md`](GOLD_PHILOSOPHY.md) — the constitution that
doesn't change release to release (Evidence First, No Magic Examples, One
Lesson Per Example, Progressive Difficulty, Boundary Evidence, Preserve
Uncertainty, Human-Centered Intent Recovery).

## Review workflow

See [`docs/datasets/REVIEW_GUIDE.md`](../datasets/REVIEW_GUIDE.md)'s
checklist and "Release bundle" section for what a release consists of and
who writes each piece, and its new "Release Checklist" section for the
reusable acceptance-criteria template.

## Decision ownership

See [`docs/decisions/`](../decisions/) — Project Decision Records capture
decisions with lasting consequences (`PDR-001`: build process before scale;
`PDR-002`: how the curator stays synced with actual repo state).

## Dataset lifecycle

See `REVIEW_GUIDE.md`'s release bundle table (design notes → review report
→ lessons learned) and
[`docs/datasets/CATEGORY_REFERENCE.md`](../datasets/CATEGORY_REFERENCE.md)'s
"Category lifecycle" section (a category's introduced/deprecated history).

## Conflict resolution

The procedure behind [`NORTH_STAR.md`](NORTH_STAR.md)'s "Repository
Authority" and "Preserve Decision History" values — not documented anywhere
until now, despite being exercised repeatedly:

1. **Check before acting.** Claude Code checks a curator proposal against
   the actual current repo before applying it — never overwrites or
   contradicts existing content on the assumption a proposal is already
   correct. This is what catches proposals made without full repo
   visibility (schema mismatches, duplicate files, terminology that doesn't
   match `TAXONOMY.md`, etc.) before they land.
2. **Surface, don't silently resolve.** A found conflict gets presented to
   the product owner with a concrete recommendation — Claude Code doesn't
   silently pick a side, and doesn't silently reject a proposal either.
3. **Product owner has final decision authority** on any dataset-content or
   process question. Claude Code and the dataset curator can both
   recommend; neither unilaterally decides.
4. **Fix the gap, not just the instance.** When a conflict reveals a
   recurring pattern (e.g. a principle restated in multiple places, a
   missing convention), the preferred fix consolidates or cross-links so
   the same conflict doesn't resurface in the next release — this is why
   `GOLD_PHILOSOPHY.md` and this doc's "Release Checklist" exist.
5. **Low-judgment fixes don't need a round trip.** A broken cross-reference
   or an obviously stale link can be corrected directly. Anything that
   changes meaning, scope, or an established convention gets flagged to the
   product owner first, not applied unilaterally.
