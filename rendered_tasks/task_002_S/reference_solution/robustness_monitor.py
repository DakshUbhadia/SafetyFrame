"""Utilities for AI safety research safety_eval_run processing."""
import csv
import io
import math
import re

def _impl_parse_header(names):
    result = [n.strip() for n in names]
    if any((not n for n in result)) or len(set(result)) != len(result):
        raise ValueError('bad header')
    return result

def _impl_convert_value(text, kind):
    if kind not in {'str', 'int', 'float', 'bool'}:
        raise ValueError('bad kind')
    text = text.strip()
    if not text:
        return None
    try:
        if kind == 'str':
            return text
        if kind == 'int':
            if not re.fullmatch('-?[0-9]+', text):
                raise ValueError('bad integer')
            return int(text)
        if kind == 'float':
            value = float(text)
            if not math.isfinite(value):
                raise ValueError('nonfinite')
            return value
        if text not in {'true', 'false'}:
            raise ValueError('bad boolean')
        return text == 'true'
    except (TypeError, OverflowError):
        raise ValueError('bad value')

def _impl_read_table(text):
    reader = csv.reader(io.StringIO(text))
    try:
        names = _impl_parse_header(next(reader))
    except StopIteration:
        return []
    result = []
    for row in reader:
        if not row:
            continue
        if len(row) != len(names):
            raise ValueError('ragged row')
        result.append(dict(zip(names, row)))
    return result

def _impl_validate_rows(rows, schema, required):
    valid = []
    errors = []
    for index, row in enumerate(rows, 1):
        converted = {}
        invalid = []
        for name, kind in schema.items():
            try:
                converted[name] = _impl_convert_value(row.get(name, ''), kind)
                if name in required and converted[name] is None:
                    invalid.append(name)
            except ValueError:
                invalid.append(name)
        if invalid:
            errors.append({'row': index, 'columns': sorted(invalid)})
        else:
            valid.append(converted)
    return (valid, errors)

def parse_header(names):
    return _impl_parse_header(names)

def convert_value(text, kind):
    return _impl_convert_value(text, kind)

def read_table(text):
    return _impl_read_table(text)

def validate_rows(rows, schema, required):
    return _impl_validate_rows(rows, schema, required)
