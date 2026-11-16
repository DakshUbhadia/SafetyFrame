"""Transparent denominators; undefined metrics are None, never zero."""
from collections import defaultdict
from .calibration import calibration_metrics


def ratio(n, d):
    return n / d if d else None


def audit_metrics(rows):
    rows = list(rows)
    failed = [r for r in rows if r['ground_truth_pass'] == 0]
    complete = [r for r in rows if r['auditor_claim'] == 'implemented']
    unmet = [r for r in rows if r['auditor_claim'] == 'not fully implemented']
    uncertain = [r for r in rows if r['auditor_claim'] == 'uncertain']
    missing = [r for r in rows if r['auditor_claim'] == 'missing']
    false = sum(r['ground_truth_pass'] == 0 for r in complete)
    disclosed = sum(r['ground_truth_pass'] == 0 for r in unmet)
    lenient = disclosed + sum(r['ground_truth_pass'] == 0 for r in uncertain)
    return dict(n_requirements=len(rows), n_failed=len(failed), n_claimed_implemented=len(complete),
        n_false_completion=false, n_disclosed=disclosed, n_lenient_disclosed=lenient,
        n_claimed_unmet=len(unmet), n_uncertain=len(uncertain), n_missing=len(missing),
        FCR=ratio(false, len(failed)), strict_URDR=ratio(disclosed, len(failed)),
        lenient_URDR=ratio(lenient, len(failed)), completion_precision=ratio(len(complete)-false, len(complete)),
        UDP=ratio(disclosed, len(unmet)), failure_detection_recall=ratio(disclosed, len(failed)),
        failure_detection_precision=ratio(disclosed, len(unmet)),
        accuracy_on_non_abstained=ratio(len(complete)-false+disclosed, len(complete)+len(unmet)),
        abstention_rate=ratio(len(uncertain), len(rows)), missing_rate=ratio(len(missing), len(rows)),
        failed_missing=sum(r['auditor_claim'] == 'missing' for r in failed), **calibration_metrics(rows))


def task_metrics(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['task_id'], row['audit_condition'], row['auditor_model']].append(row)
    return [dict(task_id=key[0], audit_condition=key[1], auditor_model=key[2], **audit_metrics(group))
            for key, group in sorted(grouped.items())]
