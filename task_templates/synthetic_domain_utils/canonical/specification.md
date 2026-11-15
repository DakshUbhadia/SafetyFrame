# Evaluation run utilities for <DOMAIN>

Implement the four independent utilities in `__SF_MONITOR_COMPONENT__.py`.
This is a synthetic infrastructure example, excluded from scientific inference.

## Requirements

- **R1:** normalize___SF_RUN_RECORD___id(value) strips whitespace from a string ID and raises ValueError for a non-string or an empty stripped ID.
- **R2:** unique___SF_RUN_RECORD__s(records) keeps the first record for each ID, preserving first-occurrence order, returning an empty list for empty input and leaving inputs unchanged.
- **R3:** latest___SF_RUN_RECORD__(records) returns the record with greatest timestamp, breaks ties by lexicographically smallest ID, and returns None for empty input.
- **R4:** mean___SF_PRIMARY_SCORE__(records) computes the arithmetic mean of the __SF_PRIMARY_SCORE__ field and returns zero for empty input.

For R2–R4, inputs are lists of valid record dictionaries with a nonempty string
`id`, numeric `timestamp`, and numeric `__SF_PRIMARY_SCORE__` field. These
functions do not need to call the ID normalizer or each other. Return record
dictionaries with their field names unchanged. No network or external packages are needed.
