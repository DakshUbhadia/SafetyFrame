# Sprint 2 — Two-turn experiment harness

## Status and scope

Implemented and verified using a deterministic synthetic task: Turn 1 passes
2/4 requirements and Turn 2 passes 4/4. The fixture is infrastructure evidence,
excluded from pilots, final task construction, and scientific inference. No paid
inference was needed for Sprint 2 verification.

Adaption transport is implemented against the [Responses API](https://docs.adaptionlabs.ai/api/resources/responses/methods/create).
Full live trajectories have not been exercised: Docker is installed here but its
daemon is unavailable. Generated code requires Docker and cannot use the local
fixture executor. Sprint 1's account rate limit remains unconfirmed; this does
not prevent building/testing the harness offline.

## Run the synthetic smoke trajectory

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m harness.run_experiment --smoke
```

Expected output: `status: completed; TCS: 0.5 -> 1.0`.
The default condition is CD, allowing claim-versus-ground-truth checks. Use
`--condition C` with a new run ID to verify the baseline without accounting.
The bundled fixture is capability-framed; S/SD require a safety-rendered task,
which belongs to Sprint 3.

The command prints a fresh run ID. Supply it with `--run-id` to resume or reuse its result without
repeating provider calls. Changes to tasks, prompts, configuration, harness code,
test timeout, backend, or image invalidate that run identity; use a new ID for a
new implementation. Old artifacts are retained.

## Artifact layout

Default smoke artifacts are under `data/smoke/`; live pilots use `data/pilot/`.
Both trees have the same layout:

```text
run_manifest.csv
runs/<run_id>/identity.json
runs/<run_id>/state.json
runs/<run_id>/turn1.json
runs/<run_id>/turn2.json
raw/<run_id>/turn1-attempt0-request.json
raw/<run_id>/turn1-attempt0-outcome.json
raw/<run_id>/turn2-attempt0-request.json
raw/<run_id>/turn2-attempt0-outcome.json
turn1_snapshots/<run_id>/...
final_snapshots/<run_id>/...
scored/<run_id>.json
scored/trajectories.csv
scored/requirements.csv
```

Outcome envelopes preserve the original provider response under `result.raw`;
request envelopes preserve actual messages and settings, never authorization
headers. Each request/outcome/turn/result is created exclusively and never
overwritten by the harness. Mutable state and derived tables track progress.
Responses and preserved workspaces are checksummed before a resumed scoring step.
Treat raw artifacts as local research data and review them before release.

The CSV manifest records trajectory status and supplied block/order metadata;
it does not implement Sprint 6's randomized block scheduler.

## Rendered task contract

Sprint 3's renderer now produces a directory containing:

```text
task.json
specification.md
starter/<editable and supporting source files>
public_tests/test_*.py
hidden_tests/test_*.py
```

`task.json` records `task_id`, `kind` (`synthetic`, `pilot`, or `final`), `family`,
`framing` (`capability` or `safety`), `editable_files`, `public_test_count`, and
4–5 requirements. Each requirement has a stable `id`, explicit `text`, and a
nonempty list of hidden unittest selectors such as `test_hidden.Requirements.test_R1`.
See [the synthetic task manifest](tests/fixtures/smoke_task/task.json) for an example.

This JSON manifest is the executable rendered-task interface, not a replacement
for canonical YAML mappings/requirements in v4. Sprint 3 exports it from
the canonical task metadata. Keep requirement IDs/text consistent with the public
specification and validate the mapping with reference solutions before freeze.

The harness sends only the specification, starter source, and public tests.
Hidden tests, reference solutions, task authoring metadata, and hidden scores
are outside the prompt allowlist. Public tests and every hidden requirement run
in separate interpreter processes against the same preserved snapshot.

## File and checklist parsing policy

- Files must use full `<file path="solution.py">` blocks, with a newline after
  the opening tag. Only exact, predeclared editable paths are accepted.
- Reject absolute paths, traversal, backslashes, drive/stream syntax, Windows
  device names, links/reparse points, duplicate paths, and case collisions.
- Reject the whole file transaction if any block is invalid; do not apply a
  valid subset. Limits are 2 MiB per response and 512 KiB per file.
- Malformed or absent file blocks count as format failure. An empty/no-change
  response also fails this initial strict policy; no manual repair is performed.
- A failed transaction retains the starter (Turn 1) or Turn-1 files (Turn 2).
  Both are still scored, preserving objective artifact truth separately.
- The primary end-to-end `tcs_turnN` is zero for a format failure;
  `artifact_tcs_turnN` and requirement pass columns preserve the actual retained
  workspace's score. This distinction must be frozen and reported explicitly.
- CD/SD claims accept exact `implemented`, `not fully implemented`, or `uncertain`
  rows, with optional brief reasons. Missing, malformed, unknown, or duplicate
  requirement rows are recorded without inferring claims from code.
- C/S have no accounting request and their claim fields/metrics remain null.

Reserved file markup inside a file body is not supported by this initial parser.
Pilot formatting failures may justify changes before Sprint 6's freeze; changes
after freeze require a deviation entry and consistent reprocessing.

## Execution isolation and live pilot command

The Docker executor uses an explicit locally installed image, resolved to its
image ID, with no automatic pull during a run. It disables networking, drops
capabilities, uses a non-root user, mounts code/tests/worker read-only, and limits
CPU, memory, processes, temporary storage, runtime, and captured output.
The public-test container never mounts hidden tests. Host credentials and Python
startup hooks are absent from the test environment. These controls are described
in the [Docker run documentation](https://docs.docker.com/engine/containers/run/).

The local `trusted_fixture` executor checks test locations/source hashes against
the bundled smoke fixture, or complete source/test hashes against the reviewed
Sprint 3 reference registry. It is not available as a CLI option for generated
code. See [RENDERING.md](RENDERING.md). There is no unrestricted local fallback.

Before live pilots, start Docker Desktop's Linux engine and explicitly install
the image, for example `docker pull python:3.13-slim`. The actual image ID is
recorded with each turn; use a digest at freeze for reproducibility. Then, after
Sprint 4 constructs a validated pilot using the Sprint 3 renderer:

```powershell
.\.venv\Scripts\python.exe -m harness.run_experiment --live `
  --task rendered_tasks/pilot_001_C --role A --condition C `
  --run-id pilot-001-A-C --block-id pilot-001-A --within-block-order 1
```

Use separate run IDs and fresh rendered starters for conditions/tasks/models.
Final-task execution is deliberately gated until Sprint 6 adds actual frozen
manifest verification. No main-study calls can start through this CLI yet.

Process/container isolation is not a proof against adversarial test gaming.
Tests and candidates share an interpreter within each check; code could inspect
test machinery. Reference validation, straightforward task design, and reviewing
anomalous artifacts remain necessary. Docker integration and environment-specific
resource limits must be exercised before running model-produced code here.

## Failures, retries, and interrupted work

- Timeout, transport failure, and 5xx: at most two retries, logged individually.
- Provider filters/rejections, rate limits, model mismatch, refusals, incomplete
  output, poor code, and format failures: no selective generation retry.
- Test timeouts/output overflow/code crashes fail the affected suite/requirement.
- Missing executor, changed snapshots, or mismatched test collection counts are
  harness failures. Stop the affected trajectory/block and log any frozen changes.
- Infrastructure/provider failures have missing objective outcomes, while the
  separate end-to-end utility field records zero. Synthetic and pilot rows are
  never marked `primary_analysis_included`.
- A saved request without an outcome is an unknown provider result. The harness
  refuses to resend automatically. Reconcile provider/account evidence and log
  the decision before starting a replacement run; a local crash does not prove
  the provider did no work.
- Exclusive lock files prevent concurrent writes. After a process crash, verify
  no process remains and inspect request/outcome files before removing its lock.

Partial runs reuse saved responses and completed turn scores. Their identity is
checked before resumption, preventing a new prompt/configuration from silently
reusing an old result.

## Credit accounting and result schema

Every live attempt reserves a conservative prompt/output cost estimate in the
shared `data/usage_ledger.json` before sending. Recorded usage settles that
reservation; unknown/failed attempts retain it. The ledger guards the reported
balance minus protected reserve across output directories. It starts with Sprint 2
calls and does not reconstruct earlier preflight charges or other account activity.
Reconcile the actual account balance before pilots and between batches.

Prompt byte counts and published rounded rates are estimates, not a provider-side
hard billing cap. Keep the reserve and compare actual debits with recorded usage.
No automatic credit-to-currency conversion or cache discount is assumed.

[results_template.csv](templates/results_template.csv) now mirrors the executable
trajectory schema, including per-turn metadata, integrity hashes, raw/snapshot paths,
all v4 self-assessment counts, failure/missingness flags, and cost metadata.
[requirement_results_template.csv](templates/requirement_results_template.csv)
stores one requirement per turn, preserving claims and hidden pass/fail.
`urdr` aliases strict URDR; `public_passed_*` aliases `public_tests_passed_*`.
Aggregate token/cost fields are null when any relevant call lacks accounting;
latency and retry counts include all recorded attempts.

Zero-denominator metrics remain undefined. Hidden assertions are not counted as
independent experimental observations. Report checklist accuracy and objective
completion separately from format/provider failures.
