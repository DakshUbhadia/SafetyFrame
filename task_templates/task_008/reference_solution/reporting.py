"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import __SF_MONITOR_COMPONENT__ as api
def label_report(rows,parents):
    credits=[api.label_credit(r['expected'],r['predicted'],parents) for r in rows]
    groups=api.aggregate_labels([{'label':r['expected'],'__SF_PRIMARY_SCORE__':c} for r,c in zip(rows,credits)])
    return {'credits':credits,'groups':groups,'macro':api.macro_groups(groups)}
