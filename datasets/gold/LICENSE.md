# License

This dataset (the contents of `datasets/gold/`, including `gold_v1.0.jsonl`
and its design notes) is licensed under the **Creative Commons
Attribution-NonCommercial-ShareAlike 4.0 International License
(CC BY-NC-SA 4.0)**.

Copyright (c) 2026 ThisIsJohnnyt.

You are free to:
- **Share** — copy and redistribute the material in any medium or format
- **Adapt** — remix, transform, and build upon the material

Under the following terms:
- **Attribution** — you must give appropriate credit to ThisIsJohnnyt,
  provide a link to the license, and indicate if changes were made.
- **NonCommercial** — you may not use the material for any purpose primarily
  intended for commercial advantage or monetary compensation.
- **ShareAlike** — if you remix, transform, or build upon the material, you
  must distribute your contributions under CC BY-NC-SA 4.0, a later version
  with the same license elements, or a BY-NC-SA Compatible License, as
  permitted by Section 3(b) of the legal code.

No additional restrictions — you may not apply legal terms or technological
measures that legally restrict others from doing anything the license
permits.

Full license text: https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en

## Which license applies to which material — this depends on the version, not when you downloaded it

CC BY-NC-SA 4.0 applies to new material and revisions first published
under it, beginning with commit `d3deeef` (2026-08-12). It does **not**,
and legally cannot, revoke the CC-BY-4.0 license already granted for
`gold_v1.0` through `gold_v1.2.3`, published between commits `1cb3490`
(2026-07-28) and `2f7a101` (2026-08-03). CC licenses are irrevocable once
granted (CC BY 4.0 legal code §2(a)(1); confirmed against the Creative
Commons FAQ), and a licensor offering new terms later does not terminate
the earlier public license (§6(c)).

**The license that applies is determined by which version/material you
have, not by the date you obtained it.** That distinction matters
concretely: this project preserves the CC-BY-4.0 era as the
[`last-cc-by-4.0`](https://github.com/ThisIsJohnnyt/intent-recovery-model/releases/tag/last-cc-by-4.0)
tag/release, obtainable at any time, including now and in the future.
Anyone who obtains that covered historical version — whether during the
original 2026-07-28 to 2026-08-12 window or years from now via that
preserved snapshot — may use it under CC-BY-4.0, including commercially.
Downloading current `main` after 2026-08-12 does not convert historical
material to CC BY-NC-SA 4.0; downloading the `last-cc-by-4.0` snapshot
after 2026-08-12 does not convert it either. Unchanged content that
happens to appear both in that snapshot and in a later revision remains
available under the earlier CC-BY-4.0 grant when sourced from the licensed
historical version.

This project cannot and does not claim any prior CC-BY-4.0 grant can be
narrowed, revoked, or converted after the fact — by this file, by the
passage of time, or by any later project decision.

Note: this license applies to the synthetic examples in this directory. It
does **not** apply to `datasets/real_validation.jsonl` or
`datasets/real_holdout.jsonl`, both of which contain the project owner's
real personal notes (for routine development-time evaluation and sealed
release-milestone evaluation, respectively — see `docs/decisions/PDR-004.md`),
are excluded from version control, and are never published.

## Scope of this file

This license currently covers only the dataset in `datasets/gold/`. It does
not, by itself, set the license for this project's training/inference code,
documentation, or any released model weights — those remain a separate,
not-yet-decided licensing question (tracked in
`training/intent_recovery_data_model_discovery_plan_chatgpt.md`). Do not
assume code or model-weight terms from this file alone.

## Revision history

- **Revision 1** (`d3deeef`, 2026-08-12): changed from CC-BY-4.0 to CC
  BY-NC-SA 4.0 to match the project's settled policy — public,
  attribution-required, noncommercial throughout the downstream lineage,
  including forks. The prior CC-BY-4.0 choice (set 2026-07-28, `1cb3490`)
  permitted unrestricted commercial reuse and was never the product of a
  deliberate commercial-use decision — no PDR backed it.
- **Revision 2** (`4742fbb`, 2026-08-12): added this section (originally
  titled "Effective date and prospective scope") after ChatGPT's
  independent review found Revision 1 stated the noncommercial lineage as
  unqualified, omitting that the prior CC-BY-4.0 grant is irrevocable.
  Also widened the ShareAlike clause to match legal-code §3(b).
- **Revision 3** (this version, pending commit): corrects Revision 2's
  own framing after ChatGPT's second independent review — the section
  tied the license boundary to *download date* ("obtained on or after
  2026-08-12"), which breaks once the `last-cc-by-4.0` tag/release keeps
  the historical version obtainable indefinitely. Reworded around
  *which version* rather than *when obtained*. Also corrected the version
  range, which had dropped `gold_v1.0` (published in the same commit,
  `1cb3490`, that first set CC-BY-4.0).
