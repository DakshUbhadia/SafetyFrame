# SafetyFrame-Eval — Data Dictionary

One row in the main trajectory table represents one `task × model × condition` trajectory.

## Identifiers

| Field | Type | Meaning |
|---|---|---|
| `run_id` | string | unique trajectory ID |
| `task_id` | string | frozen task ID |
| `task_family` | string | task family |
| `model_id` | string | exact model identifier |
| `provider` | string | provider name |
| `condition` | enum | C, S, CD, SD |
| `framing` | enum | capability, safety |
| `requirement_accounting` | bool | treatment flag |
| `block_id` | string | task×model block |
| `within_block_order` | int | randomized order |

## Model/API metadata

| Field | Type |
|---|---|
| `timestamp_turn1` | ISO datetime |
| `timestamp_turn2` | ISO datetime |
| `provider_request_id_turn1` | string/null |
| `provider_request_id_turn2` | string/null |
| `model_version_metadata` | string/null |
| `temperature` | float/null |
| `top_p` | float/null |
| `seed` | string/null |
| `max_output_tokens` | int |
| `input_tokens_turn1` | int/null |
| `output_tokens_turn1` | int/null |
| `input_tokens_turn2` | int/null |
| `output_tokens_turn2` | int/null |
| `latency_turn1_sec` | float/null |
| `latency_turn2_sec` | float/null |

## Integrity fields

| Field | Type |
|---|---|
| `prompt_hash` | string |
| `repo_hash` | string |
| `public_test_hash` | string |
| `hidden_test_hash` | string |
| `mapping_hash` | string |

## Format fields

| Field | Type |
|---|---|
| `format_success_turn1` | bool |
| `format_success_turn2` | bool |
| `files_returned_turn1` | int |
| `files_returned_turn2` | int |

## Public-test fields

| Field | Type |
|---|---|
| `public_passed_turn1` | int |
| `public_total` | int |
| `public_passed_turn2` | int |

## Hidden requirement scoring

| Field | Type |
|---|---|
| `requirements_total` | int |
| `requirements_passed_turn1` | int |
| `requirements_passed_turn2` | int |
| `tcs_turn1` | float [0,1] |
| `tcs_turn2` | float [0,1] |
| `repair_gain` | float [-1,1] |

Store requirement-level pass columns separately, e.g.:

```text
r1_pass_turn1
r1_pass_turn2
r2_pass_turn1
...
```

## Self-assessment fields — CD/SD

| Field | Type |
|---|---|
| `r1_claim` | enum |
| `r2_claim` | enum |
| `...` | |
| `actual_failed_requirements` | int |
| `failed_claimed_implemented` | int |
| `failed_acknowledged` | int |
| `claimed_unmet_total` | int |
| `urdr_strict` | float/null |
| `urdr_lenient` | float/null |
| `false_completion_rate` | float/null |
| `completion_precision` | float/null |
| `unmet_disclosure_precision` | float/null |

Claim enum:

```text
implemented
not_fully_implemented
uncertain
missing
```

## Provider failures

| Field | Type |
|---|---|
| `provider_failure_type` | enum/null |
| `retry_count` | int |
| `primary_analysis_included` | bool |
| `end_to_end_utility_score` | float/null |

Failure enum:

```text
timeout
5xx
transport
provider_filter
provider_rejection
none
```

## Raw paths

| Field | Type |
|---|---|
| `turn1_raw_path` | string |
| `turn2_raw_path` | string |
| `turn1_workspace_path` | string |
| `turn2_workspace_path` | string |

## Derived task-level table

Create a separate task-level analysis table with:

```text
task_id
model_id
tcs_C
tcs_S
tcs_CD
tcs_SD
baseline_gap
disclosure_effect_C
disclosure_effect_S
disclosure_framing_interaction
```

For Model B, CD/SD may be null.

## Missing-value rules

- Do not encode missing as zero unless the analysis definition explicitly says zero utility.
- Use null/NA for undefined self-assessment metrics when there are no failed requirements.
- Keep reason for missingness explicit.

## Sprint 2 executable storage

The trajectory schema is defined by `FIELDS` in `harness/run_experiment.py` and
mirrored in `templates/results_template.csv`. Outputs include both dictionary
names and v4 compatibility aliases: `public_passed_turnN` equals
`public_tests_passed_turnN`; `urdr` equals `urdr_strict`; `test_hash` combines
public/hidden test hashes. Aggregate tokens, latency, and reported/estimated cost
supplement per-turn metadata. Missing accounting remains null.

Per-requirement truth and claims use the long-form
`templates/requirement_results_template.csv`: one row per requirement per turn,
with stable IDs. This replaces optional wide `r1_claim`/`r1_pass_turn1` columns
without losing requirement-level observations. Each run's scored JSON also
retains detailed hidden-check results, checklist parse issues, and both turns.

`artifact_tcs_turnN` is the actual preserved workspace's requirement score.
`tcs_turnN` is the end-to-end endpoint, set to zero when the full-file transaction
is malformed or missing. Actual requirement pass counts remain unchanged;
report format failures alongside this distinction. Initial parser policy is
documented in [HARNESS.md](HARNESS.md) and must be frozen before final calls.

`phase` distinguishes synthetic, pilot, and final data; synthetic/pilot rows are
always excluded from primary scientific analysis. Provider/infrastructure
failures have null missing outcomes and zero separate end-to-end utility.
`status` and the local run manifest preserve partial, failed, and completed work.
Additional failure labels include `rate_limit`, `model_mismatch`, `provider_error`,
`invalid_provider_response`, and `missing_credentials`; none triggers selective
regeneration of weak code. See the harness documentation for retry rules.
