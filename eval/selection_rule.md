# Checkpoint-selection rule and experiment budget (v1)

Written before any trained-model dev result exists, and frozen with the rules v1 tag. These are the pilot's own
selection criteria; the client set no pilot threshold beyond the base model scoring 10/100 or less.

All numbers below come from the **dev sets** (40 knowledge, 30 trap, 15 practical), judged with the frozen judge
config and scoring rules, on the **merged q8_0 GGUF** of each checkpoint run through the frozen eval config. "Dev
baseline" means the base model's dev result from Step 5 (pass 1). The final 175 questions are never used for selection.

## Selection rule
1. **Filter:** drop any checkpoint whose dev practical refusals exceed the dev baseline + 1.
2. **Filter:** drop any checkpoint whose dev made-up answers (trap) exceed the dev baseline.
3. **Rank:** of the remaining checkpoints, pick the one with the most dev knowledge answers correct.
4. **Tie-break:** fewer dev made-up answers first, then the earlier checkpoint (earlier run, then earlier epoch).
5. If no checkpoint passes the filters, adjust the data or the training config and retrain, within the budget below.
   The rule is never relaxed after seeing results.

`needs_review` labels on dev answers are resolved by the same blind manual procedure as the final set before counting.

## Experiment budget (stopping rule)
| Item | Maximum |
|---|---|
| Training runs | 5 |
| Checkpoints evaluated on dev (merge + GGUF + dev run + judging) | 15 |
| Judge API spend, all steps together (baseline, dev evaluations, final) | USD 40 |
| GPU training time, all runs together | 40 hours |

- Every dev evaluation counts toward the budget. Each extra run reuses the small dev sets, so the dev numbers become
  less trustworthy; this is reported with the results.
- A log of every training run and dev evaluation is kept in `runs/experiment_log.md`, with its cost and the budget left.
- **If the budget runs out and no checkpoint passes the filters:** take the checkpoint ranked best by rule 3 among all
  evaluated checkpoints, run the final evaluation once, and report honestly that it failed the filters.
