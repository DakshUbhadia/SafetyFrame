# SafetyFrame-Eval — Task Authoring Guide

## Goal

Create 16–20 **functionally equivalent, domain-relabeled task pairs** that are:

- clearly benign;
- plausible in capability and safety research;
- neither trivial nor extremely difficult;
- objectively gradable;
- capable of partial success;
- free of obscure “gotcha” requirements.

## 1. Preferred task shape

Keep most tasks small:

- 1–2 editable source files;
- ~50–200 starter-code lines;
- 4–5 scored requirements;
- 2–5 public tests total;
- 2–4 hidden assertions/examples per requirement;
- deterministic behavior;
- no external network dependency;
- no large libraries unless already standard.

One-file tasks are preferred when scientific value is equal.

## 2. Dual-plausibility rule

A good task could naturally support either:

- AI capability evaluation, or
- AI safety/alignment evaluation.

Strong task families:

- evaluation record parsing;
- result aggregation;
- experiment logging;
- score normalization;
- checkpoint comparison;
- run filtering;
- validation;
- monitoring/report generation;
- configuration/state tracking;
- metric calculation.

Avoid artificial domain labels on unrelated utilities.

## 3. Requirement independence

Each task should allow partial credit.

Good:

```text
R1 parse valid records
R2 reject missing IDs
R3 deduplicate by latest timestamp
R4 deterministic ordering
R5 compute summary metric
```

Bad:

```text
R1 implement parser object
R2 use parser object
R3 aggregate parser output
R4 serialize aggregate
R5 report aggregate
```

where one parser failure mechanically destroys all five.

## 4. Requirement clarity

Every hidden test must trace to explicit language in the specification.

Do not test:

- unstated performance expectations;
- undocumented edge cases;
- stylistic preferences;
- exotic boundaries not reasonably implied.

Create a requirement-to-test matrix:

| Requirement | Written specification | Hidden checks |
|---|---|---|
| R1 | exact quoted sentence | H1a, H1b |
| R2 | exact quoted sentence | H2a, H2b, H2c |

## 5. Difficulty target

Use pilot tasks to calibrate archetypes.

Desired measurement headroom on a strong model is approximately:

```text
0.45–0.85 TCS
```

Do not force every task into this exact range.

Avoid benchmark-wide ceiling/floor effects.

## 6. Public tests

Public tests should:

- verify basic intended use;
- provide useful repair feedback;
- not reveal every hidden requirement;
- not contain safety/capability-specific behavioral differences.

Public tests themselves should be rendered equivalently when domain labels appear.

## 7. Hidden tests

Use multiple assertions per requirement where useful.

A requirement passes only when its preregistered core checks pass.

Do not inflate the independent sample size by counting assertions as separate observations.

## 8. Reference solution

Author a reference solution before final acceptance.

It must pass:

- all public tests under C;
- all hidden tests under C;
- all public tests under S;
- all hidden tests under S.

## 9. Canonical task first

Create the task in a domain-neutral canonical form.

Example placeholders:

```text
<DOMAIN>
<RUN_RECORD>
<PRIMARY_SCORE>
<MONITOR_COMPONENT>
```

Then render capability/safety variants programmatically.

Do not independently rewrite the two variants.

## 10. Linguistic balancing

Check:

- prompt token count;
- repository token count;
- number of renamed symbols;
- identifier lengths;
- naturalness.

Avoid safety variants with longer, more awkward identifiers.

Prefer simple terms like:

```text
monitor_result
alignment_score
safety_run
```

over verbose constructions.

## 11. Reverse-map validation

For code:

1. render C;
2. render S;
3. reverse both domain mappings to canonical names;
4. parse/normalize AST where practical;
5. verify equivalence.

For task text:

- compare after reverse mapping;
- only intended domain labels should differ.

## 12. Pilot versus final tasks

Pilot tasks are disposable.

Use them to discover:

- right task length;
- right requirement count;
- repair behavior;
- public-test usefulness.

Never include pilot trajectories in main inference.

## 13. Task acceptance gate

Use `04_TASK_VALIDATION_CHECKLIST.md`.

If a task fails any critical validation item, do not include it simply to increase `n`.

## 14. Suggested build order

Build reusable archetypes first:

1. parser/validation;
2. metric aggregation;
3. configuration/state;
4. monitoring/reporting.

Then create variants by changing the underlying functional problem—not merely renaming the same code repeatedly.

## 15. Authoring time rule

If one task is consuming much more time than peers, simplify or replace it.

The sprint rewards clean measurement, not benchmark cleverness.
