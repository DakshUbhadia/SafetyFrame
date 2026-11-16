"""Evidence-backed manuscript tables; no statistical recalculation or inference."""
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.artifacts import read_json


def fmt(value):
    return 'NA' if value is None else f'{value:.4f}'


def interval(row):
    return f"{fmt(row['estimate'])} [{fmt(row['lower'])}, {fmt(row['upper'])}], N={row['tasks']}"


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |',
                      '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(map(str, row)) + ' |' for row in rows])


def evidence():
    result = read_json(ROOT / 'report/final_analysis/summary.json')
    datasets = {r: read_json(ROOT / f'report/model_{r.lower()}/scored_dataset.json') for r in ('A', 'B')}
    with (ROOT / 'data/task_inventory.csv').open(encoding='utf-8', newline='') as stream:
        tasks = list(csv.DictReader(stream))
    return result, datasets, tasks


def tables(result, datasets, tasks):
    rendered = {}
    rendered['conditions'] = table(['Model', 'Condition', 'Completed / planned', 'Provider failures', 'TCS [95% CI]'],
        [(r['model'], r['condition'], f"{r['completed']}/{r['planned']}", r['provider_failed'],
          f"{fmt(r['mean'])} [{fmt(r['lower'])}, {fmt(r['upper'])}]") for r in result['conditions']])
    names = [('BaselineSafetyGap_A', 'A C minus S'), ('BaselineSafetyGap_B', 'B C minus S'),
             ('DisclosureEffect_C_A', 'A CD minus C'), ('DisclosureEffect_S_A', 'A SD minus S'),
             ('DisclosureFramingInteraction_A', 'A interaction')]
    def contrast(name, kind):
        return next(r for r in result['contrasts'] if r['contrast'] == name and r['estimand'] == kind)
    rendered['contrasts'] = table(['Contrast', 'Primary', 'Provider utility', 'Valid format'],
        [(label, *(interval(contrast(name, kind)) for kind in ('primary', 'provider_utility', 'valid_format')))
         for name, label in names])
    metrics = [('urdr_strict', 'Strict URDR'), ('urdr_lenient', 'Lenient URDR'),
               ('false_completion_rate', 'FCR'), ('completion_precision', 'Completion precision'),
               ('unmet_disclosure_precision', 'Unmet-disclosure precision')]
    def cell(condition, name):
        r = next(r for r in result['self_assessment'] if r['condition'] == condition and r['turn'] == 2 and r['metric'] == name)
        return f"{r['numerator']}/{r['denominator']} = {fmt(r['micro'])}"
    rendered['self_assessment'] = table(['Metric', 'CD', 'SD'], [(label, cell('CD', name), cell('SD', name)) for name, label in metrics])
    rendered['repair'] = table(['Model', 'Condition', 'Paired N', 'Turn 1', 'Turn 2', 'Repair', 'Artifact repair'],
        [(r['model'], r['condition'], r['completed_pairs'], fmt(r['turn1_mean_completed']), fmt(r['turn2_mean']),
          fmt(r['mean_repair_gain']), fmt(r['artifact_repair_gain'])) for r in result['repair']])
    rendered['tasks'] = table(['Task', 'Family', 'Canonical title', 'Requirements', 'Editable files'],
        [(r['task_id'], r['family'], r['title'], r['requirements_total'], r['source_files']) for r in tasks])
    rendered['failures'] = table(['Model', 'Condition', 'Turn', 'Observed / planned', 'Format failures', 'Terminal provider failures'],
        [(r['model'], r['condition'], r['turn'], f"{r['observed']}/{r['planned']}", r['format_failures'],
          r['terminal_provider_failures_at_turn']) for r in result['failures']])
    incidents = []
    for role, data in datasets.items():
        for record in data['records']:
            row = record['trajectory']
            if row['status'] == 'provider_failed':
                incidents.append((row['run_id'], 'Provider failure', len(record['turns']) + 1,
                                  row['provider_failure_type'], 'Missing primary; zero utility; no replacement'))
            elif role == 'A' and row['format_success_turn2'] is False:
                incidents.append((row['run_id'], 'Format failure', 2, 'Invalid final file transaction',
                                  f"End-to-end {fmt(row['tcs_turn2'])}; artifact {fmt(row['artifact_tcs_turn2'])}; no replacement"))
    rendered['incidents'] = table(['Run', 'Category', 'Turn', 'Observed issue', 'Analysis treatment'], sorted(incidents))
    return rendered
