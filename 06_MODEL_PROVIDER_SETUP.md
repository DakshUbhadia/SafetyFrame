# SafetyFrame-Eval — Model & Provider Setup

## 1. Goal

Choose:

- **Model A:** strongest suitable model for full factorial.
- **Model B:** meaningfully different strong family for C/S generalization.

Do not choose models because pilot framing effects look favorable.

## 2. Adaption first

Apart provides Adaption credits + Builder access.

At setup:

1. activate account;
2. create API key;
3. list account-authorized hosted models;
4. save the exact model list;
5. ask sprint Discord/Adaption support:
   - which models are enabled;
   - rate limits;
   - how hosted inference consumes sprint credits;
   - whether model IDs can silently route/version.

Record answers in this file.

### Adaption access record

- Account activated: `[yes/no]`
- API key created: `[yes/no]`
- Available models saved at: `[path]`
- Credit behavior confirmed: `[FILL]`
- Rate limits: `[FILL]`

## 3. Model-selection criteria

Prefer:

- strong coding ability;
- stable API;
- enough context for task+files+tests;
- accessible exact model ID;
- distinct family/provider for Model B.

Avoid adding a third model before the default design is complete.

## 4. Exact model record

### Model A

- Provider: `[FILL]`
- Exact model ID: `[FILL]`
- Context window: `[FILL if known]`
- Temperature support: `[FILL]`
- Seed support: `[FILL]`
- Tool use disabled/enabled: `[FILL]`
- Max output chosen: `[FILL]`

### Model B

- Provider: `[FILL]`
- Exact model ID: `[FILL]`
- Context window: `[FILL]`
- Temperature support: `[FILL]`
- Seed support: `[FILL]`
- Tool use disabled/enabled: `[FILL]`
- Max output chosen: `[FILL]`

## 5. Generation settings

Preferred:

- temperature `0` when supported;
- otherwise lowest deterministic/low-variance setting that is provider-normal;
- fixed max output token limit;
- no hidden tool calls;
- no web browsing by the experimental model;
- no shared memory/session state.

Record every provider-specific difference.

## 6. Preflight test

Before pilot:

- [ ] one trivial prompt succeeds;
- [ ] full-file output can be parsed;
- [ ] two-turn conversation works;
- [ ] response metadata is logged;
- [ ] exact model ID is logged;
- [ ] token counts available or gracefully missing;
- [ ] timeout/retry code tested;
- [ ] raw outputs persisted.

## 7. Kaggle T4

Use for:

- optional calibration model;
- pytest;
- data analysis;
- AST/reverse-map checks;
- plots.

Do not make local-model setup a blocker.

## 8. Secrets

Never commit:

- API keys;
- bearer tokens;
- provider credentials.

Use environment variables and `.env` excluded by `.gitignore`.

## 9. Provider drift

Because providers may change routing/versioning:

- use randomized blocks;
- record timestamps;
- record model version metadata when exposed;
- run matched conditions close together.

If a provider announces a model update mid-study, note it in the deviation log and inspect block timestamps.
