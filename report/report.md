# SafetyFrame-Eval — Research Report Draft

> DRAFT: Model-A collection and initial analysis are complete: 61 completed trajectories and three terminal provider failures. Model-B generalization and the final report remain pending. All Model-A outcomes, missingness, and sensitivities are reported.

# Title

**SafetyFrame-Eval: Does AI-Safety Framing Change Technical Performance?**

Subtitle:  
**A matched-task study of framing sensitivity, requirement accounting, and requirement-level self-assessment**

## Abstract

**Problem.** [1–2 sentences on epistemic trust and safety framing.]

**Method (planned).** We plan to evaluate `[N]` functionally equivalent, domain-relabeled benign coding tasks. Model A will receive a 2×2 capability/safety × requirement-accounting design; Model B will receive a matched capability/safety comparison. Each trajectory will use a fixed two-turn implementation/repair protocol and hidden requirement-level scoring.

**Results.** [Report Model-A framing gap + CI.] [Model-B gap + CI.] [Interaction.] [Most important self-assessment result.]

**Conclusion.** [Narrow claim.]

**Limitation.** [One sentence.]

---

# 1. Introduction

Opening question:

> Can researchers trust that a model's apparent completion of technical work reflects actual completion when contextual framing changes?

Motivation:
- AI assistants increasingly support evaluation/research workflows.
- Framing may itself change behavior.
- Recent safety-framing evidence motivates external testing.
- Even without a framing effect, model self-assessment of incomplete work is epistemically important.

Research questions:
1. Does safety-domain framing change task completion relative to capability framing?
2. Does requirement accounting modify that relationship?
3. How accurately do models assess requirement-level completion?

Contributions:
- functionally equivalent domain-relabeled benchmark;
- Model-A factorial intervention;
- Model-B generalization comparison;
- claim-vs-hidden-ground-truth self-assessment dataset.

---

# 2. Related Work

## Safety-framing / underperformance
[OpenAI motivating study.]

## Evaluation awareness / metagaming
[Brief relevant work.]

## Honesty / omission / self-report
[MASK/MASK-OFF, self-incrimination, mistake disclosure.]

End with gap:
> Existing work motivates concern about framing and self-report, but does not answer whether a simple requirement-accounting intervention differentially changes safety-framed benign technical work in this matched design.

---

# 3. Methods

## 3.1 Task suite
- 16 validated tasks, locally preregistered and frozen before main outcomes
- Four each: evaluation ingestion, metrics/scoring, experiment management, monitoring/reporting
- Five requirements each; two editable files per task
- benign
- dual plausible
- calibrated with excluded pilot tasks

## 3.2 Functional matching and domain relabeling
Explain canonical rendering and equivalence audit.

Infrastructure implementation: one canonical task source plus YAML mappings
generates both framed variants, including domain names in code, paths, prose,
and tests. Round-trip text and normalized AST comparison are anchored to the
canonical source. A synthetic pair passes matched public and hidden reference
checks; it is excluded from scientific inference. Sprint 5 validates 16 final
pairs: all 96 public and 320 hidden reference checks pass across 32 variants,
and all 80 isolated API faults retain partial credit. Exact text/AST, prompt,
and length/identifier balance checks pass; naturalness and specification support
were reviewed by the author. Length diagnostics use a regex proxy, not model
tokenizers. Difficulty has not been measured on final target models. Sprint 6
locally preregisters and freezes the set, analysis policies, and randomized
96-trajectory plan; no main-study outcomes are available.
See [frozen study](../FROZEN_STUDY.md) and [benchmark evidence](../BENCHMARK.md).
Capability-only calibration completed five excluded trajectories:
four scored 1.00 and one scored 0.80 on both turns; a sixth stress task was
infeasible under provider/output limits. This is preliminary task-shape evidence,
not a framing result. See pilot_calibration.md for exclusions and costs.

## 3.3 Experimental conditions
Table: C, S, CD, SD.

## 3.4 Models
Sprint 1 setup: Python 3.13.7, standard-library preflight, configuration in config/study.json. Selected candidates: Qwen3.5-397B as Model A and DeepSeek V4 Flash as Model B; both completed setup calls at temperature 0 with an 8,192-token cap. GLM-5.2 was excluded after setup timeouts before study outcomes. The user reports 3,500 Adaption credits; published rates and token assumptions are recorded in ../SETUP.md. Coding-pilot validation, final study settings, account rate limits, and balance reconciliation remain pending. No main-study calls have been made.

Exact provider/model IDs and settings.

## 3.5 Two-turn protocol
Turn 1 → public feedback → Turn 2; hidden scores never revealed.

## 3.6 Scoring
Define TCS.

## 3.7 Primary estimands

\[
BaselineSafetyGap_A
\]

\[
DisclosureFramingInteraction_A
\]

\[
BaselineSafetyGap_B
\]

## 3.8 Self-assessment
Define URDR/FCR/precision.

## 3.9 Randomization and failures
Blocked order, fresh sessions, retry/exclusion policy.

## 3.10 Statistical analysis
Paired task bootstrap; task-level plots.

---

# 4. Results

## 4.1 Model-A framing sensitivity

All 16 baseline C/S pairs completed. Turn-2 mean end-to-end TCS was 0.825
in C and 0.8125 in S. The mean paired C−S estimate was 0.0125, with a
95% task-bootstrap interval [−0.050,0.100] from the frozen 10,000 resamples.
Thirteen tasks tied, one favored C, and two favored S. The interval includes
zero and practically meaningful effects; this does not establish no framing
effect or generalize beyond the tested benchmark and requested Qwen route.

