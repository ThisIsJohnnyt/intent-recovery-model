"""Retrospective, read-only audit of the pre-Gemini, ChatGPT-era corpus.

Context: every real Gemini candidate this project has screened (V6-V12) has
gone through schema-conformance checking, collision/near-duplicate detection,
and secret-exposure scanning before being allowed anywhere near the gold
corpus. The corpus content it's being screened *against* -- and the bulk
training pool the model actually trains on -- has never been run through that
same rigor. Johnny asked, correctly, whether that gap itself is worth closing
before deciding anything about the corpus's future. This script closes it.

Two targets, both real, already-committed corpus content:
  A) datasets/synthetic.jsonl              -- 72 records, the bulk ChatGPT-
                                               sourced pool `prepare_data.py`
                                               actually trains on.
  B) gate2.py's four pinned quarantine pools (comparator/protected/
     acceptance/treatment_delta, 111 records / 1007 flattened fields total)
     -- what every Gemini candidate is checked for duplication against.

Five checks, mirroring what Gemini candidates already go through:
  1. Schema conformance against the real training contract (DATASET_SPEC.md)
     *and* against response_schema.json's stricter bounds, since those two
     already disagree on action_items and that disagreement is itself a
     finding worth surfacing quantitatively.
  2. Internal near-duplicate audit across all ~1,650 combined text fields,
     using V12's most-refined collision logic (collision_check_fully_
     stopword_filtered's underlying primitives) -- the same rigor a live
     Gemini candidate would be held to today.
  3. Secret/PII exposure scan, using the exact regexes that hard-stop a live
     paid run.
  4. Field/output-key bounds audit (folded into check 1).
  5. Statistical diversity pass (category/difficulty/length distributions).

Zero cost, zero network, zero API calls, zero corpus mutation. This script
only reads files that already exist and writes two report files next to it.
Findings-only: it does not fix, gate, flag records for remediation, or open
any follow-up work by itself.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path
from typing import Any

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[1]
sys.path.insert(0, str(PACKAGE))
import gate2  # noqa: E402

SYNTHETIC_PATH = ROOT / "datasets" / "synthetic.jsonl"

# DATASET_SPEC.md: "bullets ... up to 7 ... source-determined count".
DATASET_SPEC_BULLETS_MAX = 7
# response_schema.json (the live Gemini structured-output contract).
SCHEMA_BULLETS_MIN = 2
SCHEMA_BULLETS_MAX = 8
SCHEMA_ACTIONS_MIN = 1
SCHEMA_ACTIONS_MAX = 6

OUTPUT_BEARING_POOLS = ("comparator", "treatment_delta")
BENCHMARK_STYLE_POOLS = ("protected", "acceptance")


def load_synthetic() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with SYNTHETIC_PATH.open("r", encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line, object_pairs_hook=gate2.reject_duplicate_keys)
            if not isinstance(row, dict):
                raise gate2.Gate2Error(f"synthetic.jsonl:{lineno}: row must be an object")
            rows.append(row)
    return rows


def load_pool_rows(pool: str) -> list[dict[str, Any]]:
    pin = gate2.QUARANTINE_INPUTS[pool]
    rows, _receipt = gate2.load_jsonl(ROOT / pin["path"], pin["count"], pin["canonical_lf_sha256"])
    return rows


def flatten_output_fields(label: str, row: dict[str, Any]) -> list[tuple[str, str]]:
    fields: list[tuple[str, str]] = []
    input_text = row.get("input")
    if isinstance(input_text, str) and input_text.strip():
        fields.append((f"{label}:input", input_text))
    output = row.get("output")
    if isinstance(output, dict):
        narrative = output.get("narrative")
        if isinstance(narrative, str) and narrative.strip():
            fields.append((f"{label}:output.narrative", narrative))
        for i, text in enumerate(output.get("bullets") or [], 1):
            if isinstance(text, str) and text.strip():
                fields.append((f"{label}:output.bullets:{i:02d}", text))
        for i, text in enumerate(output.get("action_items") or [], 1):
            if isinstance(text, str) and text.strip():
                fields.append((f"{label}:output.action_items:{i:02d}", text))
    return fields


# --- Check 1 + 4: schema conformance / bounds --------------------------------

def check_schema_conformance(label: str, row: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    input_text = row.get("input")
    if not isinstance(input_text, str) or not input_text.strip():
        findings.append({"locator": label, "issue": "input_missing_or_blank"})

    output = row.get("output")
    if not isinstance(output, dict):
        findings.append({"locator": label, "issue": "missing_or_malformed_output"})
        return findings

    extra_keys = sorted(set(output) - {"narrative", "bullets", "action_items"})
    missing_keys = sorted({"narrative", "bullets", "action_items"} - set(output))
    if extra_keys:
        findings.append({"locator": label, "issue": "extra_output_keys", "detail": extra_keys})
    if missing_keys:
        findings.append({"locator": label, "issue": "missing_output_keys", "detail": missing_keys})

    narrative = output.get("narrative")
    if not isinstance(narrative, str) or not narrative.strip():
        findings.append({"locator": label, "issue": "narrative_missing_or_blank"})

    bullets = output.get("bullets")
    if not isinstance(bullets, list) or any(not isinstance(b, str) or not b.strip() for b in bullets):
        findings.append({"locator": label, "issue": "bullets_malformed_or_contains_blank"})
    else:
        if len(bullets) > DATASET_SPEC_BULLETS_MAX:
            findings.append({"locator": label, "issue": "bullets_exceeds_dataset_spec_max_7", "detail": len(bullets)})
        if len(bullets) < SCHEMA_BULLETS_MIN or len(bullets) > SCHEMA_BULLETS_MAX:
            findings.append({"locator": label, "issue": "bullets_outside_gemini_schema_bounds_2_to_8", "detail": len(bullets)})

    actions = output.get("action_items")
    if not isinstance(actions, list) or any(not isinstance(a, str) or not a.strip() for a in actions):
        findings.append({"locator": label, "issue": "action_items_malformed_or_contains_blank"})
    else:
        if len(actions) == 0:
            findings.append({"locator": label, "issue": "action_items_empty_conflicts_with_gemini_schema_minitems_1"})
        elif len(actions) > SCHEMA_ACTIONS_MAX:
            findings.append({"locator": label, "issue": "action_items_exceeds_gemini_schema_max_6", "detail": len(actions)})

    return findings


# --- Check 3: secret/PII exposure --------------------------------------------

def check_secrets(label: str, text: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if gate2.SECRET_KEY_RE.search(text):
        findings.append({"locator": label, "issue": "secret_keyword_pattern_match"})
    if gate2.BEARER_RE.search(text):
        findings.append({"locator": label, "issue": "bearer_token_pattern_match"})
    if gate2.GOOGLE_KEY_RE.search(text):
        findings.append({"locator": label, "issue": "google_api_key_pattern_match"})
    return findings


# --- Check 2: internal near-duplicate audit ----------------------------------

def record_prefix(label: str) -> str:
    parts = label.split(":")
    return ":".join(parts[:2])


def internal_duplicate_audit(all_fields: list[tuple[str, str]]) -> list[dict[str, Any]]:
    """Precomputes normalized/token/gram forms once per field (V12's exact
    primitives: stopword-filtered tokens for word-Jaccard, stopword-filtered
    ordered text for character-5-gram-Jaccard), then does one pairwise pass.
    Excludes same-record comparisons (a bullet vs. its own narrative is
    expected to overlap and isn't a cross-corpus duplication concern)."""
    precomputed = []
    for label, text in all_fields:
        normalized = gate2.normalize_for_collision(text)
        if not normalized:
            continue
        tokens = gate2._stopword_filtered_tokens(normalized)
        grams = gate2.char_5grams_stopword_filtered(text)
        precomputed.append((label, normalized, tokens, grams))

    hits: list[dict[str, Any]] = []
    n = len(precomputed)
    for i in range(n):
        label_a, norm_a, tokens_a, grams_a = precomputed[i]
        prefix_a = record_prefix(label_a)
        for j in range(i + 1, n):
            label_b, norm_b, tokens_b, grams_b = precomputed[j]
            if record_prefix(label_b) == prefix_a:
                continue
            shorter = min(len(norm_a), len(norm_b))
            if norm_a == norm_b:
                hits.append({"field_a": label_a, "field_b": label_b, "kind": "normalized_exact_match", "score": None})
                continue
            if shorter >= gate2.CONTAINMENT_MIN_NORMALIZED_CHARS and (norm_a in norm_b or norm_b in norm_a):
                hits.append({"field_a": label_a, "field_b": label_b, "kind": "normalized_containment", "score": None})
            token_score = gate2.jaccard(tokens_a, tokens_b)
            if token_score >= gate2.TOKEN_JACCARD_THRESHOLD:
                hits.append({"field_a": label_a, "field_b": label_b, "kind": "token_jaccard_threshold", "score": round(token_score, 6)})
            char_score = gate2.jaccard(grams_a, grams_b)
            if char_score >= gate2.CHAR_5GRAM_JACCARD_THRESHOLD:
                hits.append({"field_a": label_a, "field_b": label_b, "kind": "character_5gram_jaccard_threshold", "score": round(char_score, 6)})
    return hits


# --- Check 5: statistical diversity ------------------------------------------

def word_count(text: str) -> int:
    return len(gate2.WORD_RE.findall(text))


def diversity_stats_output_bearing(rows: list[dict[str, Any]]) -> dict[str, Any]:
    categories: dict[str, int] = {}
    difficulties: dict[str, int] = {}
    bullet_counts: list[int] = []
    action_counts: list[int] = []
    input_word_counts: list[int] = []
    for row in rows:
        categories[row.get("category", "<missing>")] = categories.get(row.get("category", "<missing>"), 0) + 1
        difficulties[row.get("difficulty", "<missing>")] = difficulties.get(row.get("difficulty", "<missing>"), 0) + 1
        output = row.get("output") if isinstance(row.get("output"), dict) else {}
        bullets = output.get("bullets") if isinstance(output.get("bullets"), list) else []
        actions = output.get("action_items") if isinstance(output.get("action_items"), list) else []
        bullet_counts.append(len(bullets))
        action_counts.append(len(actions))
        input_text = row.get("input")
        if isinstance(input_text, str):
            input_word_counts.append(word_count(input_text))

    def summarize(values: list[int]) -> dict[str, Any]:
        if not values:
            return {"count": 0}
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": round(statistics.mean(values), 2),
            "median": statistics.median(values),
        }

    return {
        "category_distribution": categories,
        "difficulty_distribution": difficulties,
        "bullet_count_distribution": summarize(bullet_counts),
        "action_item_count_distribution": summarize(action_counts),
        "input_word_count_distribution": summarize(input_word_counts),
    }


