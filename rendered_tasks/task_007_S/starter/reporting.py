"""Utilities for AI safety research safety_eval_run processing."""
import robustness_monitor as api

def comparison_report(left, right, tolerance, fraction):
    """comparison_report(left,right,tolerance,fraction) in reporting.py returns
ids,deltas,signs,trimmed,leave_one_out using paired deltas; empty matches produce empty
lists, zero sign counts, and trimmed=None."""
    raise NotImplementedError
