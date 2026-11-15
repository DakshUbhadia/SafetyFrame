# Sprint 3 — Canonical task rendering and equivalence

## Verified result

One canonical YAML-backed task produces C/S bundles accepted by the Sprint 2
harness. Both variants reverse-map to canonical text and normalized Python ASTs.
Both reference solutions pass 3 public tests and 8 hidden checks across 4 requirements.
The example is infrastructure evidence only: **exclude it from pilots and final
inference**. No API requests or Adaption credits are needed.

## Reproduce

Run from the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip --disable-pip-version-check --isolated install --no-cache-dir --progress-bar off -r requirements.txt

.\.venv\Scripts\python.exe -m harness.render_variants `
  --template task_templates/synthetic_domain_utils

.\.venv\Scripts\python.exe -m harness.audit_equivalence `
  --template task_templates/synthetic_domain_utils `
  --capability rendered_tasks/synthetic_domain_utils_C `
  --safety rendered_tasks/synthetic_domain_utils_S `
  --validate-reference --trusted-example

.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Expected: equivalence true, automated balance diagnostics true, reference passed.
Reports default to unique files in `data/audits/`. `--report <new-file.json>` sets
an explicit path; existing reports are preserved. See the checked
[audit evidence](data/audits/sprint3-final.json).

Omit `--validate-reference --trusted-example` for a static audit. Static success
leaves `reference_pass` null and `sprint3_exit_criteria_met` false.

## Canonical source contract

```text
task_templates/<task_id>/
  task_metadata.json
  mapping.yaml
  requirements.yaml
  authoring_notes.md                 # optional, never included in model input
  canonical/
    specification.md
    <starter files>
  reference_solution/
    <complete starter file set with implementation>
  public_tests/test_*.py
  hidden_tests/test_*.py
```

Metadata declares the ID, kind (`synthetic`, `pilot`, `final`), family, editable
files, requirement total, public test count, and both domain-plausibility notes.
`kind` controls the harness phase; auxiliary authoring flags do not override it.
Keep them consistent. Canonical YAML remains the authoring source; the renderer
exports `task.json` for execution.

Each of 4–5 requirements has a stable ID, exact supporting specification sentence,
`all_core_checks_pass`, and explicit unittest method selectors. Every hidden check
maps to one requirement. Suites currently use flat `test_*.py` modules with ordinary
test methods. Inherited, generated, parameterized, or async tests need additional
validation support. Assertions do not become independent research observations.

See the [mapping](task_templates/synthetic_domain_utils/mapping.yaml),
[requirements](task_templates/synthetic_domain_utils/requirements.yaml),
[metadata](task_templates/synthetic_domain_utils/task_metadata.json), and
[author review](task_templates/synthetic_domain_utils/authoring_notes.md).

## Mapping and publishing rules

- Use declared placeholders such as `<DOMAIN>` in prose and reserved identifiers
  such as `__SF_MONITOR_COMPONENT__` in portable filenames or code.
- Both roles define the same mapping keys. Placeholders and labels must be unique
  and non-overlapping to permit unambiguous reversal.
- Code labels must be ASCII Python identifiers, not keywords. Domain prose must
  be a nonempty single-line string. Review naturalness in both research domains.
- Do not preinsert rendered labels into canonical source; the reverse map could
  otherwise change a literal outside the intended treatment.
- Reject undeclared/unresolved tokens, path or case collisions, links/reparse
  points, non-UTF-8 source, duplicate YAML keys, object tags, and aliases.
- Substitutions happen in one pass. Python must parse after rendering. Canonical
  AST checks map placeholders to neutral identifiers without executing code.
- Sources and output trees must be separate. Line endings normalize to LF;
  original source bytes are unchanged and fingerprinted in provenance.

Both variants are validated in staging before publishing. Identical reruns reuse
identical output. Existing changed renderings are never overwritten: choose a
new `--output` root for revised sources and preserve earlier evidence.

Bundles contain starter source, specification, public/hidden tests, references,
runtime metadata, and provenance hashes. CD uses C's bundle; SD uses S's.
**Never send an entire rendered bundle to a model:** it contains private validation
material. The prompt builder allows only specification, starter files, and public
tests. Tests verify exclusion of hidden, reference, and author-only content from
all C/S/CD/SD prompts.

## Audit coverage and limits

The audit checks expected file sets and metadata/provenance, reverse-mapped text
including comments, and normalized ASTs against both canonical source and the
other rendering. This covers control flow, constants, data types, structure, and
public/hidden test logic. It checks requirement counts, selectors, editable files,
and public test counts. Prompt comparisons retain identical system messages and
payload bodies after removing only the fixed framing package and reversing labels.
Baseline and disclosure payloads are checked separately.

An identical accidental logic change in C and S fails the canonical check. A
one-sided comment fails text matching even when its AST is equal. Extra files,
changed constants, or altered tests also fail. Passing matched reference tests
and AST equality support computational equivalence under relabeling; they do not
prove complete test coverage or isolate every linguistic aspect of the treatment.

Reports include character counts, UTF-8 bytes, a regex word/punctuation token
proxy, Python identifier occurrence/unique counts, mean lengths, and label lengths.
**The proxy is not a model tokenizer.** Exact Qwen/DeepSeek token counts remain
null. Validate actual provider usage during pilots and add a verified tokenizer
only if exact pre-call counts become necessary.

Initial diagnostic thresholds are 10% relative text-proxy difference and 20%
identifier mean-length difference, with equal identifier counts. These are
authoring diagnostics, not preregistered statistical outcomes. The example's
baseline prompt proxy difference is about 0.51%, identifier occurrences are equal,
and mean identifier length differs by about 1.03%. Naturalness and domain plausibility
still require author review; the example notes record that review and explain
requirement independence and hidden-test scope.

## Reference execution

General reference validation defaults to the resource-limited Docker executor.
Use a working Linux Docker engine and an explicitly installed test image for new
tasks. Live Docker integration was not verified in Sprint 2, but Sprint 4 has now
exercised reference and model scoring in real containers; see [PILOTS.md](PILOTS.md).

`--trusted-example` allows local execution only for complete reference-source and
test-tree hashes recorded in `harness/trusted_references.json`. A path or metadata
flag cannot approve arbitrary code; even changed comments invalidate approval.
The registry is reviewed source-control material. Never add model-produced code
to bypass Docker. No unrestricted local fallback was introduced.

Next, build fresh excluded pilot tasks in Sprint 4. Do not reuse this example,
expand the final benchmark prematurely, or mark the study frozen.
