# SafetyFrame-Eval — Research Report Draft

> DRAFT: Excluded pilot results and benchmark validation are available. No main-study results have been collected; outcome placeholders remain unfilled.

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
- 16 validated tasks, pending preregistration and freeze
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
tokenizers. The set is not frozen, and difficulty has not been measured on final
target models. See [benchmark evidence](../BENCHMARK.md).
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

Report:
- C mean
- S mean
- paired gap
- 95% CI
- task-level distribution

Interpret only at tested-model/task level.

## 4.2 Model-B generalization

Same structure.

## 4.3 Requirement-accounting interaction

Report:
- CD−C
- SD−S
- interaction
- underlying condition means

Do not call it mitigation unless conditions support that wording.

## 4.4 Requirement-level self-assessment

Report:
- number of actual failed requirements
- FCR
- URDR
- completion precision
- CD vs SD pattern

## 4.5 Repair dynamics

Only if informative:
- Turn-1 TCS
- Turn-2 TCS
- RepairGain

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
