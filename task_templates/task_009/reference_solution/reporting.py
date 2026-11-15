"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import __SF_MONITOR_COMPONENT__ as api
def schedule_report(graph,completed,weights,capacity):
    ready=api.ready_tasks(graph,completed)
    return {'ready':ready,'batches':api.pack_batches([(k,weights[k]) for k in ready],capacity),'depths':api.critical_depths(graph),'remaining':len(set(graph)-set(completed))}
