"""Standalone assertion tests for
prepare_regression_balanced_repair_candidate_corpus.py -- dummy data only,
except where explicitly noted as a live check against the real repository.
No pytest dependency: run directly with
`python test_prepare_regression_balanced_repair_candidate_corpus.py`,
matching this repo's existing script-based tooling convention (see
test_prepare_phase2_contrastive_candidate_corpus.py, whose structure this
file follows).

Covers every fail-closed condition in
prepare_regression_balanced_repair_candidate_corpus.py's module docstring:
canonicalization, schema, size ceiling, Group-A provenance/balance,
Group-B action completeness, Group-C no-invention, mechanism labeling,
identity/collision checks, candidate construction and byte-preservation,
and frozen split-membership -- plus live checks that the real pinned
inputs on this exact checkout load cleanly with no manual normalization.
"""
import hashlib
import json
from pathlib import Path

import prepare_regression_balanced_repair_candidate_corpus as p
from prepare_data import input_hash

FAILURES = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f" -- {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


def expect_system_exit(fn, *args, **kwargs) -> str | None:
    try:
        fn(*args, **kwargs)
    except SystemExit as e:
        return str(e)
    return None


def make_record(text: str, output: dict, difficulty: str = "medium", category: str = "test_category") -> dict:
    return {"input": text, "output": output, "difficulty": difficulty, "category": category}


def make_output(narrative: str, bullets: list[str], actions: list[str]) -> dict:
    return {"narrative": narrative, "bullets": bullets, "action_items": actions}


# ---------------------------------------------------------------------------
# canonicalize_pinned_lf_bytes (ported logic -- same coverage shape as the
# sibling script's own tests)
# ---------------------------------------------------------------------------


def test_canonicalize_pinned_lf_bytes():
    lf = b"line one\nline two\n"
    fp = hashlib.sha256(lf).hexdigest()
    check("canonicalize: LF input passes and returns itself", p.canonicalize_pinned_lf_bytes(lf, fp, "t") == lf)

    crlf = b"line one\r\nline two\r\n"
    check("canonicalize: uniform-CRLF input normalizes to the same canonical LF", p.canonicalize_pinned_lf_bytes(crlf, fp, "t") == lf)

    mixed = b"line one\r\nline two\n"
    out = expect_system_exit(p.canonicalize_pinned_lf_bytes, mixed, fp, "t")
    check("canonicalize: mixed CRLF/bare-LF fails closed", out is not None and "mixed line endings" in out)

    bare_cr = b"line one\rline two\n"
    out = expect_system_exit(p.canonicalize_pinned_lf_bytes, bare_cr, fp, "t")
    check("canonicalize: bare CR fails closed", out is not None and "bare carriage return" in out)

    no_term = b"line one\nline two"
    out = expect_system_exit(p.canonicalize_pinned_lf_bytes, no_term, fp, "t")
    check("canonicalize: missing terminal newline fails closed", out is not None and "terminal newline" in out)

    bom = b"\xef\xbb\xbf" + lf
    out = expect_system_exit(p.canonicalize_pinned_lf_bytes, bom, fp, "t")
    check("canonicalize: BOM fails closed", out is not None and "BOM" in out)

    drifted = b"line one\nline TWO\n"
    out = expect_system_exit(p.canonicalize_pinned_lf_bytes, drifted, fp, "t")
    check("canonicalize: real content drift fails closed after normalization", out is not None and "does not match the pinned" in out)


# ---------------------------------------------------------------------------
# validate_proposal_schema
# ---------------------------------------------------------------------------


