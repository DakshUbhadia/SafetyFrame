# SafetyFrame-Eval — Protocol Deviations & Incidents

> Append entries chronologically. Never delete an entry after adding it.

## Deviation template

### DEV-[NNN]

- Timestamp:
- Research phase:
- Affected task(s):
- Affected model(s):
- Affected condition(s):
- Category:
  - [ ] task bug
  - [ ] hidden-test bug
  - [ ] public-test bug
  - [ ] prompt bug
  - [ ] parser bug
  - [ ] provider/API incident
  - [ ] model/version change
  - [ ] resource/credit constraint
  - [ ] analysis bug
  - [ ] other
- Description:
- How discovered:
- Did discovery occur before aggregate results were inspected? `[yes/no]`
- Scientific impact:
- Corrective action:
- Reruns required:
- Reruns performed:
- Does preregistration need amendment?:
- Git commit before fix:
- Git commit after fix:
- Report disclosure required? `[yes/no]`

---

## Incident-handling principles

### Frozen task bug

If a hidden test is wrong:
- fix the bug;
- rerun every affected matched condition for that task;
- do not keep only favorable old/new values.

### Parser bug

If parser behavior incorrectly rejects valid model output:
- define fix;
- apply uniformly to all already-collected raw outputs if possible;
- rerun scoring, not model generation, when raw responses are sufficient.

### Provider model change

If exact model/version changes mid-study:
- record timestamps;
- do not silently combine incompatible versions;
- consider reporting blocks separately if material.

### Credit/resource shortfall

Use the predeclared staged design rather than selectively dropping inconvenient conditions.

### Analysis correction

Preserve old output, commit correction, and describe material changes in the report.
