"""Observed-turn denominators and complete-trajectory repair, without imputation."""
from .model_a import mean


def summarize(dataset):
    result = []
    for condition in (('C', 'S', 'CD', 'SD') if dataset['role'] == 'A' else ('C', 'S')):
        records = [r for r in dataset['records'] if r['trajectory']['condition'] == condition]
        completed = [r for r in records if r['trajectory']['status'] == 'completed']
        first = [r['turns'][0]['tcs'] for r in records if r['turns']]
        second = [r['turns'][1]['tcs'] for r in completed]
        gains = [r['turns'][1]['tcs'] - r['turns'][0]['tcs'] for r in completed]
        result.append(dict(model=dataset['role'], condition=condition,
            observed_turn1=len(first), completed_pairs=len(completed),
            turn1_mean_all_observed=mean(first),
            turn1_mean_completed=mean([r['turns'][0]['tcs'] for r in completed]),
            turn2_mean=mean(second), mean_repair_gain=mean(gains),
            artifact_repair_gain=mean([r['turns'][1]['artifact_tcs'] - r['turns'][0]['artifact_tcs'] for r in completed]),
            improved=sum(v > 0 for v in gains), unchanged=sum(v == 0 for v in gains),
            worsened=sum(v < 0 for v in gains)))
    return result
