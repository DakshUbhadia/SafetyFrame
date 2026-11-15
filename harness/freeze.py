"""Create/verify the pre-outcome freeze; verification is mandatory before main calls."""
import argparse
import csv
from datetime import datetime,timedelta,timezone
import hashlib
import io
import platform
from pathlib import Path
import subprocess
import sys

import yaml

from .artifacts import confined,digest,read_json,tree_files,write_json
from .build_blocks import schedule_text
from .design_sensitivity import sensitivity_text
from .preflight import ROOT,budget_projection,validate_config

MANIFEST='freeze_manifest.json'
PROTOCOLS=['SPECIFICATION_v4.md','01_PREREGISTRATION_TEMPLATE.md','02_EXPERIMENT_PROTOCOL.md',
           '03_TASK_AUTHORING_GUIDE.md','04_TASK_VALIDATION_CHECKLIST.md','05_PROMPT_PROTOCOL.md',
           '08_DATA_DICTIONARY.md','09_SCORING_ANALYSIS_PLAN.md','10_SELF_ASSESSMENT_RUBRIC.md',
           '18_FREEZE_MANIFEST_GUIDE.md','preregistration.md','requirements.txt','.gitattributes']


def git(root,*args):
    result=subprocess.run(['git','-C',str(root),*args],capture_output=True,check=False)
    if result.returncode: raise ValueError('Git checkpoint verification failed: '+' '.join(args[:2]))
    return result.stdout


def file_hash(path):
    data=path.read_bytes().replace(b'\r\n',b'\n').replace(b'\r',b'\n')
    return 'sha256:'+hashlib.sha256(data).hexdigest()


def frozen_files(root=ROOT):
    benchmark=read_json(root/'config/benchmark.json')
    paths=set(PROTOCOLS+['data/run_manifest.csv','data/design_sensitivity.csv','data/task_inventory.csv',
                         'report/pilot_calibration.json','report/pilot_calibration.md'])
    for directory in ('config','harness','prompts','tests','data/task_validation'):
        paths.update(f'{directory}/{name}' for name in tree_files(root/directory))
    for entry in benchmark['tasks']:
        task_id=entry['task_id']; paths.add(entry['validation_record'])
        for directory in (f'task_templates/{task_id}',f'rendered_tasks/{task_id}_C',f'rendered_tasks/{task_id}_S'):
            paths.update(f'{directory}/{name}' for name in tree_files(root/directory))
    # Explicitly never include credentials, provider responses, mutable outputs, or self.
    return sorted(paths)


def validate_plan(root=ROOT):
    config=read_json(root/'config/study.json')
    validate_config(config)
    if config['study']['frozen'] is not True or config['study']['task_target']!=16:
        raise ValueError('Freeze requires an explicit sixteen-task frozen study configuration')
    if budget_projection(config)['status']!='estimated_fit':
        raise ValueError('Study must fit its planned budget')
    if (root/'data/run_manifest.csv').read_text(encoding='utf-8')!=schedule_text(root):
        raise ValueError('Schedule does not reproduce from frozen task IDs, models, and random seed')
    analysis=read_json(root/'config/analysis.json')
    if (root/'data/design_sensitivity.csv').read_text(encoding='utf-8')!=sensitivity_text(analysis):
        raise ValueError('Design-sensitivity table does not reproduce')
    execution=read_json(root/'config/execution.json')
    if execution['executor']['backend']!='docker' or not execution['executor']['image_id'].startswith('sha256:'):
        raise ValueError('Pinned Docker executor required')
    return config,analysis,execution


def create_freeze(root=ROOT):
    root=Path(root).resolve()
    if (root/MANIFEST).exists(): raise ValueError('Freeze already exists; never overwrite a freeze')
    if any(tree_files(root/'data/main'/section) for section in ('raw','runs','scored') if (root/'data/main'/section).exists()):
        raise ValueError('Final-run artifacts already exist; initial pre-outcome freeze is unavailable')
    # This command is deliberately repository-specific; full benchmark evidence
    # must be rechecked, rather than trusting metadata inclusion flags.
    if root!=ROOT.resolve(): raise ValueError('Create freeze only for the reviewed workspace')
    from .validate_benchmark import verify_inventory
    verify_inventory()
    config,analysis,execution=validate_plan(root)
    status=git(root,'status','--porcelain','--untracked-files=all').decode().strip()
    if status: raise ValueError('Commit all reviewed changes before creating freeze')
    checkpoint=git(root,'rev-parse','HEAD').decode().strip()
    paths=frozen_files(root)
    tracked=set(git(root,'ls-tree','-r','--name-only',checkpoint).decode().splitlines())
    if not set(paths)<=tracked: raise ValueError('Every frozen artifact must be in the checkpoint commit')
    from .run_tests import TestRunner
    runner=TestRunner('docker',execution['executor']['image'],execution['executor']['timeout_seconds'])
    runner.verify()
    if runner.image_id!=execution['executor']['image_id']: raise ValueError('Docker image differs from accepted references')
    now=datetime.now(timezone.utc)
    benchmark=read_json(root/'config/benchmark.json')
    manifest=dict(schema_version=1,freeze_timestamp_utc=now.isoformat(),
        freeze_timestamp_ist=now.astimezone(timezone(timedelta(hours=5,minutes=30))).isoformat(),
        git_commit=checkpoint,git_checkpoint_role='Reviewed source checkpoint; manifest is committed immediately afterward to avoid self-reference',
        researcher=execution['researcher'],freeze_authority=execution['freeze_authority'],
        task_count=16,task_ids=[entry['task_id'] for entry in benchmark['tasks']],
        models=config['models'],executor=execution['executor'],analysis=analysis,
        configuration_hash=digest(config),schedule_seed=execution['schedule_seed'],
        planned_trajectories=96,planned_responses=192,
        normalization='SHA-256 of file bytes with CRLF and CR normalized to LF; UTF-8 text artifacts',
        runtime={'python':platform.python_version(),'pyyaml':yaml.__version__},
        files={name:file_hash(confined(root,name)) for name in paths},
        tasks={entry['task_id']:entry['artifact_hashes'] for entry in benchmark['tasks']},
        external_registration=False,final_outcomes_observed=False)
    write_json(root/MANIFEST,manifest,immutable=True)
    return manifest


