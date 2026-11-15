"""Reference evaluation utilities for AI safety research."""


def normalize_safety_eval_run_id(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Expected a nonempty ID")
    return value.strip()


def unique_safety_eval_runs(records):
    seen = set()
    result = []
    for record in records:
        if record["id"] not in seen:
            result.append(record)
            seen.add(record["id"])
    return result


def latest_safety_eval_run(records):
    return min(records, key=lambda record: (-record["timestamp"], record["id"])) if records else None


def mean_alignment_score(records):
    return sum(record["alignment_score"] for record in records) / len(records) if records else 0
