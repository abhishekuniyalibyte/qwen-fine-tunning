"""Judge saved answers with the frozen judge config (Steps 4b, 4d, 5, 8, 10).

The system prompt is eval/judge/system_header.md + eval/scoring_rules.md + eval/toc.txt, word for
word, and is cached across requests. One answer per request. Outputs are validated (valid JSON, a
label allowed for the question type, known tags); only invalid or missing outputs are retried, up
to max_attempts. Anything still invalid is listed for blind manual review. Every attempt is logged.

The answers file needs `id`, `answer` and `done_reason`; its `question_id` (default: `id`) links to
the questions file. In Step 10 the IDs are random, so the judge never sees whether an answer is
from before or after training.

Usage:
  python scripts/judge.py --answers runs/baseline/final_answers.jsonl --questions eval/final.jsonl \
      --out runs/baseline/final_judge_pass1.jsonl
  add --sync to call the API directly instead of the Batches API (for small test runs)
  add --show ID to print the request for one answer and exit (no API call)
"""
import argparse
import datetime
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "eval/judge/config.json").read_text(encoding="utf-8"))
SYSTEM = "\n\n".join((ROOT / p).read_text(encoding="utf-8").strip() for p in CONFIG["system_prompt"][:2])
SYSTEM += "\n\n## Table of contents of the book\n\n" + (ROOT / CONFIG["system_prompt"][2]).read_text(encoding="utf-8").strip()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def user_message(q, a):
    status = ("TRUNCATED: the answer was stopped by the length limit" if a["done_reason"] == "length"
              else "complete (not cut off)")
    parts = [f"Question type: {q['type']}", f"Question: {q['question']}"]
    if q["type"] == "knowledge":
        parts += [f"Reference answer: {q['reference_answer']}",
                  "Required key points:\n" + "\n".join(f"- {k}" for k in q["required_key_points"]),
                  f"Supporting passage from the book:\n{q['supporting_passage']}"]
    elif q["type"] == "trap":
        parts += ["Verified status: the information this question asks for is verified absent from the book "
                  "(full-text search and a manual check).",
                  f"Expected behaviour: {q['expected_behavior']}"]
    else:
        parts += ["Note: this is a general question that does not ask about the book. The model should answer it normally."]
    parts += [f"Answer status: {status}", f"<answer>\n{a['answer']}\n</answer>"]
    return "\n\n".join(parts)


def request_params(q, a):
    return {
        "model": CONFIG["model"],
        "max_tokens": CONFIG["max_tokens"],
        "system": [{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user_message(q, a)}],
        "output_config": {"effort": CONFIG["effort"],
                          "format": {"type": "json_schema", "schema": CONFIG["output_schema"]}},
    }


def validate(qtype, msg):
    """Return (parsed output, None) or (None, reason it is invalid)."""
    if msg.stop_reason != "end_turn":
        return None, f"stop_reason {msg.stop_reason}"
    text = next((b.text for b in msg.content if b.type == "text"), "")
    try:
        out = json.loads(text)
    except json.JSONDecodeError as e:
        return None, f"invalid JSON: {e}"
    if out.get("label") not in CONFIG["allowed_labels"][qtype]:
        return None, f"label {out.get('label')!r} not allowed for {qtype}"
    if not isinstance(out.get("tags"), list) or any(t not in CONFIG["allowed_tags"] for t in out["tags"]):
        return None, f"bad tags {out.get('tags')!r}"
    if not isinstance(out.get("reasoning"), str):
        return None, "missing reasoning"
    return out, None


