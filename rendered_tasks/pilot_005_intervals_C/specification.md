# Calibration task for AI capability research

This is an excluded pilot task.

- **R1:** parse_duration(value) returns nonnegative integer milliseconds: an int excluding bool is already milliseconds; a stripped lowercase string must be digits with optional one-to-three decimal places followed by ms,s,m, converted exactly using 1,1000,60000 respectively; fractional-millisecond results or other forms raise ValueError.
- **R2:** coalesce_intervals(intervals) validates integer start/end pairs with end >= start, discards empty intervals, and returns sorted tuples merging overlapping or touching half-open intervals without mutation; invalid pairs raise ValueError.
- **R3:** subtract_intervals(inclusions,exclusions) normalizes both interval collections, subtracts the union of exclusions from the union of inclusions using half-open semantics, and returns sorted nonempty tuples without mutation.
- **R4:** coverage_by_group(records,windows) first keeps the last input record per id, then unions intervals within each group and intersects them with the union of windows, returning a group-name-sorted dictionary of covered integer milliseconds including groups with zero coverage.
- **R5:** make_summary(records,windows,limit) in reporting.py returns total_ms as the sum of group coverage, active_groups as the number with positive coverage, and groups as a list of group,coverage_ms dictionaries sorted by coverage descending then group ascending and truncated to limit; totals use all groups before truncation; limit must be a nonnegative int excluding bool or raise ValueError.

Records contain string id and group plus nonnegative integer start/end with end >= start. Intervals may use negative integer endpoints but bool endpoints are invalid. Durations may not contain signs, exponents, leading-dot fractions, internal spaces, or uppercase units. Empty collections are valid. Implement interval functions in performance_monitor.py and make_summary in reporting.py.
