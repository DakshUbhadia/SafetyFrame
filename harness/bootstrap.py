"""Prespecified paired-task percentile intervals; no requirement-level resampling."""
import math
import random


def quantile(values,p):
    if not values: return None
    ordered=sorted(values); position=(len(ordered)-1)*p
    lower=math.floor(position); upper=math.ceil(position)
    return ordered[lower]+(ordered[upper]-ordered[lower])*(position-lower)


def paired_bootstrap(task_values,settings):
    values=[task_values[key] for key in sorted(task_values)]
    if any(not isinstance(value,(int,float)) or not math.isfinite(value) for value in values):
        raise ValueError('Bootstrap requires finite complete task contrast values')
    n=len(values)
    if not n: return dict(tasks=0,estimate=None,lower=None,upper=None)
    estimate=sum(values)/n
    if n<settings['minimum_tasks_for_interval']:
        return dict(tasks=n,estimate=estimate,lower=None,upper=None)
    rng=random.Random(settings['seed'])
    means=[sum(values[rng.randrange(n)] for _ in range(n))/n for _ in range(settings['resamples'])]
    alpha=(1-settings['confidence'])/2
    return dict(tasks=n,estimate=estimate,lower=quantile(means,alpha),upper=quantile(means,1-alpha))


def complete_contrast(tasks,weights):
    """tasks maps task_id -> condition -> numeric endpoint or None."""
    result={}
    for task_id,conditions in tasks.items():
        if all(conditions.get(condition) is not None for condition in weights):
            result[task_id]=sum(conditions[c]*weight for c,weight in weights.items())
    return result
