"""Utilities for AI safety research safety_eval_run processing."""
def _impl_classify(values, low, high):
    if low > high:
        raise ValueError('thresholds')
    return ['missing' if v is None else 'low' if v < low else 'high' if v > high else 'ok' for v in values]

def _impl_breach_streaks(labels):
    out = []
    previous = None
    length = 0
    for label in labels:
        length = (length + 1 if label == previous else 1) if label in ('low', 'high') else 0
        out.append(length)
        previous = label
    return out

def _impl_alert_events(labels, min_streak, cooldown):
    if type(min_streak) is not int or min_streak <= 0 or type(cooldown) is not int or (cooldown < 0):
        raise ValueError('parameters')
    streaks = _impl_breach_streaks(labels)
    out = []
    last = None
    for i, (label, length) in enumerate(zip(labels, streaks)):
        if length == min_streak and (last is None or i - last > cooldown):
            out.append({'index': i, 'side': label})
            last = i
    return out

def _impl_merge_episodes(indices, max_gap):
    if type(max_gap) is not int or max_gap < 0:
        raise ValueError('gap')
    out = []
    for index in sorted(set(indices)):
        if out and index - out[-1]['end'] <= max_gap:
            out[-1]['end'] = index
            out[-1]['count'] += 1
        else:
            out.append(dict(start=index, end=index, count=1))
    return out

def classify(values, low, high):
    return _impl_classify(values, low, high)

def breach_streaks(labels):
    return _impl_breach_streaks(labels)

def alert_events(labels, min_streak, cooldown):
    return _impl_alert_events(labels, min_streak, cooldown)

def merge_episodes(indices, max_gap):
    return _impl_merge_episodes(indices, max_gap)
