"""Utilities for AI safety research safety_eval_run processing."""
import robustness_monitor as api

def series_report(samples, width, origin, start, end, max_missing, window):
    """series_report(samples,width,origin,start,end,max_missing,window) in reporting.py reduces
buckets, builds values for every integer bucket start through end inclusive using None
for absent buckets, forward-fills then smooths; return buckets,values,filled,smoothed
and empty lists when start>end."""
    raise NotImplementedError
