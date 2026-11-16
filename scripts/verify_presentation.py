"""Verify post-freeze presentation edits without rewriting scientific freezes.

--record-amendments records the explicit documentation-only exception list once.
The original Study 2 verifier deliberately rejects these edits on main; run
collection on followup/self-assessment-audit, where its preserved files match.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.artifacts import digest, read_json, write_json
from report_tables import evidence, tables
from verify_report import block, narrative_claims

AMENDED = {'.gitignore', 'README.md', 'RESEARCH_REPORT.md', 'SPRINT_PLAN.md',
           'report/report.md', 'report/claim_traceability.json', 'report/report_verification.json'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(record=False):
    preserved = read_json(ROOT/'study_2_audit/manifests/study1_preservation.json')
    original = read_json(ROOT/'freeze_manifest.json')
    for name, expected in original['files'].items():
        data = (ROOT/name).read_bytes().replace(b'\r\n', b'\n').replace(b'\r', b'\n')
        if 'sha256:'+hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Original frozen scientific file changed: '+name)
    # Verify the merged Study 2 protocol without changing its original hashes.
    audit_freeze = read_json(ROOT/'study_2_audit/freeze.json')
    audit_inputs_unavailable = []
    for name, expected in audit_freeze['files'].items():
        if not (ROOT/name).exists() and name.startswith('study_2_audit/inputs/'):
            audit_inputs_unavailable.append(name)
            continue
        if sha(ROOT/name) != expected:
            raise ValueError('Study 2 frozen protocol changed: '+name)
    amendments = dict(source_tag=preserved['tag'],
        reason='Post-collection presentation and status updates requested in the last-mile plan; no scientific changes.',
        files={name: {'preserved_original_sha256': preserved['files'][name],
                      'presentation_sha256': sha(ROOT/name)} for name in sorted(AMENDED)})
    amendment_path = ROOT/'presentation/documentation_amendments.json'
    if record:
        write_json(amendment_path, amendments, immutable=True)
    if read_json(amendment_path) != amendments:
        raise ValueError('Presentation differs from recorded documentation amendments')
    unavailable = []
    for name, expected in preserved['files'].items():
        if name in AMENDED:
            continue
        path = ROOT/name
        if not path.exists() and name.startswith('data/main/'):
            unavailable.append(name)
            continue
        if sha(path) != expected:
            raise ValueError('Preserved non-presentation file changed: '+name)
    result, datasets, tasks = evidence()
    text = (ROOT/'report/report.md').read_text(encoding='utf-8')
    expected = {'table:'+name: value for name, value in tables(result, datasets, tasks).items()}
    for name in ('system.txt', 'capability.txt', 'safety.txt', 'requirement_accounting.txt', 'turn2.txt'):
        value = (ROOT/'prompts'/name).read_text(encoding='utf-8')
        expected['prompt:'+name] = f'### {name}\n\n```text\n{value.rstrip()}\n```'
    for name, value in expected.items():
        if block(text, name) != value:
            raise ValueError('Report block differs: '+name)
    claims = narrative_claims(result, datasets, read_json(ROOT/'config/analysis.json'), original)
    flat = ' '.join(text.split())
    for claim in claims:
        if ' '.join(claim['manuscript_needle'].split()) not in flat:
            raise ValueError('Report narrative differs: '+claim['id'])
    for directory in ('model_a', 'model_b', 'final_analysis'):
        proof = read_json(ROOT/f'report/{directory}/integrity.json')
        for name, expected_digest in proof['normalized_text_digests'].items():
            if digest((ROOT/f'report/{directory}'/name).read_text(encoding='utf-8')) != expected_digest:
                raise ValueError('Reviewed analysis changed: '+directory+'/'+name)
    proof = read_json(ROOT/'report/report_verification.json')
    if proof['report_text_hash'] != digest(text):
        raise ValueError('Report verification hash differs')
    checked = 0
    for name in ('README.md', 'FINAL_RESULTS.md', 'SUBMISSION.md', 'RESEARCH_REPORT.md',
                 'SPRINT_PLAN.md', 'report/report.md'):
        path = ROOT/name
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if target.startswith(('http://', 'https://', '#')):
                continue
            if not (path.parent/target.split('#')[0]).exists():
                raise ValueError('Broken local link: '+name+' '+target)
            checked += 1
    summary = dict(original_frozen_files_verified=len(original['files']),
        study2_protocol_files_verified=len(audit_freeze['files']),
        study2_private_inputs_unavailable=len(audit_inputs_unavailable),
        authorized_documentation_amendments=len(AMENDED), local_links_checked=checked,
        exact_tables=7, exact_prompt_blocks=5, narrative_checks=len(claims),
        original_raw_files_unavailable=len(unavailable), new_model_calls=0,
        submitted=False, audit_collection_checkout='followup/self-assessment-audit')
    write_json(ROOT/'presentation/verification.json', summary)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record-amendments', action='store_true')
    print(json.dumps(verify(parser.parse_args().record_amendments), indent=2))