def test_schema():
    good = [make_record("x", make_output("n", ["b"], ["a"]))]
    try:
        p.validate_proposal_schema(good)
        check("schema: valid record passes", True)
    except SystemExit:
        check("schema: valid record passes", False)

    missing_key = [{"input": "x", "output": make_output("n", ["b"], ["a"]), "difficulty": "hard"}]
    out = expect_system_exit(p.validate_proposal_schema, missing_key)
    check("schema: missing top-level key fails closed", out is not None)

    bad_output_keys = [make_record("x", {"narrative": "n", "bullets": ["b"]})]
    out = expect_system_exit(p.validate_proposal_schema, bad_output_keys)
    check("schema: missing output key fails closed", out is not None)

    forbidden_cat = [make_record("x", make_output("n", ["b"], ["a"]), category=p.FORBIDDEN_CATEGORY)]
    out = expect_system_exit(p.validate_proposal_schema, forbidden_cat)
    check("schema: forbidden category fails closed", out is not None and p.FORBIDDEN_CATEGORY in out)

    empty_narrative = [make_record("x", make_output("", ["b"], ["a"]))]
    out = expect_system_exit(p.validate_proposal_schema, empty_narrative)
    check("schema: empty narrative fails closed", out is not None)

    non_string_bullet = [make_record("x", make_output("n", [1], ["a"]))]
    out = expect_system_exit(p.validate_proposal_schema, non_string_bullet)
    check("schema: non-string bullet fails closed", out is not None)


# ---------------------------------------------------------------------------
# verify_counts / verify_size_ceiling
# ---------------------------------------------------------------------------


def test_counts_and_ceiling():
    good_baseline = [{"input": f"b{i}"} for i in range(p.EXPECTED_BASELINE_COUNT)]
    good_proposal = [{"input": f"p{i}"} for i in range(p.EXPECTED_PROPOSAL_COUNT)]
    try:
        p.verify_counts(good_baseline, good_proposal)
        check("counts: exact expected counts pass", True)
    except SystemExit:
        check("counts: exact expected counts pass", False)

    out = expect_system_exit(p.verify_counts, good_baseline[:-1], good_proposal)
    check("counts: short baseline fails closed", out is not None)

    out = expect_system_exit(p.verify_counts, good_baseline, good_proposal[:-1])
    check("counts: short proposal fails closed", out is not None)

    try:
        p.verify_size_ceiling()
        check("size ceiling: actual 3 new + 4 reused passes", True)
    except SystemExit:
        check("size ceiling: actual 3 new + 4 reused passes", False)


# ---------------------------------------------------------------------------
# verify_attribution_reuse_provenance
# ---------------------------------------------------------------------------


def test_attribution_provenance():
    at1 = make_record("at1 input", make_output("n1", ["b1"], ["a1"]), "hard", "multi_person_attribution")
    at2 = make_record("at2 input", make_output("n2", ["b2"], ["a2"]), "hard", "multi_person_attribution")
    at3 = make_record("at3 input", make_output("n3", ["b3"], ["a3"]), "expert", "multi_person_attribution")
    at4 = make_record("at4 input", make_output("n4", ["b4"], ["a4"]), "hard", "multi_person_attribution")
    composite = [at1, at2, at3, at4]

    exact_reuse = [dict(r) for r in composite] + [
        make_record("b1 input", make_output("n", ["b"], ["a"])),
        make_record("b3 input", make_output("n", ["b"], ["a"])),
        make_record("c3 input", make_output("n", ["b"], ["a"])),
    ]
    try:
        p.verify_attribution_reuse_provenance(exact_reuse, composite)
        check("Group-A provenance: exact reuse passes", True)
    except SystemExit:
        check("Group-A provenance: exact reuse passes", False)

    tampered = [dict(r) for r in composite]
    tampered[0] = dict(tampered[0])
    tampered[0]["output"] = make_output("edited narrative", ["b1"], ["a1"])
    tampered_proposal = tampered + exact_reuse[4:]
    out = expect_system_exit(p.verify_attribution_reuse_provenance, tampered_proposal, composite)
    check("Group-A provenance: edited reuse (not object-identical) fails closed", out is not None)


# ---------------------------------------------------------------------------
# verify_group_a_balance
# ---------------------------------------------------------------------------


