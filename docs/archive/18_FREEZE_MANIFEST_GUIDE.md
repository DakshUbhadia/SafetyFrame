# SafetyFrame-Eval — Freeze Manifest Guide

Create a machine-readable `freeze_manifest.json` immediately before main runs.

Recommended structure:

```json
{
  "freeze_timestamp_utc": "...",
  "git_commit": "...",
  "task_count": 18,
  "task_ids": ["task_001", "..."],
  "models": {
    "A": {"provider": "...", "model_id": "..."},
    "B": {"provider": "...", "model_id": "..."}
  },
  "files": {
    "prompts/capability.txt": "sha256:...",
    "prompts/safety.txt": "sha256:...",
    "prompts/requirement_accounting.txt": "sha256:..."
  },
  "tasks": {
    "task_001": {
      "canonical_hash": "sha256:...",
      "capability_render_hash": "sha256:...",
      "safety_render_hash": "sha256:...",
      "requirements_hash": "sha256:...",
      "public_tests_hash": "sha256:...",
      "hidden_tests_hash": "sha256:..."
    }
  },
  "analysis": {
    "primary_contrasts": [
      "BaselineSafetyGap_A",
      "DisclosureFramingInteraction_A",
      "BaselineSafetyGap_B"
    ]
  }
}
```

## Hashing rule

Use SHA-256 on normalized file bytes.

Do not modify frozen files without:
- new commit;
- deviation entry;
- rerun decision.

## What does not need hashing

- notes;
- paper drafts;
- non-executable reading notes.

## Why this matters

The manifest demonstrates that task definitions, treatment text, tests, and scoring were fixed before main-result inspection.
