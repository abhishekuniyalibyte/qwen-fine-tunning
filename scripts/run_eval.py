"""Ask the evaluated model every question in an eval file through ollama (Steps 4a, 4c, 5, 8, 9).

Builds an ollama model from a GGUF with the frozen eval config, asks each question in a fresh
conversation, and saves the raw answers. Answers already saved are never generated again; only
missing or failed IDs are retried, up to max_attempts each (Step 4c). Every attempt is logged.

Usage:
  python scripts/run_eval.py --gguf models/gguf/qwen2.5-7b-instruct-base-q8_0.gguf --name qwen-base \
      --questions eval/final.jsonl --out runs/baseline/final_answers.jsonl
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "eval/eval_config.json").read_text(encoding="utf-8"))
URL = "http://localhost:11434"
EXPECTED = {"eval/final.jsonl": {"knowledge": 100, "trap": 60, "practical": 15},
            "eval/dev.jsonl": {"knowledge": 40, "trap": 30, "practical": 15}}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def modelfile(gguf, out_dir):
    # Relative path: the project path contains spaces; ollama create runs from out_dir
    rel = os.path.relpath(Path(gguf).resolve(), out_dir.resolve())
    text = (ROOT / CONFIG["modelfile_template"]).read_text(encoding="utf-8").replace("__GGUF__", rel)
    lines = [text.rstrip(), f'SYSTEM """{CONFIG["system_prompt"]}"""']
    for k, v in CONFIG["options"].items():
        for item in (v if isinstance(v, list) else [v]):
            lines.append(f'PARAMETER {k} "{item}"' if isinstance(item, str) else f"PARAMETER {k} {item}")
    return "\n".join(lines) + "\n"


def create_model(gguf, name, out_dir):
    path = out_dir / f"Modelfile.{name}"
    path.write_text(modelfile(gguf, out_dir), encoding="utf-8")
    subprocess.run(["ollama", "create", name, "-f", path.name], check=True, cwd=out_dir)
    return path


def ask(name, question):
    body = json.dumps({
        "model": name,
        "stream": False,
        "options": CONFIG["options"],
        "messages": [{"role": "system", "content": CONFIG["system_prompt"]},
                     {"role": "user", "content": question}],
    }).encode()
    req = urllib.request.Request(f"{URL}/api/chat", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.load(r)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--gguf", required=True)
    p.add_argument("--name", required=True, help="ollama model name to create, e.g. qwen-base")
    p.add_argument("--questions", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()

    version = subprocess.run(["ollama", "--version"], capture_output=True, text=True).stdout.strip()
    if CONFIG["ollama_version"] not in version:
        sys.exit(f"ollama version {version!r} does not match the frozen {CONFIG['ollama_version']}")

    questions = [json.loads(l) for l in (ROOT / a.questions).read_text(encoding="utf-8").splitlines() if l.strip()]
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    log = out.with_suffix(".log.jsonl")
    done = {}
    if out.exists():
        for l in out.read_text(encoding="utf-8").splitlines():
            r = json.loads(l)
            done[r["id"]] = r
    # Attempts are counted per invocation: a rerun after fixing a failure retries only the failed IDs,
    # and the log keeps every attempt from every invocation
    attempts = {}

    mf = create_model(a.gguf, a.name, out.parent)
    print(f"created ollama model {a.name} from {mf.name}; {len(done)} answers already saved")

    with out.open("a", encoding="utf-8") as fo, log.open("a", encoding="utf-8") as fl:
        for q in questions:
            if q["id"] in done:
                continue
            while attempts.get(q["id"], 0) < CONFIG["max_attempts"]:
                attempts[q["id"]] = attempts.get(q["id"], 0) + 1
                entry = {"id": q["id"], "attempt": attempts[q["id"]], "time": now()}
                try:
                    r = ask(a.name, q["question"])
                    row = {"id": q["id"], "type": q["type"], "question": q["question"],
                           "answer": r["message"]["content"], "done_reason": r.get("done_reason"),
                           "prompt_eval_count": r.get("prompt_eval_count"), "eval_count": r.get("eval_count"),
                           "attempt": attempts[q["id"]], "model": a.name, "gguf": Path(a.gguf).name, "time": entry["time"]}
                    if row["done_reason"] not in ("stop", "length"):
                        raise RuntimeError(f"unexpected done_reason {row['done_reason']!r}")
                    entry["result"] = "ok"
                    fl.write(json.dumps(entry) + "\n"); fl.flush()
                    fo.write(json.dumps(row, ensure_ascii=False) + "\n"); fo.flush()
                    done[q["id"]] = row
                    print(f"{q['id']}: {row['done_reason']}, {row['eval_count']} tokens")
                    break
                except Exception as e:  # logged and retried; the run fails below if attempts run out
                    entry["result"] = f"error: {e}"
                    fl.write(json.dumps(entry) + "\n"); fl.flush()
                    print(f"{q['id']}: attempt {attempts[q['id']]} failed: {e}")

    # Run validation (Step 4c): exactly the expected IDs, no duplicates, nothing missing
    ids = [json.loads(l)["id"] for l in out.read_text(encoding="utf-8").splitlines()]
    missing = sorted({q["id"] for q in questions} - set(ids))
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    extra = sorted(set(ids) - {q["id"] for q in questions})
    counts = {}
    for q in questions:
        counts[q["type"]] = counts.get(q["type"], 0) + 1
    exp = EXPECTED.get(a.questions)
    problems = []
    if missing: problems.append(f"missing {missing}")
    if dupes: problems.append(f"duplicates {dupes}")
    if extra: problems.append(f"unexpected IDs {extra}")
    if exp and counts != exp: problems.append(f"question counts {counts}, expected {exp}")
    truncated = sum(done[i]["done_reason"] == "length" for i in done)
    if problems:
        sys.exit("RUN FAILED: " + "; ".join(problems) + ". Fix the cause, then rerun (only failed IDs are retried).")
    print(f"run valid: {len(ids)} answers, {truncated} truncated (done_reason=length)")


if __name__ == "__main__":
    main()
