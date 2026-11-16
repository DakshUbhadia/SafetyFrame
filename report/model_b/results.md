# Model B framing generalization — Sprint 8

All 32 frozen C/S trajectories are terminal: 29 completed and 3 provider-failed across the same sixteen final tasks. Both turns use the unchanged frozen procedure and scoring.

Requested Model B ID: deepseek-v4-flash. Requested and returned IDs remain available per trajectory.

## Condition outcomes and missingness

| Condition | Completed / planned | Provider failures | Turn-2 mean [95% CI] | Turn-1 mean (observed N) | Mean repair gain | Turn-2 format failures |
|---|---:|---:|---|---:|---:|---:|
| C | 14/16 | 2 | 0.057 [0.000, 0.171] | 0.043 (n=14) | 0.014 | 13/14 |
| S | 15/16 | 1 | 0.227 [0.053, 0.440] | 0.163 (n=16) | 0.053 | 11/15 |

Turn-2 condition means and repair gains use completed trajectories. Turn-1 means retain every observed first turn, including a trajectory whose second turn later had a provider failure. Paired contrasts use only complete tasks; preserved-artifact scores remain separately available.

![Model B condition means](condition_means.png)

## Post-collection response-budget diagnostics

50/59 saved responses exhausted the entire configured output cap [8192] as reasoning and emitted no final text. All 59 observed responses have audited status metadata. Text-extraction mismatches: 0.

| Condition | Turn | Observed responses | File-format failures | Reasoning-only budget exhaustion |
|---|---:|---:|---:|---:|
| C | 1 | 14 | 13 | 13 |
| C | 2 | 14 | 13 | 13 |
| S | 1 | 16 | 13 | 13 |
| S | 2 | 15 | 11 | 11 |

The budget-exhausted responses report status incomplete and reason max_output_tokens; the raw payload has no final message text to recover. Under the frozen policy these are model-behavior format failures, retained as zero end-to-end TCS, separate from genuine provider failures. This post-collection diagnostic does not change scores, exclusions, token limits, or retries, and makes no new inference calls.

**Interpretation constraint:** reasoning-only budget exhaustion dominates this Model-B run. Only 1 task pairs have valid Turn-2 file formats in both conditions. The primary end-to-end gap therefore chiefly reflects whether final code was emitted under the frozen budget; it does not provide a clean comparison of coding correctness when both outputs are available. A different token/reasoning budget would require a separately registered follow-up, not replacement of these outcomes.

## Model-B framing estimate

BaselineSafetyGap_B = mean(C−S): **-0.200 [-0.431, 0.000]**, using 13 complete task pairs. Positive values favor capability framing. Intervals use 10,000 paired task resamples, seed 2026111509.

Matched condition means: C=0.062, S=0.262.

Zero-provider-utility sensitivity: -0.163 [-0.350, 0.000], N=16. Valid-format sensitivity: 0.000 [NA, NA], N=1.

![Every Model B task](task_framing_gap.png)

## Separate-model comparison

| Model | Complete pairs | Mean C−S [95% CI] | Matched C mean | Matched S mean |
|---|---:|---|---:|---:|
| A | 16 | 0.013 [-0.050, 0.100] | 0.825 | 0.812 |
| B | 13 | -0.200 [-0.431, 0.000] | 0.062 | 0.262 |

Requested model IDs: A: qwen3.5-397b; B: deepseek-v4-flash.

![Same tasks across both models](models_task_comparison.png)

These are separate fixed-system estimates on matched benign tasks, not a universal pooled language-model effect. Compare each model’s interval and per-task distribution; an interval spanning zero is inconclusive, and overlapping intervals do not establish that model effects are equal. Model A’s disclosure interaction and self-assessment belong to its separate factorial design; Model B has no CD/SD extension or prompted self-assessment in this frozen study.

## Provider outcomes and costs

- C terminal provider failure types: {'5xx': 2}.
- S terminal provider failure types: {'5xx': 1}.

Recorded outcomes: 87 attempts and 25 frozen-policy retries. Known reported cost: 0.061897 credits; known token-rate estimate: 0.066503 credits. 28 outcomes lack full usage. Unknown liabilities remain reserved; known charges are not independently verified account debits.

## Interpretation limits and reproducibility

The benchmark has sixteen self-reviewed tasks and limited pilot headroom. Ceiling/floor effects, format penalties, provider routing/version differences, missing pairs, and the broad framing package constrain interpretation. No result establishes intent or transfers automatically to other model families or safety workflows. Provider failures are missing in the primary model-behavior analysis and zero only in the labeled utility sensitivity.

The scored dataset omits response text and includes integrity digests. Raw outputs, public feedback, workspaces, hidden outcomes and identities remain under data/main. Model A’s reviewed numerical release is preserved unchanged.

~~~powershell
.\.venv\Scripts\python.exe -m analysis.model_b --dataset report/model_b/scored_dataset.json --output report/model_b_reproduced
~~~
