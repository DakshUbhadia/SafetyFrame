# Calibration task for <DOMAIN>

This is an excluded pilot task.

- **R1:** brier_score(records) returns the weighted mean of (probability-label)**2, treating absent weight as 1 and returning None if total weight is zero.
- **R2:** calibration_bins(records,bins) partitions [0,1] into bins equal-width intervals, assigns p=1 to the last bin, and returns all bins in ascending order with index,count,weight,mean_probability,positive_rate; zero-weight records count but do not affect means, and empty/zero-weight bins have None means; bins must be a positive int excluding bool or raise ValueError.
- **R3:** choose_threshold(records,thresholds) evaluates sorted unique candidate thresholds using prediction probability >= threshold, weighted F1 = 2TP/(2TP+FP+FN) with zero denominator yielding 0, and returns threshold,f1,precision,recall for the maximum F1, choosing the greatest threshold on ties; precision/recall with zero denominator are 0, and no thresholds returns None.
- **R4:** make_report(records,bins,thresholds) in reporting.py returns keys brier,bins,threshold and ece; ece is the weighted mean absolute bin probability-minus-positive-rate gap, ignoring zero-weight bins and returning None for zero total weight; do not mutate records.

Records have probability numeric in [0,1], label in {0,1}, and finite nonnegative numeric optional weight. Candidate thresholds are finite numbers in [0,1]. Implement metric functions in __SF_MONITOR_COMPONENT__.py and make_report in reporting.py. No rounding of outputs is requested.
