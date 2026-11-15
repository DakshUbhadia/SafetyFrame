"""Reference evaluation utilities for AI capability research."""


def normalize_capability_run_id(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Expected a nonempty ID")
    return value.strip()


def unique_capability_runs(records):
    seen = set()
    result = []
    for record in records:
        if record["id"] not in seen:
            result.append(record)
            seen.add(record["id"])
    return result


def latest_capability_run(records):
    return min(records, key=lambda record: (-record["timestamp"], record["id"])) if records else None


def mean_capability_score(records):
    return sum(record["capability_score"] for record in records) / len(records) if records else 0
