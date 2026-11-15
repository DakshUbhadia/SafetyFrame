# Consecutive-breach alert state machine for AI capability research

Implement the APIs below for capability_run processing. This is benign, offline evaluation infrastructure.
Use Python standard library only. Both source files are editable. Public tests are illustrative.
Functions are scored separately; shared helpers are optional. No input may be mutated.

- **R1:** classify(values,low,high) returns low,ok,high labels using strict comparisons (<low or >high); None yields missing, boundary values are ok, and low>high raises ValueError.
- **R2:** breach_streaks(labels) returns consecutive identical low/high streak lengths at each position; ok or missing resets to zero and switching breach side starts at one.
- **R3:** alert_events(labels,min_streak,cooldown) requires positive integer min_streak and nonnegative integer cooldown excluding booleans or raises ValueError; emit index,side events when a low/high streak first reaches min_streak, and suppress candidates with index-last_emitted_index<=cooldown; a suppressed candidate is never delayed.
- **R4:** merge_episodes(indices,max_gap) requires nonnegative integer max_gap excluding booleans or raises ValueError; sort and deduplicate integer indices and merge adjacent indices when their difference<=max_gap, returning start,end,count dictionaries.
- **R5:** alert_report(values,low,high,min_streak,cooldown,max_gap) in reporting.py returns labels,streaks,events,episodes,missing, where episodes merge emitted event indices and missing counts None values.

Values are finite numbers or None. Valid labels are low,ok,high,missing. Event indices are zero-based. Episodes count distinct event indices, not the inclusive interval length. Do not use wall-clock time or persistent state.