def verify_freeze(root=ROOT,require_committed=True):
    root=Path(root).resolve()
    path=root/MANIFEST
    if not path.exists(): raise ValueError('No freeze manifest; final-study calls are forbidden')
    manifest=read_json(path)
    if manifest['schema_version']!=1 or manifest['final_outcomes_observed'] is not False:
        raise ValueError('Invalid pre-outcome freeze declaration')
    expected=frozen_files(root)
    if set(manifest['files'])!=set(expected):
        raise ValueError('Frozen artifact set changed')
    for name,expected_hash in manifest['files'].items():
        if file_hash(confined(root,name))!=expected_hash:
            raise ValueError('Frozen artifact changed: '+name)
    config,analysis,execution=validate_plan(root)
    if (digest(config)!=manifest['configuration_hash'] or manifest['models']!=config['models']
            or manifest['analysis']!=analysis or manifest['executor']!=execution['executor']
            or manifest['schedule_seed']!=execution['schedule_seed']):
        raise ValueError('Frozen configuration metadata differs')
    benchmark=read_json(root/'config/benchmark.json')
    if manifest['task_ids']!=[entry['task_id'] for entry in benchmark['tasks']] or manifest['task_count']!=16:
        raise ValueError('Frozen membership differs')
    if manifest.get('tasks')!={entry['task_id']:entry['artifact_hashes'] for entry in benchmark['tasks']}:
        raise ValueError('Frozen task provenance differs')
    if manifest['runtime']!={'python':platform.python_version(),'pyyaml':yaml.__version__}:
        raise ValueError('Python/PyYAML runtime differs from freeze')
    git(root,'merge-base','--is-ancestor',manifest['git_commit'],'HEAD')
    if require_committed:
        committed=git(root,'show','HEAD:'+MANIFEST)
        if committed.replace(b'\r\n',b'\n')!=path.read_bytes().replace(b'\r\n',b'\n'):
            raise ValueError('Freeze manifest must match its committed version')
    return manifest


def planned_rows(root=ROOT):
    with (root/'data/run_manifest.csv').open(encoding='utf-8',newline='') as stream:
        return list(csv.DictReader(stream))


def authorize_final(task,condition,config,role,provider,runner,output,run_id,block_id,order,ledger):
    manifest=verify_freeze()
    matches=[row for row in planned_rows() if row['run_id']==run_id]
    if len(matches)!=1: raise ValueError('Run ID is not in the frozen schedule')
    row=matches[0]
    if (row['role']!=role or row['condition']!=condition or row['block_id']!=block_id
            or int(row['within_block_order'])!=order or row['task_id']!=task.metadata['task_id']
            or task.root.resolve()!=confined(ROOT,row['task_path']).resolve()
            or digest(config)!=manifest['configuration_hash'] or task.metadata['framing']!=row['framing']):
        raise ValueError('Requested trajectory differs from frozen schedule/configuration')
    if (provider.name!=row['provider'] or runner.backend!='docker' or ledger is None
            or runner.image!=manifest['executor']['image'] or runner.timeout!=manifest['executor']['timeout_seconds']
            or Path(output).resolve()!=(ROOT/'data/main').resolve()):
        raise ValueError('Final execution requires the frozen provider, Docker settings, shared budget, and data/main output')
    # Only the paced, re-verifying provider is permitted in final trajectories.
    from .run_frozen import FrozenProvider
    if not isinstance(provider,FrozenProvider):
        raise ValueError('Final calls require the frozen provider wrapper')
    execution=read_json(ROOT/'config/execution.json')
    if (ledger.path.resolve()!=(ROOT/'data/usage_ledger.json').resolve()
            or digest(ledger.config)!=digest(config)
            or ledger.spend_ceiling!=execution['collection']['budget_spend_ceiling_credits']
            or provider.config!=config['providers'][row['provider']]):
        raise ValueError('Final execution requires the frozen shared budget and provider settings')
    from .run_frozen import enforce_order
    enforce_order(row,planned_rows(),ROOT/'data/main')
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--create',action='store_true')
    args=parser.parse_args()
    manifest=create_freeze() if args.create else verify_freeze()
    print(f"Freeze {'created; commit freeze_manifest.json before any main call' if args.create else 'verified'}: {manifest['task_count']} tasks, 96 runs, source {manifest['git_commit']}")


if __name__=='__main__':
    main()
