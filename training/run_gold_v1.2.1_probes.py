"""Run the Gold v1.2.1 Semantic Live-Evaluation Suite's 16 probes against the
fine-tuned checkpoint and capture raw output + format validity.

Usage:
    python run_gold_v1.2.1_probes.py

Reads training/checkpoints/thoughtorganizer-flan-t5/final (the same
checkpoint exported to ONNX for the app), generates with the identical
prompt shape and generation settings train.py uses, and writes raw results
to gold_v1.2.1_probe_results.md for semantic scoring against each probe's
Expected Behavior (a separate step -- this script does not score semantics,
only captures what the model actually produced and whether the marker
format is well-formed).
"""
import json
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from prepare_data import ACTIONS_MARKER, BULLETS_MARKER, NARRATIVE_MARKER, build_prompt

CHECKPOINT_DIR = Path(__file__).parent / "checkpoints" / "thoughtorganizer-flan-t5" / "checkpoint-520"
MAX_INPUT_TOKENS = 512
GENERATION_MAX_NEW_TOKENS = 300

PROBES = [
    {"id": "01", "capability": "Interrupted/Nested Depth", "kind": "direct",
     "input": "Need to check whether the basement freezer—remind Kira to return the extension cord Sunday."},
    {"id": "02", "capability": "Interrupted/Nested Depth", "kind": "transfer",
     "input": "Figure out why the tablet keeps—put the donation box by the front door—back to the tablet, the screen goes black whenever the charger moves."},
    {"id": "03", "capability": "Interrupted/Nested Depth", "kind": "adversarial",
     "input": "Ask Celia whether the replacement cable arrived before driving to the office, not ask Celia and separately check the cable, that is one question. The break-room clock is slow again."},
    {"id": "04", "capability": "Multi-Person Attribution", "kind": "direct",
     "input": "Avery said Morgan moved the boxes to storage. Morgan has the inventory sheet. Ask Avery whether Morgan counted the damaged ones."},
    {"id": "05", "capability": "Multi-Person Attribution", "kind": "transfer",
     "input": "Nina said Cole left the charger with Priya, and Cole said Nina already backed up the photos. Send Priya the folder link. Did Nina back up every photo or only the edited ones?"},
    {"id": "06", "capability": "Multi-Person Attribution", "kind": "adversarial",
     "input": "Tessa told Rowan the permit was approved after she asked about it. She still needs the stamped copy, but I cannot tell whether “she” means Tessa or the inspector. Ask Rowan who needs it."},
    {"id": "07", "capability": "Open-Question Preservation", "kind": "direct",
     "input": "Did the refund actually reach the card? Save the confirmation page before closing the browser."},
    {"id": "08", "capability": "Open-Question Preservation", "kind": "transfer",
     "input": "Was the wet spot from the window or the plant? It was dry again by lunchtime. Put the recycling outside tonight."},
    {"id": "09", "capability": "Open-Question Preservation", "kind": "adversarial",
     "input": "Did I send the revised schedule to Imani or only save the draft, check sent mail—also need to think about the volunteer list, not sure what yet."},
    {"id": "10", "capability": "Task Retention", "kind": "direct",
     "input": "The rehearsal felt smoother and the shorter transitions probably helped, print the shipping label, but the final scene still dragged."},
    {"id": "11", "capability": "Task Retention", "kind": "transfer",
     "input": "Pay the registration fee, registration fee by Thursday, the garage light is flickering again and I am tired of dealing with it, do not forget the fee, text Jonah that I will call tomorrow."},
    {"id": "12", "capability": "Task Retention", "kind": "adversarial",
     "input": "The walkthrough ran late and the settings explanation was confusing, maybe the screenshots need captions, did Luca ever give Erin the account list, schedule the oil change, the room was too warm, account question still unresolved, and last thing replace the smoke-detector battery."},
    {"id": "13", "capability": "Regression: basic tasks", "kind": "regression",
     "input": "Pick up cat food after work. Email the signed form to the school."},
    {"id": "14", "capability": "Regression: zero action items", "kind": "regression",
     "input": "The bedroom fan makes a clicking sound at the lowest setting."},
    {"id": "15", "capability": "Regression: idea without commitment", "kind": "regression",
     "input": "Maybe build a simpler welcome screen with one large button."},
    {"id": "16", "capability": "Regression: dangling reference", "kind": "regression",
     "input": "Remember to ask them about the other one."},
]


def check_format_valid(generated: str) -> bool:
    narrative_idx = generated.find(NARRATIVE_MARKER)
    bullets_idx = generated.find(BULLETS_MARKER)
    actions_idx = generated.find(ACTIONS_MARKER)
    return (
        narrative_idx != -1
        and bullets_idx != -1
        and actions_idx != -1
        and narrative_idx < bullets_idx < actions_idx
        and generated[narrative_idx + len(NARRATIVE_MARKER) : bullets_idx].strip() != ""
    )


def main() -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    tokenizer = AutoTokenizer.from_pretrained(str(CHECKPOINT_DIR))
    model = AutoModelForSeq2SeqLM.from_pretrained(str(CHECKPOINT_DIR)).to(device)
    model.eval()

    results = []
    for probe in PROBES:
        prompt = build_prompt(probe["input"])
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=MAX_INPUT_TOKENS).to(device)
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=GENERATION_MAX_NEW_TOKENS,
                repetition_penalty=1.3,
            )
        generated = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        valid = check_format_valid(generated)
        results.append({**probe, "raw_output": generated, "format_valid": valid})
        print(f"[{probe['id']}] format_valid={valid}")

    out_path = Path(__file__).parent / "gold_v1.2.1_probe_results_epoch40.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote raw results to {out_path}")
    print(f"Format validity: {sum(r['format_valid'] for r in results)}/{len(results)}")


if __name__ == "__main__":
    main()
