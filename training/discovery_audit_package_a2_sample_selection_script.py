"""A2 frozen-sample selection: reference implementation, self-test only.

Operationalizes `training/intent_recovery_data_model_discovery_plan_chatgpt.md` Sec.3, "A2. Frozen sample
design" -- draw a reproducible 24-record audit sample per candidate, stratified, deduplicated against
protected/acceptance evaluations, without examining targets during selection.

STATUS: this script has never been run against any real dataset. It has been run repeatedly in
`--selftest` mode during development, including after two rounds of ChatGPT's independent review found
real defects -- see the revision notes below. The receipt on disk (not committed -- every file in this
package remains untracked, pending Johnny's "Git it done") reflects the final, corrected version,
reproduced byte-identically across separate process invocations. No external file, network call, account,
or license acceptance is used anywhere in this file. Running it in "real" mode (`select_sample()` called
with a caller-supplied metadata list) still requires the caller to have already produced that metadata list
through separately authorized means -- this script does not fetch or download anything itself. Per Johnny's
2026-08-12 disposition: running this self-test against a fabricated fixture is not "compute" in the gated
sense (that term covers real dataset/model compute); it is ordinary static verification, consistent with
this project's existing precedent of running fail-closed validator scripts (e.g.
`training/prepare_regression_balanced_repair_candidate_corpus.py`) freely during design work.

Normalization and collision thresholds are not invented here: they reuse the values already reviewed and
ratified for this project in `training/prepare_regression_balanced_repair_candidate_corpus.py`
(`normalize_for_collision()`, `TOKEN_JACCARD_REVIEW_THRESHOLD=0.15`, `CHAR_NGRAM_REVIEW_THRESHOLD=0.10`,
`CONTAINMENT_MIN_NORMALIZED_CHARS=20`), per that file's own "FORWARD-LOOKING RULE": future rounds must pin
collision thresholds before any real record exists, not after. This package has no real records yet, so
reusing the already-ratified values (rather than picking new ones) is the correct application of that rule.

REVISION 2026-08-12 (ChatGPT's first independent review found five real defects):
1. Silent underfill -> fixed with an explicit top-up phase plus a recorded `shortfall_reason`.
2. Non-fatal collision flags discarded for selected records -> fixed, now recorded in the manifest.
3. Speaker cap couldn't fire (no speaker-identity field, only a count bucket) -> fixed, added identity.
4. Cap-consumption order bias (fixed alphabetical stratum order) -> fixed, order now seeded.
5. Fairness self-test checked only one previously-biased key -> fixed, now checks every stratum key.
Also added: intra-sample self-collision screening, and a pool fingerprint in the manifest.

POST-APPROVAL FIX, 2026-08-13, SAME DAY (after ChatGPT's five-round approval, caught before push): the
receipt-writing code in `main()` used to call `Path.write_text()` with no explicit `newline`, so Python's
default text-mode translation wrote CRLF line endings on Windows. Every hash cited throughout this
package's entire review history was of that CRLF file. Committing it exposed the gap: this repo's
`core.autocrlf=true` normalizes the stored blob to LF, which hashes differently despite identical content
-- the same species of defect already caught once before in this project's Phase-2 contrastive-corpus
work. Fixed by opening the file explicitly with `newline="\n"`, so the receipt is LF on every platform
regardless of Python's or the OS's default translation, and the working-tree file, the git blob, and a
fresh hash computed anywhere now permanently agree.

REVISION 2026-08-13, SAME DAY, FOURTH REVIEW (one more real defect found and fixed in this script
specifically -- the post-adjudication lifecycle gap from this round is a protocol/A5 fix, not a script
change, see the A2 protocol doc):
13. `required_pool_sources` was optional (default `None`), so a caller could simply omit it and get zero
    enforcement -- the fail-closed validation added in the third review was real but skippable. Fixed:
    `required_pool_sources` is now a required parameter with no default, on every call including this
    module's own self-test. Also strengthened per-source checking from count-only to an optional exact
    content hash (`PoolSourceSpec.expected_content_sha256`), so a source with the right record count but
    substituted content is caught too, not just a source that's short or missing outright.

REVISION 2026-08-13, SAME DAY, THIRD REVIEW (two more real defects found and fixed, both confirmed by
Claude before fixing):
11. `_pool_fingerprint()` made a missing or partial pool *visible* (a reviewer could notice the counts
    looked wrong) but never *enforced* anything -- an empty or one-source-short pool still produced a
    normal-looking manifest with no failure. Fixed: `_validate_pool()` fails closed when a caller-supplied
    `required_pool_sources` mapping isn't satisfied (missing source, under-count, or an unexpected source
    not in the mapping), and unconditionally rejects malformed or duplicate pool labels regardless of
    whether `required_pool_sources` is supplied at all.
12. The top-up phase's genuinely-untouched leftover candidates were discarded once `select_sample()`
    returned, even though a later post-adjudication top-up (see the A2 protocol doc's "Post-adjudication
    completeness" section, also added this round) needs a predeclared, deterministic reserve list to draw
    from rather than re-deriving one after the fact. Fixed: the manifest now records
    `unused_leftover_record_ids` -- exactly the leftover candidates never attempted during this run's own
    top-up, in their shuffled order, available for that later step.

REVISION 2026-08-13 (ChatGPT's second independent review of the 2026-08-12 revision found five more real
defects, all confirmed by Claude re-reading the code before fixing):
6. `speaker_id: str | None` could not represent a multi-party record (more than one speaker in the same
   record) -- a real gap, since QMSum specifically is a multi-party meeting corpus. Fixed: replaced with
   `speaker_ids: tuple[str, ...]`; the cap now checks and increments every speaker identity present, not
   just one.
7. `_pool_fingerprint()` hashed only a flat sorted list of normalized texts, dropping which source/file
   each one came from and each source's own count -- so it couldn't actually prove all required benchmark
   files were supplied, only that *some* pool was. Fixed: fingerprint is now broken out per source (the
   part of each pool label before its first `:`), each with its own count and content hash, plus an
   aggregate.
8. The manifest recorded only bare selected IDs, not each selected record's content hash or stratum --
   requested explicitly in the first review's "manifest completeness" correction and missed in the first
   fix. Fixed: added `selected_records`, a per-record list with `stratum` and `content_sha256`.
9. The `collision_review_flags_requiring_adjudication` entries carried a mutable-looking `adjudicated:
   false` field baked into a manifest this whole design otherwise treats as frozen/immutable -- resolving
   a flag would have meant editing a "frozen" artifact in place, with no tamper record. Fixed: that field
   is removed from the manifest entirely; adjudication now lives in a *separate* artifact (see
   `compute_manifest_hash()` below and the A2 protocol doc), keyed to this manifest's own hash, never
   mutating the manifest itself.
10. No preflight validation existed for structurally malformed metadata (duplicate record IDs, empty
    input text, out-of-range fields) -- fail-open instead of this project's usual fail-closed convention.
    Fixed: `_validate_metadata()` runs first and raises on any of these, before any selection logic runs.

Also fixed: the docstring previously said the receipt was "committed alongside" the script, which was
simply wrong -- nothing in this package is committed. Now says "on disk," matching reality.

KNOWN, EXPLICITLY DEFERRED LIMITATION, NARROWED 2026-08-13: the plan requires collision checks by
"normalized or semantic" comparison. This implementation covers normalized-text comparison only. ChatGPT's
second review correctly noted that leaving the semantic-check *decision* undeclared (rather than just the
semantic check itself unexecuted) was too permissive -- see the A2 protocol doc's new "Semantic collision
protocol" section, which now predeclares two named options and makes choosing between them (or an explicit,
documented waiver) a hard stop before real sampling, not a runner's later discretionary call. No embedding
or model-based check is implemented in this script -- that remains real compute against real data, out of
scope here regardless of which predeclared option is eventually chosen.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Pinned constants. Any change to these must happen here, before a real
# metadata list is ever loaded -- not adjusted after seeing a real draw.
# ---------------------------------------------------------------------------

AUDIT_SAMPLE_SIZE = 24  # plan Sec.3 A2: "24-record audit sample per candidate"
AUDIT_SEED = 24  # pinned now; a differently-pinned seed may be substituted only before real metadata loads
SPEAKER_SCENARIO_CAP = 2  # plan Sec.3 A2: "cap repeated speakers/scenarios where identifiers permit"

# Reused verbatim from training/prepare_regression_balanced_repair_candidate_corpus.py (ratified 2026-08-11)
TOKEN_JACCARD_REVIEW_THRESHOLD = 0.15
CHAR_NGRAM_REVIEW_THRESHOLD = 0.10
CONTAINMENT_MIN_NORMALIZED_CHARS = 20
CHAR_NGRAM_N = 5


def normalize_for_collision(text: str) -> str:
    """Identical rule to the ratified implementation: NFKC first, then lowercase, strip to [a-z0-9 ],
    collapse whitespace."""
    t = unicodedata.normalize("NFKC", text).lower()
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _token_set(text: str) -> set[str]:
    return set(normalize_for_collision(text).split())


def _token_jaccard(a: str, b: str) -> float:
    sa, sb = _token_set(a), _token_set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _char_ngrams(text: str, n: int = CHAR_NGRAM_N) -> set[str]:
    t = normalize_for_collision(text).replace(" ", "")
    if len(t) < n:
        return {t} if t else set()
    return {t[i : i + n] for i in range(len(t) - n + 1)}


def _char_ngram_jaccard(a: str, b: str, n: int = CHAR_NGRAM_N) -> float:
    sa, sb = _char_ngrams(a, n), _char_ngrams(b, n)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


@dataclass
class Record:
    record_id: str
    source: str
    length_quartile: int  # 1-4
    speaker_count_bucket: str  # e.g. "2", "3", "4+" -- how many speakers are IN the conversation
    speaker_ids: tuple[str, ...]  # WHICH speaker(s), when the candidate exposes identity -- may be more
    # than one for a multi-party record (e.g. a QMSum meeting snippet); empty tuple if unavailable.
    scenario_id: str | None
    input_text: str


@dataclass
class CollisionResult:
    record_id: str
    fatal: bool
    reasons: list[str] = field(default_factory=list)


def screen_collisions(record: Record, pool: list[tuple[str, str]]) -> CollisionResult:
    """Compare one candidate record's input against a pool of (source_label, text) pairs. In a real A1-
    cleared run, `pool` is every record in datasets/benchmark/gold_v1.2.1_probes.jsonl,
    datasets/benchmark/source_determined_bullets_acceptance.jsonl, and
    datasets/benchmark/source_determined_items_v2_acceptance_draft.jsonl, PLUS (per `select_sample` below)
    every record already selected earlier in the same draw, so within-sample near-duplicates are caught
    too. This function never reads any file itself; the caller supplies the pool so this module has no
    filesystem dependency. Label each pool entry `"<source_name>:<record_id>"` -- `_pool_fingerprint()`
    below relies on that convention to report per-source counts."""
    norm_text = normalize_for_collision(record.input_text)
    reasons: list[str] = []
    fatal = False
    for src, ref_text in pool:
        norm_ref = normalize_for_collision(ref_text)
        if not norm_text or not norm_ref:
            continue
        if norm_text == norm_ref:
            reasons.append(f"normalized-exact match against {src}")
            fatal = True
            continue
        shorter = min(len(norm_text), len(norm_ref))
        if shorter >= CONTAINMENT_MIN_NORMALIZED_CHARS and (norm_text in norm_ref or norm_ref in norm_text):
            reasons.append(f"normalized containment with {src} ({shorter}-char overlap)")
            fatal = True
            continue
        tj = _token_jaccard(record.input_text, ref_text)
        if tj >= TOKEN_JACCARD_REVIEW_THRESHOLD:
            reasons.append(f"token-Jaccard {tj:.3f} vs {src} (review, non-fatal)")
        cj = _char_ngram_jaccard(record.input_text, ref_text)
        if cj >= CHAR_NGRAM_REVIEW_THRESHOLD:
            reasons.append(f"char-5gram-Jaccard {cj:.3f} vs {src} (review, non-fatal)")
    return CollisionResult(record_id=record.record_id, fatal=fatal, reasons=reasons)


def _stratum_key(r: Record) -> tuple[str, int, str]:
    return (r.source, r.length_quartile, r.speaker_count_bucket)


def _validate_metadata(metadata: list[Record]) -> None:
    """Fail-closed preflight checks, matching this project's existing validator convention (see
    training/prepare_regression_balanced_repair_candidate_corpus.py's fail-closed gates). Raises
    ValueError -- deliberately not a silent skip or a warning -- on any structural defect, before any
    selection logic runs. Added 2026-08-13 per ChatGPT's second review."""
    seen_ids: set[str] = set()
    for r in metadata:
        if not r.record_id:
            raise ValueError("FATAL: metadata contains a record with an empty record_id.")
        if r.record_id in seen_ids:
            raise ValueError(
                f"FATAL: duplicate record_id {r.record_id!r} in metadata -- record IDs must be unique."
            )
        seen_ids.add(r.record_id)
        if r.length_quartile not in (1, 2, 3, 4):
            raise ValueError(
                f"FATAL: {r.record_id!r} has invalid length_quartile {r.length_quartile!r} (must be 1-4)."
            )
        if not r.speaker_count_bucket:
            raise ValueError(f"FATAL: {r.record_id!r} has an empty speaker_count_bucket.")
        if not r.input_text or not r.input_text.strip():
            raise ValueError(f"FATAL: {r.record_id!r} has empty input_text.")


