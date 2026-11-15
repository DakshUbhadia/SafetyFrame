import copy

def deduplicate(records):
    chosen = {}
    for record in records:
        if record["id"] not in chosen or record["timestamp"] >= chosen[record["id"]]["timestamp"]:
            chosen[record["id"]] = record
    return [dict(chosen[ident]) for ident in sorted(chosen)]

def window_records(records, start, end):
    if start > end:
        raise ValueError("reversed window")
    return [dict(record) for record in records if start <= record["timestamp"] < end]

def weighted_rate(records):
    weight = sum(record.get("weight", 1) for record in records)
    return sum(record.get("weight", 1) * record["success"] for record in records) / weight if weight else None

def group_summary(records, start, end):
    groups = {}
    for record in window_records(deduplicate(records), start, end):
        groups.setdefault(record.get("group", "default"), []).append(record)
    return [{"group": group, "count": len(groups[group]), "rate": weighted_rate(groups[group])} for group in sorted(groups)]

def merge_metadata(base, patch):
    result = copy.deepcopy(base)
    for key, value in patch.items():
        if value is None:
            result.pop(key, None)
        elif isinstance(value, dict):
            result[key] = merge_metadata(result.get(key, {}) if isinstance(result.get(key), dict) else {}, value)
        else:
            result[key] = copy.deepcopy(value)
    return result
