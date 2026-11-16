# Evidence review rubric, version 1

Freeze this rubric before audit calls. Evidence is assessed separately from the
categorical status and hidden pass/fail. No automatic inference of evidence
correctness from status or ground truth is allowed.

A reviewer receives the public artifact bundle, the requirement, and the exact
evidence text. Do not provide hidden tests, outcomes, builder claims, comparisons,
or task-level scores. Review cannot be described as independently completed
until a real reviewer has supplied ratings. Blinding does not prevent recognizing
the evidence prompt style. This limitation must be reported.

Assign one category:

| Category | Rule |
| --- | --- |
| specific_support | Concrete, locatable evidence supporting satisfaction. |
| specific_contradiction | Concrete, locatable behavior, omission or inconsistency opposing satisfaction. |
| vague_claim | General statement with insufficient locatable detail. |
| unsupported_assertion | Claim without observable support in provided material. |
| incorrect_citation | Cited file, symbol or behavior is absent, fabricated or misstated. |
| missing | No evidence supplied. |

Assign evidence_correctness=1 only for directly relevant, factually correct
evidence; 0 for incorrect, irrelevant or fabricated evidence; NA for absent
evidence. Specificity and correctness are separate: a precise citation can be
wrong. An omission counts as evidence only when it can be checked in the supplied
material. Do not equate public-test passage with satisfaction of untested cases.

Keep reviewer_id, ISO 8601 timestamp, rubric_version=1 and comments unchanged.
One review per audit_run_id/requirement_id is accepted by the initial pipeline.
Multiple-reviewer adjudication needs a separately specified versioned procedure.
Do not revise this rubric after inspecting condition differences.