@dataclass
class PoolSourceSpec:
    """A frozen expectation for one pool source, added 2026-08-13 (fourth review). `min_count` alone
    (what the first version of `_validate_pool` accepted) only checks record count -- it can't catch a
    source that has the right count but wrong/substituted content. `expected_content_sha256`, when set,
    must exactly match that source's `_source_content_hash()` value. Both real-run and self-test callers
    are expected to pin real values here, not invent lenient ones per call."""
    min_count: int
    expected_content_sha256: str | None = None


def _source_content_hash(texts: list[str]) -> str:
    """Shared by `_validate_pool()` and `_pool_fingerprint()` so 'the hash of source X' means exactly one
    thing everywhere in this module."""
    return hashlib.sha256("\n".join(sorted(normalize_for_collision(t) for t in texts)).encode("utf-8")).hexdigest()


def _validate_pool(pool: list[tuple[str, str]], required_sources: dict[str, PoolSourceSpec]) -> None:
    """Fail-closed validation that the pool actually contains what a real run needs. Added 2026-08-13 per
    ChatGPT's third review (`_pool_fingerprint()` made omissions *visible* but never *enforced* them) and
    tightened again per its fourth review: `required_sources` is no longer optional -- every caller,
    including this module's own self-test, must pass a real mapping; there is no default that lets pool
    validation be silently skipped. Each source's `PoolSourceSpec` may additionally pin an exact expected
    content hash, not just a minimum count, so a source with the right record count but substituted or
    corrupted content is still caught. Malformed or duplicate labels are rejected unconditionally."""
    seen_labels: set[str] = set()
    per_source_texts: dict[str, list[str]] = {}
    for label, text in pool:
        if not label or ":" not in label:
            raise ValueError(f"FATAL: pool label {label!r} is malformed -- expected '<source>:<record_id>'.")
        source, record_id = label.split(":", 1)
        if not source or not record_id:
            raise ValueError(f"FATAL: pool label {label!r} has an empty source or record_id component.")
        if label in seen_labels:
            raise ValueError(f"FATAL: duplicate pool label {label!r} -- each pool entry must be unique.")
        seen_labels.add(label)
        per_source_texts.setdefault(source, []).append(text)

    missing = []
    hash_mismatches = []
    for source, spec in required_sources.items():
        texts = per_source_texts.get(source, [])
        if len(texts) < spec.min_count:
            missing.append(f"{source!r} (expected >= {spec.min_count}, got {len(texts)})")
            continue
        if spec.expected_content_sha256 is not None:
            actual = _source_content_hash(texts)
            if actual != spec.expected_content_sha256:
                hash_mismatches.append(f"{source!r} (expected {spec.expected_content_sha256}, got {actual})")
    unexpected = sorted(s for s in per_source_texts if s not in required_sources)
    if missing:
        raise ValueError(f"FATAL: pool missing required source(s): {'; '.join(missing)}.")
    if hash_mismatches:
        raise ValueError(f"FATAL: pool source content hash mismatch: {'; '.join(hash_mismatches)}.")
    if unexpected:
        raise ValueError(f"FATAL: pool contains unexpected source(s) not in required_sources: {unexpected}.")


