# SafetyFrame-Eval — Final Task Validation Checklist

Complete one copy per final task.

## Task metadata

- Task ID: `[FILL]`
- Family: `[FILL]`
- Authoring status: `[draft / validated / frozen]`
- Reviewer: `[self / other if available]`

## A. Scientific validity — REQUIRED

- [ ] Task is clearly benign.
- [ ] Task plausibly belongs in both capability and safety research.
- [ ] Capability and safety variants solve the same computational problem.
- [ ] Domain framing is the intended treatment; no one-sided warning/threat language exists.
- [ ] There are 4–5 scored requirements.
- [ ] Requirements permit partial success.
- [ ] Failure of one requirement does not mechanically force most others to fail.
- [ ] Every hidden requirement is explicitly supported by task wording.
- [ ] No hidden test depends on an obscure unstated corner case.

## B. Reference solution — REQUIRED

- [ ] Reference solution exists.
- [ ] Passes all C public tests.
- [ ] Passes all C hidden tests.
- [ ] Passes all S public tests.
- [ ] Passes all S hidden tests.
- [ ] Produces functionally equivalent outputs across renderings after reverse mapping.

## C. Renderer validity — REQUIRED

- [ ] C/S variants generated from the same canonical source.
- [ ] Same file count.
- [ ] Same logic/control flow after reverse mapping.
- [ ] Same constants/thresholds.
- [ ] Same number of requirements.
- [ ] Same public-test logic.
- [ ] Same hidden-test logic.
- [ ] Reverse-mapped normalized ASTs match where applicable.
- [ ] Only intended domain labels/comments/docs differ.

## D. Linguistic balance — REQUIRED

- [ ] Prompt lengths are reasonably similar.
- [ ] Repository lengths are reasonably similar.
- [ ] Identifier counts are the same.
- [ ] Identifier lengths are not systematically harder in safety variant.
- [ ] Safety terminology sounds natural.
- [ ] Capability terminology sounds natural.

## E. Test quality — REQUIRED

For each requirement:

### R1
- [ ] exact supporting specification sentence identified;
- [ ] at least one strong hidden check;
- [ ] no unrelated behavior in the score.

### R2
- [ ] exact supporting specification sentence identified;
- [ ] at least one strong hidden check;
- [ ] no unrelated behavior in the score.

### R3
- [ ] exact supporting specification sentence identified;
- [ ] at least one strong hidden check;
- [ ] no unrelated behavior in the score.

### R4
- [ ] exact supporting specification sentence identified;
- [ ] at least one strong hidden check;
- [ ] no unrelated behavior in the score.

### R5 (if used)
- [ ] exact supporting specification sentence identified;
- [ ] at least one strong hidden check;
- [ ] no unrelated behavior in the score.

## F. Difficulty / structure

- [ ] Public tests do not reveal every hidden requirement.
- [ ] Task is not intentionally made adversarial to create failures.
- [ ] Expected model output fits token budget.
- [ ] Task can be executed deterministically offline.
- [ ] No internet access needed.
- [ ] No hidden dependency on local machine state.

## G. Freeze decision

- [ ] ACCEPT into final benchmark.
- [ ] REJECT / revise.

Reason if rejected/revised:

`[FILL]`

Freeze hash:

`[FILL AFTER FREEZE]`
