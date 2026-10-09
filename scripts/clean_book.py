"""Clean a Project Gutenberg plain-text book.

Keeps the book's own text and removes what is not part of the book:
the Gutenberg header and footer, the production credits, the
transcriber's notes, and everything after the book's last line
(index, publisher's advertisements). The kept text is otherwise
unchanged, so quotes from the cleaned file match the original exactly.

Usage:
    python3 scripts/clean_book.py ORIGINAL.txt CLEANED.txt \
        --last-line "THE END." --note-until "PREFACE"
"""
import argparse
import hashlib
import re

START = re.compile(r"^\*\*\* START OF THE PROJECT GUTENBERG EBOOK .+ \*\*\*$")
END = re.compile(r"^\*\*\* END OF THE PROJECT GUTENBERG EBOOK .+ \*\*\*$")
NOTE_LINE = re.compile(r"^\s*\[Transcriber's note:.*\]\s*$", re.IGNORECASE)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_one(lines, test, what):
    hits = [i for i, line in enumerate(lines) if test(line)]
    if len(hits) != 1:
        raise SystemExit(f"Expected exactly one {what}, found {len(hits)}")
    return hits[0]


parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("original")
parser.add_argument("cleaned")
parser.add_argument("--last-line", required=True, help='last line of the book itself, e.g. "THE END."')
parser.add_argument("--note-until", help="heading right after the transcriber's note block, e.g. PREFACE")
args = parser.parse_args()

with open(args.original, encoding="utf-8") as f:
    lines = f.read().splitlines()

start = find_one(lines, START.match, "Gutenberg START line")
end = find_one(lines, END.match, "Gutenberg END line")
body = lines[start + 1:end]
original_words = sum(len(line.split()) for line in body)

# 1. Everything after the book's own last line (index, advertisements)
last = find_one(body, lambda line: line.strip() == args.last_line, f"last line {args.last_line!r}")
body = body[:last + 1]

# 2. Production credits: the first paragraph, if it starts with "Produced by"
first = next(i for i, line in enumerate(body) if line.strip())
if body[first].startswith("Produced by"):
    stop = first
    while stop < len(body) and body[stop].strip():
        stop += 1
    del body[first:stop]

# 3. Transcriber's note block before the book proper, and one-line [Transcriber's note: ...] remarks
if args.note_until:
    note = find_one(body, lambda line: line.strip().lower() == "transcriber's note:", "transcriber's note heading")
    after = [i for i in range(note + 1, len(body)) if body[i].strip() == args.note_until]
    if not after:
        raise SystemExit(f"No line {args.note_until!r} found after the transcriber's note")
    del body[note:after[0]]
body = [line for line in body if not NOTE_LINE.match(line)]

# 4. Leading and trailing blank lines
while body and not body[0].strip():
    body.pop(0)
while body and not body[-1].strip():
    body.pop()

text = "\n".join(body) + "\n"
with open(args.cleaned, "w", encoding="utf-8") as f:
    f.write(text)

print(f"Words between Gutenberg markers: {original_words}")
print(f"Words kept:                      {len(text.split())}")
print(f"First line: {body[0]!r}")
print(f"Last line:  {body[-1]!r}")
for word in ["gutenberg", "transcriber"]:
    print(f"'{word}' left in cleaned text: {text.lower().count(word)} (should be 0)")
print(f"SHA-256 original: {sha256(args.original)}")
print(f"SHA-256 cleaned:  {sha256(args.cleaned)}")
