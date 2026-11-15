"""Utilities for AI capability research capability_run processing."""
import copy

def flatten_record(record):
    """flatten_record(record) recursively flattens nested dictionaries to tuple-of-string
paths, treats lists and empty dictionaries as leaf values, deep-copies leaves, and
represents an empty root dictionary as {():{}}."""
    raise NotImplementedError

def unflatten_record(flat):
    """unflatten_record(flat) reconstructs a dictionary from tuple paths, deep-copies values,
and rejects non-string path segments, empty non-root paths, leaf/parent conflicts, or a
root marker combined with other paths with ValueError; an empty flat mapping yields {}
and a sole root marker must contain {}."""
    raise NotImplementedError

def to_columns(records):
    """to_columns(records) returns a path-sorted dictionary of flattened leaf columns, each a
list with None for absent paths; an empty input returns {}, and every record contributes
one slot to each column."""
    raise NotImplementedError

def from_columns(columns):
    """from_columns(columns) requires equal column lengths, rejects mismatches with ValueError,
and reconstructs one record per position using non-None cells; empty columns returns [],
and entirely None rows become {}."""
    raise NotImplementedError
