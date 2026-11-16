# Dependent research milestones

The software implements inventory, strict categorical/evidence/confidence
parsing, neutral and critic prompts, stateless collection, evidence review
imports, task bootstrap, calibration and figures. Implementation is distinct
from conducting research and obtaining human judgments. See freeze.json and
analysis/summary.json for protocol and collection state, not this checklist.

| Milestone | Completion evidence | Dependency |
| --- | --- | --- |
| 0 preservation | Git tag, branch, byte-hash manifest; final PDF remains pending | Current repository checkpoint |
| 1 inventory | All 96 records, documented exclusions, source hashes | Preservation |
| 2 harness | Synthetic request/parse/score/resume tests and no hidden-input leakage | Inventory |
| 3 local preregistration | Exact prompts/model/settings/schedule/parser/rubric freeze | Tests pass; no audit requests |
| 4–6 collection | Every scheduled fresh/evidence/confidence cell terminal | Explicit live collection after freeze |
| 7 analysis | Matched task bootstrap, sensitivities, observed figures, evidence review | Collection terminal; real reviewers |
| 8 cross-model replication | Excluded pilots, separate model freeze, C/S main outcomes | Initial audit study complete |
| 9 independent benchmark review | Blinded human ratings and unchanged comments | Real independent reviewers |
| 10 paper | Distinct Study 1/2 findings, limitations, provenance package | Observed results and review |

Optional IndependentCritic and cross-model auditing need a new study namespace
or a separate pre-outcome freeze. The runner supports multiple auditor configs
and the critic/cross_model condition names; never append cells to a live freeze.
Use the same neutral fresh prompt when testing model identity, so prompt changes
do not confound model comparisons. Do not add every matrix cell initially.

Clean builder replication is a separate study, not a replacement for budget-
limited Study 1 DeepSeek. Use 3–4 excluded tasks; validate at least 90% usable
final-code responses. Tune output budget, streaming, reasoning allocation,
timeout and format compatibility only, without looking at framing differences.
Freeze exact model, settings, parser, retry rule and tasks before at least
16 tasks × C/S; preferably three independent generations per task-condition.
Record replicate_id and retain every raw result before any averaging.

Repeated generations: prioritize 16 × 2 × 3 = 96 baseline trajectories, or
16 × 4 × 3 = 192 for the full factorial. Analyze within-task stochastic variance,
between-task variance and matched condition effects while retaining task clusters.
No live generation expansion is included in this study's 87-or-fewer audit calls.

Benchmark reviewers receive canonical specification, C/S renderings, public tests,
hidden requirement descriptions and scoring mapping, without scores, C/S gaps,
surprising-task labels or model outputs. Fixed scale: pass, minor concern,
major concern. Review equivalence, explicit-requirement correspondence, wording,
independent scorability, revealing public tests, hidden gotchas, partial credit,
and framing plausibility. Preserve reviewer comments, identity and timestamps.
Do not revise completed benchmark tasks; any revisions become benchmark_v2.

Heterogeneity remains exploratory: task family, baseline difficulty, file and
requirement counts, public coverage, starter/prompt length, identifiers,
integration complexity, relabeling, failed counts and repair gain against framing
gap, FCR, URDR, audit improvement and calibration. Display every task; do not
establish subgroup effects from four tasks per family. No confirmatory feature
selection from observed outcomes.

Only after the audit study is complete consider 40–60 distinct tasks or a new
agentic study. Preserve independently scored requirements, paired renderings,
partial credit, legitimate hidden checks, references and fault isolation.
Human recruitment, external registration, paid inference, PDF publication and
submission are separate actions, not results implied by this implementation.
