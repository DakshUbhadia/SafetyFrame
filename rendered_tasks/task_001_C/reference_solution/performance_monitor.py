"""Utilities for AI capability research capability_run processing."""
import copy
import re

def _impl_parse_path(text):
    if not isinstance(text, str) or not text:
        raise ValueError('invalid path')
    result = []
    part = ''
    escaped = False
    for char in text:
        if escaped:
            if char not in '.\\':
                raise ValueError('invalid escape')
            part += char
            escaped = False
        elif char == '\\':
            escaped = True
        elif char == '.':
            if not part:
                raise ValueError('empty segment')
            result.append(part)
            part = ''
        else:
            part += char
    if escaped or not part:
        raise ValueError('invalid ending')
    return result + [part]

def _impl_lookup(record, segments, default=None):
    node = record
    for segment in segments:
        if isinstance(node, dict) and segment in node:
            node = node[segment]
        elif isinstance(node, list) and re.fullmatch('0|[1-9][0-9]*', segment) and (int(segment) < len(node)):
            node = node[int(segment)]
        else:
            return default
    return copy.deepcopy(node)

def _impl_project(record, columns):
    return {name: _impl_lookup(record, _impl_parse_path(columns[name])) for name in sorted(columns)}

def _impl_expand_columns(columns, prefix):
    out = {name: prefix + '.' + path if prefix else path for name, path in columns.items()}
    for path in out.values():
        _impl_parse_path(path)
    return out

def parse_path(text):
    return _impl_parse_path(text)

def lookup(record, segments, default=None):
    return _impl_lookup(record, segments, default)

def project(record, columns):
    return _impl_project(record, columns)

def expand_columns(columns, prefix):
    return _impl_expand_columns(columns, prefix)
