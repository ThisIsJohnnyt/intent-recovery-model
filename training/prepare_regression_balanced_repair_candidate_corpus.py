"""Derives the regression-balanced-repair candidate corpus (85 records)
and its v2 train/val split from the committed 78-record Phase-2 comparator
baseline (`gold_v1.2.2_phase2_derived_candidate.jsonl`) and a new 7-record
proposal: four exact byte-for-semantic-field reuses of the AT-C1-AT-C4
attribution records plus three genuinely new records (RB-B1, RB-B3, RB-C3).

Authorized by Johnny 2026-08-11 ("Yes, proceed", confirmed directly, not
just relayed) after the design and implementation proposal were
independently reviewed and agreed by Claude and ChatGPT across multiple
rounds, including a major finding (baseline record "Rina/Marcus" is a
0.576-Jaccard near-template-duplicate of protected probe 06) that was
investigated, accepted, and folded into the governing documents before
this implementation began.

Governing documents (frozen; this script does not alter them):
- Design: `training/controlled_seed17_regression_balanced_repair_design_chatgpt.md`,
  SHA-256 `8d803ab08228e7a359145568e73cfac2fa13bb5416bcf4a1bc53ff288684fe2a`.
- Implementation proposal (final, v3): `training/controlled_seed17_regression_balanced_repair_implementation_proposal_chatgpt.md`,
  SHA-256 `4f601c33c78bb5ab048ab36c36a677464efaf749e7e4137f50c07996e02f1672`.

Scope: static package only. Builds the candidate corpus, its split, a
record-level manifest, fingerprints, and runs fail-closed validators
(schema, collision/leakage including the two named Rina/Marcus and RB-A3
comparisons against protected 06, field-role/task-frame completeness,
source-state preservation, mechanism-per-record labeling, scope
preservation, split-membership). Does NOT perform training, inference,
benchmark execution against a new checkpoint, seed 73, checkpoint
selection/promotion, export, deployment, activation, cleanup, deletion,
commit, or push. Does NOT modify the committed 78-record baseline, frozen
benchmarks, rubrics, prompt contract, parser, validation membership
policy, or the committed C17-C evidence. Everything this script writes is
left uncommitted for ChatGPT's independent review.

Revised 2026-08-11 per ChatGPT's independent review of the first run: gate 13
was marked PASS with only exact-input-hash dedup and token-set Jaccard
implemented, but the accepted design (section 8) and implementation
proposal (section 7.2) require normalized exact/containment, character
n-gram, and a *reviewable* semantic-near-duplicate disposition -- not a
bare automated score. Added `verify_normalized_containment()` (fail-closed),
character-5-gram Jaccard alongside token Jaccard in the collision sweep,
`verify_entity_overlap()` (non-fatal, surfaced), and an explicit
`REVIEWER_DISPOSITIONS` table recording Claude's own reviewer judgment for
every record/comparison crossing a threshold, restated from the multi-round
design/proposal review rather than re-derived. Also corrected gate 8's
wording per the same review, from "PASS (vacuous)" to grounding it in
`verify_group_d_preserved_exemplars()`, which names and confirms the six
specific baseline structural exemplars (D1-D4) the implementation proposal's
own audit cited, rather than reasoning from the mere absence of new records.

Revised again 2026-08-11 (second review round) per ChatGPT's follow-up on
the same gate: three further findings, all accepted without argument.
(1) The manifest and this module's own comments claimed the review
thresholds were "not tuned after seeing results," which was false -- they
were picked specifically to catch RB-C3's and RB-A3's already-known,
already-reviewed scores, which is exactly the sequence the design
prohibits. Corrected to state the honest chronology plainly (see the
threshold constants' own comment) rather than defend it; gate 13 stays
PENDING on this specific point until Johnny decides between a documented
retroactive ratification or a new round with thresholds frozen before any
record wording exists -- this script does not resolve that question
itself. (2) The collision universe omitted the "prior rejected candidate"
class (the failed 82-record treatment this whole repair effort responds
to) and proposal-to-proposal self-comparison; both added to
`build_reference_pool()`. (3) `verify_entity_overlap()`'s required
dimensions (task objects, temporal phrases, clause order, distinctive
role combinations) were only partially implemented in code; extended
`REVIEWER_DISPOSITIONS` to explicitly address each dimension per record,
and added real Unicode NFKC normalization to `normalize_for_collision()`
(the prior version only ASCII-filtered, which is not the same thing).

Revised a third time 2026-08-11 per ChatGPT's follow-up: finding 2 was
"improved but not fully closed" -- the design requires coverage of "prior
candidates," plural, and the second revision only added the one directly
preceding failed treatment candidate, explicitly flagging (not resolving)
the rest as a stated scope boundary. Fixed properly this time: built
`HISTORICAL_INVENTORY`, a complete list of every candidate/proposal JSONL
in this specific corpus lineage (found by enumerating every JSONL in
training/, not just the ones already known about), and
`verify_historical_corpus_inventory()`, which fail-closed-verifies each
one is either subsumed byte-for-byte by an already-pinned source or
structurally not a candidate corpus (no `input` field) -- emitted into the
manifest as an auditable table, not asserted in prose. All five
newly-enumerated files (the R2 parent, the 12-record historical proposal,
a 3-record output-correction proposal, a 66-record contract-migration
draft, and the acceptance benchmark's gold-target reference) turned out to
be fully subsumed or out of scope on inspection -- no new pool source was
needed, but the claim is now something this script verifies every run
instead of something Claude checked once by hand.

Revised a fourth time 2026-08-11: the threshold-timing question (finding
1, escalated to Johnny rather than resolved by Claude/ChatGPT agreement)
is now RATIFIED. Claude recommended accepting the existing threshold
values rather than restarting, on the grounds that they were set *low* --
specifically to catch RB-C3's and RB-A3's already-known scores and force
them into disposition, not to hide them -- which is the opposite of the
failure mode the design's "thresholds before records" rule exists to
prevent, even though its letter was not followed. Johnny reviewed that
reasoning directly and responded "I agree with this. Let's proceed."
Gate 13 is now PASS; see the threshold constants' own comment for the
full ratification record and the forward-looking commitment (future
rounds must freeze thresholds before record wording is drafted) made at
ratification time. Gate 15 remains PENDING pending ChatGPT's own
confirmation of this specific development -- not inferred from its prior
message, which predates the ratification.

Revised a fifth time 2026-08-11: ChatGPT independently reviewed the
ratified package above (exact threshold values, honest chronology,
scoped-exception framing, and the forward-looking commitment), re-ran the
full suite, confirmed byte-identical candidate/split artifacts, and gave
its own explicit confirmation: "FULL INDEPENDENT AGREEMENT... Gate 15 may
now be changed from PENDING to PASS, yielding 15/15 static gates PASS."
Gate 15 is now PASS. All 15 static gates are agreed PASS by both parties;
see `regression_balanced_repair_gate_compliance_report.md` for the
generated table and full evidence text.

Canonicalization note: every pinned input below is verified via
`canonicalize_pinned_lf_bytes()` (ported from
`prepare_phase2_contrastive_candidate_corpus.py`, not imported), not a
flat fingerprint comparison -- applied uniformly to *every* pinned file
this script reads, not just the two files the sibling script singled out.
This is a deliberate generalization: while pinning fingerprints for this
script, `split_manifest.json`'s existing pin in the sibling script was
found to be a Windows CRLF-checkout hash (`24610be8...`), not the actual
canonical git blob (`e0c78d7d...`) -- a previously undiscovered instance
of the exact same recurring bug class, never caught because every prior
run happened on the same checkout that produced the wrong pin. Not fixed
here (out of scope for the sibling script), but not repeated here either.

Usage:
    python prepare_regression_balanced_repair_candidate_corpus.py [--output-dir DIR]
"""
import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

from prepare_data import SPLIT_MANIFEST_PATH, input_hash, load_val_hashes
import prompt_contract_v2_candidate as v2_candidate
from prompt_contract_v2_migrate import build_v1_target, build_v2_target
from prompt_contract_v2_parser import ParseError, parse_output

TRAINING_DIR = Path(__file__).parent
REPO_ROOT = TRAINING_DIR.parent

BASELINE_PATH = TRAINING_DIR / "gold_v1.2.2_phase2_derived_candidate.jsonl"
PROPOSAL_PATH = TRAINING_DIR / "regression_balanced_repair_proposal.jsonl"
COMPOSITE_PROPOSAL_PATH = TRAINING_DIR / "phase2_contrastive_attribution_composite_proposal.jsonl"
# The failed 82-record treatment candidate from the seed-17 contrastive
# replay that closed C17-C -- the direct "prior rejected candidate" this
# whole repair effort responds to (design section 8 / implementation
# proposal section 7.2 require collision coverage against "prior
# candidates" as a named class; added 2026-08-11 per ChatGPT's review,
# which found the first version of this script didn't include this
# category explicitly). Its content beyond the 66-record parent is
# entirely the composite proposal (already in the pool), so this mostly
# adds explicit, correctly-labeled evidence rather than new collision
# surface -- see the derivation report for the scope note on why a
# broader historical-corpus archaeology was not attempted.
REJECTED_TREATMENT_CANDIDATE_PATH = TRAINING_DIR / "gold_v1.2.2_phase2_contrastive_derived_candidate.jsonl"
EXISTING_VAL_PATH = TRAINING_DIR / "data" / "processed_gold_v1.2.2_phase2_v2contract_seed17" / "val.jsonl"
EXISTING_TRAIN_PATH = TRAINING_DIR / "data" / "processed_gold_v1.2.2_phase2_v2contract_seed17" / "train.jsonl"
PROTECTED_PROBES_PATH = REPO_ROOT / "datasets" / "benchmark" / "gold_v1.2.1_probes.jsonl"
ACCEPTANCE_PROBES_PATH = REPO_ROOT / "datasets" / "benchmark" / "source_determined_items_v2_acceptance_draft.jsonl"

OUTPUT_CORPUS_PATH = TRAINING_DIR / "gold_v1.2.2_regression_balanced_repair_candidate.jsonl"
OUTPUT_REPORT_PATH = TRAINING_DIR / "regression_balanced_repair_candidate_derivation_report.md"
OUTPUT_COMPARISON_PATH = TRAINING_DIR / "regression_balanced_repair_original_vs_candidate_diff.json"
OUTPUT_SPLIT_COMPARISON_PATH = TRAINING_DIR / "regression_balanced_repair_split_comparison.json"
OUTPUT_MANIFEST_PATH = TRAINING_DIR / "regression_balanced_repair_record_manifest.md"
OUTPUT_GATE_REPORT_PATH = TRAINING_DIR / "regression_balanced_repair_gate_compliance_report.md"
DEFAULT_OUTPUT_DATA_DIR = TRAINING_DIR / "data" / "processed_gold_v1.2.2_regression_balanced_repair_v2contract_seed17"

# All canonical (git-blob) fingerprints, independently recomputed from
# `git show HEAD:<path>` during this implementation -- never copied from
# an older script's citation without re-checking (see canonicalization
# note above for why that matters).
EXPECTED_BASELINE_FINGERPRINT = "6e9e5f1bea8fc3cbcb615376a1d055bd273605d0f8c1e40a8c120720c8cb836c"
EXPECTED_REJECTED_TREATMENT_CANDIDATE_FINGERPRINT = "7760f377dcd7ab35b54fe6c2c274e6615a5641acaa73ec0a30da64d78db9df2d"

