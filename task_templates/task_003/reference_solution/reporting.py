"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import __SF_MONITOR_COMPONENT__ as api
def roundtrip_report(records):
    columns=api.to_columns(records)
    return {'columns':columns,'row_count':len(records),'missing_cells':sum(v is None for values in columns.values() for v in values)}
