# Study 2 audit implementation

Study 2 was motivated by the requirement-level self-assessment result observed
in Study 1. The local protocol is frozen separately before follow-up collection.
Study 1 paths, outcomes, raw records and hashes remain unchanged.

From the repository root, with the existing Python environment:

```powershell
.venv/Scripts/python -m unittest discover -s study_2_audit/tests -v
.venv/Scripts/python -m harness.audit_runner
.venv/Scripts/python -m harness.audit_study prepare
.venv/Scripts/python -m harness.audit_study verify-preservation
.venv/Scripts/python -m harness.audit_study verify-study1
.venv/Scripts/python -m harness.audit_study freeze
.venv/Scripts/python -m harness.audit_study verify
```

Preparation is idempotent before freeze and never overwrites differing artifacts.
Freeze is one-time and binds inputs, inventory, schedule, prompts, settings,
parsers, reused dependencies, analysis and rubric. After freeze, use `verify`;
do not repeat preparation or freezing. The implementation's default runner is a
zero-credit synthetic check. No live requests are sent during installation.

To explicitly start or resume collection after reviewing the frozen protocol:

```powershell
.venv/Scripts/python -m harness.audit_runner --live
.venv/Scripts/python -m analysis.audit_analysis --figures
```

Credentials load from the existing ignored .env using the existing transport.
`--limit N` supports operational batching in fixed schedule order; it must not
be used for effect-dependent stopping. Terminal results are never replaced.
Requests lacking outcomes block resends pending account reconciliation.

The inventory contains all 96 trajectories and explicit exclusion reasons.
Primary audits cover all eligible final CD/SD artifacts (fresh, evidence and
confidence). C/S lacks prompted builder claims and is inventoried for future
audits. A public input allowlist excludes metadata, hidden selectors/outcomes,
reference solutions and builder checklists. Truth joins only in scoring.

JSON null / CSV NA preserve undefined denominators. Matched comparisons pair
artifacts before averaging within tasks and bootstrap tasks 10,000 times.
Analysis writes primary and sensitivity tables, coverage/failure counts and
per-task differences. Partial results are labeled. No figures are fabricated
when there are no audit outcomes. Plotting uses analysis/requirements.txt.

Evidence review uses the frozen [rubric](evidence_rubric.md) and analysis queue.
Copy completed reviews to reviews/evidence_reviews.csv with the queue's columns;
keep exact comments, reviewer IDs and ISO timestamps. Access public bundles
through the blinded review export, not the truth-bearing inputs files.
Correctness remains NA until actual review. Human benchmark review and new model
replication require the later steps in [the roadmap](followup_roadmap.md).

Private inputs/raw/provider outputs are ignored by Git; the preservation and
freeze manifests retain hashes but do not publish raw responses. Do not commit
them without a separate release review.

The original `python -m harness.freeze` enumerates the entire harness directory
and therefore rejects additive follow-up modules as a membership change.
Its code and original manifest remain unchanged. Use `audit_study verify-study1`
to verify every original frozen hash and setting plus the preservation inventory.
The original command remains available at the preservation tag.

Export public review packets without scores or builder claims:

```powershell
.venv/Scripts/python -m harness.audit_review
```

Share only review_exports/<snapshot>/evidence/ or
review_exports/<snapshot>/benchmark/ as appropriate; keep reviews/ and inputs/
private. Evidence packets use
opaque artifact IDs. No reviewers are contacted by this command.
