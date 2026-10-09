import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""  # force CPU

import resource
import shutil
import time

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM

BASE = "models/qwen2.5-7b-instruct"
ADAPTER = "models/smoke/adapter"
OUT = "models/smoke/merged"

start = time.time()
base = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.bfloat16, device_map="cpu")
model = PeftModel.from_pretrained(base, ADAPTER)   # fresh-process reload of the adapter
model = model.merge_and_unload()
model.save_pretrained(OUT)

# Use the base model's original config and tokenizer files: transformers 5 writes
# formats that llama.cpp's converter (transformers 4.57) can't read
for name in ["config.json", "generation_config.json", "tokenizer_config.json",
             "tokenizer.json", "vocab.json", "merges.txt"]:
    shutil.copy(os.path.join(BASE, name), os.path.join(OUT, name))
jinja = os.path.join(OUT, "chat_template.jinja")
if os.path.exists(jinja):
    os.remove(jinja)

peak_gb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6  # Linux reports KB
print(f"Merged in {time.time() - start:.0f}s, peak RAM {peak_gb:.1f} GB -> {OUT}")
