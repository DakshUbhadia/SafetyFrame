"""Utilities for AI capability research capability_run processing."""
import performance_monitor as api
def ingest(text,schema,required):
    rows=api.read_table(text); valid,errors=api.validate_rows(rows,schema,required)
    return {'valid_rows':valid,'errors':errors,'total_rows':len(rows)}
