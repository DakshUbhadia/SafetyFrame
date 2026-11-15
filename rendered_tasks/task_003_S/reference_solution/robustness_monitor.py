"""Utilities for AI safety research safety_eval_run processing."""
import copy

def _impl_flatten_record(record):
    result = {}

    def visit(node, path):
        if isinstance(node, dict) and node:
            for key, value in node.items():
                visit(value, path + (key,))
        else:
            result[path] = copy.deepcopy(node)
    visit(record, ())
    return result

def _impl_unflatten_record(flat):
    if not flat:
        return {}
    if () in flat:
        if len(flat) != 1 or flat[()] != {}:
            raise ValueError('bad root')
        return {}
    out = {}
    leaves = set()
    for path, value in sorted(flat.items(), key=lambda item: len(item[0])):
        if not isinstance(path, tuple) or not path or any((not isinstance(k, str) for k in path)):
            raise ValueError('bad path')
        node = out
        for depth, key in enumerate(path[:-1], 1):
            if path[:depth] in leaves:
                raise ValueError('parent conflict')
            node = node.setdefault(key, {})
        if path[-1] in node:
            raise ValueError('leaf conflict')
        node[path[-1]] = copy.deepcopy(value)
        leaves.add(path)
    return out

def _impl_to_columns(records):
    rows = [_impl_flatten_record(r) for r in records]
    paths = sorted(set().union(*(r.keys() for r in rows))) if rows else []
    return {path: [copy.deepcopy(row.get(path)) for row in rows] for path in paths}

def _impl_from_columns(columns):
    lengths = {len(values) for values in columns.values()}
    if len(lengths) > 1:
        raise ValueError('unequal lengths')
    if not lengths:
        return []
    return [_impl_unflatten_record({path: values[i] for path, values in columns.items() if values[i] is not None}) for i in range(next(iter(lengths)))]

def flatten_record(record):
    return _impl_flatten_record(record)

def unflatten_record(flat):
    return _impl_unflatten_record(flat)

def to_columns(records):
    return _impl_to_columns(records)

def from_columns(columns):
    return _impl_from_columns(columns)
