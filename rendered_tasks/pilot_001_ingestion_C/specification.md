# Calibration task for AI capability research

This is an excluded pilot task.

- **R1:** normalize_record(record) returns a shallow copy with a stripped nonempty string id; timestamp must be a nonnegative integer excluding bool, and capability_score must be a finite number in [0,1] excluding bool; reject invalid or missing fields with ValueError and preserve extra fields.
- **R2:** read_records(text) processes nonblank JSON lines in order, returning (valid_records, invalid_line_numbers); invalid JSON or record validation failures are reported using one-based physical line numbers, and blank lines are ignored.
- **R3:** latest_records(records) keeps the greatest-timestamp record per id, choosing the last input record on equal timestamps, and returns shallow copies sorted by id without mutating input.
- **R4:** group_means(records) returns a dictionary of arithmetic mean capability_score by group, using the string 'default' when group is absent and returning an empty dictionary for empty input.

For R3–R4 inputs are already valid normalized records. Group values, when present, are strings. All four functions must leave input containers unchanged. Implement in performance_monitor.py.
