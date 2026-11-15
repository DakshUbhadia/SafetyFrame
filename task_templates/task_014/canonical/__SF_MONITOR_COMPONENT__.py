"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import math

def bucket_samples(samples, width, origin):
    """bucket_samples(samples,width,origin) requires positive finite width or raises
ValueError; group (time,value) pairs under integer floor((time-origin)/width),
preserving input value order within each bucket and returning keys in ascending order."""
    raise NotImplementedError

def reduce_buckets(buckets):
    """reduce_buckets(buckets) returns each bucket's mean excluding None, or None when no
numeric values remain; preserve the input key set."""
    raise NotImplementedError

def fill_forward(values, max_missing):
    """fill_forward(values,max_missing) requires a nonnegative integer limit excluding booleans
or raises ValueError; fill at most max_missing consecutive None entries after a known
value, leaving leading missing values and longer-gap remainder as None; each observed
value resets the gap."""
    raise NotImplementedError

def moving_average(values, window):
    """moving_average(values,window) requires a positive integer window excluding booleans or
raises ValueError; at each index average non-None values among the most recent window
positions including current, returning None when all are missing."""
    raise NotImplementedError
