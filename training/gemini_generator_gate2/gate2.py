"""Gate 2 local-only Gemini generator implementation.

This module has no provider SDK and no network transport.  Its runner accepts
only MockTransport, making paid or external execution structurally unavailable
at this gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import socket
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = Path(__file__).resolve().parent
SYSTEM_PATH = PACKAGE / "system_instruction.txt"
USER_TEMPLATE_PATH = PACKAGE / "user_message_template.txt"
SCHEMA_PATH = PACKAGE / "response_schema.json"
CARDS_PATH = PACKAGE / "mechanism_cards.json"
RATE_PATH = PACKAGE / "rate_snapshot.json"
PROVIDER_CONTRACT_PATH = PACKAGE / "provider_contract.json"

MODELS = ("gemini-3.7-flash", "gemini-3.5-flash-lite")
MAX_INPUT_TOKENS = 4_000
MAX_OUTPUT_TOKENS = 2_048
PILOT_CEILING_USD_MILLIONTHS = 3_000_000
RECONCILIATION_STOP_USD_MILLIONTHS = 2_250_000
ACCOUNT_CAP_USD_MILLIONTHS = 10_000_000
TOKEN_JACCARD_THRESHOLD = 0.15
CHAR_5GRAM_JACCARD_THRESHOLD = 0.10
CONTAINMENT_MIN_NORMALIZED_CHARS = 20
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
CARD_ID_RE = re.compile(r"^M(?:0[1-9]|1[0-2])$")
WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)
SENTENCE_RE = re.compile(r"[^.!?]+[.!?](?:\s|$)")
TEMPORAL_RE = re.compile(
    r"\b(?:today|tonight|tomorrow|yesterday|morning|afternoon|evening|monday|tuesday|"
    r"wednesday|thursday|friday|saturday|sunday|week|month|hour|minute|by|before|after)\b",
    re.IGNORECASE,
)
QUANTITY_RE = re.compile(r"\b(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten)\b", re.IGNORECASE)
ENTITY_RE = re.compile(r"\b[A-Z][a-z]{2,}\b")
ROLE_RE = re.compile(r"\b(?:writer|client|vendor|speaker|volunteer|caregiver|recipient|owner)\b", re.IGNORECASE)
SECRET_KEY_RE = re.compile(r"(?:api.?key|authorization|credential|secret|token|password|account.?id|billing.?id)", re.IGNORECASE)
BEARER_RE = re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+\-/]+=*")
GOOGLE_KEY_RE = re.compile(r"AIza[0-9A-Za-z_-]{20,}")

QUARANTINE_INPUTS = {
    "comparator": {
        "path": "training/gold_v1.2.2_phase2_derived_candidate.jsonl",
        "count": 78,
        "canonical_lf_sha256": "6e9e5f1bea8fc3cbcb615376a1d055bd273605d0f8c1e40a8c120720c8cb836c",
    },
    "protected": {
        "path": "datasets/benchmark/gold_v1.2.1_probes.jsonl",
        "count": 16,
        "canonical_lf_sha256": "767fe21a1097b51cef38728dcff0ff9ca4cf280bde8e65a7d885729f40990c0f",
    },
    "acceptance": {
        "path": "datasets/benchmark/source_determined_items_v2_acceptance_draft.jsonl",
        "count": 10,
        "canonical_lf_sha256": "b8fe4d4178e5b508757db998eacb1ee979518697c8df759ba1739227c88d448e",
    },
    "treatment_delta": {
        "path": "training/regression_balanced_repair_proposal.jsonl",
        "count": 7,
        "canonical_lf_sha256": "192372fd44fc87ea879d2ab7b751a3d54be100b447b886c213b26553284a747a",
    },
}
VALIDATION_LOCATORS = (
    "comparator:007", "comparator:040", "comparator:042", "comparator:048", "comparator:053",
    "comparator:054", "comparator:056", "comparator:069", "comparator:074", "comparator:075",
    "comparator:012", "comparator:073", "comparator:008", "comparator:030", "comparator:018",
)
REASON_CODES = {
    "provider_blocked", "transport_failed_no_retry", "model_identity_mismatch", "finish_reason_invalid",
    "schema_invalid", "extra_key", "size_limit_failed", "prompt_imitation", "protected_collision",
    "pilot_duplicate", "secret_exposure", "budget_or_usage_unknown", "manual_global_stop",
}
DIMENSIONS = (
    "schema_validity", "source_interpretability", "independent_content_retention", "task_fidelity",
    "uncertainty_question_preservation", "attribution_reference_fidelity", "chronology_qualifier_fidelity",
    "unsupported_addition_resistance", "field_appropriateness", "duplication_control_compliance", "tone_safety",
)


class Gate2Error(RuntimeError):
    pass


class ResponseSchemaError(Gate2Error):
    """A response-shape failure with a content-free machine reason."""

    def __init__(self, message: str, structured_reason: dict[str, Any]):
        self.structured_reason = structured_reason
        super().__init__(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def canonical_file(path: Path, expected_hash: str | None = None) -> tuple[bytes, dict[str, Any]]:
    resolved = path.resolve()
    try:
        relative_path = resolved.relative_to(ROOT)
    except ValueError as exc:
        raise Gate2Error(f"{path}: path is outside the project root") from exc
    raw: bytes | None = None
    last_error: OSError | None = None
    for _ in range(3):
        try:
            raw = resolved.read_bytes()
            break
        except OSError as exc:
            last_error = exc
    if raw is None:
        raise Gate2Error(f"{path}: unreadable") from last_error
    if raw.startswith(b"\xef\xbb\xbf"):
        raise Gate2Error(f"{path}: UTF-8 BOM is forbidden")
    if not raw.endswith(b"\n"):
        raise Gate2Error(f"{path}: terminal newline is required")
    has_crlf = b"\r\n" in raw
    without_crlf = raw.replace(b"\r\n", b"")
    if b"\r" in without_crlf:
        raise Gate2Error(f"{path}: bare CR is forbidden")
    if has_crlf and b"\n" in without_crlf:
        raise Gate2Error(f"{path}: mixed line endings are forbidden")
    canonical = raw.replace(b"\r\n", b"\n")
    try:
        canonical.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Gate2Error(f"{path}: invalid UTF-8") from exc
    digest = sha256_bytes(canonical)
    if expected_hash and digest != expected_hash:
        raise Gate2Error(f"{path}: canonical hash mismatch; expected {expected_hash}, got {digest}")
    return canonical, {
        "path": relative_path.as_posix(),
        "checkout_line_endings": "crlf" if has_crlf else "lf",
        "checkout_byte_sha256": sha256_bytes(raw),
        "canonical_lf_sha256": digest,
    }


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise Gate2Error(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    canonical, _ = canonical_file(path)
    try:
        return json.loads(canonical, object_pairs_hook=reject_duplicate_keys)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise Gate2Error(f"{path}: invalid JSON: {exc}") from exc


def load_jsonl(path: Path, expected_count: int, expected_hash: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    canonical, receipt = canonical_file(path, expected_hash)
    lines = canonical.decode("utf-8").splitlines()
    if len(lines) != expected_count or any(not line.strip() for line in lines):
        raise Gate2Error(f"{path}: expected {expected_count} nonblank rows, got {len(lines)}")
    rows = []
    for number, line in enumerate(lines, 1):
        try:
            row = json.loads(line, object_pairs_hook=reject_duplicate_keys)
        except (json.JSONDecodeError, Gate2Error) as exc:
            raise Gate2Error(f"{path}:{number}: invalid JSON object: {exc}") from exc
        if not isinstance(row, dict):
            raise Gate2Error(f"{path}:{number}: row must be an object")
        rows.append(row)
    receipt["record_count"] = len(rows)
    return rows, receipt


def write_canonical_json(path: Path, value: Any) -> None:
    path.write_bytes(canonical_json_bytes(value))


def normalize_for_collision(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def char_5grams(text: str) -> set[str]:
    normalized = normalize_for_collision(text).replace(" ", "")
    if not normalized:
        return set()
    if len(normalized) < 5:
        return {normalized}
    return {normalized[index:index + 5] for index in range(len(normalized) - 4)}


def jaccard(left: set[str], right: set[str]) -> float:
    return len(left & right) / len(left | right) if left and right else 0.0


def flatten_output(output: Any, label: str) -> list[tuple[str, str]]:
    if not isinstance(output, dict):
        raise Gate2Error(f"{label}: output must be an object")
    expected = {"narrative", "bullets", "action_items"}
    if set(output) != expected:
        raise Gate2Error(f"{label}: output keys must be {sorted(expected)}")
    narrative = output["narrative"]
    bullets = output["bullets"]
    actions = output["action_items"]
    if not isinstance(narrative, str) or not isinstance(bullets, list) or not isinstance(actions, list):
        raise Gate2Error(f"{label}: malformed output field types")
    if any(not isinstance(item, str) for item in bullets + actions):
        raise Gate2Error(f"{label}: output list items must be strings")
    fields = [(f"{label}:output.narrative", narrative)]
    fields.extend((f"{label}:output.bullets:{i:02d}", text) for i, text in enumerate(bullets, 1))
    fields.extend((f"{label}:output.action_items:{i:02d}", text) for i, text in enumerate(actions, 1))
    return fields


def flatten_text_leaves(value: Any, path: str) -> list[tuple[str, str]]:
    fields: list[tuple[str, str]] = []
    if isinstance(value, str) and value.strip():
        fields.append((path, value))
    elif isinstance(value, list):
        for index, item in enumerate(value, 1):
            fields.extend(flatten_text_leaves(item, f"{path}:{index:02d}"))
    elif isinstance(value, dict):
        for key, item in value.items():
            fields.extend(flatten_text_leaves(item, f"{path}:{key}"))
    return fields


def build_quarantine() -> tuple[dict[str, Any], list[tuple[str, str]]]:
    pools: dict[str, Any] = {}
    references: list[tuple[str, str]] = []
    record_total = 0
    for pool, pin in QUARANTINE_INPUTS.items():
        path = ROOT / pin["path"]
        rows, receipt = load_jsonl(path, pin["count"], pin["canonical_lf_sha256"])
        entries = []
        for index, row in enumerate(rows, 1):
            label = f"{pool}:{index:03d}"
            source = row.get("input")
            if not isinstance(source, str) or not source.strip():
                raise Gate2Error(f"{label}: missing nonblank input")
            if "output" in row:
                fields = [(f"{label}:input", source)] + flatten_output(row.get("output"), label)
            else:
                # Benchmark rows encode their target contract across expected
                # behavior, checks, likely failures, notes, and related fields.
                # Screen every nonblank textual leaf so no annotation is lost.
                fields = flatten_text_leaves(row, label)
            references.extend(fields)
            entries.append({
                "record_locator": label,
                "record_sha256": sha256_bytes(canonical_json_bytes(row)),
                "field_count": len(fields),
                "field_hashes": [{"field": field.split(":", 2)[-1], "sha256": sha256_bytes(text.encode("utf-8"))} for field, text in fields],
            })
        pools[pool] = {"pin": receipt, "entries": entries}
        record_total += len(entries)
    manifest = {
        "artifact": "gemini_generator_quarantine_manifest",
        "status": "complete_four_pinned_pools",
        "record_count": record_total,
        "screened_field_count": len(references),
        "pools": pools,
        "validation_locators_already_contained_in_comparator_pool": list(VALIDATION_LOCATORS),
        "collision_thresholds": {
            "normalized_exact": "fatal",
            "normalized_containment_min_chars": CONTAINMENT_MIN_NORMALIZED_CHARS,
            "token_jaccard": TOKEN_JACCARD_THRESHOLD,
            "character_5gram_jaccard": CHAR_5GRAM_JACCARD_THRESHOLD,
        },
        "exclusions": "No private notes, repository prose/code, annotations, or receipts are prompt examples or transmitted content.",
    }
    manifest["manifest_sha256"] = sha256_bytes(canonical_json_bytes(manifest))
    return manifest, references


def collision_check(text: str, references: Iterable[tuple[str, str]]) -> dict[str, Any]:
    normalized = normalize_for_collision(text)
    tokens = set(normalized.split())
    grams = char_5grams(text)
    reasons: list[str] = []
    structured_reasons: list[dict[str, Any]] = []
    max_token = (0.0, None)
    max_char = (0.0, None)
    for label, reference in references:
        normalized_ref = normalize_for_collision(reference)
        if not normalized or not normalized_ref:
            continue
        token_score = jaccard(tokens, set(normalized_ref.split()))
        char_score = jaccard(grams, char_5grams(reference))
        if token_score > max_token[0]:
            max_token = (token_score, label)
        if char_score > max_char[0]:
            max_char = (char_score, label)
        shorter = min(len(normalized), len(normalized_ref))
        if normalized == normalized_ref:
            reasons.append(f"normalized exact match with {label}")
            structured_reasons.append({"kind": "normalized_exact_match", "reference": label, "score": None})
        elif shorter >= CONTAINMENT_MIN_NORMALIZED_CHARS and (normalized in normalized_ref or normalized_ref in normalized):
            reasons.append(f"normalized containment with {label}")
            structured_reasons.append({"kind": "normalized_containment", "reference": label, "score": None})
        if token_score >= TOKEN_JACCARD_THRESHOLD:
            reasons.append(f"token Jaccard {token_score:.6f} with {label}")
            structured_reasons.append({"kind": "token_jaccard_threshold", "reference": label, "score": round(token_score, 6)})
        if char_score >= CHAR_5GRAM_JACCARD_THRESHOLD:
            reasons.append(f"character-5-gram Jaccard {char_score:.6f} with {label}")
            structured_reasons.append({"kind": "character_5gram_jaccard_threshold", "reference": label, "score": round(char_score, 6)})
    return {
        "fatal": bool(reasons),
        "reasons": reasons,
        "structured_reasons": structured_reasons,
        "maximum_token_jaccard": {"score": round(max_token[0], 9), "reference": max_token[1]},
        "maximum_character_5gram_jaccard": {"score": round(max_char[0], 9), "reference": max_char[1]},
    }


def qualitative_similarity(text: str, reference: str) -> dict[str, Any]:
    clauses = [normalize_for_collision(p) for p in re.split(r"[.!?;\n]+", text) if normalize_for_collision(p)]
    ref_clauses = [normalize_for_collision(p) for p in re.split(r"[.!?;\n]+", reference) if normalize_for_collision(p)]
    clause_order_overlap = sum(1 for left, right in zip(clauses, ref_clauses) if left == right)
    return {
        "named_entities": sorted(set(ENTITY_RE.findall(text)) & set(ENTITY_RE.findall(reference))),
        "quantities": sorted(set(QUANTITY_RE.findall(text)) & set(QUANTITY_RE.findall(reference))),
        "temporal_phrases": sorted({v.lower() for v in TEMPORAL_RE.findall(text)} & {v.lower() for v in TEMPORAL_RE.findall(reference)}),
        "role_terms": sorted({v.lower() for v in ROLE_RE.findall(text)} & {v.lower() for v in ROLE_RE.findall(reference)}),
        "same_position_exact_clause_count": clause_order_overlap,
    }


def candidate_fields(candidate: dict[str, Any]) -> list[tuple[str, str]]:
    source = candidate.get("source_input")
    output = candidate.get("proposed_output")
    if not isinstance(source, str):
        raise Gate2Error("candidate source_input must be a string")
    return [("source_input", source)] + flatten_output(output, "proposed_output")


def screen_candidate(
    candidate: dict[str, Any],
    quarantine_references: list[tuple[str, str]],
    earlier_candidate_references: list[tuple[str, str]],
    prompt_texts: list[tuple[str, str]],
) -> dict[str, Any]:
    fields = candidate_fields(candidate)
    results = []
    fatal_reasons: list[str] = []
    for field_name, text in fields:
        protected = collision_check(text, quarantine_references)
        earlier = collision_check(text, earlier_candidate_references)
        prompt = collision_check(text, prompt_texts)
        if protected["fatal"]:
            fatal_reasons.append(f"{field_name}:protected_collision")
        if earlier["fatal"]:
            fatal_reasons.append(f"{field_name}:pilot_duplicate")
        if prompt["fatal"]:
            fatal_reasons.append(f"{field_name}:prompt_imitation")
        diagnostic_hits = []
        for reference_name, reference in quarantine_references:
            diagnostics = qualitative_similarity(text, reference)
            if any(value for value in diagnostics.values()):
                diagnostic_hits.append({"reference": reference_name, **diagnostics})
        results.append({
            "field": field_name,
            "protected": protected,
            "earlier_candidates": earlier,
            "prompt_imitation": prompt,
            "below_threshold_qualitative_hits": diagnostic_hits,
        })
    return {"fatal": bool(fatal_reasons), "fatal_reasons": fatal_reasons, "fields": results}


# --- V11-only additions below this line -------------------------------------
# Purely additive: nothing above this comment is modified, and nothing V6-V10
# call. `collision_check`/`screen_candidate` and their thresholds/behavior are
# untouched, so every prior version's frozen tests and hash-pinned artifacts
# keep passing byte-for-byte unchanged. These new functions exist only to let
# V11 isolate a single variable -- stopword removal ahead of the token-Jaccard
# comparison -- while leaving char-5-gram scoring, exact-match detection, and
# normalized-containment detection completely alone, exactly as Johnny asked:
# fix stopword removal first, reassess from there before touching anything
# else (thresholds included).
#
# The list itself is the closed, deterministic ~120-word set of English
# function words used by common general-purpose stopword lists (articles,
# pronouns, prepositions, conjunctions, auxiliary/modal verbs, and a handful
# of generic quantifiers/discourse words). It is frozen here as part of V11's
# hash-pinned build, not sourced from any external package at runtime.
STOPWORDS = frozenset({
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him",
    "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't",
    "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
    "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
    "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then",
    "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're",
    "we've", "were", "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while",
    "who", "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll",
    "you're", "you've", "your", "yours", "yourself", "yourselves",
})


def _stopword_filtered_tokens(normalized_text: str) -> set[str]:
    """`normalized_for_collision(text).split()` with STOPWORDS removed. Takes
    already-normalized text (contractions have had their apostrophe stripped
    by normalize_for_collision's `[^a-z0-9 ]` filter, e.g. "don't" -> "dont"),
    so STOPWORDS above is only ever matched post-normalization here -- the
    apostrophe forms in the set exist for readability/documentation of the
    source list, not because they can literally match."""
    return {token for token in normalized_text.split() if token not in STOPWORDS}


def collision_check_stopword_filtered(text: str, references: Iterable[tuple[str, str]]) -> dict[str, Any]:
    """Identical to collision_check in every respect -- exact-match,
    normalized-containment, and character-5-gram Jaccard all reuse the exact
    same code paths against the exact same normalized text -- except the
    token-Jaccard comparison strips STOPWORDS from both sides before scoring.
    Thresholds (TOKEN_JACCARD_THRESHOLD, CHAR_5GRAM_JACCARD_THRESHOLD) are
    unchanged; only what counts as a "token" changes."""
    normalized = normalize_for_collision(text)
    tokens = _stopword_filtered_tokens(normalized)
    grams = char_5grams(text)
    reasons: list[str] = []
    structured_reasons: list[dict[str, Any]] = []
    max_token = (0.0, None)
    max_char = (0.0, None)
    for label, reference in references:
        normalized_ref = normalize_for_collision(reference)
        if not normalized or not normalized_ref:
            continue
        token_score = jaccard(tokens, _stopword_filtered_tokens(normalized_ref))
        char_score = jaccard(grams, char_5grams(reference))
        if token_score > max_token[0]:
            max_token = (token_score, label)
        if char_score > max_char[0]:
            max_char = (char_score, label)
        shorter = min(len(normalized), len(normalized_ref))
        if normalized == normalized_ref:
            reasons.append(f"normalized exact match with {label}")
            structured_reasons.append({"kind": "normalized_exact_match", "reference": label, "score": None})
        elif shorter >= CONTAINMENT_MIN_NORMALIZED_CHARS and (normalized in normalized_ref or normalized_ref in normalized):
            reasons.append(f"normalized containment with {label}")
            structured_reasons.append({"kind": "normalized_containment", "reference": label, "score": None})
        if token_score >= TOKEN_JACCARD_THRESHOLD:
            reasons.append(f"token Jaccard {token_score:.6f} with {label}")
            structured_reasons.append({"kind": "token_jaccard_threshold", "reference": label, "score": round(token_score, 6)})
        if char_score >= CHAR_5GRAM_JACCARD_THRESHOLD:
            reasons.append(f"character-5-gram Jaccard {char_score:.6f} with {label}")
            structured_reasons.append({"kind": "character_5gram_jaccard_threshold", "reference": label, "score": round(char_score, 6)})
    return {
        "fatal": bool(reasons),
        "reasons": reasons,
        "structured_reasons": structured_reasons,
        "maximum_token_jaccard": {"score": round(max_token[0], 9), "reference": max_token[1]},
        "maximum_character_5gram_jaccard": {"score": round(max_char[0], 9), "reference": max_char[1]},
    }


def screen_candidate_stopword_filtered(
    candidate: dict[str, Any],
    quarantine_references: list[tuple[str, str]],
    earlier_candidate_references: list[tuple[str, str]],
    prompt_texts: list[tuple[str, str]],
) -> dict[str, Any]:
    """Identical to screen_candidate except every collision_check call is
    collision_check_stopword_filtered instead. qualitative_similarity (the
    non-fatal below-threshold diagnostic) is intentionally left untouched --
    it does not drive any rejection decision."""
    fields = candidate_fields(candidate)
    results = []
    fatal_reasons: list[str] = []
    for field_name, text in fields:
        protected = collision_check_stopword_filtered(text, quarantine_references)
        earlier = collision_check_stopword_filtered(text, earlier_candidate_references)
        prompt = collision_check_stopword_filtered(text, prompt_texts)
        if protected["fatal"]:
            fatal_reasons.append(f"{field_name}:protected_collision")
        if earlier["fatal"]:
            fatal_reasons.append(f"{field_name}:pilot_duplicate")
        if prompt["fatal"]:
            fatal_reasons.append(f"{field_name}:prompt_imitation")
        diagnostic_hits = []
        for reference_name, reference in quarantine_references:
            diagnostics = qualitative_similarity(text, reference)
            if any(value for value in diagnostics.values()):
                diagnostic_hits.append({"reference": reference_name, **diagnostics})
        results.append({
            "field": field_name,
            "protected": protected,
            "earlier_candidates": earlier,
            "prompt_imitation": prompt,
            "below_threshold_qualitative_hits": diagnostic_hits,
        })
    return {"fatal": bool(fatal_reasons), "fatal_reasons": fatal_reasons, "fields": results}
# --- end V11-only additions --------------------------------------------------


# --- V12-only additions below this line -------------------------------------
# Purely additive, same discipline as the V11 block above: nothing above this
# comment is modified, and nothing V6-V11 calls these. V11's own
# collision_check_stopword_filtered/screen_candidate_stopword_filtered stay
# completely frozen -- they already ran for real and were reviewed as-is.
#
# The one isolated variable this adds: character-5-gram Jaccard is now scored
# over stopword-filtered text too, using the same fixed STOPWORDS list and the
# same unchanged CHAR_5GRAM_JACCARD_THRESHOLD. Real V11 production data showed
# the identical fan-out signature that justified fixing token-Jaccard in the
# first place -- one real candidate matched 28 different, unrelated reference
# records simultaneously, all clustered at 0.102-0.109, just over the 0.10
# threshold -- consistent with common short words inflating character-level
# n-gram overlap the same way they inflated word-level overlap.
#
# Word order must be preserved (not just filtered into a set) for this to be
# meaningful: character 5-grams span word boundaries, so which stopwords are
# removed and where changes which 5-grams exist, not just which words remain.
# A set has no reproducible iteration order (Python hash randomization), so
# rebuilding filtered text from a set here would make char_5grams_stopword_
# filtered() nondeterministic across runs -- a real, considered distinction
# from _stopword_filtered_tokens() above, which only ever feeds Jaccard set
# arithmetic and never reconstructs ordered text.
def _stopword_filtered_normalized_text_ordered(normalized_text: str) -> str:
    return " ".join(token for token in normalized_text.split() if token not in STOPWORDS)


def char_5grams_stopword_filtered(text: str) -> set[str]:
    filtered = _stopword_filtered_normalized_text_ordered(normalize_for_collision(text)).replace(" ", "")
    if not filtered:
        return set()
    if len(filtered) < 5:
        return {filtered}
    return {filtered[index:index + 5] for index in range(len(filtered) - 4)}


def collision_check_fully_stopword_filtered(text: str, references: Iterable[tuple[str, str]]) -> dict[str, Any]:
    """Identical to collision_check_stopword_filtered in every respect --
    token-Jaccard scoring, exact-match detection, and normalized-containment
    detection are all unchanged from it -- except character-5-gram Jaccard is
    now also computed over stopword-filtered text instead of the full
    normalized text. Thresholds are unchanged; only what counts as
    comparable character content changes, mirroring the token-Jaccard fix
    exactly."""
    normalized = normalize_for_collision(text)
    tokens = _stopword_filtered_tokens(normalized)
    grams = char_5grams_stopword_filtered(text)
    reasons: list[str] = []
    structured_reasons: list[dict[str, Any]] = []
    max_token = (0.0, None)
    max_char = (0.0, None)
    for label, reference in references:
        normalized_ref = normalize_for_collision(reference)
        if not normalized or not normalized_ref:
            continue
        token_score = jaccard(tokens, _stopword_filtered_tokens(normalized_ref))
        char_score = jaccard(grams, char_5grams_stopword_filtered(reference))
        if token_score > max_token[0]:
            max_token = (token_score, label)
        if char_score > max_char[0]:
            max_char = (char_score, label)
        shorter = min(len(normalized), len(normalized_ref))
        if normalized == normalized_ref:
            reasons.append(f"normalized exact match with {label}")
            structured_reasons.append({"kind": "normalized_exact_match", "reference": label, "score": None})
        elif shorter >= CONTAINMENT_MIN_NORMALIZED_CHARS and (normalized in normalized_ref or normalized_ref in normalized):
            reasons.append(f"normalized containment with {label}")
            structured_reasons.append({"kind": "normalized_containment", "reference": label, "score": None})
        if token_score >= TOKEN_JACCARD_THRESHOLD:
            reasons.append(f"token Jaccard {token_score:.6f} with {label}")
            structured_reasons.append({"kind": "token_jaccard_threshold", "reference": label, "score": round(token_score, 6)})
        if char_score >= CHAR_5GRAM_JACCARD_THRESHOLD:
            reasons.append(f"character-5-gram Jaccard {char_score:.6f} with {label}")
            structured_reasons.append({"kind": "character_5gram_jaccard_threshold", "reference": label, "score": round(char_score, 6)})
    return {
        "fatal": bool(reasons),
        "reasons": reasons,
        "structured_reasons": structured_reasons,
        "maximum_token_jaccard": {"score": round(max_token[0], 9), "reference": max_token[1]},
        "maximum_character_5gram_jaccard": {"score": round(max_char[0], 9), "reference": max_char[1]},
    }


def screen_candidate_fully_stopword_filtered(
    candidate: dict[str, Any],
    quarantine_references: list[tuple[str, str]],
    earlier_candidate_references: list[tuple[str, str]],
    prompt_texts: list[tuple[str, str]],
) -> dict[str, Any]:
    """Identical to screen_candidate_stopword_filtered except every
    collision_check call is collision_check_fully_stopword_filtered
    instead. qualitative_similarity is intentionally left untouched, same
    reasoning as V11: it does not drive any rejection decision."""
    fields = candidate_fields(candidate)
    results = []
    fatal_reasons: list[str] = []
    for field_name, text in fields:
        protected = collision_check_fully_stopword_filtered(text, quarantine_references)
        earlier = collision_check_fully_stopword_filtered(text, earlier_candidate_references)
        prompt = collision_check_fully_stopword_filtered(text, prompt_texts)
        if protected["fatal"]:
            fatal_reasons.append(f"{field_name}:protected_collision")
        if earlier["fatal"]:
            fatal_reasons.append(f"{field_name}:pilot_duplicate")
        if prompt["fatal"]:
            fatal_reasons.append(f"{field_name}:prompt_imitation")
        diagnostic_hits = []
        for reference_name, reference in quarantine_references:
            diagnostics = qualitative_similarity(text, reference)
            if any(value for value in diagnostics.values()):
                diagnostic_hits.append({"reference": reference_name, **diagnostics})
        results.append({
            "field": field_name,
            "protected": protected,
            "earlier_candidates": earlier,
            "prompt_imitation": prompt,
            "below_threshold_qualitative_hits": diagnostic_hits,
        })
    return {"fatal": bool(fatal_reasons), "fatal_reasons": fatal_reasons, "fields": results}
# --- end V12-only additions --------------------------------------------------


# --- V13-only additions below this line -------------------------------------
# Purely additive, same discipline as V11/V12 above: nothing above this
# comment is modified, and nothing V6-V12 calls this. Collision screening
# behavior (what gets accepted or rejected) is completely untouched -- this
# adds a way to *measure* a real production candidate's text length for
# real-money-spend evidence rows, it does not change any accept/reject
# decision.
#
# Motivation (from the retrospective corpus audit, 2026-08-18): V12 r2's real
# production data showed one real collision (M07) matching 19 distinct
# reference records at 22 identical char-5-gram scores -- a signature that's
# consistent with either genuine corpus repetition or the short-string
# Jaccard effect already proven twice in this project's own regression tests
# (V11's token side, V12's char-5-gram side: removing a stopword shrinks the
# union without shrinking the intersection, which can raise similarity for
# short strings). Aggregate scores alone can't distinguish the two
# explanations. Recording how long the compared text actually was --
# reusing the exact same normalization and stopword-filtering primitives the
# real scoring already runs, not a new metric -- lets that question be
# answered directly from real future collision evidence, with zero raw text
# ever persisted: only two small non-negative integers.
def field_length_metadata(text: str) -> dict[str, int]:
    """Length metadata for one piece of text, computed the same way the real
    collision scoring already sees it: `normalized_char_length` is the
    character count of `normalize_for_collision(text)` with spaces removed
    (the same string `char_5grams`/`char_5grams_stopword_filtered` windows
    over), and `stopword_filtered_token_count` is the size of the same
    stopword-filtered token set `_stopword_filtered_tokens` already produces
    for token-Jaccard scoring. Both are plain non-negative integers -- no
    text, no substring, nothing reversible to the source content."""
    normalized = normalize_for_collision(text)
    return {
        "normalized_char_length": len(normalized.replace(" ", "")),
        "stopword_filtered_token_count": len(_stopword_filtered_tokens(normalized)),
    }
# --- end V13-only additions --------------------------------------------------


def load_cards() -> dict[str, str]:
    value = load_json(CARDS_PATH)
    if not isinstance(value, dict) or set(value) != {"artifact", "cards"} or value["artifact"] != "gemini_generator_mechanism_cards":
        raise Gate2Error("invalid mechanism-card manifest")
    cards = value["cards"]
    if not isinstance(cards, list) or len(cards) != 12:
        raise Gate2Error("exactly twelve mechanism cards are required")
    result: dict[str, str] = {}
    for card in cards:
        if not isinstance(card, dict) or set(card) != {"id", "text"}:
            raise Gate2Error("malformed mechanism card")
        if not CARD_ID_RE.fullmatch(card["id"]) or not isinstance(card["text"], str) or not card["text"].strip():
            raise Gate2Error("invalid mechanism card ID or text")
        if "{{" in card["text"] or "}}" in card["text"] or card["id"] in result:
            raise Gate2Error("duplicate card or unescaped placeholder")
        result[card["id"]] = card["text"]
    if tuple(result) != tuple(f"M{i:02d}" for i in range(1, 13)):
        raise Gate2Error("mechanism cards must be ordered M01 through M12")
    return result


def render_messages(mechanism_id: str, mechanism_card: str | None = None) -> tuple[str, str]:
    cards = load_cards()
    if mechanism_id not in cards:
        raise Gate2Error(f"unknown mechanism ID: {mechanism_id}")
    if mechanism_card is not None and mechanism_card != cards[mechanism_id]:
        raise Gate2Error(f"altered mechanism card: {mechanism_id}")
    system = canonical_file(SYSTEM_PATH)[0].decode("utf-8")
    template = canonical_file(USER_TEMPLATE_PATH)[0].decode("utf-8")
    if template.count("{{MECHANISM_ID}}") != 1 or template.count("{{MECHANISM_CARD}}") != 1:
        raise Gate2Error("user template placeholders are not exact singletons")
    user = template.replace("{{MECHANISM_ID}}", mechanism_id).replace("{{MECHANISM_CARD}}", cards[mechanism_id])
    if "{{" in user or "}}" in user or "\r" in system or "\r" in user:
        raise Gate2Error("unescaped placeholder or noncanonical newline")
    return system, user


def build_schedule(references: list[tuple[str, str]]) -> dict[str, Any]:
    cards = load_cards()
    slots = []
    for card_number, (mechanism_id, mechanism_card) in enumerate(cards.items(), 1):
        ordered_models = MODELS if card_number % 2 else tuple(reversed(MODELS))
        for model in ordered_models:
            system, user = render_messages(mechanism_id, mechanism_card)
            prompt_payload = {"system_instruction": system, "user_message": user}
            prompt_hash = sha256_bytes(canonical_json_bytes(prompt_payload))
            preflight = collision_check(system + "\n" + user, references)
            slots.append({
                "slot": len(slots) + 1,
                "model": model,
                "mechanism_id": mechanism_id,
                "prompt_hash": prompt_hash,
                "prompt_collision_preflight": preflight,
            })
    if len(slots) != 24 or any(sum(s["model"] == model for s in slots) != 12 for model in MODELS):
        raise Gate2Error("schedule cardinality failure")
    if any(slot["prompt_collision_preflight"]["fatal"] for slot in slots):
        raise Gate2Error("rendered prompt collided with quarantine pool")
    manifest = {
        "artifact": "gemini_generator_schedule",
        "algorithm": "cards M01-M12; odd cards capability-first, even cards efficiency-first",
        "slot_count": 24,
        "model_counts": {model: 12 for model in MODELS},
        "slots": slots,
    }
    manifest["manifest_sha256"] = sha256_bytes(canonical_json_bytes(manifest))
    return manifest


def _validate_plain_string(value: Any, path: str, structured_reason: dict[str, Any] | None = None) -> str:
    if not isinstance(value, str) or not value.strip():
        error = ResponseSchemaError(f"{path}: nonblank string required", structured_reason) if structured_reason else Gate2Error(f"{path}: nonblank string required")
        raise error
    if any(unicodedata.category(ch) == "Cc" for ch in value):
        error = ResponseSchemaError(f"{path}: control characters are forbidden", structured_reason) if structured_reason else Gate2Error(f"{path}: control characters are forbidden")
        raise error
    return value


def parse_response(raw: bytes | str) -> dict[str, Any]:
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ResponseSchemaError("response BOM is forbidden", {"kind": "response_json_invalid"})
    try:
        text = raw.decode("utf-8")
        value = json.loads(text, object_pairs_hook=reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError, Gate2Error) as exc:
        raise ResponseSchemaError("invalid response JSON: " + str(exc), {"kind": "response_json_invalid"}) from exc
    if not isinstance(value, dict) or set(value) != {"source_input", "proposed_output"}:
        keys = set(value) if isinstance(value, dict) else set()
        raise ResponseSchemaError("response has missing or extra top-level keys", {
            "kind": "top_level_keys_invalid",
            "has_source_input": "source_input" in keys,
            "has_proposed_output": "proposed_output" in keys,
            "extra_key_count": len(keys - {"source_input", "proposed_output"}),
        })
    source = _validate_plain_string(value["source_input"], "source_input", {"kind": "source_input_not_plain_string"})
    word_count = len(WORD_RE.findall(source))
    if not 80 <= word_count <= 220:
        raise ResponseSchemaError(f"source_input word count {word_count} is outside 80..220", {"kind": "source_input_word_count_out_of_range", "actual_count": word_count, "min_allowed": 80, "max_allowed": 220})
    output = value["proposed_output"]
    if not isinstance(output, dict) or set(output) != {"narrative", "bullets", "action_items"}:
        keys = set(output) if isinstance(output, dict) else set()
        raise ResponseSchemaError("proposed_output has missing or extra keys", {
            "kind": "proposed_output_keys_invalid",
            "has_narrative": "narrative" in keys,
            "has_bullets": "bullets" in keys,
            "has_action_items": "action_items" in keys,
            "extra_key_count": len(keys - {"narrative", "bullets", "action_items"}),
        })
    narrative = _validate_plain_string(output["narrative"], "proposed_output.narrative", {"kind": "narrative_not_plain_string"})
    sentence_count = len(SENTENCE_RE.findall(narrative))
    if not 1 <= sentence_count <= 4:
        raise ResponseSchemaError(f"narrative sentence count {sentence_count} is outside 1..4", {"kind": "narrative_sentence_count_out_of_range", "actual_count": sentence_count, "min_allowed": 1, "max_allowed": 4})
    for key, minimum, maximum in (("bullets", 2, 8), ("action_items", 1, 6)):
        items = output[key]
        if not isinstance(items, list):
            raise ResponseSchemaError(f"proposed_output.{key} item count is outside {minimum}..{maximum}", {"kind": "list_not_array", "field": key})
        if not minimum <= len(items) <= maximum:
            raise ResponseSchemaError(f"proposed_output.{key} item count is outside {minimum}..{maximum}", {"kind": "list_item_count_out_of_range", "field": key, "actual_count": len(items), "min_allowed": minimum, "max_allowed": maximum})
        for index, item in enumerate(items):
            _validate_plain_string(item, f"proposed_output.{key}[{index}]", {"kind": "list_item_not_plain_string", "field": key, "index": index})
    return value


def calculate_cost(model: str, input_tokens: int, visible_output_tokens: int, thinking_tokens: int, rates: dict[str, Any]) -> int:
    if model not in MODELS or any(type(v) is not int or v < 0 for v in (input_tokens, visible_output_tokens, thinking_tokens)):
        raise Gate2Error("invalid model or token count")
    if input_tokens > MAX_INPUT_TOKENS or visible_output_tokens + thinking_tokens > MAX_OUTPUT_TOKENS:
        raise Gate2Error("token ceiling exceeded")
    model_rates = rates.get("rates", {}).get(model)
    if not isinstance(model_rates, dict) or set(model_rates) != {"input", "output_including_thinking"}:
        raise Gate2Error("missing or malformed execution-day rate")
    input_cost = (input_tokens * model_rates["input"] + 999_999) // 1_000_000
    output_tokens = visible_output_tokens + thinking_tokens
    output_cost = (output_tokens * model_rates["output_including_thinking"] + 999_999) // 1_000_000
    return input_cost + output_cost


def reservation_cost(model: str, rates: dict[str, Any]) -> int:
    return calculate_cost(model, MAX_INPUT_TOKENS, MAX_OUTPUT_TOKENS, 0, rates)


def redact_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: "[REDACTED]" if SECRET_KEY_RE.search(str(key)) else redact_secrets(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    if isinstance(value, str):
        return GOOGLE_KEY_RE.sub("[REDACTED]", BEARER_RE.sub("Bearer [REDACTED]", value))
    return value


def contains_secret(value: Any) -> bool:
    serialized = json.dumps(value, ensure_ascii=False)
    return bool(GOOGLE_KEY_RE.search(serialized) or re.search(r"(?i)bearer\s+(?!\[REDACTED\])\S+", serialized))


def request_body(slot: dict[str, Any]) -> dict[str, Any]:
    system, user = render_messages(slot["mechanism_id"])
    provider_body = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generation_config": {
            "response_mime_type": "application/json",
            "response_schema": load_json(SCHEMA_PATH),
            "candidate_count": 1,
            "thinking_level": "minimal",
            "max_output_tokens": MAX_OUTPUT_TOKENS,
        },
    }
    contract = load_json(PROVIDER_CONTRACT_PATH)
    body = {
        "method": contract["method"],
        "endpoint_template": contract["endpoint_template"],
        "model": slot["model"],
        "content_type": contract["content_type"],
        "body": provider_body,
        "stream": False,
        "timeout_seconds": 60,
    }
    forbidden = {"tools", "grounding", "retrieval", "cached_content", "temperature", "top_p", "top_k"}
    if forbidden & set(body) or forbidden & set(provider_body) or forbidden & set(provider_body["generation_config"]):
        raise Gate2Error("forbidden request control present")
    if contains_secret(body):
        raise Gate2Error("secret exposure in request body")
    return body


@dataclass(frozen=True)
class MockTransport:
    fixture: str = "provider_blocked"

    def send(self, body: dict[str, Any]) -> dict[str, Any]:
        if self.fixture != "provider_blocked":
            raise Gate2Error("unknown mock fixture")
        fixtures = load_json(PACKAGE / "mock_provider_fixtures.json")["fixtures"]
        fixture = next((item for item in fixtures if item.get("id") == self.fixture), None)
        if not isinstance(fixture, dict):
            raise Gate2Error("mock fixture is missing")
        result = {key: value for key, value in fixture.items() if key != "id"}
        result.update({"mock": True, "model": body["model"]})
        return result


@contextmanager
def zero_network_guard(counter: dict[str, int]):
    original_socket = socket.socket
    original_create_connection = socket.create_connection

    def blocked(*_args: Any, **_kwargs: Any) -> Any:
        counter["attempts"] += 1
        raise Gate2Error("network access blocked by Gate 2 guard")

    socket.socket = blocked  # type: ignore[assignment]
    socket.create_connection = blocked  # type: ignore[assignment]
    try:
        yield
    finally:
        socket.socket = original_socket  # type: ignore[assignment]
        socket.create_connection = original_create_connection  # type: ignore[assignment]


def chained_row(payload: dict[str, Any], prior_hash: str | None) -> dict[str, Any]:
    row = dict(payload)
    row["prior_row_hash"] = prior_hash
    row["row_hash"] = sha256_bytes(canonical_json_bytes(row))
    return row


def verify_chain(rows: list[dict[str, Any]]) -> None:
    prior = None
    for sequence, row in enumerate(rows, 1):
        if row.get("sequence") != sequence or row.get("prior_row_hash") != prior:
            raise Gate2Error("append-only chain sequence or prior hash mismatch")
        stored = row.get("row_hash")
        payload = {key: value for key, value in row.items() if key != "row_hash"}
        if stored != sha256_bytes(canonical_json_bytes(payload)):
            raise Gate2Error("append-only chain row hash mismatch")
        prior = stored


def validate_review(review: dict[str, Any]) -> None:
    if set(review) != {"artifact", "candidate_hash", "reviewer", "dimensions", "final_verdict", "sealed_payload_hash"}:
        raise Gate2Error("sealed review keys are invalid")
    if review["artifact"] != "gemini_generator_sealed_review" or review["reviewer"] not in {"chatgpt", "claude"}:
        raise Gate2Error("sealed review artifact or reviewer is invalid")
    if not HEX64_RE.fullmatch(review["candidate_hash"]):
        raise Gate2Error("candidate hash is invalid")
    dimensions = review["dimensions"]
    if not isinstance(dimensions, dict) or tuple(dimensions) != DIMENSIONS:
        raise Gate2Error("sealed review dimensions or order are invalid")
    for name, dimension in dimensions.items():
        if not isinstance(dimension, dict) or set(dimension) != {"verdict", "rationale"}:
            raise Gate2Error(f"{name}: invalid review dimension")
        if dimension["verdict"] not in {"pass", "fail", "not_applicable"} or not isinstance(dimension["rationale"], str) or not dimension["rationale"].strip():
            raise Gate2Error(f"{name}: invalid verdict or rationale")
    if review["final_verdict"] not in {"accept", "reject", "escalate"}:
        raise Gate2Error("invalid final verdict")
    if review["final_verdict"] == "accept" and any(v["verdict"] == "fail" for v in dimensions.values()):
        raise Gate2Error("accept cannot contain a failed dimension")
    payload = {key: value for key, value in review.items() if key != "sealed_payload_hash"}
    if review["sealed_payload_hash"] != sha256_bytes(canonical_json_bytes(payload)):
        raise Gate2Error("sealed review hash mismatch")


def compare_reviews(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    validate_review(left)
    validate_review(right)
    if left["reviewer"] == right["reviewer"] or left["candidate_hash"] != right["candidate_hash"]:
        raise Gate2Error("reviews must be from different reviewers for the same candidate")
    disagreements = [name for name in DIMENSIONS if left["dimensions"][name]["verdict"] != right["dimensions"][name]["verdict"]]
    final_agreement = left["final_verdict"] == right["final_verdict"]
    return {
        "candidate_hash": left["candidate_hash"],
        "categorical_dimension_disagreements": disagreements,
        "final_verdict_agreement": final_agreement,
        "candidate_pool_eligible": not disagreements and final_agreement and left["final_verdict"] == "accept",
        "rationale_conflict_requires_human_check": True,
        "no_corpus_mutation": True,
    }


def build_artifacts() -> dict[str, Any]:
    quarantine, references = build_quarantine()
    schedule = build_schedule(references)
    write_canonical_json(PACKAGE / "quarantine_manifest.json", quarantine)
    write_canonical_json(PACKAGE / "schedule.json", schedule)
    artifact_files = [
        SYSTEM_PATH, USER_TEMPLATE_PATH, SCHEMA_PATH, CARDS_PATH, RATE_PATH, PROVIDER_CONTRACT_PATH,
        PACKAGE / "request_receipt_schema.json", PACKAGE / "rejection_ledger_schema.json",
        PACKAGE / "cost_ledger_schema.json", PACKAGE / "sealed_review_schema.json",
        PACKAGE / "setup_attestation_template.json", PACKAGE / "collision_fixtures.json",
        PACKAGE / "response_parser_fixtures.json", PACKAGE / "cost_boundary_fixtures.json",
        PACKAGE / "mock_provider_fixtures.json", PACKAGE / "gate2.py", PACKAGE / "test_gate2.py",
        PACKAGE / "README.md",
        PACKAGE / "quarantine_manifest.json", PACKAGE / "schedule.json",
    ]
    artifacts = []
    for path in artifact_files:
        canonical, receipt = canonical_file(path)
        receipt["canonical_byte_count"] = len(canonical)
        artifacts.append(receipt)
    manifest = {
        "artifact": "gemini_generator_gate2_artifact_manifest",
        "status": "dummy_only_uncommitted_requires_independent_verification",
        "network_or_model_use_authorized": False,
        "artifacts": artifacts,
    }
    manifest["manifest_sha256"] = sha256_bytes(canonical_json_bytes(manifest))
    write_canonical_json(PACKAGE / "artifact_manifest.json", manifest)
    return manifest


def run_dummy() -> dict[str, Any]:
    build_artifacts()
    schedule = load_json(PACKAGE / "schedule.json")
    rates = load_json(RATE_PATH)
    receipts: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    cost_rows: list[dict[str, Any]] = []
    network = {"attempts": 0}
    prior_receipt = None
    prior_rejection = None
    prior_cost = None
    mock = MockTransport()
    with zero_network_guard(network):
        for slot in schedule["slots"]:
            reservation = reservation_cost(slot["model"], rates)
            if reservation > RECONCILIATION_STOP_USD_MILLIONTHS or reservation > PILOT_CEILING_USD_MILLIONTHS:
                raise Gate2Error("reservation exceeds a monetary boundary")
            body = request_body(slot)
            request_hash = sha256_bytes(canonical_json_bytes(body))
            response = redact_secrets(mock.send(body))
            if contains_secret(response) or response["network_used"]:
                raise Gate2Error("mock response leaked a secret or used network")
            raw_hash = sha256_bytes(response["raw_response"].encode("utf-8"))
            receipt = chained_row({
                "artifact": "gemini_generator_request_receipt",
                "sequence": len(receipts) + 1,
                "schedule_slot": slot["slot"],
                "model": slot["model"],
                "mechanism_id": slot["mechanism_id"],
                "request_hash": request_hash,
                "prompt_hash": slot["prompt_hash"],
                "schema_hash": sha256_bytes(canonical_file(SCHEMA_PATH)[0]),
                "transport": "mock",
                "network_used": False,
                "disposition": "rejected",
                "no_corpus_mutation": True,
            }, prior_receipt)
            receipts.append(receipt)
            prior_receipt = receipt["row_hash"]
            rejection = chained_row({
                "artifact": "gemini_generator_rejection_ledger_row",
                "sequence": len(rejections) + 1,
                "request_hash": request_hash,
                "raw_response_hash": raw_hash,
                "reason_code": "provider_blocked",
                "disposition": "rejected",
                "no_corpus_mutation": True,
            }, prior_rejection)
            rejections.append(rejection)
            prior_rejection = rejection["row_hash"]
            rate_hash = sha256_bytes(canonical_file(RATE_PATH)[0])
            cost_row = chained_row({
                "artifact": "gemini_generator_cost_ledger_row",
                "sequence": len(cost_rows) + 1,
                "schedule_slot": slot["slot"],
                "model": slot["model"],
                "mechanism_id": slot["mechanism_id"],
                "rate_snapshot_hash": rate_hash,
                "max_input_tokens": MAX_INPUT_TOKENS,
                "max_output_tokens": MAX_OUTPUT_TOKENS,
                "reserved_usd_millionths": reservation,
                "usage": {
                    "input_tokens": 0, "visible_output_tokens": 0, "thinking_tokens": 0,
                    "cached_tokens": 0, "tool_use_tokens": 0, "total_tokens": 0,
                },
                "actual_usd_millionths": 0,
                "cumulative_actual_usd_millionths": 0,
                "outstanding_reservations_usd_millionths": 0,
                "remaining_reconciliation_authority_usd_millionths": RECONCILIATION_STOP_USD_MILLIONTHS,
                "request_hash": request_hash,
                "response_hash": raw_hash,
                "receipt_hash": receipt["row_hash"],
                "disposition": "rejected",
                "stop_or_retry_reason": "provider_blocked_mock_no_retry",
            }, prior_cost)
            cost_rows.append(cost_row)
            prior_cost = cost_row["row_hash"]
    verify_chain(receipts)
    verify_chain(rejections)
    verify_chain(cost_rows)
    (PACKAGE / "dummy_request_receipts.jsonl").write_bytes(b"".join(canonical_json_bytes(row) for row in receipts))
    (PACKAGE / "dummy_rejection_ledger.jsonl").write_bytes(b"".join(canonical_json_bytes(row) for row in rejections))
    (PACKAGE / "dummy_cost_ledger.jsonl").write_bytes(b"".join(canonical_json_bytes(row) for row in cost_rows))
    receipt = {
        "artifact": "gemini_generator_gate2_dummy_dry_run_receipt",
        "status": "pass",
        "schedule_slots_exercised": len(receipts),
        "mock_provider_blocked_results": len(rejections),
        "network_guard_installed": True,
        "network_attempt_count": network["attempts"],
        "network_used": False,
        "api_key_required_or_read": False,
        "provider_sdk_present_or_used": False,
        "model_calls": 0,
        "spend_usd_millionths": 0,
        "candidate_review_performed": False,
        "corpus_mutation_performed": False,
        "request_receipt_count": len(receipts),
        "rejection_ledger_count": len(rejections),
        "cost_ledger_count": len(cost_rows),
        "request_receipt_chain_head": receipts[-1]["row_hash"],
        "rejection_ledger_chain_head": rejections[-1]["row_hash"],
        "cost_ledger_chain_head": cost_rows[-1]["row_hash"],
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(receipt))
    write_canonical_json(PACKAGE / "dummy_dry_run_receipt.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build", help="build frozen local manifests")
    sub.add_parser("dummy-run", help="exercise all 24 slots using only the built-in mock transport")
    compare = sub.add_parser("compare-reviews", help="validate and compare two sealed-review JSON files")
    compare.add_argument("left", type=Path)
    compare.add_argument("right", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        result = build_artifacts()
    elif args.command == "dummy-run":
        result = run_dummy()
    else:
        result = compare_reviews(load_json(args.left), load_json(args.right))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
