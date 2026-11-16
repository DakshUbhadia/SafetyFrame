# SafetyFrame-Eval — Reproducibility & Release Checklist

## Repository

- [ ] README explains research question.
- [ ] exact model IDs listed.
- [ ] prompts included.
- [ ] task-generation/rendering code included.
- [ ] canonical tasks included.
- [ ] C/S mappings included.
- [ ] public tests included.
- [ ] hidden tests included if release is appropriate after submission.
- [ ] scoring code included.
- [ ] analysis code included.
- [ ] figures can be regenerated.
- [ ] no API keys committed.

## Freeze artifacts

- [ ] `preregistration.md`
- [ ] `freeze_manifest.json`
- [ ] final `run_manifest.csv`
- [ ] Git commit hash recorded.

## Raw data

- [ ] raw Turn-1 outputs retained.
- [ ] raw Turn-2 outputs retained.
- [ ] provider errors retained.
- [ ] token/latency metadata retained.
- [ ] no manually edited raw responses.

## Scored data

- [ ] requirement-level pass/fail retained.
- [ ] task-level TCS retained.
- [ ] self-assessment claims retained.
- [ ] code computes derived metrics from raw scores.

## Environment

- [ ] Python version recorded.
- [ ] dependencies pinned or exported.
- [ ] pytest version recorded.
- [ ] OS/runtime notes if relevant.

## Re-run test

On a clean environment:

- [ ] one task can be rendered C/S;
- [ ] reference solution passes;
- [ ] one stored model artifact can be rescored;
- [ ] analysis script regenerates main table;
- [ ] figures regenerate.

## Documentation

- [ ] README distinguishes confirmatory vs exploratory.
- [ ] deviations disclosed.
- [ ] task count matches paper.
- [ ] model names match raw data.
- [ ] no claims exceed design.

## Optional post-sprint packaging

Inspect AI integration is optional only after core results exist.

Do not delay submission for packaging polish.
