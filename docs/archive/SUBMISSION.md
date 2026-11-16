# Sprint submission materials

**Status: not submitted.** The author confirmed this on November 16, 2026.
The manuscript and numerical analysis are complete, but no final report PDF or
submission confirmation is present in the repository. A figure PDF must not be
mistaken for the report. Official-template layout, page limits, and final PDF
inspection remain unchecked; see [source-verification limits](report/source_verification.md).

## Form fields

| Field | Prepared value |
| --- | --- |
| Project title | SafetyFrame-Eval: Safety Framing, Requirement Accounting, and Self-Assessment in AI Coding |
| Author | Daksh Ubhadia |
| Affiliation | Independent researcher |
| Track recommended in the supplied plan | Track 1 — Model Epistemics & Decision-Making Evals |
| Optional team name suggested in the supplied plan | Eye Safety — not yet confirmed as the team's chosen name |
| Repository | https://github.com/DakshUbhadia/SafetyFrame |
| Recommended PDF filename | SafetyFrame_Eval_Daksh_Ubhadia.pdf |
| Manuscript source | [report/report.md](report/report.md) |
| Results overview | [FINAL_RESULTS.md](FINAL_RESULTS.md) |

Track and team recommendations come from the last-mile plan; they are not a
claim that a form has been inspected or submitted. Confirm the official form's
current choices, deadline, title, author details, and PDF before uploading.

## Prepared project summary

SafetyFrame-Eval tests whether AI-safety framing changes technical performance on
functionally matched benign coding tasks, whether explicit requirement accounting
changes that relationship, and whether models accurately assess their own
completion. The study uses 16 frozen Python tasks with five hidden binary
requirements each. Qwen 3.5 397B was evaluated across capability, safety, and
requirement-accounting conditions, with DeepSeek V4 Flash used for a secondary
framing comparison.

For Qwen, the capability-minus-safety completion gap was small and inconclusive
(0.0125; 95% CI −0.0500 to 0.1000). The requirement-accounting interaction was not
robust to operational sensitivity analyses. The clearest result was epistemic:
across 29 completed accounting trajectories, all 145 requirement-status claims
said “implemented,” including all 20 requirements that actually failed hidden
checks. The findings suggest that explicit model completion claims should not be
treated as independent verification and should instead be checked against
external evidence.

## Remaining submission steps

- [ ] Transfer the manuscript into the official template and confirm its requirements.
- [ ] Export SafetyFrame_Eval_Daksh_Ubhadia.pdf and inspect all pages, figures, and links.
- [ ] Complete the remaining clean-environment release checks in [Sprint 11](SPRINT_PLAN.md#sprint-11--reproducibility-packaging-and-submission).
- [ ] Check the title, track, author, repository URL, and summary in the actual form.
- [ ] Submit through the official channel and retain the confirmation or receipt.

No new models, auditor runs, benchmark tasks, confirmatory hypotheses, output-
budget changes, selective retries, or significance tests are needed for these
presentation changes. Separately frozen follow-up work stays outside the sprint
submission's reported results.
