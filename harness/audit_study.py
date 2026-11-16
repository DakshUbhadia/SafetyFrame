"""Study 2 preparation, preservation, randomization and immutable protocol freeze.

Run as python -m harness.audit_study prepare|verify|freeze.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import random
from pathlib import Path
import subprocess

from .artifacts import confined, digest, read_json, safe_name, tree_files, tree_hash, write_json
from .audit_parser import STATUSES

ROOT = Path(__file__).resolve().parents[1]
STUDY = 'study_2_audit'
INVENTORY_FIELDS = ('artifact_id study1_run_id task_id model condition turn artifact_path '
    'requirements_path hidden_scores_path n_requirements n_passed n_failed artifact_hash '
    'eligible exclusion_reason').split()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def csv_text(rows, fields):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def write_once(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding='utf-8') != text:
            raise ValueError(f'Existing immutable output differs: {path}')
        return
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text)


def inventory(root=ROOT):
    """Enumerate every Study 1 trajectory; inclusion never depends on pass rate."""
    entries, rows = [], []
    for role in ('a', 'b'):
        source = f'report/model_{role}/scored_dataset.json'
        for record in read_json(root/source)['records']:
            trajectory = record['trajectory']
            run_id, task_id = trajectory['run_id'], trajectory['task_id']
            condition = trajectory['condition']
            artifact_path = f'data/main/final_snapshots/{run_id}'
            task_path = f'rendered_tasks/{task_id}_{condition[0]}'
            metadata = read_json(confined(root, task_path + '/task.json'))
            ids = [r['id'] for r in metadata['requirements']]
            turns = record['turns']
            final = turns[1] if len(turns) > 1 else None
            reason = ''
            artifact_hash = ''
            if trajectory['status'] != 'completed':
                reason = 'provider_failure_or_incomplete_trajectory'
            elif not final or set(final.get('requirements', {})) != set(ids):
                reason = 'missing_hidden_requirement_outcomes'
            elif not all(type(v) is bool for v in final['requirements'].values()):
                reason = 'invalid_hidden_requirement_outcomes'
            elif not confined(root, artifact_path).is_dir():
                reason = 'final_artifact_not_recoverable'
            else:
                artifact_hash = tree_hash(root/artifact_path)
                if artifact_hash != final['workspace_hash']:
                    raise ValueError(f'Study 1 workspace hash mismatch: {run_id}')
            passed = sum(final['requirements'].values()) if final else None
            row = dict(artifact_id=run_id, study1_run_id=run_id, task_id=task_id,
                model=trajectory['model_id'], condition=condition, turn=2, artifact_path=artifact_path,
                requirements_path=task_path + '/task.json', hidden_scores_path=source,
                n_requirements=len(ids), n_passed=passed,
                n_failed=len(ids)-passed if passed is not None else None,
                artifact_hash=artifact_hash, eligible=not reason, exclusion_reason=reason)
            rows.append(row)
            if reason:
                continue
            # Explicit allowlist: no checks, mapping, reference, score, metadata or claims in bundle.
            public = dict(specification=confined(root, task_path + '/specification.md').read_text(encoding='utf-8'),
                requirements=[{'id': r['id'], 'text': r['text']} for r in metadata['requirements']],
                files={name: path.read_text(encoding='utf-8') for name, path in tree_files(root/artifact_path).items()},
                public_tests={name: path.read_text(encoding='utf-8')
                              for name, path in tree_files(root/task_path/'public_tests').items()})
            claims = final.get('claims') or {}
            truth = [dict(requirement_id=rid, ground_truth_pass=int(final['requirements'][rid]),
                          builder_claim=claims.get(rid) if claims.get(rid) in STATUSES else 'missing') for rid in ids]
            entries.append(dict(**row, public_bundle=public, public_bundle_hash=digest(public), truth=truth,
                builder_parse_status='invalid' if final.get('claim_issues') or any(
                    r['builder_claim'] == 'missing' for r in truth) else 'valid'))
    return sorted(rows, key=lambda r: r['artifact_id']), sorted(entries, key=lambda e: e['artifact_id'])


def schedule(entries, config):
    rng = random.Random(config['randomization_seed'])
    tasks = sorted({e['task_id'] for e in entries})
    rng.shuffle(tasks)
    rows = []
    for task in tasks:
        artifacts = [e for e in entries if e['task_id'] == task and e['condition'] in config['builder_conditions']]
        rng.shuffle(artifacts)
        for entry in artifacts:
            cells = [(condition, model) for model in sorted(config['auditors']) for condition in config['conditions']]
            rng.shuffle(cells)
            for order, (condition, model) in enumerate(cells, 1):
                rows.append(dict(audit_run_id=f"audit-{entry['artifact_id']}-{model}-{condition}",
                    artifact_id=entry['artifact_id'], task_id=task, auditor_key=model,
                    auditor_model=config['auditors'][model]['model_id'], audit_condition=condition,
                    within_artifact_order=order, public_bundle_hash=entry['public_bundle_hash']))
    return rows


def validate_config(config):
    if (set(config['conditions']) - {'fresh', 'evidence', 'confidence', 'critic', 'cross_model'}
            or not config['conditions'] or len(set(config['conditions'])) != len(config['conditions'])
            or set(config['builder_conditions']) - {'CD', 'SD'}):
        raise ValueError('Invalid matched audit conditions')
    if config['maximum_attempts'] != 3 or config['minimum_request_interval_seconds'] < 60:
        raise ValueError('Frozen retry/pacing policy requires three attempts and at least 60 seconds')
    if config['bootstrap_resamples'] != 10000:
        raise ValueError('Preregistered bootstrap requires 10,000 resamples')
    ids = []
    for key, model in config['auditors'].items():
        safe_name(key)
        ids.append(model['model_id'])
        if (not model['model_id'] or model['generation'].get('max_output_tokens', 0) < 1
                or model['provider'] not in config['providers']):
            raise ValueError('Incomplete auditor configuration')
    if not ids or len(set(ids)) != len(ids):
        raise ValueError('Auditor models must be distinct')


def preservation(root=ROOT):
    result = subprocess.run(['git', '-C', str(root), 'ls-files', '-z'], capture_output=True, check=True)
    paths = {p for p in result.stdout.decode().split('\0') if p and not p.startswith(STUDY+'/')}
    for folder in ('data/main',):
        paths.update(f'{folder}/{name}' for name in tree_files(root/folder))
    return {name: file_hash(confined(root, name)) for name in sorted(paths)}


def prepare(root=ROOT):
    root = Path(root)
    study = root/STUDY
    if (study/'freeze.json').exists():
        raise ValueError('Study 2 is frozen; preparation cannot rewrite the study')
    rows, entries = inventory(root)
    config = read_json(study/'study_config.json')
    validate_config(config)
    for directory in ('raw', 'parsed', 'scored', 'analysis', 'figures', 'logs', 'inputs'):
        (study/directory).mkdir(parents=True, exist_ok=True)
    manifest = study/'manifests'
    write_once(manifest/'artifact_inventory.csv', csv_text(rows, INVENTORY_FIELDS))
    for entry in entries:
        write_once(study/'inputs'/f"{entry['artifact_id']}.json", json.dumps(entry, indent=2, ensure_ascii=False)+'\n')
    planned = schedule(entries, config)
    write_once(manifest/'audit_manifest.csv', csv_text(planned, [
        'audit_run_id', 'artifact_id', 'task_id', 'auditor_key', 'auditor_model', 'audit_condition',
        'within_artifact_order', 'public_bundle_hash']))
    randomized = dict(seed=config['randomization_seed'], algorithm='Python random.Random; task blocks then artifacts then cells',
                      run_ids=[r['audit_run_id'] for r in planned])
    write_once(manifest/'randomization.json', json.dumps(randomized, indent=2)+'\n')
    path = manifest/'study1_preservation.json'
    if not path.exists():
        checkpoint = subprocess.run(['git', '-C', str(root), 'rev-parse', 'HEAD'],
                                    capture_output=True, text=True, check=True).stdout.strip()
        write_json(path, dict(source_commit=checkpoint, timestamp=datetime.now(timezone.utc).isoformat(),
            tag='safetyframe-sprint-2026-final', final_pdf_available=bool(list((root/'report').glob('*.pdf'))),
            report_status='Sprint 10 manuscript; Sprint 11 final PDF is pending',
            hash_algorithm='SHA-256 exact bytes; existing Study 1 hashes preserved unchanged', files=preservation(root)), immutable=True)
    verify_preservation(root)
    return dict(inventory=len(rows), eligible=len(entries), excluded=len(rows)-len(entries), scheduled=len(planned))


def verify_preservation(root=ROOT):
    root = Path(root)
    manifest = read_json(root/STUDY/'manifests/study1_preservation.json')
    for name, expected in manifest['files'].items():
        if file_hash(confined(root, name)) != expected:
            raise ValueError(f'Preserved Study 1 file changed: {name}')
    checkpoint = subprocess.run(['git', '-C', str(root), 'rev-parse', manifest['tag']+'^{commit}'],
                                capture_output=True, text=True, check=True).stdout.strip()
    if checkpoint != manifest['source_commit']:
        raise ValueError('Study 1 preservation tag points to a different checkpoint')
    return manifest


def verify_study1(root=ROOT):
    """Verify the original frozen membership, permitting additive follow-up modules.

    The original verifier intentionally rejects any added file in harness/. It
    remains unchanged; this command checks its recorded file set and preservation.
    """
    root = Path(root)
    manifest = read_json(root/'freeze_manifest.json')
    from .freeze import file_hash as normalized_hash, validate_plan
    for name, expected in manifest['files'].items():
        if normalized_hash(confined(root, name)) != expected:
            raise ValueError('Original frozen artifact changed: ' + name)
    config, analysis, execution = validate_plan(root)
    if (digest(config) != manifest['configuration_hash'] or analysis != manifest['analysis']
            or execution['executor'] != manifest['executor']):
        raise ValueError('Original frozen settings changed')
    verify_preservation(root)
    return {'study1_frozen_files_verified': len(manifest['files']),
            'membership_policy': 'Original manifest, plus additive Study 2 modules; no original changes'}


def protocol_files(root=ROOT):
    root = Path(root)
    paths = []
    for directory in ('prompts', 'manifests', 'inputs'):
        paths.extend(f'{STUDY}/{directory}/{name}' for name in tree_files(root/STUDY/directory))
    paths.extend(f'{STUDY}/{name}' for name in ('study_config.json', 'preregistration.md', 'evidence_rubric.md'))
    paths.extend(f'harness/{name}' for name in ('audit_study.py', 'audit_runner.py', 'audit_parser.py',
        'evidence_parser.py', 'confidence_parser.py', 'audit_scoring.py', 'audit_review.py'))
    paths.extend(f'analysis/{name}' for name in ('audit_metrics.py', 'calibration.py', 'paired_comparisons.py',
        'audit_analysis.py', 'audit_figures.py'))
    # Pin reused transport, accounting and filesystem code without changing Study 1.
    paths.extend(f'harness/{name}' for name in ('artifacts.py', 'budget.py', 'preflight.py',
                                               'providers/adaption.py'))
    paths.extend(['requirements.txt', 'analysis/requirements.txt'])
    paths.extend(f'{STUDY}/tests/{name}' for name in tree_files(root/STUDY/'tests'))
    return {name: file_hash(confined(root, name)) for name in sorted(paths)}


def freeze(root=ROOT):
    root = Path(root)
    study = root/STUDY
    if (study/'freeze.json').exists():
        raise ValueError('Never replace an existing Study 2 freeze')
    verify_preservation(root)
    if any((study/'raw').rglob('*.json')):
        raise ValueError('Raw audit requests already exist; pre-outcome freeze unavailable')
    config = read_json(study/'study_config.json')
    validate_config(config)
    if config['protocol_status'] != 'ready_to_freeze' or not config['auditors']:
        raise ValueError('Resolve protocol choices and set protocol_status=ready_to_freeze first')
    # A freeze cannot silently omit an eligible scheduled artifact or change order.
    rows, entries = inventory(root)
    expected = schedule(entries, config)
    with (study/'manifests/audit_manifest.csv').open(encoding='utf-8', newline='') as stream:
        actual = list(csv.DictReader(stream))
    if digest(actual) != digest([{k: str(v) for k, v in r.items()} for r in expected]):
        raise ValueError('Schedule differs from preregistered deterministic randomization')
    randomized = read_json(study/'manifests/randomization.json')
    if randomized['seed'] != config['randomization_seed'] or randomized['run_ids'] != [r['audit_run_id'] for r in expected]:
        raise ValueError('Randomization record differs from schedule')
    for entry in entries:
        if read_json(study/'inputs'/f"{entry['artifact_id']}.json") != entry:
            raise ValueError('Inventory input changed after preparation')
    if (study/'manifests/artifact_inventory.csv').read_text(encoding='utf-8') != csv_text(rows, INVENTORY_FIELDS):
        raise ValueError('Inventory differs from Study 1 source')
    manifest = dict(study_id=STUDY, timestamp=datetime.now(timezone.utc).isoformat(),
        authority='Local protocol freeze, not external registration or human review', files=protocol_files(root))
    write_json(study/'freeze.json', manifest, immutable=True)
    return manifest


def verify_freeze(root=ROOT):
    root = Path(root)
    manifest = read_json(root/STUDY/'freeze.json')
    if manifest['files'] != protocol_files(root):
        raise ValueError('Study 2 protocol changed after freeze')
    verify_preservation(root)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'freeze', 'verify', 'verify-preservation', 'verify-study1'])
    args = parser.parse_args()
    result = {'prepare': prepare, 'freeze': freeze, 'verify': verify_freeze,
              'verify-preservation': verify_preservation, 'verify-study1': verify_study1}[args.command]()
    print({k: v for k, v in result.items() if k != 'files'})


if __name__ == '__main__':
    main()
