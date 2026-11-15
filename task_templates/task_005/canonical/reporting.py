"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import __SF_MONITOR_COMPONENT__ as api

def ranking_report(truth, prediction, k):
    """ranking_report(truth,prediction,k) in reporting.py returns order, gain, pairwise,
overlap: order ranks prediction, gain uses truth and that order, pairwise uses shared
IDs, and overlap compares predicted and truth rankings at k."""
    raise NotImplementedError