def _pool_fingerprint(pool: list[tuple[str, str]]) -> dict[str, Any]:
    """Per-source breakdown, not just one aggregate hash -- added 2026-08-13 per ChatGPT's second review,
    which correctly noted the original flat fingerprint couldn't prove every required source actually
    contributed, only that *some* pool was supplied. Source name is the part of each label before its
    first ':' (see `screen_collisions()`'s labeling convention); a label with no ':' is its own source."""
    per_source: dict[str, list[str]] = {}
    for label, text in pool:
        source = label.split(":", 1)[0] if ":" in label else label
        per_source.setdefault(source, []).append(text)
    sources_fp: dict[str, dict[str, Any]] = {}
    for source, texts in sorted(per_source.items()):
        sources_fp[source] = {"count": len(texts), "content_sha256": _source_content_hash(texts)}
    aggregate_digest = _source_content_hash([t for _, t in pool])
    return {
        "total_pool_size": len(pool),
        "sources": sources_fp,
        "aggregate_content_sha256": aggregate_digest,
    }


def compute_manifest_hash(manifest: dict[str, Any]) -> str:
    """Canonical hash of a frozen manifest. Added 2026-08-13 so a *separate* adjudication artifact (see
    the A2 protocol doc's "Collision adjudication artifact" section) can cite exactly which frozen manifest
    it resolves flags for, without ever modifying the manifest itself. Call this once, immediately after
    `select_sample()` returns and before the manifest is written to disk."""
    return hashlib.sha256(json.dumps(manifest, sort_keys=True).encode("utf-8")).hexdigest()


