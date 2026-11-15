# SafetyFrame-Eval — Research Sprint Plan

## Scope and starting point

This plan breaks [SPECIFICATION_v4.md](SPECIFICATION_v4.md) into sequential,
deliverable-based work sprints for one researcher. These are focused work blocks,
not multi-week Scrum iterations. Sprint 1's environment and model preflights are
implemented; account rate-limit confirmation remains pending. Sprint 2's two-turn
harness and Sprint 3's renderer/audit are verified using excluded synthetic
examples. Sprints 4–11 remain not started. See [SETUP.md](SETUP.md),
[HARNESS.md](HARNESS.md), and [RENDERING.md](RENDERING.md) for evidence.

The specification defines the research design. This plan organizes execution
without changing that design. Paths listed as deliverables are files to build or
produce, not claims that those files already exist.

The required research outcomes are:

1. Estimate capability-minus-safety framing differences separately for Models A and B.
2. Estimate the disclosure × framing interaction on Model A.
3. Compare requirement-level completion claims with hidden-test ground truth.

| Design choice | Default |
|---|---|
| Final benchmark | Target 18 tasks; minimum 16; maximum 20 |
| Requirements | 4–5 independently scored requirements per task |
| Pilot | 4–6 throwaway tasks, excluded from final inference |
| Model A | C, S, CD, SD |
| Model B | C, S |
| Trajectory | Two turns, with public-test feedback between turns |
| Primary endpoint | Turn-2 Task Completion Score (TCS) |
| Analysis unit | Task; matched conditions stay paired |
| Uncertainty | 95% task-bootstrap confidence intervals |

Conditions: **C** = capability framing; **S** = safety framing;
**CD/SD** = the corresponding framing plus requirement accounting.

## Progress tracker

Mark a sprint complete only when its exit criteria are met.

| Done | Sprint | Main deliverable | Depends on |
|---|---|---|---|
| [ ] | 1. Scope, access, and environment — local setup implemented; live acceptance pending | Working provider preflight and recorded study choices | — |
| [x] | 2. Two-turn experiment harness | Complete, logged, scored synthetic smoke trajectory; Docker integration pending before live pilots | 1 |
| [x] | 3. Task rendering and equivalence | Canonical YAML-to-C/S pipeline; text/AST checks and passing reference tests | 2 |
| [ ] | 4. Pilot and difficulty calibration | Pilot findings and chosen task archetypes | 3 |
| [ ] | 5. Final benchmark construction | At least 16 fully validated task pairs | 4 |
| [ ] | 6. Preregistration and freeze | Frozen artifacts, hashes, and randomized run manifest | 5 |
| [ ] | 7. Model A factorial | Complete C/S/CD/SD dataset and first analysis | 6 |
| [ ] | 8. Model B generalization | Complete C/S dataset | 7 |
| [ ] | 9. Final analysis and figures | Reproducible tables, intervals, and figures | 8 |
| [ ] | 10. Research report | Complete report supported by observed results | 9 |
| [ ] | 11. Reproducibility and submission | Checked release artifacts and submission package | 10 |

## Sprint 1 — Scope, access, and environment

**Goal:** Make the study executable before building the benchmark.

- [x] Review v4 and identify the three result channels and default scope.
- [ ] Confirm provider access, available model IDs, rate limits, and inference budget.
- [x] Select initial model candidates: A = `qwen3.5-397b` (Qwen), B = `deepseek-v4-flash` (DeepSeek). Validate suitability in excluded pilots before freeze.
- [x] Record exact model IDs and preflight-accepted generation settings. Context use and coding suitability still require pilot validation.
- [x] Establish the Python environment and record actual dependencies in `requirements.txt`.
- [x] Set up credentials through local environment loading and exclude secrets from version control. Authenticated catalogue and generation checks succeeded without exposing the key.
- [x] Create the initial repository structure from v4 section 62 as implementation begins.
- [x] Start a report skeleton from the retained report template; add Methods notes as work proceeds.

**Deliverables:** Provider configuration, environment setup, initial dependency
file, and partially completed preregistration containing known choices.

