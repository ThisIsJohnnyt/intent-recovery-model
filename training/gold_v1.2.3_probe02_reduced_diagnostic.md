# Probe 02 Reduced Diagnostic

Per the investigation plan's dispatch rule: probe 02 passed only 1/3
seeds (`gold_v1.2.3`-seed17), so the reduced diagnostic applies
(punctuation and interruption-interference variants only), not the full
seven-variant battery. Diagnostic only — these variants were never added
to training, benchmark scoring, or release pass-rate calculations.

**Checkpoint availability note**: `checkpoint-520` (production) and the
original `checkpoint-600` (`gold_v1.2.2` candidate) no longer exist as
model weights locally — `save_total_limit=2` pruned them during later
training runs, and no dedicated backup was made for either (unlike
`checkpoint-680`, which was preserved as `gold_v1.2.3-seed42`). Only their
benchmark JSON records survive. Ran this diagnostic against the 5
checkpoints whose weights are still available: the three `gold_v1.2.3`
seeds and the two `gold_v1.2.2`-only control seeds — arguably a more
informative set for this specific question anyway, since it includes the
controlled data-vs-seed contrast the rest of this investigation has been
using.

## Variants tested

- **Original**: `"Figure out why the tablet keeps—put the donation box by the front door—back to the tablet, the screen goes black whenever the charger moves."`
- **A (punctuation-normalized)**: em dashes replaced with commas, "back to the tablet" phrase kept — `"Figure out why the tablet keeps, put the donation box by the front door, back to the tablet, the screen goes black whenever the charger moves."`
- **B (return marker removed)**: em dashes kept, "back to the tablet" phrase removed, clause completes directly — `"Figure out why the tablet keeps—put the donation box by the front door—the screen goes black whenever the charger moves."`
- **C (no interruption)**: the two facts as plain, un-interrupted sentences — `"Figure out why the tablet's screen goes black whenever the charger moves. Put the donation box by the front door."`

## Results

| Checkpoint | Original | A (normalized punctuation) | B (marker removed) | C (no interruption) |
|---|---|---|---|---|
| v1.2.3-seed42 | Fabricates "the computer," invents causality | Garbled, invents "return to the tablet" as a bullet | **Clean** — correct causal reconnection | **Clean** |
| v1.2.3-seed17 | Garbled ("keeps getting black") | Fabricates "put the donation box... and remember to put the charger back to the tablet" | Same as original (no worse, no better) | **Clean** |
| v1.2.3-seed73 | Fabricates "which makes it difficult to figure out" | Fabricates "remember to take the screen out... Return the screen to the tablet" | Improved — drops "back to the tablet" confusion | **Clean** |
| v1.2.2-seed17-control | Garbled ("returning to the tablet") | Garbled ("It is still unclear whether the tablet keeps going") | Clean reconnection, but drops donation box from bullets/actions entirely | **Clean** |
| v1.2.2-seed73-control | Vague ("interrupted concern about the tablet's behavior") | Vague + slightly more garbled | Same vague framing, drops donation box from actions | **Clean** |

## Findings

**Variant C (no interruption) is clean on all 5 of 5 checkpoints.** The
model has no difficulty with the underlying causal content — investigate
the screen going black, separately handle the donation box — when
presented as plain sentences. This rules out a basic
capability/comprehension limitation as the explanation. The failure is
specifically about interruption handling, not about understanding tablet
+ charger + screen causality.

**Variant A (punctuation-normalized) is worse than the original on every
checkpoint that changed at all**, producing new fabrications not seen on
the original input (e.g. "remember to put the charger back to the
tablet," "Return the screen to the tablet"). This directly answers one of
the plan's diagnostic questions: **em dashes are not the problem — they
appear to help**, not hurt, interruption segmentation. Replacing them
with commas removes a useful signal and makes segmentation harder.

**Variant B (return marker removed, em dashes kept) improves causal
reconnection on 3 of 5 checkpoints** (v1.2.3-seed42 and both
`gold_v1.2.2`-only control seeds reconnect cleanly instead of garbling),
though 2 of those 3 then drop the donation-box content from
bullets/actions — a different, milder failure (content completeness)
than the original's fabrication/invented-causality failure. This
supports the hypothesis that the literal phrase **"back to the tablet"**
— not the em-dash punctuation, not general interruption handling — is
the specific element driving the worst failures (fabricated nouns,
invented causal claims).

## Interpretation

Per the investigation plan's own interpretation table: this pattern
("main thought succeeds alone but fails with insertion" + "only
canonical wording fails, not punctuation") points to **narrow surface-form
brittleness tied to the specific "back to X" resumption phrase**, not a
tokenization problem, not a general discourse-segmentation limitation,
and not a model-capacity ceiling. The model can do every component
skill this probe requires — it just hasn't reliably learned to treat
"back to the tablet" as a pure structural marker with zero semantic
content, sometimes reconnecting past it correctly and sometimes treating
it as if it introduces new content to explain or resolve.

This is consistent with (though doesn't single-handedly prove) the
original hypothesis from the seed stability study: `gold_v1.2.3`'s
independent review correctly required removing this exact phrase from
example 005's training content to avoid benchmark-wording contamination,
which may have left the model with less reinforcement on how to handle
it correctly — precisely because probe 02's own protected wording still
contains it, permanently, and can never be rewritten to avoid it.

## Non-goals confirmed

No diagnostic variant was added to `datasets/benchmark/` or
`datasets/gold/`. No training run used these variants. This is
consistent with the investigation plan's explicit non-goals.
