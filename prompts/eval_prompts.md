# Step 3b-3c: prompts for writing the evaluation questions

These prompts make the **final** (175) and **dev** (85) question sets. They are written by a
different model from the one that wrote the units (Chapter IV units: Claude Opus 5.5), so the
questions and the training data are not phrased alike. Use **ChatGPT**.

## How to run them
1. Use a **new chat for every prompt** (13 chats). Turn memory off or use a Temporary Chat, so
   nothing from the screening questions or other chats leaks in.
2. Attach the file in the "Attach" column, paste the prompt file's contents, and send.
3. Download the file ChatGPT creates and save it in `eval/raw/` under the name in the
   "Save as" column. If it gives a code block instead, paste it into that file.
4. Write down the **exact model name** shown in ChatGPT (and the date) for every chat; it goes in
   the `written_by` field.
5. Do not edit the questions by hand without noting it; the checker (`scripts/check_evalset.py`)
   reports problems and you regenerate or fix them.

| Prompt (`prompts/eval/`) | Attach | Final | Dev | Save as (`eval/raw/`) |
|---|---|---|---|---|
| `knowledge_ch01.txt` | `data/chapters/ch01.txt` | 5 | 2 | `knowledge_ch01.jsonl` |
| `knowledge_ch02.txt` | `data/chapters/ch02.txt` | 13 | 5 | `knowledge_ch02.jsonl` |
| `knowledge_ch03.txt` | `data/chapters/ch03.txt` | 4 | 2 | `knowledge_ch03.jsonl` |
| `knowledge_ch04.txt` | `data/chapters/ch04.txt` | 3 | 1 | `knowledge_ch04.jsonl` |
| `knowledge_ch05.txt` | `data/chapters/ch05.txt` | 14 | 6 | `knowledge_ch05.jsonl` |
| `knowledge_ch06.txt` | `data/chapters/ch06.txt` | 7 | 3 | `knowledge_ch06.jsonl` |
| `knowledge_ch07.txt` | `data/chapters/ch07.txt` | 13 | 5 | `knowledge_ch07.jsonl` |
| `knowledge_ch08.txt` | `data/chapters/ch08.txt` | 13 | 5 | `knowledge_ch08.jsonl` |
| `knowledge_ch09.txt` | `data/chapters/ch09.txt` | 5 | 2 | `knowledge_ch09.jsonl` |
| `knowledge_ch10.txt` | `data/chapters/ch10.txt` | 22 | 8 | `knowledge_ch10.jsonl` |
| `knowledge_ch11.txt` | `data/chapters/ch11.txt` | 1 | 1 | `knowledge_ch11.jsonl` |
| `trap.txt` | `data/books/The Handbook of Soap Manufacture.txt` (original, with index) | 60 | 30 | `trap.jsonl` |
| `practical.txt` | nothing | 15 | 15 | `practical.jsonl` |
| **Total** | | **175** | **85** | |

Knowledge questions per chapter follow each chapter's share of the book's prose (48,387 words).

## Question format
- Knowledge and trap questions start with the fixed prefix: "In The Handbook of Soap Manufacture by W. H. Simmons and H. A. Appleton, ..."
- Practical questions never mention the book.
- IDs: `kf-NN-01` / `kd-NN-01` (knowledge final / dev, NN = chapter), `tf-01` / `td-01` (trap),
  `pf-01` / `pd-01` (practical).

## After all 13 files are in `eval/raw/`
Run the checker (to be written): counts, IDs, fields, prefix, verbatim supporting passages,
absence search for every trap term, and final/dev overlap. Then check every trap question by hand
against the full book (Step 3b) before the sets are frozen.
