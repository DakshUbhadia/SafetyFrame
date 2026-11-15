"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import __SF_MONITOR_COMPONENT__ as api
def project_table(records,columns):
    names=sorted(columns); projected=[api.project(r,columns) for r in records]
    return {'columns':names,'rows':[[r[n] for n in names] for r in projected],
            'missing_counts':{n:sum(r[n] is None for r in projected) for n in names}}
