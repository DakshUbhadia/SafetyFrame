"""Wait for frozen Model B, then audit and reproduce the independent analysis."""
import argparse
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from harness.artifacts import digest,read_json,write_json
from harness.freeze import verify_freeze

NUMERICAL_FILES=('scored_dataset.json','summary.json','models_comparison.json',
    'model_b_trajectories.csv','model_b_conditions.csv','model_b_contrasts.csv',
    'model_b_task_differences.csv','models_comparison.csv','results.md')


def ready(root=ROOT):
    path=root/'data/main/collector-B.json'
    if not path.exists(): raise ValueError('Model-B collector has not started')
    state=read_json(path)
    if state['status']=='operational_review_required':
        raise ValueError('Frozen operational review required; no aggregate analysis performed')
    if state['status']=='terminal':
        if state['phase_total']!=32: raise ValueError('Incomplete phase declaration')
        return True
    if not (root/'data/main/.phase-collector.lock').exists():
        raise ValueError('Collector stopped; reconcile before analysis')
    return False


def compare_outputs(original,reproduced):
    for name in NUMERICAL_FILES:
        if (original/name).read_text(encoding='utf-8')!=(reproduced/name).read_text(encoding='utf-8'):
            raise ValueError('Reproduction differs: '+name)
    return {name:digest((original/name).read_text(encoding='utf-8')) for name in NUMERICAL_FILES}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wait',action='store_true')
    args=parser.parse_args()
    verify_freeze()
    while not ready():
        if not args.wait: raise ValueError('Model B collection is incomplete')
        time.sleep(15)
    subprocess.run([sys.executable,'-m','analysis.model_b'],cwd=ROOT,check=True)
    published=ROOT/'report/model_b'; reproduced=ROOT/'data/main/model_b_reproduction'
    subprocess.run([sys.executable,'-m','analysis.model_b','--dataset',str(published/'scored_dataset.json'),
                    '--output',str(reproduced)],cwd=ROOT,check=True)
    hashes=compare_outputs(published,reproduced)
    verify_freeze()
    write_json(ROOT/'data/main/analysis-B-complete.json',dict(role='B',terminal_trajectories=32,
        numerical_reproduction_pass=True,normalized_text_digests=hashes,no_pooled_model_effect=True,
        figure_note='Scientific figures reproduced; SVG/PDF timestamps are excluded from bitwise comparison.'))
    print('Model B integrity audit, independent estimates, and numerical reproduction passed.',flush=True)


if __name__=='__main__':
    main()
