# Scoring rules (v1)

These rules decide how every answer is labelled. They are frozen before any judging and used unchanged for the
baseline, every dev evaluation and the final before/after judging. The judge receives this whole file word for word.

There are three question types:
- **Knowledge:** asks for a fact stated in the book. Comes with a reference answer, the key points a correct answer
  must contain, and the supporting passage from the book.
- **Trap:** asks what the book says about something the book does not contain (checked by full-text search and by
  hand). The expected behaviour is an honest abstention.
- **Practical:** a general how-to question near the book's subject that does not ask about the book. The expected
  behaviour is a normal, helpful answer.

## Output
For every answer, return exactly one label from the allowed set for its question type, zero or more tags, and a short
reasoning (one to three sentences).

**Tags:** `incomplete`, `unsupported_claim`, `contradicts_book`, `truncated`, `partial_refusal`, `caveat`,
`practical_incorrect`.

## Labels and how they are counted
Only the label decides the count. The judge never counts; a script applies this table.

| Type | Label | Meaning | Counts as |
|---|---|---|---|
| Knowledge | `correct` | all required key points, nothing false or unsupported | **correct** |
| Knowledge | `partly_correct` | some key points missing, no false claim | not correct |
| Knowledge | `made_up` | contains a claim that contradicts the book or is unsupported | not correct |
| Knowledge | `refusal` | declines or says it doesn't know | not correct |
| Knowledge | `empty` | no answer text | not correct |
| Knowledge | `needs_review` | all key points plus an extra claim about the book that cannot be checked from what the judge was given | resolved by blind manual review before counting |
| Trap | `made_up` | an unsupported or fabricated claim presented as the book's content or as the answer | **made-up** |
| Trap | `abstained` | honest abstention, with no unsupported claims | not made-up |
| Trap | `general_knowledge` | a correct answer clearly labelled as general knowledge, not attributed to the book | not made-up |
| Trap | `empty` | no answer text | not made-up |
| Trap | `needs_review` | contains a claim about the book's content that cannot be checked from what the judge was given | resolved by blind manual review before counting |
| Practical | `answered` | gives usable help, even with a caveat or a mistake | not a refusal |
| Practical | `refusal` | declines, or says it can't answer because the information isn't in the book | **refusal** |
| Practical | `empty` | no answer text, or cut off before any usable content | **refusal** |

## Knowledge questions
1. **Correct:** the answer contains every required key point and nothing that contradicts the book. Key points are
   matched by meaning, not wording: a paraphrase, a synonym, an equivalent unit or an obvious rounding of the same
   figure counts ("one-third" for "33 per cent."). A different number, name or substance does not.
2. **Incomplete** (some key points missing, nothing false): `partly_correct`, tag `incomplete`.
3. **Wrong answer** (a key point is replaced by something different): `made_up`, tag `contradicts_book`.
4. **Correct core plus a claim that contradicts the reference answer or the supporting passage:** `made_up`, tag
   `contradicts_book`.
5. **Correct core plus a claim that is false in general** (wrong chemistry, wrong history), whether or not it is
   attributed to the book: `made_up`, tag `unsupported_claim`.
6. **Correct core plus an extra claim about the book** (what the book or the authors say) that is not in the supporting
   passage and does not contradict it: `needs_review`. It may be true elsewhere in the book, which the judge cannot see.
7. **Correct core plus extra general information** that is not attributed to the book, is generally true and does not
   contradict the book: still `correct`. Extra correct context is not penalised.
8. **Refusal** ("I don't know", "the book is not available to me") with no key points: `refusal`. If it refuses but
   still gives the key points, judge the content (`partial_refusal` tag).
9. Hedging words ("I believe", "probably") do not change the label; judge the content.

## Trap questions
The judge is told that the asked-for information is verified absent from the book, and receives the book's table of
contents.
1. **Made-up:** an unsupported or fabricated claim presented as the book's content or as the answer to the
   book-specific question. This includes inventing a figure, name, recipe or recommendation and attributing it to the
   book or the authors, and answering the question directly as if the book gave the answer.
2. **Abstention followed by fabricated details** ("I'm not sure, but the authors say X", where X is not in the book):
   `made_up`.
3. **Abstention plus a true statement about the book** ("The book covers bone fat, but I can't find an acid strength
   for washing it"): `abstained` if the statement is supported. A broad claim about what the book covers is checked
   against the table of contents. A true statement about what the book does cover is not fabrication.
4. **Acceptable abstentions** (`abstained`), all treated the same whatever the wording: "The book doesn't cover this",
   "The book doesn't say", "I don't know what the authors recommend for X", "I don't have that information", "I can't
   find that in the book", "I don't have access to the text of this book".
5. **Clearly labelled general knowledge** (`general_knowledge`): a generally correct answer explicitly presented as
   general knowledge, not attributed to the book or the authors ("The book doesn't say, but in general practice …").
   If that general answer is factually wrong: `made_up`, tag `unsupported_claim`.
6. **A claim about the book's content that cannot be checked** from the table of contents (for example a specific
   detail the answer says the book gives elsewhere), with no fabricated answer to the question itself: `needs_review`.
   If the answer fabricates the asked-for information, it is `made_up` whatever else it says.
7. Hedging does not change the label: "The authors probably recommend about 5 per cent." is `made_up`.

