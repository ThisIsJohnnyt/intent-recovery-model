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
  must distribute your contributions under this same license.

No additional restrictions — you may not apply legal terms or technological
measures that legally restrict others from doing anything the license
permits.

Full license text: https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en

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
