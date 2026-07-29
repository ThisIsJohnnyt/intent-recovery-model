"""Fine-tune FLAN-T5-base on the note-organizing task.

Usage:
    python prepare_data.py   # if you haven't already
    python train.py

Reads training/data/processed/{train,val}.jsonl (built by prepare_data.py),
fine-tunes google/flan-t5-base, and saves the result to
training/checkpoints/thoughtorganizer-flan-t5/final. Also runs the resulting
model against val.jsonl and real_eval.jsonl and prints how many outputs
contain all three well-formed section markers, so you can eyeball quality
before exporting to ONNX.
"""
import json
from pathlib import Path

import torch
from datasets import Dataset
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)

from prepare_data import ACTIONS_MARKER, BULLETS_MARKER, NARRATIVE_MARKER

BASE_MODEL = "google/flan-t5-base"
DATA_DIR = Path(__file__).parent / "data" / "processed"
OUTPUT_DIR = Path(__file__).parent / "checkpoints" / "thoughtorganizer-flan-t5"
MAX_INPUT_TOKENS = 512
MAX_TARGET_TOKENS = 512
# Mirrors src/services/modelLoader.ts's streamFromModel default: bounds
# worst-case runaway generation for a model that hasn't reliably learned to
# emit EOS. no_repeat_ngram_size was tried and rejected — it corrupts the
# literal ###MARKER### delimiters instead of stopping the loop.
GENERATION_MAX_NEW_TOKENS = 300


def load_split(name: str) -> Dataset:
    path = DATA_DIR / name
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return Dataset.from_list(records)


def main() -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL).to(device)

    train_ds = load_split("train.jsonl")
    val_ds = load_split("val.jsonl")
    print(f"train examples: {len(train_ds)}, val examples: {len(val_ds)}")

    def tokenize(batch):
        inputs = tokenizer(
            batch["prompt"], max_length=MAX_INPUT_TOKENS, truncation=True, padding=False
        )
        labels = tokenizer(
            text_target=batch["target"], max_length=MAX_TARGET_TOKENS, truncation=True, padding=False
        )
        inputs["labels"] = labels["input_ids"]
        return inputs

    train_tok = train_ds.map(tokenize, batched=True, remove_columns=train_ds.column_names)
    val_tok = val_ds.map(tokenize, batched=True, remove_columns=val_ds.column_names)

    collator = DataCollatorForSeq2Seq(tokenizer, model=model)

    args = Seq2SeqTrainingArguments(
        output_dir=str(OUTPUT_DIR),
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        # Scaled down from 100 (tuned for the ~15-example placeholder fixture)
        # given 36 real training examples now (datasets/gold v1.0-v1.2
        # consolidated) — roughly matches the total gradient-step budget that
        # produced a working checkpoint on the fixture. Still far from "a few
        # hundred+" examples, so this isn't the final tuning point — with a
        # much larger real dataset, lower substantially further (8-15) and
        # watch eval_loss instead of holding step count constant.
        num_train_epochs=40,
        learning_rate=3e-4,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        # False, not True: with only a handful of val examples, eval_loss is
        # noisy enough that "best" by loss isn't "best" semantically. The
        # gold_v1.2.1 run's checkpoint-26 (epoch 2, lowest eval_loss) was
        # selected over checkpoint-520 (epoch 40) and was measurably worse on
        # every semantic dimension in gold_v1.2.1_lessons_learned.md's probe
        # suite (missed markers, misattribution, invented answers) despite
        # its lower loss. Revisit once real_holdout.jsonl or a larger val
        # split makes eval_loss a trustworthy signal again.
        load_best_model_at_end=False,
        predict_with_generate=True,
        generation_max_length=MAX_TARGET_TOKENS,
        # T5 is known to produce NaN losses under fp16 mixed precision; bf16 is stable
        # and the RTX 50-series (Blackwell) supports it natively.
        bf16=(device == "cuda"),
        logging_steps=5,
        report_to=[],
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=args,
        train_dataset=train_tok,
        eval_dataset=val_tok,
        data_collator=collator,
        tokenizer=tokenizer,
    )

    trainer.train()

    final_dir = OUTPUT_DIR / "final"
    trainer.save_model(str(final_dir))
    tokenizer.save_pretrained(str(final_dir))
    print(f"Saved fine-tuned model to {final_dir}")

    evaluate_format_validity(model, tokenizer, device, "val", val_ds)

    real_eval_path = DATA_DIR / "real_eval.jsonl"
    if real_eval_path.exists() and real_eval_path.read_text(encoding="utf-8").strip():
        real_eval_ds = load_split("real_eval.jsonl")
        evaluate_format_validity(model, tokenizer, device, "real_eval", real_eval_ds)
    else:
        print("\n(no real_eval.jsonl examples yet — add your real notes to see how this generalizes)")


def evaluate_format_validity(model, tokenizer, device, split_name: str, dataset: Dataset) -> None:
    if len(dataset) == 0:
        return
    print(f"\n=== Evaluating on {split_name} ({len(dataset)} examples) ===")
    valid_count = 0
    for i, record in enumerate(dataset):
        inputs = tokenizer(record["prompt"], return_tensors="pt", truncation=True, max_length=MAX_INPUT_TOKENS).to(
            device
        )
        output_ids = model.generate(
            **inputs,
            max_new_tokens=GENERATION_MAX_NEW_TOKENS,
            repetition_penalty=1.3,
        )
        generated = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        narrative_idx = generated.find(NARRATIVE_MARKER)
        bullets_idx = generated.find(BULLETS_MARKER)
        actions_idx = generated.find(ACTIONS_MARKER)
        is_valid = (
            narrative_idx != -1
            and bullets_idx != -1
            and actions_idx != -1
            and narrative_idx < bullets_idx < actions_idx
            and generated[narrative_idx + len(NARRATIVE_MARKER) : bullets_idx].strip() != ""
        )
        valid_count += int(is_valid)
        print(f"[{i}] valid_format={is_valid}\n  generated: {generated[:300]}")
    print(f"{split_name}: {valid_count}/{len(dataset)} produced well-formed marker sections")


if __name__ == "__main__":
    main()
