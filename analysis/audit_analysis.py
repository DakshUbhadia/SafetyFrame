"""Reproducible Study 2 analysis; no calls, outcome selection or hidden edits.

python -m analysis.audit_analysis [--figures]
"""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
from statistics import mean

from harness.artifacts import confined, read_json, write_json
from harness.audit_scoring import builder_rows
from harness.audit_study import ROOT, STUDY, csv_text, verify_freeze, verify_preservation
from .audit_metrics import audit_metrics, task_metrics
from .paired_comparisons import bootstrap, paired_comparison


def save_csv(path, rows):
    if not rows:
        path.write_text('', encoding='utf-8')
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    values = [{key: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else
               'NA' if value is None else value for key, value in row.items()} for row in rows]
    path.write_text(csv_text(values, fields), encoding='utf-8')


def comparisons(rows, config):
    result = []
    for model in config['auditors'].values():
        for left, right in [('fresh', 'builder'), ('evidence', 'fresh')]:
            for metric in ('FCR', 'strict_URDR', 'lenient_URDR'):
                result.append(paired_comparison(rows, left, right, metric, model['model_id'],
                    config['analysis_seed'], config['bootstrap_resamples']))
        result.append(paired_comparison(rows, 'builder', 'fresh', 'FCR', model['model_id'],
            config['analysis_seed'], config['bootstrap_resamples']))
    return result


def macro_tasks(rows):
    artifacts = defaultdict(list)
    for row in rows:
        artifacts[row['task_id'], row['audit_condition'], row['auditor_model'], row['artifact_id']].append(row)
    tasks = defaultdict(list)
    for key, values in sorted(artifacts.items()):
        tasks[key[:3]].append(audit_metrics(values))
    result = []
    metrics = ('FCR', 'strict_URDR', 'lenient_URDR', 'completion_precision', 'UDP',
               'abstention_rate', 'missing_rate', 'Brier', 'mean_confidence_passed', 'mean_confidence_failed',
               'confidence_pass_minus_fail')
    for (task, condition, model), values in sorted(tasks.items()):
        row = dict(task_id=task, audit_condition=condition, auditor_model=model, n_artifacts=len(values))
        for metric in metrics:
            selected = [v[metric] for v in values if v[metric] is not None]
            row[metric] = mean(selected) if selected else None
        result.append(row)
    return result


def condition_summary(tasks, config):
    grouped = defaultdict(list)
    for row in tasks:
        grouped[row['audit_condition'], row['auditor_model']].append(row)
    result = []
    for (condition, model), group in sorted(grouped.items()):
        for metric in ('FCR', 'strict_URDR', 'lenient_URDR', 'Brier', 'mean_confidence_failed',
                       'mean_confidence_passed', 'confidence_pass_minus_fail'):
            values = [r[metric] for r in group if r[metric] is not None]
            result.append(dict(audit_condition=condition, auditor_model=model, metric=metric,
                **bootstrap(values, config['analysis_seed'], config['bootstrap_resamples'])))
    return result


def evidence_review(rows, reviews):
    """Join independently reviewed evidence; never infer correctness from truth/status."""
    from harness.evidence_parser import EVIDENCE_CATEGORIES
    index = {(r['audit_run_id'], r['requirement_id']): r for r in rows if r['audit_condition'] == 'evidence'}
    seen = set()
    for review in reviews:
        key = (review['audit_run_id'], review['requirement_id'])
        if key not in index or key in seen:
            raise ValueError('Unknown or duplicate evidence-review key')
        seen.add(key)
        if not review.get('reviewer_id') or not review.get('timestamp') or review.get('rubric_version') != '1':
            raise ValueError('Review identity, timestamp and frozen rubric version are required')
        if review['evidence_specificity'] not in EVIDENCE_CATEGORIES:
            raise ValueError('Invalid evidence category')
        correctness = review['evidence_correctness']
        if correctness not in ('0', '1', 'NA', ''):
            raise ValueError('Invalid evidence correctness')
        row = index[key]
        if not row['evidence_text'] and (review['evidence_specificity'] != 'missing' or correctness not in ('NA', '')):
            raise ValueError('Missing evidence must have missing specificity and NA correctness')
        row.update(evidence_specificity=review['evidence_specificity'],
                   evidence_correctness=int(correctness) if correctness in ('0', '1') else None,
                   reviewer_id=review['reviewer_id'], review_timestamp=review['timestamp'],
                   rubric_version='1', review_comments=review.get('comments', ''))


