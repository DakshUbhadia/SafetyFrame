"""Utilities for AI safety research safety_eval_run processing."""
import robustness_monitor as api

def schedule_report(graph, completed, weights, capacity):
    """schedule_report(graph,completed,weights,capacity) in reporting.py returns
ready,batches,depths,remaining; pack only ready tasks, use weights by task ID, and count
remaining as graph IDs absent from completed."""
    raise NotImplementedError
