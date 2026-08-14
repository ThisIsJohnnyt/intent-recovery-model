# Auxiliary span guide revision-3 final disagreement and closure record

**Date:** 2026-08-14  
**Status:** Final correction rerun failed; no correction or redraw remains; return to Johnny  
**Guide revision 3 SHA-256:** `96311377b1caa4a3efccb901b557508f85e65b0ce18d1c239da902296d12df82`  
**ChatGPT correction pass SHA-256:** `55981bf5aa299891120bc24f53a8da6e4569f1951774d1f74a917f9d2f448372`  
**Claude correction pass SHA-256:** `e3c165a61304aabd62b7b62fe4ce69bee3d13270347f62317a5b65cc73288d91`  
**Base manifest SHA-256:** `6314b4336e0fac4a52735f0072ce82a2d5ba44f65a90ef536628a7d34d70dcb5`  
**Supplement manifest SHA-256:** `3e265857720cc48da6a618d9a534dfa3e69658c869858b1a65170e3bc0ff0467`  

## 1. Authority and preservation

This is the required final comparison after the single correction rerun permitted by guide revision 2 and
implemented by revision 3. Both 15-record passes were independently created, schema-validated, sealed, and
hashed before comparison. Neither sealed pass was edited.

Guide revision 3 explicitly allows no second correction, record replacement, supplemental draw, or
adjudication into apparent agreement. This result therefore closes the current auxiliary-span guide-
validation path as failed and returns to Johnny.

Nothing here authorizes annotation edits, full-corpus annotation, implementation, model/tokenizer use,
training, Gemini setup/generation/spending, staging, commit, or push.

## 2. Gate results

| Gate | Required | Result | Status |
|---|---:|---:|---|
| Schema validation | Both passes pass | Both pass | PASS |
| Record count | 15 each | 15 / 15 | PASS |
| Proposition count | Exact per record | 88 / 88 globally and exact per record | PASS |
| Record-level annotation agreement | 15 / 15 | 12 / 15 | **FAIL** |
| Fresh agreed empty-field coverage | At least 1 proposition | 0 | **FAIL** |

The final correction rerun fails both semantic gates.

Raw span differences that consist only of one allowed terminal punctuation mark occur in comparators 040,
042, 048, 056, 069, 075, 012, 008, and 030. They are boundary-equivalent under the guide and are not counted
as substantive disagreement.

Exact agreement after boundary equivalence is reached on:

`007, 042, 048, 054, 056, 069, 074, 075, 012, 073, 008, 030`.

Substantive disagreement remains on `040`, `053`, and supplemental fresh `018`.

## 3. Complete substantive disagreement inventory

### Comparator 040

1. Initial missing-callback fact (`p03`): ChatGPT assigns `narrative`+`bullet`; Claude assigns `narrative`
   only. Revision 3 Section 8.2 said both plumber-callback facts receive narrative+bullet, but the sealed pass
   still differs and may not be repaired after sealing.
2. Target-inferred plumber follow-up (`p11`): ChatGPT assigns `actor`+`recipient`+`object`, using Section 3's
   permission to derive roles from exact committed action wording (`Follow up with the plumber about the
   leak`). Claude assigns `actor` only. Terminal punctuation is boundary-equivalent.

### Comparator 053

`I know` (`p02`) is `experiencer` for ChatGPT and `actor` for Claude. Revision 3 classifies cognition as an
experiencer role, but the sealed result differs and may not be harmonized after the fact.

### Comparator 018 (fresh supplement)

1. `too much to do` (`p01`): ChatGPT assigns `narrative`+`bullet`, interpreting the committed
   overwhelmed/behind narrative and bullet as identifiable realization of the workload fact. Claude assigns
   an empty field list, interpreting those fields as general thematic gist rather than realization of that
   specific semantic contribution.
2. `wife wants to go over the budget tonight` source fact (`p03`): ChatGPT assigns
   `actor`+`object`+`experiencer`; Claude assigns `object`+`experiencer`, omitting actor for the controlled
   desired event.
3. Target-inferred budget-review task (`p04`): ChatGPT assigns `actor`+`object` and `time`, using the explicit
   budget theme and source `tonight`. Claude assigns `actor` and `deadline`, using the committed action's
   `before tonight` framing and omitting object.
4. `just so behind` (`p07`): ChatGPT assigns implicit-writer `experiencer`; Claude assigns no roles.

No other substantive difference exists.

## 4. Fresh empty-field coverage failure

The five fresh records are `012, 073, 008, 030, 018`.

- ChatGPT assigns zero empty-field propositions across all five.
- Claude assigns one: comparator 018 `too much to do`.
- Therefore the count of **agreed** fresh empty-field propositions is zero.

This is exactly the one-shot residual risk disclosed before the supplemental draw. The lexical selector
correctly found zero content-token overlap, but semantic annotation showed that one reviewer regarded the
target's paraphrastic overwhelmed/behind content as realization while the other did not. The selector was not
wrongly executed; lexical omission simply did not guarantee semantic omission.

The failure cannot be resolved by declaring Claude's empty-field judgment sufficient, because the gate
requires agreement. It also cannot be resolved by choosing ChatGPT's mapping, editing a pass, changing the
meaning of unfielded content, drawing a sixth record, or revising the guide again.

## 5. Improvement versus the initial run

Revision 3 materially improved reproducibility:

- initial revision-2 agreement: 2 of 14 records;
- final revision-3 agreement: 12 of 15 records;
- all per-record proposition counts now agree; and
- the remaining disagreement is limited to seven field/role/qualifier decisions across three records.

This is useful diagnostic evidence, but it does not satisfy a fail-closed gate. Near-agreement is not pass.

## 6. Closure consequence

The current auxiliary-span-supervision annotation guide is not validated for generator readiness or
full-corpus annotation. Under the frozen rules:

1. do not annotate the full corpus;
2. do not treat revision 3 as a validated annotation contract;
3. do not expose the five fresh records to Gemini;
4. do not begin Gemini generator readiness on the premise that this gate passed; and
5. return to Johnny for a higher-level project decision rather than another local correction.

Reasonable future decisions are outside this record's authority. They may include retiring this auxiliary-
span path, redesigning the representation/validation strategy under a new milestone, or explicitly
decoupling Gemini generator readiness from auxiliary-span supervision with a new risk analysis. None is
authorized here.
