"""Utilities for AI safety research safety_eval_run processing."""
def _impl_decide(probabilities, threshold):
    return [int(p >= threshold) for p in probabilities]

def _impl_confusion(labels, decisions):
    if len(labels) != len(decisions):
        raise ValueError('length')
    out = dict(tp=0, fp=0, tn=0, fn=0)
    for y, p in zip(labels, decisions):
        out['tp' if y and p else 'fn' if y else 'fp' if p else 'tn'] += 1
    return out

def _impl_decision_cost(counts, costs):
    return sum((counts.get(k, 0) * costs.get(k, 0) for k in ('tp', 'fp', 'tn', 'fn')))

def _impl_best_threshold(labels, probabilities, candidates, costs):
    if not candidates or len(labels) != len(probabilities):
        raise ValueError('input')
    pairs = [(_impl_decision_cost(_impl_confusion(labels, _impl_decide(probabilities, t)), costs), -t) for t in set(candidates)]
    cost, negative = min(pairs)
    return {'threshold': -negative, 'cost': cost}

def decide(probabilities, threshold):
    return _impl_decide(probabilities, threshold)

def confusion(labels, decisions):
    return _impl_confusion(labels, decisions)

def decision_cost(counts, costs):
    return _impl_decision_cost(counts, costs)

def best_threshold(labels, probabilities, candidates, costs):
    return _impl_best_threshold(labels, probabilities, candidates, costs)
