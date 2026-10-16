# Raw evaluation questions: provenance

These files are the question-writing model's output, before merging into
`eval/final.jsonl` and `eval/dev.jsonl`. Hand edits are listed in `EDITS.md`.

## Writer
| Item | Value |
|---|---|
| Model | GPT-6, reasoning effort "Extra High", in the ChatGPT app |
| Mode | Temporary Chat, one new chat per prompt |
| Date | 2026-10-14 (knowledge files); 2026-10-16 (trap and practical files) |
| `written_by` value | `ChatGPT app, GPT-6 (Extra High), <date of the file>` |

The ChatGPT app shows no dated model snapshot, so the name above is the most
exact record available. The writer is a different model from the one that wrote
the knowledge units (Claude Opus 5.5), as Step 3b requires.

## Files
| File | Prompt | Attached | Questions |
|---|---|---|---|
| `knowledge_chNN.jsonl` (NN = 01-11) | `prompts/eval/knowledge_chNN.txt` | `data/chapters/chNN.txt` | 100 final + 40 dev in total |
| `trap.jsonl` | `prompts/eval/trap.txt` | `data/books/The Handbook of Soap Manufacture.txt` (original, with index) | 60 final + 30 dev |
| `practical.jsonl` | `prompts/eval/practical.txt` | nothing | 15 final + 15 dev |

Runs that were repeated with an improved prompt replaced the earlier file; the
prompt file in `prompts/eval/` is the version that produced the file here.
Corrections made through a follow-up message in the same chat (Chapter X) are
listed in `EDITS.md`.
