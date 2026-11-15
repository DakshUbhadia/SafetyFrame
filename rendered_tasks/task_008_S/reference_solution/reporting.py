"""Utilities for AI safety research safety_eval_run processing."""
import robustness_monitor as api
def label_report(rows,parents):
    credits=[api.label_credit(r['expected'],r['predicted'],parents) for r in rows]
    groups=api.aggregate_labels([{'label':r['expected'],'alignment_score':c} for r,c in zip(rows,credits)])
    return {'credits':credits,'groups':groups,'macro':api.macro_groups(groups)}
