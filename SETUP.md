# Sprint 1 — Environment and provider setup

## Current status

**Local setup implemented; live account acceptance pending.** Python 3.13.7 was
found and `.venv` was created in this workspace. Sprints 1–2 use the standard library;
Sprint 3 adds pinned PyYAML 6.0.3 for canonical task parsing. Sprint 2's
two-turn provider wrapper, public/hidden runners, parser, and resumable logging
are now implemented; see [HARNESS.md](HARNESS.md).

The initial inspection had no configured key; authenticated catalogue discovery
subsequently succeeded. Model A is selected as `qwen3.5-397b` and Model B as
`deepseek-v4-flash`. Both passed generation preflight at temperature 0 and an
8,192-token output cap. Sprint 4 has now completed five excluded Model A coding
pilots using that cap, with one preliminary partial-success profile. See
[PILOTS.md](PILOTS.md) for usable outcomes, stress failures, and retained settings.
The user's latest reported balance is **3,500 Adaption credits**, superseding the
earlier 1,250-credit allocation. Published hosted token rates have been checked;
account-specific limits and actual spending still need verification.

**Account discovery update:** The user's catalogue run succeeded with HTTP 200
and returned seven hosted model IDs: `glm-5.3-flash`, `glm-5.2`, `qwen3.5-397b`,
`gemma-4-26b-a4b-it`, `qwen3.8-27b`, `deepseek-v4-flash`, and `gemma-4-31b-it`.
Evidence: `data/setup/preflight-20261114T091607Z-d5c0f392.json`.
The key works for model listing. This does not yet verify generation access,
per-model settings, actual remaining credits, or rate limits. The response
contained no rate-limit headers. No generation requests were made by that command.

## Local commands

Run these from the repository root in PowerShell. Activation is optional; using
the virtual environment executable avoids PowerShell execution-policy changes.

