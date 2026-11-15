# Model A collection and initial analysis

Sprint 7 executes the frozen Model-A factorial: 16 tasks × C/S/CD/SD,
64 trajectories, two turns each. Collection uses the existing frozen runtime;
the new collector and analysis live outside frozen source directories.
No main-task selection, generation setting, retry rule, pacing limit, or
scoring/analysis definition is changed.

## Collect or resume

From PowerShell in the repository:

~~~powershell
.\.venv\Scripts\python.exe -m harness.freeze
.\.venv\Scripts\python.exe scripts/collect_frozen.py --role A --execute
~~~

The collector visits exactly the frozen A rows, in execution order. Every run
reuses the frozen CLI, which verifies prior terminal state, task/model/condition,
prompts, settings, Docker image, budget, and full committed freeze. Re-entering
an already terminal ID validates saved responses/workspaces without inference.
No replacement run IDs or selective reruns are generated.

The shared 60-second request-start interval and 40-credit cumulative ledger
ceiling remain in force. Earlier pilot/unknown liabilities are retained.
Terminal provider failures stay in the dataset; frozen operational pause rules
require a documented review before continuing. Missing outcomes, checksum
changes, or executor faults stop for reconciliation instead of skipping a run.
Never remove a lock until the associated processes and request/outcome state
have been checked.

Progress is data/main/collector-A.json. The immutable plan remains
data/run_manifest.csv; actual statuses are exported separately to
data/main/run_manifest.csv. Raw outputs, public feedback, response metadata,
both snapshots, hidden checks, claims, and terminal identities remain in
data/main. These local research artifacts are ignored by Git until reviewed
for release.

## Analyze only the completed planned phase

The analysis refuses to produce aggregate results until all 64 planned A runs
have terminal completed/provider_failed records. It verifies record/state
checksums, frozen task/model identities, saved response/snapshot hashes, and
the frozen score/claim formulas before releasing a scored dataset. No Model-B
outcomes enter this analysis.

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r analysis/requirements.txt
.\.venv\Scripts\python.exe -m analysis.model_a
~~~

Outputs go to report/model_a: condition means, paired primary/secondary contrasts,
10,000-resample task-bootstrap intervals, provider-utility and valid-format
sensitivities, per-task differences, both-turn self-assessment counts/micro/macro
ratios, repair summaries, and PNG/SVG/PDF scientific figures. Missing denominators
remain NA/null. The released scored_dataset.json omits model response text and
contains integrity digests linking it to private local evidence.

Reproduce the published estimates without inference or private response text:

~~~powershell
.\.venv\Scripts\python.exe -m analysis.model_a --dataset report/model_a/scored_dataset.json --output report/model_a_reproduced
~~~

Frozen statistical helpers and config/analysis.json remain authoritative.
Figures use Matplotlib; analysis/requirements.txt pins the additional plotting
environment separately from the frozen inference dependencies.

## Verify the new tooling

~~~powershell
.\.venv\Scripts\python.exe -m unittest discover -s analysis/tests
~~~

Tests use synthetic outcomes and mocked collectors. They do not contact a model.
Current collection completeness and actual results must be established from
the terminal records, not from these tests.
