# Final analysis and figures — Sprint 9

The final analysis uses the existing 96 terminal trajectories: Model A's
64 C/S/CD/SD runs and Model B's 32 C/S runs. Ninety completed; six ended in
documented provider failures. No further inference is needed for this sprint.

## Reproduce from reviewed scored data

```powershell
.\.venv\Scripts\python.exe -m analysis.primary
```

This checks every reviewed release digest and frozen run identity, recomputes
scores and claim counts from requirement outcomes and parsed claims, and verifies
the complete original model summaries. It exports [final results](../../report/final_analysis/results.md),
tables, plotting data and scientific PNG/SVG/PDF figures. The original
report/model_a and report/model_b releases remain unchanged.

The inference environment is in requirements.txt; additional plotting dependencies
are pinned in analysis/requirements.txt. Install both into the existing virtual
environment when reproducing on another machine. The committed freeze must verify.

## Audit local evidence and verify reproduction

```powershell
.\.venv\Scripts\python.exe scripts/finish_analysis.py
.\.venv\Scripts\python.exe -m unittest discover -s analysis/tests
```

The finalizer additionally audits local raw responses, request/retry identities,
workspace hashes and scoring under data/main. It compares those records with
the reviewed datasets, then reproduces ten numerical/narrative artifacts in
data/main/sprint9_reproduction. [integrity.json](../../report/final_analysis/integrity.json)
records the digests and source checkpoint. Raw evidence is local and excluded
from Git; portable numerical reproduction uses the first command above.
Neither command contacts a model or spends inference credits.

## Result files

| Artifact under report/final_analysis | Contents |
|---|---|
| summary.json | All three channels, secondary effects, sensitivities and B diagnostics |
| conditions.csv | Planned/completed/provider-failed counts, means and task intervals |
| contrasts.csv | Primary, provider-utility and valid-format estimates, intervals and paired N |
| matched_means.csv | Condition means on each contrast's exact matched subset |
| task_contrasts.csv | Every planned task's contrast or explicit missing value |
| self_assessment.csv | Both turns; strict/lenient URDR, FCR and precision, counts and micro/macro ratios |
| failures.csv | Format failures, missing responses, terminal provider failures, artifact and end-to-end means |
| repair.csv | Observed-turn counts, paired repair, artifact repair, improved/unchanged/worsened counts |
| figure_data.json | Exact numerical inputs selected from the result tables |
| results.md | Findings, sensitivities, interpretation limits and figure links |

Figures 1–4 under report/figures show Model A condition means, every task's
C-minus-S for both models, Model A disclosure effects/interaction, and
Turn-2 self-assessment. Figure 5 is secondary: paired repair with artifact and
end-to-end scores separated. Variable SVG/PDF export timestamps are excluded
from byte comparison; figure values are explicitly exported and checked.

## Statistical scope

The frozen bootstrap resamples task contrast values, preserving all contributing
conditions: 10,000 percentile resamples, seed 2026111509, sorted task IDs and an
independent stream for each contrast. Each contrast retains its own complete
pairs/quadruples. Models remain separate; requirements are nested within tasks.
No requirement-independent tests or universal pooled model effect are introduced.

Provider failures are missing in the primary estimand and zero in the separately
labeled provider-utility sensitivity. Invalid file transactions remain zero
end-to-end TCS; preserved-artifact correctness is separately reported. The
valid-format sensitivity requires all contributing transactions to parse.
Undefined ratios/intervals stay JSON null, empty CSV or NA.

Repair uses completed trajectories. In particular, Model B S has 16 observed
first turns but only 15 completed pairs, so its all-observed Turn-1 mean must
not be subtracted from its completed-only Turn-2 mean to calculate repair.

## Interpretation

Model A's baseline gap is inconclusive: 0.0125, 95% CI [-0.0500, 0.1000],
N=16. Its negative disclosure interaction is sensitive to provider and format
handling. All 20 failed Turn-2 artifact requirements in CD/SD were claimed
implemented; this is descriptive inaccuracy, without establishing intent.

Model B's primary gap is -0.2000 [-0.4308, 0.0000], N=13, but 50/59 replies
exhausted the reasoning budget without emitting final code. Only one task has
valid Turn-2 file format in both conditions, so its valid-format interval is
undefined. This is chiefly a code-emission result under the fixed budget;
it does not cleanly isolate coding correctness or establish generalization.

No settings, scores, exclusions, retry policies or outcomes were changed to
improve results. A larger-budget experiment would be a separately registered
follow-up. Sprint 10's full report and Sprint 11's submission remain outstanding.

## Implementation

analysis/primary.py validates and recomputes results; analysis/bootstrap.py uses
the frozen bootstrap; analysis/self_assessment.py and analysis/repair.py handle
descriptive metrics; analysis/figures.py exports the scientific figures.
The previously reviewed model analyses provide cross-checks against drift.
