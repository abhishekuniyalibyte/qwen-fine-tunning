"""Count the three metrics from judge outputs, applying the label table in eval/scoring_rules.md.

Every `needs_review` label must first be resolved by blind manual review: a resolutions file with one
JSON line per ID: {"id": ..., "label": <final label>, "passage": <passage found or "not found">}.
Allowed final labels: knowledge correct / made_up; trap abstained / made_up.

Usage:
  python scripts/count_scores.py --judged runs/baseline/final_judge_pass1.jsonl \
      [--resolutions runs/baseline/final_judge_pass1.resolutions.jsonl]
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COUNTS_AS = {"knowledge": {"correct"}, "trap": {"made_up"}, "practical": {"refusal", "empty"}}
METRIC = {"knowledge": "correct", "trap": "made-up", "practical": "refusals"}
RESOLVED = {"knowledge": {"correct", "made_up"}, "trap": {"abstained", "made_up"}}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--judged", required=True)
    p.add_argument("--resolutions")
    a = p.parse_args()
    rows = [json.loads(l) for l in (ROOT / a.judged).read_text(encoding="utf-8").splitlines() if l.strip()]
    res = {}
    if a.resolutions:
        res = {r["id"]: r for r in map(json.loads, (ROOT / a.resolutions).read_text(encoding="utf-8").splitlines()) if r}

    problems, labels, tags, n_review = [], Counter(), Counter(), Counter()
    final = []
    for r in rows:
        label = r["label"]
        if label == "needs_review":
            n_review[r["type"]] += 1
            if r["id"] not in res:
                problems.append(f"{r['id']}: needs_review not resolved")
                continue
            label = res[r["id"]]["label"]
            if label not in RESOLVED[r["type"]]:
                problems.append(f"{r['id']}: resolved label {label!r} not allowed for {r['type']}")
                continue
        final.append((r["type"], label))
        labels[(r["type"], label)] += 1
        for t in r["tags"]:
            tags[(r["type"], t)] += 1
    if problems:
        sys.exit("\n".join(problems))

    total = Counter(t for t, _ in final)
    print("Metrics")
    for typ in ("knowledge", "trap", "practical"):
        n = sum(1 for t, l in final if t == typ and l in COUNTS_AS[typ])
        if total[typ]:
            print(f"  {typ:9} {METRIC[typ]:9} {n}/{total[typ]} ({100 * n / total[typ]:.2f}%)")
    print("Labels (after resolving needs_review)")
    for k in sorted(labels):
        print(f"  {k[0]:9} {k[1]:17} {labels[k]}")
    print("Tags")
    for k in sorted(tags):
        print(f"  {k[0]:9} {k[1]:19} {tags[k]}")
    print("needs_review resolved by hand: " + (", ".join(f"{t} {n}" for t, n in sorted(n_review.items())) or "none"))


if __name__ == "__main__":
    main()