**Exit criteria:** A trivial request succeeds for each selected model, metadata
can be captured, and the default study fits the available access and budget.

**Implementation status:** `.venv`, `config/study.json`, `harness/preflight.py`,
`requirements.txt`, `.gitignore`, `.env.example`, `preregistration.md`, and
`report/report.md` are present. Offline tests cover budget accounting, isolated
requests, evidence handling, and credential protection. Both models passed live
smoke checks at the proposed study settings. Account rate limits and actual-balance
reconciliation remain pending; Sprint 1 is not marked complete. Model choices and
published prices are now recorded in [SETUP.md](SETUP.md). The latest reported
balance is 3,500 credits; the core study remains at 18 tasks with no automatic expansion.

**Reference:** [Model/provider setup](06_MODEL_PROVIDER_SETUP.md).

## Sprint 2 — Two-turn experiment harness

**Goal:** Execute and preserve an entire trajectory reliably.

- [x] Implement provider wrappers with explicit generation settings and request logging.
- [x] Implement the `<file path="...">...</file>` parser and editable-file restrictions.
- [x] Reject paths outside the task workspace and preserve raw responses unchanged.
- [x] Implement clean workspace creation and controlled test execution with time limits.
- [x] Run public and hidden tests separately; map hidden checks to requirement IDs.
- [x] Save Turn-1 workspace and scores before applying Turn-2 changes.
- [x] Send only public-test feedback to Turn 2, preserving context within that trajectory.
- [x] Start a fresh conversation and workspace for every new trajectory.
- [x] Parse CD/SD requirement checklists, including uncertain and missing claims.
- [x] Implement infrastructure retries, failure classification, and resumable run status.
- [x] Reconcile results storage with v4 section 61 and the data dictionary; expand the CSV starter as needed.

**Deliverables:** `harness/providers/`, `harness/parse_files.py`,
`harness/run_tests.py`, `harness/run_experiment.py`, and smoke-run artifacts.

**Exit criteria:** One synthetic task completes both turns with raw outputs,
snapshots, requirement scores, claims, and metadata saved. Checks demonstrate
that hidden-test information never enters the model feedback, workspace paths
cannot escape the task directory, and failures are recorded consistently.

**Verification:** Synthetic CD trajectory improves from 2/4 to 4/4 requirements,
with raw requests/responses, both workspace snapshots, checklist claims, metadata,
and exported tables. Regression tests cover rejected paths, feedback separation,
bounded retries, format/provider failures, interrupted-run recovery, credit
reservations, and idempotent resume. See [HARNESS.md](HARNESS.md) for commands and
artifact locations. Docker command restrictions are tested, but live container
execution is pending because the Docker daemon is inaccessible here. No paid
generation was used for Sprint 2. Final-study execution remains gated until freeze.

**References:** [Experiment protocol](02_EXPERIMENT_PROTOCOL.md),
[prompt protocol](05_PROMPT_PROTOCOL.md), [data dictionary](08_DATA_DICTIONARY.md).

## Sprint 3 — Canonical task rendering and equivalence

**Goal:** Produce matched task pairs through one auditable pipeline.

- [x] Define the canonical task specification, starter files, requirements, and mappings.
- [x] Implement programmatic capability/safety rendering, including test identifiers where needed.
- [x] Keep hidden tests, reference solutions, and authoring notes out of model payloads.
- [x] Implement reverse mapping and normalized AST comparison where applicable.
- [x] Check equal file sets, constants, requirement counts, and test behavior.
- [x] Record prompt/repository length and identifier balance diagnostics, labeling token proxies explicitly.
- [x] Render and validate one synthetic example end to end.

**Deliverables:** `harness/render_variants.py`, `harness/audit_equivalence.py`,
and an auditable example task pair with reference solution.

**Exit criteria:** Both renderings pass reference tests and reverse-map to the
same computational problem; only intended domain cues differ.

**Verification:** `synthetic_domain_utils` renders into C/S bundles from one YAML
mapping and requirement source. Both references pass 3 public tests and 8 hidden
checks across 4 requirements. Reverse-mapped text and ASTs match canonical source;
mutation and leakage tests exercise failure cases. The example is excluded from
pilots and final inference. See [RENDERING.md](RENDERING.md) and
[audit evidence](data/audits/sprint3-final.json). No API credits were spent.

