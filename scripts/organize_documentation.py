"""One-time documentation moves with byte-preserved source snapshots.

Preview by default. --apply moves tracked documents with Git and rewrites only
relative Markdown link targets in readable documentation. Scientific records
and frozen executable code are never rewritten.
"""
import argparse
import hashlib
import json
import posixpath
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
METHODS = ['02_EXPERIMENT_PROTOCOL.md', '05_PROMPT_PROTOCOL.md', '08_DATA_DICTIONARY.md',
           '09_SCORING_ANALYSIS_PLAN.md', '10_SELF_ASSESSMENT_RUBRIC.md', 'HARNESS.md',
           'RENDERING.md', 'SPECIFICATION_v4.md', 'FINAL_ANALYSIS.md', 'RESEARCH_REPORT.md']
ARCHIVE = ['01_PREREGISTRATION_TEMPLATE.md', '03_TASK_AUTHORING_GUIDE.md',
           '04_TASK_VALIDATION_CHECKLIST.md', '06_MODEL_PROVIDER_SETUP.md', '07_RUNBOOK.md',
           '11_DEVIATION_LOG_TEMPLATE.md', '13_REPORT_TEMPLATE.md', '15_REPRODUCIBILITY_CHECKLIST.md',
           '18_FREEZE_MANIFEST_GUIDE.md', 'PILOTS.md', 'SETUP.md', 'SPRINT_PLAN.md', 'SUBMISSION.md']
LINK = re.compile(r'(\]\()([^\s)]+)(\))')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    moves = {name: 'docs/methods/'+name for name in METHODS}
    moves.update({name: 'docs/archive/'+name for name in ARCHIVE})
    moves.update({p.relative_to(ROOT).as_posix(): 'docs/archive/'+p.relative_to(ROOT).as_posix()
                  for p in sorted((ROOT/'templates').rglob('*')) if p.is_file()})
    if not args.apply:
        print(json.dumps(moves, indent=2))
        return
    destination = ROOT/'presentation/documentation_cleanup.json'
    if destination.exists():
        raise ValueError('Cleanup already recorded; never overwrite its provenance')
    source_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    originals, snapshots = {}, {}
    snapshot_root = ROOT/'docs/archive/source_snapshots'
    snapshot_root.mkdir(parents=True, exist_ok=True)
    (snapshot_root/'.gitattributes').write_text('* -text\n', encoding='utf-8')

    def preserve(name):
        if name in originals:
            return
        data = (ROOT/name).read_bytes()
        path = 'docs/archive/source_snapshots/'+name+'.txt'
        target = ROOT/path
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream:
            stream.write(data)
        originals[name] = path
        snapshots[path] = sha(data)

    for name in ('.gitignore', 'README.md', 'RESEARCH_REPORT.md', 'SPRINT_PLAN.md',
                 'report/report.md', 'report/claim_traceability.json', 'report/report_verification.json'):
        preserve(name)
    for name, target in moves.items():
        if name.endswith('.md'):
            preserve(name)
        else:
            originals[name] = target
            snapshots[target] = sha((ROOT/name).read_bytes())
        (ROOT/target).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', 'mv', '--', name, target], cwd=ROOT, check=True)
    frozen = json.loads((ROOT/'freeze_manifest.json').read_text(encoding='utf-8'))['files']
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    reverse = {target: source for source, target in moves.items()}
    edits = {}
    for current in tracked:
        if not current.endswith('.md') or current.startswith(('study_2_audit/', 'report/model_a/',
                'report/model_b/', 'report/final_analysis/')) or current in frozen:
            continue
        old = reverse.get(current, current)
        path = ROOT/current
        text = path.read_text(encoding='utf-8')

        def replace(match):
            target = match[2]
            if target.startswith(('#', 'http:', 'https:', 'mailto:')):
                return match[0]
            file, sep, anchor = target.partition('#')
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(old), file))
            moved = moves.get(resolved, resolved)
            if resolved == 'templates':
                moved = 'docs/archive/templates'
            relative = posixpath.relpath(moved, posixpath.dirname(current) or '.')
            return match[1]+relative+(sep+anchor if sep else '')+match[3]

        updated = LINK.sub(replace, text)
        if updated != text:
            if old not in originals:
                preserve(old)
            path.write_text(updated, encoding='utf-8', newline='\n')
            edits[current] = sha(path.read_bytes())
    destination.write_text(json.dumps(dict(source_commit=source_commit,
        policy='Exact original bytes retained; only readable documentation link targets relocated. Frozen manifests unchanged.',
        moves=moves, originals=originals, snapshot_sha256=snapshots, link_rewritten_files=edits), indent=2)+'\n',
        encoding='utf-8')
    print(f'Moved {len(moves)} files; preserved {len(originals)} sources; updated links in {len(edits)} documents.')


if __name__ == '__main__':
    main()
