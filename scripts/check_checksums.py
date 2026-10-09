import hashlib
import os

from huggingface_hub import HfApi

REPO = "Qwen/Qwen2.5-7B-Instruct"
REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
LOCAL_DIR = "models/qwen2.5-7b-instruct"

info = HfApi().model_info(REPO, revision=REVISION, files_metadata=True)
all_ok = True
for f in info.siblings:
    if not f.lfs:
        continue
    h = hashlib.sha256()
    with open(os.path.join(LOCAL_DIR, f.rfilename), "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 24), b""):
            h.update(chunk)
    ok = h.hexdigest() == f.lfs.sha256
    all_ok &= ok
    print(f"{f.rfilename}: {'OK' if ok else 'MISMATCH'}")
print("ALL OK" if all_ok else "SOME FILES ARE CORRUPTED: re-run hf download")