```powershell
# Only needed when creating the environment on a new checkout:
python -m venv .venv

.\.venv\Scripts\python.exe -m pip --disable-pip-version-check --isolated install --no-cache-dir --progress-bar off -r requirements.txt
.\.venv\Scripts\python.exe -m harness.preflight --offline
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Python 3.11 or later is required; record the exact version used for final runs.
PyYAML is the only third-party Python dependency currently required; the renderer
uses a restricted safe loader. See [RENDERING.md](RENDERING.md) for Sprint 3 commands.
The offline command validates the initial design/configuration and calculates
run counts without contacting any provider. Success here does **not** certify
that the live Sprint 1 exit criteria are met.

## Configure account access locally

Set `ADAPTION_API_KEY` in the current terminal, or copy `.env.example` to `.env`
and enter the key there using a local editor. The preflight loads literal
`KEY=value` lines from `.env`; existing process variables take precedence.
It does not execute shell expressions or expand `${...}` values. Never paste
credentials into `config/study.json`, the report, or preregistration.

`.gitignore` excludes `.env`, environment variants, the virtual environment,
Python caches, and account-specific preflight JSON. `.env.example` is safe to track.
Store any catalogue or response artifacts outside `data/setup/` only after reviewing them.

```powershell
.\.venv\Scripts\python.exe -m harness.preflight --list-models
```

This reads the account-authorized hosted catalogue and saves a timestamped report
under `data/setup/`. An API key cannot establish the rate limit or balance by itself;
record those from your account dashboard or provider support with an evidence reference.

## Select models and supported settings

Edit `config/study.json` after discovery:

1. Choose a strong coding model as A and a meaningfully different model family as B.
2. Copy exact IDs from the account catalogue, not documentation examples.
3. Record each family and selection rationale independently of framing outcomes.
4. Verify context/output capacity and supported settings using provider/model evidence.
5. Adjust `generation.max_output_tokens` consistently across conditions within each model.
   The retained value, 8192, is accepted in setup and five usable coding pilots;
   a larger reasoning cap was tested only in the rejected stress trial.
6. Add `generation.temperature: 0` only if supported; otherwise record the lowest
   supported setting or explain why the parameter is omitted.
7. Set `settings_verified` and `settings_evidence` only after checking the actual
   study settings. Smoke requests now use the configured study output cap to
   check parameter acceptance; they do not validate coding quality or maximum context use.
8. Record each provider's `requests_per_minute` and `rate_limit_source`.

The current preflight supports Adaption's documented hosted Responses contract.
Another provider requires its own adapter and verified contract; changing the URL
alone is not sufficient. The Adaption wrapper is implemented in Sprint 2.
`top_p` and `seed` are omitted because the consulted Adaption Responses schema does
not list them; do not assume those settings are supported by every hosted model.

## Budget worksheet

All amounts must use one unit, such as account credits or USD. Record:

- `budget.available`: reported current balance, now 3,500 Adaption credits;
  update it to the remaining usable balance after checking the account.
- `budget.protected_reserve`: 700 credits held back as a conservative planning choice.
  This leaves a 2,800-credit ceiling, not a spending target.
- `budget.unit` and `budget.source`: unit and evidence/date for balance and rates.
- `models.A/B.estimated_cost_per_trajectory`: estimated cost of **both turns**,
  including replayed context and expected output.
- `budget.pilot_allowance`: estimated total cost of 4–6 pilot tasks and preflight calls.
- `budget.retry_allowance`: explicit reserve for infrastructure retries.

At task count `n`, projected cost is:

```text
4n × Model-A trajectory cost
+ 2n × Model-B trajectory cost
+ pilot/preflight allowance
+ retry allowance
```

The tool reports 16/18/20-task scenarios and checks the configured target against
funds after the protected reserve. An estimate is not a provider quote or account-enforced spend cap. No conversion
between credits and currency is assumed. The specification's sponsored credit
amount is not treated as a verified account balance.

### Selected models and cost assumptions

Model A uses Qwen3.5-397B for the full factorial; Model B uses DeepSeek V4 Flash for C/S.
They are different families and both appear in the authenticated catalogue.
Selection does not claim either is best on our unbuilt benchmark. Verify coding
suitability using excluded pilots before freezing the models and task design.
GLM-5.2 was excluded at setup after two transport/timeouts at 45 and 60 seconds,
before any main-study outcomes. No further GLM requests are planned.

Published hosted rates checked November 14, 2026, in credits per million tokens:

| Role | Exact ID | Input | Output | Trajectories at 18 tasks |
|---|---|---|---|---|
| A | `qwen3.5-397b` | 0.55 | 3.50 | 72 |
| B | `deepseek-v4-flash` | 0.045 | 0.14 | 36 |

Source: [Adaption hosted pricing](https://docs.adaptionlabs.ai/inference-stacks/models).
Upstream cards: [DeepSeek V4 Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash),
[Qwen3.5](https://huggingface.co/Qwen/Qwen3.5-397B-A17B).

Assume 24,000 total input tokens across both turns (including replay) and at most
16,384 output tokens per trajectory with the proposed 8,192-per-turn cap. Ignore
cache discounts. Rounded-up per-trajectory estimates are 0.071 credits for A and
0.0034 for B. These are transparent planning assumptions, not measured task sizes.

At 18 tasks the core estimate is 5.2344 credits. Add 10 credits for pilots/preflight
and 20 for retries: **35.2344 credits planned**. A stress scenario with 200,000 total
input tokens per trajectory and the same output caps costs about **42.46 credits**
including those allowances. Larger prompts, output/reasoning billing, model-setting
changes, or rate changes require recalculation. Actual account debits take precedence.

Do not expand to more models or tasks simply because funds remain. Keep the core
18-task design, confirm adequate headroom through pilot usage, then freeze. The
bottleneck is validated task construction and finishing the report.

Generation evidence: Qwen completed in 12.96 seconds in
`data/setup/preflight-20261114T093213Z-fb983287.json` (then assigned role B);
DeepSeek completed in `data/setup/preflight-20261114T093258Z-8de026bd.json`.
The first Qwen call exhausted a 128-token reasoning cap; the follow-up used the
actual proposed study cap and passed. These are setup calls, not benchmark results.
Timed-out calls may still have incurred provider charges; reconcile the balance
before pilots rather than assuming every timeout costs zero.

Use paid inference only for necessary model preflight, excluded calibration pilots,
and the core Model A / Model B dataset. Keep rendering, validation, reference tests,
analysis, and report drafting local. Skip paid task-idea generation, optional
extensions, and stochastic reruns by default. Reconcile actual usage with the account
balance after pilots and each execution batch before starting more work. The
Sprint 2 ledger reserves/settles live-attempt cost estimates in
`data/usage_ledger.json`. It does not reconstruct earlier preflight charges or
other account usage; preflight itself is not a billing ledger.
Revisit the reserve only for a documented core-study need. Do not weaken matching or
validation to save credits; use 16 validated tasks if 18 will not fit.

## Live acceptance

```powershell
# One small, potentially billable request per model; no automatic retries:
.\.venv\Scripts\python.exe -m harness.preflight --smoke

