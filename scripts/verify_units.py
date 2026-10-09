"""Check unit files written by the AI, and optionally merge them.

Checks every unit for: valid JSON, required fields, allowed type, unique
and well-formed unit_id, chapter matching the ID, a verbatim
source_passage that exists in the book, and a self-contained statement.
Also warns about near-duplicate statements.

Coverage: for each chapter, measures how much of the chapter's prose
(headings and tables excluded) is covered by the units' source passages.
Coverage below --min-coverage is an error. Uncovered sentences are written
to <units folder>/chNN_uncovered.txt, ready to paste back to the AI.

Usage:
    python3 scripts/verify_units.py data/books/soap_clean.txt data/units/ch04.jsonl
    python3 scripts/verify_units.py data/books/soap_clean.txt data/units/ch*.jsonl \
        --write data/units.jsonl --written-by "MODEL NAME AND VERSION"
"""
import argparse
import difflib
import json
import os
import re
from collections import Counter

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
# Rough guide: about 1 unit per 55 words of prose (tables and headings excluded)
TARGETS = {"I": 41, "II": 115, "III": 40, "IV": 30, "V": 127, "VI": 61,
           "VII": 118, "VIII": 118, "IX": 48, "X": 183, "XI": 6}
TYPES = {"fact", "definition", "example", "link"}
FIELDS = ["unit_id", "chapter", "section", "type", "statement", "source_passage"]


def flat(s):
    for a, b in [("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("—", "-"), ("–", "-"), ("_", "")]:
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def norm(s):
    return flat(s).lower()


def prose_sentences(text):
    """Yield (start, end, sentence) for prose sentences, skipping headings and tables."""
    pos = 0
    for s in re.split(r"(?<=[.;:?!])\s+(?=[A-Z(\"'\[])", text):
        start = text.find(s, pos)
        pos = start + len(s)
        letters = sum(c.isalpha() for c in s)
        if "|" in s or len(s.split()) < 5 or s.upper() == s or letters < 0.6 * len(s):
            continue
        yield start, pos, s


def coverage(chapter_text, group):
    # Drop the chapter heading and the indented list of section titles under it
    lines = chapter_text.splitlines()
    i = seen = 0
    while i < len(lines) and seen < 2:  # "CHAPTER N." and the chapter title
        seen += bool(lines[i].strip())
        i += 1
    while i < len(lines) and (lines[i].startswith("    ") or not lines[i].strip()):
        i += 1  # the indented section-title list
    text = flat("\n".join(lines[i:]))
    low = text.lower()
    covered = bytearray(len(text))
    for u in group:
        p = norm(u["source_passage"])
        i = low.find(p)
        while p and i >= 0:
            covered[i:i + len(p)] = b"\x01" * len(p)
            i = low.find(p, i + 1)
    total = done = 0
    missed = []
    for start, end, s in prose_sentences(text):
        words = len(s.split())
        total += words
        if sum(covered[start:end]) >= 0.5 * (end - start):
            done += words
        else:
            missed.append(s)
    return (done / total if total else 1.0), missed


parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("book")
parser.add_argument("units", nargs="+")
parser.add_argument("--chapters-dir", default="data/chapters", help="folder with ch01.txt ... ch11.txt")
parser.add_argument("--min-coverage", type=float, default=0.85, help="minimum share of chapter prose covered")
parser.add_argument("--write", help="merged output file, written only if there are no errors")
parser.add_argument("--written-by", help="model name and version, added to every unit when merging")
args = parser.parse_args()

with open(args.book, encoding="utf-8") as f:
    book = norm(f.read())

units, errors, warnings = [], [], []
for path in args.units:
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, start=1):
            if not line.strip():
                continue
            where = f"{path}:{n}"
            try:
                u = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"{where}: invalid JSON ({e})")
                continue
            missing = [k for k in FIELDS if not str(u.get(k, "")).strip()]
            if missing:
                errors.append(f"{where}: missing or empty {missing}")
                continue
            uid = u["unit_id"]
            m = re.fullmatch(r"u(\d{2})-(\d{3})", uid)
            if not m:
                errors.append(f"{where}: bad unit_id {uid!r} (expected like u02-001)")
            elif not 1 <= int(m.group(1)) <= 11 or ROMAN[int(m.group(1)) - 1] != u["chapter"]:
                errors.append(f"{where}: {uid} does not match chapter {u['chapter']!r}")
            if u["type"] not in TYPES:
                errors.append(f"{where}: {uid} has type {u['type']!r}, allowed {sorted(TYPES)}")
            passage = u["source_passage"]
            if "..." in passage or "…" in passage:
                errors.append(f"{where}: {uid} source_passage contains '...'; it must be one continuous quote")
            elif norm(passage) not in book:
                errors.append(f"{where}: {uid} source_passage NOT FOUND in book: {passage[:80]!r}")
            statement = u["statement"].strip()
            words = len(statement.split())
            if words < 5 or words > 80:
                warnings.append(f"{where}: {uid} statement has {words} words")
            if re.match(r"^(it|this|these|they|he|she|its|such)\b", statement, re.IGNORECASE):
                warnings.append(f"{where}: {uid} statement starts with a pronoun, not self-contained: {statement[:60]!r}")
            units.append(u)