def test_group_a_balance():
    shared_out = make_output("X told Y the plan was approved.", ["The plan was approved.", "Ask X to send Y the link."], ["Ask X to send Y the link."])
    a1 = make_record("Elena told Owen...", shared_out, "hard", "multi_person_attribution")
    a2 = make_record("Casey told Morgan...", make_output("n", ["It is unclear whether Casey or Morgan followed up."], ["Ask Casey to send Morgan the link."]), "hard", "multi_person_attribution")
    a3 = make_record("Joel/Priya...", make_output("n", ["It is unclear whether Joel or the courier needs it."], ["Ask Priya who needs it."]), "expert", "multi_person_attribution")
    a4 = make_record("Owen told Elena...", shared_out, "hard", "multi_person_attribution")
    good = [a1, a2, a3, a4]
    try:
        p.verify_group_a_balance(good)
        check("Group-A balance: valid resolve/preserve/order-swap set passes", True)
    except SystemExit:
        check("Group-A balance: valid resolve/preserve/order-swap set passes", False)

    broken_a4 = dict(a4)
    broken_a4["output"] = make_output("different", ["different bullet"], ["different action"])
    broken = [a1, a2, a3, broken_a4]
    out = expect_system_exit(p.verify_group_a_balance, broken)
    check("Group-A balance: RB-A1/RB-A4 no longer identical fails closed", out is not None)

    no_ambiguity_a2 = dict(a2)
    no_ambiguity_a2["output"] = make_output("n", ["Casey followed up with the museum."], ["Ask Casey to send Morgan the link."])
    broken2 = [a1, no_ambiguity_a2, a3, a4]
    out = expect_system_exit(p.verify_group_a_balance, broken2)
    check("Group-A balance: RB-A2 resolving the ambiguity fails closed", out is not None)


# ---------------------------------------------------------------------------
# verify_group_b_action_completeness
# ---------------------------------------------------------------------------


def test_group_b_action_completeness():
    b1 = make_record(
        "Before the service counter closes on Thursday, take the sealed calibration packet to the north depot. The lobby clock was six minutes slow.",
        make_output(
            "n",
            ["Take the sealed calibration packet to the north depot before the service counter closes on Thursday.", "The lobby clock was six minutes slow."],
            ["Take the sealed calibration packet to the north depot before the service counter closes on Thursday."],
        ),
        "hard", "cross_field_completeness",
    )
    b3 = make_record(
        "When the projector cart returns, place three labeled adapters in the locked drawer. The hallway smelled like floor polish.",
        make_output(
            "n",
            ["Place three labeled adapters in the locked drawer when the projector cart returns.", "The hallway smelled like floor polish."],
            ["Place three labeled adapters in the locked drawer when the projector cart returns."],
        ),
        "hard", "cross_field_completeness",
    )
    good = [None, None, None, None, b1, b3, None]  # only indices 4,5 (RB-B1/RB-B3) matter to this check
    try:
        p.verify_group_b_action_completeness(good)
        check("Group-B: complete action frames pass", True)
    except SystemExit:
        check("Group-B: complete action frames pass", False)

    b1_dropped_deadline = dict(b1)
    b1_dropped_deadline["output"] = make_output(
        "n",
        ["Take the sealed calibration packet to the north depot.", "The lobby clock was six minutes slow."],
        ["Take the sealed calibration packet to the north depot."],  # Thursday dropped
    )
    broken = [None, None, None, None, b1_dropped_deadline, b3, None]
    out = expect_system_exit(p.verify_group_b_action_completeness, broken)
    check("Group-B: dropped deadline qualifier fails closed", out is not None and "Thursday" in out)

    b1_promoted_observation = dict(b1)
    b1_promoted_observation["output"] = make_output(
        "n",
        ["Take the sealed calibration packet to the north depot before the service counter closes on Thursday.", "The lobby clock was six minutes slow."],
        ["Take the sealed calibration packet to the north depot before the service counter closes on Thursday.", "Fix the lobby clock."],
    )
    broken2 = [None, None, None, None, b1_promoted_observation, b3, None]
    out = expect_system_exit(p.verify_group_b_action_completeness, broken2)
    check("Group-B: promoted observation (2 actions instead of 1) fails closed", out is not None)


# ---------------------------------------------------------------------------
# verify_group_c_no_invention
# ---------------------------------------------------------------------------


