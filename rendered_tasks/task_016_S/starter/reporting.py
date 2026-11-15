"""Utilities for AI safety research safety_eval_run processing."""
import robustness_monitor as api

def report_changes(before, after, fields):
    """report_changes(before,after,fields) in reporting.py returns diff,summary,markdown, where
markdown lists changed rows only with id and fields columns; fields cells join changed
field names in sorted order with comma-space."""
    raise NotImplementedError
