"""Utilities for AI safety research safety_eval_run processing."""
import robustness_monitor as api
def schedule_report(graph,completed,weights,capacity):
    ready=api.ready_tasks(graph,completed)
    return {'ready':ready,'batches':api.pack_batches([(k,weights[k]) for k in ready],capacity),'depths':api.critical_depths(graph),'remaining':len(set(graph)-set(completed))}