# Diagnose one role if needed; this cannot complete the two-model acceptance:
.\.venv\Scripts\python.exe -m harness.preflight --smoke --role A
```

Each smoke request uses a new stateless input, disables tools and agentic memory,
disables provider storage, and uses the configured study output cap (currently
8,192 tokens). An earlier 128-token cap exhausted Qwen's reasoning budget before
any answer. The prompt still requests only a short acknowledgement. It records requested
and returned model IDs, response/request IDs when exposed, usage, latency, status,
and allowlisted rate-limit headers. Missing optional usage/version fields remain null.
Incomplete, failed, or empty responses do not count as success. Model refusals and
format parsing use the initial policies in [HARNESS.md](HARNESS.md), pending freeze.
Paid smoke requests are skipped until a costed study plan fits the ceiling;
catalogue discovery and offline checks remain available without a cost estimate.

Reports are retained as unique files so later checks do not overwrite earlier evidence.
No authorization headers or provider error bodies are written. Redirects are rejected
to avoid forwarding credentials. Tests use simulated providers and never spend credits.

Local validation passed: 12 offline unit tests, configuration validation, and
`pip check`. The initial catalogue attempt had no key and made no network request;
the subsequent user-run catalogue discovery succeeded as recorded above.
Timestamped evidence is in `data/setup/`.

Exit codes: `0` = successful offline validation/catalogue discovery, or all live
acceptance criteria met; `1` = live checks incomplete/failed; `2` = setup/configuration error.

Mark Sprint 1 complete only after:

- Both exact selected models produce completed text responses in one all-role smoke run.
- Families, generation support, rate limits, and an adequate budget are documented.
- The resulting preflight report has `sprint_1_complete: true`.
- The actual choices/evidence are copied into the draft preregistration and Methods notes.

## Review findings and remaining boundaries

The sprint plan preserves v4's 18-task target, Model-A factorial, Model-B C/S,
two-turn endpoint, and task-level inference. The setup preserves those invariants.
At 18 tasks the core workload is 108 trajectories / 216 responses, before pilots
and retries. Account access and budget are external dependencies, so they cannot
be marked complete based on local scaffolding.

The results CSV starter has been reconciled in Sprint 2, with a separate
requirement-level claims/pass table. No final benchmark,
freeze manifest, main-study run manifest, or study outcomes are fabricated here.
Sprint 6 completes a local preregistration and committed freeze; no human
signature or external registration is asserted. The retained study has 16
tasks and 192 planned responses. Official account RPM remains unconfirmed;
the frozen collector instead imposes a conservative serial minimum of
60 seconds between request starts. It does not claim a confirmed account limit.
The original Sprint-1 account-rate evidence gap remains visible.
See [FROZEN_STUDY.md](FROZEN_STUDY.md) for current execution and budget policies.

## Provider sources consulted

- [Adaption hosted model listing](https://docs.adaptionlabs.ai/api/python/resources/models/methods/list):
  account-scoped discovery through `GET /api/v1/models?type=hosted`.
- [Adaption Responses API](https://docs.adaptionlabs.ai/api/resources/responses/methods/create):
  endpoint, bearer authorization, input and generation fields, storage/memory/tool
  controls, response status, and usage metadata.

These sources establish the API contract; they do not establish this user's
model access, account pricing, model-family suitability, or remaining balance.
