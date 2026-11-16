# Final analysis — Sprint 9

All 96 frozen trajectories are terminal: 90 completed and six provider-failed. The final analysis recomputes both turns from saved requirement outcomes and parsed claims, checks the original reviewed summaries, and preserves the pre-outcome settings and scoring.

## Prespecified result channels and sensitivities

| Model | Contrast | Estimand | Paired tasks | Estimate | 95% task-bootstrap interval |
|---|---|---|---:|---:|---|
| A | BaselineSafetyGap_A | primary | 16 | 0.0125 | [-0.0500, 0.1000] |
| A | BaselineSafetyGap_A | provider_utility | 16 | 0.0125 | [-0.0500, 0.1000] |
| A | BaselineSafetyGap_A | valid_format | 16 | 0.0125 | [-0.0500, 0.1000] |
| A | DisclosureFramingInteraction_A | primary | 14 | -0.1286 | [-0.2714, -0.0143] |
| A | DisclosureFramingInteraction_A | provider_utility | 16 | -0.0375 | [-0.2125, 0.1750] |
| A | DisclosureFramingInteraction_A | valid_format | 13 | -0.0769 | [-0.1692, 0.0000] |
| A | DisclosureEffect_C_A | primary | 14 | 0.0429 | [0.0000, 0.1143] |
| A | DisclosureEffect_C_A | provider_utility | 16 | -0.0500 | [-0.2125, 0.0750] |
| A | DisclosureEffect_C_A | valid_format | 14 | 0.0429 | [0.0000, 0.1143] |
| A | DisclosureEffect_S_A | primary | 15 | -0.0667 | [-0.2133, 0.0667] |
| A | DisclosureEffect_S_A | provider_utility | 16 | -0.0875 | [-0.2250, 0.0375] |
| A | DisclosureEffect_S_A | valid_format | 14 | -0.0143 | [-0.1286, 0.0857] |
| B | BaselineSafetyGap_B | primary | 13 | -0.2000 | [-0.4308, 0.0000] |
| B | BaselineSafetyGap_B | provider_utility | 16 | -0.1625 | [-0.3500, 0.0000] |
| B | BaselineSafetyGap_B | valid_format | 1 | 0.0000 | [NA, NA] |

Task is the independent unit. The 10,000 percentile bootstrap resamples retain complete matched conditions, use seed 2026111509 and sorted task IDs, and start an independent random stream for each contrast. Primary provider failures are missing; provider-utility sensitivity assigns them zero; valid-format sensitivity retains only tasks with all contributing Turn-2 transactions valid. N=1 does not support an interval. No models are pooled and no multiplicity-adjusted confirmatory p-values are claimed.

Condition means in conditions.csv use all completed trajectories. matched_means.csv records each contrast-specific subset; simple effects use different subsets from the complete-quadruple interaction.

## What these results support

Model A's C-minus-S estimate is 0.0125 [-0.0500, 0.1000], N=16. The interval includes zero and differences exceeding the frozen 0.05 practical threshold in either direction. This is inconclusive, not evidence of equivalence or absence of framing effects.

The Model A interaction is -0.1286 [-0.2714, -0.0143], N=14. Its provider-utility and valid-format sensitivities are weaker. One SD Turn-2 format failure scores zero end-to-end despite a fully passing preserved artifact. A robust mitigation or intent claim is unsupported.

**Model B limitation:** 50/59 observed replies exhausted all 8,192 output tokens on reasoning and emitted no final text. The audited metadata show no lost final text in extraction. There are 24/29 Turn-2 format failures and only one valid-format pair. The primary gap -0.2000 [-0.4308, 0.0000], N=13, chiefly reflects code emission under the fixed budget; it does not cleanly isolate coding correctness. Ten paired tasks tie, three favor S, none favor C. No poor outcomes were replaced or settings adjusted. The two fixed-model estimates cannot establish a universal model effect or a model-by-framing interaction.

## Self-assessment (Model A, Turn 2)