**References:** [Task authoring](03_TASK_AUTHORING_GUIDE.md),
[validation checklist](04_TASK_VALIDATION_CHECKLIST.md), and `templates/`.

## Sprint 4 — Pilot and difficulty calibration

**Goal:** Find task patterns that allow informative partial success.

- [ ] Build 4–6 disposable pilot tasks with distinct difficulty profiles.
- [ ] Use capability-framed runs on a strong model to assess difficulty.
- [ ] Measure Turn-1/Turn-2 TCS, repair saturation, format failures, and token usage.
- [ ] Aim for approximate capability-framed completion of 0.45–0.85 across the calibrated patterns.
- [ ] Adjust explicit requirements, coupling, file count, and public-test coverage before final construction.
- [ ] Resolve harness or parser problems discovered in pilot runs.
- [ ] Record chosen task archetypes and explicitly exclude all pilot tasks from final inference.

**Deliverables:** Separate pilot artifacts and a short calibration record explaining
which task patterns to use and why.

**Exit criteria:** The pipeline works reliably and selected patterns offer
measurement headroom. Final tasks will be newly constructed; selection does not
depend on observed capability-versus-safety effects.

## Sprint 5 — Final benchmark construction

**Goal:** Build the smallest complete, scientifically credible benchmark.

- [ ] Build tasks in batches, validating each batch before expanding.
- [ ] Cover evaluation ingestion, metrics/scoring, experiment management, and monitoring/reporting.
- [ ] Give each task 4–5 explicit, independently scorable requirements.
- [ ] Provide canonical files, domain mappings, requirement metadata, public tests, hidden tests, and reference solutions.
- [ ] Connect every hidden check to an explicit requirement; avoid unstated gotchas.
- [ ] Verify that a local failure can leave other requirements passable.
- [ ] Run each reference solution against public and hidden tests in both C and S.
- [ ] Complete equivalence, linguistic balance, and per-task validation records.
- [ ] Reach 16 validated tasks first; add 17–18 only when equally sound.
- [ ] Add 19–20 only if quality and remaining time permit.

**Deliverables:** `task_templates/`, `rendered_tasks/`, completed task inventory,
and validation evidence for every included task.

**Exit criteria:** At least 16 tasks pass every critical acceptance gate. No
final task has been selected for a favorable observed framing difference.

**Reference:** [Final task validation](04_TASK_VALIDATION_CHECKLIST.md).

## Sprint 6 — Preregistration, scheduling, and freeze

**Goal:** Lock the study before final-study model calls.

- [ ] Complete `preregistration.md` from the retained template.
- [ ] Freeze task IDs, mappings, reference solutions, tests, prompts, scoring, and models.
- [ ] Fix settings, format-failure handling, missingness, retries, and provider-failure policies.
- [ ] Specify strict/lenient self-assessment rules, zero-denominator handling, and metric aggregation.
- [ ] Fix the paired task-bootstrap procedure, resample count, and random seed.
- [ ] Implement `harness/build_blocks.py`; randomize within each task × model block and block order.
- [ ] Generate `data/run_manifest.csv` with Model A C/S/CD/SD and Model B C/S.
- [ ] Record integrity hashes and freeze metadata in `freeze_manifest.json`.
- [ ] Preserve a version-control checkpoint and verify hashes before main runs.
- [ ] Compute the lightweight design-sensitivity table before observing final outcomes.

**Deliverables:** Completed preregistration, freeze manifest, randomized run manifest,
and analysis configuration.

**Exit criteria:** All choices needed for execution and scoring are recorded,
all included tasks are validated, and the frozen artifact set can be verified.

For `n` tasks, the default study contains `6n` trajectories and `12n` model
responses, excluding pilots and retries:

| Tasks | Model A trajectories | Model B trajectories | Total trajectories | Responses |
|---|---|---|---|---|
| 16 | 64 | 32 | 96 | 192 |
| 18 | 72 | 36 | 108 | 216 |
| 20 | 80 | 40 | 120 | 240 |

