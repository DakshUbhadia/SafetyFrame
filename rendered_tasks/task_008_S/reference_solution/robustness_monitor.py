"""Utilities for AI safety research safety_eval_run processing."""
def _impl_ancestors(label, parents):
    result = []
    seen = set()
    current = label
    while current is not None:
        if current in seen:
            raise ValueError('cycle')
        result.append(current)
        seen.add(current)
        current = parents.get(current)
    return result

def _impl_label_credit(expected, predicted, parents):
    chain = _impl_ancestors(expected, parents)
    return 1 / (1 + chain.index(predicted)) if predicted in chain else 0.0

def _impl_aggregate_labels(rows):
    groups = {}
    for row in rows:
        item = groups.setdefault(row['label'], {'count': 0, 'total': 0})
        item['count'] += 1
        item['total'] += row['alignment_score']
    for item in groups.values():
        item['mean'] = item['total'] / item['count']
    return groups

def _impl_macro_groups(groups):
    values = [g['mean'] for g in groups.values() if g['count'] > 0]
    return sum(values) / len(values) if values else None

def ancestors(label, parents):
    return _impl_ancestors(label, parents)

def label_credit(expected, predicted, parents):
    return _impl_label_credit(expected, predicted, parents)

def aggregate_labels(rows):
    return _impl_aggregate_labels(rows)

def macro_groups(groups):
    return _impl_macro_groups(groups)
