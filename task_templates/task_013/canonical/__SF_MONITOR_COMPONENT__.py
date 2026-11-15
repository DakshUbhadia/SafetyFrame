"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
def classify(values, low, high):
    """classify(values,low,high) returns low,ok,high labels using strict comparisons (<low or
>high); None yields missing, boundary values are ok, and low>high raises ValueError."""
    raise NotImplementedError

def breach_streaks(labels):
    """breach_streaks(labels) returns consecutive identical low/high streak lengths at each
position; ok or missing resets to zero and switching breach side starts at one."""
    raise NotImplementedError

def alert_events(labels, min_streak, cooldown):
    """alert_events(labels,min_streak,cooldown) requires positive integer min_streak and
nonnegative integer cooldown excluding booleans or raises ValueError; emit index,side
events when a low/high streak first reaches min_streak, and suppress candidates with
index-last_emitted_index<=cooldown; a suppressed candidate is never delayed."""
    raise NotImplementedError

def merge_episodes(indices, max_gap):
    """merge_episodes(indices,max_gap) requires nonnegative integer max_gap excluding booleans
or raises ValueError; sort and deduplicate integer indices and merge adjacent indices
when their difference<=max_gap, returning start,end,count dictionaries."""
    raise NotImplementedError
