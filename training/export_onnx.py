"""Export a fine-tuned checkpoint to the ONNX layout a downstream application
(e.g. thought-organizer-app, via @xenova/transformers) expects, staged as a
release-ready bundle.

Usage:
    python export_onnx.py [checkpoint_dir] [output_name]

Defaults: checkpoint_dir=checkpoints/thoughtorganizer-flan-t5/final,
output_name=thoughtorganizer-flan-t5.

Produces training/releases/<output_name>/ (gitignored -- this repo doesn't
commit exported models directly; upload the directory's contents as a
GitHub Release's assets instead, per docs/decisions/PDR-003.md) with:
    config.json, generation_config.json, special_tokens_map.json,
    spiece.model, tokenizer.json, tokenizer_config.json
    onnx/encoder_model.onnx, onnx/encoder_model_quantized.onnx
    onnx/decoder_model_merged.onnx, onnx/decoder_model_merged_quantized.onnx
    manifest.json (sha256 + size for every file above -- everything a
    checksum manifest can state without a human decision; "release",
    "contract_version", "base_model", and "training_datasets" are left as
    placeholders since those are release-process decisions, not something
    to infer from the export)

This matches the layout @xenova/transformers reads for a local/self-hosted
text2text-generation pipeline (see node_modules/@xenova/transformers/src/models.js
and env.js: onnx/<fileName>[_quantized].onnx, quantized selected via the
`quantized: true` pipeline option, root-level model files loaded from
env.localModelPath + model name). See docs/inference-contract.md for the
versioned contract a release like this one satisfies.
"""
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

import onnx
from onnxruntime.quantization import QuantType, quantize_dynamic
from optimum.exporters.onnx import main_export

# The onnxruntime-web version bundled in @xenova/transformers (1.14.0) only
# supports up to ONNX IR version 8, but the currently-installed onnx/optimum
# export toolchain defaults to IR version 9 for models with subgraphs (e.g.
# the merged decoder's use-cache `If` branch) even though the actual opset
# used (18) doesn't require any IR9-only feature. Without this downgrade,
# loading the exported model in a browser fails with "Can't create a
# session" / "Unsupported model IR version: 9, max supported IR version: 8".
MAX_SUPPORTED_IR_VERSION = 8

ROOT_CONFIG_FILES = [
    "config.json",
    "generation_config.json",
    "special_tokens_map.json",
    "spiece.model",
    "tokenizer.json",
    "tokenizer_config.json",
]


def main() -> None:
    checkpoint_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "checkpoints" / "thoughtorganizer-flan-t5" / "final"
    output_name = sys.argv[2] if len(sys.argv) > 2 else "thoughtorganizer-flan-t5"
    dest_dir = Path(__file__).parent / "releases" / output_name

    if not checkpoint_dir.exists():
        print(f"Checkpoint not found: {checkpoint_dir}", file=sys.stderr)
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmp:
        export_dir = Path(tmp)
        print(f"Exporting {checkpoint_dir} to ONNX...")
        main_export(
            model_name_or_path=str(checkpoint_dir),
            output=export_dir,
            task="text2text-generation-with-past",
        )

        onnx_dir = dest_dir / "onnx"
        onnx_dir.mkdir(parents=True, exist_ok=True)

        for name in ROOT_CONFIG_FILES:
            shutil.copy(export_dir / name, dest_dir / name)

        # transformers.js's merged decoder handles both with/without past via
        # a use_cache_branch input, so decoder_model.onnx and
        # decoder_with_past_model.onnx are redundant and left out. The
        # unquantized encoder/decoder are only an intermediate input to
        # quantization below, not something the app ever loads (it always
        # requests quantized: true) — quantize straight from the temp export
        # dir instead of also copying the full-precision originals into dest.
        for onnx_name in ["encoder_model", "decoder_model_merged"]:
            src = export_dir / f"{onnx_name}.onnx"

            quantized_dst = onnx_dir / f"{onnx_name}_quantized.onnx"
            print(f"Quantizing {onnx_name}.onnx...")
            # decoder_model_merged's top-level graph is a single `If` node
            # (branching on the use-cache flag) with the real weights nested
            # inside its subgraphs; without EnableSubgraph, quantize_dynamic
            # silently skips them (produced a "quantized" file the same size
            # as the original).
            quantize_dynamic(
                str(src),
                str(quantized_dst),
                weight_type=QuantType.QUInt8,
                extra_options={"EnableSubgraph": True},
            )

            model = onnx.load(str(quantized_dst))
            if model.ir_version > MAX_SUPPORTED_IR_VERSION:
                model.ir_version = MAX_SUPPORTED_IR_VERSION
                onnx.checker.check_model(model)
                onnx.save(model, str(quantized_dst))

    manifest_path = dest_dir / "manifest.json"
    manifest = {
        "release": "REPLACE-ME e.g. intent-recovery-model-v0.2.0",
        "contract_version": "REPLACE-ME -- see docs/inference-contract.md",
        "files": [
            {
                "name": str(f.relative_to(dest_dir)).replace("\\", "/"),
                "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
                "size_bytes": f.stat().st_size,
            }
            for f in sorted(dest_dir.rglob("*"))
            if f.is_file()
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"\nDone. Model files written to {dest_dir}")
    for f in sorted(dest_dir.rglob("*")):
        if f.is_file() and f != manifest_path:
            print(f"  {f.relative_to(dest_dir)} ({f.stat().st_size / 1e6:.1f} MB)")
    print(
        f"\nWrote {manifest_path.name} with checksums for every file above. "
        "Fill in \"release\" and \"contract_version\" before uploading this "
        "directory's contents as a GitHub Release's assets."
    )


if __name__ == "__main__":
    main()
