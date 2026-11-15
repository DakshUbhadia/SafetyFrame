"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import __SF_MONITOR_COMPONENT__ as api
def assignment_report(tasks,conditions):
    rows=api.assign_blocks(tasks,conditions)
    return {'rows':rows,'valid':api.validate_assignments(rows,tasks,conditions),'counts':api.assignment_counts(rows),
            'position_counts':{c:[sum(r['condition']==c and r['position']==p for r in rows) for p in range(1,len(conditions)+1)] for c in conditions}}
