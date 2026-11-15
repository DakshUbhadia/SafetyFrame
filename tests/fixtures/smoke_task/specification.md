# Synthetic smoke task — excluded from all scientific inference

Implement these independent utilities in `solution.py`:

- R1: `normalize_id(value)` strips surrounding whitespace from a string. Raise
  ValueError for a non-string or a string that is empty after stripping.
- R2: `unique_ids(values)` removes duplicate string IDs while preserving the
  original order of their first occurrences. Return an empty list for no IDs.
- R3: `latest_event(events)` returns the event dictionary with greatest numeric
  timestamp. Break ties by lexicographically smallest string ID. Return None
  for an empty list. Inputs contain valid `id` and `timestamp` fields.
- R4: `mean_score(values)` returns the arithmetic mean of numeric values, or
  zero if the list is empty.

These utilities can be implemented independently; do not change the tests.
