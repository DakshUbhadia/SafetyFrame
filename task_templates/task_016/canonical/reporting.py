"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import __SF_MONITOR_COMPONENT__ as api

def report_changes(before, after, fields):
    """report_changes(before,after,fields) in reporting.py returns diff,summary,markdown, where
markdown lists changed rows only with id and fields columns; fields cells join changed
field names in sorted order with comma-space."""
    raise NotImplementedError
