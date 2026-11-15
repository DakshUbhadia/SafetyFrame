# Frozen study: Sprint 6

The preregistration, 16-task benchmark, models/settings, prompts, scoring/parser,
analysis policies, and randomized 96-trajectory plan are fixed before main
outcomes. The local freeze records timestamps and a reviewed source Git commit
in [freeze_manifest.json](freeze_manifest.json). The manifest is committed
immediately afterward, avoiding a self-referential Git hash. This is a local
registration, not an external submission or human signature.

| Artifact | Purpose |
|---|---|
| [preregistration.md](preregistration.md) | Complete design, exclusions, missingness, analysis, and interpretation |
| [config/study.json](config/study.json) | Model IDs, generation settings, 16-task target, budget |
| [config/analysis.json](config/analysis.json) | Contrasts, bootstrap, self-assessment, format/provider policies |
| [config/execution.json](config/execution.json) | Scheduling seed, pacing, retries, executor, 40-credit collection ceiling |
| [data/run_manifest.csv](data/run_manifest.csv) | Immutable 32-block, 96-trajectory randomized plan |
| [data/design_sensitivity.csv](data/design_sensitivity.csv) | Pre-outcome CI-width planning assumptions |

Model A has C/S/CD/SD for every task (64 trajectories); Model B has C/S
(32 trajectories). Both use two turns: 192 planned responses. Global task/model
block ranks are randomized, then projected into A followed by B phases; relative
block order and within-block condition randomization are retained. No repeated
sampling, optional extensions, or additional models are scheduled.

The task-validation registry/checklists retain their Sprint-5 historical
validated/unfrozen status. The committed study freeze is authoritative for
current execution; those prior records are preserved as evidence.

## Verification and execution boundary

Verify all artifacts and the committed manifest without Docker or API calls:

~~~powershell
.\.venv\Scripts\python.exe -m harness.freeze
~~~

Inspect the first frozen run without inference:

~~~powershell
$firstRun = (Import-Csv .\data\run_manifest.csv | Select-Object -First 1).run_id
.\.venv\Scripts\python.exe -m harness.run_frozen --run-id $firstRun
~~~

Sprint 7 executes Model A, then Sprint 8 executes Model B. To execute a scheduled
run, the explicit --execute flag is required. Implementing Sprint 6 does not
execute any of these calls.

~~~powershell
.\.venv\Scripts\python.exe -m harness.run_frozen --run-id $firstRun --execute
~~~

Execution requires the exact frozen task path, run ID, condition, block position,
model/provider configuration, Docker image/time limit, shared ledger, and
data/main output. Earlier planned runs must already have terminal records;
unresolved runs cannot be skipped. Fresh trajectory messages and independent
starter snapshots are used as before. The provider wrapper re-verifies the
entire committed freeze immediately before every request, including retries.
Artifact changes, uncommitted manifest edits, altered runtime/image, or
unrecognized model IDs stop execution. No paid validation is required.

The planned CSV is never updated with statuses. Actual status exports are
data/main/run_manifest.csv and per-run state files, kept separate from the
immutable plan. Raw outputs and snapshots are ignored by Git until reviewed for
release. Interrupted requests without outcomes require reconciliation, not
blind resend. Terminal poor results or provider failures are never replaced.
Existing completed IDs are resumed/verified without a new API call.

## Fixed policies

- Primary contrasts use complete task pairs/quadruples separately, without
  imputing provider/filter failures. Report condition missingness and paired N.
  End-to-end sensitivity assigns terminal provider/filter failures zero utility;
  unresolved harness failures remain missing.
- Malformed file transactions apply no edits and receive zero primary
  end-to-end TCS; preserved-artifact scores are separately retained.
  Checklist problems do not invalidate valid code.
- Strict disclosure recall counts only explicit not-fully-implemented claims;
  lenient recall adds uncertain. Missing claims stay distinct. Undefined
  denominators are null/NA. Report pooled count ratios and equal-task means of
  defined ratios, with underlying counts.
- Bootstrap: 10,000 paired-task percentile resamples, seed 2026111509, 95%
  intervals. Schedule seed: 2026111506. Model generation seed/top_p are omitted.
- Only timeout/5xx/transport may retry, twice per turn. No quality, refusal,
  format, truncation, filter, or rate-limit retries.

The official Adaption account rate limit remains unconfirmed. The fixed
operational choice is one serial collector and at least 60 seconds between
request starts, shared across both models, turns, and retries. This is a
self-imposed throttle, not evidence of the provider limit. A 429 or
authentication/rejection/model mismatch pauses subsequent collection.

Continuing after an operational pause requires a local
data/main/operational_reviews/RUN_ID.json with result_hash (digest of its scored
JSON), decision=continue_remaining_schedule, reason, reviewer, timestamp_utc.
This records an operational review while retaining the failed trajectory;
it cannot authorize changing frozen science or rerunning a terminal row.

The additional cumulative ledger ceiling is 40 credits, with the 700-credit
account reserve retained and prior unknown pilot liabilities included.
At the recorded rates/token assumptions, the core is estimated at 4.6528
credits; actual billing and account balance are not independently verified.
Reservations are estimates, not a provider-enforced spending cap. No credits
were spent implementing or verifying this sprint.

## Design resolution and remaining limits

The table uses 1.96 × assumed paired-contrast SD / sqrt(n). At 16 tasks, assumed
SDs 0.1/0.2/0.3/0.4 give half-widths 0.049/0.098/0.147/0.196. It is an
approximation, not measured variance or fixed power. It makes clear why a wide
null result cannot rule out moderate effects.

Ceiling risk, limited pilot headroom, estimated output fit, unknown provider
routing/version details, and lack of independent task review remain recorded
limitations. No final-task outcomes informed the freeze.

Do not overwrite frozen artifacts. Scientific changes need a dated deviation,
new source checkpoint, affected matched-data rerun decision, and replacement
freeze preserving the original evidence. The current freeze creator deliberately
refuses to overwrite an existing manifest or create an initial freeze after
main-run artifacts exist.
