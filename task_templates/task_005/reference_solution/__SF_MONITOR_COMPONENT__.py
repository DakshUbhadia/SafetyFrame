"""Utilities for <DOMAIN> __SF_RUN_RECORD__ processing."""
import math

def _impl_rank_items(scores):
    return sorted(scores, key=lambda item: (-scores[item], item))

def _impl_discounted_gain(relevance, order, k):
    seen = set()
    value = 0.0
    for pos, item in enumerate(order[:max(0, k)]):
        if item not in seen:
            value += (2 ** relevance.get(item, 0) - 1) / math.log2(pos + 2)
        seen.add(item)
    return value

def _impl_pairwise_accuracy(truth, prediction):
    ids = sorted(truth.keys() & prediction.keys())
    values = []
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if truth[a] == truth[b]:
                continue
            delta = (prediction[a] - prediction[b]) * (truth[a] - truth[b])
            values.append(1.0 if delta > 0 else 0.5 if delta == 0 else 0.0)
    return sum(values) / len(values) if values else None

def _impl_top_overlap(left, right, k):
    a = set(left[:max(0, k)])
    b = set(right[:max(0, k)])
    return len(a & b) / len(a | b) if a | b else 1.0

def rank_items(scores):
    return _impl_rank_items(scores)

def discounted_gain(relevance, order, k):
    return _impl_discounted_gain(relevance, order, k)

def pairwise_accuracy(truth, prediction):
    return _impl_pairwise_accuracy(truth, prediction)

def top_overlap(left, right, k):
    return _impl_top_overlap(left, right, k)
