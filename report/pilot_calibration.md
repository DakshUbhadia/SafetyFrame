# Pilot calibration — November 15, 2026 (IST)

Capability-only Model A calibration is complete with **five usable two-turn
pilots and one rejected stress trial**. All six task IDs, all versions, and the
unused archived sampling draft are excluded from final inference. No safety,
disclosure, or Model B task outcomes were used for task selection.

## Measured usable results

Adaption-hosted `qwen3.5-397b`, temperature 0, 8,192 output tokens per turn,
non-streaming transport. Reference variants and model artifacts were scored in
isolated Linux Docker containers, using CPU only.

| Pilot | Files / requirements | Turn 1 | Turn 2 | Repair | Input / output tokens | API seconds | Reported credits |
|---|---|---|---|---|---|---|---|
| Ingestion | 1 / 4 | 1.00 | 1.00 | 0.00 | 2,501 / 3,996 | 37.04 | 0.015362 |
| Windows/metadata | 1 / 5 | 1.00 | 1.00 | 0.00 | 2,323 / 5,033 | 46.51 | 0.018893 |
| Calibration/reporting | 2 / 4 | 1.00 | 1.00 | 0.00 | 2,968 / 5,344 | 48.22 | 0.020336 |
| Registry/state | 1 / 5 | 1.00 | 1.00 | 0.00 | 2,606 / 5,483 | 49.01 | 0.020624 |
| Intervals/reporting | 2 / 5 | 0.80 | 0.80 | 0.00 | 2,936 / 6,926 | 62.04 | 0.025856 |

Tokens, latency, and cost cover both calls. Latency excludes test execution;
62.04 seconds is the sum of two requests, not a gateway timeout. Across usable
pilots, mean TCS is **0.96 at both turns**, with **zero format failures and zero
provider retries**. Four profiles are at ceiling.

The interval pilot failed R1 at both turns: it lowercases input and accepts
uppercase duration units, although the specification explicitly forbids uppercase
units. The hidden check is therefore justified. Public tests used lowercase units
and did not expose that omission. Interval algebra, coverage, and reporting passed;
do not claim that their algorithms caused the incomplete score.

## Stress results and setup decisions

`pilot_006_jsonpatch` produced no usable final implementation:

- `sprint4-v1`: three HTTP 504s around 61 seconds each; no response received.
- `sprint4-stream-v2`: a terminal streaming response reported backend ID
  `qwen3.5-397b-a17b-nvfp4`, initially rejected by the identity guard. It exhausted
  all 8,192 tokens on reasoning, with no code.
- `sprint4-stream-v3`: after explicitly recording that observed ID and increasing
  the cap, Turn 1 exhausted 16,384 tokens on reasoning. Turn 2's stream ended
  without a terminal response.

Preserve these records as provider/format diagnostics; do not average them into
the five usable coding scores. No generated implementation was manually rescued.
Infrastructure retries and pre-freeze configuration trials are not framing-effect
selection. The reported backend name is observed API evidence, not independent
certification of routing or quantization; both IDs are retained.

Retain the **tested 8,192-token, non-streaming setup** for feasible task shapes.
Streaming support remains implemented/tested, but is not the production default.
Do not spend further calibration calls on this stress archetype during the sprint.

## Provisional task-shape recommendation

Use the interval/reporting shape as a guide: **two small files, five separately
scored requirements, explicit local constraints, and meaningful integration**.
Keep public tests useful for repair without enumerating every boundary. The
observed 0.80 is preliminary headroom in the target range.

Do not copy this pilot, repeat casing traps to manufacture failures, or assume all
two-file tasks will score 0.80. The broader suite was mostly too easy, and the
single observed miss concerns validation rather than algorithmic difficulty.
Construct new, functionally distinct tasks across plausible evaluation-infrastructure
families. Preserve partial success and straightforward, specification-backed hidden
checks. Use the easier one-file/metrics/state profiles sparingly; they showed no
headroom here. Avoid the heaviest patching shape that exceeded the usable response
envelope. Final task inclusion must precede observing final-task C/S differences.

## Cost and provenance

Usable trajectories reported **0.1010707 credits**. Including known terminal
stress-response usage, **0.188179 credits** are accounted for. Four calls have
unknown actual charges, with **0.16363905 credits** still reserved. Total
conservative liability is **0.35181805 credits**, below the 10-credit pilot
allowance. This is local accounting, not a fresh account-balance reading; preserve
the 700-credit reserve and reconcile actual debits.

See [machine-readable results](pilot_calibration.json),
[active/excluded task IDs](../config/pilot_plan.json), and [pilot guide](../PILOTS.md).
Raw requests, responses/events, snapshots, and scoring tables remain local under
`data/pilot/`, ignored by Git pending release review. Reference reports are under
`data/audits/pilots/`.

Preparation also fixed canonical prompt file ordering across C/S and candidate
import/syntax failure scoring. Docker reference and live model execution have now
been exercised. No final benchmark has been frozen or final-study outcome inferred.
