"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import copy

def index_rows(rows):
    """index_rows(rows) returns deep-copied rows indexed by string id, rejecting duplicate IDs
with ValueError; preserve input rows and nested values."""
    raise NotImplementedError

def diff_reports(before, after, fields):
    """diff_reports(before,after,fields) compares rows by id, returning added,removed ID lists
sorted lexically and changed rows sorted by id; each changed row has id and fields
mapping changed requested fields to before,after values; absent values equal None and
unchanged rows are omitted."""
    raise NotImplementedError

def summarize_changes(diff):
    """summarize_changes(diff) returns added,removed,changed counts plus fields counts across
changed rows, with fields in sorted key order; counts are rows, not numeric magnitudes."""
    raise NotImplementedError

def render_markdown(rows, columns):
    """render_markdown(rows,columns) renders a Markdown table with columns as both header
labels and lookup keys in supplied order, using ' | ' separators and leading '| ' and
trailing ' |'; escape backslash as two backslashes, pipe as backslash-pipe, and newline
as <br>; missing or None cells become empty text; produce header,--- separator,and rows
joined by newline with no final newline; empty columns return empty string."""
    raise NotImplementedError
