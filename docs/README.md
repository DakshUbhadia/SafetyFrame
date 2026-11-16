# SafetyFrame-Eval Documentation

The repository root contains final findings and core provenance. Detailed
methodology and historical sprint material are organized here.

## Methods

- [Experiment protocol](methods/02_EXPERIMENT_PROTOCOL.md)
- [Prompt protocol](methods/05_PROMPT_PROTOCOL.md)
- [Data dictionary](methods/08_DATA_DICTIONARY.md)
- [Scoring and analysis plan](methods/09_SCORING_ANALYSIS_PLAN.md)
- [Self-assessment rubric](methods/10_SELF_ASSESSMENT_RUBRIC.md)
- [Harness](methods/HARNESS.md)
- [Task rendering and equivalence](methods/RENDERING.md)
- [Full research specification](methods/SPECIFICATION_v4.md)
- [Final analysis reproduction](methods/FINAL_ANALYSIS.md)
- [Report evidence and source checks](methods/RESEARCH_REPORT.md)

## Reproduce and verify

On this reorganized checkout:

```powershell
python scripts/verify_presentation.py
```

This checks every original frozen scientific hash at its preserved location,
the Study 2 protocol, reviewed analysis, report tables/prompts/narrative, and
current navigation. It makes no model calls. Relocations and exact-byte snapshots
are recorded in [the cleanup manifest](../presentation/documentation_cleanup.json).
The original freeze manifests retain their original paths and hashes; no
relocation was backdated into them.

The frozen harness expects its original root paths. To reproduce Study 1 with
the original commands, use a separate checkout of the preservation tag:

```powershell
git clone --branch safetyframe-sprint-2026-final https://github.com/DakshUbhadia/SafetyFrame.git SafetyFrame-study1
cd SafetyFrame-study1
python -m pip install -r requirements.txt -r analysis/requirements.txt
python -m analysis.primary
python scripts/verify_report.py
```

Match the original Python runtime documented in the freeze. The original
verifier checks the runtime and committed file membership. Raw provider evidence
is withheld from Git and is needed only for the separate local evidence audit.
These numerical reproduction commands do not collect new outcomes.

Frozen Study 2 collection uses `followup/self-assessment-audit`, whose original
paths, protocol and preservation hashes remain unchanged. Its implementation is
also present on main, but the strict collector intentionally rejects main's
post-freeze documentation changes. No follow-up outcomes enter Study 1.

## Historical material and preserved sources

[The archive](archive/README.md) contains setup, pilot calibration, planning,
runbooks, authoring guides, and starter templates. Historical statuses describe
their original sprint, not the current collection state. Readable moved copies
have relative links updated; content was not rewritten to erase negative results.

Exact pre-cleanup bytes are retained as plain-text source snapshots under
`archive/source_snapshots/`, with binary Git attributes to prevent newline
normalization. These are evidence, rather than additional navigable documentation.
Old preregistration links are preserved as originally written; use the methods
index above or the original-path map in the cleanup manifest to locate moved files.

## Results

- [Final results](../FINAL_RESULTS.md)
- [Report and paper status](../report/README.md)
- [Model A provenance](../MODEL_A.md)
- [Model B provenance](../MODEL_B.md)
- [Exact final analysis](../report/final_analysis/results.md)
