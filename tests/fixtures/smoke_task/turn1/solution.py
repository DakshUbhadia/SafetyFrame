def normalize_id(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Expected a nonempty ID")
    return value.strip()


def unique_ids(values):
    return list(dict.fromkeys(values))


def latest_event(events):
    return events[-1] if events else None


def mean_score(values):
    return sum(values) / len(values) if values else None