**References:** [Preregistration template](01_PREREGISTRATION_TEMPLATE.md),
[freeze manifest guide](18_FREEZE_MANIFEST_GUIDE.md).

## Sprint 7 — Model A full factorial

**Goal:** Complete the primary causal comparison and intervention dataset.

- [ ] Run every frozen Model A task block in its randomized C/S/CD/SD order.
- [ ] Verify hashes and reset state before each trajectory.
- [ ] Save both turns, public feedback, hidden scores, claims, and provider metadata.
- [ ] Follow the frozen retry policy; never rerun poor output selectively.
- [ ] Resolve run-manifest entries to completed trajectories or documented failures.
- [ ] After the planned Model A set completes, compute condition means and paired C−S estimates.
- [ ] Compute CD−C, SD−S, their interaction, and task-bootstrap intervals.
- [ ] Produce an initial task-level framing plot, self-assessment table, and repair summary.
- [ ] Update the Results skeleton with observed findings and limitations.

**Deliverables:** Model A raw and scored datasets, first result table, and first figures.

**Exit criteria:** Every planned Model A trajectory has an auditable terminal
status. Primary estimates are reproducible, with missingness and failures visible.

## Sprint 8 — Model B framing generalization

**Goal:** Test the framing comparison on a second model family.

- [ ] Run C/S on the same frozen final task set using Model B's manifest.
- [ ] Preserve the same two-turn procedure, scoring rules, and logging standards.
- [ ] Report condition-specific provider failures and missingness.
- [ ] Compute Model B's paired C−S estimate and task-bootstrap interval.
- [ ] Produce its task-level framing plot.
- [ ] Describe similarities and differences between models without pooling them into a universal effect.

**Deliverables:** Model B raw and scored datasets and generalization results.

**Exit criteria:** All planned Model B C/S trajectories have terminal statuses
and the second model's framing result is reproducible.

## Sprint 9 — Final analysis and figures

**Goal:** Turn frozen datasets into the three research result channels.

- [ ] Recompute derived metrics from stored requirement scores and parsed claims.
- [ ] Estimate `BaselineSafetyGap_A = mean(TCS_C − TCS_S)`.
- [ ] Estimate `DisclosureFramingInteraction_A = mean((TCS_SD − TCS_S) − (TCS_CD − TCS_C))`.
- [ ] Estimate `BaselineSafetyGap_B` separately.
- [ ] Preserve matched conditions during task-level bootstrap resampling.
- [ ] Compute strict URDR, FCR, completion precision, and unmet-disclosure precision for CD/SD.
- [ ] Show relevant numerator/denominator counts and leave zero-denominator metrics undefined.
- [ ] Compute lenient URDR and Turn-2 minus Turn-1 RepairGain as secondary measures.
- [ ] Report format failures and provider failures separately from coding performance.
- [ ] Apply the preregistered missingness and sensitivity rules consistently.
- [ ] Generate Figures 1–4: Model A condition means, task-level C−S for both models,
  Model A disclosure simple effects/interaction, and self-assessment accuracy.
- [ ] Add an optional RepairGain figure only if informative.

**Deliverables:** `analysis/primary.py`, `analysis/bootstrap.py`,
`analysis/self_assessment.py`, `analysis/repair.py`, `analysis/figures.py`,
result tables, and `report/figures/`.

**Exit criteria:** Analysis reproduces from saved data; figures match tables;
tasks remain the independent units; all three result channels are covered.

**References:** [Scoring/analysis plan](09_SCORING_ANALYSIS_PLAN.md),
[self-assessment rubric](10_SELF_ASSESSMENT_RUBRIC.md).

## Sprint 10 — Research report

**Goal:** Explain what the study establishes, including null or mixed findings.

- [ ] Complete Introduction, Related Work, Methods, Results, Discussion, and Limitations.
- [ ] Verify cited research and submission requirements against their original sources.
- [ ] Present Model A framing, Model B framing, interaction, self-assessment, and repair in that order.
- [ ] Include task counts, exact models/settings, failure handling, and uncertainty.
- [ ] Show disclosure simple effects alongside the interaction.
- [ ] Use mitigation language only when safety performance improves and the gap narrows beneficially.
- [ ] Distinguish inaccurate completion claims from evidence of intent.
- [ ] Describe precision limits, benign coding scope, fixed two-turn procedure,
  provider differences, and the framing treatment package.
