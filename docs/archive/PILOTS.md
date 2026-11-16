# Sprint 4 — Excluded pilot calibration

The pilot suite tests task difficulty and the actual two-turn pipeline before
final benchmark construction. It uses Model A (`qwen3.5-397b`) under capability
framing only, with no requirement-accounting intervention. It is not evidence
about a framing effect. All pilot tasks and outputs are excluded from final inference.

## Task profiles

| ID | Files | Requirements | Intended diagnostic |
|---|---|---|---|
| `pilot_001_ingestion` | 1 | 4 | Straightforward parsing, validation, and aggregation |
| `pilot_002_windows` | 1 | 5 | Deduplication/window order, weighted metrics, recursive metadata |
| `pilot_003_calibration` | 2 | 4 | Weighted calibration metrics and report integration |
| `pilot_004_registry` | 1 | 5 | Atomic state transitions, event replay, versioning |
| `pilot_005_intervals` | 2 | 5 | Exact duration parsing, interval algebra, reporting |
| `pilot_006_jsonpatch` | 2 | 5 | JSON Pointer, structural equality, atomic move/copy integration |

These are freshly authored tasks, not reused synthetic fixtures. The unused
sampling draft was archived locally before any model run and replaced after
the initial simpler profiles hit ceiling. See [pilot_plan.json](../../config/pilot_plan.json)
for the active cohort and permanent exclusion IDs. The final benchmark must use
new task definitions, not these tasks or their model outputs.

## Reproduce the pipeline

Start Docker Desktop's Linux engine. The project uses an explicitly pulled
`python:3.13-slim` image and records its actual image ID for each reference and
model trajectory. Code runs with networking disabled, read-only mounts, a non-root
user, resource limits, bounded output, and per-suite timeouts. No GPU is used.

```powershell
.\.venv\Scripts\python.exe -m harness.build_pilots
.\.venv\Scripts\python.exe -m harness.run_pilots --prepare
.\.venv\Scripts\python.exe -m harness.run_pilots --run --campaign new-calibration-run
.\.venv\Scripts\python.exe -m harness.run_pilots --summarize --campaign sprint4-v1
```

Preparation renders C/S from canonical YAML and runs both references against
public and hidden checks, without inference calls. Paid calibration runs only
C; S renderings are used only to validate the infrastructure. The runner verifies
task and image hashes before generating code. `--task-ids` selects a subset for a
staged run. Live runs skip the rejected JSON-patch stress profile by default.
The existing sprint4-v1 records used earlier setup versions, so do not rerun that
campaign with changed code. Reuse any campaign only with unchanged source/configuration;
the harness refuses silent identity changes. Use a new campaign for an explicitly
documented revised calibration setup.

Do not rerun completed pilots just to get lower scores. An implementation change
or task revision must be recorded, and all results remain excluded. Different
pilot profiles are diagnostics, not independent framing-effect observations.

## Budget and execution settings

The initial settings are temperature 0, 8,192 output tokens per turn, and a
180-second provider timeout to allow reasoning plus code generation. These are
the retained settings after the documented stress trials. The transport
still retries only genuine timeout/transport/5xx failures, at most twice. Refusals,
poor code, incomplete outputs, and normal format failures are never selectively retried.

The campaign shares the cross-run credit ledger and imposes the configured
10-credit pilot allowance as an additional reservation ceiling. Unknown requests
retain their cost reservation. This is conservative local accounting, not a
provider-enforced billing cap. Reconcile actual account debits before final calls.
Account rate limits remain unpublished in the project; the runner uses serial
requests and stops on a rate-limit/provider failure rather than probing repeatedly.

On Windows the Docker client uses the explicit local Desktop Linux-engine pipe
and an empty client configuration, avoiding reliance on a user's credential/config
directory. Set `SAFETYFRAME_DOCKER_HOST` only if your local engine endpoint differs.

## Recorded evidence

- Canonical sources: `task_templates/pilot_*/`.
- Matched renderings: `rendered_tasks/pilot_*_C/` and `pilot_*_S/`.
- Reference and equivalence reports: `data/audits/pilots/`.
- Local preparation state: `data/pilot/preparation.json`.
- Requests, raw responses, both snapshots, scores, and per-requirement data:
  `data/pilot/`, following the [harness layout](../methods/HARNESS.md).
- Derived campaign summary: `data/pilot/sprint4-v1-summary.json`.
- Reviewed interpretation and recommended task pattern:
  [report/pilot_calibration.md](../../report/pilot_calibration.md).

Raw pilot outputs and account spending files are ignored by Git pending release
review. Canonical tasks and aggregate interpretation remain inspectable.

## Pre-freeze infrastructure corrections

1. Multi-file C/S audits caught a real order imbalance: rendered alphabetical
   filenames could reorder prompt files. Prompt construction now sorts by reverse-mapped
   canonical paths. A regression test verifies equivalence across that boundary.
2. Candidate import/syntax failures can collapse unittest discovery into one failed
   test. These now fail the affected public/hidden checks rather than being
   misclassified as an infrastructure collection-count error. Genuine unexpected
   collection counts still stop the run.
3. The provider timeout was increased from a preflight-sized 60 seconds to 180;
   Docker setup and live reference execution were verified before paid pilots.

These changes precede final-study freeze. They do not rescue individual model
artifacts or alter hidden checks in response to a framing result.

## Difficulty decisions

The approximate 0.45–0.85 completion range is a design target, not a result to
manufacture. Use clear partial-success tasks with explicit requirements. If a
profile is at ceiling, increase integration/state complexity and reduce exhaustive
public-test revelation while retaining useful repair feedback. If scores are low
because outputs are truncated or malformed, fix the output envelope first rather
than calling that coding difficulty. Preserve reasonable requirements and avoid
unstated or exotic hidden-test traps.

Calibration summaries report both turns, repair gain, format failures, token use,
latency, cost accounting, and final failed requirements. A summary's
`observed_headroom_profiles` includes only complete, format-valid runs in the target
range. Inspect the actual failures before choosing an archetype, and state when
headroom has not yet been demonstrated. A high score is not evidence against
framing sensitivity; this stage does not compare framings.

## Completed calibration and stress disposition

Five usable pilots completed both turns. Four scored 1.00 and interval/reporting
scored 0.80 at both turns; usable mean TCS was 0.96, with no format failures or
provider retries. The interval miss concerned explicitly forbidden uppercase
duration units, not interval algebra. Headroom evidence is therefore preliminary.

The sixth stress task hit three upstream HTTP 504s. [Adaption's streaming API](https://docs.adaptionlabs.ai/inference-stacks/generate-a-model-response)
was then tested in new campaigns, preserving terminal responses and event logs.
Streaming exposed the backend model name and reasoning-only truncation at both
8,192 and 16,384 tokens; the final repair stream ended without a terminal response.
It is not a usable coding score. The guard accepts only explicitly recorded model
identifiers and rejects unfamiliar changes. The incomplete stream is not manually
reconstructed into an implementation.

Streaming support remains available, but the retained default is non-streaming
at 8,192 tokens, as validated on the five usable trajectories. Do not repeat the
stress profile merely to obtain a score. Its failed/unknown charges stay in the
credit ledger. See the [calibration record](../../report/pilot_calibration.md) for exact
measurements, accounting, exclusions, and the provisional final-task recommendation.
