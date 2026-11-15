"""Utilities for AI capability research capability_run processing."""
import performance_monitor as api

def ranking_report(truth, prediction, k):
    """ranking_report(truth,prediction,k) in reporting.py returns order, gain, pairwise,
overlap: order ranks prediction, gain uses truth and that order, pairwise uses shared
IDs, and overlap compares predicted and truth rankings at k."""
    raise NotImplementedError