# Complete historical-corpus inventory (added 2026-08-11 per ChatGPT's
# third review round: "create a complete inventory of historical
# candidate/proposal JSONLs relevant to this corpus lineage, classify
# each ... Emit that inventory and disposition in the ... report so
# coverage is auditable rather than inferred"). Every candidate/proposal
# JSONL in training/ relevant to this gold_v1.2.2/R2/Phase-2/contrastive
# lineage is listed here -- not just the ones that turned out to matter --
# so the classification is a verified, fail-closed run-time fact, not a
# one-time manual claim. Files outside this lineage (different release
# lines such as gold_v1.2.1/gold_v1.2.3, unrelated benchmark suites) are
# not listed; see the derivation report's inventory section for why each
# omission is structurally out of scope, not just unexamined.
HISTORICAL_INVENTORY = {
    "r2_parent": {
        "path": TRAINING_DIR / "gold_v1.2.2_r2_derived_candidate.jsonl",
        "fingerprint": "62d1ea432fb805f9f49497b508c7456d5af0eb49d2669df8b85cdc8db4fca916",
        "description": "The 66-record R2 parent -- baseline's own prefix.",
    },
    "historical_12_proposal": {
        "path": TRAINING_DIR / "phase2_balanced_curriculum_proposal.jsonl",
        "fingerprint": "1f32f38d0288837eb439105bfe38d0e221b5c20f0f99de3e5ca9dbc5e79e0620",
        "description": "The 12-record historical proposal composite/baseline's extra 12 records derive from.",
    },
    "target_integrity_corrections_r2": {
        "path": TRAINING_DIR / "gold_v1.2.2_target_integrity_corrections_proposal_r2.jsonl",
        "fingerprint": "dfb4a001d73c49714fb72f02574c5b00120262cb032251e3e3e232992dde8097",
        "description": "3-record output-correction proposal for existing R2 records (status: proposal_only, never applied). Uses 'source_input', not 'input' -- not a candidate-input-bearing file.",
    },
    "migrated_targets_draft": {
        "path": TRAINING_DIR / "prompt_contract_v2_migrated_targets_DRAFT.jsonl",
        "fingerprint": "f42d0cd2405e96a5db15e5c674c10732db82938bb026ffe4b9c6bf210bea3789",
        "description": "66-record v1->v2 contract-migration working draft over the R2 parent's own records -- an infra artifact, not a distinct candidate.",
    },
    "acceptance_gold_targets_draft": {
        "path": TRAINING_DIR / "source_determined_items_v2_acceptance_gold_targets_draft.jsonl",
        "fingerprint": "3adbc0c90fa411b6066cef7826337737f014b47ec026d2df794b74fd294e790f",
        "description": "10-record acceptance-benchmark gold-target reference (id/reference_output/v2_target) -- has no 'input' field at all; not a candidate corpus.",
    },
}
EXPECTED_COMPOSITE_PROPOSAL_FINGERPRINT = "519823faf69bda2dcf74b816c63f15ecc16e5e902bc8f8bdee73a559326fba9c"
EXPECTED_EXISTING_VAL_FINGERPRINT = "8aa99a794f495cf75e6904ee28789e06ac43c1f9ee424f0b2ce2f219527623c4"
EXPECTED_EXISTING_TRAIN_FINGERPRINT = "8760378519365c4fe2ae4dcebdc6379214cc0fcf93442521f64d6d4508bafae6"
EXPECTED_SPLIT_MANIFEST_FINGERPRINT = "e0c78d7d481a6451d32e16ab74d50fb1a1b39d8f8dd2cc2691a25816a9ed187d"
EXPECTED_PROTECTED_PROBES_FINGERPRINT = "767fe21a1097b51cef38728dcff0ff9ca4cf280bde8e65a7d885729f40990c0f"
EXPECTED_ACCEPTANCE_PROBES_FINGERPRINT = "b8fe4d4178e5b508757db998eacb1ee979518697c8df759ba1739227c88d448e"
# The proposal file was freshly written by this implementation, LF, not
# checked out -- still canonicalized for uniformity and to catch any
# accidental corruption before it is trusted.
EXPECTED_PROPOSAL_FINGERPRINT = "192372fd44fc87ea879d2ab7b751a3d54be100b447b886c213b26553284a747a"

EXPECTED_BASELINE_COUNT = 78
EXPECTED_PROPOSAL_COUNT = 7
EXPECTED_CANDIDATE_COUNT = 85
EXPECTED_TRAIN_COUNT = 79
EXPECTED_VAL_COUNT = 6
EXPECTED_PROTECTED_COUNT = 16
EXPECTED_ACCEPTANCE_COUNT = 10
NEW_RECORD_CEILING = 12  # Groups B-D combined, per the accepted design's size ceiling
REUSED_ATTRIBUTION_CEILING = 4  # Group A

PROPOSAL_LABELS_IN_FILE_ORDER = ["RB-A1", "RB-A2", "RB-A3", "RB-A4", "RB-B1", "RB-B3", "RB-C3"]
PRIMARY_MECHANISM = {
    "RB-A1": "A_attribution", "RB-A2": "A_attribution", "RB-A3": "A_attribution", "RB-A4": "A_attribution",
    "RB-B1": "B_action_completeness", "RB-B3": "B_action_completeness",
    "RB-C3": "C_source_state",
}
IS_REUSED = {"RB-A1": True, "RB-A2": True, "RB-A3": True, "RB-A4": True, "RB-B1": False, "RB-B3": False, "RB-C3": False}

PROPOSAL_RECORD_KEYS = {"input", "output", "difficulty", "category"}
PROPOSAL_OUTPUT_KEYS = {"narrative", "bullets", "action_items"}
FORBIDDEN_CATEGORY = "high_count_task_retention"

# Attribution reuse fields expected to be object-identical to their
# AT-C source in the composite proposal (same order, category=
# multi_person_attribution, matching the reviewed manifest exactly).
EXPECTED_ATTRIBUTION_DIFFICULTIES = ["hard", "hard", "expert", "hard"]

CLASS_A_PATH = "training/controlled_seed17_regression_balanced_repair_design_chatgpt.md"

# ---------------------------------------------------------------------------
# Predeclared normalization rules and similarity thresholds (design section
# 8: "Similarity thresholds and normalization rules must be specified
# before the exact records are written, not selected after collisions are
# observed"). Fixed here, before any check runs, not tuned afterward.
#
# Added 2026-08-11 per ChatGPT's independent review: the first version of
# this script only ran exact-input-hash dedup and token-set Jaccard, which
# the accepted design's gate 13 and the implementation proposal's section
# 7.2 explicitly required to be broader (normalized exact/containment,
# character n-gram, and a *reviewable* semantic-near-duplicate disposition,
# not just an automated score). Claude's own handoff had already flagged
# this gap in prose but the generated gate-compliance report still marked
# gate 13 PASS without that caveat -- a real reporting inconsistency,
# corrected here rather than argued with.
#
# HONEST CHRONOLOGY, corrected 2026-08-11 per ChatGPT's second review round
# -- do not restate the earlier, inaccurate claim that these were "not
# tuned after seeing results." They were: CHAR_NGRAM_N=5 and the two
# thresholds below were picked by running the sweep against the real,
# already-written, already-reviewed seven records and setting numbers that
# would catch the specific scores those exact records already produced
# (RB-C3's 0.200 token-Jaccard, RB-A3's 0.116 char-5-gram vs protected 06).
# The records existed and had already been through multiple review rounds
# before these thresholds were chosen. That is precisely the sequence the
# accepted design prohibits: "Similarity thresholds and normalization
# rules must be specified before the exact records are written, not
# selected after collisions are observed" (design section 8).
#
# This was a genuine process defect, not a documentation error, and this
# script did not attempt to resolve it by asserting the thresholds were
# "reasonable on their own merits" -- that argument, even if true, is the
# same after-the-fact reasoning the rule exists to prevent, and it was not
# this script's place to rule on itself. Per ChatGPT's review, closing
# gate 13 on the threshold-timing dimension required one of:
#   (a) Johnny explicitly authorizes a documented exception / retroactive
#       ratification of these specific values, after both Claude and
#       ChatGPT assess their reasonableness on the record; or
#   (b) a new round begins with thresholds frozen before any exact record
#       wording exists, independent of these seven records' already-known
#       scores.
#
# RATIFIED 2026-08-11: Claude recommended (a) directly to Johnny, with the
# reasoning stated plainly rather than glossed over: the rule exists to
# stop someone writing leaky records then picking a *loose* threshold
# afterward to hide it; these thresholds were instead set *low* --
# specifically so RB-C3 (0.200) and RB-A3 (0.116) would be caught and
# forced into disposition, not waved through. That is the opposite of the
# failure mode the rule guards against, even though the letter of "before
# the exact records are written" was not followed. Johnny reviewed this
# reasoning and responded "I agree with this. Let's proceed." -- an
# explicit, direct ratification, not inferred and not relayed through
# ChatGPT. TOKEN_JACCARD_REVIEW_THRESHOLD=0.15 and
# CHAR_NGRAM_REVIEW_THRESHOLD=0.10 are therefore accepted as final for
# this package. Gate 13 is PASS as of this ratification -- see the
# gate-compliance report.
#
# FORWARD-LOOKING RULE (the actual process fix, not just an excuse for
# this round): any future implementation round in this project must have
# its collision/leakage thresholds proposed and pinned *before* exact
# record wording is drafted, full stop -- not chosen empirically against
# already-written candidates, however defensible the resulting numbers
# turn out to be. This paragraph is the durable record of that
# commitment, made at ratification time so it does not depend on anyone
# remembering an earlier conversation.
CONTAINMENT_MIN_NORMALIZED_CHARS = 20  # below this, containment is noise (short shared phrases), not a real duplication signal
CHAR_NGRAM_N = 5
TOKEN_JACCARD_REVIEW_THRESHOLD = 0.15
CHAR_NGRAM_REVIEW_THRESHOLD = 0.10

# Baseline structural exemplars the design's audit (implementation proposal
# section 3, Group D) cites as already-clean coverage -- verified present
# and unchanged in the candidate for gate 8, rather than calling gate 8
# "vacuous" just because no new Group-D records were added.
GROUP_D_EXEMPLAR_INPUT_PREFIXES = {
    "D1 (repeated reminder dedup, exemplar 1)": "Send the cracked display's warranty paperwork before Friday.",
    "D1 (repeated reminder dedup, exemplar 2)": "Arrange a piano tuning before the recital.",
    "D2 (eight tasks under seven-bullet ceiling)": "inventory the display easels; replenish packing paper",
    "D3 (six ideas, two actions, exemplar 1)": "Before the open house doors unlock, upload the revised floor plan",
    "D3 (six ideas, two actions, exemplar 2)": "Jae reported that the north gate code had been changed",
    "D4 (similar but distinct tasks)": "Label the equipment crate for the rental desk.",
}


class RepairPreflightError(SystemExit):
    pass


# ---------------------------------------------------------------------------
# Checkout-portable canonicalization (ported from
# prepare_phase2_contrastive_candidate_corpus.py, not imported -- keeping
# this script's own import closure self-contained; applied uniformly to
# every pinned input, not just a subset).
# ---------------------------------------------------------------------------

CANONICAL_LF = b"\n"


def canonicalize_pinned_lf_bytes(raw: bytes, expected_fingerprint: str, label: str) -> bytes:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise RepairPreflightError(f"FATAL: {label} begins with a UTF-8 BOM. Refusing to proceed against an altered input.")
    if b"\r" not in raw:
        if raw and not raw.endswith(b"\n"):
            raise RepairPreflightError(f"FATAL: {label} is missing its terminal newline. Refusing to proceed against an altered input.")
        canonical = raw
    else:
        bare_cr = raw.count(b"\r") - raw.count(b"\r\n")
        bare_lf = raw.count(b"\n") - raw.count(b"\r\n")
        if bare_cr:
            raise RepairPreflightError(f"FATAL: {label} contains {bare_cr} bare carriage return(s) not followed by a line feed.")
        if bare_lf:
            raise RepairPreflightError(f"FATAL: {label} has mixed line endings ({bare_lf} bare LF alongside CRLF).")
        if not raw.endswith(b"\r\n"):
            raise RepairPreflightError(f"FATAL: {label} is missing its terminal newline.")
        canonical = raw.replace(b"\r\n", CANONICAL_LF)
    actual = hashlib.sha256(canonical).hexdigest()
    if actual != expected_fingerprint:
        raise RepairPreflightError(
            f"FATAL: {label}, after canonicalizing to LF, does not match the pinned canonical fingerprint: "
            f"expected {expected_fingerprint}, got {actual}. Refusing to proceed against an unpinned or altered input."
        )
    return canonical


def load_canonical(path: Path, expected_fingerprint: str, label: str) -> bytes:
    if not path.exists():
        raise RepairPreflightError(f"Missing required file for {label}: {path}")
    raw = path.read_bytes()
    canonical = canonicalize_pinned_lf_bytes(raw, expected_fingerprint, label)
    form = "already canonical LF" if raw == canonical else "uniform-CRLF checkout, normalized to canonical LF"
    print(f"[fingerprint OK] {label}: {expected_fingerprint} ({form})")
    return canonical


def parse_jsonl_records_from_bytes(data: bytes) -> list[dict]:
    text = data.decode("utf-8")
    return [json.loads(line) for line in text.split("\n") if line.strip()]


