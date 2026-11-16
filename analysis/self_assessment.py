"""Descriptive claim accuracy; requirements are never independent samples."""
from harness.scoring import aggregate_assessments, assess


def summarize(dataset):
    result = []
    if dataset['role'] != 'A':
        return result  # B has no prompted requirement accounting.
    for condition in ('CD', 'SD'):
        records = [r for r in dataset['records'] if r['trajectory']['condition'] == condition]
        for number in (1, 2):
            turns = [r['turns'][number - 1] for r in records if len(r['turns']) >= number]
            values = [assess(t['requirements'], t['claims']) for t in turns]
            for name, value in aggregate_assessments(values).items():
                result.append(dict(model='A', condition=condition, turn=number, metric=name,
                                   **value, claim_issue_trajectories=sum(bool(t['claim_issues']) for t in turns)))
    return result
