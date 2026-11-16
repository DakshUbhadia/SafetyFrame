"""Recompute the final three result channels from reviewed saved scores, offline."""
import argparse
from copy import deepcopy
from pathlib import Path

from harness.artifacts import digest, read_json, write_json
from harness.freeze import planned_rows, verify_freeze
from harness.preflight import ROOT
from harness.scoring import assess
from .bootstrap import estimate
from .model_a import mean, summarize as summary_a, write_csv
from .model_b import summarize as summary_b
from .repair import summarize as repair
from .self_assessment import summarize as self_assessment


def rederive(dataset):
    """Recalculate every score/count from requirements and parsed claims; fail on drift."""
    data = deepcopy(dataset)
    for record in data['records']:
        row = record['trajectory']
        done = row['status'] == 'completed'
        if row['status'] not in ('completed', 'provider_failed') or (done and len(record['turns']) != 2):
            raise ValueError('Invalid terminal record')
        if not done and len(record['turns']) not in (0, 1):
            raise ValueError('Provider failure cannot contain a completed second turn')
        if row['requirements_total'] != 5:
            raise ValueError('Frozen requirement count changed')
        for number in (1, 2):
            if len(record['turns']) >= number:
                turn = record['turns'][number - 1]
                requirements = turn['requirements']
                if set(requirements) != {f'R{i}' for i in range(1, 6)} or any(type(v) is not bool for v in requirements.values()):
                    raise ValueError('Invalid requirement scores')
                claims = turn['claims']
                accounting = row['condition'] in ('CD', 'SD')
                if accounting:
                    if not isinstance(claims, dict) or set(claims) != set(requirements) or any(
                            v not in ('implemented', 'not_fully_implemented', 'uncertain', 'missing') for v in claims.values()):
                        raise ValueError('Invalid parsed claims')
                elif claims is not None:
                    raise ValueError('Unprompted claims cannot enter the baseline analysis')
                if type(turn['format_success']) is not bool:
                    raise ValueError('Invalid format state')
                passed = sum(requirements.values()); artifact = passed / len(requirements)
                score = artifact if turn['format_success'] else 0
                computed = dict(requirements_passed=passed, artifact_tcs=artifact, tcs=score,
                                assessment=assess(requirements, claims))
                for key, value in computed.items():
                    if turn[key] != value:
                        raise ValueError('Stored turn disagrees with recomputation: ' + key)
                    turn[key] = value
                expected = dict(tcs=score, artifact_tcs=artifact, requirements_passed=passed,
                                format_success=turn['format_success'])
            else:
                expected = dict(tcs=None, artifact_tcs=None, requirements_passed=None, format_success=None)
            for key, value in expected.items():
                field = f'{key}_turn{number}'
                if row[field] != value:
                    raise ValueError('Stored trajectory disagrees with recomputation: ' + field)
                row[field] = value
        gain = row['tcs_turn2'] - row['tcs_turn1'] if done else None
        for key, value in dict(repair_gain=gain, primary_analysis_included=done,
                               end_to_end_utility_score=row['tcs_turn2'] if done else 0).items():
            if row[key] != value:
                raise ValueError('Stored trajectory disagrees with recomputation: ' + key)
            row[key] = value
    return data


def load_reviewed(role, manifest):
    directory = ROOT / 'report' / f'model_{role.lower()}'
    proof = read_json(directory / 'integrity.json')
    for name, expected in proof['normalized_text_digests'].items():
        if digest((directory / name).read_text(encoding='utf-8')) != expected:
            raise ValueError('Reviewed release changed: ' + role + '/' + name)
    data = read_json(directory / 'scored_dataset.json')
    if data['role'] != role or data['freeze_hash'] != digest(manifest):
        raise ValueError('Wrong frozen dataset')
    planned = {r['run_id']: r for r in planned_rows() if r['role'] == role}
    actual = [r['trajectory'] for r in data['records']]
    if len(actual) != len(planned) or {r['run_id'] for r in actual} != set(planned):
        raise ValueError('Schedule mismatch')
    for row in actual:
        expected = planned[row['run_id']]
        for key in ('task_id', 'condition', 'model_id', 'provider', 'block_id'):
            if row[key] != expected[key]:
                raise ValueError('Frozen identity mismatch: ' + key)
        if row['phase'] != 'final' or int(row['within_block_order']) != int(expected['within_block_order']):
            raise ValueError('Frozen execution order mismatch')
    return rederive(data)