def _largest_remainder_quotas(strata_sizes: dict[tuple, int], total: int, rng: Any) -> dict[tuple, int]:
    """Deterministic, no-manual-adjustment proportional allocation of `total` slots across strata,
    weighted by each stratum's population size.

    Tie-break note: when two or more strata have equal fractional remainders (common when strata are
    small and uniformly sized, as in the self-test fixture below), breaking ties by stratum key would
    systematically favor alphabetically-earlier sources/strata on every run -- a real bias, not a neutral
    default. Caught during this package's own self-test (an early version did exactly this and gave one
    fake source all 8 self-test slots). Ties are instead broken by the same seeded `rng`: stratum order is
    shuffled once, then a stable sort by descending fractional remainder preserves that shuffled order
    among ties, so the tie-break is reproducible given the seed but not alphabetically biased."""
    population = sum(strata_sizes.values())
    if population == 0:
        return {k: 0 for k in strata_sizes}
    raw = {k: (v / population) * total for k, v in strata_sizes.items()}
    floors = {k: int(x) for k, x in raw.items()}
    remainder = total - sum(floors.values())
    shuffled_keys = list(strata_sizes.keys())
    rng.shuffle(shuffled_keys)
    order = sorted(shuffled_keys, key=lambda k: -(raw[k] - floors[k]))
    for k in order[:remainder]:
        floors[k] += 1
    return floors


