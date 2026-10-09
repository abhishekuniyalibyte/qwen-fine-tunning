import torch
from unsloth import FastLanguageModel

model, tok = FastLanguageModel.from_pretrained(
    model_name="models/qwen2.5-7b-instruct",   # local path, not the hub name
    max_seq_length=512,
    load_in_4bit=True,
    dtype=torch.float16,                       # Turing: no bf16
)
FastLanguageModel.for_inference(model)

msgs = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "In two sentences, what is a lathe used for?"},
]
inputs = tok.apply_chat_template(
    msgs, add_generation_prompt=True, return_tensors="pt", return_dict=True
).to("cuda")
out = model.generate(**inputs, max_new_tokens=80, do_sample=False)
print(tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True))
print(f"Peak VRAM: {torch.cuda.max_memory_allocated() / 1e9:.2f} GB")
