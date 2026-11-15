"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import __SF_MONITOR_COMPONENT__ as api
def migration_report(rows):
    valid,errors=api.migrate_table(rows); counts={}
    for row in valid: counts[row['id']]=counts.get(row['id'],0)+1
    return {'migrated':valid,'errors':errors,'duplicate_ids':sorted(k for k,v in counts.items() if v>1)}
