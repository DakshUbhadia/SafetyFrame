"""Utilities for AI capability research capability_run processing."""
import copy

def _impl_latest_checkpoints(events):
    result = {}
    for e in events:
        if e['job'] not in result or e['sequence'] >= result[e['job']]['sequence']:
            result[e['job']] = copy.deepcopy(e)
    return result

def _impl_resume_jobs(jobs, checkpoints):
    return sorted((j for j in set(jobs) if checkpoints.get(j, {}).get('status') != 'complete'))

def _impl_reconcile_artifacts(expected, observed):
    return {'missing': sorted(expected.keys() - observed.keys()), 'changed': sorted((k for k in expected.keys() & observed.keys() if expected[k] != observed[k])), 'unexpected': sorted(observed.keys() - expected.keys())}

def _impl_plan_retries(jobs, checkpoints, max_attempts):
    if type(max_attempts) is not int or max_attempts <= 0:
        raise ValueError('limit')
    return sorted((j for j in set(jobs) if checkpoints.get(j, {}).get('status', 'pending') in ('pending', 'failed') and checkpoints.get(j, {}).get('attempts', 0) < max_attempts))

def latest_checkpoints(events):
    return _impl_latest_checkpoints(events)

def resume_jobs(jobs, checkpoints):
    return _impl_resume_jobs(jobs, checkpoints)

def reconcile_artifacts(expected, observed):
    return _impl_reconcile_artifacts(expected, observed)

def plan_retries(jobs, checkpoints, max_attempts):
    return _impl_plan_retries(jobs, checkpoints, max_attempts)