- [ ] Add prompts, task metadata, scoring details, and deviations to appendices.
- [ ] Include the ethical/dual-use appendix and a 150–250 word abstract, per v4.

**Deliverables:** Complete report draft with figures, references, and appendices.

**Exit criteria:** Every numerical statement traces to analysis output. The
report answers all three research questions without requiring a significant framing gap.

**Reference:** [Report template](13_REPORT_TEMPLATE.md).

## Sprint 11 — Reproducibility, packaging, and submission

**Goal:** Produce an inspectable research artifact and a checked submission.

- [ ] Record the runtime, dependencies, model settings, artifact locations, and reproduction commands.
- [ ] Verify a clean environment can render a task pair, pass reference tests,
  rescore a stored response, and regenerate tables and figures.
- [ ] Check that task/model counts agree across the manifest, datasets, figures, and paper.
- [ ] Preserve raw responses, snapshots, scoring outputs, hashes, and deviation records.
- [ ] Check the release for credentials and unintended private information.
- [ ] Document confirmatory versus exploratory analyses and any withheld artifacts.
- [ ] Export the final PDF, open it manually, inspect figures, and test repository links.
- [ ] Confirm submission format and deadline, submit, and retain the confirmation.

**Deliverables:** Reproduction instructions, release-ready repository, final PDF,
and submission confirmation.

**Exit criteria:** The reported results reproduce and the submission package has
been checked and submitted through the required channel.

**Reference:** [Reproducibility checklist](15_REPRODUCIBILITY_CHECKLIST.md).

## Optional extension — Only after the core report is secure

This is outside the required sprint sequence. Skip it if it threatens analysis,
writing, or submission time. Record the rationale and label result-contingent
work as exploratory or an extension.

- [ ] Model B CD/SD: consider only after Model A factorial, Model B C/S, and a
  substantive report draft exist, with an interesting Model A interaction and adequate resources.
- [ ] Minimal-context robustness: 6–8 tasks with byte-identical repositories,
  changing only opening context, if the primary framing result warrants it.
- [ ] Neutral framing: consider only after C>S when distinguishing capability
  boost from safety suppression would materially clarify the findings.
- [ ] Stochastic reruns or qualitative annotation: add only to resolve a specific observed uncertainty.

Do not add a third model, 24+ tasks, fine-tuning, a website, a multi-agent
environment, or an evaluation-awareness workstream during the core sprint.

## Calendar and scope control

The specification lists an operational submission target of **November 16, 2026,
4:00 PM IST**, with a stated deadline of **5:29 PM IST** that day. These are
planning dates from v4; confirm the official deadline during submission preparation.

| Window | Intended checkpoint |
|---|---|
| November 14 | Sprints 1–6, followed by Model A; v4's target is a complete Model A dataset and first results by night. |
| November 15 | Complete Model B, final analysis, figures, and the report. |
| November 16 | Reproduction checks, PDF review, and submission; no new core experiments. |

This is an aggressive target, not a completion estimate. Because implementation
has not started, feasibility depends on pilot findings, task-authoring speed,
provider availability, and generation latency. Check remaining time at the end
of every sprint; do not mark incomplete work complete to fit the calendar.

If time or credits become tight:

1. Freeze at 16 excellent tasks instead of expanding to 18–20.
2. Keep Model A's full factorial and Model B's C/S design.
3. Drop optional extensions, stochastic reruns, and manual annotation first.
4. Protect validation, hidden scoring, all three result channels, and report time.
5. If the default study becomes infeasible, record the shortfall and any amendment;
   report incomplete or changed scope honestly rather than silently dropping conditions.

For a post-freeze bug, use the [deviation log](11_DEVIATION_LOG_TEMPLATE.md).
Rescore stored artifacts when sufficient; rerun affected matched conditions
consistently when new generation is necessary. Never retain only favorable corrections.
