# SafetyFrame-Eval — Research Report Template

> Fill only with observed results. Do not write numerical placeholders as if they were findings.

# Title

**SafetyFrame-Eval: Does AI-Safety Framing Change Technical Performance?**

Subtitle:  
**A matched-task study of framing sensitivity, requirement accounting, and requirement-level self-assessment**

## Abstract

**Problem.** [1–2 sentences on epistemic trust and safety framing.]

**Method.** We evaluated `[N]` functionally equivalent, domain-relabeled benign coding tasks. Model A received a 2×2 capability/safety × requirement-accounting design; Model B received a matched capability/safety comparison. Each trajectory used a fixed two-turn implementation/repair protocol and hidden requirement-level scoring.

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
- N tasks
- families
- 4–5 requirements each
- benign
- dual plausible
- calibrated with excluded pilot tasks

## 3.2 Functional matching and domain relabeling
Explain canonical rendering and equivalence audit.

## 3.3 Experimental conditions
Table: C, S, CD, SD.

## 3.4 Models
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
