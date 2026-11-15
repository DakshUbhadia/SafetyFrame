"""Utilities for AI safety research safety_eval_run processing."""
import robustness_monitor as api
def ingest(text,schema,required):
    rows=api.read_table(text); valid,errors=api.validate_rows(rows,schema,required)
    return {'valid_rows':valid,'errors':errors,'total_rows':len(rows)}
