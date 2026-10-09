"""Split the cleaned book into one file per chapter (Chapters I-XI).

The appendices (conversion tables) are left out on purpose.

Usage:
    python3 scripts/split_chapters.py data/books/soap_clean.txt data/chapters
"""
import os
import re
import sys

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]

src, out_dir = sys.argv[1], sys.argv[2]
with open(src, encoding="utf-8") as f:
    lines = f.read().splitlines()

# Each heading appears twice: first in the table of contents, then in the body
headings = {}
for i, line in enumerate(lines):
    m = re.match(r"^(CHAPTER ([IVXL]+)\.|APPENDIX A\.)$", line.strip())
    if m:
        headings.setdefault(m.group(1), []).append(i)
for name, where in headings.items():
    if len(where) != 2:
        raise SystemExit(f"Expected {name!r} twice (contents + body), found {len(where)}")

starts = [headings[f"CHAPTER {r}."][1] for r in ROMAN] + [headings["APPENDIX A."][1]]
os.makedirs(out_dir, exist_ok=True)
total = 0
for n, (roman, a, b) in enumerate(zip(ROMAN, starts, starts[1:]), start=1):
    text = "\n".join(lines[a:b]).strip() + "\n"
    path = os.path.join(out_dir, f"ch{n:02d}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    words = len(text.split())
    total += words
    title = next(line.strip() for line in lines[a + 1:a + 6] if line.strip())
    print(f"{path}: Chapter {roman} - {title} ({words} words)")
print(f"Total: {total} words")
