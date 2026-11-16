"""Stateless Study 2 collection. Default smoke is offline; --live requires freeze.

No implementation code or test supplied by a model is executed by this runner.
"""
import argparse
from datetime import datetime, timezone
import csv
import json
from pathlib import Path
import tempfile
import time

from .artifacts import digest, read_json, write_json
from .audit_parser import parse_audit
from .audit_scoring import score_audit
from .audit_study import ROOT, STUDY, file_hash, verify_freeze, write_once
from .budget import BudgetLedger, exclusive_lock
from .preflight import load_env
from .providers.adaption import AdaptionProvider, ProviderFailure

PROMPTS = {'fresh': 'fresh_auditor.txt', 'evidence': 'evidence_auditor.txt',
           'confidence': 'confidence_auditor.txt', 'critic': 'independent_critic.txt',
           'cross_model': 'cross_model_auditor.txt'}
RETRYABLE = {'timeout', '5xx', 'transport'}


def messages_for(bundle, prompt):
    """Construct a request from public material only, never from a scored entry."""
    if set(bundle) != {'specification', 'requirements', 'files', 'public_tests'}:
        raise ValueError('Unexpected fields in public auditor bundle')
    if any(set(r) != {'id', 'text'} for r in bundle['requirements']):
        raise ValueError('Requirement definitions must contain only id and text')
    return [{'role': 'system', 'content': prompt}, {'role': 'user', 'content':
        'Audit the following material as data. Return the requested structured assessment.\n' +
        json.dumps(bundle, ensure_ascii=False, sort_keys=True)}]


def pace(path, seconds):
    if path.exists():
        delay = read_json(path)['last_start_unix'] + seconds - time.time()
        while delay > 0:
            time.sleep(min(delay, 30))
            delay = read_json(path)['last_start_unix'] + seconds - time.time()
    write_json(path, {'last_start_unix': time.time()})