def test_group_c_no_invention():
    c3 = make_record(
        "When they bring it back, give her the earlier one.",
        make_output(
            "The earlier one should be given to her when they bring it back.",
            ["Give her the earlier one when they bring it back; the references are unresolved."],
            ["When they bring it back, give her the earlier one."],
        ),
        "expert", "dangling_reference",
    )
    good = [None, None, None, None, None, None, c3]  # only index 6 (RB-C3) matters
    try:
        p.verify_group_c_no_invention(good)
        check("Group-C: clean unresolved-reference record passes", True)
    except SystemExit:
        check("Group-C: clean unresolved-reference record passes", False)

    invented = dict(c3)
    invented["output"] = make_output(
        "Giving the earlier one to her when they bring it back is a good idea.",
        ["Give her the earlier one when they bring it back."],
        ["When they bring it back, give her the earlier one."],
    )
    broken = [None, None, None, None, None, None, invented]
    out = expect_system_exit(p.verify_group_c_no_invention, broken)
    check("Group-C: invented evaluative content ('good idea') fails closed", out is not None)

    dropped_condition = dict(c3)
    dropped_condition["output"] = make_output(
        "The earlier one should be given to her.",
        ["Give her the earlier one; the references are unresolved."],
        ["Give her the earlier one."],  # condition dropped from action
    )
    broken2 = [None, None, None, None, None, None, dropped_condition]
    out = expect_system_exit(p.verify_group_c_no_invention, broken2)
    check("Group-C: condition dropped from action fails closed", out is not None)


# ---------------------------------------------------------------------------
# verify_mechanism_labeling
# ---------------------------------------------------------------------------


def test_mechanism_labeling():
    try:
        p.verify_mechanism_labeling()
        check("mechanism labeling: real PRIMARY_MECHANISM mapping passes", True)
    except SystemExit:
        check("mechanism labeling: real PRIMARY_MECHANISM mapping passes", False)

    original = dict(p.PRIMARY_MECHANISM)
    try:
        p.PRIMARY_MECHANISM["RB-A1"] = "not_a_real_mechanism"
        out = expect_system_exit(p.verify_mechanism_labeling)
        check("mechanism labeling: invalid mechanism value fails closed", out is not None)
    finally:
        p.PRIMARY_MECHANISM.clear()
        p.PRIMARY_MECHANISM.update(original)


# ---------------------------------------------------------------------------
# normalize_for_collision / character n-grams / normalized containment
# (added 2026-08-11 per ChatGPT's review)
# ---------------------------------------------------------------------------


def test_normalize_for_collision():
    check("normalize: lowercases and strips punctuation", p.normalize_for_collision("Hello, World!!") == "hello world")
    check("normalize: collapses whitespace", p.normalize_for_collision("a   b\tc\nd") == "a b c d")
    check("normalize: strips digits-adjacent punctuation but keeps digits", p.normalize_for_collision("Room #42B.") == "room 42b")


def test_char_ngram_jaccard():
    check("char-ngram: identical text scores 1.0", p._char_ngram_jaccard("the quick brown fox", "the quick brown fox") == 1.0)
    check("char-ngram: totally different short strings score low", p._char_ngram_jaccard("apple", "zzzzz") < 0.2)
    check("char-ngram: empty string scores 0.0, no crash", p._char_ngram_jaccard("", "something") == 0.0)
    check("char-ngram: near-identical text (one word changed) scores high but not 1.0", 0.5 < p._char_ngram_jaccard("take the packet to the depot", "take the packet to the office") < 1.0)


def test_verify_normalized_containment():
    baseline_pool = [("baseline", "The lobby clock was six minutes slow.")]
    clean_proposal = [make_record("A completely unrelated sentence about packets.", make_output("n", ["b"], ["a"]))]
    try:
        p.verify_normalized_containment(clean_proposal, baseline_pool)
        check("containment: unrelated text passes", True)
    except SystemExit:
        check("containment: unrelated text passes", False)

    exact_dup_pool = [("baseline", "A completely unrelated sentence about packets.")]
    out = expect_system_exit(p.verify_normalized_containment, clean_proposal, exact_dup_pool)
    check("containment: normalized-exact duplicate fails closed", out is not None and "normalized-exact" in out)

    long_ref = "This is a long reference sentence that fully contains the proposed text somewhere inside it for testing purposes today."
    containing_pool = [("baseline", long_ref)]
    contained_proposal = [make_record("fully contains the proposed text somewhere inside it", make_output("n", ["b"], ["a"]))]
    out = expect_system_exit(p.verify_normalized_containment, contained_proposal, containing_pool)
    check("containment: substring containment above the length floor fails closed", out is not None and "containment" in out)

    short_shared_pool = [("baseline", "call the dentist please")]
    short_proposal = [make_record("please call", make_output("n", ["b"], ["a"]))]
    try:
        p.verify_normalized_containment(short_proposal, short_shared_pool)
        check("containment: trivially short shared substring (below the noise floor) passes", True)
    except SystemExit:
        check("containment: trivially short shared substring (below the noise floor) passes", False)


