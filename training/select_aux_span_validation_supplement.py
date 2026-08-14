"""Frozen one-record supplement selector for auxiliary-span guide validation.

The real entry point requires ``--execute-frozen-supplement``.  ``--self-test``
uses synthetic in-memory records and never opens a corpus or manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_SELECTOR_PATH = ROOT / "training" / "select_aux_span_validation_records.py"
BASE_SELECTOR_SHA256 = "e79d889dd9ab0c5ccc6e8e62be52625fd724786aea3a6095aea368870f88823b"
BASE_MANIFEST_PATH = ROOT / "training" / "controlled_seed17_aux_span_validation_manifest.json"
BASE_MANIFEST_SHA256 = "6314b4336e0fac4a52735f0072ce82a2d5ba44f65a90ef536628a7d34d70dcb5"
DISAGREEMENT_PATH = ROOT / "training" / "controlled_seed17_aux_span_validation_disagreement_record.md"
DISAGREEMENT_SHA256 = "cd4bc970eaa165f82785e5e5d3bf464a9cef415d877d8004c2c002bd2c17547f"
OUTPUT_PATH = ROOT / "training" / "controlled_seed17_aux_span_validation_supplement_manifest.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


if sha256_bytes(BASE_SELECTOR_PATH.read_bytes()) != BASE_SELECTOR_SHA256:
    raise RuntimeError("FATAL: base selector hash mismatch")
_spec = importlib.util.spec_from_file_location("aux_span_base_selector", BASE_SELECTOR_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError("FATAL: cannot load pinned base selector")
base = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = base
_spec.loader.exec_module(base)


MIN_CONTENT_TOKENS = 3
PREDICATE_CUE_RE = re.compile(
    r"\b(?:am|are|arrived|ask|asked|be|been|bring|brought|buy|call|called|can|check|checked|"
    r"close|closed|confirm|confirmed|could|did|do|does|draft|email|failed|felt|file|forgot|"
    r"get|got|had|handed|has|have|helped|is|jam|jammed|leave|left|looked|lost|made|must|need|needed|"
    r"needs|open|opened|order|pick|print|remind|remember|request|return|review|ran|said|"
    r"schedule|seem|seemed|send|sent|should|stressed|take|test|text|thinking|thought|told|"
    r"update|upload|wait|waited|want|wanted|was|were|will|wonder|would)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SupplementCandidate:
    record_id: int
    record: dict[str, Any]
    category: str
    omitted_segments: tuple[dict[str, Any], ...]
    max_token_jaccard: float
    max_char_5gram_jaccard: float


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def target_content_tokens(record: dict[str, Any], label: str) -> set[str]:
    result: set[str] = set()
    for text in base.target_strings(record, label):
        result.update(base.content_tokens(text))
    return result


def omission_signatures(record: dict[str, Any], label: str) -> tuple[dict[str, Any], ...]:
    """Return strong mechanical omission signals; this is not semantic annotation."""
    source = base.record_input(record, label)
    target_tokens = target_content_tokens(record, label)
    signatures: list[dict[str, Any]] = []
    for raw_segment in base.CLAUSE_SPLIT_RE.split(source):
        segment = raw_segment.strip(" \t,:")
        tokens = sorted(base.content_tokens(segment))
        if len(tokens) < MIN_CONTENT_TOKENS:
            continue
        predicate_cues = [match.group(0).lower() for match in PREDICATE_CUE_RE.finditer(segment)]
        if not predicate_cues:
            continue
        overlap = sorted(set(tokens) & target_tokens)
        if overlap:
            continue
        signatures.append(
            {
                "source_segment": segment,
                "content_tokens": tokens,
                "predicate_cues": predicate_cues,
                "target_content_token_overlap": [],
            }
        )
    return tuple(signatures)


def load_pinned_base_manifest() -> dict[str, Any]:
    raw = BASE_MANIFEST_PATH.read_bytes()
    if sha256_bytes(raw) != BASE_MANIFEST_SHA256:
        raise RuntimeError("FATAL: base validation manifest hash mismatch")
    if sha256_bytes(DISAGREEMENT_PATH.read_bytes()) != DISAGREEMENT_SHA256:
        raise RuntimeError("FATAL: disagreement-record hash mismatch")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=base._reject_duplicate_keys)


def select_supplement() -> tuple[SupplementCandidate, list[dict[str, Any]], dict[str, Any]]:
    base_manifest = load_pinned_base_manifest()
    comparator, comparator_receipt = base.load_pinned_jsonl("comparator")
    protected, protected_receipt = base.load_pinned_jsonl("protected")
    acceptance, acceptance_receipt = base.load_pinned_jsonl("acceptance")
    treatment, treatment_receipt = base.load_pinned_jsonl("treatment_delta")
    existing_records = base_manifest["regression_records"] + base_manifest["fresh_records"]
    existing_ids = {record["record_id"] for record in existing_records}
    excluded_ids = existing_ids | set(base.STATIC_PROTECTED_ANALOGUE_IDS)
    references = (
        base.reference_inputs(protected, "protected")
        + base.reference_inputs(acceptance, "acceptance")
        + base.reference_inputs(treatment, "treatment_delta")
        + [(record["record_locator"], record["source_input"]) for record in existing_records]
    )
    existing_categories = {record["category"] for record in base_manifest["fresh_records"]}
    candidates: list[SupplementCandidate] = []
    exclusions: list[dict[str, Any]] = []
    for record_id, record in enumerate(comparator, 1):
        label = f"comparator:{record_id:03d}"
        if record_id in excluded_ids:
            exclusions.append({"record_id": record_id, "reason": "existing validation or static protected analogue"})
            continue
        source = base.record_input(record, label)
        fatal, max_token, max_char, reasons = base.collision_metrics(source, references)
        if fatal:
            exclusions.append({"record_id": record_id, "reason": "leakage or validation-set collision", "details": reasons})
            continue
        signatures = omission_signatures(record, label)
        if not signatures:
            exclusions.append({"record_id": record_id, "reason": "no strong zero-overlap predicate segment"})
            continue
        category = record.get("category")
        if not isinstance(category, str) or not category:
            raise RuntimeError(f"FATAL: {label} lacks a category")
        candidates.append(SupplementCandidate(record_id, record, category, signatures, max_token, max_char))
    if not candidates:
        raise RuntimeError("FATAL: no eligible supplemental candidate satisfies the frozen omission signature")
    candidates.sort(
        key=lambda candidate: (
            -len(candidate.omitted_segments),
            -max(len(segment["content_tokens"]) for segment in candidate.omitted_segments),
            -sum(len(segment["content_tokens"]) for segment in candidate.omitted_segments),
            candidate.category in existing_categories,
            candidate.max_token_jaccard,
            candidate.max_char_5gram_jaccard,
            candidate.record_id,
        )
    )
    receipts = {
        "comparator": comparator_receipt,
        "protected": protected_receipt,
        "acceptance": acceptance_receipt,
        "treatment_delta": treatment_receipt,
    }
    return candidates[0], exclusions, {"base_manifest": base_manifest, "input_receipts": receipts}


def build_manifest() -> dict[str, Any]:
    selected, exclusions, context = select_supplement()
    base_manifest = context["base_manifest"]
    payload = {"input": selected.record["input"], "output": selected.record["output"]}
    supplemental_record = {
        "set": "fresh_supplement",
        "record_locator": f"comparator:{selected.record_id:03d}",
        "record_id": selected.record_id,
        "category": selected.category,
        "difficulty": selected.record.get("difficulty"),
        "record_sha256": sha256_bytes(canonical_json_bytes(payload)),
        "source_input": selected.record["input"],
        "committed_target": selected.record["output"],
        "assigned_stress_feature": "unfielded_independent_content_supplement",
        "omission_signatures": list(selected.omitted_segments),
        "leakage_maxima": {
            "token_jaccard": round(selected.max_token_jaccard, 9),
            "character_5gram_jaccard": round(selected.max_char_5gram_jaccard, 9),
        },
    }
    combined_records = base_manifest["regression_records"] + base_manifest["fresh_records"] + [supplemental_record]
    manifest: dict[str, Any] = {
        "artifact": "controlled_seed17_aux_span_validation_supplement_manifest",
        "status": "frozen_unannotated",
        "authority_boundary": (
            "Freezes one supplemental fresh record only. Does not authorize annotation, guide revision, "
            "model/tokenizer use, Gemini activity, staging, commit, or push."
        ),
        "governing_pins": {
            "base_selector_sha256": BASE_SELECTOR_SHA256,
            "base_manifest_sha256": BASE_MANIFEST_SHA256,
            "disagreement_record_sha256": DISAGREEMENT_SHA256,
        },
        "input_pins_and_checkout_receipts": context["input_receipts"],
        "selection_rules": {
            "supplement_size": 1,
            "minimum_content_tokens": MIN_CONTENT_TOKENS,
            "target_content_token_overlap": 0,
            "predicate_cue_regex": PREDICATE_CUE_RE.pattern,
            "excluded_existing_validation_ids": sorted(
                record["record_id"] for record in base_manifest["regression_records"] + base_manifest["fresh_records"]
            ),
            "static_protected_analogue_ids": list(base.STATIC_PROTECTED_ANALOGUE_IDS),
            "collision_thresholds": {
                "normalized_exact": "exclude",
                "normalized_containment_min_chars": base.CONTAINMENT_MIN_NORMALIZED_CHARS,
                "token_jaccard": base.TOKEN_JACCARD_THRESHOLD,
                "character_5gram_jaccard": base.CHAR_5GRAM_JACCARD_THRESHOLD,
                "all_threshold_crossings": "exclude",
            },
            "tie_break": (
                "omission segment count desc; longest segment content-token count desc; total omitted "
                "content-token count desc; unused fresh category first; token max asc; char-5gram max asc; id asc"
            ),
        },
        "supplemental_record": supplemental_record,
        "exclusion_audit": exclusions,
        "combined_validation_record_count": len(combined_records),
        "combined_validation_set_fingerprint": sha256_bytes(canonical_json_bytes(combined_records)),
        "future_gemini_quarantine": base_manifest["future_gemini_quarantine"] + [supplemental_record["record_locator"]],
    }
    manifest["manifest_sha256"] = sha256_bytes(canonical_json_bytes(manifest))
    return manifest


def run_self_test() -> None:
    omitted = {
        "input": "Call Mina tomorrow. The bronze latch jammed twice.",
        "output": {"narrative": "Call Mina tomorrow.", "bullets": ["Call Mina"], "action_items": ["Call Mina"]},
    }
    signatures = omission_signatures(omitted, "synthetic-omitted")
    assert len(signatures) == 1
    assert signatures[0]["source_segment"] == "The bronze latch jammed twice"
    represented = {
        "input": "The bronze latch jammed twice.",
        "output": {
            "narrative": "The bronze latch jammed twice.",
            "bullets": ["Bronze latch jammed twice"],
            "action_items": [],
        },
    }
    assert omission_signatures(represented, "synthetic-represented") == ()
    no_predicate = {
        "input": "bronze latch workshop notes",
        "output": {"narrative": "", "bullets": [], "action_items": []},
    }
    assert omission_signatures(no_predicate, "synthetic-no-predicate") == ()
    print("PASS: synthetic supplement self-test; no corpus or manifest opened")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--execute-frozen-supplement", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        run_self_test()
        return
    if OUTPUT_PATH.exists():
        raise RuntimeError(f"FATAL: supplement manifest already exists; refusing to overwrite {OUTPUT_PATH}")
    manifest = build_manifest()
    OUTPUT_PATH.write_bytes(json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")
    print(f"WROTE {OUTPUT_PATH}")
    print(f"manifest_sha256={sha256_bytes(OUTPUT_PATH.read_bytes())}")
    print("supplemental_record_locator=" + manifest["supplemental_record"]["record_locator"])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
