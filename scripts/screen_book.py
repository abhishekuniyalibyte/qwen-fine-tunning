import csv
import json
import sys
import urllib.request

MODEL = "qwen2.5:7b-instruct-q8_0"
SYSTEM = "You are a helpful assistant."
OPTIONS = {"temperature": 0, "seed": 3407, "num_ctx": 4096, "num_predict": 512}


def ask(question):
    body = json.dumps({
        "model": MODEL,
        "stream": False,
        "options": OPTIONS,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": question},
        ],
    }).encode()
    req = urllib.request.Request("http://localhost:11434/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        resp = json.load(r)
    return resp["message"]["content"].strip(), resp.get("done_reason")


src, out = sys.argv[1], sys.argv[2]
with open(src, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
for row in rows:
    answer, reason = ask(row["Question"])
    row["Model answer"] = answer
    row["done_reason"] = reason
    print(f"{row['ID']}: {reason}, {len(answer)} chars")
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"Saved {len(rows)} answers to {out}")
