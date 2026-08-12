# Third-Party Notices

This project's model releases build on `google/flan-t5-base`. This file documents
what was verified, what wasn't, and why — not just a blanket "we comply" claim.

## Upstream component: `google/flan-t5-base`

- **Source**: https://huggingface.co/google/flan-t5-base
- **License**: Apache License, Version 2.0. Verified directly by fetching the
  repository's file listing at `https://huggingface.co/google/flan-t5-base/tree/main`
  — it contains no standalone `LICENSE` or `NOTICE` file. The Apache 2.0
  designation comes from the repository's own metadata/model card, not a
  vendored license file at the source. Per Apache §4(d), since no NOTICE file
  exists at the source, there is nothing to reproduce under that clause — this
  is recorded as "none found," not assumed.
- **Full license text**: [`LICENSES/Apache-2.0.txt`](LICENSES/Apache-2.0.txt)
  (vendored verbatim from https://www.apache.org/licenses/LICENSE-2.0.txt).

### Exact revision used — disclosed gap, not asserted precision

Later experiments in this project (the seed-17 studies, `training/controlled_seed17_*`)
consistently pin `google/flan-t5-base` to Hugging Face snapshot revision
`7bcac572ce56db69c1ea7c8af255c5d7c9672fc2`, resolved via
`huggingface_hub.scan_cache_dir()` against the local cache.

**The original `v0.1.0` release (trained before 2026-07-29) does not have this
guarantee.** `training/train.py` loads the base model via
`AutoTokenizer.from_pretrained(BASE_MODEL)` / `AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL)`
with no explicit `revision` argument — confirmed by reading the script directly.
This means it resolved to whatever Hugging Face's `main` branch pointed to at
the time that specific training run happened, and that exact commit was never
recorded. The later revision-pinning discipline was adopted specifically
*because* of this gap, not retroactively confirmed for `v0.1.0`. Treat
`v0.1.0`'s exact base-model bytes as "google/flan-t5-base, exact revision not
recorded" rather than assuming it matches the later-pinned revision above.
`training/train.py` now pins that revision explicitly for all future runs
(see the commit that added this file).

## Provenance of released files (`intent-recovery-model-v0.1.0` and later)

Verified against `training/export_onnx.py` directly, and then checked further:
these files are copied via `shutil.copy()` from the fine-tuned model's
Hugging Face export directory (`export_onnx.py` line ~83), but "copied by
our script" is not the same as "byte-identical to Google's original." To
find out, the actual `v0.1.0` release assets were downloaded and hashed
against the same files at the later-pinned upstream revision
(`7bcac572ce56db69c1ea7c8af255c5d7c9672fc2` — not `v0.1.0`'s own exact
revision, which is unrecorded per above, but the closest verifiable
reference available):

| File | SHA-256 matches pinned upstream revision? |
|---|---|
| `spiece.model` | **Yes** — byte-identical. |
| `config.json` | **No.** |
| `generation_config.json` | **No.** |
| `special_tokens_map.json` | **No.** |
| `tokenizer.json` | **No.** |
| `tokenizer_config.json` | **No.** |

Diffing the two smaller files explains why: `config.json` and
`generation_config.json` gained fields (`classifier_dropout`,
`dense_act_fn`, `dtype`, `is_gated_act`) and changed `eos_token_id` from a
scalar to a list, all consistent with `save_pretrained()` reserializing
through a newer `transformers` version (`4.57.6` in the release vs.
`4.23.1`/`4.27.0.dev0` at the pinned upstream revision) — not a deliberate
edit, but a real change in bytes and, in places, content.

**Corrected provenance**, replacing the earlier blanket "not authored by
this project" claim:

| File | Provenance |
|---|---|
| `spiece.model` | Copied upstream binary; verified byte-identical to the later pinned reference (`v0.1.0`'s own exact upstream revision is unrecorded, so this is the closest available comparison, not a guarantee of identity to what `v0.1.0` specifically started from). |
| `config.json`, `generation_config.json`, `special_tokens_map.json`, `tokenizer.json`, `tokenizer_config.json` | Upstream-derived, but **reserialized** through this project's fine-tuning/export pipeline (`save_pretrained()` via a newer `transformers` version than Google's original upload used) — verified to differ byte-for-byte from the pinned upstream reference. Treated as modified/derived files under Apache §4(b), not unmodified Source form, unless byte-identity to the specific historical upstream revision is separately proven. |
| `encoder_model_quantized.onnx`, `decoder_model_merged_quantized.onnx` | Derivative Works under Apache 2.0's definition — exported to ONNX format and quantized from the fine-tuned model weights, which are themselves fine-tuned from `google/flan-t5-base`'s original weights. This project's contribution: the fine-tuning (via `datasets/gold/` training data) and the ONNX export/quantization transformation. |
| `intent-recovery-model-v0.1.0.manifest.json` | Project-created (SHA-256 checksums of the above). |

Per Apache §4(b), the reserialized configuration/tokenizer files above
count as modified files carrying prominent notices that they changed — this
table is that notice.

## What this means practically

- This project does not claim ownership of `google/flan-t5-base`'s tokenizer,
  configuration, or architecture. Those remain Google's, under Apache 2.0.
- This project's actual contribution — the fine-tuning process, the training
  data (`datasets/gold/`, see [PDR-006](docs/decisions/PDR-006.md)), and the
  ONNX export/quantization work — is what this project's own licensing terms
  apply to, not the upstream components wholesale.
- See [`MODEL_RELEASE_NOTICE.md`](MODEL_RELEASE_NOTICE.md) for why released
  model *weights* specifically are handled as a request rather than an
  asserted license, and [PDR-008](docs/decisions/PDR-008.md) for the full
  reasoning.
