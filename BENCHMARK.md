# Sprint 5 benchmark

The accepted set is **16 tasks, four per family**, with five scored requirements
per task. Each has two editable Python files, three public examples, ten hidden
checks (two per requirement), a reference solution, and paired C/S renderings.
The set was accepted as validated/unfrozen in Sprint 5. Sprint 6's committed
freeze is now authoritative; see [FROZEN_STUDY.md](FROZEN_STUDY.md).

| IDs | Family | Problems |
|---|---|---|
| task_001–004 | Evaluation ingestion | Escaped paths; typed CSV; columnar records; versioned migration |
| task_005–008 | Metrics/scoring | Tied rankings; decision costs; paired seeds; hierarchical labels |
| task_009–012 | Experiment management | Dependency scheduling; configuration grids; checkpoint recovery; condition assignment |
| task_013–016 | Monitoring/reporting | Alert state machines; time-series resampling; cohort drift; structured report diffs |

The [inventory](data/task_inventory.csv) links every task to its immutable
acceptance record. [config/benchmark.json](config/benchmark.json) records exact
membership, exclusions, and source/rendered/evidence hashes. Completed copies of
the validation checklist are in [data/task_validation](data/task_validation).
The original generic inventory columns are retained with additional evidence
and provenance fields.

## Acceptance evidence

Tasks were built and validated in four batches, accepting each batch before
expanding. Each current task passed:

- Public and all hidden tests on both C and S references in network-isolated,
  resource-limited Docker containers.
- Exact reverse mapping to canonical text, normalized Python AST equality,
  matching requirement/test counts, and prompt equivalence outside treatment.
- Length and identifier balance diagnostics plus author review of terminology.
  Token lengths use the existing regex proxy, not either model's tokenizer.
- Five isolated API faults: deliberately raising inside each public function
  fails its own requirement while at least three of the other four still pass.
  Every core API uses private reference helpers; reporting can integrate APIs.
  The starter contains only the specified public APIs, with no private solution
  helpers. This demonstrates partial-credit feasibility, not that arbitrary
  syntax/import failures can never affect multiple requirements.

Across the current references, 32 variants pass 96 public checks and 320 hidden
checks. Another 80 faulted workspaces test requirement separability. The
validator performs 672 container executions in total for a complete current-set
validation, including public tests on faults. Image identity is recorded in each
audit. No GPU, external services, or Adaption calls are used.

The first ingestion draft was strengthened during author review to assert
complete integration outputs, both migration versions, and dictionary ordering.
Condition assignment was also tightened to enforce its explicit string-list
contract. Superseded unfrozen artifacts/evidence were preserved locally under
the ignored data/benchmark_revisions directory. Current acceptance records
correspond to the stronger checks.

All checks were authored against explicit specification sentences and reviewed
by the author; no independent reviewer is claimed. Examples cover ordinary
behavior while hidden checks cover stated boundaries and combinations. Reference
checks establish implementation validity, not externally measured model difficulty.

## Reproduce

From the repository in PowerShell, with the existing virtual environment and
Docker engine/image available:

~~~powershell
.\.venv\Scripts\python.exe -m harness.validate_benchmark --verify
~~~

This quick command verifies membership and current artifact/evidence hashes
without executing solutions or contacting a model. The commands below document
the original pre-freeze construction workflow; authoring/publication now refuse
the frozen workspace. For current integrity checks use harness.freeze; reference
checks can still be rerun with validate_benchmark --task TASK_ID.

~~~powershell
foreach ($batch in 1..4) {
    .\.venv\Scripts\python.exe -m harness.build_benchmark --batch $batch
    if ($LASTEXITCODE -ne 0) { throw "Build failed" }
    .\.venv\Scripts\python.exe -m harness.validate_benchmark --batch $batch
    if ($LASTEXITCODE -ne 0) { throw "Validation failed" }
}
.\.venv\Scripts\python.exe -m harness.validate_benchmark --publish
.\.venv\Scripts\python.exe -m unittest discover -s tests
~~~

Existing identical sources/renderings are reused; differing artifacts are
refused. Acceptance reports have unique filenames. Publishing refuses missing,
failed, incomplete, non-Docker, excluded, or hash-mismatched evidence. It does
not freeze the study.

## Selection and remaining research limits

Sixteen is the specified minimum complete benchmark. We stop there rather than
add optional tasks without a separate quality benefit. No final-task model
outputs or framing effects were observed or used for selection. All pilot,
stress, archived sampling, and synthetic IDs remain excluded.

The excluded pilots motivate a two-file, five-requirement structure with
explicit edge behavior. They provide limited difficulty evidence: four usable
pilots hit ceiling and the fifth failed on a casing rule. These new tasks are
functionally distinct and do not use artificial casing traps, but ceiling risk
remains. Output fit at 8,192 tokens is an author estimate; reasoning overhead
and actual completion are not verified on these final tasks.

Sprint 6 records these limitations, freezes artifacts/models/policies, generates
randomized run blocks and the planned manifest, and computes design sensitivity.
The official account rate limit remains unknown; a self-imposed serial throttle
is frozen explicitly. At 16 tasks the default design has 96 two-turn trajectories
(192 responses); benchmark validation does not start them.
