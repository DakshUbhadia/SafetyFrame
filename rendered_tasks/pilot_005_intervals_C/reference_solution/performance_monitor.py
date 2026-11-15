import re
from decimal import Decimal

def parse_duration(value):
    if type(value) is int and value>=0: return value
    if not isinstance(value,str): raise ValueError("invalid duration")
    match=re.fullmatch(r"([0-9]+(?:\.[0-9]{1,3})?)(ms|s|m)",value.strip())
    if not match: raise ValueError("invalid duration")
    result=Decimal(match[1])*{"ms":1,"s":1000,"m":60000}[match[2]]
    if result!=result.to_integral_value(): raise ValueError("fractional millisecond")
    return int(result)

def coalesce_intervals(intervals):
    valid=[]
    for pair in intervals:
        if not isinstance(pair,(list,tuple)) or len(pair)!=2 or any(type(x) is not int for x in pair) or pair[1]<pair[0]: raise ValueError("invalid interval")
        if pair[0]<pair[1]: valid.append(tuple(pair))
    result=[]
    for start,end in sorted(valid):
        if result and start<=result[-1][1]: result[-1]=(result[-1][0],max(result[-1][1],end))
        else: result.append((start,end))
    return result

def subtract_intervals(inclusions,exclusions):
    pieces=coalesce_intervals(inclusions)
    for a,b in coalesce_intervals(exclusions):
        remaining=[]
        for start,end in pieces:
            if b<=start or a>=end: remaining.append((start,end))
            else:
                if start<a: remaining.append((start,a))
                if b<end: remaining.append((b,end))
        pieces=remaining
    return pieces

def coverage_by_group(records,windows):
    chosen={r["id"]:r for r in records}; groups={}
    for r in chosen.values(): groups.setdefault(r["group"],[]).append((r["start"],r["end"]))
    windows=coalesce_intervals(windows); result={}
    for group,intervals in sorted(groups.items()):
        result[group]=sum(max(0,min(b,d)-max(a,c)) for a,b in coalesce_intervals(intervals) for c,d in windows)
    return result
