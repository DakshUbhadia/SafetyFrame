"""Utilities for AI safety research safety_eval_run processing."""
import robustness_monitor as api
def project_table(records,columns):
    names=sorted(columns); projected=[api.project(r,columns) for r in records]
    return {'columns':names,'rows':[[r[n] for n in names] for r in projected],
            'missing_counts':{n:sum(r[n] is None for r in projected) for n in names}}