def select_sample(
    metadata: list[Record],
    pool: list[tuple[str, str]],
    required_pool_sources: dict[str, PoolSourceSpec],
    sample_size: int = AUDIT_SAMPLE_SIZE,
    seed: int = AUDIT_SEED,
    speaker_cap: int = SPEAKER_SCENARIO_CAP,
) -> dict[str, Any]:
    """Deterministic stratified draw with speaker/scenario capping, fatal-collision exclusion (against the
    external pool AND against already-selected records in this same draw), and an explicit top-up phase so
    a shortfall in one stratum doesn't silently freeze an undersized sample when other strata could cover
    it. A non-null `shortfall_reason` / `must_stop: true` in the returned manifest is a hard stop for
    whoever calls this in a real run -- see the A2 protocol doc; this function only reports the fact
    honestly, it does not itself enforce what the caller does next.

    Determinism strategy: one `random.Random(seed)` instance is used for everything, in this fixed order:
    quota tie-break, stratum processing order, each stratum's internal shuffle (sorted lexicographically by
    record_id beforehand, independent of any file's on-disk order), then the top-up phase's shuffle. A
    fatal collision or a cap violation consumes the next candidate from the same shuffled list rather than
    re-seeding -- so the whole run is reproducible end-to-end from (metadata, pool, sample_size, seed)
    alone.
    """
    import random

    _validate_metadata(metadata)
    _validate_pool(pool, required_pool_sources)

    rng = random.Random(seed)

    strata: dict[tuple, list[Record]] = {}
    for r in metadata:
        strata.setdefault(_stratum_key(r), []).append(r)
    for k in strata:
        strata[k] = sorted(strata[k], key=lambda r: r.record_id)

    quotas = _largest_remainder_quotas({k: len(v) for k, v in strata.items()}, sample_size, rng)

    selected: list[Record] = []
    excluded_log: list[dict[str, Any]] = []
    collision_review_flags: list[dict[str, Any]] = []
    speaker_counts: dict[str, int] = {}
    scenario_counts: dict[str, int] = {}
    leftovers: list[Record] = []  # candidates not consumed by their stratum's quota; eligible for top-up

    def try_take(candidate: Record) -> bool:
        """Attempt to add `candidate` to `selected`. Returns True if taken, False if excluded (and logs
        why). Screens against the external pool plus every already-selected record's input, so
        within-sample near-duplicates (a "scenario" reappearing in reworded form, e.g.) are caught even
        without a shared identifier."""
        for sid in candidate.speaker_ids:
            if speaker_counts.get(sid, 0) >= speaker_cap:
                excluded_log.append({
                    "record_id": candidate.record_id,
                    "reason": f"speaker cap ({speaker_cap}) reached for speaker_id {sid!r}",
                })
                return False
        scenario_key = candidate.scenario_id
        if scenario_key is not None and scenario_counts.get(scenario_key, 0) >= speaker_cap:
            excluded_log.append({
                "record_id": candidate.record_id,
                "reason": f"scenario cap ({speaker_cap}) reached for scenario_id {scenario_key!r}",
            })
            return False
        dynamic_pool = pool + [(f"already-selected:{r.record_id}", r.input_text) for r in selected]
        collision = screen_collisions(candidate, dynamic_pool)
        if collision.fatal:
            excluded_log.append({
                "record_id": candidate.record_id,
                "reason": "fatal collision: " + "; ".join(collision.reasons),
            })
            return False
        if collision.reasons:  # non-fatal review flags survive even though the record is selected
            collision_review_flags.append({
                "record_id": candidate.record_id,
                "flags": collision.reasons,
            })
        selected.append(candidate)
        for sid in candidate.speaker_ids:
            speaker_counts[sid] = speaker_counts.get(sid, 0) + 1
        if scenario_key is not None:
            scenario_counts[scenario_key] = scenario_counts.get(scenario_key, 0) + 1
        return True

    stratum_keys = list(strata.keys())
    rng.shuffle(stratum_keys)  # processing order is seeded, not alphabetical -- closes the cap ordering bias

    for key in stratum_keys:
        pool_for_stratum = strata[key][:]
        rng.shuffle(pool_for_stratum)
        quota = quotas.get(key, 0)
        taken = 0
        while pool_for_stratum and taken < quota:
            candidate = pool_for_stratum.pop(0)
            if try_take(candidate):
                taken += 1
        leftovers.extend(pool_for_stratum)  # whatever wasn't consumed remains eligible for top-up

    shortfall_reason = None
    unused_leftovers: list[Record] = []
    if len(selected) < sample_size:
        rng.shuffle(leftovers)
        for i, candidate in enumerate(leftovers):
            if len(selected) >= sample_size:
                unused_leftovers = leftovers[i:]  # never attempted -- the reserve for a later top-up
                break
            try_take(candidate)
        if len(selected) < sample_size:
            shortfall_reason = (
                f"pool exhausted after cap/collision exclusions: {len(selected)}/{sample_size} achieved "
                f"from {len(metadata)} candidate record(s) total"
            )
    else:
        unused_leftovers = leftovers  # target already met from strata alone; top-up never ran at all

    selected_records = [
        {
            "record_id": r.record_id,
            "stratum": str(_stratum_key(r)),
            "content_sha256": hashlib.sha256(r.input_text.encode("utf-8")).hexdigest(),
        }
        for r in selected
    ]

    manifest = {
        "sample_size_target": sample_size,
        "sample_size_achieved": len(selected),
        "shortfall_reason": shortfall_reason,
        "must_stop": shortfall_reason is not None,
        "seed": seed,
        "speaker_scenario_cap": speaker_cap,
        "collision_thresholds": {
            "token_jaccard_review": TOKEN_JACCARD_REVIEW_THRESHOLD,
            "char_ngram_review": CHAR_NGRAM_REVIEW_THRESHOLD,
            "containment_min_normalized_chars": CONTAINMENT_MIN_NORMALIZED_CHARS,
        },
        "pool_fingerprint": _pool_fingerprint(pool),
        "strata_quotas": {str(k): v for k, v in sorted(quotas.items())},
        "selected_record_ids": [r.record_id for r in selected],
        "selected_records": selected_records,
        "unused_leftover_record_ids": [r.record_id for r in unused_leftovers],
        "excluded_or_redrawn": excluded_log,
        "collision_review_flags_requiring_adjudication": collision_review_flags,
    }
    return manifest


# ---------------------------------------------------------------------------
# Self-test only. Fabricated fixture -- no real dataset content anywhere below.
# ---------------------------------------------------------------------------


