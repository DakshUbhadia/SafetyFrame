# SafetyFrame-Eval

Research plan and starter templates for evaluating framing sensitivity,
requirement accounting, and requirement-level self-assessment on benign coding tasks.

The Python environment, model preflight, draft preregistration, report skeleton,
two-turn experiment harness, canonical renderer, and equivalence audit are implemented. Qwen and DeepSeek passed model
access checks; account rate limits remain unconfirmed. The harness passes an
offline synthetic repair trajectory and a paired reference audit. Sprint 4 has
five usable excluded capability pilots and a documented stress trial. Sprint 5
adds 16 validated final task pairs across four families, with five requirements
each. Preregistration/freeze, main-study collection, and analysis remain pending.

See [SETUP.md](SETUP.md) for environment commands, local credential setup,
account discovery, budget configuration, and live acceptance. Track work in
[SPRINT_PLAN.md](SPRINT_PLAN.md). Initial study choices are in
[config/study.json](config/study.json). See [HARNESS.md](HARNESS.md) for two-turn
smoke commands, pilot task input, execution isolation, resumability, and result files.
See [RENDERING.md](RENDERING.md) for canonical YAML authoring, C/S rendering,
reference validation, and balance diagnostics.
See [PILOTS.md](PILOTS.md) and [calibration results](report/pilot_calibration.md)
for measured pilot outcomes and the provisional task-shape recommendation.
See [BENCHMARK.md](BENCHMARK.md) for the accepted task inventory, completed
checklists, Docker reference/fault evidence, and reproduction commands.

Start with [SPECIFICATION_v4.md](SPECIFICATION_v4.md), which defines the research
design. The accepted Sprint 5 set uses the 16-task minimum (18 target, 20 maximum),
Model A in C/S/CD/SD, Model B in C/S, and two turns per trajectory.

## Execution materials

| File | Purpose |
|---|---|
| [01_PREREGISTRATION_TEMPLATE.md](01_PREREGISTRATION_TEMPLATE.md) | Record choices before final-study calls. |
| [02_EXPERIMENT_PROTOCOL.md](02_EXPERIMENT_PROTOCOL.md) | Execute independent, blocked, two-turn trajectories. |
| [03_TASK_AUTHORING_GUIDE.md](03_TASK_AUTHORING_GUIDE.md) | Construct canonical tasks and domain mappings. |
| [04_TASK_VALIDATION_CHECKLIST.md](04_TASK_VALIDATION_CHECKLIST.md) | Validate each final task and its tests. |
| [05_PROMPT_PROTOCOL.md](05_PROMPT_PROTOCOL.md) | Define condition prompts, output format, and feedback. |
| [06_MODEL_PROVIDER_SETUP.md](06_MODEL_PROVIDER_SETUP.md) | Record provider access, model IDs, settings, and preflight checks. |
| [07_RUNBOOK.md](07_RUNBOOK.md) | Follow the setup, pilot, freeze, experiment, and analysis workflow. |
| [08_DATA_DICTIONARY.md](08_DATA_DICTIONARY.md) | Define trajectory, requirement, and metadata fields. |
| [09_SCORING_ANALYSIS_PLAN.md](09_SCORING_ANALYSIS_PLAN.md) | Define scores, paired estimates, bootstrap intervals, and figures. |
| [10_SELF_ASSESSMENT_RUBRIC.md](10_SELF_ASSESSMENT_RUBRIC.md) | Classify requirement claims against hidden-test ground truth. |
| [11_DEVIATION_LOG_TEMPLATE.md](11_DEVIATION_LOG_TEMPLATE.md) | Record changes and incidents after freeze. |
| [13_REPORT_TEMPLATE.md](13_REPORT_TEMPLATE.md) | Draft the research report from observed results. |
| [15_REPRODUCIBILITY_CHECKLIST.md](15_REPRODUCIBILITY_CHECKLIST.md) | Check the environment, artifacts, data, and release. |
| [18_FREEZE_MANIFEST_GUIDE.md](18_FREEZE_MANIFEST_GUIDE.md) | Define the machine-readable integrity manifest. |

The existing document numbers are preserved so references remain stable.
Where materials differ, use v4 for the design, the completed preregistration for
frozen study choices, and the relevant protocol for implementation details.

## Starter templates

| File | Purpose |
|---|---|
| [task_spec_template.md](templates/task_spec_template.md) | Canonical task specification and validation notes. |
| [mapping_template.yaml](templates/mapping_template.yaml) | Capability/safety domain substitutions. |
| [requirements_template.yaml](templates/requirements_template.yaml) | Requirement IDs and hidden-check mapping. |
| [task_metadata_template.json](templates/task_metadata_template.json) | Per-task metadata and editable files. |
| [task_inventory_template.csv](templates/task_inventory_template.csv) | Benchmark-wide inclusion and validation record. |
| [run_manifest_template.csv](templates/run_manifest_template.csv) | Block order and trajectory status. |
| [results_template.csv](templates/results_template.csv) | Starting trajectory results table. |
| [requirement_results_template.csv](templates/requirement_results_template.csv) | Requirement-level pass/fail and claims for each turn. |
| [deviation_log_template.csv](templates/deviation_log_template.csv) | Structured incident record. |

These are unfilled starters. The result CSVs now match the Sprint 2 trajectory
and requirement schemas, including v4 metadata and self-assessment counts.
Validate actual pilot logging before freezing.

## Implementation boundary

The initial runtime directories follow v4 section 62. `requirements.txt` documents
the Python harness and pinned PyYAML parser; live test execution also requires a
working Docker engine and an explicitly installed image. Later dependencies will be added
when used. [preregistration.md](preregistration.md) is an unsigned draft and
[report/report.md](report/report.md) contains planned Methods and unfilled results.
The freeze manifest and final study run manifest will be created in Sprint 6 from
actual validated tasks and verified model choices.

The superseded v3 specification and duplicate navigation, daily scheduling,
resource, interpretation, and decision guides were removed during cleanup.
Their core workflow and interpretation guidance remain in v4 and the protocols above.
