# SafetyFrame-Eval — Operational Runbook

This is the document to keep open while executing.

## Phase 0 — setup

- [ ] activate Adaption;
- [ ] identify Model A/B;
- [ ] create repo;
- [ ] implement raw-response logging;
- [ ] implement full-file parser;
- [ ] implement clean-workspace reset;
- [ ] implement public-test runner;
- [ ] implement hidden-test scorer;
- [ ] implement Turn-1 snapshot;
- [ ] implement Turn-2 repair;
- [ ] implement randomized block manifest.

## Phase 1 — pilot

Create 4–6 throwaway tasks.

Run enough capability-framed pilot trajectories to judge:

- ceiling/floor;
- output format reliability;
- public-feedback usefulness;
- repair saturation;
- token limits.

### Pilot decision

If most TCS > 0.90:
- increase requirement difficulty or independence;
- reduce public-test coverage;
- add one moderate explicit edge requirement.

If most TCS < 0.35:
- simplify tasks;
- reduce multi-file dependencies;
- make requirements clearer;
- reduce complex edge conditions.

If format failures > ~10%:
- simplify file-output schema before final freeze.

If Turn 2 makes almost everything perfect:
- make public tests less exhaustive while still useful.

## Phase 2 — final task construction

Build 16 validated tasks first.

Then:
- add 17–18 if clean;
- add 19–20 only if time/quality allow.

For each task:
1. canonical specification;
2. requirements;
3. public tests;
4. hidden tests;
5. reference solution;
6. domain mapping;
7. C/S render;
8. equivalence audit;
9. validation checklist.

## Phase 3 — freeze

Complete:
- `01_PREREGISTRATION_TEMPLATE.md`;
- `freeze_manifest.json`;
- run manifest.

Do not start final calls before freeze.

## Phase 4 — Model A

For each randomized block:

1. verify block/task hashes;
2. run first randomized condition;
3. complete Turn 1;
4. score hidden offline;
5. send public feedback;
6. complete Turn 2;
7. score final;
8. save checklist if CD/SD;
9. repeat for remaining conditions;
10. mark block complete.

Do not inspect aggregate C/S means after every task. Complete the planned set unless a genuine infrastructure problem occurs.

## Phase 5 — first analysis checkpoint

After Model A complete:

Generate immediately:

- condition mean TCS;
- task-level C−S plot;
- BaselineSafetyGap_A + CI;
- CD−C;
- SD−S;
- DisclosureFramingInteraction_A + CI;
- self-assessment confusion table;
- FCR/URDR;
- RepairGain summary.

Write 5–10 bullet findings before starting optional work.

## Phase 6 — Model B

Run C/S blocks only.

Then compute:
- BaselineSafetyGap_B;
- task-level C−S plot;
- compare direction/heterogeneity descriptively with Model A.

## Phase 7 — paper-first rule

Before any optional extension:
- create Methods draft;
- create Results draft;
- insert Figures 1–4;
- write limitations bullet list.

Only then decide on optional Model-B CD/SD or other robustness.

## Incident handling

### A test bug discovered after some runs

Stop affected task.

Determine whether:
- only one condition affected;
- all renderings affected;
- scoring only affected.

Fix, log deviation, and rerun all affected matched conditions for the task.

### Prompt bug

If treatment text was wrong:
- stop study;
- determine affected blocks;
- fix;
- rerun all matched conditions in affected blocks;
- log deviation.

### Provider outage

Pause. Do not switch model IDs casually.

Resume when stable or formally amend preregistration.

### Credit pressure

Use default staged design:
- finish Model A full factorial;
- Model B C/S;
- skip extensions.

## End-of-day backup

At minimum back up:

- raw responses;
- run manifest;
- scores;
- frozen tasks;
- analysis outputs;
- Git commit.

Do not rely on notebook runtime persistence alone.
