"""Utilities for AI safety research safety_eval_run processing."""
import robustness_monitor as api

def drift_report(reference, current, key, alpha):
    """drift_report(reference,current,key,alpha) in reporting.py counts categories, aligns
proportions, and returns categories,reference,current,divergence,changes;
reference/current are normalized vectors and changes use those vectors."""
    raise NotImplementedError
