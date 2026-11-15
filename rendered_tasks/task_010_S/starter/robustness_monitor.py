"""Utilities for AI safety research safety_eval_run processing."""
import copy
import hashlib
import itertools
import json

def deep_merge(base, override):
    """deep_merge(base,override) recursively merges dictionaries; non-dictionary overrides,
including lists and None, replace base values; return a deep copy and preserve both
inputs."""
    raise NotImplementedError

def expand_grid(grid):
    """expand_grid(grid) returns dictionaries for the Cartesian product of value lists, with
dimensions sorted by key and values in supplied order; an empty grid yields [{}], any
empty dimension yields [], and repeated values remain repeated."""
    raise NotImplementedError

def select_shard(items, index, count):
    """select_shard(items,index,count) returns deep copies of items at positions p where
p%count==index; count must be a positive integer and index an integer in [0,count),
excluding booleans, otherwise raise ValueError."""
    raise NotImplementedError

def canonical_fingerprint(config):
    """canonical_fingerprint(config) returns SHA-256 hex of UTF-8 JSON with recursively sorted
keys, separators comma/colon without spaces, ensure_ascii=False, and allow_nan=False;
nonfinite numbers raise ValueError."""
    raise NotImplementedError
