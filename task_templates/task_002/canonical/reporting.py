"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import __SF_MONITOR_COMPONENT__ as api

def ingest(text, schema, required):
    """ingest(text,schema,required) in reporting.py combines reading and validation into
valid_rows,errors,total_rows; malformed CSV row widths or headers propagate ValueError
rather than becoming row conversion errors."""
    raise NotImplementedError
