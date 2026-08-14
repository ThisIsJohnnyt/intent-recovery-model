"""Frozen, model-free selector for the revision-2 auxiliary-span validation set.

Design rule: review this file before running it against the real corpus.  The
only real-data entry point requires ``--execute-frozen-selection``.  ``--self-test``
uses synthetic records and does not open any repository dataset.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "training" / "controlled_seed17_aux_span_validation_manifest.json"

INPUTS = {
    "comparator": (
        ROOT / "training" / "gold_v1.2.2_phase2_derived_candidate.jsonl",
        78,
        "6e9e5f1bea8fc3cbcb615376a1d055bd273605d0f8c1e40a8c120720c8cb836c",
    ),
    "protected": (
        ROOT / "datasets" / "benchmark" / "gold_v1.2.1_probes.jsonl",
        16,
        "767fe21a1097b51cef38728dcff0ff9ca4cf280bde8e65a7d885729f40990c0f",
    ),
    "acceptance": (
        ROOT / "datasets" / "benchmark" / "source_determined_items_v2_acceptance_draft.jsonl",
        10,
        "b8fe4d4178e5b508757db998eacb1ee979518697c8df759ba1739227c88d448e",
    ),
    "treatment_delta": (
        ROOT / "training" / "regression_balanced_repair_proposal.jsonl",
        7,
        "192372fd44fc87ea879d2ab7b751a3d54be100b447b886c213b26553284a747a",
    ),
}

GUIDE_PATH = ROOT / "training" / "controlled_seed17_aux_span_annotation_guide_r2_chatgpt.md"
GUIDE_SHA256 = "d652cc02958e8575f24d20ab0ecc674f5ce7887f55fd0d8403d58d913dcd0923"
STATIC_AUDIT_PATH = ROOT / "training" / "build_rbr17c_static_audit_map.py"
STATIC_AUDIT_SHA256 = "aee75d7ecd8db680056c8a8e9f11e9ff5cfb52a285fdb2d319d1ca2c6ea6cfca"

REGRESSION_IDS = (7, 40, 42, 48, 53, 54, 56, 69, 74, 75)
STATIC_PROTECTED_ANALOGUE_IDS = (42, 48, 53, 54, 56, 61, 69, 70, 74, 75, 76)
FRESH_SET_SIZE = 4
FEATURE_ORDER = (
    "unfielded_independent_content",
    "implicit_actor_task",
    "referential_expression",
    "qualifier_precedence",
)

# Previously ratified collision rules.  For this selection, review-threshold
# crossings are conservatively fatal because these records are validation data.
TOKEN_JACCARD_THRESHOLD = 0.15
CHAR_5GRAM_JACCARD_THRESHOLD = 0.10
CONTAINMENT_MIN_NORMALIZED_CHARS = 20

CONTENT_STOPWORDS = frozenset(
    "a an and are as at be been but by for from had has have i if in is it of on or that the then to was were will with".split()
)
CLAUSE_SPLIT_RE = re.compile(r"(?:[.!?;\n]+|\s+[—–-]\s+)")
REFERENTIAL_RE = re.compile(
    r"\b(?:he|she|they|him|her|them|his|hers|their|theirs|it|its|this|that|these|those|"
    r"former|latter|earlier one|earlier version|same one|same version)\b",
    re.IGNORECASE,
)
TASK_CUE_RE = re.compile(
    r"(?:^|\b)(?:need to|needs to|remember to|remind\b|must\b|should\b|have to|has to|"
    r"ask\b|call\b|send\b|check\b|confirm\b|email\b|text\b|schedule\b|book\b|buy\b|"
    r"bring\b|take\b|return\b|pick up\b|follow up\b|review\b|print\b|file\b|order\b|"
    r"document\b|update\b|draft\b|upload\b|deliver\b|get\b)",
    re.IGNORECASE,
)
EXPLICIT_ACTOR_RE = re.compile(
    r"(?:^|[.;!?]\s+)(?:i|we|he|she|they|you|[A-Z][a-z]+)\s+"
    r"(?:need|needs|must|should|have|has|will|can|asked|asks|said|says|told|reminded|"
    r"send|call|check|confirm|email|text|schedule|book|buy|bring|take|return|review|print|file|order|document|update|draft|upload|deliver|get)\b"
)
QUALIFIER_PATTERNS = {
    "deadline": re.compile(r"\b(?:by|before|no later than|due)\s+(?:\w+\s*){1,4}", re.IGNORECASE),
    "trigger": re.compile(r"\b(?:after|once|when|upon|until|as soon as)\b", re.IGNORECASE),
    "condition": re.compile(r"\b(?:if|unless|provided that|in case)\b", re.IGNORECASE),
    "time": re.compile(
        r"\b(?:today|tonight|tomorrow|yesterday|morning|afternoon|evening|monday|tuesday|"
        r"wednesday|thursday|friday|saturday|sunday|week|month|hour|minute|late|early)\b",
        re.IGNORECASE,
    ),
    "quantity": re.compile(r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b", re.IGNORECASE),
    "destination": re.compile(r"\b(?:to|into|onto|at)\s+(?:the\s+)?(?:office|folder|site|room|desk|store|school|clinic|museum|client)\b", re.IGNORECASE),
    "purpose": re.compile(r"\b(?:so that|in order to|for the purpose of)\b", re.IGNORECASE),
    "object_modifier": re.compile(r"\b(?:earlier|final|draft|revised|updated|signed|stamped|cracked|damaged|repaired|approved)\s+\w+", re.IGNORECASE),
}


@dataclass(frozen=True)
class Candidate:
    record_id: int
    record: dict[str, Any]
    category: str
    feature_scores: dict[str, int]
    feature_evidence: dict[str, list[str]]
    max_token_jaccard: float
    max_char_5gram_jaccard: float


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def canonicalize_pinned_bytes(label: str, raw: bytes, expected_canonical_hash: str) -> tuple[bytes, str]:
    """Accept only uniform LF or uniform CRLF, then verify canonical-LF identity."""
    if raw.startswith(b"\xef\xbb\xbf"):
        raise RuntimeError(f"FATAL: {label} has a UTF-8 BOM")
    if not raw.endswith(b"\n"):
        raise RuntimeError(f"FATAL: {label} lacks a terminal newline")
    has_crlf = b"\r\n" in raw
    without_crlf = raw.replace(b"\r\n", b"")
    if b"\r" in without_crlf:
        raise RuntimeError(f"FATAL: {label} has a bare CR")
    if has_crlf and b"\n" in without_crlf:
        raise RuntimeError(f"FATAL: {label} has mixed LF and CRLF line endings")
    line_endings = "crlf" if has_crlf else "lf"
    canonical = raw.replace(b"\r\n", b"\n")
    actual_hash = sha256_bytes(canonical)
    if actual_hash != expected_canonical_hash:
        raise RuntimeError(
            f"FATAL: {label} canonical-LF hash mismatch: expected {expected_canonical_hash}, got {actual_hash}"
        )
    return canonical, line_endings


def load_pinned_jsonl(label: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path, expected_count, expected_canonical_hash = INPUTS[label]
    raw = path.read_bytes()
    canonical, line_endings = canonicalize_pinned_bytes(label, raw, expected_canonical_hash)
    try:
        decoded = canonical.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"FATAL: {label} is not valid UTF-8") from exc
    lines = decoded.splitlines()
    if len(lines) != expected_count or any(not line.strip() for line in lines):
        raise RuntimeError(f"FATAL: {label} expected {expected_count} nonblank records, got {len(lines)}")
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, 1):
        value = json.loads(line, object_pairs_hook=_reject_duplicate_keys)
        if not isinstance(value, dict):
            raise RuntimeError(f"FATAL: {label}:{line_number} is not a JSON object")
        records.append(value)
    receipt = {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "record_count": expected_count,
        "checkout_line_endings": line_endings,
        "checkout_byte_sha256": sha256_bytes(raw),
        "canonical_lf_sha256": expected_canonical_hash,
    }
    return records, receipt


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def normalize_for_collision(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_set(text: str) -> set[str]:
    return set(normalize_for_collision(text).split())


def content_tokens(text: str) -> set[str]:
    return {token for token in token_set(text) if token not in CONTENT_STOPWORDS and len(token) > 1}


def jaccard(left: set[str], right: set[str]) -> float:
    return len(left & right) / len(left | right) if left and right else 0.0


def char_5grams(text: str) -> set[str]:
    normalized = normalize_for_collision(text).replace(" ", "")
    if not normalized:
        return set()
    if len(normalized) < 5:
        return {normalized}
    return {normalized[index : index + 5] for index in range(len(normalized) - 4)}


def record_input(record: dict[str, Any], label: str) -> str:
    value = record.get("input")
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"FATAL: {label} lacks a nonblank string input")
    return value


def reference_inputs(records: Iterable[dict[str, Any]], label: str) -> list[tuple[str, str]]:
    return [(f"{label}:{index:03d}", record_input(record, f"{label}:{index:03d}")) for index, record in enumerate(records, 1)]


def collision_metrics(text: str, references: list[tuple[str, str]]) -> tuple[bool, float, float, list[str]]:
    normalized = normalize_for_collision(text)
    maximum_token = 0.0
    maximum_char = 0.0
    reasons: list[str] = []
    for label, reference in references:
        normalized_reference = normalize_for_collision(reference)
        if not normalized or not normalized_reference:
            continue
        token_score = jaccard(set(normalized.split()), set(normalized_reference.split()))
        char_score = jaccard(char_5grams(text), char_5grams(reference))
        maximum_token = max(maximum_token, token_score)
        maximum_char = max(maximum_char, char_score)
        shorter = min(len(normalized), len(normalized_reference))
        if normalized == normalized_reference:
            reasons.append(f"normalized exact match with {label}")
        elif shorter >= CONTAINMENT_MIN_NORMALIZED_CHARS and (
            normalized in normalized_reference or normalized_reference in normalized
        ):
            reasons.append(f"normalized containment with {label}")
        if token_score >= TOKEN_JACCARD_THRESHOLD:
            reasons.append(f"token Jaccard {token_score:.6f} with {label}")
        if char_score >= CHAR_5GRAM_JACCARD_THRESHOLD:
            reasons.append(f"character-5-gram Jaccard {char_score:.6f} with {label}")
    return bool(reasons), maximum_token, maximum_char, reasons


def target_strings(record: dict[str, Any], label: str) -> list[str]:
    output = record.get("output")
    if not isinstance(output, dict):
        raise RuntimeError(f"FATAL: {label} lacks an output object")
    strings: list[str] = []
    narrative = output.get("narrative")
    if isinstance(narrative, str) and narrative.strip():
        strings.append(narrative)
    for key in ("bullets", "action_items"):
        values = output.get(key)
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            raise RuntimeError(f"FATAL: {label} output.{key} must be a string list")
        strings.extend(value for value in values if value.strip())
    return strings


def feature_profile(record: dict[str, Any], label: str) -> tuple[dict[str, int], dict[str, list[str]]]:
    source = record_input(record, label)
    targets = target_strings(record, label)
    evidence: dict[str, list[str]] = {feature: [] for feature in FEATURE_ORDER}

    # Selection heuristic only: an independently punctuated source segment whose
    # content has little lexical realization anywhere in the committed target.
    for segment in (part.strip(" \t,:") for part in CLAUSE_SPLIT_RE.split(source)):
        segment_tokens = content_tokens(segment)
        if len(segment_tokens) < 2:
            continue
        maximum = max((jaccard(segment_tokens, content_tokens(target)) for target in targets), default=0.0)
        if maximum < 0.20:
            evidence["unfielded_independent_content"].append(
                f"low-target-overlap segment ({maximum:.3f}): {segment[:120]}"
            )

    task_cues = list(TASK_CUE_RE.finditer(source))
    explicit_actor = bool(EXPLICIT_ACTOR_RE.search(source))
    action_items = record.get("output", {}).get("action_items", [])
    if task_cues and action_items and not explicit_actor:
        evidence["implicit_actor_task"].append(
            f"{len(task_cues)} task cue(s), {len(action_items)} committed action(s), no explicit-actor pattern"
        )

    referents = [match.group(0) for match in REFERENTIAL_RE.finditer(source)]
    if referents:
        evidence["referential_expression"].append("referential cues: " + ", ".join(referents[:12]))

    qualifier_hits: list[str] = []
    for qualifier, pattern in QUALIFIER_PATTERNS.items():
        count = len(list(pattern.finditer(source)))
        if count:
            qualifier_hits.append(f"{qualifier}:{count}")
    if qualifier_hits:
        evidence["qualifier_precedence"].append("qualifier cues: " + ", ".join(qualifier_hits))

    scores = {
        "unfielded_independent_content": len(evidence["unfielded_independent_content"]),
        "implicit_actor_task": len(task_cues) + len(action_items) if evidence["implicit_actor_task"] else 0,
        "referential_expression": len(referents),
        "qualifier_precedence": len(qualifier_hits),
    }
    return scores, evidence


def select_candidates(comparator: list[dict[str, Any]], references: list[tuple[str, str]]) -> tuple[list[Candidate], list[dict[str, Any]]]:
    excluded_ids = set(REGRESSION_IDS) | set(STATIC_PROTECTED_ANALOGUE_IDS)
    eligible: list[Candidate] = []
    exclusions: list[dict[str, Any]] = []
    for record_id, record in enumerate(comparator, 1):
        label = f"comparator:{record_id:03d}"
        if record_id in excluded_ids:
            exclusions.append({"record_id": record_id, "reason": "regression set or static protected-analogue register"})
            continue
        source = record_input(record, label)
        fatal, max_token, max_char, reasons = collision_metrics(source, references)
        if fatal:
            exclusions.append({"record_id": record_id, "reason": "leakage threshold", "details": reasons})
            continue
        scores, evidence = feature_profile(record, label)
        category = record.get("category")
        if not isinstance(category, str) or not category:
            raise RuntimeError(f"FATAL: {label} lacks a category")
        eligible.append(Candidate(record_id, record, category, scores, evidence, max_token, max_char))

    selected: list[Candidate] = []
    used_categories: set[str] = set()
    for feature in FEATURE_ORDER:
        choices = []
        for candidate in eligible:
            if candidate in selected or candidate.feature_scores[feature] <= 0:
                continue
            selected_pool = [
                (f"already_selected:{prior.record_id:03d}", record_input(prior.record, "already selected"))
                for prior in selected
            ]
            pairwise_fatal, _, _, _ = collision_metrics(
                record_input(candidate.record, f"comparator:{candidate.record_id:03d}"), selected_pool
            )
            if not pairwise_fatal:
                choices.append(candidate)
        if not choices:
            raise RuntimeError(f"FATAL: no leakage-clean unused candidate covers {feature}")
        choices.sort(
            key=lambda candidate: (
                -candidate.feature_scores[feature],
                candidate.category in used_categories,
                candidate.max_token_jaccard,
                candidate.max_char_5gram_jaccard,
                candidate.record_id,
            )
        )
        choice = choices[0]
        selected.append(choice)
        used_categories.add(choice.category)

    if len(selected) != FRESH_SET_SIZE or any(
        not any(candidate.feature_scores[feature] > 0 for candidate in selected) for feature in FEATURE_ORDER
    ):
        raise RuntimeError("FATAL: fresh-set size or stress-feature coverage invariant failed")
    return selected, exclusions


def frozen_record(record_id: int, record: dict[str, Any], set_name: str) -> dict[str, Any]:
    payload = {"input": record["input"], "output": record["output"]}
    return {
        "set": set_name,
        "record_locator": f"comparator:{record_id:03d}",
        "record_id": record_id,
        "category": record.get("category"),
        "difficulty": record.get("difficulty"),
        "record_sha256": sha256_bytes(canonical_json_bytes(payload)),
        "source_input": record["input"],
        "committed_target": record["output"],
    }


def build_manifest() -> dict[str, Any]:
    if sha256_bytes(GUIDE_PATH.read_bytes()) != GUIDE_SHA256:
        raise RuntimeError("FATAL: annotation-guide hash mismatch")
    if sha256_bytes(STATIC_AUDIT_PATH.read_bytes()) != STATIC_AUDIT_SHA256:
        raise RuntimeError("FATAL: static-audit-map hash mismatch")
    comparator, comparator_receipt = load_pinned_jsonl("comparator")
    protected, protected_receipt = load_pinned_jsonl("protected")
    acceptance, acceptance_receipt = load_pinned_jsonl("acceptance")
    treatment, treatment_receipt = load_pinned_jsonl("treatment_delta")
    input_receipts = {
        "comparator": comparator_receipt,
        "protected": protected_receipt,
        "acceptance": acceptance_receipt,
        "treatment_delta": treatment_receipt,
    }
    references = (
        reference_inputs(protected, "protected")
        + reference_inputs(acceptance, "acceptance")
        + reference_inputs(treatment, "treatment_delta")
    )
    selected, exclusions = select_candidates(comparator, references)
    regression = [frozen_record(record_id, comparator[record_id - 1], "regression") for record_id in REGRESSION_IDS]
    fresh = []
    for assigned_feature, candidate in zip(FEATURE_ORDER, selected):
        item = frozen_record(candidate.record_id, candidate.record, "fresh")
        item.update(
            {
                "assigned_stress_feature": assigned_feature,
                "all_feature_scores": candidate.feature_scores,
                "feature_evidence": candidate.feature_evidence,
                "leakage_maxima": {
                    "token_jaccard": round(candidate.max_token_jaccard, 9),
                    "character_5gram_jaccard": round(candidate.max_char_5gram_jaccard, 9),
                },
            }
        )
        fresh.append(item)
    manifest: dict[str, Any] = {
        "artifact": "controlled_seed17_aux_span_validation_manifest",
        "status": "frozen_unannotated",
        "execution_history": {
            "prior_failed_attempt_count": 1,
            "prior_failure": {
                "date": "2026-08-14",
                "stage": "input_line_ending_preflight",
                "reason": "original LF-only reader rejected uniform-CRLF Windows checkout materialization",
                "manifest_written": False,
            },
            "successful_manifest_generation_count": 1,
        },
        "authority_boundary": (
            "Freezes records only. Does not authorize annotation, model/tokenizer use, Gemini activity, "
            "implementation, training, evaluation, checkpoint operations, staging, commit, or push."
        ),
        "input_pins_and_checkout_receipts": input_receipts,
        "governing_pins": {
            "annotation_guide_sha256": GUIDE_SHA256,
            "static_audit_map_sha256": STATIC_AUDIT_SHA256,
        },
        "selection_rules": {
            "fresh_set_size": FRESH_SET_SIZE,
            "feature_order": list(FEATURE_ORDER),
            "regression_ids": list(REGRESSION_IDS),
            "static_protected_analogue_ids": list(STATIC_PROTECTED_ANALOGUE_IDS),
            "collision_thresholds": {
                "normalized_exact": "exclude",
                "normalized_containment_min_chars": CONTAINMENT_MIN_NORMALIZED_CHARS,
                "token_jaccard": TOKEN_JACCARD_THRESHOLD,
                "character_5gram_jaccard": CHAR_5GRAM_JACCARD_THRESHOLD,
                "all_threshold_crossings": "exclude",
            },
            "tie_break": "score desc; unused category first; token max asc; char-5gram max asc; record id asc",
            "within_fresh_set_collision_screen": "same thresholds; any crossing excludes the later choice",
        },
        "regression_records": regression,
        "fresh_records": fresh,
        "exclusion_audit": exclusions,
        "future_gemini_quarantine": [item["record_locator"] for item in fresh],
    }
    validation_records = regression + fresh
    manifest["validation_set_fingerprint"] = sha256_bytes(canonical_json_bytes(validation_records))
    manifest["manifest_sha256"] = sha256_bytes(canonical_json_bytes(manifest))
    return manifest


def run_self_test() -> None:
    assert normalize_for_collision(" Café—A! ") == "caf a"
    assert jaccard({"a", "b"}, {"b", "c"}) == 1 / 3
    assert char_5grams("abcd") == {"abcd"}
    canonical_fixture = b'{"x":1}\n{"x":2}\n'
    canonical_hash = sha256_bytes(canonical_fixture)
    normalized_lf, lf_style = canonicalize_pinned_bytes("synthetic-lf", canonical_fixture, canonical_hash)
    normalized_crlf, crlf_style = canonicalize_pinned_bytes(
        "synthetic-crlf", canonical_fixture.replace(b"\n", b"\r\n"), canonical_hash
    )
    assert normalized_lf == normalized_crlf == canonical_fixture
    assert lf_style == "lf" and crlf_style == "crlf"

    rejected_fixtures = {
        "bom": b"\xef\xbb\xbf" + canonical_fixture,
        "mixed": b'{"x":1}\r\n{"x":2}\n',
        "bare-cr": b'{"x":1}\r{"x":2}\n',
        "missing-terminal-newline": b'{"x":1}',
    }
    for fixture_label, fixture in rejected_fixtures.items():
        try:
            canonicalize_pinned_bytes(f"synthetic-{fixture_label}", fixture, canonical_hash)
        except RuntimeError:
            pass
        else:
            raise AssertionError(f"{fixture_label} fixture was not rejected")
    try:
        canonicalize_pinned_bytes("synthetic-content-drift", b'{"x":3}\n', canonical_hash)
    except RuntimeError as exc:
        assert "hash mismatch" in str(exc)
    else:
        raise AssertionError("post-canonicalization content drift was not rejected")
    exact, _, _, reasons = collision_metrics("Send the file Friday", [("x", "send the file friday")])
    assert exact and any("exact" in reason for reason in reasons)
    synthetic = {
        "input": "Need to call the clinic Friday. Blue cabinet thought.",
        "output": {"narrative": "Call the clinic Friday.", "bullets": ["Call clinic"], "action_items": ["Call clinic"]},
    }
    scores, _ = feature_profile(synthetic, "synthetic")
    assert scores["unfielded_independent_content"] > 0
    assert scores["implicit_actor_task"] > 0
    assert scores["qualifier_precedence"] > 0
    referential = {
        "input": "Mara gave Jo the folder and she filed it.",
        "output": {"narrative": "Mara gave Jo the folder and she filed it.", "bullets": [], "action_items": []},
    }
    assert feature_profile(referential, "synthetic")[0]["referential_expression"] == 2
    print("PASS: synthetic self-test; no repository dataset opened")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--execute-frozen-selection", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        run_self_test()
        return
    if OUTPUT_PATH.exists():
        raise RuntimeError(f"FATAL: manifest already exists; refusing to overwrite {OUTPUT_PATH}")
    manifest = build_manifest()
    OUTPUT_PATH.write_bytes(json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
    print(f"WROTE {OUTPUT_PATH}")
    print(f"manifest_sha256={sha256_bytes(OUTPUT_PATH.read_bytes())}")
    print("fresh_record_locators=" + ",".join(item["record_locator"] for item in manifest["fresh_records"]))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
