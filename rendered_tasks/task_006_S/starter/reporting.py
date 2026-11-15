"""Utilities for AI safety research safety_eval_run processing."""
import robustness_monitor as api

def decision_report(labels, probabilities, threshold, costs):
    """decision_report(labels,probabilities,threshold,costs) in reporting.py returns
decisions,counts,cost,precision,recall; precision and recall are None when their
denominator is zero."""
    raise NotImplementedError
