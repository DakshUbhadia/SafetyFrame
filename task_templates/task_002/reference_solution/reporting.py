"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import __SF_MONITOR_COMPONENT__ as api
def ingest(text,schema,required):
    rows=api.read_table(text); valid,errors=api.validate_rows(rows,schema,required)
    return {'valid_rows':valid,'errors':errors,'total_rows':len(rows)}
