"""Pair artifacts first, aggregate their differences per task, resample tasks."""
from collections import defaultdict
import random
from statistics import mean
from .audit_metrics import audit_metrics


def percentile(values, q):
    values = sorted(values)
    position = (len(values)-1)*q
    lower = int(position)
    upper = min(lower+1, len(values)-1)
    return values[lower] + (values[upper]-values[lower])*(position-lower)


def bootstrap(values, seed=2026111702, resamples=10000):
    if resamples < 1:
        raise ValueError('resamples must be positive')
    values = list(values)
    if not values:
        return dict(mean_difference=None, ci_low=None, ci_high=None, n_matched_tasks=0)
    rng = random.Random(seed)
    draws = [mean(rng.choices(values, k=len(values))) for _ in range(resamples)]
    return dict(mean_difference=mean(values), ci_low=percentile(draws, .025),
                ci_high=percentile(draws, .975), n_matched_tasks=len(values))


def paired_comparison(rows, left, right, metric, auditor_model, seed=2026111702, resamples=10000):
    # left - right. Builder-auditor FCR is also reported as AuditImprovement.
    grouped = defaultdict(list)
    for row in rows:
        if row['audit_condition'] in {left, right} and (
                row['audit_condition'] == 'builder' or row['auditor_model'] == auditor_model):
            grouped[row['task_id'], row['artifact_id'], row['audit_condition']].append(row)
    deltas = defaultdict(list)
    for task, artifact, condition in sorted(grouped):
        if condition != left or (task, artifact, right) not in grouped:
            continue
        lrows, rrows = grouped[task, artifact, left], grouped[task, artifact, right]
        if {r['requirement_id'] for r in lrows} != {r['requirement_id'] for r in rrows}:
            raise ValueError('Paired requirements differ')
        a, b = audit_metrics(lrows)[metric], audit_metrics(rrows)[metric]
        if a is not None and b is not None:
            deltas[task].append(a-b)
    task_differences = {task: mean(values) for task, values in sorted(deltas.items())}
    return dict(left=left, right=right, metric=metric, auditor_model=auditor_model,
                n_matched_artifacts=sum(map(len, deltas.values())), task_differences=task_differences,
                **bootstrap(task_differences.values(), seed, resamples))
