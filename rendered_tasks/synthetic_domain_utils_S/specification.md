# Evaluation run utilities for AI safety research

Implement the four independent utilities in `robustness_monitor.py`.
This is a synthetic infrastructure example, excluded from scientific inference.

## Requirements

- **R1:** normalize_safety_eval_run_id(value) strips whitespace from a string ID and raises ValueError for a non-string or an empty stripped ID.
- **R2:** unique_safety_eval_runs(records) keeps the first record for each ID, preserving first-occurrence order, returning an empty list for empty input and leaving inputs unchanged.
- **R3:** latest_safety_eval_run(records) returns the record with greatest timestamp, breaks ties by lexicographically smallest ID, and returns None for empty input.
- **R4:** mean_alignment_score(records) computes the arithmetic mean of the alignment_score field and returns zero for empty input.

For R2–R4, inputs are lists of valid record dictionaries with a nonempty string
`id`, numeric `timestamp`, and numeric `alignment_score` field. These
functions do not need to call the ID normalizer or each other. Return record
dictionaries with their field names unchanged. No network or external packages are needed.
