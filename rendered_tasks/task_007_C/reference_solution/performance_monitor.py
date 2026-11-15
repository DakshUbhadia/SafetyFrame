"""Utilities for AI capability research capability_run processing."""
import math

def _impl_match_pairs(left, right):
    return [(k, right[k] - left[k]) for k in sorted(left.keys() & right.keys())]

def _impl_sign_summary(deltas, tolerance):
    if tolerance < 0:
        raise ValueError('negative tolerance')
    return {'positive': sum((x > tolerance for x in deltas)), 'negative': sum((x < -tolerance for x in deltas)), 'ties': sum((-tolerance <= x <= tolerance for x in deltas))}

def _impl_trimmed_mean(values, fraction):
    if not 0 <= fraction < 0.5:
        raise ValueError('fraction')
    if not values:
        return None
    k = math.floor(len(values) * fraction)
    ordered = sorted(values)
    kept = ordered[k:len(values) - k]
    return sum(kept) / len(kept)

def _impl_leave_one_out(values):
    if len(values) < 2:
        return []
    total = sum(values)
    return [(total - x) / (len(values) - 1) for x in values]

def match_pairs(left, right):
    return _impl_match_pairs(left, right)

def sign_summary(deltas, tolerance):
    return _impl_sign_summary(deltas, tolerance)

def trimmed_mean(values, fraction):
    return _impl_trimmed_mean(values, fraction)

def leave_one_out(values):
    return _impl_leave_one_out(values)
