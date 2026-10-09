# Book provenance

| Field | Value |
|---|---|
| Title | The Handbook of Soap Manufacture |
| Authors | W. H. Simmons and H. A. Appleton |
| Original publication | Scott, Greenwood & Son, London, 1908 |
| Source | Project Gutenberg eBook #21724 — https://www.gutenberg.org/ebooks/21724 |
| Gutenberg release | 7 June 2007; most recently updated 2 January 2021 |
| Downloaded file URL | TODO (the exact link you downloaded, e.g. the "Plain Text UTF-8" link) |
| Download date | TODO (your file is dated 2026-10-08) |

## Files
| File | Description | SHA-256 |
|---|---|---|
| `The Handbook of Soap Manufacture.txt` | original download, unchanged | `636894b6887bcd82740c86b906d0a861d9ec2c08895bfe8c9c0125875846ab21` |
| `soap_clean.txt` | cleaned text (63,922 words) | `5b6bda1e594902e2b081ec1785ca1ab90342cea61810e333f6a9027212f945cc` |

## Cleaning
Command:
    python3 scripts/clean_book.py "data/books/The Handbook of Soap Manufacture.txt" data/books/soap_clean.txt --last-line "THE END." --note-until "PREFACE"

Removed: Gutenberg header and footer, production credits, transcriber's notes, and everything after "THE END." (index and publisher's advertisements). The kept text is otherwise unchanged.
