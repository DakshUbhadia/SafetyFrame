"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import copy
import hashlib
import itertools
import json

def _impl_deep_merge(base, override):
    if not isinstance(base, dict) or not isinstance(override, dict):
        return copy.deepcopy(override)
    out = copy.deepcopy(base)
    for k, v in override.items():
        out[k] = _impl_deep_merge(out[k], v) if k in out else copy.deepcopy(v)
    return out

def _impl_expand_grid(grid):
    keys = sorted(grid)
    return [dict(zip(keys, copy.deepcopy(values))) for values in itertools.product(*(grid[k] for k in keys))]

def _impl_select_shard(items, index, count):
    if type(count) is not int or count <= 0 or type(index) is not int or (not 0 <= index < count):
        raise ValueError('shard')
    return [copy.deepcopy(v) for i, v in enumerate(items) if i % count == index]

def _impl_canonical_fingerprint(config):
    text = json.dumps(config, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def deep_merge(base, override):
    return _impl_deep_merge(base, override)

def expand_grid(grid):
    return _impl_expand_grid(grid)

def select_shard(items, index, count):
    return _impl_select_shard(items, index, count)

def canonical_fingerprint(config):
    return _impl_canonical_fingerprint(config)
