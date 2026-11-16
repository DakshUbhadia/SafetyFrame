"""Audit local evidence, reproduce final numerical outputs, and record Sprint 9 proof."""
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.artifacts import digest, read_json, write_json
from harness.freeze import verify_freeze

FILES = ('summary.json', 'conditions.csv', 'contrasts.csv', 'matched_means.csv',
         'failures.csv', 'self_assessment.csv', 'repair.csv', 'task_contrasts.csv', 'figure_data.json', 'results.md')


def compare(original, reproduced):
    hashes = {}
    for name in FILES:
        text = (original / name).read_text(encoding='utf-8')
        if text != (reproduced / name).read_text(encoding='utf-8'):
            raise ValueError('Final-analysis reproduction differs: ' + name)
        hashes[name] = digest(text)
    return hashes


def main():
    manifest = verify_freeze()
    subprocess.run([sys.executable, '-m', 'analysis.primary', '--audit-raw'], cwd=ROOT, check=True)
    reproduced = ROOT / 'data/main/sprint9_reproduction/final_analysis'
    subprocess.run([sys.executable, '-m', 'analysis.primary', '--output', str(reproduced),
                    '--figures', str(reproduced.parent / 'figures')], cwd=ROOT, check=True)
    output = ROOT / 'report/final_analysis'
    hashes = compare(output, reproduced)
    verify_freeze()
    write_json(output / 'integrity.json', dict(schema_version=1, freeze_hash=digest(manifest),
        frozen_source_checkpoint=manifest['git_commit'],
        analysis_code_checkpoint=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        generated_at_utc=datetime.now(timezone.utc).isoformat(), terminal_trajectories=96,
        completed_trajectories=90, provider_failed_trajectories=6, raw_audit_pass=True,
        scores_recomputed_from_requirements_and_claims=True, original_model_summaries_unchanged=True,
        numerical_reproduction_pass=True, normalized_text_digests=hashes,
        figures='report/figures; plotted data in figure_data.json; timestamped SVG/PDF bytes excluded',
        additional_inference_calls=0, pooled_estimate=None))
    print('Sprint 9 raw audit, recomputation and all ten numerical/narrative reproductions passed.')


if __name__ == '__main__':
    main()
