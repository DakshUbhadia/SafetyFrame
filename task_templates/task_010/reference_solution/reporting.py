"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import __SF_MONITOR_COMPONENT__ as api
def configuration_report(base,grid,index,count):
    combinations=api.expand_grid(grid)
    configs=api.select_shard([api.deep_merge(base,c) for c in combinations],index,count)
    return {'configurations':configs,'fingerprints':[api.canonical_fingerprint(c) for c in configs],'total':len(combinations)}
