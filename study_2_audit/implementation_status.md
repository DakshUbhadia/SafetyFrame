# Implementation status

The implementation specification mixes immediate software requirements with
research stages that depend on future model outcomes or real human review.
This change implements the primary audit study and the tools to conduct it.
It does not assert that the entire research program has been conducted.

| Requirement | Implemented evidence |
| --- | --- |
| Preserve Study 1 | Local tag and follow-up branch; manifests/study1_preservation.json; every original frozen file independently checked |
| Inventory before inference | 96 trajectories, 90 eligible, six provider exclusions; all original hidden outcomes linked and final artifact hashes verified |
| Matched primary sample | All 29 eligible CD/SD artifacts, including all-pass artifacts and the recoverable final-format-failure artifact |
| Fresh/evidence/confidence | Exact prompts; 87 randomized audit requests scheduled; no requests sent by setup |
| Hidden-data separation | Public-field allowlist; requirement IDs/text only; hidden outcomes and builder claims join after inference |
| Strict parsers | Whitespace/case normalization; duplicate/missing/unknown IDs; NA confidence; evidence extracted without invented ratings |
| Durable collection | Stateless existing transport, raw/request persistence, three-attempt transient-only retry, pacing, budget reservations, terminal resume, ambiguous-request block |
| Protocol freeze | One-time local freeze of settings, inputs, inventory, schedule, prompts, parsers, analysis, tests and evidence rubric |
| Analysis | FCR, strict/lenient URDR, precision, classification, abstention/missingness, Brier, descriptive AUROC and calibration bins |
| Inference | Matched artifacts averaged within task; 10,000 paired task bootstrap resamples; every task difference retained |
| Sensitivities | Valid-parse-only, missing failure-to-disclose, artifact/task macro and descriptive requirement pooling |
| Reproducibility | Raw records reparsed/rescored before analysis; immutable mismatches reject manual edits; no invented outcomes |
| Figures | Four main figures in PDF/PNG/SVG when corresponding outcomes exist; optional cross-model matrix |
| Human review tooling | Frozen evidence rubric, blinded public packets, private key, strict rating import; benchmark checklist exported for 16 tasks |
| Later studies | Critic/cross-model prompt and model-grid support; replication/repeated-generation/review dependencies explicitly recorded in followup_roadmap.md |

Validation: 21 follow-up tests, 74 existing harness/benchmark tests and 38
existing analysis tests passed. The new integration tests use synthetic outcomes
to exercise persistence, analysis and figures without provider calls.

Study 1 limitations: the preserved source has a Sprint 10 manuscript; a final
PDF was not available to preserve. The legacy freeze verifier enumerates all
harness files and rejects additive Study 2 modules. Its original code remains
unchanged; `python -m harness.audit_study verify-study1` checks the 570 originally
frozen files, original settings and preservation hashes. The original verifier
can also be run against the preservation tag's source.

Collection state is authoritative in analysis/summary.json. Human evidence and
benchmark review, cross-model builder pilots/main replication, repeated builder
generations, larger/agentic benchmarks and a follow-up results paper are pending
their documented prerequisites. No paid inference, reviewer outreach or
publication was performed as part of implementing the software.
