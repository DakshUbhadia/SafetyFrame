from __SF_MONITOR_COMPONENT__ import coverage_by_group

def make_summary(records,windows,limit):
    if type(limit) is not int or limit<0: raise ValueError("invalid limit")
    coverage=coverage_by_group(records,windows)
    ordered=sorted(coverage,key=lambda group:(-coverage[group],group))
    return {"total_ms":sum(coverage.values()),"active_groups":sum(value>0 for value in coverage.values()),
        "groups":[{"group":g,"coverage_ms":coverage[g]} for g in ordered[:limit]]}
