# Calibration task for AI capability research

This is an excluded pilot task.

- **R1:** deduplicate(records) keeps the greatest-timestamp record per id, choosing the last input record on ties, and returns records sorted by id without mutating inputs.
- **R2:** window_records(records,start,end) retains records with start <= timestamp < end in input order, returns empty for start == end, and raises ValueError for start > end.
- **R3:** weighted_rate(records) computes sum(weight*success)/sum(weight), defaulting absent weight to 1 and returning None when the total weight is zero.
- **R4:** group_summary(records,start,end) deduplicates globally before applying the time window, then returns groups sorted by name as dictionaries with group, count, and rate; count includes zero-weight records, and absent group means 'default'.
- **R5:** merge_metadata(base,patch) recursively merges dictionaries, deletes a key when its patch value is None, replaces lists and other values, and returns independent deep copies without mutating either input.

Inputs are valid dictionaries: id is a string, timestamp is numeric, success is bool, weight is finite nonnegative numeric, and group is a string. Utility functions may assume those types. An absent key patched with None stays absent. Empty summaries return []. Implement in performance_monitor.py.