def diversity_stats_benchmark_style(rows: list[dict[str, Any]]) -> dict[str, Any]:
    categories: dict[str, int] = {}
    statuses: dict[str, int] = {}
    kinds: dict[str, int] = {}
    for row in rows:
        categories[row.get("category", "<missing>")] = categories.get(row.get("category", "<missing>"), 0) + 1
        statuses[row.get("status", "<missing>")] = statuses.get(row.get("status", "<missing>"), 0) + 1
        kinds[row.get("kind", "<missing>")] = kinds.get(row.get("kind", "<missing>"), 0) + 1
    return {"category_distribution": categories, "status_distribution": statuses, "kind_distribution": kinds}


# --- Orchestration ------------------------------------------------------------

def run_audit() -> dict[str, Any]:
    synthetic_rows = load_synthetic()
    synthetic_fields = []
    for idx, row in enumerate(synthetic_rows, 1):
        synthetic_fields.extend(flatten_output_fields(f"synthetic:{idx:03d}", row))

    manifest, pool_fields = gate2.build_quarantine()

    pool_rows = {pool: load_pool_rows(pool) for pool in gate2.QUARANTINE_INPUTS}

    # Check 1 + 4: schema conformance, output-bearing pools + synthetic.
    schema_findings: list[dict[str, Any]] = []
    for idx, row in enumerate(synthetic_rows, 1):
        schema_findings.extend(check_schema_conformance(f"synthetic:{idx:03d}", row))
    for pool in OUTPUT_BEARING_POOLS:
        for idx, row in enumerate(pool_rows[pool], 1):
            schema_findings.extend(check_schema_conformance(f"{pool}:{idx:03d}", row))

    schema_not_applicable = {
        pool: (
            f"{pool} pool rows are benchmark/probe artifacts (input + expected_behavior + "
            f"checks/notes, no output.narrative/bullets/action_items) -- a structurally "
            f"different artifact type than the training-data contract this check targets. "
            f"All {len(pool_rows[pool])} rows already passed gate2.build_quarantine()'s own "
            f"structural validation (well-formed JSON, non-blank input, hash-pin match) "
            f"just by loading successfully."
        )
        for pool in BENCHMARK_STYLE_POOLS
    }

    # Check 3: secret/PII scan across every field in both targets.
    secret_findings: list[dict[str, Any]] = []
    for label, text in synthetic_fields:
        secret_findings.extend(check_secrets(label, text))
    for label, text in pool_fields:
        secret_findings.extend(check_secrets(label, text))

    # Check 2: internal near-duplicate audit across the combined field set.
    combined_fields = synthetic_fields + pool_fields
    duplicate_hits = internal_duplicate_audit(combined_fields)

    # Check 5: diversity stats.
    diversity = {
        "synthetic": diversity_stats_output_bearing(synthetic_rows),
        "comparator": diversity_stats_output_bearing(pool_rows["comparator"]),
        "treatment_delta": diversity_stats_output_bearing(pool_rows["treatment_delta"]),
        "protected": diversity_stats_benchmark_style(pool_rows["protected"]),
        "acceptance": diversity_stats_benchmark_style(pool_rows["acceptance"]),
    }

    return {
        "artifact": "corpus_retro_audit_2026-08-18",
        "scope": {
            "synthetic_record_count": len(synthetic_rows),
            "synthetic_field_count": len(synthetic_fields),
            "pool_record_count": manifest["record_count"],
            "pool_field_count": manifest["screened_field_count"],
            "combined_field_count": len(combined_fields),
        },
        "schema_conformance_findings": schema_findings,
        "schema_conformance_not_applicable": schema_not_applicable,
        "secret_exposure_findings": secret_findings,
        "internal_near_duplicate_findings": duplicate_hits,
        "diversity_stats": diversity,
    }


def main() -> int:
    result = run_audit()
    json_path = PACKAGE / "corpus_retro_audit_2026-08-18_findings.json"
    json_path.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    print(f"wrote {json_path}")
    print(json.dumps(result["scope"], indent=2))
    print(f"schema findings: {len(result['schema_conformance_findings'])}")
    print(f"secret findings: {len(result['secret_exposure_findings'])}")
    print(f"internal near-duplicate findings: {len(result['internal_near_duplicate_findings'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