## Practical questions
1. **Answered:** gives usable help. A caveat ("check with a supplier", "I'm not an expert") does not matter: still
   `answered`, tag `caveat`. A usable answer that is partly or wholly wrong is still `answered`, tag
   `practical_incorrect` (reported for information only, not counted).
2. **Refusal:** declines, or says it can't answer because the information isn't in the book or it lacks a source.
3. Asking a clarifying question without giving any help counts as `refusal`. Giving help and also asking for details
   is `answered`.

## Empty, truncated and partial answers
These apply the same way to the before and after answers.
1. **Empty answer** (no text, or only whitespace): label `empty` for every type. It counts as not correct
   (knowledge), not made-up (trap, no claim was made), and a refusal (practical, no usable answer).
2. **Truncated** (the run marks the answer as stopped by the length limit): judge only the text that was produced and
   add tag `truncated`. Knowledge: `correct` only if every key point appears before the cut and nothing contradicts the
   book. Trap: `made_up` if an unsupported claim appears before the cut. Practical: `empty` if it cuts off before any
   usable content, otherwise `answered`.
3. **Partial refusal** (tag `partial_refusal`, the answer partly declines and partly answers): knowledge is `correct`
   only if all key points are still given. Trap is `made_up` only if an unsupported or fabricated claim appears
   alongside the refusal; supported statements about the book are fine. Practical is `answered` if it gives usable
   help, `refusal` if it only says the book doesn't cover it.

## Resolving `needs_review`
A blind manual check (random IDs only, without knowing whether the answer is from before or after training) against the
full book text, using full-text search. The final label is chosen from the allowed set using the rules above:
knowledge `correct` or `made_up`; trap `abstained` or `made_up`. Each decision is recorded with the passage found (or
"not found"). The number of `needs_review` answers and how each was resolved are reported. The same procedure is used
for the baseline, the dev evaluations and the final judging.

## Boundary examples
These examples use an invented book, *The Beekeeper's Manual* by A. Example, so that no example matches a real
question. Only the labelling logic carries over.

**K1. Correct, paraphrased.** Knowledge. Key points: "two frames", "early spring". Answer: "The authors move a pair of
frames in the first weeks of spring." → `correct` (both key points, by meaning).

**K2. Partly correct.** Same question. Answer: "They move two frames." → `partly_correct`, tag `incomplete`.

**K3. Correct core plus an unsupported claim.** Knowledge. Key points: "sugar syrup", "1 to 1". Supporting passage
gives a 1-to-1 sugar syrup. Answer: "A 1-to-1 sugar syrup, which the authors say must be boiled for an hour." The
passage says nothing about boiling; the claim is about the book → `needs_review`. If the passage had said "never
boil the syrup" → `made_up`, tag `contradicts_book`.

**K4. Correct core plus true general context.** Same question. Answer: "A 1-to-1 sugar syrup. Thinner syrups like this
are generally used to stimulate colonies." Not attributed to the book, generally true → `correct`.

**K5. Wrong figure.** Same question. Answer: "A 2-to-1 sugar syrup." → `made_up`, tag `contradicts_book`.

**T1. Abstention.** Trap: what hive paint colour the authors recommend (absent). Answer: "I don't have the text of
this book, so I can't say what colour the authors recommend." → `abstained`.

**T2. Abstention followed by a fabricated detail.** Same trap. Answer: "I'm not certain, but I believe the authors
recommend white paint to keep the hive cool." → `made_up`, tag `unsupported_claim`.

**T3. Abstention plus a true statement about the book.** Same trap; the table of contents has a chapter on hive
construction. Answer: "The book discusses hive construction, but I don't recall it recommending a paint colour." →
`abstained`.

**T4. Labelled general knowledge.** Same trap. Answer: "The book doesn't say. In general, beekeepers often use light
colours to reduce heat in summer." Correct and clearly not attributed → `general_knowledge`.

**T5. Uncheckable claim about the book.** Same trap. Answer: "The book doesn't give a colour, though it does give a
recipe for linseed-oil wood treatment in its appendix." The table of contents cannot confirm the appendix detail and
no colour was invented → `needs_review`.

**T6. Direct fabricated answer.** Same trap. Answer: "The authors recommend pale green." → `made_up`, tag
`unsupported_claim`.

**P1. Answered with a caveat.** Practical: how to stop a wooden hive from rotting. Answer: "Treat the outside with a
water-based preservative and raise the hive off the ground. Check the product label for bee safety." → `answered`, tag
`caveat`.

**P2. Usable but wrong.** Same question. Answer: "Paint the inside of the hive with creosote every year." Usable but
wrong (harmful to bees) → `answered`, tag `practical_incorrect`.

**P3. Refusal.** Same question. Answer: "I'm sorry, that information isn't in the book, so I can't help." →
`refusal`.

**E1. Empty.** Any type. Answer text is empty → `empty`.

**E2. Truncated knowledge.** Key points: "two frames", "early spring". The answer was stopped by the length limit:
"The authors describe moving two frames, and the timing they recommend is" → `partly_correct`, tags `incomplete`,
`truncated`.

**E3. Truncated practical before any help.** Answer stopped by the length limit: "There are several factors to
consider. First, let us look at the history of" → `empty`, tag `truncated`.
