"""Utilities for AI safety research safety_eval_run processing."""
import robustness_monitor as api

def ingest(text, schema, required):
    """ingest(text,schema,required) in reporting.py combines reading and validation into
valid_rows,errors,total_rows; malformed CSV row widths or headers propagate ValueError
rather than becoming row conversion errors."""
    raise NotImplementedError
