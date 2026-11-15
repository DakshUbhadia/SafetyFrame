"""Utilities for AI capability research capability_run processing."""
def _impl_rotate_conditions(conditions, offset):
    if not isinstance(conditions, list) or not conditions or any((not isinstance(c, str) for c in conditions)) or (len(set(conditions)) != len(conditions)):
        raise ValueError('conditions')
    k = offset % len(conditions)
    return conditions[k:] + conditions[:k]

def _impl_assign_blocks(tasks, conditions):
    if len(set(tasks)) != len(tasks):
        raise ValueError('tasks')
    _impl_rotate_conditions(conditions, 0)
    return [{'task': task, 'condition': c, 'position': j + 1} for i, task in enumerate(tasks) for j, c in enumerate(_impl_rotate_conditions(conditions, i))]

def _impl_validate_assignments(rows, tasks, conditions):
    if not conditions or len(set(tasks)) != len(tasks) or len(set(conditions)) != len(conditions):
        return False
    pairs = set()
    positions = {t: set() for t in tasks}
    for r in rows:
        t = r['task']
        c = r['condition']
        p = r['position']
        if t not in positions or c not in conditions or type(p) is not int or (not 1 <= p <= len(conditions)) or ((t, c) in pairs) or (p in positions[t]):
            return False
        pairs.add((t, c))
        positions[t].add(p)
    return len(pairs) == len(tasks) * len(conditions)

def _impl_assignment_counts(rows):
    return {c: sum((r['condition'] == c for r in rows)) for c in sorted({r['condition'] for r in rows})}

def rotate_conditions(conditions, offset):
    return _impl_rotate_conditions(conditions, offset)

def assign_blocks(tasks, conditions):
    return _impl_assign_blocks(tasks, conditions)

def validate_assignments(rows, tasks, conditions):
    return _impl_validate_assignments(rows, tasks, conditions)

def assignment_counts(rows):
    return _impl_assignment_counts(rows)
