"""Reviewed throwaway calibration task definitions; none may enter final inference."""

PILOTS = [
    {
        "id": "pilot_001_ingestion", "family": "ingestion", "profile": "one file, four straightforward requirements",
        "requirements": [
            "normalize_record(record) returns a shallow copy with a stripped nonempty string id; timestamp must be a nonnegative integer excluding bool, and __SF_PRIMARY_SCORE__ must be a finite number in [0,1] excluding bool; reject invalid or missing fields with ValueError and preserve extra fields.",
            "read_records(text) processes nonblank JSON lines in order, returning (valid_records, invalid_line_numbers); invalid JSON or record validation failures are reported using one-based physical line numbers, and blank lines are ignored.",
            "latest_records(records) keeps the greatest-timestamp record per id, choosing the last input record on equal timestamps, and returns shallow copies sorted by id without mutating input.",
            "group_means(records) returns a dictionary of arithmetic mean __SF_PRIMARY_SCORE__ by group, using the string 'default' when group is absent and returning an empty dictionary for empty input."
        ],
        "extra": "For R3–R4 inputs are already valid normalized records. Group values, when present, are strings. All four functions must leave input containers unchanged. Implement in __SF_MONITOR_COMPONENT__.py.",
        "files": {"__SF_MONITOR_COMPONENT__.py": '''
import json
import math

def normalize_record(record):
    if not isinstance(record, dict):
        raise ValueError("record must be a dictionary")
    ident = record.get("id")
    timestamp = record.get("timestamp")
    score = record.get("__SF_PRIMARY_SCORE__")
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
        totals[group] = totals.get(group, 0) + record["__SF_PRIMARY_SCORE__"]
        counts[group] = counts.get(group, 0) + 1
    return {group: totals[group] / counts[group] for group in sorted(totals)}
'''},
        "public": '''
def test_normalize(self):
    self.assertEqual(api.normalize_record(row(" a "))["id"], "a")
def test_lines(self):
    good, bad = api.read_records(json.dumps(row("a")) + "\\nnot-json")
    self.assertEqual(([r["id"] for r in good], bad), (["a"], [2]))
def test_means(self):
    self.assertEqual(api.group_means([row("a", score=0), row("b", score=1)]), {"default": .5})
''',
        "helper": '''
def row(ident, timestamp=1, score=.5, **extra):
    return {"id": ident, "timestamp": timestamp, "__SF_PRIMARY_SCORE__": score, **extra}
''',
        "hidden": [
            ['''
self.assertEqual(api.normalize_record(row(" a ", note="keep")), row("a", note="keep"))
original = row(" a "); api.normalize_record(original); self.assertEqual(original["id"], " a ")
''', '''
for bad in [None, {}, row(" "), row("a", timestamp=True), row("a", timestamp=-1), row("a", score=True), row("a", score=float("nan")), row("a", score=2)]:
    with self.assertRaises(ValueError): api.normalize_record(bad)
'''],
            ['''
text = "\\n" + json.dumps(row(" a ")) + "\\n[]\\n{broken\\n" + json.dumps(row("b"))
good, bad = api.read_records(text)
self.assertEqual([r["id"] for r in good], ["a", "b"]); self.assertEqual(bad, [3,4])
''', '''
self.assertEqual(api.read_records(" \\n\\n"), ([], []))
self.assertEqual(api.read_records(json.dumps(row("a", score=-1)))[1], [1])
'''],
            ['''
records = [row("b",3), row("a",4), row("b",1), row("a",4,score=.8)]
before = copy.deepcopy(records)
self.assertEqual(api.latest_records(records), [records[3],records[0]])
self.assertEqual(records,before)
''', '''
self.assertEqual(api.latest_records([]), [])
r=row("x"); out=api.latest_records([r]); out[0]["id"]="changed"; self.assertEqual(r["id"],"x")
'''],
            ['''
records=[row("a",score=.25,group="g"),row("b",score=.75,group="g"),row("c",score=1)]
self.assertEqual(api.group_means(records),{"g":.5,"default":1})
''', '''
self.assertEqual(api.group_means([]), {})
records=[row("a",score=.1),row("b",score=.3)]
self.assertAlmostEqual(api.group_means(records)["default"],.2)
''']
        ]
    },
    {
        "id": "pilot_002_windows", "family": "aggregation", "profile": "one file, five requirements, order-sensitive edge cases",
        "requirements": [
            "deduplicate(records) keeps the greatest-timestamp record per id, choosing the last input record on ties, and returns records sorted by id without mutating inputs.",
            "window_records(records,start,end) retains records with start <= timestamp < end in input order, returns empty for start == end, and raises ValueError for start > end.",
            "weighted_rate(records) computes sum(weight*success)/sum(weight), defaulting absent weight to 1 and returning None when the total weight is zero.",
            "group_summary(records,start,end) deduplicates globally before applying the time window, then returns groups sorted by name as dictionaries with group, count, and rate; count includes zero-weight records, and absent group means 'default'.",
            "merge_metadata(base,patch) recursively merges dictionaries, deletes a key when its patch value is None, replaces lists and other values, and returns independent deep copies without mutating either input."
        ],
        "extra": "Inputs are valid dictionaries: id is a string, timestamp is numeric, success is bool, weight is finite nonnegative numeric, and group is a string. Utility functions may assume those types. An absent key patched with None stays absent. Empty summaries return []. Implement in __SF_MONITOR_COMPONENT__.py.",
        "files": {"__SF_MONITOR_COMPONENT__.py": '''
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
'''},
        "helper": '''
def row(ident, timestamp=1, success=True, **extra):
    return {"id":ident,"timestamp":timestamp,"success":success,**extra}
''',
        "public": '''
def test_window(self):
    self.assertEqual(len(api.window_records([row("a",1),row("b",5)],0,3)),1)
def test_rate(self):
    self.assertEqual(api.weighted_rate([row("a",success=True),row("b",success=False)]),.5)
def test_metadata(self):
    self.assertEqual(api.merge_metadata({"x":1},{"y":2}),{"x":1,"y":2})
''',
        "hidden": [
            ['''
rs=[row("b",4),row("a",2),row("b",4,False),row("a",1)]
self.assertEqual(api.deduplicate(rs),[rs[1],rs[2]])
''','''
rs=[row("a")]; before=copy.deepcopy(rs); api.deduplicate(rs); self.assertEqual(rs,before)
self.assertEqual(api.deduplicate([]),[])
'''],
            ['''
rs=[row("a",0),row("b",1),row("c",2)]
self.assertEqual(api.window_records(rs,0,2),rs[:2]); self.assertEqual(api.window_records(rs,1,1),[])
''','''
with self.assertRaises(ValueError): api.window_records([],2,1)
self.assertEqual(api.window_records([],0,1),[])
'''],
            ['''
self.assertAlmostEqual(api.weighted_rate([row("a",success=True,weight=3),row("b",success=False,weight=1)]),.75)
self.assertEqual(api.weighted_rate([row("a",success=False,weight=0),row("b")]),1)
''','''
self.assertIsNone(api.weighted_rate([])); self.assertIsNone(api.weighted_rate([row("a",weight=0)]))
'''],
            ['''
rs=[row("x",1,group="g"),row("x",9,group="g"),row("a",2,group="z",weight=0),row("b",3,False)]
self.assertEqual(api.group_summary(rs,0,5),[{"group":"default","count":1,"rate":0},{"group":"z","count":1,"rate":None}])
''','''
rs=[row("a",1,group="g",weight=0),row("b",2,group="g",weight=2)]
self.assertEqual(api.group_summary(rs,0,4),[{"group":"g","count":2,"rate":1}]); self.assertEqual(api.group_summary([],0,1),[])
'''],
            ['''
base={"a":{"x":1,"y":[1]},"b":2}; patch={"a":{"x":None,"z":3},"b":[4],"missing":None}
self.assertEqual(api.merge_metadata(base,patch),{"a":{"y":[1],"z":3},"b":[4]})
''','''
base={"a":[1]}; patch={"b":{"c":[2]}}; out=api.merge_metadata(base,patch)
out["a"].append(3); out["b"]["c"].append(4)
self.assertEqual(base,{"a":[1]}); self.assertEqual(patch,{"b":{"c":[2]}})
''']
        ]
    }
]

