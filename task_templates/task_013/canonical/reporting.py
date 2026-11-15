"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import __SF_MONITOR_COMPONENT__ as api

def alert_report(values, low, high, min_streak, cooldown, max_gap):
    """alert_report(values,low,high,min_streak,cooldown,max_gap) in reporting.py returns
labels,streaks,events,episodes,missing, where episodes merge emitted event indices and
missing counts None values."""
    raise NotImplementedError