ids = Counter(u["unit_id"] for u in units)
errors += [f"duplicate unit_id {uid} ({c} times)" for uid, c in ids.items() if c > 1]

by_chapter = {}
for u in units:
    by_chapter.setdefault(u["chapter"], []).append(u)
for chapter, group in by_chapter.items():
    statements = [norm(u["statement"]) for u in group]
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            if difflib.SequenceMatcher(None, statements[i], statements[j]).ratio() > 0.85:
                warnings.append(f"near-duplicate statements: {group[i]['unit_id']} / {group[j]['unit_id']}")

gaps_dir = os.path.dirname(args.units[0]) or "."
print(f"Per chapter (unit count is a rough guide; coverage must be >= {args.min_coverage:.0%}):")
for number, r in enumerate(ROMAN, start=1):
    if r not in by_chapter and len(args.units) == 1:
        continue
    group = by_chapter.get(r, [])
    with open(os.path.join(args.chapters_dir, f"ch{number:02d}.txt"), encoding="utf-8") as f:
        share, missed = coverage(f.read(), group)
    gaps_file = os.path.join(gaps_dir, f"ch{number:02d}_uncovered.txt")
    if missed:
        with open(gaps_file, "w", encoding="utf-8") as f:
            f.write("".join(f"{k}. {s}\n" for k, s in enumerate(missed, start=1)))
    elif os.path.exists(gaps_file):
        os.remove(gaps_file)
    flag = "" if share >= args.min_coverage else "  <-- below minimum"
    print(f"  {r:5} {len(group):4} units (guide ~{TARGETS[r]})   coverage {share:4.0%}   uncovered sentences {len(missed)}{flag}")
    if share < args.min_coverage:
        errors.append(f"chapter {r}: coverage {share:.0%} is below {args.min_coverage:.0%}; uncovered sentences listed in {gaps_file}")
print(f"Types: {dict(Counter(u['type'] for u in units))}")
for w in warnings:
    print("WARNING:", w)
for e in errors:
    print("ERROR:", e)
print(f"{len(units)} units, {len(errors)} errors, {len(warnings)} warnings")

if args.write:
    if errors:
        raise SystemExit("Not writing merged file: fix the errors first")
    if not args.written_by:
        raise SystemExit("--written-by is required with --write")
    units.sort(key=lambda u: u["unit_id"])
    with open(args.write, "w", encoding="utf-8") as f:
        for u in units:
            u["written_by"] = args.written_by
            f.write(json.dumps(u, ensure_ascii=False) + "\n")
    print(f"Wrote {len(units)} units to {args.write}")