# ---------------------------------------------------------------------------
# entity/quantity extraction and overlap
# ---------------------------------------------------------------------------


def test_entity_extraction_and_overlap():
    entities = p._extract_entities_and_numbers("Before the service counter closes on Thursday, take the sealed calibration packet to the north depot.")
    check("entities: extracts day-of-week", "thursday" in entities)
    check("entities: does not extract the sentence-initial capitalized word as a false entity", "Before" not in entities)

    numeric = p._extract_entities_and_numbers("Place three labeled adapters in drawer 12.")
    check("entities: extracts numeric tokens", "12" in numeric)

    proposal = [make_record("Ask Priya to send the packet to Joel on Thursday.", make_output("n", ["b"], ["a"]))]
    overlapping_pool = [("baseline", "Priya said Joel would be at the office on Thursday.")]
    findings = p.verify_entity_overlap(proposal, overlapping_pool)
    check("entity overlap: 3+ shared proper-noun/day tokens produces a finding", len(findings) == 1)

    non_overlapping_pool = [("baseline", "Casey and Morgan discussed the plan on Friday.")]
    findings2 = p.verify_entity_overlap(proposal, non_overlapping_pool)
    check("entity overlap: no shared entities produces no finding", len(findings2) == 0)


# ---------------------------------------------------------------------------
# Group-D exemplar preservation (gate 8 correction)
# ---------------------------------------------------------------------------


def test_group_d_preserved_exemplars():
    candidate = [{"input": prefix + " some trailing content here."} for prefix in p.GROUP_D_EXEMPLAR_INPUT_PREFIXES.values()]
    try:
        found = p.verify_group_d_preserved_exemplars(candidate)
        check("Group-D exemplars: all present passes", all(found.values()) and len(found) == len(p.GROUP_D_EXEMPLAR_INPUT_PREFIXES))
    except SystemExit:
        check("Group-D exemplars: all present passes", False)

    missing_one = candidate[:-1]
    out = expect_system_exit(p.verify_group_d_preserved_exemplars, missing_one)
    check("Group-D exemplars: one missing fails closed", out is not None)


# ---------------------------------------------------------------------------
# identity / collision checks
# ---------------------------------------------------------------------------


def test_identity_checks():
    baseline = [make_record("unique baseline input 1", make_output("n", ["b"], ["a"]))]
    proposal = [make_record("unique proposal input 1", make_output("n", ["b"], ["a"]))]
    bench_hashes = {input_hash("some benchmark input")}
    try:
        p.verify_no_duplicate_or_colliding_inputs(baseline, proposal, bench_hashes)
        check("identity: no collisions passes", True)
    except SystemExit:
        check("identity: no collisions passes", False)

    dup_baseline = baseline + [dict(baseline[0])]
    out = expect_system_exit(p.verify_no_duplicate_or_colliding_inputs, dup_baseline, proposal, bench_hashes)
    check("identity: duplicate within baseline fails closed", out is not None)

    dup_proposal = proposal + [dict(proposal[0])]
    out = expect_system_exit(p.verify_no_duplicate_or_colliding_inputs, baseline, dup_proposal, bench_hashes)
    check("identity: duplicate within proposal fails closed", out is not None)

    colliding_proposal = [make_record(baseline[0]["input"], make_output("n", ["b"], ["a"]))]
    out = expect_system_exit(p.verify_no_duplicate_or_colliding_inputs, baseline, colliding_proposal, bench_hashes)
    check("identity: proposal colliding with baseline input fails closed", out is not None)

    bench_colliding_proposal = [make_record("some benchmark input", make_output("n", ["b"], ["a"]))]
    out = expect_system_exit(p.verify_no_duplicate_or_colliding_inputs, baseline, bench_colliding_proposal, bench_hashes)
    check("identity: proposal colliding with a benchmark input fails closed", out is not None)