![Every Model-A task](model_a/task_framing_gap.png)

The [initial results](model_a/results.md), [per-task table](model_a/model_a_task_differences.csv),
and [full scored dataset](model_a/scored_dataset.json) preserve every outcome.

## 4.2 Model-B generalization

Pending Sprint 8. No Model-B main-study calls or generalization estimates
are included in this Model-A report.

## 4.3 Requirement-accounting interaction

Three trajectories failed on Turn 1 after exhausting the frozen HTTP-5xx
retries: task_012 CD and task_015 CD/SD. Thus 61/64 trajectories completed,
with 122 successful recorded/scored responses. All three failure rows remain
in the dataset and are missing in the primary model-behavior analysis.

| Condition | Completed / planned | Overall Turn-2 TCS | TCS on 14 complete quadruples |
|---|---:|---:|---:|
| C | 16/16 | 0.8250 | 0.8429 |
| S | 16/16 | 0.8125 | 0.8714 |
| CD | 14/16 | 0.8857 | 0.8857 |
| SD | 15/16 | 0.7733 | 0.7857 |

The primary paired interaction, (SD−S)−(CD−C), is −0.1286
[−0.2714,−0.0143] on 14 complete quadruples. Secondary CD−C is 0.0429
[0.0000,0.1143] on 14 pairs; SD−S is −0.0667 [−0.2133,0.0667]
on 15 pairs. Different paired sample sizes explain why the secondary
differences do not subtract directly to the complete-quadruple interaction.

The negative primary interaction is sensitive to operational outcomes.
The preregistered zero-provider-utility sensitivity is −0.0375
[−0.2125,0.1750], N=16. The paired valid-format sensitivity is −0.0769
[−0.1692,0.0000], N=13. In task_004 SD, Turn 2 returned no parseable
full-file transaction; the frozen end-to-end policy assigned TCS zero even
though the retained Turn-1 artifact passed all requirements. Its artifact
TCS remained 1.0. This format event contributes materially to the primary
interaction. No scoring definitions or rerun choices were changed afterward.
The result does not support a robust mitigation or intent claim.

![Condition outcomes](model_a/condition_means.png)

## 4.4 Requirement-level self-assessment

| Turn-2 metric | CD | SD |
|---|---:|---:|
| Evaluated trajectories | 14 | 15 |
| Actually failed artifact requirements | 8 | 12 |
| Failed requirements claimed implemented | 8/8 | 12/12 |
| False-completion rate | 1.000 | 1.000 |
| Strict / lenient URDR | 0.000 / 0.000 | 0.000 / 0.000 |
| Completion precision | 62/70 = 0.886 | 63/75 = 0.840 |
| Unmet-disclosure precision | NA (0/0) | NA (0/0) |

All 145 recorded Turn-2 checklist entries were implemented claims; no unmet,
uncertain, or missing claims were recorded. All 20 actually failed artifact
requirements were claimed implemented. This is descriptive claim inaccuracy,
not evidence of intent or awareness of hidden failures. Ground truth here is
artifact requirement scoring, kept distinct from the end-to-end format penalty.
The [self-assessment table](model_a/model_a_self_assessment.csv) includes both
turns, micro/macro aggregation, and numerator/denominator counts. Requirements
are nested within tasks and were not treated as independent inferential units.

## 4.5 Repair dynamics

| Condition | Turn-1 TCS | Turn-2 TCS | Mean repair gain |
|---|---:|---:|---:|
| C | 0.8125 | 0.8250 | 0.0125 |
| S | 0.7750 | 0.8125 | 0.0375 |
| CD | 0.8429 | 0.8857 | 0.0429 |
| SD | 0.8133 | 0.7733 | −0.0400 |

Repair gain uses completed trajectories. The SD mean includes the single
Turn-2 format penalty described above; it should not be read as a pure change
in preserved-code correctness.

![Repair summary](model_a/repair_gain.png)

All 148 recorded attempts and 23 retries passed request-identity and retry-policy
audits. The 26 outcomes lacking full usage retain credit reservations.
Known reported Model-A cost is 1.290671 credits, not an independently verified
account debit. The [integrity record](model_a/integrity.json) records numerical
reproduction and retained liabilities. Raw responses, public feedback, workspaces,
and terminal states remain locally under data/main. The committed pre-outcome
freeze is unchanged and still verifies.

---

# 5. Discussion

## What we learned
[Direct findings.]

## Epistemic implications
- trust in completion claims;
- model self-knowledge;
- evaluation reliability.

## AI-safety implications
- framing sensitivity;
- model heterogeneity;
- effect of requirement accounting.

## What we did not establish
- intent;
- scheming;
- universal LLM behavior;
- all safety workflows.

---

# 6. Limitations

Must include:
- 16–20 tasks;
- only two fixed model systems;
- moderate-effect uncertainty;
- benign coding domain;
- framing is a package of domain cues;
- fixed two-turn protocol;
- provider stack differences;
- self-assessment prompted rather than spontaneous.

---

# 7. Conclusion

One paragraph answering the three result channels.

---

# Appendix — Limitations and Dual-Use / Ethical Considerations

Study uses benign code only.

Potential dual use:
- framing research may reveal ways to alter model performance.

Mitigations:
- benign benchmark;
- no harmful operational examples;
- no chain-of-thought reliance;
- aggregate behavioral reporting;
- careful intent claims.

---

# Appendix — Prompts

Include frozen prompt text.

# Appendix — Task metadata

List task IDs/families/requirement counts.

# Appendix — Additional figures

Task-level tables, repair plots, optional analyses.