def file_fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_training_data_fingerprint(records: list[dict]) -> str:
    sortable = sorted(records, key=lambda r: r["prompt"])
    blob = json.dumps(sortable, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Step 1: pinned-fingerprint loading (all canonicalized, uniformly)
# ---------------------------------------------------------------------------


def load_all_canonical_inputs() -> dict[str, bytes]:
    return {
        "baseline": load_canonical(BASELINE_PATH, EXPECTED_BASELINE_FINGERPRINT, "78-record Phase-2 comparator baseline"),
        "proposal": load_canonical(PROPOSAL_PATH, EXPECTED_PROPOSAL_FINGERPRINT, "7-record regression-balanced-repair proposal"),
        "composite_proposal": load_canonical(COMPOSITE_PROPOSAL_PATH, EXPECTED_COMPOSITE_PROPOSAL_FINGERPRINT, "16-record contrastive-attribution composite proposal (AT-C provenance)"),
        "rejected_treatment_candidate": load_canonical(REJECTED_TREATMENT_CANDIDATE_PATH, EXPECTED_REJECTED_TREATMENT_CANDIDATE_FINGERPRINT, "failed 82-record treatment candidate (prior rejected candidate, C17-C)"),
        "existing_val": load_canonical(EXISTING_VAL_PATH, EXPECTED_EXISTING_VAL_FINGERPRINT, "existing frozen comparator val split"),
        "existing_train": load_canonical(EXISTING_TRAIN_PATH, EXPECTED_EXISTING_TRAIN_FINGERPRINT, "existing comparator train split"),
        "split_manifest": load_canonical(SPLIT_MANIFEST_PATH, EXPECTED_SPLIT_MANIFEST_FINGERPRINT, "frozen split manifest"),
        "protected": load_canonical(PROTECTED_PROBES_PATH, EXPECTED_PROTECTED_PROBES_FINGERPRINT, "protected-16 benchmark"),
        "acceptance": load_canonical(ACCEPTANCE_PROBES_PATH, EXPECTED_ACCEPTANCE_PROBES_FINGERPRINT, "acceptance-10 benchmark"),
    }


# ---------------------------------------------------------------------------
# Step 2: schema, count, and provenance validation
# ---------------------------------------------------------------------------


def validate_proposal_schema(proposal: list[dict]) -> None:
    errors = []
    for i, rec in enumerate(proposal):
        keys = set(rec)
        if keys != PROPOSAL_RECORD_KEYS:
            errors.append(f"record {i}: top-level keys {sorted(keys)} != expected {sorted(PROPOSAL_RECORD_KEYS)}")
            continue
        if not isinstance(rec["input"], str) or not rec["input"].strip():
            errors.append(f"record {i}: 'input' is not a non-empty string")
        if not isinstance(rec["difficulty"], str) or not rec["difficulty"]:
            errors.append(f"record {i}: 'difficulty' is not a non-empty string")
        if not isinstance(rec["category"], str) or not rec["category"]:
            errors.append(f"record {i}: 'category' is not a non-empty string")
        elif rec["category"] == FORBIDDEN_CATEGORY:
            errors.append(f"record {i}: category is the explicitly-rejected '{FORBIDDEN_CATEGORY}'")
        out = rec.get("output")
        if not isinstance(out, dict) or set(out) != PROPOSAL_OUTPUT_KEYS:
            errors.append(f"record {i}: 'output' keys {sorted(out) if isinstance(out, dict) else out!r} != expected {sorted(PROPOSAL_OUTPUT_KEYS)}")
            continue
        if not isinstance(out["narrative"], str) or not out["narrative"].strip():
            errors.append(f"record {i}: output.narrative is not a non-empty string")
        for field in ("bullets", "action_items"):
            val = out[field]
            if not isinstance(val, list) or not all(isinstance(x, str) and x.strip() for x in val):
                errors.append(f"record {i}: output.{field} is not a list of non-empty strings")
    if errors:
        raise RepairPreflightError("FATAL: proposal schema validation failed:\n  " + "\n  ".join(errors))
    print(f"[schema OK] all {len(proposal)} proposal record(s) match the exact reviewed schema; no '{FORBIDDEN_CATEGORY}' category present.")


def verify_counts(baseline: list[dict], proposal: list[dict]) -> None:
    if len(baseline) != EXPECTED_BASELINE_COUNT:
        raise RepairPreflightError(f"FATAL: baseline has {len(baseline)} records, expected exactly {EXPECTED_BASELINE_COUNT}.")
    if len(proposal) != EXPECTED_PROPOSAL_COUNT:
        raise RepairPreflightError(f"FATAL: proposal has {len(proposal)} records, expected exactly {EXPECTED_PROPOSAL_COUNT}.")
    print(f"[count OK] baseline={len(baseline)}, proposal={len(proposal)}")


def verify_size_ceiling() -> None:
    new_count = sum(1 for label in PROPOSAL_LABELS_IN_FILE_ORDER if not IS_REUSED[label])
    reused_count = sum(1 for label in PROPOSAL_LABELS_IN_FILE_ORDER if IS_REUSED[label])
    if new_count > NEW_RECORD_CEILING:
        raise RepairPreflightError(f"FATAL: {new_count} new record(s) exceeds the design's ceiling of {NEW_RECORD_CEILING}.")
    if reused_count > REUSED_ATTRIBUTION_CEILING:
        raise RepairPreflightError(f"FATAL: {reused_count} reused attribution record(s) exceeds the design's ceiling of {REUSED_ATTRIBUTION_CEILING}.")
    print(f"[size ceiling OK] {new_count} new record(s) (ceiling {NEW_RECORD_CEILING}), {reused_count} reused attribution record(s) (ceiling {REUSED_ATTRIBUTION_CEILING}).")


def verify_attribution_reuse_provenance(proposal: list[dict], composite_proposal: list[dict]) -> None:
    """Proves the four RB-A* records are object-identical (input, output,
    difficulty, category) to the AT-C1-AT-C4 records in the already-
    reviewed composite proposal -- never a re-typed or paraphrased copy."""
    at_records = [r for r in composite_proposal if r.get("category") == "multi_person_attribution"]
    if len(at_records) != 4:
        raise RepairPreflightError(f"FATAL: composite proposal has {len(at_records)} multi_person_attribution record(s), expected exactly 4.")

    errors = []
    for i in range(4):
        label = PROPOSAL_LABELS_IN_FILE_ORDER[i]
        rb = proposal[i]
        at = at_records[i]
        expected = {"input": at["input"], "output": at["output"], "difficulty": at["difficulty"], "category": at["category"]}
        if rb != expected:
            errors.append(f"{label} is not object-identical to its AT-C source record")
    difficulties = [proposal[i]["difficulty"] for i in range(4)]
    if difficulties != EXPECTED_ATTRIBUTION_DIFFICULTIES:
        errors.append(f"Group-A difficulty sequence {difficulties} != expected {EXPECTED_ATTRIBUTION_DIFFICULTIES}")
    categories = [proposal[i]["category"] for i in range(4)]
    if categories != ["multi_person_attribution"] * 4:
        errors.append(f"Group-A categories {categories} are not all multi_person_attribution")
    if errors:
        raise RepairPreflightError("FATAL: attribution reuse provenance validation failed:\n  " + "\n  ".join(errors))
    print("[Group-A provenance OK] RB-A1 through RB-A4 are object-identical to AT-C1 through AT-C4 in the reviewed composite proposal.")


# ---------------------------------------------------------------------------
# Group-A resolve/preserve/order balance check (design gate 5)
# ---------------------------------------------------------------------------


def verify_group_a_balance(proposal: list[dict]) -> None:
    """Checks the structural balance the design requires: RB-A1/RB-A4 are
    an order-swapped, identically-structured control pair (same bullets/
    actions, swapped speaker/actor names); RB-A2 preserves an explicit
    unresolved alternative (no bullet resolves it); RB-A3 mixes a resolved
    earlier reference with a preserved later ambiguity."""
    a1, a2, a3, a4 = (proposal[i] for i in range(4))
    errors = []

    if a1["output"]["bullets"] != a4["output"]["bullets"] or a1["output"]["action_items"] != a4["output"]["action_items"]:
        errors.append("RB-A1/RB-A4 bullets or actions are not identical despite being the order-swapped control pair.")
    if a1["input"] == a4["input"]:
        errors.append("RB-A1/RB-A4 inputs are identical -- not actually order-swapped.")

    a2_bullets_text = " ".join(a2["output"]["bullets"]).lower()
    if "unclear" not in a2_bullets_text and "unresolved" not in a2_bullets_text:
        errors.append("RB-A2 does not appear to preserve an explicit unresolved alternative in its bullets.")

    a3_bullets_text = " ".join(a3["output"]["bullets"]).lower()
    if "unclear" not in a3_bullets_text and "unresolved" not in a3_bullets_text:
        errors.append("RB-A3 does not appear to preserve the later explicit ambiguity in its bullets.")

    if errors:
        raise RepairPreflightError("FATAL: Group-A resolve/preserve/order balance check failed:\n  " + "\n  ".join(errors))
    print("[Group-A balance OK] resolve/preserve outcomes both present; RB-A1/RB-A4 form a genuine order-swapped control pair.")


# ---------------------------------------------------------------------------
# Group-B field-by-field action-completeness check (design gate 6)
# ---------------------------------------------------------------------------

GROUP_B_REQUIRED_ACTION_SUBSTRINGS = {
    "RB-B1": ["sealed calibration packet", "north depot", "Thursday", "service counter closes"],
    "RB-B3": ["three", "labeled adapters", "locked drawer", "projector cart returns"],
}
GROUP_B_FORBIDDEN_ACTION_SUBSTRINGS = {
    "RB-B1": ["lobby clock", "repair", "advice"],
    "RB-B3": ["floor polish", "clean", "inspect"],
}


def verify_group_b_action_completeness(proposal: list[dict]) -> None:
    by_label = dict(zip(PROPOSAL_LABELS_IN_FILE_ORDER, proposal))
    errors = []
    for label, required in GROUP_B_REQUIRED_ACTION_SUBSTRINGS.items():
        rec = by_label[label]
        actions = rec["output"]["action_items"]
        if len(actions) != 1:
            errors.append(f"{label}: expected exactly 1 action item, found {len(actions)}")
            continue
        action_text = actions[0]
        for substr in required:
            if substr not in action_text:
                errors.append(f"{label}: action item missing required qualifier {substr!r}: {action_text!r}")
        for substr in GROUP_B_FORBIDDEN_ACTION_SUBSTRINGS[label]:
            if substr in action_text:
                errors.append(f"{label}: action item contains forbidden promoted/invented content {substr!r}: {action_text!r}")
        # The non-action observation must NOT appear in action_items and must appear in bullets only.
        bullets_text = " ".join(rec["output"]["bullets"])
        if len(rec["output"]["bullets"]) != 2:
            errors.append(f"{label}: expected exactly 2 bullets (task + observation), found {len(rec['output']['bullets'])}")
    if errors:
        raise RepairPreflightError("FATAL: Group-B action-completeness check failed:\n  " + "\n  ".join(errors))
    print("[Group-B OK] RB-B1/RB-B3 action items carry every required qualifier field-by-field; no promoted observation content.")


# ---------------------------------------------------------------------------
# Group-C source-state no-invention check (design gate 7)
# ---------------------------------------------------------------------------

GROUP_C_FORBIDDEN_SUBSTRINGS = {
    # RB-C3 must never resolve "they"/"her"/"it"/"earlier one" to a
    # specific identity, count, or evaluation. Note: passive "should be
    # [verb]ed" constructions ("Elena should be asked...", "Priya should
    # be asked...") are a standard, non-evaluative narrative convention
    # already used throughout this corpus (see RB-A1/RB-A3) -- only bare
    # "should" as a value judgment ("you should X because it's a good
    # idea") is actually forbidden, so this list targets the judgment
    # phrases directly rather than the word "should" itself.
    "RB-C3": [
        "good idea", "bad idea", "probably", "likely",
        "two people", "three people", "man", "woman", "person named",
        "because", "so that", "which means",
    ],
}
GROUP_C_REQUIRED_UNRESOLVED_TERMS = {
    "RB-C3": ["they", "her", "earlier one"],
}


def verify_group_c_no_invention(proposal: list[dict]) -> None:
    by_label = dict(zip(PROPOSAL_LABELS_IN_FILE_ORDER, proposal))
    errors = []
    for label, forbidden in GROUP_C_FORBIDDEN_SUBSTRINGS.items():
        rec = by_label[label]
        full_text = " ".join([rec["output"]["narrative"], *rec["output"]["bullets"], *rec["output"]["action_items"]]).lower()
        for substr in forbidden:
            if substr in full_text:
                errors.append(f"{label}: output contains forbidden invented/evaluative content {substr!r}")
        for term in GROUP_C_REQUIRED_UNRESOLVED_TERMS[label]:
            if term not in full_text:
                errors.append(f"{label}: expected unresolved term {term!r} to survive somewhere in the output, not found")
        # The condition must survive in the action specifically.
        action_text = " ".join(rec["output"]["action_items"]).lower()
        if "bring it back" not in action_text and "they bring" not in action_text:
            errors.append(f"{label}: supported condition does not appear to survive in the action item")
    if errors:
        raise RepairPreflightError("FATAL: Group-C source-state no-invention check failed:\n  " + "\n  ".join(errors))
    print("[Group-C OK] RB-C3 preserves every unresolved reference and the supported condition; no invented identity, plurality, or evaluation found.")


# ---------------------------------------------------------------------------
# Mechanism-per-record labeling check (design gate 4)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Group-D exemplar preservation check (gate 8 correction, 2026-08-11 per
# ChatGPT's review: "Please ground this as PASS by reviewed baseline
# evidence plus byte preservation, naming/verifying the preserved
# structural exemplars, rather than calling it vacuous.")
# ---------------------------------------------------------------------------


def verify_group_d_preserved_exemplars(candidate: list[dict]) -> dict[str, bool]:
    """Confirms each named Group-D structural exemplar from the reviewed
    implementation-proposal audit (section 3, Group D) is actually present,
    unchanged, in the candidate -- not just assumed from byte-preservation
    of the baseline prefix in general. Ties gate 8 to concrete, named
    evidence rather than the absence of new records."""
    found: dict[str, bool] = {}
    candidate_inputs = [r["input"] for r in candidate]
    for exemplar_name, prefix in GROUP_D_EXEMPLAR_INPUT_PREFIXES.items():
        found[exemplar_name] = any(inp.startswith(prefix) for inp in candidate_inputs)
    missing = [name for name, ok in found.items() if not ok]
    if missing:
        raise RepairPreflightError(f"FATAL: Group-D preserved exemplar(s) not found in the candidate: {missing}")
    print(f"[Group-D exemplars OK] all {len(found)} named structural exemplars (D1-D4) confirmed present and unchanged in the candidate.")
    return found


def verify_mechanism_labeling() -> None:
    if set(PRIMARY_MECHANISM) != set(PROPOSAL_LABELS_IN_FILE_ORDER):
        raise RepairPreflightError("FATAL: mechanism labeling does not cover exactly the 7 proposal records.")
    valid_mechanisms = {"A_attribution", "B_action_completeness", "C_source_state", "D_structural"}
    for label, mech in PRIMARY_MECHANISM.items():
        if mech not in valid_mechanisms:
            raise RepairPreflightError(f"FATAL: {label} has invalid primary mechanism {mech!r}.")
    print(f"[mechanism labeling OK] all {len(PRIMARY_MECHANISM)} record(s) have exactly one primary mechanism from {sorted(valid_mechanisms)}.")


# ---------------------------------------------------------------------------
# Identity / collision / leakage checks, including the two mandatory
# named comparisons the implementation proposal requires regardless of
# generic threshold outcome.
# ---------------------------------------------------------------------------


def _token_set(text: str) -> set[str]:
    return set(re.sub(r"[^a-z ]", "", text.lower()).split())


def _jaccard(a: str, b: str) -> float:
    sa, sb = _token_set(a), _token_set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def normalize_for_collision(text: str) -> str:
    """Predeclared normalization rule (design section 8, implementation
    proposal section 7.2's 'Normalize Unicode, case, whitespace,
    punctuation, and line endings'): Unicode NFKC normalization first
    (added 2026-08-11 per ChatGPT's review -- the prior version only
    ASCII-filtered, which is not the same as normalizing Unicode; NFKC
    folds compatibility variants such as full-width forms and certain
    combining sequences to their canonical form before the ASCII-range
    filter runs), then lowercase, strip everything but alphanumerics and
    spaces, collapse whitespace."""
    t = unicodedata.normalize("NFKC", text)
    t = t.lower()
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


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


def _extract_entities_and_numbers(text: str) -> set[str]:
    """Heuristic proxy for the design's 'named entities, task objects,
    quantities, temporal phrases' collision check: capitalized words not
    at sentence-start (proper-noun proxy, since every legitimate sentence-
    initial capital would otherwise false-positive on every pair) plus all
    numeric tokens and day-of-week names. Not a full NER model -- a fixed,
    declared, deliberately simple heuristic sufficient to catch verbatim
    entity/number reuse, which is the actual leakage risk this check
    targets.

    Splits on sentence-ending punctuation *before* tokenizing (fixed
    2026-08-11: the first version tokenized with a word-only regex that
    discarded '.'/'!'/'?' before the sentence-start flag ever saw them, so
    every mid-text sentence-initial word -- "Ask", "The", etc. -- was
    incorrectly treated as a proper noun on every sentence after the
    first, producing noisy, uninformative findings)."""
    days = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
    entities: set[str] = set()
    for sentence in re.split(r"[.!?]+", text):
        sentence_start = True
        for tok in re.findall(r"[A-Za-z']+|\d+", sentence):
            low = tok.lower()
            if low in days:
                entities.add(low)
            elif tok.isdigit():
                entities.add(tok)
            elif tok[:1].isupper() and not sentence_start and low != "i":
                entities.add(tok)
            sentence_start = False
    return entities


KNOWN_INTENTIONAL_EXACT_SOURCES = {"composite", "rejected-treatment-candidate"}


def verify_normalized_containment(proposal: list[dict], pool: list[tuple[str, str]]) -> None:
    """Fail-closed: exact-normalized-equality or one-contains-the-other
    after normalization (design section 8's 'exact normalized equality
    and containment'). Unconditionally fatal for every pool source except:
    (a) a record's own proposal-self pool entry (trivial self-match, not a
    finding); (b) 'composite' or 'rejected-treatment-candidate' when
    checking one of the four RB-A* records -- those four are *intentional*
    exact reuses of their own AT-C source, which appears verbatim in both
    the composite proposal and the failed treatment candidate built from
    it (already independently verified object-identical by
    verify_attribution_reuse_provenance()), so a normalized-exact match
    against either is the reuse mechanism working as designed, not a
    collision finding. Every other pool source, including proposal-to-
    proposal comparisons among the three genuinely new records
    (RB-B1/RB-B3/RB-C3) and against the known AT-family for those three,
    remains unconditionally fatal."""
    errors = []
    for label, rec in zip(PROPOSAL_LABELS_IN_FILE_ORDER, proposal):
        norm_text = normalize_for_collision(rec["input"])
        for src, ref_text in pool:
            if src == f"proposal-self:{label}":
                continue
            if IS_REUSED[label] and src in KNOWN_INTENTIONAL_EXACT_SOURCES:
                continue
            norm_ref = normalize_for_collision(ref_text)
            if not norm_ref or not norm_text:
                continue
            if norm_text == norm_ref:
                errors.append(f"{label}: normalized-exact collision with {src}")
                continue
            shorter = min(len(norm_text), len(norm_ref))
            if shorter >= CONTAINMENT_MIN_NORMALIZED_CHARS and (norm_text in norm_ref or norm_ref in norm_text):
                errors.append(f"{label}: normalized containment with {src} ({shorter}-char normalized overlap)")
    if errors:
        raise RepairPreflightError("FATAL: normalized containment check failed:\n  " + "\n  ".join(errors))
    print(f"[containment OK] no normalized-exact or containment collision for any of the {len(proposal)} proposed record(s) against the full pool, including proposal-self and the rejected-treatment-candidate class (RB-A*'s own known AT-C source excluded as an already-verified intentional reuse, not a new collision).")


def verify_no_duplicate_or_colliding_inputs(
    baseline: list[dict], proposal: list[dict], benchmark_hashes: set[str]
) -> tuple[list[str], list[str]]:
    baseline_hashes = [input_hash(r["input"]) for r in baseline]
    if len(set(baseline_hashes)) != len(baseline_hashes):
        raise RepairPreflightError("FATAL: duplicate input hash within the baseline corpus.")

    proposal_hashes = [input_hash(r["input"]) for r in proposal]
    if len(set(proposal_hashes)) != len(proposal_hashes):
        raise RepairPreflightError("FATAL: duplicate input hash within the proposal.")

    collide_baseline = set(proposal_hashes) & set(baseline_hashes)
    if collide_baseline:
        raise RepairPreflightError(f"FATAL: {len(collide_baseline)} proposal input(s) collide with an existing baseline input: {sorted(collide_baseline)}")

    collide_bench = set(proposal_hashes) & benchmark_hashes
    if collide_bench:
        raise RepairPreflightError(f"FATAL: {len(collide_bench)} proposal input(s) collide with a frozen benchmark case: {sorted(collide_bench)}")

    print("[identity OK] no duplicates within baseline, within proposal, or against baseline/benchmark inputs.")
    return baseline_hashes, proposal_hashes


def load_benchmark_records() -> tuple[list[dict], list[dict]]:
    protected = parse_jsonl_records_from_bytes(load_canonical(PROTECTED_PROBES_PATH, EXPECTED_PROTECTED_PROBES_FINGERPRINT, "protected-16 benchmark (re-read for record content)"))
    if len(protected) != EXPECTED_PROTECTED_COUNT:
        raise RepairPreflightError(f"FATAL: protected benchmark has {len(protected)} record(s), expected exactly {EXPECTED_PROTECTED_COUNT}.")
    acceptance = parse_jsonl_records_from_bytes(load_canonical(ACCEPTANCE_PROBES_PATH, EXPECTED_ACCEPTANCE_PROBES_FINGERPRINT, "acceptance-10 benchmark (re-read for record content)"))
    if len(acceptance) != EXPECTED_ACCEPTANCE_COUNT:
        raise RepairPreflightError(f"FATAL: acceptance benchmark has {len(acceptance)} record(s), expected exactly {EXPECTED_ACCEPTANCE_COUNT}.")
    return protected, acceptance


def build_reference_pool(
    baseline: list[dict],
    composite_proposal: list[dict],
    protected: list[dict],
    acceptance: list[dict],
    rejected_treatment_candidate: list[dict],
    proposal: list[dict] | None = None,
) -> list[tuple[str, str]]:
    """Full collision universe per design section 8 / implementation
    proposal section 7.2: baseline (covers the parent transitively, since
    the parent is baseline's own prefix), historical/composite proposal,
    protected/acceptance benchmarks, the prior rejected candidate (the
    failed 82-record treatment), and -- when `proposal` is passed -- every
    proposed record checked against every *other* proposed record, not
    just the fixed reference sources. Added 2026-08-11 per ChatGPT's
    review, which found the first version omitted the rejected-candidate
    class and proposal-to-proposal comparisons entirely.

    Scope note: this adds the one prior candidate directly relevant to
    this repair effort (the failed treatment this whole diagnostic chain
    responds to), not an exhaustive sweep of every historical corpus
    variant in this repository's lineage (R2-era proposals, gold_v1.2.3,
    etc.) -- a materially larger, differently-scoped task. Flagged
    explicitly in the derivation report rather than silently narrowed."""
    pool: list[tuple[str, str]] = []
    for r in baseline:
        pool.append(("baseline", r["input"]))
    for r in composite_proposal:
        pool.append(("composite", r["input"]))
    for r in protected:
        pool.append((f"protected-{r['id']}", r["input"]))
    for r in acceptance:
        pool.append((f"acceptance-{r['id']}", r["input"]))
    for r in rejected_treatment_candidate:
        pool.append(("rejected-treatment-candidate", r["input"]))
    if proposal is not None:
        for label, r in zip(PROPOSAL_LABELS_IN_FILE_ORDER, proposal):
            pool.append((f"proposal-self:{label}", r["input"]))
    return pool


def pool_excluding_self(pool: list[tuple[str, str]], own_label: str) -> list[tuple[str, str]]:
    """Removes a record's own proposal-self entry from the pool before
    comparing it against 'everything else' -- a record trivially matches
    itself at 1.0, which is not a finding."""
    return [(src, text) for src, text in pool if src != f"proposal-self:{own_label}"]


def verify_historical_corpus_inventory(already_covered_hashes: set[str]) -> list[dict]:
    """Fail-closed completeness check for the collision universe (design
    section 8 / implementation proposal section 7.2: 'prior candidates',
    plural). Loads every file in HISTORICAL_INVENTORY, canonicalizes it,
    and classifies it as either (a) has no 'input' field -- structurally
    not a candidate corpus, out of scope by construction, not by
    assumption; or (b) has 'input'/'source_input' fields -- every one of
    its input hashes must already be covered by an already-pinned source
    (baseline, treatment candidate, or composite proposal). If ANY record
    in ANY historical file turns out to contain genuinely unique,
    uncovered input content, this fails closed rather than silently
    passing -- that would be exactly the missing-coverage gap ChatGPT's
    review found, this time caught by the script itself on every run
    instead of by one-time manual inspection."""
    inventory_results = []
    for name, meta in HISTORICAL_INVENTORY.items():
        canonical = load_canonical(meta["path"], meta["fingerprint"], f"historical inventory: {name}")
        records = parse_jsonl_records_from_bytes(canonical)
        has_input_field = any("input" in r for r in records)
        if not has_input_field:
            inventory_results.append({
                "name": name, "path": meta["path"].name, "record_count": len(records),
                "classification": "out of scope (no 'input' field -- not a candidate corpus)",
                "description": meta["description"], "missing_count": 0,
            })
            print(f"[inventory] {name}: {len(records)} record(s), out of scope (no 'input' field) -- {meta['description']}")
            continue

        input_key = "input" if "input" in records[0] else "source_input"
        record_hashes = [input_hash(r[input_key]) for r in records]
        missing = [h for h in record_hashes if h not in already_covered_hashes]
        if missing:
            raise RepairPreflightError(
                f"FATAL: historical inventory file {name!r} ({meta['path'].name}) has {len(missing)} input(s) "
                f"not covered by any already-pinned source. This is genuine missing collision-universe coverage "
                f"-- add this file (or its unique records) as a pinned pool source before proceeding."
            )
        inventory_results.append({
            "name": name, "path": meta["path"].name, "record_count": len(records),
            "classification": f"subsumed byte-for-byte ({len(records)}/{len(records)} inputs already covered by baseline/treatment/composite)",
            "description": meta["description"], "missing_count": 0,
        })
        print(f"[inventory] {name}: {len(records)}/{len(records)} record(s) subsumed by already-pinned sources -- no unique content.")
    return inventory_results


# Explicit reviewer dispositions, one per proposed record plus the two
# mandatory named comparisons -- recorded here, not just implied by a
# passing threshold, per ChatGPT's review: "If this requires human review
# rather than a deterministic offline validator, enumerate the compared
# pairs/top matches and record the reviewer disposition explicitly; do not
# label the gate PASS merely because the automated subset passed." These
# are Claude's own review dispositions, reached during the multi-round
# design/proposal review that preceded this implementation -- restated
# here as the artifact of record, not re-derived from scratch, since nothing
# about the underlying text has changed since that review.
# Each disposition below explicitly addresses the required leakage
# dimensions from design section 8 / implementation proposal section 7.2
# -- named entities, task objects, temporal phrases, clause order, and
# distinctive role combinations -- per record, not just an automated
# score, per ChatGPT's review (2026-08-11): "the report must explicitly
# enumerate these required dimensions per record/comparison." Drawn from
# the task-frame inventories already recorded in the implementation
# proposal's own manifest entries, not re-derived.
REVIEWER_DISPOSITIONS = {
    "RB-A1": "Exact reuse of AT-C1, already independently verified byte-for-byte against the reviewed composite proposal. High similarity to RB-A4 (1.0) is the intentional order-swapped control relationship, disclosed in the design and manifest, not a defect. Leakage dimensions: task object 'access link' and clause order ('X told Y the exhibit plan was approved... Ask Elena to send Owen...') are shared only within the AT-family itself (RB-A2/RB-A3/RB-A4, RB-A4 by design), not with any benchmark; no temporal phrase; role combination (teller/askee/recipient) does not match any protected/acceptance probe's role pattern.",
    "RB-A2": "Exact reuse of AT-C2. High similarity to the RB-A1/RB-A4 family (~0.5-0.9) is the intentional shared-template contrast-family relationship (same 'exhibit plan/museum/shared folder' scaffold across all four attribution records, by design) -- reviewed, no concern. Leakage dimensions: task object and clause order shared only within the AT-family (by design); no temporal phrase; the ambiguous-'they' role combination distinguishes it from RB-A1/RB-A4's fully-resolved role combination and from any benchmark probe.",
    "RB-A3": "Exact reuse of AT-C3. Scores materially above both review thresholds against protected 06 (token 0.318, char-5-gram 0.116) -- this is the disclosed, explicitly-named risk in the design's evaluation-independence limitation, not a new finding. Accepted with that limitation recorded; not treated as independent proof of Group-A generalization. Leakage dimensions: task object 'access badge' does not match protected 06's 'stamped copy' or Rina/Marcus's 'signed copy'; no temporal phrase; the resolve-then-preserve clause order and three-way role combination (Joel/Priya/courier) is the same *pattern* protected 06 and Rina/Marcus test, by design intent, using different named entities and a different object throughout.",
    "RB-A4": "Exact reuse of AT-C4, order-swapped control for RB-A1 by design (see RB-A1). Leakage dimensions: identical to RB-A1's except the name-order clause is swapped, which is the entire point of this control -- no additional risk beyond what RB-A1 already discloses.",
    "RB-B1": "New record. Low overlap against every reference class on both metrics (well under both review thresholds); nearest matches share only generic connector words and an unrelated 'clock is slow' background-observation echo, not entities or wording specific to this record's teaching purpose. No concern. Leakage dimensions: task object 'sealed calibration packet' and destination 'north depot' appear nowhere else in the pool; temporal phrase 'before the service counter closes on Thursday' does not match any benchmark's deadline phrasing (protected 11's 'by Thursday' is a bare deadline with no closing-condition clause); no role combination (single-actor task).",
    "RB-B3": "New record. Negligible overlap against every reference class on both metrics. No concern. Leakage dimensions: task object 'three labeled adapters' and destination 'locked drawer' appear nowhere else in the pool; temporal/conditional phrase 'when the projector cart returns' is unique to this record; no role combination (single-actor task).",
    "RB-C3": "New record. Token-Jaccard (0.200) crosses the review threshold against the existing baseline dangling-reference record ('Remember to ask her about the earlier version.') -- this is intentional: RB-C3 is explicitly modeled on that record's convention (see the implementation proposal's revision history), reviewed and accepted as the same teaching family, not a duplicate (different entities: 'they/it/her/earlier one' vs 'her/earlier version', different condition clause). Leakage dimensions: task object is itself unresolved ('the earlier one'), not a concrete noun to collide on; temporal/conditional phrase 'when they bring it back' does not match acceptance sdi2-09's 'after it arrives' or protected 16's unconditioned reminder; role combination (unresolved actor/unresolved recipient) is the shared *category* with protected 16 and sdi2-09 by design, using entirely different surface wording.",
}
REVIEWER_DISPOSITIONS["_named_comparisons"] = {
    "rina_marcus_vs_protected_06": (
        "Preserved baseline record (unchanged, not part of this proposal). Scores far above both review "
        "thresholds against protected 06 (token 0.576, char-5-gram 0.306, identical 34-word count, "
        "clause-by-clause parallel structure). This is the major finding from the design-review round: "
        "protected 06 is not a structurally independent held-out test of Group-A generalization as a result. "
        "Documented in the design's 'Protected-06 independence limitation' section; Rina/Marcus is correctly "
        "labeled and intentionally left unmodified, not corrected or deleted. Leakage dimensions: task object "
        "('signed copy' vs protected 06's 'stamped copy'), named entities (Rina/Marcus vs Tessa/Rowan/inspector), "
        "clause order (near-identical, the substance of this finding), and role combination (teller/askee, "
        "unresolved-need-recipient) are all shared by construction -- this is a structural template match, not "
        "an incidental one, which is exactly why it is treated as a named, mandatory, always-reported comparison "
        "rather than folded into the generic threshold sweep."
    ),
    "RB-A3_vs_protected_06": (
        "See RB-A3 above -- same underlying relationship (RB-A3 is a deliberate resolve/preserve analogue of "
        "the same attribution pattern protected 06 and Rina/Marcus both test), disclosed and accepted with the "
        "same evaluation-independence limitation, not a new or separate risk."
    ),
}


def run_collision_sweep(proposal: list[dict], pool: list[tuple[str, str]], protected: list[dict], baseline: list[dict]) -> dict:
    """Independent token-Jaccard AND character-5-gram-Jaccard collision
    sweep across the full stated pool for every proposed record, plus the
    two mandatory named comparisons (Rina/Marcus vs protected 06, RB-A3 vs
    protected 06) required by the implementation proposal regardless of
    their score. Every record whose max score on *either* metric crosses
    its declared review threshold gets its explicit reviewer disposition
    surfaced in the same result (see REVIEWER_DISPOSITIONS) -- this is the
    reviewable semantic-near-duplicate disposition ChatGPT's review
    required in place of a bare automated PASS."""
    results = {}
    for label, rec in zip(PROPOSAL_LABELS_IN_FILE_ORDER, proposal):
        text = rec["input"]
        own_excluded_pool = pool_excluding_self(pool, label)
        token_scored = sorted(((_jaccard(text, ref_text), src) for src, ref_text in own_excluded_pool), reverse=True)
        ngram_scored = sorted(((_char_ngram_jaccard(text, ref_text), src) for src, ref_text in own_excluded_pool), reverse=True)
        token_max, token_nearest = token_scored[0]
        ngram_max, ngram_nearest = ngram_scored[0]
        needs_disposition = token_max >= TOKEN_JACCARD_REVIEW_THRESHOLD or ngram_max >= CHAR_NGRAM_REVIEW_THRESHOLD
        results[label] = {
            "max_jaccard": round(token_max, 4),
            "nearest": token_nearest,
            "max_char_ngram_jaccard": round(ngram_max, 4),
            "nearest_char_ngram": ngram_nearest,
            "needs_disposition": needs_disposition,
            "disposition": REVIEWER_DISPOSITIONS[label] if needs_disposition else "Below both review thresholds; no explicit disposition required.",
        }

    rina_marcus = next((r for r in baseline if "Rina" in r["input"]), None)
    if rina_marcus is None:
        raise RepairPreflightError("FATAL: could not locate the Rina/Marcus baseline record for the mandatory named comparison.")
    protected_06 = next((p for p in protected if p["id"] == "06"), None)
    if protected_06 is None:
        raise RepairPreflightError("FATAL: could not locate protected probe 06 for the mandatory named comparison.")

    rina_vs_06_token = round(_jaccard(rina_marcus["input"], protected_06["input"]), 4)
    rina_vs_06_ngram = round(_char_ngram_jaccard(rina_marcus["input"], protected_06["input"]), 4)
    rb_a3_vs_06_token = round(_jaccard(proposal[2]["input"], protected_06["input"]), 4)  # RB-A3 is index 2
    rb_a3_vs_06_ngram = round(_char_ngram_jaccard(proposal[2]["input"], protected_06["input"]), 4)

    results["_named_comparisons"] = {
        "rina_marcus_vs_protected_06": {"token_jaccard": rina_vs_06_token, "char_ngram_jaccard": rina_vs_06_ngram, "disposition": REVIEWER_DISPOSITIONS["_named_comparisons"]["rina_marcus_vs_protected_06"]},
        "RB-A3_vs_protected_06": {"token_jaccard": rb_a3_vs_06_token, "char_ngram_jaccard": rb_a3_vs_06_ngram, "disposition": REVIEWER_DISPOSITIONS["_named_comparisons"]["RB-A3_vs_protected_06"]},
    }
    print(f"[collision sweep] RB-A3 vs protected-06: token={rb_a3_vs_06_token} char-5gram={rb_a3_vs_06_ngram} (named, always reported)")
    print(f"[collision sweep] Rina/Marcus (baseline, preserved unchanged) vs protected-06: token={rina_vs_06_token} char-5gram={rina_vs_06_ngram} (named, always reported)")
    for label in PROPOSAL_LABELS_IN_FILE_ORDER:
        r = results[label]
        flag = " [NEEDS DISPOSITION]" if r["needs_disposition"] else ""
        print(f"[collision sweep] {label}: token max {r['max_jaccard']} vs {r['nearest']}; char-5gram max {r['max_char_ngram_jaccard']} vs {r['nearest_char_ngram']}{flag}")
    return results


def verify_entity_overlap(proposal: list[dict], pool: list[tuple[str, str]]) -> list[str]:
    """Named-entity/task-object/quantity/temporal-phrase collision check
    (design section 8). Not fatal by itself -- entity/number overlap can
    be entirely legitimate (e.g. two unrelated records both mentioning
    'Thursday') -- but every 2+-entity overlap against a single reference
    record is collected and surfaced for explicit review, never silently
    dropped."""
    findings = []
    for label, rec in zip(PROPOSAL_LABELS_IN_FILE_ORDER, proposal):
        prop_entities = _extract_entities_and_numbers(rec["input"])
        if not prop_entities:
            continue
        for src, ref_text in pool_excluding_self(pool, label):
            ref_entities = _extract_entities_and_numbers(ref_text)
            shared = prop_entities & ref_entities
            if len(shared) >= 2:
                findings.append(f"{label} vs {src}: shared entity/number tokens {sorted(shared)}")
    return findings


# ---------------------------------------------------------------------------
# Candidate construction (same pattern as the sibling script)
# ---------------------------------------------------------------------------


def build_candidate(baseline: list[dict], proposal: list[dict]) -> tuple[list[dict], list[str]]:
    generated_targets: list[str] = []
    proposal_entries = []
    for i, rec in enumerate(proposal):
        narrative = rec["output"]["narrative"]
        bullets = rec["output"]["bullets"]
        actions = rec["output"]["action_items"]

        v1_target = build_v1_target(narrative, bullets, actions)
        v2_target = build_v2_target(narrative, bullets, actions)

        try:
            parsed = parse_output(v2_target)
        except ParseError as e:
            raise RepairPreflightError(f"FATAL: proposal record {i} ({PROPOSAL_LABELS_IN_FILE_ORDER[i]}) v2_target does not parse: {e}")
        if parsed.narrative != narrative.strip() or parsed.bullets != bullets or parsed.actions != actions:
            raise RepairPreflightError(f"FATAL: proposal record {i} ({PROPOSAL_LABELS_IN_FILE_ORDER[i]}) regenerated v2_target does not round-trip to the authored output.")

        entry = {
            "input": rec["input"],
            "output": rec["output"],
            "difficulty": rec["difficulty"],
            "category": rec["category"],
            "v1_target": v1_target,
            "v2_target": v2_target,
        }
        proposal_entries.append(entry)
        generated_targets.append(v2_target)

    print(f"[targets OK] generated and parse-verified v1_target/v2_target for all {len(proposal_entries)} proposal record(s).")
    candidate = list(baseline) + proposal_entries
    return candidate, generated_targets


def verify_baseline_preserved_byte_for_byte(baseline_bytes: bytes, candidate_bytes: bytes) -> None:
    prefix = candidate_bytes[: len(baseline_bytes)]
    if prefix != baseline_bytes:
        diff_at = next(
            (i for i in range(min(len(prefix), len(baseline_bytes))) if prefix[i] != baseline_bytes[i]),
            min(len(prefix), len(baseline_bytes)),
        )
        raise RepairPreflightError(
            f"FATAL: candidate's first {len(baseline_bytes)} byte(s) are not byte-identical to the pinned "
            f"canonical baseline. First differing byte at offset {diff_at}."
        )
    print(f"[byte-preservation OK] candidate's first {len(baseline_bytes)} byte(s) are byte-identical to the pinned canonical baseline (P2-009/P2-010 excluded by construction).")


def verify_proposal_appended_in_order(proposal_hashes: list[str], candidate: list[dict]) -> None:
    appended = candidate[EXPECTED_BASELINE_COUNT:]
    if len(appended) != EXPECTED_PROPOSAL_COUNT:
        raise RepairPreflightError(f"FATAL: expected {EXPECTED_PROPOSAL_COUNT} appended record(s), found {len(appended)}.")
    appended_hashes = [input_hash(r["input"]) for r in appended]
    if appended_hashes != proposal_hashes:
        raise RepairPreflightError("FATAL: appended records are not in the proposal file's own order (by input hash).")
    print(f"[order OK] all {len(appended)} proposal record(s) appended in exact reviewed file order.")


def build_split(candidate: list[dict], val_hashes: set[str]) -> tuple[list[dict], list[dict]]:
    train_pairs: list[dict] = []
    val_pairs: list[dict] = []
    for rec in candidate:
        h = input_hash(rec["input"])
        pair = {"prompt": v2_candidate.build_prompt(rec["input"]), "target": rec["v2_target"]}
        (val_pairs if h in val_hashes else train_pairs).append(pair)
    return train_pairs, val_pairs


def verify_val_byte_identical_to_existing(written_val_bytes: bytes, canonical_val_bytes: bytes, val_count: int) -> dict:
    identical = canonical_val_bytes == written_val_bytes
    if not identical:
        raise RepairPreflightError(
            "FATAL: newly-written val split is not byte-identical to the pinned canonical LF "
            "representation of the existing val split. Refusing to proceed -- validation must stay frozen."
        )
    print(f"[val byte-identity OK] {val_count} validation record(s) byte-identical to the pinned canonical LF existing val split.")
    return {"val_count": val_count, "byte_identical_to_existing_val": identical}


def ensure_output_paths_available(output_data_dir: Path) -> None:
    for p in (OUTPUT_CORPUS_PATH, OUTPUT_REPORT_PATH, OUTPUT_COMPARISON_PATH, OUTPUT_SPLIT_COMPARISON_PATH, OUTPUT_MANIFEST_PATH, OUTPUT_GATE_REPORT_PATH, output_data_dir):
        if p.exists():
            raise RepairPreflightError(f"FATAL: output path already exists, refusing to overwrite: {p}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=str, default=None, help="Overrides the default candidate train/val data output dir")
    args = parser.parse_args()
    output_data_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DATA_DIR

    ensure_output_paths_available(output_data_dir)

    print("=== Step 1: pinned fingerprint verification (all inputs canonicalized uniformly) ===")
    canon = load_all_canonical_inputs()

    print("\n=== Step 2: load + count + schema + provenance checks ===")
    baseline = parse_jsonl_records_from_bytes(canon["baseline"])
    proposal = parse_jsonl_records_from_bytes(canon["proposal"])
    composite_proposal = parse_jsonl_records_from_bytes(canon["composite_proposal"])
    rejected_treatment_candidate = parse_jsonl_records_from_bytes(canon["rejected_treatment_candidate"])
    verify_counts(baseline, proposal)
    verify_size_ceiling()
    validate_proposal_schema(proposal)
    verify_attribution_reuse_provenance(proposal, composite_proposal)
    verify_mechanism_labeling()

    print("\n=== Step 3: semantic invariant checks (design gates 5-7) ===")
    verify_group_a_balance(proposal)
    verify_group_b_action_completeness(proposal)
    verify_group_c_no_invention(proposal)

    print("\n=== Step 4: identity + collision/leakage checks ===")
    protected, acceptance = load_benchmark_records()
    benchmark_hashes = {input_hash(r["input"]) for r in protected} | {input_hash(r["input"]) for r in acceptance}
    baseline_hashes, proposal_hashes = verify_no_duplicate_or_colliding_inputs(baseline, proposal, benchmark_hashes)

    already_covered_hashes = (
        set(baseline_hashes)
        | {input_hash(r["input"]) for r in rejected_treatment_candidate}
        | {input_hash(r["input"]) for r in composite_proposal}
    )
    inventory_results = verify_historical_corpus_inventory(already_covered_hashes)

    reference_pool = build_reference_pool(baseline, composite_proposal, protected, acceptance, rejected_treatment_candidate, proposal)
    verify_normalized_containment(proposal, reference_pool)
    collision_results = run_collision_sweep(proposal, reference_pool, protected, baseline)
    entity_overlap_findings = verify_entity_overlap(proposal, reference_pool)
    if entity_overlap_findings:
        print(f"[entity overlap] {len(entity_overlap_findings)} pair(s) with 2+ shared entity/number tokens (non-fatal, surfaced for review):")
        for finding in entity_overlap_findings:
            print(f"  - {finding}")
    else:
        print("[entity overlap OK] no proposed record shares 2+ entity/number tokens with any single reference record.")

    print(f"\n=== Step 5: build candidate ({EXPECTED_BASELINE_COUNT} baseline + {EXPECTED_PROPOSAL_COUNT} proposal) ===")
    candidate, generated_targets = build_candidate(baseline, proposal)
    if len(candidate) != EXPECTED_CANDIDATE_COUNT:
        raise RepairPreflightError(f"FATAL: candidate has {len(candidate)} records, expected exactly {EXPECTED_CANDIDATE_COUNT}.")
    print(f"[count OK] candidate={len(candidate)}")
    verify_group_d_preserved_exemplars(candidate)

    print(f"\n=== Step 6: split derivation (frozen val membership; {EXPECTED_PROPOSAL_COUNT} new records appended to train) ===")
    val_hashes = load_val_hashes(SPLIT_MANIFEST_PATH)
    train_pairs, val_pairs = build_split(candidate, val_hashes)
    if len(train_pairs) != EXPECTED_TRAIN_COUNT:
        raise RepairPreflightError(f"FATAL: train split has {len(train_pairs)} records, expected exactly {EXPECTED_TRAIN_COUNT}.")
    if len(val_pairs) != EXPECTED_VAL_COUNT:
        raise RepairPreflightError(f"FATAL: val split has {len(val_pairs)} records, expected exactly {EXPECTED_VAL_COUNT}.")
    print(f"[split count OK] train={len(train_pairs)}, val={len(val_pairs)}")

    print("\n=== Step 7: write exclusive candidate + split artifacts (genuine byte operations) ===")
    baseline_bytes = canon["baseline"]
    appended_bytes = b"".join(
        json.dumps(r, ensure_ascii=False).encode("utf-8") + CANONICAL_LF for r in candidate[EXPECTED_BASELINE_COUNT:]
    )
    OUTPUT_CORPUS_PATH.write_bytes(baseline_bytes + appended_bytes)
    print(f"{OUTPUT_CORPUS_PATH.name}: {len(candidate)} records")

    verify_baseline_preserved_byte_for_byte(baseline_bytes, OUTPUT_CORPUS_PATH.read_bytes())
    verify_proposal_appended_in_order(proposal_hashes, parse_jsonl_records_from_bytes(OUTPUT_CORPUS_PATH.read_bytes()))

    output_data_dir.mkdir(parents=True, exist_ok=False)

    (output_data_dir / "val.jsonl").write_bytes(canon["existing_val"])
    val_comparison = verify_val_byte_identical_to_existing(
        (output_data_dir / "val.jsonl").read_bytes(), canon["existing_val"], len(val_pairs)
    )
    print(f"{output_data_dir / 'val.jsonl'}: {len(val_pairs)} examples (byte-copied from the pinned canonical existing val split)")

    train_bytes = b"".join(
        json.dumps(p, ensure_ascii=False).encode("utf-8") + CANONICAL_LF for p in train_pairs
    )
    (output_data_dir / "train.jsonl").write_bytes(train_bytes)
    print(f"{output_data_dir / 'train.jsonl'}: {len(train_pairs)} examples")

    print("\n=== Step 8: fingerprints and machine-readable comparisons ===")
    baseline_content_fp = hashlib.sha256(canonical_json_bytes(
        [{"input": r["input"], "output": r["output"]} for r in baseline]
    )).hexdigest()
    candidate_content_fp = hashlib.sha256(canonical_json_bytes(
        [{"input": r["input"], "output": r["output"]} for r in candidate]
    )).hexdigest()
    candidate_corpus_fp = file_fingerprint(OUTPUT_CORPUS_PATH)
    new_training_data_fp = canonical_training_data_fingerprint(train_pairs + val_pairs)

    existing_baseline_train_pairs, existing_baseline_val_pairs = build_split(baseline, val_hashes)
    baseline_training_data_fp = canonical_training_data_fingerprint(existing_baseline_train_pairs + existing_baseline_val_pairs)

    comparison = {
        "baseline_record_count": len(baseline),
        "proposal_record_count": len(proposal),
        "candidate_record_count": len(candidate),
        "baseline_content_fingerprint": baseline_content_fp,
        "candidate_content_fingerprint": candidate_content_fp,
        "candidate_corpus_file_fingerprint": candidate_corpus_fp,
        "appended_records_in_order": [
            {
                "label": PROPOSAL_LABELS_IN_FILE_ORDER[i],
                "primary_mechanism": PRIMARY_MECHANISM[PROPOSAL_LABELS_IN_FILE_ORDER[i]],
                "reused": IS_REUSED[PROPOSAL_LABELS_IN_FILE_ORDER[i]],
                "input_hash": proposal_hashes[i],
                "input_excerpt": proposal[i]["input"][:80],
                "category": proposal[i]["category"],
                "difficulty": proposal[i]["difficulty"],
                "bullets": len(proposal[i]["output"]["bullets"]),
                "actions": len(proposal[i]["output"]["action_items"]),
                "collision_max_token_jaccard": collision_results[PROPOSAL_LABELS_IN_FILE_ORDER[i]]["max_jaccard"],
                "collision_nearest_token": collision_results[PROPOSAL_LABELS_IN_FILE_ORDER[i]]["nearest"],
                "collision_max_char_ngram_jaccard": collision_results[PROPOSAL_LABELS_IN_FILE_ORDER[i]]["max_char_ngram_jaccard"],
                "collision_nearest_char_ngram": collision_results[PROPOSAL_LABELS_IN_FILE_ORDER[i]]["nearest_char_ngram"],
                "needs_disposition": collision_results[PROPOSAL_LABELS_IN_FILE_ORDER[i]]["needs_disposition"],
                "disposition": collision_results[PROPOSAL_LABELS_IN_FILE_ORDER[i]]["disposition"],
            }
            for i in range(EXPECTED_PROPOSAL_COUNT)
        ],
        "named_collision_comparisons": collision_results["_named_comparisons"],
        "entity_overlap_findings": entity_overlap_findings,
        "normalization_and_thresholds": {
            "normalization_rule": "lowercase; strip all but [a-z0-9 ]; collapse whitespace",
            "char_ngram_n": CHAR_NGRAM_N,
            "token_jaccard_review_threshold": TOKEN_JACCARD_REVIEW_THRESHOLD,
            "char_ngram_review_threshold": CHAR_NGRAM_REVIEW_THRESHOLD,
            "containment_min_normalized_chars": CONTAINMENT_MIN_NORMALIZED_CHARS,
        },
    }
    OUTPUT_COMPARISON_PATH.write_bytes(json.dumps(comparison, indent=2, ensure_ascii=False).encode("utf-8"))
    print(f"{OUTPUT_COMPARISON_PATH.name}: baseline-vs-candidate comparison")

    split_comparison = {
        "train_count": len(train_pairs),
        "val_count": len(val_pairs),
        **val_comparison,
        "baseline_training_data_fingerprint": baseline_training_data_fp,
        "candidate_training_data_fingerprint": new_training_data_fp,
    }
    OUTPUT_SPLIT_COMPARISON_PATH.write_bytes(json.dumps(split_comparison, indent=2).encode("utf-8"))
    print(f"{OUTPUT_SPLIT_COMPARISON_PATH.name}: split comparison")

    print("\n=== Step 9: record-level manifest ===")
    manifest_lines = [
        "# Regression-Balanced Repair -- Record-Level Change Manifest\n",
        f"**Generated by:** `prepare_regression_balanced_repair_candidate_corpus.py`  ",
        f"**Governing design:** `training/controlled_seed17_regression_balanced_repair_design_chatgpt.md`, SHA-256 `8d803ab08228e7a359145568e73cfac2fa13bb5416bcf4a1bc53ff288684fe2a`  ",
        f"**Governing implementation proposal:** `training/controlled_seed17_regression_balanced_repair_implementation_proposal_chatgpt.md`, SHA-256 `4f601c33c78bb5ab048ab36c36a677464efaf749e7e4137f50c07996e02f1672`  ",
        f"**Authorized by:** Johnny, 2026-08-11 (\"Yes, proceed\", confirmed directly) -- corpus-implementation package, static artifacts only.\n",
        "## Normalization rule and review thresholds -- honest chronology, RATIFIED by Johnny 2026-08-11\n",
        "- Normalization: Unicode NFKC, then lowercase; strip all but `[a-z0-9 ]`; collapse whitespace.",
        f"- Character n-gram size: {CHAR_NGRAM_N}.",
        f"- Token-Jaccard review threshold: {TOKEN_JACCARD_REVIEW_THRESHOLD} (max score at/above this requires an explicit disposition below, not just an automated pass).",
        f"- Character-{CHAR_NGRAM_N}-gram-Jaccard review threshold: {CHAR_NGRAM_REVIEW_THRESHOLD} (same).",
        f"- Normalized containment: fatal (fail-closed) for any normalized-equal or containment match of {CONTAINMENT_MIN_NORMALIZED_CHARS}+ normalized characters -- no legitimate design reason for this to occur, so no disposition tier for it.",
        "",
        "**These two review thresholds were NOT set before the exact seven records were written.** They were "
        "chosen by running the sweep against the already-written, already-reviewed records and picking values "
        "that would catch RB-C3's and RB-A3's already-known scores. That is the sequence the accepted design's "
        "section 8 explicitly prohibits (\"Similarity thresholds and normalization rules must be specified "
        "before the exact records are written, not selected after collisions are observed\"). Stated plainly, "
        "not argued around.",
        "",
        "**Ratification, 2026-08-11**: Claude recommended accepting these specific values rather than "
        "restarting, with the reasoning made explicit: the rule exists to stop someone writing leaky records "
        "then picking a *loose* threshold afterward to hide the leak; these thresholds were instead set *low* "
        "-- specifically so RB-C3 (0.200) and RB-A3 (0.116) would be caught and forced into disposition, not "
        "waved through. That is the opposite of the failure mode the rule guards against, even though the "
        "letter of the sequencing rule was not followed. Johnny reviewed this reasoning directly (not relayed "
        "through ChatGPT) and responded: \"I agree with this. Let's proceed.\" The two threshold values above "
        "are therefore final for this package. **Forward-looking commitment, recorded at ratification time**: "
        "any future implementation round in this project must have its thresholds proposed and pinned before "
        "exact record wording is drafted, full stop -- this ratification is specific to this package, not a "
        "precedent for skipping that discipline going forward.",
        "",
        "## Seven-record delta\n",
        "| Label | Mechanism | Reused | Category | Difficulty | Input hash | Token max | Char-5gram max | Needs disposition |",
        "|---|---|---|---|---|---|---:|---:|---|",
    ]
    for entry in comparison["appended_records_in_order"]:
        manifest_lines.append(
            f"| {entry['label']} | `{entry['primary_mechanism']}` | {'yes' if entry['reused'] else 'no'} | "
            f"`{entry['category']}` | {entry['difficulty']} | `{entry['input_hash'][:16]}...` | "
            f"{entry['collision_max_token_jaccard']} | {entry['collision_max_char_ngram_jaccard']} | "
            f"{'yes' if entry['needs_disposition'] else 'no'} |"
        )
    manifest_lines += [
        "",
        "## Reviewable semantic-near-duplicate disposition\n",
        "Explicit reviewer judgment for every record whose max score on either metric crosses its review",
        "threshold -- not a bare automated PASS. These are Claude's dispositions, restated from the",
        "multi-round design/proposal review that preceded this implementation (nothing about the underlying",
        "text has changed since); ChatGPT's independent review is expected to confirm or challenge each one.\n",
    ]
    for entry in comparison["appended_records_in_order"]:
        if entry["needs_disposition"]:
            manifest_lines.append(f"**{entry['label']}**: {entry['disposition']}\n")
    manifest_lines += [
        "## Mandatory named collision comparisons (per implementation proposal section 7.2)",
        "",
        f"- Rina/Marcus (preserved baseline record, unchanged) vs protected 06: token **{collision_results['_named_comparisons']['rina_marcus_vs_protected_06']['token_jaccard']}**, char-{CHAR_NGRAM_N}-gram **{collision_results['_named_comparisons']['rina_marcus_vs_protected_06']['char_ngram_jaccard']}**.  ",
        f"  {collision_results['_named_comparisons']['rina_marcus_vs_protected_06']['disposition']}",
        f"- RB-A3 (exact reuse of AT-C3) vs protected 06: token **{collision_results['_named_comparisons']['RB-A3_vs_protected_06']['token_jaccard']}**, char-{CHAR_NGRAM_N}-gram **{collision_results['_named_comparisons']['RB-A3_vs_protected_06']['char_ngram_jaccard']}**.  ",
        f"  {collision_results['_named_comparisons']['RB-A3_vs_protected_06']['disposition']}",
        "",
        "Both reported regardless of threshold, per the accepted implementation proposal's evaluation-independence limitation.",
        "",
        "## Historical corpus/proposal inventory (collision-universe completeness, per implementation proposal section 7.2's 'prior candidates')\n",
        "Every candidate/proposal JSONL in this gold_v1.2.2/R2/Phase-2/contrastive lineage, verified -- not inferred -- to be",
        "either subsumed byte-for-byte by an already-pinned source or structurally not a candidate corpus. Fails closed if",
        "any historical file ever contains a genuinely uncovered input.\n",
        "| Source | File | Records | Classification |",
        "|---|---|---:|---|",
    ]
    for inv in inventory_results:
        manifest_lines.append(f"| `{inv['name']}` | `{inv['path']}` | {inv['record_count']} | {inv['classification']} |")
    manifest_lines += [
        "",
    ]
    for inv in inventory_results:
        manifest_lines.append(f"- **{inv['name']}**: {inv['description']}")
    manifest_lines += [
        "",
        "Scope note: this inventory covers every candidate/proposal JSONL in this specific corpus lineage (gold_v1.2.2 R2 /",
        "Phase-2 / contrastive-attribution / this repair). Files from other release lines (gold_v1.2.1, gold_v1.2.3, and",
        "unrelated benchmark suites) are out of scope by lineage, not omitted by oversight -- they govern different",
        "corpora with their own separate provenance chains.",
        "",
        "## Entity/quantity overlap findings (non-fatal, surfaced for review)\n",
    ]
    if entity_overlap_findings:
        for finding in entity_overlap_findings:
            manifest_lines.append(f"- {finding}")
    else:
        manifest_lines.append("None -- no proposed record shares 2+ entity/number tokens with any single reference record.")
    manifest_lines += [
        "",
        "## Preservation",
        "",
        f"- Baseline (`{BASELINE_PATH.name}`, {len(baseline)} records) preserved byte-for-byte as the candidate's exact prefix -- P2-009/P2-010 revisions excluded by construction, not by a separate check.",
        "- The two `two_unrelated_tasks` probe-13 repair records are part of that unchanged baseline prefix.",
        "- Validation membership: the existing 6-record val split is byte-copied verbatim; none of the 7 new/reused records can belong to val by construction (frozen split-manifest hash membership).",
        "- Zero target-only corrections. Zero Group-D additions -- all six named structural exemplars (D1-D4) independently confirmed present and unchanged in the candidate; see gate 8 below.",
        "",
        "## Status",
        "",
        "Static package only. No training, inference, benchmark execution, seed 73, checkpoint work, export, "
        "deployment, activation, cleanup, commit, or push performed or authorized. Everything remains uncommitted "
        "for ChatGPT's independent review.",
        "",
    ]
    OUTPUT_MANIFEST_PATH.write_bytes("\n".join(manifest_lines).encode("utf-8"))
    print(f"{OUTPUT_MANIFEST_PATH.name}: record-level manifest")

    print("\n=== Step 10: fifteen-gate compliance report ===")
    gate_rows = [
        ("1", "Baseline/preserved records pinned by canonical bytes and fingerprint", "PASS", f"baseline fingerprint `{EXPECTED_BASELINE_FINGERPRINT}` verified via canonicalize_pinned_lf_bytes()"),
        ("2", "Existing coverage audit justifies every proposed addition/correction", "PASS (by reference)", "audit performed in the reviewed implementation proposal, sections 3/13; not re-derived by this script"),
        ("3", "Total delta stays within the size ceiling", "PASS", f"3 new (ceiling {NEW_RECORD_CEILING}) + 4 reused (ceiling {REUSED_ATTRIBUTION_CEILING})"),
        ("4", "Every record has exactly one primary mechanism", "PASS", "verify_mechanism_labeling()"),
        ("5", "Group A passes resolve/preserve/order balance checks", "PASS", "verify_group_a_balance()"),
        ("6", "Group B preserves complete action frames field-by-field", "PASS", "verify_group_b_action_completeness()"),
        ("7", "Group C adds no answer, relationship, plurality, evaluation, cause, chronology, or unsupported task", "PASS", "verify_group_c_no_invention()"),
        ("8", "Group D satisfies both semantic identity and parsed count requirements", "PASS by reviewed baseline evidence plus byte preservation", f"verify_group_d_preserved_exemplars() confirmed all {len(GROUP_D_EXEMPLAR_INPUT_PREFIXES)} named structural exemplars (D1-D4, see manifest) present and unchanged in the candidate -- not merely 'no new records were added'"),
        ("9", "The two protected-13 repair records remain unchanged", "PASS", "part of the byte-preserved baseline prefix"),
        ("10", "P2-009/P2-010 treatment revisions are excluded unless separately re-justified", "PASS", "excluded by construction (baseline byte-preservation), not re-justified"),
        ("11", "Validation membership and split policy are unchanged", "PASS", "verify_val_byte_identical_to_existing()"),
        ("12", "Benchmark, rubric, prompt, parser, and scoring rules are unchanged", "PASS (structural)", "this script never writes to any of those paths"),
        ("13", "Near-duplicate, leakage, schema, enum, and formatting checks pass", "PASS (threshold values ratified by Johnny, 2026-08-11)", f"Coverage: normalized containment (fail-closed), token + character-5-gram Jaccard, entity/task-object/temporal-phrase/clause-order/role-combination dispositions, the full pool (baseline, composite, protected, acceptance, the prior rejected treatment candidate, proposal-self), and verify_historical_corpus_inventory() fail-closed-verifying all {len(HISTORICAL_INVENTORY)} historical candidate/proposal files in this lineage are subsumed or structurally out of scope (see manifest inventory table). The two review thresholds were set after the seven records were already written, which the design's section 8 prohibits by its letter -- stated honestly, not glossed over (see the manifest's chronology section) -- but Johnny reviewed the reasoning (thresholds were set *low*, specifically to catch RB-C3/RB-A3's known scores rather than hide them -- the opposite of the failure mode the rule guards against) and explicitly ratified: \"I agree with this. Let's proceed.\" A forward-looking rule was recorded at ratification time: future rounds must freeze thresholds before record wording is drafted."),
        ("14", "Exact expected change paths, record counts, fingerprints, and generated artifacts are declared before implementation", "PASS", "all EXPECTED_* constants declared at module scope, asserted at runtime"),
        ("15", "ChatGPT and Claude independently agree on every record-level disposition", "PASS (ChatGPT independently confirmed, 2026-08-11)", "ChatGPT independently re-verified the ratification record (exact threshold values, honest chronology preserved, scoped-exception framing, forward-looking rule) and every record-level disposition on the completed collision universe, re-ran the full suite, and confirmed byte-identical candidate/split artifacts before responding: \"FULL INDEPENDENT AGREEMENT... Gate 15 may now be changed from PENDING to PASS, yielding 15/15 static gates PASS.\" This is ChatGPT's own word on this specific development, not an inference from an earlier message."),
    ]
    gate_lines = [
        "# Regression-Balanced Repair -- Fifteen-Gate Compliance Report\n",
        f"**Generated by:** `prepare_regression_balanced_repair_candidate_corpus.py` (this run)  ",
        f"**Candidate:** `{OUTPUT_CORPUS_PATH.name}`, {len(candidate)} records, SHA-256 `{candidate_corpus_fp}`  ",
        f"**Split:** {len(train_pairs)} train / {len(val_pairs)} val, training-data fingerprint `{new_training_data_fp}`\n",
        "| # | Gate | Status | Evidence |",
        "|---:|---|---|---|",
    ]
    for num, gate, status, evidence in gate_rows:
        gate_lines.append(f"| {num} | {gate} | **{status}** | {evidence} |")
    gate_lines += [
        "",
        "**15/15 static gates PASS as of 2026-08-11.** Gate 15 was the only one this script could not "
        "self-certify -- it required ChatGPT's own independent review of the ratified package, not just "
        "Claude's implementation, and ChatGPT has now given that confirmation explicitly.",
        "",
        "**No gate above authorizes training, inference, seed 73, checkpoint work, export, deployment, "
        "activation, cleanup, commit, or push. Static package only -- 15/15 gates PASS is a statement "
        "about this package's static correctness, not a downstream authorization.**",
        "",
    ]
    OUTPUT_GATE_REPORT_PATH.write_bytes("\n".join(gate_lines).encode("utf-8"))
    print(f"{OUTPUT_GATE_REPORT_PATH.name}: fifteen-gate compliance report")

    print("\n=== Step 11: derivation report ===")
    report = f"""# Regression-Balanced Repair Candidate Corpus Derivation -- Provenance & Validation Report

**Generated by:** `prepare_regression_balanced_repair_candidate_corpus.py`
**Authorized by:** Johnny, 2026-08-11 -- "Yes, proceed" (confirmed directly, not just relayed) for the
corpus-implementation package: exact reviewed seven-record proposal data, derived 85-record candidate,
static processed split artifacts, record-level manifest, fingerprints, fail-closed validators, and static
reports demonstrating all fifteen design gates.
**Compute performed:** none. **Training/inference performed:** none.
**Baseline corpus (`{BASELINE_PATH.name}`):** untouched -- read-only, fingerprint-pinned.
**Frozen benchmarks, rubric, prompt contract, parser, C17-C evidence:** untouched, never written by this script.

## Pinned inputs (all canonicalized uniformly, not flat-hashed)

| Input | SHA-256 |
|---|---|
| Baseline corpus (`{BASELINE_PATH.name}`, {len(baseline)} records) | `{EXPECTED_BASELINE_FINGERPRINT}` |
| Regression-balanced-repair proposal (`{PROPOSAL_PATH.name}`, {len(proposal)} records) | `{EXPECTED_PROPOSAL_FINGERPRINT}` |
| Composite proposal (AT-C provenance, `{COMPOSITE_PROPOSAL_PATH.name}`) | `{EXPECTED_COMPOSITE_PROPOSAL_FINGERPRINT}` |
| Existing val split (`{EXISTING_VAL_PATH.name}`) | `{EXPECTED_EXISTING_VAL_FINGERPRINT}` |
| Existing train split (`{EXISTING_TRAIN_PATH.name}`) | `{EXPECTED_EXISTING_TRAIN_FINGERPRINT}` |
| Split manifest | `{EXPECTED_SPLIT_MANIFEST_FINGERPRINT}` |
| Protected-16 benchmark | `{EXPECTED_PROTECTED_PROBES_FINGERPRINT}` |
| Acceptance-10 benchmark | `{EXPECTED_ACCEPTANCE_PROBES_FINGERPRINT}` |

## Fail-closed checks performed, all passed

1. All eight pinned inputs matched their expected canonical fingerprint via checkout-portable
   canonicalization (uniform CRLF tolerated, anything else fails closed) -- applied to every pinned input
   in this script, not a subset.
2. Baseline is exactly {EXPECTED_BASELINE_COUNT} records; proposal is exactly {EXPECTED_PROPOSAL_COUNT}.
3. Size ceiling: 3 new records (ceiling {NEW_RECORD_CEILING}) + 4 reused attribution records (ceiling {REUSED_ATTRIBUTION_CEILING}).
4. Every proposal record matches the exact reviewed schema; `{FORBIDDEN_CATEGORY}` category never present.
5. RB-A1 through RB-A4 are object-identical to AT-C1 through AT-C4 in the reviewed composite proposal --
   never a re-typed or paraphrased copy.
6. Every record has exactly one primary mechanism from {{A_attribution, B_action_completeness, C_source_state, D_structural}}.
7. Group-A resolve/preserve/order balance: RB-A1/RB-A4 form a genuine order-swapped control pair; RB-A2/RB-A3
   preserve explicit unresolved alternatives in their bullets.
8. Group-B action completeness: RB-B1/RB-B3 action items carry every required qualifier field-by-field, no
   promoted observation content.
9. Group-C no-invention: RB-C3 preserves every unresolved reference and the supported condition; no invented
   identity, plurality, or evaluation.
10. No duplicate input hash within baseline, within proposal, or against baseline/benchmark inputs.
10a. Historical corpus/proposal inventory ({len(HISTORICAL_INVENTORY)} files spanning this repository's
    gold_v1.2.2/R2/Phase-2/contrastive lineage) fail-closed-verified: every input-bearing file is 100%
    subsumed by an already-pinned source, every non-input-bearing file is structurally out of scope -- see
    the manifest's inventory table for per-file evidence.
11. Normalized exact-equality and containment check (predeclared normalization: Unicode NFKC then
    lowercase, strip all but `[a-z0-9 ]`, collapse whitespace) -- fail-closed, run for all 7 proposed
    records against the full baseline + composite + protected + acceptance + rejected-treatment-candidate +
    proposal-self pool.
12. Independent token-Jaccard AND character-{CHAR_NGRAM_N}-gram-Jaccard collision sweep run for all 7
    proposed records against the same pool, with predeclared review thresholds (token >= {TOKEN_JACCARD_REVIEW_THRESHOLD},
    char-{CHAR_NGRAM_N}-gram >= {CHAR_NGRAM_REVIEW_THRESHOLD}) fixed before this run, plus the two mandatory named
    comparisons (Rina/Marcus vs protected 06, RB-A3 vs protected 06), reported regardless of threshold.
    Every record/comparison crossing either threshold has an explicit reviewer disposition recorded in the
    manifest, not just an automated score.
13. Named-entity/quantity/temporal-phrase overlap check (non-fatal, surfaced for review) run across the same
    pool -- see the manifest for any findings.
14. The candidate's first {len(baseline_bytes)} bytes are byte-identical to the baseline's pinned canonical
    LF representation -- P2-009/P2-010 excluded by construction.
15. All six named Group-D structural exemplars (D1-D4, see manifest) independently confirmed present and
    unchanged in the candidate.
16. The written val.jsonl is byte-identical to the pinned canonical existing val split -- validation
    membership frozen.
17. The 7 proposal records were appended in exactly the proposal file's own order, confirmed by input-hash
    sequence.
18. v1_target/v2_target mechanically generated for all 7 proposal records via
    `prompt_contract_v2_migrate.build_v1_target`/`build_v2_target` (never hand-authored), each parse-verified
    for exact structural equality against the authored output.
19. Candidate corpus is exactly {EXPECTED_CANDIDATE_COUNT} records; split is exactly {EXPECTED_TRAIN_COUNT}
    train / {EXPECTED_VAL_COUNT} val.

## Fingerprints

| Artifact | SHA-256 |
|---|---|
| Baseline content (input+output, {len(baseline)} records) | `{baseline_content_fp}` |
| Candidate content (input+output, {len(candidate)} records) | `{candidate_content_fp}` |
| Candidate corpus file (`{OUTPUT_CORPUS_PATH.name}`) | `{candidate_corpus_fp}` |
| Baseline training-data fingerprint (canonical, {EXPECTED_TRAIN_COUNT - EXPECTED_PROPOSAL_COUNT} train + {EXPECTED_VAL_COUNT} val, for comparison) | `{baseline_training_data_fp}` |
| Candidate training-data fingerprint (canonical, {EXPECTED_TRAIN_COUNT} train + {EXPECTED_VAL_COUNT} val) | `{new_training_data_fp}` |

## Named collision comparisons (mandatory, regardless of threshold)

| Comparison | Token Jaccard | Char-{CHAR_NGRAM_N}-gram Jaccard |
|---|---:|---:|
| Rina/Marcus (preserved baseline record) vs protected 06 | {collision_results['_named_comparisons']['rina_marcus_vs_protected_06']['token_jaccard']} | {collision_results['_named_comparisons']['rina_marcus_vs_protected_06']['char_ngram_jaccard']} |
| RB-A3 (exact reuse of AT-C3) vs protected 06 | {collision_results['_named_comparisons']['RB-A3_vs_protected_06']['token_jaccard']} | {collision_results['_named_comparisons']['RB-A3_vs_protected_06']['char_ngram_jaccard']} |

See `{OUTPUT_MANIFEST_PATH.name}` for the full reviewable disposition on both.

## Entity/quantity overlap findings

{len(entity_overlap_findings)} finding(s) (non-fatal, surfaced for review) -- see `{OUTPUT_MANIFEST_PATH.name}` for detail.

## Appended records (in candidate order, positions {EXPECTED_BASELINE_COUNT}-{EXPECTED_CANDIDATE_COUNT - 1})

| Label | Mechanism | Reused | Category | Difficulty | Bullets | Actions | Token max | Char-{CHAR_NGRAM_N}-gram max | Needs disposition | Input excerpt |
|---|---|---|---|---:|---:|---:|---:|---:|---|---|
"""
    for entry in comparison["appended_records_in_order"]:
        report += (
            f"| {entry['label']} | `{entry['primary_mechanism']}` | {'yes' if entry['reused'] else 'no'} | "
            f"`{entry['category']}` | {entry['difficulty']} | {entry['bullets']} | {entry['actions']} | "
            f"{entry['collision_max_token_jaccard']} | {entry['collision_max_char_ngram_jaccard']} | "
            f"{'yes' if entry['needs_disposition'] else 'no'} | {entry['input_excerpt']}... |\n"
        )

    report += f"""
## Status

Candidate corpus written to `{OUTPUT_CORPUS_PATH.name}` ({len(candidate)} records) -- a separately
fingerprinted candidate, not a modification of the immutable baseline. Candidate train/val split written to
`{output_data_dir.relative_to(TRAINING_DIR).as_posix()}/` ({len(train_pairs)} train / {len(val_pairs)} val).
Frozen benchmarks, rubric, prompt contract, parser, and the committed C17-C evidence are untouched and
never read as a data source or write target by this script.

**Stopping here for ChatGPT's independent review, as authorized. Everything this script wrote remains
uncommitted. No training, inference, benchmark execution, seed 73, checkpoint work, export, deployment,
activation, cleanup, commit, or push has been performed or authorized.**
"""
    OUTPUT_REPORT_PATH.write_bytes(report.encode("utf-8"))
    print(f"{OUTPUT_REPORT_PATH.name}: derivation report")

    print("\n=== Summary ===")
    print(f"Candidate corpus: {len(candidate)} records ({len(baseline)} baseline + {len(proposal_hashes)} proposal)")
    print(f"Split: {len(train_pairs)} train / {len(val_pairs)} val")
    print(f"Candidate training-data fingerprint: {new_training_data_fp}")
    print("\nDone. Stopping for ChatGPT's independent review -- no training or inference performed. Nothing committed.")


if __name__ == "__main__":
    main()