def test_jaccard_helper():
    check("jaccard: identical text scores 1.0", p._jaccard("the quick brown fox", "the quick brown fox") == 1.0)
    check("jaccard: disjoint text scores 0.0", p._jaccard("apple banana", "car dog") == 0.0)
    check("jaccard: empty string scores 0.0, no crash", p._jaccard("", "something") == 0.0)


# ---------------------------------------------------------------------------
# build_candidate byte-preservation and order checks
# ---------------------------------------------------------------------------


def test_build_candidate_and_preservation():
    baseline = [{"input": "b0", "output": make_output("n0", ["b0"], ["a0"]), "difficulty": "easy", "category": "cat", "v1_target": "x", "v2_target": "y"}]
    proposal = [make_record("p0 unique input", make_output("New task recorded.", ["New task recorded."], ["New task recorded."]))]
    candidate, targets = p.build_candidate(baseline, proposal)
    check("build_candidate: candidate length == baseline + proposal", len(candidate) == 2)
    check("build_candidate: generated exactly one target per proposal record", len(targets) == 1)
    check("build_candidate: baseline record passed through unmodified", candidate[0] == baseline[0])
    check("build_candidate: appended record has v1_target/v2_target populated", bool(candidate[1]["v1_target"]) and bool(candidate[1]["v2_target"]))

    baseline_bytes = b'{"a": 1}\n'
    identical_candidate_bytes = baseline_bytes + b'{"b": 2}\n'
    try:
        p.verify_baseline_preserved_byte_for_byte(baseline_bytes, identical_candidate_bytes)
        check("byte-preservation: identical prefix passes", True)
    except SystemExit:
        check("byte-preservation: identical prefix passes", False)

    drifted_candidate_bytes = b'{"a": 2}\n' + b'{"b": 2}\n'
    out = expect_system_exit(p.verify_baseline_preserved_byte_for_byte, baseline_bytes, drifted_candidate_bytes)
    check("byte-preservation: drifted prefix fails closed", out is not None)


def test_build_split_frozen_membership():
    val_hashes = {input_hash("val input")}
    candidate = [
        {"input": "val input", "v2_target": "vt"},
        {"input": "train input 1", "v2_target": "tt1"},
        {"input": "brand new proposal record", "v2_target": "tt2"},
    ]
    train, val = p.build_split(candidate, val_hashes)
    check("split: val membership determined by frozen hash set, not position", len(val) == 1 and val[0]["target"] == "vt")
    check("split: everything not in the frozen val set goes to train, including brand-new records", len(train) == 2)


# ---------------------------------------------------------------------------
# Live checks against the real, unmodified repository (no manual
# normalization) -- matching this repo's established testing convention.
# ---------------------------------------------------------------------------


def test_historical_corpus_inventory_negative():
    """verify_historical_corpus_inventory() reads from fixed real paths (it
    verifies this repo's actual historical lineage, not synthetic data),
    so the meaningful negative case is: an empty/insufficient coverage set
    must fail closed rather than silently pass. The positive real-data
    case (everything actually subsumed or out of scope) is exercised in
    the live test below, against the real already-covered hash set."""
    out = expect_system_exit(p.verify_historical_corpus_inventory, set())
    check("historical inventory: empty coverage set fails closed (real historical files are NOT trivially covered by nothing)", out is not None and "not covered by any already-pinned source" in out)