def analyze(root=ROOT, figures=False):
    root = Path(root)
    study = root/STUDY
    verify_preservation(root)
    if (study/'freeze.json').exists():
        verify_freeze(root)
    config = read_json(study/'study_config.json')
    with (study/'manifests/audit_manifest.csv').open(encoding='utf-8', newline='') as stream:
        schedule = list(csv.DictReader(stream))
    entries = {r['artifact_id']: read_json(study/'inputs'/f"{r['artifact_id']}.json") for r in schedule}
    baseline = builder_rows(entries.values())
    records = []
    for row in schedule:
        path = study/'scored'/f"{row['audit_run_id']}.json"
        if path.exists():
            stored = read_json(path)
            from harness.audit_runner import persist_result
            outcome = confined(root, stored['metadata']['raw_response_path'])
            if outcome.parent != study/'raw'/row['audit_run_id']:
                raise ValueError('Scored response points outside its scheduled audit')
            # Reparse and rescore immutable raw data; mismatches reject manual edits.
            records.append(persist_result(study, row, entries[row['artifact_id']], read_json(outcome), outcome))
    audit_rows = [row for record in records for row in record['rows']]
    reviews_path = study/'reviews/evidence_reviews.csv'
    if reviews_path.exists():
        with reviews_path.open(encoding='utf-8', newline='') as stream:
            evidence_review(audit_rows, list(csv.DictReader(stream)))
    all_rows = baseline + audit_rows
    # Primary: provider-completed responses, including invalid model output as missing.
    primary = [r for r in all_rows if r['provider_status'] == 'completed']
    valid = [r for r in primary if r['parse_status'] == 'valid']
    task_rows = task_metrics(primary)
    macros = macro_tasks(primary)
    pooled = []
    groups = defaultdict(list)
    for row in primary:
        groups[row['audit_condition'], row['auditor_model']].append(row)
    for (condition, model), values in sorted(groups.items()):
        pooled.append(dict(audit_condition=condition, auditor_model=model, descriptive_only=True,
                           **audit_metrics(values)))
    terminal = len(records)
    status = 'not_started' if not records else 'complete' if terminal == len(schedule) else 'incomplete'
    summary = dict(study_id=STUDY, collection_status=status, scheduled=len(schedule), terminal=terminal,
        provider_failures=sum(r['provider_status'] != 'completed' for r in records),
        malformed_completed=sum(r['provider_status'] == 'completed' and r['parse_status'] != 'valid' for r in records),
        protocol_frozen=(study/'freeze.json').exists(), inference_unit='task',
        result_note='No Study 2 findings until audit outcomes exist; partial collections are explicitly labeled.',
        primary=comparisons(primary, config), valid_parse_only=comparisons(valid, config),
        missing_as_failure_to_disclose=comparisons(all_rows, config),
        condition_summary=condition_summary(macros, config), requirement_pooled_descriptive=pooled)
    output = study/'analysis'
    output.mkdir(parents=True, exist_ok=True)
    save_csv(output/'audit_results.csv', all_rows)
    save_csv(output/'task_metrics.csv', task_rows)
    save_csv(output/'artifact_macro_task_metrics.csv', macros)
    save_csv(output/'paired_comparisons.csv', summary['primary'])
    save_csv(output/'valid_parse_only.csv', summary['valid_parse_only'])
    save_csv(output/'missing_as_failure_to_disclose.csv', summary['missing_as_failure_to_disclose'])
    save_csv(output/'condition_summary.csv', summary['condition_summary'])
    save_csv(output/'requirement_pooled_descriptive.csv', pooled)
    # Blinded evidence-review queue excludes condition comparison, claims and hidden truth.
    queue = [dict(audit_run_id=r['audit_run_id'], requirement_id=r['requirement_id'],
                  artifact_id=r['artifact_id'], evidence_text=r['evidence_text'],
                  reviewer_id='', timestamp='', rubric_version='1', evidence_specificity='',
                  evidence_correctness='', comments='') for r in audit_rows if r['audit_condition'] == 'evidence']
    save_csv(output/'evidence_review_queue.csv', queue)
    write_json(output/'summary.json', summary)
    if figures and audit_rows:
        from .audit_figures import generate_figures
        generate_figures(primary, summary, study/'figures')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--figures', action='store_true')
    args = parser.parse_args()
    result = analyze(figures=args.figures)
    print({k: result[k] for k in ('collection_status', 'scheduled', 'terminal', 'provider_failures')})


if __name__ == '__main__':
    main()