PILOTS.extend([
    {
        "id":"pilot_003_calibration","family":"metrics_reporting","profile":"two files, four requirements, weighted metrics and report integration",
        "requirements":[
            "brier_score(records) returns the weighted mean of (probability-label)**2, treating absent weight as 1 and returning None if total weight is zero.",
            "calibration_bins(records,bins) partitions [0,1] into bins equal-width intervals, assigns p=1 to the last bin, and returns all bins in ascending order with index,count,weight,mean_probability,positive_rate; zero-weight records count but do not affect means, and empty/zero-weight bins have None means; bins must be a positive int excluding bool or raise ValueError.",
            "choose_threshold(records,thresholds) evaluates sorted unique candidate thresholds using prediction probability >= threshold, weighted F1 = 2TP/(2TP+FP+FN) with zero denominator yielding 0, and returns threshold,f1,precision,recall for the maximum F1, choosing the greatest threshold on ties; precision/recall with zero denominator are 0, and no thresholds returns None.",
            "make_report(records,bins,thresholds) in reporting.py returns keys brier,bins,threshold and ece; ece is the weighted mean absolute bin probability-minus-positive-rate gap, ignoring zero-weight bins and returning None for zero total weight; do not mutate records."
        ],
        "extra":"Records have probability numeric in [0,1], label in {0,1}, and finite nonnegative numeric optional weight. Candidate thresholds are finite numbers in [0,1]. Implement metric functions in __SF_MONITOR_COMPONENT__.py and make_report in reporting.py. No rounding of outputs is requested.",
        "files":{
            "__SF_MONITOR_COMPONENT__.py":'''
def brier_score(records):
    weight=sum(r.get("weight",1) for r in records)
    return sum(r.get("weight",1)*(r["probability"]-r["label"])**2 for r in records)/weight if weight else None

def calibration_bins(records,bins):
    if type(bins) is not int or bins<=0: raise ValueError("bins must be positive integer")
    buckets=[[] for _ in range(bins)]
    for r in records: buckets[min(int(r["probability"]*bins),bins-1)].append(r)
    result=[]
    for i,rs in enumerate(buckets):
        weight=sum(r.get("weight",1) for r in rs)
        result.append({"index":i,"count":len(rs),"weight":weight,
            "mean_probability":sum(r.get("weight",1)*r["probability"] for r in rs)/weight if weight else None,
            "positive_rate":sum(r.get("weight",1)*r["label"] for r in rs)/weight if weight else None})
    return result

def choose_threshold(records,thresholds):
    best=None
    for threshold in sorted(set(thresholds)):
        tp=fp=fn=0
        for r in records:
            w=r.get("weight",1); pred=r["probability"]>=threshold
            tp+=w*(pred and r["label"]==1); fp+=w*(pred and r["label"]==0); fn+=w*((not pred) and r["label"]==1)
        f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0
        row={"threshold":threshold,"f1":f1,"precision":tp/(tp+fp) if tp+fp else 0,"recall":tp/(tp+fn) if tp+fn else 0}
        if best is None or (f1,threshold)>(best["f1"],best["threshold"]): best=row
    return best
''',
            "reporting.py":'''
from __SF_MONITOR_COMPONENT__ import brier_score, calibration_bins, choose_threshold

def make_report(records,bins,thresholds):
    groups=calibration_bins(records,bins)
    weight=sum(g["weight"] for g in groups)
    ece=sum(g["weight"]*abs(g["mean_probability"]-g["positive_rate"]) for g in groups if g["weight"])/weight if weight else None
    return {"brier":brier_score(records),"bins":groups,"threshold":choose_threshold(records,thresholds),"ece":ece}
'''
        },
        "test_imports":"import reporting\n",
        "helper":'''
def row(p,y,w=1): return {"probability":p,"label":y,"weight":w}
''',
        "public":'''
def test_brier(self):
    self.assertAlmostEqual(api.brier_score([row(0,0),row(1,1)]),0)
def test_bins(self):
    self.assertEqual([g["count"] for g in api.calibration_bins([row(.1,0),row(.9,1)],2)],[1,1])
def test_report(self):
    self.assertEqual(set(reporting.make_report([row(.1,0),row(.9,1)],2,[.5])),{"brier","bins","threshold","ece"})
''',
        "hidden":[
            ['''
self.assertAlmostEqual(api.brier_score([row(.2,0,3),row(.6,1,1)]),.07)
''','''
self.assertIsNone(api.brier_score([])); self.assertIsNone(api.brier_score([row(.5,1,0)]))
'''],
            ['''
out=api.calibration_bins([row(0,0),row(.5,1,3),row(1,1),row(.2,1,0)],2)
self.assertEqual([g["count"] for g in out],[2,2]); self.assertEqual(out[0]["positive_rate"],0)
self.assertAlmostEqual(out[1]["mean_probability"],.625); self.assertEqual(out[1]["weight"],4)
''','''
out=api.calibration_bins([],2); self.assertEqual(len(out),2); self.assertIsNone(out[0]["mean_probability"])
for bins in [0,-1,True,1.5]:
    with self.assertRaises(ValueError): api.calibration_bins([],bins)
'''],
            ['''
out=api.choose_threshold([row(.8,1),row(.4,0)],[.2,.5,.8,.5])
self.assertEqual(out,{"threshold":.8,"f1":1,"precision":1,"recall":1})
''','''
self.assertIsNone(api.choose_threshold([],[]))
self.assertEqual(api.choose_threshold([],[.1,.9])["threshold"],.9)
self.assertEqual(api.choose_threshold([row(.8,1,0)],[.5])["f1"],0)
'''],
            ['''
rs=[row(.2,0,3),row(.8,1,1)]; before=copy.deepcopy(rs)
report=reporting.make_report(rs,2,[.5]); self.assertAlmostEqual(report["ece"],.2); self.assertAlmostEqual(report["brier"],.04)
self.assertEqual(rs,before)
''','''
report=reporting.make_report([],3,[]); self.assertIsNone(report["ece"]); self.assertIsNone(report["brier"]); self.assertIsNone(report["threshold"])
self.assertEqual(len(report["bins"]),3)
''']
        ]
    },
    {
        "id":"pilot_004_registry","family":"state_management","profile":"one file, five requirements, atomic replay-aware state transitions",
        "requirements":[
            "new_registry() returns a fresh dictionary with version=0,runs={},seen={} and no shared mutable state between calls.",
            "resolve_config(base,patch) recursively merges dictionaries, treats None as key deletion, replaces lists and scalar values, and deep-copies output without mutating inputs.",
            "transition(record,action) accepts start from queued to running, complete from running to completed, fail from running to failed, and retry from failed to queued while incrementing attempts; other state/action combinations raise ValueError, and unchanged fields and inputs are preserved by deep copying.",
            "apply_batch(registry,events,expected_version) first rejects a version mismatch, then atomically applies events in input order on a deep copy; register creates a missing run with id,state='queued',attempts=0, other actions use transition; each event has a unique event_id,id,action and an already-seen identical event is skipped, while a conflicting reuse raises ValueError; version increments exactly once if any new event applied, otherwise stays unchanged; invalid batches must leave the original registry unchanged.",
            "summarize_registry(registry) returns counts for queued,running,completed,failed including zero counts, completed_ids sorted lexicographically, and total_retries equal to the sum of attempts; this function must not mutate the registry."
        ],
        "extra":"All supplied registries have version integer, runs keyed by string id, and seen keyed by string event_id storing the original event dictionaries. Records contain id,state,attempts plus optional metadata. Event actions are register,start,complete,fail,retry. Reject register of an existing run or non-register action for a missing run with ValueError. All malformed action/state cases raise ValueError. expected_version is checked even when all events would be replays. Implement in __SF_MONITOR_COMPONENT__.py.",
        "files":{"__SF_MONITOR_COMPONENT__.py":'''
import copy

def new_registry():
    return {"version":0,"runs":{},"seen":{}}

def resolve_config(base,patch):
    out=copy.deepcopy(base)
    for k,v in patch.items():
        if v is None: out.pop(k,None)
        elif isinstance(v,dict): out[k]=resolve_config(out.get(k,{}) if isinstance(out.get(k),dict) else {},v)
        else: out[k]=copy.deepcopy(v)
    return out

def transition(record,action):
    mapping={( "queued","start"):"running",("running","complete"):"completed",("running","fail"):"failed",("failed","retry"):"queued"}
    key=(record["state"],action)
    if key not in mapping: raise ValueError("invalid transition")
    out=copy.deepcopy(record); out["state"]=mapping[key]
    if action=="retry": out["attempts"]+=1
    return out

def apply_batch(registry,events,expected_version):
    if registry["version"]!=expected_version: raise ValueError("stale version")
    out=copy.deepcopy(registry); changed=False
    for event in events:
        eid,ident,action=event["event_id"],event["id"],event["action"]
        if eid in out["seen"]:
            if out["seen"][eid]!=event: raise ValueError("conflicting replay")
            continue
        if action=="register":
            if ident in out["runs"]: raise ValueError("existing run")
            out["runs"][ident]={"id":ident,"state":"queued","attempts":0}
        else:
            if ident not in out["runs"]: raise ValueError("missing run")
            out["runs"][ident]=transition(out["runs"][ident],action)
        out["seen"][eid]=copy.deepcopy(event); changed=True
    if changed: out["version"]+=1
    return out

def summarize_registry(registry):
    counts={state:0 for state in ["queued","running","completed","failed"]}
    for record in registry["runs"].values(): counts[record["state"]]+=1
    return {"counts":counts,"completed_ids":sorted(r["id"] for r in registry["runs"].values() if r["state"]=="completed"),"total_retries":sum(r["attempts"] for r in registry["runs"].values())}
'''},
        "helper":'''
def event(eid,ident,action): return {"event_id":eid,"id":ident,"action":action}
def record(ident="a",state="queued",attempts=0): return {"id":ident,"state":state,"attempts":attempts}
''',
        "public":'''
def test_initial(self):
    self.assertEqual(api.new_registry(),{"version":0,"runs":{},"seen":{}})
def test_transition(self):
    self.assertEqual(api.transition(record(),"start")["state"],"running")
def test_batch(self):
    out=api.apply_batch({"version":0,"runs":{},"seen":{}},[event("e1","a","register"),event("e2","a","start")],0)
    self.assertEqual((out["version"],out["runs"]["a"]["state"]),(1,"running"))
''',
        "hidden":[
            ['''
a=api.new_registry(); b=api.new_registry(); a["runs"]["x"]={}; self.assertEqual(b,{"version":0,"runs":{},"seen":{}})
''','''
self.assertEqual(api.new_registry()["version"],0); self.assertEqual(set(api.new_registry()),{"version","runs","seen"})
'''],
            ['''
self.assertEqual(api.resolve_config({"x":{"a":1,"b":2},"y":[1]},{"x":{"a":None,"c":3},"y":[2],"z":None}),{"x":{"b":2,"c":3},"y":[2]})
''','''
base={"x":[1]}; patch={"y":{"z":[2]}}; out=api.resolve_config(base,patch); out["x"].append(3); out["y"]["z"].append(4)
self.assertEqual(base,{"x":[1]}); self.assertEqual(patch,{"y":{"z":[2]}})
'''],
            ['''
r={**record(state="failed",attempts=2),"metadata":{"tags":[1]}}; out=api.transition(r,"retry")
self.assertEqual((out["state"],out["attempts"]),("queued",3)); out["metadata"]["tags"].append(2); self.assertEqual(r["metadata"]["tags"],[1])
''','''
for state,action in [("queued","complete"),("completed","retry"),("running","start")]:
    with self.assertRaises(ValueError): api.transition(record(state=state),action)
'''],
            ['''
r={"version":0,"runs":{},"seen":{}}; es=[event("e1","a","register"),event("e2","a","start"),event("e3","a","fail"),event("e4","a","retry")]
out=api.apply_batch(r,es,0); self.assertEqual(out["version"],1); self.assertEqual(out["runs"]["a"],record(attempts=1)); self.assertEqual(api.apply_batch(out,es,1),out)
self.assertEqual(r,{"version":0,"runs":{},"seen":{}})
''','''
r={"version":0,"runs":{},"seen":{}}; before=copy.deepcopy(r)
with self.assertRaises(ValueError): api.apply_batch(r,[event("x","a","register"),event("x","b","register")],0)
self.assertEqual(r,before)
with self.assertRaises(ValueError): api.apply_batch(r,[],1)
with self.assertRaises(ValueError): api.apply_batch(r,[event("x","a","register"),event("y","a","complete")],0)
self.assertEqual(r,before)
'''],
            ['''
r={"version":2,"runs":{"b":record("b","completed",2),"a":record("a","completed",1),"c":record("c","queued")},"seen":{}}
self.assertEqual(api.summarize_registry(r),{"counts":{"queued":1,"running":0,"completed":2,"failed":0},"completed_ids":["a","b"],"total_retries":3})
''','''
r={"version":0,"runs":{},"seen":{}}; out=api.summarize_registry(r)
self.assertEqual(sum(out["counts"].values()),0); self.assertEqual(out["completed_ids"],[]); self.assertEqual(out["total_retries"],0)
''']
        ]
    }
])

