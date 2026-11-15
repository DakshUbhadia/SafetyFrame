"""Reference evaluation utilities for <DOMAIN>."""


def normalize___SF_RUN_RECORD___id(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Expected a nonempty ID")
    return value.strip()


def unique___SF_RUN_RECORD__s(records):
    seen = set()
    result = []
    for record in records:
        if record["id"] not in seen:
            result.append(record)
            seen.add(record["id"])
    return result


def latest___SF_RUN_RECORD__(records):
    return min(records, key=lambda record: (-record["timestamp"], record["id"])) if records else None


def mean___SF_PRIMARY_SCORE__(records):
    return sum(record["__SF_PRIMARY_SCORE__"] for record in records) / len(records) if records else 0
