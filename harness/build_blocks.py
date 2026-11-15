"""Deterministic task/model blocks and immutable planned run schedule; no inference."""
import argparse
import csv
import io
import random
from pathlib import Path

from .artifacts import read_json
from .preflight import ROOT,validate_config
from .validate_benchmark import verify_inventory

FIELDS=['run_id','block_id','block_order','execution_order','phase','role','task_id','task_family',
        'model_id','provider','condition','framing','requirement_accounting','within_block_order','task_path','status']


def build_rows(config,benchmark,seed):
    validate_config(config)
    tasks=sorted(benchmark['tasks'],key=lambda t:t['task_id'])
    if len(tasks)!=16 or len({t['task_id'] for t in tasks})!=16:
        raise ValueError('Expected the accepted sixteen-task benchmark')
    rng=random.Random(seed)
    blocks=[(t,role) for t in tasks for role in ('A','B')]
    rng.shuffle(blocks)
    planned=[]
    for block_order,(task,role) in enumerate(blocks,1):
        model=config['models'][role]
        conditions=list(model['conditions']); rng.shuffle(conditions)
        for order,condition in enumerate(conditions,1):
            framing='capability' if condition.startswith('C') else 'safety'
            planned.append(dict(run_id=f"main-{role}-{task['task_id']}-{condition}",
                block_id=f"block-{role}-{task['task_id']}",block_order=block_order,phase=role,role=role,
                task_id=task['task_id'],task_family=task['family'],model_id=model['model_id'],
                provider=model['provider'],condition=condition,framing=framing,
                requirement_accounting=condition in ('CD','SD'),within_block_order=order,
                task_path=f"rendered_tasks/{task['task_id']}_{'C' if condition.startswith('C') else 'S'}",status='planned'))
    rows=[r for role in ('A','B') for r in planned if r['role']==role]
    for order,row in enumerate(rows,1): row['execution_order']=order
    return rows


def csv_text(rows):
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=FIELDS,lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    return stream.getvalue()


def schedule_text(root=ROOT):
    config=read_json(root/'config/study.json')
    benchmark=read_json(root/'config/benchmark.json')
    settings=read_json(root/'config/execution.json')
    return csv_text(build_rows(config,benchmark,settings['schedule_seed']))


def write_schedule(root=ROOT):
    verify_inventory()
    path=root/'data/run_manifest.csv'; text=schedule_text(root)
    if path.exists():
        if path.read_text(encoding='utf-8')!=text: raise ValueError('Existing planned schedule differs; do not overwrite')
    else:
        path.write_text(text,encoding='utf-8',newline='\n')
    return path


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    path=write_schedule()
    print(f'{path}: 32 blocks, 64 Model A + 32 Model B trajectories, 192 responses; no inference started')


if __name__=='__main__':
    main()