| Condition | Metric | Numerator / denominator | Micro | Equal-task macro | Defined tasks / observed tasks |
|---|---|---:|---:|---:|---:|
| CD | urdr_strict | 0/8 | 0.0000 | 0.0000 | 6/14 |
| CD | urdr_lenient | 0/8 | 0.0000 | 0.0000 | 6/14 |
| CD | false_completion_rate | 8/8 | 1.0000 | 1.0000 | 6/14 |
| CD | completion_precision | 62/70 | 0.8857 | 0.8857 | 14/14 |
| CD | unmet_disclosure_precision | 0/0 | NA | NA | 0/14 |
| SD | urdr_strict | 0/12 | 0.0000 | 0.0000 | 7/15 |
| SD | urdr_lenient | 0/12 | 0.0000 | 0.0000 | 7/15 |
| SD | false_completion_rate | 12/12 | 1.0000 | 1.0000 | 7/15 |
| SD | completion_precision | 63/75 | 0.8400 | 0.8400 | 15/15 |
| SD | unmet_disclosure_precision | 0/0 | NA | NA | 0/15 |

All 20 failed artifact requirements (8 CD, 12 SD) were claimed implemented. This is descriptive claim inaccuracy, not evidence of intent. Strict URDR counts not-fully-implemented; lenient URDR adds uncertain. Missing labels are never acknowledgements. Zero denominators remain JSON null, empty CSV, or NA. No requirement-independent significance tests are used. Both turns and all micro/macro denominators are in self_assessment.csv; B has no prompted self-assessment.

## Failures and repair

failures.csv separates observed format failures, absent responses and terminal provider failures by model, condition and turn. Provider-failed trajectory counts repeat across turns for context; terminal_provider_failures_at_turn is the count to sum across turns. No harness failure is unresolved. Artifact means are separate from end-to-end format-penalized scores.

| Model | Condition | Observed Turn 1 | Completed pairs | Turn-1 mean (all observed) | Turn-2 mean | Repair gain | Artifact repair |
|---|---|---:|---:|---:|---:|---:|---:|
| A | C | 16 | 16 | 0.8125 | 0.8250 | 0.0125 | 0.0125 |
| A | S | 16 | 16 | 0.7750 | 0.8125 | 0.0375 | 0.0375 |
| A | CD | 14 | 14 | 0.8429 | 0.8857 | 0.0429 | 0.0429 |
| A | SD | 15 | 15 | 0.8133 | 0.7733 | -0.0400 | 0.0267 |
| B | C | 14 | 14 | 0.0429 | 0.0571 | 0.0143 | 0.0571 |
| B | S | 16 | 15 | 0.1625 | 0.2267 | 0.0533 | 0.0533 |

Repair uses paired completed trajectories; subtracting all-observed Turn-1 means from completed-only Turn-2 means is invalid when a second turn has a provider failure. The optional repair figure separates preserved-code changes from format penalties.

## Figures

![Model A condition means](../figures/figure_1_condition_means.png)

![Every task framing gap](../figures/figure_2_task_framing.png)

![Disclosure effects and interaction](../figures/figure_3_disclosure_interaction.png)

![Self-assessment accuracy](../figures/figure_4_self_assessment.png)

![Secondary repair](../figures/figure_5_repair.png)

figure_data.json is the exact plotting input, selected from the exported tables. Each figure is available as PNG, SVG and PDF. Numerical outputs reproduce exactly; SVG/PDF generation timestamps are excluded from byte comparison.

## Reproduction and scope

~~~powershell
.\.venv\Scripts\python.exe -m analysis.primary
.\.venv\Scripts\python.exe scripts/finish_analysis.py
~~~

No inference calls, changed scores, new exclusions, additional tasks or unregistered experiments are introduced. The original Model A and B releases remain unchanged. The benchmark is small and self-reviewed, with limited pilot headroom, ceiling/floor effects and fixed provider systems. Independent validation and any larger-budget experiment belong to a separate follow-up. This completes Sprint 9 analysis; literature review, full paper and submission remain later sprints.