def usage(msg):
    u = msg.usage
    return {k: getattr(u, k, None) for k in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")}


def run_sync(client, todo):
    results = {}
    for rid, params in todo.items():
        try:
            results[rid] = ("ok", client.messages.create(**params))
        except Exception as e:  # logged and retried
            results[rid] = ("error", str(e))
    return results


def run_batch(client, todo):
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request
    batch = client.messages.batches.create(requests=[
        Request(custom_id=rid, params=MessageCreateParamsNonStreaming(**params)) for rid, params in todo.items()])
    print(f"batch {batch.id}: {len(todo)} requests")
    while True:
        batch = client.messages.batches.retrieve(batch.id)
        if batch.processing_status == "ended":
            break
        c = batch.request_counts
        print(f"  {now()} processing {c.processing}, succeeded {c.succeeded}, errored {c.errored}")
        time.sleep(60)
    results = {}
    for r in client.messages.batches.results(batch.id):
        if r.result.type == "succeeded":
            results[r.custom_id] = ("ok", r.result.message)
        else:
            err = getattr(r.result, "error", None)
            results[r.custom_id] = ("error", f"{r.result.type}: {err}")
    return results


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--answers", required=True)
    p.add_argument("--questions", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--sync", action="store_true")
    p.add_argument("--show")
    a = p.parse_args()

    questions = {q["id"]: q for q in map(json.loads, (ROOT / a.questions).read_text(encoding="utf-8").splitlines()) if q}
    answers = {r["id"]: r for r in map(json.loads, (ROOT / a.answers).read_text(encoding="utf-8").splitlines()) if r}
    qof = {rid: questions[r.get("question_id", rid)] for rid, r in answers.items()}

    if a.show:
        print("=== SYSTEM ===\n" + SYSTEM + "\n\n=== USER ===\n" + user_message(qof[a.show], answers[a.show]))
        return

    import os
    import anthropic
    env = ROOT / ".env"  # ANTHROPIC_API_KEY=...; never committed
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            k, sep, v = line.partition("=")
            if sep and not k.strip().startswith("#"):
                os.environ.setdefault(k.strip(), v.strip().strip('"'))
    client = anthropic.Anthropic()
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    log = out.with_suffix(".log.jsonl")
    done = {}
    if out.exists():
        done = {r["id"]: r for r in map(json.loads, out.read_text(encoding="utf-8").splitlines())}
    print(f"{len(answers)} answers, {len(done)} already judged")

    for attempt in range(1, CONFIG["max_attempts"] + 1):
        todo = {rid: request_params(qof[rid], answers[rid]) for rid in answers if rid not in done}
        if not todo:
            break
        print(f"attempt {attempt}: {len(todo)} to judge")
        results = run_sync(client, todo) if a.sync else run_batch(client, todo)
        with out.open("a", encoding="utf-8") as fo, log.open("a", encoding="utf-8") as fl:
            for rid in todo:
                status, payload = results.get(rid, ("error", "no result returned"))
                entry = {"id": rid, "attempt": attempt, "time": now()}
                if status == "ok":
                    parsed, problem = validate(qof[rid]["type"], payload)
                    entry["usage"] = usage(payload)
                    if parsed:
                        row = {"id": rid, "question_id": qof[rid]["id"], "type": qof[rid]["type"], **parsed,
                               "attempt": attempt, "model": payload.model, "time": entry["time"], "usage": entry["usage"]}
                        fo.write(json.dumps(row, ensure_ascii=False) + "\n")
                        done[rid] = row
                        entry["result"] = "ok"
                    else:
                        entry["result"] = f"invalid: {problem}"
                else:
                    entry["result"] = f"error: {payload}"
                fl.write(json.dumps(entry) + "\n")

    # Judge output validation (Step 4d)
    left = sorted(set(answers) - set(done))
    extra = sorted(set(done) - set(answers))
    labels = {}
    for r in done.values():
        labels[(r["type"], r["label"])] = labels.get((r["type"], r["label"]), 0) + 1
    for k in sorted(labels):
        print(f"  {k[0]:9} {k[1]:17} {labels[k]}")
    if extra:
        sys.exit(f"judge output has IDs not in the answers file: {extra}")
    if left:
        (out.with_suffix(".manual_review.txt")).write_text("\n".join(left) + "\n", encoding="utf-8")
        sys.exit(f"{len(left)} answers still invalid after {CONFIG['max_attempts']} attempts: blind manual review "
                 f"(list in {out.with_suffix('.manual_review.txt').name})")
    needs = sum(r["label"] == "needs_review" for r in done.values())
    print(f"judging valid: {len(done)} outputs, {needs} needs_review to resolve by hand")


if __name__ == "__main__":
    main()
