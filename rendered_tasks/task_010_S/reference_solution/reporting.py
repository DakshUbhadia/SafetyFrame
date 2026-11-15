"""Utilities for AI safety research safety_eval_run processing."""
import robustness_monitor as api
def configuration_report(base,grid,index,count):
    combinations=api.expand_grid(grid)
    configs=api.select_shard([api.deep_merge(base,c) for c in combinations],index,count)
    return {'configurations':configs,'fingerprints':[api.canonical_fingerprint(c) for c in configs],'total':len(combinations)}