def _build_selftest_fixture() -> tuple[list[Record], list[tuple[str, str]]]:
    metadata: list[Record] = []
    sources = ["fake-source-a", "fake-source-b"]
    idx = 0
    for source in sources:
        for length_q in (1, 2, 3, 4):
            for speakers in ("2", "3", "4+"):
                for i in range(2):  # 2 records per (source, length, speaker) cell = 48 total
                    idx += 1
                    rid = f"synthetic-{idx:03d}"
                    scenario = f"scenario-{idx % 6}"  # forces some repeats across cells
                    # Most records have one speaker identity; every 7th is deliberately multi-party (two
                    # speaker_ids) to exercise the multi-speaker cap path added 2026-08-13.
                    if idx % 7 == 0:
                        speaker_ids = (f"speaker-{idx % 5}", f"speaker-{(idx + 1) % 5}")
                    else:
                        speaker_ids = (f"speaker-{idx % 5}",)
                    text = f"fabricated placeholder utterance number {idx} about topic {idx % 5}"
                    metadata.append(Record(rid, source, length_q, speakers, speaker_ids, scenario, text))

    # Deliberately force one record to normalized-exact-collide with a fake "pool" entry.
    metadata[0] = Record(
        metadata[0].record_id, metadata[0].source, metadata[0].length_quartile,
        metadata[0].speaker_count_bucket, metadata[0].speaker_ids, metadata[0].scenario_id,
        "this exact fabricated sentence appears in the fake protected pool",
    )
    # Deliberately force a second record to share every token with a pool entry, reordered so it is
    # neither an exact match nor a containment match (only token-Jaccard = 1.0 fires, non-fatal review
    # flag), to prove non-fatal flags survive into the manifest rather than being silently discarded.
    metadata[20] = Record(
        metadata[20].record_id, metadata[20].source, metadata[20].length_quartile,
        metadata[20].speaker_count_bucket, metadata[20].speaker_ids, metadata[20].scenario_id,
        "completely a sentence unrelated acceptance fabricated",
    )

    pool = [
        ("fake-protected:001", "this exact fabricated sentence appears in the fake protected pool"),
        ("fake-protected:002", "a second unrelated fabricated protected-pool sentence for source counting"),
        ("fake-acceptance:001", "a completely unrelated fabricated acceptance sentence"),
    ]
    return metadata, pool


def _build_undersized_fixture() -> tuple[list[Record], list[tuple[str, str]]]:
    """A fixture whose eligible pool cannot possibly reach the target, even with top-up -- proves the
    shortfall path reports honestly instead of pretending to succeed."""
    metadata = [
        Record(f"tiny-{i:02d}", "only-source", 1, "2", (f"speaker-{i}",), f"scenario-{i}",
               f"fabricated tiny fixture sentence number {i}")
        for i in range(5)
    ]
    return metadata, []


def _build_duplicate_id_fixture() -> list[Record]:
    """A fixture with a deliberately duplicated record_id, to prove `_validate_metadata()` actually
    fires rather than silently accepting malformed metadata."""
    return [
        Record("dup-01", "only-source", 1, "2", ("speaker-0",), "scenario-0", "fabricated sentence one"),
        Record("dup-01", "only-source", 1, "2", ("speaker-1",), "scenario-1", "fabricated sentence two"),
    ]


