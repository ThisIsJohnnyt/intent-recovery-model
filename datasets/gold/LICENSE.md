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

## Effective date and prospective scope — read before assuming "permanently noncommercial" applies to a copy you already have

**CC BY-NC-SA 4.0 applies to versions of this dataset obtained on or after
2026-08-12.** It does not, and legally cannot, revoke the CC-BY-4.0 license
this dataset carried from 2026-07-28 to 2026-08-12 (commit `1cb3490` through
`2f7a101`, inclusive of `gold_v1.1` through `gold_v1.2.3`). CC licenses are
irrevocable once granted (CC BY 4.0 legal code §2(a)(1); confirmed against
the Creative Commons FAQ). **If you obtained a copy of this dataset during
that window, you retain your CC-BY-4.0 rights for that copy — including the
right to use it commercially — regardless of this later change.** This
project cannot and does not claim otherwise.

Only material first published on or after 2026-08-12, and any later
revision, is offered exclusively under CC BY-NC-SA 4.0.

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

- **2026-08-12**: changed from CC-BY-4.0 to CC BY-NC-SA 4.0 to match the
  project's settled policy — public, attribution-required, noncommercial
  throughout the downstream lineage, including forks. The prior CC-BY-4.0
  choice (set 2026-07-28, `1cb3490`) permitted unrestricted commercial reuse
  and was never the product of a deliberate commercial-use decision — no PDR
  backed it.
