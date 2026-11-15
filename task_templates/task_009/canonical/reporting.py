"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import __SF_MONITOR_COMPONENT__ as api

def schedule_report(graph, completed, weights, capacity):
    """schedule_report(graph,completed,weights,capacity) in reporting.py returns
ready,batches,depths,remaining; pack only ready tasks, use weights by task ID, and count
remaining as graph IDs absent from completed."""
    raise NotImplementedError
