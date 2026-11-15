import json
import math

def normalize_record(record):
    if not isinstance(record, dict):
        raise ValueError("record must be a dictionary")
    ident = record.get("id")
    timestamp = record.get("timestamp")
    score = record.get("capability_score")
    if not isinstance(ident, str) or not ident.strip():
        raise ValueError("invalid id")
    if type(timestamp) is not int or timestamp < 0:
        raise ValueError("invalid timestamp")
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 1:
        raise ValueError("invalid score")
    return {**record, "id": ident.strip()}

def read_records(text):
    valid, invalid = [], []
    for index, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            valid.append(normalize_record(json.loads(line)))
        except (ValueError, TypeError):
            invalid.append(index)
    return valid, invalid

def latest_records(records):
    chosen = {}
    for record in records:
        if record["id"] not in chosen or record["timestamp"] >= chosen[record["id"]]["timestamp"]:
            chosen[record["id"]] = record
    return [dict(chosen[ident]) for ident in sorted(chosen)]

def group_means(records):
    totals, counts = {}, {}
    for record in records:
        group = record.get("group", "default")
        totals[group] = totals.get(group, 0) + record["capability_score"]
        counts[group] = counts.get(group, 0) + 1
    return {group: totals[group] / counts[group] for group in sorted(totals)}
