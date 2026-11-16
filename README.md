# SafetyFrame-Eval

**SafetyFrame-Eval: Safety Framing, Requirement Accounting, and Self-Assessment in AI Coding**

Research for the **AI × Epistemics Research Sprint, November 2026**. We test
whether AI-safety framing changes performance on matched benign coding tasks,
whether requirement accounting changes that relationship, and whether completion
claims identify unmet requirements.

## Headline result: every failed requirement was claimed implemented

Across **29 completed Qwen requirement-accounting trajectories**, all **145/145
final requirement-status claims** said `implemented`. **13/29 trajectories
(44.8%)** contained at least one failed artifact requirement, yet **20/20 failed
requirements** were still claimed implemented. None was acknowledged incomplete
or uncertain: strict unmet-requirement disclosure rate (URDR) **0.0000**;
false-completion rate **1.0000**.

![Failed requirements and completion claims](report/figures/claim_ground_truth.png)

*All 20 failed final artifact requirements were labeled implemented. These are
descriptive counts nested within tasks, not 20 independent experimental units.
[Counts and dataset provenance](report/claim_figure_data.json).*

A model-generated completion checklist should be checked against external tests,
requirement-linked evidence, or independent review before it is trusted as a
validation signal.

**[Final results](FINAL_RESULTS.md) · [Research report](report/report.md) ·
[Frozen study](FROZEN_STUDY.md) · [Reproduce the analysis](FINAL_ANALYSIS.md)**

## What was tested

The frozen study uses **16 matched Python tasks**, each with **five independently
scored hidden requirements**, in a two-turn implementation-and-repair protocol.
Capability (C) and safety (S) variants are computationally matched. CD/SD add
explicit requirement accounting. Inference uses paired tasks and 10,000
task-bootstrap resamples, preserving dependence among requirements.

| Result | Estimate and uncertainty | Interpretation |
| --- | --- | --- |
| Qwen 3.5 397B capability − safety TCS | **0.0125**, 95% CI **[−0.0500, 0.1000]**; 16 matched task pairs | Inconclusive; does not establish equivalence. |
| Qwen accounting × framing interaction | **−0.1286**, 95% CI **[−0.2714, −0.0143]**; 14 complete task quadruples | Nominal but sensitivity-dependent; not robust mitigation evidence. |
| DeepSeek V4 Flash framing comparison | **50/59 observed replies** exhausted the frozen output budget in reasoning without emitting final code; only one valid-format C/S pair remained | Operationally confounded; not a clean cross-model correctness replication. |

The accounting interaction weakens in both prespecified sensitivities:
provider utility **−0.0375 [−0.2125, 0.1750]** (16 tasks), and valid format
**−0.0769 [−0.1692, 0.0000]** (13 tasks).
[Exact contrasts and matched denominators](report/final_analysis/contrasts.csv).

## Study and submission status

**Study 1 collection, final analysis, and manuscript content are complete.** All
96 planned trajectories reached terminal status: 90 completed and six provider
failures under the frozen retry policy. Mixed, null, malformed, and operationally
limited outcomes were retained; no selective replacement runs were used.

**PDF packaging and submission remain pending.** No final report PDF or submission
confirmation is recorded, and the author confirmed that the project has not yet
been submitted. Figure PDFs are available but are not the submission manuscript.
[Submission materials and remaining steps](SUBMISSION.md).

## Methods, evidence, and reproducibility

| Artifact | Purpose |
| --- | --- |
| [Final results](FINAL_RESULTS.md) | Headline findings, denominator definitions, and limitations. |
| [Research report](report/report.md) | Full methods, narrative, references, and appendices. |
| [Exact final analysis](report/final_analysis/results.md) | Primary estimates, sensitivities, repair, and failure accounting. |
| [Frozen study](FROZEN_STUDY.md) | Committed freeze, hashes, randomized run plan, and integrity checks. |
| [Benchmark](BENCHMARK.md) | Canonical task definitions, C/S variants, public and hidden tests, requirement mappings, and validation. |
| [Model A provenance](MODEL_A.md) / [Model B provenance](MODEL_B.md) | Scored datasets, operational records, and model-specific limitations. |
| [Preregistration](preregistration.md) | Original local registration, preserved unchanged. |
| [Experiment protocol](02_EXPERIMENT_PROTOCOL.md) / [Scoring plan](09_SCORING_ANALYSIS_PLAN.md) | Two-turn procedure, requirement scoring, estimands, and bootstrap. |
| [Analysis reproduction](FINAL_ANALYSIS.md) / [Report verification](RESEARCH_REPORT.md) | Offline commands, evidence checks, and plotting dependencies. |

The repository releases scored outcomes and claims without response/reasoning
text. Credentials, raw provider records, and account-specific metadata stay local
pending release review. The registration/scoring timing discrepancy is disclosed
in the report. Internal task review is not independent validation; the local
preregistration is not an external registration.

Run `python scripts/verify_presentation.py` to check the original scientific
hashes, merged Study 2 protocol, report evidence, and explicit documentation-only
amendments on main. Original Study 1 reproduction uses the preservation tag
`safetyframe-sprint-2026-final`; frozen Study 2 collection uses the
`followup/self-assessment-audit` branch. Its strict preservation check correctly
rejects main's newer navigation text. Neither freeze has been rewritten.

## Scope and interpretation

The framing estimate is inconclusive, accounting is not a robust mitigation, and
the clearest descriptive result is inaccurate requirement-level self-assessment.
Hidden outcomes establish a mismatch between claims and artifact behavior; they
do not establish awareness, deception, scheming, or intentional concealment.
The small benign benchmark, single generation per condition, fixed provider
systems, and DeepSeek budget limitation restrict generalization.

The separately frozen [Study 2 audit implementation](https://github.com/DakshUbhadia/SafetyFrame/tree/followup/self-assessment-audit/study_2_audit)
tests fresh and evidence-grounded verification in a follow-up namespace.
Its collection has not started and contributes no results to this sprint study.
No new confirmatory experiments are part of these presentation updates.

For development, see [setup](SETUP.md), [harness](HARNESS.md),
[rendering](RENDERING.md), [pilots](PILOTS.md), and the
[sprint history and remaining release work](SPRINT_PLAN.md).
