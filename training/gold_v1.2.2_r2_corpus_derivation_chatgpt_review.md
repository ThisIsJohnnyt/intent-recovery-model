# Gold v1.2.2 Revision-2 Corpus Derivation — ChatGPT Review

**Review status:** Candidate derivation verified. One non-blocking report-wording correction requested.

**Model compute performed during review:** none. No training, inference, checkpoint loading, or model evaluation was performed.

## Materials reviewed

- `gold_v1.2.2_r2_derive_corpus.py`
- `gold_v1.2.2_r2_derived_candidate.jsonl`
- `gold_v1.2.2_r2_corpus_derivation_report.md`
- Approved `gold_v1.2.2_target_integrity_corrections_proposal_r2.jsonl`

## Independent verification results

The following were recomputed independently from the delivered candidate and the approved Revision-2 proposal rather than accepted from the derivation report:

1. The candidate contains exactly 66 records and 66 unique inputs.
2. Every record has the expected top-level fields: `input`, `output`, `difficulty`, `category`, `v1_target`, and `v2_target`.
3. The three approved correction input hashes resolve uniquely to candidate indices 15, 38, and 52.
4. At each of those indices, the candidate `output` exactly equals the proposal's approved `proposed_output`:
   - `ti-001`: actions 3 → 2;
   - `ti-002`: actions 5 → 1; and
   - `ti-003`: actions 2 → 2.
5. Replacing those three outputs with the proposal's approved `current_output` reconstructs an old-corpus view in which the only structured-output differences are indices `[15, 38, 52]`.
6. Input, category, difficulty, and record order remain identical across the reconstructed old and delivered candidate views.
7. All 66 stored `v1_target` values exactly equal an independent reconstruction from their structured outputs.
8. All 66 stored `v2_target` values independently parse into narrative, bullets, and actions exactly equal to their structured outputs.
9. The full-corpus action distribution recomputes to `{0: 8, 1: 25, 2: 19, 3: 7, 4: 7}`.
10. The approved proposal's action and bullet deltas match the actual current/proposed structures for all three corrections.

## Fingerprint reproduction

| Artifact or logical content | Recomputed SHA-256 | Report match |
|---|---|---|
| Approved Revision-2 proposal file | `dfb4a001d73c49714fb72f02574c5b00120262cb032251e3e3e232992dde8097` | Yes |
| Reconstructed old corpus content | `0c1ad1ef5bc72b61bb3205810d7aaa5fec84049bfada916eb1343d9df3bc05f2` | Yes |
| Derived candidate corpus content | `42b250a92446569fab2cf44b57130749ecdb42626b7c1c335122daaec6ff281b` | Yes |
| Reconstructed old v2 serialization | `6542ada49eaf3f97b3d78f3df120f7b0578772e5a5c66afa3610b5c290b0b6b8` | Yes |
| Derived candidate v2 serialization | `e033fa1da370bdb329cde209d9ed093639e6e529ef6d84bd1c1f5164e4b68101` | Yes |

For transport-level identification, the delivered files themselves hash to:

| Delivered file | SHA-256 |
|---|---|
| `gold_v1.2.2_r2_derived_candidate.jsonl` | `197adb3578b27c8b76bdbb33b3dcb35398ccd980932f0f718a5fedd732b9c1ac` |
| `gold_v1.2.2_r2_derive_corpus.py` | `9071771178f059dff4349e2ca7e723b24d2558c935a032676608f80bb08912ff` |
| `gold_v1.2.2_r2_corpus_derivation_report.md` | `e82695b7eb747f0377933ae86f9d7c49023f4bfcce1707cfdb775af49589b79b` |

## Finding: report overstates the drift-check comparison

The derivation report says `current_output` was verified **byte-identical** to the pinned record's `output`. The implementation parses both JSON documents and then checks Python dictionary/list equality:

```python
if corr["current_output"] != rec["output"]:
```

This verifies exact structured-value equality, including all nested strings, lists, keys, and values. It does not verify that the original JSON source bytes used identical whitespace or key ordering.

### Required correction

Change the report language from "byte-identical" to "structurally identical as parsed JSON" (or equivalent). The safeguard confirmation should describe the check the program actually performs.

This is a documentation-accuracy correction only:

- It does not invalidate the structured drift guard.
- It does not change any approved correction.
- It does not change the candidate corpus.
- It does not require the derivation to be rerun.

## Alignment and next gate

I am aligned with the derived candidate and the derivation outcome. The candidate may proceed after Claude independently confirms the wording correction and records the corrected report. Gold v1.2.2 must remain immutable.

No training or inference is authorized by this review. Any model compute remains a separate product-owner decision after the derivation package is closed.
