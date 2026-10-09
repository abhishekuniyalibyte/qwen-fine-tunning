import json
import time

import torch
from unsloth import FastLanguageModel
from unsloth.chat_templates import train_on_responses_only
from datasets import load_dataset
from trl import SFTConfig, SFTTrainer

BASE = "models/qwen2.5-7b-instruct"
DATA = "data/smoke_test.jsonl"
OUT = "models/smoke/adapter"
MAX_SEQ = 512
MAX_STEPS = 20

model, tok = FastLanguageModel.from_pretrained(
    model_name=BASE, max_seq_length=MAX_SEQ, load_in_4bit=True, dtype=torch.float16,
)
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    lora_alpha=16,
    lora_dropout=0,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    use_gradient_checkpointing="unsloth",
    random_state=3407,
)

ds = load_dataset("json", data_files=DATA, split="train")
ds = ds.map(lambda ex: {"text": tok.apply_chat_template(ex["messages"], tokenize=False)})
print("Formatted example:\n", ds[0]["text"])

trainer = SFTTrainer(
    model=model,
    processing_class=tok,
    train_dataset=ds,
    args=SFTConfig(
        output_dir="models/smoke/checkpoints",
        dataset_text_field="text",
        max_length=MAX_SEQ,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        max_steps=MAX_STEPS,
        learning_rate=2e-4,
        lr_scheduler_type="linear",
        warmup_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        fp16=True,
        bf16=False,
        logging_steps=1,
        seed=3407,
        save_strategy="no",
        report_to="none",
    ),
)
# Loss only on the assistant answer (including <|im_end|>), not on system/user tokens
trainer = train_on_responses_only(
    trainer,
    instruction_part="<|im_start|>user\n",
    response_part="<|im_start|>assistant\n",
)

row = trainer.train_dataset[0]
if "labels" in row:
    trained = [t for t in row["labels"] if t != -100]
    print("Tokens with loss (should be the answer + <|im_end|>):\n", repr(tok.decode(trained)))

torch.cuda.reset_peak_memory_stats()
start = time.time()
trainer.train()
elapsed = time.time() - start

model.save_pretrained(OUT)
tok.save_pretrained(OUT)

stats = {
    "steps": MAX_STEPS,
    "seconds_per_step": round(elapsed / MAX_STEPS, 2),
    "peak_vram_allocated_gb": round(torch.cuda.max_memory_allocated() / 1e9, 2),
    "peak_vram_reserved_gb": round(torch.cuda.max_memory_reserved() / 1e9, 2),
}
with open("models/smoke/train_stats.json", "w") as f:
    json.dump(stats, f, indent=2)
print(stats)