def compute(datasets, config):
    summaries = {role: (summary_a if role == 'A' else summary_b)(data, config)
                 for role, data in datasets.items()}
    contrasts = []
    condition_rows = []
    failures = []
    task_rows = []
    specs = {**config['contrasts'], **config['secondary_contrasts']}
    for role, data in datasets.items():
        summary = summaries[role]
        for condition, values in summary['conditions'].items():
            condition_rows.append(dict(model=role, condition=condition, planned=values['planned'],
                completed=values['completed'], provider_failed=values['provider_failed'], harness_unresolved=0,
                mean=values['estimate'], lower=values['lower'], upper=values['upper'],
                artifact_turn2_mean=values['artifact_turn2_mean']))
            selected = [r for r in data['records'] if r['trajectory']['condition'] == condition]
            for number in (1, 2):
                observed = [r['turns'][number - 1] for r in selected if len(r['turns']) >= number]
                failures.append(dict(model=role, condition=condition, turn=number, planned=len(selected),
                    observed=len(observed), missing=len(selected)-len(observed),
                    format_failures=sum(not t['format_success'] for t in observed),
                    provider_failed_trajectories=sum(r['trajectory']['status'] == 'provider_failed' for r in selected),
                    terminal_provider_failures_at_turn=sum(r['trajectory']['status'] == 'provider_failed'
                        and len(r['turns']) + 1 == number for r in selected), harness_unresolved=0,
                    artifact_mean=mean([t['artifact_tcs'] for t in observed]),
                    end_to_end_mean=mean([t['tcs'] for t in observed])))
        matrices = {kind: {} for kind in ('primary', 'provider_utility', 'valid_format')}
        for record in data['records']:
            row = record['trajectory']; task = row['task_id']; condition = row['condition']
            done = row['status'] == 'completed'
            values = dict(primary=row['tcs_turn2'] if done else None,
                provider_utility=row['end_to_end_utility_score'],
                valid_format=row['tcs_turn2'] if done and row['format_success_turn2'] else None)
            for kind, value in values.items():
                matrices[kind].setdefault(task, {})[condition] = value
        for name, spec in specs.items():
            if spec['role'] != role:
                continue
            for kind, matrix in matrices.items():
                result = estimate(matrix, spec['weights'], config['bootstrap'])
                reviewed = summary['contrasts'][name]
                reference = reviewed if kind == 'primary' else reviewed[
                    'utility_sensitivity' if kind == 'provider_utility' else 'valid_format_sensitivity']
                if any(result[k] != reference[k] for k in ('tasks', 'estimate', 'lower', 'upper')):
                    raise ValueError('Final contrast differs from reviewed estimand')
                contrasts.append(dict(model=role, contrast=name, estimand=kind,
                    **{k: result[k] for k in ('tasks', 'estimate', 'lower', 'upper')},
                    matched_condition_means={c: mean([matrix[t][c] for t in result['task_values']])
                                             for c in spec['weights']}))
                for task in sorted(summary['task_outcomes']):
                    task_rows.append(dict(model=role, contrast=name, estimand=kind, task_id=task,
                                          value=result['task_values'].get(task)))
    return dict(schema_version=1, freeze_hash=datasets['A']['freeze_hash'],
        analysis_config_hash=digest(config), dataset_hashes={r:digest(d) for r,d in datasets.items()},
        bootstrap=config['bootstrap'], unit='task', pooled_estimate=None,
        conditions=condition_rows, contrasts=contrasts, failures=failures,
        self_assessment=self_assessment(datasets['A']),
        repair=[row for data in datasets.values() for row in repair(data)],
        task_contrasts=task_rows, model_b_response_diagnostics=summaries['B']['response_diagnostics'])


def export(result, output, figures_dir):
    from .figures import figure_data, render, narrative
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / 'summary.json', result)
    for name in ('conditions', 'failures', 'self_assessment', 'repair', 'task_contrasts'):
        rows = result[name]
        write_csv(output / f'{name}.csv', list(rows[0]), rows)
    contrasts = [{k:v for k,v in row.items() if k != 'matched_condition_means'} for row in result['contrasts']]
    write_csv(output / 'contrasts.csv', list(contrasts[0]), contrasts)
    matched = [dict(model=r['model'], contrast=r['contrast'], estimand=r['estimand'], condition=c,
                    tasks=r['tasks'], mean=v) for r in result['contrasts'] for c,v in r['matched_condition_means'].items()]
    write_csv(output / 'matched_means.csv', list(matched[0]), matched)
    spec = figure_data(result)
    write_json(output / 'figure_data.json', spec)
    render(spec, figures_dir)
    import os
    relative = Path(os.path.relpath(figures_dir, output)).as_posix()
    (output / 'results.md').write_text(narrative(result, relative), encoding='utf-8', newline='\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'report/final_analysis')
    parser.add_argument('--figures', type=Path, default=ROOT / 'report/figures')
    parser.add_argument('--audit-raw', action='store_true', help='Additionally verify local raw/workspace evidence; no API calls')
    args = parser.parse_args()
    manifest = verify_freeze(); config = read_json(ROOT / 'config/analysis.json')
    datasets = {role: load_reviewed(role, manifest) for role in ('A', 'B')}
    if args.audit_raw:
        from .model_a import load_phase
        from .response_quality import enrich
        for role, data in datasets.items():
            raw = load_phase(role=role)
            if role == 'B':
                raw = enrich(raw, ROOT, manifest['models']['B']['generation']['max_output_tokens'])
            if raw != data:
                raise ValueError('Raw audit differs from reviewed release: ' + role)
    result = compute(datasets, config)
    # Preserve and verify every reviewed estimate and count, not just the headline gaps.
    for role, data in datasets.items():
        summary = (summary_a if role == 'A' else summary_b)(data, config)
        if role == 'B': summary['requested_model_id'] = manifest['models']['B']['model_id']
        if summary != read_json(ROOT / f'report/model_{role.lower()}/summary.json'):
            raise ValueError('Recomputed summary differs from reviewed release: ' + role)
    export(result, args.output, args.figures)
    verify_freeze()
    print('Sprint 9: all 96 terminal rows recomputed; three result channels, sensitivities and figures exported offline.')


if __name__ == '__main__':
    main()
