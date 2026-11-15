"""Utilities for AI safety research safety_eval_run processing."""
import robustness_monitor as api
def roundtrip_report(records):
    columns=api.to_columns(records)
    return {'columns':columns,'row_count':len(records),'missing_cells':sum(v is None for values in columns.values() for v in values)}
