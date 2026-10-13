# Step 3a: prompts for writing knowledge units (Process B)

Use one new chat per chapter, with the AI chosen for units (not the one that writes the evaluation sets).
Attach `data/chapters/chNN.txt`, then paste prompt 1 with the values from the table filled in
(ready-made copies are in `prompts/units/chNN_prompt.txt`).

Unit size (v2, 13 Oct): the client asked for 300-500 units for the whole book. The chapters have
48,387 words of prose (headings and tables excluded), so the target is about 1 unit per 120 words
of prose, about 400 units in total. {N} = prose words / 120; {MAX} = the larger of {N} + 2 and
{N} x 1.2. The sum of {MAX} is 488. (v1 asked for 1 unit per 55 words; Chapter IV came out at
64 units, about 5 times the v2 target.)

| File | {NN} | {ROMAN} | {TITLE} | {N} | {MAX} |
|---|---|---|---|---|---|
| ch01.txt | 01 | I | Introduction | 19 | 23 |
| ch02.txt | 02 | II | Constitution of Oils and Fats, and their Saponification | 52 | 62 |
| ch03.txt | 03 | III | Raw Materials used in Soap-making | 18 | 22 |
| ch04.txt | 04 | IV | Bleaching and Treatment of Raw Materials intended for Soap-making | 13 | 16 |
| ch05.txt | 05 | V | Soap-making | 58 | 70 |
| ch06.txt | 06 | VI | Treatment of Settled Soap | 28 | 34 |
| ch07.txt | 07 | VII | Toilet, Textile and Miscellaneous Soaps | 54 | 65 |
| ch08.txt | 08 | VIII | Soap Perfumes | 54 | 65 |
| ch09.txt | 09 | IX | Glycerine Manufacture and Purification | 22 | 26 |
| ch10.txt | 10 | X | Analysis of Raw Materials, Soap, and Glycerine | 84 | 101 |
| ch11.txt | 11 | XI | Statistics of the Soap Industry | 2 | 4 |

## Prompt 1: write the units

```
I am building a knowledge-unit file from one chapter of a public-domain
book, for a fine-tuning experiment.

Book: The Handbook of Soap Manufacture, by W. H. Simmons and H. A. Appleton (1908)
Chapter: {ROMAN} — {TITLE}
Attached: the full text of this chapter only.

Use only the attached chapter. Do not use outside knowledge.

Task: turn the chapter into knowledge units that together cover EVERY
substantive fact, quantity, step, condition and reason in the chapter,
in order from the first section to the last (including footnotes).
Write between {N} and {MAX} units; never more than {MAX}. To stay
within the limit, make units larger; never leave knowledge out. Skip
only sentences that carry no knowledge (pure transitions such as
"let us now consider ...").

A unit is one paragraph-sized, self-contained piece of knowledge from
the book: one topic (one substance, one stage of a process, one
property, one comparison), usually covered by 2-6 consecutive
sentences. A unit may contain several related facts about its topic.
Types (if a unit mixes kinds, choose the main one):
- fact: a specific claim, quantity, property, condition or step
- definition: what a term means as the book uses it
- example: a specific instance, recipe, formula or described procedure
- link: a relation the book states between two things (cause and
  effect, comparison, contrast, sequence, reason)

Rules:
1. One topic per unit. Group consecutive sentences about the same
   topic into one unit; start a new unit when the topic changes.
2. The statement must be self-contained: name the subject explicitly;
   never start with "It", "This", "They", "Such"; no "the above",
   "the following", "as mentioned".
3. Say only what the passage says. Keep all numbers, units (deg. Tw.,
   per cent., cwt.), names and qualifications exactly ("as a rule",
   "usually", "if the salt is pure"). Do not turn a conditional
   statement into a universal one. The statement is 1-4 sentences,
   at most 150 words.
4. source_passage: copy the continuous passage from the chapter that
   supports the statement, verbatim, character for character (1-6
   consecutive sentences). Every fact in the statement must be in this
   passage. No "..." and no paraphrase.
5. Procedures: one unit per stage of a procedure (a few closely linked
   steps), in the book's order. Name the process in every statement so
   each unit is self-contained.
6. Chemical equations: include the equation in the source_passage when
   the sentence is about it, and write the statement in words.
7. Large tables: take at most a few units from a table, only where one
   fact can be stated cleanly; prefer the prose.
8. Skip the list of section titles at the top of the chapter, figure
   captions, and references to figures.
9. No duplicates: two units must not state the same fact.

Output: JSON Lines only, one object per line, no commentary, no code fence:
{"unit_id": "u{NN}-001", "chapter": "{ROMAN}", "section": "<nearest section heading, as written>", "type": "fact", "statement": "...", "source_passage": "..."}

Number the units u{NN}-001, u{NN}-002, ... in chapter order. If the
output is too long for one reply, stop after a complete line; I will
say "continue" and you carry on the numbering.
```

## Prompt 2: fill the gaps (same chat)

Run `verify_units.py`. If coverage is below 85%, it writes the uncovered sentences to
`data/units/chNN_uncovered.txt`. Paste that file's contents into this prompt:

```
These sentences from the chapter are not yet covered by any unit:

<paste the contents of data/units/chNN_uncovered.txt here>

Create units for every one of them that carries knowledge (skip pure
transition sentences). Group consecutive sentences on the same topic
into one unit, and keep the chapter total at or below {MAX}. Same
rules and output format as before.
Continue the numbering from u{NN}-<next number>. JSON Lines only.
```

Append the new lines to the end of `data/units/chNN.jsonl` and run `verify_units.py` again.
Repeat until coverage is at least 85% and there are 0 errors.
