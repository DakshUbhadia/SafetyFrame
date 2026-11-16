"""Verify the manuscript against reviewed evidence; optionally refresh marked tables."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from harness.artifacts import digest, read_json, write_json
from harness.freeze import verify_freeze
from report_tables import evidence, fmt, interval, tables


def block(text, name):
    pattern = re.escape(f'<!-- BEGIN {name} -->') + r'\n(.*?)\n?' + re.escape(f'<!-- END {name} -->')
    matches = re.findall(pattern, text, re.S)
    if len(matches) != 1:
        raise ValueError('Expected exactly one manuscript block: ' + name)
    return matches[0].strip()


def replace(text, name, value):
    start = f'<!-- BEGIN {name} -->'; end = f'<!-- END {name} -->'
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError('Invalid block: ' + name)
    a = text.index(start) + len(start); b = text.index(end, a)
    return text[:a] + '\n' + value + '\n' + text[b:]


def narrative_claims(result, datasets, config, manifest):
    """Source-derived needles check prose too, including counts absent from headline tables."""
    def contrast(name, kind='primary'):
        return next(r for r in result['contrasts'] if r['contrast'] == name and r['estimand'] == kind)
    claims = []
    def add(identifier, needle, source, value):
        claims.append(dict(id=identifier, manuscript_needle=needle, evidence=source, value=value))
    for name in ('BaselineSafetyGap_A', 'BaselineSafetyGap_B', 'DisclosureFramingInteraction_A',
                 'DisclosureEffect_C_A', 'DisclosureEffect_S_A'):
        r = contrast(name)
        add(name, interval(r).split(', N=')[0], f'final_analysis/summary.json:contrasts[{name},primary]', r)
    for name, kind in [('DisclosureFramingInteraction_A', 'provider_utility'),
                       ('DisclosureFramingInteraction_A', 'valid_format'), ('BaselineSafetyGap_B', 'provider_utility')]:
        r = contrast(name, kind)
        add(name + '_' + kind, interval(r).split(', N=')[0], f'final_analysis/summary.json:contrasts[{name},{kind}]', r)
    cond = result['conditions']; planned = sum(r['planned'] for r in cond); completed = sum(r['completed'] for r in cond)
    add('study_terminal_counts', f'All {planned} planned trajectories are terminal: {completed} completed',
        'final_analysis/summary.json:sum(conditions.planned/completed)', [planned, completed])
    records = [r for d in datasets.values() for r in d['records']]
    observed = sum(len(r['turns']) for r in records)
    attempts = sum(len(r['attempts']) for r in records)
    retries = sum(r['trajectory']['retry_count'] for r in records)
    unknown = sum(a['estimated_cost'] is None for r in records for a in r['attempts'])
    add('observed_responses', f'{observed} observed responses', 'model_a/b/scored_dataset.json:sum(len(turns))', observed)
    add('attempts_retries_unknown', f'{attempts} attempts and {retries} retries, with {unknown} outcomes lacking full usage',
        'model_a/b/scored_dataset.json:attempts and retry/usage fields', [attempts, retries, unknown])
    diagnostic = result['model_b_response_diagnostics']
    add('budget_exhaustion', f"{diagnostic['reasoning_only_budget_exhaustions']}/{diagnostic['observed_responses']} observed replies",
        'final_analysis/summary.json:model_b_response_diagnostics', diagnostic)
    add('budget_mismatches', 'extraction mismatches were zero',
        'final_analysis/summary.json:model_b_response_diagnostics.extraction_mismatches', diagnostic['extraction_mismatches'])
    if diagnostic['extraction_mismatches'] != 0: raise ValueError('Mismatch count no longer supports prose')
    bformat = [r for r in result['failures'] if r['model'] == 'B' and r['turn'] == 2]
    failures = sum(r['format_failures'] for r in bformat); total = sum(r['observed'] for r in bformat)
    add('b_final_formats', f'{failures}/{total} Turn-2 format failures', 'final_analysis/summary.json:failures[B,turn2]', [failures, total])
    valid = contrast('BaselineSafetyGap_B', 'valid_format')
    if valid['tasks'] != 1 or valid['estimate'] != 0 or valid['lower'] is not None or valid['upper'] is not None:
        raise ValueError('Valid-format narrative no longer matches')
    add('one_valid_b_pair', 'only one valid-format pair, whose gap was zero and interval undefined',
        'final_analysis/summary.json:contrasts[BaselineSafetyGap_B,valid_format]', valid)
    a = read_json(ROOT / 'report/model_a/summary.json')
    assessment = a['self_assessment']
    claimed = sum(assessment[c]['2']['counts']['claimed_implemented'] for c in ('CD', 'SD'))
    failed = sum(assessment[c]['2']['counts']['actual_failed_requirements'] for c in ('CD', 'SD'))
    add('all_accounting_claims', f'All {claimed} final accounting entries claimed implemented',
        'model_a/summary.json:self_assessment.CD/SD.2.counts.claimed_implemented', claimed)
    add('failed_requirements', f'All {failed} failed artifact requirements',
        'model_a/summary.json:self_assessment.CD/SD.2.counts.actual_failed_requirements', failed)
    for c in ('CD', 'SD'):
        counts = assessment[c]['2']['counts']
        if counts['failed_claimed_implemented'] != counts['actual_failed_requirements']:
            raise ValueError('All-failed-claimed assertion no longer holds')
    matched = contrast('DisclosureFramingInteraction_A')['matched_condition_means']
    add('interaction_matched_means', '/'.join(fmt(matched[c]) for c in ('C', 'S', 'CD', 'SD')),
        'final_analysis/summary.json:interaction primary matched_condition_means', matched)
    means = contrast('BaselineSafetyGap_B')['matched_condition_means']
    add('b_matched_means', f"{fmt(means['C'])} and {fmt(means['S'])}",
        'final_analysis/summary.json:B baseline matched_condition_means', means)
    b_s = next(r for r in result['repair'] if r['model'] == 'B' and r['condition'] == 'S')
    add('b_turn1_mean', f"its all-observed Turn-1 mean is {fmt(b_s['turn1_mean_all_observed'])}",
        'final_analysis/summary.json:repair[B,S]', b_s)
    for role in ('A', 'B'):
        values = [r['value'] for r in result['task_contrasts'] if r['model'] == role and r['estimand'] == 'primary'
                  and r['contrast'] == f'BaselineSafetyGap_{role}' and r['value'] is not None]
        counts = [sum(v == 0 for v in values), sum(v > 0 for v in values), sum(v < 0 for v in values)]
        expected = [13, 1, 2] if role == 'A' else [10, 0, 3]
        if counts != expected: raise ValueError('Task distribution prose changed: ' + role)
        add('task_distribution_' + role, 'Thirteen tasks tied, one favored C and two favored S' if role == 'A'
            else 'ten pairs tied, three favored S and none favored C',
            'final_analysis/summary.json:task_contrasts[baseline,primary]', counts)
    add('bootstrap_resamples', f"{config['bootstrap']['resamples']:,} paired task-bootstrap resamples",
        '../config/analysis.json:bootstrap.resamples', config['bootstrap']['resamples'])
    add('bootstrap_seed', f"seed {config['bootstrap']['seed']}", '../config/analysis.json:bootstrap.seed', config['bootstrap']['seed'])
    add('schedule_seed', f"Schedule seed is {read_json(ROOT/'config/execution.json')['schedule_seed']}",
        '../config/execution.json:schedule_seed', read_json(ROOT/'config/execution.json')['schedule_seed'])
    add('freeze_checkpoint', manifest['git_commit'], '../freeze_manifest.json:git_commit', manifest['git_commit'])
    return claims


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh-tables', action='store_true', help='Update only marked tables and verbatim prompt blocks')
    args = parser.parse_args()
    manifest = verify_freeze(); config = read_json(ROOT / 'config/analysis.json')
    result, datasets, tasks = evidence()
    path = ROOT / 'report/report.md'; text = path.read_text(encoding='utf-8')
    expected = {'table:' + name: value for name, value in tables(result, datasets, tasks).items()}
    for name in ('system.txt', 'capability.txt', 'safety.txt', 'requirement_accounting.txt', 'turn2.txt'):
        value = (ROOT / 'prompts' / name).read_text(encoding='utf-8')
        expected['prompt:' + name] = f'### {name}\n\n```text\n{value.rstrip()}\n```'
    if args.refresh_tables:
        for name, value in expected.items(): text = replace(text, name, value)
        path.write_text(text, encoding='utf-8', newline='\n')
    for name, value in expected.items():
        if block(text, name) != value: raise ValueError('Manuscript block differs from evidence: ' + name)
    # Check all upstream numerical/narrative evidence, not just the summaries used above.
    for directory in ('model_a', 'model_b', 'final_analysis'):
        proof = read_json(ROOT / f'report/{directory}/integrity.json')
        for name, expected_digest in proof['normalized_text_digests'].items():
            if digest((ROOT / f'report/{directory}' / name).read_text(encoding='utf-8')) != expected_digest:
                raise ValueError('Reviewed analysis changed: ' + directory + '/' + name)
    abstract = text.split('## Abstract\n', 1)[1].split('\n## 1.', 1)[0].strip()
    word_count = len(abstract.split())
    if not 150 <= word_count <= 250: raise ValueError('Abstract length: ' + str(word_count))
    for heading in ('1. Introduction', '2. Related work', '3. Methods', '4. Results', '5. Discussion', '6. Limitations', '7. Conclusion'):
        if '## ' + heading not in text: raise ValueError('Missing section: ' + heading)
    order = [text.index('### 4.' + str(i)) for i in range(1, 6)]
    if order != sorted(order): raise ValueError('Result channels are out of order')
    if re.search(r'\[(?:N\]|TODO\b|Report Model|Direct findings\.|Narrow claim\.)', text):
        raise ValueError('Unfilled report placeholder')
    claims = narrative_claims(result, datasets, config, manifest)
    flat = ' '.join(text.split())
    for claim in claims:
        if ' '.join(claim['manuscript_needle'].split()) not in flat:
            raise ValueError('Narrative does not match source: ' + claim['id'])
    generated = {'claim_traceability.json', 'report_verification.json'}
    checked_links = []
    for target in re.findall(r'\]\(([^)]+)\)', text):
        if target.startswith(('https://', 'http://', '#')): continue
        file = (path.parent / target.split('#')[0]).resolve()
        if not file.exists() and file.name not in generated: raise ValueError('Broken local link: ' + target)
        checked_links.append(target)
    write_json(ROOT / 'report/claim_traceability.json', dict(schema_version=1,
        report_text_hash=digest(text), narrative_claims=claims,
        table_evidence={name: digest(value) for name, value in expected.items()},
        scope='Source-derived narrative checks plus exact rendered tables; manual review still required.'))
    write_json(ROOT / 'report/report_verification.json', dict(schema_version=1,
        generated_at_utc=datetime.now(timezone.utc).isoformat(), report_text_hash=digest(text),
        source_checkpoint=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        freeze_hash=digest(manifest), abstract_words=word_count, exact_tables=7, exact_prompt_blocks=5,
        narrative_checks=len(claims), local_links_checked=len(checked_links),
        original_analysis_releases_unchanged=True, numerical_analysis_unchanged=True,
        author='Daksh Ubhadia', affiliation='Independent researcher', author_metadata_user_confirmed=True,
        additional_inference_calls=0, pdf_exported=False, page_limit_verified=False,
        official_template_layout_verified=False, submitted=False,
        remaining='Sprint 11: official-template layout, PDF/page inspection, clean-environment release checks and submission.'))
    print(f'Report verified: {word_count}-word abstract, 7 evidence tables, 5 exact prompts, {len(claims)} narrative checks; frozen results unchanged.')


if __name__ == '__main__':
    main()
