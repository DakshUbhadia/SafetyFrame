"""Requirement-level Study 2 schema; hidden outcomes join only after inference."""
from .audit_parser import STATUSES


def score_audit(entry, parsed, metadata, provider_status='completed'):
    rows = []
    for requirement in entry['truth']:
        rid = requirement['requirement_id']
        item = parsed['requirements'][rid]
        rows.append(dict(study_id='study_2_audit', audit_run_id=metadata['audit_run_id'],
            artifact_id=entry['artifact_id'], study1_run_id=entry['study1_run_id'],
            task_id=entry['task_id'], builder_model=entry['model'], builder_condition=entry['condition'],
            auditor_model=metadata['auditor_model'], audit_condition=metadata['audit_condition'],
            requirement_id=rid, ground_truth_pass=requirement['ground_truth_pass'],
            builder_claim=requirement['builder_claim'], auditor_claim=item['status'],
            probability_fully_satisfied=item['probability_fully_satisfied'], evidence_text=item['evidence_text'],
            evidence_specificity='missing' if not item['evidence_text'] else None,
            evidence_correctness=None, provider_status=provider_status, parse_status=parsed['parse_status'],
            requirement_parse_errors=item['errors'], **{k: metadata.get(k) for k in (
                'raw_response_path', 'request_id', 'input_tokens', 'output_tokens', 'latency_ms',
                'retry_count', 'timestamp')}))
    return rows


def builder_rows(entries):
    rows = []
    for entry in entries:
        # C/S never elicited builder claims: no invented builder baseline.
        if entry['condition'] not in {'CD', 'SD'}:
            continue
        parsed = {'parse_status': entry['builder_parse_status'], 'requirements': {
            r['requirement_id']: {'status': r['builder_claim'], 'probability_fully_satisfied': None,
                                  'evidence_text': None, 'errors': []} for r in entry['truth']}}
        rows.extend(score_audit(entry, parsed, dict(audit_run_id='builder-' + entry['artifact_id'],
            auditor_model=entry['model'], audit_condition='builder')))
    return rows