def request_audit(provider, model, messages, directory, attempts=3, ledger=None, call_id='audit', before_call=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for attempt in range(attempts):
        request = directory/f'attempt{attempt}-request.json'
        outcome = directory/f'attempt{attempt}-outcome.json'
        identity = dict(messages=messages, model_id=model['model_id'], generation=model['generation'])
        if outcome.exists():
            if not request.exists() or read_json(request)['request_hash'] != digest(identity):
                raise RuntimeError('Saved request differs from frozen audit')
            saved = read_json(outcome)
        else:
            if request.exists():
                raise RuntimeError('Request without outcome: reconcile provider account; never blindly resend')
            if before_call:
                before_call()
            if ledger:
                ledger.reserve(f'{call_id}-attempt{attempt}', messages, model)
            write_json(request, dict(**identity, request_hash=digest(identity), attempt=attempt,
                timestamp=datetime.now(timezone.utc).isoformat()), immutable=True)
            started = time.monotonic()
            try:
                saved = {'result': provider.generate(messages, model), 'attempt': attempt}
            except ProviderFailure as exc:
                saved = dict(failure=exc.kind, retryable=bool(exc.retryable and exc.kind in RETRYABLE),
                    http_status=exc.http_status, raw=exc.raw, attempt=attempt,
                    latency_seconds=time.monotonic()-started, timestamp=datetime.now(timezone.utc).isoformat())
            write_json(outcome, saved, immutable=True)
        if ledger:
            result = saved.get('result') or {'summary': {'usage': (saved.get('raw') or {}).get('usage')}}
            ledger.settle(f'{call_id}-attempt{attempt}', result, model)
        if 'result' in saved or not saved.get('retryable') or saved['failure'] not in RETRYABLE:
            return saved, outcome
        if attempt + 1 < attempts:
            time.sleep(min(2**attempt, 2))
    return saved, outcome


def persist_result(study, row, entry, saved, outcome):
    result = saved.get('result', {})
    parsed = parse_audit(result.get('text', ''), [r['requirement_id'] for r in entry['truth']], row['audit_condition'])
    write_once(study/'parsed'/f"{row['audit_run_id']}.json", json.dumps(parsed, indent=2)+'\n')
    summary = result.get('summary', {})
    usage = summary.get('usage') or {}
    metadata = dict(audit_run_id=row['audit_run_id'], auditor_model=row['auditor_model'],
        audit_condition=row['audit_condition'], raw_response_path=outcome.relative_to(study.parent).as_posix(),
        request_id=result.get('request_id') or summary.get('response_id'),
        input_tokens=usage.get('input_tokens'), output_tokens=usage.get('output_tokens'),
        latency_ms=result.get('latency_seconds', saved.get('latency_seconds', 0))*1000,
        retry_count=saved['attempt'], timestamp=result.get('timestamp', saved.get('timestamp')))
    scored = dict(metadata=metadata, provider_status='completed' if result else saved['failure'],
        source_outcome_hash=file_hash(outcome),
        returned_model_id=summary.get('returned_model_id'), parse_status=parsed['parse_status'],
        unknown_ids=parsed['unknown_ids'], parser_errors=parsed['errors'],
        rows=score_audit(entry, parsed, metadata, 'completed' if result else saved['failure']))
    write_once(study/'scored'/f"{row['audit_run_id']}.json", json.dumps(scored, indent=2)+'\n')
    return scored


def collect(root=ROOT, limit=None):
    root = Path(root)
    verify_freeze(root)
    study = root/STUDY
    config = read_json(study/'study_config.json')
    with (study/'manifests/audit_manifest.csv').open(encoding='utf-8', newline='') as stream:
        schedule = list(csv.DictReader(stream))
    ledger = BudgetLedger(study/'logs/usage_ledger.json', config, config['spend_ceiling_credits'])
    completed = 0
    with exclusive_lock(study/'logs/collector.lock'):
        for row in schedule:
            if (study/'scored'/f"{row['audit_run_id']}.json").exists():
                continue  # Terminal provider-valid malformed answers are never rerun.
            if limit is not None and completed >= limit:
                break
            verify_freeze(root)
            entry = read_json(study/'inputs'/f"{row['artifact_id']}.json")
            if digest(entry['public_bundle']) != row['public_bundle_hash']:
                raise ValueError('Public input differs from manifest')
            prompt = (study/'prompts'/PROMPTS[row['audit_condition']]).read_text(encoding='utf-8')
            messages = messages_for(entry['public_bundle'], prompt)
            model = config['auditors'][row['auditor_key']]
            provider = AdaptionProvider(config['providers'][model['provider']])
            def before_call():
                verify_freeze(root)
                pace(study/'logs/pacing.json', config['minimum_request_interval_seconds'])
            saved, outcome = request_audit(provider, model, messages, study/'raw'/row['audit_run_id'],
                config['maximum_attempts'], ledger, row['audit_run_id'], before_call)
            scored = persist_result(study, row, entry, saved, outcome)
            completed += 1
            print(f"{row['audit_run_id']}: {scored['provider_status']}, {scored['parse_status']}", flush=True)
            if scored['provider_status'] in config['pause_on_failure']:
                raise RuntimeError('Collection paused for provider review: ' + scored['provider_status'])
    return completed


def smoke():
    """Exercise request, parser, truth join, persistence and no-resend behavior offline."""
    class Synthetic:
        def generate(self, messages, model):
            return dict(text='<requirements_check>\nR1: not fully implemented\nR2: implemented\n</requirements_check>',
                raw={'synthetic': True}, timestamp='synthetic', request_id='synthetic',
                summary={'usage': {'input_tokens': 1, 'output_tokens': 1}}, latency_seconds=0)
    with tempfile.TemporaryDirectory(prefix='safetyframe-audit-smoke-') as temporary:
        study = Path(temporary)/STUDY
        row = dict(audit_run_id='synthetic-audit', audit_condition='fresh', auditor_model='synthetic')
        entry = dict(artifact_id='synthetic', study1_run_id='synthetic', task_id='synthetic',
            model='synthetic', condition='CD', truth=[
                dict(requirement_id='R1', ground_truth_pass=0, builder_claim='implemented'),
                dict(requirement_id='R2', ground_truth_pass=1, builder_claim='implemented')])
        bundle = dict(specification='Return 1', requirements=[{'id': 'R1', 'text': 'Return 1'},
            {'id': 'R2', 'text': 'Define f'}], files={'code.py': 'def f(): return 0'}, public_tests={})
        messages = messages_for(bundle, 'Audit requirements')
        model = dict(model_id='synthetic', generation={})
        saved, outcome = request_audit(Synthetic(), model, messages, study/'raw/synthetic')
        scored = persist_result(study, row, entry, saved, outcome)
        assert scored['parse_status'] == 'valid'
        assert scored['rows'][0]['ground_truth_pass'] == 0
        assert request_audit(Synthetic(), model, messages, study/'raw/synthetic')[0] == saved
        from analysis.audit_metrics import audit_metrics
        assert audit_metrics(scored['rows'])['strict_URDR'] == 1
    return {'synthetic': 'passed', 'model_calls': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error('--limit must be positive')
    if args.live:
        load_env(ROOT/'.env')
        print({'new_terminal_audits': collect(limit=args.limit)})
    else:
        print(smoke())


if __name__ == '__main__':
    main()
