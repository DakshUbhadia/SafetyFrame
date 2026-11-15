"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import copy
import re

def parse_path(text):
    """parse_path(text) splits dot-separated paths, using backslash to escape a dot or
backslash; reject empty segments, empty input, non-string input, invalid escapes, and a
trailing backslash with ValueError."""
    raise NotImplementedError

def lookup(record, segments, default=None):
    """lookup(record,segments,default=None) traverses dictionary keys and canonical list
indices (0 or a nonzero digit followed by digits); return a deep copy or the supplied
default for a missing key, invalid index, or scalar traversal; empty segments select the
whole record."""
    raise NotImplementedError

def project(record, columns):
    """project(record,columns) resolves output-name to path-string mappings, returns values in
sorted output-name order, and uses None for missing fields while preserving False and
zero values."""
    raise NotImplementedError

def expand_columns(columns, prefix):
    """expand_columns(columns,prefix) prepends prefix plus a dot to each path when prefix is
nonempty, preserves paths when prefix is empty, returns a new dictionary, and rejects
invalid resulting paths with ValueError."""
    raise NotImplementedError