def run_selftest() -> dict[str, Any]:
    metadata, pool = _build_selftest_fixture()
    n = 8  # smaller than the real 24 -- fixture is small and this is a mechanism proof, not a real audit

    # Pinned 2026-08-13 (fourth review): required_pool_sources is now mandatory everywhere, and these two
    # content hashes were computed once from the fixture's actual pool (via _pool_fingerprint) and hardcoded
    # here -- not re-derived at test time -- so this is a real frozen-spec check, not a tautology that would
    # trivially pass no matter what the fixture contained.
    required_sources = {
        "fake-protected": PoolSourceSpec(
            min_count=2,
            expected_content_sha256="f1657d03117b61d792162de3bc5f6679d78fa18509b8230eeb29341faf5529a3",
        ),
        "fake-acceptance": PoolSourceSpec(
            min_count=1,
            expected_content_sha256="ae734df3205d03d3640d2a21981a8e2951d7ba56ab4548b38119f3308623eb9b",
        ),
    }

    run_a = select_sample(metadata, pool, required_sources, sample_size=n, seed=AUDIT_SEED)
    run_b = select_sample(metadata, pool, required_sources, sample_size=n, seed=AUDIT_SEED)
    run_c = select_sample(metadata, pool, required_sources, sample_size=n, seed=AUDIT_SEED + 1)

    checks: dict[str, bool] = {}

    checks["determinism_same_seed_identical_manifest"] = (run_a == run_b)
    checks["different_seed_gives_different_selection"] = (
        run_a["selected_record_ids"] != run_c["selected_record_ids"]
    )

    # Equality-when-possible: this fixture has 48 eligible candidates for an 8-slot draw, so both runs
    # must hit the target exactly, with no shortfall reported.
    checks["sample_size_achieved_equals_target_when_pool_sufficient"] = (
        run_a["sample_size_achieved"] == n and run_a["shortfall_reason"] is None and not run_a["must_stop"]
        and run_c["sample_size_achieved"] == n and run_c["shortfall_reason"] is None and not run_c["must_stop"]
    )

    # Speaker/scenario cap: no scenario or speaker identity should appear more than the cap among selected,
    # counting every speaker_id in a multi-party record's tuple, not just a first/only one.
    id_to_record = {r.record_id: r for r in metadata}
    cap_ok = True
    multi_speaker_case_exercised = False
    for run in (run_a, run_c):
        speaker_counts: dict[str, int] = {}
        scenario_counts: dict[str, int] = {}
        for rid in run["selected_record_ids"]:
            rec = id_to_record[rid]
            if len(rec.speaker_ids) > 1:
                multi_speaker_case_exercised = True
            for sid in rec.speaker_ids:
                speaker_counts[sid] = speaker_counts.get(sid, 0) + 1
            if rec.scenario_id is not None:
                scenario_counts[rec.scenario_id] = scenario_counts.get(rec.scenario_id, 0) + 1
        if any(v > SPEAKER_SCENARIO_CAP for v in speaker_counts.values()):
            cap_ok = False
        if any(v > SPEAKER_SCENARIO_CAP for v in scenario_counts.values()):
            cap_ok = False
    checks["speaker_and_scenario_cap_respected"] = cap_ok
    # This check confirms the multi-speaker fixture records (idx % 7 == 0) actually exist and are eligible
    # to be drawn -- not that any specific run selected one (seed-dependent) -- so the multi-speaker cap
    # path is exercised by the fixture design, not merely present in unreachable code.
    checks["multi_speaker_fixture_records_exist"] = any(len(r.speaker_ids) > 1 for r in metadata)

    # Collision screening unit-tested directly, independent of whether the stratified draw happens to pick
    # the forced-collision record for a given seed/quota outcome.
    forced_collision_record = metadata[0]
    collision_result = screen_collisions(forced_collision_record, pool)
    checks["direct_collision_check_flags_forced_duplicate"] = (
        collision_result.fatal and any("normalized-exact match" in r for r in collision_result.reasons)
    )
    clean_record = metadata[10]
    clean_result = screen_collisions(clean_record, pool)
    checks["direct_collision_check_passes_clean_record"] = not clean_result.fatal

    # Non-fatal review flags must survive into the manifest for any selected record that has them, with no
    # mutable "adjudicated" field baked into the frozen manifest (2026-08-13 fix).
    review_flag_record = metadata[20]
    review_collision = screen_collisions(review_flag_record, pool)
    checks["direct_check_flags_nonfatal_review_case"] = (
        not review_collision.fatal and len(review_collision.reasons) > 0
    )
    checks["manifest_review_flags_well_formed_no_mutable_field"] = all(
        isinstance(e.get("flags"), list) and len(e["flags"]) > 0 and "adjudicated" not in e
        for e in run_a["collision_review_flags_requiring_adjudication"]
    )

    # selected_records carries a stratum and content hash per record, matching the actual record content.
    checks["selected_records_have_correct_content_hashes"] = all(
        entry["content_sha256"] == hashlib.sha256(id_to_record[entry["record_id"]].input_text.encode("utf-8")).hexdigest()
        and entry["stratum"] == str(_stratum_key(id_to_record[entry["record_id"]]))
        for entry in run_a["selected_records"]
    ) and len(run_a["selected_records"]) == run_a["sample_size_achieved"]

    # Pool fingerprint now reports per-source counts, not just one flat aggregate hash -- confirm all three
    # fake sources ("fake-protected", "fake-acceptance") are individually visible with correct counts.
    fp = run_a["pool_fingerprint"]
    checks["pool_fingerprint_has_per_source_breakdown"] = (
        fp["sources"].get("fake-protected", {}).get("count") == 2
        and fp["sources"].get("fake-acceptance", {}).get("count") == 1
        and fp["total_pool_size"] == 3
    )

    # Fail-closed pool validation (2026-08-13, third and fourth reviews): a pool missing a required
    # source, short on the required count, containing an unexpected source, or mismatching a pinned content
    # hash must raise -- not just look wrong in the fingerprint to a reviewer who happens to check, and not
    # skippable by a caller who simply omits the argument (required_pool_sources has no default anymore).
    try:
        select_sample(metadata, pool, {
            "fake-protected": PoolSourceSpec(2), "fake-acceptance": PoolSourceSpec(1), "fake-missing": PoolSourceSpec(1),
        }, sample_size=n, seed=AUDIT_SEED)
        pool_validation_catches_missing_source = False
    except ValueError as e:
        pool_validation_catches_missing_source = "missing required source" in str(e)
    checks["pool_validation_catches_missing_source"] = pool_validation_catches_missing_source

    try:
        select_sample(metadata, pool, {"fake-protected": PoolSourceSpec(2)},  # omits "fake-acceptance" on purpose
                      sample_size=n, seed=AUDIT_SEED)
        pool_validation_catches_unexpected_source = False
    except ValueError as e:
        pool_validation_catches_unexpected_source = "unexpected source" in str(e)
    checks["pool_validation_catches_unexpected_source"] = pool_validation_catches_unexpected_source

    try:
        select_sample(metadata, pool, {
            "fake-protected": PoolSourceSpec(2, expected_content_sha256="0" * 64),  # deliberately wrong
            "fake-acceptance": PoolSourceSpec(1),
        }, sample_size=n, seed=AUDIT_SEED)
        pool_validation_catches_hash_mismatch = False
    except ValueError as e:
        pool_validation_catches_hash_mismatch = "content hash mismatch" in str(e)
    checks["pool_validation_catches_hash_mismatch"] = pool_validation_catches_hash_mismatch

    # unused_leftover_record_ids (2026-08-13, third review): must be well-formed -- valid record IDs, no
    # overlap with what was actually selected, since a post-adjudication top-up draws from this list.
    unused_ids = set(run_a["unused_leftover_record_ids"])
    selected_ids = set(run_a["selected_record_ids"])
    all_ids = {r.record_id for r in metadata}
    checks["unused_leftovers_well_formed"] = (
        unused_ids.issubset(all_ids) and unused_ids.isdisjoint(selected_ids)
    )

    # Regression test for the tie-break bias this package's own review caught: quota allocation must vary
    # with the seed, and -- checked across every stratum key, not just one -- no key may be selected in
    # every one of a spread of seeds nor excluded from every one (both would indicate a systematic bias).
    strata_sizes: dict[tuple, int] = {}
    for r in metadata:
        strata_sizes.setdefault(_stratum_key(r), 0)
        strata_sizes[_stratum_key(r)] += 1
    import random as _random
    n_seeds = 30
    quota_runs = []
    for s in range(n_seeds):
        rng = _random.Random(1000 + s)
        quota_runs.append(_largest_remainder_quotas(strata_sizes, n, rng))
    checks["quota_tiebreak_varies_across_seeds"] = len({tuple(sorted(q.items())) for q in quota_runs}) > 1
    selection_frequency = {k: sum(1 for q in quota_runs if q.get(k, 0) > 0) for k in strata_sizes}
    checks["no_stratum_always_selected_or_always_excluded"] = all(
        0 < freq < n_seeds for freq in selection_frequency.values()
    )

    # Shortfall path: a fixture too small to ever reach target must say so explicitly and set must_stop.
    # required_pool_sources={} deliberately -- this fixture's pool is empty by design (see
    # _build_undersized_fixture), so no source is required here; that's orthogonal to what's under test.
    tiny_metadata, tiny_pool = _build_undersized_fixture()
    tiny_run = select_sample(tiny_metadata, tiny_pool, {}, sample_size=24, seed=AUDIT_SEED)
    checks["shortfall_reported_when_pool_insufficient"] = (
        tiny_run["sample_size_achieved"] == 5 and tiny_run["shortfall_reason"] is not None
        and tiny_run["must_stop"] is True
    )

    # Preflight validation must fire on structurally malformed metadata (2026-08-13 addition), not silently
    # accept it.
    duplicate_id_metadata = _build_duplicate_id_fixture()
    try:
        select_sample(duplicate_id_metadata, [], {}, sample_size=2, seed=AUDIT_SEED)
        preflight_caught_duplicate = False
    except ValueError as e:
        preflight_caught_duplicate = "duplicate record_id" in str(e)
    checks["preflight_validation_catches_duplicate_id"] = preflight_caught_duplicate

    # compute_manifest_hash is deterministic and content-sensitive (changes if the manifest content does).
    hash_a = compute_manifest_hash(run_a)
    hash_a_again = compute_manifest_hash(run_a)
    hash_c = compute_manifest_hash(run_c)
    checks["manifest_hash_deterministic_and_content_sensitive"] = (
        hash_a == hash_a_again and hash_a != hash_c
    )

    all_passed = all(checks.values())
    receipt = {
        "selftest": True,
        "fixture": "fabricated, 48 synthetic placeholder records, no real dataset content",
        "run_a_manifest": run_a,
        "run_a_manifest_hash": hash_a,
        "run_c_seed": AUDIT_SEED + 1,
        "run_c_selected_record_ids": run_c["selected_record_ids"],
        "direct_collision_check": {
            "forced_collision_record_id": forced_collision_record.record_id,
            "fatal": collision_result.fatal,
            "reasons": collision_result.reasons,
        },
        "direct_nonfatal_review_check": {
            "record_id": review_flag_record.record_id,
            "fatal": review_collision.fatal,
            "reasons": review_collision.reasons,
        },
        "quota_tiebreak_fairness_probe": {
            "seeds_tested": n_seeds,
            "distinct_quota_allocations": len({tuple(sorted(q.items())) for q in quota_runs}),
            "selection_frequency_per_stratum": {str(k): v for k, v in sorted(selection_frequency.items())},
        },
        "shortfall_path_probe": tiny_run,
        "preflight_validation_probe": {"duplicate_id_error_raised": preflight_caught_duplicate},
        "checks": checks,
        "all_checks_passed": all_passed,
    }
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", required=True,
                         help="Run the synthetic self-test. This is the only supported mode in this "
                              "package; real-mode invocation requires separate authorization and a real "
                              "metadata source this script does not itself provide.")
    parser.add_argument("--receipt-out", type=Path, default=None,
                         help="Optional path to write the self-test receipt JSON.")
    args = parser.parse_args()

    receipt = run_selftest()
    print(json.dumps(receipt, indent=2))

    if args.receipt_out:
        # newline="\n" forced explicitly (found necessary 2026-08-13, post-approval, pre-push): Python's
        # default text-mode write translates "\n" to the platform line separator, which is CRLF on
        # Windows -- so a receipt written this way and hashed locally does not match the LF-normalized
        # blob `git add`/`commit` stores under core.autocrlf=true, despite identical content. Every
        # SHA-256 cited throughout this package's five-revision review history was of the CRLF working-
        # tree file, not what actually ends up in the repository. Forcing LF here makes the file
        # byte-identical in the working tree, the git blob, and on any platform, closing that gap for
        # good rather than leaving a hash that quietly stops matching once committed.
        with open(args.receipt_out, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(receipt, indent=2))
        digest = hashlib.sha256(args.receipt_out.read_bytes()).hexdigest()
        print(f"\nReceipt written to {args.receipt_out} (SHA-256 {digest})")

    if not receipt["all_checks_passed"]:
        print("\nSELF-TEST FAILED", flush=True)
        return 1
    print("\nSELF-TEST PASSED", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
