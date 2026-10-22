"""Check the raw evaluation questions and merge them into eval/final.jsonl and eval/dev.jsonl (Steps 3b-3c).

Errors stop the merge; warnings are printed for a manual look and do not stop it.
Each question gets `written_by` (Step 3b); each trap gets `verified_absent`, which is
true only if its box is ticked in eval/raw/trap_review.md (scripts/make_trap_review.py).

Usage:
  python scripts/check_evalset.py           # check, and write the merged files if there are no errors
  python scripts/check_evalset.py --check   # check only
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "eval/raw"
PREFIX = "In The Handbook of Soap Manufacture by W. H. Simmons and H. A. Appleton, "
BOOK_WORDS = ("handbook of soap", "simmons", "appleton", "the book", "the authors")
SCREENING = ROOT / "data/books/soap_manufacture_screening.csv"
WRITER = "ChatGPT app, GPT-6 (Extra High), {date}"
DATES = {"knowledge": "2026-10-14", "trap": "2026-10-16", "practical": "2026-10-16"}
EXPECTED = {  # (split, type) -> count; trap kinds checked separately
    ("final", "knowledge"): 100, ("final", "trap"): 60, ("final", "practical"): 15,
    ("dev", "knowledge"): 40, ("dev", "trap"): 30, ("dev", "practical"): 15,
}
TRAP_KINDS = {"final": {"absent_topic": 40, "absent_detail": 20}, "dev": {"absent_topic": 20, "absent_detail": 10}}
ID_RE = {"knowledge": r"k([fd])-(\d\d)-\d\d", "trap": r"t([fd])-\d\d", "practical": r"p([fd])-\d\d"}
FIELDS = {
    "knowledge": ["id", "split", "type", "chapter", "question", "reference_answer", "required_key_points", "supporting_passage"],
    "trap": ["id", "split", "type", "kind", "missing_item", "question", "reference_answer", "expected_behavior",
             "absence_search_terms", "required_key_points", "supporting_passage"],
    "practical": ["id", "split", "type", "question", "reference_answer", "required_key_points", "supporting_passage"],
}
SIMILAR = 0.5   # word-set overlap (Jaccard) above which two questions are listed for a manual look
PASSAGE_OVERLAP = 60  # shared characters above which two supporting passages count as overlapping

errors, warnings = [], []


def norm(s):
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip()


def words(s):
    s = norm(s).lower().replace(PREFIX.lower(), "")
    return {w for w in re.findall(r"[a-z0-9]+", s) if len(w) > 3}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a | b else 0.0


def shared_run(a, b):
    """Length of the longest common substring (dynamic programming, fine for passages of a few hundred chars)."""
    a, b = norm(a).lower(), norm(b).lower()
    best, prev = 0, [0] * (len(b) + 1)
    for ca in a:
        cur = [0]
        for j, cb in enumerate(b):
            cur.append(prev[j] + 1 if ca == cb else 0)
        best = max(best, max(cur))
        prev = cur
    return best


def load(path):
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                errors.append(f"{path.name}:{n}: invalid JSON ({e})")
    return rows


def edited_ids(rows_by_file):
    """IDs listed in EDITS.md (an 'all N' entry means every question in that file)."""
    ids = set()
    for line in (RAW / "EDITS.md").read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not re.match(r"\d{4}-\d\d-\d\d", cells[0]):
            continue
        if cells[2].startswith("all"):
            ids |= {r["id"] for r in rows_by_file.get(cells[1], [])}
        else:
            ids |= {i.strip() for i in cells[2].split(",")}
    return ids


def ticked_traps():
    path = RAW / "trap_review.md"
    if not path.exists():
        return None
    ticked, current = set(), None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"## (t[fd]-\d\d) ", line)
        if m:
            current = m.group(1)
        elif current and re.match(r"- \[[xX]\] Verified absent", line):
            ticked.add(current)
    return ticked


# Load
files = sorted(RAW.glob("knowledge_ch*.jsonl")) + [RAW / "trap.jsonl", RAW / "practical.jsonl"]
rows_by_file = {f.name: load(f) for f in files}
rows = [r for rs in rows_by_file.values() for r in rs]

# Per-question checks
seen = set()
for fname, rs in rows_by_file.items():
    for r in rs:
        rid, typ = r.get("id", "?"), r.get("type")
        if typ not in FIELDS:
            errors.append(f"{rid}: unknown type {typ!r}")
            continue
        missing = [k for k in FIELDS[typ] if k not in r]
        if missing:
            errors.append(f"{rid}: missing fields {missing}")
            continue
        if rid in seen:
            errors.append(f"{rid}: duplicate ID")
        seen.add(rid)
        m = re.fullmatch(ID_RE[typ], rid)
        if not m or {"f": "final", "d": "dev"}[m.group(1)] != r["split"]:
            errors.append(f"{rid}: ID does not match type {typ} / split {r['split']}")
        q = r["question"]
        if typ in ("knowledge", "trap"):
            if not q.startswith(PREFIX):
                errors.append(f"{rid}: question does not start with the fixed prefix")
            elif not q[len(PREFIX):][:1].islower():
                errors.append(f"{rid}: first letter after the prefix is not lower case")
        else:
            if any(w in q.lower() for w in BOOK_WORDS):
                errors.append(f"{rid}: practical question mentions the book")
        if not q.rstrip().endswith("?"):
            warnings.append(f"{rid}: question does not end with '?'")

        if typ == "knowledge":
            if not fname.endswith(f"ch{m.group(2) if m else '??'}.jsonl"):
                errors.append(f"{rid}: chapter number in the ID does not match file {fname}")
            if not r["required_key_points"]:
                errors.append(f"{rid}: no required key points")
            chapter = norm((ROOT / f"data/chapters/{fname[10:14]}.txt").read_text(encoding="utf-8"))
            if not r["supporting_passage"] or norm(r["supporting_passage"]) not in chapter:
                errors.append(f"{rid}: supporting passage is not verbatim in data/chapters/{fname[10:14]}.txt")
        else:
            if r["supporting_passage"] is not None or r["required_key_points"]:
                errors.append(f"{rid}: {typ} question must have supporting_passage null and no key points")
        if typ == "trap":
            if r["kind"] not in ("absent_topic", "absent_detail"):
                errors.append(f"{rid}: unknown trap kind {r['kind']!r}")
            if not r["expected_behavior"].startswith("abstain"):
                errors.append(f"{rid}: expected_behavior does not start with 'abstain'")

# Counts
for (split, typ), n in EXPECTED.items():
    got = sum(r.get("split") == split and r.get("type") == typ for r in rows)
    if got != n:
        errors.append(f"{split} {typ}: {got} questions, expected {n}")
for split, kinds in TRAP_KINDS.items():
    for kind, n in kinds.items():
        got = sum(r.get("split") == split and r.get("kind") == kind and r.get("type") == "trap" for r in rows)
        if got != n:
            errors.append(f"{split} {kind}: {got} traps, expected {n}")

# Overlap within the eval set (also dev vs final) and with the screening questions
valid = [r for r in rows if r.get("type") in FIELDS and "question" in r]
for i, a in enumerate(valid):
    for b in valid[i + 1:]:
        if a["type"] != b["type"]:
            continue
        j = jaccard(words(a["question"]), words(b["question"]))
        if j >= SIMILAR:
            warnings.append(f"{a['id']} / {b['id']}: similar questions (overlap {j:.2f})")
        if a["type"] == "knowledge" and a.get("chapter") == b.get("chapter"):
            k = shared_run(a["supporting_passage"], b["supporting_passage"])
            if k >= PASSAGE_OVERLAP:
                warnings.append(f"{a['id']} / {b['id']}: supporting passages share {k} characters")
        if a["type"] == "trap" and jaccard(words(a["missing_item"]), words(b["missing_item"])) >= SIMILAR:
            warnings.append(f"{a['id']} / {b['id']}: similar missing items ({a['missing_item']!r} / {b['missing_item']!r})")

with SCREENING.open(encoding="utf-8", newline="") as f:
    screening = list(csv.DictReader(f))
for s in screening:
    for r in valid:
        if r["type"] != "knowledge":
            continue
        j = jaccard(words(s["Question"]), words(r["question"]))
        if j >= SIMILAR:
            warnings.append(f"{r['id']}: similar to screening {s['ID']} (overlap {j:.2f})")
        k = shared_run(s["Exact supporting quotation"], r["supporting_passage"])
        if k >= PASSAGE_OVERLAP:
            warnings.append(f"{r['id']}: supporting passage shares {k} characters with screening {s['ID']}")

# Trap verification (hand check)
ticked = ticked_traps()
traps = [r for r in valid if r["type"] == "trap"]
if ticked is None:
    errors.append("eval/raw/trap_review.md not found: run scripts/make_trap_review.py and tick the checked traps")
else:
    unticked = [r["id"] for r in traps if r["id"] not in ticked]
    if unticked:
        errors.append(f"{len(unticked)} of {len(traps)} traps not ticked in trap_review.md: {', '.join(unticked)}")

# Report
for w in warnings:
    print("WARNING", w)
for e in errors:
    print("ERROR  ", e)
print(f"\n{len(rows)} questions, {len(errors)} errors, {len(warnings)} warnings")
if errors or "--check" in sys.argv:
    sys.exit(1 if errors else 0)

# Merge
edited = edited_ids(rows_by_file)
order = {"knowledge": 0, "trap": 1, "practical": 2}
for split in ("final", "dev"):
    out = []
    for r in sorted((r for r in rows if r["split"] == split), key=lambda r: (order[r["type"]], r["id"])):
        r = dict(r)
        r["written_by"] = WRITER.format(date=DATES[r["type"]]) + ("; edited, see eval/raw/EDITS.md" if r["id"] in edited else "")
        if r["type"] == "trap":
            r["verified_absent"] = r["id"] in ticked
        out.append(r)
    path = ROOT / f"eval/{split}.jsonl"
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out), encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}: {len(out)} questions")
