# Qwen2.5-7B-Instruct LoRA pilot: teaching a model one book

A reproducible before/after experiment: fine-tune **Qwen2.5-7B-Instruct** with a
LoRA adapter on a public-domain book the base model barely knows, and measure
the effect with a blind, rule-based evaluation.

**Status: building the evaluation (Step 3).** No training has been done yet, so
there are no results yet.

## The book
*The Handbook of Soap Manufacture* by W. H. Simmons and H. A. Appleton
(Scott, Greenwood & Son, 1908), Project Gutenberg eBook
[#21724](https://www.gutenberg.org/ebooks/21724). Original file, cleaning script
and SHA-256 hashes: [`data/books/PROVENANCE.md`](data/books/PROVENANCE.md).

In a screening run, the base model answered 0 of 20 hard questions about this
book correctly.

## What is measured
The same three numbers are reported before and after fine-tuning:

| Metric | Questions | Good result |
|---|---|---|
| Correct answers on book knowledge | 100 | higher after training |
| Made-up answers on trap questions (things the book does not contain) | 60 | low |
| Refusals on practical questions that need no book | 15 | low |

Only fully correct knowledge answers count. Separate dev sets (40 / 30 / 15)
are used for tuning and checkpoint selection; the final 175 questions are never
used for tuning.

## Method (planned)
1. Split the book into about 400 knowledge units (facts, definitions,
   examples, links).
2. Write and freeze the evaluation sets, scoring rules and judge configuration
   before any training.
3. Baseline: run the untouched base model (GGUF q8_0 in ollama) on all
   questions.
4. Train a QLoRA adapter (Unsloth, fp16) on question-answer data generated
   from the units, plus refusal and rehearsal examples.
5. Merge the adapter on CPU (plain PEFT, bf16), convert to GGUF q8_0, and run
   the same questions with identical settings.
6. Judge the before and after answers together, shuffled and blind, with a
   model from another family (Claude Sonnet 5.5).

The only thing that differs between the before and after runs is the adapter.

## Repository layout
| Path | Contents |
|---|---|
| `data/books/` | original and cleaned book text, provenance, screening questions |
| `data/chapters/` | the book split into Chapters I-XI |
| `data/units/` | knowledge units (in progress) |
| `prompts/` | prompts used to write units and evaluation questions |
| `eval/raw/` | evaluation questions as written, with provenance and an edit log |
| `screening/` | screening run of the base model (book choice) |
| `scripts/` | cleaning, splitting, verification and pipeline scripts |
| `versions.md` | hardware, package and model versions |
| `requirements.lock`, `requirements-llamacpp.lock` | pinned environments |

## Reproducing
Two Python environments are used: `.venv` for training, merging and evaluation
(`pip install -r requirements.lock`), and `.venv-llamacpp` for GGUF conversion
only (llama.cpp's own requirements, pinned in `requirements-llamacpp.lock`).
Exact versions of every tool and model are in [`versions.md`](versions.md).
