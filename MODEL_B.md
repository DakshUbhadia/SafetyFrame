# Model B framing generalization

Sprint 8 executes the frozen DeepSeek Model-B C/S comparison on the same
sixteen final tasks: 32 trajectories, two turns each. It uses the existing
frozen runtime, generation settings, scoring, serial pacing, retry rules,
and shared 40-credit ledger ceiling. No CD/SD extension is collected.

## Collection and resumption

**Completed:** all 32 planned trajectories are terminal: 29 completed and three
HTTP-5xx provider failures. There are 59 saved/scored responses. The paired
C-minus-S estimate is -0.200 (95% task-bootstrap CI [-0.431, 0.000], 13 pairs).
See [results and figures](report/model_b/results.md) and
[integrity evidence](report/model_b/integrity.json).

**Major limitation:** 50/59 replies used all 8,192 output tokens on reasoning
and emitted no final text. Raw-payload audits found no text-extraction loss.
These remain format-failure zeros under the frozen policy. Only one task has
valid Turn-2 file output in both frames, so this is chiefly a budget-constrained
code-emission result, not a clean comparison of coding correctness. No limits,
scores, exclusions, or retry rules were changed after collection.

Known reported B usage cost is 0.061897 credits; retained B liability including
unknown usage is 0.11046535 credits. Actual account debits remain unverified.
Collection commands below are retained for provenance and idempotent resumption;
the completed phase does not need to be run again.

~~~powershell
.\.venv\Scripts\python.exe -m harness.freeze
.\.venv\Scripts\python.exe scripts/collect_frozen.py --role B --execute
~~~

Only frozen B run IDs are executed, in their scheduled order. All preceding
A rows must already have terminal records. Existing completed IDs validate
saved responses and workspaces without repeating inference. Provider failures
remain in the dataset; no poor or failed row is selectively replaced.
Critical frozen operational pauses require a documented review.

Progress is data/main/collector-B.json. Actual run states and exports remain
separate from the immutable data/run_manifest.csv. Raw responses, both scored
workspaces, public feedback, claims metadata, retry outcomes and identities stay
local under data/main. Credentials and response text are excluded from the
reviewed scored release.

## Audit and analyze after all 32 rows are terminal

~~~powershell
.\.venv\Scripts\python.exe -m analysis.model_b
~~~

Or wait for the active collector and then automatically audit, generate results,
and reproduce all numerical/narrative outputs:

~~~powershell
.\.venv\Scripts\python.exe scripts/finish_model_b.py --wait
~~~

The shared phase loader audits B's own task/model identities, settings, stored
response/workspace hashes, frozen requirement scoring, and request/outcome retry
sequences. It refuses incomplete phases. The default A loader still produces
exactly the eight reviewed Sprint-7 numerical/narrative outputs; A's release
is preserved unchanged.

Outputs go to report/model_b: scored_dataset.json, summary.json, condition and
contrast tables, per-task differences, separate-model comparison tables, results
text, and PNG/SVG/PDF scientific figures. Model B's independent paired C−S
estimate uses the frozen 10,000 task-bootstrap resamples and seed 2026111509.
Primary, provider-utility, and valid-format estimands remain separate, with
condition-specific missingness and failures visible. Self-assessment is not
scored in this baseline-only B design.

The comparison reads A's reviewed summary and checks its integrity. Each
model retains its own estimate, interval, and complete-pair count. The model
effects are never pooled into a universal model-population effect. Differences
between point estimates or overlapping intervals alone do not establish a
model-by-framing interaction.

## Reproduce without inference

~~~powershell
.\.venv\Scripts\python.exe -m analysis.model_b --dataset report/model_b/scored_dataset.json --output report/model_b_reproduced
.\.venv\Scripts\python.exe -m unittest discover -s analysis/tests
~~~

Plotting dependencies are pinned in analysis/requirements.txt. Numerical JSON,
CSVs, comparison tables, and results text must reproduce exactly; variable
SVG/PDF timestamps are excluded from bitwise comparison. The finalizer records
its evidence in data/main/analysis-B-complete.json. No extra API calls are
made by analysis, plotting, tests, or reproduction.
