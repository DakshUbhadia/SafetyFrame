"""Utilities for AI capability research capability_run processing."""
import math

def _impl_bucket_samples(samples, width, origin):
    if not math.isfinite(width) or width <= 0:
        raise ValueError('width')
    result = {}
    for time, value in samples:
        result.setdefault(math.floor((time - origin) / width), []).append(value)
    return {k: result[k] for k in sorted(result)}

def _impl_reduce_buckets(buckets):
    out = {}
    for key, values in buckets.items():
        kept = [v for v in values if v is not None]
        out[key] = sum(kept) / len(kept) if kept else None
    return out

def _impl_fill_forward(values, max_missing):
    if type(max_missing) is not int or max_missing < 0:
        raise ValueError('limit')
    out = []
    last = None
    gap = 0
    for value in values:
        if value is not None:
            last = value
            gap = 0
            out.append(value)
        else:
            gap += 1
            out.append(last if gap <= max_missing else None)
    return out

def _impl_moving_average(values, window):
    if type(window) is not int or window <= 0:
        raise ValueError('window')
    out = []
    for i in range(len(values)):
        kept = [v for v in values[max(0, i - window + 1):i + 1] if v is not None]
        out.append(sum(kept) / len(kept) if kept else None)
    return out

def bucket_samples(samples, width, origin):
    return _impl_bucket_samples(samples, width, origin)

def reduce_buckets(buckets):
    return _impl_reduce_buckets(buckets)

def fill_forward(values, max_missing):
    return _impl_fill_forward(values, max_missing)

def moving_average(values, window):
    return _impl_moving_average(values, window)