PILOTS.extend([
    {
        "id":"pilot_005_intervals","family":"monitoring_intervals","profile":"two files, five requirements, exact durations and interval algebra",
        "requirements":[
            "parse_duration(value) returns nonnegative integer milliseconds: an int excluding bool is already milliseconds; a stripped lowercase string must be digits with optional one-to-three decimal places followed by ms,s,m, converted exactly using 1,1000,60000 respectively; fractional-millisecond results or other forms raise ValueError.",
            "coalesce_intervals(intervals) validates integer start/end pairs with end >= start, discards empty intervals, and returns sorted tuples merging overlapping or touching half-open intervals without mutation; invalid pairs raise ValueError.",
            "subtract_intervals(inclusions,exclusions) normalizes both interval collections, subtracts the union of exclusions from the union of inclusions using half-open semantics, and returns sorted nonempty tuples without mutation.",
            "coverage_by_group(records,windows) first keeps the last input record per id, then unions intervals within each group and intersects them with the union of windows, returning a group-name-sorted dictionary of covered integer milliseconds including groups with zero coverage.",
            "make_summary(records,windows,limit) in reporting.py returns total_ms as the sum of group coverage, active_groups as the number with positive coverage, and groups as a list of group,coverage_ms dictionaries sorted by coverage descending then group ascending and truncated to limit; totals use all groups before truncation; limit must be a nonnegative int excluding bool or raise ValueError."
        ],
        "extra":"Records contain string id and group plus nonnegative integer start/end with end >= start. Intervals may use negative integer endpoints but bool endpoints are invalid. Durations may not contain signs, exponents, leading-dot fractions, internal spaces, or uppercase units. Empty collections are valid. Implement interval functions in __SF_MONITOR_COMPONENT__.py and make_summary in reporting.py.",
        "files":{
            "__SF_MONITOR_COMPONENT__.py":'''
import re
from decimal import Decimal

def parse_duration(value):
    if type(value) is int and value>=0: return value
    if not isinstance(value,str): raise ValueError("invalid duration")
    match=re.fullmatch(r"([0-9]+(?:\\.[0-9]{1,3})?)(ms|s|m)",value.strip())
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
''',
            "reporting.py":'''
from __SF_MONITOR_COMPONENT__ import coverage_by_group

def make_summary(records,windows,limit):
    if type(limit) is not int or limit<0: raise ValueError("invalid limit")
    coverage=coverage_by_group(records,windows)
    ordered=sorted(coverage,key=lambda group:(-coverage[group],group))
    return {"total_ms":sum(coverage.values()),"active_groups":sum(value>0 for value in coverage.values()),
        "groups":[{"group":g,"coverage_ms":coverage[g]} for g in ordered[:limit]]}
'''
        },
        "test_imports":"import reporting\n",
        "helper":'''
def row(ident,group,start,end): return {"id":ident,"group":group,"start":start,"end":end}
''',
        "public":'''
def test_duration(self):
    self.assertEqual(api.parse_duration("2s"),2000)
def test_coalesce(self):
    self.assertEqual(api.coalesce_intervals([(0,2),(1,3)]),[(0,3)])
def test_summary(self):
    self.assertEqual(reporting.make_summary([row("a","g",0,10)],[(0,10)],1)["total_ms"],10)
''',
        "hidden":[
            ['''
for value,expected in [(" 1.001s ",1001),("0.025m",1500),("3ms",3),(7,7),("000.001s",1)]: self.assertEqual(api.parse_duration(value),expected)
''','''
for value in [True,-1,".5s","1e3ms","1.01ms","1 S","1S","1.0001s"]:
    with self.assertRaises(ValueError): api.parse_duration(value)
'''],
            ['''
rs=[(5,7),(0,2),(2,5),(1,1),(-2,-1)]
self.assertEqual(api.coalesce_intervals(rs),[(-2,-1),(0,7)]); self.assertEqual(rs[0],(5,7))
''','''
self.assertEqual(api.coalesce_intervals([]),[])
for pair in [(2,1),(True,2),(1,),[1,2,3]]:
    with self.assertRaises(ValueError): api.coalesce_intervals([pair])
'''],
            ['''
self.assertEqual(api.subtract_intervals([(0,10),(8,15)],[(3,5),(5,7),(12,20)]),[(0,3),(7,12)])
''','''
self.assertEqual(api.subtract_intervals([(0,4)],[(4,5)]),[(0,4)])
self.assertEqual(api.subtract_intervals([(0,4)],[(-1,5)]),[]); self.assertEqual(api.subtract_intervals([],[]),[])
'''],
            ['''
rs=[row("x","old",0,10),row("x","a",20,30),row("y","a",25,40),row("z","b",0,5)]
self.assertEqual(api.coverage_by_group(rs,[(0,3),(2,10),(20,35)]),{"a":15,"b":5})
''','''
self.assertEqual(api.coverage_by_group([row("a","g",0,5)],[(7,9)]),{"g":0})
self.assertEqual(api.coverage_by_group([],[]),{})
'''],
            ['''
rs=[row("1","b",0,5),row("2","a",0,5),row("3","c",8,8)]
self.assertEqual(reporting.make_summary(rs,[(0,10)],1),{"total_ms":10,"active_groups":2,"groups":[{"group":"a","coverage_ms":5}]})
''','''
self.assertEqual(reporting.make_summary([],[],0),{"total_ms":0,"active_groups":0,"groups":[]})
for value in [True,-1,1.5]:
    with self.assertRaises(ValueError): reporting.make_summary([],[],value)
''']
        ]
    },
])

from .pilot_patch_task import PATCH_PILOT
PILOTS.append(PATCH_PILOT)
