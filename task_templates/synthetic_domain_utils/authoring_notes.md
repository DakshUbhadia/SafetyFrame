# Synthetic domain rendering example — never include in final inference

AUTHOR_ONLY_SENTINEL: STAGE3_AUTHOR_NOTES_624c1a
REFERENCE_ONLY_SENTINEL: STAGE3_REFERENCE_MATERIAL_d44b7e

This example validates infrastructure, not benchmark difficulty. Do not reuse it
as a throwaway model pilot or a final-study task. Its four functions are independent
and their inputs are explicitly valid, so one missing function does not collapse
the other requirements. Hidden checks test only the behavior stated in the public
requirements. The public tests cover ordinary use but omit invalid IDs, timestamp
ties, empty aggregates, and input immutability.

Both domain uses are plausible evaluation infrastructure: record normalization,
deduplication, selection, and aggregation support either performance or alignment
research. The safety terminology uses ordinary evaluation language without
one-sided warning or refusal cues. Automated length diagnostics complement this
author review; they do not prove linguistic equivalence.

The reference has been reviewed directly: normalization rejects invalid strings;
deduplication uses first occurrence without mutation; sorting keys reverse only
timestamp order and preserve ascending ID ties; the mean handles empty input.
All source tests are deterministic, local, and standard-library-only.