def test_live_pinned_inputs_load_cleanly():
    try:
        canon = p.load_all_canonical_inputs()
        check("live: all 9 pinned inputs load and canonicalize cleanly on this checkout", set(canon) == {
            "baseline", "proposal", "composite_proposal", "existing_val", "existing_train",
            "split_manifest", "protected", "acceptance", "rejected_treatment_candidate",
        })
    except SystemExit as e:
        check("live: all 9 pinned inputs load and canonicalize cleanly on this checkout", False, str(e))
        return

    baseline = p.parse_jsonl_records_from_bytes(canon["baseline"])
    proposal = p.parse_jsonl_records_from_bytes(canon["proposal"])
    check("live: real baseline has exactly 78 records", len(baseline) == p.EXPECTED_BASELINE_COUNT)
    check("live: real proposal has exactly 7 records", len(proposal) == p.EXPECTED_PROPOSAL_COUNT)

    try:
        p.validate_proposal_schema(proposal)
        p.verify_size_ceiling()
        composite_proposal = p.parse_jsonl_records_from_bytes(canon["composite_proposal"])
        p.verify_attribution_reuse_provenance(proposal, composite_proposal)
        p.verify_mechanism_labeling()
        p.verify_group_a_balance(proposal)
        p.verify_group_b_action_completeness(proposal)
        p.verify_group_c_no_invention(proposal)
        check("live: real 7-record proposal passes every semantic invariant check", True)
    except SystemExit as e:
        check("live: real 7-record proposal passes every semantic invariant check", False, str(e))
        return

    try:
        protected = p.parse_jsonl_records_from_bytes(canon["protected"])
        acceptance = p.parse_jsonl_records_from_bytes(canon["acceptance"])
        rejected_treatment_candidate = p.parse_jsonl_records_from_bytes(canon["rejected_treatment_candidate"])
        check("live: real rejected-treatment-candidate has exactly 82 records", len(rejected_treatment_candidate) == 82)

        already_covered_hashes = (
            {input_hash(r["input"]) for r in baseline}
            | {input_hash(r["input"]) for r in rejected_treatment_candidate}
            | {input_hash(r["input"]) for r in composite_proposal}
        )
        inventory_results = p.verify_historical_corpus_inventory(already_covered_hashes)
        check(
            "live: real historical-corpus inventory covers all 5 known lineage files, all subsumed or out of scope",
            len(inventory_results) == len(p.HISTORICAL_INVENTORY)
            and all(r["missing_count"] == 0 for r in inventory_results),
        )

        pool = p.build_reference_pool(baseline, composite_proposal, protected, acceptance, rejected_treatment_candidate, proposal)
        check(
            "live: reference pool includes proposal-self entries for all 7 records",
            sum(1 for src, _ in pool if src.startswith("proposal-self:")) == p.EXPECTED_PROPOSAL_COUNT,
        )
        check(
            "live: reference pool includes the rejected-treatment-candidate class",
            sum(1 for src, _ in pool if src == "rejected-treatment-candidate") == 82,
        )
        p.verify_normalized_containment(proposal, pool)
        collision_results = p.run_collision_sweep(proposal, pool, protected, baseline)
        check(
            "live: real named comparisons match the values established during design/proposal review",
            abs(collision_results["_named_comparisons"]["rina_marcus_vs_protected_06"]["token_jaccard"] - 0.5758) < 0.001
            and abs(collision_results["_named_comparisons"]["RB-A3_vs_protected_06"]["token_jaccard"] - 0.3182) < 0.001,
        )
        p.verify_entity_overlap(proposal, pool)
        check("live: real 7-record proposal passes normalized containment (incl. self+rejected-candidate) + collision sweep + entity overlap", True)
    except SystemExit as e:
        check("live: real 7-record proposal passes normalized containment (incl. self+rejected-candidate) + collision sweep + entity overlap", False, str(e))


def run_all():
    test_canonicalize_pinned_lf_bytes()
    test_schema()
    test_counts_and_ceiling()
    test_attribution_provenance()
    test_group_a_balance()
    test_group_b_action_completeness()
    test_group_c_no_invention()
    test_mechanism_labeling()
    test_normalize_for_collision()
    test_char_ngram_jaccard()
    test_verify_normalized_containment()
    test_entity_extraction_and_overlap()
    test_group_d_preserved_exemplars()
    test_historical_corpus_inventory_negative()
    test_identity_checks()
    test_jaccard_helper()
    test_build_candidate_and_preservation()
    test_build_split_frozen_membership()
    test_live_pinned_inputs_load_cleanly()

    print(f"\n{len(FAILURES)} failure(s)" if FAILURES else "\nAll tests passed.")
    if FAILURES:
        for f in FAILURES:
            print(f"  FAILED: {f}")
        raise SystemExit(1)


if __name__ == "__main__":
    run_all()
