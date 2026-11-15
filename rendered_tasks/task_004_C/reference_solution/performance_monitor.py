"""Utilities for AI capability research capability_run processing."""
import copy
import math

def _impl_convert_score(value, unit):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or (not math.isfinite(value)) or (unit not in {'fraction', 'percent'}):
        raise ValueError('bad score')
    result = value / 100 if unit == 'percent' else value
    if not 0 <= result <= 1:
        raise ValueError('score range')
    return result

def _impl_rename_fields(row, mapping):
    out = {}
    for key, value in row.items():
        target = mapping.get(key, key)
        if target in out:
            raise ValueError('rename collision')
        out[target] = copy.deepcopy(value)
    return out

def _impl_migrate_row(row):
    if type(row.get('version')) is not int or row['version'] not in (1, 2):
        raise ValueError('bad version')
    old = row['version'] == 1
    id_key = 'run_id' if old else 'id'
    score_key = 'score' if old else 'capability_score'
    if id_key not in row or score_key not in row or (not isinstance(row[id_key], str)) or (not row[id_key].strip()):
        raise ValueError('bad row')
    return {'version': 2, 'id': row[id_key].strip(), 'capability_score': _impl_convert_score(row[score_key], 'percent' if old else 'fraction'), 'metadata': copy.deepcopy(row.get('metadata', {}))}

def _impl_migrate_table(rows):
    valid = []
    errors = []
    for index, row in enumerate(rows, 1):
        try:
            valid.append(_impl_migrate_row(row))
        except ValueError:
            errors.append(index)
    return (valid, errors)

def convert_score(value, unit):
    return _impl_convert_score(value, unit)

def rename_fields(row, mapping):
    return _impl_rename_fields(row, mapping)

def migrate_row(row):
    return _impl_migrate_row(row)

def migrate_table(rows):
    return _impl_migrate_table(rows)
