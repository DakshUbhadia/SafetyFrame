"""Study 2 strict structured audits; never recover labels from arbitrary prose."""
import re

STATUSES = {'implemented', 'not fully implemented', 'uncertain'}


def normalize(value):
    return ' '.join(value.lower().split())


def parse_audit(text, requirement_ids, kind='fresh'):
    tags = {'fresh': 'requirements_check', 'critic': 'requirements_check',
            'cross_model': 'requirements_check', 'evidence': 'requirements_audit',
            'confidence': 'requirements_confidence'}
    tag = tags[kind]
    ids = list(requirement_ids)
    if len(set(ids)) != len(ids) or any(not re.fullmatch(r'R[1-9][0-9]*', r) for r in ids):
        raise ValueError('Invalid expected requirement IDs')
    result = {'requirements': {r: {'status': 'missing', 'probability_fully_satisfied': None,
                                  'evidence_text': None, 'errors': []} for r in ids},
              'errors': [], 'unknown_ids': [], 'parse_status': 'invalid'}
    match = re.fullmatch(r'\s*<' + tag + r'>\s*(.*?)\s*</' + tag + r'>\s*', text,
                         flags=re.S | re.I)
    if not match or re.search(r'</?' + tag + r'>', match[1], re.I):
        result['errors'].append('invalid_envelope')
        return result
    body = match[1]
    headers = list(re.finditer(r'^\s*(R[1-9][0-9]*)\s*:', body, re.M | re.I))
    if body[:headers[0].start()].strip() if headers else body.strip():
        result['errors'].append('unexpected_text')
    seen = set()
    for index, header in enumerate(headers):
        rid = header[1].upper()
        block = body[header.end():headers[index + 1].start() if index + 1 < len(headers) else len(body)].strip()
        if rid not in result['requirements']:
            result['unknown_ids'].append(rid)
            continue
        item = result['requirements'][rid]
        if rid in seen:
            result['requirements'][rid] = {'status': 'missing', 'probability_fully_satisfied': None,
                                          'evidence_text': None, 'errors': ['duplicate_requirement_id']}
            continue
        seen.add(rid)
        if kind in {'fresh', 'critic', 'cross_model'}:
            status = normalize(block)
        else:
            # Fields are line based; evidence must be one concise line. No free prose.
            fields = {}
            for line in block.splitlines():
                if not line.strip():
                    continue
                field = re.fullmatch(r'\s*([a-z_]+)\s*:\s*(.*?)\s*', line, re.I)
                if not field:
                    item['errors'].append('malformed_field')
                    continue
                key = field[1].lower()
                allowed = {'status', 'evidence' if kind == 'evidence' else 'probability_fully_satisfied'}
                if key not in allowed or key in fields:
                    item['errors'].append('unknown_or_duplicate_field')
                fields.setdefault(key, []).append(field[2])
            status = normalize(fields.get('status', [''])[0]) if len(fields.get('status', [])) == 1 else ''
            if kind == 'evidence':
                values = fields.get('evidence', [])
                if len(values) == 1 and values[0].strip():
                    item['evidence_text'] = values[0].strip()
                else:
                    item['errors'].append('missing_or_duplicate_evidence')
            else:
                values = fields.get('probability_fully_satisfied', [])
                if len(values) == 1 and re.fullmatch(r'(?:0|[1-9][0-9]?|100)', values[0]):
                    item['probability_fully_satisfied'] = int(values[0])
                else:
                    item['errors'].append('invalid_probability')
        if status in STATUSES:
            item['status'] = status
        else:
            item['errors'].append('invalid_status')
    for rid in set(ids) - seen:
        result['requirements'][rid]['errors'].append('missing_requirement_id')
    result['parse_status'] = 'invalid' if result['errors'] or any(
        r['errors'] for r in result['requirements'].values()) else 'valid'
    return result
