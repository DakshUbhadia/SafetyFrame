"""Utilities for AI capability research capability_run processing."""
import performance_monitor as api
def drift_report(reference,current,key,alpha):
    p=api.aligned_proportions(api.category_counts(reference,key),api.category_counts(current,key),alpha)
    return {'categories':p['categories'],'reference':p['left'],'current':p['right'],'divergence':api.jensen_shannon(p['left'],p['right']),'changes':api.rank_changes(p['categories'],p['left'],p['right'])}
