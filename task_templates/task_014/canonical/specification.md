# Missing-aware time-series resampling for <DOMAIN>

Implement the APIs below for __SF_RUN_RECORD__ processing. This is benign, offline evaluation infrastructure.
Use Python standard library only. Both source files are editable. Public tests are illustrative.
Functions are scored separately; shared helpers are optional. No input may be mutated.

- **R1:** bucket_samples(samples,width,origin) requires positive finite width or raises ValueError; group (time,value) pairs under integer floor((time-origin)/width), preserving input value order within each bucket and returning keys in ascending order.
- **R2:** reduce_buckets(buckets) returns each bucket's mean excluding None, or None when no numeric values remain; preserve the input key set.
- **R3:** fill_forward(values,max_missing) requires a nonnegative integer limit excluding booleans or raises ValueError; fill at most max_missing consecutive None entries after a known value, leaving leading missing values and longer-gap remainder as None; each observed value resets the gap.
- **R4:** moving_average(values,window) requires a positive integer window excluding booleans or raises ValueError; at each index average non-None values among the most recent window positions including current, returning None when all are missing.
- **R5:** series_report(samples,width,origin,start,end,max_missing,window) in reporting.py reduces buckets, builds values for every integer bucket start through end inclusive using None for absent buckets, forward-fills then smooths; return buckets,values,filled,smoothed and empty lists when start>end.

Times, origin, and numeric values are finite real numbers. Bucket boundaries are left-closed/right-open. Samples may be unsorted and repeated. start/end are integer bucket indices, not timestamps. All output arrays use chronological bucket order.
