"""Wait for the terminal Model-A phase, then audit, analyze, and reproduce locally."""
import argparse
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from harness.artifacts import digest,read_json,write_json
from harness.freeze import verify_freeze

NUMERICAL_FILES=('scored_dataset.json','summary.json','model_a_trajectories.csv',
    'model_a_conditions.csv','model_a_contrasts.csv','model_a_self_assessment.csv',
    'model_a_task_differences.csv','results.md')


def ready(root=ROOT):
    progress=root/'data/main/collector-A.json'
    if not progress.exists(): raise ValueError('Model-A collector has not started')
    state=read_json(progress)
    if state['status']=='operational_review_required':
        raise ValueError('Collection requires operational review; no aggregate analysis performed')
    if state['status']=='terminal':
        if state['phase_total']!=64: raise ValueError('Incomplete phase declaration')
        return True
    if not (root/'data/main/.phase-collector.lock').exists():
        raise ValueError('Collector stopped before terminal declaration; reconcile before analysis')
    return False


def compare_outputs(original,reproduced):
    for name in NUMERICAL_FILES:
        if (original/name).read_text(encoding='utf-8')!=(reproduced/name).read_text(encoding='utf-8'):
            raise ValueError('Reproduction differs: '+name)
    return {name:digest((original/name).read_text(encoding='utf-8')) for name in NUMERICAL_FILES}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wait',action='store_true',help='Wait for the active serial collector')
    args=parser.parse_args()
    verify_freeze()
    while not ready():
        if not args.wait: raise ValueError('Model-A phase still running; no aggregate analysis performed')
        time.sleep(15)
    subprocess.run([sys.executable,'-m','analysis.model_a'],cwd=ROOT,check=True)
    published=ROOT/'report/model_a'
    reproduced=ROOT/'data/main/model_a_reproduction'
    subprocess.run([sys.executable,'-m','analysis.model_a','--dataset',str(published/'scored_dataset.json'),
                    '--output',str(reproduced)],cwd=ROOT,check=True)
    hashes=compare_outputs(published,reproduced)
    verify_freeze()
    write_json(ROOT/'data/main/analysis_complete.json',dict(role='A',terminal_trajectories=64,
        numerical_reproduction_pass=True,normalized_text_digests=hashes,
        figure_note='Plots are reproduced; SVG/PDF timestamps are not used for bitwise comparison.'))
    print('Model A: raw/scored integrity audit and numerical reproduction passed; results are in report/model_a.',flush=True)


if __name__=='__main__':
    main()
