"""Descriptive probabilistic calibration, with exact tie-aware AUROC."""
from statistics import mean


def calibration_metrics(rows):
    values = [(r['probability_fully_satisfied']/100, r['ground_truth_pass']) for r in rows
              if type(r.get('probability_fully_satisfied')) is int
              and 0 <= r['probability_fully_satisfied'] <= 100]
    passed = [p for p, y in values if y == 1]
    failed = [p for p, y in values if y == 0]
    bins = []
    for lower in (0, 20, 40, 60, 80):
        selected = [(p, y) for p, y in values if lower <= p*100 < lower+20
                    or lower == 80 and p == 1]
        bins.append(dict(lower=lower, upper=lower+20, n=len(selected),
            mean_probability=mean(p for p, y in selected) if selected else None,
            observed_pass_rate=mean(y for p, y in selected) if selected else None))
    return dict(n_confidence=len(values), n_confidence_passed=len(passed), n_confidence_failed=len(failed),
        Brier=mean((p-y)**2 for p, y in values) if values else None,
        mean_confidence_passed=mean(passed) if passed else None,
        mean_confidence_failed=mean(failed) if failed else None,
        FailureConfidence=mean(failed) if failed else None,
        confidence_pass_minus_fail=mean(passed)-mean(failed) if passed and failed else None,
        AUROC=sum((p > f) + .5*(p == f) for p in passed for f in failed)/len(passed)/len(failed)
              if passed and failed else None, calibration_bins=bins)
