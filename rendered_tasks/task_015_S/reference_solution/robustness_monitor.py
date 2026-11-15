"""Utilities for AI safety research safety_eval_run processing."""
import math

def _impl_category_counts(rows, key):
    counts = {}
    for row in rows:
        value = row.get(key)
        if value is not None:
            counts[value] = counts.get(value, 0) + 1
    return counts

def _impl_aligned_proportions(left, right, alpha):
    if not math.isfinite(alpha) or alpha < 0:
        raise ValueError('alpha')
    categories = sorted(left.keys() | right.keys())
    vectors = []
    for counts in (left, right):
        v = [counts.get(c, 0) + alpha for c in categories]
        total = sum(v)
        vectors.append([x / total if total else 0.0 for x in v])
    return {'categories': categories, 'left': vectors[0], 'right': vectors[1]}

def _impl_jensen_shannon(left, right):
    if len(left) != len(right) or any((not math.isfinite(x) or x < 0 for x in list(left) + list(right))):
        raise ValueError('vectors')

    def norm(values):
        total = sum(values)
        return [v / total if total else 0.0 for v in values]
    a = norm(left)
    b = norm(right)
    mid = [(x + y) / 2 for x, y in zip(a, b)]
    return 0.5 * sum((x * math.log2(x / m) for v in (a, b) for x, m in zip(v, mid) if x > 0))

def _impl_rank_changes(categories, left, right):
    if len(categories) != len(left) or len(left) != len(right):
        raise ValueError('length')
    rows = [{'category': c, 'delta': b - a} for c, a, b in zip(categories, left, right)]
    return sorted(rows, key=lambda r: (-abs(r['delta']), r['category']))

def category_counts(rows, key):
    return _impl_category_counts(rows, key)

def aligned_proportions(left, right, alpha):
    return _impl_aligned_proportions(left, right, alpha)

def jensen_shannon(left, right):
    return _impl_jensen_shannon(left, right)

def rank_changes(categories, left, right):
    return _impl_rank_changes(categories, left, right)
