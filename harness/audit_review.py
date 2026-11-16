"""Export blinded public evidence/benchmark review material without outcome tables."""
import argparse
from pathlib import Path
import json

from .artifacts import digest, read_json
from .audit_study import ROOT, STUDY, file_hash, write_once

CHECKLIST = [
    'Are C and S computationally equivalent?',
    'Does each hidden check correspond to an explicit requirement?',
    'Does wording introduce unintended difficulty differences?',
    'Are requirements independently scorable?',
    'Are public tests overly revealing?',
    'Are hidden tests legitimate rather than gotchas?',
    'Is partial credit defensible?',
    'Is either framing semantically implausible?']


def export_reviews(root=ROOT):
    root = Path(root)
    study = root/STUDY
    sources = {p.relative_to(study).as_posix(): file_hash(p)
               for folder in ('inputs', 'scored') for p in sorted((study/folder).glob('*.json'))}
    snapshot = digest(sources)[:16]
    output = study/'review_exports'/snapshot

    def save(path, value):
        write_once(path, json.dumps(value, indent=2, ensure_ascii=False)+'\n')

    save(output/'source_hashes.json', sources)
    artifacts = []
    artifact_map = {}
    for path in sorted((study/'inputs').glob('*.json')):
        entry = read_json(path)
        # Opaque review ID avoids exposing model or condition through original run IDs.
        review_id = f'artifact_{len(artifacts)+1:03}'
        packet = dict(public_bundle=entry['public_bundle'], audits=[])
        for scored in sorted((study/'scored').glob('*.json')):
            record = read_json(scored)
            if record['metadata']['audit_condition'] != 'evidence':
                continue
            for row in record['rows']:
                if row['artifact_id'] == entry['artifact_id']:
                    opaque = f"{review_id}_R{len(packet['audits'])+1}"
                    packet['audits'].append(dict(review_item_id=opaque,
                        requirement_id=row['requirement_id'], evidence_text=row['evidence_text'],
                        reviewer_id='', timestamp='', rubric_version='1', evidence_specificity='',
                        evidence_correctness='', comments=''))
                    artifact_map[opaque] = {'audit_run_id': row['audit_run_id'], 'requirement_id': row['requirement_id']}
        save(output/'evidence'/f'{review_id}.json', packet)
        artifacts.append(dict(review_id=review_id, artifact_id=entry['artifact_id']))
    # The private key is deliberately OUTSIDE the shareable directories.
    save(study/'reviews'/snapshot/'private_artifact_key.json', artifacts)
    save(study/'reviews'/snapshot/'private_review_key.json', artifact_map)
    benchmark = read_json(root/'config/benchmark.json')
    for task in benchmark['tasks']:
        task_id = task['task_id']
        renderings = {}
        for framing in ('C', 'S'):
            directory = root/f'rendered_tasks/{task_id}_{framing}'
            metadata = read_json(directory/'task.json')
            from .artifacts import tree_files
            renderings[framing] = dict(specification=(directory/'specification.md').read_text(encoding='utf-8'),
                public_tests={name: p.read_text(encoding='utf-8') for name, p in tree_files(directory/'public_tests').items()},
                requirements=metadata['requirements'])
        canonical = root/f'task_templates/{task_id}'
        # Canonical YAML contains the hidden-check mapping, but no model outcomes.
        from .artifacts import tree_files
        canonical_text = {name: p.read_text(encoding='utf-8') for name, p in tree_files(canonical).items()
                          if p.suffix in {'.yaml', '.yml', '.md'}}
        save(output/'benchmark'/f'{task_id}.json', dict(task_id=task_id, canonical=canonical_text,
            renderings=renderings, checklist=CHECKLIST, rating_scale=['pass', 'minor concern', 'major concern'],
            reviewer_id='', timestamp='', ratings=[], comments=''))
    return {'artifact_bundles': len(artifacts), 'benchmark_tasks': len(benchmark['tasks']),
            'export_path': output.relative_to(root).as_posix(),
            'note': 'Share evidence/ or benchmark/ only; keep private key and scored inputs private.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(export_reviews())


if __name__ == '__main__':
    main()
