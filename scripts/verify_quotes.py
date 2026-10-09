import csv
import re
import sys


def norm(s):
    for a, b in [("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("—", "-"), ("–", "-"), ("_", "")]:
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip().lower()


book_path, csv_path = sys.argv[1], sys.argv[2]
book = norm(open(book_path, encoding="utf-8").read())
with open(csv_path, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

ids = [r["ID"] for r in rows]
print(f"{len(rows)} rows, {len(set(ids))} unique IDs")
bad = 0
for r in rows:
    parts = [p for p in re.split(r"\s*(?:\.\.\.|…)\s*", r["Exact supporting quotation"]) if p.strip()]
    missing = [p for p in parts if norm(p) not in book]
    if missing:
        bad += 1
        print(f"{r['ID']}: NOT FOUND -> {missing[0][:100]!r}")
    else:
        print(f"{r['ID']}: OK")
print("ALL QUOTES VERIFIED" if bad == 0 else f"{bad} question(s) need fixing or replacing")
